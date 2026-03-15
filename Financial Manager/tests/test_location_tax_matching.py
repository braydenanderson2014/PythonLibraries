"""
Test to verify location-to-tax-rate matching
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.pos_database import POSDatabase
from src.pos_manager import POSManager

def test_location_matching():
    """Test different location formats and how they match tax rates"""
    print("=" * 70)
    print("TEST: Location to Tax Rate Matching")
    print("=" * 70)
    
    # Create fresh database
    if os.path.exists("test_location_tax.db"):
        os.remove("test_location_tax.db")
    
    db = POSDatabase("test_location_tax.db")
    pos_manager = POSManager(db)
    
    # Set a default rate first
    print("\n1. Setting DEFAULT tax rate to 8.00%")
    pos_manager.set_default_tax_rate(0.08)
    
    # Set location-specific rates with different formats
    test_cases = [
        ("UTAH", 0.0845, "All uppercase"),
        ("UT", 0.0885, "State code only"),
        ("Utah, UT", 0.0925, "City, State format"),
        ("Salt Lake City", 0.0765, "City name only"),
    ]
    
    print("\n2. Setting various location tax rates:")
    for location, rate, description in test_cases:
        pos_manager.add_location_tax_rate(location, rate)
        print(f"   {location:20} = {rate*100:.2f}%  ({description})")
    
    # Test lookups with different input formats
    test_lookups = [
        ("UTAH", "Uppercase - exact match"),
        ("utah", "Lowercase - should convert to uppercase"),
        ("Utah", "Mixed case - should convert to uppercase"),
        ("UT", "State code"),
        ("ut", "State code lowercase"),
        ("Salt Lake City", "City name"),
        ("salt lake city", "City lowercase"),
        ("Utah, UT", "Full format"),
        ("unknown", "Unknown location (should use DEFAULT)"),
        ("", "Empty string (should use DEFAULT)"),
        (None, "None (should use DEFAULT)"),
    ]
    
    print("\n3. Looking up tax rates with various input formats:")
    print(f"   {'Input':<25} {'Returned':>10} {'Expected?':>15}")
    print("   " + "-" * 50)
    
    for location, description in test_lookups:
        try:
            rate = pos_manager.get_tax_rate(location)
            location_display = repr(location) if location else "None"
            print(f"   {location_display:<25} {rate*100:>9.2f}%  {description}")
        except Exception as e:
            print(f"   {repr(location):<25} ERROR: {e}")
    
    print("\n4. Show what's in the cache:")
    all_rates = pos_manager.get_all_tax_rates()
    print(f"   Cache contains {len(all_rates)} entries:")
    for location, rate in all_rates.items():
        print(f"      {location}: {rate*100:.2f}%")
    
    print("\n" + "=" * 70)
    print("ANALYSIS")
    print("=" * 70)
    print("""
The issue: When you set "UTAH" in the tax settings with 8.45%, but then enter
"Utah" or other variations in the sales screen, it might not find the match.

The code does convert to uppercase and strips spaces, so "utah", "Utah", "UTAH"
should all match "UTAH". But if there's a mismatch in how it's stored or 
retrieved, it will fall back to the DEFAULT rate of 8.00%.

Check the "Returned" column above - they should match the expected rates.
If "Utah" returns 8.00% instead of 8.45%, that's the problem!
    """)

if __name__ == "__main__":
    try:
        test_location_matching()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
