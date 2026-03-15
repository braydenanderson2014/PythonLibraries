# Transaction Rules - Quick Reference Guide

## What Are Transaction Rules?

Transaction Rules automatically categorize your transactions based on patterns in their descriptions. Instead of manually categorizing every transaction, create rules once and let the system do the work!

**Example:** Create a rule that says "if description contains 'amazon', categorize as 'Shopping'" - now all Amazon purchases are automatically categorized!

## Getting Started

### Step 1: Open Rule Manager
1. Go to the **Settings** tab
2. Click **"Manage Transaction Rules"** button
3. The Rule Manager window opens

### Step 2: Create Your First Rule
1. Click **"➕ Add Rule"**
2. Fill in the form:
   - **Pattern**: `amazon` (what to look for)
   - **Match Type**: `Contains` (how to match)
   - **Category**: `Shopping` (what to assign)
   - **Type**: `Any` (income or expense)
   - **Notes**: `Online shopping` (optional)
3. Click **Save**

### Step 3: Test It
1. Add a transaction with "Amazon.com" in description
2. Watch it automatically categorize as "Shopping"! ✨

## Creating Effective Rules

### Pattern Types

#### 📝 Contains (Recommended for Beginners)
Matches if pattern appears anywhere in description (case-insensitive).

**Examples:**
```
Pattern: "starbucks"
✅ Matches: "STARBUCKS #1234", "Starbucks Coffee", "starbucks app"
❌ Doesn't match: "coffee shop"

Pattern: "grocery"
✅ Matches: "GROCERY OUTLET", "Local Grocery Store"
```

#### 🎯 Exact Match
Requires exact description (case-insensitive).

**Examples:**
```
Pattern: "paycheck"
✅ Matches: "PAYCHECK", "paycheck"
❌ Doesn't match: "Weekly Paycheck" (extra words)
```

#### 🔍 Regex (Advanced)
Powerful pattern matching for complex cases.

**Examples:**
```
Pattern: "shell|chevron|76"
Matches: All three gas stations

Pattern: "mcdonald|burger king|wendy"
Matches: All three fast food chains
```

### Transaction Types

Filter rules by transaction type:
- **Any**: Matches income AND expenses (default)
- **Income**: Only matches income transactions
- **Expense**: Only matches expense transactions

**Use Cases:**
```
Pattern: "paycheck" + Type: Income → "Salary"
Pattern: "refund" + Type: Income → "Refund"
Pattern: "purchase" + Type: Expense → "Shopping"
```

## Common Rule Examples

### 🛒 Shopping
```
amazon → Shopping
walmart → Shopping
target → Shopping
ebay|etsy → Online Shopping
```

### 🍕 Food & Dining
```
starbucks|peet's|coffee → Coffee
mcdonald|burger|wendy|taco bell → Fast Food
olive garden|cheesecake|outback → Dining Out
safeway|kroger|publix → Groceries
```

### ⛽ Transportation
```
shell|chevron|76|arco|bp → Gas & Fuel
uber|lyft → Rideshare
parking|meter → Parking
```

### 💰 Income
```
paycheck (Income only) → Salary
bonus (Income only) → Bonus
interest (Income only) → Interest Income
dividend (Income only) → Dividends
```

### 🏠 Bills & Utilities
```
pg&e|pge|electric → Utilities
comcast|xfinity|internet → Internet
netflix|hulu|disney|spotify → Subscriptions
rent|mortgage → Housing
```

### 💳 Transfers
```
transfer from|transfer to → Transfer
online banking transfer → Transfer
mobile deposit → Deposit
```

## Rule Priority

Rules are applied in order (Priority 1, 2, 3...). **First match wins!**

### Why Priority Matters

Without proper priority, a general rule might override a specific one:

❌ **Wrong Order:**
```
Priority 1: "food" → "Food & Dining"
Priority 2: "whole foods" → "Groceries"
Result: "Whole Foods Market" matches "food" first → "Food & Dining" ❌
```

