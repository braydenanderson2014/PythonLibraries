# Weapons and Injury System - Complete Implementation Guide

## Overview

The Aurora Engine now features a comprehensive weapons and injury system with:
- **15 weapons** with full combat stats (damage, accuracy, speed, strength requirements, instant kill chances)
- **11 medical conditions** with skill modifiers, bleeding mechanics, and infection risk
- **Combat calculation system** with skill-based hit chance, damage scaling, and injury determination
- **Medical treatment mechanics** for healing wounds and curing infections
- **Ongoing injury effects** including bleeding damage, infection spread, and natural healing

## Quick Start

```python
from Engine.tribute import Tribute
from Engine.weapons_system import get_weapons_system

# Create tribute with weapons
tribute = Tribute('tribute_1', {
    'name': 'Katniss',
    'weapons': ['bow', 'knife'],
    'skills': {'combat': 8, 'strength': 6}
})

# Automatically equips best weapon for their strength
print(tribute.equipped_weapon)  # 'bow'

# Apply injury
tribute.add_condition('bleeding_mild')

# Get skills modified by injuries
modified = tribute.get_effective_combat_skills()
print(modified['strength'])  # Reduced by 15%

# Process ongoing effects (per phase)
result = tribute.process_condition_effects(phases_elapsed=1)
# Health reduced by bleeding damage
```

## System Architecture

### WeaponsSystem Class (`Engine/weapons_system.py`)

Central management system for all weapons and medical conditions.

**Key Components:**
- `Weapon` dataclass: Combat properties and calculation methods
- `Condition` dataclass: Injury properties and skill modifier application
- `WeaponsSystem` class: Main management and combat resolution

**Global Access:**
```python
from Engine.weapons_system import get_weapons_system
ws = get_weapons_system()
```

### Tribute Integration (`Engine/tribute.py`)

Tributes now have weapon management and injury tracking:

**New Fields:**
- `self.equipped_weapon`: Currently equipped weapon ID
- `self.conditions`: List of active medical conditions
- `self.bleeding_wounds`: Subset of conditions that are bleeding
- `self.infections`: Subset of conditions that are infected

**New Methods:**
- Weapon management: `add_weapon()`, `equip_weapon()`, `get_equipped_weapon()`
- Injury management: `add_condition()`, `remove_condition()`, `is_bleeding()`, `is_infected()`, `is_critically_injured()`
- Combat calculations: `get_effective_combat_skills()`
- Medical treatment: `treat_wounds()`
- Ongoing effects: `process_condition_effects()`

## Weapons System

### 15 Weapons with Full Stats

| Weapon | Type | Base Damage | Accuracy | Speed | Str Mult | Instant Kill | Str Req |
|--------|------|-------------|----------|-------|----------|--------------|---------|
| Fists | MELEE | 2 | 0.9 | 1.0 | 0.5 | 2% | 1 |
| Knife | MELEE | 4 | 0.8 | 0.9 | 0.3 | 8% | 2 |
| Sword | MELEE | 6 | 0.7 | 0.7 | 0.8 | 12% | 4 |
| Axe | MELEE | 8 | 0.6 | 0.5 | 1.0 | 15% | 5 |
| Spear | MELEE | 5 | 0.75 | 0.8 | 0.6 | 10% | 3 |
| Mace | MELEE | 7 | 0.65 | 0.6 | 0.9 | 14% | 5 |
| Trident | MELEE | 6 | 0.7 | 0.75 | 0.7 | 13% | 4 |
| Club | MELEE | 5 | 0.7 | 0.8 | 0.7 | 9% | 3 |
| Machete | MELEE | 5 | 0.75 | 0.8 | 0.5 | 11% | 3 |
| Bow | RANGED | 4 | 0.85 | 0.7 | 0.4 | 18% | 3 |
| Crossbow | RANGED | 6 | 0.9 | 0.4 | 0.6 | 22% | 4 |
| Slingshot | RANGED | 2 | 0.8 | 0.9 | 0.2 | 3% | 2 |
| Blowgun | RANGED | 1 | 0.95 | 1.0 | 0.0 | 5% | 1 |
| Throwing Knife | THROWN | 3 | 0.75 | 0.85 | 0.3 | 6% | 2 |
| Rock | THROWN | 2 | 0.6 | 1.0 | 0.4 | 1% | 1 |

### Combat Calculation Formula

