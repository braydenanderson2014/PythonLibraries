# CSV/Excel Export Enhancements Summary

## Overview
Enhanced the rent management export functionality to better track overpayments and clearly distinguish credit usage from actual rent payments.

## Changes Implemented

### 1. **Overpayment Created Column** ✅
- **Purpose**: Track when a payment results in creating an overpayment credit
- **Implementation**: 
  - Added new `_calculate_overpayment_created()` helper function
  - Calculates if a payment exceeded the expected rent for that month
  - Only counts the first payment that creates overpayment (not subsequent ones)
  - Ignores credit usage payments (they don't create new overpayments)
- **Location**: 
  - Excel: Column G "Overpayment Created"
  - CSV: Column 7 "Overpayment Created"

### 2. **Credit Usage Row Highlighting** ✅
- **Purpose**: Visually distinguish credit usage rows from actual rent payments
- **Implementation**:
  - Rows containing "Overpayment Credit" or "Service Credit" are highlighted in light yellow (#FFF2CC)
  - Entire row is colored to make it immediately obvious
  - Only applies to Excel format (CSV has "Is Credit Usage" column instead)
- **Rationale**: These rows represent credit usage, not new money received, so they shouldn't be counted in payment totals

### 3. **Disclaimer/Information Note** ✅
- **Purpose**: Explain the credit usage tracking system to users
- **Implementation**:
  - **Excel**: Prominent disclaimer at the top of each sheet in a gray box with italic text
  - **CSV**: Multi-line disclaimer at the beginning of the file
  - **Message**: "ℹ️ NOTE: Rows highlighted in light yellow (Excel) or marked 'Yes' in 'Is Credit Usage' column (CSV) are Overpayment Credit or Service Credit usage. These do NOT represent new rent payments and are not included in total payment calculations, as they were already counted when the original overpayment occurred."

### 4. **CSV-Specific Additions** ✅
- **Is Credit Usage Column**: Added explicit Yes/No column in CSV since we can't color rows
- **Overpayment Created Column**: Same as Excel, shows amount created by each payment

## Files Modified

### Primary Files
1. **`/ui/rent_management_tab.py`**
   - Added `_calculate_overpayment_created()` method
   - Updated `export_to_excel()` with:
     - Disclaimer at top
     - Credit usage row highlighting
     - New "Overpayment Created" column
   - Updated `export_to_csv_plain()` with:
     - Disclaimer at top
     - "Is Credit Usage" column
     - "Overpayment Created" column

2. **`/ui/comprehensive_tenant_analysis_tab.py`**
   - Added `_calculate_overpayment_created()` method
   - Updated `_create_tenant_sheet()` with same enhancements
   - Applied to all individual tenant sheets in comprehensive reports

## Technical Details

### Overpayment Calculation Logic
```python
def _calculate_overpayment_created(self, tenant, payment):
    # Skip credit usage payments
    if payment.get('is_credit_usage', False):
        return 0.0
    
    # Get expected rent for the month
    expected_rent = self.rent_tracker.get_effective_rent(tenant, year, month)
    
    # Calculate total paid up to this payment
    total_paid = sum of all payments for this month up to this date
    
    # If total exceeds expected
    if total_paid > expected_rent:
        # Check if previous payments already covered it
        previous_total = total_paid - current_payment_amount
        if previous_total >= expected_rent:
            return 0.0  # Already covered
        else:
            return total_paid - expected_rent  # This payment created overpayment
    
    return 0.0
```

### Color Scheme
- **Credit Usage Rows**: Light Yellow (#FFF2CC) - entire row
- **Status Colors** (unchanged):
  - Paid in Full: Green (#C6EFCE)
  - Overpayment: Light Green (#92D050)
  - Partial Payment: Yellow (#FFEB9C)
  - Not Paid: Red (#FFC7CE)
  - Delinquent: Dark Red (#FF0000)

## Example Output

### Excel Export
```
┌──────────────────────────────────────────────────────────────────────────────┐
│ ℹ️ NOTE: Rows highlighted in light yellow are Overpayment Credit or        │
│ Service Credit usage. These do NOT represent new rent payments...           │
└──────────────────────────────────────────────────────────────────────────────┘

PAYMENT HISTORY
┌──────────────┬─────────┬──────────────────────┬──────────┬────────┬─────────┬────────────────────┬───────┐
│ Date         │ Amount  │ Type                 │ For Month│ Status │ Details │ Overpayment Created│ Notes │
├──────────────┼─────────┼──────────────────────┼──────────┼────────┼─────────┼────────────────────┼───────┤
│ 07/26/2025   │ $1350   │ Card                 │ 2025-07  │ Paid   │ Fully   │                    │       │
│ 07/29/2025   │ $2400   │ Cash                 │ 2025-08  │ Overpay│ Over by │ $1050.00           │       │
│ [YELLOW ROW] │ $500    │ Overpayment Credit   │ 2025-09  │ Paid   │ Credit  │                    │       │
└──────────────┴─────────┴──────────────────────┴──────────┴────────┴─────────┴────────────────────┴───────┘
```

### CSV Export
```csv
NOTE: Rows marked with "Yes" in the "Is Credit Usage" column are Overpayment Credit...

Section,Payment History
Date Received,Amount,Type,For Month,Status,Details,Is Credit Usage,Overpayment Created,Notes
2025-07-26,1350.00,Card,2025-07,Paid in Full,Fully paid,No,,
2025-07-29,2400.00,Cash,2025-08,Overpayment,Overpaid by $1050.00,No,1050.00,
2025-08-15,500.00,Overpayment Credit,2025-09,Paid in Full,Credit applied,Yes,,Applied credit
```

## Benefits

1. **Clear Tracking**: Users can now see exactly which payments created overpayments
2. **Visual Distinction**: Credit usage is clearly separated from actual payments
3. **Better Reporting**: Easier to calculate actual money received vs. credits used
4. **Transparency**: Disclaimer explains the tracking system to prevent confusion
5. **Consistent Format**: Both CSV and Excel have the same information (with format-appropriate presentation)

## Testing Recommendations

1. Export a tenant with multiple overpayments
2. Verify overpayment amounts are correctly calculated
3. Confirm credit usage rows are highlighted in Excel
4. Check that CSV has proper "Is Credit Usage" values
5. Verify disclaimer appears on all exports
6. Test with tenants who have both regular payments and credit usage

## Future Enhancements

- Add summary totals excluding credit usage
- Add filter option to hide/show credit usage rows
- Create visual chart showing actual payments vs. credit usage
- Add monthly breakdown of overpayment creation
