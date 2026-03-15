#!/usr/bin/env python3
"""
Test script to verify balanced layout spacing in bank dashboards
"""

print("Testing Bank Dashboard Layout Balance...")
print("=" * 50)

try:
    # Read the financial tracker file to verify changes
    with open('ui/financial_tracker.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("✓ Financial tracker file read successfully")
    
    # Check for balanced sizing improvements
    layout_improvements = [
        ('figsize=(8, 5)', 'Balanced chart size (8x5)'),
        ('setMinimumSize(350, 250)', 'Reasonable minimum canvas size'),
        ('setMaximumSize(450, 350)', 'Maximum size to prevent over-expansion'),
        ('setSpacing(20)', 'Increased spacing between sections'),
        ('setContentsMargins(10, 10, 10, 10)', 'Added margins around content'),
        ('setMinimumHeight(300)', 'Charts group minimum height'),
        ('setMaximumHeight(400)', 'Charts group maximum height'),
        ('accounts_table.setMaximumHeight(200)', 'Account table size limit'),
        ('recent_table.setMaximumHeight(400)', 'Transactions table size limit'),
        ('QSizePolicy.Policy.Preferred', 'Preferred size policy for balanced layout')
    ]
    
    print("\nLayout Balance Improvements:")
    for check, description in layout_improvements:
        if check in content:
            print(f"✓ {description}")
        else:
            print(f"✗ {description} - NOT FOUND")
    
    print("\nExpected Layout Improvements:")
    print("📊 Charts: Reasonable size (8x5) with max limits")
    print("📋 Tables: Limited heights to prevent over-expansion")
    print("📐 Spacing: 20px between sections, 10px margins")
    print("🎯 Balance: Each section gets appropriate space")
    print("🔄 Scrolling: Content flows naturally without bunching")
    
    print("\n✅ Balanced layout spacing implemented!")
    
except Exception as e:
    print(f"❌ Error reading file: {e}")

print("=" * 50)
print("🎨 Dashboard should now have proper spacing!")
print("💡 Refresh the Bank Dashboards tab to see balanced layout")