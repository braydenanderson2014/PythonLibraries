"""Test suite for split transaction functionality"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.bank import Bank, Transaction
from datetime import datetime

def test_transaction_splits():
    """Test Transaction class split functionality"""
    print("\n=== Testing Transaction Split Functionality ===\n")
    
    # Test 1: Create transaction with splits
    print("Test 1: Creating transaction with splits...")
    splits = [
        {'category': 'Food', 'amount': 50.00},
        {'category': 'Household', 'amount': 30.00},
        {'category': 'Personal Care', 'amount': 15.00}
    ]
    
    tx = Transaction(
        amount=95.00,
        desc="Grocery Store Trip",
        account="Checking",
        type_='out',
        splits=splits
    )
    
    assert tx.is_split() == True, "Transaction should be marked as split"
    assert len(tx.splits) == 3, f"Expected 3 splits, got {len(tx.splits)}"
    print("✓ Transaction created with 3 splits")
    
    # Test 2: Validate splits sum
    print("\nTest 2: Validating split amounts...")
    assert tx.validate_splits() == True, "Splits should sum to transaction amount"
    print("✓ Splits sum correctly: $95.00")
    
    # Test 3: Invalid splits (don't sum to total)
    print("\nTest 3: Testing invalid splits...")
    invalid_tx = Transaction(
        amount=100.00,
        desc="Invalid Split",
        account="Checking",
        type_='out',
        splits=[
            {'category': 'Food', 'amount': 50.00},
            {'category': 'Gas', 'amount': 25.00}  # Only $75, should be $100
        ]
    )
    
    assert invalid_tx.validate_splits() == False, "Invalid splits should not validate"
    print("✓ Invalid splits detected correctly")
    
    # Test 4: Get categories from split transaction
    print("\nTest 4: Getting categories from split transaction...")
    categories = tx.get_categories()
    assert categories == ['Food', 'Household', 'Personal Care'], f"Expected 3 categories, got {categories}"
    print(f"✓ Categories extracted: {', '.join(categories)}")
    
    # Test 5: Regular transaction (no splits)
    print("\nTest 5: Testing regular transaction (no splits)...")
    regular_tx = Transaction(
        amount=50.00,
        desc="Coffee",
        account="Checking",
        type_='out',
        category='Dining'
    )
    
    assert regular_tx.is_split() == False, "Regular transaction should not be split"
    assert regular_tx.validate_splits() == True, "Regular transaction should validate"
    assert regular_tx.get_categories() == ['Dining'], "Should return single category"
    print("✓ Regular transaction works correctly")
    
    print("\n=== Transaction Split Tests: ALL PASSED ✓ ===\n")

def test_bank_split_transactions():
    """Test Bank class handling of split transactions"""
    print("=== Testing Bank Split Transaction Handling ===\n")
    
    # Create a fresh bank instance with no data
    from src.bank import BANK_DATA_FILE as original_bank_file
    import src.bank
    
    test_bank_file = '/tmp/test_bank_splits.json'
    if os.path.exists(test_bank_file):
        os.remove(test_bank_file)
    
    # Temporarily change the bank data file path
    src.bank.BANK_DATA_FILE = test_bank_file
    
    # Create empty bank file (just an array)
    with open(test_bank_file, 'w') as f:
        import json
        json.dump([], f)  # Empty array of transactions
    
    bank = Bank()
    bank.current_user_id = 'test_user'
    
    # Test 1: Add split transaction
    print("Test 1: Adding split transaction to bank...")
    splits = [
        {'category': 'Groceries', 'amount': 75.00},
        {'category': 'Cleaning Supplies', 'amount': 25.00}
    ]
    
    bank.add_transaction(
        amount=100.00,
        desc="Walmart Shopping",
        account="Checking",
        type_='out',
        category='Shopping',  # Main category (will be overridden by splits)
        splits=splits
    )
    
    transactions = bank.list_transactions(user_id='test_user')
    assert len(transactions) == 1, f"Expected 1 transaction, got {len(transactions)}"
    
    tx = transactions[0]
    assert 'splits' in tx, "Transaction should have splits field"
    assert len(tx['splits']) == 2, f"Expected 2 splits, got {len(tx['splits'])}"
    print("✓ Split transaction added successfully")
    
    # Test 2: Get financial summary with splits
    print("\nTest 2: Testing financial summary with split transactions...")
    summary = bank.get_financial_summary(user_id='test_user')
    
    assert summary['total_expenses'] == 100.00, f"Expected $100 total, got ${summary['total_expenses']}"
    
    # Check that splits are counted in categories
    expense_by_cat = summary['expense_by_category']
    assert 'Groceries' in expense_by_cat, "Groceries category should be in summary"
    assert 'Cleaning Supplies' in expense_by_cat, "Cleaning Supplies category should be in summary"
    assert expense_by_cat['Groceries'] == 75.00, f"Expected $75 for Groceries, got ${expense_by_cat['Groceries']}"
    assert expense_by_cat['Cleaning Supplies'] == 25.00, f"Expected $25 for Cleaning Supplies, got ${expense_by_cat['Cleaning Supplies']}"
    
    print(f"✓ Category breakdown correct:")
    print(f"  - Groceries: ${expense_by_cat['Groceries']:.2f}")
    print(f"  - Cleaning Supplies: ${expense_by_cat['Cleaning Supplies']:.2f}")
    
    # Test 3: Add regular transaction and verify both work together
    print("\nTest 3: Adding regular transaction alongside split transaction...")
    bank.add_transaction(
        amount=30.00,
        desc="Gas Station",
        account="Checking",
        type_='out',
        category='Transportation'
    )
    
    summary = bank.get_financial_summary(user_id='test_user')
    assert summary['total_expenses'] == 130.00, f"Expected $130 total, got ${summary['total_expenses']}"
    assert 'Transportation' in summary['expense_by_category'], "Transportation should be in summary"
    assert summary['expense_by_category']['Transportation'] == 30.00, "Transportation should be $30"
    
    print("✓ Regular and split transactions work together")
    print(f"  Total expenses: ${summary['total_expenses']:.2f}")
    
    # Test 4: Validate splits (should fail with invalid splits)
    print("\nTest 4: Testing split validation...")
    try:
        bank.add_transaction(
            amount=100.00,
            desc="Invalid Split",
            account="Checking",
            type_='out',
            category='Shopping',
            splits=[
                {'category': 'Food', 'amount': 50.00},
                {'category': 'Gas', 'amount': 40.00}  # Only $90, should be $100
            ]
        )
        print("✗ Validation failed - invalid splits were accepted")
        assert False, "Should have raised ValueError for invalid splits"
    except ValueError as e:
        print(f"✓ Validation working: {e}")
    
    # Cleanup
    if os.path.exists(test_bank_file):
        os.remove(test_bank_file)
    
    # Restore original path
    src.bank.BANK_DATA_FILE = original_bank_file
    
    print("\n=== Bank Split Transaction Tests: ALL PASSED ✓ ===\n")

def test_budget_split_transactions():
    """Test Budget manager handling of split transactions"""
    print("=== Testing Budget Manager with Split Transactions ===\n")
    
    from src.budget import BudgetManager, Budget
    from datetime import date
    
    # Create test data
    test_budget_file = '/tmp/test_budgets_splits.json'
    if os.path.exists(test_budget_file):
        os.remove(test_budget_file)
    
    budget_mgr = BudgetManager(test_budget_file)
    
    # Add budgets
    groceries_budget = Budget(category='Groceries', monthly_limit=200.00, user_id='test_user')
    household_budget = Budget(category='Household', monthly_limit=50.00, user_id='test_user')
    
    budget_mgr.add_budget(groceries_budget)
    budget_mgr.add_budget(household_budget)
    
    # Create transactions with splits
    today = date.today()
    transactions = [
        {
            'amount': 150.00,
            'desc': 'Supermarket',
            'type': 'out',
            'date': today.strftime('%Y-%m-%d'),
            'splits': [
                {'category': 'Groceries', 'amount': 120.00},
                {'category': 'Household', 'amount': 30.00}
            ]
        },
        {
            'amount': 50.00,
            'desc': 'Grocery Store 2',
            'type': 'out',
            'category': 'Groceries',
            'date': today.strftime('%Y-%m-%d'),
            'splits': []  # Regular transaction
        }
    ]
    
    print("Test 1: Calculating spending with split transactions...")
    groceries_spending = budget_mgr.calculate_spending(transactions, 'Groceries', today.year, today.month)
    household_spending = budget_mgr.calculate_spending(transactions, 'Household', today.year, today.month)
    
    assert groceries_spending == 170.00, f"Expected $170 for Groceries (120+50), got ${groceries_spending}"
    assert household_spending == 30.00, f"Expected $30 for Household, got ${household_spending}"
    
    print(f"✓ Spending calculated correctly:")
    print(f"  - Groceries: ${groceries_spending:.2f} / $200.00")
    print(f"  - Household: ${household_spending:.2f} / $50.00")
    
    print("\nTest 2: Getting budget status with splits...")
    groceries_status = budget_mgr.get_budget_status(transactions, 'Groceries', today.year, today.month)
    household_status = budget_mgr.get_budget_status(transactions, 'Household', today.year, today.month)
    
    assert groceries_status['spent'] == 170.00, "Groceries spent should be $170"
    assert groceries_status['status'] == 'warning', f"Groceries should be in warning status (85%), got {groceries_status['status']}"
    
    assert household_status['spent'] == 30.00, "Household spent should be $30"
    assert household_status['status'] == 'good', f"Household should be in good status (60%), got {household_status['status']}"
    
    print(f"✓ Budget status correct:")
    print(f"  - Groceries: {groceries_status['status']} ({groceries_status['percentage']:.1f}%)")
    print(f"  - Household: {household_status['status']} ({household_status['percentage']:.1f}%)")
    
    # Cleanup
    if os.path.exists(test_budget_file):
        os.remove(test_budget_file)
    
    print("\n=== Budget Split Transaction Tests: ALL PASSED ✓ ===\n")

if __name__ == '__main__':
    print("\n" + "="*60)
    print("SPLIT TRANSACTION TEST SUITE")
    print("="*60)
    
    try:
        test_transaction_splits()
        test_bank_split_transactions()
        test_budget_split_transactions()
        
        print("\n" + "="*60)
        print("ALL TESTS PASSED! ✓✓✓")
        print("="*60 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
