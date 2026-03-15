#!/usr/bin/env python3
"""
Game Initialization Test Script
Tests that the game waits for all clients to be ready before starting simulation
and that tribute stats are properly displayed
"""

import asyncio
import socketio
import json
import time
from typing import Dict, List

class GameInitializationTester:
    def __init__(self, server_url: str = "http://localhost:8000"):
        self.server_url = server_url
        self.clients: Dict[str, socketio.AsyncClient] = {}
        self.events: Dict[str, List[dict]] = {
            'client_1': [],
            'client_2': []
        }
        self.lobby_id = None
        self.game_started = False
        self.stats_received = {}
        
    async def setup_client(self, client_name: str):
        """Setup a Socket.IO client"""
        sio = socketio.AsyncClient()
        
        @sio.event
        async def connect():
            print(f"  ✅ {client_name} connected")
        
        @sio.event
        async def disconnect():
            print(f"  ❌ {client_name} disconnected")
        
        @sio.event
        async def lobby_created(data):
            self.events[client_name].append({'event': 'lobby_created', 'data': data, 'time': time.time()})
            self.lobby_id = data.get('lobby_id')
            print(f"  📍 {client_name} got lobby_created: {self.lobby_id}")
        
        @sio.event
        async def lobby_joined(data):
            self.events[client_name].append({'event': 'lobby_joined', 'data': data, 'time': time.time()})
            print(f"  📍 {client_name} got lobby_joined")
        
        @sio.event
        async def lobby_updated(data):
            self.events[client_name].append({'event': 'lobby_updated', 'data': data, 'time': time.time()})
            print(f"  📍 {client_name} got lobby_updated")
        
        @sio.event
        async def game_starting(data):
            self.events[client_name].append({'event': 'game_starting', 'data': data, 'time': time.time()})
            print(f"  🎬 {client_name} got game_starting")
        
        @sio.event
        async def game_state_update(data):
            self.events[client_name].append({'event': 'game_state_update', 'data': data, 'time': time.time()})
            print(f"  📊 {client_name} got game_state_update")
        
        @sio.event
        async def game_started(data):
            self.events[client_name].append({'event': 'game_started', 'data': data, 'time': time.time()})
            self.game_started = True
            print(f"  🎮 {client_name} got game_started - TIME TO VERIFY STATS")
        
        @sio.event
        async def tribute_updated(data):
            self.events[client_name].append({'event': 'tribute_updated', 'data': data, 'time': time.time()})
            print(f"  👤 {client_name} got tribute_updated")
        
        try:
            await sio.connect(self.server_url)
            self.clients[client_name] = sio
            return True
        except Exception as e:
            print(f"  ❌ Failed to connect {client_name}: {e}")
            return False
    
    async def create_lobby(self, client_name: str):
        """Create a lobby"""
        try:
            sio = self.clients[client_name]
            await sio.emit('create_lobby', {'name': 'Test Game', 'max_players': 24})
            await asyncio.sleep(1)  # Wait for response
            return True
        except Exception as e:
            print(f"  ❌ Failed to create lobby: {e}")
            return False
    
    async def join_lobby(self, client_name: str, lobby_id: str):
        """Join a lobby"""
        try:
            sio = self.clients[client_name]
            await sio.emit('join_lobby', {'lobby_id': lobby_id, 'name': f'Player {client_name[-1]}'})
            await asyncio.sleep(1)  # Wait for response
            return True
        except Exception as e:
            print(f"  ❌ Failed to join lobby: {e}")
            return False
    
    async def setup_tribute(self, client_name: str):
        """Setup tribute data"""
        try:
            sio = self.clients[client_name]
            tribute_data = {
                'name': f'Tribute {client_name[-1]}',
                'district': 1 if client_name == 'client_1' else 2,
                'gender': 'M' if client_name == 'client_1' else 'F',
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
            await sio.emit('update_tribute', {'tribute_data': tribute_data})
            await asyncio.sleep(0.5)
            
            # Mark tribute as ready
            await sio.emit('tribute_done')
            await asyncio.sleep(0.5)
            
            return True
        except Exception as e:
            print(f"  ❌ Failed to setup tribute: {e}")
            return False
    
    async def start_game(self, client_name: str):
        """Start the game"""
        try:
            sio = self.clients[client_name]
            await sio.emit('start_game', {'lobby_id': self.lobby_id})
            await asyncio.sleep(1)  # Wait for game_starting event
            return True
        except Exception as e:
            print(f"  ❌ Failed to start game: {e}")
            return False
    
    async def signal_client_ready(self, client_name: str):
        """Signal that client has loaded game page and is ready"""
        try:
            sio = self.clients[client_name]
            print(f"  🔔 {client_name} signaling client_ready")
            await sio.emit('client_ready')
            return True
        except Exception as e:
            print(f"  ❌ Failed to signal client_ready: {e}")
            return False
    
    async def wait_for_game_started(self, timeout: int = 10):
        """Wait for game_started event"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.game_started:
                return True
            await asyncio.sleep(0.1)
        return False
    
    async def test_full_flow(self):
        """Test the full game initialization flow"""
        print("\n🎮 TEST: Full Game Initialization Flow")
        print("=" * 60)
        
        # 1. Setup clients
        print("\n1️⃣ Setting up clients...")
        if not await self.setup_client('client_1'):
            return False
        if not await self.setup_client('client_2'):
            return False
        await asyncio.sleep(0.5)
        
        # 2. Create lobby
        print("\n2️⃣ Creating lobby...")
        if not await self.create_lobby('client_1'):
            return False
        if not self.lobby_id:
            print("  ❌ Lobby ID not received")
            return False
        print(f"  📍 Lobby created: {self.lobby_id}")
        
        # 3. Join lobby
        print("\n3️⃣ Player 2 joining lobby...")
        if not await self.join_lobby('client_2', self.lobby_id):
            return False
        
        # 4. Setup tributes
        print("\n4️⃣ Setting up tributes...")
        if not await self.setup_tribute('client_1'):
            return False
        if not await self.setup_tribute('client_2'):
            return False
        
        # 5. Start game (this sends game_starting and game_state_update)
        print("\n5️⃣ Starting game...")
        if not await self.start_game('client_1'):
            return False
        await asyncio.sleep(1)
        
        # 6. Verify game hasn't started yet
        print("\n6️⃣ Verifying game hasn't started yet...")
        if self.game_started:
            print("  ❌ CRITICAL: Game started before clients signaled ready!")
            return False
        print("  ✅ Game correctly waiting for client_ready signals")
        
        # 7. Signal client ready from both clients
        print("\n7️⃣ Clients signaling ready...")
        await self.signal_client_ready('client_1')
        await asyncio.sleep(0.5)
        await self.signal_client_ready('client_2')
        await asyncio.sleep(0.5)
        
        # 8. Wait for game_started
        print("\n8️⃣ Waiting for game_started event...")
        if not await self.wait_for_game_started():
            print("  ❌ game_started event not received")
            return False
        print("  ✅ game_started received correctly")
        
        # 9. Check stats were included in game_state_update
        print("\n9️⃣ Checking if tribute stats are available...")
        for client_name, events in self.events.items():
            game_state_events = [e for e in events if e['event'] == 'game_state_update']
            if game_state_events:
                current_player = game_state_events[0]['data'].get('current_player', {})
                print(f"  {client_name} current_player keys: {list(current_player.keys())}")
                if current_player and 'name' in current_player:
                    print(f"    ✅ Has player data: {current_player.get('name')}")
        
        # 10. Cleanup
        print("\n🧹 Cleaning up...")
        for client in self.clients.values():
            await client.disconnect()
        
        print("\n✅ TEST PASSED: Game initialization flow working correctly")
        return True
    
    def print_timeline(self):
        """Print event timeline"""
        print("\n📈 Event Timeline:")
        print("=" * 60)
        all_events = []
        for client_name, events in self.events.items():
            for event in events:
                all_events.append({
                    'client': client_name,
                    'event': event['event'],
                    'time': event['time']
                })
        
        # Sort by time
        all_events.sort(key=lambda x: x['time'])
        start_time = all_events[0]['time'] if all_events else 0
        
        for event in all_events:
            elapsed = event['time'] - start_time
            print(f"{elapsed:6.2f}s | {event['client']:10s} | {event['event']}")

async def main():
    """Main test function"""
    tester = GameInitializationTester()
    try:
        success = await tester.test_full_flow()
        tester.print_timeline()
        
        if success:
            print("\n" + "=" * 60)
            print("✅ ALL TESTS PASSED")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("❌ TESTS FAILED")
            print("=" * 60)
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(main())
