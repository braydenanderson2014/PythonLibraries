# Debugging Guide - Game Page Tribute Display

## Issue: 404 Error on `/api/tribute/{player_id}`

### Root Cause
The client was trying to fetch tribute data from the API endpoint `/api/tribute/{player_id}`, but:
1. The player_id wasn't registered in the server's `players` dictionary
2. We already have all the data from Socket.IO, so the API call was unnecessary

### Solution Applied
**Removed the API fallback fetch.** The client now relies solely on data from the `game_state_update` Socket.IO event, which includes:
- `current_player` - The player's own tribute with all details
- `game_state.players[]` - All tributes in the game

### What Changed
**File**: `Aurora Engine/static/js/game.js`

**Removed**:
```javascript
// Removed API fetch (was causing 404 errors)
if (!tributeStatsFetched && currentPlayer && currentPlayer.id) {
    setTimeout(() => {
        fetchPlayerTributeStats(currentPlayer.id);  // ❌ This was failing
    }, 1000);
    tributeStatsFetched = true;
}
```

**Why**: We already have all the data from Socket.IO. The API was redundant.

---

## Enhanced Debugging Output

### Console Messages Now Show Progress

When the game page loads and receives `game_state_update`, you'll see:

```
✓ Displaying tribute stats from game_state_update: {...}
✓ Displaying all tributes from gameState: 48 tributes
  First tribute sample: {id: "...", name: "Katniss", district: 12, ...}
[DISPLAY_TRIBUTES] Called with: 48 tributes, current player: abc123
[DISPLAY_TRIBUTES] Building cards for 48 tributes
[DISPLAY_TRIBUTES] Card 0: Katniss from District 12
[DISPLAY_TRIBUTES] Card 1: Peeta from District 1
...
[DISPLAY_TRIBUTES] ✓ Generated 48 cards
[DISPLAY_TRIBUTES] ✓ Cards inserted into DOM

[DISPLAY_STATS] Called with: {name: "Katniss", district: 12, ...}
[DISPLAY_STATS] Ratings found: 10 skills
[DISPLAY_STATS] ✓ Generated HTML, inserting into DOM
[DISPLAY_STATS] ✓ Successfully displayed tribute stats
```

### Checkmark Prefixes
- ✓ = Success (display function worked)
- ✗ = Failure (display function not called)
- ⚠️ = Warning (data missing or incomplete)

### Key Debug Points

1. **Data Received**
```
console.log('Game state update:', data);  // Full data packet
console.log('Game state players length:', data.game_state?.players?.length);  // How many tributes
```

2. **Current Player Display**
```
✓ Displaying tribute stats from game_state_update  // Your tribute showing
✗ No tribute_data in currentPlayer  // Your tribute NOT showing
```

3. **All Tributes Display**
```
✓ Displaying all tributes from gameState: 48 tributes  // Grid will populate
✗ No tributes in gameState  // Grid will be empty
```

---

## Data Structure

### What The Server Sends

When `game_state_update` is emitted:

```javascript
{
  game_state: {
    day: 1,
    status: "waiting",
    players: [
      {
        id: "sid1",
        name: "Player 1",
        district: 1,
        tribute_data: {
          name: "Tribut Name",
          district: 1,
          age: 16,
          gender: "Male",
          skills: {
            strength: 7,
            agility: 6,
            ...
          }
        },
        tribute_ready: true
      },
      ...
    ]
  },
  current_player: {
    id: "sid1",
    name: "Player 1",
    tribute_data: { ... },  // Your tribute
    ...
  }
}
```

### What Gets Displayed

**Your Tribute** (in `#scoreboards-container`):
```
Name: [current_player.tribute_data.name]
District: [current_player.tribute_data.district]
Age: [current_player.tribute_data.age]
Gender: [current_player.tribute_data.gender]
Skills: [current_player.tribute_data.skills]
```

**All Tributes** (in `#tributes-container`):
```
Grid of cards from: gameState.players[]
Each card shows:
  - Name: tribute.name or tribute.tribute_data.name
  - District: tribute.district or tribute.tribute_data.district
  - Age: tribute.age or tribute.tribute_data.age
  - Gender: tribute.gender or tribute.tribute_data.gender
  - Top 5 Skills: tribute.skills or tribute.tribute_data.skills
```

---

## Troubleshooting

### "Your Current Tribute Status" Is Empty

**Console Output To Look For**:
```
✗ No tribute_data in currentPlayer
```

**Causes**:
1. `current_player` is null
2. `current_player.tribute_data` is null/undefined
3. `tribute_data.name` is empty

