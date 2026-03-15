"""
Test suite for Loan Calculator
Verifies amortization calculations, extra payment scenarios, and payoff projections
"""

import sys
import os
from datetime import date

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.loan_calculator import LoanCalculator


def test_basic_amortization():
    """Test basic amortization schedule calculation"""
    print("\n" + "="*60)
    print("TEST 1: Basic Amortization Schedule")
    print("="*60)
    
    # $10,000 loan at 5% for 12 months with $856.07 payment
    calculator = LoanCalculator(
        principal=10000,
        annual_rate=0.05,
        monthly_payment=856.07,
        start_date=date(2024, 1, 1)
    )
    
    schedule = calculator.calculate_standard_schedule()
    stats = calculator.get_summary_stats(schedule)
    
    print(f"Principal: ${calculator.principal:,.2f}")
    print(f"Interest Rate: {calculator.annual_rate * 100:.2f}%")
    print(f"Monthly Payment: ${calculator.monthly_payment:,.2f}")
    print(f"\nResults:")
    print(f"  Total Payments: {stats['total_payments']}")
    print(f"  Total Paid: ${stats['total_paid']:,.2f}")
    print(f"  Total Interest: ${stats['total_interest']:,.2f}")
    print(f"  Payoff Date: {stats['payoff_date']}")
    
    # Verify the loan is paid off
    final_balance = schedule[-1]['balance']
    assert final_balance < 0.01, f"Expected near-zero balance, got ${final_balance:.2f}"
    
    # Verify total principal equals original principal
    total_principal = sum(p['principal'] for p in schedule)
    assert abs(total_principal - calculator.principal) < 1.0, \
        f"Expected principal ${calculator.principal:.2f}, got ${total_principal:.2f}"
    
    print("\n✅ Basic amortization test PASSED")
    return True


def test_extra_monthly_payment():
    """Test extra monthly payment scenario"""
    print("\n" + "="*60)
    print("TEST 2: Extra Monthly Payment")
    print("="*60)
    
    # $100,000 mortgage at 4% with $477.42 payment (30 years)
    calculator = LoanCalculator(
        principal=100000,
        annual_rate=0.04,
        monthly_payment=477.42,
        start_date=date(2024, 1, 1)
    )
    
    # Compare standard vs $200 extra monthly
    comparison = calculator.compare_scenarios(extra_monthly=200)
    
    print(f"Principal: ${calculator.principal:,.2f}")
    print(f"Interest Rate: {calculator.annual_rate * 100:.2f}%")
    print(f"Monthly Payment: ${calculator.monthly_payment:,.2f}")
    print(f"\nStandard Schedule:")
    print(f"  Months: {comparison['standard']['months_to_payoff']}")
    print(f"  Total Interest: ${comparison['standard']['total_interest']:,.2f}")
    print(f"\nWith $200 Extra Monthly:")
    print(f"  Months: {comparison['accelerated']['months_to_payoff']}")
    print(f"  Total Interest: ${comparison['accelerated']['total_interest']:,.2f}")
    print(f"\nSavings:")
    print(f"  Interest Saved: ${comparison['interest_saved']:,.2f}")
    print(f"  Time Saved: {comparison['months_saved']} months ({comparison['years_saved']:.1f} years)")
    
    # Verify interest is actually saved
    assert comparison['interest_saved'] > 0, "Expected interest savings with extra payments"
    assert comparison['months_saved'] > 0, "Expected time savings with extra payments"
    
    print("\n✅ Extra monthly payment test PASSED")
    return True


def test_lump_sum_payment():
    """Test lump sum payment scenario"""
    print("\n" + "="*60)
    print("TEST 3: Lump Sum Payment")
    print("="*60)
    
    # $50,000 loan at 6% with $500 monthly payment
    calculator = LoanCalculator(
        principal=50000,
        annual_rate=0.06,
        monthly_payment=500,
        start_date=date(2024, 1, 1)
    )
    
    # Apply $10,000 lump sum at month 12
    comparison = calculator.compare_scenarios(lump_sum=10000, lump_sum_month=12)
    
    print(f"Principal: ${calculator.principal:,.2f}")
    print(f"Interest Rate: {calculator.annual_rate * 100:.2f}%")
    print(f"Monthly Payment: ${calculator.monthly_payment:,.2f}")
    print(f"Lump Sum: $10,000 at month 12")
    print(f"\nStandard Schedule:")
    print(f"  Months: {comparison['standard']['months_to_payoff']}")
    print(f"  Total Interest: ${comparison['standard']['total_interest']:,.2f}")
    print(f"\nWith Lump Sum:")
    print(f"  Months: {comparison['accelerated']['months_to_payoff']}")
    print(f"  Total Interest: ${comparison['accelerated']['total_interest']:,.2f}")
    print(f"\nSavings:")
    print(f"  Interest Saved: ${comparison['interest_saved']:,.2f}")
    print(f"  Time Saved: {comparison['months_saved']} months")
    
    # Verify lump sum reduces payoff time
    assert comparison['months_saved'] > 0, "Expected lump sum to reduce payoff time"
    assert comparison['interest_saved'] > 0, "Expected lump sum to save interest"
    
    print("\n✅ Lump sum payment test PASSED")
    return True


