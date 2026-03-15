#!/usr/bin/env python3
"""
Direct test of cornucopia supply distribution without waiting for countdown
"""

import sys
import os
import time
sys.path.append(os.path.join(os.path.dirname(__file__), 'Engine'))

from aurora_integration import AuroraLobbyIntegration

def test_cornucopia_supply_distribution():
    """Test cornucopia supply distribution directly"""
    print("=== Direct Cornucopia Supply Distribution Test ===\n")
    
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
                "name": "Alex Johnson",
                "district": 1,
                "gender": "Male",
                "age": 17,
                "skills": {"strength": 8, "agility": 7, "hunting": 7, "endurance": 7, "charisma": 6, "intelligence": 6, "social": 6, "stealth": 5, "survival": 5, "luck": 5},
                "skill_priority": ["strength", "agility", "hunting"]
            }
        },
        {
            "id": "tribute2",
            "name": "Player2", 
            "tribute_ready": True,
            "tribute_data": {
                "name": "Sarah Chen",
                "district": 3,
                "gender": "Female",
                "age": 16,
                "skills": {"intelligence": 9, "agility": 7, "stealth": 7, "social": 6, "survival": 6, "endurance": 5, "hunting": 5, "strength": 4, "charisma": 5, "luck": 6},
                "skill_priority": ["intelligence", "agility", "stealth"]
            }
        }
    ]
    
    # Start the game
    game_started = integration.start_game(test_players)
    if not game_started:
        print("✗ Failed to start game")
        return
    
    print("✓ Game started with 2 tributes")
    
    # Check initial supplies
    print(f"\n=== Initial Supply Check ===")
    engine = integration.engine
    for tribute_id, tribute_obj in engine.game_state.tributes.items():
        print(f"{tribute_obj.name}: Inventory={tribute_obj.inventory}, Weapons={tribute_obj.weapons}, Food={tribute_obj.food_supplies}, Water={tribute_obj.water_supplies}")
    
    # Directly force cornucopia bloodbath
    print(f"\n=== Forcing Cornucopia Bloodbath ===")
    
    # Get tribute data
    tributes = []
    for tribute_id, tribute_obj in engine.game_state.tributes.items():
        tributes.append({
            "id": tribute_id,
            "name": tribute_obj.name,
            "skills": tribute_obj.skills,
            "district": tribute_obj.district
        })
    
    # Force cornucopia to bloodbath phase
    cornucopia_controller = engine.cornucopia_controller
    cornucopia_controller.current_phase = cornucopia_controller.current_phase.__class__.BLOODBATH
    cornucopia_controller.cornucopia_participants = ["tribute1", "tribute2"]  # Both participate
    
    print(f"Phase: {cornucopia_controller.current_phase.value}")
    print(f"Participants: {cornucopia_controller.cornucopia_participants}")
    
    # Manually call process_cornucopia_updates which should trigger bloodbath
    messages = engine.process_cornucopia_updates()
    
    print(f"Generated {len(messages)} messages:")
    for msg in messages:
        msg_type = msg.get('message_type', 'unknown')
        data = msg.get('data', {})
        print(f"  {msg_type}: {data}")
    
    # Check supplies after bloodbath
    print(f"\n=== Post-Bloodbath Supply Check ===")
    for tribute_id, tribute_obj in engine.game_state.tributes.items():
        print(f"Tribute {tribute_id} ({tribute_obj.name}):")
        print(f"  Status: {tribute_obj.status}")
        print(f"  Health: {tribute_obj.health}")
        print(f"  Inventory: {tribute_obj.inventory}")
        print(f"  Weapons: {tribute_obj.weapons}")
        print(f"  Food supplies: {tribute_obj.food_supplies}")
        print(f"  Water supplies: {tribute_obj.water_supplies}")

if __name__ == "__main__":
    test_cornucopia_supply_distribution()