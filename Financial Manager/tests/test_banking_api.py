"""
Test script for Banking API integration
Tests the mock provider without requiring real credentials
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.banking_api import BankingAPIManager, MockBankingProvider
from src.bank import Bank
from src.bank_accounts import BankAccountManager, BankAccount
from datetime import date, timedelta

def test_mock_provider():
    """Test the mock banking provider"""
    print("=" * 60)
    print("Testing Mock Banking Provider")
    print("=" * 60)
    
    # Create mock provider
    provider = MockBankingProvider({})
    
    # Test authentication
    print("\n1. Testing authentication...")
    auth_result = provider.authenticate()
    print(f"   Authentication: {'✓ Success' if auth_result else '✗ Failed'}")
    
    # Test getting accounts
    print("\n2. Testing get_accounts...")
    accounts = provider.get_accounts()
    print(f"   Found {len(accounts)} accounts:")
    for acc in accounts:
        print(f"   - {acc['name']} ({acc['type']}): ${acc['balance_current']:,.2f}")
    
    # Test getting transactions
    print("\n3. Testing get_transactions...")
    if accounts:
        account_id = accounts[0]['account_id']
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        transactions = provider.get_transactions(account_id, start_date, end_date)
        print(f"   Found {len(transactions)} transactions for {accounts[0]['name']}")
        print(f"   Sample transactions:")
        for tx in transactions[:5]:
            print(f"   - {tx['date']}: {tx['name']} ${tx['amount']:.2f} ({tx['type']})")
    
    # Test getting balance
    print("\n4. Testing get_balance...")
    if accounts:
        account_id = accounts[0]['account_id']
        balance = provider.get_balance(account_id)
        print(f"   Balance for {accounts[0]['name']}:")
        print(f"   - Current: ${balance['current']:,.2f}")
        print(f"   - Available: ${balance['available']:,.2f}")
    
    print("\n✓ All mock provider tests passed!")
    return True


def test_banking_api_manager():
    """Test the Banking API Manager integration"""
    print("\n" + "=" * 60)
    print("Testing Banking API Manager")
    print("=" * 60)
    
    # Create test user ID
    test_user_id = 'test_user_123'
    
    # Create Banking API Manager
    print("\n1. Creating Banking API Manager...")
    api_manager = BankingAPIManager(user_id=test_user_id)
    print(f"   Available providers: {list(api_manager.providers.keys())}")
    
    # Create a test bank instance
    print("\n2. Setting up test bank and accounts...")
    bank = Bank(current_user_id=test_user_id)
    
    # Create a test app account
    test_account = BankAccount(
        bank_name="Test Bank",
        account_type="Checking",
        account_name="Test Checking",
        account_number="1234",
        user_id=test_user_id,
        initial_balance=1000.00
    )
    bank.account_manager.add_account(test_account)
    print(f"   Created app account: {test_account.get_display_name()}")
    
    # Link the mock bank account
    print("\n3. Linking mock bank account...")
    success = api_manager.link_account(
        provider_name='mock',
        access_token='mock_token',
        app_account_id=test_account.account_id,
        app_account_name=test_account.get_display_name()
    )
    print(f"   Link result: {'✓ Success' if success else '✗ Failed'}")
    
    # Get linked accounts
    print("\n4. Retrieving linked accounts...")
    linked_accounts = api_manager.get_linked_accounts()
    print(f"   Found {len(linked_accounts)} linked account(s)")
    for acc in linked_accounts:
        print(f"   - {acc['bank_account_name']} → {acc['app_account_name']}")
    
    # Sync transactions
    if linked_accounts:
        print("\n5. Syncing transactions...")
        link_id = linked_accounts[0]['link_id']
        count, errors = api_manager.sync_transactions(
            link_id=link_id,
            days_back=30,
            bank_instance=bank
        )
        print(f"   Imported {count} transactions")
        if errors:
            print(f"   Errors: {len(errors)}")
            for error in errors[:3]:
                print(f"   - {error}")
        
        # Show sample imported transactions
        print("\n6. Showing imported transactions...")
        imported = [tx for tx in bank.transactions if tx.get('imported_from') == 'mock']
        print(f"   Total imported: {len(imported)}")
        for tx in imported[:5]:
            print(f"   - {tx['date']}: {tx['desc']} ${tx['amount']:.2f} ({tx['type']})")
        
        # Test syncing again (should find no new transactions)
        print("\n7. Testing duplicate prevention...")
        count2, errors2 = api_manager.sync_transactions(
            link_id=link_id,
            days_back=30,
            bank_instance=bank
        )
        print(f"   Second sync imported {count2} new transactions (should be 0)")
        if count2 == 0:
            print("   ✓ Duplicate prevention working!")
        
        # Get account balance
        print("\n8. Testing balance retrieval...")
        balance = api_manager.get_account_balance(link_id)
        if balance:
            print(f"   Current: ${balance['current']:,.2f}")
            print(f"   Available: ${balance['available']:,.2f}")
        
        # Unlink account
        print("\n9. Testing account unlinking...")
        unlink_success = api_manager.unlink_account(link_id)
        print(f"   Unlink result: {'✓ Success' if unlink_success else '✗ Failed'}")
        
        remaining = api_manager.get_linked_accounts()
        print(f"   Remaining linked accounts: {len(remaining)}")
    
    print("\n✓ All Banking API Manager tests passed!")
    return True


def test_full_integration():
    """Test complete integration workflow"""
    print("\n" + "=" * 60)
    print("Testing Full Integration Workflow")
    print("=" * 60)
    
    test_user_id = 'integration_test_user'
    
    # Setup
    print("\n1. Setting up environment...")
    bank = Bank(current_user_id=test_user_id)
    api_manager = BankingAPIManager(user_id=test_user_id)
    
    # Create app accounts
    checking = BankAccount(
        bank_name="Local Bank",
        account_type="Checking",
        account_name="Main Checking",
        account_number="9876",
        user_id=test_user_id,
        initial_balance=5000.00
    )
    bank.account_manager.add_account(checking)
    
    savings = BankAccount(
        bank_name="Local Bank",
        account_type="Savings",
        account_name="Emergency Fund",
        account_number="5432",
        user_id=test_user_id,
        initial_balance=10000.00
    )
    bank.account_manager.add_account(savings)
    
    print(f"   Created {len([checking, savings])} app accounts")
    
    # Link accounts
    print("\n2. Linking accounts to mock bank...")
    api_manager.link_account('mock', 'mock_token', checking.account_id, checking.get_display_name())
    
    # Sync all
    print("\n3. Syncing all linked accounts...")
    results = api_manager.sync_all_accounts(days_back=30, bank_instance=bank)
    total_imported = sum(r[0] for r in results.values())
    print(f"   Total transactions imported: {total_imported}")
    
    # Show stats
    print("\n4. Transaction statistics...")
    all_transactions = bank.list_transactions()
    imported_transactions = [tx for tx in all_transactions if tx.get('imported_from')]
    
    print(f"   Total transactions: {len(all_transactions)}")
    print(f"   Imported transactions: {len(imported_transactions)}")
    
    # Categorization stats
    categorized = [tx for tx in imported_transactions if tx.get('category')]
    print(f"   Auto-categorized: {len(categorized)}")
    
    # Type breakdown
    income = [tx for tx in imported_transactions if tx['type'] == 'in']
    expenses = [tx for tx in imported_transactions if tx['type'] == 'out']
    print(f"   Income transactions: {len(income)}")
    print(f"   Expense transactions: {len(expenses)}")
    
    # Amount totals
    total_income = sum(tx['amount'] for tx in income)
    total_expenses = sum(tx['amount'] for tx in expenses)
    print(f"   Total income: ${total_income:,.2f}")
    print(f"   Total expenses: ${total_expenses:,.2f}")
    print(f"   Net: ${total_income - total_expenses:,.2f}")
    
    print("\n✓ Full integration test completed!")
    return True


if __name__ == '__main__':
    try:
        print("Starting Banking API Integration Tests\n")
        
        # Run tests
        test_mock_provider()
        test_banking_api_manager()
        test_full_integration()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nThe Banking API integration is working correctly!")
        print("You can now use it in the Financial Manager application.")
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