**Hit Chance:**
```
base_chance = 40% + (combat_skill × 5%)  # Range: 40-90%
weapon_modifier = weapon.accuracy_modifier  # 0.6-0.95
dodge_modifier = 1.0 - (defender_agility / 10 × 0.2)  # Max -20%

final_hit_chance = base_chance × weapon_modifier × dodge_modifier
```

**Damage Calculation:**
```
base_damage = weapon.base_damage
strength_bonus = (strength - weapon.strength_requirement) × weapon.strength_multiplier
skill_bonus = combat_skill × 0.5
variance = random(-20%, +20%)

total_damage = (base_damage + strength_bonus + skill_bonus) × (1 + variance)
```

**Instant Kill Check:**
```
if random() < weapon.instant_kill_chance:
    defender.status = "dead"
```

**Strength Requirements:**
- If tribute strength < weapon requirement: Damage penalty applied
- If tribute strength >= weapon requirement: Full effectiveness
- Weak tributes cannot equip weapons above their strength

### Weapon Selection (Auto-Equip)

When a tribute acquires multiple weapons, the system auto-selects the best weapon:

```python
def get_best_weapon(weapons: List[str], strength: int) -> str:
    usable = [w for w in weapons if can_use_weapon(w, strength)]
    if not usable:
        return "fists"
    
    # Sort by: base_damage × strength_multiplier (descending)
    return max(usable, key=lambda w: w.base_damage * w.strength_multiplier)
```

**Example:**
- Tribute with strength 6 has: [bow, knife, sword, axe]
- Axe requires strength 5 (too heavy for strength 6?)
- System selects: **sword** (best damage for strength 6)

## Injury System

### 11 Medical Conditions

| Condition | Severity | Skill Modifiers | Bleeding | Infection Risk | Healing |
|-----------|----------|-----------------|----------|----------------|---------|
| **Healthy** | 0 | None | No | 0% | - |
| **Bruised** | 1 | -5% all physical | No | 0% | 2 phases |
| **Bleeding Mild** | 2 | -15% strength, -10% agility | 2 HP/phase | 20% | 3 phases |
| **Bleeding Medium** | 3 | -30% strength, -25% agility | 5 HP/phase | 40% | 6 phases |
| **Bleeding Severe** | 4 | -50% strength, -40% agility | 10 HP/phase | 60% | 12 phases |
| **Bleeding Fatal** | 5 | -80% strength, -70% agility | 15 HP/phase | 80% | Fatal (3 phases to death) |
| **Infected** | 3 | -30% all skills | No | - | Fatal (8 phases to death) |
| **Broken Arm** | 4 | -60% strength, -70% combat | No | 0% | 20 phases |
| **Broken Leg** | 4 | -80% agility, -50% combat | No | 0% | 20 phases |
| **Concussion** | 4 | -40% intelligence, -30% agility, -40% combat | No | 0% | 10 phases |
| **Poisoned** | 5 | -50% strength/agility, -60% combat | No | - | Fatal (5 phases to death) |

### Injury Determination (from Combat Damage)

Injuries are automatically determined based on damage dealt:

| Damage Range | Resulting Injury |
|--------------|------------------|
| 0-3 | Bruised |
| 3-5 | Bleeding Mild |
| 5-8 | Bleeding Medium |
| 8-12 | Bleeding Severe |
| 12+ | Bleeding Fatal |

### Skill Modifiers in Action

**Example: Tribute with Broken Arm**
```python
tribute.skills = {
    'strength': 8,
    'combat': 7,
    'agility': 6
}

tribute.add_condition('broken_arm')
modified = tribute.get_effective_combat_skills()

print(modified['strength'])  # 3.2 (-60%)
print(modified['combat'])    # 2.1 (-70%)
print(modified['agility'])   # 6.0 (no change)
```

**Example: Multiple Conditions**
```python
tribute.add_condition('bleeding_medium')  # -30% strength, -25% agility
tribute.add_condition('concussion')       # -40% all combat skills

modified = tribute.get_effective_combat_skills()
# Modifiers stack multiplicatively
# strength: 8 × 0.7 = 5.6
# combat: 7 × 0.6 = 4.2 (concussion penalty)
# agility: 6 × 0.75 × 0.7 = 3.15 (both penalties)
```

### Ongoing Injury Effects (Per Phase)

