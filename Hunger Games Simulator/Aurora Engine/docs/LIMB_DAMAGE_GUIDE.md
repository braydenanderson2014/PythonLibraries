# Limb Damage & Dismemberment System - Complete Guide

## Overview

The Aurora Engine now features a realistic limb damage system with body part targeting, dismemberment, and disabilities:

- **6 Body Parts**: Head, Torso, Left/Right Arms, Left/Right Legs
- **Dismemberment**: Limbs can be severed with heavy weapons (15+ damage)
- **Disabilities**: No arms = can't hold weapon, No legs = can't walk, Hobbling with one leg
- **Limb-Specific Wounds**: Different wounds affect different skills
- **Realistic Penalties**: Head trauma affects intelligence, arm wounds affect strength/combat, leg wounds affect agility
- **Bleeding & Infection**: Severed limbs bleed 15-25 HP/phase, infection risk up to 70%

## Quick Start

```python
from Engine.tribute import Tribute

# Create tribute
tribute = Tribute('tribute1', {
    'name': 'Katniss',
    'weapons': ['sword'],
    'skills': {'combat': 8, 'strength': 7}
})

# Apply wound to specific body part
result = tribute.apply_limb_wound("left_arm", "sword", damage=12)
print(result['wound_type'])  # "slash"
print(result['severity'])     # 4
print(result['bleeding_rate']) # 10 HP/phase

# Check if severed
if result.get('severed'):
    print("Limb was severed!")

# Get skill penalties
penalties = tribute.get_limb_penalties()
# {'strength': -0.60, 'combat': -0.70}

# Get effective skills (with all modifiers)
skills = tribute.get_effective_combat_skills_with_limbs()
# Automatically includes limb damage AND condition penalties

# Process ongoing effects each phase
effects = tribute.process_limb_damage_effects(phases_elapsed=1)
print(effects['health_loss'])  # HP lost to bleeding
print(effects['new_infections'])  # Newly infected wounds
```

## Body Parts & Hit Chances

### Body Part Targeting

When combat occurs, the system determines which body part is hit based on size and vulnerability:

| Body Part | Hit Chance | Notes |
|-----------|------------|-------|
| Head | 15% | Small but vulnerable - instant death at 16+ damage |
| Torso | 40% | Largest target - affects endurance |
| Left Arm | 10% | Can be severed - affects weapon use |
| Right Arm | 10% | Can be severed - affects weapon use |
| Left Leg | 12.5% | Can be severed - affects movement |
| Right Leg | 12.5% | Can be severed - affects movement |

**Targeted Attacks:**
- Can specify body part to target
- 70% chance to hit targeted part
- 30% chance to hit adjacent part

```python
# In combat calculation
result = ws.calculate_combat(
    attacker_weapon,
    attacker_skills,
    attacker.conditions,
    defender_skills,
    defender.conditions,
    target_body_part="head"  # NEW: Target specific part
)

print(result['body_part_hit'])  # Which part was actually hit
```

## Wound Types & Severity

### Wound Types by Weapon

**Dismemberment Weapons** (axe, sword, machete, trident):
- **15+ damage**: Guaranteed limb severing on arms/legs
- **12-14 damage**: 40-85% chance to sever
- **< 12 damage**: Slash wounds (no severing)

**Crushing Weapons** (mace, club, rock):
- Create broken bones at severity 3+
- Create bruises at lower severity

**Piercing Weapons** (spear, knife, arrow, bolt):
- Create stab wounds
- Deep penetration

### Severity Levels (1-5)

| Severity | Damage Range | Effects |
|----------|--------------|---------|
| **1 - Minor** | 0-3 damage | Light bleeding (2-4 HP/phase), minor penalties |
| **2 - Moderate** | 3-6 damage | Moderate bleeding (4-7 HP/phase), -20-40% skills |
| **3 - Severe** | 6-10 damage | Heavy bleeding (6-11 HP/phase), -40-60% skills |
| **4 - Critical** | 10-15 damage | Extreme bleeding (8-16 HP/phase), -60-80% skills |
| **5 - Severed/Fatal** | 15+ damage | Limb severed, 15-25 HP/phase, death in 3 phases if untreated |

## Dismemberment Mechanics

### When Limbs Are Severed

**Requirements:**
- Dismemberment weapon (axe, sword, machete, trident)
- 12+ damage to arm or leg
- 15+ damage guarantees severing

