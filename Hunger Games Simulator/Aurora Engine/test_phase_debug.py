#!/usr/bin/env python3
"""
Debug test to see what phase we're in and when phases advance
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Engine'))

from aurora_integration import AuroraLobbyIntegration
import json
import time

def test_phase_advancement():
    """Test phase advancement and stat decay"""
    print("=" * 60)
    print("Aurora Engine Phase & Stat Decay Test")
    print("=" * 60)
    
    # Initialize integration
    integration = AuroraLobbyIntegration()
    config_path = os.path.join(os.path.dirname(__file__), 'Engine', 'config.json')
    
    print(f"\n1. Initializing engine...")
    integration.initialize_engine("test_lobby_phase", config_path=config_path)
    
    # Create mock players
    players = [
        {
            'id': 'player_1',
            'name': 'Player 1',
            'tribute_ready': True,
            'tribute_data': {
                'name': 'Tribute 1',
                'district': 1,
                'gender': 'Male',
                'age': 18,
                'skills': {'sword': 8},
                'trait_scores': {},
                'conditions': ['healthy']
            }
        },
        {
            'id': 'player_2',
            'name': 'Player 2',
            'tribute_ready': True,
            'tribute_data': {
                'name': 'Tribute 2',
                'district': 2,
                'gender': 'Female',
                'age': 17,
                'skills': {'spear': 7},
                'trait_scores': {},
                'conditions': ['healthy']
            }
        }
    ]
    
    print(f"   Starting game...")
    integration.start_game(players)
    
    # Get phase info
    print(f"\n2. Initial phase info:")
    phase_info = integration.engine.phase_controller.get_current_phase_info()
    print(f"   Phase: {phase_info['phase_info']['name']}")
    print(f"   Type: {phase_info['phase_info']['type']}")
    print(f"   Duration: {phase_info['phase_info']['duration_minutes']} minutes")
    
    # Check initial stats
    status = integration.get_game_status()
    tributes = status.get('tribute_scoreboards', {})
    first_id = list(tributes.keys())[0]
    print(f"\n3. Initial stats for {tributes[first_id]['name']}:")
    print(f"   Hunger: {tributes[first_id]['hunger']}")
    print(f"   Thirst: {tributes[first_id]['thirst']}")
    print(f"   Fatigue: {tributes[first_id]['fatigue']}")
    
    # Try to force phase advance
    print(f"\n4. Attempting to force phase advance...")
    # Set phase timer to now so it advances
    integration.engine.game_state.phase_timer = __import__('datetime').datetime.now()
    
    # Process tick - this should trigger phase advance
    messages = integration.process_game_tick()
    print(f"   Messages from tick: {len(messages)}")
    for msg in messages:
        print(f"      - {msg.get('message_type', 'unknown')}")
    
    # Check new phase
    phase_info = integration.engine.phase_controller.get_current_phase_info()
    print(f"\n5. New phase after tick:")
    print(f"   Phase: {phase_info['phase_info']['name']}")
    print(f"   Type: {phase_info['phase_info']['type']}")
    
    # Check updated stats
    status = integration.get_game_status()
    tributes = status.get('tribute_scoreboards', {})
    print(f"\n6. Updated stats for {tributes[first_id]['name']}:")
    print(f"   Hunger: {tributes[first_id]['hunger']}")
    print(f"   Thirst: {tributes[first_id]['thirst']}")
    print(f"   Fatigue: {tributes[first_id]['fatigue']}")
    
    print("\n" + "=" * 60)

if __name__ == '__main__':
    try:
        test_phase_advancement()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
