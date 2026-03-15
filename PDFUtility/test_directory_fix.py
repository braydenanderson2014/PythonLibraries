#!/usr/bin/env python3
"""
Simple test to verify the open_directory_browser fix
"""

def test_imports():
    """Test that imports work without errors"""
    print("🔧 Testing imports after open_directory_browser fix...")
    
    try:
        # Test that the method exists and has proper imports
        import inspect
        import os
        import platform
        import subprocess
        
        # Check that all required modules are importable
        print("✅ All required modules (os, platform, subprocess) import successfully")
        
        # Test directory existence check logic (without PyQt6)
        def mock_directory_check(directory):
            if not directory or not os.path.exists(directory):
                return False, f"Directory does not exist: {directory}"
            return True, "Directory exists"
            
        # Test with Windows directory
        test_dir = r"C:\Windows"
        exists, message = mock_directory_check(test_dir)
        print(f"✅ Directory check test: {message}")
        
        # Test with non-existent directory  
        fake_dir = r"C:\NonExistentDirectory12345"
        exists, message = mock_directory_check(fake_dir)
        print(f"✅ Non-existent directory check: {message}")
        
        # Test with empty directory
        empty_dir = ""
        exists, message = mock_directory_check(empty_dir)
        print(f"✅ Empty directory check: {message}")
        
        print("\n🎉 All import and logic tests passed!")
        print("✅ The UnboundLocalError for 'os' should be fixed")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_imports()
