#!/usr/bin/env python3
"""
CEF Python integration for HTML rendering in the PDF editor.
This provides a full Chrome-based browser widget for rendering HTML content.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk
import tempfile
import threading
import time

try:
    from cefpython3 import cefpython as cef
    CEF_AVAILABLE = True
except ImportError:
    CEF_AVAILABLE = False

class CEFBrowserFrame(ttk.Frame):
    """
    A Tkinter frame that embeds a CEF browser for HTML rendering.
    Provides full Chrome rendering capabilities within the editor.
    """
    
    def __init__(self, parent, html_content="", **kwargs):
        super().__init__(parent, **kwargs)
        
        self.parent = parent
        self.browser = None
        self.html_content = html_content
        self.temp_file = None
        
        if not CEF_AVAILABLE:
            self._create_fallback_widget()
            return
            
        try:
            self._initialize_cef()
            self._create_browser_widget()
        except Exception as e:
            print(f"CEF initialization failed: {e}")
            self._create_fallback_widget()
    
    def _initialize_cef(self):
        """Initialize CEF Python if not already done."""
        if hasattr(cef, '_initialized') and cef._initialized:
            return
            
        # CEF settings
        settings = {
            'debug': False,
            'log_severity': cef.LOGSEVERITY_INFO,
            'log_file': '',
            'multi_threaded_message_loop': False,
        }
        
        # Application settings
        app_settings = {
            'string_encoding': 'utf-8',
        }
        
        # Initialize CEF
        cef.Initialize(settings, app_settings)
        cef._initialized = True
    
    def _create_browser_widget(self):
        """Create the CEF browser widget."""
        # Create a temporary HTML file for the content
        self._create_temp_html_file()
        
        # Browser settings
        browser_settings = {
            'file_access_from_file_urls': True,
            'universal_access_from_file_urls': True,
        }
        
        # Window info for embedding in Tkinter
        window_info = cef.WindowInfo()
        window_info.SetAsChild(self.winfo_id())
        
        # Create browser
        self.browser = cef.CreateBrowserSync(
            window_info=window_info,
            url=f"file://{self.temp_file}",
            settings=browser_settings
        )
        
        # Bind resize event
        self.bind('<Configure>', self._on_configure)
        
        # Start CEF message loop in a separate thread
        self._start_message_loop()
    
    def _create_temp_html_file(self):
        """Create a temporary HTML file with the content."""
        if self.temp_file:
            try:
                os.unlink(self.temp_file)
            except:
                pass
                
        # Create temp file
        fd, self.temp_file = tempfile.mkstemp(suffix='.html', text=True)
        
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            if self.html_content:
                f.write(self.html_content)
            else:
                f.write(self._get_default_html())
    
    def _get_default_html(self):
        """Get default HTML content when none is provided."""
        return '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>CEF Browser</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            padding: 20px; 
            background: #f5f5f5; 
        }
        .placeholder {
            text-align: center;
            color: #666;
            margin-top: 50px;
        }
    </style>
</head>
<body>
    <div class="placeholder">
        <h2>CEF Browser Ready</h2>
        <p>Load HTML content to display here.</p>
    </div>
</body>
</html>'''
    
    def _start_message_loop(self):
        """Start the CEF message loop in a separate thread."""
        def message_loop():
            while True:
                try:
                    cef.MessageLoopWork()
                    time.sleep(0.01)  # 10ms delay
                except:
                    break
        
        self.message_thread = threading.Thread(target=message_loop, daemon=True)
        self.message_thread.start()
    
    def _on_configure(self, event):
        """Handle window resize events."""
        if self.browser and event.widget == self:
            # Resize browser to match frame
            self.browser.SetBounds(0, 0, event.width, event.height)
    
    def _create_fallback_widget(self):
        """Create a fallback widget when CEF is not available."""
        from tkinter import scrolledtext
        
        fallback_label = ttk.Label(
            self, 
            text="CEF Python not available\nFalling back to basic text display",
            justify="center"
        )
        fallback_label.pack(expand=True)
        
        self.text_widget = scrolledtext.ScrolledText(
            self, 
            wrap="word", 
            font=("Consolas", 10)
        )
        self.text_widget.pack(fill="both", expand=True)
        
        if self.html_content:
            self.text_widget.insert("1.0", self.html_content)
    
    def set_html(self, html_content):
        """Set new HTML content in the browser."""
        self.html_content = html_content
        
        if not CEF_AVAILABLE or not self.browser:
            # Update fallback widget
            if hasattr(self, 'text_widget'):
                self.text_widget.delete("1.0", "end")
                self.text_widget.insert("1.0", html_content)
            return
        
        # Update CEF browser
        self._create_temp_html_file()
        self.browser.LoadUrl(f"file://{self.temp_file}")
    
    def get_html(self):
        """Get current HTML content."""
        return self.html_content
    
    def reload(self):
        """Reload the browser content."""
        if self.browser:
            self.browser.Reload()
    
    def destroy(self):
        """Clean up resources."""
        if self.browser:
            self.browser.CloseBrowser(True)
            self.browser = None
        
        if self.temp_file:
            try:
                os.unlink(self.temp_file)
            except:
                pass
            self.temp_file = None
        
        super().destroy()

class CEFManager:
    """Singleton manager for CEF Python lifecycle."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def initialize(self):
        """Initialize CEF Python globally."""
        if self._initialized or not CEF_AVAILABLE:
            return
            
        try:
            settings = {
                'debug': False,
                'log_severity': cef.LOGSEVERITY_WARNING,
                'multi_threaded_message_loop': False,
            }
            
            cef.Initialize(settings)
            self._initialized = True
            print("CEF Python initialized successfully")
            
        except Exception as e:
            print(f"Failed to initialize CEF Python: {e}")
    
    def shutdown(self):
        """Shutdown CEF Python."""
        if self._initialized and CEF_AVAILABLE:
            try:
                cef.Shutdown()
                self._initialized = False
                print("CEF Python shut down")
            except Exception as e:
                print(f"Error shutting down CEF Python: {e}")
    
    def is_available(self):
        """Check if CEF Python is available and initialized."""
        return CEF_AVAILABLE and self._initialized

