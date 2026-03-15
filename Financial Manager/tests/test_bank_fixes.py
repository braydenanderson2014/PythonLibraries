#!/usr/bin/env python3
"""
Test script to verify that the bank.py type error fixes work correctly
"""

import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_bank_functionality():
    """Test that the Bank class functions work without type errors"""
    print("Testing Bank class functionality after type error fixes...")
    
    try:
        from src.bank import Bank, Loan, RecurringTransaction
        
        # Test Bank initialization
        bank = Bank(current_user_id="test_user")
        print("✓ Bank initialization successful")
        
        # Test adding a loan with auto account creation
        bank.add_loan(
            principal=10000,
            annual_rate=0.05,
            payment_amount=300,
            desc="Test Car Loan",
            user_id="test_user",
            auto_create_account=True
        )
        print("✓ Loan creation with auto account successful")
        
        # Test listing loans
        loans = bank.list_loans("test_user")
        print(f"✓ Loan listing successful - found {len(loans)} loans")
        
        # Test creating a bank account
        account = bank.create_bank_account(
            bank_name="Test Bank",
            account_type="Checking", 
            account_name="Test Account",
            account_number="1234",
            user_id="test_user",
            initial_balance=1000.0
        )
        print("✓ Bank account creation successful")
        
        # Test processing recurring transactions (which includes loan payments)
        recurring_tx = RecurringTransaction(
            amount=300,
            desc="Car Loan Payment",
            account="Test Account",
            type_='loan_payment',
            frequency='monthly',
            user_id="test_user"
        )
        
        # Add the recurring transaction to the bank
        bank.recurring_transactions.append(recurring_tx.to_dict())
        
        # Test processing
        bank.process_recurring_transactions()
        print("✓ Recurring transaction processing successful")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing bank functionality: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_type_safety():
    """Test specific type safety improvements"""
    print("\nTesting type safety improvements...")
    
    try:
        from src.bank import Bank
        
        # Test with None user_id (should be handled gracefully)
        bank = Bank()
        
        # Test loan creation with None user_id
        bank.add_loan(
            principal=5000,
            annual_rate=0.04,
            payment_amount=200,
            desc="Test Loan",
            user_id=None,  # This should be handled without error
            auto_create_account=True
        )
        print("✓ None user_id handling successful")
        
        # Test account creation with None user_id
        account = bank.create_bank_account(
            bank_name="Test Bank 2",
            account_type="Savings",
            account_name="Test Savings",
            account_number="5678",
            user_id=None,  # This should be handled without error
            initial_balance=500.0
        )
        print("✓ None user_id in account creation successful")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing type safety: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Bank.py Type Error Fixes Verification")
    print("=" * 60)
    
    success = True
    
    # Test basic functionality
    success &= test_bank_functionality()
    
    # Test type safety
    success &= test_type_safety()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 All tests passed! Bank.py type errors have been fixed!")
        print("\nFixed Issues:")
        print("✓ user_id None handling in BankAccount creation")
        print("✓ get_loans() -> list_loans() method call")
        print("✓ pay_loan() -> proper loan payment handling")
        print("✓ loan.description -> loan.desc attribute access")
        print("✓ Safe string operations with None checking")
    else:
        print("❌ Some tests failed. Please check the error messages above.")
    
    print("=" * 60)