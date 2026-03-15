# Rental Summaries System Documentation

## Overview

The Rental Summaries system provides comprehensive reporting and analysis tools for rental properties. It generates detailed summaries at three time scales:

1. **Monthly Summaries** - Track rent payments and status for a specific month
2. **Yearly Summaries** - Analyze annual performance and delinquency patterns
3. **Rental Period Summaries** - Complete overview of the entire rental duration

All summaries can be displayed on-screen, exported to JSON, or converted to CSV for spreadsheet analysis.

## Features

### Summary Types

#### Monthly Summary
- Expected rent for the month
- Actual payments received
- Balance due
- Payment breakdown by date and type
- Monthly status and delinquency flags
- Due date information

#### Yearly Summary
- Total expected rent for the year
- Total payments received
- Total balance owed
- Payment rate percentage
- Breakdown of months: paid, partial, delinquent
- Detailed monthly breakdown table

#### Rental Period Summary
- Complete rental information (dates, contact, notes)
- Account status
- Total expected rent across entire period
- Total payments received
- Overpayment credits and service credits
- Delinquency tracking
- Yearly breakdown for multi-year leases

### Output Formats

1. **Console Display** - Formatted text output with ASCII tables
2. **JSON Export** - Complete summary data structure
3. **CSV Export** - Spreadsheet-compatible format

## Installation & Setup

The `RentalSummaries` class requires a `RentTracker` instance:

```python
from rental_summaries import RentalSummaries
from rent_tracker import RentTracker
from tenant import TenantManager

# Initialize the system
tenant_manager = TenantManager()
rent_tracker = RentTracker(tenant_manager=tenant_manager)
summaries = RentalSummaries(rent_tracker=rent_tracker)
```

## Usage Examples

### Basic Monthly Summary

```python
# Get monthly summary
summary = summaries.get_monthly_summary(
    tenant_id='TENANT123',
    year=2025,
    month=1
)

# Print to console
summaries.print_monthly_summary(
    tenant_id='TENANT123',
    year=2025,
    month=1
)
```

**Output Example:**
```
======================================================================
MONTHLY SUMMARY - January 2025
======================================================================
Tenant: John Smith (ID: TENANT123)
Due Date: 2025-01-05
----------------------------------------------------------------------
Expected Rent:        $  1200.00
Total Paid:           $  1200.00
Balance:              $     0.00
Status:               OK
----------------------------------------------------------------------
Payment Count:        1

Payments:
  • 2025-01-05: $ 1200.00 (Check)
======================================================================
```

### Yearly Summary

```python
# Get yearly summary
summary = summaries.get_yearly_summary(
    tenant_id='TENANT123',
    year=2025
)

# Print to console
summaries.print_yearly_summary(
    tenant_id='TENANT123',
    year=2025
)
```

**Output Includes:**
- Total expected and paid for the year
- Payment rate percentage
- Month-by-month breakdown table
- Delinquency count

### Rental Period Summary

```python
# Get complete rental period summary
summary = summaries.get_rental_period_summary(
    tenant_id='TENANT123'
)

# Print to console
summaries.print_rental_period_summary(
    tenant_id='TENANT123'
)
```

**Output Includes:**
- Tenant information and contact details
- Rental period dates and duration
- Account status
- Total credits (overpayment, service)
- Yearly breakdown for multi-year leases

## Data Structure Reference

### Monthly Summary Dictionary

```python
{
    'tenant_id': str,
    'tenant_name': str,
    'year': int,
    'month': int,
    'month_display': str,  # e.g., "January 2025"
    'expected_rent': float,
    'total_paid': float,
    'balance': float,
    'payment_count': int,
    'payments': [
        {
            'date': str,
            'amount': float,
            'type': str,  # e.g., "Check", "Cash", "ACH"
            'is_credit_usage': bool
        },
        ...
    ],
    'status': str,  # e.g., "OK", "DELINQUENT"
    'due_date': str,  # YYYY-MM-DD format
    'is_delinquent': bool
}
```

### Yearly Summary Dictionary

```python
{
    'tenant_id': str,
    'tenant_name': str,
    'year': int,
    'total_expected_rent': float,
    'total_paid': float,
    'total_balance': float,
    'payment_rate': float,  # Percentage
    'months_paid': int,
    'months_partial': int,
    'months_delinquent': int,
    'monthly_details': [
        # List of monthly summaries
        { ... }
    ]
}
```

### Rental Period Summary Dictionary

```python
{
    'tenant_id': str,
    'tenant_name': str,
    'rental_start_date': str,  # ISO format
    'rental_end_date': str,
    'rental_period_days': int,
    'account_status': str,
    'rent_amount': float,
    'deposit_amount': float,
    'contact_info': dict,
    'total_expected_rent': float,
    'total_paid': float,
    'total_balance': float,
    'overpayment_credit': float,
    'service_credit': float,
    'delinquency_balance': float,
    'delinquent_months': int,
    'payment_rate': float,  # Percentage
    'yearly_summaries': [
        # List of yearly summaries
        { ... }
    ]
}
```

## Export Functions

### Export to JSON

```python
# Monthly summary
summaries.export_monthly_summary_json(
    tenant_id='TENANT123',
    year=2025,
    month=1,
    filepath='monthly.json'
)

# Yearly summary
summaries.export_yearly_summary_json(
    tenant_id='TENANT123',
    year=2025,
    filepath='yearly.json'
)

# Rental period summary
summaries.export_rental_period_summary_json(
    tenant_id='TENANT123',
    filepath='period.json'
)
```

