# Enemy System Implementation Summary

## Overview

The Aurora Engine's RelationshipManager now includes a comprehensive **Enemy Tracking System** with threat priorities, dynamic enemy creation from game events, and full integration with the Nemesis Behavior Engine for strategic combat decisions.

## Key Features Implemented

### 1. Enemy Data Structure

Each relationship can now be marked as an enemy with:
- `is_enemy`: Boolean flag
- `enemy_priority`: Threat level 0-100 (higher = greater threat)
- `enemy_reason`: Description of why they became enemies
- `enemy_created_phase`: When enemy status was established

### 2. Priority Tiers

```
0-30:   Low priority - Minor threats
30-50:  Medium priority - Moderate threats
50-70:  High priority - Serious threats
70-90:  Critical priority - Major threats
90-100: Extreme priority - Kill-on-sight targets
```

### 3. Dynamic Enemy Creation

Enemies are automatically created from game events:

| Event Type | Priority | Trust Penalty | Description |
|------------|----------|---------------|-------------|
| `killed_ally` | 90 | -60 | Killed tribute's ally |
| `betrayal` | 85 | -50 | Betrayed alliance |
| `combat_attack` | 75 | -40 | Attacked in arena |
| `witnessed_kill` | 70 | -40 | Witnessed brutal kill |
| `stole_supplies` | 60 | -35 | Stole critical supplies |
| `skill_rivalry` | 30-80 | -20 | Overlapping skills (priority based on skill overlap) |
| `resource_competition` | 55 | -25 | Competing for resources |

### 4. Pre-defined Enemies (Web UI Support)

```json
{
  "tribute1_id|tribute2_id": {
    "trust": 15,
    "is_enemy": true,
    "enemy_priority": 75,
    "enemy_reason": "Historical district rivalry",
    "relationship_type": "rival"
  }
}
```

## API Methods

### Mark as Enemy
```python
relationship_manager.mark_as_enemy(
    tribute1_id="player1",
    tribute2_id="player2",
    priority=75.0,
    reason="Killed my district partner",
    trust_penalty=-40.0
)
```

### Dynamic Enemy Creation
```python
relationship_manager.create_enemy_from_event(
    tribute1_id="player1",
    tribute2_id="player2",
    event_type="killed_ally",
    tribute1_skills={"combat": 8},
    tribute2_skills={"combat": 9}
)
```

### Update Enemy Priority
```python
relationship_manager.update_enemy_priority(
    tribute1_id="player1",
    tribute2_id="player2",
    new_priority=95.0,
    reason="Obtained deadly weapon - now extreme threat"
)
```

### Get Enemies
```python
# All enemies sorted by priority descending
enemies = relationship_manager.get_enemies("player1", min_priority=0.0)
# Returns: [(enemy_id, priority), ...]

# Only high-priority enemies (70+)
high_threats = relationship_manager.get_enemies("player1", min_priority=70.0)
```

### Check Enemy Status
```python
if relationship_manager.is_enemy("player1", "player2"):
    print("They are enemies!")
```

### Reconciliation
```python
relationship_manager.remove_enemy_status(
    tribute1_id="player1",
    tribute2_id="player2",
    reason="Formed temporary truce to fight common enemy"
)
```

## Nemesis Behavior Engine Integration

### Combat Actions Enhanced

```python
def _generate_combat_actions(self, tribute, game_state):
    # Get high-priority enemies (70+)
    high_priority_enemies = relationship_manager.get_enemies(
        tribute.tribute_id, min_priority=70.0
    )
    
    for other_tribute in nearby_tributes:
        # Calculate base combat score
        combat_score = self._calculate_combat_viability(tribute, other_tribute)
        
        # Boost combat score for enemies based on priority
        if is_enemy:
            priority_boost = (enemy_priority / 100) * 0.4  # Up to +0.4
            adjusted_score = combat_score + priority_boost
            
            # Lower attack threshold for high-priority enemies
            if adjusted_score > 0.3 or is_high_priority_enemy:
                # 1.5x priority multiplier for high-priority enemies
                priority_multiplier = 1.5 if is_high_priority_enemy else 1.0
                
                # Generate ATTACK action with boosted priority
```

**Effect**: Tributes actively seek out and prioritize attacking their high-priority enemies, even if combat isn't normally favorable.

### Avoid Actions Enhanced

```python
def _generate_social_actions(self, tribute, game_state):
    if trust < 30 or relationship.is_enemy:
        # Calculate avoid priority based on enemy threat level
        avoid_priority = 0.7
        
        if relationship.is_enemy:
            # Higher priority to avoid more dangerous enemies
            threat_multiplier = 1.0 + (relationship.enemy_priority / 100)
            avoid_priority = min(1.0, avoid_priority * threat_multiplier)
        
        # Generate AVOID action with threat-adjusted priority
```

**Effect**: Tributes prioritize avoiding high-threat enemies (90+ priority) over lower threats.

## Test Results

From `test_relationships.py` enemy system tests:

### Phase 10: Dynamic Enemy Creation
```
District 7 male witnesses District 1 male kill an ally
→ Enemy status: True
→ Threat priority: 90/100
→ Trust: 0.0
→ Reason: "Killed my ally"
```

### Phase 12: Multiple Event Types
```
Betrayal:        Priority 85, Trust 0.0
Stole supplies:  Priority 60, Trust 15.0
Combat attack:   Priority 75, Trust 10.0
Witnessed kill:  Priority 70, Trust 10.0
```

