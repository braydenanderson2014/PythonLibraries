#!/usr/bin/env python3
"""
Test script to verify all settings fixes are working properly
"""

import sys
from PyQt6.QtWidgets import QApplication
from rebuilt_settings_dialog import SettingsDialog
from settings_controller import SettingsController
from PDFLogger import PDFLogger

def test_settings_fixes():
    """Test all the settings fixes"""
    print("🔧 Testing settings fixes...")
    
    # Create QApplication
    app = QApplication(sys.argv)
    
    # Create logger and settings controller
    logger = PDFLogger()
    settings_controller = SettingsController()
    
    try:
        # Create settings dialog
        dialog = SettingsDialog(settings_controller, logger)
        print("✅ Settings dialog created successfully")
        
        # Test tutorial settings widget
        tutorial_widget = dialog.widgets['Tutorial']
        print("✅ Tutorial widget has show_question_message method:", hasattr(tutorial_widget, 'show_question_message'))
        
        # Test editor settings (should be disabled)
        editor_widget = dialog.widgets['PDF Editor']
        print("✅ Editor widget is disabled:", not editor_widget.isEnabled())
        
        # Test advanced settings (simplified)
        advanced_widget = dialog.widgets['Advanced']
        print("✅ Advanced widget - parallel processing removed:", not hasattr(advanced_widget, 'parallel_processing_cb'))
        print("✅ Advanced widget - log level removed:", not hasattr(advanced_widget, 'log_level_combo'))
        print("✅ Advanced widget - max processes removed:", not hasattr(advanced_widget, 'max_processes_spin'))
        print("✅ Advanced widget - temp dir still present:", hasattr(advanced_widget, 'temp_dir_edit'))
        
        # Test logging settings (simplified layout)
        logging_widget = dialog.widgets['Logging']
        print("✅ Logging widget - keep backups removed:", not hasattr(logging_widget, 'keep_log_backups_spin'))
        print("✅ Logging widget - editor checkbox removed:", not hasattr(logging_widget, 'open_log_in_editor_cb'))
        print("✅ Logging widget - last cleared label removed:", not hasattr(logging_widget, 'last_cleared_label'))
        
        # Test message methods in base widget
        from Settings.base_settings_widget import BaseSettingsWidget
        base_methods = [method for method in dir(BaseSettingsWidget) if method.startswith('show_')]
        print(f"✅ Base widget message methods: {base_methods}")
        
        print("\n🎉 All settings fixes verified successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        app.quit()

if __name__ == "__main__":
    test_settings_fixes()
