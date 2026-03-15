# URL State Management & Session Recovery

## Problem
Previously, all lobby-related pages (lobby selection, tribute creation, waiting room) were served from the root `/` path. This caused issues:

1. **No session recovery on disconnect** - If the page reloaded or connection was lost, the app had no way to know:
   - Which lobby you were in
   - Which player ID you were
   - What state you should be in (tribute creation vs waiting for game)

2. **No meaningful browser history** - Back/forward buttons couldn't navigate between states

3. **URL inconsistency** - Only the game page (`/game/{lobbyId}`) changed the URL, creating state mismatch

## Solution
Implement URL-based state preservation. The URL now reflects the exact state of the application:

### URL Routes

| URL | State | Purpose |
|-----|-------|---------|
| `/` | Lobby Selection | Browse and select lobbies |
| `/lobby/{lobbyId}` | Tribute Creation | In a lobby, creating/editing tribute |
| `/lobby/{lobbyId}/waiting` | Waiting for Game | Tribute submitted, waiting for host to start |
| `/game/{lobbyId}` | Game In Progress | Game page (handled by game.js) |

### Implementation Details

#### Server-Side (lobby_server.py)
Added three new routes:
- `GET /lobby/{lobby_id}` - Serves lobby.html for tribute creation
- `GET /lobby/{lobby_id}/waiting` - Serves lobby.html for waiting state
- Existing routes preserved for backward compatibility

#### Client-Side (static/js/lobby.js)

**Key Functions:**

1. **`window.updatePageURL(state)`** - Updates browser URL using `history.pushState()`
   - Accepts state strings like `'lobbies'`, `'lobby:LOBBYID'`, `'waiting:LOBBYID'`
   - Only updates if URL actually changed (avoids redundant history entries)
   - Logs all URL changes for debugging

2. **`window.restoreStateFromURL()`** - Parses current URL to determine state
   - Used on page load to recover from disconnections
   - Returns object with `type` and `lobbyId` properties

3. **`window.handlePopState(event)`** - Handles browser back/forward button
   - Enables meaningful browser history navigation

**Integration Points:**

The URL is updated at these key events:
- `selectLobby()` → Sets URL to `/lobby/{lobbyId}`
- `lobby_joined` event → Sets URL to `/lobby/{lobbyId}`
- `lobby_created` event → Sets URL to `/lobby/{lobbyId}`
- `lobby_updated` (tribute ready) → Sets URL to `/lobby/{lobbyId}/waiting`
- `backToLobbySelection()` → Sets URL to `/`
- `resetToLogin()` → Sets URL to `/`

## Usage Example

### User Journey with URL Changes

1. User opens browser → `/` (Lobby Selection)
2. Clicks "Create Lobby" → `/` (Shows form)
3. Submits form → `/lobby/abc123` (Tribute Creation)
4. Finishes tribute → `/lobby/abc123/waiting` (Waiting Room)
5. Host starts game → `/game/abc123` (Game starts)

### Session Recovery

If connection drops while at `/lobby/abc123/waiting`:
1. Page reloads or user manually refreshes
2. Browser navigates to `/lobby/abc123/waiting`
3. Server serves lobby.html with `lobby_id=abc123` in template context
4. Client-side can now use URL to determine previous state
5. Socket reconnects and re-syncs with server

## Benefits

✅ **State Preservation** - URL encodes current state, survives page reloads
✅ **Session Recovery** - Rejoining at correct state after disconnection
✅ **Browser History** - Back button navigates between states (future implementation)
✅ **Deep Linking** - URLs can be bookmarked or shared (with player context)
✅ **Debugging** - Network tab shows exact state at any time
✅ **Consistent UX** - Every screen change reflected in address bar

## Future Enhancements

1. **State Restoration Logic** - Fully implement `handlePopState()` to restore state when using back button
2. **URL Parameters** - Add player ID to URL: `/lobby/{lobbyId}?player={playerId}`
3. **Resume Links** - Generate shareable resume links with resume code: `/lobby/{lobbyId}?resume={code}`
4. **Analytics** - Track state transitions via URL changes in analytics
5. **Deep Linking** - Share specific game states as URLs (e.g., spectator join links)

## Technical Notes

- Uses `history.pushState()` for non-destructive URL changes (no page reload)
- Each state change creates a new browser history entry
- Back/forward buttons navigate through history (ready for implementation)
- Works with Cloudflare Tunnel (no CORS issues, all same origin)
- Socket.IO connection persists across URL changes (no page reload)
