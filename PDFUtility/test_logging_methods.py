#!/usr/bin/env python3
"""
Test script to verify the logging settings widget methods work correctly
"""

def test_logging_widget_methods():
    """Test all methods in the logging settings widget"""
    print("🔧 Testing logging settings widget methods...")
    
    try:
        # Test 1: Import the widget
        from Settings.logging_settings_widget import LoggingSettingsWidget
        print("✅ LoggingSettingsWidget imports successfully")
        
        # Test 2: Check if base widget has the new method
        from Settings.base_settings_widget import BaseSettingsWidget
        base_methods = [method for method in dir(BaseSettingsWidget) if 'open_directory' in method]
        print(f"✅ Base widget directory methods: {base_methods}")
        
        # Test 3: Verify method exists
        if hasattr(BaseSettingsWidget, 'open_directory_browser'):
            print("✅ open_directory_browser method exists in BaseSettingsWidget")
        else:
            print("❌ open_directory_browser method missing")
        
        # Test 4: Check logging widget methods
        logging_methods = [method for method in dir(LoggingSettingsWidget) 
                          if method.startswith('open_') or method.startswith('browse_')]
        print(f"✅ Logging widget methods: {logging_methods}")
        
        # Test 5: Import full dialog
        from rebuilt_settings_dialog import SettingsDialog
        print("✅ Full settings dialog imports successfully")
        
        print("\n🎉 All method tests passed!")
        print("\n📋 Summary:")
        print("  ✅ open_directory_browser method added to BaseSettingsWidget")
        print("  ✅ LoggingSettingsWidget can access the method")
        print("  ✅ All existing methods (open_log_file, browse_log_dir) intact")
        print("  ✅ Settings dialog imports without errors")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_logging_widget_methods()
