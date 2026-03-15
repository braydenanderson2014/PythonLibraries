# Bleeding Severity System

**Status**: ✅ **IMPLEMENTED** (November 7, 2025)

## Overview

The bleeding severity system classifies wounds into five distinct levels (NONE, MILD, MODERATE, SEVERE, FATAL) with escalating danger, infection risks, and treatment difficulty.

## Severity Levels

### NONE (No Bleeding)
- **Bleeding Rate**: 0 HP/phase
- **Infection Risk**: 5% per phase
- **Death Timer**: None
- **Treatable**: N/A
- **Example**: Bruises, minor contusions

### MILD (Minor Bleeding)
- **Bleeding Rate**: 1-3 HP/phase
- **Infection Risk**: 15% per phase
- **Death Timer**: None
- **Treatable**: Yes (easy)
- **Treatment Success**: +10% with bandage
- **Treatment Effect**: Bleeding stops completely → NONE
- **Example**: Small knife cuts, minor lacerations

### MODERATE (Significant Bleeding)
- **Bleeding Rate**: 4-7 HP/phase
- **Infection Risk**: 30% per phase
- **Death Timer**: None
- **Treatable**: Yes
- **Treatment Success**: +10% with bandage
- **Treatment Effect**: Bleeding stops → MILD
- **Example**: Sword slashes, deep cuts, minor internal bleeding

### SEVERE (Critical Bleeding)
- **Bleeding Rate**: 8-14 HP/phase
- **Infection Risk**: 50% per phase
- **Death Timer**: 8 phases if untreated
- **Treatable**: Yes (difficult)
- **Treatment Penalty**: +20% difficulty
- **Treatment Effect**: Bleeding reduced → MODERATE
- **Example**: Deep sword wounds, major lacerations, broken bones with internal bleeding

### FATAL (Life-Threatening Bleeding)
- **Bleeding Rate**: 15-25 HP/phase
- **Infection Risk**: 70% per phase
- **Death Timer**: 
  - **Untreatable wounds**: 1 phase (guaranteed death)
  - **Treatable wounds**: 3 phases if untreated
- **Treatable**: 70% yes, 30% no
- **Treatment Penalty**: +30% difficulty
- **Treatment Effect**: Bleeding reduced → SEVERE (cannot stop completely)
- **Example**: Severed limbs, massive axe wounds, arterial damage

## Untreatable Fatal Bleeding

**30% of FATAL severity wounds are marked as untreatable** (`is_fatal_bleeding=True`).

### Characteristics:
- **Cannot be treated** - Medical attempts automatically fail
- **Death in 1 phase** - Tribute will die within 1 phase regardless of actions
- **No cure** - As explicitly requested: "Fatal there is no cure"
- **High threat** - Creates urgent, dramatic situations

### Treatment Attempt Response:
```
"Fatal bleeding from torso - wound is too severe to treat!"
```

## Wound Type Classification

### Severed Limbs (Dismemberment)
- **Always FATAL severity**
- Bleeding: 15-25 HP/phase
- 30% chance of being untreatable
- Requires tourniquet (reduces to SEVERE if treatable)

### Slash/Cut/Stab Wounds
Classified by bleeding rate:
- 1-3 HP/phase → **MILD** (15% infection)
- 4-7 HP/phase → **MODERATE** (30% infection)
- 8-14 HP/phase → **SEVERE** (50% infection)
- 15+ HP/phase → **FATAL** (70% infection, 30% untreatable)

### Broken Bones (Internal Bleeding)
- 1-3 HP/phase → **MILD** (10% infection)
- 4-5 HP/phase → **MODERATE** (25% infection)
- Rarely severe or fatal

### Bruises
- 0 HP/phase → **NONE** (5% infection)
- No bleeding, minimal risk

## Treatment System

### Success Calculation
```python
base_chance = 0.4 + (medical_skill / 10) * 0.4  # 40-80%
severity_penalty = wound.severity * 0.1

# Bleeding severity modifiers:
if FATAL: severity_penalty += 0.3    # Very hard
if SEVERE: severity_penalty += 0.2   # Hard  
if MODERATE: severity_penalty += 0.1 # Somewhat difficult

success_chance = max(0.1, base_chance - severity_penalty)

# Medical supply bonuses:
if medical_kit: success_chance += 0.25
if bandage and bleeding <= MODERATE: success_chance += 0.1
```

### Treatment Effects by Severity

| Current Severity | Treatment Success | Result |
|-----------------|-------------------|---------|
| **FATAL** | If treatable | Reduced to SEVERE (still 8+ HP/phase) |
| **SEVERE** | Yes | Reduced to MODERATE (4-7 HP/phase) |
| **MODERATE** | Yes | Stopped → MILD (0 HP/phase) |
| **MILD** | Yes | Stopped → NONE (0 HP/phase) |

**Note**: FATAL bleeding can only be *reduced*, never fully stopped in one treatment.

## Infection Risk Progression

Infection risk scales directly with bleeding severity:

```
NONE: 5% → MILD: 15% → MODERATE: 30% → SEVERE: 50% → FATAL: 70%
```

This creates escalating danger: **higher bleeding = higher infection chance**.

## Death Mechanics

