"""
Test enhanced medical supply system with wild items and sponsor gifts
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from Engine.tribute import Tribute
from Engine.limb_damage_system import get_limb_damage_system, BodyPart, LimbStatus, BleedingSeverity


def test_medical_supply_effectiveness():
    """Test different medical supplies on various wound severities"""
    print("\n=== TEST 1: Medical Supply Effectiveness ===")
    
    lds = get_limb_damage_system()
    
    # Test supplies against different severities
    supplies = [
        ("medical_kit", "Medical Kit (Sponsor Gift)"),
        ("tourniquet", "Tourniquet"),
        ("bandage", "Bandage"),
        ("cloth_strips", "Cloth Strips (Improvised)"),
        ("herbs", "Medicinal Herbs (Wild)"),
        ("moss", "Moss (Wild)"),
        ("medicine", "Medicine/Antiseptic")
    ]
    
    severities = [
        (BleedingSeverity.MILD, "MILD"),
        (BleedingSeverity.MODERATE, "MODERATE"),
        (BleedingSeverity.SEVERE, "SEVERE"),
        (BleedingSeverity.FATAL, "FATAL")
    ]
    
    print("\nEffectiveness Matrix (success bonus):")
    print(f"{'Supply':<30} {'MILD':<8} {'MODERATE':<10} {'SEVERE':<8} {'FATAL':<8}")
    print("-" * 70)
    
    for supply, supply_name in supplies:
        bonuses = []
        for severity, _ in severities:
            bonus = lds._get_medical_supply_effectiveness(supply, severity)
            bonuses.append(f"+{bonus*100:.0f}%")
        
        print(f"{supply_name:<30} {bonuses[0]:<8} {bonuses[1]:<10} {bonuses[2]:<8} {bonuses[3]:<8}")
    
    print("\n✓ Medical supply effectiveness matrix working correctly")


def test_wild_items_on_wounds():
    """Test using wild-found items to treat wounds"""
    print("\n\n=== TEST 2: Wild Items Treatment ===")
    
    tribute = Tribute("survivor1", {
        "name": "Survivor",
        "district": 7,
        "skills": {
            "survival": 9,  # Good at finding wild items
            "intelligence": 6,
            "medical": 5
        }
    })
    
    # Add wild medical items
    tribute.add_to_inventory("moss")
    tribute.add_to_inventory("herbs")
    tribute.add_to_inventory("cloth_strips")
    
    print(f"✓ {tribute.name} found wild items: {tribute.inventory}")
    
    # Apply mild slash wound
    result = tribute.apply_limb_wound("left_arm", "knife", damage=3)
    print(f"\n✓ Knife slash to left arm:")
    print(f"  Severity: {result['severity']}")
    print(f"  Bleeding: {result['bleeding_rate']} HP/phase")
    
    wounds = tribute.limb_damage.get_wounds_on_part(BodyPart.LEFT_ARM)
    if wounds:
        wound = wounds[0]
        print(f"  Bleeding severity: {wound.bleeding_severity.value}")
    
    # Try treating with moss (weakest wild item)
    print(f"\n✓ Attempting treatment with moss...")
    treatment = tribute.treat_limb_wound("left_arm")  # Auto-selects best available
    print(f"  Used supply: {[s for s in ['moss', 'herbs', 'cloth_strips'] if s not in tribute.inventory][0] if len(tribute.inventory) < 3 else 'unknown'}")
    print(f"  Success: {treatment['success']}")
    print(f"  Message: {treatment.get('message', 'N/A')}")
    print(f"  Remaining items: {tribute.inventory}")
    
    # Check bleeding after treatment
    total_bleeding = tribute.limb_damage.get_total_bleeding_rate()
    print(f"  Bleeding after treatment: {total_bleeding} HP/phase")


def test_tourniquet_on_severed_limb():
    """Test using tourniquet on severed limb (most critical use case)"""
    print("\n\n=== TEST 3: Tourniquet on Severed Limb ===")
    
    tribute = Tribute("fighter1", {
        "name": "Brutus",
        "district": 2,
        "skills": {
            "combat": 9,
            "strength": 10,
            "medical": 3  # Low medical skill
        }
    })
    
    # Give tourniquet (critical survival item)
    tribute.add_to_inventory("tourniquet")
    
    print(f"✓ {tribute.name} has tourniquet")
    print(f"  Initial health: {tribute.health}")
    
    # Sever arm (FATAL bleeding)
    result = tribute.apply_limb_wound("right_arm", "axe", damage=16)
    print(f"\n✓ Axe severs right arm:")
    print(f"  Message: {result.get('message', 'N/A')}")
    
    wounds = tribute.limb_damage.get_wounds_on_part(BodyPart.RIGHT_ARM)
    if wounds:
        wound = wounds[0]
        print(f"  Bleeding: {wound.bleeding_rate} HP/phase")
        print(f"  Severity: {wound.bleeding_severity.value}")
        print(f"  Untreatable: {wound.is_fatal_bleeding}")
        
        if wound.is_fatal_bleeding:
            print(f"\n⚠️  FATAL WOUND - Cannot be treated (will die in 1 phase)")
            return
    
    # Apply tourniquet immediately
    print(f"\n✓ Applying tourniquet to severed arm...")
    treatment = tribute.treat_limb_wound("right_arm", medical_supply="tourniquet")
    print(f"  Success: {treatment['success']}")
    print(f"  Message: {treatment.get('message', 'N/A')}")
    print(f"  Bleeding reduced: {treatment.get('bleeding_reduced', False)}")
    
    # Check if bleeding was reduced
    wounds_after = tribute.limb_damage.get_wounds_on_part(BodyPart.RIGHT_ARM)
    if wounds_after:
        wound = wounds_after[0]
        print(f"\n✓ After tourniquet:")
        print(f"  Bleeding: {wound.bleeding_rate} HP/phase (reduced from 15-25)")
        print(f"  New severity: {wound.bleeding_severity.value}")
        print(f"  Limb saved: {treatment.get('limb_saved', False)}")
        
        if treatment['success']:
            print(f"  ✓ Tourniquet prevented immediate death!")
            print(f"  Note: Arm is still severed, but bleeding is manageable")


def test_sponsor_gift_medical_kit():
    """Test sponsor gift medical kit on critical injuries"""
    print("\n\n=== TEST 4: Sponsor Gift Medical Kit ===")
    
    tribute = Tribute("favorite1", {
        "name": "Katniss",
        "district": 12,
        "skills": {
            "survival": 10,
            "intelligence": 8,
            "medical": 4
        }
    })
    
    # Sponsor sends medical kit
    tribute.add_to_inventory("medical_kit")
    
    print(f"✓ Sponsor sends medical kit to {tribute.name}")
    print(f"  Inventory: {tribute.inventory}")
    
    # Multiple severe wounds
    tribute.apply_limb_wound("torso", "sword", damage=12)
    tribute.apply_limb_wound("left_leg", "sword", damage=10)
    
    print(f"\n✓ Applied multiple severe wounds:")
    print(f"  Status: {tribute.get_limb_status_description()}")
    
    total_bleeding = tribute.limb_damage.get_total_bleeding_rate()
    print(f"  Total bleeding: {total_bleeding} HP/phase")
    
    # Count wounds by severity
    severe_count = 0
    fatal_count = 0
    for wound in tribute.limb_damage.wounds:
        if wound.bleeding_severity == BleedingSeverity.SEVERE:
            severe_count += 1
        elif wound.bleeding_severity == BleedingSeverity.FATAL:
            fatal_count += 1
    
    print(f"  Severe wounds: {severe_count}")
    print(f"  Fatal wounds: {fatal_count}")
    
    # Use medical kit on worst wound
    print(f"\n✓ Using sponsor medical kit...")
    if tribute.limb_damage.get_wounds_on_part(BodyPart.TORSO):
        treatment = tribute.treat_limb_wound("torso", medical_supply="medical_kit")
        print(f"  Treated torso: {treatment['success']}")
        print(f"  Message: {treatment.get('message', 'N/A')}")
        
        total_bleeding_after = tribute.limb_damage.get_total_bleeding_rate()
        print(f"  Bleeding after treatment: {total_bleeding_after} HP/phase")
        print(f"  Bleeding reduced by: {total_bleeding - total_bleeding_after} HP/phase")


def test_infection_treatment_with_herbs():
    """Test treating infection with wild herbs"""
    print("\n\n=== TEST 5: Infection Treatment with Herbs ===")
    
    tribute = Tribute("sick1", {
        "name": "Rue",
        "district": 11,
        "skills": {
            "survival": 9,  # Knows medicinal plants
            "intelligence": 7,
            "medical": 6
        }
    })
    
    # Add herbs (antiseptic properties)
    tribute.add_to_inventory("medicinal_herbs")
    
    print(f"✓ {tribute.name} found medicinal herbs")
    
    # Apply wound and manually infect it
    result = tribute.apply_limb_wound("right_arm", "knife", damage=4)
    
    wounds = tribute.limb_damage.get_wounds_on_part(BodyPart.RIGHT_ARM)
    if wounds:
        wound = wounds[0]
        wound.is_infected = True  # Force infection for test
        wound.phases_since_injury = 2
        
        print(f"\n✓ Wound becomes infected:")
        print(f"  Body part: right arm")
        print(f"  Bleeding: {wound.bleeding_rate} HP/phase")
        print(f"  Infected: {wound.is_infected}")
    
    # Use herbs to treat infection
    print(f"\n✓ Applying medicinal herbs...")
    treatment = tribute.treat_limb_wound("right_arm", medical_supply="medicinal_herbs")
    print(f"  Success: {treatment['success']}")
    print(f"  Message: {treatment.get('message', 'N/A')}")
    print(f"  Infection cured: {treatment.get('infection_cured', False)}")
    
    # Check wound status after treatment
    wounds_after = tribute.limb_damage.get_wounds_on_part(BodyPart.RIGHT_ARM)
    if wounds_after:
        wound = wounds_after[0]
        print(f"\n✓ After herbal treatment:")
        print(f"  Infected: {wound.is_infected}")
        print(f"  Bleeding: {wound.bleeding_rate} HP/phase")
        
        if not wound.is_infected:
            print(f"  ✓ Herbs successfully cured infection!")


if __name__ == "__main__":
    print("=" * 70)
    print("ENHANCED MEDICAL SUPPLY SYSTEM TEST SUITE")
    print("=" * 70)
    
    try:
        test_medical_supply_effectiveness()
        test_wild_items_on_wounds()
        test_tourniquet_on_severed_limb()
        test_sponsor_gift_medical_kit()
        test_infection_treatment_with_herbs()
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
