import json
import os
from datetime import datetime, date
from typing import Dict, List, Optional
from calendar import monthrange
try:
    from .app_paths import BUDGETS_DATA_FILE
except ImportError:
    from app_paths import BUDGETS_DATA_FILE
from assets.Logger import Logger
logger = Logger()


class Budget:
    """Represents a budget for a specific category with spending limits"""
    
    def __init__(self, category, monthly_limit, identifier=None, user_id=None, 
                 color_good='#4CAF50', color_warning='#FF9800', color_over='#F44336',
                 warning_threshold=0.8, notes=''):
        logger.debug("Budget", f"Creating budget for category: {category}, limit: ${monthly_limit}")
        self.category = category
        self.monthly_limit = monthly_limit
        self.identifier = identifier or self._generate_identifier()
        self.user_id = user_id
        self.color_good = color_good  # Green when under budget
        self.color_warning = color_warning  # Orange when approaching limit
        self.color_over = color_over  # Red when over budget
        self.warning_threshold = warning_threshold  # Percentage (0.8 = 80%)
        self.notes = notes
        self.active = True
    
    @staticmethod
    def _generate_identifier():
        import random
        import string
        return ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(12))
    
    def to_dict(self):
        return {
            'category': self.category,
            'monthly_limit': self.monthly_limit,
            'identifier': self.identifier,
            'user_id': self.user_id,
            'color_good': self.color_good,
            'color_warning': self.color_warning,
            'color_over': self.color_over,
            'warning_threshold': self.warning_threshold,
            'notes': self.notes,
            'active': self.active
        }
    
    @classmethod
    def from_dict(cls, data):
        budget = cls(
            category=data.get('category'),
            monthly_limit=data.get('monthly_limit'),
            identifier=data.get('identifier'),
            user_id=data.get('user_id'),
            color_good=data.get('color_good', '#4CAF50'),
            color_warning=data.get('color_warning', '#FF9800'),
            color_over=data.get('color_over', '#F44336'),
            warning_threshold=data.get('warning_threshold', 0.8),
            notes=data.get('notes', '')
        )
        budget.active = data.get('active', True)
        return budget