### Fatal Bleeding (Untreatable)
- **Phase 1**: Tribute takes 15-25 HP damage from bleeding
- **End of Phase 1**: Death flag set (`death_from_bleeding=True`)
- **Message**: "X is bleeding out and will die soon!" or similar
- Cannot be prevented by any means

### Fatal Bleeding (Treatable)
- **Phases 1-2**: Takes 15-25 HP/phase, can be treated
- **Phase 3**: If not treated, death flag set
- **Treatment**: Reduces to SEVERE (8-14 HP/phase), extends survival time

### Severe Bleeding
- **Phases 1-7**: Takes 8-14 HP/phase, can be treated
- **Phase 8**: If not treated, death flag set
- **Treatment**: Reduces to MODERATE, no death timer

## Game Integration Examples

### Event Generation
```python
# Check for fatal bleeding in events
for wound in tribute.limb_damage.wounds:
    if wound.bleeding_severity == BleedingSeverity.FATAL:
        if wound.is_fatal_bleeding:
            events.append({
                'message': f"{tribute.name} is bleeding out rapidly! Nothing can be done!",
                'type': 'fatal_bleeding',
                'fatal': True
            })
        else:
            events.append({
                'message': f"{tribute.name} is bleeding critically and needs immediate medical attention!",
                'type': 'severe_bleeding'
            })
```

### AI Behavior Integration
```python
# Nemesis Behavior Engine priority calculation
fatal_wounds = [w for w in tribute.limb_damage.wounds 
                if w.bleeding_severity == BleedingSeverity.FATAL]

if fatal_wounds and not any(w.is_fatal_bleeding for w in fatal_wounds):
    # Has treatable fatal bleeding - URGENT priority
    return {'action': 'FIND_MEDICAL_SUPPLIES', 'priority': 99}

# Don't waste supplies on doomed tributes
has_untreatable = any(w.is_fatal_bleeding for w in tribute.limb_damage.wounds)
if has_untreatable:
    return {'action': 'LEAVE_TO_DIE', 'priority': 80}
```

### Combat Messages
```python
# Show bleeding severity in combat results
if wound.bleeding_severity == BleedingSeverity.FATAL:
    message += " - FATAL BLEEDING!"
elif wound.bleeding_severity == BleedingSeverity.SEVERE:
    message += " - SEVERE BLEEDING!"
elif wound.bleeding_severity == BleedingSeverity.MODERATE:
    message += " - Moderate bleeding"
```

## Code Reference

### Primary Implementation
- **File**: `Engine/limb_damage_system.py`
- **Lines**: 18-26 (BleedingSeverity enum)
- **Lines**: 30-54 (LimbWound dataclass)
- **Lines**: 380-463 (create_wound method - classification logic)
- **Lines**: 465-512 (process_wound_effects - death timing)
- **Lines**: 540-650 (treat_wound method - treatment logic)

### Integration Points
- **Tribute class**: `Engine/tribute.py`
  - `apply_limb_wound()` - Creates wounds with severity
  - `process_limb_damage_effects()` - Checks death timers
  - `treat_limb_wound()` - Attempts treatment

### Testing
- **File**: `test_limb_damage.py`
- **Test 9**: Bleeding severity classification
- **Test 10**: Untreatable fatal bleeding (30% chance test)

## Design Rationale

### Why 5 Severity Levels?
- **NONE**: Allows for non-bleeding injuries (bruises)
- **MILD**: Minor wounds that are easily treatable
- **MODERATE**: Standard combat wounds with real danger
- **SEVERE**: Critical wounds that require urgent attention
- **FATAL**: Life-or-death situations with high drama

### Why 30% Untreatable Rate?
- **Balance**: Not every fatal wound = instant death
- **Drama**: Creates "doomed tribute" scenarios
- **Strategy**: Medical supplies still valuable for 70% of fatal wounds
- **Realism**: Some wounds (major arteries, multiple organs) are beyond field medicine

### Why Infection Risk Scales?
- **Logical**: Larger wounds = more exposure = higher infection chance
- **Pressure**: Forces tributes to treat wounds quickly
- **Complexity**: Adds another layer of danger beyond just bleeding
- **Compounding**: Severe bleeding + high infection = urgent crisis

## Testing Results

✅ **All tests passing** (November 7, 2025)
- Bleeding classification working correctly
- Infection risks scaling as designed (15% → 30% → 50% → 70%)
- Treatment difficulty scaling with severity
- Untreatable wounds properly refuse treatment
- Death timers functioning (1 phase for untreatable, 3 for fatal, 8 for severe)

## Future Enhancements

### Potential Additions:
1. **Cauterization**: Stop bleeding at cost of HP/sanity
2. **Blood loss effects**: Fatigue, reduced combat at <50% HP
3. **Shock mechanics**: Immediate debuffs from severe wounds
4. **Scars**: Permanent effects from severe/fatal wounds that were treated
5. **Field surgery**: High medical skill allows stabilization of fatal wounds
6. **Bleeding out slowly**: Visual/narrative feedback as HP drains

---

**Last Updated**: November 7, 2025  
**Implementation Status**: ✅ Complete  
**Test Coverage**: 100% (10/10 tests passing)