**Effects of Severed Arms:**
- **One arm severed**: -50% strength, -60% combat (per arm)
- **Both arms severed**: Cannot hold weapons, equipped weapon dropped
- **Bleeding**: 15-25 HP/phase (FATAL if untreated)
- **Death**: 3 phases without medical treatment

**Effects of Severed Legs:**
- **One leg severed**: -70% agility, -50% stealth, -40% combat, hobbling movement
- **Both legs severed**: Cannot walk, extreme penalties
- **Bleeding**: 15-25 HP/phase (FATAL if untreated)
- **Death**: 3 phases without medical treatment

### Checking Limb Status

```python
# Check if can hold weapon
can_hold = tribute.can_hold_weapon()
if not can_hold:
    # Both arms severed or too damaged
    print("Cannot hold weapons!")

# Check walking ability
can_walk = tribute.can_walk_normally()
if not can_walk:
    can_walk, status = tribute.limb_damage.can_walk()
    print(f"Movement: {status}")  # "hobbling on one leg" or "both legs severed"

# Get severed limbs
severed = tribute.limb_damage.get_severed_limbs()
for limb in severed:
    print(f"Missing: {limb.value}")

# Get injury description
description = tribute.get_limb_status_description()
# "Missing: left arm, right leg | Bleeding: 35 HP/phase | 2 infected wound(s)"
```

## Skill Penalties by Body Part

### Head Wounds
- **Intelligence**: -20-50% (affects medical treatment, strategy)
- **Perception**: -30-70% (affects awareness, spotting items)
- **Combat**: -20-50%
- **Concussion** (10-15 damage): -40% intelligence, -30% agility, -40% combat
- **Skull Fracture** (16+ damage): Instant death

### Torso Wounds
- **Strength**: -15-40%
- **Endurance**: -20-50%
- **Agility**: -15-40%
- Multiple torso wounds stack rapidly

### Arm Wounds
- **Strength**: -20-60% (per arm)
- **Combat**: -25-70% (per arm)
- **Severed arm**: -50% strength, -60% combat (per arm)
- **Both arms severed**: Cannot hold weapons

### Leg Wounds
- **Agility**: -30-80% (per leg)
- **Stealth**: -20-50% (per leg)
- **Combat**: -15-40% (per leg)
- **Severed leg**: -70% agility, -50% stealth, -40% combat (per leg)
- **One leg severed**: Can hobble, severe penalties
- **Both legs severed**: Cannot walk

### Pain Multiplier
- Wounds cause pain (1-10 scale)
- Higher pain increases all penalties
- Severed limbs = maximum pain (10)
- Head wounds have +2 pain bonus

## Bleeding & Infection

### Bleeding Rates

| Wound Type | Bleeding Rate |
|------------|---------------|
| Bruise | 0 HP/phase |
| Broken bone | 1-5 HP/phase (internal bleeding) |
| Cut/Slash (minor) | 2-6 HP/phase |
| Cut/Slash (moderate) | 6-11 HP/phase |
| Cut/Slash (severe) | 10-16 HP/phase |
| Stab wound | 4-18 HP/phase |
| **Severed limb** | **15-25 HP/phase** |

**Multiple wounds stack**: 3 moderate wounds = 15-30 HP/phase

### Infection Risk

| Wound Type | Infection Risk (per phase) |
|------------|----------------------------|
| Bruise | 5% |
| Broken bone | 5% |
| Cut/Slash | 20-60% (by severity) |
| Stab wound | 20-60% (by severity) |
| **Severed limb** | **70%** |

**Infected wounds:**
- All skill penalties increased by 50%
- Death in 8 phases if untreated
- Requires medicine or medical_kit to cure

### Example: Severed Arm Progression

```
Phase 1: Arm severed, 20 HP bleeding, 70% infection risk
Phase 2: 20 HP bleeding (health: 80), infection check: FAILED
Phase 3: 20 HP bleeding (health: 60), wound infected!
Phase 4: 20 HP bleeding (health: 40), infection worsening...
Phase 5: 20 HP bleeding (health: 20), critical condition
Phase 6: Death from blood loss (if untreated)
```

## Medical Treatment

### Treating Limb Wounds

