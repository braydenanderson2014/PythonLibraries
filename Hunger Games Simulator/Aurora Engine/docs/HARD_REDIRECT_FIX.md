# Critical Fix: Hard Redirect Causing Socket Disconnect

## Problem Identified

When `game_starting` event was received, `lobby.js` was doing a **hard page redirect**:

```javascript
window.location.href = `/game/${lobbyId}`;  // ❌ HARD REDIRECT
```

This caused:
1. Page completely reloads
2. Socket.IO connection drops and reconnects
3. Console clears
4. Game initialization state lost
5. UI appears to "flash" or reload mid-initialization

## Root Cause Analysis

**The Event Flow (BROKEN):**
```
1. Admin clicks "Start Game"
   ↓
2. Server: game_starting event sent
   ↓
3. lobby.js receives event → window.location.href = /game/{id}
   ↓ ❌ FULL PAGE RELOAD HERE
4. Socket disconnects/reconnects
   ↓
5. Page reloads, console clears
   ↓
6. app.js game_starting handler fires (but too late)
   ↓
7. Game page shows but tributes empty (state lost)
```

## The Solution

**Don't do hard redirects in SPA mode!** Let `app.js` handle navigation via the DOM/CSS instead.

### Changes Made

**File: `static/js/lobby.js`**

Two locations fixed (lines ~402-420 and ~430-460):

**BEFORE:**
```javascript
socket.on('game_starting', (data) => {
    if (!isSpectating) {
        window.location.href = `/game/${lobbyId}`;  // ❌ HARD REDIRECT
    }
});

socket.on('game_started', (data) => {
    if (!isSpectating) {
        window.location.href = `/game/${lobbyId}`;  // ❌ HARD REDIRECT
    }
});
```

**AFTER:**
```javascript
socket.on('game_starting', (data) => {
    if (!isSpectating) {
        console.log('✅ Allowing app.js to handle SPA navigation (no hard redirect)');
        // Let app.js handle the game page initialization via SPA
        // The game_starting event is also received there
    }
});

socket.on('game_started', (data) => {
    if (!isSpectating) {
        console.log('✅ Allowing app.js to handle SPA navigation (no hard redirect)');
        // Let app.js handle the game page initialization via SPA
    }
});
```

## New Event Flow (FIXED)

```
1. Admin clicks "Start Game"
   ↓
2. Server: game_starting event sent
   ↓
3. lobby.js receives event → (logs but doesn't redirect)
   ↓
4. ✅ Socket connection stays intact!
   ↓
5. app.js receives same event:
   └─> showSection('game-section')  // ✅ SPA navigation (no reload)
   └─> initializeGamePageWithSocket(socket)  // ✅ Direct socket passed
   ↓
6. Game page shows with socket still connected
   ↓
7. DOM elements load
   ↓
8. client_ready sent after DOM ready
   ↓
9. ✅ Game fully initialized with all tributes visible
```

## Why This Works

- ✅ **No page reload** → Socket connection never drops
- ✅ **Console never clears** → Can see full initialization flow
- ✅ **SPA navigation** → `app.js` handles it via CSS/DOM
- ✅ **Game state preserved** → No restart/reinit on navigate
- ✅ **Tributes appear correctly** → Data flows uninterrupted

## Testing

**What You Should See Now:**

1. Start game
2. Console shows: `✅ Allowing app.js to handle SPA navigation`
3. **No page reload** (URL might change but via history API, not hard redirect)
4. Console shows: `✅ Socket passed directly, initializing game page`
5. Console shows: `✅ [CLIENT_READY] All DOM elements ready`
6. Game page loads with tributes in sidebars
7. Game events appear in center log
8. **No "Connecting..." state** - socket never dropped!

---

**Files Modified:**
- `static/js/lobby.js` (2 event handlers: game_starting, game_started)

**Status:** ✅ Ready to test - hard refresh and start a game!
