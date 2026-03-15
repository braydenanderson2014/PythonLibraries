#!/usr/bin/env python3

import hashlib
import os

def test_migration_logic():
    """Test the PIN to password migration logic"""
    
    # Test PIN: "1234"
    test_pin = "1234"
    test_pin_hash = hashlib.sha256(test_pin.encode()).hexdigest()
    print(f"Test PIN: {test_pin}")
    print(f"Test PIN hash: {test_pin_hash}")
    
    # Check if pin_hash.txt exists and has correct content
    if os.path.exists("pin_hash.txt"):
        with open("pin_hash.txt", "r") as f:
            saved_hash = f.read().strip()
        print(f"Saved PIN hash: {saved_hash}")
        print(f"Hashes match: {test_pin_hash == saved_hash}")
    else:
        print("pin_hash.txt not found")
    
    # Check if password_hash.txt exists
    if os.path.exists("password_hash.txt"):
        print("password_hash.txt exists (migration completed)")
    else:
        print("password_hash.txt not found (migration not completed)")

if __name__ == "__main__":
    test_migration_logic()
