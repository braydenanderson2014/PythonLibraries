#!/usr/bin/env python3
"""
Test tribute stats API endpoint
"""

import asyncio
import socketio
import aiohttp
import json

async def test_stats_api():
    """Test the /api/tribute endpoint"""
    print("🧪 Testing /api/tribute API endpoint")
    print("=" * 60)
    
    sio = socketio.AsyncClient()
    player_id = None
    
    @sio.event
    async def connect():
        print("✅ Connected to server")
    
    @sio.event
    async def lobby_created(data):
        print(f"📍 Lobby created: {data.get('lobby_id')}")
    
    try:
        # Connect
        await sio.connect("http://localhost:8000")
        await asyncio.sleep(0.5)
        
        # Get player ID from connection
        player_id = sio.sid
        print(f"Player ID (sid): {player_id}")
        
        # Create lobby
        await sio.emit('create_lobby', {'name': 'Test', 'max_players': 24})
        await asyncio.sleep(1)
        
        # Create tribute
        tribute_data = {
            'name': 'Test Tribute',
            'district': 1,
            'gender': 'M',
            'age': 16,
            'skills': {
                'intelligence': 8,
                'hunting': 6,
                'strength': 7,
                'social': 5,
                'stealth': 6,
                'survival': 7,
                'agility': 8,
                'endurance': 7,
                'charisma': 5,
                'luck': 5
            },
            'skill_priority': ['hunting', 'strength', 'agility', 'endurance', 'survival', 'intelligence', 'stealth', 'social', 'charisma', 'luck']
        }
        print(f"Updating tribute for player {player_id}")
        await sio.emit('update_tribute', {'tribute_data': tribute_data})
        await asyncio.sleep(2)  # Wait longer
        print(f"Tribute update sent")
        
        # Now test the API
        async with aiohttp.ClientSession() as session:
            print(f"\n📡 Fetching /api/tribute/{player_id}")
            async with session.get(f"http://localhost:8000/api/tribute/{player_id}") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"✅ Status: {resp.status}")
                    print(f"\n📊 Response data:")
                    print(f"  Name: {data.get('name')}")
                    print(f"  District: {data.get('district')}")
                    print(f"  Gender: {data.get('gender')}")
                    print(f"  Age: {data.get('age')}")
                    print(f"  Final Ratings: {data.get('final_ratings')}")
                    print(f"  Base Ratings: {data.get('base_ratings')}")
                    print(f"  Skill Priority: {data.get('skill_priority')}")
                    
                    if data.get('final_ratings'):
                        print(f"\n✅ Stats API working correctly!")
                    else:
                        print(f"\n❌ No final_ratings in response!")
                else:
                    print(f"❌ Status: {resp.status}")
                    text = await resp.text()
                    print(f"Response: {text}")
        
        await sio.disconnect()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_stats_api())
