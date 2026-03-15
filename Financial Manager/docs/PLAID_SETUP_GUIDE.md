# Plaid Setup Guide

This guide walks you through setting up Plaid for production use with the Financial Manager.

## Step 1: Create Plaid Account

1. Go to https://dashboard.plaid.com/signup
2. Sign up for a free account
3. Verify your email
4. Complete the onboarding questionnaire

## Step 2: Get API Credentials

1. Log into Plaid Dashboard
2. Go to **Team Settings** → **Keys**
3. Copy your:
   - **client_id**
   - **sandbox secret** (for testing)
   - **development secret** (for real data testing)
   - **production secret** (for live use)

## Step 3: Configure Financial Manager

Edit `resources/banking_api_config.json`:

```json
{
  "providers": {
    "plaid": {
      "enabled": true,
      "client_id": "YOUR_CLIENT_ID_HERE",
      "secret": "YOUR_SECRET_HERE",
      "environment": "sandbox"
    },
    "mock": {
      "enabled": true
    }
  }
}
```

**Environments:**
- `sandbox` - Fake data, instant approval (use for testing)
- `development` - Real data, limited institutions (use for development)
- `production` - Full access (requires Plaid approval)

## Step 4: Implement Plaid Link (Web Interface)

Plaid Link is a web-based flow for users to connect their banks. You'll need to integrate this separately.

### Option A: Simple HTML/JavaScript Implementation

Create `plaid_link.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Connect Bank Account</title>
    <script src="https://cdn.plaid.com/link/v2/stable/link-initialize.js"></script>
</head>
<body>
    <h1>Connect Your Bank Account</h1>
    <button id="link-button">Connect Bank</button>
    
    <script>
        // Get link token from your backend
        fetch('/api/create_link_token', {
            method: 'POST',
        })
        .then(response => response.json())
        .then(data => {
            const linkToken = data.link_token;
            
            // Initialize Plaid Link
            const handler = Plaid.create({
                token: linkToken,
                onSuccess: (public_token, metadata) => {
                    // Send public_token to backend to exchange for access_token
                    fetch('/api/exchange_token', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            public_token: public_token
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        alert('Bank connected! Access Token: ' + data.access_token);
                        // Now use this access_token in Financial Manager
                    });
                },
                onExit: (err, metadata) => {
                    if (err != null) {
                        console.error('Plaid Link error:', err);
                    }
                }
            });
            
            document.getElementById('link-button').onclick = () => {
                handler.open();
            };
        });
    </script>
</body>
</html>
```

### Option B: Python Flask Backend

Create a simple Flask server to handle Plaid Link flow:

```python
from flask import Flask, request, jsonify
import plaid
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.products import Products
from plaid.model.country_code import CountryCode

app = Flask(__name__)

# Configure Plaid client
configuration = plaid.Configuration(
    host=plaid.Environment.Sandbox,  # Use Sandbox for testing
    api_key={
        'clientId': 'YOUR_CLIENT_ID',
        'secret': 'YOUR_SANDBOX_SECRET'
    }
)
api_client = plaid.ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)

@app.route('/api/create_link_token', methods=['POST'])
def create_link_token():
    """Create a link token for Plaid Link"""
    try:
        request = LinkTokenCreateRequest(
            products=[Products("transactions")],
            client_name="Financial Manager",
            country_codes=[CountryCode('US')],
            language='en',
            user={
                'client_user_id': 'user-id-here'
            }
        )
        response = client.link_token_create(request)
        return jsonify(response.to_dict())
    except plaid.ApiException as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/exchange_token', methods=['POST'])
def exchange_token():
    """Exchange public token for access token"""
    public_token = request.json['public_token']
    try:
        exchange_request = ItemPublicTokenExchangeRequest(
            public_token=public_token
        )
        response = client.item_public_token_exchange(exchange_request)
        access_token = response['access_token']
        return jsonify({'access_token': access_token})
    except plaid.ApiException as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(port=5000, debug=True)
```

### Install Plaid Python Library

```bash
pip install plaid-python
```

## Step 5: Get Access Token

After implementing Plaid Link:

1. Run your web server/app
2. User clicks "Connect Bank"
3. Plaid Link opens
4. User selects their bank
5. User enters credentials
6. Plaid returns public_token
7. Exchange public_token for access_token
8. Copy the access_token

## Step 6: Link Account in Financial Manager

1. Open Financial Manager
2. Go to **Banking API** tab
3. Click **Link New Account**
4. Select **Plaid** provider
5. Paste the **access_token**
6. Select which app account to link to
7. Click **Link Account**