### Phase 13: Skill Rivalry
```
Skills: {combat: 9, stealth: 8} vs {combat: 8, stealth: 9}
→ Priority: 32/100 (based on skill overlap)
→ Reason: "Skill rivalry detected"
```

### Phase 14: Priority Updates
```
Initial: 90/100
Updated: 95/100
Reason: "Obtained deadly weapon - now extreme threat"
```

### Phase 17: Summary Statistics
```
District 1 Male:
  - 4 total enemies
  - 1 high-priority enemy (70+): District 7 Male (95/100)

District 7 Male:
  - 2 total enemies
  - 1 high-priority enemy: District 1 Male (95/100)
  - Reason: "Killed my ally"
```

## Data Storage

Enemy data is included in:

### Game State Messages
```python
{
  "relationships": [
    {
      "tribute1_id": "player1",
      "tribute2_id": "player2",
      "trust": 15.0,
      "is_enemy": True,
      "enemy_priority": 75.0,
      "enemy_reason": "Killed my ally"
    }
  ]
}
```

### Relationship Summary
```python
{
  "tribute_id": "player1",
  "allies": ["player2"],
  "enemies": [
    {"id": "player3", "priority": 90, "reason": "Killed my ally"},
    {"id": "player4", "priority": 60, "reason": "Stole supplies"}
  ],
  "high_priority_enemies": [
    {"id": "player3", "priority": 90, "reason": "Killed my ally"}
  ]
}
```

### Save/Load State
Enemy data persists through save/load:
```python
state = relationship_manager.save_state()
# Includes: is_enemy, enemy_priority, enemy_reason, enemy_created_phase

relationship_manager.load_state(state)
# Restores all enemy data
```

## Use Cases

### 1. Pre-Game Rivalries
Set up historical rivalries via web UI before game starts:
```json
{
  "district1_male|district2_male": {
    "is_enemy": true,
    "enemy_priority": 70,
    "enemy_reason": "Historical district rivalry"
  }
}
```

### 2. Revenge Arcs
When tribute's ally is killed, automatically create high-priority enemy:
```python
# Ally killed event
relationship_manager.create_enemy_from_event(
    tribute_id,
    killer_id,
    "killed_ally"
)
# → Priority: 90, Trust: -60
```

### 3. Dynamic Threat Assessment
Enemy obtains powerful weapon or wins important fight:
```python
relationship_manager.update_enemy_priority(
    tribute_id,
    enemy_id,
    new_priority=95,
    reason="Now has deadly weapon"
)
```

### 4. Strategic Combat
Nemesis Behavior Engine uses enemy priorities for:
- Target selection in combat (prioritize high-threat enemies)
- Avoidance decisions (flee from overwhelming threats)
- Alliance formation (team up against common enemies)

### 5. Temporary Truces
Two enemies reconcile to fight common threat:
```python
relationship_manager.remove_enemy_status(
    tribute1_id,
    tribute2_id,
    "Formed temporary truce"
)
# → +10 trust, enemy status removed
```

## Future Enhancements

Potential additions:
1. **Enemy of my enemy**: Bonus to form alliances with tribute who shares your enemy
2. **Vengeance tracking**: Remember who killed allies, special events for revenge
3. **Fear system**: Very high-priority enemies (95+) cause tributes to flee even with good combat odds
4. **Rivalry escalation**: Skill rivalries increase in priority after repeated encounters
5. **Enemy networks**: Track who is allied with your enemies for strategic planning

## Files Modified

1. **Engine/relationship_manager.py** (+200 lines)
   - Added enemy fields to Relationship dataclass
   - Added `mark_as_enemy()`, `create_enemy_from_event()`, `update_enemy_priority()`
   - Added `get_enemies()`, `is_enemy()`, `remove_enemy_status()`
   - Updated `initialize_relationships()` to support pre-defined enemies
   - Updated `get_relationship_summary()` to include enemy data
   - Updated `get_all_relationships_data()` to include enemy data
   - Updated `save_state()` and `load_state()` for enemy persistence

2. **Nemesis Behavior Engine/NemesisBehaviorEngine.py** (+50 lines)
   - Enhanced `_generate_combat_actions()` to boost priority for high-threat enemies
   - Enhanced `_generate_social_actions()` to prioritize avoiding dangerous enemies
   - Combat threshold lowered for high-priority enemies (0.3 vs normal)
   - Avoid priority scaled by enemy threat level (up to 2x for extreme threats)

3. **test_relationships.py** (+200 lines)
   - Added 8 enemy system test phases (Phases 10-17)
   - Tests dynamic enemy creation, pre-defined enemies, event types
   - Tests skill rivalry calculation, priority updates, filtering
   - Tests reconciliation and comprehensive summary output

4. **docs/RELATIONSHIP_SYSTEM.md** (updated)
   - Added Enemy System section with priority tiers
   - Added dynamic enemy creation event table
   - Added enemy management API examples
   - Updated pre-defined relationship format examples

## Summary

The enemy system adds strategic depth to the Aurora Engine by:
- **Tracking threats**: 0-100 priority scale for enemy danger levels
- **Dynamic creation**: 7 event types automatically create enemies
- **Strategic combat**: Nemesis Behavior Engine prioritizes attacking high-threat enemies
- **Smart avoidance**: Tributes flee from overwhelming threats
- **Web UI integration**: Pre-define enemies and rivalries before game start
- **Full persistence**: Enemy data saves/loads with game state

Total implementation: **~450 new lines** across 4 files with comprehensive testing and documentation.