**Bleeding Damage:**
- Mild: 2 HP/phase
- Medium: 5 HP/phase
- Severe: 10 HP/phase
- Fatal: 15 HP/phase

**Infection Risk:**
- Each bleeding wound has a chance to become infected each phase
- Mild: 20% → Medium: 40% → Severe: 60% → Fatal: 80%
- Infected condition is fatal if untreated (8 phases to death)

**Natural Healing:**
- Minor injuries heal on their own over time
- Severe injuries (broken bones) take 20 phases
- Fatal conditions (fatal bleeding, infected, poisoned) do NOT heal naturally

**Processing:**
```python
# Call once per phase in game loop
result = tribute.process_condition_effects(phases_elapsed=1)

print(result['health_loss'])        # HP lost to bleeding
print(result['new_infections'])     # New infections from bleeding
print(result['conditions_healed'])  # Conditions that healed naturally
print(result['fatal'])              # True if tribute died from conditions
```

## Medical Treatment System

### Treating Wounds and Infections

```python
# Tribute needs medical supplies in inventory
tribute.inventory = ['medical_kit', 'bandage', 'medicine']

# Apply injuries
tribute.add_condition('bleeding_medium')
tribute.add_condition('infected')

# Attempt treatment
result = tribute.treat_wounds()

print(result['success'])           # True if treatment succeeded
print(result['wounds_treated'])    # ['bleeding_medium']
print(result['infections_cured'])  # ['infected']
print(result['message'])           # "Treated 1 wounds and 1 infections"
```

### Medical Supplies

| Item | Effect |
|------|--------|
| **Bandage** | Stop mild/medium bleeding (downgrade severity) |
| **Medicine** | Cure infection (remove infected condition) |
| **Medical Kit** | Treat both bleeding and infection |

### Treatment Success Rate

```python
success_chance = 0.5 + (medical_skill / 20.0) - (injury_severity / 20.0)
# Clamped to 20-95%

# Example:
# Intelligence 7, treating mild bleeding (severity 2)
# success = 0.5 + 7/20 - 2/20 = 0.5 + 0.35 - 0.1 = 0.75 (75%)
```

### Treatment Effects

**Bleeding:**
- Mild → Healed (becomes "bruised")
- Medium → Downgraded to mild
- Severe → Downgraded to medium
- Fatal → Downgraded to severe

**Infection:**
- Removed completely if treatment succeeds

**Medical Supply Consumption:**
- One medical item consumed per successful treatment
- Priority: medical_kit > medicine > bandage

## Combat Integration

### Full Combat Example

```python
from Engine.weapons_system import get_weapons_system

# Setup
ws = get_weapons_system()
attacker = Tribute('cato', {...})
defender = Tribute('thresh', {...})

# Ensure weapons equipped
attacker.equip_weapon('sword')
defender.equip_weapon('knife')

# Get modified skills (accounting for injuries)
attacker_skills = attacker.get_effective_combat_skills()
defender_skills = defender.get_effective_combat_skills()

# Calculate combat
result = ws.calculate_combat(
    attacker.get_equipped_weapon(),
    attacker_skills,
    attacker.conditions,
    defender_skills,
    defender.conditions
)

# Process result
if result['hit']:
    # Apply damage
    defender.update_health(-result['damage'], "combat")
    
    # Apply injury
    if result['new_condition']:
        defender.add_condition(result['new_condition'])
    
    # Check instant kill
    if result['instant_kill']:
        defender.status = "dead"
        print(f"{attacker.name} killed {defender.name} instantly!")
    else:
        print(result['description'])
        # Example: "The Sword hits for 12 damage, causing Severe Bleeding!"
```

## Nemesis Behavior Engine Integration

### Weapon-Aware Combat Decisions

```python
# In NemesisBehaviorEngine._generate_combat_actions()

# Get effective skills (modified by injuries)
modified_skills = tribute.get_effective_combat_skills()

# Check if tribute can fight effectively
combat_skill = modified_skills['combat']
if combat_skill < 3:
    # Too injured to fight, prioritize healing or fleeing
    return self._generate_avoidance_actions(...)

# Check weapon strength requirements
equipped = tribute.get_equipped_weapon()
weapon = ws.get_weapon(equipped)
if not weapon.can_use(modified_skills['strength']):
    # Too weak for equipped weapon, switch to lighter weapon
    lighter_weapons = [w for w in tribute.weapons 
                      if ws.get_weapon(w).can_use(modified_skills['strength'])]
    if lighter_weapons:
        tribute.equip_weapon(lighter_weapons[0])
```

