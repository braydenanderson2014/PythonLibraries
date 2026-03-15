#!/usr/bin/env python3
"""
Simple test for spectator functionality - checks server endpoints
"""

import requests
import json
import time
import sys

def test_server_endpoints():
    """Test basic server endpoints for spectator functionality"""
    base_url = "http://localhost:8000"

    print("🧪 Testing Spectator Server Endpoints")
    print("=" * 50)

    try:
        # Test 1: Server is running
        print("1. Testing server connectivity...")
        response = requests.get(base_url)
        if response.status_code != 200:
            raise Exception(f"Server returned status {response.status_code}")
        print("   ✅ Server is running")

        # Test 2: Web interface loads
        print("2. Testing web interface...")
        content = response.text
        if "spectator-section" not in content:
            raise Exception("Spectator section not found in HTML")
        if "spectator.js" not in content:
            raise Exception("Spectator JavaScript not found in HTML")
        print("   ✅ Web interface has spectator elements")

        # Test 3: Static files accessible
        print("3. Testing static files...")
        static_files = [
            "/static/js/spectator.js",
            "/static/js/lobby.js",
            "/static/js/app.js"
        ]
        for file_path in static_files:
            response = requests.get(f"{base_url}{file_path}")
            if response.status_code != 200:
                raise Exception(f"Static file {file_path} not accessible")
        print("   ✅ Static files are accessible")

        # Test 4: Debug endpoint (if available)
        print("4. Testing debug endpoint...")
        try:
            response = requests.get(f"{base_url}/debug/players")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Debug endpoint works - {len(data.get('players', {}))} players tracked")
            else:
                print(f"   ⚠️  Debug endpoint returned status {response.status_code}")
        except Exception as e:
            print(f"   ⚠️  Debug endpoint not accessible: {e}")

        print("\n🎉 All basic spectator endpoint tests passed!")
        return True

    except requests.exceptions.RequestException as e:
        print(f"\n❌ Network error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False

def test_spectator_javascript():
    """Test that spectator JavaScript has required functions"""
    base_url = "http://localhost:8000"

    print("\n🧪 Testing Spectator JavaScript Functions")
    print("=" * 50)

    try:
        response = requests.get(f"{base_url}/static/js/spectator.js")
        if response.status_code != 200:
            raise Exception("Cannot load spectator.js")

        content = response.text

        required_functions = [
            "joinAsSpectator",
            "updateSpectatorDisplay",
            "spectator_joined",
            "spectator_update"
        ]

        for func in required_functions:
            if func not in content:
                raise Exception(f"Required function '{func}' not found in spectator.js")

        print("   ✅ All required spectator functions found")

        # Check for event handlers
        if "spectator_joined" not in content or "spectator_update" not in content:
            raise Exception("Spectator event handlers not found")

        print("   ✅ Spectator event handlers found")

        return True

    except Exception as e:
        print(f"❌ JavaScript test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting Basic Spectator Tests")
    print("Make sure the lobby server is running on http://localhost:8000")
    print()

    # Wait a moment for server to be ready
    time.sleep(2)

    success1 = test_server_endpoints()
    success2 = test_spectator_javascript()

    if success1 and success2:
        print("\n✅ All basic spectator tests completed successfully!")
        print("\n📋 Manual Testing Checklist:")
        print("1. Open http://localhost:8000 in browser")
        print("2. Create a lobby as a player")
        print("3. Open another browser tab/window")
        print("4. Go to lobby selection page and try joining as spectator")
        print("5. Verify spectator view loads and shows lobby information")
        print("6. Check browser console for any JavaScript errors")
        return 0
    else:
        print("\n❌ Some basic spectator tests failed!")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)