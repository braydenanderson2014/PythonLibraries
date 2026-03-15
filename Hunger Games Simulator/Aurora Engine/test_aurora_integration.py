#!/usr/bin/env python3
"""
Quick test of Aurora Engine integration to verify stat decay and tribute data flow
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Engine'))

from aurora_integration import AuroraLobbyIntegration
import json

def test_aurora_engine():
    """Test basic Aurora Engine functionality"""
    print("=" * 60)
    print("Aurora Engine Integration Test")
    print("=" * 60)
    
    # Initialize integration
    integration = AuroraLobbyIntegration()
    config_path = os.path.join(os.path.dirname(__file__), 'Engine', 'config.json')
    
    print(f"\n1. Initializing engine with config: {config_path}")
    integration.initialize_engine("test_lobby_123", config_path=config_path)
    print("   ✅ Engine initialized")
    
    # Create mock players
    print("\n2. Creating test players...")
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
                'skills': {'sword': 8, 'survival': 7},
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
                'skills': {'spear': 7, 'survival': 8},
                'trait_scores': {},
                'conditions': ['healthy']
            }
        }
    ]
    
    print(f"   ✅ Created {len(players)} test players")
    
    # Start game
    print("\n3. Starting game...")
    result = integration.start_game(players)
    if result:
        print("   ✅ Game started successfully")
    else:
        print("   ❌ Failed to start game")
        return False
    
    # Get initial game status
    print("\n4. Checking initial game status...")
    status = integration.get_game_status()
    print(f"   Engine Status: {status.get('engine_status', {}).get('status', 'Unknown')}")
    
    tribute_scoreboards = status.get('tribute_scoreboards', {})
    print(f"   Number of tributes: {len(tribute_scoreboards)}")
    
    if tribute_scoreboards:
        print("\n   Tribute Details:")
        for tribute_id, tribute_data in tribute_scoreboards.items():
            print(f"     - {tribute_data['name']} (District {tribute_data['district']})")
            print(f"       Health: {tribute_data['health']}, Hunger: {tribute_data['hunger']}, Thirst: {tribute_data['thirst']}, Fatigue: {tribute_data['fatigue']}")
    else:
        print("   ⚠️  No tribute scoreboards returned!")
    
    # Check config stat decay rates
    print("\n5. Checking config stat decay rates...")
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    decay_rates = config.get('stat_decay_rates', {})
    if decay_rates:
        print("   ✅ Stat decay rates found in config:")
        print(f"      Hunger: +{decay_rates.get('hunger', 'Not set')}")
        print(f"      Thirst: +{decay_rates.get('thirst', 'Not set')}")
        print(f"      Fatigue: +{decay_rates.get('fatigue', 'Not set')}")
    else:
        print("   ❌ No stat_decay_rates in config!")
    
    # Process some game ticks
    print("\n6. Processing game ticks to test stat decay...")
    initial_hunger = tribute_scoreboards[list(tribute_scoreboards.keys())[0]]['hunger'] if tribute_scoreboards else 0
    
    for tick in range(5):
        messages = integration.process_game_tick()
        print(f"   Tick {tick + 1}: {len(messages)} messages generated")
    
    # Check final status
    print("\n7. Checking final status after ticks...")
    final_status = integration.get_game_status()
    final_scoreboards = final_status.get('tribute_scoreboards', {})
    
    if final_scoreboards:
        first_tribute_id = list(final_scoreboards.keys())[0]
        final_hunger = final_scoreboards[first_tribute_id]['hunger']
        print(f"   Initial hunger: {initial_hunger}")
        print(f"   Final hunger: {final_hunger}")
        if final_hunger > initial_hunger:
            print(f"   ✅ Stat decay working! Hunger increased by {final_hunger - initial_hunger}")
        else:
            print(f"   ⚠️  Hunger did not increase (expected > {initial_hunger}, got {final_hunger})")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)
    
    return True

if __name__ == '__main__':
    try:
        test_aurora_engine()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
