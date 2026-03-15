# Enhanced Medical Supply System

**Status**: ✅ **IMPLEMENTED** (November 7, 2025)

## Overview

The medical supply system now supports **wild-found items**, **improvised materials**, and **sponsor gifts** for treating bleeding and infections. Different supplies have varying effectiveness based on wound severity.

## Medical Supply Types

### Sponsor Gifts (Premium)
**Medical Kit / First Aid Kit**
- **Effectiveness**: +30% success on all severities
- **Best for**: Any wound severity
- **Treats**: Bleeding, infection, wounds
- **Source**: Sponsor gift, Cornucopia (rare)
- **Note**: Most comprehensive treatment option

### Emergency Supplies
**Tourniquet**
- **Effectiveness**: 
  - FATAL: +35% (best option)
  - SEVERE: +30%
  - MODERATE: +15%
  - MILD: +5%
- **Best for**: Severed limbs, arterial bleeding
- **Treats**: Critical bleeding only
- **Source**: Cornucopia, sponsor gift, improvised from belt/rope
- **Critical Use**: Essential for severed limbs to prevent death in 1 phase

### Standard Medical Supplies
**Bandages / Gauze**
- **Effectiveness**:
  - MILD: +20% (very effective)
  - MODERATE: +18% (good)
  - SEVERE: +12% (can help)
  - FATAL: +5% (limited)
- **Best for**: Mild to moderate bleeding
- **Treats**: Bleeding, minor wounds
- **Source**: Cornucopia, backpacks, sponsor gift

**Medicine / Antiseptic / Alcohol**
- **Effectiveness**: +8% all severities
- **Best for**: Infection treatment
- **Treats**: Infection primarily, minor bleeding help
- **Source**: Cornucopia, sponsor gift

### Improvised Supplies
**Cloth Strips / Torn Clothing**
- **Effectiveness**:
  - MILD: +15%
  - MODERATE: +12%
  - SEVERE: +8%
  - FATAL: +3%
- **Best for**: Mild to moderate wounds
- **Treats**: Bleeding
- **Source**: Tear own clothing, use shirt
- **Note**: Always available if you have clothes

### Wild-Found Items (Hunger Games Lore)
**Medicinal Herbs (Yarrow, Plantain)**
- **Effectiveness**:
  - MILD: +18% (good)
  - MODERATE: +14% (decent)
  - SEVERE/FATAL: +6% (limited)
- **Best for**: Mild to moderate wounds, infection
- **Treats**: Bleeding (clotting), infection (antiseptic)
- **Source**: Foraged in forests, fields
- **Note**: Rue's specialty in original story

**Moss / Leaf Packs**
- **Effectiveness**:
  - MILD: +12%
  - MODERATE: +8%
  - SEVERE/FATAL: +2%
- **Best for**: Mild wounds only
- **Treats**: Basic clotting
- **Source**: Foraged near water, trees
- **Note**: Basic wilderness first aid

## Severed Limbs - Always Critical

**New Rule**: Severed limbs are **ALWAYS severe or fatal bleeding** (50% chance untreatable)

### Severed Limb Mechanics
- **Bleeding**: 15-25 HP/phase (FATAL severity)
- **Untreatable Chance**: 50% (up from 30%)
- **Death Timer**: 
  - If untreatable: 1 phase (guaranteed death)
  - If treatable: 3 phases without treatment
- **Best Treatment**: Tourniquet (+35% success)
- **Treatment Effect**: Reduces FATAL → SEVERE (manageable, but still dangerous)

### Severed Limb Treatment Priority
```python
# Without tourniquet:
Success with medical_kit: 40-80% base - 30% penalty = 10-50%

# With tourniquet:
Success with tourniquet: 40-80% base - 30% penalty + 35% bonus = 45-85%
```

**Critical**: Tourniquets are essential for surviving dismemberment!

## Treatment Success Calculation

### Base Formula
```python
base_chance = 0.4 + (medical_skill / 10) * 0.4  # 40-80%
severity_penalty = wound.severity * 0.1

# Bleeding severity penalties:
if FATAL: severity_penalty += 0.3    # -30%
if SEVERE: severity_penalty += 0.2   # -20%
if MODERATE: severity_penalty += 0.1 # -10%

success_chance = max(0.1, base_chance - severity_penalty)

# Add medical supply bonus
success_chance += supply_effectiveness_bonus
```

### Example Success Rates

**Medical Skill 5 (average), MILD wound:**
- No supply: 60% - 10% = 50%
- Bandage: 50% + 20% = **70%**
- Medical kit: 50% + 30% = **80%**
- Moss: 50% + 12% = **62%**

**Medical Skill 5, FATAL wound (severed limb):**
- No supply: 60% - 50% = 10%
- Medical kit: 10% + 30% = **40%**
- Tourniquet: 10% + 35% = **45%**
- Bandage: 10% + 5% = **15%**

## Auto-Supply Selection

When no supply is specified, system auto-selects best available:

### Priority Order (Best First)
1. medical_kit / first_aid_kit
2. tourniquet (for severe/fatal only)
3. antiseptic / medicine
4. bandage / gauze
5. herbs / medicinal_herbs
6. cloth / cloth_strips
7. moss / leaves

```python
# Usage - auto-selects best available supply
result = tribute.treat_limb_wound("torso")

# Or specify exact supply
result = tribute.treat_limb_wound("torso", medical_supply="tourniquet")
```

