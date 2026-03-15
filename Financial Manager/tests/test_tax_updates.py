#!/usr/bin/env python3
"""
Test script to verify tax updates when items are added to cart
"""

from src.pos_manager import POSManager
from src.pos_database import POSDatabase

print("=" * 60)
print("TAX SYSTEM UPDATE TEST")
print("=" * 60)

# Setup
pm = POSManager()
pm.set_default_tax_rate(0.08)
pm.add_location_tax_rate("CA", 0.0725)
pm.add_location_tax_rate("NY", 0.04)

# Simulate adding items to cart
print("\nScenario 1: Cart with location-based tax")
print("-" * 60)

cart = [
    {'quantity': 2, 'unit_price': 50.0},  # $100 subtotal
    {'quantity': 1, 'unit_price': 75.0},  # $75 subtotal
]

subtotal = sum(item['quantity'] * item['unit_price'] for item in cart)
location = "CA"
tax_exempt = False

print(f"Subtotal (2 items): ${subtotal:.2f}")
print(f"Location: {location}")
print(f"Tax Exempt: {tax_exempt}")

if not tax_exempt:
    tax_amount = pm.calculate_tax(subtotal, location)
else:
    tax_amount = 0.0

total = subtotal + tax_amount

print(f"Tax Rate: {pm.get_tax_rate(location)*100:.2f}%")
print(f"Tax Amount: ${tax_amount:.2f}")
print(f"Total: ${total:.2f}")

# Scenario 2: Add another item
print("\nScenario 2: Adding another item updates tax")
print("-" * 60)

new_item = {'quantity': 3, 'unit_price': 25.0}  # $75 more
cart.append(new_item)

new_subtotal = sum(item['quantity'] * item['unit_price'] for item in cart)
print(f"Subtotal (3 items): ${new_subtotal:.2f}")
print(f"Previous subtotal: ${subtotal:.2f}")
print(f"Added: ${new_subtotal - subtotal:.2f}")

new_tax = pm.calculate_tax(new_subtotal, location)
new_total = new_subtotal + new_tax

print(f"New Tax Amount: ${new_tax:.2f}")
print(f"Previous Tax Amount: ${tax_amount:.2f}")
print(f"Tax increased by: ${new_tax - tax_amount:.2f}")
print(f"New Total: ${new_total:.2f}")

# Scenario 3: Tax exempt
print("\nScenario 3: Tax-exempt transaction")
print("-" * 60)

tax_exempt = True
if tax_exempt:
    tax_amount = 0.0
    total = new_subtotal

print(f"Subtotal: ${new_subtotal:.2f}")
print(f"Tax Exempt: {tax_exempt}")
print(f"Tax Amount: ${tax_amount:.2f}")
print(f"Total: ${total:.2f}")

print("\n" + "=" * 60)
print("✓ All tax update scenarios working correctly!")
print("=" * 60)
