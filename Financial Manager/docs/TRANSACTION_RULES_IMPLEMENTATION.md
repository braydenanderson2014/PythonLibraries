# Transaction Rules & Auto-Categorization - Implementation Guide

## Overview

The Transaction Rules system automatically categorizes transactions based on description patterns. This dramatically reduces manual categorization work by applying predefined rules to match transaction descriptions and assign appropriate categories.

**Key Features:**
- Pattern-based matching (contains, regex, exact match)
- Priority-based rule application (first match wins)
- Auto-categorization on transaction creation
- Bulk application to existing transactions
- Rule testing and statistics
- Type filtering (Income/Expense/Any)

## Architecture

### Components

#### 1. TransactionRule Class (`src/transaction_rules.py`)
Represents a single categorization rule with:
- **Pattern**: Text pattern to match in transaction descriptions
- **Match Type**: How to match the pattern (contains/regex/exact)
- **Category**: Category to assign when matched
- **Type Filter**: Optional filter for Income/Expense transactions
- **Priority**: Order of rule application (lower = higher priority)
- **Enabled**: Whether rule is active
- **Statistics**: Match count and last used timestamp

#### 2. RuleManager Class (`src/transaction_rules.py`)
Manages the collection of rules:
- CRUD operations (add, update, remove)
- Priority ordering and reordering
- Rule application engine
- Bulk operations
- Statistics tracking
- JSON persistence

#### 3. UI Components (`ui/financial_tracker.py`)

**RuleManagerDialog**: Main rules management interface
- Rules table with 7 columns
- Add/Edit/Delete operations
- Priority reordering (move up/down)
- Enable/disable toggles
- Test rule functionality
- Apply to all transactions
- Statistics view

**AddRuleDialog**: Form for creating/editing rules
- Pattern input
- Match type selection
- Category input
- Transaction type filter
- Priority assignment
- Notes field

**TestRuleDialog**: Rule testing tool
- Real-time pattern testing
- Shows all matching rules
- Indicates which rule would be applied

## Data Model

### TransactionRule Structure
```python
{
    "identifier": "rule_1234567890",  # Unique ID
    "pattern": "amazon",               # Pattern to match
    "match_type": "contains",          # contains/regex/exact
    "category": "Shopping",            # Category to assign
    "type": "",                        # "" (any), "in" (income), "out" (expense)
    "enabled": true,                   # Whether rule is active
    "priority": 0,                     # Lower = higher priority
    "notes": "Online shopping",        # Optional description
    "match_count": 15,                 # Usage statistics
    "last_used": "2024-01-15T10:30:00" # Last match timestamp
}
```

### Storage
Rules are stored in `resources/transaction_rules.json`:
```json
[
    {
        "identifier": "rule_1234567890",
        "pattern": "amazon",
        "match_type": "contains",
        "category": "Shopping",
        "type": "",
        "enabled": true,
        "priority": 0,
        "notes": "Online shopping",
        "match_count": 15,
        "last_used": "2024-01-15T10:30:00"
    },
    {
        "identifier": "rule_9876543210",
        "pattern": "starbucks|peet's|coffee",
        "match_type": "regex",
        "category": "Food & Dining",
        "type": "out",
        "enabled": true,
        "priority": 1,
        "notes": "Coffee shops",
        "match_count": 32,
        "last_used": "2024-01-16T08:15:00"
    }
]
```

## Pattern Matching

### Match Types

#### 1. Contains (Substring Match)
Most common and flexible. Case-insensitive substring search.

**Examples:**
```
Pattern: "amazon"
Matches: "Amazon.com", "AMAZON MARKETPLACE", "amazon prime"
```

#### 2. Regex (Regular Expression)
Advanced pattern matching with full regex support.

**Examples:**
```
Pattern: "shell|chevron|76"
Matches: "SHELL #1234", "Chevron Station", "76 Gas"

Pattern: "^walmart.*store"
Matches: "WALMART STORE #1234"
Not: "WALMART.COM" (no 'store' at end)

Pattern: "\d{4}.*starbucks"
Matches: "1234 STARBUCKS", "5678-STARBUCKS"
```

#### 3. Exact Match
Requires exact string match (case-insensitive).

**Examples:**
```
Pattern: "salary"
Matches: "SALARY", "salary"
Not: "Monthly Salary" (extra words)
```

### Type Filtering

Rules can optionally filter by transaction type:
- **Any**: Matches all transactions (default)
- **Income (in)**: Only matches income transactions
- **Expense (out)**: Only matches expense transactions

