"""
Visual test for Loan Amortization dialogs
Run this to verify UI components display correctly
"""

import sys
import os
from datetime import date
from PyQt6.QtWidgets import QApplication

# Add paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.bank import Loan
from ui.financial_tracker import LoanDetailsDialog, WhatIfCalculatorDialog


def test_loan_details_dialog():
    """Test the Loan Details dialog"""
    print("\n[TEST] Opening Loan Details Dialog...")
    
    # Create a sample loan
    loan = Loan(
        principal=100000,
        annual_rate=0.04,
        payment_amount=500,
        desc="Test Mortgage - 30 Year",
        frequency='monthly',
        start_date=date(2024, 1, 1).isoformat(),
        user_id='test_user',
        account_id='test_account',
        account_name='My Mortgage',
        identifier='test_loan_1'
    )
    
    # Create and show dialog
    app = QApplication(sys.argv)
    dialog = LoanDetailsDialog(loan)
    
    print("✅ Loan Details Dialog created successfully")
    print("   - Check Payment Schedule tab")
    print("   - Check Charts tab")
    print("   - Try Export to CSV button")
    print("   - Try What-If Calculator button")
    
    result = dialog.exec()
    print(f"Dialog closed with result: {result}")
    

def test_what_if_dialog():
    """Test the What-If Calculator dialog"""
    print("\n[TEST] Opening What-If Calculator Dialog...")
    
    # Create a sample loan
    loan = Loan(
        principal=50000,
        annual_rate=0.06,
        payment_amount=500,
        desc="Test Car Loan",
        frequency='monthly',
        start_date=date(2024, 1, 1).isoformat(),
        user_id='test_user',
        account_id='test_account',
        account_name='My Car Loan',
        identifier='test_loan_2'
    )
    
    # Create and show dialog
    app = QApplication(sys.argv)
    dialog = WhatIfCalculatorDialog(loan)
    
    print("✅ What-If Calculator Dialog created successfully")
    print("   - Check current loan info display")
    print("   - Try entering extra monthly payment")
    print("   - Try entering lump sum payment")
    print("   - Click Calculate Scenarios button")
    print("   - Review comparison results and charts")
    
    result = dialog.exec()
    print(f"Dialog closed with result: {result}")


def main():
    """Run visual tests"""
    print("="*60)
    print("LOAN AMORTIZATION UI VISUAL TEST")
    print("="*60)
    print("\nThis test will open UI dialogs for manual verification.")
    print("Close each dialog to proceed to the next test.")
    
    try:
        # Test 1: Loan Details
        test_loan_details_dialog()
        
        print("\n" + "="*60)
        
        # Test 2: What-If Calculator
        test_what_if_dialog()
        
        print("\n" + "="*60)
        print("✅ All visual tests completed")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
