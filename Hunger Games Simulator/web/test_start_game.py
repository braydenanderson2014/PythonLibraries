#!/usr/bin/env python3
"""
Test script to debug the start game issue
"""
import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_start_game():
    """Test starting a game to see what error occurs"""
    # First create a lobby
    create_response = requests.post(f"{BASE_URL}/api/lobby/create", json={
        "admin_name": "TestAdmin",
        "max_players": 24
    })

    if create_response.status_code != 200:
        print(f"Failed to create lobby: {create_response.status_code} - {create_response.text}")
        return

    lobby_data = create_response.json()
    lobby_code = lobby_data['lobby_code']
    print(f"Created lobby: {lobby_code}")

    # Try to start the game (should fail due to no tributes)
    start_response = requests.post(f"{BASE_URL}/api/lobby/{lobby_code}/start", json={
        "admin_name": "TestAdmin"
    })

    print(f"Start game response: {start_response.status_code}")
    print(f"Response body: {start_response.text}")

    try:
        data = start_response.json()
        print(f"Parsed JSON: {json.dumps(data, indent=2)}")
    except:
        print("Could not parse response as JSON")

if __name__ == "__main__":
    test_start_game()