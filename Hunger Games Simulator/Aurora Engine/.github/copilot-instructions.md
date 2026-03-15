# Aurora Engine - AI Coding Agent Instructions

## System Architecture

**Four-Layer Stack:**
1. **Web Layer** (`lobby_server.py`): FastAPI + Socket.IO for real-time multiplayer lobby
2. **Integration Layer** (`aurora_integration.py`): Bridges lobby to game engine
3. **Engine Layer** (`Engine/Aurora_Engine.py`): Core simulation for phases, events, stat decay
4. **AI Layer** (`Nemesis Behavior Engine/`): Sophisticated tribute decision-making AI

**Key Insight**: The engine is decoupled from networking. Always work through `AuroraLobbyIntegration` when connecting UI to engine logic. The Nemesis Behavior Engine operates independently for tribute AI decisions.

## Critical Data Flows

### Game Lifecycle
```
1. Players join lobby via Socket.IO
2. Admin starts game → AuroraLobbyIntegration.initialize_engine()
3. Game loop: process_game_tick() called every 1 second
4. Each tick checks: phase elapsed? → advance phase + apply stat decay
5. Each tick checks: event timer? → generate_event()
6. Results broadcast to all players via socket.emit('game_update', ...)
```

### Phase Advancement & Stat Decay (SEE: `aurora_integration.py` lines 163-176)
- **ALL phases must be processed** (Cornucopia, Day, Night) — no exclusions
- Stat decay applied automatically on phase end:
  - Hunger: +5, Thirst: +7, Fatigue: +4 per phase (from `config.json`)
  - Sanity floor enforced at 50 minimum
- Phase durations in `config.json` under `timers.phase_transitions`

### Admin Commands (SEE: `admin_controls.py`)
Real-time game control via Socket.IO events:
- `admin_force_next_phase`: Skip current phase timer
- `admin_force_next_event`: Generate event immediately  
- `admin_update_timing`: Modify `config.json` timers on-the-fly
- `admin_get_tribute_stats`: Query tribute health/stats

### Nemesis Behavior Engine Integration
- **AI Decision Making**: Tributes use `NemesisBehaviorEngine.make_decision()` for autonomous actions
- **Action Types**: 16 action types including survival, medical, combat, social, strategic
- **Multi-Factor Analysis**: Considers skills, district bonuses, medical conditions, resources, **relationships, and enemy priorities**
- **Relationship-Aware**: Uses RelationshipManager for trust-based decisions (alliances, betrayals, cooperation)
- **Enemy-Aware Combat**: Prioritizes attacking high-threat enemies (70+ priority), lowers attack threshold for enemies
- **Strategic Avoidance**: Scales avoidance priority by enemy threat level (up to 2x for extreme threats)
- **Action Queue Pattern**: Player actions should be queued and weighted against AI suggestions
```python
# Example integration pattern:
from Nemesis_Behavior_Engine.NemesisBehaviorEngine import NemesisBehaviorEngine
from Engine.relationship_manager import RelationshipManager

engine = NemesisBehaviorEngine()
rel_manager = RelationshipManager()
engine.set_relationship_manager(rel_manager)

decision = engine.make_decision(tribute, game_state)
# decision.action_type, .target, .priority_score, .risk_level available
# Decisions now consider trust, alliances, and enemy priorities
```

### Relationship & Enemy System (SEE: `Engine/relationship_manager.py`)
- **Trust Tracking**: 0-100 scale with 6 relationship types (Enemy, Rival, Neutral, Acquaintance, Ally, Close Ally)
- **Trust Decay**: 2% per phase toward neutral (50), alliances decay slower toward 70
- **Enemy System**: Track enemies with threat priority 0-100 (higher = greater threat)
- **Dynamic Enemy Creation**: 7 event types auto-create enemies (killed_ally, betrayal, combat_attack, witnessed_kill, stole_supplies, skill_rivalry, resource_competition)
- **Pre-defined Relationships**: Web UI can define alliances, rivalries, and enemies before game start
- **Betrayal Mechanics**: Multi-factor risk calculation based on trust + desperation
- **Gossip Network**: Betrayals spread negative reputation (-30), cooperation spreads positive (+10)
```python
# Example enemy creation from event:
relationship_manager.create_enemy_from_event(
    tribute_id, killer_id, "killed_ally"  # Priority: 90, Trust: -60
)

# Get high-priority enemies for combat decisions:
high_threats = relationship_manager.get_enemies(tribute_id, min_priority=70.0)
```

## Project Patterns & Conventions

### Dataclass Usage Pattern
```python
# In lobby_server.py - tributes are TributeData objects:
@dataclass
class TributeData:
    name: str
    skills: Dict[str, int]  # Always dict, never list
    # When serializing for Socket.IO, use serialize_for_socket() helper

# When passing to engine, convert: {"name": "...", "skills": {...}, ...}
```

### Socket.IO Event Pattern (SEE: `lobby_server.py` lines 587+)
```python
@sio.event
async def my_event(sid, data):
    try:
        result = await some_operation(data)
        await sio.emit('response_event', result, room=data['lobby_id'])
    except Exception as e:
        await sio.emit('error', {'error': str(e)}, to=sid)
```
**Convention**: Always emit response to `room=lobby_id` for broadcast to all players, not individual `to=sid`.

### Config Pattern (SEE: `Engine/config.json`)
```json
{
  "stat_decay_rates": { "hunger": 5, "thirst": 7, ... },
  "timers": {
    "event_cooldowns": { "Combat Events": 45, ... },
    "phase_transitions": { "cornucopia": 30, "day_phase": 60, ... }
  }
}
```
**Important**: Config is loaded once at engine init. Changes via `admin_update_timing` persist to disk but engine reads on next tick.

