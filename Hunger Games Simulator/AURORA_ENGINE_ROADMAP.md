# Aurora Engine Development Roadmap

## Current Architecture Overview

### Key Components:
1. **Aurora Engine** (`Engine/Aurora Engine.py`) - Main orchestrator
2. **GameState** (`Engine/game_state.py`) - Manages all tributes, events, and game state
3. **Tribute** (`Engine/tribute.py`) - Individual tribute with stats and behavior
4. **PhaseController** - Manages game phases (Cornucopia, Day 1-3, etc.)
5. **AuroraIntegration** (`aurora_integration.py`) - Bridge to lobby_server
6. **NemesisBehaviorEngine** - AI decision-making (needs to be integrated)

### Web UI Integration Points:
- `engine_status_update` - Engine status + tribute scoreboards
- `game_update` - Game events and phase changes
- `animation_events` - Visual event data
- `/api/tribute/{player_id}` - Individual tribute details

---

## What's Working ✅
- Tribute creation with initial stats (health=100, sanity=100, hunger=0, etc.)
- Stat update methods exist (`update_health()`, `update_sanity()`, etc.)
- Tribute scoreboards can be retrieved with all stats
- Web UI displays stats in left sidebar and right sidebar

---

## What Needs to Be Fixed/Built 🔧

### Priority 1: Stat Updates During Gameplay
**Problem**: Tributes' stats don't change during the game. They're created at 100 health and stay there forever.

**Solution**: 
- [ ] Modify `generate_event()` in Aurora Engine to update stats based on events
  - Arena Events should cause damage/sanity loss
  - PvP Events should update health, fatigue, sanity
  - Time-based events should increment hunger/thirst/fatigue each phase
  
- [ ] Add phase-end stat updates in `check_timers_and_advance()`
  - Increment hunger by 5-10 per day
  - Increment thirst by 5-10 per day  
  - Increment fatigue by 3-5 per day
  - Apply natural decay effects
  
- [ ] Create combat resolution system
  - Roll skill checks for PvP combats
  - Calculate damage based on skills + weapons
  - Update health, apply bleeding wounds, etc.

### Priority 2: Event System Integration
**Problem**: Events don't actually affect tributes. "PvP: A and B encounter" is just flavor text.

**Solution**:
- [ ] Flesh out `_generate_random_encounter_event()` to:
  - Roll combat between two tributes
  - Update their health/sanity/fatigue
  - Record the outcome (kill, injury, flee, ally)
  
- [ ] Implement Arena Events to damage tributes:
  - Fire/cold/poison events should apply gradual damage
  - Natural disasters should cause injuries
  
- [ ] Implement Supply Events:
  - Food/water finds should reduce hunger/thirst
  - Medical supplies should heal wounds

### Priority 3: NemesisBehaviorEngine Integration
**Problem**: Tributes don't make intelligent decisions. They're passive.

**Solution**:
- [ ] Connect NemesisBehaviorEngine to each tribute
- [ ] Get behavior decisions each phase:
  - Should I attack? Flee? Hide? Search for food?
  - Decision should be based on stats (low health = hide, high hunger = search)
- [ ] Apply decisions to game events

### Priority 4: Real-Time Web UI Updates
**Problem**: Stats don't update in web UI during game.

**Solution**:
- [ ] After each event, emit `tribute_updated` socket event with new stats
- [ ] Include updated scoreboard data in `engine_status_update`
- [ ] Ensure tribute_scoreboards includes current stat values

### Priority 5: Death & Elimination
**Problem**: Tributes never die, even in combat.

**Solution**:
- [ ] Add death logic: if health ≤ 0, mark as dead
- [ ] Remove dead tributes from active events
- [ ] Broadcast death events to web UI
- [ ] Check win condition: if only 1 tribute alive, game ends

---

## Implementation Order

1. **Step 1**: Add phase-end stat decays (hunger/thirst/fatigue each phase)
   - Test: Run game, see stats change in web UI
   
2. **Step 2**: Implement basic combat (PvP events cause damage)
   - Test: Two tributes encounter, health decreases
   
3. **Step 3**: Add death detection and elimination
   - Test: Tributes die in combat, removed from arena
   
4. **Step 4**: Connect NemesisBehaviorEngine for decisions
   - Test: Tributes make decisions, events reflect their choices
   
5. **Step 5**: Full event system (arena hazards, resources, etc.)

---

## Key Data Flows to Establish

### Per-Phase Flow:
1. Phase starts
2. Each tribute gets behavior decision from NemesisBehaviorEngine
3. Events are generated based on:
   - Tribute locations
   - Tribute decisions
   - Random arena events
4. Events update tribute stats
5. **Socket events sent to web UI** ← This is critical!
6. Phase timer expires, go to next phase
7. Stats decay (hunger +5, thirst +5, fatigue +3)
8. Repeat

### Event Stat Update Flow:
```
Event Generated
  → If PvP: Apply damage to both tributes
  → If Arena: Apply hazard damage to affected tributes
  → If Supply: Update hunger/thirst for finder
  → Calculate stat changes
  → Emit 'tribute_updated' to web UI
  → Add to event log
```

---

## Files to Modify

- `Engine/Aurora Engine.py` - Add event impact logic
- `Engine/tribute.py` - Already good, just use existing update methods
- `Engine/game_state.py` - Add phase-end decay logic
- `aurora_integration.py` - Already good, ensure stat data flows to web
- `Nemesis Behavior Engine/` - Connect to tribute decision making
