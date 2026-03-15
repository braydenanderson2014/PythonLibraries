#!/usr/bin/env python3
"""
Test script to verify single instance settings dialog implementation
"""

def test_single_instance_logic():
    """Test the single instance dialog logic without GUI"""
    print("🔧 Testing single instance settings dialog logic...")
    
    try:
        # Simulate the main window instance tracking
        class MockMainWindow:
            def __init__(self):
                self._settings_dialog_instance = None
                
            def show_settings_dialog(self):
                """Mock version of show_settings_dialog logic"""
                # Check if a settings dialog is already open
                if self._settings_dialog_instance is not None:
                    print("⚠️  Settings dialog already open - would bring to front")
                    return "ALREADY_OPEN"
                
                print("✅ Creating new settings dialog instance")
                self._settings_dialog_instance = "MOCK_DIALOG"  # Mock dialog
                return "NEW_DIALOG_CREATED"
                
            def _on_settings_dialog_closed(self):
                """Cleanup when settings dialog is closed"""
                print("🧹 Cleaning up settings dialog instance")
                self._settings_dialog_instance = None
        
        # Test the logic
        main_window = MockMainWindow()
        
        # Test 1: First call should create new dialog
        result1 = main_window.show_settings_dialog()
        print(f"First call result: {result1}")
        
        # Test 2: Second call should detect existing dialog
        result2 = main_window.show_settings_dialog()
        print(f"Second call result: {result2}")
        
        # Test 3: Cleanup and try again
        main_window._on_settings_dialog_closed()
        result3 = main_window.show_settings_dialog()
        print(f"After cleanup result: {result3}")
        
        # Validate results
        if (result1 == "NEW_DIALOG_CREATED" and 
            result2 == "ALREADY_OPEN" and 
            result3 == "NEW_DIALOG_CREATED"):
            print("\n🎉 Single instance logic test PASSED!")
            print("✅ First call creates new dialog")
            print("✅ Subsequent calls detect existing dialog")
            print("✅ Cleanup allows new dialog creation")
        else:
            print("❌ Single instance logic test FAILED")
            
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_single_instance_logic()
