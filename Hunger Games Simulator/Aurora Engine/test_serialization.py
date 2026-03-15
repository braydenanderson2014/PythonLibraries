#!/usr/bin/env python3
"""
Quick test to verify JSON serialization in Socket.IO messages
"""

import asyncio
import socketio
import json

async def test_game_start():
    """Test creating a lobby and starting a game to verify serialization"""
    
    # Create socket client
    sio = socketio.AsyncClient()
    
    try:
        # Connect to server
        await sio.connect('http://localhost:8000')
        print("✓ Connected to server")
        
        # Create a lobby
        await sio.emit('create_lobby', {'lobbyName': 'Test Serialization'})
        
        # Wait for lobby creation
        await asyncio.sleep(1)
        
        # Join as admin (first player gets admin)
        await sio.emit('join_lobby', {
            'lobbyId': 'Test Serialization',
            'playerName': 'TestAdmin'
        })
        
        # Wait for join
        await asyncio.sleep(1)
        
        # Set ready with tribute
        await sio.emit('set_ready', {
            'lobbyId': 'Test Serialization',
            'tribute': {
                'name': 'Test Tribute',
                'district': 1,
                'gender': 'Male',
                'age': 16,
                'skills': {'strength': 5, 'agility': 5, 'hunting': 5, 'stealth': 5, 'survival': 5, 'intelligence': 5, 'endurance': 5, 'social': 5, 'charisma': 5, 'luck': 5},
                'skill_priority': ['strength', 'agility', 'hunting']
            }
        })
        
        # Wait for ready
        await asyncio.sleep(1)
        
        # Add AI tributes to fill lobby
        await sio.emit('admin_generate_ai_tributes', {
            'lobbyId': 'Test Serialization',
            'numTributes': 3
        })
        
        # Wait for AI generation
        await asyncio.sleep(2)
        
        # Start the game
        print("🎮 Starting game...")
        await sio.emit('admin_start_game', {'lobbyId': 'Test Serialization'})
        
        # Wait for game to start and cornucopia messages
        await asyncio.sleep(5)
        
        print("✅ Game started successfully - no JSON serialization errors!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        
    finally:
        await sio.disconnect()

@socketio.AsyncClient().event
async def game_update(data):
    """Handle game updates to check for serialization"""
    print(f"📥 Received game_update: {type(data)}")
    # Try to serialize to JSON to verify it works
    try:
        json.dumps(data)
        print("   ✓ JSON serialization successful")
    except Exception as e:
        print(f"   ❌ JSON serialization failed: {e}")

@socketio.AsyncClient().event  
async def error(data):
    """Handle errors"""
    print(f"❌ Server error: {data}")

if __name__ == "__main__":
    asyncio.run(test_game_start())