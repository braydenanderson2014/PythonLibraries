#!/usr/bin/env python3

import os
import subprocess
import sys

def test_application():
    """Test the application and capture output"""
    
    # Remove password file if it exists
    if os.path.exists("password_hash.txt"):
        os.remove("password_hash.txt")
        print("Removed existing password_hash.txt")
    
    # Check PIN file exists
    if os.path.exists("pin_hash.txt"):
        with open("pin_hash.txt", "r") as f:
            pin_hash = f.read().strip()
        print(f"PIN file exists with hash: {pin_hash}")
    else:
        print("ERROR: pin_hash.txt not found!")
        return
    
    # Run the application and capture output
    print("Starting application...")
    try:
        # Run the app in a subprocess with output capture
        result = subprocess.run([sys.executable, "Rent_Tracker.py"], 
                               capture_output=True, text=True, timeout=10)
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        print("Return code:", result.returncode)
    except subprocess.TimeoutExpired:
        print("Application started but didn't exit within 10 seconds (expected for GUI app)")
    except Exception as e:
        print(f"Error running application: {e}")

if __name__ == "__main__":
    test_application()
