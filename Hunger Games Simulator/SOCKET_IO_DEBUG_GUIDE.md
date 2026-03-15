# Socket.IO Connection Debugging Guide

## Quick Verification Checklist

### Browser Console (F12 → Console Tab)
Look for these **GOOD** signs:
- ✅ `Connecting to server: wss://hungergames.monkeybusinesspreschool-ut.com`
- ✅ `WebSocket URL will be: wss://hungergames.monkeybusinesspreschool-ut.com/socket.io/`
- ✅ `✅ Connected to server successfully`
- ✅ `Socket ID: [some-long-id]`
- ✅ `Game page loaded, signaling client ready`

Look for these **BAD** signs (if you see these, there's an issue):
- ❌ `Refused to set unsafe header 'User-Agent'` (User-Agent issue - should be FIXED now)
- ❌ `Connection error: [any error]` (repeated multiple times = connection problem)
- ❌ `ping timeout` (server not responding - check server is running)
- ❌ `A listener indicated an asynchronous response by returning true` (browser extension blocking)

### Network Tab (F12 → Network Tab)
Look for these **GOOD** signs:
- ✅ Repeated POST requests to `/socket.io/?...` with Status 200
- ✅ Polling requests happening every 5-10 seconds
- ✅ Each request shows request/response with data payload

Look for these **BAD** signs:
- ❌ 4xx or 5xx errors on `/socket.io/` requests
- ❌ Requests timing out or showing "Pending" for long periods
- ❌ No requests appearing at all after connection
- ❌ Many failed requests followed by reconnection attempts

## Detailed Debugging Steps

### Step 1: Verify Server is Running
```bash
# Local testing
curl http://localhost:8000/

# Production (check with your domain)
curl https://hungergames.monkeybusinesspreschool-ut.com/
```
Expected: Should return HTML page without errors

### Step 2: Check Socket.IO Connection Details

In browser console, run:
```javascript
// This will show connection details
console.log('Socket connected:', socket.connected);
console.log('Socket ID:', socket.id);
console.log('Transport:', socket.io.engine.transport.name);
console.log('URL:', socket.io.engine.uri);
```

Expected output:
```
Socket connected: true
Socket ID: abc123def456...
Transport: polling  (or websocket if upgraded)
URL: https://hungergames.monkeybusinesspreschool-ut.com/socket.io/?...
```

### Step 3: Test Manual Event Emission

In browser console:
```javascript
// Emit a test event to server
socket.emit('test_event', {data: 'test'}, (response) => {
    console.log('Server response:', response);
});

// You should see the response logged
```

### Step 4: Monitor Real-Time Connection Issues

In browser console:
```javascript
socket.on('disconnect', (reason) => {
    console.log('DISCONNECTED:', reason);
    console.log('Reconnecting attempts...');
});

socket.on('connect_error', (error) => {
    console.log('CONNECTION ERROR:', error.message);
});

socket.on('reconnect_attempt', () => {
    console.log('Attempting to reconnect...');
});

socket.on('reconnect', (attemptNumber) => {
    console.log('Reconnected! Attempts:', attemptNumber);
});
```

## Common Issues and Solutions

### Issue: "Refused to set unsafe header 'User-Agent'"
**Status**: ✅ FIXED in app.js (User-Agent headers removed)
**If still seeing**: Clear browser cache (Ctrl+Shift+Delete), hard refresh (Ctrl+Shift+R)

### Issue: Connection keeps timing out
**Possible Causes**:
1. Server not running or not responding
2. Firewall blocking traffic
3. Cloudflare Tunnel not forwarding properly
4. WebSocket being blocked by proxy

**Solution**:
- Verify server is running: `python lobby_server.py`
- Check server logs for errors
- Use `forcePolling: true` to force long-polling (should be automatic on production)

### Issue: "ping timeout" repeatedly
**Cause**: Server not sending pings or client not receiving them
**Solution**:
- Check server's `ping_interval: 8` and `ping_timeout: 20`
- Verify network latency isn't >10 seconds
- Check firewall/proxy isn't filtering WebSocket frames

### Issue: Extension/CSP blocking
**Error**: `"A listener indicated an asynchronous response by returning true..."`
**Solution**:
- Disable browser extensions and test in incognito mode
- Check website's Content-Security-Policy headers
- forcePolling=true helps mitigate this

## Testing Connection from Command Line

### Test HTTP endpoint
```bash
# Local
curl -v http://localhost:8000/

# Production
curl -v https://hungergames.monkeybusinesspreschool-ut.com/
```

### Test Socket.IO endpoint
```bash
# Local
curl -v http://localhost:8000/socket.io/?EIO=4&transport=polling

# Production  
curl -v https://hungergames.monkeybusinesspreschool-ut.com/socket.io/?EIO=4&transport=polling
```

Expected: 200 response with Socket.IO handshake data

## Performance Baseline

With proper Cloudflare Tunnel setup, you should see:
- **Connection time**: 2-5 seconds
- **Polling interval**: 5-10 seconds between requests
- **Message round-trip**: 100-500ms
- **Zero reconnections** once connected

If experiencing worse performance, check:
1. Network tab for slow requests
2. Server logs for processing delays  
3. Cloudflare Tunnel logs for proxy issues
4. Browser console for connection errors

## Enabling Verbose Logging (Development Only)

To enable detailed logging on client side, add to app.js connectSocket():
```javascript
// After creating socket, add:
socket.io.engine.on('drain', () => console.log('Drained'));
socket.io.engine.on('packet', (packet) => console.log('Packet:', packet));
```

To enable on server side (already enabled in lobby_server.py):
```python
# Already configured:
logger=True,
engineio_logger=True,
```

Check server logs for detailed connection information.

## Final Verification

✅ Connection working if you see in console:
1. "Connecting to server: ..."
2. "WebSocket URL will be: ..."
3. "✅ Connected to server successfully"
4. "Socket ID: [ID]"
5. On game page: "Game page loaded, signaling client ready"

If you see all 5 messages, the Socket.IO connection is working properly!
