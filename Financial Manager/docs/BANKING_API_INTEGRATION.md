# Banking API Integration

## Overview

The Financial Manager now includes banking API integration that allows you to:
- Link real bank accounts to your Financial Manager app accounts
- Automatically import transactions from your bank
- Keep your financial data synchronized
- Auto-categorize transactions based on bank data

## Supported Providers

### 1. Plaid (Production Ready)
[Plaid](https://plaid.com/) is a leading banking API service that connects to thousands of financial institutions.

**Features:**
- Connect to 12,000+ financial institutions
- Real-time balance checking
- Transaction history import
- Categorization data
- Secure OAuth-based authentication

**Setup:**
1. Sign up for a Plaid account at https://dashboard.plaid.com/signup
2. Get your `client_id` and `secret` from the Plaid Dashboard
3. Configure in Financial Manager settings
4. Use Plaid Link to authenticate with your bank
5. Exchange public token for access token
6. Link the account in Financial Manager

### 2. Mock Provider (Testing)
A mock banking provider for testing without real credentials.

**Features:**
- Generates sample transactions
- Multiple test accounts
- No external dependencies
- Perfect for development and testing

**Setup:**
Enabled by default - no configuration needed!

## Architecture

### Components

1. **banking_api.py** - Core integration module
   - `BankingAPIProvider` - Base class for banking providers
   - `PlaidProvider` - Plaid API implementation
   - `MockBankingProvider` - Mock provider for testing
   - `BankingAPIManager` - Manages linked accounts and syncing

2. **banking_api_widget.py** - UI component
   - Link/unlink bank accounts
   - Sync transactions
   - View linked account status
   - Progress tracking

3. **Configuration Files**
   - `banking_api_config.json` - Provider credentials and settings
   - `linked_bank_accounts.json` - Linked account information

### Data Flow

```
┌─────────────────┐
│  Banking API    │
│  (Plaid/Mock)   │
└────────┬────────┘
         │
         │ Get Transactions
         ▼
┌─────────────────┐
│ BankingAPI      │
│ Manager         │
└────────┬────────┘
         │
         │ Import & Transform
         ▼
┌─────────────────┐
│ Financial       │
│ Manager Bank    │
│ Instance        │
└─────────────────┘
```

## Usage Guide

### Linking a Bank Account

1. Navigate to the **🏦 Banking API** tab
2. Click **"Link New Account"**
3. Select your banking provider (Mock or Plaid)
4. If using Plaid:
   - Complete the Plaid Link flow in a separate window
   - Exchange the public token for an access token
   - Paste the access token
5. Select which app account to link to
6. Click **"Link Account"**

### Syncing Transactions

#### Manual Sync (Single Account)
1. In the Banking API tab, find your linked account
2. Click the **"Sync"** button for that account
3. Choose how many days back to sync (default: 30 days)
4. Wait for sync to complete
5. Review imported transactions in the Transactions tab

#### Automatic Sync (All Accounts)
1. Click **"Sync All Accounts"**
2. Choose sync period
3. All linked accounts will sync automatically
4. View summary of imported transactions

### Managing Linked Accounts

- **View Status**: See when each account was last synced
- **Unlink**: Remove the connection (doesn't delete existing transactions)
- **Refresh**: Reload the linked accounts list

## Transaction Mapping

When transactions are imported from the bank:

| Bank Field | Financial Manager Field | Notes |
|------------|------------------------|-------|
| transaction_id | external_id | For deduplication |
| account_id | account_id | Mapped to linked app account |
| amount | amount | Converted to positive |
| date | date | Transaction date |
| name/merchant_name | desc | Transaction description |
| category | category | Auto-categorized if enabled |
| type (debit/credit) | type (in/out) | Income vs expense |

### Deduplication

The system prevents duplicate imports by:
1. Storing `external_id` (provider + transaction_id)
2. Checking for existing external_id before importing
3. Only new transactions are added

## Configuration

### Plaid Configuration

Edit `resources/banking_api_config.json`:

```json
{
  "providers": {
    "plaid": {
      "enabled": true,
      "client_id": "your_client_id_here",
      "secret": "your_secret_here",
      "environment": "sandbox"
    }
  }
}
```

**Environments:**
- `sandbox` - Testing with fake data
- `development` - Real data, limited institutions
- `production` - Full access (requires approval)

### Auto-Categorization

When linking an account, you can enable auto-categorization:
- Uses category data from the bank
- Maps to Financial Manager categories
- Can be manually adjusted later
- Rule-based categorization still applies

## Security Considerations

### Data Storage

- **Access Tokens**: Stored locally in `linked_bank_accounts.json`
- **Encryption**: Consider encrypting sensitive files
- **File Permissions**: Ensure proper access restrictions

### Best Practices

1. **Use Environment Variables** for production credentials
2. **Enable 2FA** on your Plaid account
3. **Regularly Rotate** access tokens
4. **Monitor** linked account activity
5. **Audit** imported transactions

### Plaid Security Features

- OAuth 2.0 authentication
- End-to-end encryption
- Bank-grade security
- No storage of bank credentials
- Token-based access

## Troubleshooting

### "No accounts found from provider"
- **Mock**: Should work immediately
- **Plaid**: Check that access token is valid and not expired

### "Failed to fetch transactions"
- Check internet connection
- Verify API credentials are correct
- Check Plaid environment setting
- Review error logs

### Duplicate Transactions
- Should not occur due to external_id checking
- If it does, check that external_id is being stored
- May need to manually delete duplicates

### Import Shows 0 Transactions
- Check date range (may be no transactions in that period)
- Verify bank account has transactions
- Check that account is linked correctly

## Development

### Adding a New Provider

1. Create a new provider class extending `BankingAPIProvider`:

```python
class NewProvider(BankingAPIProvider):
    def authenticate(self) -> bool:
        # Implement authentication
        pass
    
    def get_accounts(self) -> List[Dict[str, Any]]:
        # Get accounts
        pass
    
    def get_transactions(self, account_id, start_date, end_date):
        # Fetch transactions
        pass
    
    def get_balance(self, account_id):
        # Get balance
        pass
```

2. Register in `BankingAPIManager._initialize_providers()`
3. Add configuration to settings
4. Update UI to support new provider

### Testing

Use the Mock provider for testing:

```python
from src.banking_api import BankingAPIManager

# Create manager
api_manager = BankingAPIManager(user_id='test_user')

# Link mock account
api_manager.link_account(
    provider_name='mock',
    access_token='mock_token',
    app_account_id='your_account_id',
    app_account_name='Test Account'
)

# Sync transactions
count, errors = api_manager.sync_transactions(
    link_id='link_id_from_above',
    days_back=30,
    bank_instance=bank
)

print(f"Imported {count} transactions")
```

## API Reference

### BankingAPIManager

#### Methods

**`link_account(provider_name, access_token, app_account_id, app_account_name)`**
Link a bank account to an app account.

**`unlink_account(link_id)`**
Unlink a bank account.

**`sync_transactions(link_id, days_back, bank_instance)`**
Sync transactions from a linked account.

**`sync_all_accounts(days_back, bank_instance)`**
Sync all linked accounts.

**`get_linked_accounts()`**
Get all linked accounts for current user.

**`get_account_balance(link_id)`**
Get current balance for a linked account.

**`configure_provider(provider_name, **credentials)`**
Configure a banking provider with credentials.

### BankingAPIProvider (Abstract)

Base class for banking providers.

**Required Methods:**
- `authenticate()` - Authenticate with API
- `get_accounts()` - Retrieve accounts
- `get_transactions(account_id, start_date, end_date)` - Get transactions
- `get_balance(account_id)` - Get account balance

## Future Enhancements

- [ ] Scheduled automatic syncing
- [ ] Balance reconciliation
- [ ] Transaction categorization suggestions
- [ ] Support for investment accounts
- [ ] Credit card payment tracking
- [ ] Multi-currency support
- [ ] Webhook notifications
- [ ] Additional provider support (Yodlee, Open Banking, etc.)

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review Plaid documentation: https://plaid.com/docs/
3. Check application logs
4. File an issue on GitHub

## License

Part of the Financial Manager application.
