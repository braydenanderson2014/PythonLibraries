# Rent Management API - Authentication Architecture

## Overview

The Rent Management API now uses **API-only user accounts** with session-based authentication. This solves the initialization problem by:

1. **No RentTracker at Startup** - Server starts without loading any tenant data
2. **User Authentication Required** - All data endpoints require valid login credentials
3. **Session Tokens** - Users receive tokens that expire after 1 hour
4. **Desktop/API Separation** - Desktop users cannot access API (and vice versa)

## Why This Design?

### Problem Solved
Previously, the API tried to initialize `RentTracker` with `user_id=None`, which failed because:
- `TenantManager` needs a valid user to load tenant data
- `RentTracker.__init__()` called `_initialize_notification_systems()` 
- This cascade caused initialization failures

### Solution
- API-only users have an `api_only: true` flag in their account
- Server only initializes AccountManager (lightweight, no user context needed)
- RentTracker is NOT loaded until after authentication
- Only API-only users can access the API

## Setup

### 1. Create an API User

```bash
python src/rent_web_server_runner.py --create-user apiuser:password123
```

Output:
```
✓ User created: apiuser
Account ID: fAlXr1HoSY
```

### 2. Start the Server

```bash
python src/rent_web_server_runner.py --port 5000
```

Server outputs:
```
[INFO] RentWebServer: Loading AccountManager for authentication...
[INFO] RentWebServer: AccountManager loaded successfully
[INFO] RentWebServer: Starting Rent Management Web Server on port 5000
[INFO] RentWebServer: Authentication required - RentTracker loaded per session
...
Running on http://127.0.0.1:5000
```

### 3. Login to Get Token

```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "apiuser", "password": "password123"}'
```

Response:
```json
{
  "status": "success",
  "token": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "fAlXr1HoSY",
  "username": "apiuser",
  "session_expires_in_seconds": 3600,
  "timestamp": "2026-01-19T17:26:29.123456"
}
```

### 4. Use Token for Protected Endpoints

```bash
# Get all tenants
curl http://localhost:5000/api/tenants \
  -H "Authorization: Bearer 550e8400-e29b-41d4-a716-446655440000"

# Get specific tenant
curl http://localhost:5000/api/tenants/T001 \
  -H "Authorization: Bearer 550e8400-e29b-41d4-a716-446655440000"

# Create dispute
curl -X POST http://localhost:5000/api/tenants/T001/disputes \
  -H "Authorization: Bearer 550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{
    "dispute_type": "payment_not_recorded",
    "description": "Payment made on 1/15 not showing",
    "amount": 1800.00,
    "reference_month": "2026-01"
  }'
```

## Endpoints

### Authentication (No Auth Required)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/auth/login` | Get authentication token |
| GET | `/api/health` | Health check |

### Protected Endpoints (Require Token)

**Tenant Status:**
- `GET /api/tenants` - All tenants
- `GET /api/tenants/<id>` - Specific tenant
- `GET /api/tenants/<id>/payment-summary` - Payment info
- `GET /api/tenants/<id>/delinquency` - Delinquency info
- `GET /api/tenants/<id>/monthly-breakdown` - Monthly details
- `GET /api/tenants/<id>/export` - Full data export

**Disputes:**
- `GET /api/disputes` - All disputes
- `GET /api/disputes/<id>` - Specific dispute
- `GET /api/tenants/<id>/disputes` - Tenant's disputes
- `POST /api/tenants/<id>/disputes` - Create dispute
- `PUT /api/disputes/<id>/status` - Update dispute status

**Info:**
- `GET /api/info/dispute-types` - Available dispute types
- `GET /api/info/dispute-statuses` - Available statuses

**Session:**
- `GET /api/auth/verify` - Verify token is valid
- `POST /api/auth/logout` - Revoke token

## How It Works

### Initialization Flow

```
1. Server Start
   ├─ Load AccountManager (just loads accounts.json)
   ├─ Initialize SessionManager (empty, no sessions yet)
   ├─ Create Flask app with authentication routes
   └─ Listen on port 5000

2. User POST /api/auth/login
   ├─ Verify username/password
   ├─ Check account has api_only=true flag
   ├─ Create session token
   └─ Return token

3. User GET /api/tenants with token
   ├─ Verify token is valid and not expired
   ├─ Load RentTracker(user_id) for this user
   ├─ Initialize RentStatusAPI(rent_tracker)
   ├─ Execute API method
   └─ Return data

4. Token Expires After 1 Hour
   ├─ User must login again
   └─ New RentTracker loaded for new session
```