## Step 7: Sync Transactions

1. Click **Sync** button for the linked account
2. Choose sync period (e.g., 30 days)
3. Wait for transactions to import
4. View imported transactions in Transactions tab

## Testing with Sandbox

Plaid's Sandbox environment uses test credentials:

**Test Bank Login:**
- Username: `user_good`
- Password: `pass_good`
- MFA: `1234`

These credentials work with any bank in Sandbox mode.

## Production Checklist

Before going to production:

- [ ] Apply for production access (Plaid Dashboard → Production Access)
- [ ] Update environment to `production` in config
- [ ] Use production secret key
- [ ] Implement secure token storage
- [ ] Add error handling
- [ ] Set up monitoring
- [ ] Test with real accounts
- [ ] Review security best practices
- [ ] Implement token rotation
- [ ] Add user notifications

## Security Best Practices

1. **Never commit secrets to version control**
   ```bash
   # Add to .gitignore
   resources/banking_api_config.json
   ```

2. **Use environment variables in production**
   ```python
   import os
   config['plaid']['client_id'] = os.environ.get('PLAID_CLIENT_ID')
   config['plaid']['secret'] = os.environ.get('PLAID_SECRET')
   ```

3. **Encrypt sensitive files**
   ```bash
   # Encrypt config file
   gpg -c resources/banking_api_config.json
   ```

4. **Rotate tokens regularly**
   - Set expiration on access tokens
   - Re-authenticate periodically
   - Monitor for suspicious activity

5. **Use HTTPS only**
   - All API calls over HTTPS
   - Secure your backend
   - Use SSL certificates

## Troubleshooting

### "INVALID_CREDENTIALS" Error
- Check that client_id and secret are correct
- Verify environment matches (sandbox/development/production)
- Ensure credentials are for the right environment

### "INVALID_ACCESS_TOKEN" Error
- Access token may have expired
- Need to re-authenticate with Plaid Link
- Generate new access token

### "ITEM_LOGIN_REQUIRED" Error
- User needs to re-authenticate with their bank
- Bank may have changed login requirements
- Use Plaid Link Update mode

### No Transactions Returned
- Check date range
- Verify account has transactions
- Some banks have delays (up to 24 hours)
- Check Plaid Dashboard for status

## Rate Limits

Plaid has rate limits:

| Environment | Requests/Second | Requests/Day |
|-------------|----------------|--------------|
| Sandbox     | 10             | Unlimited    |
| Development | 10             | 1,000        |
| Production  | 40             | 500,000      |

## Costs

Plaid pricing (as of 2024):

- **Development**: Free for testing
- **Production**: Pay per connected account
  - Starter: $0.25-$0.50 per connected account/month
  - Volume discounts available
  - See https://plaid.com/pricing/ for details

## Support Resources

- **Plaid Documentation**: https://plaid.com/docs/
- **API Reference**: https://plaid.com/docs/api/
- **Community**: https://community.plaid.com/
- **Support**: support@plaid.com
- **Status Page**: https://status.plaid.com/

## Alternative: Using Mock Provider

For testing without Plaid setup:

1. Use the built-in Mock provider
2. No credentials needed
3. Generates realistic test data
4. Perfect for development
5. Switch to Plaid when ready for production

```python
# Just link with mock provider
api_manager.link_account(
    provider_name='mock',
    access_token='mock_token',  # Any string works
    app_account_id='your_account_id',
    app_account_name='Your Account'
)
```

## Next Steps

Once Plaid is working:

1. ✅ Test with Sandbox
2. ✅ Verify transactions import correctly
3. ✅ Check categorization
4. ✅ Test duplicate prevention
5. ✅ Apply for production access
6. ✅ Update to production environment
7. ✅ Deploy to users
8. ✅ Monitor usage and errors

## Quick Start (Sandbox)

For immediate testing:

1. Get sandbox credentials from Plaid
2. Update config with sandbox settings
3. Run `test_banking_api.py` (uses mock, but you can modify)
4. Or use this quick script:

```python
from src.banking_api import PlaidProvider

provider = PlaidProvider({
    'client_id': 'YOUR_CLIENT_ID',
    'secret': 'YOUR_SANDBOX_SECRET',
    'environment': 'sandbox'
})

# Test authentication
if provider.authenticate():
    print("✓ Plaid configured correctly!")
else:
    print("✗ Check your credentials")
```

---

**Remember**: Start with Sandbox, test thoroughly, then move to production after Plaid approval.
