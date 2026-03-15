#!/usr/bin/env python3
"""
Debug the personalize narrative function specifically
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'Engine'))

from aurora_integration import AuroraLobbyIntegration

def test_personalize_narrative_debug():
    """Debug the _personalize_narrative function"""
    print("=== Debugging Personalize Narrative Function ===\n")
    
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
                "name": "Cato Williams",
                "district": 2,
                "gender": "Male",
                "age": 18,
                "skills": {"strength": 10, "endurance": 9, "agility": 8, "hunting": 7, "intelligence": 6, "charisma": 6, "social": 5, "stealth": 4, "survival": 5, "luck": 4},
                "skill_priority": ["strength", "endurance", "agility"]
            }
        },
        {
            "id": "tribute2",
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
            "id": "tribute3",
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
    
    # Get the engine directly
    engine = integration.engine
    
    # Test the personalize narrative function directly
    test_narrative = "The golden horn becomes a battleground as {tribute1}, {tribute2}, and {tribute3} converge on the precious supplies within."
    test_participants = ["tribute1", "tribute2", "tribute3"]
    
    print(f"Original narrative: {test_narrative}")
    print(f"Participants: {test_participants}")
    
    # Test the function directly
    personalized = engine._personalize_narrative(test_narrative, test_participants)
    print(f"Personalized narrative: {personalized}")
    
    # Let's also manually test the tribute lookup
    print(f"\n=== Manual Tribute Lookup ===")
    for i, participant_id in enumerate(test_participants):
        tribute_obj = engine.game_state.tributes.get(participant_id)
        if tribute_obj:
            print(f"Participant {i+1} ({participant_id}): {tribute_obj.name} from District {tribute_obj.district}")
        else:
            print(f"Participant {i+1} ({participant_id}): NOT FOUND")
    
    # Let's also test what happens in the event generation
    print(f"\n=== Testing Event Generation Participants ===")
    # Manually call the function that generates participants
    test_event_data = {
        "participants": "random_3",
        "description": "Test event",
        "narrative": test_narrative
    }
    
    participants = engine._generate_participants_for_event(test_event_data, "Combat Events")
    print(f"Generated participants: {participants}")
    
    if participants:
        personalized_with_generated = engine._personalize_narrative(test_narrative, participants)
        print(f"Personalized with generated participants: {personalized_with_generated}")

if __name__ == "__main__":
    test_personalize_narrative_debug()