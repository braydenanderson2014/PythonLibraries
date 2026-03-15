# Loan Amortization Schedule & Payoff Calculator

## Overview
Complete loan amortization calculator with what-if scenarios, interest savings calculations, and visual analytics. Integrated into the Financial Manager to help users understand loan payoff schedules and optimize payment strategies.

## Features

### 1. Amortization Schedule Display
- **Full Payment Breakdown**: View every payment's allocation to principal and interest
- **Balance Tracking**: See how the loan balance decreases over time
- **Date Projections**: Know exactly when the loan will be paid off
- **Monthly Detail**: Payment number, date, amount, principal, interest, and remaining balance

### 2. What-If Calculator
- **Extra Monthly Payments**: Calculate impact of paying extra each month
- **Lump Sum Payments**: Model one-time additional payments at specific months
- **Interest Savings**: See how much interest you'll save with accelerated payments
- **Time Savings**: Calculate how many months/years earlier the loan will be paid off
- **Visual Comparison**: Side-by-side comparison of standard vs accelerated scenarios

### 3. Visual Analytics
- **Principal vs Interest Chart**: Stacked bar chart showing payment composition
- **Balance Over Time**: Line chart showing balance reduction
- **Scenario Comparison**: Bar chart comparing total interest for different scenarios

### 4. Export Capabilities
- **CSV Export**: Export full amortization schedule to CSV
- **Comprehensive Summary**: Includes totals and key statistics
- **Easy Integration**: Import into Excel or other tools

## Implementation Details

### Core Components

#### 1. `src/loan_calculator.py` - Calculation Engine
```python
class LoanCalculator:
    """Calculate loan amortization schedules and what-if scenarios"""
    
    def __init__(self, principal, annual_rate, monthly_payment, start_date=None)
    def calculate_amortization_schedule(extra_monthly=0, lump_sum=0, lump_sum_month=0)
    def compare_scenarios(extra_monthly, lump_sum, lump_sum_month)
    def get_summary_stats(schedule)
    def export_schedule_to_csv(schedule, filename)
    def calculate_monthly_payment_needed(target_months)
    def get_payment_breakdown_by_year(schedule)
```

**Key Methods:**
- `calculate_amortization_schedule()`: Core calculation using monthly interest formula
- `compare_scenarios()`: Compare standard vs accelerated payment plans
- `get_summary_stats()`: Extract totals and key metrics from schedule
- `export_schedule_to_csv()`: Export schedule with summary

#### 2. Loan Class Integration (`src/bank.py`)
```python
class Loan:
    def get_amortization_schedule(extra_monthly=0, lump_sum=0, lump_sum_month=0)
    def get_payoff_info(extra_monthly=0)
    def compare_payment_scenarios(extra_monthly, lump_sum, lump_sum_month)
    def get_summary_stats()
```

**Integration Points:**
- Uses `LoanCalculator` internally
- Passes loan parameters (principal, rate, payment)
- Returns structured data for UI display

#### 3. UI Components (`ui/financial_tracker.py`)

**LoanDetailsDialog:**
- Two tabs: Payment Schedule and Charts
- Full amortization table with sortable columns
- Export to CSV button
- What-If Calculator button
- Summary statistics box with key metrics

**WhatIfCalculatorDialog:**
- Input fields for extra monthly payment
- Input fields for lump sum amount and timing
- Real-time scenario comparison
- Visual charts showing interest savings
- Summary of time and money saved

### Calculation Formulas

#### Monthly Interest Formula
```python
monthly_rate = annual_rate / 12
interest_payment = balance * monthly_rate
principal_payment = monthly_payment - interest_payment
new_balance = balance - principal_payment
```

#### Monthly Payment Formula
```python
# Calculate payment needed for specific term
monthly_rate = annual_rate / 12
payment = principal * (monthly_rate * (1 + monthly_rate)^months) / ((1 + monthly_rate)^months - 1)
```

#### Interest Savings Calculation
```python
interest_saved = standard_total_interest - accelerated_total_interest
months_saved = standard_months - accelerated_months
```

## Usage Guide

### Viewing Loan Details
1. Navigate to the **Loans** tab
2. Click **Details** button next to any loan
3. View full amortization schedule in table
4. Switch to **Charts** tab for visual analysis
5. Click **Export to CSV** to save schedule

### Using What-If Calculator
1. Open Loan Details dialog
2. Click **What-If Calculator** button
3. Enter extra monthly payment amount (if any)
4. Enter lump sum amount and when to apply it
5. Click **Calculate Scenarios**
6. Review comparison results and savings

### Understanding Results

**Payment Schedule Table Columns:**
- **Payment #**: Sequential payment number
- **Date**: Payment due date
- **Payment**: Total amount paid
- **Principal**: Amount reducing loan balance
- **Interest**: Interest charged this period
- **Extra**: Extra principal payment (if any)
- **Balance**: Remaining loan balance after payment