## Event Integration Examples

### Finding Wild Items
```python
# Foraging event
if tribute.skills['survival'] >= 7:
    found_items = random.choice([
        "medicinal_herbs",
        "moss",
        "leaf_pack"
    ])
    tribute.add_to_inventory(found_items)
    return f"{tribute.name} found {found_items} and knows how to use it!"
```

### Improvising Supplies
```python
# Desperate situation - tear shirt for bandages
if tribute.has_severe_bleeding() and not tribute.has_medical_supplies():
    tribute.add_to_inventory("cloth_strips")
    return f"{tribute.name} tears their shirt into strips to stop the bleeding!"
```

### Sponsor Gifts
```python
# High-stakes moment - sponsor sends medical kit
if tribute.has_fatal_bleeding() and tribute.is_popular():
    tribute.add_to_inventory("medical_kit")
    return f"A parachute! {tribute.name} receives a medical kit from sponsors!"
```

### Tourniquet on Severed Limb
```python
# Critical injury - tourniquet is only hope
if wound.wound_type == "severed" and not wound.is_fatal_bleeding:
    if "tourniquet" in tribute.inventory or "belt" in tribute.inventory:
        result = tribute.treat_limb_wound(body_part, medical_supply="tourniquet")
        if result['success']:
            return f"{tribute.name} applies a tourniquet to the severed limb! They're stabilized but in critical condition."
        else:
            return f"{tribute.name} frantically tries to apply a tourniquet but fumbles with the straps as blood pours out!"
    else:
        return f"{tribute.name} is bleeding out from a severed limb! Without a tourniquet, they have only moments left..."
```

## Infection Treatment

### Antiseptic-Capable Supplies
The following supplies can cure infections:
- medical_kit / first_aid_kit
- medicine
- antiseptic
- alcohol
- herbs / medicinal_herbs

### Treatment Priority
1. **Medical kit**: Treats bleeding + infection simultaneously
2. **Medicine/Antiseptic**: Infection only, minor bleeding help
3. **Herbs**: Good for both bleeding and infection (natural)
4. **Bandages**: Bleeding only, no infection treatment

## Game Balance Recommendations

### Cornucopia Spawns
```python
medical_supplies = [
    ("medical_kit", 5),        # 5% - rare, valuable
    ("tourniquet", 8),         # 8% - critical for dismemberment
    ("bandage", 15),           # 15% - common
    ("medicine", 10),          # 10% - decent
    ("antiseptic", 8)          # 8% - useful
]
```

### Sponsor Gift Tiers
```python
sponsor_gifts = {
    "tier_1": ["medical_kit", "tourniquet"],  # Premium (10+ sponsors)
    "tier_2": ["bandage", "medicine"],        # Standard (5+ sponsors)
    "tier_3": ["cloth_strips", "herbs"]       # Basic (2+ sponsors)
}
```

### Foraging Success Rates
```python
# Based on survival skill
if survival >= 9:
    find_chance = 0.6  # 60% find medicinal herbs
elif survival >= 7:
    find_chance = 0.4  # 40% find moss
elif survival >= 5:
    find_chance = 0.2  # 20% find basic leaves
```

## Combat Survival Strategy

### Immediate Priorities After Combat
1. **Check for severed limbs** - Use tourniquet IMMEDIATELY
2. **Check for fatal bleeding** - Use medical kit or tourniquet
3. **Treat severe bleeding** - Use bandages or herbs
4. **Treat infections** - Use medicine or herbs
5. **Treat mild wounds** - Use any remaining supplies

### Inventory Management
**Essential Combat Kit**:
- 1x tourniquet (for emergencies)
- 2-3x bandages (standard wounds)
- 1x medicine (infection backup)

**Scavenging Priority**:
1. Medical kit (take always)
2. Tourniquet (life-saver)
3. Medicine (infection is deadly)
4. Bandages (bulk up)
5. Wild herbs (free backup)

## Testing

### Test File
`test_medical_supplies.py` includes:
- Supply effectiveness matrix
- Wild item treatment tests
- Tourniquet on severed limb scenarios
- Sponsor gift medical kit usage
- Infection treatment with herbs

### Run Tests
```powershell
python test_medical_supplies.py
```

### Expected Outcomes
- Tourniquet is most effective on FATAL bleeding (+35%)
- Bandages excel on MILD/MODERATE (+18-20%)
- Medical kit works well on all severities (+30%)
- Wild items provide reasonable alternatives (+8-18%)
- Herbs can cure infections (antiseptic properties)

## Code Reference

### Primary Implementation
- **File**: `Engine/limb_damage_system.py`
- **Method**: `_get_medical_supply_effectiveness()` (lines 545-640)
- **Method**: `treat_wound()` (lines 641-745)
- **Method**: `create_wound()` (lines 390-470) - Severed limb mechanics

### Integration
- **File**: `Engine/tribute.py`
- **Method**: `treat_limb_wound()` (lines 700-760) - Auto-supply selection
- **Method**: `treat_wounds()` (lines 490-510) - Supply consumption

---

**Last Updated**: November 7, 2025  
**Implementation Status**: ✅ Complete  
**Test Coverage**: 5/5 tests (supply effectiveness, wild items, tourniquet, sponsor gifts, herbs)
