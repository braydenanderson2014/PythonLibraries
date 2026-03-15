#!/usr/bin/env python3
"""
Example application for testing the build system.
"""

import sys
from pathlib import Path

def main():
    print("=" * 50)
    print("Example Application")
    print("=" * 50)
    print(f"Python Version: {sys.version}")
    print(f"Running from: {Path(__file__).parent}")
    print()
    
    name = input("Enter your name: ")
    print(f"\nHello, {name}! This is a test application.")
    print("This executable was built using Build System v2.")
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
