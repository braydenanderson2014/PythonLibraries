import json
import os
import sqlite3
from assets.Logger import Logger
from datetime import datetime, date
from typing import List, Dict, Any, Optional
try:
    from .app_paths import ACTION_QUEUE_FILE
except ImportError:
    from app_paths import ACTION_QUEUE_FILE
logger = Logger()
class ActionQueue:
    """
    A queue system for scheduled actions like rent changes, notifications, etc.
    Actions are executed when their scheduled date is reached.
    """
    
    def __init__(self, queue_file=None):
        self.queue_file = queue_file or ACTION_QUEUE_FILE
        self.actions = []
        logger.info("ActionQueue", f"Initializing with queue file: {self.queue_file}")
        self.load()
    
    def add_action(self, action_type: str, scheduled_date: str, tenant_id: str, 
                   action_data: Dict[str, Any], description: str = "") -> str:
        """
        Add a new action to the queue
        
        Args:
            action_type: Type of action ('rent_change', 'notification', 'lease_expiry', etc.)
            scheduled_date: Date when action should be executed (YYYY-MM-DD format)
            tenant_id: ID of the tenant this action applies to
            action_data: Dictionary containing action-specific data
            description: Human-readable description of the action
            
        Returns:
            action_id: Unique identifier for the queued action
        """
        action_id = self._generate_action_id()
        
        action = {
            'action_id': action_id,
            'action_type': action_type,
            'scheduled_date': scheduled_date,
            'tenant_id': tenant_id,
            'action_data': action_data,
            'description': description,
            'status': 'pending',
            'created_date': date.today().strftime('%Y-%m-%d'),
            'executed_date': None,
            'execution_result': None
        }
        
        self.actions.append(action)
        logger.info("ActionQueue", f"Added action: {action}")
        self.save()
        return action_id
    
    def add_rent_change(self, tenant_id: str, new_rent: float, effective_date: str, 
                       old_rent: float = None, notes: str = "") -> str:
        """
        Queue a rent change action
        
        Args:
            tenant_id: ID of the tenant
            new_rent: New rent amount
            effective_date: Date when rent change takes effect (YYYY-MM-DD)
            old_rent: Current rent amount (for reference)
            notes: Optional notes about the rent change
            
        Returns:
            action_id: Unique identifier for the queued rent change
        """
        action_data = {
            'new_rent': new_rent,
            'old_rent': old_rent,
            'notes': notes
        }
        
        description = f"Change rent to ${new_rent:.2f}"
        if old_rent:
            if new_rent > old_rent:
                description += f" (increase from ${old_rent:.2f})"
            elif new_rent < old_rent:
                description += f" (decrease from ${old_rent:.2f})"
        logger.debug("ActionQueue", f"Preparing rent change action: {description}")
        return self.add_action('rent_change', effective_date, tenant_id, action_data, description)
    
    def add_rental_period_change(self, tenant_id: str, new_start_date: str, new_end_date: str, 
                                effective_date: str, period_description: str = "", notes: str = "") -> str:
        """
        Queue a rental period change action (e.g., lease renewal)
        
        Args:
            tenant_id: ID of the tenant
            new_start_date: New lease start date (YYYY-MM-DD)
            new_end_date: New lease end date (YYYY-MM-DD)
            effective_date: Date when period change takes effect (usually same as new_start_date)
            period_description: Description like "12 months" or "1 year"
            notes: Optional notes about the period change
            
        Returns:
            action_id: Unique identifier for the queued period change
        """
        action_data = {
            'new_start_date': new_start_date,
            'new_end_date': new_end_date,
            'period_description': period_description,
            'notes': notes
        }
        
        from datetime import datetime
        start_formatted = datetime.strptime(new_start_date, '%Y-%m-%d').strftime('%b %d, %Y')
        end_formatted = datetime.strptime(new_end_date, '%Y-%m-%d').strftime('%b %d, %Y')
        description = f"Update rental period to {start_formatted} - {end_formatted}"
        if period_description:
            description += f" ({period_description})"
        
        logger.debug("ActionQueue", f"Preparing rental period change action: {description}")
        return self.add_action('rental_period_change', effective_date, tenant_id, action_data, description)
    
    def add_notification(self, tenant_id: str, notification_date: str, 
                        message: str, notification_type: str = 'general') -> str:
        """
        Queue a notification action
        
        Args:
            tenant_id: ID of the tenant (can be 'all' for system-wide notifications)
            notification_date: Date when notification should be shown
            message: Notification message
            notification_type: Type of notification ('lease_expiry', 'rent_increase', 'general', etc.)
            
        Returns:
            action_id: Unique identifier for the queued notification
        """
        action_data = {
            'message': message,
            'notification_type': notification_type
        }
        logger.debug("ActionQueue", f"Preparing notification action: {message[:50]}...")
        return self.add_action('notification', notification_date, tenant_id, action_data, f"Notification: {message[:50]}...")
    
    def get_pending_actions(self, tenant_id: str = None) -> List[Dict]:
        """Get all pending actions, optionally filtered by tenant"""
        pending = [action for action in self.actions if action['status'] == 'pending']
        
        if tenant_id:
            pending = [action for action in pending if action['tenant_id'] == tenant_id]
        
        # Sort by scheduled date
        pending.sort(key=lambda x: x['scheduled_date'])
        logger.debug("ActionQueue", f"Retrieved {len(pending)} pending actions for tenant: {tenant_id}")
        return pending
    
    def get_due_actions(self, check_date: str = None) -> List[Dict]:
        """Get actions that are due to be executed"""
        if check_date is None:
            check_date = date.today().strftime('%Y-%m-%d')
        
        due_actions = []
        for action in self.actions:
            if (action['status'] == 'pending' and 
                action['scheduled_date'] <= check_date):
                due_actions.append(action)
        
        logger.debug("ActionQueue", f"Retrieved {len(due_actions)} due actions as of {check_date}")
        return due_actions
    
    def execute_action(self, action_id: str, execution_result: Dict = None) -> bool:
        """
        Mark an action as executed
        
        Args:
            action_id: ID of the action to execute
            execution_result: Optional result data from the execution
            
        Returns:
            bool: True if action was found and marked as executed
        """
        for action in self.actions:
            if action['action_id'] == action_id:
                action['status'] = 'executed'
                action['executed_date'] = date.today().strftime('%Y-%m-%d')
                action['execution_result'] = execution_result
                self.save()
                logger.info("ActionQueue", f"Executed action: {action_id}")
                return True
        logger.warning("ActionQueue", f"Action ID not found for execution: {action_id}")
        return False
    
    def cancel_action(self, action_id: str, reason: str = "") -> bool:
        """
        Cancel a pending action
        
        Args:
            action_id: ID of the action to cancel
            reason: Optional reason for cancellation
            
        Returns:
            bool: True if action was found and cancelled
        """
        for action in self.actions:
            if action['action_id'] == action_id and action['status'] == 'pending':
                action['status'] = 'cancelled'
                action['execution_result'] = {'cancelled': True, 'reason': reason}
                self.save()
                logger.info("ActionQueue", f"Cancelled action: {action_id} Reason: {reason}")
                return True
        logger.warning("ActionQueue", f"Action ID not found or not pending for cancellation: {action_id}")
        return False
    
    def get_action(self, action_id: str) -> Optional[Dict]:
        """Get a specific action by ID"""
        for action in self.actions:
            if action['action_id'] == action_id:
                logger.debug("ActionQueue", f"Retrieved action: {action_id}")
                return action
        logger.warning("ActionQueue", f"Action ID not found: {action_id}")
        return None
    
    def get_tenant_actions(self, tenant_id: str, status: str = None) -> List[Dict]:
        """Get all actions for a specific tenant"""
        tenant_actions = [action for action in self.actions if action['tenant_id'] == tenant_id]
        
        if status:
            tenant_actions = [action for action in tenant_actions if action['status'] == status]
        
        # Sort by scheduled date (newest first)
        tenant_actions.sort(key=lambda x: x['scheduled_date'], reverse=True)
        logger.debug("ActionQueue", f"Retrieved {len(tenant_actions)} actions for tenant: {tenant_id}")
        return tenant_actions
    
    def get_all_actions(self, status: str = None) -> List[Dict]:
        """Get all actions, optionally filtered by status"""
        if status:
            filtered_actions = [action for action in self.actions if action['status'] == status]
        else:
            filtered_actions = self.actions.copy()
        
        # Sort by scheduled date (newest first)
        filtered_actions.sort(key=lambda x: x['scheduled_date'], reverse=True)
        logger.debug("ActionQueue", f"Retrieved {len(filtered_actions)} actions with status: {status if status else 'all'}")
        return filtered_actions
    
    def remove_action(self, action_id: str) -> bool:
        """Remove an action from the queue by ID"""
        original_count = len(self.actions)
        self.actions = [action for action in self.actions if action['action_id'] != action_id]
        
        if len(self.actions) < original_count:
            self.save()
            logger.info("ActionQueue", f"Removed action: {action_id}")
        return False
    
    def cleanup_old_actions(self, days_old: int = 365):
        """Remove executed/cancelled actions older than specified days"""
        from datetime import timedelta
        
        cutoff_date = datetime.now().date() - timedelta(days=days_old)
        cutoff_str = cutoff_date.strftime('%Y-%m-%d')
        
        # Count actions before cleanup
        old_count = len(self.actions)
        
        # Keep only actions that are:
        # 1. Still pending, OR
        # 2. Executed/cancelled but newer than cutoff date
        filtered_actions = []
        for action in self.actions:
            if action['status'] not in ['executed', 'cancelled']:
                # Keep all pending actions
                filtered_actions.append(action)
                logger.debug("ActionQueue", f"Keeping pending action: {action['action_id']}")
            else:
                # For executed/cancelled actions, check date
                action_date = action.get('executed_date') or action.get('created_date') or '9999-12-31'
                if action_date >= cutoff_str:
                    # Keep actions newer than cutoff
                    logger.debug("ActionQueue", f"Keeping executed/cancelled action: {action['action_id']}")
                    filtered_actions.append(action)
        
        self.actions = filtered_actions
        
        # Count actions after cleanup
        new_count = len(self.actions)
        removed_count = old_count - new_count
        logger.info("ActionQueue", f"Cleaned up {removed_count} old actions older than {cutoff_str}")
        
        self.save()
        return removed_count
    
    def cleanup_by_status(self, statuses: List[str], days_old: int = 30):
        """Remove actions with specific statuses older than specified days"""
        from datetime import timedelta
        
        cutoff_date = datetime.now().date() - timedelta(days=days_old)
        cutoff_str = cutoff_date.strftime('%Y-%m-%d')
        
        # Count actions before cleanup
        old_count = len(self.actions)
        
        # Remove actions with specified statuses older than cutoff
        filtered_actions = []
        for action in self.actions:
            if action['status'] not in statuses:
                # Keep actions with different statuses
                filtered_actions.append(action)
            else:
                # For actions with target statuses, check date
                action_date = action.get('executed_date') or action.get('created_date') or '9999-12-31'
                if action_date >= cutoff_str:
                    filtered_actions.append(action)
        
        self.actions = filtered_actions
        
        # Count actions after cleanup
        new_count = len(self.actions)
        removed_count = old_count - new_count
        logger.info("ActionQueue", f"Cleaned up {removed_count} actions with statuses {statuses} older than {cutoff_str}")
        self.save()
        return removed_count
    
    def get_cleanup_statistics(self, days_old: int = 30) -> Dict:
        """Get statistics about what would be cleaned up"""
        from datetime import timedelta
        
        cutoff_date = datetime.now().date() - timedelta(days=days_old)
        cutoff_str = cutoff_date.strftime('%Y-%m-%d')
        
        cleanup_candidates = []
        for action in self.actions:
            if action['status'] in ['executed', 'cancelled']:
                action_date = action.get('executed_date') or action.get('created_date')
                # Handle None dates safely
                if action_date is None:
                    action_date = '9999-12-31'  # Very far future, won't be cleaned
                    logger.debug("ActionQueue", f"Action with missing date treated as future: {action['action_id']}")
                if action_date < cutoff_str:
                    cleanup_candidates.append(action)
                    logger.debug("ActionQueue", f"Found cleanup candidate: {action['action_id']}")
        
        stats = {
            'total_candidates': len(cleanup_candidates),
            'executed': len([a for a in cleanup_candidates if a['status'] == 'executed']),
            'cancelled': len([a for a in cleanup_candidates if a['status'] == 'cancelled']),
            'cutoff_date': cutoff_str
        }
        logger.debug("ActionQueue", f"Cleanup statistics: {stats}")
        
        return stats
    
    def get_cancelled_count(self):
        """Get count of cancelled actions"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT COUNT(*) FROM action_queue 
                WHERE status = 'cancelled'
            ''')
            count = cursor.fetchone()[0]
            
            conn.close()
            logger.info("ActionQueue", f"Counted {count} cancelled actions in database")
            return count
            
        except Exception as e:
            print(f"Error getting cancelled count: {e}")
            return 0
    
    def cleanup_all_cancelled(self):
        """Remove all cancelled actions regardless of age"""
        old_count = len(self.actions)
        
        # Keep only actions that are not cancelled
        self.actions = [action for action in self.actions if action['status'] != 'cancelled']
        logger.info("ActionQueue", f"Cleaned up all cancelled actions, removed {old_count - len(self.actions)} actions")
        
        new_count = len(self.actions)
        removed_count = old_count - new_count
        
        self.save()
        return removed_count
    
    def get_cancelled_count(self) -> int:
        """Get count of all cancelled actions"""
        cancelled = len([action for action in self.actions if action['status'] == 'cancelled'])
        
        logger.info("ActionQueue", f"Counted {cancelled} cancelled actions in memory")
        return cancelled
    
    def _generate_action_id(self) -> str:
        """Generate a unique action ID"""
        import random
        import string
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        action_id = f"ACT_{timestamp}_{random_part}"
        logger.debug("ActionQueue", f"Generated action ID: {action_id}")
        return action_id
    
    def save(self):
        """Save actions to file"""
        os.makedirs(os.path.dirname(self.queue_file), exist_ok=True)
        with open(self.queue_file, 'w') as f:
            json.dump(self.actions, f, indent=2)
        logger.info("ActionQueue", f"Saved {len(self.actions)} actions to file: {self.queue_file}")
    def load(self):
        """Load actions from file"""
        if os.path.exists(self.queue_file):
            try:
                with open(self.queue_file, 'r') as f:
                    content = f.read().strip()
                    if content:
                        self.actions = json.loads(content)
                    else:
                        self.actions = []
            except Exception:
                self.actions = []
        else:
            self.actions = []
        logger.info("ActionQueue", f"Loaded {len(self.actions)} actions from file: {self.queue_file}")

# Example usage and testing
if __name__ == "__main__":
    # Test the action queue
    queue = ActionQueue()
    
    # Add a rent change
    action_id = queue.add_rent_change(
        tenant_id="test_tenant_123",
        new_rent=1700.0,
        effective_date="2025-10-01",
        old_rent=1600.0,
        notes="Annual rent increase"
    )
    logger.info("ActionQueue", f"Added rent change action: {action_id}")
    
    # Add a notification
    notification_id = queue.add_notification(
        tenant_id="test_tenant_123",
        notification_date="2025-09-15",
        message="Your lease will be renewed next month",
        notification_type="lease_renewal"
    )
    logger.info("ActionQueue", f"Added notification: {notification_id}")
    
    # Check pending actions
    pending = queue.get_pending_actions("test_tenant_123")
    logger.info("ActionQueue", f"Pending actions for tenant: {len(pending)}")
    for action in pending:
        logger.info("ActionQueue", f"  - {action['description']} on {action['scheduled_date']}")
    
    # Check due actions
    due = queue.get_due_actions()
    logger.info("ActionQueue", f"Due actions: {len(due)}")