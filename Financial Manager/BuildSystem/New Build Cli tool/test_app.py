#!/usr/bin/env python3
"""
Simple test script for BuildCLI build system testing.
"""

import sys
import datetime

def main():
    print("BuildCLI Test Application")
    print(f"Python version: {sys.version}")
    print(f"Current time: {datetime.datetime.now()}")
    print("This is a test executable built with BuildCLI!")
    
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()