def test_calculate_monthly_payment():
    """Test monthly payment calculation"""
    print("\n" + "="*60)
    print("TEST 4: Calculate Monthly Payment")
    print("="*60)
    
    # Calculate payment for $200,000 mortgage at 3.5% for 30 years
    principal = 200000
    annual_rate = 0.035
    months = 360  # 30 years
    
    payment = LoanCalculator.calculate_loan_payment(principal, annual_rate, months)
    
    print(f"Principal: ${principal:,.2f}")
    print(f"Interest Rate: {annual_rate * 100:.2f}%")
    print(f"Term: {months} months ({months / 12:.0f} years)")
    print(f"\nCalculated Monthly Payment: ${payment:,.2f}")
    
    # Verify the payment actually pays off the loan
    calculator = LoanCalculator(principal, annual_rate, payment)
    schedule = calculator.calculate_standard_schedule()
    
    # Should be close to the expected term
    assert abs(len(schedule) - months) < 5, \
        f"Expected ~{months} payments, got {len(schedule)}"
    
    print(f"Verification: Loan paid off in {len(schedule)} months")
    
    print("\n✅ Monthly payment calculation test PASSED")
    return True


def test_yearly_breakdown():
    """Test annual payment breakdown"""
    print("\n" + "="*60)
    print("TEST 5: Yearly Payment Breakdown")
    print("="*60)
    
    # $150,000 loan at 4.5% with $760.03 payment
    calculator = LoanCalculator(
        principal=150000,
        annual_rate=0.045,
        monthly_payment=760.03,
        start_date=date(2024, 1, 1)
    )
    
    schedule = calculator.calculate_standard_schedule()
    yearly = calculator.get_payment_breakdown_by_year(schedule)
    
    print(f"Principal: ${calculator.principal:,.2f}")
    print(f"Interest Rate: {calculator.annual_rate * 100:.2f}%")
    print(f"Monthly Payment: ${calculator.monthly_payment:,.2f}")
    print(f"\nYearly Breakdown (first 5 years):")
    print(f"{'Year':<8} {'Payments':<10} {'Total Paid':<15} {'Principal':<15} {'Interest':<15} {'End Balance':<15}")
    print("-" * 90)
    
    for year in sorted(yearly.keys())[:5]:
        data = yearly[year]
        print(f"{year:<8} {data['payments']:<10} "
              f"${data['total_paid']:>12,.2f}  "
              f"${data['total_principal']:>12,.2f}  "
              f"${data['total_interest']:>12,.2f}  "
              f"${data['ending_balance']:>12,.2f}")
    
    # Verify each year has 12 payments (except possibly last year)
    years = sorted(yearly.keys())
    for year in years[:-1]:  # All but last year
        assert yearly[year]['payments'] == 12, \
            f"Expected 12 payments for year {year}, got {yearly[year]['payments']}"
    
    print("\n✅ Yearly breakdown test PASSED")
    return True


def test_zero_interest():
    """Test zero interest loan (payment plan)"""
    print("\n" + "="*60)
    print("TEST 6: Zero Interest Loan")
    print("="*60)
    
    # $12,000 zero interest for 12 months
    calculator = LoanCalculator(
        principal=12000,
        annual_rate=0.0,
        monthly_payment=1000,
        start_date=date(2024, 1, 1)
    )
    
    schedule = calculator.calculate_standard_schedule()
    stats = calculator.get_summary_stats(schedule)
    
    print(f"Principal: ${calculator.principal:,.2f}")
    print(f"Interest Rate: {calculator.annual_rate * 100:.2f}%")
    print(f"Monthly Payment: ${calculator.monthly_payment:,.2f}")
    print(f"\nResults:")
    print(f"  Payments: {stats['total_payments']}")
    print(f"  Total Interest: ${stats['total_interest']:,.2f}")
    
    # Verify no interest charged
    assert abs(stats['total_interest']) < 0.01, \
        f"Expected zero interest, got ${stats['total_interest']:.2f}"
    
    # Verify correct number of payments
    assert stats['total_payments'] == 12, \
        f"Expected 12 payments, got {stats['total_payments']}"
    
    print("\n✅ Zero interest test PASSED")
    return True


def test_csv_export():
    """Test CSV export functionality"""
    print("\n" + "="*60)
    print("TEST 7: CSV Export")
    print("="*60)
    
    # Create a simple loan schedule
    calculator = LoanCalculator(
        principal=5000,
        annual_rate=0.06,
        monthly_payment=500,
        start_date=date(2024, 1, 1)
    )
    
    schedule = calculator.calculate_standard_schedule()
    
    # Export to CSV
    filename = '/tmp/test_amortization_schedule.csv'
    success = calculator.export_schedule_to_csv(schedule, filename)
    
    print(f"Principal: ${calculator.principal:,.2f}")
    print(f"Exporting schedule to: {filename}")
    
    assert success, "CSV export failed"
    
    # Verify file was created
    assert os.path.exists(filename), f"CSV file not created: {filename}"
    
    # Read and verify content
    with open(filename, 'r') as f:
        lines = f.readlines()
        assert len(lines) > len(schedule), "CSV should have headers and summary"
        assert 'Payment #' in lines[0], "CSV should have headers"
    
    print(f"✅ CSV exported successfully: {len(lines)} lines")
    print("\n✅ CSV export test PASSED")
    
    return True


def run_all_tests():
    """Run all test cases"""
    print("\n" + "="*60)
    print("LOAN CALCULATOR TEST SUITE")
    print("="*60)
    
    tests = [
        test_basic_amortization,
        test_extra_monthly_payment,
        test_lump_sum_payment,
        test_calculate_monthly_payment,
        test_yearly_breakdown,
        test_zero_interest,
        test_csv_export
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except AssertionError as e:
            print(f"\n❌ Test FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"\n❌ Test ERROR: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Tests Run: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! 🎉")
    else:
        print(f"\n⚠️  {failed} test(s) failed")
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
