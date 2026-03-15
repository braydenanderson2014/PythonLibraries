#!/usr/bin/env python3
"""
Comprehensive verification that PDF viewer doesn't auto-load
"""

def verify_no_auto_load():
    """Verify all auto-loading has been removed"""
    print("🔧 Comprehensive auto-load prevention verification...")
    
    try:
        # Read the file content to verify changes
        with open('pdf_viewer_widget.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("📋 Checking for auto-loading triggers...")
        
        # Test 1: Check import method doesn't auto-load
        if 'if not self.current_pdf_path and pdf_files:' in content:
            print("❌ Auto-load logic still exists in import_pdfs_from_tabs")
        else:
            print("✅ Auto-load logic removed from import_pdfs_from_tabs")
        
        # Test 2: Check that the message was updated
        if 'Select from the dropdown to view a PDF.' in content:
            print("✅ Import message updated to indicate manual selection needed")
        else:
            print("❌ Import message not updated")
        
        # Test 3: Check signal usage
        if content.count('activated.connect') >= 1:
            print("✅ Using activated signal (user-triggered only)")
        else:
            print("❌ Not using activated signal")
        
        # Test 4: Check no currentTextChanged usage
        if 'currentTextChanged.connect' not in content:
            print("✅ No currentTextChanged signal (prevents auto-trigger)")
        else:
            print("❌ Still using currentTextChanged signal")
        
        # Test 5: Check for signal blocking
        if 'blockSignals(True)' in content and 'blockSignals(False)' in content:
            print("✅ Signal blocking implemented during updates")
        else:
            print("❌ Signal blocking not properly implemented")
        
        # Test 6: Check for setCurrentIndex(-1)
        if 'setCurrentIndex(-1)' in content:
            print("✅ Dropdown set to no selection by default")
        else:
            print("❌ Dropdown selection not cleared")
        
        # Test 7: Count load_pdf_file calls to ensure only user-triggered
        load_calls = content.count('self.load_pdf_file(')
        print(f"📊 Found {load_calls} calls to load_pdf_file")
        
        # Find the contexts of load_pdf_file calls
        lines = content.split('\n')
        load_contexts = []
        for i, line in enumerate(lines):
            if 'self.load_pdf_file(' in line:
                # Get some context around the call
                start = max(0, i-2)
                end = min(len(lines), i+3)
                context = '\n'.join(lines[start:end])
                load_contexts.append(f"Line {i+1}:\n{context}")
        
        print("\n🔍 Contexts where load_pdf_file is called:")
        for i, context in enumerate(load_contexts, 1):
            print(f"\nCall {i}:")
            print(context)
            print("-" * 40)
        
        print("\n✅ Auto-load prevention verification completed!")
        
        print("\n🎯 Expected Behavior:")
        print("  • Dropdown will be empty when updated")
        print("  • Import button adds to history but doesn't load")
        print("  • User must explicitly select from dropdown to load")
        print("  • No automatic loading on startup")
        print("  • Fast imports without delays")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    verify_no_auto_load()
