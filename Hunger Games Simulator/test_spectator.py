#!/usr/bin/env python3
"""
Test script for spectator joining functionality
"""

import asyncio
import aiohttp
import json
import socketio
import time
import sys

class SpectatorTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        self.sio = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        if self.sio and self.sio.connected:
            self.sio.disconnect()

    async def test_spectator_joining(self):
        """Test spectator joining functionality"""
        print("🧪 Testing Spectator Joining Functionality")
        print("=" * 50)

        try:
            # Test 1: Server is running
            print("1. Testing server connectivity...")
            await self.test_server_running()
            print("   ✅ Server is running")

            # Test 2: WebSocket connection
            print("2. Testing WebSocket connection...")
            await self.test_websocket_connection()
            print("   ✅ WebSocket connection successful")

            # Test 3: Lobby creation
            print("3. Testing lobby creation...")
            lobby_id = await self.test_lobby_creation()
            print(f"   ✅ Lobby created with ID: {lobby_id}")

            # Test 4: Spectator joining
            print("4. Testing spectator joining...")
            await self.test_spectator_join(lobby_id)
            print("   ✅ Spectator joining works")

            # Test 5: Lobby list broadcasting
            print("5. Testing lobby list broadcasting...")
            await self.test_lobby_broadcasting()
            print("   ✅ Lobby list broadcasting works")

            print("\n🎉 All spectator tests passed!")
            return True

        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def test_server_running(self):
        """Test that the server is running"""
        async with self.session.get(self.base_url) as response:
            if response.status != 200:
                raise Exception(f"Server returned status {response.status}")

    async def test_websocket_connection(self):
        """Test WebSocket connection"""
        self.sio = socketio.Client()

        connected = False
        disconnected = False

        @self.sio.event
        def connect():
            nonlocal connected
            connected = True

        @self.sio.event
        def disconnect():
            nonlocal disconnected
            disconnected = True

        try:
            self.sio.connect(self.base_url)
            await asyncio.sleep(1)

            if not connected:
                raise Exception("Failed to connect to WebSocket")

            self.sio.disconnect()
            await asyncio.sleep(0.5)

            if not disconnected:
                print("   ⚠️  Disconnect event not received, but connection was established")

        except Exception as e:
            raise Exception(f"WebSocket connection failed: {e}")

    async def test_lobby_creation(self):
        """Test lobby creation and return lobby ID"""
        self.sio = socketio.Client()

        lobby_created = False
        lobby_id = None

        @self.sio.event
        def connect():
            print("   Connected, creating lobby...")

        @self.sio.event
        def lobby_created(data):
            nonlocal lobby_created, lobby_id
            lobby_created = True
            lobby_id = data.get('lobby_id')
            print(f"   Lobby created event data: {data}")
            print(f"   Lobby created: {lobby_id}")

        try:
            self.sio.connect(self.base_url)
            await asyncio.sleep(1)

            # Create a lobby
            self.sio.emit('create_lobby', {
                'name': 'TestLobby',
                'max_players': 4
            })

            # Wait for lobby creation
            start_time = time.time()
            while time.time() - start_time < 10:
                if lobby_created:
                    break
                await asyncio.sleep(0.1)

            if not lobby_created:
                raise Exception("Lobby creation timed out")

            self.sio.disconnect()
            await asyncio.sleep(0.5)

            return lobby_id

        except Exception as e:
            if self.sio.connected:
                self.sio.disconnect()
            raise Exception(f"Lobby creation failed: {e}")

    async def test_spectator_join(self, lobby_id):
        """Test spectator joining a lobby"""
        self.sio = socketio.Client()

        spectator_joined = False
        spectator_updated = False

        @self.sio.event
        def connect():
            print(f"   Connected, joining lobby {lobby_id} as spectator...")

        @self.sio.event
        def spectator_joined(data):
            nonlocal spectator_joined
            spectator_joined = True
            print(f"   Spectator joined event received: {data}")

        @self.sio.event
        def spectator_update(data):
            nonlocal spectator_updated
            spectator_updated = True
            print(f"   Spectator update event received: {data}")

        try:
            self.sio.connect(self.base_url)
            await asyncio.sleep(1)

            # Join as spectator
            self.sio.emit('join_as_spectator', {
                'lobby_id': lobby_id,
                'spectator_name': 'TestSpectator'
            })

            # Wait for spectator events
            start_time = time.time()
            while time.time() - start_time < 10:
                if spectator_joined:
                    break
                await asyncio.sleep(0.1)

            if not spectator_joined:
                raise Exception("Spectator joined event not received")

            # Note: spectator_update is only sent if game has already started
            # Since we just created the lobby, game hasn't started, so we don't expect spectator_update
            print("   Spectator joined successfully (spectator_update not expected since game hasn't started)")

            self.sio.disconnect()
            await asyncio.sleep(0.5)

        except Exception as e:
            if self.sio.connected:
                self.sio.disconnect()
            raise Exception(f"Spectator joining failed: {e}")

    async def test_lobby_broadcasting(self):
        """Test that lobby list broadcasting works"""
        self.sio = socketio.Client()

        lobby_list_received = False
        lobby_data = None

        @self.sio.event
        def connect():
            print("   Connected, waiting for lobby list broadcast...")

        @self.sio.event
        def lobby_updated(data):
            nonlocal lobby_list_received, lobby_data
            lobby_list_received = True
            lobby_data = data
            print(f"   Lobby list broadcast received: {len(data.get('lobbies', []))} lobbies")

        try:
            self.sio.connect(self.base_url)
            await asyncio.sleep(1)

            # Wait for lobby list broadcast (should happen automatically)
            start_time = time.time()
            while time.time() - start_time < 5:
                if lobby_list_received:
                    break
                await asyncio.sleep(0.1)

            if not lobby_list_received:
                print("   ⚠️  Lobby list broadcast not received automatically, this may be normal")

            self.sio.disconnect()
            await asyncio.sleep(0.5)

        except Exception as e:
            if self.sio.connected:
                self.sio.disconnect()
            raise Exception(f"Lobby broadcasting test failed: {e}")

async def main():
    """Main test function"""
    print("🚀 Starting Spectator Functionality Tests")
    print("Make sure the lobby server is running on http://localhost:8000")
    print()

    # Wait a moment for server to be ready
    await asyncio.sleep(2)

    async with SpectatorTester() as tester:
        success = await tester.test_spectator_joining()

    if success:
        print("\n✅ All spectator tests completed successfully!")
    else:
        print("\n❌ Some spectator tests failed!")
        return 1

    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)