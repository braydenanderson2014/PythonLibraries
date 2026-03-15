# Budget System - User Guide

## Overview

The Budget System is a new feature in the Financial Manager that helps you track spending against monthly budgets. Transactions are automatically color-coded based on how they fit within your budget:

- **Green (Good)**: Under budget - you're doing well!
- **Orange (Warning)**: Approaching your limit (default: 80% spent)
- **Red (Over Budget)**: You've exceeded your budget limit

## Features

### 1. Budget Creation
- Set monthly spending limits for different categories
- Customize warning thresholds (when to show orange warning)
- Add notes to remember why you set specific limits

### 2. Visual Feedback
- **Transaction Table**: All transactions are automatically color-coded based on their budget status
- **Budget Tab**: View detailed breakdown of all budgets with current spending
- **Real-time Updates**: Colors update instantly as you add/edit transactions

### 3. Budget Tracking
- Track spending by category for any month
- See percentage of budget used
- View remaining budget amount
- Monthly summary showing total budgeted vs. total spent

## How to Use

### Creating a Budget

1. Go to the **Budgets** tab
2. Click **"Add Budget"**
3. Fill in the form:
   - **Category**: Must match transaction categories (e.g., "Groceries", "Entertainment")
   - **Monthly Limit**: Maximum amount you want to spend per month
   - **Warning Threshold**: Percentage at which to show warning color (default: 0.80 = 80%)
   - **Notes**: Optional notes about this budget
4. Click **OK** to save

### Viewing Budget Status

The Budget tab shows:
- **Category**: The category being budgeted
- **Monthly Limit**: Your spending limit
- **Spent**: How much you've spent this month
- **Remaining**: How much you have left
- **Progress %**: Percentage of budget used
- **Status**: Good/Warning/Over Budget (color-coded)

### Budget Colors Explained

| Color | Status | Meaning | Example |
|-------|--------|---------|---------|
| 🟢 Green | Good | Under warning threshold | $400 spent of $500 limit (80%) |
| 🟠 Orange | Warning | Between threshold and limit | $450 spent of $500 limit (90%) |
| 🔴 Red | Over | Exceeded limit | $550 spent of $500 limit (110%) |

### Transaction Highlighting

The **Transactions** tab automatically highlights rows based on budget status:
- Only **outgoing transactions** (Expense/Loan Payment) are checked against budgets
- **Income transactions** are not highlighted
- Transactions with **no category** or **no budget** are not highlighted
- Colors show the **cumulative budget status** for that category in that month

### Changing Budget View Month

Use the **"View Month"** date picker in the Budget tab to:
- View budget status for past months
- See how you've been doing historically
- Plan for future months

### Editing Budgets

1. In the Budget tab, click **"Edit"** next to any budget
2. Update any fields (category, limit, threshold, notes)
3. Click **OK** to save
4. Transaction colors will update automatically

### Deleting Budgets

1. In the Budget tab, click **"Delete"** next to any budget
2. Confirm the deletion
3. Transaction highlighting for that category will be removed

## Tips for Effective Budgeting

### 1. Match Categories Exactly
- Budget categories must **exactly match** transaction categories
- Use the same spelling and capitalization
- Create budgets after you've established your transaction categories

### 2. Set Realistic Limits
- Review past spending before setting limits
- Start conservative and adjust as needed
- Use the warning threshold to get early alerts

### 3. Regular Reviews
- Check the Budget tab weekly
- Use the month selector to review past months
- Adjust budgets based on actual spending patterns

### 4. Use Budget Colors as Signals
- **Green**: You're on track, keep it up!
- **Orange**: Time to be more careful with spending
- **Red**: Stop spending in this category or adjust your budget

### 5. Customize Warning Thresholds
- Default is 80% (warning when 80% spent)
- Set lower (e.g., 0.60) for stricter alerts
- Set higher (e.g., 0.90) for more lenient tracking

## Budget Calculations

### Monthly Spending Calculation
The system calculates spending as:
- **Sum of all outgoing transactions** (type = 'out' or 'loan_payment')
- **In the selected category**
- **For the selected month**
- Income transactions are NOT counted against budgets

### Status Determination
```
If spent >= limit:
    Status = "Over Budget" (Red)
Else if spent >= (limit × warning_threshold):
    Status = "Warning" (Orange)
Else:
    Status = "Good" (Green)
```

### Example
- **Budget**: $500 for Groceries
- **Warning Threshold**: 0.80 (80%)
- **Warning triggers at**: $400 ($500 × 0.80)

| Spent | Percentage | Status | Color |
|-------|------------|--------|-------|
| $300 | 60% | Good | Green |
| $420 | 84% | Warning | Orange |
| $530 | 106% | Over | Red |

## Data Storage

Budgets are stored in:
```
resources/budgets.json
```

Format:
```json
[
  {
    "category": "Groceries",
    "monthly_limit": 500.00,
    "identifier": "abc123...",
    "user_id": "admin",
    "color_good": "#4CAF50",
    "color_warning": "#FF9800",
    "color_over": "#F44336",
    "warning_threshold": 0.8,
    "notes": "Weekly shopping budget",
    "active": true
  }
]
```

## Troubleshooting

### Budget not showing in Transactions tab?
- Make sure the budget category **exactly matches** the transaction category
- Check that the transaction is an outgoing transaction (not income)
- Verify the transaction has a date and category

### Colors not updating?
- Click **"Refresh Budget Status"** in the Budget tab
- Make sure transactions have been saved properly
- Check that the budget is marked as active

### Wrong month showing?
- Use the **"View Month"** date picker to select the correct month
- Budget calculations are always based on the selected month

### Budget total seems wrong?
- Budget system only counts **outgoing transactions** (Expense/Loan Payment)
- Income transactions are not counted
- Verify transaction dates are in the selected month

## Advanced Features

### Custom Colors (Future Enhancement)
Currently, colors are fixed:
- Green: #4CAF50
- Orange: #FF9800  
- Red: #F44336

Future versions may allow customization.

### Budget Templates (Future Enhancement)
Future versions may include:
- Copy budgets to next month
- Budget templates by season
- Shared household budgets

### Budget Reports (Future Enhancement)
Future versions may include:
- Month-over-month comparison
- Budget variance reports
- Export budget summaries

## Integration with Other Features

### Bank Accounts
- Budgets track spending across all bank accounts
- Filter by specific accounts in future versions

### Recurring Transactions
- Recurring transactions are automatically included in budget calculations
- Set budgets considering your recurring expenses

### Loans
- Loan payments count against budgets if categorized
- Consider loan payments when setting budget limits

## FAQ

**Q: Do I need a budget for every category?**
A: No, only create budgets for categories you want to actively track.

**Q: Can I have multiple budgets for the same category?**
A: No, each category can only have one budget per user.

**Q: Do budgets roll over month-to-month?**
A: No, each month is independent. Budgets reset at the start of each month.

**Q: Can I set weekly or yearly budgets?**
A: Currently only monthly budgets are supported. Future versions may add other time periods.

**Q: Will old transactions be highlighted?**
A: Yes! When you create a budget, all past transactions in that category will be color-coded based on historical budget status.

**Q: Can I export budget data?**
A: Budget data is stored in JSON format and can be backed up by copying budgets.json.

## Support

For issues or feature requests:
1. Check the Transaction and Budget tabs for error messages
2. Review console output for debug information
3. Verify budgets.json is properly formatted
4. Ensure transaction categories match budget categories exactly