### Export to CSV

```python
# Get summary first
summary = summaries.get_yearly_summary(tenant_id='TENANT123', year=2025)

# Export to CSV
summaries.export_to_csv(
    summary=summary,
    filepath='yearly_report.csv',
    summary_type='yearly'
)
```

Supported CSV types:
- `'monthly'` - Single month summary
- `'yearly'` - Annual breakdown
- `'period'` - Multi-year rental period

## Integration with Existing Systems

### With TenantManager

```python
# Get all tenants
tenants = tenant_manager.list_tenants()

# Generate reports for all tenants
for tenant in tenants:
    summaries.print_rental_period_summary(tenant.tenant_id)
```

### With Payment History

The system automatically:
- Tracks payment history by month
- Identifies credit usage vs. regular payments
- Calculates delinquent periods
- Manages service credits and overpayments

## Advanced Usage

### Generate Reports for Date Range

```python
def generate_q1_reports(tenant_id, year):
    """Generate reports for first quarter"""
    for month in range(1, 4):
        summaries.print_monthly_summary(tenant_id, year, month)
        # Or export to CSV
        summary = summaries.get_monthly_summary(tenant_id, year, month)
        filename = f"report_{year}_Q1_month{month}.csv"
        summaries.export_to_csv(summary, filename, 'monthly')
```

### Multi-Tenant Analysis

```python
def generate_all_tenant_reports(year):
    """Generate yearly reports for all tenants"""
    tenants = tenant_manager.list_tenants()
    
    for tenant in tenants:
        summary = summaries.get_yearly_summary(tenant.tenant_id, year)
        
        # Skip tenants with perfect payment
        if summary['payment_rate'] < 100:
            summaries.print_yearly_summary(tenant.tenant_id, year)
```

### Identify Problem Accounts

```python
def identify_delinquent_tenants():
    """Find all tenants with delinquent months"""
    tenants = tenant_manager.list_tenants()
    delinquent = []
    
    for tenant in tenants:
        summary = summaries.get_rental_period_summary(tenant.tenant_id)
        if summary and summary['delinquent_months'] > 0:
            delinquent.append({
                'name': tenant.name,
                'delinquent_months': summary['delinquent_months'],
                'balance': summary['total_balance']
            })
    
    return delinquent
```

## API Reference

### Main Methods

#### `get_monthly_summary(tenant_id, year, month) → Dict`
Generates summary for a specific month.

#### `get_yearly_summary(tenant_id, year) → Dict`
Generates summary for an entire year.

#### `get_rental_period_summary(tenant_id) → Dict`
Generates comprehensive summary for entire rental period.

#### `print_monthly_summary(tenant_id, year, month) → bool`
Prints formatted monthly summary to console.

#### `print_yearly_summary(tenant_id, year) → bool`
Prints formatted yearly summary to console.

#### `print_rental_period_summary(tenant_id) → bool`
Prints formatted rental period summary to console.

#### `export_monthly_summary_json(tenant_id, year, month, filepath) → bool`
Exports monthly summary to JSON file.

#### `export_yearly_summary_json(tenant_id, year, filepath) → bool`
Exports yearly summary to JSON file.

#### `export_rental_period_summary_json(tenant_id, filepath) → bool`
Exports rental period summary to JSON file.

#### `export_to_csv(summary, filepath, summary_type) → bool`
Exports any summary to CSV format.

### Formatting Methods

#### `format_monthly_display(summary) → str`
Returns formatted string for monthly summary.

#### `format_yearly_display(summary) → str`
Returns formatted string for yearly summary.

#### `format_rental_period_display(summary) → str`
Returns formatted string for rental period summary.

## Logging

All operations are logged through the Logger system:

```python
# Debug information
logger.debug("RentalSummaries", "Generating monthly summary...")

# Info for successful operations
logger.info("RentalSummaries", "Monthly summary printed successfully")

# Warnings for issues
logger.warning("RentalSummaries", "Tenant not found")

# Errors for failures
logger.error("RentalSummaries", "Failed to generate summary")
```

## Error Handling

The system handles various error conditions:

1. **Missing tenant** - Returns None with warning
2. **Invalid dates** - Gracefully parses multiple date formats
3. **Missing data** - Uses default values (0.0 for amounts, etc.)
4. **Database errors** - Logs error and returns None

Example error handling:

```python
summary = summaries.get_monthly_summary('INVALID_ID', 2025, 1)
if summary is None:
    print("Failed to generate summary")
else:
    summaries.print_monthly_summary('VALID_ID', 2025, 1)
```

## Performance Notes

- Monthly summaries are calculated on-demand
- Yearly summaries cache monthly results internally
- Rental period summaries collect all yearly data
- Large datasets (3+ years) may take a few seconds

## Troubleshooting

### No data appearing in summary

**Cause:** Tenant has no payment history or months_to_charge is not set

**Solution:** Ensure tenant has rental period defined and RentTracker has processed payments

### Export files not created

**Cause:** Invalid filepath or permission issues

**Solution:** Check filepath is writable and filename is valid

### Delinquency calculation incorrect

**Cause:** Payment history not synchronized with due dates

**Solution:** Run `rent_tracker.check_and_update_delinquency()` before generating summaries

## Future Enhancements

Planned features:
- HTML report generation
- PDF export with branding
- Email integration for automatic reports
- Batch processing for all tenants
- Custom date range queries
- Trend analysis and forecasting
- Late fee calculations in summaries
