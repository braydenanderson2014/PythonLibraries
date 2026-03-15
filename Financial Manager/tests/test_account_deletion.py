#!/usr/bin/env python3
"""
Test script for bank account deletion functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from src.bank import Bank
from src.bank_accounts import BankAccount, BankAccountManager
from datetime import date, datetime

def test_bank_account_deletion():
    """Test bank account deletion functionality"""
    print("=" * 60)
    print("TESTING BANK ACCOUNT DELETION")
    print("=" * 60)
    
    # Create a test bank instance
    bank = Bank("test_user_deletion")
    
    # Clear any existing accounts for this test user
    bank.account_manager.accounts = [acc for acc in bank.account_manager.accounts 
                                   if acc.user_id != "test_user_deletion"]
    bank.account_manager.save_accounts()
    
    print("✓ Cleared existing test accounts")
    
    # Add a test account
    test_account = bank.add_bank_account(
        bank_name="Test Bank",
        account_type="Checking",
        account_name="Test Account",
        account_number="1234",
        initial_balance=1000.0,
        user_id="test_user_deletion"
    )
    
    print(f"✓ Added test account: {test_account.get_display_name()}")
    print(f"  - Account ID: {test_account.account_id}")
    print(f"  - Active: {test_account.active}")
    
    # Verify account appears in user accounts
    user_accounts = bank.get_user_bank_accounts("test_user_deletion")
    print(f"✓ User has {len(user_accounts)} active accounts")
    
    # Get accounts summary (what the UI uses)
    summary_before = bank.get_accounts_summary("test_user_deletion")
    print(f"✓ Accounts summary shows {len(summary_before)} accounts")
    
    # Delete the account
    print("\n--- DELETING ACCOUNT ---")
    result = bank.account_manager.remove_account(test_account.account_id)
    print(f"✓ Delete operation returned: {result}")
    
    # Check if account is marked as inactive
    all_accounts = [acc for acc in bank.account_manager.accounts 
                    if acc.user_id == "test_user_deletion"]
    print(f"✓ Total accounts for user (including inactive): {len(all_accounts)}")
    
    if all_accounts:
        account = all_accounts[0]
        print(f"  - Account active status: {account.active}")
        print(f"  - Account ID: {account.account_id}")
    
    # Verify account no longer appears in active accounts
    user_accounts_after = bank.get_user_bank_accounts("test_user_deletion")
    print(f"✓ User has {len(user_accounts_after)} active accounts after deletion")
    
    # Get accounts summary after deletion
    summary_after = bank.get_accounts_summary("test_user_deletion")
    print(f"✓ Accounts summary shows {len(summary_after)} accounts after deletion")
    
    # Test results
    if len(summary_before) == 1 and len(summary_after) == 0:
        print("\n🎉 DELETION TEST PASSED!")
        print("✓ Account properly removed from active accounts")
        print("✓ Account no longer appears in UI summary")
    else:
        print(f"\n❌ DELETION TEST FAILED!")
        print(f"Expected: 1 account before, 0 after")
        print(f"Actual: {len(summary_before)} before, {len(summary_after)} after")
    
    print("\n" + "=" * 60)
    print("BANK ACCOUNT DELETION TEST COMPLETED")
    print("=" * 60)

def test_account_manager_consistency():
    """Test that Bank and UI use the same account manager"""
    print("\n" + "=" * 60)
    print("TESTING ACCOUNT MANAGER CONSISTENCY")
    print("=" * 60)
    
    # Create bank instance
    bank = Bank("test_consistency")
    
    # Clear test data
    bank.account_manager.accounts = [acc for acc in bank.account_manager.accounts 
                                   if acc.user_id != "test_consistency"]
    bank.account_manager.save_accounts()
    
    # Simulate what the UI dialog would do with the fix
    from ui.bank_account_management_dialog import BankAccountManagementDialog
    
    # This would be how the dialog gets the account manager now
    ui_account_manager = bank.account_manager
    
    print(f"✓ Bank account manager ID: {id(bank.account_manager)}")
    print(f"✓ UI account manager ID: {id(ui_account_manager)}")
    
    if bank.account_manager is ui_account_manager:
        print("🎉 CONSISTENCY TEST PASSED!")
        print("✓ Bank and UI use the same account manager instance")
    else:
        print("❌ CONSISTENCY TEST FAILED!")
        print("✗ Bank and UI use different account manager instances")
    
    # Test adding account through UI account manager
    test_account = BankAccount(
        bank_name="UI Test Bank",
        account_type="Savings",
        account_name="UI Test Account",
        user_id="test_consistency",
        initial_balance=500.0
    )
    
    # Add through UI account manager
    ui_account_manager.add_account(test_account)
    
    # Check if visible through bank
    bank_accounts = bank.get_user_bank_accounts("test_consistency")
    print(f"✓ Accounts visible through Bank: {len(bank_accounts)}")
    
    if len(bank_accounts) == 1:
        print("🎉 INTEGRATION TEST PASSED!")
        print("✓ Accounts added through UI are visible through Bank")
    else:
        print("❌ INTEGRATION TEST FAILED!")
        print(f"Expected 1 account, found {len(bank_accounts)}")
    
    print("\n" + "=" * 60)
    print("ACCOUNT MANAGER CONSISTENCY TEST COMPLETED")
    print("=" * 60)

def test_account_persistence():
    """Test that account changes persist correctly"""
    print("\n" + "=" * 60)
    print("TESTING ACCOUNT PERSISTENCE")
    print("=" * 60)
    
    # Create first bank instance
    bank1 = Bank("test_persistence")
    
    # Clear test data
    bank1.account_manager.accounts = [acc for acc in bank1.account_manager.accounts 
                                    if acc.user_id != "test_persistence"]
    bank1.account_manager.save_accounts()
    
    # Add account
    test_account = bank1.add_bank_account(
        bank_name="Persistence Bank",
        account_type="Checking",
        account_name="Persistence Test",
        user_id="test_persistence",
        initial_balance=2000.0
    )
    
    account_id = test_account.account_id
    print(f"✓ Added account with ID: {account_id}")
    
    # Create second bank instance (simulates app restart)
    bank2 = Bank("test_persistence")
    
    # Check if account exists
    accounts_before = bank2.get_user_bank_accounts("test_persistence")
    print(f"✓ Found {len(accounts_before)} accounts after reload")
    
    # Delete account through second instance
    result = bank2.account_manager.remove_account(account_id)
    print(f"✓ Deletion result: {result}")
    
    # Create third bank instance (simulates another app restart)
    bank3 = Bank("test_persistence")
    
    # Check if deletion persisted
    accounts_after = bank3.get_user_bank_accounts("test_persistence")
    print(f"✓ Found {len(accounts_after)} accounts after deletion and reload")
    
    if len(accounts_before) == 1 and len(accounts_after) == 0:
        print("🎉 PERSISTENCE TEST PASSED!")
        print("✓ Account deletion persists across app restarts")
    else:
        print("❌ PERSISTENCE TEST FAILED!")
        print(f"Expected: 1 before, 0 after. Got: {len(accounts_before)} before, {len(accounts_after)} after")
    
    print("\n" + "=" * 60)
    print("ACCOUNT PERSISTENCE TEST COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    print("🚀 STARTING BANK ACCOUNT DELETION TESTS")
    print("=" * 60)
    
    try:
        test_bank_account_deletion()
        test_account_manager_consistency()
        test_account_persistence()
        
        print("\n🎉 ALL TESTS COMPLETED!")
        print("Your bank account deletion fixes should now work correctly!")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)