# Test function
def test_cef_integration():
    """Test CEF integration with a sample HTML."""
    print("Testing CEF Python Integration:")
    print("=" * 50)
    
    if not CEF_AVAILABLE:
        print("❌ CEF Python not available. Install with: pip install cefpython3")
        return False
    
    test_html = '''<!DOCTYPE html>
<html>
<head>
    <title>CEF Test</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: linear-gradient(45deg, #f0f8ff, #e6f3ff); }
        h1 { color: #2c5aa0; text-shadow: 1px 1px 2px #ccc; }
        .box { background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin: 10px 0; }
        button { background: #4CAF50; color: white; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background: #45a049; }
        table { border-collapse: collapse; width: 100%; margin: 10px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <h1>🌟 CEF Browser Test</h1>
    <div class="box">
        <h2>Modern CSS Features</h2>
        <p>This demonstrates CSS gradients, shadows, and animations that work in CEF but not in tkhtmlview.</p>
        <button onclick="changeColor()">Click me!</button>
    </div>
    
    <div class="box">
        <h2>Dynamic Table</h2>
        <table id="dataTable">
            <tr><th>Feature</th><th>Status</th></tr>
            <tr><td>CSS3 Support</td><td>✅ Full</td></tr>
            <tr><td>JavaScript</td><td>✅ Full</td></tr>
            <tr><td>Modern HTML5</td><td>✅ Full</td></tr>
        </table>
    </div>
    
    <script>
        function changeColor() {
            document.body.style.background = 'linear-gradient(45deg, #ffe6e6, #fff0e6)';
            
            // Add a new row to demonstrate JavaScript functionality
            const table = document.getElementById('dataTable');
            const newRow = table.insertRow();
            newRow.innerHTML = '<td>Button Clicked</td><td>✅ Working</td>';
        }
        
        // Add some animation
        document.addEventListener('DOMContentLoaded', function() {
            const boxes = document.querySelectorAll('.box');
            boxes.forEach((box, index) => {
                box.style.opacity = '0';
                box.style.transform = 'translateY(20px)';
                box.style.transition = 'all 0.5s ease';
                
                setTimeout(() => {
                    box.style.opacity = '1';
                    box.style.transform = 'translateY(0)';
                }, index * 200);
            });
        });
    </script>
</body>
</html>'''
    
    try:
        # Initialize CEF
        cef_manager = CEFManager()
        cef_manager.initialize()
        
        if not cef_manager.is_available():
            print("❌ CEF initialization failed")
            return False
        
        # Create test window
        root = tk.Tk()
        root.title("CEF Python Test")
        root.geometry("800x600")
        
        # Create CEF browser frame
        browser_frame = CEFBrowserFrame(root, html_content=test_html)
        browser_frame.pack(fill="both", expand=True)
        
        print("✅ CEF browser created successfully")
        print("🌐 Test window opened. Close it to continue...")
        
        # Run for a short time to test
        root.after(5000, root.quit)  # Auto-close after 5 seconds
        root.mainloop()
        
        # Cleanup
        browser_frame.destroy()
        root.destroy()
        cef_manager.shutdown()
        
        print("✅ CEF test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ CEF test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_cef_integration()
