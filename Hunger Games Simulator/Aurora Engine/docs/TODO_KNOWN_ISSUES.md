# Aurora Engine - Known Issues & Enhancement Todos

## Status: 🎉 WORKING - Game loads and runs successfully!

---

## Todo 1: Cornucopia Phase & Fist Weapons

**Priority:** HIGH  
**Affected Files:** `Engine/Aurora_Engine.py`, `Engine/Phase_Controller/phase_controller.py`, `Engine/config.json`

### Problem
1. First phase should be **Cornucopia phase** where tributes decide whether to rush the supplies
2. Tributes without arms should still be able to use **fists as weapons**
3. Currently missing Cornucopia decision logic

### What Needs to Happen
- Tributes get presented with Cornucopia event at game start
- Tributes can choose: Rush cornucopia (risky) OR avoid it (safer)
- Cornucopia contains weapons/supplies that give temporary boosts
- Tributes without weapons default to using fists (damage based on strength stat)

### Implementation Details
- **Phase structure:** Cornucopia → Day Phase → Night Phase (already in config)
- **Weapons system:** Add fists as default weapon when `equipped_weapon` is None
- **Cornucopia event:** Generate at phase start asking tributes for decision
- **Integration with Nemesis Behavior Engine:** Behavior engine should suggest whether to rush or not

### Related Code
- `Engine/Aurora_Engine.py` - `generate_event()`, weapon selection logic
- `Engine/Phase_Controller/phase_controller.py` - Phase transitions
- `Engine/config.json` - Event cooldowns for Cornucopia events
- `Nemesis Behavior Engine/NemesisBehaviorEngine.py` - Behavior suggestions

### Expected Behavior
```
Game Start: Cornucopia Phase begins
Event: "The Cornucopia awaits! Do you rush for supplies or avoid the bloodbath?"
Player sees: Fight/Flee/Ally buttons
Behavior Engine: Suggests best choice based on tribute stats
Result: Cornucopia combat events generate if tributes clash
```

---

## Todo 2: Color Scheme & Text Visibility in Tribute Status

**Priority:** HIGH  
**Affected Files:** `static/css/style.css`, `templates/game.html`

### Problem
- Yellow text on light background is hard to read
- Tribute stats sidebar has low contrast
- Other text colors not dark enough for visibility

### Specific Issues
1. Skill priority ratings show in yellow - barely visible
2. Health/Hunger/Thirst/Fatigue stat labels are too light
3. Overall tribute status box needs better contrast

### What Needs to Change
- Dark background for tribute stats area
- High-contrast text colors (white, bright colors on dark)
- Better visual hierarchy between labels and values
- Color-coded stat bars (green=healthy, red=critical, etc.)

