#!/usr/bin/env python3
"""
Test script to verify enhanced JSON output from main.py
"""

import subprocess
import json
import time
import os
import sys

def test_enhanced_json_output():
    """Test that main.py produces enhanced JSON output in web mode."""
    print("Testing enhanced JSON output from main.py...")

    # Set web mode environment variable (though it should use settings.json)
    env = os.environ.copy()
    env['HUNGER_GAMES_MODE'] = 'web'

    # Run main.py for a short time to generate output
    try:
        # Run with timeout to avoid infinite loop
        process = subprocess.Popen([
            sys.executable, 'main.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
           text=True, cwd=os.getcwd(), env=env)

        print("Waiting for simulation to initialize and produce output...")
        
        # Check periodically while the process is running
        import time
        for i in range(30):  # Check for 30 seconds
            time.sleep(1)
            
            # Check if web_output.json was created and has content
            web_output_file = os.path.join('data', 'web_output.json')
            if os.path.exists(web_output_file):
                try:
                    with open(web_output_file, 'r') as f:
                        content = f.read().strip()
                        if content:
                            data = json.loads(content)
                            break
                except json.JSONDecodeError:
                    continue  # File might be partially written
        
        # Terminate the process
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()

            print("JSON structure:")
            print(f"  - timestamp: {data.get('timestamp')}")
            print(f"  - status: {data.get('status')}")
            print(f"  - message: {data.get('message', 'None')[:80]}...")

            game_data = data.get('game_data', {})
            if game_data and len(game_data) > 0:
                print("✓ Game data found:")
                print(f"  - day: {game_data.get('day')}")
                print(f"  - phase: {game_data.get('phase')}")
                print(f"  - active_tributes_count: {game_data.get('active_tributes_count')}")
                print(f"  - active_tributes: {len(game_data.get('active_tributes', []))} tributes")

                if game_data.get('active_tributes'):
                    tribute = game_data['active_tributes'][0]
                    print(f"  - Sample tribute data: {tribute.get('name')} (District {tribute.get('district')})")
                    print(f"    Health: {tribute.get('health')}, Weapons: {tribute.get('weapons')}")
                    print(f"    Skills: {tribute.get('skills')}")
                else:
                    print("✗ No active tributes in game_data")
            else:
                print("✗ No game_data found in JSON (empty dict)")
                print(f"Available keys: {list(data.keys())}")
                print(f"game_data value: {data.get('game_data')}")
                print(f"game_data type: {type(data.get('game_data'))}")
        else:
            print(f"✗ web_output.json not found at {web_output_file}")

        # Terminate the process
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()

    except Exception as e:
        print(f"Error running test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_enhanced_json_output()