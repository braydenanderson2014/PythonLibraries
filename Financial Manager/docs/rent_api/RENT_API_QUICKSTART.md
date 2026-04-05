# Quick Start - Rent Management API (Auth Edition)

## 30-Second Setup

```bash
# 1. Create an API user
cd "Python Projects/Financial Manager"
python src/rent_web_server_runner.py --create-user myapi:mypass

# 2. Start the server
python src/rent_web_server_runner.py --port 5000

# 3. In another terminal, test it
python -c "
import requests
import json

# Login
r = requests.post('http://localhost:5000/api/auth/login',
                  json={'username': 'myapi', 'password': 'mypass'})
token = r.json()['token']
print(f'✓ Logged in! Token: {token[:10]}...')

# Get tenants
r = requests.get('http://localhost:5000/api/tenants',
                 headers={'Authorization': f'Bearer {token}'})
print(f'✓ Found {len(r.json()[\"tenants\"])} tenants')
"
```

## What Changed?

**Old:** API tried to load RentTracker with `user_id=None` → Crashed ❌

**New:** API requires login first → Loads RentTracker per user → Works ✅

## New Endpoints

### Login (Public - No Auth)
```bash
POST /api/auth/login
Body: {"username": "myapi", "password": "mypass"}
Returns: {"token": "...", "expires_in_seconds": 3600}
```

### All Other Endpoints (Require Token)
```bash
GET /api/tenants
Header: Authorization: Bearer YOUR_TOKEN_HERE
```

## Command Reference

```bash
# Create user
python src/rent_web_server_runner.py --create-user USERNAME:PASSWORD

# Start server
python src/rent_web_server_runner.py --port 5000

# Start with debug
python src/rent_web_server_runner.py --port 5000 --debug

# Use different port
python src/rent_web_server_runner.py --port 8000
```

## Python Client

```python
from src.rent_web_client import create_client

client = create_client('http://localhost:5000')

# Login once
success, result = client.login('myapi', 'mypass')
if not success:
    exit(f"Login failed: {result}")

# Use API (client remembers token)
success, tenants = client.get_all_tenants()
success, tenant = client.get_tenant('T001')
success, disputes = client.get_all_disputes()
success, dispute = client.create_dispute(
    'T001',
    'payment_not_recorded',
    'Payment on 1/15 not recorded',
    1800.00
)
```

## Curl Examples

```bash
# 1. Login
TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"myapi","password":"mypass"}' | grep -o '"token":"[^"]*' | cut -d'"' -f4)

# 2. Use token
curl http://localhost:5000/api/tenants \
  -H "Authorization: Bearer $TOKEN"

curl http://localhost:5000/api/tenants/T001 \
  -H "Authorization: Bearer $TOKEN"

curl http://localhost:5000/api/info/dispute-types \
  -H "Authorization: Bearer $TOKEN"

# 3. Create dispute
curl -X POST http://localhost:5000/api/tenants/T001/disputes \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "dispute_type": "payment_not_recorded",
    "description": "Payment on 1/15 not recorded",
    "amount": 1800.00,
    "reference_month": "2026-01"
  }'

# 4. Logout (revoke token)
curl -X POST http://localhost:5000/api/auth/logout \
  -H "Authorization: Bearer $TOKEN"
```

## Desktop App Integration

```python
# In your main application startup:
import threading
from src.rent_web_server_runner import run_rent_web_server

# Start API server in background thread
api_thread = threading.Thread(
    target=run_rent_web_server,
    args=(5000, False),
    daemon=True
)
api_thread.start()

# Your existing desktop app code continues normally
self.rent_tracker = RentTracker(current_user_id=self.user_id)
# ... rest of app ...
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: No module named 'flask'` | `pip install flask flask-cors requests` |
| `Address already in use` | Use different port: `--port 8000` |
| `Non-API user attempted API login` | Account needs `api_only: true` flag (created with `--create-user`) |
| `Invalid or expired token` | Login again to get new token |
| Port working but can't connect | Check firewall, try `http://127.0.0.1:5000` instead of `localhost` |

## API Endpoints Summary

| Method | Endpoint | Public | Description |
|--------|----------|--------|-------------|
| POST | `/api/auth/login` | ✅ | Get token |
| GET | `/api/auth/verify` | ❌ | Verify token |
| POST | `/api/auth/logout` | ❌ | Revoke token |
| GET | `/api/health` | ✅ | Health check |
| GET | `/api/tenants` | ❌ | All tenants |
| GET | `/api/tenants/<id>` | ❌ | Specific tenant |
| GET | `/api/tenants/<id>/payment-summary` | ❌ | Payment info |
| GET | `/api/tenants/<id>/delinquency` | ❌ | Delinquency info |
| GET | `/api/tenants/<id>/monthly-breakdown` | ❌ | Monthly data |
| GET | `/api/tenants/<id>/export` | ❌ | Full export |
| GET | `/api/disputes` | ❌ | All disputes |
| GET | `/api/disputes/<id>` | ❌ | Specific dispute |
| GET | `/api/tenants/<id>/disputes` | ❌ | Tenant's disputes |
| POST | `/api/tenants/<id>/disputes` | ❌ | Create dispute |
| PUT | `/api/disputes/<id>/status` | ❌ | Update dispute |
| GET | `/api/info/dispute-types` | ❌ | Dispute types |
| GET | `/api/info/dispute-statuses` | ❌ | Dispute statuses |

## Files

- `src/rent_api_auth.py` - Authentication system (NEW)
- `src/rent_web_server.py` - Flask server with auth (UPDATED)
- `src/rent_web_server_runner.py` - Server launcher (UPDATED)
- `src/rent_web_client.py` - Python client
- `RENT_API_AUTHENTICATION.md` - Full documentation
- `API_ARCHITECTURE_UPDATE.md` - Architecture overview

## Key Concepts

1. **API-Only Users** - Special account flag prevents desktop app access
2. **Tokens** - Session tokens expire after 1 hour
3. **Per-Session RentTracker** - Each user gets their own instance
4. **No User Context at Startup** - Server starts without user data
5. **Request Authentication** - Every API request (except login/health) needs token

