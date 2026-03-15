# Weapons & Injuries - Quick Reference

## Weapon Stats Cheat Sheet

**Best Weapons by Category:**
- **Highest Damage:** Axe (8), Mace (7)
- **Best Accuracy:** Blowgun (0.95), Crossbow (0.9)
- **Fastest:** Fists (1.0), Rock (1.0), Blowgun (1.0)
- **Highest Instant Kill:** Crossbow (22%), Bow (18%)
- **Lightest (Low Str Req):** Fists (1), Blowgun (1), Rock (1)
- **Heaviest (High Str Req):** Axe (5), Mace (5)

## Injury Severity Quick Check

```python
if tribute.is_critically_injured():      # Severity ≥ 4
    # URGENT action needed
if tribute.is_bleeding():                 # Any bleeding wound
    # Find bandages/medical kit
if tribute.is_infected():                 # Has infection
    # Find medicine ASAP (fatal in 8 phases)
```

## Combat Resolution Flow

```python
# 1. Get effective skills (with injury penalties)
attacker_skills = attacker.get_effective_combat_skills()
defender_skills = defender.get_effective_combat_skills()

# 2. Calculate combat
ws = get_weapons_system()
result = ws.calculate_combat(
    attacker.get_equipped_weapon(),
    attacker_skills,
    attacker.conditions,
    defender_skills,
    defender.conditions
)

# 3. Apply results
if result['hit']:
    defender.update_health(-result['damage'], "combat")
    if result['new_condition']:
        defender.add_condition(result['new_condition'])
    if result['instant_kill']:
        defender.status = "dead"
```

## Per-Phase Processing

```python
# For each living tribute at end of phase:
result = tribute.process_condition_effects(phases_elapsed=1)

# Check results:
if result['health_loss'] > 0:
    # Bleeding damage applied
if result['new_infections']:
    # Wounds became infected
if result['fatal']:
    # Died from untreated injuries
```

## Medical Treatment

```python
# Check for supplies
if any(item in ["bandage", "medicine", "medical_kit"] for item in tribute.inventory):
    result = tribute.treat_wounds()
    
    if result['success']:
        # Wounds treated: result['wounds_treated']
        # Infections cured: result['infections_cured']
        # Medical supply consumed
```

## Common Patterns

### Check if tribute can fight
```python
modified = tribute.get_effective_combat_skills()
if modified['combat'] < 3:
    # Too injured to fight effectively
    priority_action = "FIND_MEDICAL_SUPPLIES"
```

### Switch weapon if too weak
```python
equipped = tribute.get_equipped_weapon()
weapon = ws.get_weapon(equipped)
if not weapon.can_use(tribute.skills['strength']):
    # Find lighter weapon
    lighter = [w for w in tribute.weapons 
              if ws.get_weapon(w).strength_requirement <= tribute.skills['strength']]
    if lighter:
        tribute.equip_weapon(lighter[0])
```

### Prioritize medical supplies for injured tributes
```python
if tribute.is_bleeding() or tribute.is_infected():
    # High priority for medical supplies
    if "bandage" in found_items:
        tribute.add_to_inventory("bandage")
    if "medicine" in found_items:
        tribute.add_to_inventory("medicine")
```

## Injury Penalties Summary

| Condition | Str | Agi | Combat | Other |
|-----------|-----|-----|--------|-------|
| Bruised | -5% | -5% | -5% | All physical -5% |
| Bleeding Mild | -15% | -10% | - | - |
| Bleeding Medium | -30% | -25% | - | - |
| Bleeding Severe | -50% | -40% | - | - |
| Bleeding Fatal | -80% | -70% | - | - |
| Infected | -30% | -30% | -30% | All skills -30% |
| Broken Arm | -60% | - | -70% | - |
| Broken Leg | - | -80% | -50% | - |
| Concussion | - | -30% | -40% | Intel -40% |
| Poisoned | -50% | -50% | -60% | - |

## Fatal Conditions (Will Die if Untreated)

- **Bleeding Fatal:** 3 phases to death, 15 HP/phase
- **Infected:** 8 phases to death, no HP loss but -30% all skills
- **Poisoned:** 5 phases to death, -50% strength/agility, -60% combat

## API Quick Reference

### Tribute Weapon Methods
```python
tribute.add_weapon(weapon_id)                     # Add to inventory
tribute.equip_weapon(weapon_id) -> bool           # Equip weapon
tribute.get_equipped_weapon() -> str              # Get current weapon
tribute.get_effective_combat_skills() -> dict     # Skills with injury modifiers
```

### Tribute Injury Methods
```python
tribute.add_condition(condition_id)               # Apply injury
tribute.remove_condition(condition_id)            # Remove injury
tribute.is_bleeding() -> bool                     # Has bleeding wounds
tribute.is_infected() -> bool                     # Has infection
tribute.is_critically_injured() -> bool           # Severity ≥ 4
tribute.treat_wounds() -> dict                    # Attempt treatment
tribute.process_condition_effects(phases) -> dict # Ongoing effects
```

### WeaponsSystem Methods
```python
ws.get_weapon(weapon_id) -> Weapon
ws.get_condition(condition_id) -> Condition
ws.get_best_weapon(weapons, strength) -> str
ws.calculate_combat(...) -> dict
ws.process_condition_effects(health, conditions, phases) -> dict
```

## Testing Commands

```bash
# Run full test suite
python test_weapons_injuries.py

# Quick manual test
python -c "from Engine.tribute import Tribute; t = Tribute('test', {'weapons': ['sword']}); print(t.equipped_weapon)"
```

## Files Reference

- **Core System:** `Engine/weapons_system.py` (900+ lines)
- **Tribute Integration:** `Engine/tribute.py` (weapon/injury methods)
- **Tests:** `test_weapons_injuries.py` (5 test scenarios)
- **Full Guide:** `docs/WEAPONS_INJURIES_GUIDE.md`
- **This Quick Ref:** `docs/WEAPONS_INJURIES_QUICK_REF.md`
