#!/usr/bin/env python3
"""
Test script for Aurora Engine integration
"""

import sys
import os
import json
from datetime import datetime

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(__file__))

def test_aurora_integration():
    """Test the Aurora Engine integration"""
    try:
        from aurora_integration import AuroraLobbyIntegration

        print("Testing Aurora Engine integration...")

        # Create integration instance
        integration = AuroraLobbyIntegration()

        # Initialize engine
        config_path = os.path.join(os.path.dirname(__file__), "Engine", "config.json")
        state_path = os.path.join(os.path.dirname(__file__), "Engine", "game_state.json")

        print(f"Config path: {config_path}")
        print(f"State path: {state_path}")

        integration.initialize_engine("test_lobby", config_path, state_path)
        print("✓ Engine initialized successfully")

        # Test game status
        status = integration.get_game_status()
        print(f"✓ Game status retrieved: {status.get('engine_status', {}).get('game_active', 'unknown')}")

        # Test with sample players
        sample_players = [
            {
                'id': 'player1',
                'tribute_ready': True,
                'tribute_data': {
                    'name': 'Test Tribute 1',
                    'district': 1,
                    'gender': 'Male',
                    'age': 16,
                    'skills': {'strength': 7, 'agility': 6, 'intelligence': 5}
                }
            },
            {
                'id': 'player2',
                'tribute_ready': True,
                'tribute_data': {
                    'name': 'Test Tribute 2',
                    'district': 2,
                    'gender': 'Female',
                    'age': 17,
                    'skills': {'strength': 5, 'agility': 8, 'intelligence': 6}
                }
            }
        ]

        print("Testing game start with sample players...")
        success = integration.start_game(sample_players)
        if success:
            print("✓ Game started successfully")
        else:
            print("✗ Failed to start game")
            return False

        # Test game tick processing
        print("Testing game tick processing...")
        messages = integration.process_game_tick()
        print(f"✓ Processed {len(messages)} messages in first tick")

        # Test player input processing
        print("Testing player input processing...")
        input_data = {
            'id': 'test_input_1',
            'command_type': 'status_request',
            'player_id': 'player1'
        }
        response = integration.process_player_input(input_data)
        if response:
            print("✓ Player input processed successfully")
        else:
            print("✗ Failed to process player input")

        # Test game events
        print("Testing game events retrieval...")
        events = integration.get_game_events_since()
        print(f"✓ Retrieved {len(events)} animation events")

        # Save game state
        print("Testing game state saving...")
        integration.save_game_state()
        print("✓ Game state saved")

        print("\n🎉 All Aurora Engine integration tests passed!")
        return True

    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_aurora_integration()
    sys.exit(0 if success else 1)