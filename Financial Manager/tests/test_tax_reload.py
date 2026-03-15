"""
Test to verify that tax rates are properly reloaded after being saved.
This tests the fix for the issue where manually overridden tax percentages
didn't show correctly until the program was rebooted.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.pos_database import POSDatabase
from src.pos_manager import POSManager

def test_tax_reload():
    """Test that tax rates are reloaded after being changed"""
    print("=" * 60)
    print("TEST: Tax Rate Reload After Save")
    print("=" * 60)
    
    # Create fresh database
    if os.path.exists("test_tax_reload.db"):
        os.remove("test_tax_reload.db")
    
    # Initialize database and manager
    db = POSDatabase("test_tax_reload.db")
    pos_manager = POSManager(db)
    
    print("\n1. Initial state - No location-specific rates set")
    print(f"   All tax rates: {pos_manager.get_all_tax_rates()}")
    
    print("\n2. Getting tax rate for 'Utah' (should default to 8%)")
    initial_rate = pos_manager.get_tax_rate("Utah")
    print(f"   Tax rate for Utah: {initial_rate*100:.2f}%")
    
    print("\n3. Setting custom tax rate for UTAH to 8.45%")
    pos_manager.add_location_tax_rate("UTAH", 0.0845)
    print(f"   Added location tax rate")
    
    print("\n4. WITHOUT reload - using cached value")
    # Note: This might show 0.08 if cache isn't reloaded
    rate_before_reload = pos_manager.get_tax_rate("UTAH")
    print(f"   Tax rate before reload: {rate_before_reload*100:.2f}%")
    
    print("\n5. Reloading tax rates from database")
    pos_manager.reload_tax_rates()
    print(f"   Tax rates reloaded")
    
    print("\n6. AFTER reload - should show 8.45%")
    rate_after_reload = pos_manager.get_tax_rate("UTAH")
    print(f"   Tax rate after reload: {rate_after_reload*100:.2f}%")
    
    print("\n7. All tax rates in cache (retrieved as decimals):")
    all_rates = pos_manager.get_all_tax_rates()
    for location, rate in list(all_rates.items())[:5]:  # Show first 5
        print(f"   {location}: {rate*100:.2f}%")  # Convert decimal back to percentage for display
    
    # Verify the fix
    print("\n" + "=" * 60)
    print("VERIFICATION")
    print("=" * 60)
    
    if abs(rate_after_reload - 0.0845) < 0.0001:
        print("[PASS] Tax rate correctly reloaded to 8.45%")
        return True
    else:
        print(f"[FAIL] Expected 8.45%, got {rate_after_reload*100:.2f}%")
        return False

if __name__ == "__main__":
    try:
        success = test_tax_reload()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
