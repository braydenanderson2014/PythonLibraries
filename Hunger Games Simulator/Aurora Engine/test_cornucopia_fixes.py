#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test cornucopia system fixes:
1. Early step-off deaths (1% chance per game)
2. Supply distribution only after bloodbath completes
"""

import sys
import os
import io

# Set UTF-8 encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import json
import time

# Add Engine directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Engine'))

from aurora_integration import AuroraLobbyIntegration


def test_early_step_off():
    """Test the 1% early step-off death system"""
    print("\n" + "="*80)
    print("TEST 1: Early Step-Off Death System (1% chance per game)")
    print("="*80)
    
    # Run 100 games to see if we get approximately 1 early step-off
    early_step_offs = 0
    games_run = 100
    
    for game_num in range(1, games_run + 1):
        integration = AuroraLobbyIntegration()
        integration.initialize_engine(f"test_game_{game_num}", config_path="Engine/config.json")
        
        # Create test players
        players = []
        for i in range(1, 25):  # 24 tributes
            players.append({
                "id": f"player_{i}",
                "player_name": f"Player {i}",
                "tribute_ready": True,
                "tribute_data": {
                    "name": f"Tribute {i}",
                    "district": ((i - 1) % 12) + 1,
                    "skills": {
                        "strength": 5,
                        "agility": 5,
                        "intelligence": 5,
                        "charisma": 5,
                        "survival": 5,
                        "hunting": 5
                    }
                }
            })
        
        # Start game
        integration.start_game(players)
        
        # Process ticks during countdown
        countdown_complete = False
        ticks = 0
        max_ticks = 70  # 60 second countdown + buffer
        
        while not countdown_complete and ticks < max_ticks:
            messages = integration.process_game_tick()
            
            for msg in messages:
                msg_type = msg.get("message_type")
                
                # Check for early step-off
                if msg_type == "early_step_off":
                    early_step_offs += 1
                    tribute_name = msg.get("data", {}).get("tribute_name", "Unknown")
                    countdown_remaining = msg.get("data", {}).get("countdown_remaining", 0)
                    print(f"  Game {game_num}: EARLY STEP-OFF! {tribute_name} at {countdown_remaining}s remaining")
                    
                # Check for gong (countdown complete)
                elif msg_type == "cornucopia_gong":
                    countdown_complete = True
            
            ticks += 1
            time.sleep(0.1)  # Simulate real-time ticks
        
        if game_num % 10 == 0:
            print(f"  Completed {game_num}/{games_run} games, {early_step_offs} early step-offs so far...")
    
    print(f"\n✓ Test complete: {early_step_offs}/{games_run} games had early step-offs")
    print(f"  Expected: ~1 (1%), Actual: {early_step_offs} ({early_step_offs/games_run*100:.1f}%)")
    
    if 0 <= early_step_offs <= 5:  # Allow some variance
        print("  ✓ PASS: Early step-off rate is within expected range")
    else:
        print("  ✗ FAIL: Early step-off rate is outside expected range")
    
    return early_step_offs


def test_supply_distribution_timing():
    """Test that supplies are only distributed after bloodbath completes"""
    print("\n" + "="*80)
    print("TEST 2: Supply Distribution Timing")
    print("="*80)
    
    integration = AuroraLobbyIntegration()
    integration.initialize_engine("test_supply_timing", config_path="Engine/config.json")
    
    # Create test players
    players = []
    for i in range(1, 13):  # 12 tributes for faster test
        players.append({
            "id": f"player_{i}",
            "player_name": f"Player {i}",
            "tribute_ready": True,
            "tribute_data": {
                "name": f"Tribute {i}",
                "district": i,
                "skills": {
                    "strength": 5,
                    "agility": 5,
                    "intelligence": 5,
                    "charisma": 5,
                    "survival": 5,
                    "hunting": 5
                }
            }
        })
    
    # Start game
    integration.start_game(players)
    
    # Track when events happen
    countdown_started = False
    gong_sounded = False
    bloodbath_occurred = False
    phase_changed = False
    supplies_found_before_phase_change = False
    
    # Process game ticks
    ticks = 0
    max_ticks = 100
    
    while ticks < max_ticks and not phase_changed:
        messages = integration.process_game_tick()
        
        # Check tribute inventories during countdown/bloodbath
        if not phase_changed:
            for tribute_id, tribute in integration.engine.game_state.tributes.items():
                if tribute.status == "alive":
                    if len(tribute.weapons) > 0 or len(tribute.inventory) > 0:
                        if not phase_changed:
                            supplies_found_before_phase_change = True
                            print(f"  ✗ {tribute.name} has supplies BEFORE phase change!")
                            print(f"     Weapons: {tribute.weapons}")
                            print(f"     Inventory: {tribute.inventory}")
        
        for msg in messages:
            msg_type = msg.get("message_type")
            
            if msg_type == "cornucopia_countdown_start":
                countdown_started = True
                print("  ✓ Countdown started")
                
            elif msg_type == "cornucopia_gong":
                gong_sounded = True
                print("  ✓ Gong sounded")
                
            elif msg_type == "cornucopia_bloodbath":
                bloodbath_occurred = True
                print("  ✓ Bloodbath occurred")
                
            elif msg_type == "phase_changed":
                phase_changed = True
                print("  ✓ Phase changed (cornucopia → day)")
                
                # NOW check if tributes have supplies
                tribute_with_supplies = 0
                for tribute_id, tribute in integration.engine.game_state.tributes.items():
                    if tribute.status == "alive":
                        if len(tribute.weapons) > 0 or len(tribute.inventory) > 0:
                            tribute_with_supplies += 1
                
                print(f"  ✓ After phase change: {tribute_with_supplies} tributes have supplies")
        
        ticks += 1
        time.sleep(0.1)
    
    print("\nSummary:")
    print(f"  Countdown started: {countdown_started}")
    print(f"  Gong sounded: {gong_sounded}")
    print(f"  Bloodbath occurred: {bloodbath_occurred}")
    print(f"  Phase changed: {phase_changed}")
    print(f"  Supplies found before phase change: {supplies_found_before_phase_change}")
    
    if not supplies_found_before_phase_change and phase_changed:
        print("\n  ✓ PASS: Supplies were NOT distributed until after phase change")
        return True
    else:
        print("\n  ✗ FAIL: Supplies were distributed too early")
        return False


def test_cornucopia_controller_state():
    """Test that cornucopia controller tracks state correctly"""
    print("\n" + "="*80)
    print("TEST 3: Cornucopia Controller State Tracking")
    print("="*80)
    
    from cornucopia_controller import CornucopiaController
    
    # Load config
    with open("Engine/config.json", 'r') as f:
        config = json.load(f)
    
    controller = CornucopiaController(config)
    
    # Test initial state
    print("  Testing initial state...")
    assert controller.early_step_off_checked == False, "early_step_off_checked should be False initially"
    assert controller.supplies_distributed == False, "supplies_distributed should be False initially"
    assert len(controller.pending_supply_distribution) == 0, "pending_supply_distribution should be empty"
    print("    ✓ Initial state correct")
    
    # Test countdown start
    print("  Testing countdown start...")
    tributes = [
        {"id": "1", "name": "Test Tribute", "district": 1, "skills": {}}
    ]
    controller.start_countdown(tributes)
    assert controller.active_tributes == tributes, "active_tributes should be stored"
    assert controller.early_step_off_checked == False, "early_step_off_checked resets on start"
    print("    ✓ Countdown start works")
    
    # Test supply distribution storage
    print("  Testing supply distribution storage...")
    controller.store_supply_distribution_data(tributes, 5, 10)
    assert controller.pending_supply_distribution["supplies_claimed"] == 5
    assert controller.pending_supply_distribution["participants"] == 10
    assert controller.supplies_distributed == False, "supplies not distributed yet"
    print("    ✓ Supply distribution data stored")
    
    # Test getting pending distribution
    print("  Testing pending distribution retrieval...")
    data = controller.get_pending_supply_distribution()
    assert data is not None, "Should return data"
    assert controller.supplies_distributed == True, "Should mark as distributed"
    print("    ✓ Pending distribution retrieved")
    
    # Test second retrieval returns None
    print("  Testing duplicate retrieval prevention...")
    data2 = controller.get_pending_supply_distribution()
    assert data2 is None, "Should return None after distribution"
    print("    ✓ Duplicate retrieval prevented")
    
    print("\n  ✓ PASS: All state tracking tests passed")
    return True


if __name__ == "__main__":
    print("\n" + "="*80)
    print("CORNUCOPIA SYSTEM FIXES TEST SUITE")
    print("="*80)
    
    try:
        # Test 1: State tracking (fast)
        test_cornucopia_controller_state()
        
        # Test 2: Supply distribution timing
        test_supply_distribution_timing()
        
        # Test 3: Early step-offs (slow - 100 games)
        print("\nRunning early step-off test (this will take a minute)...")
        test_early_step_off()
        
        print("\n" + "="*80)
        print("ALL TESTS COMPLETE")
        print("="*80)
        
    except Exception as e:
        print(f"\n✗ TEST FAILED WITH ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
