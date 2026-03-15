#!/usr/bin/env python3
"""
Test script for cornucopia phase event generation
"""

import sys
import os
import json
sys.path.append(os.path.join(os.path.dirname(__file__), 'Engine'))

from aurora_integration import AuroraLobbyIntegration

def test_cornucopia_events():
    """Test that cornucopia phase generates appropriate events"""
    print("=== Testing Cornucopia Event Generation ===\n")
    
    # Create integration and start a test game
    integration = AuroraLobbyIntegration()
    config_path = os.path.join("Engine", "config.json")
    integration.initialize_engine("test_lobby", config_path)
    
    # Create test players
    test_players = [
        {
            "id": "p1",
            "name": "Test Player 1", 
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
            "name": "Test Player 2",
            "tribute_ready": True,
            "tribute_data": {
                "name": "Peeta Mellark",
                "district": 12,
                "gender": "Male", 
                "age": 16,
                "skills": {"strength": 8, "charisma": 9, "social": 8, "intelligence": 7, "endurance": 6, "agility": 5, "hunting": 4, "stealth": 4, "survival": 6, "luck": 5},
                "skill_priority": ["strength", "charisma", "social"]
            }
        },
        {
            "id": "p3",
            "name": "Test Player 3",
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
            "id": "p4",
            "name": "Test Player 4",
            "tribute_ready": True,
            "tribute_data": {
                "name": "Clove", 
                "district": 2,
                "gender": "Female",
                "age": 15,
                "skills": {"agility": 9, "strength": 8, "hunting": 7, "stealth": 7, "intelligence": 6, "endurance": 6, "charisma": 5, "social": 4, "survival": 5, "luck": 5},
                "skill_priority": ["agility", "strength", "hunting"]
            }
        }
    ]
    
    # Start the game
    integration.start_game(test_players)
    print("✓ Game started successfully\n")
    
    # Get current phase info
    engine = integration.engine
    phase_info = engine.phase_controller.get_current_phase_info()
    
    print(f"Current phase: {phase_info['phase_info']['name']}")
    print(f"Phase type: {phase_info['phase_info']['type']}")
    print(f"Allowed events: {phase_info['phase_info']['allowed_events']}")
    print(f"Is cornucopia completed: {phase_info['game_state']['cornucopia_completed']}\n")
    
    # Generate several events to test cornucopia preference
    print("Generating 10 events to test cornucopia preference...")
    cornucopia_events = []
    other_events = []
    
    for i in range(10):
        # Try to force event generation
        event_result = engine.generate_event()
        if event_result:
            event_data = event_result.get('data', {}).get('event_data', {})
            description = event_data.get('description', '')
            narrative = event_data.get('narrative', '')
            
            print(f"  Event {i+1}: {description}")
            print(f"    Narrative: {narrative[:100]}...")
            
            # Check if it's cornucopia-related
            if 'cornucopia' in description.lower() or 'cornucopia' in narrative.lower():
                cornucopia_events.append(description)
                print("    ✓ CORNUCOPIA EVENT")
            else:
                other_events.append(description)
                print("    - Regular event")
        else:
            print(f"  Event {i+1}: No event generated")
        print()
    
    print(f"\n=== RESULTS ===")
    print(f"Cornucopia-specific events: {len(cornucopia_events)}")
    print(f"Other events: {len(other_events)}")
    
    if cornucopia_events:
        print(f"\nCornucopia events generated:")
        for event in cornucopia_events:
            print(f"  - {event}")
    
    if len(cornucopia_events) > 0:
        print("\n✓ Cornucopia events are being prioritized!")
    else:
        print("\n⚠ No cornucopia events generated - may need adjustment")
    
    print(f"\nPhase type verification: {phase_info['phase_info']['type'] == 'cornucopia'}")

if __name__ == "__main__":
    test_cornucopia_events()