#!/usr/bin/env python3
"""
Test script to create a lobby, list lobbies, and test lobby selection
"""

import asyncio
import socketio

async def test_lobby_selection():
    """Create a test lobby and test selecting/joining it"""
    sio = socketio.AsyncClient()
    created_lobby_id = None

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
        for lobby in lobbies:
            print(f"  - {lobby['name']} (ID: {lobby['id']}) - {lobby['player_count']}/{lobby['max_players']} players")

    @sio.event
    async def lobby_created(data):
        nonlocal created_lobby_id
        created_lobby_id = data['lobby_id']
        print(f"Lobby created: {data['lobby']['name']} (ID: {created_lobby_id})")

    @sio.event
    async def lobby_joined(data):
        print(f"Successfully joined lobby: {data['lobby_id']}")
        print(f"Player ID: {data['player_id']}")

    @sio.event
    async def lobby_join_failed(data):
        print(f"Failed to join lobby: {data.get('reason', 'Unknown reason')}")

    try:
        # Connect to server
        await sio.connect('http://localhost:8000')
        print("Connected to lobby server")

        # Wait a moment
        await asyncio.sleep(1)

        # Create a test lobby
        print("Creating test lobby...")
        await sio.emit('create_lobby', {
            'name': 'Test Lobby for Selection',
            'max_players': 4
        })

        # Wait for lobby creation
        await asyncio.sleep(2)

        # List lobbies
        print("Listing lobbies...")
        await sio.emit('list_lobbies')

        # Wait for response
        await asyncio.sleep(2)

        # Try to join the lobby if we have the ID
        if created_lobby_id:
            print(f"Attempting to join the created lobby (ID: {created_lobby_id})...")
            await sio.emit('join_lobby', {
                'lobby_id': created_lobby_id,
                'name': 'TestPlayer'
            })

            # Wait for response
            await asyncio.sleep(2)
        else:
            print("No lobby ID available to test joining")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await sio.disconnect()

if __name__ == "__main__":
    print("Testing lobby selection functionality...")
    asyncio.run(test_lobby_selection())