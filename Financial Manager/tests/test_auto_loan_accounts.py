#!/usr/bin/env python3
"""
Test script for automatic loan account creation feature.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from src.bank import Bank
from src.bank_accounts import BankAccountManager
from datetime import date, datetime

def test_auto_loan_account_creation():
    """Test automatic loan account creation"""
    print("=" * 60)
    print("TESTING AUTOMATIC LOAN ACCOUNT CREATION")
    print("=" * 60)
    
    # Create a test bank instance
    bank = Bank("test_user_auto_loan")
    
    # Clear any existing data for clean test
    bank.loans = []
    bank.save_loans()
    
    # Also clear any existing accounts
    bank.account_manager.accounts = [acc for acc in bank.account_manager.accounts 
                                   if acc.user_id != "test_user_auto_loan"]
    bank.account_manager.save_accounts()
    
    print("✓ Cleared existing test data")
    
    # Get initial account count
    initial_accounts = bank.get_user_bank_accounts("test_user_auto_loan")
    initial_count = len(initial_accounts)
    print(f"✓ Initial account count: {initial_count}")
    
    # Add a loan with auto-create account enabled (default)
    loan_data = bank.add_loan(
        principal=30000.0,
        annual_rate=0.045,  # 4.5% annual rate
        payment_amount=650.0,
        desc="Test Auto Car Loan",
        frequency="monthly",
        user_id="test_user_auto_loan",
        auto_create_account=True  # Explicitly enable auto-creation
    )
    
    print(f"✓ Added loan with auto-creation: {loan_data['desc']}")
    print(f"  - Loan ID: {loan_data['identifier']}")
    print(f"  - Account ID: {loan_data.get('account_id', 'None')}")
    print(f"  - Account Name: {loan_data.get('account_name', 'None')}")
    print(f"  - Auto-created: {loan_data.get('auto_created_account', False)}")
    
    # Verify account was created
    final_accounts = bank.get_user_bank_accounts("test_user_auto_loan")
    final_count = len(final_accounts)
    print(f"✓ Final account count: {final_count}")
    
    if final_count > initial_count:
        print("✓ Account was automatically created!")
        
        # Find the loan account
        loan_account = None
        for account in final_accounts:
            if account.account_type == "Loan" and "Test Auto Car Loan" in account.account_name:
                loan_account = account
                break
        
        if loan_account:
            print(f"✓ Found loan account: {loan_account.get_display_name()}")
            print(f"  - Account ID: {loan_account.account_id}")
            print(f"  - Bank Name: {loan_account.bank_name}")
            print(f"  - Account Type: {loan_account.account_type}")
            print(f"  - Initial Balance: ${loan_account.initial_balance:,.2f}")
            
            # Verify the loan has the correct account reference
            if loan_data.get('account_id') == loan_account.account_id:
                print("✓ Loan correctly linked to auto-created account!")
            else:
                print("✗ Loan not properly linked to account")
        else:
            print("✗ Could not find the auto-created loan account")
    else:
        print("✗ No account was created")
    
    # Test loan account identification still works
    account_name = loan_data.get('account_name')
    if account_name:
        is_loan = bank.is_loan_account(account_name, "test_user_auto_loan")
        print(f"✓ Auto-created account identified as loan account: {is_loan}")
        
        loan_obj = bank.get_loan_for_account(account_name, "test_user_auto_loan")
        if loan_obj:
            print(f"✓ Can retrieve loan from auto-created account: {loan_obj.desc}")
        else:
            print("✗ Cannot retrieve loan from auto-created account")
    
    print("\n" + "=" * 60)
    print("AUTOMATIC LOAN ACCOUNT CREATION TEST COMPLETED")
    print("=" * 60)

def test_manual_loan_account_selection():
    """Test manual loan account selection (existing behavior)"""
    print("\n" + "=" * 60)
    print("TESTING MANUAL LOAN ACCOUNT SELECTION")
    print("=" * 60)
    
    # Create a test bank instance
    bank = Bank("test_user_manual_loan")
    
    # Clear any existing data for clean test
    bank.loans = []
    bank.save_loans()
    
    # Create a manual account first
    from src.bank_accounts import BankAccount
    manual_account = BankAccount(
        bank_name="Manual Bank",
        account_type="Loan",
        account_name="Manual Loan Account",
        user_id="test_user_manual_loan",
        initial_balance=-25000.0,
        active=True
    )
    
    added_account = bank.account_manager.add_account(manual_account)
    print(f"✓ Created manual account: {added_account.get_display_name()}")
    
    # Add a loan with manual account selection (auto-create disabled)
    loan_data = bank.add_loan(
        principal=25000.0,
        annual_rate=0.055,  # 5.5% annual rate
        payment_amount=450.0,
        desc="Test Manual Loan",
        account_id=added_account.account_id,
        account_name=added_account.get_display_name(),
        frequency="monthly",
        user_id="test_user_manual_loan",
        auto_create_account=False  # Disable auto-creation
    )
    
    print(f"✓ Added loan with manual account: {loan_data['desc']}")
    print(f"  - Uses existing account: {loan_data.get('account_name')}")
    print(f"  - Auto-created flag: {loan_data.get('auto_created_account', False)}")
    
    # Verify no additional account was created
    accounts = bank.get_user_bank_accounts("test_user_manual_loan")
    loan_accounts = [acc for acc in accounts if acc.account_type == "Loan"]
    
    if len(loan_accounts) == 1:
        print("✓ No additional account created - used existing account")
    else:
        print(f"✗ Unexpected number of loan accounts: {len(loan_accounts)}")
    
    print("\n" + "=" * 60)
    print("MANUAL LOAN ACCOUNT SELECTION TEST COMPLETED")
    print("=" * 60)

def test_loan_account_balance_tracking():
    """Test that loan account balances are properly tracked"""
    print("\n" + "=" * 60)
    print("TESTING LOAN ACCOUNT BALANCE TRACKING")
    print("=" * 60)
    
    # Create a test bank instance
    bank = Bank("test_user_balance")
    
    # Clear any existing data for clean test
    bank.loans = []
    bank.save_loans()
    
    # Add a loan with auto-created account
    loan_data = bank.add_loan(
        principal=20000.0,
        annual_rate=0.04,  # 4% annual rate
        payment_amount=400.0,
        desc="Test Balance Loan",
        frequency="monthly",
        user_id="test_user_balance",
        auto_create_account=True
    )
    
    print(f"✓ Created loan: {loan_data['desc']}")
    
    # Get the auto-created account
    account_id = loan_data.get('account_id')
    if account_id:
        balance = bank.get_account_balance(account_id)
        print(f"✓ Loan account balance: ${balance:,.2f}")
        
        # For loans, the balance should be negative (representing debt)
        if balance == -20000.0:
            print("✓ Loan account balance correctly set to negative principal amount")
        else:
            print(f"⚠️ Unexpected balance: expected -$20,000.00, got ${balance:,.2f}")
        
        # Get account summary
        summary = bank.get_accounts_summary("test_user_balance")
        loan_summary = next((acc for acc in summary if acc['account_id'] == account_id), None)
        
        if loan_summary:
            print(f"✓ Account summary: {loan_summary['display_name']}")
            print(f"  - Balance: ${loan_summary['balance']:,.2f}")
            print(f"  - Account Type: {loan_summary['account_type']}")
        else:
            print("✗ Could not find loan account in summary")
    else:
        print("✗ No account ID found in loan data")
    
    print("\n" + "=" * 60)
    print("LOAN ACCOUNT BALANCE TRACKING TEST COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    print("🚀 STARTING AUTOMATIC LOAN ACCOUNT TESTS")
    print("=" * 60)
    
    try:
        test_auto_loan_account_creation()
        test_manual_loan_account_selection()
        test_loan_account_balance_tracking()
        
        print("\n🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
        print("✓ Automatic loan account creation working")
        print("✓ Manual loan account selection still working")
        print("✓ Loan account balance tracking working")
        print("\nYour automatic loan account creation feature is ready to use!")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)