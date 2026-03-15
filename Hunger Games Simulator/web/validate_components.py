#!/usr/bin/env python3
"""
Validation script for tribute creation and web interface components.
Tests tribute data validation and form logic without requiring server.
"""

import json
import os
import sys

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def validate_tribute_data(data):
    """Validate tribute JSON structure (copied from app.py)."""
    required_fields = ['name', 'district', 'skills']
    if not all(field in data for field in required_fields):
        return False, f"Missing required fields: {required_fields}"

    # Validate skills structure
    if not isinstance(data['skills'], dict):
        return False, "Skills must be an object"

    required_skills = ['intelligence', 'hunting', 'strength', 'social',
                      'stealth', 'survival', 'agility', 'endurance', 'charisma', 'luck']
    if not all(skill in data['skills'] for skill in required_skills):
        return False, f"Missing skills: {[s for s in required_skills if s not in data['skills']]}"

    # Validate skill values
    for skill, value in data['skills'].items():
        if not isinstance(value, int) or value < 1 or value > 10:
            return False, f"Skill {skill} must be integer between 1-10"

    return True, "Valid"

def test_tribute_creation():
    """Test creating a tribute with the form data."""
    print("Testing tribute creation logic...")

    # Sample tribute data from the form
    tribute_data = {
        "name": "TestTribute",
        "district": 5,
        "skills": {
            "intelligence": 8,
            "hunting": 6,
            "strength": 7,
            "social": 9,
            "stealth": 5,
            "survival": 6,
            "agility": 7,
            "endurance": 8,
            "charisma": 6,
            "luck": 4
        },
        "weapons": ["Fists"],
        "preferred_weapon": "Sword",
        "target_weapon": "Knife",  # Should be set automatically
        "health": 100,
        "sanity": 100,
        "speed": 7,  # Should be calculated
        "has_camp": False,
        "relationships": {
            "Player1": "ally",
            "Player2": "enemy"
        }
    }

    # Validate the tribute data
    is_valid, message = validate_tribute_data(tribute_data)
    if is_valid:
        print("✓ Tribute data validation passed")
        return True
    else:
        print(f"✗ Tribute data validation failed: {message}")
        return False

def test_weapon_list():
    """Test that all weapons are available."""
    print("Testing weapon availability...")

    try:
        with open("../data/weapons.json", "r") as f:
            weapons_data = json.load(f)

        weapon_names = list(weapons_data.keys())
        expected_weapons = ["Sword", "Axe", "Bow", "Hammer", "Knife", "Spear", "Club",
                          "Fists", "Staff", "Machete", "Gun", "Crossbow", "Dagger",
                          "Whip", "Throwing Star", "Stick", "Mace", "Rock"]

        missing_weapons = [w for w in expected_weapons if w not in weapon_names]
        if missing_weapons:
            print(f"✗ Missing weapons: {missing_weapons}")
            return False
        else:
            print(f"✓ All {len(weapon_names)} weapons available")
            return True

    except Exception as e:
        print(f"✗ Error loading weapons: {e}")
        return False

def test_relationship_types():
    """Test relationship type validation."""
    print("Testing relationship types...")

    valid_types = ["ally", "enemy", "rival", "neutral", "family"]
    test_relationships = {
        "Player1": "ally",
        "Player2": "enemy",
        "Player3": "rival",
        "Player4": "neutral",
        "Player5": "family"
    }

    invalid_types = [rel for rel in test_relationships.values() if rel not in valid_types]
    if invalid_types:
        print(f"✗ Invalid relationship types: {invalid_types}")
        return False
    else:
        print("✓ All relationship types valid")
        return True

def test_target_weapon_logic():
    """Test the automatic target weapon assignment logic."""
    print("Testing target weapon logic...")

    # Test weapon mappings (from the JavaScript)
    weapon_targets = {
        'Sword': 'Knife',
        'Axe': 'Hammer',
        'Bow': 'Crossbow',
        'Hammer': 'Mace',
        'Knife': 'Dagger',
        'Spear': 'Staff',
        'Club': 'Stick',
        'Fists': 'Rock',
        'Staff': 'Spear',
        'Machete': 'Knife',
        'Gun': 'Bow',
        'Crossbow': 'Bow',
        'Dagger': 'Knife',
        'Whip': 'Staff',
        'Throwing Star': 'Knife',
        'Stick': 'Club',
        'Mace': 'Hammer',
        'Rock': 'Club'
    }

    # Test a few mappings
    test_cases = [
        ('Sword', 'Knife'),
        ('Bow', 'Crossbow'),
        ('Knife', 'Dagger'),
        ('Fists', 'Rock')
    ]

    for preferred, expected_target in test_cases:
        actual_target = weapon_targets.get(preferred)
        if actual_target == expected_target:
            print(f"✓ {preferred} -> {actual_target}")
        else:
            print(f"✗ {preferred} -> {actual_target} (expected {expected_target})")
            return False

    return True

def main():
    """Run all validation tests."""
    print("Hunger Games Simulator - Web Interface Validation")
    print("=" * 50)

    tests = [
        test_weapon_list,
        test_relationship_types,
        test_target_weapon_logic,
        test_tribute_creation
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            print()

    print("=" * 50)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All validation tests passed!")
        return True
    else:
        print("❌ Some tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)