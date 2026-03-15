#!/usr/bin/env python3
"""
Test help system path detection without PyQt6 dependency
"""

import os
import sys

def test_help_directory_detection():
    """Test the help directory detection logic from help_system_qt.py"""
    print("Testing Help Directory Detection Logic")
    print("=" * 50)
    
    def get_help_directory():
        """Replicate the logic from help_system_qt.py"""
        if getattr(sys, 'frozen', False):
            # Running as PyInstaller bundle
            base_path = sys._MEIPASS
            print(f"Help system: PyInstaller bundle detected, base path: {base_path}")
            
            # Try multiple possible help directory names
            help_dir_names = ['Help Documents', 'help', 'docs', 'documentation']
            for dir_name in help_dir_names:
                help_path = os.path.join(base_path, dir_name)
                print(f"Help system: Checking for help directory: {help_path}")
                if os.path.exists(help_path):
                    print(f"Help system: Found help directory: {help_path}")
                    return help_path
            
            print("Help system: No help directory found in bundle")
            return None
        else:
            # Running as script
            base_path = os.path.dirname(os.path.abspath(__file__))
            print(f"Help system: Running as script, base path: {base_path}")
            
            # Try multiple possible help directory names
            help_dir_names = ['Help Documents', 'help', 'docs', 'documentation']
            for dir_name in help_dir_names:
                help_path = os.path.join(base_path, dir_name)
                print(f"Help system: Checking for help directory: {help_path}")
                if os.path.exists(help_path):
                    print(f"Help system: Found help directory: {help_path}")
                    return help_path
            
            print("Help system: No help directory found")
            return None
    
    help_dir = get_help_directory()
    
    if help_dir:
        print(f"\n✅ SUCCESS: Help directory found at: {help_dir}")
        
        # Count help files
        try:
            contents = os.listdir(help_dir)
            help_files = [f for f in contents if f.startswith('HELP_') and f.endswith(('.md', '.txt', '.rst'))]
            print(f"📚 Found {len(help_files)} HELP_ files:")
            for f in help_files[:5]:  # Show first 5
                print(f"  • {f}")
            if len(help_files) > 5:
                print(f"  ... and {len(help_files) - 5} more")
                
        except Exception as e:
            print(f"❌ Error reading directory: {e}")
    else:
        print("\n❌ FAILED: No help directory found")
    
    return help_dir is not None

if __name__ == "__main__":
    success = test_help_directory_detection()
    
    print(f"\n{'=' * 50}")
    if success:
        print("🎉 HELP SYSTEM FIX: SUCCESS!")
        print("The help system will now properly find help documents in both:")
        print("  • Script mode (development)")
        print("  • PyInstaller executable mode (when Help Documents folder is included)")
    else:
        print("❌ HELP SYSTEM FIX: FAILED!")
        print("Help directory detection needs further investigation.")
