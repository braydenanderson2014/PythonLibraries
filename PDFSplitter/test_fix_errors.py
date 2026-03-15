# test_fix_errors.py

import os
import sys
import tempfile
import importlib

# Add the parent directory to the path so we can import the necessary modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_test_files():
    """Create test HTML and Markdown files."""
    temp_dir = tempfile.mkdtemp()
    
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Test HTML File</title>
</head>
<body>
    <h1>Test HTML File</h1>
    <p>This is a test HTML file for renderer error fixes testing.</p>
</body>
</html>
"""

    md_content = """# Test Markdown File

This is a test Markdown file for renderer error fixes testing.

## Features

- Bold text: **bold**
- Italic text: *italic*
- Code: `code`
"""

    html_path = os.path.join(temp_dir, "test.html")
    md_path = os.path.join(temp_dir, "test.md")
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
        
    return temp_dir, html_path, md_path

def test_qapplication_initialization():
    """Test that QApplication initializes properly."""
    print("Testing QApplication Initialization")
    print("==================================")
    
    try:
        # Try to import PyQt
        from PyQt6.QtWidgets import QApplication
        print("✅ PyQt6 imported successfully")
        
        # Initialize QApplication with proper arguments
        import sys
        argv = sys.argv if len(sys.argv) > 0 else ["PDFSplitter"]
        app = QApplication(argv)
        
        print("✅ QApplication initialized successfully with argv:", argv)
        return True
        
    except Exception as e:
        print(f"❌ QApplication initialization failed: {e}")
        return False

def test_document_model():
    """Test that TextDocumentModel works properly."""
    print("\nTesting TextDocumentModel")
    print("=======================")
    
    try:
        # Import the TextDocumentModel
        from editor.text_document_model import TextDocumentModel
        print("✅ TextDocumentModel imported successfully")
        
        # Create test files
        temp_dir, html_path, md_path = create_test_files()
        
        # Create a TextDocumentModel for the HTML file
        html_model = TextDocumentModel(filepath=html_path)
        
        # Test content loading
        if html_model.content and "Test HTML File" in html_model.content:
            print("✅ TextDocumentModel loaded HTML content successfully")
        else:
            print("❌ TextDocumentModel failed to load HTML content")
            
        # Test setting content
        html_model.set_content("<h1>New content</h1>")
        if html_model.modified:
            print("✅ TextDocumentModel correctly marked as modified")
        else:
            print("❌ TextDocumentModel not marked as modified")
            
        # Test saving
        new_path = os.path.join(temp_dir, "new_test.html")
        html_model.save(outpath=new_path)
        
        if os.path.exists(new_path):
            with open(new_path, 'r', encoding='utf-8') as f:
                content = f.read()
            if content == "<h1>New content</h1>":
                print("✅ TextDocumentModel saved content successfully")
            else:
                print("❌ TextDocumentModel saved incorrect content")
        else:
            print("❌ TextDocumentModel failed to save content")
            
        # Clean up
        import shutil
        shutil.rmtree(temp_dir)
        
        return True
        
    except Exception as e:
        print(f"❌ TextDocumentModel test failed: {e}")
        return False

def test_pyqt_frame_helper():
    """Test PyQtWebFrame helper."""
    print("\nTesting PyQtWebFrame Helper")
    print("=========================")
    
    # Check for required packages
    missing_packages = []
    try:
        import tkinter
    except ImportError:
        missing_packages.append("tkinter")
    
    try:
        from PyQt6.QtWidgets import QApplication
    except ImportError:
        missing_packages.append("PyQt6")
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("⚠️ Skipping PyQtWebFrame test")
        print("  To run this test, install the missing packages:")
        
        if "PyQt6" in missing_packages:
            print("  - pip install PyQt6 PyQt6-WebEngine")
        
        if "tkinter" in missing_packages:
            print("  - tkinter is part of the standard library, but may require:")
            print("    - Windows: Installing Python with tkinter option")
            print("    - Linux: sudo apt-get install python3-tk")
            print("    - macOS: brew install python-tk")
        
        return False
    
    try:
        # Import the PyQtWebFrame
        from editor.renderers.pyqt_frame_helper import PyQtWebFrame, PYQT_AVAILABLE
        print(f"✅ PyQtWebFrame imported successfully (PyQt Available: {PYQT_AVAILABLE})")
        
        if not PYQT_AVAILABLE:
            print("⚠️ PyQt not available, skipping renderer test")
            return False
        
        # Test importing renderers
        from editor.renderers.pyqt_html_renderer.renderer import Renderer as HTMLRenderer
        print("✅ HTML Renderer imported successfully")
        
        from editor.renderers.pyqt_markdown_renderer.renderer import Renderer as MarkdownRenderer
        print("✅ Markdown Renderer imported successfully")
        
        # Check extensions
        html_exts = HTMLRenderer.extensions()
        md_exts = MarkdownRenderer.extensions()
        
        print(f"✅ HTML Renderer Extensions: {html_exts}")
        print(f"✅ Markdown Renderer Extensions: {md_exts}")
        
        # Create test files
        temp_dir, html_path, md_path = create_test_files()
        
        # Create a test tkinter window to test embedding
        import tkinter as tk
        root = tk.Tk()
        root.title("PyQt Embedding Test")
        root.geometry("800x600")
        
        # Create a frame to hold the PyQtWebFrame
        frame = tk.Frame(root)
        frame.pack(fill="both", expand=True)
        
        # Read test HTML content
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
            
        print("✅ Created test environment")
        
        # Create a PyQtWebFrame
        web_frame = PyQtWebFrame(frame, html_content=html_content)
        web_frame.pack(fill="both", expand=True)
        
        print("✅ Created PyQtWebFrame")
        
        # Test setting HTML
        web_frame.set_html("<h1>New content via set_html</h1>")
        
        print("✅ Set HTML content")
        
        # Add a button to close the test
        def close_test():
            root.destroy()
            
        close_button = tk.Button(root, text="Close Test", command=close_test)
        close_button.pack(pady=10)
        
        print("Opening test window - close it to continue")
        
        # Start the event loop
        root.after(5000, lambda: print("Still running... close the window to continue"))
        root.mainloop()
        
        print("✅ PyQtWebFrame test completed successfully")
        
        # Clean up
        import shutil
        shutil.rmtree(temp_dir)
        
        return True
        
    except Exception as e:
        print(f"❌ PyQtWebFrame test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Get Python version
    py_version = sys.version_info
    print(f"Python version: {py_version.major}.{py_version.minor}.{py_version.micro}")
    
    # Run the tests
    test_qapplication_initialization()
    test_document_model()
    
    # Run PyQt tests if user confirms
    if input("\nRun PyQt embedding test (requires GUI interaction)? (y/n): ").lower().strip() == 'y':
        test_pyqt_frame_helper()
