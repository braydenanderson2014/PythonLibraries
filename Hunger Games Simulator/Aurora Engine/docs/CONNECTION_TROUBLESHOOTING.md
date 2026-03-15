# Hunger Games Simulator - Connection Troubleshooting Guide

## Quick Diagnosis

### Step 1: Check Server Health
```bash
# Terminal 1: Start the server
cd h:\Hunger Games Simulator\Aurora Engine
python lobby_server.py
```

The startup message should show:
```
🔧 Connection Configuration:
  - Socket.IO ping timeout: 20s (client timeout: 20s) ✅ ALIGNED
  - Socket.IO ping interval: 8s
  - Transports: polling-first (stable), then websocket (upgrade)
  - Force polling on Cloudflare Tunnel/proxies: ENABLED
```

### Step 2: Run Connection Tests
```bash
# Terminal 2: Run stability tests
cd h:\Hunger Games Simulator\Aurora Engine
python test_connection_stability.py

# Or test a remote server
python test_connection_stability.py http://your-cloudflare-domain.com
```

Expected output:
```
✅ PASS: HTTP Connectivity
✅ PASS: Diagnostics Endpoint
✅ PASS: Socket.IO Connection
✅ PASS: Connection Persistence (30s)
✅ PASS: Rapid Reconnections (5x)
```

### Step 3: Check Live Diagnostics
```bash
# While server is running, open in browser:
http://localhost:8000/api/connection-diagnostics

# Or from remote:
https://your-cloudflare-domain.com/api/connection-diagnostics
```

## Root Causes Identified & Fixed

### ✅ FIXED: Asymmetric Timeout (Was Causing Disconnections)
**Problem**: Server ping_timeout=60s, Client timeout=20s
**Impact**: After 20s of no messages, client assumed dead and disconnected, but server kept connection alive for 60s
**Solution**: Changed both to 20s + ping_interval=8s to keep connection alive

**Before**:
```python
ping_timeout=60,      # Server waits 60s
ping_interval=25,     # Server sends ping every 25s
# Client timeout=20s   # Client gives up after 20s ❌ MISMATCH
```

**After**:
```python
ping_timeout=20,      # Server waits 20s
ping_interval=8,      # Server sends ping every 8s (2.5x before timeout)
# Client timeout=20s   # Now matches! ✅
```

### ✅ FIXED: Transport Priority Mismatch (Was Causing Upgrade Failures)
**Problem**: Server prefers polling, Client tries WebSocket first
**Impact**: Connection negotiation delays, WebSocket upgrades often fail through proxies
**Solution**: Aligned both to polling-first

**Before**:
```javascript
transports: ['websocket', 'polling']  // Client: WebSocket first
transports: ['polling', 'websocket']  // Server: Polling first ❌ OPPOSITE
```

**After**:
```javascript
transports: ['polling', 'websocket']  // Both: Polling first (stable for proxies) ✅
```

### ✅ FIXED: Cloudflare Tunnel Connection Drops (Was Causing Proxy Issues)
**Problem**: Cloudflare Tunnel closes idle WebSocket connections after ~100 seconds
**Impact**: Long-running games disconnect players randomly
**Solution**: Enabled polling-only mode for non-localhost + shorter ping interval

**Implementation**:
```javascript
// Client automatically forces polling for non-localhost
forcePolling: window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1'

// Server sends pings every 8s to keep connection alive through proxy
ping_interval=8,      // Pings keep connection from timing out
```

### ✅ FIXED: Uvicorn Worker Timeout (Was Causing Random Disconnects)
**Problem**: Uvicorn default worker timeout 120s, long-lived connections get killed
**Impact**: Players disconnected after 2 minutes of activity
**Solution**: Configured keepalive and extended timeouts

**Before**:
```python
uvicorn.run(app, host="0.0.0.0", port=8000)  # Uses defaults ❌
```

