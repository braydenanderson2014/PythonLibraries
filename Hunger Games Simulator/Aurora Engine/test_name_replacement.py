#!/usr/bin/env python3
"""
Test event generation and name replacement after cornucopia
"""

import sys
import os
import time
import json
sys.path.append(os.path.join(os.path.dirname(__file__), 'Engine'))

from aurora_integration import AuroraLobbyIntegration

def test_post_cornucopia_events():
    """Test event generation and name replacement in the game phases after cornucopia"""
    print("=== Testing Post-Cornucopia Event Generation ===\n")
    
    # Create integration
    integration = AuroraLobbyIntegration()
    config_path = os.path.join("Engine", "config.json")
    integration.initialize_engine("test_lobby", config_path)
    
    # Create test tributes
    test_players = [
        {
            "id": "career1",
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
            "id": "district12",
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
            "id": "youngtribute",
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
    
    # Fast-forward through cornucopia (just process until it's done)
    cornucopia_completed = False
    for tick in range(10):
        messages = integration.process_game_tick()
        engine = integration.engine
        if hasattr(engine, 'cornucopia_controller') and engine.cornucopia_controller.is_completed():
            cornucopia_completed = True
            print(f"✓ Cornucopia completed after {tick + 1} ticks")
            break
        time.sleep(0.5)  # Fast processing
    
    if not cornucopia_completed:
        print("⚠️ Cornucopia didn't complete, continuing anyway...")
    
    # Now test regular event generation
    print(f"\n=== Testing Regular Event Generation ===")
    events_seen = set()
    proper_names_found = False
    placeholder_failures = 0
    
    for tick in range(20):  # 20 more ticks to generate events
        print(f"\n--- Post-Cornucopia Tick {tick + 1} ---")
        
        messages = integration.process_game_tick()
        
        for msg in messages:
            msg_type = msg.get('message_type', 'unknown')
            data = msg.get('data', {})
            
            if msg_type == 'game_event':
                event_name = data.get('event', {}).get('name', 'Unknown Event')
                narrative = data.get('event', {}).get('narrative', '')
                description = data.get('event', {}).get('description', '')
                
                events_seen.add(event_name)
                
                # Check for proper names
                tribute_names = ['Cato Williams', 'Katniss Everdeen', 'Rue Martinez']
                found_names = [name for name in tribute_names if name in narrative or name in description]
                if found_names:
                    proper_names_found = True
                    print(f"   ✅ Found tribute names: {found_names}")
                
                # Check for placeholder failures
                if '{tribute' in narrative or '{name' in narrative or '{tribute' in description or '{name' in description:
                    placeholder_failures += 1
                    print(f"   ❌ PLACEHOLDER FAILURE in {event_name}")
                    print(f"      Narrative: {narrative}")
                    print(f"      Description: {description}")
                else:
                    print(f"   ✅ No placeholders found")
                
                print(f"   🎭 EVENT: {event_name}")
                print(f"   📖 Narrative: {narrative[:80]}...")
                
            elif msg_type in ['phase_change', 'stat_update']:
                print(f"   📊 {msg_type.upper()}: {data}")
        
        time.sleep(1)  # Real-time pacing
    
    # Results
    print(f"\n=== EVENT GENERATION TEST RESULTS ===")
    print(f"📊 Unique Events Generated: {len(events_seen)}")
    print(f"✅ Proper Names Found: {proper_names_found}")
    print(f"❌ Placeholder Failures: {placeholder_failures}")
    print(f"📝 Events Generated: {', '.join(list(events_seen))}")
    
    if proper_names_found and placeholder_failures == 0:
        print(f"\n🎉 NAME REPLACEMENT WORKING CORRECTLY!")
    else:
        print(f"\n⚠️ Issues found with name replacement")

if __name__ == "__main__":
    test_post_cornucopia_events()