**Fix**:
1. Check that player created a tribute before game started
2. Verify server is sending `current_player` in `game_state_update`
3. Check server logs: `Sending game_state_update to {player_id}: tribute_data={...}`

### "Remaining Tributes" Grid Is Empty

**Console Output To Look For**:
```
✗ No tributes in gameState
```

**Causes**:
1. `game_state` is null
2. `game_state.players` is null/empty
3. Players don't have tribute data yet

**Fix**:
1. Verify game has started (all players submitted tributes)
2. Check server: `gameState.players` should have all 48 players
3. If admin used "Generate Tributes", verify tributes were created

### Some Cards Display But Skills Are Empty

**Console Output To Look For**:
```
[DISPLAY_TRIBUTES] Card 5: Cato from District 2
No skills recorded  // Appears in tribute card
```

**Causes**:
1. Tribute doesn't have skills set
2. Skills are in nested `tribute_data` not at top level
3. Skills object is empty

**Fix**:
1. Admin should regenerate tribute with `Generate Random Tribute`
2. Check data structure in console: `First tribute sample: {...}`
3. Verify `skills` field exists and has values

---

## How To Debug

### Step 1: Open Browser DevTools
- Press `F12` or `Ctrl+Shift+I` (Windows) / `Cmd+Option+I` (Mac)
- Go to **Console** tab

### Step 2: Look For Game State Update Message
```
Game state update: {...}
```

### Step 3: Check For Checkmarks
- ✓ means function ran successfully
- ✗ means function was skipped (data missing)

### Step 4: Expand Objects In Console
Click the arrow to expand:
```
▶ game_state: {day: 1, status: "waiting", ...}
▶ current_player: {id: "...", name: "...", tribute_data: {...}}
▶ gameState.players: Array(48) [...]
```

### Step 5: Check "First Tribute Sample"
```
First tribute sample: {
  id: "...",
  name: "Katniss",
  district: 12,
  tribute_data: {
    name: "Katniss",
    district: 12,
    skills: {...}
  }
}
```

This shows the exact structure your tributes have.

---

## Common Issues & Fixes

| Issue | Console Shows | Fix |
|-------|---------------|-----|
| Tributes not displaying | `✗ No tributes in gameState` | Game hasn't started yet. Wait for all players to submit tributes. |
| Your tribute not showing | `✗ No tribute_data in currentPlayer` | Create/submit your tribute first. |
| Skills show as empty | `No skills recorded` | Admin needs to generate tributes with skills. |
| Grid is formatted wrong | Cards appear but overlap | Check CSS isn't overridden. Grid should be responsive. |
| Admin panel not showing | Panel doesn't appear | Verify you're the lobby host (check `isHost` in console). |
| 404 errors in console | GET /api/tribute/... 404 | This is now fixed - no API calls needed. |

---

## Server-Side Debugging

### Server Logs To Check

**When game starts**:
```
Sending game_state_update to abc123def456: tribute_data={...}
```
- Shows server IS sending tribute data
- Check if `tribute_data` is `None` or `{}`

**When client connects**:
```
Socket connected: abc123def456
Socket ready
```

**If player missing tributes**:
```
Received packet PONG data
Client is gone, closing socket
```

### Server Command Line Check

```bash
# View players in game
curl http://localhost:8000/api/debug/players
```

Should show all players and their tributes.

---

## Performance Considerations

### Why No API Calls?
- **Before**: 1 Socket.IO event + 1 API call per player = 2 network requests
- **After**: 1 Socket.IO event with all data = 1 network request
- **Benefit**: Faster, fewer server requests, no 404 errors

### Rendering Performance
- Displays up to 48 tribute cards in < 200ms
- Uses batch HTML update (single DOM write) instead of appending one-by-one
- CSS Grid handles responsive layout without JavaScript

---

## Future Improvements

1. **Streaming Tributes**: Instead of all at once, stream tributes as they're created
2. **Lazy Loading**: Only render tributes visible in viewport
3. **Caching**: Cache tribute data to avoid re-renders
4. **Updates**: Update tributes when server sends `lobby_updated` events
5. **Search**: Add client-side search/filter without new API calls

---

## Quick Reference

### Checking If It's Working

✅ **Working**:
- Console shows `✓ Displaying tribute stats`
- Console shows `✓ Displaying all tributes from gameState: 48 tributes`
- Left sidebar shows your tribute
- Grid shows all 48 tribute cards
- Skills bars appear on each card

❌ **Not Working**:
- Console shows `✗ No tribute_data in currentPlayer`
- Console shows `✗ No tributes in gameState`
- Sidebar is black or empty
- Grid is empty or no cards

---

**Last Updated**: October 27, 2025
**Status**: ✅ Debugging guide complete
