"""
Banking API Providers - Usage Examples

This module demonstrates how to use different banking API providers
with the Financial Manager application.
"""

from src.banking_api import BankingAPIManager
from datetime import datetime, date, timedelta


# ============================================================================
# Example 1: Setup and Configuration
# ============================================================================

def example_initialize_manager():
    """Initialize the banking API manager"""
    # Create manager for a specific user
    manager = BankingAPIManager(user_id="user_123")
    
    # Check available providers
    print("Available providers:", list(manager.providers.keys()))
    
    # Load current config
    print("Config:", manager.config)
    
    return manager


# ============================================================================
# Example 2: Mock Provider (Development/Testing)
# ============================================================================

def example_mock_provider():
    """Use the mock provider for testing"""
    manager = BankingAPIManager(user_id="dev_user")
    
    # Link mock account
    success = manager.link_account(
        provider_name='mock',
        app_account_id='checking_001',
        app_account_name='My Test Checking Account'
    )
    
    if success:
        print("✓ Successfully linked mock account")
        
        # View linked accounts
        linked = manager.get_linked_accounts()
        for account in linked:
            print(f"  - {account['bank_account_name']} ({account['provider']})")
            print(f"    Bank account: {account['bank_account_mask']}")
            print(f"    Type: {account['bank_account_type']}")
            print(f"    Linked: {account['linked_date']}")


# ============================================================================
# Example 3: Plaid Provider
# ============================================================================

def example_plaid_provider():
    """Use Plaid provider (requires Plaid API key)"""
    manager = BankingAPIManager(user_id="user_123")
    
    # First, configure Plaid credentials in banking_config.json
    # Then, get user's access token from Plaid OAuth flow
    
    plaid_access_token = "access_token_from_plaid_oauth"  # Replace with real token
    
    # Link account from Plaid
    success = manager.link_account(
        provider_name='plaid',
        app_account_id='plaid_acc_001',
        app_account_name='My Plaid-linked Bank Account',
        access_token=plaid_access_token
    )
    
    if success:
        print("✓ Successfully linked Plaid account")
        
        # List all linked accounts
        for account in manager.get_linked_accounts():
            print(f"\nAccount: {account['bank_account_name']}")
            print(f"  Bank: {account['bank_account_name']}")
            print(f"  Type: {account['bank_account_type']}")
            print(f"  Last 4: {account['bank_account_mask']}")
            print(f"  Last Synced: {account['last_sync'] or 'Never'}")


# ============================================================================
# Example 4: Finicity Provider
# ============================================================================

def example_finicity_provider():
    """Use Finicity provider (requires Finicity API key)"""
    manager = BankingAPIManager(user_id="user_456")
    
    # Configure Finicity in banking_config.json first
    # Then get customer ID from Finicity
    
    finicity_customer_id = "1234567890"  # Replace with real customer ID
    
    # Link account from Finicity
    success = manager.link_account(
        provider_name='finicity',
        app_account_id='finicity_acc_001',
        app_account_name='My Finicity-linked Account',
        customer_id=finicity_customer_id
    )
    
    if success:
        print("✓ Successfully linked Finicity account")
        
        # Get account details
        for account in manager.get_linked_accounts():
            if account['provider'] == 'finicity':
                print(f"\nFinicity Account Details:")
                print(f"  Customer ID: {account.get('customer_id')}")
                print(f"  Bank Account: {account['bank_account_name']}")


# ============================================================================
# Example 5: Stripe Provider
# ============================================================================

def example_stripe_provider():
    """Use Stripe provider for connected accounts"""
    manager = BankingAPIManager(user_id="business_user")
    
    # Configure Stripe API key in banking_config.json first
    
    # Link Stripe connected bank accounts
    success = manager.link_account(
        provider_name='stripe',
        app_account_id='stripe_acc_001',
        app_account_name='My Stripe Connected Account'
    )
    
    if success:
        print("✓ Successfully linked Stripe accounts")
        
        # List all Stripe accounts
        for account in manager.get_linked_accounts():
            if account['provider'] == 'stripe':
                print(f"\nStripe Account: {account['bank_account_name']}")
                print(f"  Mask: {account['bank_account_mask']}")
                print(f"  Type: {account['bank_account_type']}")


