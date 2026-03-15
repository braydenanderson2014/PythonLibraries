#!/usr/bin/env python3
"""
Test script for the Hunger Games Simulator web interface.
Tests lobby creation, joining, tribute upload, and basic functionality.
"""

import requests
import json
import time
import sys
import os

# Add the parent directory to the path so we can import from the main project
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = "http://localhost:5000"

def test_lobby_creation():
    """Test creating a new lobby"""
    print("Testing lobby creation...")

    response = requests.post(f"{BASE_URL}/api/lobby/create", json={
        "admin_name": "TestAdmin",
        "max_players": 4
    })

    if response.status_code == 200:
        data = response.json()
        print(f"✓ Lobby created: {data['lobby_code']}")
        return data['lobby_code']
    else:
        print(f"✗ Failed to create lobby: {response.status_code}")
        return None

def test_lobby_joining(lobby_code):
    """Test joining an existing lobby"""
    print(f"Testing lobby joining for code: {lobby_code}...")

    response = requests.post(f"{BASE_URL}/api/lobby/{lobby_code}/join", json={
        "player_name": "TestPlayer"
    })

    if response.status_code == 200:
        data = response.json()
        print(f"✓ Successfully joined lobby: {data['player_id']}")
        return data['player_id']
    else:
        print(f"✗ Failed to join lobby: {response.status_code}")
        return None

def test_lobby_info(lobby_code):
    """Test getting lobby information"""
    print(f"Testing lobby info retrieval for code: {lobby_code}...")

    response = requests.get(f"{BASE_URL}/api/lobby/{lobby_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✓ Lobby info retrieved: {len(data['players'])} players")
        return data
    else:
        print(f"✗ Failed to get lobby info: {response.status_code}")
        return None

def test_tribute_upload(lobby_code, player_id):
    """Test uploading a custom tribute"""
    print(f"Testing tribute upload for lobby: {lobby_code}...")

    tribute_data = {
        "name": "TestTribute",
        "district": 1,
        "skills": {
            "intelligence": 7,
            "hunting": 6,
            "strength": 8,
            "social": 5,
            "stealth": 6,
            "survival": 7,
            "agility": 6,
            "endurance": 8,
            "charisma": 4,
            "luck": 5
        },
        "preferred_weapon": "Sword",
        "health": 100,
        "sanity": 100,
        "speed": 6
    }

    response = requests.post(f"{BASE_URL}/api/lobby/{lobby_code}/upload-tribute", json={
        "player_id": player_id,
        "tribute_data": tribute_data
    })

    if response.status_code == 200:
        print("✓ Tribute uploaded successfully")
        return True
    else:
        print(f"✗ Failed to upload tribute: {response.status_code}")
        return False

def test_game_start(lobby_code):
    """Test starting a game (admin only)"""
    print(f"Testing game start for lobby: {lobby_code}...")

    response = requests.post(f"{BASE_URL}/api/lobby/{lobby_code}/start")

    if response.status_code == 200:
        data = response.json()
        print(f"✓ Game started: {data['game_id']}")
        return data['game_id']
    else:
        print(f"✗ Failed to start game: {response.status_code}")
        return None

def test_game_status(game_id):
    """Test getting game status"""
    print(f"Testing game status for game: {game_id}...")

    response = requests.get(f"{BASE_URL}/api/game/{game_id}/status")

    if response.status_code == 200:
        data = response.json()
        print(f"✓ Game status retrieved: {data['status']}")
        return data
    else:
        print(f"✗ Failed to get game status: {response.status_code}")
        return None

def main():
    """Run all tests"""
    print("Starting Hunger Games Simulator Web Interface Tests")
    print("=" * 50)

    # Test lobby creation
    lobby_code = test_lobby_creation()
    if not lobby_code:
        print("Cannot continue without lobby")
        return

    # Test lobby joining
    player_id = test_lobby_joining(lobby_code)
    if not player_id:
        print("Cannot continue without player")
        return

    # Test lobby info
    lobby_info = test_lobby_info(lobby_code)
    if not lobby_info:
        return

    # Test tribute upload
    if not test_tribute_upload(lobby_code, player_id):
        return

    # Test game start
    game_id = test_game_start(lobby_code)
    if not game_id:
        return

    # Test game status
    game_status = test_game_status(game_id)
    if not game_status:
        return

    print("=" * 50)
    print("All tests completed successfully!")

if __name__ == "__main__":
    main()