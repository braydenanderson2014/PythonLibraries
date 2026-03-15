#!/usr/bin/env python3
"""
Test script for the new financial tracker system.
"""

from src.bank import Bank
from src.account import AccountManager

def test_financial_system():
    print("=== Testing Enhanced Financial System ===")
    
    # Test user-based finances
    print("\n1. Testing User-Based Finances:")
    bank = Bank()
    bank.set_current_user('braydenanderson2014')
    
    # Add some test transactions
    bank.add_transaction(
        amount=3000.0,
        desc="Salary",
        account="Checking",
        type_='in',
        category="Income"
    )
    
    bank.add_transaction(
        amount=1200.0,
        desc="Rent Payment",
        account="Checking",
        type_='out',
        category="Housing"
    )
    
    bank.add_transaction(
        amount=300.0,
        desc="Groceries",
        account="Checking",
        type_='out',
        category="Food"
    )
    
    print(f"Added 3 transactions for braydenanderson2014")
    
    # Test recurring transactions
    print("\n2. Testing Recurring Transactions:")
    bank.add_recurring_transaction(
        amount=3000.0,
        desc="Monthly Salary",
        account="Checking",
        type_='in',
        category="Salary",
        frequency='monthly'
    )
    
    bank.add_recurring_transaction(
        amount=1200.0,
        desc="Monthly Rent",
        account="Checking",
        type_='out',
        category="Housing",
        frequency='monthly'
    )
    
    print("Added 2 recurring transactions")
    
    # Test financial summary
    print("\n3. Testing Financial Summary:")
    summary = bank.get_financial_summary('braydenanderson2014')
    print(f"Total Income: ${summary['total_income']:.2f}")
    print(f"Total Expenses: ${summary['total_expenses']:.2f}")
    print(f"Net Balance: ${summary['net_balance']:.2f}")
    print(f"Income Categories: {summary['income_by_category']}")
    print(f"Expense Categories: {summary['expense_by_category']}")
    
    # Test user finance combination
    print("\n4. Testing User Finance Combination:")
    
    # Add some transactions for admin user
    bank.set_current_user('admin')
    bank.add_transaction(
        amount=2000.0,
        desc="Freelance Work",
        account="Savings",
        type_='in',
        category="Income"
    )
    
    # Combine finances between users
    bank.combine_user_finances('braydenanderson2014', 'admin')
    print("Combined finances between braydenanderson2014 and admin")
    
    # Test combined view
    combined_summary = bank.get_financial_summary('braydenanderson2014')
    print(f"Combined Total Income: ${combined_summary['total_income']:.2f}")
    print(f"Combined Total Expenses: ${combined_summary['total_expenses']:.2f}")
    print(f"Combined Net Balance: ${combined_summary['net_balance']:.2f}")
    
    # Test recurring transaction processing
    print("\n5. Testing Recurring Transaction Processing:")
    processed_count = bank.process_recurring_transactions()
    print(f"Processed {processed_count} recurring transactions")
    
    print("\n=== Financial System Test Complete ===")

if __name__ == "__main__":
    test_financial_system()
