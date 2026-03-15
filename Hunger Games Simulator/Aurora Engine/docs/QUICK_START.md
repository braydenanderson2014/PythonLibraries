# Quick Start - Connection Fixes

## What Was Fixed

| Issue | Root Cause | Fix | Impact |
|-------|-----------|-----|--------|
| Random disconnects | Server timeout 60s, Client 20s → asymmetric | Aligned both to 20s + ping every 8s | No more timeout-based drops |
| WebSocket fails through proxy | Transport negotiation mismatch | Polling-first on both ends | Stable through Cloudflare Tunnel |
| Drops after 2 minutes | Uvicorn worker timeout | Added keepalive=5s, timeout=15s | Works for full game duration |
| Can't debug issues | No diagnostics | Added `/api/connection-diagnostics` | Real-time monitoring available |
| Hard to verify fixes | No test suite | Added `test_connection_stability.py` | Can verify before deploying |

## Startup Output (What You Should See)

```
🔧 Connection Configuration:
  - Socket.IO ping timeout: 20s (client timeout: 20s) ✅ ALIGNED
  - Socket.IO ping interval: 8s (sends ping every 8s to keep alive)
  - Transports: polling-first (stable), then websocket (upgrade)
  - Force polling on Cloudflare Tunnel/proxies: ENABLED
  - Uvicorn keepalive: 5s (connections stay alive)

📊 Diagnostics available at: http://localhost:8000/api/connection-diagnostics
```

## Quick Tests

### Test 1: Local Connection (2 min)
```bash
cd h:\Hunger Games Simulator\Aurora Engine
python lobby_server.py
# In another terminal:
python test_connection_stability.py
```
✅ All 5 tests should PASS

### Test 2: Diagnostics (1 min)
```bash
# While server running, open:
http://localhost:8000/api/connection-diagnostics
```
✅ Should show active clients, lobbies, system stats

### Test 3: Full Game (10 min)
- Start server
- Create lobby
- Add 3+ players
- Create tributes for all
- Start game
✅ Game should complete without player disconnections

## Key Configuration Values (Reference)

**Server (`lobby_server.py`)**:
- `ping_timeout=20` seconds
- `ping_interval=8` seconds
- `transports=['polling', 'websocket']`
- Uvicorn `keepalive=5`, `timeout_keep_alive=15`

**Client (`app.js`)**:
- `timeout: 20000` milliseconds (= 20s)
- `transports: ['polling', 'websocket']`
- `forcePolling: true` for non-localhost

## Monitoring During Gameplay

### Browser Console (F12)
Look for:
- ✅ `Connected to server successfully` at start
- ✅ `Received pong from server` periodically (every ~8s)
- ❌ NO messages like "Connection error" or "ping timeout"

### Server Logs
Should see:
- `Client connected: <socket_id>` when player joins
- `game_starting` events as games start
- Minimal disconnect messages
- ❌ NO "ping timeout" or "transport close" errors

### Diagnostics Endpoint
```bash
curl http://localhost:8000/api/connection-diagnostics | jq .
```

Watch for:
- ✅ `connected_clients` growing as players join
- ✅ `socket_connections` stable (not growing unbounded)
- ✅ `memory_mb` under 500MB
- ❌ NO growing connection count after game starts

## Troubleshooting Quick Reference

| Problem | Check | Fix |
|---------|-------|-----|
| "Can't connect" | `curl http://localhost:8000` | Start server, check firewall |
| Connections drop after 2m | Server logs for "timeout" | Verify keepalive settings were applied |
| Works locally, fails on tunnel | Browser console, verify transport | Should show "using: polling" |
| Rapid reconnects | Run `test_connection_stability.py` | Check timeout alignment |
| Unknown issues | `/api/connection-diagnostics` | Review system stats and config |

## Files Changed

- ✅ `lobby_server.py`: Socket.IO config (lines 155-182), Uvicorn startup (lines 1257-1296), diagnostics endpoint (lines 378-453)
- ✅ `app.js`: Socket.IO client config (lines 37-72)
- ✅ Added: `test_connection_stability.py` (connection testing suite)
- ✅ Added: `CONNECTION_FIX_SUMMARY.md` (detailed explanation)
- ✅ Added: `CONNECTION_TROUBLESHOOTING.md` (troubleshooting guide)
- ✅ Added: `CONNECTION_DIAGNOSTICS.md` (issues & analysis)

## Success Criteria ✓

When fixed is working correctly, you should see:

- [ ] All 5 connection tests pass
- [ ] `/api/connection-diagnostics` shows active clients
- [ ] Game starts and completes without player disconnects
- [ ] Browser console shows no connection errors
- [ ] Server logs show no "ping timeout" errors
- [ ] Works through Cloudflare Tunnel
- [ ] Works through port forwarding / VSCode Remote

## Next Actions

1. **Test locally**: Run `python test_connection_stability.py` ➜ All pass?
2. **Monitor gameplay**: Start server and run full game ➜ No disconnects?
3. **Test remote**: If using Cloudflare/port forwarding, test there
4. **Deploy**: If all tests pass, the fixes are ready for production

---

**Questions?** Check `CONNECTION_TROUBLESHOOTING.md` for detailed troubleshooting guide.
