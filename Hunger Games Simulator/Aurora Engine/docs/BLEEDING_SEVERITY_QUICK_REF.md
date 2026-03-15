# Bleeding Severity Quick Reference

**5 Severity Levels** | **Infection Scaling** | **Untreatable Fatal Wounds**

---

## At-a-Glance Table

| Severity | HP/Phase | Infection | Death Timer | Treatable? | Treatment Effect |
|----------|----------|-----------|-------------|------------|------------------|
| **NONE** | 0 | 5% | - | N/A | - |
| **MILD** | 1-3 | 15% | - | ✅ Easy | Stop → NONE |
| **MODERATE** | 4-7 | 30% | - | ✅ | Stop → MILD |
| **SEVERE** | 8-14 | 50% | 8 phases | ✅ Hard | Reduce → MODERATE |
| **FATAL** | 15-25 | 70% | 1-3 phases | ⚠️ 70% yes, 30% no | Reduce → SEVERE |

---

## Key Mechanics

### Untreatable Fatal Wounds (30% of FATAL)
```
✗ Cannot be treated (auto-fail)
✗ Death in 1 phase
✗ No cure, no way to prevent
✓ Creates urgent drama
```

### Treatment Difficulty
```
MILD:     Easy (+10% with bandage)
MODERATE: Standard (+10% with bandage)
SEVERE:   Hard (-20% success, +20% difficulty)
FATAL:    Very hard (-30% success, +30% difficulty)
```

### Death Timers
```
FATAL (untreatable): 1 phase → death
FATAL (treatable):   3 phases → death if not treated
SEVERE:              8 phases → death if not treated
MODERATE/MILD:       No timer (only HP loss kills)
```

---

## Wound Type → Severity Mapping

### Dismemberment (Severed Limbs)
- **Always FATAL** (15-25 HP/phase)
- 30% chance untreatable
- Example: Axe severs arm

### Combat Wounds (Slash/Stab)
- **1-3 HP**: MILD
- **4-7 HP**: MODERATE
- **8-14 HP**: SEVERE
- **15+ HP**: FATAL (30% untreatable)

### Internal Bleeding (Broken Bones)
- **1-3 HP**: MILD (10% infection)
- **4-5 HP**: MODERATE (25% infection)

### Blunt Trauma (Bruises)
- **0 HP**: NONE (5% infection)

---

## Code Snippets

### Check Bleeding Severity
```python
for wound in tribute.limb_damage.wounds:
    if wound.bleeding_severity == BleedingSeverity.FATAL:
        if wound.is_fatal_bleeding:
            # Doomed - cannot be treated
            print(f"{tribute.name} is bleeding out!")
        else:
            # Critical but treatable
            print(f"{tribute.name} needs urgent medical attention!")
```

### Attempt Treatment
```python
result = tribute.treat_limb_wound("torso")
if not result['success']:
    if result.get('untreatable'):
        # Wound too severe
        print("Fatal bleeding cannot be treated!")
    else:
        # Treatment failed
        print("Failed to stop the bleeding")
```

### Check Death Risk
```python
result = tribute.process_limb_damage_effects(1)
if result.get('death_from_bleeding'):
    # Tribute died from blood loss
    print(f"{tribute.name} has bled out")
if result.get('fatal_bleeding_wounds'):
    # Has fatal wounds, on death timer
    print(f"{tribute.name} is critically wounded!")
```

---

## Event Messages Examples

### FATAL (Untreatable)
> "Katniss is bleeding out from a severed artery! There's nothing that can be done!"

### FATAL (Treatable)
> "Peeta is bleeding heavily from a deep axe wound! He needs immediate medical attention!"

### SEVERE
> "Thresh is bleeding badly from multiple sword slashes. He needs treatment soon."

### MODERATE
> "Rue has moderate bleeding from a knife wound. She should bandage it."

### MILD
> "Cato has a small cut on his arm that's bleeding slightly."

---

## AI Behavior Priorities

```python
# Priority levels for Nemesis Behavior Engine:

Untreatable FATAL:  Leave to die (priority 80)
Treatable FATAL:    Find medical supplies (priority 99)
SEVERE:             Treat wounds (priority 85)
MODERATE:           Treat wounds (priority 60)
MILD:               Treat wounds (priority 30)
```

---

## Testing Commands

```powershell
# Run all limb damage tests (includes bleeding severity)
python test_limb_damage.py

# Tests 9-10 specifically test bleeding severity:
# - Test 9: Classification (MILD/MODERATE/SEVERE/FATAL)
# - Test 10: Untreatable fatal bleeding (death in 1 phase)
```

---

**Implementation**: `Engine/limb_damage_system.py`  
**Documentation**: `docs/BLEEDING_SEVERITY_SYSTEM.md`  
**Last Updated**: November 7, 2025