### Implementation Details
- Update `.tribute-scoreboards-sidebar` styling
- Update `.player-tribute-stats` styling
- Ensure WCAG AA contrast ratio (4.5:1 for text)
- Use dark backgrounds (#1a1a1a or similar) for stat boxes
- Use white text (#ffffff) for labels
- Keep color-coded bars for quick visual reference

### Related Code
- `static/css/style.css` - All styling
- `static/js/game.js` lines 670-840 - HTML generation for tribute stats

### Testing
```
Check readability on:
- Light theme monitor
- Dark theme monitor  
- Full screen
- Dev tools open
```

---

## Todo 3: Remaining Tributes Show as DEAD at Game Start

**Priority:** HIGH  
**Affected Files:** `Engine/Aurora_Engine.py`, `static/js/game.js`

### Problem
- When game starts, remaining tributes show "DEAD" status badge
- This makes no sense - game just started, everyone should be alive
- Dead tributes should show after they're actually eliminated

### Root Cause
- Tributes likely initialized with `alive: False` or default status is wrong
- Status rendering logic not checking actual game state

### What Needs to Happen
1. Ensure tributes start with `alive: True`
2. Only show "DEAD" badge when tribute has actually died (health = 0 or eliminated)
3. Add status tracking: "ALIVE", "DEAD", "UNKNOWN"
4. Update display logic to respect actual alive status

### Implementation Details
- Check `Engine/game_state.py` - tribute initialization
- Check `Engine/Aurora_Engine.py` - tribute creation in `start_game()`
- Update `static/js/game.js` tribute rendering (lines ~520-620) to show actual status
- Add status field to tribute data model if missing

### Related Code
```python
# Engine/Aurora_Engine.py - start_game()
for player in players:
    tribute = Tribute(...)
    tribute.alive = True  # ✅ Ensure this is set
    tribute.health = 100  # ✅ Should start healthy
    engine.tributes.append(tribute)
```

```javascript
// static/js/game.js - updateTributeScoreboards()
const statusBadge = tribute.alive ? 'ALIVE' : 'DEAD';  // ✅ Show correct status
```

### Testing
```
1. Start game with 3+ tributes
2. Check remaining tributes panel
3. All should show ALIVE (no DEAD badges)
4. Kill a tribute via admin command
5. That tribute should now show DEAD
```

---

## Todo 4: Fight/Flee/Ally Buttons - Queue & Behavior Engine Integration

**Priority:** MEDIUM  
**Affected Files:** `admin_controls.py`, `Engine/Aurora_Engine.py`, `Nemesis Behavior Engine/NemesisBehaviorEngine.py`, `lobby_server.py`

### Problem
- Fight/Flee/Ally buttons show "processing" when clicked
- But engine has no handler for player actions
- Actions are lost/ignored
- Need to integrate with Nemesis Behavior Engine

### Desired Behavior
1. Player clicks action (Fight/Flee/Ally)
2. Action is **queued** for processing
3. **Behavior Engine suggests** what tribute should actually do
4. Weighted decision: Player intent vs Behavior suggestion
5. Action processed based on decision

### Implementation Plan

#### Step 1: Create Player Action Queue
```python
# Engine/Aurora_Engine.py
class PlayerAction:
    def __init__(self, player_id, action, timestamp):
        self.player_id = player_id
        self.action = action  # 'fight', 'flee', 'ally'
        self.timestamp = timestamp
        self.processed = False

self.action_queue = []  # Store pending actions
```

#### Step 2: Socket Handler for Actions
```python
# lobby_server.py
@sio.event
async def player_action(sid, data):
    """Handle Fight/Flee/Ally player actions"""
    action = data.get('action')  # 'fight', 'flee', 'ally'
    lobby_id = data.get('lobby_id')
    
    # Queue the action
    if lobby_id in active_games:
        active_games[lobby_id].queue_player_action(sid, action)
        await sio.emit('action_queued', {
            'action': action,
            'status': 'pending'
        }, to=sid)
```

#### Step 3: Behavior Engine Integration
```python
# Engine/Aurora_Engine.py - process_game_tick()
def process_player_actions(self):
    """Process queued player actions through behavior engine"""
    for action in self.action_queue:
        tribute = self.get_tribute(action.player_id)
        
        # Get behavior suggestion
        suggestion = self.behavior_engine.get_action_suggestion(
            tribute,
            current_situation,
            player_action=action.action
        )
        
        # Weight: 60% behavior, 40% player intent
        final_action = self.weighted_decision(
            player_wants=action.action,
            behavior_suggests=suggestion,
            weights={'behavior': 0.6, 'player': 0.4}
        )
        
        # Execute final action
        self.execute_action(tribute, final_action)
        action.processed = True
```

#### Step 4: Action Types
- **Fight:** Tribute engages in combat with nearby tributes
- **Flee:** Tribute runs away from current location
- **Ally:** Tribute attempts to form alliance with nearby tributes

### Related Code
- `admin_controls.py` - Could extend for action handling
- `Engine/Aurora_Engine.py` - Add `queue_player_action()`, `process_player_actions()`
- `Nemesis Behavior Engine/NemesisBehaviorEngine.py` - Add `get_action_suggestion()`
- `lobby_server.py` - Add `player_action` event handler
- `static/js/game.js` lines 350-380 - Update button handlers to emit actions

### Testing Scenario
```
1. Start game
2. Generate PvP event: "Two tributes encounter each other!"
3. Player clicks "Fight" button
4. Console: "Action queued: fight"
5. Behavior engine decides: "This tribute should FLEE (low strength)"
6. Final decision: FLEE (60% behavior weight)
7. Event shows: "Tribute ran away!"
```

### Console Output Expected
```
[ACTION_QUEUE] Player action queued: fight
[BEHAVIOR_ENGINE] Suggestion: flee (confidence: 0.85)
[ACTION_DECISION] Weighted result: flee (player: fight @ 0.4, behavior: flee @ 0.6)
[ACTION_EXECUTE] Tribute fled the encounter
```

---

## Summary of Fixes Needed

| Todo | Priority | Complexity | Status |
|------|----------|-----------|--------|
| Cornucopia Phase & Fists | HIGH | Medium | 📋 TODO |
| Color Scheme (Text Visibility) | HIGH | Low | 📋 TODO |
| Dead Badge at Game Start | HIGH | Low | 📋 TODO |
| Player Actions & Behavior Integration | MEDIUM | High | 📋 TODO |

---

## Related Documentation
- See `docs/HARD_REDIRECT_FIX.md` - How we fixed the socket disconnect issue
- See `docs/POLLING_TIMING_FIX.md` - How we fixed DOM timing
- See `.github/copilot-instructions.md` - Architecture & patterns guide

---

**Last Updated:** October 30, 2025  
**Session:** Game initialization working, now addressing gameplay mechanics
