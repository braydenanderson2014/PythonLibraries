# Enemy System Quick Reference

## Quick Start

### Mark Someone as Enemy
```python
relationship_manager.mark_as_enemy(
    "player1", "player2",
    priority=75.0,
    reason="Killed my ally"
)
```

### Create Enemy from Event
```python
# Auto-sets priority and trust based on event type
relationship_manager.create_enemy_from_event(
    "player1", "player2",
    "killed_ally"  # Priority: 90, Trust: -60
)
```

### Get All Enemies
```python
# Returns [(enemy_id, priority), ...] sorted by priority
enemies = relationship_manager.get_enemies("player1")

# Only high threats (70+)
high_threats = relationship_manager.get_enemies("player1", min_priority=70.0)
```

### Update Enemy Priority
```python
relationship_manager.update_enemy_priority(
    "player1", "player2",
    new_priority=95.0,
    reason="Got deadly weapon"
)
```

### Remove Enemy Status
```python
relationship_manager.remove_enemy_status(
    "player1", "player2",
    reason="Temporary truce"
)
```

## Event Types

| Event | Priority | Trust | When to Use |
|-------|----------|-------|-------------|
| `killed_ally` | 90 | -60 | Killed tribute's ally |
| `betrayal` | 85 | -50 | Betrayed alliance |
| `combat_attack` | 75 | -40 | Attacked in arena |
| `witnessed_kill` | 70 | -40 | Witnessed killing |
| `stole_supplies` | 60 | -35 | Stole resources |
| `skill_rivalry` | 30-80 | -20 | Similar skills |
| `resource_competition` | 55 | -25 | Competing for resources |

## Priority Tiers

```
0-30:   Low - Minor threat
30-50:  Medium - Moderate threat
50-70:  High - Serious threat
70-90:  Critical - Major threat
90-100: Extreme - Kill-on-sight
```

## Pre-defined Enemies (Web UI)

```json
{
  "player1|player2": {
    "trust": 15,
    "is_enemy": true,
    "enemy_priority": 75,
    "enemy_reason": "District rivalry",
    "relationship_type": "rival"
  }
}
```

## Nemesis Behavior Engine Effects

### Combat Priority Boost
- Base combat score + (enemy_priority / 100) × 0.4
- High-priority enemies (70+) get 1.5× priority multiplier
- Attack threshold lowered to 0.3 for high-priority enemies

### Avoidance Priority
- Base avoid priority: 0.7
- Multiplied by (1.0 + enemy_priority / 100)
- Max avoid priority: 1.0 (100%)

### Example
```python
# Normal tribute: Combat score 0.5 → Attack priority 0.4
# High-priority enemy (priority 80): Combat score 0.5 + 0.32 boost = 0.82
# → Attack priority 0.82 × 0.8 × 1.5 = 0.984 (very high!)
```

## Checking Enemy Status

```python
# Check if enemies
if relationship_manager.is_enemy("player1", "player2"):
    print("They are enemies!")

# Get relationship details
rel = relationship_manager.get_relationship("player1", "player2")
if rel.is_enemy:
    print(f"Priority: {rel.enemy_priority}")
    print(f"Reason: {rel.enemy_reason}")
    print(f"Created: Phase {rel.enemy_created_phase}")
```

## Summary Data

```python
# Get tribute's relationship summary
summary = relationship_manager.get_relationship_summary("player1")

# All enemies
for enemy in summary['enemies']:
    print(f"{enemy['id']}: Priority {enemy['priority']}")

# Only high-priority (70+)
for enemy in summary['high_priority_enemies']:
    print(f"THREAT: {enemy['id']} - {enemy['reason']}")
```

## Common Patterns

### Revenge Arc
```python
# Ally killed by enemy
relationship_manager.create_enemy_from_event(
    survivor_id, killer_id, "killed_ally"
)
# Priority: 90, Trust: 0 → Survivor will hunt killer
```

### Escalating Rivalry
```python
# Initial rivalry
relationship_manager.mark_as_enemy(
    "player1", "player2",
    priority=50, reason="Competition"
)

# Later: Player2 gets stronger
relationship_manager.update_enemy_priority(
    "player1", "player2",
    new_priority=75,
    reason="Now armed and dangerous"
)
```

### Temporary Truce
```python
# Enemies face common threat
relationship_manager.remove_enemy_status(
    "player1", "player2",
    reason="Truce against common enemy"
)
# Trust +10, enemy status removed
# Can become enemies again later
```

## Integration with Events

### In Aurora Engine
```python
def handle_kill_event(killer_id, victim_id, witnesses):
    # Update relationships for witnesses
    for witness_id in witnesses:
        # Create enemy relationship
        self.relationship_manager.create_enemy_from_event(
            witness_id, killer_id,
            "witnessed_kill"
        )
        
        # If victim was witness's ally, stronger enemy
        if self.relationship_manager.is_allied(witness_id, victim_id):
            self.relationship_manager.create_enemy_from_event(
                witness_id, killer_id,
                "killed_ally"
            )
```

### In Game Event Generation
```python
def generate_betrayal_event(betrayer_id, victim_id):
    # Create enemy relationship
    relationship_manager.create_enemy_from_event(
        victim_id, betrayer_id,
        "betrayal"
    )
    
    # Spread gossip (reputation -30)
    # Break alliance if existed
    # Generate event message
```

## Testing

Run comprehensive enemy system test:
```bash
cd "h:\Hunger Games Simulator\Aurora Engine"
python test_relationships.py
```

Test output includes:
- Dynamic enemy creation from events
- Pre-defined enemy setup
- Priority updates and filtering
- High-priority enemy identification
- Reconciliation mechanics
- Comprehensive summaries

## Files

- **RelationshipManager**: `Engine/relationship_manager.py`
- **Nemesis Integration**: `Nemesis Behavior Engine/NemesisBehaviorEngine.py`
- **Tests**: `test_relationships.py`
- **Documentation**: `docs/RELATIONSHIP_SYSTEM.md`, `docs/ENEMY_SYSTEM_SUMMARY.md`