# ============================================================================
# Example 6: Open Banking Provider (TrueLayer, etc.)
# ============================================================================

def example_open_banking_provider():
    """Use Open Banking provider (TrueLayer, Yapstone, etc.)"""
    manager = BankingAPIManager(user_id="user_789")
    
    # Configure Open Banking in banking_config.json:
    # Set provider_type to 'truelayer', 'yapstone', etc.
    # Provide API credentials
    
    # Get user ID from Open Banking provider's OAuth flow
    open_banking_user_id = "user_from_open_banking_oauth"
    
    # Link account from Open Banking provider
    success = manager.link_account(
        provider_name='open_banking',
        app_account_id='ob_acc_001',
        app_account_name='My EU Bank Account',
        user_id=open_banking_user_id
    )
    
    if success:
        print("✓ Successfully linked Open Banking account")
        
        # List all Open Banking accounts
        for account in manager.get_linked_accounts():
            if account['provider'] == 'open_banking':
                print(f"\nOpen Banking Account: {account['bank_account_name']}")
                print(f"  User ID: {account.get('user_id')}")
                print(f"  Currency: {account.get('currency')}")


# ============================================================================
# Example 7: Syncing Transactions
# ============================================================================

def example_sync_transactions(manager, bank_instance):
    """Sync transactions from linked accounts"""
    
    # Get all linked accounts
    linked_accounts = manager.get_linked_accounts()
    
    if not linked_accounts:
        print("No linked accounts found")
        return
    
    # Sync transactions from each account
    for account in linked_accounts:
        link_id = account['link_id']
        print(f"\nSyncing from {account['bank_account_name']} ({account['provider']})...")
        
        # Sync last 30 days
        new_count, errors = manager.sync_transactions(
            link_id=link_id,
            days_back=30,
            bank_instance=bank_instance
        )
        
        # Report results
        if errors:
            print(f"  ⚠ Synced {new_count} transactions with {len(errors)} error(s):")
            for error in errors:
                print(f"    - {error}")
        else:
            print(f"  ✓ Successfully synced {new_count} new transactions")


# ============================================================================
# Example 8: Viewing Linked Accounts
# ============================================================================

def example_view_linked_accounts(manager):
    """View all linked accounts for current user"""
    
    linked_accounts = manager.get_linked_accounts()
    
    if not linked_accounts:
        print("No linked accounts")
        return
    
    print(f"\nLinked Accounts ({len(linked_accounts)} total):\n")
    
    for i, account in enumerate(linked_accounts, 1):
        print(f"{i}. {account['bank_account_name']}")
        print(f"   Provider: {account['provider']}")
        print(f"   Bank Account: {account['bank_account_mask']}")
        print(f"   Type: {account['bank_account_type']}")
        print(f"   App Account: {account['app_account_name']}")
        print(f"   Linked: {account['linked_date']}")
        print(f"   Last Sync: {account['last_sync'] or 'Never'}")
        print(f"   Auto Sync: {'Yes' if account['auto_sync'] else 'No'}")
        print(f"   Auto Categorize: {'Yes' if account['auto_categorize'] else 'No'}")
        print()


# ============================================================================
# Example 9: Unlinking Accounts
# ============================================================================

def example_unlink_account(manager):
    """Unlink a bank account"""
    
    linked_accounts = manager.get_linked_accounts()
    
    if not linked_accounts:
        print("No linked accounts to unlink")
        return
    
    # Show accounts and ask user to select
    print("Linked Accounts:")
    for i, account in enumerate(linked_accounts, 1):
        print(f"{i}. {account['bank_account_name']} ({account['provider']})")
    
    # For this example, unlink the first account
    account_to_unlink = linked_accounts[0]
    link_id = account_to_unlink['link_id']
    
    success = manager.unlink_account(link_id)
    
    if success:
        print(f"✓ Successfully unlinked {account_to_unlink['bank_account_name']}")
    else:
        print(f"✗ Failed to unlink account")