### Injury-Aware Decision Making

```python
# Check injury status before making decisions
if tribute.is_critically_injured():
    # Reduce aggression, prioritize survival
    aggression_modifier = 0.3
    
    if tribute.is_bleeding():
        # URGENT: Find medical supplies or treat wounds
        return {'action': 'FIND_MEDICAL_SUPPLIES', 'priority': 95}
    
    if tribute.is_infected():
        # URGENT: Find medicine
        return {'action': 'FIND_MEDICINE', 'priority': 90}

# Normal decision-making with modified skills
decision = self.make_decision(tribute, modified_skills, context)
```

### New Action Types for Medical System

Add these to Nemesis Behavior Engine:

```python
ActionType.TREAT_BLEEDING = "treat_bleeding"      # Use bandages to stop bleeding
ActionType.TREAT_INFECTION = "treat_infection"    # Use medicine for infection
ActionType.REST_TO_HEAL = "rest_to_heal"          # Natural healing for minor injuries
ActionType.FIND_MEDICAL_SUPPLIES = "find_medical" # Search for medical items
```

## Event Generation Integration

### Combat Events with Weapons

```python
# In Aurora_Engine.generate_event()

def generate_combat_event(attacker, defender):
    ws = get_weapons_system()
    
    # Get combat-ready skills
    attacker_skills = attacker.get_effective_combat_skills()
    defender_skills = defender.get_effective_combat_skills()
    
    # Calculate combat
    result = ws.calculate_combat(
        attacker.get_equipped_weapon(),
        attacker_skills,
        attacker.conditions,
        defender_skills,
        defender.conditions
    )
    
    # Generate event message
    if result['instant_kill']:
        message = f"{attacker.name} kills {defender.name} with a deadly strike from their {result['weapon']}!"
        defender.status = "dead"
    elif result['hit']:
        defender.update_health(-result['damage'], "combat")
        defender.add_condition(result['new_condition'])
        message = result['description']
        # Example: "Cato hits Thresh with Sword for 12 damage, causing Severe Bleeding!"
    else:
        message = f"{attacker.name} attacks {defender.name} with {result['weapon']}, but misses!"
    
    return {
        'type': 'combat',
        'message': message,
        'attacker': attacker.id,
        'defender': defender.id,
        'result': result
    }
```

### Injury-Based Events

```python
def generate_injury_events(tribute):
    """Generate events for ongoing injury effects"""
    events = []
    
    if tribute.is_bleeding():
        severity = max([ws.get_condition(c).severity.value 
                       for c in tribute.bleeding_wounds])
        
        if severity >= 4:
            events.append({
                'type': 'injury',
                'message': f"{tribute.name} is bleeding heavily and growing dangerously weak.",
                'tribute': tribute.id
            })
    
    if tribute.is_infected():
        events.append({
            'type': 'injury',
            'message': f"{tribute.name}'s wound has become infected. Fever sets in.",
            'tribute': tribute.id
        })
    
    if tribute.is_critically_injured():
        conditions = [ws.get_condition(c).name for c in tribute.conditions 
                     if ws.get_condition(c).severity.value >= 4]
        events.append({
            'type': 'injury',
            'message': f"{tribute.name} struggles to move with {', '.join(conditions)}.",
            'tribute': tribute.id
        })
    
    return events
```

### Medical Treatment Events

```python
def generate_medical_event(tribute, ally=None):
    """Generate medical treatment events"""
    
    if ally:
        # Ally treats tribute's wounds
        result = tribute.treat_wounds(medical_skill=ally.skills['intelligence'])
        if result['success']:
            message = f"{ally.name} treats {tribute.name}'s wounds. "
            if result['wounds_treated']:
                message += f"Stopped bleeding. "
            if result['infections_cured']:
                message += f"Cured infection."
            return {'type': 'medical', 'message': message}
    else:
        # Self-treatment
        result = tribute.treat_wounds()
        if result['success']:
            return {
                'type': 'medical',
                'message': f"{tribute.name} treats their own wounds. {result['message']}"
            }
        else:
            return {
                'type': 'medical',
                'message': f"{tribute.name} attempts to treat their wounds but fails."
            }
```

## Phase Processing

### Per-Phase Updates

Add to phase advancement logic in `Aurora_Engine.py`:

```python
def advance_phase(self):
    """Process phase end effects"""
    
    # Process ongoing injury effects for all living tributes
    for tribute in self.get_living_tributes():
        result = tribute.process_condition_effects(phases_elapsed=1)
        
        # Generate event if significant health loss
        if result['health_loss'] > 5:
            self.add_event({
                'type': 'injury_effect',
                'message': f"{tribute.name} loses {result['health_loss']} HP from bleeding.",
                'tribute': tribute.id
            })
        
        # Generate event for new infections
        for infection in result['new_infections']:
            self.add_event({
                'type': 'infection',
                'message': f"{tribute.name}'s wounds have become infected!",
                'tribute': tribute.id
            })
        
        # Check for death from injuries
        if result['fatal'] or tribute.health <= 0:
            tribute.status = "dead"
            self.add_event({
                'type': 'death',
                'message': f"{tribute.name} succumbs to their injuries.",
                'tribute': tribute.id
            })
    
    # Continue with normal phase advancement (stat decay, etc.)
    self._apply_stat_decay()
    self._advance_phase_timer()
```

## Testing

### Run Test Suite

```bash
python test_weapons_injuries.py
```

**Test Coverage:**
1. **Weapon Management** - Equipping, auto-selection, strength requirements
2. **Injuries and Conditions** - Application, skill modifiers, critical injuries
3. **Medical Treatment** - Treating wounds, curing infections, success rates
4. **Combat Simulation** - Full combat with weapons, damage, injuries
5. **Ongoing Effects** - Multi-phase bleeding, infection spread, death

### Manual Testing

```python
# Test weapon effectiveness
tribute = Tribute('test', {'weapons': ['sword', 'bow'], 'skills': {'strength': 8}})
print(f"Best weapon: {tribute.equipped_weapon}")  # Should select based on strength

# Test injury penalties
tribute.add_condition('bleeding_severe')
modified = tribute.get_effective_combat_skills()
print(f"Combat reduced: {tribute.skills['combat']} → {modified['combat']}")

# Test bleeding progression
for phase in range(5):
    result = tribute.process_condition_effects()
    print(f"Phase {phase}: Lost {result['health_loss']} HP, Health: {tribute.health}")
```

## Configuration

### Adding New Weapons

Edit `Engine/weapons_system.py`, `WeaponsSystem._load_default_weapons()`:

```python
self.weapons['custom_weapon'] = Weapon(
    weapon_id='custom_weapon',
    name='Custom Weapon',
    weapon_type=WeaponType.MELEE,
    base_damage=7,
    accuracy_modifier=0.75,
    speed_modifier=0.7,
    strength_multiplier=0.8,
    instant_kill_chance=0.15,
    strength_requirement=5
)
```

### Adding New Conditions

Edit `Engine/weapons_system.py`, `WeaponsSystem._load_default_conditions()`:

```python
self.conditions['custom_injury'] = Condition(
    condition_id='custom_injury',
    name='Custom Injury',
    severity=InjurySeverity.MODERATE,
    modifiers={'combat': -0.3, 'strength': -0.4},
    bleeding=True,
    bleeding_level='medium',
    infection_risk=0.5,
    natural_healing_phases=8
)
```

## Summary

**Weapons System:**
- 15 weapons with realistic combat stats
- Skill-based hit chance (40-90%)
- Damage scaling with strength and combat skill
- Instant kill mechanics (1-22% depending on weapon)
- Strength requirements prevent weak tributes from using heavy weapons

**Injury System:**
- 11 medical conditions with skill penalties
- Bleeding damage (2-15 HP/phase)
- Infection risk and spread
- Natural healing for minor injuries
- Fatal conditions require treatment

**Integration:**
- Tributes auto-equip best weapon for their strength
- Injuries modify skills used in behavior decisions
- Combat generates injuries based on damage
- Medical treatment with success rates
- Phase-by-phase injury progression

**Next Steps:**
1. Integrate with Nemesis Behavior Engine for injury-aware decisions
2. Update Aurora Engine combat events to use weapon system
3. Add medical treatment events and action types
4. Test full combat flow with multiple tributes

---

**Files:**
- Core: `Engine/weapons_system.py` (900+ lines)
- Integration: `Engine/tribute.py` (new methods added)
- Tests: `test_weapons_injuries.py` (5 comprehensive tests)
- Docs: This guide

**Status:** ✅ Complete and tested