```python
# Treat specific body part
result = tribute.treat_limb_wound(
    "left_arm",
    medical_skill=8,  # Defaults to tribute's intelligence
    medical_supply="medical_kit"  # "bandage", "medicine", "medical_kit"
)

print(result['success'])          # Treatment succeeded?
print(result['bleeding_stopped']) # Stopped bleeding?
print(result['infection_cured'])  # Cured infection?
print(result['message'])          # Description
```

### Treatment Success Rates

**Base Success:**
```
success_chance = 40% + (medical_skill × 4%) - (severity × 10%)
```

**Examples:**
- Intelligence 8, treating minor wound (severity 2): 72% success
- Intelligence 5, treating severe wound (severity 4): 40% success
- Intelligence 10 + medical_kit, treating critical (severity 5): 70% success

**Medical Kit Bonus**: +20% success chance

### Treatment Effects

**For Bleeding:**
- **Severed limb**: Reduces bleeding to 1/3 (tourniquet applied), limb still lost
- **Other wounds**: Stops bleeding completely

**For Infection:**
- **Medicine or Medical Kit**: Can cure infection
- **Bandage alone**: Cannot cure infection

**Supply Consumption:**
- One medical item consumed per successful treatment
- Failed treatment does not consume items

## Combat Integration

### Full Combat with Limb Damage

```python
from Engine.weapons_system import get_weapons_system

ws = get_weapons_system()

# Calculate combat with all modifiers
attacker_skills = attacker.get_effective_combat_skills_with_limbs()
defender_skills = defender.get_effective_combat_skills_with_limbs()

result = ws.calculate_combat(
    attacker.equipped_weapon,
    attacker_skills,
    attacker.conditions,
    defender_skills,
    defender.conditions,
    target_body_part="head"  # Optional targeting
)

if result['hit']:
    # Apply wound to specific body part
    wound = defender.apply_limb_wound(
        result['body_part_hit'],  # "head", "left_arm", etc.
        "sword",                   # Weapon type
        result['damage']           # Damage dealt
    )
    
    # Apply HP damage
    defender.update_health(-result['damage'], "combat")
    
    # Check for severing
    if wound.get('severed'):
        print(f"{wound['message']}")  # "Thresh's left arm has been severed!"
        
        # Check if can still fight
        if not defender.can_hold_weapon():
            print(f"{defender.name} drops their weapon!")
            defender.equipped_weapon = None
    
    # Check for instant death (head trauma)
    if wound.get('fatal'):
        defender.status = "dead"
```

### Combat Descriptions with Body Parts

The system generates contextual descriptions:

```
"The Sword hits the left leg for 15 damage, causing Fatal Bleeding!"
"The Axe strikes the head, killing instantly!"
"The Bow hits the torso for 8 damage, causing Severe Bleeding!"
```

## Phase Processing

### Per-Phase Updates

```python
# In game loop, process each living tribute
for tribute in living_tributes:
    # Process limb damage effects
    limb_result = tribute.process_limb_damage_effects(phases_elapsed=1)
    
    # Check bleeding
    if limb_result['health_loss'] > 0:
        print(f"{tribute.name} loses {limb_result['health_loss']} HP from bleeding")
    
    # Check new infections
    for body_part in limb_result['new_infections']:
        print(f"{tribute.name}'s {body_part} wound has become infected!")
    
    # Check for death
    if limb_result.get('death_from_bleeding'):
        print(limb_result['death_message'])
        tribute.status = "dead"
    
    if limb_result.get('death_from_infection'):
        print(limb_result['death_message'])
        tribute.status = "dead"
```

## Event Generation Examples

### Dismemberment Events

```python
def generate_dismemberment_event(attacker, defender, body_part, weapon):
    severed_limbs = defender.limb_damage.get_severed_limbs()
    
    if severed_limbs:
        limb_name = body_part.replace('_', ' ')
        message = f"{attacker.name} severs {defender.name}'s {limb_name} with their {weapon}!"
        
        # Check for disabilities
        if not defender.can_hold_weapon():
            message += f" {defender.name} drops their weapon, unable to fight!"
        
        if not defender.can_walk_normally():
            can_walk, status = defender.limb_damage.can_walk()
            if not can_walk:
                message += f" {defender.name} cannot walk!"
            elif status == "hobbling on one leg":
                message += f" {defender.name} hobbles on one leg!"
        
        return {
            'type': 'dismemberment',
            'message': message,
            'attacker': attacker.id,
            'victim': defender.id,
            'body_part': body_part,
            'fatal': not can_walk or not defender.can_hold_weapon()
        }
```