**Example Use Cases:**
```
Pattern: "paycheck" + Type: Income → "Salary"
Pattern: "paycheck" + Type: Expense → (won't match expenses)
Pattern: "transfer" + Type: Any → "Transfer" (matches both)
```

## Priority System

Rules are applied in priority order (lower number = higher priority):
- **Priority 0**: Applied first
- **Priority 1**: Applied second if priority 0 doesn't match
- **Priority N**: Applied Nth

**First Match Wins**: Once a rule matches, no further rules are evaluated.

### Priority Best Practices

1. **Specific before General**
   ```
   Priority 0: "whole foods" → "Groceries"
   Priority 1: "food" → "Food & Dining"
   ```

2. **Exact before Contains**
   ```
   Priority 0: exact:"target" → "Shopping"
   Priority 1: contains:"target" → "Other"
   ```

3. **Type-Specific before General**
   ```
   Priority 0: "paypal" + Income → "Refund"
   Priority 1: "paypal" + Expense → "Online Purchase"
   Priority 2: "paypal" + Any → "PayPal Transaction"
   ```

## Integration Points

### 1. Initialization
RuleManager is initialized in `FinancialTracker.__init__`:
```python
self.rule_manager = RuleManager()
```

### 2. Auto-Categorization on Transaction Creation
When adding a transaction, rules are automatically applied if category is unset or "Uncategorized":
```python
def add_transaction(self):
    # ... create transaction ...
    
    if transaction and hasattr(self, 'rule_manager'):
        tx_category = transaction.get('category', '')
        if not tx_category or tx_category == 'Uncategorized':
            matched = self.rule_manager.apply_rules(transaction)
            if matched:
                self.bank.save_data()
```

### 3. Manual Access
Users can open the Rule Manager from Settings tab:
```python
def manage_transaction_rules(self):
    dialog = RuleManagerDialog(self, self.rule_manager)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        self.refresh_data()
```

### 4. Bulk Application
Apply rules to all existing transactions:
```python
def apply_to_all(self):
    transactions = parent.bank.list_transactions(user_id=parent.current_user_id)
    stats = self.rule_manager.apply_to_all(transactions, overwrite=False)
    parent.bank.save()
```

## API Reference

### TransactionRule Class

#### Constructor
```python
TransactionRule(pattern, category, match_type='contains', 
                type='', enabled=True, priority=0, notes='')
```

#### Methods
- `matches(transaction_desc)`: Check if rule matches description
- `apply(transaction)`: Apply rule to transaction (returns True if applied)
- `to_dict()`: Convert to dictionary for JSON serialization
- `from_dict(data)`: Create rule from dictionary (class method)

### RuleManager Class

#### Constructor
```python
RuleManager(rules_file='resources/transaction_rules.json')
```

#### CRUD Operations
- `add_rule(rule)`: Add new rule
- `update_rule(identifier, updates)`: Update existing rule
- `remove_rule(identifier)`: Remove rule
- `get_rule(identifier)`: Get rule by ID
- `list_rules()`: Get all rules sorted by priority

#### Rule Application
- `apply_rules(transaction)`: Apply first matching rule to transaction
- `apply_to_all(transactions, overwrite=False)`: Bulk apply to transactions
- `test_rule(pattern, match_type, description)`: Test pattern against description

#### Priority Management
- `reorder_rules(identifier, new_priority)`: Change rule priority
- `move_up(identifier)`: Decrease priority (move up in list)
- `move_down(identifier)`: Increase priority (move down in list)

#### Statistics
- `get_statistics()`: Get usage statistics for all rules
- Rule objects track `match_count` and `last_used` automatically

#### Import/Export
- `export_rules(file_path)`: Export rules to JSON file
- `import_rules(file_path, merge=True)`: Import rules from JSON file

## Common Use Cases

### 1. Vendor Categorization
Automatically categorize transactions from known vendors:

```python
# Groceries
amazon fresh → Groceries
whole foods → Groceries
trader joe → Groceries

# Gas Stations
shell|chevron|76|arco → Gas & Fuel

# Restaurants
(mcdonald|burger king|wendy) → Fast Food
(olive garden|cheesecake|applebee) → Dining Out
```

### 2. Income Recognition
Categorize income sources:

```python
paycheck + Income → Salary
bonus + Income → Bonus
interest earned + Income → Interest Income
refund + Income → Refund
```

### 3. Bill Payments
Identify recurring bills:

```python
^pg&e|pge → Utilities
^comcast|xfinity → Internet
netflix|hulu|disney → Subscriptions
```

