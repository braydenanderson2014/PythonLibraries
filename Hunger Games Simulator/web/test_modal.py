#!/usr/bin/env python3
"""
Test script to verify modal behavior
"""
import requests
from bs4 import BeautifulSoup

def test_modal_hidden():
    """Test that the edit tribute modal is hidden by default"""
    try:
        response = requests.get('http://127.0.0.1:5000')
        if response.status_code != 200:
            print(f"❌ Server not responding (status: {response.status_code})")
            return False

        soup = BeautifulSoup(response.text, 'html.parser')
        modal = soup.find(id='editTributeModal')

        if not modal:
            print("❌ Modal not found in HTML")
            return False

        # Check if modal has display: none in style attribute
        style = modal.get('style', '')
        print(f"Modal style attribute: '{style}'")
        if 'display: none' not in style:
            print(f"❌ Modal style doesn't contain 'display: none'. Style: {style}")
            return False

        print("✅ Modal is properly hidden in HTML")
        return True

    except Exception as e:
        print(f"❌ Error testing modal: {e}")
        return False

if __name__ == "__main__":
    print("Testing modal visibility...")
    test_modal_hidden()