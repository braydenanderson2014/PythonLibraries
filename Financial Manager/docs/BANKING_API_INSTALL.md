# Banking API Integration - Installation & Setup

## Quick Start

The banking API integration is now part of Financial Manager. Follow these steps to get started:

### 1. Check Installation

All necessary files are already included:
- ✅ `src/banking_api.py` - Core integration
- ✅ `ui/banking_api_widget.py` - UI interface
- ✅ `src/app_paths.py` - Updated with new paths
- ✅ `ui/financial_tracker.py` - Updated with Banking API tab

### 2. Dependencies

The banking API uses standard Python libraries already included with Financial Manager:

```bash
# Required (should already be installed)
PyQt6
requests
python-dateutil
```

For Plaid production use, install:
```bash
pip install plaid-python
```

### 3. First Run

1. **Start Financial Manager**:
   ```bash
   python main.py
   ```

2. **Navigate to Banking API Tab**:
   - Look for the "🏦 Banking API" tab
   - It will be next to "Net Worth" and "Bank Dashboards"

3. **Create a Bank Account First**:
   - Go to "Bank Dashboards" tab
   - Create at least one account (e.g., "Main Checking")
   - This is required before linking

### 4. Test with Mock Provider

The Mock provider is perfect for testing without real bank credentials:

1. In Banking API tab, click **"Link New Account"**
2. Select **"Mock"** from provider dropdown
3. Select which app account to link to
4. Click **"Link Account"**
5. You'll see 2 mock accounts linked (Checking & Savings)
6. Click **"Sync"** on any account
7. Choose days to sync (e.g., 30)
8. Transactions will import automatically!

### 5. View Imported Transactions

1. Go to **"Transactions"** tab
2. You'll see transactions with:
   - Descriptions like "Grocery Store", "Gas Station", "Salary Deposit"
   - Auto-assigned categories
   - Date, amount, and type
3. These are marked as imported from the banking API

### 6. Run Tests (Optional)

Verify everything works:

```bash
cd "Python Projects/Financial Manager"
python test_banking_api.py
```

Expected output:
```
✓ ALL TESTS PASSED!
The Banking API integration is working correctly!
```

## Configuration Files

The system creates these files automatically:

### `resources/banking_api_config.json`
Provider credentials and settings:
```json
{
  "providers": {
    "plaid": {
      "enabled": false,
      "client_id": "",
      "secret": "",
      "environment": "sandbox"
    },
    "mock": {
      "enabled": true
    }
  }
}
```

### `resources/linked_bank_accounts.json`
Linked account information (created automatically)

## Using Plaid (Optional)

For real bank integration:

1. See [PLAID_SETUP_GUIDE.md](PLAID_SETUP_GUIDE.md) for detailed instructions
2. Get credentials from https://dashboard.plaid.com
3. Update `banking_api_config.json` with your credentials
4. Follow Plaid Link flow to authenticate
5. Link accounts using access tokens

## Features Available Now

✅ **Link Accounts** - Connect real or mock banks
✅ **Sync Transactions** - Import transaction history
✅ **Auto-Categorize** - Automatic category assignment
✅ **Duplicate Prevention** - No duplicate imports
✅ **Balance Checking** - View account balances
✅ **Multiple Accounts** - Link multiple banks
✅ **User Isolation** - Each user has separate linked accounts

## Common Workflows

### Import Last Month's Transactions

1. Link your account (mock or real)
2. Click "Sync"
3. Enter "30" for days back
4. Wait for import to complete
5. Review in Transactions tab

### Link Multiple Banks

1. Create multiple app accounts (e.g., "Chase Checking", "Bank of America Savings")
2. Link each one separately
3. Use "Sync All Accounts" to sync everything at once

### Set Up Automatic Categorization

1. When linking an account, ensure "Auto-categorize" is enabled (default)
2. Imported transactions will use bank-provided categories
3. You can still manually adjust categories later
4. Transaction rules will also apply

## Troubleshooting

### Banking API Tab Not Showing

- Make sure you're running the updated version
- Check that `ui/banking_api_widget.py` exists
- Restart the application

### Can't Link Account

- Make sure you've created at least one bank account first
- Go to "Bank Dashboards" → Create a new account
- Then try linking again

### No Transactions Import

- Check that the date range has transactions
- For mock provider, it always generates some
- For Plaid, check that authentication was successful

### Import Shows 0 New Transactions

- This is normal if you've already synced
- Duplicate prevention is working
- Try extending the date range

## Directory Structure

```
Financial Manager/
├── src/
│   ├── banking_api.py           ← Core integration
│   ├── bank.py                  ← Updated with external_id support
│   ├── app_paths.py             ← Updated with new paths
│   └── ...
├── ui/
│   ├── banking_api_widget.py    ← Banking UI
│   ├── financial_tracker.py     ← Updated with tab
│   └── ...
├── resources/
│   ├── banking_api_config.json  ← Auto-created
│   └── linked_bank_accounts.json ← Auto-created
├── test_banking_api.py          ← Test suite
├── BANKING_API_INTEGRATION.md   ← Full documentation
├── PLAID_SETUP_GUIDE.md         ← Plaid setup
└── BANKING_API_SUMMARY.md       ← Feature summary
```

## Next Steps

1. ✅ **Test with Mock Provider** - Verify it works
2. ✅ **Explore Features** - Try all sync options
3. ✅ **Check Categorization** - See how it auto-categorizes
4. ✅ **Review Documentation** - Read full integration guide
5. ⭕ **Set Up Plaid** - When ready for real banks (optional)

## Getting Help

- **Full Documentation**: `BANKING_API_INTEGRATION.md`
- **Plaid Setup**: `PLAID_SETUP_GUIDE.md`
- **Test Suite**: Run `python test_banking_api.py`
- **Summary**: `BANKING_API_SUMMARY.md`

## Video Tutorial (Coming Soon)

A video walkthrough will be available showing:
- Linking a mock account
- Syncing transactions
- Viewing imported data
- Setting up Plaid

## Feedback

If you encounter issues or have suggestions:
1. Check the troubleshooting section
2. Review the documentation
3. Run the test suite
4. File an issue with details

---

**Status**: ✅ Fully Functional - Ready to Use!

Start with the Mock provider to test, then move to Plaid when ready for real bank integration.
