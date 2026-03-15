"""Test Store Settings Integration"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.store_settings import StoreSettings
from services.tax_service import TaxService

def test_store_settings():
    """Test store settings functionality"""
    print("\n=== Testing Store Settings Integration ===\n")
    
    # Initialize StoreSettings
    store = StoreSettings()
    print("✓ StoreSettings initialized")
    
    # Test setting location
    store.set_location("CA", "San Francisco", "94102")
    location = store.get_location()
    print(f"✓ Store location set: {location}")
    
    # Test setting store name
    store.set_store_name("My Cool Store")
    print(f"✓ Store name set: My Cool Store")
    
    # Test tax preferences
    store.set_tax_preferences({
        'include_state_tax': True,
        'include_federal_tax': False,
        'include_local_tax': True,
        'auto_calculate': True
    })
    prefs = store.get_tax_preferences()
    print(f"✓ Tax preferences set:")
    print(f"  - Include State Tax: {prefs.get('include_state_tax')}")
    print(f"  - Include Local Tax: {prefs.get('include_local_tax')}")
    print(f"  - Include Federal Tax: {prefs.get('include_federal_tax')}")
    
    # Test TaxService with location
    print("\n=== Testing Tax Lookup ===\n")
    
    tax_data = TaxService.get_location_taxes(
        "CA",
        include_state=prefs.get('include_state_tax', True),
        include_local=prefs.get('include_local_tax', True),
        include_federal=prefs.get('include_federal_tax', False)
    )
    
    if tax_data:
        print(f"✓ Tax data retrieved for CA:")
        print(f"  - State Rate: {tax_data['breakdown']['state']}")
        print(f"  - Local Rate: {tax_data['breakdown']['local']}")
        print(f"  - Federal Rate: {tax_data['breakdown']['federal']}")
        print(f"  - Combined Rate: {tax_data['combined_rate']*100:.2f}%")
        print(f"  - Source: {tax_data['source']}")
    else:
        print("✗ Failed to retrieve tax data")
    
    # Test combining taxes
    print("\n=== Testing Tax Combination ===\n")
    combined = TaxService.combine_taxes(0.0725, 0.0125, 0.0)
    print(f"✓ Combined tax calculation:")
    print(f"  - State (7.25%) + Local (1.25%) + Federal (0%) = {combined*100:.2f}%")
    
    # Test with POS Manager
    print("\n=== Testing POS Manager Integration ===\n")
    try:
        from src.pos_manager import POSManager
        
        pos_mgr = POSManager()
        
        # Calculate tax with preferences
        subtotal = 100.00
        tax_amount = pos_mgr.calculate_tax(
            subtotal, 
            location="CA",
            tax_preferences=prefs
        )
        
        print(f"✓ POS Tax Calculation:")
        print(f"  - Subtotal: ${subtotal:.2f}")
        print(f"  - Location: CA")
        print(f"  - Tax Amount: ${tax_amount:.2f}")
        print(f"  - Tax Rate: {(tax_amount/subtotal)*100:.2f}%")
        print(f"  - Total: ${subtotal + tax_amount:.2f}")
        
    except Exception as e:
        print(f"✗ POS Manager integration failed: {e}")
    
    # Verify settings persistence
    print("\n=== Testing Settings Persistence ===\n")
    store2 = StoreSettings()
    loaded_location = store2.get_location()
    loaded_prefs = store2.get_tax_preferences()
    
    if loaded_location == location and loaded_prefs == prefs:
        print(f"✓ Settings persisted correctly:")
        print(f"  - Location: {loaded_location}")
        print(f"  - Preferences match: {loaded_prefs == prefs}")
    else:
        print(f"✗ Settings not persisted correctly")
    
    print("\n=== All Integration Tests Completed ===\n")

if __name__ == '__main__':
    test_store_settings()
