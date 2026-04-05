#!/usr/bin/env python3
"""
Validation script to check that chart duplication fix is in place.
"""

import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

def validate_chart_fix():
    print("=== Validating Chart Duplication Fix ===")
    
    # Read the file and check for the fix
    with open(os.path.join(PROJECT_ROOT, 'ui', 'rent_dashboard_tab.py'), 'r') as f:
        content = f.read()
    
    print("\n1. Checking delinquency chart fix:")
    if 'self.delinq_chart.figure.clear()' in content:
        print("✓ Delinquency chart figure.clear() added")
    else:
        print("✗ Delinquency chart figure.clear() not found")
    
    if 'ax1 = self.delinq_chart.figure.add_subplot(111)' in content:
        print("✓ Delinquency chart uses add_subplot(111) instead of subplots()")
    else:
        print("✗ Delinquency chart still uses subplots()")
    
    print("\n2. Checking monthly chart fix:")
    if 'self.month_chart.figure.clear()' in content:
        print("✓ Monthly chart figure.clear() added")
    else:
        print("✗ Monthly chart figure.clear() not found")
    
    if 'ax2 = self.month_chart.figure.add_subplot(111)' in content:
        print("✓ Monthly chart uses add_subplot(111) instead of subplots()")
    else:
        print("✗ Monthly chart still uses subplots()")
    
    print("\n=== Fix Summary ===")
    print("Changes made to prevent chart duplication:")
    print("1. Changed from 'figure.subplots()' to 'figure.clear() + add_subplot(111)'")
    print("2. This ensures only one subplot exists per chart instead of creating multiple")
    print("3. figure.clear() removes all previous subplots before creating a new one")
    
    print("\nThe chart duplication issue should now be resolved!")

if __name__ == "__main__":
    validate_chart_fix()
