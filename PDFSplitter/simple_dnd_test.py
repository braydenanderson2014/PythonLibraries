#!/usr/bin/env python3
"""Simple tkinterdnd2 test"""

try:
    import tkinterdnd2
    print("SUCCESS: tkinterdnd2 imported")
    
    # Check what's available
    attrs = [attr for attr in dir(tkinterdnd2) if not attr.startswith('_')]
    print(f"Available attributes: {attrs}")
    
    # Test specific imports
    try:
        from tkinterdnd2 import TkinterDnD
        print("SUCCESS: TkinterDnD imported")
    except ImportError as e:
        print(f"FAILED: TkinterDnD import - {e}")
    
    try:
        from tkinterdnd2 import DND_FILES
        print(f"SUCCESS: DND_FILES imported - {DND_FILES}")
    except ImportError as e:
        print(f"FAILED: DND_FILES import - {e}")
        
    # Try to create a window
    try:
        root = TkinterDnD.Tk()
        print("SUCCESS: TkinterDnD.Tk() created")
        root.withdraw()  # Hide the window
        root.destroy()
    except Exception as e:
        print(f"FAILED: TkinterDnD.Tk() creation - {e}")
        
except ImportError as e:
    print(f"FAILED: tkinterdnd2 import - {e}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

print("Test complete")
