#!/usr/bin/env python3
"""
Test the complete fixes: UI timer, tribute name replacement, and narrative flow
"""

import sys
import os
import time
import json
sys.path.append(os.path.join(os.path.dirname(__file__), 'Engine'))

from aurora_integration import AuroraLobbyIntegration

def test_complete_fixes():
    """Test all fixes together: UI timer, name placeholders, and narrative flow"""
    print("=== Testing Complete Cornucopia Fixes ===\n")
    
    # Create a temporary config with fast countdown for testing
    config_path = os.path.join("Engine", "config.json")
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Reduce countdown to 8 seconds for faster testing
    original_countdown = config["cornucopia_settings"]["countdown_seconds"]
    config["cornucopia_settings"]["countdown_seconds"] = 8
    
    temp_config_path = os.path.join("Engine", "test_config.json")
    with open(temp_config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    try:
        # Create integration
        integration = AuroraLobbyIntegration()
        integration.initialize_engine("test_lobby", temp_config_path)
        
        # Create test tributes with realistic names
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
            },
            {
                "id": "district1",
                "name": "Player4", 
                "tribute_ready": True,
                "tribute_data": {
                    "name": "Marvel Sanchez",
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
        if not game_started:
            print("✗ Failed to start game")
            return
        
        print("✓ Game started with 4 tributes")
        print("✓ Testing: UI timer, name placeholders, and narrative flow")
        
        # Track issues
        countdown_displayed = False
        proper_names_found = False
        events_seen = set()
        repeated_events = 0
        
        # Process the full sequence with realistic timing
        for tick in range(25):  # About 25 seconds
            start_time = time.time()
            print(f"\n--- Tick {tick + 1} ---")
            
            messages = integration.process_game_tick()
            
            for msg in messages:
                msg_type = msg.get('message_type', 'unknown')
                data = msg.get('data', {})
                
                if msg_type == 'cornucopia_countdown_start':
                    countdown_displayed = True
                    print(f"   🏺 COUNTDOWN: {data.get('countdown_seconds')}s")
                    print(f"   📝 UI Timer Message: {data.get('message', '')}")
                    
                elif msg_type == 'cornucopia_timer_update':
                    timer = data.get('remaining_seconds', 'N/A')
                    phase = data.get('phase', 'N/A')
                    print(f"   ⏰ Timer: {timer}s (Phase: {phase})")
                    
                elif msg_type == 'game_event':
                    event_name = data.get('event', {}).get('name', 'Unknown Event')
                    narrative = data.get('event', {}).get('narrative', '')
                    
                    # Check for proper names (no placeholders)
                    if 'Cato Williams' in narrative or 'Katniss Everdeen' in narrative or 'Rue Martinez' in narrative or 'Marvel Sanchez' in narrative:
                        proper_names_found = True
                    
                    # Check for placeholder failures
                    has_placeholders = '{tribute' in narrative or '{name' in narrative
                    
                    # Track event repetition
                    if event_name in events_seen:
                        repeated_events += 1
                        print(f"   🔄 REPEATED EVENT: {event_name}")
                    else:
                        events_seen.add(event_name)
                    
                    print(f"   🎭 EVENT: {event_name}")
                    print(f"   📖 Narrative: {narrative[:100]}...")
                    if has_placeholders:
                        print(f"   ❌ PLACEHOLDERS NOT REPLACED!")
                    else:
                        print(f"   ✅ Names properly replaced")
                        
                elif msg_type in ['tribute_decision', 'cornucopia_bloodbath']:
                    print(f"   🏺 {msg_type.upper()}: {data}")
                    
            # Stop if cornucopia is completed
            engine = integration.engine
            if hasattr(engine, 'cornucopia_controller') and engine.cornucopia_controller.is_completed():
                print(f"\n🏁 Cornucopia phase completed!")
                break
                
            # Sleep for realistic timing
            elapsed = time.time() - start_time
            sleep_time = max(0, 1.0 - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        # Summary
        print(f"\n=== FIX VERIFICATION RESULTS ===")
        print(f"✅ UI Timer Displayed: {countdown_displayed}")
        print(f"✅ Proper Names Found: {proper_names_found}")
        print(f"📊 Unique Events Seen: {len(events_seen)}")
        print(f"🔄 Repeated Events: {repeated_events}")
        print(f"📝 Events: {', '.join(list(events_seen)[:5])}...")
        
        if countdown_displayed and proper_names_found and repeated_events < 3:
            print(f"\n🎉 ALL FIXES SUCCESSFUL!")
        else:
            print(f"\n⚠️ Some issues may remain")
    
    finally:
        # Clean up
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)
        
        # Restore original config
        config["cornucopia_settings"]["countdown_seconds"] = original_countdown
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

if __name__ == "__main__":
    test_complete_fixes()