### Key Differences from Original

**Before:**
- RentTracker loaded with `user_id=None` at startup ❌
- All endpoints available without auth
- One RentTracker shared by all requests

**After:**
- Server starts without RentTracker ✅
- RentTracker loaded PER authenticated user ✅
- Each session has its own RentTracker instance ✅
- Tokens expire automatically ✅

## Python Client Usage

```python
from src.rent_web_client import create_client

# Create client
client = create_client('http://localhost:5000')

# Login
success, response = client.login('apiuser', 'password123')
if success:
    print(f"Logged in! Token: {response['token']}")
    
    # Now use other methods
    success, tenants = client.get_all_tenants()
    if success:
        print(f"Found {len(tenants)} tenants")
else:
    print(f"Login failed: {response['error']}")
```

## User Management

### Create Multiple API Users

```bash
# User 1 - can view only
python src/rent_web_server_runner.py --create-user viewer:pass123

# User 2 - dispute handler
python src/rent_web_server_runner.py --create-user handler:pass456

# User 3 - admin
python src/rent_web_server_runner.py --create-user admin:pass789
```

### User Account Structure

```json
{
  "username": "apiuser",
  "account_id": "fAlXr1HoSY",
  "password_hash": "ad9507ff0f807b4593db43891c82aad76732e0a0de291b586e6e7b1cb0abde87",
  "details": {
    "role": "api_user",
    "api_only": true,
    "description": "API-only account for remote access"
  }
}
```

## Security Features

1. **Password Hashing** - Uses salted hash (PBKDF2)
2. **Token-Based** - No session cookies, just tokens
3. **Expiration** - Tokens expire after 1 hour by default
4. **API-Only Flag** - Desktop users cannot login to API
5. **CORS Enabled** - Can be called from web clients
6. **No RentTracker Exposure** - User never directly accesses RentTracker

## Session Management

### Active Sessions

```python
from src.rent_api_auth import SessionManager

session_manager = SessionManager()
sessions = session_manager.get_active_sessions()
# Returns dict of {token: {username, user_id, duration_seconds}}
```

### Token Timeout

Default: 1 hour (3600 seconds)

```python
# Change timeout when creating server
server = create_server(
    account_manager=am,
    ...
)
# Then modify:
server.session_manager.timeout_seconds = 7200  # 2 hours
```

### Manual Token Revocation

```python
# On logout
curl -X POST http://localhost:5000/api/auth/logout \
  -H "Authorization: Bearer TOKEN"
```

## Integration with Desktop App

The API can run **alongside** the desktop app without any conflicts:

```python
# In your main_application.py
def __init__(self):
    # Start web API in background
    import threading
    from src.rent_web_server_runner import run_rent_web_server
    
    api_thread = threading.Thread(
        target=run_rent_web_server,
        args=(5000, False),
        daemon=True
    )
    api_thread.start()
    
    # Desktop app continues normally
    self.rent_tracker = RentTracker(current_user_id=self.user_id)
    self.setup_ui()
    # ...
```

Benefits:
- ✅ Desktop app uses RentTracker normally
- ✅ Web API runs separately with auth
- ✅ No port conflicts
- ✅ Separate user contexts
- ✅ No modifications needed to existing UI code

## Troubleshooting

### "Non-API user attempted API login"
**Cause:** Account doesn't have `api_only: true` flag

**Solution:** Create account with `--create-user` flag, or manually edit accounts.json:
```json
"details": {
  "api_only": true
}
```

### "Invalid or expired token"
**Cause:** Token was invalid or 1 hour has passed

**Solution:** Login again with `/api/auth/login`

### "API not initialized" (Error 503)
**Cause:** Server is still loading (very unlikely)

**Solution:** Wait a moment and retry

### Port Already in Use
**Solution:** Use different port
```bash
python src/rent_web_server_runner.py --port 8000
```

## Files

```
src/
├── rent_api.py               # Core API logic (unchanged)
├── rent_web_server.py        # Flask server (now with auth routes)
├── rent_api_auth.py          # Authentication system (NEW)
├── rent_web_server_runner.py # Server launcher (updated for auth)
└── rent_web_client.py        # Python client (unchanged)
```

## Next Steps

1. ✅ Authentication system working
2. ✅ RentTracker initialized per session (when needed)
3. ⏳ Add RentTracker lazy initialization on first API call
4. ⏳ Add admin panel for user management
5. ⏳ Add request logging and analytics
6. ⏳ Add rate limiting per user
7. ⏳ Add JWT support for production

