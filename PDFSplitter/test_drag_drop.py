#!/usr/bin/env python3
"""
Test script for drag and drop functionality.
Run this to diagnose drag and drop issues.
"""

import sys
import traceback

def test_tkinterdnd2_import():
    """Test if tkinterdnd2 can be imported and used."""
    print("=== Testing tkinterdnd2 Import ===")
    
    try:
        import tkinterdnd2
        print(f"✓ tkinterdnd2 imported successfully")
        print(f"  Version: {getattr(tkinterdnd2, '__version__', 'unknown')}")
        print(f"  Location: {tkinterdnd2.__file__}")
        
        # Test TkinterDnD class
        if hasattr(tkinterdnd2, 'TkinterDnD'):
            print(f"✓ TkinterDnD class available")
        else:
            print(f"✗ TkinterDnD class NOT available")
            
        # Test DND_FILES constant
        if hasattr(tkinterdnd2, 'DND_FILES'):
            print(f"✓ DND_FILES constant available: {tkinterdnd2.DND_FILES}")
        else:
            print(f"✗ DND_FILES constant NOT available")
            
        return True
        
    except ImportError as e:
        print(f"✗ Failed to import tkinterdnd2: {e}")
        print("  Try installing: pip install tkinterdnd2")
        return False
    except Exception as e:
        print(f"✗ Unexpected error importing tkinterdnd2: {e}")
        traceback.print_exc()
        return False

def test_tkinter_dnd_window():
    """Test if TkinterDnD window can be created."""
    print("\n=== Testing TkinterDnD Window Creation ===")
    
    try:
        from tkinterdnd2 import TkinterDnD, DND_FILES
        
        # Create a simple DnD window
        root = TkinterDnD.Tk()
        root.title("Drag & Drop Test")
        root.geometry("400x300")
        
        print("✓ TkinterDnD.Tk window created successfully")
        
        # Test if we can create a widget and register for drops
        import tkinter as tk
        listbox = tk.Listbox(root)
        listbox.pack(fill='both', expand=True)
        
        # Test drop target registration
        listbox.drop_target_register(DND_FILES)
        print("✓ Drop target registered successfully")
        
        def handle_drop(event):
            print(f"Drop event received: {event.data}")
            
        listbox.dnd_bind('<<Drop>>', handle_drop)
        print("✓ Drop event bound successfully")
        
        # Add instructions
        label = tk.Label(root, text="Drag and drop files here to test")
        label.pack(pady=10)
        
        print("✓ Test window ready - try dragging files to it")
        print("  Close the window to continue...")
        
        root.mainloop()
        return True
        
    except Exception as e:
        print(f"✗ Failed to create TkinterDnD window: {e}")
        traceback.print_exc()
        return False

def test_ttkbootstrap_integration():
    """Test if ttkbootstrap and TkinterDnD can work together."""
    print("\n=== Testing ttkbootstrap + TkinterDnD Integration ===")
    
    try:
        from tkinterdnd2 import TkinterDnD, DND_FILES
        import ttkbootstrap as ttk
        from ttkbootstrap import Window
        
        # Try the combined approach
        class TestDnDWindow(TkinterDnD.Tk, Window):
            def __init__(self, *args, **kwargs):
                TkinterDnD.Tk.__init__(self)
                # Skip Window.__init__ to avoid double Tk initialization
                super(TkinterDnD.Tk, self).__init__(*args, **kwargs)
        
        root = TestDnDWindow(themename="darkly")
        root.title("ttkbootstrap + DnD Test")
        root.geometry("400x300")
        
        print("✓ Combined TkinterDnD + ttkbootstrap window created")
        
        # Test themed widgets with DnD
        import tkinter as tk
        listbox = tk.Listbox(root)
        listbox.pack(fill='both', expand=True, padx=10, pady=10)
        
        listbox.drop_target_register(DND_FILES)
        
        def handle_drop(event):
            files = root.tk.splitlist(event.data)
            print(f"Dropped files: {files}")
            for file in files:
                listbox.insert(tk.END, file)
                
        listbox.dnd_bind('<<Drop>>', handle_drop)
        
        label = ttk.Label(root, text="Drag files here (themed with ttkbootstrap)")
        label.pack(pady=5)
        
        print("✓ Integration test ready - try dragging files")
        print("  Close the window to continue...")
        
        root.mainloop()
        return True
        
    except Exception as e:
        print(f"✗ Failed integration test: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all drag and drop tests."""
    print("Drag & Drop Diagnostics")
    print("=" * 50)
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    print()
    
    # Test 1: Import
    import_ok = test_tkinterdnd2_import()
    
    if not import_ok:
        print("\n❌ Cannot continue - tkinterdnd2 import failed")
        return
    
    # Test 2: Basic DnD window
    try:
        basic_ok = test_tkinter_dnd_window()
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        basic_ok = True
    
    # Test 3: Integration with ttkbootstrap
    if basic_ok:
        try:
            integration_ok = test_ttkbootstrap_integration()
        except KeyboardInterrupt:
            print("\n⚠️  Test interrupted by user")
            integration_ok = True
    else:
        print("\n⏭️  Skipping integration test due to basic test failure")
        integration_ok = False
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY:")
    print(f"  Import test: {'✓' if import_ok else '✗'}")
    print(f"  Basic DnD:   {'✓' if basic_ok else '✗'}")
    print(f"  Integration: {'✓' if integration_ok else '✗'}")
    print()
    
    if import_ok and basic_ok and integration_ok:
        print("🎉 All tests passed! Drag & drop should work.")
    else:
        print("❌ Some tests failed. Check the output above for details.")
        print("\nCommon solutions:")
        print("  - Install tkinterdnd2: pip install tkinterdnd2")
        print("  - Try a different version: pip install tkinterdnd2==0.3.0")
        print("  - Check if you're in a virtual environment")
        print("  - Restart your Python interpreter")

if __name__ == "__main__":
    main()
