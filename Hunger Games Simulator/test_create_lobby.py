#!/usr/bin/env python3
"""
Test script to create a lobby and verify the lobby list functionality
"""

import asyncio
import socketio

async def test_lobby_creation():
    """Create a test lobby and verify it appears in the list"""
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
        for lobby in lobbies:
            print(f"  - {lobby['name']} (ID: {lobby['id']})")

    @sio.event
    async def lobby_created(data):
        print(f"Lobby created: {data['lobby']['name']} (ID: {data['lobby_id']})")

    try:
        # Connect to server
        await sio.connect('http://localhost:8000')
        print("Connected to lobby server")

        # Wait a moment
        await asyncio.sleep(1)

        # Create a test lobby
        print("Creating test lobby...")
        await sio.emit('create_lobby', {
            'name': 'Test Lobby',
            'max_players': 4
        })

        # Wait for lobby creation
        await asyncio.sleep(2)

        # List lobbies
        print("Listing lobbies...")
        await sio.emit('list_lobbies')

        # Wait for response
        await asyncio.sleep(2)

        # List lobbies again to test duplicate prevention
        print("Listing lobbies again...")
        await sio.emit('list_lobbies')

        # Wait for response
        await asyncio.sleep(2)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await sio.disconnect()

if __name__ == "__main__":
    print("Testing lobby creation and listing...")
    asyncio.run(test_lobby_creation())