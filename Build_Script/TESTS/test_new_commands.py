#!/usr/bin/env python3
"""
Test script for the new CLI commands
"""

import subprocess
import sys

def test_command(cmd_args):
    """Test a CLI command and return result"""
    try:
        result = subprocess.run([sys.executable, 'build_cli.py'] + cmd_args, 
                              capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def main():
    """Test the new CLI commands"""
    print("🧪 Testing New CLI Commands")
    print("=" * 40)
    
    test_commands = [
        (['--help'], "Help command"),
        (['--preview-name'], "Preview name command"),
        (['--virtual', 'test_env'], "Virtual environment command"),
        (['--downgrade', '3.8'], "Downgrade command"),
        (['--target', 'main.py'], "Target command"),
        (['--show-console', 'true'], "Show console command"),
        (['--auto'], "Auto mode command"),
        (['--backup'], "Backup command"),
        (['--scan-project'], "Scan project command"),
        (['--export-config'], "Export config command"),
    ]
    
    passed = 0
    total = len(test_commands)
    
    for args, description in test_commands:
        print(f"\n🔧 Testing: {description}")
        print(f"   Command: build_cli {' '.join(args)}")
        
        success, stdout, stderr = test_command(args)
        
        if success:
            print(f"   ✅ PASSED")
            passed += 1
        else:
            print(f"   ❌ FAILED")
            if stderr:
                print(f"   Error: {stderr}")
    
    print(f"\n📊 Test Results: {passed}/{total} commands passed")
    
    if passed == total:
        print("🎉 All commands are working correctly!")
    else:
        print("⚠️  Some commands need attention")

if __name__ == "__main__":
    main()
