#!/usr/bin/env python3
"""
Test Enhanced Aurora Engine Event System
Verifies that rich narratives are being generated and broadcast properly
"""

import sys
import os

# Add Aurora Engine directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from aurora_integration import aurora_integration
import asyncio
import json
from datetime import datetime


def create_test_players():
    """Create test players for the game"""
    districts = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    names = [
        "Katniss Everdeen", "Peeta Mellark",
        "Cato", "Clove",
        "Foxface", "Thresh",
        "Rue", "Marvel",
        "Glimmer", "Finch",
        "Annie Cresta", "Johanna Mason",
        "Beetee", "Wiress",
        "Mags", "Finnick Odair",
        "Cashmere", "Gloss",
        "Enobaria", "Brutus",
        "Chaff", "Seeder",
        "Woof", "Cecelia"
    ]
    
    players = []
    for i in range(min(24, len(names))):
        player = {
            'id': f"test_player_{i}",
            'name': names[i],
            'district': districts[i % 12],
            'tribute_ready': True,
            'tribute_data': {
                'name': names[i],
                'district': districts[i % 12],
                'gender': 'Female' if i % 2 == 0 else 'Male',
                'age': 16 + (i % 6),
                'skills': {
                    'strength': 4 + (i % 7),
                    'agility': 5 + (i % 6),
                    'intelligence': 4 + (i % 7),
                    'charisma': 5 + (i % 6),
                    'survival': 6 + (i % 5),
                    'hunting': 4 + (i % 7),
                    'social': 5 + (i % 6),
                    'stealth': 5 + (i % 6),
                    'endurance': 5 + (i % 6),
                    'luck': 5 + (i % 6)
                },
                'trait_scores': {},
                'conditions': ['healthy']
            }
        }
        players.append(player)
    
    return players


async def test_enhanced_events():
    """Test the enhanced event system"""
    
    print("=" * 80)
    print("TESTING ENHANCED AURORA ENGINE EVENT SYSTEM")
    print("=" * 80)
    
    # Initialize engine
    config_path = os.path.join(os.path.dirname(__file__), "Engine", "config.json")
    aurora_integration.initialize_engine("test_lobby", config_path=config_path)
    print("✓ Engine initialized with event broadcaster\n")
    
    # Create test players
    players = create_test_players()
    print(f"✓ Created {len(players)} test tributes\n")
    
    # Start game
    if not aurora_integration.start_game(players):
        print("✗ Failed to start game")
        return
    
    print("✓ Game started successfully\n")
    print("=" * 80)
    print("MONITORING GAME EVENTS (First 50 ticks)")
    print("=" * 80)
    print()
    
    # Process game ticks and display enhanced events
    death_count = 0
    combat_count = 0
    survival_count = 0
    event_count = 0
    
    for tick in range(50):  # Run for 50 ticks
        messages = aurora_integration.process_game_tick()
        
        if messages:
            print(f"\n{'─' * 80}")
            print(f"TICK {tick + 1} - {len(messages)} messages")
            print(f"{'─' * 80}\n")
            
            for msg in messages:
                event_count += 1
                msg_type = msg.get('message_type', 'unknown')
                category = msg.get('category', '-')
                priority = msg.get('priority', '-')
                
                # Track event types
                if category == 'death':
                    death_count += 1
                elif category == 'combat':
                    combat_count += 1
                elif category in ['survival', 'exploration']:
                    survival_count += 1
                
                data = msg.get('data', {})
                title = data.get('title', msg_type)
                narrative = data.get('narrative', '')
                
                # Display enhanced event
                print(f"📣 {title}")
                print(f"   Type: {msg_type} | Category: {category} | Priority: {priority}")
                
                if narrative:
                    # Truncate long narratives for display
                    if len(narrative) > 300:
                        narrative = narrative[:300] + "..."
                    print(f"\n{narrative}\n")
                
                # Show consequences if present
                consequences = data.get('consequences', [])
                if consequences and len(consequences) > 0:
                    print(f"   Consequences: {', '.join(consequences[:3])}")
                
                # Show style hints
                hints = data.get('style_hints', {})
                if hints:
                    importance = hints.get('importance', '-')
                    duration = hints.get('display_duration', 0)
                    print(f"   Display: {importance} ({duration}ms)")
                
                print()
        
        # Check if game ended
        status = aurora_integration.get_game_status()
        if not status.get('game_active', False):
            print("\n🏆 GAME ENDED!")
            break
        
        # Small delay between ticks
        await asyncio.sleep(0.5)
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total Events: {event_count}")
    print(f"  - Deaths: {death_count}")
    print(f"  - Combat: {combat_count}")
    print(f"  - Survival: {survival_count}")
    print(f"  - Other: {event_count - death_count - combat_count - survival_count}")
    
    # Get final game status
    final_status = aurora_integration.get_game_status()
    scoreboards = final_status.get('tribute_scoreboards', {})
    alive_tributes = [name for name, data in scoreboards.items() if data.get('alive', False)]
    
    print(f"\nTributes Remaining: {len(alive_tributes)}")
    if alive_tributes:
        print(f"Survivors: {', '.join(alive_tributes[:5])}")
        if len(alive_tributes) > 5:
            print(f"          ...and {len(alive_tributes) - 5} more")
    
    print("\n✓ Enhanced event system test complete!")
    print("=" * 80)


def test_event_broadcaster_directly():
    """Test the event broadcaster with sample events"""
    from Engine.event_broadcaster import EventBroadcaster, EventCategory, EventPriority
    
    print("\n" + "=" * 80)
    print("TESTING EVENT BROADCASTER DIRECTLY")
    print("=" * 80)
    
    broadcaster = EventBroadcaster()
    
    # Test 1: Death event
    print("\n1. Testing Death Event Enhancement:")
    death_event = {
        'message_type': 'tribute_death',
        'data': {
            'victim_name': 'Katniss Everdeen',
            'victim_id': 'tribute_1',
            'killer_name': 'Cato',
            'cause': 'combat'
        }
    }
    
    # Mock game state
    class MockGameState:
        def __init__(self):
            self.tribute_statuses = {'tribute_1': 'dead', 'tribute_2': 'alive'}
            self.tributes = {}
    
    enhanced = broadcaster._enhance_death_event(death_event, MockGameState())
    print(f"   Category: {enhanced.get('category')}")
    print(f"   Priority: {enhanced.get('priority')}")
    print(f"   Title: {enhanced['data']['title']}")
    print(f"   Narrative preview: {enhanced['data']['narrative'][:150]}...")
    
    # Test 2: Phase change
    print("\n2. Testing Phase Change Enhancement:")
    phase_event = {
        'message_type': 'phase_change',
        'data': {
            'phase_name': 'Night Falls',
            'day': 1,
            'time_of_day': 'night'
        }
    }
    
    enhanced = broadcaster._enhance_phase_change(phase_event, MockGameState())
    print(f"   Category: {enhanced.get('category')}")
    print(f"   Title: {enhanced['data']['title']}")
    print(f"   Narrative: {enhanced['data']['narrative'][:200]}...")
    
    print("\n✓ Event broadcaster tests complete!")
    print("=" * 80)


if __name__ == "__main__":
    print("\n🎮 Enhanced Aurora Engine Test Suite\n")
    
    # Test broadcaster directly first
    test_event_broadcaster_directly()
    
    # Then test full integration
    asyncio.run(test_enhanced_events())
    
    print("\n🎉 All tests complete!\n")
