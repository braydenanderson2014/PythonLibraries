"""
Goal Management System for Financial Tracker
Handles savings goals with progress tracking, projections, and contributions
"""

import json
import os
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import uuid

from assets.Logger import Logger
logger = Logger()


class Goal:
    """Represents a financial savings goal"""
    
    def __init__(self, name, target_amount, target_date=None, current_amount=0.0,
                 monthly_contribution=0.0, linked_account_id=None, priority='medium',
                 icon='💰', notes='', user_id=None, goal_id=None, created_date=None):
        """
        Initialize a savings goal.
        
        Args:
            name: Goal name (e.g., "Emergency Fund")
            target_amount: Target amount to save
            target_date: Target completion date (YYYY-MM-DD)
            current_amount: Current saved amount
            monthly_contribution: Optional monthly contribution amount
            linked_account_id: Optional linked bank account
            priority: Priority level (low/medium/high/critical)
            icon: Emoji icon for display
            notes: Optional notes about the goal
            user_id: User ID who owns this goal
            goal_id: Unique goal identifier (auto-generated if None)
            created_date: Creation date (auto-set if None)
        """
        logger.debug("Goal", f"Creating goal: {name}, target={target_amount}, priority={priority}")
        self.goal_id = goal_id or f"goal_{uuid.uuid4().hex[:8]}"
        self.name = name
        self.target_amount = float(target_amount)
        self.current_amount = float(current_amount)
        self.target_date = target_date
        self.monthly_contribution = float(monthly_contribution)
        self.linked_account_id = linked_account_id
        self.priority = priority
        self.icon = icon
        self.notes = notes
        self.user_id = user_id
        self.created_date = created_date or date.today().isoformat()
        self.contributions = []  # List of contribution transactions
        self.completed = False
        self.completed_date = None
        logger.info("Goal", f"Goal created: {self.goal_id} - {name}")
    
    def get_progress_percentage(self):
        """Calculate progress as percentage (0-100)"""
        if self.target_amount <= 0:
            logger.debug("Goal", f"Invalid target amount for {self.goal_id}")
            return 100.0
        percentage = (self.current_amount / self.target_amount) * 100
        logger.debug("Goal", f"Progress for {self.goal_id}: {percentage:.1f}%")
        return min(100.0, max(0.0, percentage))
    
    def get_remaining_amount(self):
        """Calculate remaining amount to reach goal"""
        return max(0.0, self.target_amount - self.current_amount)
    
    def get_days_until_target(self):
        """Calculate days until target date"""
        if not self.target_date:
            return None
        
        try:
            target = datetime.strptime(self.target_date, '%Y-%m-%d').date()
            today = date.today()
            delta = (target - today).days
            return delta
        except:
            return None
    
    def get_months_until_target(self):
        """Calculate months until target date"""
        days = self.get_days_until_target()
        if days is None:
            return None
        return round(days / 30.0, 1)
    
    def get_projected_completion_date(self):
        """
        Calculate projected completion date based on monthly contribution.
        Returns date string or None if contribution is zero or goal is already met.
        """
        if self.monthly_contribution <= 0:
            return None
        
        remaining = self.get_remaining_amount()
        if remaining <= 0:
            return date.today().isoformat()
        
        months_needed = remaining / self.monthly_contribution
        today = date.today()
        projected_date = today + relativedelta(months=int(months_needed))
        
        # Add extra days for partial month
        days_extra = int((months_needed % 1) * 30)
        projected_date = projected_date + relativedelta(days=days_extra)
        
        return projected_date.isoformat()
    
    def get_required_monthly_contribution(self):
        """
        Calculate required monthly contribution to reach goal by target date.
        Returns None if no target date is set.
        """
        if not self.target_date:
            return None
        
        months = self.get_months_until_target()
        if months is None or months <= 0:
            return None
        
        remaining = self.get_remaining_amount()
        required = remaining / months
        return round(required, 2)
    
    def is_on_track(self):
        """
        Determine if goal is on track based on current progress vs target date.
        Returns: 'ahead', 'on-track', 'behind', or None if no target date
        """
        if not self.target_date or self.monthly_contribution <= 0:
            return None
        
        projected_date_str = self.get_projected_completion_date()
        if not projected_date_str:
            return None
        
        try:
            projected = datetime.strptime(projected_date_str, '%Y-%m-%d').date()
            target = datetime.strptime(self.target_date, '%Y-%m-%d').date()
            
            days_diff = (projected - target).days
            
            if days_diff < -30:
                return 'ahead'
            elif days_diff <= 30:
                return 'on-track'
            else:
                return 'behind'
        except:
            return None
    
    def add_contribution(self, amount, transaction_id=None, contribution_date=None):
        """
        Add a contribution to this goal.
        
        Args:
            amount: Contribution amount
            transaction_id: Optional linked transaction ID
            contribution_date: Date of contribution (defaults to today)
        """
        logger.debug("Goal", f"Adding contribution of {amount} to goal {self.goal_id}")
        contribution = {
            'amount': float(amount),
            'date': contribution_date or date.today().isoformat(),
            'transaction_id': transaction_id
        }
        self.contributions.append(contribution)
        self.current_amount += float(amount)
        logger.info("Goal", f"Contribution added to {self.goal_id}: {amount}, new total: {self.current_amount}")
        
        # Check if goal is completed
        if self.current_amount >= self.target_amount and not self.completed:
            self.completed = True
            self.completed_date = date.today().isoformat()
            logger.info("Goal", f"Goal {self.goal_id} marked as completed!")
    
    def remove_contribution(self, contribution_index):
        """Remove a contribution by index"""
        logger.debug("Goal", f"Removing contribution at index {contribution_index} from goal {self.goal_id}")
        if 0 <= contribution_index < len(self.contributions):
            contribution = self.contributions.pop(contribution_index)
            self.current_amount -= contribution['amount']
            logger.info("Goal", f"Contribution removed from {self.goal_id}: {contribution['amount']}, new total: {self.current_amount}")
            
            # Unmark as completed if we go below target
            if self.current_amount < self.target_amount:
                self.completed = False
                self.completed_date = None
                logger.info("Goal", f"Goal {self.goal_id} marked as incomplete")
    
    def get_total_contributions(self):
        """Get total amount contributed"""
        return sum(c['amount'] for c in self.contributions)
    
    def get_contribution_count(self):
        """Get number of contributions"""
        return len(self.contributions)
    
    def get_average_contribution(self):
        """Calculate average contribution amount"""
        count = self.get_contribution_count()
        if count == 0:
            return 0.0
        return self.get_total_contributions() / count
    
    def to_dict(self):
        """Convert goal to dictionary for JSON serialization"""
        return {
            'goal_id': self.goal_id,
            'name': self.name,
            'target_amount': self.target_amount,
            'current_amount': self.current_amount,
            'target_date': self.target_date,
            'monthly_contribution': self.monthly_contribution,
            'linked_account_id': self.linked_account_id,
            'priority': self.priority,
            'icon': self.icon,
            'notes': self.notes,
            'user_id': self.user_id,
            'created_date': self.created_date,
            'contributions': self.contributions,
            'completed': self.completed,
            'completed_date': self.completed_date
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create goal from dictionary"""
        goal = cls(
            name=data['name'],
            target_amount=data['target_amount'],
            target_date=data.get('target_date'),
            current_amount=data.get('current_amount', 0.0),
            monthly_contribution=data.get('monthly_contribution', 0.0),
            linked_account_id=data.get('linked_account_id'),
            priority=data.get('priority', 'medium'),
            icon=data.get('icon', '💰'),
            notes=data.get('notes', ''),
            user_id=data.get('user_id'),
            goal_id=data.get('goal_id'),
            created_date=data.get('created_date')
        )
        goal.contributions = data.get('contributions', [])
        goal.completed = data.get('completed', False)
        goal.completed_date = data.get('completed_date')
        return goal


class GoalManager:
    """Manages collection of financial goals"""
    
    def __init__(self, goals_file='resources/goals.json'):
        """
        Initialize Goal Manager.
        
        Args:
            goals_file: Path to goals JSON file
        """
        logger.debug("GoalManager", f"Initializing GoalManager with file: {goals_file}")
        self.goals_file = goals_file
        self.goals = []
        self.load()
    
    def load(self):
        """Load goals from JSON file"""
        logger.debug("GoalManager", f"Loading goals from {self.goals_file}")
        if os.path.exists(self.goals_file):
            try:
                with open(self.goals_file, 'r') as f:
                    data = json.load(f)
                    self.goals = [Goal.from_dict(g) for g in data]
                logger.info("GoalManager", f"Loaded {len(self.goals)} goals from file")
            except Exception as e:
                logger.error("GoalManager", f"Failed to load goals: {str(e)}")
                self.goals = []
        else:
            # Create empty file
            logger.debug("GoalManager", f"Goals file not found, creating new file: {self.goals_file}")
            self.goals = []
            self.save()
    
    def save(self):
        """Save goals to JSON file"""
        logger.debug("GoalManager", f"Saving {len(self.goals)} goals to {self.goals_file}")
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.goals_file), exist_ok=True)
            
            with open(self.goals_file, 'w') as f:
                data = [g.to_dict() for g in self.goals]
                json.dump(data, f, indent=2)
            logger.info("GoalManager", f"Saved {len(self.goals)} goals successfully")
        except Exception as e:
            logger.error("GoalManager", f"Failed to save goals: {str(e)}")
    
    def add_goal(self, name, target_amount, target_date=None, monthly_contribution=0.0,
                 linked_account_id=None, priority='medium', icon='💰', notes='', user_id=None):
        """
        Add a new goal.
        
        Returns:
            Goal: The created goal
        """
        logger.debug("GoalManager", f"Adding new goal: {name}, target={target_amount}, priority={priority}")
        goal = Goal(
            name=name,
            target_amount=target_amount,
            target_date=target_date,
            monthly_contribution=monthly_contribution,
            linked_account_id=linked_account_id,
            priority=priority,
            icon=icon,
            notes=notes,
            user_id=user_id
        )
        self.goals.append(goal)
        self.save()
        logger.info("GoalManager", f"Goal added: {goal.goal_id} - {name}")
        return goal
    
    def update_goal(self, goal_id, **kwargs):
        """
        Update goal properties.
        
        Args:
            goal_id: Goal identifier
            **kwargs: Properties to update
        """
        logger.debug("GoalManager", f"Updating goal {goal_id} with {len(kwargs)} fields")
        goal = self.get_goal(goal_id)
        if not goal:
            logger.warning("GoalManager", f"Goal not found: {goal_id}")
            return False
        
        # Update allowed properties
        allowed_fields = ['name', 'target_amount', 'current_amount', 'target_date',
                         'monthly_contribution', 'linked_account_id', 'priority',
                         'icon', 'notes', 'completed']
        
        updated_fields = []
        for key, value in kwargs.items():
            if key in allowed_fields:
                setattr(goal, key, value)
                updated_fields.append(key)
        
        self.save()
        logger.info("GoalManager", f"Goal {goal_id} updated: {', '.join(updated_fields)}")
        return True
    
    def remove_goal(self, goal_id):
        """Remove a goal"""
        logger.debug("GoalManager", f"Removing goal: {goal_id}")
        initial_count = len(self.goals)
        self.goals = [g for g in self.goals if g.goal_id != goal_id]
        self.save()
        if len(self.goals) < initial_count:
            logger.info("GoalManager", f"Goal removed: {goal_id}")
        else:
            logger.warning("GoalManager", f"Goal not found for removal: {goal_id}")
    
    def get_goal(self, goal_id):
        """Get goal by ID"""
        logger.debug("GoalManager", f"Looking up goal: {goal_id}")
        for goal in self.goals:
            if goal.goal_id == goal_id:
                logger.debug("GoalManager", f"Goal found: {goal.name}")
                return goal
        logger.warning("GoalManager", f"Goal not found: {goal_id}")
        return None
    
    def list_goals(self, user_id=None, priority=None, completed=None):
        """
        List goals with optional filtering.
        
        Args:
            user_id: Filter by user ID
            priority: Filter by priority level
            completed: Filter by completion status (True/False)
        
        Returns:
            List of goals sorted by priority
        """
        logger.debug("GoalManager", f"Listing goals with filters - user_id={user_id}, priority={priority}, completed={completed}")
        filtered = self.goals
        
        if user_id is not None:
            filtered = [g for g in filtered if g.user_id == user_id]
        
        if priority is not None:
            filtered = [g for g in filtered if g.priority == priority]
        
        if completed is not None:
            filtered = [g for g in filtered if g.completed == completed]
        
        # Sort by priority (critical > high > medium > low) and then by name
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        filtered.sort(key=lambda g: (priority_order.get(g.priority, 4), g.name))
        
        logger.info("GoalManager", f"Listed {len(filtered)} goals")
        return filtered
    
    def add_contribution_to_goal(self, goal_id, amount, transaction_id=None):
        """
        Add a contribution to a goal.
        
        Args:
            goal_id: Goal identifier
            amount: Contribution amount
            transaction_id: Optional linked transaction
        
        Returns:
            bool: True if successful, False otherwise
        """
        logger.debug("GoalManager", f"Adding contribution of {amount} to goal {goal_id}")
        goal = self.get_goal(goal_id)
        if not goal:
            logger.error("GoalManager", f"Failed to add contribution - goal not found: {goal_id}")
            return False
        
        goal.add_contribution(amount, transaction_id)
        self.save()
        logger.info("GoalManager", f"Contribution added to goal {goal_id}: {amount}")
        return True
    
    def get_statistics(self, user_id=None):
        """
        Get goal statistics.
        
        Returns:
            dict: Statistics about goals
        """
        logger.debug("GoalManager", f"Computing statistics for user_id={user_id}")
        goals = self.list_goals(user_id=user_id)
        
        total_target = sum(g.target_amount for g in goals if not g.completed)
        total_saved = sum(g.current_amount for g in goals if not g.completed)
        total_remaining = sum(g.get_remaining_amount() for g in goals if not g.completed)
        
        completed_goals = [g for g in goals if g.completed]
        active_goals = [g for g in goals if not g.completed]
        
        on_track = len([g for g in active_goals if g.is_on_track() in ['ahead', 'on-track']])
        behind = len([g for g in active_goals if g.is_on_track() == 'behind'])
        
        stats = {
            'total_goals': len(goals),
            'active_goals': len(active_goals),
            'completed_goals': len(completed_goals),
            'total_target_amount': total_target,
            'total_saved_amount': total_saved,
            'total_remaining_amount': total_remaining,
            'overall_progress_percentage': (total_saved / total_target * 100) if total_target > 0 else 0,
            'goals_on_track': on_track,
            'goals_behind': behind,
            'total_contributions': sum(g.get_contribution_count() for g in goals)
        }
        logger.info("GoalManager", f"Statistics: {len(goals)} goals, {stats['active_goals']} active, {stats['completed_goals']} completed, {stats['goals_on_track']} on-track")
        return stats
    
    def export_goals(self, file_path):
        """Export goals to a file"""
        logger.debug("GoalManager", f"Exporting {len(self.goals)} goals to {file_path}")
        try:
            with open(file_path, 'w') as f:
                data = [g.to_dict() for g in self.goals]
                json.dump(data, f, indent=2)
            logger.info("GoalManager", f"Exported {len(self.goals)} goals successfully")
            return True
        except Exception as e:
            logger.error("GoalManager", f"Failed to export goals: {str(e)}")
            return False
    
    def import_goals(self, file_path, merge=True):
        """
        Import goals from a file.
        
        Args:
            file_path: Path to import file
            merge: If True, merge with existing goals. If False, replace all.
        
        Returns:
            int: Number of goals imported
        """
        logger.debug("GoalManager", f"Importing goals from {file_path}, merge={merge}")
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                imported_goals = [Goal.from_dict(g) for g in data]
            
            if not merge:
                logger.debug("GoalManager", f"Replacing {len(self.goals)} goals with {len(imported_goals)} imported goals")
                self.goals = imported_goals
            else:
                # Merge, avoiding duplicates by goal_id
                existing_ids = {g.goal_id for g in self.goals}
                new_goals = 0
                for goal in imported_goals:
                    if goal.goal_id not in existing_ids:
                        self.goals.append(goal)
                        new_goals += 1
                logger.debug("GoalManager", f"Merged goals: {new_goals} new goals added, {len(imported_goals) - new_goals} duplicates skipped")
            
            self.save()
            logger.info("GoalManager", f"Imported {len(imported_goals)} goals successfully")
            return len(imported_goals)
        except Exception as e:
            logger.error("GoalManager", f"Failed to import goals: {str(e)}")
            return 0
