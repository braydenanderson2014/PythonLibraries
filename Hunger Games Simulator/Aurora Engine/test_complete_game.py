#!/usr/bin/env python3
"""
Complete end-to-end test of Aurora Engine with multiple phases
Verifies stat decay, phase progression, and tribute data
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Engine'))

from aurora_integration import AuroraLobbyIntegration
import json

def test_complete_game_flow():
    """Test complete game flow through multiple phases"""
    print("=" * 70)
    print("Aurora Engine - Complete Game Flow Test")
    print("=" * 70)
    
    # Initialize integration
    integration = AuroraLobbyIntegration()
    config_path = os.path.join(os.path.dirname(__file__), 'Engine', 'config.json')
    
    print(f"\n[SETUP] Initializing Aurora Engine...")
    integration.initialize_engine("test_complete_game", config_path=config_path)
    
    # Create 3 test players
    players = [
        {
            'id': 'player_1',
            'name': 'Player 1',
            'tribute_ready': True,
            'tribute_data': {
                'name': 'Katniss',
                'district': 12,
                'gender': 'Female',
                'age': 18,
                'skills': {'bow': 9, 'survival': 8},
                'trait_scores': {},
                'conditions': ['healthy']
            }
        },
        {
            'id': 'player_2',
            'name': 'Player 2',
            'tribute_ready': True,
            'tribute_data': {
                'name': 'Peeta',
                'district': 12,
                'gender': 'Male',
                'age': 18,
                'skills': {'strength': 8, 'camouflage': 6},
                'trait_scores': {},
                'conditions': ['healthy']
            }
        },
        {
            'id': 'player_3',
            'name': 'Player 3',
            'tribute_ready': True,
            'tribute_data': {
                'name': 'Thresh',
                'district': 11,
                'gender': 'Male',
                'age': 18,
                'skills': {'strength': 9, 'weapons': 7},
                'trait_scores': {},
                'conditions': ['healthy']
            }
        }
    ]
    
    print(f"[SETUP] Starting game with {len(players)} players...")
    integration.start_game(players)
    print(f"✅ Game started successfully")
    
    # Track tribute stats across phases
    tribute_history = {}
    
    print(f"\n[GAME] Processing 10 game ticks across multiple phases...")
    print(f"{'Tick':<5} {'Phase':<20} {'Tributes Alive':<15} {'Sample Stats (Hunger/Thirst/Fatigue)':<40}")
    print("-" * 80)
    
    for tick in range(10):
        # Process tick
        messages = integration.process_game_tick()
        
        # Get current status
        status = integration.get_game_status()
        tributes = status.get('tribute_scoreboards', {})
        
        # Get current phase
        phase_info = integration.engine.phase_controller.get_current_phase_info()
        current_phase = phase_info['phase_info']['name'] if phase_info else 'Unknown'
        
        # Count alive tributes
        alive_count = sum(1 for t in tributes.values() if t['status'] == 'alive')
        
        # Get first alive tribute for stats sample
        first_alive = None
        for tid, tribute in tributes.items():
            if tribute['status'] == 'alive':
                first_alive = tribute
                break
        
        stats_str = f"{first_alive['hunger']}/{first_alive['thirst']}/{first_alive['fatigue']}" if first_alive else "N/A"
        
        print(f"{tick+1:<5} {current_phase:<20} {alive_count:<15} {stats_str:<40}")
        
        # Store tribute stats for comparison
        if tick == 0:
            for tid, tribute in tributes.items():
                tribute_history[tid] = {
                    'name': tribute['name'],
                    'initial': {
                        'hunger': tribute['hunger'],
                        'thirst': tribute['thirst'],
                        'fatigue': tribute['fatigue'],
                        'sanity': tribute['sanity']
                    }
                }
        
        # Track messages
        for msg in messages:
            if msg.get('message_type') == 'phase_changed':
                print(f"    ⏭️  Phase changed to: {msg['data'].get('name', 'Unknown')}")
    
    # Final status report
    print("\n" + "=" * 70)
    print("[RESULTS] Final Game Status")
    print("=" * 70)
    
    final_status = integration.get_game_status()
    final_tributes = final_status.get('tribute_scoreboards', {})
    
    print(f"\nTribute Statistics (Initial → Final):")
    print(f"{'Name':<15} {'Health':<12} {'Hunger':<12} {'Thirst':<12} {'Fatigue':<12} {'Status':<10}")
    print("-" * 70)
    
    for tid, tribute in final_tributes.items():
        if tid in tribute_history:
            hist = tribute_history[tid]
            initial_hunger = hist['initial']['hunger']
            final_hunger = tribute['hunger']
            hunger_change = final_hunger - initial_hunger
            
            print(f"{tribute['name']:<15} {tribute['health']:<12} "
                  f"{initial_hunger}→{final_hunger:<9} {final_hunger - hist['initial']['thirst']:<11} "
                  f"{final_hunger - hist['initial']['fatigue']:<11} {tribute['status']:<10}")
    
    # Verify stat decay occurred
    print(f"\n[VERIFICATION] Stat Decay Check:")
    all_increased = True
    for tid, tribute in final_tributes.items():
        if tid in tribute_history and tribute['status'] == 'alive':
            initial = tribute_history[tid]['initial']
            if not (tribute['hunger'] >= initial['hunger'] and 
                    tribute['thirst'] >= initial['thirst'] and 
                    tribute['fatigue'] >= initial['fatigue']):
                all_increased = False
                print(f"  ❌ {tribute['name']}: Stats did NOT increase as expected")
            else:
                print(f"  ✅ {tribute['name']}: Stats increased correctly")
    
    print("\n" + "=" * 70)
    if all_increased:
        print("✅ TEST PASSED - Stat decay working correctly!")
    else:
        print("⚠️  TEST INCOMPLETE - Some stats did not increase")
    print("=" * 70 + "\n")
    
    return all_increased

if __name__ == '__main__':
    try:
        success = test_complete_game_flow()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
