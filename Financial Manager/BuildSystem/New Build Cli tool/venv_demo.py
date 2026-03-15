#!/usr/bin/env python3
"""
Virtual Environment Management Demo Script for BuildCLI

This script demonstrates all the virtual environment management features.
"""

import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a command and display the output."""
    print(f"\n{'='*60}")
    print(f"DEMO: {description}")
    print(f"Command: {cmd}")
    print(f"{'='*60}")
    
    result = subprocess.run(cmd, shell=True, capture_output=False)
    return result.returncode == 0

def main():
    """Run the virtual environment demo."""
    print("BuildCLI Virtual Environment Management Demo")
    print("=" * 60)
    
    commands = [
        ("python main.py venv-list", "List all virtual environments"),
        ("python main.py venv-create demo-env", "Create a new virtual environment"),
        ("python main.py venv-list", "List environments after creation"),
        ("python main.py venv-activate demo-env", "Activate the virtual environment"),
        ("python main.py \"pip-install requests flask --venv demo-env\"", "Install packages in virtual environment"),
        ("python main.py venv-list", "View environment with installed packages"),
        ("python main.py pip-scan", "Scan current project for dependencies"),
        ("python main.py venv-deactivate", "Deactivate virtual environment"),
        ("python main.py \"venv-create python39-env --version 3.9\"", "Create environment with specific Python version (will show installation needed)"),
        ("python main.py venv-repair demo-env", "Repair a virtual environment"),
        ("python main.py \"venv-replace demo-env 3.11\"", "Replace environment with different Python version"),
    ]
    
    successful = []
    failed = []
    
    for cmd, description in commands:
        success = run_command(cmd, description)
        if success:
            successful.append(description)
        else:
            failed.append(description)
        
        input("\nPress Enter to continue to next command...")
    
    print(f"\n{'='*60}")
    print("DEMO SUMMARY")
    print(f"{'='*60}")
    print(f"Successful operations: {len(successful)}")
    for op in successful:
        print(f"  ✓ {op}")
    
    if failed:
        print(f"\nFailed operations: {len(failed)}")
        for op in failed:
            print(f"  ✗ {op}")
    
    print(f"\n{'='*60}")
    print("CLEANUP")
    print(f"{'='*60}")
    
    cleanup_commands = [
        ("python main.py \"venv-remove demo-env --force\"", "Remove demo environment"),
        ("python main.py \"venv-remove python39-env --force\"", "Remove Python 3.9 environment (if created)"),
        ("python main.py venv-list", "Verify cleanup")
    ]
    
    for cmd, description in cleanup_commands:
        run_command(cmd, description)
    
    print("\nDemo completed!")

if __name__ == "__main__":
    main()