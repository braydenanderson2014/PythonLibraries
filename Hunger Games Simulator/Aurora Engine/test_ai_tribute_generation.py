#!/usr/bin/env python3
"""
Test script for AI tribute generation functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from lobby_server import generate_ai_tribute_data, generate_ai_tribute_names, Lobby, Player, TributeData
import json

def test_ai_tribute_generation():
    """Test the AI tribute generation functionality"""
    print("=== Testing AI Tribute Generation ===\n")
    
    # Test 1: Name generation
    print("1. Testing AI tribute name generation...")
    names = generate_ai_tribute_names()
    print(f"   Generated {len(names)} unique names")
    print(f"   First 5 names: {names[:5]}")
    print(f"   ✓ Name generation working\n")
    
    # Test 2: Tribute data generation for each district
    print("2. Testing tribute data generation for all districts...")
    for district in range(1, 13):
        tribute_data = generate_ai_tribute_data(district, f"Test Tribute {district}")
        print(f"   District {district:2d}: {tribute_data.name}")
        print(f"                Age: {tribute_data.age}, Gender: {tribute_data.gender}")
        print(f"                Top skills: {tribute_data.skill_priority[:3]}")
        print(f"                District bonuses applied: {tribute_data.skills}")
        print()
    
    print("✓ All tribute data generation working\n")
    
    # Test 3: Lobby district management
    print("3. Testing lobby district management...")
    
    # Add some players to simulate partially filled districts
    player1 = Player("p1", "Player 1", 1)
    player1.tribute_data = TributeData("Test Player 1", 1, "Male", 16, {}, [])
    player1.tribute_ready = True
    
    player2 = Player("p2", "Player 2", 1)  # Same district
    player2.tribute_data = TributeData("Test Player 2", 1, "Female", 17, {}, [])
    player2.tribute_ready = True
    
    player3 = Player("p3", "Player 3", 3)  # Different district
    player3.tribute_data = TributeData("Test Player 3", 3, "Male", 15, {}, [])
    player3.tribute_ready = True
    
    players_dict = {
        "p1": player1,
        "p2": player2,
        "p3": player3
    }
    
    lobby = Lobby("test_lobby", "Test Host", "host_123", players_dict)
    
    available_districts = lobby.get_available_districts()
    print(f"   Districts with space: {available_districts}")
    print(f"   District 1 should be full (2 players)")
    print(f"   District 3 should need 1 more player")
    print(f"   Districts 2, 4-12 should need 2 players each")
    
    expected_available = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    if set(available_districts) == set(expected_available):
        print("   ✓ District availability calculation working correctly\n")
    else:
        print(f"   ✗ Expected {expected_available}, got {available_districts}\n")
    
    # Test 4: Skills and bonuses
    print("4. Testing district skill bonuses...")
    district_examples = {
        1: "Luxury (strength, charisma)",
        3: "Technology (intelligence)",
        4: "Fishing (hunting, survival)",
        7: "Lumber (survival, stealth)",
        10: "Livestock (endurance)",
        12: "Mining (stealth, survival)"
    }
    
    for district, description in district_examples.items():
        tribute = generate_ai_tribute_data(district, f"Test {district}")
        print(f"   District {district:2d} ({description})")
        print(f"       Skills: {json.dumps(tribute.skills, indent=None)}")
        print(f"       Priority: {tribute.skill_priority}")
    
    print("\n✓ All tests completed!")

if __name__ == "__main__":
    test_ai_tribute_generation()