### 4. Transfer Detection
Identify internal transfers:

```python
^transfer from|^transfer to → Transfer
online banking transfer → Transfer
mobile deposit → Deposit
```

## Testing Workflow

### 1. Create Test Rules
```python
# Open Rule Manager from Settings tab
# Click "Add Rule"
# Enter pattern: "test"
# Select match type: "contains"
# Enter category: "Testing"
# Save
```

### 2. Test Pattern
```python
# Click "Test Rule" in Rule Manager
# Enter sample description: "This is a test transaction"
# Verify "test" rule is highlighted
```

### 3. Add Test Transaction
```python
# Add transaction with description containing "test"
# Verify category is automatically set to "Testing"
```

### 4. Apply to Existing
```python
# Add several uncategorized transactions
# Click "Apply to All Transactions"
# Verify transactions are categorized
```

## Performance Considerations

### Rule Count
- **Optimal**: 20-50 rules for typical use
- **Maximum**: 500+ rules supported but may slow UI
- **Recommendation**: Consolidate similar patterns using regex

### Pattern Complexity
- **Contains**: Very fast (O(n) substring search)
- **Regex**: Moderate (depends on pattern complexity)
- **Exact**: Very fast (O(n) string comparison)

### Optimization Tips
1. Put most commonly matched rules at top (lower priority number)
2. Use contains instead of regex when possible
3. Combine multiple patterns with regex alternation: `shop1|shop2|shop3`
4. Disable unused rules instead of deleting

## Error Handling

### Invalid Regex Patterns
If a regex pattern is invalid, the rule automatically falls back to contains matching:
```python
try:
    return bool(re.search(pattern, desc, re.IGNORECASE))
except re.error:
    print(f"[WARNING] Invalid regex in rule {self.identifier}")
    return pattern in desc  # Fallback to contains
```

### Missing Category
Rules without categories are prevented at UI level. Empty category validation in AddRuleDialog.

### File Access Issues
If `transaction_rules.json` doesn't exist, it's created automatically. Read/write errors are logged.

## Migration & Backwards Compatibility

### Existing Transactions
Rules don't automatically recategorize existing transactions. Use "Apply to All" button to bulk update.

### Manual Categories
Auto-categorization respects manually set categories:
- Empty or "Uncategorized" → Rules applied
- Any other category → Rules skipped

### Schema Updates
Rules file format is versioned. Future updates will include migration logic.

## Security Considerations

### Pattern Injection
Regex patterns are validated at runtime. Invalid patterns fall back to safe contains matching.

### File Permissions
`transaction_rules.json` should be readable/writable only by the application user.

### Data Privacy
Rules may contain sensitive information (vendor names). Keep rules file secure.

## Future Enhancements

### Planned Features
1. **Smart Suggestions**: Analyze existing transactions to suggest rules
2. **Import/Export UI**: Built-in UI for rule sharing
3. **Rule Templates**: Pre-built rule sets for common scenarios
4. **Machine Learning**: Learn categorization from user corrections
5. **Multi-Pattern Rules**: Multiple patterns per rule (OR logic)
6. **Amount-Based Rules**: Match transactions by amount range
7. **Date-Based Rules**: Seasonal or time-specific categorization
8. **Conflict Resolution**: Warn when multiple rules could match

### Community Contributions
Consider creating a shared rule repository where users can contribute and download rule sets.

## Troubleshooting

### Rules Not Applied
1. Check rule is enabled (checkbox in table)
2. Verify pattern matches description (use Test Rule)
3. Check transaction type matches rule type filter
4. Ensure rule priority is appropriate
5. Verify category exists in system

### Unexpected Categorization
1. Check rule priority order
2. Use Test Rule to see all matching rules
3. Review regex patterns for unintended matches
4. Consider adding type filter to narrow matches

### Performance Issues
1. Disable unused rules
2. Consolidate similar patterns with regex
3. Move most-used rules to top priority
4. Consider using contains instead of complex regex

### File Corruption
If `transaction_rules.json` is corrupted:
1. Backup the file
2. Delete or rename it
3. Restart application (new file created)
4. Manually re-create rules

## Related Documentation
- [Transaction System](TRANSACTIONS.md)
- [Split Transactions](SPLIT_TRANSACTIONS.md)
- [Transaction Attachments](ATTACHMENTS_IMPLEMENTATION.md)
- [Bank Account Management](BANK_ACCOUNTS.md)

## Support & Feedback
For issues, suggestions, or questions about Transaction Rules, please contact the development team or file an issue in the project repository.
