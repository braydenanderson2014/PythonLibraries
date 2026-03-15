#!/usr/bin/env python3
"""
Final comprehensive test of all fixes
"""

import sys
import os
import time
import json
sys.path.append(os.path.join(os.path.dirname(__file__), 'Engine'))

from aurora_integration import AuroraLobbyIntegration

def test_final_comprehensive():
    """Final test of all fixes: UI timer, name replacement, and narrative flow"""
    print("=== 🎯 FINAL COMPREHENSIVE TEST - ALL FIXES ===\n")
    
    # Create integration with short countdown for faster testing
    config_path = os.path.join("Engine", "config.json")
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Temporary fast countdown
    original_countdown = config["cornucopia_settings"]["countdown_seconds"]
    config["cornucopia_settings"]["countdown_seconds"] = 6
    
    temp_config_path = os.path.join("Engine", "test_config.json")
    with open(temp_config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    try:
        integration = AuroraLobbyIntegration()
        integration.initialize_engine("test_lobby", temp_config_path)
        
        # Create realistic tributes
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
            print("❌ Failed to start game")
            return
        
        print("✅ Game started with 4 tributes")
        
        # Track all success criteria
        ui_timer_working = False
        names_replaced = False
        events_varied = False
        no_placeholder_failures = True
        
        events_seen = set()
        proper_names_found = []
        placeholder_failures = []
        
        # Simulate the complete experience
        for tick in range(20):
            start_time = time.time()
            print(f"\n--- Tick {tick + 1} ---")
            
            messages = integration.process_game_tick()
            
            for msg in messages:
                msg_type = msg.get('message_type', 'unknown')
                data = msg.get('data', {})
                
                # Check UI timer
                if msg_type == 'cornucopia_countdown_start':
                    ui_timer_working = True
                    print(f"   🏺 ✅ UI TIMER: Countdown started ({data.get('countdown_seconds')}s)")
                    
                elif msg_type == 'cornucopia_timer_update':
                    print(f"   ⏰ Timer: {data.get('remaining_seconds')}s (Phase: {data.get('phase')})")
                    
                # Check events and name replacement
                elif msg_type == 'game_event':
                    event_data = data.get('event_data', {})
                    narrative = event_data.get('narrative', '')
                    description = event_data.get('description', '')
                    name = event_data.get('name', 'Unknown Event')
                    
                    events_seen.add(name)
                    
                    # Check for proper names
                    tribute_names = ['Cato Williams', 'Katniss Everdeen', 'Rue Martinez', 'Marvel Sanchez']
                    found_names = [tn for tn in tribute_names if tn in narrative or tn in description]
                    if found_names:
                        names_replaced = True
                        proper_names_found.extend(found_names)
                        print(f"   ✅ NAMES: Found {found_names}")
                    
                    # Check for placeholder failures
                    placeholders = [p for p in ['{tribute', '{name'] if p in narrative or p in description]
                    if placeholders:
                        no_placeholder_failures = False
                        placeholder_failures.append(name)
                        print(f"   ❌ PLACEHOLDERS: {placeholders} in {name}")
                    
                    print(f"   🎭 EVENT: {name}")
                    print(f"   📖 {narrative[:60]}...")
                    
                elif msg_type in ['tribute_decision', 'cornucopia_bloodbath', 'cornucopia_gong']:
                    print(f"   🏺 {msg_type.upper()}")
                    
            # Check if cornucopia completed
            engine = integration.engine
            if hasattr(engine, 'cornucopia_controller') and engine.cornucopia_controller.is_completed():
                print(f"\n🏁 Cornucopia phase completed!")
                break
                
            # Real-time delay
            elapsed = time.time() - start_time
            sleep_time = max(0, 1.0 - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        # Generate some post-cornucopia events to test variety
        engine = integration.engine
        print(f"\n=== Testing Event Variety ===")
        for i in range(3):
            event = engine.generate_event("PvP Events")
            if event:
                event_data = event.get('data', {}).get('event_data', {})
                name = event_data.get('name', 'Unknown')
                events_seen.add(name)
        
        events_varied = len(events_seen) > 2  # Multiple unique events
        
        # Final Results
        print(f"\n=== 🎯 COMPREHENSIVE TEST RESULTS ===")
        print(f"✅ UI Timer Working: {ui_timer_working}")
        print(f"✅ Names Replaced: {names_replaced}")
        print(f"✅ No Placeholder Failures: {no_placeholder_failures}")
        print(f"✅ Events Varied: {events_varied}")
        print(f"📊 Unique Events: {len(events_seen)} ({', '.join(list(events_seen)[:3])}...)")
        print(f"👥 Names Found: {len(set(proper_names_found))} unique")
        if placeholder_failures:
            print(f"❌ Placeholder Failures: {placeholder_failures}")
        
        # Overall success
        all_fixes_working = ui_timer_working and names_replaced and no_placeholder_failures and events_varied
        
        if all_fixes_working:
            print(f"\n🎉 ALL FIXES SUCCESSFUL! 🎉")
            print(f"✅ The Hunger Games cornucopia experience is now working perfectly:")
            print(f"   🏺 Countdown timer displays in UI")
            print(f"   👥 Tribute names replace placeholders")
            print(f"   📚 Narrative flow is varied and interesting")
        else:
            print(f"\n⚠️ Some issues may remain")
            
    finally:
        # Cleanup
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)
        
        config["cornucopia_settings"]["countdown_seconds"] = original_countdown
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

if __name__ == "__main__":
    test_final_comprehensive()