class BudgetManager:
    """Manages budgets and tracks spending against them"""
    
    def __init__(self, user_id=None):
        logger.debug("BudgetManager", f"Initializing BudgetManager for user: {user_id}")
        self.user_id = user_id
        self.budgets: List[Budget] = []
        self.load_budgets()
        logger.info("BudgetManager", "BudgetManager initialization complete")
    
    def load_budgets(self):
        """Load budgets from JSON file"""
        logger.debug("BudgetManager", f"Loading budgets for user: {self.user_id}")
        if os.path.exists(BUDGETS_DATA_FILE):
            try:
                with open(BUDGETS_DATA_FILE, 'r') as f:
                    data = json.load(f)
                    self.budgets = [Budget.from_dict(b) for b in data]
                    # Filter by user if user_id is set
                    if self.user_id:
                        self.budgets = [b for b in self.budgets if b.user_id == self.user_id]
                logger.info("BudgetManager", f"Loaded {len(self.budgets)} budgets for user {self.user_id}")
            except Exception as e:
                logger.error("BudgetManager", f"Error loading budgets: {str(e)}")
                self.budgets = []
        else:
            logger.debug("BudgetManager", "No budgets file found, starting with empty list")
            self.budgets = []
    
    def save_budgets(self):
        """Save all budgets to JSON file"""
        logger.debug("BudgetManager", f"Saving {len(self.budgets)} budgets for user {self.user_id}")
        # Load all budgets first (including other users)
        all_budgets = []
        if os.path.exists(BUDGETS_DATA_FILE):
            try:
                with open(BUDGETS_DATA_FILE, 'r') as f:
                    all_budgets = json.load(f)
            except Exception as e:
                logger.error("BudgetManager", f"Error loading all budgets: {str(e)}")
                all_budgets = []
        
        # Remove budgets for current user
        if self.user_id:
            all_budgets = [b for b in all_budgets if b.get('user_id') != self.user_id]
        
        # Add current user's budgets
        all_budgets.extend([b.to_dict() for b in self.budgets])
        
        # Save to file
        try:
            os.makedirs(os.path.dirname(BUDGETS_DATA_FILE), exist_ok=True)
            with open(BUDGETS_DATA_FILE, 'w') as f:
                json.dump(all_budgets, f, indent=2)
            logger.info("BudgetManager", f"Saved {len(self.budgets)} budgets to file")
        except Exception as e:
            logger.error("BudgetManager", f"Error saving budgets: {str(e)}")
    
    def add_budget(self, budget: Budget):
        """Add a new budget"""
        logger.info("BudgetManager", f"Adding budget for category '{budget.category}' with limit ${budget.monthly_limit}")
        self.budgets.append(budget)
        self.save_budgets()
    
    def remove_budget(self, identifier: str):
        """Remove a budget by identifier"""
        logger.info("BudgetManager", f"Removing budget with identifier: {identifier}")
        self.budgets = [b for b in self.budgets if b.identifier != identifier]
        self.save_budgets()
    
    def update_budget(self, identifier: str, **kwargs):
        """Update an existing budget"""
        logger.debug("BudgetManager", f"Updating budget {identifier} with {len(kwargs)} field(s)")
        for budget in self.budgets:
            if budget.identifier == identifier:
                logger.info("BudgetManager", f"Updated budget for category '{budget.category}' with changes: {list(kwargs.keys())}")
                for key, value in kwargs.items():
                    if hasattr(budget, key):
                        setattr(budget, key, value)
                self.save_budgets()
                return True
        logger.warning("BudgetManager", f"Budget {identifier} not found for update")
        return False
    
    def get_budget(self, category: str) -> Optional[Budget]:
        """Get budget for a specific category"""
        logger.debug("BudgetManager", f"Retrieving budget for category: {category}")
        for budget in self.budgets:
            if budget.category == category and budget.active:
                logger.debug("BudgetManager", f"Found budget for category '{category}': ${budget.monthly_limit}")
                return budget
        logger.debug("BudgetManager", f"No budget found for category: {category}")
        return None
    
    def get_all_budgets(self) -> List[Budget]:
        """Get all active budgets"""
        active_budgets = [b for b in self.budgets if b.active]
        logger.debug("BudgetManager", f"Retrieved {len(active_budgets)} active budgets")
        return active_budgets
    
    def calculate_spending(self, transactions: List, category: str, year: int, month: int) -> float:
        """Calculate total spending for a category in a specific month (handles split transactions)"""
        logger.debug("BudgetManager", f"Calculating spending for '{category}' in {year}-{month:02d}")
        total = 0.0
        for trans in transactions:
            # Only count outgoing transactions
            if trans.get('type') not in ['out', 'loan_payment']:
                continue
            
            # Check date first
            trans_date = trans.get('date')
            if not trans_date:
                continue
            
            try:
                dt = datetime.strptime(trans_date, '%Y-%m-%d')
                if dt.year != year or dt.month != month:
                    continue
            except:
                continue
            
            # Check if transaction is split
            splits = trans.get('splits', [])
            if splits:
                # Sum amounts from splits that match this category
                for split in splits:
                    if split.get('category') == category:
                        total += abs(float(split.get('amount', 0)))
            else:
                # Regular transaction - check main category
                if trans.get('category') == category:
                    total += abs(float(trans.get('amount', 0)))
        
        logger.info("BudgetManager", f"Total spending for '{category}' in {year}-{month:02d}: ${total:.2f}")
        return total
    
    def get_budget_status(self, transactions: List, category: str, year: int = None, month: int = None) -> Dict:
        """
        Get budget status for a category in a specific month
        Returns: {
            'budget': Budget object or None,
            'spent': float,
            'remaining': float,
            'percentage': float,
            'status': 'good' | 'warning' | 'over' | 'no_budget',
            'color': str (hex color)
        }
        """
        # Use current month if not specified
        if year is None or month is None:
            today = date.today()
            year = today.year
            month = today.month
        
        logger.debug("BudgetManager", f"Getting budget status for '{category}' in {year}-{month:02d}")
        budget = self.get_budget(category)
        
        if not budget:
            logger.debug("BudgetManager", f"No budget found for category '{category}'")
            return {
                'budget': None,
                'spent': 0.0,
                'remaining': 0.0,
                'percentage': 0.0,
                'status': 'no_budget',
                'color': None
            }
        
        spent = self.calculate_spending(transactions, category, year, month)
        remaining = budget.monthly_limit - spent
        percentage = (spent / budget.monthly_limit) if budget.monthly_limit > 0 else 0.0
        
        # Determine status and color
        if percentage >= 1.0:
            status = 'over'
            color = budget.color_over
            logger.warning("BudgetManager", f"Budget '{category}' is OVER BUDGET: ${spent:.2f} / ${budget.monthly_limit:.2f}")
        elif percentage >= budget.warning_threshold:
            status = 'warning'
            color = budget.color_warning
            logger.warning("BudgetManager", f"Budget '{category}' is APPROACHING LIMIT: ${spent:.2f} / ${budget.monthly_limit:.2f} ({percentage*100:.1f}%)")
        else:
            status = 'good'
            color = budget.color_good
            logger.debug("BudgetManager", f"Budget '{category}' status GOOD: ${spent:.2f} / ${budget.monthly_limit:.2f}")
        
        return {
            'budget': budget,
            'spent': spent,
            'remaining': remaining,
            'percentage': percentage,
            'status': status,
            'color': color
        }
    
    def check_transaction(self, transaction: Dict, all_transactions: List) -> Dict:
        """
        Check if a transaction fits within budget
        Returns budget status including whether this transaction should be highlighted
        """
        logger.debug("BudgetManager", f"Checking transaction against budget")
        category = transaction.get('category')
        if not category:
            logger.debug("BudgetManager", "Transaction has no category, cannot check budget")
            return {'status': 'no_budget', 'color': None, 'message': 'No category'}
        
        # Get transaction date
        trans_date = transaction.get('date')
        if not trans_date:
            logger.debug("BudgetManager", "Transaction has no date, cannot check budget")
            return {'status': 'no_budget', 'color': None, 'message': 'No date'}
        
        try:
            dt = datetime.strptime(trans_date, '%Y-%m-%d')
        except:
            logger.warning("BudgetManager", f"Invalid transaction date format: {trans_date}")
            return {'status': 'no_budget', 'color': None, 'message': 'Invalid date'}
        
        # Only check outgoing transactions
        if transaction.get('type') not in ['out', 'loan_payment']:
            logger.debug("BudgetManager", "Transaction is income, skipping budget check")
            return {'status': 'income', 'color': None, 'message': 'Income transaction'}
        
        logger.debug("BudgetManager", f"Checking category '{category}' for date {dt.year}-{dt.month:02d}")
        status = self.get_budget_status(all_transactions, category, dt.year, dt.month)
        
        return {
            'status': status['status'],
            'color': status['color'],
            'message': f"${status['spent']:.2f} / ${status['budget'].monthly_limit:.2f}" if status['budget'] else 'No budget',
            'percentage': status['percentage'],
            'spent': status['spent'],
            'budget_limit': status['budget'].monthly_limit if status['budget'] else 0
        }
    
    def get_monthly_summary(self, transactions: List, year: int = None, month: int = None) -> Dict:
        """Get summary of all budget statuses for a month"""
        if year is None or month is None:
            today = date.today()
            year = today.year
            month = today.month
        
        logger.info("BudgetManager", f"Generating monthly budget summary for {year}-{month:02d}")
        summary = {
            'total_budgeted': 0.0,
            'total_spent': 0.0,
            'categories': {}
        }
        
        for budget in self.get_all_budgets():
            status = self.get_budget_status(transactions, budget.category, year, month)
            summary['total_budgeted'] += budget.monthly_limit
            summary['total_spent'] += status['spent']
            summary['categories'][budget.category] = status
        
        logger.info("BudgetManager", f"Monthly summary: ${summary['total_spent']:.2f} spent of ${summary['total_budgeted']:.2f} budgeted ({len(summary['categories'])} categories)")
        return summary
