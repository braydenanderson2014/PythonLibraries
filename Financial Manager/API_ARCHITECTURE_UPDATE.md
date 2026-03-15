# Rent API Architecture Update - Summary

## Problem

The original design had a critical architectural flaw:

```python
# OLD: rent_web_server_runner.py
rent_tracker = RentTracker()  # ❌ Initialized with user_id=None
server = create_server(rent_tracker)
server.run()
```

**Why it failed:**
- `RentTracker.__init__()` → `TenantManager(user_id=None)`
- `TenantManager.__init__()` → tries to load tenants without user context
- `_path_exists` gets `None` instead of a valid path
- **Result:** Server crashed on startup

## Solution: API-Only User Accounts

Instead of trying to initialize RentTracker with no user, we now:

1. **Create API-only user accounts** - Each has an `api_only: true` flag
2. **Require authentication** - All data endpoints need a valid token
3. **Load RentTracker per session** - Only after user authenticates
4. **Session-based access** - Users get tokens that expire after 1 hour

```python
# NEW: rent_web_server_runner.py
account_manager = AccountManager()  # ✅ No user context needed
server = create_server(account_manager=account_manager, rent_tracker=None)
server.run()

# Later, when user sends POST /api/auth/login:
# 1. Verify username/password
# 2. Create session token
# 3. On next request with token:
#    - Verify token
#    - Load RentTracker(user_id) for THAT session
#    - Execute API method
#    - Return data
```

## Key Changes

### 1. New Authentication Module

**File:** `src/rent_api_auth.py`

```python
# SessionManager - manages tokens and expiration
session = session_manager.create_session(user_id, username)
# Returns: {'token': '...', 'user_id': '...', 'created_at': ..., ...}

# RentAPIAuthenticator - handles login
result = authenticator.authenticate_user(username, password)
# Returns: {'success': True/False, 'token': '...', ...}
```

### 2. Updated Flask Server

**File:** `src/rent_web_server.py`

```python
# Authentication endpoints
POST   /api/auth/login      # No auth required - get token
GET    /api/auth/verify     # Auth required - verify token valid
POST   /api/auth/logout     # Auth required - revoke token

# All other endpoints now have @require_auth decorator
@require_auth
@app.route('/api/tenants')
def get_all_tenants():
    # Token already verified by decorator
    # request.current_user contains session data
```

### 3. Updated Server Runner

**File:** `src/rent_web_server_runner.py`

```python
# NEW: Create API users
python src/rent_web_server_runner.py --create-user username:password

# Server doesn't load RentTracker at startup
server = create_server(
    account_manager=account_manager,
    rent_tracker=None,  # Important: None, not RentTracker()
    ...
)
```

## Flow Diagram

```
┌─────────────────────────────────────────────────────────┐
│  1. SERVER STARTUP                                      │
├─────────────────────────────────────────────────────────┤
│  ✓ Load AccountManager (accounts.json only)             │
│  ✓ Initialize SessionManager (empty)                    │
│  ✓ Create Flask app with auth routes                    │
│  ✗ DO NOT load RentTracker                              │
│  → Server ready to accept requests                      │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│  2. USER LOGIN (POST /api/auth/login)                   │
├─────────────────────────────────────────────────────────┤
│  username=apiuser, password=password123                 │
│  → Verify credentials                                   │
│  → Check api_only=true                                  │
│  → Create session token                                 │
│  ← Return token to client                               │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│  3. PROTECTED REQUEST (GET /api/tenants)                │
├─────────────────────────────────────────────────────────┤
│  Authorization: Bearer TOKEN123                         │
│  → Verify token is valid & not expired                  │
│  → Load RentTracker(this_user_id)  ← LAZY LOAD         │
│  → Initialize RentStatusAPI(rent_tracker)               │
│  → Execute get_all_tenants_status()                     │
│  ← Return tenant data                                   │
│  → RentTracker stays in memory for this session         │
└─────────────────────────────────────────────────────────┘
                            ↓
          Token expires after 1 hour
          User must login again for new token
```

## Benefits

