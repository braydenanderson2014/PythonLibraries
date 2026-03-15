#!/usr/bin/env python3
"""
Test complete cornucopia flow including supply distribution
"""

import sys
import os
import time
sys.path.append(os.path.join(os.path.dirname(__file__), 'Engine'))

from aurora_integration import AuroraLobbyIntegration

def test_cornucopia_complete_flow():
    """Test complete cornucopia flow with supply distribution"""
    print("=== Testing Complete Cornucopia Flow ===\n")
    
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
    
    # AFTER game starts, force the countdown to be almost finished
    print(f"\n=== Fast-forwarding Cornucopia Countdown ===")
    from datetime import datetime, timedelta
    cornucopia_controller = integration.engine.cornucopia_controller
    cornucopia_controller.start_time = datetime.now() - timedelta(seconds=29.5)  # Almost finished
    
    # Check initial supplies
    print(f"\n=== Initial Supply Check ===")
    engine = integration.engine
    for tribute_id, tribute_obj in engine.game_state.tributes.items():
        print(f"{tribute_obj.name}: Inventory={tribute_obj.inventory}, Weapons={tribute_obj.weapons}, Food={tribute_obj.food_supplies}, Water={tribute_obj.water_supplies}")
    
    # Process several ticks to advance through cornucopia phases
    for i in range(10):
        print(f"\nTick {i+1} - Phase: {cornucopia_controller.current_phase.value}")
        messages = integration.process_game_tick()
        
        for msg in messages:
            msg_type = msg.get('message_type', 'unknown')
            if msg_type in ['cornucopia_countdown', 'cornucopia_gong', 'cornucopia_decision', 'cornucopia_bloodbath', 'tribute_decision']:
                data = msg.get('data', {})
                if 'message' in data:
                    print(f"  {msg_type}: {data['message']}")
                if 'supplies_claimed' in data:
                    print(f"  Supplies claimed: {data['supplies_claimed']}")
                if 'decision' in data:
                    print(f"  {data.get('tribute_name', 'Unknown')} decided: {data['decision']}")
        
        # Check tribute supplies after each tick
        any_supplies = False
        for tribute_id, tribute_obj in engine.game_state.tributes.items():
            if tribute_obj.inventory or tribute_obj.weapons or tribute_obj.food_supplies > 0 or tribute_obj.water_supplies > 0:
                any_supplies = True
                print(f"  {tribute_obj.name}: Inventory={tribute_obj.inventory}, Weapons={tribute_obj.weapons}, Food={tribute_obj.food_supplies}, Water={tribute_obj.water_supplies}")
        
        if not any_supplies:
            print(f"  No supplies found yet...")
        
        # Check if cornucopia is completed
        if cornucopia_controller.is_completed():
            print("  ✓ Cornucopia completed!")
            break
    
    print(f"\n=== Final Supply Check ===")
    for tribute_id, tribute_obj in engine.game_state.tributes.items():
        print(f"Tribute {tribute_id} ({tribute_obj.name}):")
        print(f"  Status: {tribute_obj.status}")
        print(f"  Health: {tribute_obj.health}")
        print(f"  Inventory: {tribute_obj.inventory}")
        print(f"  Weapons: {tribute_obj.weapons}")
        print(f"  Food supplies: {tribute_obj.food_supplies}")
        print(f"  Water supplies: {tribute_obj.water_supplies}")

if __name__ == "__main__":
    test_cornucopia_complete_flow()