"""
Transaction Rules Manager - Auto-categorization system for transactions
"""

import json
import os
import re
import random
import string
from datetime import datetime
try:
    from .app_paths import RULES_FILE
except ImportError:
    from app_paths import RULES_FILE

from assets.Logger import Logger
logger = Logger()

def generate_rule_id(length=12):
    """Generate unique rule identifier"""
    chars = string.ascii_letters + string.digits
    return 'rule_' + ''.join(random.SystemRandom().choice(chars) for _ in range(length))

class TransactionRule:
    """Represents a single transaction categorization rule"""
    
    def __init__(self, pattern, category, match_type='contains', type_=None, 
                 identifier=None, enabled=True, priority=0, notes=''):
        self.identifier = identifier or generate_rule_id()
        self.pattern = pattern
        self.match_type = match_type  # 'contains', 'regex', 'exact'
        self.category = category
        self.type = type_  # Optional: 'in', 'out', or None for any
        self.enabled = enabled
        self.priority = priority  # Lower number = higher priority
        self.notes = notes
        self.created_date = datetime.now().isoformat()
        self.last_used = None
        self.match_count = 0
    
    def matches(self, transaction_desc):
        """
        Check if this rule matches a transaction description.
        
        Args:
            transaction_desc: Transaction description string
            
        Returns:
            bool: True if rule matches, False otherwise
        """
        if not self.enabled:
            return False
        
        # Case-insensitive matching
        desc = transaction_desc.lower()
        pattern = self.pattern.lower()
        
        try:
            if self.match_type == 'exact':
                return desc == pattern
            elif self.match_type == 'contains':
                return pattern in desc
            elif self.match_type == 'regex':
                return bool(re.search(pattern, desc, re.IGNORECASE))
            else:
                # Default to contains
                return pattern in desc
        except re.error:
            # Invalid regex, fall back to contains
            logger.warning("TransactionRule", f"Invalid regex pattern in rule {self.identifier}: {self.pattern}")
            return pattern in desc
    
    def apply(self, transaction):
        """
        Apply this rule to a transaction (modifies transaction in place).
        
        Args:
            transaction: Transaction dict or object
            
        Returns:
            bool: True if rule was applied, False otherwise
        """
        desc = transaction.get('desc', '') if isinstance(transaction, dict) else transaction.desc
        
        if self.matches(desc):
            # Check type filter if specified
            if self.type:
                tx_type = transaction.get('type', '') if isinstance(transaction, dict) else transaction.type
                if tx_type != self.type:
                    return False
            
            # Apply category
            if isinstance(transaction, dict):
                transaction['category'] = self.category
            else:
                transaction.category = self.category
            
            # Update statistics
            self.last_used = datetime.now().isoformat()
            self.match_count += 1
            
            return True
        
        return False
    
    def to_dict(self):
        """Convert rule to dictionary for JSON serialization"""
        return {
            'identifier': self.identifier,
            'pattern': self.pattern,
            'match_type': self.match_type,
            'category': self.category,
            'type': self.type,
            'enabled': self.enabled,
            'priority': self.priority,
            'notes': self.notes,
            'created_date': self.created_date,
            'last_used': self.last_used,
            'match_count': self.match_count
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create rule from dictionary"""
        rule = cls(
            pattern=data['pattern'],
            category=data['category'],
            match_type=data.get('match_type', 'contains'),
            type_=data.get('type'),
            identifier=data.get('identifier'),
            enabled=data.get('enabled', True),
            priority=data.get('priority', 0),
            notes=data.get('notes', '')
        )
        rule.created_date = data.get('created_date', rule.created_date)
        rule.last_used = data.get('last_used')
        rule.match_count = data.get('match_count', 0)
        return rule


class RuleManager:
    """Manages transaction categorization rules"""
    
    def __init__(self, rules_file=None):
        self.rules_file = rules_file or RULES_FILE
        self.rules = []
        logger.debug("RuleManager", f"Initializing RuleManager with file: {self.rules_file}")
        self.load()
        logger.info("RuleManager", f"RuleManager initialized with {len(self.rules)} rules")
    
    def load(self):
        """Load rules from JSON file"""
        logger.debug("RuleManager", f"Loading rules from {self.rules_file}")
        if os.path.exists(self.rules_file):
            try:
                with open(self.rules_file, 'r') as f:
                    data = json.load(f)
                    self.rules = [TransactionRule.from_dict(r) for r in data]
                    # Sort by priority
                    self.rules.sort(key=lambda r: r.priority)
                logger.info("RuleManager", f"Loaded {len(self.rules)} rules")
            except Exception as e:
                logger.error("RuleManager", f"Failed to load rules: {e}")
                self.rules = []
        else:
            logger.debug("RuleManager", f"Rules file not found, creating new")
            self.rules = []
            self.save()  # Create empty file
    
    def save(self):
        """Save rules to JSON file"""
        try:
            logger.debug("RuleManager", f"Saving {len(self.rules)} rules to {self.rules_file}")
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.rules_file), exist_ok=True)
            
            with open(self.rules_file, 'w') as f:
                data = [r.to_dict() for r in self.rules]
                json.dump(data, f, indent=2)
            logger.info("RuleManager", f"Saved {len(self.rules)} rules")
        except Exception as e:
            logger.error("RuleManager", f"Failed to save rules: {e}")
    
    def add_rule(self, pattern, category, match_type='contains', type_=None, 
                 enabled=True, priority=None, notes=''):
        """
        Add a new rule.
        
        Args:
            pattern: Pattern to match in transaction description
            category: Category to assign
            match_type: 'contains', 'regex', or 'exact'
            type_: Optional transaction type filter ('in', 'out')
            enabled: Whether rule is active
            priority: Rule priority (lower = higher priority), auto-assigned if None
            notes: Optional notes about the rule
            
        Returns:
            TransactionRule: The created rule
        """
        logger.debug("RuleManager", f"Adding rule: pattern='{pattern}' category='{category}'")
        # Auto-assign priority if not specified
        if priority is None:
            priority = len(self.rules)
        
        rule = TransactionRule(
            pattern=pattern,
            category=category,
            match_type=match_type,
            type_=type_,
            enabled=enabled,
            priority=priority,
            notes=notes
        )
        
        self.rules.append(rule)
        self.rules.sort(key=lambda r: r.priority)
        self.save()
        logger.info("RuleManager", f"Rule added: {rule.identifier}")
        
        return rule
    
    def remove_rule(self, identifier):
        """Remove a rule by identifier"""
        logger.debug("RuleManager", f"Removing rule: {identifier}")
        self.rules = [r for r in self.rules if r.identifier != identifier]
        self.save()
        logger.info("RuleManager", f"Rule removed: {identifier}")
    
    def update_rule(self, identifier, **kwargs):
        """
        Update a rule's properties.
        
        Args:
            identifier: Rule identifier
            **kwargs: Properties to update (pattern, category, match_type, etc.)
        """
        logger.debug("RuleManager", f"Updating rule {identifier} with {len(kwargs)} changes")
        for rule in self.rules:
            if rule.identifier == identifier:
                for key, value in kwargs.items():
                    if hasattr(rule, key):
                        setattr(rule, key, value)
                self.save()
                logger.info("RuleManager", f"Rule {identifier} updated")
                return rule
        logger.warning("RuleManager", f"Rule {identifier} not found")
        return None
    
    def get_rule(self, identifier):
        """Get a rule by identifier"""
        for rule in self.rules:
            if rule.identifier == identifier:
                return rule
        return None
    
    def list_rules(self, enabled_only=False):
        """
        List all rules.
        
        Args:
            enabled_only: If True, only return enabled rules
            
        Returns:
            list: List of TransactionRule objects
        """
        if enabled_only:
            return [r for r in self.rules if r.enabled]
        return self.rules
    
    def reorder_rules(self, rule_identifiers):
        """
        Reorder rules by providing list of identifiers in desired order.
        
        Args:
            rule_identifiers: List of rule identifiers in new order
        """
        logger.debug("RuleManager", f"Reordering {len(rule_identifiers)} rules")
        # Create mapping of identifier to rule
        rule_map = {r.identifier: r for r in self.rules}
        
        # Rebuild rules list in new order
        new_rules = []
        for i, identifier in enumerate(rule_identifiers):
            if identifier in rule_map:
                rule = rule_map[identifier]
                rule.priority = i
                new_rules.append(rule)
        
        # Add any rules not in the reorder list
        for rule in self.rules:
            if rule.identifier not in rule_identifiers:
                rule.priority = len(new_rules)
                new_rules.append(rule)
        
        self.rules = new_rules
        self.save()
        logger.info("RuleManager", f"Rules reordered successfully")
    
    def apply_rules(self, transaction):
        """
        Apply all enabled rules to a transaction in priority order.
        First matching rule wins.
        
        Args:
            transaction: Transaction dict or object
            
        Returns:
            TransactionRule: The rule that was applied, or None
        """
        for rule in self.rules:
            if rule.enabled and rule.apply(transaction):
                return rule
        return None
    
    def apply_to_all(self, transactions, overwrite=False):
        """
        Apply rules to multiple transactions.
        
        Args:
            transactions: List of transaction dicts or objects
            overwrite: If True, apply even if transaction already has category
            
        Returns:
            dict: Statistics about applied rules
        """
        logger.debug("RuleManager", f"Applying rules to {len(transactions)} transactions")
        stats = {
            'total': len(transactions),
            'categorized': 0,
            'skipped': 0,
            'by_rule': {}
        }
        
        for transaction in transactions:
            # Check if already categorized
            has_category = False
            if isinstance(transaction, dict):
                has_category = bool(transaction.get('category'))
            else:
                has_category = bool(transaction.category)
            
            if has_category and not overwrite:
                stats['skipped'] += 1
                continue
            
            # Apply rules
            applied_rule = self.apply_rules(transaction)
            if applied_rule:
                stats['categorized'] += 1
                rule_id = applied_rule.identifier
                stats['by_rule'][rule_id] = stats['by_rule'].get(rule_id, 0) + 1
        
        # Save updated match counts
        self.save()
        logger.info("RuleManager", f"Applied rules: {stats['categorized']}/{stats['total']} categorized, {stats['skipped']} skipped")
        
        return stats
    
    def test_rule(self, pattern, match_type, test_string):
        """
        Test a rule pattern against a test string.
        
        Args:
            pattern: Rule pattern
            match_type: 'contains', 'regex', or 'exact'
            test_string: String to test against
            
        Returns:
            bool: True if pattern matches
        """
        temp_rule = TransactionRule(
            pattern=pattern,
            category='TEST',
            match_type=match_type
        )
        return temp_rule.matches(test_string)
    
    def get_suggestions(self, transaction_desc):
        """
        Get matching rules for a transaction description without applying them.
        
        Args:
            transaction_desc: Transaction description
            
        Returns:
            list: List of matching TransactionRule objects
        """
        matches = []
        for rule in self.rules:
            if rule.enabled and rule.matches(transaction_desc):
                matches.append(rule)
        return matches
    
    def get_statistics(self):
        """Get statistics about rules usage"""
        return {
            'total_rules': len(self.rules),
            'enabled_rules': len([r for r in self.rules if r.enabled]),
            'disabled_rules': len([r for r in self.rules if not r.enabled]),
            'total_matches': sum(r.match_count for r in self.rules),
            'most_used': sorted(self.rules, key=lambda r: r.match_count, reverse=True)[:5]
        }
    
    def export_rules(self, file_path):
        """Export rules to a file"""
        logger.debug("RuleManager", f"Exporting {len(self.rules)} rules to {file_path}")
        try:
            with open(file_path, 'w') as f:
                data = [r.to_dict() for r in self.rules]
                json.dump(data, f, indent=2)
            logger.info("RuleManager", f"Exported {len(self.rules)} rules")
            return True
        except Exception as e:
            logger.error("RuleManager", f"Failed to export rules: {e}")
            return False
    
    def import_rules(self, file_path, merge=True):
        """
        Import rules from a file.
        
        Args:
            file_path: Path to rules JSON file
            merge: If True, merge with existing rules; if False, replace all
            
        Returns:
            int: Number of rules imported
        """
        logger.debug("RuleManager", f"Importing rules from {file_path} (merge={merge})")
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                imported_rules = [TransactionRule.from_dict(r) for r in data]
                
                if merge:
                    # Add to existing rules
                    existing_ids = {r.identifier for r in self.rules}
                    for rule in imported_rules:
                        if rule.identifier not in existing_ids:
                            self.rules.append(rule)
                else:
                    # Replace all rules
                    self.rules = imported_rules
                
                self.rules.sort(key=lambda r: r.priority)
                self.save()
                logger.info("RuleManager", f"Imported {len(imported_rules)} rules")
                
                return len(imported_rules)
        except Exception as e:
            logger.error("RuleManager", f"Failed to import rules: {e}")
            return 0