### Bleeding Events

```python
def generate_bleeding_event(tribute):
    total_bleeding = tribute.limb_damage.get_total_bleeding_rate()
    
    if total_bleeding >= 20:
        return {
            'type': 'severe_bleeding',
            'message': f"{tribute.name} is bleeding heavily from multiple wounds, losing {total_bleeding} HP per phase!",
            'tribute': tribute.id
        }
    elif total_bleeding >= 10:
        return {
            'type': 'bleeding',
            'message': f"{tribute.name} is bleeding badly and growing weak.",
            'tribute': tribute.id
        }
```

### Infection Events

```python
def generate_infection_event(tribute):
    infection_count = tribute.limb_damage.get_infection_count()
    
    if infection_count > 0:
        return {
            'type': 'infection',
            'message': f"{tribute.name} has {infection_count} infected wound(s). Fever sets in.",
            'tribute': tribute.id
        }
```

## Testing

### Run Test Suite

```bash
python test_limb_damage.py
```

**Test Coverage:**
1. **Limb Wound Application** - Basic wound mechanics
2. **Dismemberment** - Severing limbs, weapon dropping
3. **Leg Damage** - Movement penalties, hobbling
4. **Head Trauma** - Intelligence penalties, instant death
5. **Bleeding & Infection** - Multi-phase progression
6. **Medical Treatment** - Treating wounds, stopping bleeding
7. **Combat with Limb Targeting** - Full combat simulation
8. **Multiple Wounds Stacking** - Cumulative penalties

All tests pass (100% success rate).

## API Reference

### Tribute Methods

```python
# Apply wound
tribute.apply_limb_wound(body_part: str, weapon_type: str, damage: int) -> Dict

# Check capabilities
tribute.can_hold_weapon() -> bool
tribute.can_walk_normally() -> bool
tribute.has_severed_limbs() -> bool

# Get penalties and skills
tribute.get_limb_penalties() -> Dict[str, float]
tribute.get_effective_combat_skills_with_limbs() -> Dict[str, float]

# Treatment
tribute.treat_limb_wound(body_part: str, medical_skill: int, medical_supply: str) -> Dict

# Ongoing effects
tribute.process_limb_damage_effects(phases_elapsed: int) -> Dict

# Status
tribute.get_limb_status_description() -> str
```

### LimbDamageSystem Methods

```python
from Engine.limb_damage_system import get_limb_damage_system

lds = get_limb_damage_system()

# Body part selection
body_part = lds.select_hit_location(target=None)

# Wound determination
wound_type, severity = lds.determine_wound_type(weapon_type, damage, body_part)

# Wound creation
wound = lds.create_wound(body_part, wound_type, severity, weapon_type)

# Treatment
result = lds.treat_wound(wound, medical_skill, medical_supply)

# Effects processing
result = lds.process_wound_effects(limb_state, phases_elapsed)
```

## Configuration

### Modifying Hit Chances

Edit `Engine/limb_damage_system.py`, `LimbDamageSystem.__init__()`:

```python
self.hit_chances = {
    BodyPart.HEAD: 0.20,      # Increase head shot chance
    BodyPart.TORSO: 0.35,     # Decrease torso chance
    # ... etc
}
```

### Modifying Dismemberment Thresholds

Edit `determine_wound_type()` method:

```python
if damage >= 18:  # Increase threshold
    return "severed", 5
elif damage >= 14:
    sever_chance = 0.3 + (damage - 14) * 0.1  # Adjust formula
```

## Summary

**Limb Damage System Features:**
- ✅ 6 body parts with realistic hit chances
- ✅ Limb severing with dismemberment weapons (15+ damage)
- ✅ Disabilities (no arms = can't hold weapon, no legs = can't walk)
- ✅ Body part-specific skill penalties
- ✅ Extreme bleeding from severed limbs (15-25 HP/phase)
- ✅ High infection risk (70% for severed limbs)
- ✅ Medical treatment with success rates
- ✅ Full combat integration with targeting
- ✅ Comprehensive test suite (8 scenarios, 100% pass)

**Files:**
- Core: `Engine/limb_damage_system.py` (600+ lines)
- Integration: `Engine/tribute.py` (new methods)
- Tests: `test_limb_damage.py` (8 test scenarios)
- Docs: This guide

**Status:** ✅ Complete and production-ready
