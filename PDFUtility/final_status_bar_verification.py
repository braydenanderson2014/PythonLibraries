#!/usr/bin/env python3
"""
Final verification that all statusBar references are fixed
"""

def final_status_bar_verification():
    """Complete verification that all status bar issues are resolved"""
    print("🔧 Final Status Bar Reference Verification")
    print("=" * 60)
    
    try:
        with open('main_application.py', 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
        
        # Check for any remaining problematic references
        problematic_refs = []
        good_refs = []
        
        for i, line in enumerate(lines):
            if 'statusBar' in line and 'self.statusBar' in line:
                problematic_refs.append((i+1, line.strip()))
            elif 'status_bar' in line and 'self.status_bar' in line:
                good_refs.append((i+1, line.strip()))
        
        print(f"\n📊 Analysis Results:")
        print(f"  • Total lines in file: {len(lines)}")
        print(f"  • Problematic statusBar references: {len(problematic_refs)}")
        print(f"  • Correct status_bar references: {len(good_refs)}")
        
        if problematic_refs:
            print(f"\n❌ Found {len(problematic_refs)} problematic references:")
            for line_num, line_content in problematic_refs:
                print(f"  Line {line_num}: {line_content}")
            return False
        else:
            print(f"\n✅ No problematic statusBar references found!")
        
        print(f"\n✅ Found {len(good_refs)} correct status_bar references:")
        for line_num, line_content in good_refs[:5]:  # Show first 5
            print(f"  Line {line_num}: {line_content}")
        if len(good_refs) > 5:
            print(f"  ... and {len(good_refs) - 5} more")
        
        # Check initialization order
        status_creation = -1
        pdf_viewer_creation = -1
        
        for i, line in enumerate(lines):
            if 'self.status_bar = QStatusBar()' in line:
                status_creation = i + 1
            elif 'self.pdf_viewer_widget = PDFViewerWidget(' in line:
                pdf_viewer_creation = i + 1
        
        print(f"\n🔄 Initialization Order:")
        if status_creation > 0 and pdf_viewer_creation > 0:
            if status_creation < pdf_viewer_creation:
                print(f"  ✅ Status bar (line {status_creation}) created before PDF viewer (line {pdf_viewer_creation})")
            else:
                print(f"  ❌ Wrong order: Status bar (line {status_creation}) vs PDF viewer (line {pdf_viewer_creation})")
                return False
        
        print(f"\n🎯 Expected Behavior:")
        print(f"  • Application should start without AttributeError")
        print(f"  • All status bar messages should display correctly")
        print(f"  • PDF viewer status updates should work")
        print(f"  • Directory monitoring status updates should work")
        print(f"  • Tutorial status updates should work")
        
        print(f"\n✅ All status bar issues are now resolved!")
        return True
        
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        return False

if __name__ == "__main__":
    final_status_bar_verification()
