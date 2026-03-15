#!/usr/bin/env python3
"""
Simple Lobby Client Example
Demonstrates how to connect to the lobby server
"""

import socketio
import asyncio
import json

class LobbyClient:
    def __init__(self, server_url="http://localhost:8000"):
        self.sio = socketio.AsyncClient()
        self.server_url = server_url
        self.setup_events()

    def setup_events(self):
        @self.sio.event
        async def connect():
            print("Connected to lobby server")

        @self.sio.event
        async def disconnect():
            print("Disconnected from lobby server")

        @self.sio.event
        async def lobby_joined(data):
            print(f"Joined lobby: {data['lobby_id']}")
            print(f"Your player ID: {data['player_id']}")

        @self.sio.event
        async def lobby_updated(data):
            lobby = data['lobby']
            print(f"\n--- Lobby Update: {lobby['name']} ---")
            print(f"Players ({len(lobby['players'])}):")
            for player in lobby['players'].values():
                status = "Ready" if player['ready'] else "Not Ready"
                host = " (Host)" if player['id'] == lobby['host_id'] else ""
                print(f"  - {player['name']}: {status}{host}")
            print("-" * 30)

        @self.sio.event
        async def game_started(data):
            print("🎮 Game has started!")

        @self.sio.event
        async def game_update(data):
            if data.get('status') == 'running':
                print(data.get('message', ''))
            elif data.get('status') == 'completed':
                print(f"🏆 {data.get('message', 'Game completed!')}")
                await self.sio.disconnect()

        @self.sio.event
        async def lobby_list(data):
            lobbies = data.get('lobbies', [])
            print(f"\n--- Available Lobbies ({len(lobbies)}) ---")
            if lobbies:
                for lobby in lobbies:
                    print(f"  - {lobby['name']} ({lobby['player_count']}/{lobby['max_players']} players) - Host: {lobby['host_name']}")
            else:
                print("  No lobbies available")
            print("-" * 30)

        @self.sio.event
        async def lobby_created(data):
            lobby = data['lobby']
            print(f"\n--- Lobby Created ---")
            print(f"ID: {data['lobby_id']}")
            print(f"Name: {lobby['name']}")
            print(f"Max Players: {lobby['max_players']}")
            print("-" * 30)

    async def connect(self):
        """Connect to the lobby server"""
        try:
            await self.sio.connect(self.server_url)
            print(f"Connected to {self.server_url}")
        except Exception as e:
            print(f"Failed to connect: {e}")

    async def join_lobby(self, player_name):
        """Join a lobby"""
        await self.sio.emit('join_lobby', {'name': player_name})

    async def toggle_ready(self):
        """Toggle ready status"""
        await self.sio.emit('toggle_ready')

    async def start_game(self):
        """Start the game (host only)"""
        await self.sio.emit('start_game')

    async def disconnect(self):
        """Disconnect from server"""
        await self.sio.disconnect()

    async def create_lobby(self, lobby_name, max_players=24):
        """Create a new lobby"""
        await self.sio.emit('create_lobby', {
            'name': lobby_name,
            'max_players': max_players
        })

    async def list_lobbies(self):
        """List available lobbies"""
        await self.sio.emit('list_lobbies')

async def main():
    """Example usage"""
    client = LobbyClient()

    try:
        # Connect to server
        await client.connect()

        # Join lobby
        player_name = input("Enter your name: ")
        await client.join_lobby(player_name)

        # Simple command loop
        while True:
            cmd = input("Command (ready/start/quit): ").lower().strip()

            if cmd == 'ready':
                await client.toggle_ready()
            elif cmd == 'start':
                await client.start_game()
            elif cmd == 'quit':
                break
            else:
                print("Commands: ready, start, quit")

    except KeyboardInterrupt:
        print("\nDisconnecting...")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    print("Hunger Games Lobby Client")
    print("Make sure the lobby server is running first!")
    asyncio.run(main())