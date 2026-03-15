# URL State Transition Diagram

## State Machine Visualization

```
                         ┌─────────────────────────────────────────┐
                         │         APPLICATION STATES              │
                         └─────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│   START: Browser loads app                                                  │
│   ├─ URL: "/"                                                               │
│   ├─ State: Lobby Selection                                                │
│   ├─ Section: lobby-selection-section                                      │
│   └─ Action: User browses available lobbies                                 │
│                                                                             │
│   ┌─ Option A: User Creates New Lobby ──────────────────────────────┐      │
│   │                                                                  │      │
│   │  FROM:  URL: "/"                                               │      │
│   │         Section: lobby-selection-section (form shown inline)   │      │
│   │                                                                │      │
│   │  EVENT: user clicks "Create Lobby" button                     │      │
│   │         form submitted with: name, lobby_name, max_players    │      │
│   │                                                                │      │
│   │  EMIT:  socket.emit('create_lobby', {...})                  │      │
│   │                                                                │      │
│   │  RECEIVE: socket.on('lobby_created', {...})                │      │
│   │           data includes:                                       │      │
│   │           - lobby_id (auto-assigned as host)                 │      │
│   │           - player_id                                         │      │
│   │           - available_districts                               │      │
│   │           - resume_code                                       │      │
│   │                                                                │      │
│   │  UPDATE:  1. currentLobbyId = data.lobby_id                 │      │
│   │           2. currentPlayerId = data.player_id                │      │
│   │           3. window.updatePageURL('lobby:' + lobbyId)      │      │
│   │                                                                │      │
│   │  TO:      URL: "/lobby/{lobbyId}"                            │      │
│   │           Section: tribute-section                           │      │
│   │           State: Tribute Creation (as host)                 │      │
│   │                                                                │      │
│   └────────────────────────────────────────────────────────────────┘      │
│                                                                             │
│   ┌─ Option B: User Joins Existing Lobby ─────────────────────────┐      │
│   │                                                                 │      │
│   │  FROM:  URL: "/"                                              │      │
│   │         Section: lobby-selection-section                      │      │
│   │                                                                 │      │
│   │  EVENT: user clicks a lobby card                              │      │
│   │         selectLobby(lobbyId, lobbyData) called               │      │
│   │                                                                 │      │
│   │  UPDATE: 1. window.updatePageURL('lobby:' + lobbyId)       │      │
│   │          2. Show login-section                                │      │
│   │                                                                 │      │
│   │  TO:      URL: "/lobby/{lobbyId}"                            │      │
│   │           Section: login-section                             │      │
│   │           State: Lobby Selected (awaiting join)              │      │
│   │                                                                 │      │
│   │  NEXT:  USER ENTERS NAME ──────────────────────────────────┐ │      │
│   │        │                                                      │ │      │
│   │        │  EVENT: user clicks "Join Lobby" button             │ │      │
│   │        │         enterName: {name, resumeCode}               │ │      │
│   │        │                                                      │ │      │
│   │        │  EMIT:  socket.emit('join_lobby', {               │ │      │
│   │        │         lobby_id, name                              │ │      │
│   │        │  })                                                  │ │      │
│   │        │                                                      │ │      │
│   │        │  RECEIVE: socket.on('lobby_joined', {...})       │ │      │
│   │        │           data includes:                             │ │      │
│   │        │           - player_id                               │ │      │
│   │        │           - available_districts                     │ │      │
│   │        │           - player.tribute_data (if exists)        │ │      │
│   │        │                                                      │ │      │
│   │        │  UPDATE:  1. currentPlayerId = data.player_id      │ │      │
│   │        │           2. window.updatePageURL('lobby:'+ID)   │ │      │
│   │        │           3. Show tribute-section                   │ │      │
│   │        │                                                      │ │      │
│   │        │  TO:      URL: "/lobby/{lobbyId}"                 │ │      │
│   │        │           Section: tribute-section                 │ │      │
│   │        │           State: Tribute Creation (as player)      │ │      │
│   │        └──────────────────────────────────────────────────┘ │      │
│   │                                                                 │      │
│   └─────────────────────────────────────────────────────────────────┘      │
│                                                                             │
│   ┌─ Tribute Creation Phase ──────────────────────────────────────┐      │
│   │                                                                 │      │
│   │  FROM:  URL: "/lobby/{lobbyId}"                              │      │
│   │         Section: tribute-section                             │      │
│   │         State: Creating/Editing Tribute                      │      │
│   │                                                                 │      │
│   │  ACTIONS: User edits tribute form fields:                    │      │
│   │  - Select district                                           │      │
│   │  - Select gender                                             │      │
│   │  - Enter age                                                 │      │
│   │  - Enter name                                                │      │
│   │  - Drag skills to prioritize                                │      │
│   │                                                                 │      │
│   │  URL STATE: Unchanged: "/lobby/{lobbyId}"                  │      │
│   │             (State already captures "in lobby" context)      │      │
│   │                                                                 │      │
│   │  AUTO-SAVE: Tribute changes emit:                            │      │
│   │             socket.emit('update_tribute', {...})           │      │
│   │                                                                 │      │
│   │  NEXT:  USER COMPLETES TRIBUTE ─────────────────────────┐  │      │
│   │        │                                                  │  │      │
│   │        │  EVENT: user clicks "Done with Tribute"        │  │      │
│   │        │                                                  │  │      │
│   │        │  EMIT:  socket.emit('update_tribute', {        │  │      │
│   │        │         tribute_data,                           │  │      │
│   │        │         ready: true                             │  │      │
│   │        │  })                                              │  │      │
│   │        │                                                  │  │      │
│   │        │  RECEIVE: socket.on('lobby_updated', {         │  │      │
│   │        │           lobby: {players, ...},               │  │      │
│   │        │           ...                                   │  │      │
│   │        │  })                                              │  │      │
│   │        │                                                  │  │      │
│   │        │  UPDATE:  If tribute_ready === true:            │  │      │
│   │        │           window.updatePageURL(                │  │      │
│   │        │               'waiting:' + lobbyId           │  │      │
│   │        │           )                                      │  │      │
│   │        │           window.lobbyApp.showSection(         │  │      │
│   │        │               'lobby-section'                   │  │      │
│   │        │           )                                      │  │      │
│   │        │                                                  │  │      │
│   │        │  TO:      URL: "/lobby/{lobbyId}/waiting"      │  │      │
│   │        │           Section: lobby-section               │  │      │
│   │        │           State: Waiting for Game Start        │  │      │
│   │        │                                                  │  │      │
│   │        └──────────────────────────────────────────────┘  │      │
│   │                                                                 │      │
│   └─────────────────────────────────────────────────────────────────┘      │
│                                                                             │
│   ┌─ Waiting for Game Phase ──────────────────────────────────┐           │
│   │                                                               │           │
│   │  FROM:  URL: "/lobby/{lobbyId}/waiting"                   │           │
│   │         Section: lobby-section                            │           │
│   │         State: Waiting for Host to Start Game            │           │
│   │                                                               │           │
│   │  STATUS: Tributes ready: X/Y players                      │           │
│   │          Host can start when >= 2 tributes ready          │           │
│   │                                                               │           │
│   │  HOST ACTION: Clicks "Start Game"                         │           │
│   │               socket.emit('start_game', {lobby_id})      │           │
│   │                                                               │           │
│   │  RECEIVE: socket.on('game_starting', {                  │           │
│   │           lobby_id,                                       │           │
│   │           ...                                             │           │
│   │  })                                                         │           │
│   │                                                               │           │
│   │  REDIRECT: window.location.href = '/game/{lobbyId}'     │           │
│   │            (Full page load to game.html)                 │           │
│   │                                                               │           │
│   │  TO:      URL: "/game/{lobbyId}"                         │           │
│   │           Page: game.html                                │           │
│   │           State: Game In Progress                        │           │
│   │                                                               │           │
│   └───────────────────────────────────────────────────────────┘           │
│                                                                             │
│   ┌─ Session Recovery on Disconnect ──────────────────────────┐          │
│   │                                                               │          │
│   │  SCENARIO: Network drops while at "/lobby/{lobbyId}"     │          │
│   │                                                               │          │
│   │  1. Socket connection lost                                 │          │
│   │     - Socket.IO starts reconnection attempts              │          │
│   │     - Browser shows offline state                         │          │
│   │                                                               │          │
│   │  2. User manually refreshes or browser auto-reloads      │          │
│   │     - Browser requests: GET /lobby/{lobbyId}             │          │
│   │     - Server validates lobby exists                       │          │
│   │     - Server returns lobby.html                           │          │
│   │                                                               │          │
│   │  3. Client initialization runs:                           │          │
│   │     - DOMContentLoaded event fires                        │          │
│   │     - initializeLobbyPage() called                        │          │
│   │     - window.restoreStateFromURL() parses path           │          │
│   │     - Result: { type: 'lobby', lobbyId: 'abc123' }      │          │
│   │                                                               │          │
│   │  4. State restoration:                                     │          │
│   │     - Shows "Reconnecting to lobby..." message            │          │
│   │     - Sets window.lobbyPageState.selectedLobbyId         │          │
│   │     - Waits for socket connection                         │          │
│   │                                                               │          │
│   │  5. Socket reconnects:                                     │          │
│   │     - Server identifies player by socket session          │          │
│   │     - Server sends: socket.on('lobby_joined', {...})    │          │
│   │     - Includes previous tribute_data if submitted         │          │
│   │                                                               │          │
│   │  6. Client receives event:                                 │          │
│   │     - Updates currentPlayerId, currentLobbyId             │          │
│   │     - Shows tribute-section with existing data            │          │
│   │     - Calls updatePageURL() to confirm URL state          │          │
│   │                                                               │          │
│   │  RESULT: User back exactly where they were!              │          │
│   │          No data lost, no restart required                │          │
│   │                                                               │          │
│   └───────────────────────────────────────────────────────────┘          │
│                                                                             │
└──────────────────────────────────────────────────────────────────────────────┘
```

