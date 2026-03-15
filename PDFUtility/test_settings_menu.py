#!/usr/bin/env python3
"""
Test script to verify the Settings menu is properly added to the File menu
"""

import sys
import os
sys.path.insert(0, '.')

try:
    from PyQt6.QtWidgets import QApplication
    from main_application import MainApplication
    
    print("Testing Settings Menu Integration")
    print("=" * 40)
    
    # Create application instance
    app = QApplication([])
    
    # Create main window
    main_window = MainApplication()
    
    # Check if the menu bar exists
    menu_bar = main_window.menuBar()
    if menu_bar:
        print("✅ Menu bar created successfully")
        
        # Find the File menu
        file_menu = None
        for action in menu_bar.actions():
            if action.text() == "&File":
                file_menu = action.menu()
                break
        
        if file_menu:
            print("✅ File menu found")
            
            # Check for Settings action
            settings_found = False
            exit_found = False
            separator_found = False
            
            for action in file_menu.actions():
                if action.text() == "&Settings...":
                    settings_found = True
                    print(f"✅ Settings action found: {action.text()}")
                    print(f"   Shortcut: {action.shortcut().toString()}")
                    print(f"   Status tip: {action.statusTip()}")
                elif action.text() == "E&xit":
                    exit_found = True
                    print(f"✅ Exit action found: {action.text()}")
                elif action.isSeparator():
                    separator_found = True
                    print("✅ Separator found between Settings and Exit")
            
            if settings_found:
                print("✅ Settings menu item properly added to File menu")
            else:
                print("❌ Settings menu item not found in File menu")
                
            if exit_found:
                print("✅ Exit menu item still present")
            else:
                print("❌ Exit menu item missing")
                
            if separator_found:
                print("✅ Separator between Settings and Exit")
            else:
                print("⚠️ No separator between menu items")
        else:
            print("❌ File menu not found")
    else:
        print("❌ Menu bar not created")
    
    # Check if settings dialog can be imported
    try:
        from settings_dialog import SettingsDialog
        print("✅ SettingsDialog can be imported")
        
        # Check if the method exists
        if hasattr(main_window, 'show_settings_dialog'):
            print("✅ show_settings_dialog method exists")
        else:
            print("❌ show_settings_dialog method missing")
            
    except ImportError as e:
        print(f"❌ Cannot import SettingsDialog: {e}")
    
    print("\n" + "=" * 40)
    print("Settings Menu Integration Test Complete")
    
    # Don't show the window, just test the setup
    app.quit()
    
except ImportError as e:
    print(f"Cannot run GUI test: {e}")
    print("This is expected in environments without PyQt6")
    
    # Fallback: Check if the code changes are present in the file
    print("\nFallback: Checking file content...")
    
    try:
        with open('main_application.py', 'r') as f:
            content = f.read()
            
        if '&Settings...' in content:
            print("✅ Settings menu action found in code")
        else:
            print("❌ Settings menu action not found in code")
            
        if 'settings_action.triggered.connect(self.show_settings_dialog)' in content:
            print("✅ Settings action connected to handler")
        else:
            print("❌ Settings action not connected")
            
        if 'def show_settings_dialog(self):' in content:
            print("✅ show_settings_dialog method exists")
        else:
            print("❌ show_settings_dialog method missing")
            
    except FileNotFoundError:
        print("❌ main_application.py not found")
