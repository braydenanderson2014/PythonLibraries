"""
Net Worth Tracking System for Financial Tracker
Tracks assets vs liabilities over time with monthly snapshots
"""

import json
import os
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

from assets.Logger import Logger
logger = Logger()


class NetWorthSnapshot:
    """Represents a snapshot of net worth at a specific point in time"""
    
    def __init__(self, snapshot_date, assets=0.0, liabilities=0.0, 
                 account_breakdown=None, user_id=None):
        """
        Initialize a net worth snapshot.
        
        Args:
            snapshot_date: Date of snapshot (YYYY-MM-DD)
            assets: Total assets amount
            liabilities: Total liabilities amount
            account_breakdown: Dict of account_id -> balance
            user_id: User ID who owns this snapshot
        """
        self.date = snapshot_date if isinstance(snapshot_date, str) else snapshot_date.isoformat()
        self.assets = float(assets)
        self.liabilities = float(liabilities)
        self.net_worth = self.assets - self.liabilities
        self.account_breakdown = account_breakdown or {}
        self.user_id = user_id
        logger.debug("NetWorthSnapshot", f"Created snapshot for {self.date} with assets=${self.assets:.2f}, liabilities=${self.liabilities:.2f}, net_worth=${self.net_worth:.2f}")
    
    def get_asset_allocation(self):
        """Get breakdown of assets by account"""
        assets = {k: v for k, v in self.account_breakdown.items() if v > 0}
        return assets
    
    def get_liability_breakdown(self):
        """Get breakdown of liabilities by account"""
        liabilities = {k: abs(v) for k, v in self.account_breakdown.items() if v < 0}
        return liabilities
    
    def to_dict(self):
        """Convert snapshot to dictionary for JSON serialization"""
        return {
            'date': self.date,
            'assets': self.assets,
            'liabilities': self.liabilities,
            'net_worth': self.net_worth,
            'account_breakdown': self.account_breakdown,
            'user_id': self.user_id
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create snapshot from dictionary"""
        snapshot = cls(
            snapshot_date=data['date'],
            assets=data.get('assets', 0.0),
            liabilities=data.get('liabilities', 0.0),
            account_breakdown=data.get('account_breakdown', {}),
            user_id=data.get('user_id')
        )
        return snapshot


class NetWorthTracker:
    """Manages net worth snapshots and calculations"""
    
    def __init__(self, history_file='resources/net_worth_history.json'):
        """
        Initialize Net Worth Tracker.
        
        Args:
            history_file: Path to history JSON file
        """
        self.history_file = history_file
        self.snapshots = []
        self.load()
    
    def load(self):
        """Load snapshots from JSON file"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    self.snapshots = [NetWorthSnapshot.from_dict(s) for s in data]
                    # Sort by date
                    self.snapshots.sort(key=lambda s: s.date)
                logger.info("NetWorthTracker", f"Loaded {len(self.snapshots)} net worth snapshots from {self.history_file}")
            except Exception as e:
                logger.error("NetWorthTracker", f"Failed to load net worth history: {str(e)}")
                self.snapshots = []
        else:
            logger.debug("NetWorthTracker", f"History file not found at {self.history_file}, initializing empty snapshots")
            self.snapshots = []
            self.save()
    
    def save(self):
        """Save snapshots to JSON file"""
        try:
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            
            with open(self.history_file, 'w') as f:
                json.dump([s.to_dict() for s in self.snapshots], f, indent=2)
            
            logger.debug("NetWorthTracker", f"Saved {len(self.snapshots)} snapshots to {self.history_file}")
        except Exception as e:
            logger.error("NetWorthTracker", f"Failed to save net worth history: {str(e)}")
    
    def calculate_current_net_worth(self, bank, account_manager, user_id=None):
        """
        Calculate current net worth from bank and account data.
        
        Args:
            bank: Bank instance with transactions and loans
            account_manager: AccountManager instance
            user_id: User ID to calculate for
        
        Returns:
            NetWorthSnapshot: Current snapshot
        """
        assets = 0.0
        liabilities = 0.0
        account_breakdown = {}
        
        # Calculate account balances
        accounts = account_manager.list_accounts()
        for account in accounts:
            if user_id and account.user_id != user_id:
                continue
            
            if not account.active:
                continue
            
            # Start with initial balance
            balance = account.initial_balance
            
            # Add/subtract transactions for this account
            transactions = bank.list_transactions(user_id=user_id)
            for tx in transactions:
                if tx.get('account_id') == account.account_id:
                    if tx['type'] == 'in':
                        balance += tx['amount']
                    else:
                        balance -= tx['amount']
            
            account_breakdown[account.get_display_name()] = balance
            
            if balance >= 0:
                assets += balance
            else:
                liabilities += abs(balance)
        
        # Add loans as liabilities
        loans = bank.list_loans(user_id=user_id)
        for loan in loans:
            if loan.active:
                remaining = loan.remaining_principal
                if remaining > 0:
                    loan_name = f"{loan.desc} (Loan)"
                    account_breakdown[loan_name] = -remaining
                    liabilities += remaining
        
        snapshot = NetWorthSnapshot(
            snapshot_date=date.today(),
            assets=assets,
            liabilities=liabilities,
            account_breakdown=account_breakdown,
            user_id=user_id
        )
        
        return snapshot
    
    def add_snapshot(self, snapshot):
        """
        Add a snapshot to history.
        
        Args:
            snapshot: NetWorthSnapshot instance
        """
        # Check if snapshot for this date already exists
        existing = self.get_snapshot_by_date(snapshot.date, snapshot.user_id)
        if existing:
            logger.debug("NetWorthTracker", f"Replacing existing snapshot for {snapshot.date}")
            # Replace existing snapshot
            self.snapshots = [s for s in self.snapshots 
                            if not (s.date == snapshot.date and s.user_id == snapshot.user_id)]
        
        self.snapshots.append(snapshot)
        self.snapshots.sort(key=lambda s: s.date)
        self.save()
        logger.info("NetWorthTracker", f"Added snapshot for {snapshot.date} with net_worth=${snapshot.net_worth:.2f}")
    
    def get_snapshot_by_date(self, snapshot_date, user_id=None):
        """Get snapshot for a specific date"""
        date_str = snapshot_date if isinstance(snapshot_date, str) else snapshot_date.isoformat()
        
        for snapshot in self.snapshots:
            if snapshot.date == date_str:
                if user_id is None or snapshot.user_id == user_id:
                    return snapshot
        return None
    
    def get_snapshots_for_user(self, user_id=None):
        """Get all snapshots for a user"""
        if user_id is None:
            return self.snapshots
        
        return [s for s in self.snapshots if s.user_id == user_id]
    
    def get_latest_snapshot(self, user_id=None):
        """Get most recent snapshot"""
        snapshots = self.get_snapshots_for_user(user_id)
        if not snapshots:
            return None
        return snapshots[-1]
    
    def get_snapshots_in_range(self, start_date, end_date, user_id=None):
        """
        Get snapshots within a date range.
        
        Args:
            start_date: Start date (YYYY-MM-DD or date object)
            end_date: End date (YYYY-MM-DD or date object)
            user_id: Optional user filter
        
        Returns:
            List of snapshots
        """
        start_str = start_date if isinstance(start_date, str) else start_date.isoformat()
        end_str = end_date if isinstance(end_date, str) else end_date.isoformat()
        
        snapshots = self.get_snapshots_for_user(user_id)
        return [s for s in snapshots if start_str <= s.date <= end_str]
    
    def get_growth_rate(self, user_id=None, months=12):
        """
        Calculate growth rate over specified months.
        
        Args:
            user_id: User ID
            months: Number of months to calculate over
        
        Returns:
            dict: Growth statistics
        """
        snapshots = self.get_snapshots_for_user(user_id)
        logger.debug("NetWorthTracker", f"Calculating growth rate for {len(snapshots)} snapshots over {months} months")
        
        if len(snapshots) < 2:
            logger.warning("NetWorthTracker", f"Insufficient snapshots ({len(snapshots)}) for growth calculation")
            return {
                'absolute_change': 0.0,
                'percentage_change': 0.0,
                'monthly_average': 0.0,
                'insufficient_data': True
            }
        
        # Get snapshots from last N months
        end_date = date.today()
        start_date = end_date - relativedelta(months=months)
        
        recent_snapshots = self.get_snapshots_in_range(start_date, end_date, user_id)
        
        if len(recent_snapshots) < 2:
            # Fall back to oldest and newest available
            oldest = snapshots[0]
            newest = snapshots[-1]
            logger.debug("NetWorthTracker", f"Using full range: {oldest.date} to {newest.date}")
        else:
            oldest = recent_snapshots[0]
            newest = recent_snapshots[-1]
            logger.debug("NetWorthTracker", f"Using recent range: {oldest.date} to {newest.date}")
        
        absolute_change = newest.net_worth - oldest.net_worth
        
        if oldest.net_worth != 0:
            percentage_change = (absolute_change / abs(oldest.net_worth)) * 100
        else:
            percentage_change = 0.0
        
        # Calculate monthly average
        date_diff_days = (datetime.strptime(newest.date, '%Y-%m-%d') - 
                         datetime.strptime(oldest.date, '%Y-%m-%d')).days
        months_elapsed = max(1, date_diff_days / 30.0)
        monthly_average = absolute_change / months_elapsed
        
        logger.info("NetWorthTracker", f"Growth rate calculated: absolute_change=${absolute_change:.2f}, percentage={percentage_change:.2f}%, monthly_avg=${monthly_average:.2f}")
        return {
            'absolute_change': absolute_change,
            'percentage_change': percentage_change,
            'monthly_average': monthly_average,
            'oldest_date': oldest.date,
            'newest_date': newest.date,
            'oldest_value': oldest.net_worth,
            'newest_value': newest.net_worth,
            'insufficient_data': False
        }
    
    def get_statistics(self, user_id=None):
        """
        Get comprehensive statistics.
        
        Returns:
            dict: Statistics
        """
        snapshots = self.get_snapshots_for_user(user_id)
        logger.debug("NetWorthTracker", f"Calculating statistics for {len(snapshots)} snapshots")
        
        if not snapshots:
            logger.warning("NetWorthTracker", "No snapshots available for statistics")
            return {
                'total_snapshots': 0,
                'current_net_worth': 0.0,
                'highest_net_worth': 0.0,
                'lowest_net_worth': 0.0,
                'average_net_worth': 0.0
            }
        
        net_worths = [s.net_worth for s in snapshots]
        stats = {
            'total_snapshots': len(snapshots),
            'current_net_worth': snapshots[-1].net_worth if snapshots else 0.0,
            'highest_net_worth': max(net_worths),
            'lowest_net_worth': min(net_worths),
            'average_net_worth': sum(net_worths) / len(net_worths),
            'current_assets': snapshots[-1].assets if snapshots else 0.0,
            'current_liabilities': snapshots[-1].liabilities if snapshots else 0.0,
            'first_snapshot_date': snapshots[0].date if snapshots else None,
            'latest_snapshot_date': snapshots[-1].date if snapshots else None
        }
        logger.info("NetWorthTracker", f"Statistics: current=${stats['current_net_worth']:.2f}, high=${stats['highest_net_worth']:.2f}, low=${stats['lowest_net_worth']:.2f}, avg=${stats['average_net_worth']:.2f}")
        return stats
    
    def create_monthly_snapshot(self, bank, account_manager, user_id=None):
        """
        Create a monthly snapshot for the first day of current month.
        
        Args:
            bank: Bank instance
            account_manager: AccountManager instance
            user_id: User ID
        
        Returns:
            NetWorthSnapshot: Created snapshot or None if already exists
        """
        # First day of current month
        today = date.today()
        first_of_month = date(today.year, today.month, 1)
        logger.debug("NetWorthTracker", f"Creating monthly snapshot for {first_of_month}")
        
        # Check if snapshot already exists
        existing = self.get_snapshot_by_date(first_of_month, user_id)
        if existing:
            logger.debug("NetWorthTracker", f"Monthly snapshot already exists for {first_of_month}")
            return None
        
        # Calculate and save snapshot
        snapshot = self.calculate_current_net_worth(bank, account_manager, user_id)
        snapshot.date = first_of_month.isoformat()
        self.add_snapshot(snapshot)
        logger.info("NetWorthTracker", f"Created monthly snapshot for {first_of_month} with net_worth=${snapshot.net_worth:.2f}")
        
        return snapshot
    
    def delete_snapshot(self, snapshot_date, user_id=None):
        """Delete a snapshot"""
        date_str = snapshot_date if isinstance(snapshot_date, str) else snapshot_date.isoformat()
        
        self.snapshots = [s for s in self.snapshots 
                         if not (s.date == date_str and (user_id is None or s.user_id == user_id))]
        self.save()
    
    def export_to_csv(self, file_path, user_id=None):
        """Export snapshots to CSV file"""
        import csv
        
        snapshots = self.get_snapshots_for_user(user_id)
        logger.debug("NetWorthTracker", f"Exporting {len(snapshots)} snapshots to {file_path}")
        
        try:
            from datetime import datetime
            with open(file_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Report Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
                writer.writerow([])
                writer.writerow(['Date', 'Assets', 'Liabilities', 'Net Worth'])
                
                for snapshot in snapshots:
                    writer.writerow([
                        snapshot.date,
                        f'{snapshot.assets:.2f}',
                        f'{snapshot.liabilities:.2f}',
                        f'{snapshot.net_worth:.2f}'
                    ])
            
            logger.info("NetWorthTracker", f"Successfully exported {len(snapshots)} snapshots to {file_path}")
            return True
        except Exception as e:
            logger.error("NetWorthTracker", f"Failed to export net worth data to {file_path}: {str(e)}")
            return False