### Testing Pattern (SEE: `test_complete_game.py`, `test_phase_debug.py`)
```python
from aurora_integration import AuroraLobbyIntegration

integration = AuroraLobbyIntegration()
integration.initialize_engine("test_id", config_path="Engine/config.json")
integration.start_game(players)  # players = [{id, name, tribute_ready, tribute_data}]

# Simulate game loop:
for _ in range(10):
    messages = integration.process_game_tick()
    for msg in messages:
        print(msg)  # Process updates
```
Always create fresh `AuroraLobbyIntegration` instances per test/game to avoid state bleed.

## Connection & Transport Configuration

**Critical for stability** (SEE: `README_CONNECTION_FIXES.md`):
- Socket.IO timeout must be symmetric: **server ping_timeout=20s, client timeout=20s**
- Server sends ping every 8s (before timeout)
- Use polling-first transport strategy for proxy/Cloudflare compatibility:
  ```python
  socketio.AsyncServer(
      ping_timeout=20, ping_interval=8,
      transports=['polling', 'websocket'],  # polling FIRST
      ...
  )
  ```
- Uvicorn: Use `keepalive=5, timeout=15` to prevent mid-game disconnects

## Build & Test Commands

```powershell
# Start server (will listen on localhost:8000)
python lobby_server.py

# Run integration tests (from project root)
python test_complete_game.py      # Full game flow, 3 phases
python test_phase_debug.py        # Phase advancement & stat decay  
python test_aurora_integration.py # Config loading & engine init
python test_relationships.py      # Relationship & enemy system (17 test phases)

# Test Nemesis Behavior Engine
cd "Nemesis Behavior Engine"; python test_behavior_engine.py

# Check server health
curl http://localhost:8000/api/connection-diagnostics
```


## File Navigation

- **Game Simulation**: `Engine/Aurora_Engine.py` (1229 lines)
- **Relationships & Enemies**: `Engine/relationship_manager.py` (750+ lines)
- **Phase Control**: `Engine/Phase_Controller/phase_controller.py`
- **Lobby/Server**: `lobby_server.py` (1674 lines)
- **Integration Glue**: `aurora_integration.py` (272 lines)
- **Admin Control**: `admin_controls.py` (209 lines)
- **AI Decision Engine**: `Nemesis Behavior Engine/NemesisBehaviorEngine.py` (1100+ lines, enemy-aware)
- **Configuration**: `Engine/config.json`, `Engine/event_messages.json`
- **Event Definitions**: `Events/` directory (Arena, Combat, Custom, Idle, PvP event JSONs)

## When Adding Features

1. **Stat system change**: Update `config.json` stat_decay_rates, verify in test
2. **New event type**: Add to `event_messages.json`, implement in `Aurora_Engine.generate_event()`
3. **Admin command**: Add to `AdminControls` class, wire Socket.IO handler in `lobby_server.py`
4. **Networking fix**: Test with `test_connection_stability.py` before deployment
5. **Phase logic change**: Verify all phases process, add test case to `test_phase_debug.py`
6. **AI behavior change**: Modify `NemesisBehaviorEngine`, test with `test_behavior_engine.py`
7. **Relationship/enemy change**: Update `RelationshipManager`, test with `test_relationships.py`
8. **Event-based enemy creation**: Use `create_enemy_from_event()` with event type (killed_ally, betrayal, etc.)
7. **Player action integration**: Queue actions, weight against AI suggestions via Nemesis Engine
8. **Relationship/enemy change**: Update `RelationshipManager`, test with `test_relationships.py`
9. **Event-based enemy creation**: Use `create_enemy_from_event()` with event type (killed_ally, betrayal, etc.)

## Known Limitations & Enhancement Todos

See `docs/TODO_KNOWN_ISSUES.md` for:
- Cornucopia phase implementation needed
- Player action queue & behavior engine integration
- UI color scheme improvements
- Dead tribute badge bug at game start

## Recent Implementations (November 7, 2025)

**Enemy System** - Comprehensive enemy tracking with threat priorities:
1. Enemy tracking with 0-100 priority scale (higher = greater threat)
2. Dynamic enemy creation from 7 event types (killed_ally, betrayal, combat_attack, etc.)
3. Pre-defined enemies from web UI with custom priorities
4. Nemesis Behavior Engine enhancement: prioritizes attacking high-threat enemies (70+)
5. Strategic avoidance: scales avoidance priority by enemy threat level (up to 2x)
6. Complete test suite (8 test phases) and documentation (3 guides)

See `docs/ENEMY_SYSTEM_SUMMARY.md` and `docs/ENEMY_SYSTEM_QUICK_REFERENCE.md` for details.

## Recent Fixes Applied (Oct 30, 2025)

**Hard Redirect Bug** - Was causing socket disconnect on game start. Fixed by:
1. Removing `window.location.href = /game/{id}` hard redirects from `lobby.js`
2. Using SPA navigation in `app.js` instead
3. Passing socket directly instead of waiting for async initialization

**DOM Timing Issue** - Fixed by:
1. Checking for required DOM elements before signaling `client_ready`
2. Polling for elements until they exist (50ms interval, max 5 attempts)

See `docs/HARD_REDIRECT_FIX.md` and `docs/POLLING_TIMING_FIX.md` for details.

---

**Last Updated**: November 7, 2025