✅ **Correct Order:**
```
Priority 1: "whole foods" → "Groceries"
Priority 2: "food" → "Food & Dining"
Result: "Whole Foods Market" matches "whole foods" first → "Groceries" ✅
```

### Priority Best Practices

1. **Specific patterns before general patterns**
   ```
   Priority 1: "shell gas" → "Gas & Fuel"
   Priority 2: "shell" → "Shopping" (Shell gift cards)
   ```

2. **Type-specific before type-general**
   ```
   Priority 1: "paypal" + Income → "Refund"
   Priority 2: "paypal" + Expense → "Purchase"
   Priority 3: "paypal" + Any → "PayPal"
   ```

3. **Exact before contains**
   ```
   Priority 1: Exact "target" → "Target Store"
   Priority 2: Contains "target" → "Other Target"
   ```

## Managing Rules

### Reordering Rules
- Click **⬆️ Move Up** to increase priority (move higher in list)
- Click **⬇️ Move Down** to decrease priority (move lower in list)

### Editing Rules
1. Select rule in table
2. Click **✏️ Edit**
3. Make changes
4. Click **Save**

### Disabling vs Deleting
- **Disable**: Keeps rule but stops using it (toggle checkbox)
- **Delete**: Permanently removes rule
- **Tip**: Disable seasonal rules instead of deleting!

### Testing Rules
1. Click **🧪 Test Rule**
2. Enter a sample transaction description
3. See which rules match and which would be applied
4. Perfect for verifying regex patterns!

## Applying Rules

### New Transactions
Rules automatically apply when you add transactions with no category or "Uncategorized".

### Existing Transactions
1. Click **📋 Apply to All Transactions**
2. Confirm the action
3. Rules apply to all uncategorized transactions
4. See summary: "Categorized 25 transactions, Skipped 10"

**Note:** Manual categories are preserved - only empty/uncategorized transactions are updated.

## Advanced Tips

### Combining Multiple Patterns (Regex)
Instead of multiple rules, combine with `|` (OR):

❌ **Multiple Rules:**
```
Rule 1: "mcdonald" → "Fast Food"
Rule 2: "burger king" → "Fast Food"
Rule 3: "wendy" → "Fast Food"
```

✅ **One Combined Rule:**
```
Pattern: "mcdonald|burger king|wendy"
Match Type: Regex
Category: "Fast Food"
```

### Case Sensitivity
All matching is case-insensitive - "AMAZON", "Amazon", and "amazon" all match!

### Partial Words
Contains matching finds patterns anywhere:
- Pattern `mart` matches: "WalMART", "KrogerSMART", "Apartment"
- Be specific to avoid false matches!

### Special Characters in Regex
Need to match special characters? Escape them with `\`:
```
Pattern: "\$99\.99"  → Matches "$99.99"
Pattern: "card#\d{4}" → Matches "card#1234"
```

## Rule Statistics

View rule effectiveness:
1. Click **📊 Statistics**
2. See for each rule:
   - Times used
   - Last used date
   - Most/least effective rules

**Tip:** Disable rules with 0 matches to keep list clean!

## Troubleshooting

### "My rule isn't matching!"

**Check List:**
1. ✅ Rule is **enabled** (checkbox checked)
2. ✅ Pattern **exactly matches** part of description
3. ✅ Transaction **type** matches rule filter (Income/Expense/Any)
4. ✅ No higher-priority rule matches first
5. ✅ Category exists in system

**Solution:** Use **Test Rule** to verify pattern!

### "Wrong category is applied!"

**Likely Causes:**
1. Higher-priority rule matches first
2. Too general pattern matches unintended transactions

**Solutions:**
- Check priority order (specific before general)
- Make pattern more specific
- Add transaction type filter
- Use **Test Rule** to see all matching rules

### "Rules applied to wrong transactions!"

**Solution:** Use **Apply to All** carefully:
- It only updates empty/uncategorized transactions
- Manual categories are preserved
- Review rules before bulk apply

## Real-World Examples

### Example 1: New User Setup (5 minutes)

**Goal:** Categorize most common transactions

```
Priority 1: "paycheck" + Income → "Salary"
Priority 2: "amazon" → "Shopping"
Priority 3: "safeway|kroger|grocery" → "Groceries"
Priority 4: "shell|chevron|gas" → "Gas & Fuel"
Priority 5: "netflix|hulu|spotify" → "Subscriptions"
Priority 6: "starbucks|coffee" → "Coffee"
Priority 7: "restaurant|dining" → "Dining Out"
```

**Result:** 80% of transactions auto-categorized!

### Example 2: Advanced User (20 rules)

**Goal:** Complete automation

```
# Income (Priorities 1-3)
Priority 1: Exact "salary deposit" + Income → "Salary"
Priority 2: "bonus" + Income → "Bonus"
Priority 3: "interest|dividend" + Income → "Investment Income"

