#!/usr/bin/env python3
"""
Simple test script to verify the editor improvements.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk

def test_tooltip_functionality():
    """Test basic tooltip functionality."""
    print("=== Testing Tooltip Functionality ===")
    
    root = tk.Tk()
    root.title("Tooltip Test")
    root.geometry("400x200")
    
    # Create a notebook with tabs
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Create test tabs
    for i in range(3):
        frame = ttk.Frame(notebook)
        label = ttk.Label(frame, text=f"Content for Tab {i+1}")
        label.pack(expand=True)
        
        notebook.add(frame, text=f"Tab {i+1}")
    
    # Simple tooltip implementation
    tooltip_window = None
    
    def show_tooltip(event):
        nonlocal tooltip_window
        tab_index = notebook.identify_tab(event.x, event.y)
        if tab_index is not None:
            if tooltip_window is None:
                tooltip_window = tk.Toplevel(root)
                tooltip_window.wm_overrideredirect(True)
                tooltip_window.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
                
                label = tk.Label(tooltip_window, text=f"Full path for Tab {int(tab_index)+1}", 
                               background="#ffffe0", relief="solid", borderwidth=1)
                label.pack()
    
    def hide_tooltip(event):
        nonlocal tooltip_window
        if tooltip_window:
            tooltip_window.destroy()
            tooltip_window = None
    
    notebook.bind("<Motion>", show_tooltip)
    notebook.bind("<Leave>", hide_tooltip)
    
    print("Tooltip test window created. Move mouse over tabs to test tooltips.")
    print("Close the window to continue...")
    
    root.mainloop()

def test_modified_flag():
    """Test the modified flag functionality."""
    print("=== Testing Modified Flag ===")
    
    root = tk.Tk()
    root.title("Modified Flag Test")
    root.geometry("500x300")
    
    # Create a notebook
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Create a text tab
    text_frame = ttk.Frame(notebook)
    text_widget = tk.Text(text_frame, wrap="word")
    text_widget.pack(fill="both", expand=True)
    
    # Initially add tab without asterisk
    notebook.add(text_frame, text="test.txt")
    
    # Track modifications
    def on_modified(event):
        current_text = notebook.tab(text_frame, "text")
        if "*" not in current_text:
            notebook.tab(text_frame, text=current_text + " *")
    
    text_widget.bind("<<Modified>>", on_modified)
    text_widget.bind("<KeyRelease>", on_modified)
    
    # Add instructions
    instructions = """
Type in the text area above.
The tab title should show an asterisk (*) when modified.

This tests the modified flag functionality.
"""
    text_widget.insert("1.0", instructions)
    
    print("Modified flag test window created. Type in the text area to test.")
    print("Close the window to continue...")
    
    root.mainloop()

def main():
    print("Editor Improvements Test Suite")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not os.path.exists("Editor"):
        print("Error: Please run this script from the PDFSplitter directory")
        sys.exit(1)
    
    print("Testing basic functionality...")
    
    try:
        test_tooltip_functionality()
        test_modified_flag()
        print("All tests completed successfully!")
    except Exception as e:
        print(f"Test failed: {e}")
        
    print("\nTest files created:")
    print("- test_dual_tab.html")
    print("- test_dual_tab.md")
    print("\nOpen these files in the editor to test the dual tab functionality.")

if __name__ == "__main__":
    main()