## State Transition Table

| From State | Trigger | To State | URL Change |
|-----------|---------|---------|-----------|
| Lobby Selection | Create lobby | Tribute Creation | `/` → `/lobby/{ID}` |
| Lobby Selection | Select & Join | Tribute Creation | `/` → `/lobby/{ID}` |
| Tribute Creation | Complete tribute | Waiting for Game | `/lobby/{ID}` → `/lobby/{ID}/waiting` |
| Waiting for Game | Host starts game | Game In Progress | `/lobby/{ID}/waiting` → `/game/{ID}` |
| Any State | Disconnect & Reconnect | Same State | URL Preserved |
| Any State | Back to selection | Lobby Selection | `/*` → `/` |
| Game In Progress | Game ends | Lobby Selection | `/game/{ID}` → `/` |

## URL State Recovery Logic

```javascript
// Page Load: Check Current URL
window.location.pathname = "/lobby/abc123"

↓

// Client calls restoreStateFromURL()
const urlState = {
    type: 'lobby',
    lobbyId: 'abc123'
};

↓

// If recovering from disconnect
if (urlState.type === 'lobby') {
    // Show "Reconnecting..." message
    // Wait for socket reconnection
    // Server will send lobby_joined or lobby_updated
}

↓

// When socket reconnects and server sends data
socket.on('lobby_joined', (data) => {
    currentPlayerId = data.player_id;
    currentLobbyId = data.lobby_id;
    // Load tribute data if exists
    // Show tribute-section
});

↓

// Client is back to normal state
// No user action required!
```

## Benefits Visualization

```
BEFORE (Root "/" for everything):
┌─────────────────────────────┐
│ User at: /                  │
│ State: Tribute Creation     │
│                             │
│ Network drops...            │
│ Page reloads...             │
│                             │
│ URL still: /                │
│ Server: "What lobby?"       │
│ Client: "Don't know..."     │
│                             │
│ Result: ❌ Lost & Confused  │
└─────────────────────────────┘

AFTER (URL reflects state):
┌─────────────────────────────┐
│ User at: /lobby/abc123      │
│ State: Tribute Creation     │
│                             │
│ Network drops...            │
│ Page reloads...             │
│                             │
│ URL still: /lobby/abc123    │
│ Server: "Here's abc123..."  │
│ Client: "Ah! Restore!"      │
│                             │
│ Result: ✅ Back on Track!   │
└─────────────────────────────┘
```

## Future Enhancement: Resume Links

```
Possible Future URL Format:
/lobby/{lobbyId}?resume={resumeCode}

Example:
/lobby/abc123?resume=XYZ789

Benefits:
- Players can paste link to rejoin
- Resume code auto-populated
- Eliminates manual code entry
- Works across devices
- Browser history preserved
```
