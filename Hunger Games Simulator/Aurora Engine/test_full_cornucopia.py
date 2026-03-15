#!/usr/bin/env python3
"""
Test the complete cornucopia system with faster timing for testing
"""

import sys
import os
import time
import json
sys.path.append(os.path.join(os.path.dirname(__file__), 'Engine'))

from aurora_integration import AuroraLobbyIntegration

def test_full_cornucopia():
    """Test the complete cornucopia sequence with fast timing"""
    print("=== Testing Complete Cornucopia System ===\n")
    
    # Create a temporary config with faster countdown for testing
    config_path = os.path.join("Engine", "config.json")
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Temporarily reduce countdown to 10 seconds for faster testing
    original_countdown = config["cornucopia_settings"]["countdown_seconds"]
    config["cornucopia_settings"]["countdown_seconds"] = 10
    
    temp_config_path = os.path.join("Engine", "test_config.json")
    with open(temp_config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    try:
        # Create integration and start test game
        integration = AuroraLobbyIntegration()
        integration.initialize_engine("test_lobby", temp_config_path)
        
        # Create test tributes with different skill profiles
        test_players = [
            {
                "id": "career1",
                "name": "Career1", 
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
                "id": "district12",
                "name": "District12", 
                "tribute_ready": True,
                "tribute_data": {
                    "name": "Katniss",
                    "district": 12,
                    "gender": "Female",
                    "age": 16,
                    "skills": {"hunting": 9, "stealth": 8, "survival": 9, "agility": 7, "intelligence": 6, "strength": 5, "endurance": 7, "social": 4, "charisma": 5, "luck": 6},
                    "skill_priority": ["hunting", "stealth", "survival"]
                }
            },
            {
                "id": "youngtribute",
                "name": "Young", 
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
                "id": "balanced",
                "name": "Balanced", 
                "tribute_ready": True,
                "tribute_data": {
                    "name": "Peeta",
                    "district": 12,
                    "gender": "Male",
                    "age": 16,
                    "skills": {"strength": 7, "endurance": 7, "intelligence": 8, "charisma": 8, "social": 8, "survival": 6, "hunting": 4, "stealth": 5, "agility": 6, "luck": 6},
                    "skill_priority": ["strength", "intelligence", "charisma"]
                }
            }
        ]
        
        # Start the game
        game_started = integration.start_game(test_players)
        if not game_started:
            print("✗ Failed to start game")
            return
        
        print("✓ Game started with 4 tributes")
        print("✓ 10-second countdown for faster testing")
        
        # Track the cornucopia sequence
        countdown_started = False
        gong_sounded = False
        decisions_made = False
        bloodbath_occurred = False
        
        # Process ticks until cornucopia is complete
        for tick in range(30):  # Max 30 ticks (30 seconds)
            start_time = time.time()
            print(f"\n--- Tick {tick + 1} ---")
            
            messages = integration.process_game_tick()
            
            for msg in messages:
                msg_type = msg.get('message_type', 'unknown')
                data = msg.get('data', {})
                
                if msg_type == 'cornucopia_countdown_start':
                    countdown_started = True
                    print(f"   🏺 COUNTDOWN STARTED: {data.get('countdown_seconds')}s")
                    
                elif msg_type == 'cornucopia_timer_update':
                    remaining = data.get('remaining_seconds', 'N/A')
                    phase = data.get('phase', 'N/A')
                    print(f"   ⏰ Timer: {remaining}s, Phase: {phase}")
                    
                elif msg_type == 'cornucopia_gong':
                    gong_sounded = True
                    print(f"   🔔 GONG! {data.get('message', '')}")
                    
                elif msg_type == 'tribute_decision':
                    if not decisions_made:
                        print(f"   🤔 DECISIONS PHASE:")
                        decisions_made = True
                    name = data.get('tribute_name', 'Unknown')
                    decision = data.get('decision', 'unknown')
                    reasoning = data.get('reasoning', '')
                    print(f"      {name}: {decision.upper()}")
                    if reasoning:
                        print(f"         Reasoning: {reasoning}")
                    
                elif msg_type == 'cornucopia_bloodbath':
                    bloodbath_occurred = True
                    print(f"   ⚔️ BLOODBATH RESULTS:")
                    print(f"      Participants: {data.get('participants', 0)}")
                    print(f"      Casualties: {data.get('casualties', 0)}")
                    print(f"      Supplies claimed: {data.get('supplies_claimed', 0)}")
                    
                elif msg_type == 'tributes_fled':
                    fled_count = data.get('fled_count', 0)
                    print(f"   🏃 {fled_count} tributes fled to safety")
                    
                elif msg_type == 'early_step_off':
                    death = data.get('death_occurred', False)
                    tribute = data.get('tribute_name', 'Unknown')
                    print(f"   💥 EARLY STEP-OFF: {tribute} {'DIED' if death else 'survived'}")
                    
            # Check if cornucopia is completed
            engine = integration.engine
            if hasattr(engine, 'cornucopia_controller') and engine.cornucopia_controller.is_completed():
                print(f"\n🏁 CORNUCOPIA COMPLETED after {tick + 1} ticks!")
                break
                
            # Sleep for 1 second to maintain realistic timing
            elapsed = time.time() - start_time
            sleep_time = max(0, 1.0 - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        # Summary
        print(f"\n=== CORNUCOPIA SEQUENCE SUMMARY ===")
        print(f"✓ Countdown started: {countdown_started}")
        print(f"✓ Gong sounded: {gong_sounded}")
        print(f"✓ Decisions made: {decisions_made}")
        print(f"✓ Bloodbath occurred: {bloodbath_occurred}")
        
        if countdown_started and gong_sounded and decisions_made:
            print(f"🎉 FULL CORNUCOPIA SEQUENCE SUCCESSFUL!")
        else:
            print(f"⚠️ Some phases may not have completed")
    
    finally:
        # Clean up temporary config
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)
        
        # Restore original config
        config["cornucopia_settings"]["countdown_seconds"] = original_countdown
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

if __name__ == "__main__":
    test_full_cornucopia()