**After**:
```python
uvicorn.run(
    app,
    host="0.0.0.0",
    port=8000,
    keepalive=5,              # TCP keepalive every 5s
    timeout_keep_alive=15,    # Worker timeout for idle connections
    ws_ping_interval=20,      # WebSocket ping every 20s
    ws_ping_pong_interval=20  # Wait 20s for pong
)
```

## Troubleshooting by Symptom

### Symptom: Random Player Disconnections
**Likely Cause**: Ping timeout mismatch or idle connection timeout
**Check**: 
- Run `test_connection_stability.py` - specifically "Connection Persistence" test
- Check `/api/connection-diagnostics` for socket count dropping
**Solution**:
- Verify ping_timeout/interval are synchronized
- Ensure uvicorn keepalive is set to 5s

### Symptom: Connections Work Locally, Fail Through Cloudflare Tunnel
**Likely Cause**: WebSocket upgrade failing through proxy, or polling timeout
**Check**:
- Browser console should show "using: polling" not "using: websocket"
- Test with `python test_connection_stability.py https://your-domain.com`
**Solution**:
- Verify `forcePolling=true` for non-localhost in app.js
- Reduce ping_interval if timeouts still occur

### Symptom: "Can't connect to server" Error Message
**Likely Cause**: HTTP request failing, CORS issue, or port forwarding down
**Check**:
- Run test: `python test_connection_stability.py` should show HTTP connectivity
- Check firewall: `netstat -an | findstr 8000` (Windows) or `lsof -i :8000` (Mac/Linux)
- Check port forwarding status if using VSCode Remote Dev
**Solution**:
- Verify server is running: `http://localhost:8000`
- Check port forwarding is active in VSCode Remote Dev tunnel
- Verify firewall allows port 8000

### Symptom: Intermittent "Connection Timeout" Errors
**Likely Cause**: Proxy buffering or connection pool exhaustion
**Check**:
- Run "Rapid Reconnections" test in `test_connection_stability.py`
- Check `/api/connection-diagnostics` for connection count growing unbounded
**Solution**:
- Middleware already sets `X-Accel-Buffering: no` - should help
- If socket count keeps growing, there's a connection leak (investigate per-player cleanup)

### Symptom: Port Forwarding Tunnel Frequently Disconnects
**Likely Cause**: VSCode Remote Dev tunnel is unstable or network issue
**Check**:
- Check `~/.vscode-server/data/logs/` for tunnel logs
- Test local connectivity: `python test_connection_stability.py http://localhost:8000`
**Solution**:
- Close and reopen VSCode Remote Dev tunnel
- Test with Cloudflare Tunnel instead if available
- Check home internet stability

## Monitoring Commands

### Monitor Diagnostics in Real-Time
```bash
# Run in terminal (requires curl/wget)
# Linux/Mac:
watch -n 5 'curl http://localhost:8000/api/connection-diagnostics | jq .'

# Windows PowerShell:
while($true) { 
    Invoke-WebRequest http://localhost:8000/api/connection-diagnostics | ConvertFrom-Json | ConvertTo-Json | Out-Host
    Start-Sleep 5
}
```

### Monitor Server Logs
```bash
# Server logs should show:
# - Client connected/disconnected
# - Lobby created/joined
# - Game started/ended
# - Any errors in game simulation

# Watch for these WARNING signs:
# - "ping timeout" messages
# - "transport close" messages
# - "io server disconnect" reason
```

### Monitor Browser Console
Press F12 in browser, then Console tab:
- Should see `✅ Connected to server successfully`
- Should see `Socket ID: <id>` printed
- Should NOT see `❌ Connection error` messages
- Should see `⏓ Received pong from server` periodically

## Performance Tips

### For Stable Long-Running Games:
1. **Reduce Ping Interval**: Change `ping_interval=8` to `ping_interval=5` if disconnects persist
2. **Increase Connection Timeout**: If players have very slow connections, increase `timeout_keep_alive` to 30s
3. **Monitor Resources**: Use `/api/connection-diagnostics` to watch memory and connection count
4. **Enable Compression**: Add `engineio_logger_binary=False` to Socket.IO config

