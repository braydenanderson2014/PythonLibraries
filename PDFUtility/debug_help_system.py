#!/usr/bin/env python3
"""
Debug script to test help system in both script and simulated bundle modes
"""

import os
import sys
import tempfile
import shutil

def test_script_mode():
    """Test help system in normal script mode"""
    print("🔍 TESTING SCRIPT MODE")
    print("=" * 50)
    
    # Simulate the help system logic
    def get_help_directory():
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
            help_dir_names = ['Help Documents', 'help', 'docs', 'documentation']
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
            help_dir_names = ['Help Documents', 'help', 'docs', 'documentation']
        
        print(f"Base path: {base_path}")
        print(f"Frozen: {getattr(sys, 'frozen', False)}")
        
        for dir_name in help_dir_names:
            help_path = os.path.join(base_path, dir_name)
            print(f"Checking: {help_path}")
            if os.path.exists(help_path):
                print(f"✅ FOUND: {help_path}")
                return help_path, dir_name
            else:
                print(f"❌ NOT FOUND: {help_path}")
        
        return None, None
    
    help_dir, found_name = get_help_directory()
    
    if help_dir:
        print(f"\n✅ SUCCESS: Found help directory '{found_name}' at: {help_dir}")
        try:
            files = os.listdir(help_dir)
            help_files = [f for f in files if f.startswith('HELP_')]
            print(f"📚 Help files found: {len(help_files)}")
        except Exception as e:
            print(f"❌ Error reading directory: {e}")
    else:
        print("\n❌ FAILED: No help directory found in script mode")
    
    return help_dir is not None

def test_simulated_bundle_mode():
    """Test what would happen in PyInstaller bundle mode"""
    print("\n🔍 TESTING SIMULATED BUNDLE MODE")
    print("=" * 50)
    
    # Create a temporary directory to simulate _MEIPASS
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Simulated _MEIPASS: {temp_dir}")
        
        # Copy Help Documents to temp directory to simulate bundle
        source_help = os.path.join(os.path.dirname(__file__), "Help Documents")
        if os.path.exists(source_help):
            dest_help = os.path.join(temp_dir, "Help Documents")
            shutil.copytree(source_help, dest_help)
            print(f"✅ Copied Help Documents to: {dest_help}")
        else:
            print("❌ Source Help Documents not found")
            return False
        
        # Simulate frozen mode
        original_frozen = getattr(sys, 'frozen', False)
        original_meipass = getattr(sys, '_MEIPASS', None)
        
        try:
            sys.frozen = True
            sys._MEIPASS = temp_dir
            
            print(f"Set sys.frozen = {sys.frozen}")
            print(f"Set sys._MEIPASS = {sys._MEIPASS}")
            
            # Test help directory detection
            help_dir_names = ['Help Documents', 'help', 'docs', 'documentation']
            
            for dir_name in help_dir_names:
                help_path = os.path.join(temp_dir, dir_name)
                print(f"Checking: {help_path}")
                if os.path.exists(help_path):
                    print(f"✅ FOUND: {help_path}")
                    # Count files
                    try:
                        files = os.listdir(help_path)
                        help_files = [f for f in files if f.startswith('HELP_')]
                        print(f"📚 Help files in bundle: {len(help_files)}")
                        if help_files:
                            print(f"First few files: {help_files[:3]}")
                        return True
                    except Exception as e:
                        print(f"❌ Error reading bundle directory: {e}")
                else:
                    print(f"❌ NOT FOUND: {help_path}")
            
            print("❌ No help directory found in simulated bundle")
            return False
            
        finally:
            # Restore original values
            if original_frozen:
                sys.frozen = original_frozen
            else:
                delattr(sys, 'frozen')
            
            if original_meipass:
                sys._MEIPASS = original_meipass
            elif hasattr(sys, '_MEIPASS'):
                delattr(sys, '_MEIPASS')

def check_spec_file():
    """Check the PyInstaller spec file configuration"""
    print("\n🔍 CHECKING PYINSTALLER SPEC FILE")
    print("=" * 50)
    
    spec_file = "PDF Utility-08042025-ALPHA.spec"
    if os.path.exists(spec_file):
        print(f"✅ Found spec file: {spec_file}")
        with open(spec_file, 'r') as f:
            content = f.read()
            
        # Look for datas section
        if 'datas=' in content:
            print("✅ Found datas section in spec file")
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'datas=' in line or 'Help Documents' in line:
                    print(f"Line {i+1}: {line.strip()}")
        else:
            print("❌ No datas section found in spec file")
            
        # Check for Help Documents inclusion
        if 'Help Documents' in content:
            print("✅ 'Help Documents' found in spec file")
        else:
            print("❌ 'Help Documents' NOT found in spec file")
            
    else:
        print(f"❌ Spec file not found: {spec_file}")

if __name__ == "__main__":
    print("🚀 COMPREHENSIVE HELP SYSTEM DEBUG TEST")
    print("=" * 60)
    
    script_success = test_script_mode()
    bundle_success = test_simulated_bundle_mode()
    check_spec_file()
    
    print("\n" + "=" * 60)
    print("📋 SUMMARY")
    print("=" * 60)
    print(f"Script Mode: {'✅ PASS' if script_success else '❌ FAIL'}")
    print(f"Bundle Mode: {'✅ PASS' if bundle_success else '❌ FAIL'}")
    
    if script_success and bundle_success:
        print("\n🎉 OVERALL: SUCCESS! Help system should work in built executable.")
    else:
        print("\n⚠️  OVERALL: Issues detected. Help system may not work in built executable.")
        print("\nRecommendations:")
        if not script_success:
            print("- Fix help directory detection in script mode")
        if not bundle_success:
            print("- Check PyInstaller spec file datas configuration")
            print("- Ensure Help Documents folder is properly included in build")
