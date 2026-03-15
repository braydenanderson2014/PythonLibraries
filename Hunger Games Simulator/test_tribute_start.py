#!/usr/bin/env python3
"""
Test script to verify tribute submission and game starting with 2+ players
"""

import asyncio
import socketio

async def test_tribute_and_start_game():
    """Test tribute submission and game starting with minimal players"""
    sio1 = socketio.AsyncClient()
    sio2 = socketio.AsyncClient()

    lobby_id = None
    player1_id = None
    player2_id = None

    # Player 1 event handlers
    @sio1.event
    async def connect():
        print("Player 1 connected")

    @sio1.event
    async def lobby_created(data):
        nonlocal lobby_id
        lobby_id = data['lobby_id']
        print(f"Player 1 created lobby: {lobby_id}")

    @sio1.event
    async def lobby_joined(data):
        nonlocal player1_id
        player1_id = data['player_id']
        print(f"Player 1 joined lobby, ID: {player1_id}")

    @sio1.event
    async def lobby_updated(data):
        print(f"Player 1: Lobby updated - {len(data['lobby']['players'])} players")

    @sio1.event
    async def game_started(data):
        print("Player 1: Game started!")

    @sio1.event
    async def game_start_failed(data):
        print(f"Player 1: Game start failed: {data.get('reason', 'Unknown')}")

    # Player 2 event handlers
    @sio2.event
    async def connect():
        print("Player 2 connected")

    @sio2.event
    async def lobby_joined(data):
        nonlocal player2_id
        player2_id = data['player_id']
        print(f"Player 2 joined lobby, ID: {player2_id}")

    @sio2.event
    async def lobby_updated(data):
        print(f"Player 2: Lobby updated - {len(data['lobby']['players'])} players")

    @sio2.event
    async def game_started(data):
        print("Player 2: Game started!")

    try:
        # Connect both players
        await sio1.connect('http://localhost:8000')
        await sio2.connect('http://localhost:8000')

        await asyncio.sleep(1)

        # Player 1 creates lobby
        print("Player 1 creating lobby...")
        await sio1.emit('create_lobby', {
            'name': 'Tribute Test Lobby',
            'max_players': 4
        })

        await asyncio.sleep(2)

        # Player 2 joins lobby
        if lobby_id:
            print("Player 2 joining lobby...")
            await sio2.emit('join_lobby', {
                'lobby_id': lobby_id,
                'name': 'Player2'
            })

        await asyncio.sleep(2)

        # Both players submit tributes
        print("Player 1 submitting tribute...")
        await sio1.emit('update_tribute', {
            'tribute_data': {
                'name': 'Test Tribute 1',
                'district': 1,
                'gender': 'Male',
                'age': 16,
                'skills': {'strength': 5, 'agility': 5, 'intelligence': 5, 'charisma': 5, 'survival': 5, 'combat': 5},
                'personality': 'Brave',
                'appearance': 'Strong',
                'backstory': 'From District 1'
            }
        })
        await sio1.emit('tribute_done')

        await asyncio.sleep(1)

        print("Player 2 submitting tribute...")
        await sio2.emit('update_tribute', {
            'tribute_data': {
                'name': 'Test Tribute 2',
                'district': 2,
                'gender': 'Female',
                'age': 17,
                'skills': {'strength': 4, 'agility': 6, 'intelligence': 4, 'charisma': 6, 'survival': 4, 'combat': 5},
                'personality': 'Smart',
                'appearance': 'Agile',
                'backstory': 'From District 2'
            }
        })
        await sio2.emit('tribute_done')

        await asyncio.sleep(2)

        # Player 1 (host) tries to start game
        print("Player 1 attempting to start game...")
        await sio1.emit('start_game')

        await asyncio.sleep(3)

        print("Test completed - check if game started successfully")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await sio1.disconnect()
        await sio2.disconnect()

if __name__ == "__main__":
    print("Testing tribute submission and game starting...")
    asyncio.run(test_tribute_and_start_game())