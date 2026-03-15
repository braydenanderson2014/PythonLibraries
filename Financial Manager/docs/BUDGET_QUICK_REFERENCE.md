# Budget System - Quick Reference Card

## 🎯 What is it?
Visual spending tracker that color-codes your transactions based on budget status.

## 🎨 Color System
- 🟢 **Green** = Under budget (Good!)
- 🟠 **Orange** = Approaching limit (Warning!)
- 🔴 **Red** = Over budget (Alert!)

## ⚡ Quick Start

### Create Your First Budget
1. Click **Budgets** tab
2. Click **Add Budget** button
3. Enter:
   - Category: "Groceries"
   - Monthly Limit: $500
4. Click **OK**

### View Budget Status
- Go to **Budgets** tab
- See all your budgets with:
  - How much you've spent
  - How much remains
  - Color-coded status

### See Transaction Colors
- Go to **Transactions** tab
- Rows are colored by budget status
- Green = good, Orange = warning, Red = over

## 💡 Pro Tips

### Match Categories Exactly
```
✓ Budget: "Groceries" → Transaction: "Groceries"
✗ Budget: "Groceries" → Transaction: "groceries"
```

### Set Warning Thresholds
- Default: 80% (warning at $400 of $500)
- Lower = earlier warnings
- Higher = later warnings

### Review Past Months
Use the date picker in Budgets tab to see:
- How you did last month
- Spending trends over time

## 🔧 Common Tasks

### Edit a Budget
1. Budgets tab → Find budget
2. Click **Edit** button
3. Change values
4. Click **OK**

### Delete a Budget
1. Budgets tab → Find budget
2. Click **Delete** button
3. Confirm deletion

### See Different Month
1. Budgets tab
2. Change **View Month** date picker
3. Budget status updates

## ⚠️ Important Notes

✓ Only **expenses** count (not income)  
✓ Categories must **match exactly**  
✓ Budgets are **per month** (reset monthly)  
✓ Works with **all bank accounts**

## 🆘 Troubleshooting

**No colors showing?**
→ Check category spelling matches exactly

**Wrong totals?**
→ Make sure you're viewing correct month

**Budget not saving?**
→ Check category field isn't empty

## 📊 Example

```
Budget: Entertainment = $200/month
Threshold: 80%

$100 spent → Green (50% used)
$170 spent → Orange (85% used)
$220 spent → Red (110% used - over!)
```

## 🎓 Best Practices

1. **Start Conservative**: Set lower limits initially
2. **Review Weekly**: Check budget tab regularly
3. **Adjust as Needed**: Update budgets based on reality
4. **Use Warnings**: Set threshold to get early alerts
5. **Track Trends**: Compare month-over-month

## 📱 Quick Actions

| Want to... | Do this... |
|------------|-----------|
| Add budget | Budgets tab → Add Budget |
| Change limit | Budgets tab → Edit button |
| See colored transactions | Transactions tab |
| View last month | Budgets tab → Change date |
| Stop tracking category | Budgets tab → Delete button |

## 🚀 Advanced

### Custom Warning Points
- 0.60 = Warning at 60% (strict)
- 0.80 = Warning at 80% (normal)
- 0.95 = Warning at 95% (lenient)

### Budget Notes
Add reminders in notes field:
- "Includes weekly date night"
- "Gas for commute only"
- "Save 20% for vacation"

---

**Need More Help?** See `docs/BUDGET_GUIDE.md` for complete documentation.
