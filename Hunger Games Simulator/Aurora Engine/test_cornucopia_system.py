#!/usr/bin/env python3
"""
Test script for the cornucopia countdown and decision system
"""

import sys
import os
import json
sys.path.append(os.path.join(os.path.dirname(__file__), 'Engine'))

from aurora_integration import AuroraLobbyIntegration

def test_cornucopia_system():
    """Test the complete cornucopia system"""
    print("=== Testing Cornucopia Countdown & Decision System ===\n")
    
    # Create integration and start a test game
    integration = AuroraLobbyIntegration()
    config_path = os.path.join("Engine", "config.json")
    integration.initialize_engine("test_lobby", config_path)
    
    # Create test players from different districts
    test_players = [
        {
            "id": "p1",
            "name": "Katniss", 
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
            "id": "p2", 
            "name": "Cato",
            "tribute_ready": True,
            "tribute_data": {
                "name": "Cato",
                "district": 2,
                "gender": "Male", 
                "age": 18,
                "skills": {"strength": 10, "endurance": 9, "agility": 8, "hunting": 7, "intelligence": 6, "charisma": 6, "social": 5, "stealth": 4, "survival": 5, "luck": 4},
                "skill_priority": ["strength", "endurance", "agility"]
            }
        },
        {
            "id": "p3",
            "name": "Rue",
            "tribute_ready": True, 
            "tribute_data": {
                "name": "Rue",
                "district": 11,
                "gender": "Female",
                "age": 12,
                "skills": {"agility": 9, "stealth": 8, "survival": 7, "intelligence": 7, "hunting": 6, "social": 6, "endurance": 5, "charisma": 5, "strength": 3, "luck": 6},
                "skill_priority": ["agility", "stealth", "survival"]
            }
        },
        {
            "id": "p4",
            "name": "Marvel",
            "tribute_ready": True,
            "tribute_data": {
                "name": "Marvel", 
                "district": 1,
                "gender": "Male",
                "age": 17,
                "skills": {"strength": 8, "agility": 7, "hunting": 7, "endurance": 7, "charisma": 6, "intelligence": 6, "social": 6, "stealth": 5, "survival": 5, "luck": 5},
                "skill_priority": ["strength", "agility", "hunting"]
            }
        }
    ]
    
    # Start the game
    game_started = integration.start_game(test_players)
    if game_started:
        print("✓ Game started successfully")
    else:
        print("✗ Failed to start game")
        return
    
    # Check initial game state
    game_status = integration.get_game_status()
    print(f"Game active: {game_status.get('game_active')}")
    
    # Check if we have engine access
    if hasattr(integration, 'engine') and integration.engine:
        print("✓ Engine accessible")
        if hasattr(integration.engine, 'cornucopia_controller'):
            print("✓ Cornucopia controller found")
        else:
            print("⚠ No cornucopia controller found")
    else:
        print("✗ Engine not accessible")
    
    print("\n" + "="*50)
    print("SIMULATING CORNUCOPIA SEQUENCE")
    print("="*50)
    
    # Process several game ticks to simulate the cornucopia sequence
    for tick in range(20):
        print(f"\n--- Tick {tick + 1} ---")
        messages = integration.process_game_tick()
        
        if messages:
            for msg in messages:
                msg_type = msg.get('message_type', 'unknown')
                print(f"📩 {msg_type}")
                
                if msg_type == 'cornucopia_countdown_start':
                    data = msg.get('data', {})
                    print(f"   🏺 Countdown started: {data.get('countdown_seconds')}s")
                    print(f"   Message: {data.get('message', '')}")
                    
                elif msg_type == 'cornucopia_timer_update':
                    data = msg.get('data', {})
                    print(f"   ⏰ Timer: {data.get('remaining_seconds')}s remaining")
                    print(f"   Phase: {data.get('phase')}")
                    
                elif msg_type == 'cornucopia_gong':
                    data = msg.get('data', {})
                    print(f"   🔔 GONG! {data.get('message', '')}")
                    
                elif msg_type == 'tribute_decision':
                    data = msg.get('data', {})
                    print(f"   🤔 {data.get('tribute_name')} decides to {data.get('decision')}")
                    print(f"      Reasoning: {data.get('reasoning', '')}")
                    
                elif msg_type == 'cornucopia_bloodbath':
                    data = msg.get('data', {})
                    print(f"   ⚔️ BLOODBATH!")
                    print(f"      Participants: {data.get('participants', 0)}")
                    print(f"      Casualties: {data.get('casualties', 0)}")
                    print(f"      Supplies claimed: {data.get('supplies_claimed', 0)}")
                    
                elif msg_type == 'tributes_fled':
                    data = msg.get('data', {})
                    print(f"   🏃 {data.get('fled_count', 0)} tributes fled to safety")
                    
                elif msg_type == 'early_step_off':
                    data = msg.get('data', {})
                    print(f"   💥 Early step-off! Death: {data.get('death_occurred', False)}")
                    
                else:
                    print(f"   Data: {msg.get('data', {})}")
        else:
            print("   No messages this tick")
            
        # Check if cornucopia is completed
        engine = integration.engine
        if hasattr(engine, 'cornucopia_controller') and engine.cornucopia_controller.is_completed():
            print(f"\n🏁 Cornucopia phase completed after {tick + 1} ticks!")
            break
    
    print(f"\n=== Test Complete ===")
    print("✅ Cornucopia countdown and decision system tested successfully!")

if __name__ == "__main__":
    test_cornucopia_system()