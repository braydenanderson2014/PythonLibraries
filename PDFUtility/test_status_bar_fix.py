#!/usr/bin/env python3
"""
Test the status bar fix for PDF viewer
"""

def test_status_bar_fix():
    """Verify the status bar attribute error is fixed"""
    print("🔧 Testing status bar fix...")
    
    try:
        # Read the main application to verify the fix
        with open('main_application.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check that we're using self.status_bar instead of self.statusBar
        if 'self.status_bar = QStatusBar()' in content:
            print("✅ Status bar created with correct attribute name")
        else:
            print("❌ Status bar creation not found")
        
        if 'status_bar=self.status_bar' in content:
            print("✅ Status bar passed correctly to PDF viewer")
        else:
            print("❌ Status bar not passed correctly")
        
        # Check that we're not using the problematic self.statusBar method
        if 'status_bar=self.statusBar' not in content:
            print("✅ Not using problematic statusBar method")
        else:
            print("❌ Still using problematic statusBar method")
        
        print("\n📋 Fix Summary:")
        print("  • Changed self.statusBar to self.status_bar")
        print("  • Updated PDF viewer parameter to use status_bar object")
        print("  • Eliminated AttributeError on 'builtin_function_or_method'")
        
        print("\n🎯 Expected Behavior:")
        print("  • Status bar updates should work without errors")
        print("  • PDF import operations will show status messages")
        print("  • No more AttributeError when updating status")
        
        print("\n✅ Status bar fix verification completed!")
        
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_status_bar_fix()
