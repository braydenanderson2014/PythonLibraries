#!/usr/bin/env python3
"""
Test script to verify PyQt6 and QWebEngine installation and compatibility with the system.
Run this before using the PyQt WebEngine renderers to verify that everything is working properly.
"""

import os
import sys
import platform
import tkinter as tk
from tkinter import messagebox

def check_pyqt_available():
    """Check if PyQt6 is available."""
    try:
        import PyQt6
        return True, PyQt6.__version__
    except ImportError:
        return False, None
    except Exception as e:
        return False, str(e)

def check_webengine_available():
    """Check if PyQtWebEngine is available."""
    try:
        from PyQt6 import QtWebEngineWidgets
        return True, "Available"
    except ImportError:
        return False, None
    except Exception as e:
        return False, str(e)

def get_system_info():
    """Get system information."""
    return {
        "System": platform.system(),
        "Release": platform.release(),
        "Version": platform.version(),
        "Architecture": platform.architecture(),
        "Machine": platform.machine(),
        "Processor": platform.processor(),
        "Python": platform.python_version(),
    }

def main():
    """Main function."""
    print("PyQt6 WebEngine Installation Test")
    print("=================================")
    
    # Check if PyQt6 is available
    pyqt_available, pyqt_version = check_pyqt_available()
    
    if pyqt_available:
        print("✅ PyQt6 is installed!")
        print(f"Version: {pyqt_version}")
    else:
        print("❌ PyQt6 is not installed!")
        print("\nTo install PyQt6, run the following command:")
        print("  pip install PyQt6")
        
        # Show a message box
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "PyQt6 Not Installed",
            "PyQt6 is not installed. Please install it with:\n\npip install PyQt6"
        )
        root.destroy()
        return
    
    # Check if QWebEngine is available
    webengine_available, webengine_version = check_webengine_available()
    
    if webengine_available:
        print("✅ QWebEngine is available!")
    else:
        print("❌ QWebEngine is not available!")
        print("\nTo install QWebEngine, run the following command:")
        print("  pip install PyQt6-WebEngine")
        
        # Show a message box
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "QWebEngine Not Installed",
            "QWebEngine is not installed. Please install it with:\n\npip install PyQt6-WebEngine"
        )
        root.destroy()
        return
    
    # Print system information
    print("\nSystem Information:")
    sys_info = get_system_info()
    for key, value in sys_info.items():
        print(f"  {key}: {value}")
    
    # Test WebEngine by creating a simple browser
    print("\nTesting QWebEngine by creating a sample browser...")
    try:
        import sys
        from PyQt6.QtCore import QUrl, QTimer
        from PyQt6.QtWidgets import QApplication, QMainWindow
        from PyQt6.QtWebEngineWidgets import QWebEngineView
        
        app = QApplication([])
        
        # Create a window with a web view
        window = QMainWindow()
        window.setWindowTitle("QWebEngine Test")
        window.setGeometry(100, 100, 800, 600)
        
        # Create web view and load a test page
        web_view = QWebEngineView()
        web_view.setHtml("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>QWebEngine Test</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    background: linear-gradient(45deg, #f0f8ff, #e6f3ff);
                    text-align: center;
                }
                h1 { 
                    color: #2c5aa0; 
                    text-shadow: 1px 1px 2px #ccc;
                    animation: fadeIn 1s ease;
                }
                @keyframes fadeIn {
                    from { opacity: 0; }
                    to { opacity: 1; }
                }
                .test-box {
                    background: white;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    padding: 20px;
                    margin: 20px auto;
                    max-width: 500px;
                }
                button {
                    background: #4CAF50;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 4px;
                    cursor: pointer;
                }
                button:hover {
                    background: #45a049;
                }
            </style>
        </head>
        <body>
            <h1>QWebEngine Test</h1>
            <div class="test-box">
                <h2>✅ QWebEngine is working correctly!</h2>
                <p>This window demonstrates that QWebEngine is properly installed and can render HTML content with CSS and JavaScript.</p>
                <button id="testBtn">Click me!</button>
            </div>
            
            <script>
                document.getElementById('testBtn').addEventListener('click', function() {
                    this.textContent = 'JavaScript Works!';
                    document.querySelector('.test-box').style.background = '#f5fff5';
                });
                
                // Add animated elements
                const box = document.createElement('div');
                box.className = 'test-box';
                box.innerHTML = '<h3>Dynamic Content</h3><p>This content was added dynamically with JavaScript.</p>';
                box.style.animation = 'fadeIn 1s ease';
                document.body.appendChild(box);
            </script>
        </body>
        </html>
        """)
        window.setCentralWidget(web_view)
        
        # Show the window
        window.show()
        print("✅ QWebEngine window created successfully!")
        
        # Auto-close after 5 seconds
        QTimer.singleShot(5000, app.quit)
        
        # Start the application event loop
        app.exec()
        
        print("✅ QWebEngine test completed successfully!")
    except Exception as e:
        print(f"❌ QWebEngine test failed: {e}")
        import traceback
        traceback.print_exc()
        
        # Show a message box
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "QWebEngine Test Failed",
            f"QWebEngine test failed with error:\n\n{e}\n\n"
            "Check the console for more details."
        )
        root.destroy()
        return
    
    # All tests passed
    print("\n✅ All tests passed! PyQt6 with QWebEngine is ready to use.")
    
    # Show a message box
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo(
        "PyQt6 WebEngine Ready",
        "PyQt6 with QWebEngine is installed and working correctly.\n\n"
        "You can now use the QWebEngine-based renderers for HTML and Markdown files."
    )
    root.destroy()

if __name__ == "__main__":
    main()
