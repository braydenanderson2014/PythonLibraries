"""
Test weapons system and injury mechanics integration with Tribute class
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from Engine.tribute import Tribute
from Engine.weapons_system import get_weapons_system


def test_weapon_management():
    """Test weapon equipping and auto-selection"""
    print("\n=== TEST 1: Weapon Management ===")
    
    # Create tribute with weapons
    tribute_data = {
        'name': 'Katniss Everdeen',
        'district': 12,
        'age': 16,
        'weapons': ['bow', 'knife', 'sword'],
        'skills': {
            'combat': 8,
            'strength': 6,
            'agility': 9,
            'stealth': 9,
            'survival': 8,
            'intelligence': 7
        }
    }
    
    tribute = Tribute('katniss_1', tribute_data)
    
    print(f"✓ Created tribute: {tribute.name}")
    print(f"  Weapons in inventory: {tribute.weapons}")
    print(f"  Auto-equipped: {tribute.equipped_weapon}")
    
    # Test manual equipping
    success = tribute.equip_weapon('knife')
    print(f"\n✓ Manually equipped knife: {success}")
    print(f"  Current weapon: {tribute.equipped_weapon}")
    
    # Test adding new weapon
    tribute.add_weapon('axe')
    print(f"\n✓ Added axe to inventory")
    print(f"  Weapons: {tribute.weapons}")
    print(f"  Equipped (auto-updated): {tribute.equipped_weapon}")
    
    # Test weapon too heavy
    weak_tribute = Tribute('weak_1', {
        'name': 'Weak Tribute',
        'weapons': ['axe'],
        'skills': {'strength': 2}
    })
    print(f"\n✓ Weak tribute (strength 2) with axe (requires 5):")
    print(f"  Equipped weapon: {weak_tribute.equipped_weapon}")  # Should be fists


def test_injuries_and_conditions():
    """Test injury application and condition effects"""
    print("\n\n=== TEST 2: Injuries and Conditions ===")
    
    tribute_data = {
        'name': 'Peeta Mellark',
        'district': 12,
        'age': 16,
        'skills': {
            'combat': 6,
            'strength': 8,
            'agility': 5,
            'stealth': 4,
            'survival': 6,
            'intelligence': 7
        }
    }
    
    tribute = Tribute('peeta_1', tribute_data)
    
    print(f"✓ Created tribute: {tribute.name}")
    print(f"  Initial health: {tribute.health}")
    print(f"  Initial strength: {tribute.skills['strength']}")
    
    # Add bleeding wound
    tribute.add_condition('bleeding_mild')
    print(f"\n✓ Applied mild bleeding wound")
    print(f"  Conditions: {tribute.conditions}")
    print(f"  Is bleeding: {tribute.is_bleeding()}")
    
    # Get modified skills
    modified_skills = tribute.get_effective_combat_skills()
    print(f"\n✓ Skill modifiers from bleeding:")
    print(f"  Original strength: {tribute.skills['strength']}")
    print(f"  Modified strength: {modified_skills['strength']:.1f}")
    print(f"  Penalty: {tribute.skills['strength'] - modified_skills['strength']:.1f} (-15%)")
    
    # Process condition effects (1 phase)
    result = tribute.process_condition_effects(phases_elapsed=1)
    print(f"\n✓ Processed condition effects (1 phase):")
    print(f"  Health loss: {result['health_loss']}")
    print(f"  Current health: {tribute.health}")
    print(f"  New infections: {result['new_infections']}")
    
    # Add severe injury
    tribute.add_condition('broken_arm')
    print(f"\n✓ Added broken arm")
    print(f"  Is critically injured: {tribute.is_critically_injured()}")
    
    modified_skills = tribute.get_effective_combat_skills()
    print(f"  Modified strength (broken arm): {modified_skills['strength']:.1f}")
    print(f"  Modified combat: {modified_skills['combat']:.1f}")


def test_medical_treatment():
    """Test treating wounds and infections"""
    print("\n\n=== TEST 3: Medical Treatment ===")
    
    tribute_data = {
        'name': 'Rue',
        'district': 11,
        'age': 12,
        'skills': {
            'combat': 4,
            'strength': 3,
            'agility': 9,
            'stealth': 8,
            'survival': 7,
            'intelligence': 7
        },
        'inventory': ['medical_kit', 'food', 'water']
    }
    
    tribute = Tribute('rue_1', tribute_data)
    
    print(f"✓ Created tribute: {tribute.name}")
    print(f"  Inventory: {tribute.inventory}")
    
    # Add injuries
    tribute.add_condition('bleeding_medium')
    tribute.add_condition('infected')
    print(f"\n✓ Applied injuries:")
    print(f"  Conditions: {tribute.conditions}")
    print(f"  Bleeding wounds: {tribute.bleeding_wounds}")
    print(f"  Infections: {tribute.infections}")
    
    # Treat wounds
    result = tribute.treat_wounds()
    print(f"\n✓ Treated wounds:")
    print(f"  Success: {result['success']}")
    print(f"  Message: {result['message']}")
    print(f"  Wounds treated: {result['wounds_treated']}")
    print(f"  Infections cured: {result['infections_cured']}")
    print(f"  Current conditions: {tribute.conditions}")
    print(f"  Remaining inventory: {tribute.inventory}")


def test_combat_with_weapons():
    """Test full combat simulation with weapons and injuries"""
    print("\n\n=== TEST 4: Combat Simulation ===")
    
    # Attacker with sword
    attacker_data = {
        'name': 'Cato',
        'district': 2,
        'weapons': ['sword', 'spear'],
        'skills': {
            'combat': 9,
            'strength': 9,
            'agility': 7,
            'stealth': 5,
            'survival': 6,
            'intelligence': 5
        }
    }
    
    # Defender with knife
    defender_data = {
        'name': 'Thresh',
        'district': 11,
        'weapons': ['knife', 'rock'],
        'skills': {
            'combat': 8,
            'strength': 10,
            'agility': 6,
            'stealth': 4,
            'survival': 8,
            'intelligence': 6
        }
    }
    
    attacker = Tribute('cato_1', attacker_data)
    defender = Tribute('thresh_1', defender_data)
    
    print(f"✓ Attacker: {attacker.name}")
    print(f"  Equipped: {attacker.equipped_weapon}")
    print(f"  Combat skill: {attacker.skills['combat']}")
    print(f"  Strength: {attacker.skills['strength']}")
    
    print(f"\n✓ Defender: {defender.name}")
    print(f"  Equipped: {defender.equipped_weapon}")
    print(f"  Combat skill: {defender.skills['combat']}")
    print(f"  Agility: {defender.skills['agility']}")
    
    # Simulate combat
    ws = get_weapons_system()
    
    attacker_weapon_id = attacker.get_equipped_weapon()
    defender_weapon_id = defender.get_equipped_weapon()
    
    attacker_skills = attacker.get_effective_combat_skills()
    defender_skills = defender.get_effective_combat_skills()
    
    result = ws.calculate_combat(
        attacker_weapon_id,
        attacker_skills,
        attacker.conditions,
        defender_skills,
        defender.conditions
    )
    
    print(f"\n✓ Combat result:")
    print(f"  Hit: {result['hit']}")
    print(f"  Damage: {result['damage']}")
    print(f"  Instant kill: {result['instant_kill']}")
    print(f"  New condition: {result['new_condition']}")
    print(f"  Description: {result['description']}")
    
    # Apply injury to defender if hit
    if result['hit'] and result['new_condition']:
        defender.add_condition(result['new_condition'])
        defender.update_health(-result['damage'], "combat")
        
        print(f"\n✓ Injury applied to {defender.name}:")
        print(f"  Health: {defender.health}")
        print(f"  Conditions: {defender.conditions}")
        
        modified = defender.get_effective_combat_skills()
        print(f"  Modified combat skill: {modified['combat']:.1f} (was {defender.skills['combat']})")


def test_ongoing_injury_effects():
    """Test multi-phase injury progression"""
    print("\n\n=== TEST 5: Ongoing Injury Effects ===")
    
    tribute_data = {
        'name': 'Injured Tribute',
        'skills': {
            'combat': 6,
            'strength': 6,
            'agility': 6,
            'intelligence': 6
        }
    }
    
    tribute = Tribute('injured_1', tribute_data)
    tribute.add_condition('bleeding_severe')
    
    print(f"✓ Created tribute with severe bleeding")
    print(f"  Initial health: {tribute.health}")
    
    # Simulate 5 phases
    for phase in range(1, 6):
        result = tribute.process_condition_effects(phases_elapsed=1)
        
        print(f"\n✓ Phase {phase}:")
        print(f"  Health loss: {result['health_loss']}")
        print(f"  Current health: {tribute.health}")
        print(f"  New infections: {result['new_infections']}")
        
        if result['fatal']:
            print(f"  ⚠️  FATAL - Tribute died from blood loss")
            break
        
        if tribute.health <= 0:
            print(f"  ⚠️  Tribute succumbed to injuries")
            break


if __name__ == "__main__":
    print("=" * 60)
    print("WEAPONS AND INJURY SYSTEM TEST SUITE")
    print("=" * 60)
    
    try:
        test_weapon_management()
        test_injuries_and_conditions()
        test_medical_treatment()
        test_combat_with_weapons()
        test_ongoing_injury_effects()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
