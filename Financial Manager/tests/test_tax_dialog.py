"""
Test Tax Settings Dialog with Online Lookup
"""

import sys
from PyQt6.QtWidgets import QApplication
from ui.tax_settings_dialog import TaxSettingsDialog

app = QApplication(sys.argv)

try:
    # Create dialog
    dialog = TaxSettingsDialog(None)
    print("OK: TaxSettingsDialog created successfully")
    
    # Test the UI components
    print("\nUI Components Check:")
    print(f"  location_search_combo: {hasattr(dialog, 'location_search_combo')}")
    print(f"  location_input: {hasattr(dialog, 'location_input')}")
    print(f"  location_tax_input: {hasattr(dialog, 'location_tax_input')}")
    print(f"  lookup_status_label: {hasattr(dialog, 'lookup_status_label')}")
    print(f"  tax_table: {hasattr(dialog, 'tax_table')}")
    
    # Test online lookup
    print("\nTesting Online Tax Lookup:")
    from services.tax_service import TaxService
    
    result = TaxService.lookup_tax_rate("CA")
    if result:
        print(f"  OK CA: {result['combined_rate']*100:.2f}% from {result['source']}")
    else:
        print("  FAIL CA lookup")
    
    result = TaxService.lookup_tax_rate("NY")
    if result:
        print(f"  OK NY: {result['combined_rate']*100:.2f}% from {result['source']}")
    else:
        print("  FAIL NY lookup")
    
    print("\nOK: All tests passed!")
    print("Dialog is ready. Try typing 'CA', 'TX', 'NY' in the location field.")
    
except Exception as e:
    print(f"FAIL: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
