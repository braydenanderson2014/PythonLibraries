# Nemesis Behavior Engine

The Nemesis Behavior Engine is a sophisticated AI system that handles all tribute decision-making in the Hunger Games Simulator. It makes intelligent choices based on skill scores, district bonuses, medical conditions, resource availability, and social dynamics.

## Features

### 🎯 **Multi-Factor Decision Making**
- **Trait Scores**: Uses weighted skill priorities from web UI configuration
- **District Bonuses**: Applies district-specific advantages (e.g., District 1 combat bonus)
- **Medical Conditions**: Considers bleeding, infections, and limb injuries
- **Resource Management**: Evaluates available food, water, weapons, and medical supplies
- **Social Dynamics**: Handles alliances, enemies, and interpersonal relationships

### 🏥 **Medical Awareness**
- **Bleeding Management**: Prioritizes treatment of severe bleeding wounds
- **Infection Control**: Considers infection risks and treatment needs
- **Limb Injuries**: Accounts for penalties from arm/leg injuries on combat and gathering
- **Health Monitoring**: Adjusts risk-taking based on current health status

### ⚔️ **Combat Intelligence**
- **Weapon Effectiveness**: Uses weapon calculator to evaluate combat viability
- **Opponent Assessment**: Considers enemy health, weapons, and skills
- **Instant Kill Chances**: Factors in weapon-specific kill probabilities
- **Strategic Combat**: Only engages when odds are favorable

### 🤝 **Social Strategies**
- **Alliance Formation**: Identifies beneficial partnerships based on complementary skills
- **Betrayal Logic**: Considers when to break alliances (future enhancement)
- **Trust Assessment**: Evaluates district compatibility and shared enemies

### 🏞️ **Environmental Adaptation**
- **Location Safety**: Moves to safer areas when threatened
- **Resource Gathering**: Prioritizes needed supplies (food, water, medical)
- **Shelter Building**: Constructs shelter when night approaches
- **Strategic Positioning**: Hides when injured or outnumbered

## Action Types

The engine can choose from these action categories:

### Survival Actions
- `gather_food` - Collect food supplies
- `gather_water` - Collect water supplies
- `rest` - Recover fatigue
- `build_shelter` - Construct shelter
- `start_fire` - Build campfire

### Medical Actions
- `treat_bleeding` - Stop bleeding wounds
- `treat_infection` - Cure infections
- `gather_medical` - Find medical supplies

### Combat Actions
- `attack` - Engage specific enemy
- `gather_weapons` - Find better weapons
- `hide` - Avoid detection

### Social Actions
- `form_alliance` - Propose partnership
- `observe` - Gather intelligence

### Strategic Actions
- `move` - Change location
- `scavenge` - General resource gathering

## Usage

### Basic Usage

```python
from NemesisBehaviorEngine import NemesisBehaviorEngine

# Initialize the engine
engine = NemesisBehaviorEngine()

# Make a decision for a tribute
decision = engine.make_decision(tribute, game_state)

# Execute the decision
print(f"Action: {decision.action_type.value}")
if decision.target:
    print(f"Target: {decision.target}")
print(f"Priority: {decision.priority_score:.2f}")
```

### Integration with Aurora Engine

The behavior engine integrates seamlessly with the Aurora Engine tribute system:

```python
# Tribute has medical conditions that affect decisions
tribute.bleeding_wounds = [{"level": "severe", "location": "arm"}]
tribute.infections = [{"location": "leg"}]
tribute.extremities["left_arm"] = "injured"

# Engine considers these in decision making
decision = engine.make_decision(tribute, game_state)
# May prioritize medical treatment over combat
```

## Configuration

### District Bonuses
Located in `../../data/district_bonuses.json`:

```json
{
  "1": {"strength": 1.1, "combat": 1.1, "survival": 0.9},
  "2": {"intelligence": 1.1, "agility": 1.1, "combat": 0.9}
}
```

### Weapons & Conditions
Uses `../../data/weapons_and_conditions.json` for weapon effectiveness and medical conditions.

## Decision Factors

### Priority Scoring
Each action receives a score based on:

1. **Base Urgency** (0.0-1.0): How badly the action is needed
2. **Trait Alignment** (0.5-1.5): How well it matches tribute's strengths
3. **District Bonus** (0.9-1.2): District-specific modifiers
4. **Medical Modifier** (0.3-1.0): Health condition penalties
5. **Resource Modifier** (0.1-1.0): Resource availability
6. **Risk Modifier** (0.3-1.5): Risk tolerance adjustment
7. **Social Modifier** (0.1-1.5): Relationship considerations

### Final Score Calculation
```
final_score = base_score × trait_mod × district_mod × medical_mod × resource_mod × risk_mod × social_mod
```

## Testing

Run the test script to see the engine in action:

```bash
cd "Aurora Engine/Nemesis Behavior Engine"
python test_behavior_engine.py
```

This demonstrates a tribute with bleeding wounds making strategic decisions based on their high intelligence and strength scores.

## Future Enhancements

- **Betrayal Logic**: Dynamic alliance breaking
- **Long-term Planning**: Multi-phase strategy development
- **Personality Evolution**: Learning from past decisions
- **Event Response**: Reacting to arena events and announcements
- **Team Coordination**: Group decision-making for alliances

## Dependencies

- `utils.weapon_effectiveness.WeaponEffectivenessCalculator`
- `Engine.tribute.Tribute` class
- JSON configuration files for districts and weapons

The engine gracefully handles missing dependencies and provides fallback behavior.