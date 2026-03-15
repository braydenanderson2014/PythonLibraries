#!/usr/bin/env python3
"""
Quick test to check cornucopia timer behavior
"""

import sys
import os
import time
sys.path.append(os.path.join(os.path.dirname(__file__), 'Engine'))

from aurora_integration import AuroraLobbyIntegration

def test_cornucopia_timer():
    """Test just the timer mechanics"""
    print("=== Testing Cornucopia Timer ===\n")
    
    # Create integration and start a test game
    integration = AuroraLobbyIntegration()
    config_path = os.path.join("Engine", "config.json")
    integration.initialize_engine("test_lobby", config_path)
    
    # Create minimal test players
    test_players = [
        {
            "id": "p1",
            "name": "TestPlayer1", 
            "tribute_ready": True,
            "tribute_data": {
                "name": "Test Tribute 1",
                "district": 1,
                "gender": "Male",
                "age": 16,
                "skills": {"strength": 5, "agility": 5, "hunting": 5, "stealth": 5, "survival": 5, "intelligence": 5, "endurance": 5, "social": 5, "charisma": 5, "luck": 5},
                "skill_priority": ["strength", "agility", "hunting"]
            }
        },
        {
            "id": "p2",
            "name": "TestPlayer2", 
            "tribute_ready": True,
            "tribute_data": {
                "name": "Test Tribute 2",
                "district": 2,
                "gender": "Female",
                "age": 17,
                "skills": {"strength": 5, "agility": 5, "hunting": 5, "stealth": 5, "survival": 5, "intelligence": 5, "endurance": 5, "social": 5, "charisma": 5, "luck": 5},
                "skill_priority": ["stealth", "survival", "intelligence"]
            }
        }
    ]
    
    # Start the game
    game_started = integration.start_game(test_players)
    if not game_started:
        print("✗ Failed to start game")
        return
    
    print("✓ Game started successfully")
    
    # Process game ticks with real time delays
    for tick in range(10):
        start_time = time.time()
        print(f"\n--- Tick {tick + 1} (Real time) ---")
        
        messages = integration.process_game_tick()
        
        for msg in messages:
            msg_type = msg.get('message_type', 'unknown')
            if msg_type == 'cornucopia_timer_update':
                data = msg.get('data', {})
                remaining = data.get('remaining_seconds', 'N/A')
                phase = data.get('phase', 'N/A')
                print(f"   ⏰ Timer: {remaining}s remaining, Phase: {phase}")
                
        # Sleep for 1 second to simulate real game tick timing
        elapsed = time.time() - start_time
        sleep_time = max(0, 1.0 - elapsed)
        if sleep_time > 0:
            time.sleep(sleep_time)
            
        total_tick_time = time.time() - start_time
        print(f"   Tick took {total_tick_time:.2f}s")

if __name__ == "__main__":
    test_cornucopia_timer()