| Aspect | Before | After |
|--------|--------|-------|
| **Startup** | Crashes with None path | ✅ Starts successfully |
| **User Context** | None (no user) | ✅ Per-user context via token |
| **RentTracker** | Loaded always (breaks) | ✅ Loaded per session (lazy) |
| **Security** | No authentication | ✅ Token-based auth |
| **Expiration** | N/A (no users) | ✅ 1-hour token timeout |
| **Desktop Conflict** | Shared RentTracker | ✅ Separate instances per session |
| **Scalability** | Single RentTracker | ✅ Multiple concurrent sessions |

## User Workflow

### For Admin (Setting Up)

```bash
# 1. Create API users
python src/rent_web_server_runner.py --create-user viewer:pass123
python src/rent_web_server_runner.py --create-user admin:pass456

# 2. Start server
python src/rent_web_server_runner.py --port 5000
```

### For API Client (Using API)

```bash
# 1. Login
curl -X POST http://localhost:5000/api/auth/login \
  -d '{"username":"viewer","password":"pass123"}'
# Returns: {"token":"abcd1234..."}

# 2. Use token for all requests
curl http://localhost:5000/api/tenants \
  -H "Authorization: Bearer abcd1234..."

# 3. When token expires, login again
```

## Code Integration

### Existing Desktop App (No Changes Needed)

```python
# main_application.py - existing code works as-is
class MainWindow(QMainWindow):
    def __init__(self):
        # Desktop app uses its own RentTracker
        self.rent_tracker = RentTracker(current_user_id=self.logged_in_user)
        # ...
        
        # OPTIONALLY: Start API in background
        # (doesn't interfere with desktop app)
        import threading
        from src.rent_web_server_runner import run_rent_web_server
        
        api_thread = threading.Thread(
            target=run_rent_web_server,
            args=(5000, False),
            daemon=True
        )
        api_thread.start()
```

### Web Client (Using Python)

```python
from src.rent_web_client import create_client

client = create_client('http://localhost:5000')
success, response = client.login('viewer', 'pass123')

if success:
    token = response['token']
    client.token = token  # Client remembers token
    
    # Now use API
    success, tenants = client.get_all_tenants()
    success, disputes = client.get_all_disputes()
```

## Files Modified/Created

### New Files
- ✅ `src/rent_api_auth.py` - Authentication system

### Modified Files
- ✅ `src/rent_web_server.py` - Added auth routes and @require_auth decorator
- ✅ `src/rent_web_server_runner.py` - Changed initialization flow
- ✅ `RENT_API_AUTHENTICATION.md` - Full auth documentation

### Unchanged Files
- ✅ `src/rent_api.py` - Core API logic (no changes needed)
- ✅ `src/rent_web_client.py` - Client library (works with new auth)
- ✅ `Python Projects/` desktop app - Works normally

## Testing Checklist

- [ ] Server starts without errors
- [ ] Create API user: `--create-user test:test123`
- [ ] Health endpoint works: `GET /api/health`
- [ ] Login endpoint works: `POST /api/auth/login`
- [ ] Protected endpoint rejects without token (401)
- [ ] Protected endpoint works with token
- [ ] Token expires after 1 hour (or manually login again)
- [ ] Desktop app still works normally
- [ ] Multiple users can login concurrently

## Next Iteration

### Immediate (Working)
- ✅ Authentication system with tokens
- ✅ Session management with expiration
- ✅ API-only user flag support
- ✅ Protected endpoints with @require_auth

### Near Future
- ⏳ Lazy load RentTracker only on first API call (not on login)
- ⏳ Admin endpoint to list/revoke active sessions
- ⏳ Rate limiting per user
- ⏳ Request logging with user attribution

### Later
- ⏳ JWT tokens for better security
- ⏳ OAuth2 support
- ⏳ Admin dashboard
- ⏳ API usage analytics

## Migration Guide

If you have existing code using the old API:

### Old Code (Will Not Work)
```python
from src.rent_web_server_runner import run_rent_web_server
# This still works, but expects tenant data without login
run_rent_web_server(port=5000)
```

### New Code (Required)
```python
from src.rent_web_server_runner import run_rent_web_server, create_api_user

# 1. Create API user first
create_api_user('apiuser', 'password123')

# 2. Start server
run_rent_web_server(port=5000)

# 3. Login to get token
# POST /api/auth/login with username/password

# 4. Use token for all requests
# All endpoints now require: Authorization: Bearer TOKEN
```