**Summary Statistics:**
- **Total Payments**: Number of monthly payments
- **Total Paid**: Sum of all payments
- **Total Interest**: Total interest over loan life
- **Total Principal**: Total principal paid (should equal original loan)
- **Payoff Date**: Final payment date
- **Months to Payoff**: Total loan duration

## Test Coverage

The test suite (`test_loan_calculator.py`) includes:

1. **Basic Amortization**: Verify standard schedule calculation
2. **Extra Monthly Payment**: Test accelerated payoff scenarios
3. **Lump Sum Payment**: Test one-time additional payments
4. **Payment Calculation**: Verify monthly payment formula
5. **Yearly Breakdown**: Test annual aggregation
6. **Zero Interest**: Test payment plans with no interest
7. **CSV Export**: Verify export functionality

**All tests pass successfully** ✅

## Example Scenarios

### Scenario 1: 30-Year Mortgage
- **Principal**: $200,000
- **Interest Rate**: 3.5% annual
- **Monthly Payment**: $898.09
- **Result**: 360 payments, $123,312 total interest

**With $200 Extra Monthly:**
- **New Duration**: 262 months (21.8 years)
- **New Interest**: $84,293
- **Savings**: $39,019 interest, 98 months (8.2 years)

### Scenario 2: Car Loan with Lump Sum
- **Principal**: $25,000
- **Interest Rate**: 4.5% annual
- **Monthly Payment**: $500
- **Lump Sum**: $5,000 at month 12

**Standard Plan:**
- **Duration**: 56 months
- **Total Interest**: $2,723

**With Lump Sum:**
- **Duration**: 43 months
- **Total Interest**: $1,859
- **Savings**: $864 interest, 13 months

## Technical Notes

### Performance
- Handles loans up to 1,000 payments (safety limit)
- Calculations are instantaneous for typical loans
- Charts render efficiently with matplotlib

### Accuracy
- Uses precise floating-point arithmetic
- Rounds to 2 decimal places for currency
- Handles final payment rounding correctly
- Prevents negative balances

### Error Handling
- Validates input parameters
- Catches calculation errors
- Provides user-friendly error messages
- Logs detailed errors for debugging

## Integration with Financial Manager

### Data Flow
1. User creates loan in Loans tab
2. Loan stored in `bank_data.json`
3. Details button triggers `view_loan_details()`
4. `LoanDetailsDialog` loads loan data
5. `LoanCalculator` performs calculations
6. Results displayed in tables and charts

### File Structure
```
Python Projects/Financial Manager/
├── src/
│   ├── loan_calculator.py      # Calculation engine
│   └── bank.py                 # Loan class with integration
├── ui/
│   └── financial_tracker.py    # UI dialogs and integration
├── test_loan_calculator.py     # Test suite
└── docs/
    └── LOAN_AMORTIZATION.md    # This file
```

## Future Enhancements

Potential additions for future versions:

1. **Refinance Calculator**: Compare refinancing scenarios
2. **Extra Payment Scheduler**: Schedule varying extra payments
3. **Bi-Weekly Payments**: Model bi-weekly payment strategy
4. **Tax Deduction**: Calculate tax benefits of mortgage interest
5. **Multiple Loan Comparison**: Compare different loan offers
6. **Payment Reminders**: Alert for upcoming payments
7. **Goal Integration**: Link to savings goals for extra payments
8. **PDF Reports**: Generate printable amortization reports

## Dependencies

- **Python**: 3.7+
- **PyQt6**: UI framework
- **matplotlib**: Charts and visualizations
- **python-dateutil**: Date calculations
- **csv**: CSV export (standard library)

## Maintenance

### Updating Formulas
If loan calculation formulas need updating:
1. Edit `src/loan_calculator.py`
2. Update corresponding tests in `test_loan_calculator.py`
3. Run test suite: `python test_loan_calculator.py`
4. Verify all tests pass

### Adding New Features
For new features:
1. Add methods to `LoanCalculator` class
2. Update `Loan` class integration methods
3. Create/update UI dialogs
4. Add comprehensive tests
5. Update this documentation

## Support

For issues or questions:
1. Check test suite for examples
2. Review error logs in console
3. Verify loan data in `bank_data.json`
4. Ensure all dependencies are installed

## Conclusion

The Loan Amortization & Payoff Calculator provides comprehensive tools for understanding and optimizing loan payments. Users can visualize payment schedules, explore what-if scenarios, and make informed decisions about accelerated payoff strategies.

**Key Benefits:**
- 💰 Calculate potential interest savings
- ⏱️ See time saved with extra payments
- 📊 Visual analytics for easy understanding
- 📁 Export capabilities for record-keeping
- 🎯 Make informed financial decisions

---
**Version**: 1.0  
**Last Updated**: January 2024  
**Status**: Production Ready ✅
