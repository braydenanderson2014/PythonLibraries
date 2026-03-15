#!/usr/bin/env python3
"""
Aurora Engine Integration Test and Demo
Run this script to test the complete Aurora Engine + Lobby Server integration
"""

import sys
import os
import asyncio
import json
from datetime import datetime

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(__file__))

async def demo_integration():
    """Demonstrate the Aurora Engine integration with lobby server simulation"""
    try:
        from aurora_integration import AuroraLobbyIntegration

        print("🚀 Starting Aurora Engine Integration Demo")
        print("=" * 50)

        # Initialize integration
        integration = AuroraLobbyIntegration()
        config_path = os.path.join(os.path.dirname(__file__), "Engine", "config.json")
        state_path = os.path.join(os.path.dirname(__file__), "Engine", "game_state.json")

        integration.initialize_engine("demo_lobby", config_path, state_path)
        print("✓ Aurora Engine initialized")

        # Simulate lobby players
        demo_players = [
            {
                'id': 'player_1',
                'tribute_ready': True,
                'tribute_data': {
                    'name': 'Katniss Everdeen',
                    'district': 12,
                    'gender': 'Female',
                    'age': 16,
                    'skills': {'strength': 6, 'agility': 9, 'intelligence': 7, 'survival': 10}
                }
            },
            {
                'id': 'player_2',
                'tribute_ready': True,
                'tribute_data': {
                    'name': 'Peeta Mellark',
                    'district': 12,
                    'gender': 'Male',
                    'age': 16,
                    'skills': {'strength': 8, 'agility': 5, 'intelligence': 6, 'survival': 7}
                }
            },
            {
                'id': 'player_3',
                'tribute_ready': True,
                'tribute_data': {
                    'name': 'Gale Hawthorne',
                    'district': 12,
                    'gender': 'Male',
                    'age': 17,
                    'skills': {'strength': 9, 'agility': 7, 'intelligence': 5, 'survival': 8}
                }
            }
        ]

        print(f"🎮 Starting game with {len(demo_players)} players...")
        success = integration.start_game(demo_players)
        if not success:
            print("❌ Failed to start game")
            return

        print("✓ Game started successfully!")
        print("\n📊 Game Status:")
        status = integration.get_game_status()
        print(json.dumps(status, indent=2))

        # Test game tick processing
        print("\n⏰ Running game simulation...")
        for tick in range(3):
            print(f"\n--- Tick {tick + 1} ---")
            messages = integration.process_game_tick()
            print(f"📨 Generated {len(messages)} messages")

            for msg in messages[:2]:  # Show first 2 messages
                print(f"  • {msg.get('message_type', 'unknown')}: {msg.get('data', {}).get('description', 'N/A')[:100]}...")

            # Get animation events
            events = integration.get_game_events_since()
            if events:
                print(f"🎬 {len(events)} animation events available")

            # Show current engine status
            status = integration.get_game_status()
            engine_status = status.get('engine_status', {}).get('engine_status', {})
            if engine_status:
                print(f"🔄 Engine Status: {engine_status.get('status', 'unknown')} - {engine_status.get('message', '')}")

            await asyncio.sleep(1)  # Simulate real-time pacing

        # Test player input
        print("\n🎯 Testing player input processing...")
        input_data = {
            'id': 'demo_input_1',
            'command_type': 'status_request',
            'player_id': 'player_1'
        }
        response = integration.process_player_input(input_data)
        if response:
            print("✓ Player input processed successfully")
        else:
            print("❌ Player input processing failed")

        # Save final state
        print("\n💾 Saving game state...")
        integration.save_game_state()
        print("✓ Game state saved to game_state.json")

        # Final status
        final_status = integration.get_game_status()
        print("\n🏁 Final Game Status:")
        print(f"  • Active: {final_status.get('engine_status', {}).get('game_active')}")
        print(f"  • Current Phase: {final_status.get('engine_status', {}).get('phase_info', {}).get('current_phase')}")
        print(f"  • Current Day: {final_status.get('engine_status', {}).get('phase_info', {}).get('day')}")

        print("\n🎉 Aurora Engine Integration Demo Complete!")
        print("\nTo run the full lobby server with Aurora Engine integration:")
        print("1. Run: python lobby_server.py")
        print("2. Open http://localhost:8000 in your browser")
        print("3. Create a lobby and start a game")
        print("4. The Aurora Engine will automatically handle game simulation")

    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(demo_integration())