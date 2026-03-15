#!/usr/bin/env python3
"""
Debug script to test if cornucopia events are being selected
"""

import sys
import os
import json
sys.path.append(os.path.join(os.path.dirname(__file__), 'Engine'))

def test_event_structure():
    """Test if cornucopia events are properly structured in the event messages"""
    print("=== Testing Event Message Structure ===\n")
    
    # Load event messages
    with open(os.path.join("Engine", "event_messages.json"), 'r') as f:
        event_messages = json.load(f)
    
    # Check arena events
    arena_events = event_messages.get("events", {}).get("arena_events", {})
    print(f"Arena events found: {len(arena_events)}")
    for event_id, event_data in arena_events.items():
        if "cornucopia" in event_id.lower() or "cornucopia" in event_data.get("description", "").lower():
            print(f"  ✓ Cornucopia arena event: {event_id}")
    
    # Check combat events  
    combat_events = event_messages.get("events", {}).get("combat_events", {})
    print(f"\nCombat events found: {len(combat_events)}")
    for event_id, event_data in combat_events.items():
        if "cornucopia" in event_id.lower() or "cornucopia" in event_data.get("description", "").lower():
            print(f"  ✓ Cornucopia combat event: {event_id}")
    
    print(f"\nTesting cornucopia detection logic...")
    
    # Test the detection logic we implemented
    for event_category in ["arena_events", "combat_events"]:
        available_events = event_messages.get("events", {}).get(event_category, {})
        
        cornucopia_events = {k: v for k, v in available_events.items() 
                           if "cornucopia" in v.get("id", "").lower() or 
                              "cornucopia" in v.get("name", "").lower() or
                              "cornucopia" in v.get("description", "").lower()}
        
        print(f"  {event_category} - cornucopia events detected: {list(cornucopia_events.keys())}")

if __name__ == "__main__":
    test_event_structure()