#!/usr/bin/env python3
"""
Quick UI Test for Modular Settings Dialog
Tests the visual layout and sizing improvements
"""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget

def test_settings_dialog():
    """Test the settings dialog UI"""
    app = QApplication(sys.argv)
    
    # Create a simple main window
    main_window = QMainWindow()
    main_window.setWindowTitle("Settings Dialog UI Test")
    main_window.setGeometry(100, 100, 300, 200)
    
    # Central widget with a button to open settings
    central_widget = QWidget()
    layout = QVBoxLayout(central_widget)
    
    test_button = QPushButton("Open Settings Dialog")
    
    def open_settings():
        from modular_settings_dialog import SettingsDialog
        dialog = SettingsDialog(main_window)
        dialog.exec()
    
    test_button.clicked.connect(open_settings)
    layout.addWidget(test_button)
    
    main_window.setCentralWidget(central_widget)
    main_window.show()
    
    return app.exec()

if __name__ == "__main__":
    print("🧪 Testing Modular Settings Dialog UI...")
    print("📋 Improvements Applied:")
    print("  ✅ Added size policies for proper expansion")
    print("  ✅ Improved layout margins and spacing")
    print("  ✅ Enhanced group box styling with padding")
    print("  ✅ Better tab container space allocation")
    print("  ✅ Dialog size increased to 800x650")
    print()
    print("🚀 Click 'Open Settings Dialog' to test the UI improvements!")
    
    try:
        sys.exit(test_settings_dialog())
    except KeyboardInterrupt:
        print("\n👋 Test cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error during test: {e}")
        sys.exit(1)
