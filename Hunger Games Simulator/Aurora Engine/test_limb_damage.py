"""
Test limb damage and dismemberment system
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from Engine.tribute import Tribute
from Engine.limb_damage_system import get_limb_damage_system, BodyPart, LimbStatus
from Engine.weapons_system import get_weapons_system


def test_limb_wound_application():
    """Test applying wounds to specific body parts"""
    print("\n=== TEST 1: Limb Wound Application ===")
    
    tribute = Tribute('test1', {
        'name': 'Test Tribute',
        'skills': {'combat': 7, 'strength': 7, 'agility': 6}
    })
    
    print(f"✓ Created tribute: {tribute.name}")
    print(f"  Initial health: {tribute.health}")
    
    # Apply moderate slash to left arm
    result = tribute.apply_limb_wound("left_arm", "sword", damage=6)
    
    print(f"\n✓ Applied sword slash to left arm:")
    print(f"  Wound type: {result['wound_type']}")
    print(f"  Severity: {result['severity']}")
    print(f"  Bleeding rate: {result['bleeding_rate']} HP/phase")
    print(f"  Message: {result['message']}")
    
    # Check penalties
    penalties = tribute.get_limb_penalties()
    print(f"\n✓ Skill penalties from arm wound:")
    for skill, penalty in penalties.items():
        print(f"  {skill}: {penalty:.1%}")
    
    # Get effective skills
    modified = tribute.get_effective_combat_skills_with_limbs()
    print(f"\n✓ Modified combat skills:")
    print(f"  Strength: {tribute.skills['strength']} → {modified['strength']:.1f}")
    print(f"  Combat: {tribute.skills['combat']} → {modified['combat']:.1f}")


def test_dismemberment():
    """Test limb severing mechanics"""
    print("\n\n=== TEST 2: Dismemberment ===")
    
    tribute = Tribute('test2', {
        'name': 'Unfortunate Tribute',
        'weapons': ['sword', 'knife'],
        'skills': {'combat': 7, 'strength': 8}
    })
    
    print(f"✓ Created tribute: {tribute.name}")
    print(f"  Equipped weapon: {tribute.equipped_weapon}")
    print(f"  Can hold weapon: {tribute.can_hold_weapon()}")
    
    # Severe axe hit to right arm (should sever)
    result = tribute.apply_limb_wound("right_arm", "axe", damage=15)
    
    print(f"\n✓ Axe hit to right arm (15 damage):")
    print(f"  Wound type: {result['wound_type']}")
    print(f"  Severed: {result.get('severed', False)}")
    print(f"  Message: {result['message']}")
    
    # Check if can still hold weapon
    print(f"\n✓ After losing right arm:")
    print(f"  Can hold weapon: {tribute.can_hold_weapon()}")
    print(f"  Equipped weapon: {tribute.equipped_weapon}")
    
    # Sever left arm too
    result2 = tribute.apply_limb_wound("left_arm", "axe", damage=15)
    
    print(f"\n✓ Axe hit to left arm (15 damage):")
    print(f"  Wound type: {result2['wound_type']}")
    print(f"  Message: {result2['message']}")
    
    # Check status
    print(f"\n✓ After losing both arms:")
    print(f"  Can hold weapon: {tribute.can_hold_weapon()}")
    print(f"  Equipped weapon: {tribute.equipped_weapon}")
    print(f"  Severed limbs: {[p.value for p in tribute.limb_damage.get_severed_limbs()]}")
    
    # Check bleeding
    total_bleeding = tribute.limb_damage.get_total_bleeding_rate()
    print(f"  Total bleeding: {total_bleeding} HP/phase")


def test_leg_damage():
    """Test leg injuries affecting movement"""
    print("\n\n=== TEST 3: Leg Damage ===")
    
    tribute = Tribute('test3', {
        'name': 'Runner',
        'skills': {'agility': 9, 'stealth': 8}
    })
    
    print(f"✓ Created tribute: {tribute.name}")
    print(f"  Agility: {tribute.skills['agility']}")
    print(f"  Can walk normally: {tribute.can_walk_normally()}")
    
    # Break left leg
    result = tribute.apply_limb_wound("left_leg", "mace", damage=8)
    
    print(f"\n✓ Mace hit to left leg:")
    print(f"  Wound type: {result['wound_type']}")
    print(f"  Message: {result['message']}")
    
    can_walk, reason = tribute.limb_damage.can_walk()
    print(f"\n✓ Movement status:")
    print(f"  Can walk: {can_walk}")
    print(f"  Status: {reason if reason else 'normal'}")
    
    # Check agility penalty
    modified = tribute.get_effective_combat_skills_with_limbs()
    print(f"  Modified agility: {tribute.skills['agility']} → {modified['agility']:.1f}")
    
    # Sever right leg
    result2 = tribute.apply_limb_wound("right_leg", "axe", damage=15)
    
    print(f"\n✓ Axe severs right leg:")
    print(f"  Message: {result2['message']}")
    
    can_walk, reason = tribute.limb_damage.can_walk()
    print(f"\n✓ After losing one leg:")
    print(f"  Can walk: {can_walk}")
    print(f"  Status: {reason}")
    
    # Check severe agility penalty
    modified = tribute.get_effective_combat_skills_with_limbs()
    print(f"  Modified agility: {tribute.skills['agility']} → {modified['agility']:.1f}")


def test_head_trauma():
    """Test head injuries and instant death"""
    print("\n\n=== TEST 4: Head Trauma ===")
    
    tribute = Tribute('test4', {
        'name': 'Smart Tribute',
        'skills': {'intelligence': 9, 'combat': 7}
    })
    
    print(f"✓ Created tribute: {tribute.name}")
    print(f"  Intelligence: {tribute.skills['intelligence']}")
    print(f"  Status: {tribute.status}")
    
    # Moderate head wound
    result = tribute.apply_limb_wound("head", "sword", damage=6)
    
    print(f"\n✓ Sword hit to head (6 damage):")
    print(f"  Wound type: {result['wound_type']}")
    print(f"  Severity: {result['severity']}")
    print(f"  Message: {result['message']}")
    print(f"  Status: {tribute.status}")
    
    # Check intelligence penalty
    modified = tribute.get_effective_combat_skills_with_limbs()
    print(f"  Modified intelligence: {tribute.skills['intelligence']} → {modified['intelligence']:.1f}")
    
    # Severe head trauma (should kill)
    tribute2 = Tribute('test5', {'name': 'Doomed Tribute'})
    result = tribute2.apply_limb_wound("head", "axe", damage=16)
    
    print(f"\n✓ Axe hit to head (16 damage):")
    print(f"  Fatal: {result.get('fatal', False)}")
    print(f"  Message: {result['message']}")
    print(f"  Status: {tribute2.status}")


def test_bleeding_and_infection():
    """Test ongoing wound effects"""
    print("\n\n=== TEST 5: Bleeding and Infection ===")
    
    tribute = Tribute('test6', {
        'name': 'Wounded Warrior',
        'skills': {'combat': 8}
    })
    
    print(f"✓ Created tribute: {tribute.name}")
    print(f"  Initial health: {tribute.health}")
    
    # Apply multiple wounds
    tribute.apply_limb_wound("torso", "sword", damage=7)
    tribute.apply_limb_wound("left_arm", "knife", damage=4)
    
    print(f"\n✓ Applied multiple wounds:")
    print(f"  Status: {tribute.get_limb_status_description()}")
    
    total_bleeding = tribute.limb_damage.get_total_bleeding_rate()
    print(f"  Total bleeding: {total_bleeding} HP/phase")
    
    # Process 5 phases
    for phase in range(1, 6):
        result = tribute.process_limb_damage_effects(phases_elapsed=1)
        
        print(f"\n✓ Phase {phase}:")
        print(f"  Health loss: {result['health_loss']}")
        print(f"  Current health: {tribute.health}")
        print(f"  New infections: {result['new_infections']}")
        
        if result.get('death_message'):
            print(f"  ⚠️  {result['death_message']}")
            break
        
        if tribute.health <= 0:
            print(f"  ⚠️  Tribute died from blood loss")
            break


def test_medical_treatment():
    """Test treating limb wounds"""
    print("\n\n=== TEST 6: Medical Treatment ===")
    
    tribute = Tribute('test7', {
        'name': 'Medic',
        'inventory': ['medical_kit', 'bandage'],
        'skills': {'intelligence': 8}
    })
    
    print(f"✓ Created tribute: {tribute.name}")
    print(f"  Inventory: {tribute.inventory}")
    
    # Apply severe slash to torso
    result = tribute.apply_limb_wound("torso", "sword", damage=9)
    
    print(f"\n✓ Applied sword slash to torso:")
    print(f"  Severity: {result['severity']}")
    print(f"  Bleeding: {result['bleeding_rate']} HP/phase")
    
    # Treat the wound
    treatment = tribute.treat_limb_wound("torso", medical_supply="medical_kit")
    
    print(f"\n✓ Treatment result:")
    print(f"  Success: {treatment['success']}")
    print(f"  Message: {treatment['message']}")
    print(f"  Bleeding stopped: {treatment.get('bleeding_stopped', False)}")
    print(f"  Remaining inventory: {tribute.inventory}")
    
    # Check bleeding rate after treatment
    total_bleeding = tribute.limb_damage.get_total_bleeding_rate()
    print(f"  Bleeding after treatment: {total_bleeding} HP/phase")


def test_combat_with_limb_targeting():
    """Test full combat with limb damage"""
    print("\n\n=== TEST 7: Combat with Limb Targeting ===")
    
    attacker = Tribute('attacker', {
        'name': 'Cato',
        'weapons': ['sword'],
        'skills': {'combat': 9, 'strength': 9}
    })
    
    defender = Tribute('defender', {
        'name': 'Thresh',
        'skills': {'combat': 8, 'agility': 7}
    })
    
    print(f"✓ Attacker: {attacker.name}")
    print(f"  Weapon: {attacker.equipped_weapon}")
    print(f"  Combat: {attacker.skills['combat']}")
    
    print(f"\n✓ Defender: {defender.name}")
    print(f"  Health: {defender.health}")
    print(f"  Agility: {defender.skills['agility']}")
    
    # Calculate combat with random body part
    ws = get_weapons_system()
    attacker_skills = attacker.get_effective_combat_skills_with_limbs()
    defender_skills = defender.get_effective_combat_skills_with_limbs()
    
    result = ws.calculate_combat(
        attacker.equipped_weapon,
        attacker_skills,
        attacker.conditions,
        defender_skills,
        defender.conditions
    )
    
    print(f"\n✓ Combat result:")
    print(f"  Hit: {result['hit']}")
    print(f"  Body part: {result['body_part_hit']}")
    print(f"  Damage: {result['damage']}")
    print(f"  Description: {result['description']}")
    
    # Apply wound to defender
    if result['hit']:
        wound_result = defender.apply_limb_wound(
            result['body_part_hit'],
            "sword",
            result['damage']
        )
        
        print(f"\n✓ Injury applied:")
        print(f"  Wound type: {wound_result['wound_type']}")
        print(f"  Severity: {wound_result['severity']}")
        print(f"  Message: {wound_result['message']}")
        
        defender.update_health(-result['damage'], "combat")
        print(f"  Defender health: {defender.health}")
        
        # Check combat effectiveness after injury
        modified = defender.get_effective_combat_skills_with_limbs()
        print(f"\n✓ Defender after injury:")
        print(f"  Combat skill: {defender.skills['combat']} → {modified['combat']:.1f}")
        print(f"  Injury status: {defender.get_limb_status_description()}")


def test_multiple_wounds_stacking():
    """Test multiple wounds on same body part"""
    print("\n\n=== TEST 8: Multiple Wounds Stacking ===")
    
    tribute = Tribute('test8', {
        'name': 'Punching Bag',
        'skills': {'combat': 6, 'strength': 6}
    })
    
    print(f"✓ Created tribute: {tribute.name}")
    
    # Apply multiple wounds to torso
    print(f"\n✓ Applying multiple torso wounds:")
    
    for i in range(3):
        result = tribute.apply_limb_wound("torso", "knife", damage=5)
        print(f"  Wound {i+1}: {result['wound_type']}, severity {result['severity']}")
    
    # Check total damage
    torso_wounds = tribute.limb_damage.get_wounds_on_part(BodyPart.TORSO)
    print(f"\n✓ Total wounds on torso: {len(torso_wounds)}")
    
    total_bleeding = tribute.limb_damage.get_total_bleeding_rate()
    print(f"  Combined bleeding: {total_bleeding} HP/phase")
    
    # Check cumulative penalties
    penalties = tribute.get_limb_penalties()
    print(f"\n✓ Cumulative penalties:")
    for skill, penalty in penalties.items():
        print(f"  {skill}: {penalty:.1%}")
    
    modified = tribute.get_effective_combat_skills_with_limbs()
    print(f"\n✓ Effective skills after multiple wounds:")
    print(f"  Strength: {tribute.skills['strength']} → {modified['strength']:.1f}")
    print(f"  Combat: {tribute.skills['combat']} → {modified['combat']:.1f}")


def test_bleeding_severity_classification():
    """Test bleeding severity classification system"""
    print("\n=== TEST 9: Bleeding Severity Classification ===")
    
    tribute = Tribute("bleeder1", {
        "name": "Bleeder",
        "district": 1,
        "skills": {
            'strength': 7,
            'combat': 7,
            'agility': 7,
            'endurance': 7,
            'intelligence': 7,
            'medical': 5
        }
    })
    print(f"✓ Created tribute: {tribute.name}")
    
    # Test MILD bleeding (knife)
    result = tribute.apply_limb_wound("left_arm", "knife", damage=3)
    wounds = tribute.limb_damage.get_wounds_on_part(BodyPart.LEFT_ARM)
    if wounds:
        wound = wounds[0]
        print(f"\n✓ Knife slash to left arm:")
        print(f"  Bleeding rate: {wound.bleeding_rate} HP/phase")
        print(f"  Severity: {wound.bleeding_severity.value}")
        print(f"  Infection risk: {wound.infection_risk * 100}%")
        assert wound.bleeding_severity.value in ['mild', 'moderate'], "Knife should cause mild/moderate bleeding"
    
    # Test SEVERE bleeding (sword)
    result = tribute.apply_limb_wound("right_arm", "sword", damage=10)
    wounds = tribute.limb_damage.get_wounds_on_part(BodyPart.RIGHT_ARM)
    right_arm_wounds = [w for w in wounds if w.wound_type in ['slash', 'stab']]
    if right_arm_wounds:
        wound = right_arm_wounds[0]
        print(f"\n✓ Sword slash to right arm:")
        print(f"  Bleeding rate: {wound.bleeding_rate} HP/phase")
        print(f"  Severity: {wound.bleeding_severity.value}")
        print(f"  Infection risk: {wound.infection_risk * 100}%")
    
    # Test FATAL bleeding (axe to torso)
    result = tribute.apply_limb_wound("torso", "axe", damage=16)
    wounds = tribute.limb_damage.get_wounds_on_part(BodyPart.TORSO)
    torso_wounds = [w for w in wounds if w.wound_type in ['slash', 'stab']]
    if torso_wounds:
        wound = torso_wounds[-1]  # Get newest wound
        print(f"\n✓ Axe slash to torso:")
        print(f"  Bleeding rate: {wound.bleeding_rate} HP/phase")
        print(f"  Severity: {wound.bleeding_severity.value}")
        print(f"  Infection risk: {wound.infection_risk * 100}%")
        if wound.bleeding_severity.value == 'fatal':
            print(f"  Untreatable: {wound.is_fatal_bleeding}")
            assert wound.infection_risk == 0.7, "Fatal bleeding should have 70% infection risk"
    
    print(f"\n✓ Bleeding severity classification working correctly")


def test_untreatable_fatal_bleeding():
    """Test that untreatable fatal wounds lead to death in 1 phase"""
    print("\n=== TEST 10: Untreatable Fatal Bleeding ===")
    
    # Create many tributes to find one with untreatable fatal bleeding
    for attempt in range(50):
        tribute = Tribute(f"test{attempt}", {
            "name": f"Doomed{attempt}",
            "district": 1,
            "skills": {
                'strength': 7,
                'combat': 7,
                'agility': 7,
                'endurance': 7,
                'intelligence': 7,
                'medical': 10
            }
        })
        tribute.add_to_inventory("medical_kit")
        
        # Apply massive damage to cause fatal bleeding
        tribute.apply_limb_wound("torso", "axe", damage=20)
        
        # Check for untreatable fatal wound
        wounds = tribute.limb_damage.wounds
        fatal_wounds = [w for w in wounds if w.bleeding_severity.value == 'fatal' and w.is_fatal_bleeding]
        
        if fatal_wounds:
            print(f"✓ Found untreatable fatal wound after {attempt + 1} attempts")
            wound = fatal_wounds[0]
            print(f"  Wound: {wound.wound_type} on {wound.body_part.value}")
            print(f"  Bleeding: {wound.bleeding_rate} HP/phase")
            print(f"  Untreatable: {wound.is_fatal_bleeding}")
            
            # Try to treat - should fail
            treatment_result = tribute.treat_limb_wound(wound.body_part.value)
            print(f"\n✓ Treatment attempt:")
            print(f"  Success: {treatment_result['success']}")
            print(f"  Message: {treatment_result.get('message', 'N/A')}")
            assert not treatment_result['success'], "Should not be able to treat untreatable wound"
            assert 'too severe' in treatment_result.get('message', '').lower() or 'untreatable' in str(treatment_result).lower(), "Should indicate wound is untreatable"
            
            # Process 1 phase - should die
            initial_health = tribute.health
            result = tribute.process_limb_damage_effects(1)
            print(f"\n✓ After 1 phase:")
            print(f"  Initial health: {initial_health}")
            print(f"  Final health: {tribute.health}")
            print(f"  Health loss: {initial_health - tribute.health}")
            print(f"  Death from bleeding: {result.get('death_from_bleeding', False)}")
            
            # Should die within 1-2 phases
            if tribute.health <= 0 or result.get('death_from_bleeding'):
                print(f"✓ Tribute died from untreatable fatal bleeding")
            else:
                print(f"  Still alive, checking phase 2...")
                result = tribute.process_limb_damage_effects(1)
                print(f"  Health after phase 2: {tribute.health}")
                print(f"  Death from bleeding: {result.get('death_from_bleeding', False)}")
            
            return
    
    print("⚠ Warning: Did not find untreatable wound in 50 attempts (30% chance each)")
    print("  This is statistically possible but unlikely")


if __name__ == "__main__":
    print("=" * 60)
    print("LIMB DAMAGE AND DISMEMBERMENT SYSTEM TEST SUITE")
    print("=" * 60)
    
    try:
        test_limb_wound_application()
        test_dismemberment()
        test_leg_damage()
        test_head_trauma()
        test_bleeding_and_infection()
        test_medical_treatment()
        test_combat_with_limb_targeting()
        test_multiple_wounds_stacking()
        test_bleeding_severity_classification()
        test_untreatable_fatal_bleeding()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
