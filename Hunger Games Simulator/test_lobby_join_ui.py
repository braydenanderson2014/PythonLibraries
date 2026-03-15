#!/usr/bin/env python3
"""
Test script to verify lobby joining works with the new UI
"""

import asyncio
import socketio

async def test_lobby_join_ui():
    """Test that lobby joining works properly"""
    sio = socketio.AsyncClient()

    @sio.event
    async def connect():
        print("Connected to server")

    @sio.event
    async def disconnect():
        print("Disconnected from server")

    @sio.event
    async def lobby_list(data):
        lobbies = data.get('lobbies', [])
        print(f"Received lobby list with {len(lobbies)} lobbies")
        for i, lobby in enumerate(lobbies):
            print(f"  {i+1}. {lobby['name']} (ID: {lobby['id']}) - {lobby['player_count']}/{lobby['max_players']} players")

    @sio.event
    async def lobby_created(data):
        print(f"Lobby created: {data['lobby']['name']} (ID: {data['lobby_id']})")

    @sio.event
    async def lobby_joined(data):
        print(f"✅ Successfully joined lobby: {data['lobby_id']}")
        print(f"Player ID: {data['player_id']}")

    @sio.event
    async def lobby_join_failed(data):
        print(f"❌ Failed to join lobby: {data.get('reason', 'Unknown reason')}")

    try:
        # Connect to server
        await sio.connect('http://localhost:8000')
        print("Connected to lobby server")

        # Wait a moment
        await asyncio.sleep(1)

        # List lobbies first
        print("Listing available lobbies...")
        await sio.emit('list_lobbies')
        await asyncio.sleep(2)

        # Create a test lobby
        print("Creating test lobby...")
        await sio.emit('create_lobby', {
            'name': 'UI Test Lobby',
            'max_players': 4
        })
        await asyncio.sleep(2)

        # List lobbies again to see the new one
        print("Listing lobbies after creation...")
        await sio.emit('list_lobbies')
        await asyncio.sleep(2)

        # Try to join the lobby (simulating clicking the join button)
        print("Attempting to join the UI Test Lobby...")
        await sio.emit('join_lobby', {
            'lobby_id': 'ui_test_lobby_id',  # This would be set by the UI
            'name': 'UITestPlayer'
        })
        await asyncio.sleep(2)

        print("Test completed - check if joining worked")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await sio.disconnect()

if __name__ == "__main__":
    print("Testing lobby join UI functionality...")
    asyncio.run(test_lobby_join_ui())