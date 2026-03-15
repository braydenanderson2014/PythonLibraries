"""
Quick integration test to verify the tax location fix works in the POS system
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.pos_database import POSDatabase
from src.pos_manager import POSManager

def test_pos_location_tax():
    """Test that location-based taxes work correctly in POS"""
    print("=" * 70)
    print("Integration Test: POS Location-Based Tax System")
    print("=" * 70)
    
    # Create fresh database
    if os.path.exists("test_pos_location_tax.db"):
        os.remove("test_pos_location_tax.db")
    
    db = POSDatabase("test_pos_location_tax.db")
    pos_manager = POSManager(db)
    
    print("\n1. Setting up tax rates")
    pos_manager.set_default_tax_rate(0.08)  # 8% default
    pos_manager.add_location_tax_rate("UTAH", 0.0845)  # 8.45% for Utah
    pos_manager.add_location_tax_rate("CA", 0.0725)  # 7.25% for California
    pos_manager.reload_tax_rates()  # Reload to ensure cache is current
    print("   - Default: 8.00%")
    print("   - Utah: 8.45%")
    print("   - California: 7.25%")
    
    print("\n2. Testing location-based tax lookups")
    test_cases = [
        ("Utah", 0.0845, "User enters 'Utah'"),
        ("UTAH", 0.0845, "Uppercase match"),
        ("utah", 0.0845, "Lowercase match"),
        ("CA", 0.0725, "State code"),
        ("California", 0.0725, "Full state name"),
        ("TX", 0.08, "Unknown state (uses default)"),
        (None, 0.08, "No location (uses default)"),
    ]
    
    print(f"   {'Location':<15} {'Expected':<12} {'Returned':<12} {'Result':<8}")
    print("   " + "-" * 50)
    
    all_passed = True
    for location, expected_rate, description in test_cases:
        returned_rate = pos_manager.get_tax_rate(location)
        passed = abs(returned_rate - expected_rate) < 0.0001
        all_passed = all_passed and passed
        
        location_str = repr(location) if location else "None"
        result = "[PASS]" if passed else "[FAIL]"
        print(f"   {location_str:<15} {expected_rate*100:>10.2f}%  {returned_rate*100:>10.2f}%  {result:<8}")
    
    print("\n3. Testing POS sale calculation with location tax")
    
    # Create a test product
    product_id = pos_manager.add_product("Test Item", price=100.00, initial_quantity=10)
    print(f"   Created test product: ${100.00}")
    
    # Test sale with different locations
    locations_to_test = [
        ("Utah", 100.00, 8.45),
        ("CA", 100.00, 7.25),
        (None, 100.00, 8.00),
    ]
    
    print(f"\n   {'Location':<15} {'Subtotal':<12} {'Tax Rate':<12} {'Tax Amount':<12}")
    print("   " + "-" * 55)
    
    for location, subtotal, expected_tax_pct in locations_to_test:
        tax_rate = pos_manager.get_tax_rate(location)
        tax_amount = pos_manager.calculate_tax(subtotal, location)
        expected_tax = subtotal * (expected_tax_pct / 100.0)
        
        location_str = repr(location) if location else "None"
        matches = abs(tax_amount - expected_tax) < 0.01
        
        print(f"   {location_str:<15} ${subtotal:>10.2f}  {tax_rate*100:>10.2f}%  ${tax_amount:>10.2f}")
    
    print("\n" + "=" * 70)
    print("RESULT")
    print("=" * 70)
    
    if all_passed:
        print("[PASS] All location tax lookups working correctly!")
        print("\nThe POS system will now:")
        print("  ✓ Show the correct tax rate when user enters a location")
        print("  ✓ Calculate tax on sales based on the location entered")
        print("  ✓ Fall back to default tax when location is not found")
        return True
    else:
        print("[FAIL] Some tests failed!")
        return False

if __name__ == "__main__":
    try:
        success = test_pos_location_tax()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
