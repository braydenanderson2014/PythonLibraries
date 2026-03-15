#!/usr/bin/env python3
"""
Test script for tribute generation and game starting
"""
import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_tribute_generation():
    """Test that tribute generation works when starting a game with few tributes"""
    try:
        # Create a lobby
        response = requests.post(f"{BASE_URL}/api/lobby/create", json={
            "admin_name": "TestAdmin"
        })
        if response.status_code != 200:
            print(f"❌ Failed to create lobby: {response.status_code}")
            return False

        lobby_data = response.json()
        lobby_code = lobby_data['lobby']['code']
        print(f"✅ Created lobby: {lobby_code}")

        # Join with one more player
        response = requests.post(f"{BASE_URL}/api/lobby/{lobby_code}/join", json={
            "player_name": "TestPlayer"
        })
        if response.status_code != 200:
            print(f"❌ Failed to join lobby: {response.status_code}")
            return False

        print("✅ Joined lobby with 2 players")

        # Try to start game (should fail and ask for generation)
        response = requests.post(f"{BASE_URL}/api/lobby/{lobby_code}/start", json={
            "admin_name": "TestAdmin"
        })

        if response.status_code == 400:
            data = response.json()
            if 'need_generation' in data and data['need_generation']:
                print(f"✅ Correctly detected need for {data['missing_count']} more tributes")
                return True
            else:
                print(f"❌ Unexpected error: {data}")
                return False
        else:
            print(f"❌ Expected 400 status, got {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Error testing tribute generation: {e}")
        return False

if __name__ == "__main__":
    print("Testing tribute generation...")
    test_tribute_generation()