# ============================================================================
# Example 10: Configuring Providers
# ============================================================================

def example_configure_providers():
    """Configure banking providers programmatically"""
    
    manager = BankingAPIManager(user_id="admin_user")
    
    # Enable and configure Plaid
    manager.configure_provider(
        'plaid',
        enabled=True,
        client_id='your_plaid_client_id',
        secret='your_plaid_secret',
        environment='sandbox'
    )
    print("✓ Configured Plaid")
    
    # Enable and configure Finicity
    manager.configure_provider(
        'finicity',
        enabled=True,
        partner_id='your_partner_id',
        partner_secret='your_partner_secret',
        app_key='your_app_key'
    )
    print("✓ Configured Finicity")
    
    # Enable and configure Stripe
    manager.configure_provider(
        'stripe',
        enabled=True,
        api_key='sk_test_your_api_key'
    )
    print("✓ Configured Stripe")
    
    # Enable and configure Open Banking
    manager.configure_provider(
        'open_banking',
        enabled=True,
        provider_type='truelayer',
        client_id='your_client_id',
        client_secret='your_client_secret',
        base_url='https://api.truelayer.com'
    )
    print("✓ Configured Open Banking")


# ============================================================================
# Example 11: Multi-Provider Setup
# ============================================================================

def example_multi_provider_setup():
    """Setup and use multiple providers"""
    
    manager = BankingAPIManager(user_id="multi_provider_user")
    
    print("Setting up multiple providers...\n")
    
    # Link account from Plaid
    print("1. Linking Plaid account...")
    manager.link_account(
        provider_name='mock',
        app_account_id='account_1',
        app_account_name='Primary Checking'
    )
    
    # Link account from Finicity
    print("2. Linking Mock account...")
    manager.link_account(
        provider_name='mock',
        app_account_id='account_2',
        app_account_name='Savings Account'
    )
    
    # Show all linked accounts
    print("\n3. All linked accounts:")
    example_view_linked_accounts(manager)


# ============================================================================
# Example 12: Error Handling
# ============================================================================

def example_error_handling(manager, bank_instance):
    """Handle errors during sync operations"""
    
    linked_accounts = manager.get_linked_accounts()
    
    if not linked_accounts:
        print("Error: No linked accounts found")
        return
    
    # Sync with comprehensive error handling
    for account in linked_accounts:
        link_id = account['link_id']
        
        try:
            new_count, errors = manager.sync_transactions(
                link_id=link_id,
                days_back=30,
                bank_instance=bank_instance
            )
            
            # Check for errors
            if errors:
                print(f"Errors syncing {account['bank_account_name']}:")
                for error in errors:
                    print(f"  - {error}")
            
            # Check for no transactions
            if new_count == 0:
                print(f"No new transactions for {account['bank_account_name']}")
            else:
                print(f"Successfully synced {new_count} transactions")
                
        except Exception as e:
            print(f"Exception syncing {account['bank_account_name']}: {e}")


# ============================================================================
# Main Example Runner
# ============================================================================

if __name__ == "__main__":
    print("=== Banking API Providers - Usage Examples ===\n")
    
    # Initialize manager
    print("1. Initializing Banking API Manager...")
    manager = example_initialize_manager()
    print()
    
    # Use mock provider for demonstration
    print("2. Using Mock Provider (for testing)...")
    example_mock_provider()
    print()
    
    # View linked accounts
    print("3. Viewing Linked Accounts...")
    example_view_linked_accounts(manager)
    print()
    
    print("✓ Examples completed!")
    print("\nNote: For real providers (Plaid, Finicity, Stripe, Open Banking),")
    print("you'll need to configure API credentials in banking_config.json")
    print("and obtain user authentication tokens from each provider's OAuth flow.")