# Shopping (Priorities 4-7)
Priority 4: "amazon prime" → "Subscriptions"
Priority 5: "amazon" → "Shopping"
Priority 6: "walmart|target|costco" → "Shopping"
Priority 7: "etsy|ebay" → "Online Shopping"

# Food (Priorities 8-12)
Priority 8: "whole foods|trader joe|sprouts" → "Groceries"
Priority 9: "safeway|kroger|albertsons" → "Groceries"
Priority 10: "starbucks|peet's|philz" → "Coffee"
Priority 11: "mcdonald|burger|taco bell|wendy" → "Fast Food"
Priority 12: "restaurant|cafe|bistro|diner" → "Dining Out"

# Transportation (Priorities 13-15)
Priority 13: "shell|chevron|76|arco|texaco" → "Gas & Fuel"
Priority 14: "uber|lyft|taxi" → "Rideshare"
Priority 15: "parking|meter" → "Parking"

# Bills (Priorities 16-20)
Priority 16: "pg&e|pge|sdge|electric" → "Utilities"
Priority 17: "comcast|xfinity|att|verizon" → "Internet/Phone"
Priority 18: "netflix|hulu|disney|hbo|paramount" → "Streaming"
Priority 19: "spotify|apple music|pandora" → "Music"
Priority 20: "rent|mortgage|lease" → "Housing"
```

**Result:** 95%+ auto-categorization!

## Best Practices

### Do's ✅
- Start with common vendors (Amazon, Walmart, gas stations)
- Use Contains for most rules (simplest)
- Test patterns before saving
- Put specific patterns before general ones
- Review statistics monthly
- Disable instead of delete seasonal rules
- Use Apply to All after creating multiple rules

### Don'ts ❌
- Don't create too many similar rules (combine with regex)
- Don't use very generic patterns ("the", "store")
- Don't forget to set priority for new rules
- Don't delete rules you might need later (disable instead)
- Don't apply rules to already-categorized transactions
- Don't forget to enable rules after creating!

## Keyboard Shortcuts

While Rule Manager is open:
- **Ctrl+N**: Add new rule
- **Delete**: Delete selected rule
- **Ctrl+Up**: Move selected rule up
- **Ctrl+Down**: Move selected rule down
- **Space**: Toggle selected rule enabled/disabled

## Getting Help

### Test Rule Feature
**Most Useful Tool!** Enter a transaction description and instantly see:
- Which rules match
- Which rule would be applied (highest priority)
- Why other rules didn't match

### Statistics View
Understand which rules are working:
- High match count = useful rule
- Zero matches = consider disabling or adjusting pattern
- Recent last_used = actively matching

### Pattern Resources
Learn regex patterns:
- [Regex101.com](https://regex101.com) - Pattern tester
- [RegexOne Tutorial](https://regexone.com) - Learn regex basics

## Next Steps

1. **Create your first 5-10 rules** for most common transactions
2. **Add a few transactions** and verify auto-categorization
3. **Use Apply to All** on existing uncategorized transactions
4. **Review and refine** rules based on results
5. **Add more rules** as you discover patterns
6. **Check statistics** monthly to optimize

---

**Remember:** Rules save you time! Spend 10 minutes setting them up, save hours of manual categorization. Start simple, expand as needed! 🚀
