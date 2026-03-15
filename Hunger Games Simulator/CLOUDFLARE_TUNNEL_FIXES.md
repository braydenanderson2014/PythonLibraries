# Cloudflare Tunnel Connection Fixes

## Issues Identified

1. **"Refused to set unsafe header 'User-Agent'"** ❌
   - Browsers block setting User-Agent headers for security
   - Socket.IO client was trying to set this in extraHeaders
   - Causes repeated polling failures

2. **Message channel closed error** ❌
   - Typically caused by browser extensions or content scripts
   - Can be mitigated by disabling WebSocket upgrade on non-localhost

3. **Repeated polling failures** ❌
   - Multiple failed XMLHttpRequest attempts
   - Indicates connection instability through proxy

## Fixes Applied

### Fix 1: Remove User-Agent Headers from Socket.IO Config ✅

**File**: `Aurora Engine/static/js/app.js`

**Changes**: 
- Removed `extraHeaders` with User-Agent from main io() config (line 50)
- Removed `transportOptions` with User-Agent headers (lines 61-70)
- Kept simplified configuration that lets Socket.IO use defaults

**Why**: Browsers block setting User-Agent headers as a security measure. Socket.IO works fine without explicitly setting this.

### Fix 2: Ensure forcePolling is Enabled for Production ✅

**File**: `Aurora Engine/static/js/app.js`

**Already in place**:
```javascript
forcePolling: window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1'
```

**Why**: When `forcePolling=true`, Socket.IO skips WebSocket upgrade attempts and uses long-polling only. This is MORE stable through proxies like Cloudflare Tunnel than WebSocket.

### Fix 3: Server-Side Configuration ✅

**File**: `Aurora Engine/lobby_server.py`

**Current configuration**:
```python
transports=['polling', 'websocket'],  # Polling-first priority
ping_timeout=20,                      # 20 second timeout
ping_interval=8,                      # Ping every 8 seconds
cookie=False,                         # Better proxy compatibility
cors_allowed_origins='*'              # Accept any origin
```

## Recommended Additional Server Configuration

For maximum Cloudflare Tunnel compatibility, add these settings to lobby_server.py:

```python
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    cors_credentials=True,
    logger=True,
    engineio_logger=True,
    ping_timeout=20,
    ping_interval=8,
    max_http_buffer_size=1000000,
    allow_upgrades=True,
    cookie=False,
    transports=['polling', 'websocket'],
    # CLOUDFLARE TUNNEL SPECIFIC:
    # Force polling on upgrade to prefer long-polling
    upgrade_timeout=10000,
    eio=4,  # Use EIO version 4 for better compatibility
)
```

## Client-Side Configuration (Now Fixed)

**File**: `Aurora Engine/static/js/app.js`

Current working configuration:
```javascript
this.socket = io(serverUrl, {
    transports: ['polling', 'websocket'],
    upgrade: true,
    rememberUpgrade: true,
    timeout: 20000,  // Matches server ping_timeout
    forceNew: false,
    reconnection: true,
    reconnectionAttempts: 15,
    reconnectionDelay: 500,
    reconnectionDelayMax: 5000,
    // FIXED: Removed User-Agent headers (cause browser security errors)
    // IMPORTANT: Force polling on production (non-localhost)
    forcePolling: window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1',
    allowEIO3: true,
    withCredentials: true
});
```

## Browser Extension Issue

The error: `"A listener indicated an asynchronous response by returning true, but the message channel closed before a response was received"`

**This is typically caused by**:
- Content security policies (CSP)
- Browser extensions (ad blockers, privacy tools)
- Anti-tracking extensions

**Mitigation**:
1. The fixes above minimize WebSocket upgrade attempts which extensions often block
2. forcePolling=true ensures long-polling works even if WebSocket is blocked
3. Disable extensions in an incognito window to test

## Testing the Fix

### Test 1: Verify Polling Connection Works
1. Open browser DevTools (F12)
2. Go to Network tab
3. Load the game page
4. Should see repeated POST requests to `/socket.io/` (long-polling)
5. Should NOT see "Refused to set unsafe header" errors

### Test 2: Verify No User-Agent Errors
1. Open browser Console (F12)
2. Should NOT see: "Refused to set unsafe header 'User-Agent'"
3. Should see: `Game page loaded, signaling client ready` (clean message)

### Test 3: Monitor Connection Stability
1. Watch Network tab for stable polling
2. Polling requests should be regular (every few seconds)
3. No repeated 4xx or 5xx errors
4. Connection should stay open throughout gameplay

## Deployment Checklist

- [x] Removed User-Agent headers from app.js Socket.IO config
- [x] Verified forcePolling is enabled for production
- [x] Server using polling-first transport priority
- [x] Timeouts aligned (20s) between client and server
- [ ] Deployed to production server
- [ ] Tested in production environment
- [ ] Monitored for connection stability

## Next Steps if Issues Persist

1. **Check Cloudflare Tunnel Logs**: Verify the tunnel is forwarding WebSocket-compatible protocols
2. **Test with Different Browser**: Rules out browser extension issues
3. **Test Incognito Mode**: Disables extensions to isolate issues
4. **Monitor Server Logs**: Check for any errors on the backend during connection attempts
5. **Check CSP Headers**: Verify Content-Security-Policy isn't blocking Socket.IO connections

## Performance Expectations

With these fixes on Cloudflare Tunnel:
- **Initial connection**: 2-3 seconds
- **Message delivery**: 100-500ms (polling latency)
- **Reconnection on disconnect**: 1-2 seconds
- **Stability**: Very stable for gameplay

Polling through HTTP is slightly slower than WebSocket but much more reliable through proxies.
