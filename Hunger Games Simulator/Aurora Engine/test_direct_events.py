#!/usr/bin/env python3
"""
Direct test of event generation and name replacement
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'Engine'))

from aurora_integration import AuroraLobbyIntegration

def test_event_generation_directly():
    """Test event generation and name replacement directly"""
    print("=== Direct Event Generation Test ===\n")
    
    # Create integration
    integration = AuroraLobbyIntegration()
    config_path = os.path.join("Engine", "config.json")
    integration.initialize_engine("test_lobby", config_path)
    
    # Create test tributes
    test_players = [
        {
            "id": "tribute1",
            "name": "Player1", 
            "tribute_ready": True,
            "tribute_data": {
                "name": "Cato Williams",
                "district": 2,
                "gender": "Male",
                "age": 18,
                "skills": {"strength": 10, "endurance": 9, "agility": 8, "hunting": 7, "intelligence": 6, "charisma": 6, "social": 5, "stealth": 4, "survival": 5, "luck": 4},
                "skill_priority": ["strength", "endurance", "agility"]
            }
        },
        {
            "id": "tribute2",
            "name": "Player2", 
            "tribute_ready": True,
            "tribute_data": {
                "name": "Katniss Everdeen",
                "district": 12,
                "gender": "Female",
                "age": 16,
                "skills": {"hunting": 9, "stealth": 8, "survival": 9, "agility": 7, "intelligence": 6, "strength": 5, "endurance": 7, "social": 4, "charisma": 5, "luck": 6},
                "skill_priority": ["hunting", "stealth", "survival"]
            }
        },
        {
            "id": "tribute3",
            "name": "Player3", 
            "tribute_ready": True,
            "tribute_data": {
                "name": "Rue Martinez",
                "district": 11,
                "gender": "Female",
                "age": 12,
                "skills": {"agility": 9, "stealth": 8, "survival": 7, "intelligence": 7, "hunting": 6, "social": 6, "endurance": 5, "charisma": 5, "strength": 3, "luck": 6},
                "skill_priority": ["agility", "stealth", "survival"]
            }
        }
    ]
    
    # Start the game
    game_started = integration.start_game(test_players)
    if not game_started:
        print("✗ Failed to start game")
        return
    
    print("✓ Game started with 3 tributes")
    
    # Get the engine directly
    engine = integration.engine
    
    # Test event generation directly
    print("\n=== Testing Direct Event Generation ===")
    
    for i in range(5):
        print(f"\n--- Direct Event {i+1} ---")
        
        # Try to generate events directly
        event = engine.generate_event("Combat Events")
        if event:
            event_data = event.get('data', {}).get('event_data', {})
            narrative = event_data.get('narrative', '')
            description = event_data.get('description', '')
            name = event_data.get('name', 'Unknown')
            
            print(f"Event Name: {name}")
            print(f"Narrative: {narrative}")
            print(f"Description: {description}")
            
            # Check for names
            tribute_names = ['Cato Williams', 'Katniss Everdeen', 'Rue Martinez']
            found_names = [tn for tn in tribute_names if tn in narrative or tn in description]
            
            # Check for placeholders
            has_placeholders = '{tribute' in narrative or '{name' in narrative or '{tribute' in description
            
            print(f"Found Names: {found_names}")
            print(f"Has Placeholders: {has_placeholders}")
            
            if found_names and not has_placeholders:
                print("✅ Name replacement working correctly!")
            elif has_placeholders:
                print("❌ Placeholders not replaced!")
            else:
                print("⚠️ No tribute names found (might be non-tribute event)")
                
        else:
            print("No event generated")
            
        # Try different event types
        if i == 1:
            event = engine.generate_event("Arena Events")
        elif i == 2:
            event = engine.generate_event("PvP Events")
        
    # Also test the tribute data access directly
    print(f"\n=== Testing Tribute Data Access ===")
    for tribute_id, tribute_obj in engine.game_state.tributes.items():
        print(f"Tribute ID: {tribute_id}")
        print(f"  Name: {tribute_obj.name}")
        print(f"  District: {tribute_obj.district}")
        print(f"  Type: {type(tribute_obj)}")

if __name__ == "__main__":
    test_event_generation_directly()