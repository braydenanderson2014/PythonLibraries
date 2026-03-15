# Rental Summaries - Quick Reference

## Quick Start

```python
from rental_summaries import RentalSummaries
from rent_tracker import RentTracker
from tenant import TenantManager

# Setup
tenant_manager = TenantManager()
rent_tracker = RentTracker(tenant_manager=tenant_manager)
summaries = RentalSummaries(rent_tracker=rent_tracker)
```

## Print Summaries

### Monthly Summary
```python
summaries.print_monthly_summary(tenant_id, year=2025, month=1)
```

### Yearly Summary
```python
summaries.print_yearly_summary(tenant_id, year=2025)
```

### Rental Period Summary
```python
summaries.print_rental_period_summary(tenant_id)
```

## Get Summary Data

### As Dictionary
```python
# Monthly
summary = summaries.get_monthly_summary(tenant_id, 2025, 1)

# Yearly
summary = summaries.get_yearly_summary(tenant_id, 2025)

# Rental Period
summary = summaries.get_rental_period_summary(tenant_id)
```

### Access Fields
```python
summary['tenant_name']          # Tenant name
summary['expected_rent']        # Expected payment amount
summary['total_paid']           # Amount paid
summary['balance']              # Amount owed
summary['payment_rate']         # Percentage (yearly/period only)
summary['is_delinquent']        # Boolean (monthly only)
```

## Export Data

### To JSON
```python
# Monthly
summaries.export_monthly_summary_json(tenant_id, 2025, 1, 'file.json')

# Yearly
summaries.export_yearly_summary_json(tenant_id, 2025, 'file.json')

# Rental Period
summaries.export_rental_period_summary_json(tenant_id, 'file.json')
```

### To CSV
```python
summary = summaries.get_yearly_summary(tenant_id, 2025)
summaries.export_to_csv(summary, 'report.csv', summary_type='yearly')
```

## Common Patterns

### Loop Through All Tenants
```python
tenants = tenant_manager.list_tenants()
for tenant in tenants:
    summaries.print_rental_period_summary(tenant.tenant_id)
```

### Generate Quarterly Reports
```python
for month in range(1, 4):  # Jan, Feb, Mar
    summary = summaries.get_monthly_summary(tenant_id, 2025, month)
    # Use summary data
```

### Find Delinquent Tenants
```python
for tenant in tenant_manager.list_tenants():
    summary = summaries.get_rental_period_summary(tenant.tenant_id)
    if summary['delinquent_months'] > 0:
        print(f"{tenant.name}: {summary['delinquent_months']} months delinquent")
```

### Export All Tenant Reports
```python
for tenant in tenant_manager.list_tenants():
    filename = f"report_{tenant.tenant_id}_2025.json"
    summaries.export_rental_period_summary_json(tenant.tenant_id, filename)
```

## Return Values

### Success
- Methods return `True` if successful
- `get_*_summary()` returns Dictionary
- `print_*_summary()` returns `True` on success

### Failure
- Methods return `False` if failed
- `get_*_summary()` returns `None` on failure
- Errors are logged to Logger

## Summary Types

| Type | Scope | Data |
|------|-------|------|
| Monthly | Single month | Expected, paid, balance, payments list |
| Yearly | 12 months | Monthly breakdown, payment rate, delinquency count |
| Period | Entire lease | All years, credits, complete tenant info |

## Output Formats

| Format | Method | Use Case |
|--------|--------|----------|
| Console | `print_*()` | Quick review |
| JSON | `export_*_json()` | Data analysis |
| CSV | `export_to_csv()` | Spreadsheet import |

## Common Issues

| Issue | Solution |
|-------|----------|
| No data shown | Check tenant exists and has payment history |
| Export fails | Verify filepath is writable |
| Wrong delinquency | Run `rent_tracker.check_and_update_delinquency()` first |
| Missing months | Check `tenant.months_to_charge` is populated |

## Integration Points

- **TenantManager** - Get tenant data
- **RentTracker** - Access payment history and calculate rent
- **Logger** - Track all operations

## Sample Output

### Monthly Summary
```
Expected Rent:        $  1200.00
Total Paid:           $  1200.00
Balance:              $     0.00
Status:               OK
```

### Yearly Summary
```
Total Expected Rent:  $ 14400.00
Total Paid:           $ 14400.00
Total Balance:        $     0.00
Payment Rate:           100.0%
```

## Best Practices

1. **Before generating reports** - Run `rent_tracker.check_and_update_delinquency()`
2. **Batch operations** - Export all at once to avoid repeated calculations
3. **Error handling** - Check return value before using data
4. **Logging** - Monitor logger output for issues
5. **Schedule exports** - Run at consistent intervals (weekly/monthly)
