#!/usr/bin/env python3
"""
Comprehensive verification and troubleshooting for status bar fix
"""

def comprehensive_status_bar_check():
    """Complete verification of status bar implementation"""
    print("🔧 Comprehensive Status Bar Fix Verification")
    print("=" * 60)
    
    try:
        with open('main_application.py', 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
        
        print("\n📋 File Analysis:")
        print(f"  • Total lines: {len(lines)}")
        
        # Find critical lines
        status_creation_line = -1
        pdf_viewer_line = -1
        
        for i, line in enumerate(lines):
            if 'self.status_bar = QStatusBar()' in line:
                status_creation_line = i + 1
                print(f"  • Status bar creation: Line {status_creation_line}")
            elif 'self.pdf_viewer_widget = PDFViewerWidget(' in line:
                pdf_viewer_line = i + 1
                print(f"  • PDF viewer creation: Line {pdf_viewer_line}")
        
        # Check order
        if status_creation_line > 0 and pdf_viewer_line > 0:
            if status_creation_line < pdf_viewer_line:
                print(f"  ✅ Order is correct: {status_creation_line} < {pdf_viewer_line}")
            else:
                print(f"  ❌ Order is wrong: {status_creation_line} >= {pdf_viewer_line}")
                return False
        
        # Check parameter passing
        if 'status_bar=self.status_bar' in content:
            print("  ✅ Status bar parameter passed correctly")
        else:
            print("  ❌ Status bar parameter not found")
            return False
        
        # Check for old problematic code
        if 'status_bar=self.statusBar' in content:
            print("  ❌ Old problematic statusBar method still present")
            return False
        else:
            print("  ✅ No old statusBar method references")
        
        print("\n🔍 Context around PDF viewer creation:")
        if pdf_viewer_line > 0:
            start = max(0, pdf_viewer_line - 6)
            end = min(len(lines), pdf_viewer_line + 3)
            for i in range(start, end):
                marker = " >>> " if i == pdf_viewer_line - 1 else "     "
                print(f"{marker}Line {i+1}: {lines[i]}")
        
        print("\n✅ All checks passed!")
        print("\n💡 If you're still getting the error:")
        print("  1. Restart the application completely")
        print("  2. Check if you're running the right file")
        print("  3. Verify no other Python processes are cached")
        print("  4. Try running from a fresh terminal")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        return False

if __name__ == "__main__":
    comprehensive_status_bar_check()
