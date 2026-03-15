# Connection & Reliability Diagnostic Report

## Issues Identified

### 1. **Socket.IO Transport Priority Mismatch**
- **Problem**: Server configured with `['polling', 'websocket']` but client tries `['websocket', 'polling']`
- **Impact**: Server prefers polling but client prefers WebSocket, causing negotiation delays
- **Solution**: Align transports priority across server and client

### 2. **Cloudflare Tunnel Specific Issues**
- **Problem**: Cloudflare Tunnel doesn't handle upgrade mechanism well; forces connection downgrade
- **Impact**: Initial WebSocket connection succeeds but downgrades to polling unexpectedly
- **Solution**: Detect Cloudflare Tunnel and force polling-only mode from start

### 3. **Ping/Timeout Configuration**
- **Current**: `ping_timeout=60`, `ping_interval=25` on server
- **Problem**: Client has 20-second connection timeout but server waits 60 seconds before considering connection dead
- **Impact**: Timing mismatch causes asymmetric disconnections
- **Solution**: Synchronize timeout values between client and server

### 4. **Port Forwarding Buffering**
- **Problem**: Middleware sets `X-Accel-Buffering: no` but port forwarding proxy may ignore headers
- **Impact**: Real-time data gets buffered, causing message delays or disconnections
- **Solution**: Configure server-level streaming support and disable response buffering at uvicorn level

### 5. **WebSocket Header Stripping**
- **Problem**: Proxy infrastructure may strip WebSocket upgrade headers
- **Impact**: WebSocket connections fail silently, forcing fallback to polling with latency
- **Solution**: Detect WebSocket failures and provide clear logging

### 6. **Connection Pool Exhaustion**
- **Problem**: No connection pooling or recycling mechanism
- **Impact**: Long-running connections accumulate, causing memory leaks
- **Solution**: Implement connection health checks and periodic recycling

### 7. **Uvicorn Not Optimized for WebSockets**
- **Problem**: Default uvicorn settings not tuned for long-lived WebSocket connections
- **Impact**: Worker processes timeout or disconnect after period of inactivity
- **Solution**: Configure uvicorn with appropriate keepalive and timeout settings

## Critical Configuration Issues Found

### Server (lobby_server.py - lines 156-172)
```python
# ISSUES:
# 1. Transports list: ['polling', 'websocket'] - should match client
# 2. ping_timeout=60 but client timeout is 20 seconds - asymmetric!
# 3. cookie=False might interfere with session tracking
# 4. allowEIO3=True might cause protocol mismatch
```

### Client (app.js - lines 35-60)
```javascript
// ISSUES:
# 1. Transports: ['websocket', 'polling'] - opposite of server preference
# 2. forcePolling: true for non-localhost (good!) but WebSocket still attempted first
# 3. timeout: 20000 but server ping_timeout is 60000
# 4. reconnectionDelay: 1000 constant (should use exponential backoff)
```

### Uvicorn Startup (lines 1169-1170)
```python
# ISSUES:
# 1. No timeout configuration - uses defaults (120s worker timeout)
# 2. No keepalive configuration
# 3. Single worker default - doesn't scale
# 4. No graceful shutdown handling
```

## Recommended Fixes (Priority Order)

### CRITICAL (Fix First)
1. **Align ping/timeout values** (server and client should match)
2. **Fix transport ordering** (decide: WebSocket-first or polling-first)
3. **Configure uvicorn properly** (keepalive, timeout, workers)

### HIGH (Fix Next)
4. **Detect Cloudflare Tunnel** and force polling-only for non-localhost
5. **Improve reconnection logic** (exponential backoff, jitter)
6. **Add connection diagnostics** (debug endpoint, logging)

### MEDIUM (Fix Later)
7. **Implement connection pooling** (health checks, recycling)
8. **Add adaptive bitrate** (reduce data size if connection unstable)
9. **Monitor and alert** (connection stats, error tracking)

## Testing Strategy

### Before Changes
- [ ] Record baseline disconnect rate
- [ ] Test with port forwarding
- [ ] Test with Cloudflare Tunnel
- [ ] Test with WebSocket disabled

### After Changes
- [ ] Verify alignment of client/server timeout values
- [ ] Check transport priority matches everywhere
- [ ] Run 1-hour stability test with multiple connections
- [ ] Test failover from WebSocket to polling
- [ ] Verify Cloudflare Tunnel polling-only mode works
