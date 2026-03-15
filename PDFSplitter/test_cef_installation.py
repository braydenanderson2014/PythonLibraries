#!/usr/bin/env python3
"""
Test script to verify CEF Python installation and compatibility with the system.
Run this before using the CEF renderers to verify that CEF is working properly.
"""

import os
import sys
import platform
import tkinter as tk
from tkinter import messagebox

def check_cef_available():
    """Check if cefpython3 is available."""
    try:
        import cefpython3
        return True, cefpython3.__version__
    except ImportError:
        return False, None
    except Exception as e:
        # Check if the error is related to Python version compatibility
        if "No module named" in str(e) and "cefpython3" in str(e):
            return False, f"Import error: {str(e)}. CEF Python may not support Python {platform.python_version()}."
        return False, str(e)



def check_python_compatibility():
    """Check if the current Python version is compatible with cefpython3."""
    python_version = sys.version_info
    
    # cefpython3 is typically compatible with Python up to 3.9
    if python_version.major == 3 and python_version.minor > 9:
        return False, f"Python {python_version.major}.{python_version.minor}.{python_version.micro} is not supported by cefpython3. Use Python 3.9 or lower."
    
    return True, None

def main():
    """Main function."""
    print("CEF Python Installation Test")
    print("===========================")
    
    # Check Python compatibility first
    python_compatible, error_msg = check_python_compatibility()
    if not python_compatible:
        print(f"❌ {error_msg}")
        print("\nYou have several options:")
        print("  1. Use a lower Python version (3.9 or below)")
        print("  2. Look for alternative HTML rendering solutions")
        print("  3. Check if there are newer unofficial builds of cefpython for Python 3.13")
        
        # Show alternatives
        suggest_alternatives()
        
        # Show a message box
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Python Version Incompatible",
            f"{error_msg}\n\nCEF Python typically supports Python versions up to 3.9.\n\n"
            f"See console for alternative solutions."
        )
        root.destroy()
        return
    
    # Check if CEF is available
    cef_available, version = check_cef_available()
    
    if cef_available:
        print("✅ CEF Python is installed!")
        print(f"Version: {version}")
    else:
        print("❌ CEF Python is not installed!")
        if version:
            print(f"Error: {version}")
        print("\nTo install CEF Python, run one of the following commands:")
        print("  pip install cefpython3")
        print("  conda install -c conda-forge cefpython3")
        
        # Show a message box
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "CEF Python Not Installed",
            "CEF Python is not installed. Please install it with:\n\npip install cefpython3\n\n"
            "or\n\nconda install -c conda-forge cefpython3"
        )
        root.destroy()
        return
    
    # Print system information
    print("\nSystem Information:")
    sys_info = get_system_info()
    for key, value in sys_info.items():
        print(f"  {key}: {value}")
    
    # Test CEF initialization
    print("\nTesting CEF initialization...")
    try:
        import cefpython3 as cef
        settings = {
            "debug": True,
            "log_severity": cef.LOGSEVERITY_INFO,
            "log_file": "cef_debug.log",
        }
        cef.Initialize(settings)
        print("✅ CEF initialized successfully!")
        
        # Clean up
        cef.Shutdown()
        print("✅ CEF shutdown successfully!")
    except Exception as e:
        print(f"❌ CEF initialization failed: {e}")
        
        # Show a message box
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "CEF Initialization Failed",
            f"CEF initialization failed with error:\n\n{e}\n\n"
            "Check the console for more details."
        )
        root.destroy()
        return
    
    # All tests passed
    print("\n✅ All tests passed! CEF Python is ready to use.")
    
    # Show a message box
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo(
        "CEF Python Ready",
        "CEF Python is installed and working correctly.\n\n"
        "You can now use the CEF-based renderers for HTML and Markdown files."
    )
    root.destroy()

def suggest_alternatives():
    """Print suggested alternatives to CEF for newer Python versions."""
    print("\n🔍 Alternative HTML/Markdown Rendering Options for Python 3.10+:")
    print("\n1. PyWebview (https://pywebview.flowrl.com/)")
    print("   - Modern web UI toolkit that allows displaying HTML content")
    print("   - Compatible with newer Python versions")
    print("   - Installation: pip install pywebview")
    
    print("\n2. QWebEngine with PyQt6/PySide6")
    print("   - Chromium-based web engine included with PyQt6/PySide6")
    print("   - Full support for modern HTML5, CSS3, JavaScript")
    print("   - Installation: pip install PyQt6 PyQtWebEngine")
    
    print("\n3. WebKit (wxPython)")
    print("   - WebKit integration in wxPython")
    print("   - Installation: pip install wxPython")
    
    print("\n4. Python Virtual Environment with Python 3.9")
    print("   - Create a separate virtual environment with Python 3.9")
    print("   - Install cefpython3 within that environment")
    print("   - Example:")
    print("     python -m venv py39env --python=python3.9")
    print("     py39env\\Scripts\\activate")
    print("     pip install cefpython3")

if __name__ == "__main__":
    main()
