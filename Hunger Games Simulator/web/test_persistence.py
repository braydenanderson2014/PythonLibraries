#!/usr/bin/env python3
"""
Test script to verify localStorage persistence
"""
import json
import os

def test_persistence():
    """Test that the persistence functions are properly implemented"""
    # Read the HTML file
    html_path = os.path.join(os.path.dirname(__file__), 'templates', 'index.html')
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check for persistence functions
    checks = [
        'saveLobbyState()',
        'loadLobbyState()',
        'clearLobbyState()',
        'restoreLobbyState()',
        'localStorage.setItem',
        'localStorage.getItem',
        'localStorage.removeItem'
    ]

    missing = []
    for check in checks:
        if check not in content:
            missing.append(check)

    if missing:
        print(f"❌ Missing persistence functions: {missing}")
        return False

    print("✅ All persistence functions found in HTML")
    return True

if __name__ == "__main__":
    print("Testing persistence implementation...")
    test_persistence()