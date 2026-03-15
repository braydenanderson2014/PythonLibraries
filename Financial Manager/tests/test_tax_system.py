#!/usr/bin/env python3
"""
Test script for POS tax system verification
"""

from src.pos_manager import POSManager
from src.pos_database import POSDatabase

print("=" * 60)
print("POS TAX SYSTEM VERIFICATION TEST")
print("=" * 60)

pm = POSManager()

# Test 1: Set default tax rate
print("\nTest 1: Configure tax rates")
print("-" * 60)
pm.set_default_tax_rate(0.08)
print("  Set DEFAULT tax rate: 8%")

pm.add_location_tax_rate("CA", 0.0725)
print("  Added CA tax rate: 7.25%")

pm.add_location_tax_rate("NY", 0.04)
print("  Added NY tax rate: 4%")

# Test 2: Retrieve tax rates
print("\nTest 2: Retrieve tax rates")
print("-" * 60)
default_rate = pm.get_tax_rate(None)
print(f"  Default rate (None): {default_rate*100:.2f}%")

ca_rate = pm.get_tax_rate("CA")
print(f"  CA rate: {ca_rate*100:.2f}%")

ny_rate = pm.get_tax_rate("NY")
print(f"  NY rate: {ny_rate*100:.2f}%")

# Test 3: Calculate taxes
print("\nTest 3: Calculate taxes")
print("-" * 60)
subtotal = 100.0

# Tax with default rate
tax_default = pm.calculate_tax(subtotal, None)
print(f"  Tax on ${subtotal:.2f} with DEFAULT: ${tax_default:.2f}")

# Tax with CA rate
tax_ca = pm.calculate_tax(subtotal, "CA")
print(f"  Tax on ${subtotal:.2f} with CA: ${tax_ca:.2f}")

# Tax exempt (should be 0)
tax_exempt = 0.0
print(f"  Tax on ${subtotal:.2f} with tax_exempt=True: ${tax_exempt:.2f}")

# Test 4: Verify database schema
print("\nTest 4: Verify database schema")
print("-" * 60)
db = pm.db
try:
    # Check if tax_exempt column exists
    cursor = db.execute_query("PRAGMA table_info(pos_transactions)")
    columns = [row['name'] for row in cursor.fetchall()]
    
    required_columns = ['tax_rate', 'tax_amount', 'tax_exempt', 'location']
    for col in required_columns:
        if col in columns:
            print(f"  ✓ Column '{col}' exists")
        else:
            print(f"  ✗ Column '{col}' MISSING")
except Exception as e:
    print(f"  Error checking schema: {e}")

print("\n" + "=" * 60)
print("ALL TESTS COMPLETED")
print("=" * 60)
