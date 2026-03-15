# Polling Timing Fix - Verification Guide

## How to Test the Fix

### Setup
1. **Start the server:**
   ```powershell
   cd "h:\Hunger Games Simulator\Aurora Engine"
   python lobby_server.py
   ```

2. **Open browser:**
   - Go to `http://localhost:8000`
   - Open DevTools: Press `F12` → go to **Console** tab

### Test Scenario 1: Fresh Page Load

**Steps:**
1. In console, watch for messages
2. Create a new lobby
3. Add 2+ players
4. Each player creates a tribute
5. Host clicks "Start Game"

**Expected Console Output:**
```
⏳ DOM still loading, waiting for DOMContentLoaded before signaling server
...
✅ DOM fully loaded, signaling client ready
✓ Displaying current player stats: {id: '...', name: '...', ...}
✓ Displaying all tributes from gameState: 24 tributes
✅ Rendering 24 tribute scoreboard(s) in tributes-container
Game state update: {...}
Game update: {...}
```

**What to Check:**
- ✅ No "not found" errors
- ✅ Left sidebar shows tribute with stats
- ✅ Right sidebar shows all tributes
- ✅ Center log shows game events

---

### Test Scenario 2: Page Already Cached

**Steps:**
1. Start game (completes scenario 1)
2. Press Ctrl+R to reload the page (while connected)
3. Watch console

**Expected Console Output:**
```
✅ DOM already loaded, signaling client ready
Game page loaded, signaling client ready
Game state update: {...}
Game update: {...}
```

**What to Check:**
- ✅ Uses cached load path (100ms delay)
- ✅ Data still renders correctly
- ✅ Game state preserved

---

### Test Scenario 3: Slow Network

**Steps:**
1. In DevTools, go to **Network** tab
2. Set throttling to "Slow 3G" or "Slow 4G"
3. Create lobby with 2-3 players
4. Each creates tribute
5. Start game
6. Watch console carefully

**Expected Console Output:**
```
⏳ DOM still loading, waiting for DOMContentLoaded before signaling server
[possibly some game events here]
✅ DOM fully loaded, signaling client ready
Game state update arrives...
✓ Displaying current player stats...
✓ Displaying all tributes...
```

**What to Check:**
- ✅ DOMContentLoaded waits for DOM, not network
- ✅ Even on slow connection, tribute renders correctly
- ✅ No race condition errors

---

## Key Console Messages

| Message | Meaning |
|---------|---------|
| ⏳ DOM still loading... | Page HTML is being built, waiting |
| ✅ DOM fully loaded... | HTML ready, client can signal server |
| ✅ DOM already loaded... | Using cached/reload path with 100ms delay |
| ✓ Displaying current player stats | Tribute rendering started |
| ✓ Displaying all tributes | All tributes list rendering started |
| ✅ Rendering N tribute scoreboard(s) | Successful render of tribute count |
| ❌ not found | BAD: Element doesn't exist (should not happen now) |

---

## Visual Checklist

When game starts, you should see:

### Left Sidebar ("Your Tribute")
- [ ] Tribute name displayed
- [ ] District and age shown
- [ ] Skill priority list (if available)
- [ ] All skills with ratings shown
- [ ] Stats bars (health, hunger, thirst, etc.)

### Right Sidebar ("Remaining")  
- [ ] Grid of tribute cards
- [ ] Each card shows name, district, skills
- [ ] Stats bars visible
- [ ] No placeholder text ("No data", "loading forever", etc.)

### Center Area
- [ ] Game log shows events as they happen
- [ ] No error messages
- [ ] Phase and timer information updates

### Browser Console (F12 → Console)
- [ ] No red error messages
- [ ] "not found" messages should be GONE
- [ ] Blue info messages (ℹ️) show progression
- [ ] Yellow warning messages (⚠️) are OK for edge cases

---

## Troubleshooting

### Problem: Still Seeing "not found" Errors

**Possible causes:**
1. Old code not loaded - **Solution:** Hard refresh: `Ctrl+Shift+R` (clears cache)
2. Browser cached old version - **Solution:** Restart browser or use private/incognito window
3. Server not restarted - **Solution:** Stop server (`Ctrl+C`) and run `python lobby_server.py` again

### Problem: Left Sidebar Empty / Right Sidebar Empty

**Expected:** Takes ~1-2 seconds after "Start Game" to populate

**If stays empty:**
1. Check console for errors
2. Look for "Displaying all tributes from gameState: X tributes" message
3. If not present, check server logs for errors
4. Try reloading page with `F5`

### Problem: Game Events Not Showing

**Check:**
1. Is game actually running? (Check center area)
2. Is `#game-log` element rendering? (Check Dev Tools → Elements)
3. Are there socket errors? (Check console)
4. Try: `socket.emit('request_game_state')` in console to force update

---

## Performance Expectations

| Stage | Time | Status |
|-------|------|--------|
| Page load starts | 0ms | DOM building |
| DOMContentLoaded fires | ~500-2000ms | Depends on network |
| client_ready emitted | ~500-2100ms | After DOMContentLoaded |
| Server receives client_ready | ~500-2150ms | Network latency added |
| First game_state_update | ~550-2200ms | Server sends initial state |
| Tributes render on screen | ~600-2300ms | Visible to player |

**Note:** All times assume localhost. Remote servers may be slower.

---

## Files to Monitor

Check these files in browser DevTools if debugging:

- `static/js/game.js` - Lines 80-110 (the fix location)
- `static/js/app.js` - Lines 142-155 (game_starting handler)
- `templates/game.html` - HTML elements being created

---

## Success Criteria ✅

The fix is working correctly if:

1. ✅ Console shows "DOM fully loaded, signaling client ready"
2. ✅ No "not found" errors when tributes render
3. ✅ Left sidebar: Your tribute appears with full stats
4. ✅ Right sidebar: All remaining tributes appear as cards
5. ✅ Center: Game events appear in real-time
6. ✅ Game runs for full duration without breaking UI

---

**Last Updated:** October 29, 2025