### For Cloudflare Tunnel Stability:
1. **Use Polling Only**: Setting `forcePolling=true` is already enabled
2. **Keep Tunnel Active**: Cloudflare Tunnel closes after ~90 seconds idle, so ping_interval=8s keeps it alive
3. **Monitor with curl**: `curl https://your-domain.com/api/connection-diagnostics` periodically

### For Port Forwarding Stability:
1. **Check Firewall**: Ensure port 8000 is not blocked
2. **Monitor VSCode Tunnel**: Restart if logs show frequent reconnects
3. **Use Polling**: Port forwarding benefits from polling over WebSocket
4. **Reduce Packet Size**: Max message size is 1MB, but keep messages smaller

## Configuration Reference

### Socket.IO Server Settings (lobby_server.py)
```python
sio = socketio.AsyncServer(
    ping_timeout=20,        # ⚠️ CRITICAL: Must match client timeout
    ping_interval=8,        # ✅ Keeps connection alive (2.5x before timeout)
    transports=['polling', 'websocket'],  # ✅ Polling first for stability
    allow_upgrades=True,    # Allows upgrade to WebSocket if available
    upgrade_mode='probe',   # Try upgrade but don't fail if it doesn't work
    max_http_buffer_size=1000000,
    cookie=False,           # ✅ Better proxy compatibility
)
```

### Uvicorn Startup Settings (lobby_server.py)
```python
uvicorn.run(
    app,
    keepalive=5,              # TCP keepalive every 5s
    timeout_keep_alive=15,    # Worker timeout for idle connections
    timeout_notify=30,        # Graceful shutdown notification
    ws_max_size=1000000,      # Max WebSocket message size
    ws_ping_interval=20,      # WebSocket-specific ping interval
    ws_ping_pong_interval=20, # Wait up to 20s for pong response
)
```

### Client Socket.IO Settings (app.js)
```javascript
io(serverUrl, {
    transports: ['polling', 'websocket'],  // ✅ Must match server
    timeout: 20000,           // ⚠️ CRITICAL: Must match server ping_timeout
    reconnectionDelay: 500,   // Initial backoff
    reconnectionDelayMax: 5000,  // Max backoff
    reconnectionAttempts: 15, // Try 15 times before giving up
    forcePolling: true,       // ✅ For non-localhost (Cloudflare, etc.)
})
```

## Testing Scenarios

### Scenario 1: Test Cloudflare Tunnel Stability
```bash
# Run test against Cloudflare domain
python test_connection_stability.py https://your-domain.com

# Expected: All tests pass
# If Connection Persistence fails: Increase ping_interval or reduce ping_timeout
```

### Scenario 2: Test Port Forwarding Stability
```bash
# If using port forwarding from VSCode Remote Dev
# Test should report using 'polling' transport
# Connection Persistence should complete full 30s

# If fails: Check port forwarding is active and stable
```

### Scenario 3: Load Test with Multiple Connections
```bash
# Modify test_connection_stability.py's rapid reconnections to 20 attempts
python test_connection_stability.py --attempts 20

# Ensure success rate stays above 95%
```

## When to Escalate

If connection issues persist after trying fixes above:

1. **Collect Diagnostics**:
   - Output of `test_connection_stability.py`
   - Output of `/api/connection-diagnostics` 
   - Browser console screenshot (F12)
   - Server startup logs (first 50 lines)

2. **Check for Specific Patterns**:
   - Which transport is actually being used? (polling or websocket)
   - How long do connections stay alive?
   - What's the error message when disconnection happens?

3. **Consider Network Issues**:
   - Is home internet stable? (Use `ping 8.8.8.8` test)
   - Is Cloudflare Tunnel active? (Check their dashboard)
   - Is VSCode Remote Dev tunnel working? (Check VSCode Remote indicator)

## References

- Socket.IO Docs: https://socket.io/docs/v4/socket-io-protocol/
- Python-socketio: https://python-socketio.readthedocs.io/
- Cloudflare Tunnel: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/
- Uvicorn Settings: https://www.uvicorn.org/
