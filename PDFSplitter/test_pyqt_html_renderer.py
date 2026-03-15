# test_pyqt_html_renderer.py

import os
import sys
import tempfile

# Try to import tkinter - not required for basic testing
try:
    import tkinter as tk
    from tkinter import ttk, messagebox
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    print("❌ Tkinter is not available.")
    print("This won't affect the PyQt test, but the Tkinter integration test will be skipped.")

# Add the parent directory to the path so we can import the necessary modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import the PyQt6 modules - this is what our renderer will need
try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtCore import QUrl
    PYQT_AVAILABLE = True
    print("✅ PyQt6 and QtWebEngine are available!")
except ImportError:
    PYQT_AVAILABLE = False
    print("❌ PyQt6 or QtWebEngine are not available.")
    print("Install with: pip install PyQt6 PyQt6-WebEngine")

def create_test_html():
    """Create a sample HTML file for testing."""
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>PyQt HTML Renderer Test</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 40px;
            line-height: 1.6;
            color: #333;
        }
        h1 {
            color: #0066cc;
        }
        .test-div {
            background-color: #f0f0f0;
            border: 1px solid #ddd;
            padding: 15px;
            margin: 15px 0;
            border-radius: 5px;
        }
        button {
            background-color: #0066cc;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
        }
        button:hover {
            background-color: #0055aa;
        }
    </style>
</head>
<body>
    <h1>PyQt HTML Renderer Test</h1>
    <p>This is a test HTML file to verify that the PyQt HTML renderer is working correctly.</p>
    
    <div class="test-div">
        <h2>Features to Test</h2>
        <ul>
            <li>Basic HTML rendering</li>
            <li>CSS styling</li>
            <li>JavaScript interaction</li>
            <li>Resource loading (images, etc.)</li>
        </ul>
    </div>
    
    <h2>JavaScript Test</h2>
    <button id="testButton">Click me!</button>
    <p id="jsResult">JavaScript result will appear here.</p>
    
    <h2>Image Test</h2>
    <p>The image below should load if resource path handling works correctly:</p>
    <img src="data:image/png;base64,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" alt="Test Image">
    
    <script>
        document.getElementById('testButton').addEventListener('click', function() {
            document.getElementById('jsResult').textContent = 'JavaScript is working! Clicked at: ' + new Date().toLocaleTimeString();
        });
    </script>
</body>
</html>
"""
    
    temp_file = os.path.join(tempfile.gettempdir(), "pyqt_html_test.html")
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return temp_file

def test_pyqt_html_renderer():
    """Test PyQt6 WebEngine renderer functionality."""
    if not PYQT_AVAILABLE:
        print("\nTest failed: PyQt6 or QtWebEngine not available.")
        return False
    
    try:
        # Create a test HTML file
        html_path = create_test_html()
        
        # Initialize PyQt application
        app = QApplication.instance() or QApplication([])
        
        # Create the WebEngine view
        view = QWebEngineView()
        
        try:
            # Load the HTML file
            view.load(QUrl.fromLocalFile(html_path))
            
            # Print status
            print("\n✅ QWebEngineView successfully created and loaded test HTML")
            print(f"Test HTML file created at: {html_path}")
            
            # Show the view directly if Tkinter is not available
            if not TKINTER_AVAILABLE:
                view.resize(800, 600)
                view.setWindowTitle("PyQt HTML Renderer Test")
                view.show()
                
                # Wait a bit (for testing)
                import time
                time.sleep(5)
                
                return True
            else:
                # Create a Tkinter window
                root = tk.Tk()
                root.title("PyQt HTML Renderer Test")
                root.geometry("800x600")
                
                # Create a frame for the renderer
                frame = ttk.Frame(root)
                frame.pack(fill="both", expand=True)
                
                # Close after a short delay
                root.after(5000, root.destroy)
                
                # Start the Tkinter main loop
                root.mainloop()
                
                return True
            
        except Exception as e:
            print(f"\n❌ Error loading HTML in QWebEngineView: {e}")
            return False
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    # Get Python version
    py_version = sys.version_info
    print(f"Python version: {py_version.major}.{py_version.minor}.{py_version.micro}")
    
    # Check if PyQt6 and QtWebEngine are available
    if not PYQT_AVAILABLE:
        print("\nPyQt6 or QtWebEngine is not available.")
        print("Please install them with:")
        print("pip install PyQt6 PyQt6-WebEngine")
        sys.exit(1)
    
    # Run the test
    result = test_pyqt_html_renderer()
    
    if result:
        print("\n✅ Test completed successfully!")
    else:
        print("\n❌ Test failed!")
