#!/usr/bin/env python3

import os
import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk

# Adjust the import path to find the module
current_dir = Path(__file__).parent.absolute()
project_root = current_dir.parent.parent  # This should be the PDFSplitter root
sys.path.insert(0, str(project_root))

try:
    from editor.renderers.pyqt_frame_helper import PyQtWebFrame, PYQT_AVAILABLE
    print("Successfully imported PyQtWebFrame module.")
except ImportError:
    print("Failed to import PyQtWebFrame. Make sure the module exists and is in the correct location.")
    # Falling back to direct import
    current_file = Path(__file__).resolve()
    helper_file = current_file.parent / "pyqt_frame_helper.py"
    
    if helper_file.exists():
        print(f"Found helper file at {helper_file}")
        # Use importlib to import the module directly
        import importlib.util
        spec = importlib.util.spec_from_file_location("pyqt_frame_helper", helper_file)
        if spec:
            pyqt_frame_helper = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(pyqt_frame_helper)
            PyQtWebFrame = pyqt_frame_helper.PyQtWebFrame
            PYQT_AVAILABLE = pyqt_frame_helper.PYQT_AVAILABLE
            print("Successfully imported PyQtWebFrame from local file.")
        else:
            print("Failed to create spec for PyQtWebFrame module.")
            sys.exit(1)
    else:
        print(f"Cannot find helper file at {helper_file}")
        sys.exit(1)

class TestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PyQtWebFrame Test")
        self.root.geometry("800x600")
        
        # Create a frame
        frame = ttk.Frame(root)
        frame.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Add a label
        label = ttk.Label(frame, text="Testing PyQtWebFrame")
        label.pack(pady=10)
        
        # Create tabs
        notebook = ttk.Notebook(frame)
        notebook.pack(expand=True, fill="both")
        
        # Tab 1: Simple HTML
        tab1 = ttk.Frame(notebook)
        notebook.add(tab1, text="Simple HTML")
        
        # Add PyQtWebFrame to tab1
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test HTML</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 20px;
                }
                h1 {
                    color: #2c3e50;
                }
                p {
                    line-height: 1.6;
                }
                .highlight {
                    background-color: #f1c40f;
                    padding: 5px;
                }
            </style>
        </head>
        <body>
            <h1>Hello from PyQt WebEngine</h1>
            <p>This is a test of the PyQtWebFrame class using the new approach with a separate window.</p>
            <p>The content is rendered using <span class="highlight">PyQt6 WebEngine</span> for optimal rendering quality.</p>
            <p>Click the "Show Preview" button to view this content in a standalone window.</p>
        </body>
        </html>
        """
        self.frame1 = PyQtWebFrame(tab1, html_content=html_content)
        self.frame1.pack(expand=True, fill="both")
        
        # Tab 2: URL loading
        tab2 = ttk.Frame(notebook)
        notebook.add(tab2, text="URL Test")
        
        # Add PyQtWebFrame to tab2
        self.frame2 = PyQtWebFrame(tab2)
        self.frame2.pack(expand=True, fill="both")
        
        # Add a button to load a URL
        button = ttk.Button(tab2, text="Load Example URL", 
                           command=lambda: self.frame2.load_url("https://example.com"))
        button.pack(pady=10)
        
        # Status label
        status = "PyQt WebEngine is available" if PYQT_AVAILABLE else "PyQt WebEngine is NOT available"
        self.status_label = ttk.Label(frame, text=f"Status: {status}")
        self.status_label.pack(pady=5)
        
        # Add a quit button
        quit_button = ttk.Button(frame, text="Quit", command=root.quit)
        quit_button.pack(pady=10)

def main():
    print(f"Python version: {sys.version}")
    print(f"Tkinter version: {tk.TkVersion}")
    print(f"PyQt available: {PYQT_AVAILABLE}")
    
    root = tk.Tk()
    app = TestApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
