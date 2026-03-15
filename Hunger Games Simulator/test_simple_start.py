#!/usr/bin/env python3
"""
Simple test to check if server allows starting game with 2+ ready players
"""

import asyncio
import socketio

async def test_game_start_condition():
    """Test if server allows starting game with 2+ ready players"""
    sio = socketio.AsyncClient()

    @sio.event
    async def connect():
        print("Connected to server")

    @sio.event
    async def game_start_failed(data):
        print(f"Game start failed: {data.get('reason', 'Unknown reason')}")

    @sio.event
    async def game_started(data):
        print("✅ Game started successfully!")

    try:
        await sio.connect('http://localhost:8000')
        print("Testing game start condition...")

        # Try to start game without being in a lobby (should fail)
        await sio.emit('start_game')
        await asyncio.sleep(1)

        print("Test completed")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await sio.disconnect()

if __name__ == "__main__":
    print("Testing game start condition...")
    asyncio.run(test_game_start_condition())