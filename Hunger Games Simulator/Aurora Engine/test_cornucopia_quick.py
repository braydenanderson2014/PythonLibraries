#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick test for cornucopia fixes - focuses on key functionality
"""

import sys
import os
import io

# Set UTF-8 encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import json

# Add Engine directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Engine'))

print("\n" + "="*80)
print("QUICK CORNUCOPIA FIXES TEST")
print("="*80)

# Test 1: Cornucopia Controller State
print("\n[TEST 1] Cornucopia Controller State Tracking")
print("-" * 80)

try:
    from cornucopia_controller import CornucopiaController
    
    # Load config
    with open("Engine/config.json", 'r') as f:
        config = json.load(f)
    
    controller = CornucopiaController(config)
    
    # Check game_early_step_off_chance is configured
    chance = config.get("cornucopia_settings", {}).get("game_early_step_off_chance")
    print(f"[OK] game_early_step_off_chance configured: {chance} (1% = 0.01)")
    assert chance == 0.01, "Should be 0.01 (1%)"
    
    # Test early_step_off_checked flag
    assert controller.early_step_off_checked == False, "Should start False"
    print("[OK] early_step_off_checked flag initialized correctly")
    
    # Test supplies_distributed flag
    assert controller.supplies_distributed == False, "Should start False"
    print("[OK] supplies_distributed flag initialized correctly")
    
    # Test supply distribution storage
    tributes = [{"id": "1", "name": "Test", "district": 1, "skills": {}}]
    controller.store_supply_distribution_data(tributes, 5, 10)
    assert len(controller.pending_supply_distribution) > 0
    print("[OK] Supply distribution data storage works")
    
    # Test get_pending_supply_distribution
    data = controller.get_pending_supply_distribution()
    assert data is not None
    assert controller.supplies_distributed == True
    print("[OK] get_pending_supply_distribution works")
    
    # Test second call returns None
    data2 = controller.get_pending_supply_distribution()
    assert data2 is None
    print("[OK] Duplicate supply distribution prevented")
    
    print("\n[TEST 1 RESULT] PASS - State tracking working correctly")
    
except Exception as e:
    print(f"\n[TEST 1 RESULT] FAIL - {e}")
    import traceback
    traceback.print_exc()

# Test 2: Early Step-Off System
print("\n[TEST 2] Early Step-Off System")
print("-" * 80)

try:
    # Check that _check_early_step_offs method exists and tracks correctly
    controller2 = CornucopiaController(config)
    tributes = [
        {"id": f"t{i}", "name": f"Tribute {i}", "district": i, "skills": {}}
        for i in range(1, 25)
    ]
    
    controller2.start_countdown(tributes)
    assert len(controller2.active_tributes) == 24
    print("[OK] Active tributes stored on countdown start")
    
    assert controller2.early_step_off_checked == False
    print("[OK] early_step_off_checked is False before check")
    
    # Manually trigger check
    result = controller2._check_early_step_offs()
    assert controller2.early_step_off_checked == True
    print("[OK] early_step_off_checked set to True after first check")
    
    # Second check should return None immediately
    result2 = controller2._check_early_step_offs()
    assert result2 is None
    print("[OK] Second check returns None (only checks once)")
    
    # If result occurred, check structure
    if result:
        assert result.get("message_type") == "early_step_off"
        assert "tribute_id" in result.get("data", {})
        assert "tribute_name" in result.get("data", {})
        assert result.get("data", {}).get("death_occurred") == True
        print(f"[OK] Early step-off occurred for {result['data']['tribute_name']}")
        print(f"     Structure is correct (always fatal)")
    else:
        print("[OK] No early step-off this run (expected with 1% chance)")
    
    print("\n[TEST 2 RESULT] PASS - Early step-off system working correctly")
    
except Exception as e:
    print(f"\n[TEST 2 RESULT] FAIL - {e}")
    import traceback
    traceback.print_exc()

# Test 3: Supply Distribution Deferred
print("\n[TEST 3] Supply Distribution Deferred Until Phase Complete")
print("-" * 80)

try:
    controller3 = CornucopiaController(config)
    tributes = [{"id": f"t{i}", "name": f"Tribute {i}", "district": i, "skills": {}} for i in range(1, 13)]
    
    # Store supply data
    controller3.store_supply_distribution_data(tributes, 5, 10)
    
    # Check supplies_distributed is still False
    assert controller3.supplies_distributed == False
    print("[OK] supplies_distributed remains False after storing data")
    
    # Check pending_supply_distribution has data
    assert len(controller3.pending_supply_distribution) > 0
    assert controller3.pending_supply_distribution["supplies_claimed"] == 5
    print("[OK] Supply data stored correctly")
    
    # Now get the distribution (simulating phase complete)
    dist_data = controller3.get_pending_supply_distribution()
    assert dist_data is not None
    assert controller3.supplies_distributed == True
    print("[OK] Supplies marked as distributed after retrieval")
    
    # Try to get again - should be None
    dist_data2 = controller3.get_pending_supply_distribution()
    assert dist_data2 is None
    print("[OK] Cannot distribute supplies twice")
    
    print("\n[TEST 3 RESULT] PASS - Supply distribution correctly deferred")
    
except Exception as e:
    print(f"\n[TEST 3 RESULT] FAIL - {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("ALL TESTS COMPLETE")
print("="*80)
print("\nSUMMARY:")
print("  1. Early step-off system: 1% per game, only checks once")
print("  2. Supply distribution: Deferred until after phase completion")
print("  3. Both systems use proper state tracking to prevent duplicates")
print("\nChanges made:")
print("  - config.json: Added game_early_step_off_chance: 0.01")
print("  - cornucopia_controller.py: Added early_step_off_checked flag")
print("  - cornucopia_controller.py: Added supplies_distributed flag")
print("  - cornucopia_controller.py: Added pending_supply_distribution storage")
print("  - Aurora Engine.py: Kill tribute on early step-off event")
print("  - Aurora Engine.py: Defer supply distribution until advance_phase()")
