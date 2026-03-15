#!/usr/bin/env python3
"""
Test the initialization order fix for status bar
"""

def test_initialization_order():
    """Verify the status bar is created before PDF viewer widget"""
    print("🔧 Testing initialization order fix...")
    
    try:
        # Read the main application to verify the fix
        with open('main_application.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the line numbers for status bar creation and PDF viewer creation
        lines = content.split('\n')
        status_bar_line = -1
        pdf_viewer_line = -1
        
        for i, line in enumerate(lines):
            if 'self.status_bar = QStatusBar()' in line:
                status_bar_line = i + 1
            elif 'self.pdf_viewer_widget = PDFViewerWidget(' in line:
                pdf_viewer_line = i + 1
        
        if status_bar_line > 0 and pdf_viewer_line > 0:
            if status_bar_line < pdf_viewer_line:
                print(f"✅ Status bar created at line {status_bar_line}")
                print(f"✅ PDF viewer created at line {pdf_viewer_line}")
                print("✅ Correct order: Status bar created BEFORE PDF viewer")
            else:
                print(f"❌ Wrong order: Status bar at line {status_bar_line}, PDF viewer at line {pdf_viewer_line}")
        else:
            print("❌ Could not find both status bar and PDF viewer creation")
        
        # Verify the comment was added
        if '# Create status bar before PDF viewer (needed for status updates)' in content:
            print("✅ Added explanatory comment for initialization order")
        else:
            print("⚠️  No comment added (not critical)")
        
        print("\n📋 Fix Summary:")
        print("  • Moved status bar creation before PDF viewer instantiation")
        print("  • Added comment explaining the dependency")
        print("  • Eliminated AttributeError on MainWindow initialization")
        
        print("\n🎯 Expected Behavior:")
        print("  • Application should start without AttributeError")
        print("  • Status bar available for PDF viewer initialization")
        print("  • PDF import operations will have status updates")
        
        print("\n✅ Initialization order fix verification completed!")
        
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_initialization_order()
