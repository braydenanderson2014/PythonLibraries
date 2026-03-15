#!/usr/bin/env python3
"""
Debug tribute status display and supply pickup issues
"""

import sys
import os
import time
sys.path.append(os.path.join(os.path.dirname(__file__), 'Engine'))

from aurora_integration import AuroraLobbyIntegration

def debug_tribute_status():
    """Debug tribute status and supply tracking"""
    print("=== Debugging Tribute Status & Supply Issues ===\n")
    
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
    
    # Check initial tribute statuses
    print(f"\n=== Initial Tribute Status Check ===")
    engine = integration.engine
    
    for tribute_id, tribute_obj in engine.game_state.tributes.items():
        print(f"Tribute {tribute_id} ({tribute_obj.name}):")
        print(f"  Status: {tribute_obj.status}")
        print(f"  Health: {tribute_obj.health}")
        print(f"  Inventory: {tribute_obj.inventory}")
        print(f"  Weapons: {tribute_obj.weapons}")
        print(f"  Food supplies: {tribute_obj.food_supplies}")
        print(f"  Water supplies: {tribute_obj.water_supplies}")
    
    # Check game state tribute statuses
    print(f"\n=== Game State Tribute Statuses ===")
    for tribute_id, status in engine.game_state.tribute_statuses.items():
        print(f"  {tribute_id}: {status}")
    
    # Check scoreboards data (what gets sent to UI)
    print(f"\n=== Scoreboards Data (UI Data) ===")
    scoreboards = engine.game_state.get_tribute_scoreboards()
    for tribute_id, data in scoreboards.items():
        print(f"Tribute {tribute_id}:")
        print(f"  Name: {data['name']}")
        print(f"  Status: {data['status']}")
        print(f"  Health: {data['health']}")
        print(f"  Inventory: {data['inventory']}")
        print(f"  Weapons: {data['weapons']}")
        print(f"  Food/Water: {data['food_supplies']}/{data['water_supplies']}")
    
    # Test supply pickup by generating a cornucopia event
    print(f"\n=== Testing Supply Pickup ===")
    
    # Force both tributes to participate in cornucopia
    if hasattr(engine, 'cornucopia_controller'):
        controller = engine.cornucopia_controller
        
        # Manually set tributes as cornucopia participants
        controller.cornucopia_participants = ["tribute1", "tribute2"]
        controller.current_phase = controller.current_phase.__class__.BLOODBATH
        
        # Execute bloodbath
        tributes = []
        for tribute_id, tribute_obj in engine.game_state.tributes.items():
            tributes.append({
                "id": tribute_id,
                "name": tribute_obj.name,
                "skills": tribute_obj.skills,
                "district": tribute_obj.district
            })
        
        print(f"Executing bloodbath with {len(tributes)} tributes...")
        bloodbath_messages = controller.execute_bloodbath(tributes)
        
        for msg in bloodbath_messages:
            print(f"Bloodbath message: {msg.get('message_type')} - {msg.get('data', {})}")
    
    # Check post-bloodbath supplies
    print(f"\n=== Post-Bloodbath Supply Check ===")
    for tribute_id, tribute_obj in engine.game_state.tributes.items():
        print(f"Tribute {tribute_id} ({tribute_obj.name}):")
        print(f"  Status: {tribute_obj.status}")
        print(f"  Health: {tribute_obj.health}")
        print(f"  Inventory: {tribute_obj.inventory}")
        print(f"  Weapons: {tribute_obj.weapons}")
        print(f"  Food supplies: {tribute_obj.food_supplies}")
        print(f"  Water supplies: {tribute_obj.water_supplies}")
    
    # Test the integration layer data
    print(f"\n=== Integration Layer Status ===")
    game_status = integration.get_game_status()
    tribute_scoreboards = game_status.get('tribute_scoreboards', {})
    
    print(f"Engine status: {game_status.get('engine_status', {})}")
    print(f"Scoreboards count: {len(tribute_scoreboards)}")
    
    for tribute_id, data in tribute_scoreboards.items():
        print(f"UI Data for {tribute_id}:")
        print(f"  Name: {data.get('name')}")
        print(f"  Status: {data.get('status')}")
        print(f"  Health: {data.get('health')}")
        print(f"  Inventory: {data.get('inventory')}")

if __name__ == "__main__":
    debug_tribute_status()