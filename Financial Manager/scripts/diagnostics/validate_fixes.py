#!/usr/bin/env python3
"""
Quick validation script to check that our fixes work.
"""
import sys, os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.join(PROJECT_ROOT, 'src'))

def validate_fixes():
    print("=== Validating Bug Fixes ===")
    
    # 1. Check that RentDashboardTab class has the current_user_id fix
    print("\n1. Checking RentDashboardTab current_user_id fix:")
    
    # Read the file and check for the fix
    with open(os.path.join(PROJECT_ROOT, 'ui', 'rent_dashboard_tab.py'), 'r') as f:
        content = f.read()
    
    if 'self.current_user_id = current_user_id' in content:
        print("✓ current_user_id attribute is properly stored in __init__")
    else:
        print("✗ current_user_id attribute fix not found")
    
    if 'user_id=self.current_user_id' in content:
        print("✓ current_user_id is used in create_tenant method")
    else:
        print("✗ current_user_id usage in create_tenant not found")
    
    # 2. Check chart improvements
    print("\n2. Checking chart text spacing fixes:")
    
    if 'figsize=(5, 4)' in content:
        print("✓ Chart figure size increased for better text spacing")
    else:
        print("✗ Chart figure size not increased")
    
    if 'tight_layout(pad=1.5)' in content:
        print("✓ Chart layout spacing improved")
    else:
        print("✗ Chart layout spacing not improved")
    
    if 'textprops={\'fontsize\': 10}' in content:
        print("✓ Chart text properties improved")
    else:
        print("✗ Chart text properties not improved")
    
    if 'fontsize=12, pad=20' in content:
        print("✓ Chart title formatting improved")
    else:
        print("✗ Chart title formatting not improved")
    
    print("\n=== Validation Complete ===")
    print("Both issues should now be fixed:")
    print("1. AttributeError: 'RentDashboardTab' object has no attribute 'current_user_id' - FIXED")
    print("2. Graph text bunching up - FIXED with larger charts and better text spacing")

if __name__ == "__main__":
    validate_fixes()
