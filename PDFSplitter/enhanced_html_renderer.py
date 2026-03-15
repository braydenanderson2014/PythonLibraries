#!/usr/bin/env python3
"""
Enhanced HTML renderer using CEF Python for better rendering capabilities.
Falls back to existing tkhtmlview/text widget approach if CEF is not available.
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

try:
    from cef_browser_widget import CEFBrowserFrame, CEFManager, CEF_AVAILABLE
except ImportError:
    CEF_AVAILABLE = False

class EnhancedHTMLRenderer:
    """
    Enhanced HTML renderer with CEF Python support.
    Provides full Chrome-based rendering when available.
    """
    
    def __init__(self, editor, logger):
        self.editor = editor
        self.logger = logger
        self.cef_manager = None
        
        if CEF_AVAILABLE:
            self.cef_manager = CEFManager()
            self.cef_manager.initialize()
            self.logger.info("HTMLRenderer", "CEF Python available - using Chrome rendering engine")
        else:
            self.logger.info("HTMLRenderer", "CEF Python not available - using fallback rendering")
    
    def create_preview_widget(self, parent_frame, html_content, file_path=None):
        """
        Create an HTML preview widget using the best available renderer.
        
        Args:
            parent_frame: The tkinter frame to contain the widget
            html_content: The HTML content to display
            file_path: Optional file path for relative resource resolution
            
        Returns:
            The created widget instance
        """
        
        if CEF_AVAILABLE and self.cef_manager and self.cef_manager.is_available():
            return self._create_cef_widget(parent_frame, html_content, file_path)
        else:
            return self._create_fallback_widget(parent_frame, html_content, file_path)
    
    def _create_cef_widget(self, parent_frame, html_content, file_path=None):
        """Create CEF-based HTML widget."""
        try:
            # Process HTML content with interceptors for local resources
            if file_path:
                processed_content = self._process_html_content(html_content, file_path)
            else:
                processed_content = html_content
            
            # Create CEF browser frame
            cef_widget = CEFBrowserFrame(parent_frame, html_content=processed_content)
            cef_widget.pack(fill="both", expand=True)
            
            self.logger.info("HTMLRenderer", "Created CEF browser widget")
            return cef_widget
            
        except Exception as e:
            self.logger.error("HTMLRenderer", f"Failed to create CEF widget: {e}")
            return self._create_fallback_widget(parent_frame, html_content, file_path)
    
    def _create_fallback_widget(self, parent_frame, html_content, file_path=None):
        """Create fallback HTML widget using tkhtmlview or text."""
        try:
            # Try tkhtmlview first
            from tkhtmlview import HTMLScrolledText
            
            if file_path:
                processed_content = self._process_html_content(html_content, file_path)
            else:
                processed_content = html_content
            
            widget = HTMLScrolledText(parent_frame, html=processed_content)
            widget.pack(fill="both", expand=True)
            
            self.logger.info("HTMLRenderer", "Created tkhtmlview widget")
            return widget
            
        except ImportError:
            # Final fallback to enhanced text widget
            return self._create_text_fallback(parent_frame, html_content)
    
    def _create_text_fallback(self, parent_frame, html_content):
        """Create enhanced text widget fallback."""
        from tkinter import scrolledtext
        
        # Create scrolled text widget
        text_widget = scrolledtext.ScrolledText(
            parent_frame,
            wrap="word",
            font=("Consolas", 10),
            bg="#ffffff",
            fg="#000000"
        )
        text_widget.pack(fill="both", expand=True)
        
        # Format HTML content for better readability
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            title = soup.find('title')
            title_text = title.get_text() if title else "HTML Document"
            
            body = soup.find('body')
            if body:
                formatted_text = self._format_html_for_text(body)
            else:
                formatted_text = soup.get_text()
            
            text_widget.insert("1.0", f"=== {title_text} ===\n\n{formatted_text}")
            
        except ImportError:
            # If BeautifulSoup not available, just show raw HTML
            text_widget.insert("1.0", html_content)
        
        text_widget.config(state="disabled")
        self.logger.info("HTMLRenderer", "Created enhanced text fallback widget")
        return text_widget
    
    def _process_html_content(self, html_content, file_path):
        """Process HTML content with CSS and JavaScript interceptors."""
        try:
            # Import interceptors (assuming they exist)
            from Editor.renderers.html_renderer.css_interceptor import CSSInterceptor
            from Editor.renderers.html_renderer.java_script_interceptor import JavaScriptInterceptor
            
            base_dir = os.path.dirname(file_path) if file_path else os.getcwd()
            
            # Process CSS
            css_processor = CSSInterceptor(html_content, base_path=base_dir)
            processed_content = css_processor.inline_css()
            
            # Process JavaScript (for CEF, we can allow more JS than for tkhtmlview)
            if CEF_AVAILABLE:
                # For CEF, we can be more permissive with JavaScript
                js_processor = JavaScriptInterceptor(processed_content)
                processed_content = js_processor.safe_scripts()
            else:
                # For fallback widgets, be more restrictive
                js_processor = JavaScriptInterceptor(processed_content)
                processed_content = js_processor.safe_scripts()
            
            return processed_content
            
        except ImportError:
            # If interceptors not available, return original content
            self.logger.warning("HTMLRenderer", "CSS/JS interceptors not available")
            return html_content
        except Exception as e:
            self.logger.error("HTMLRenderer", f"Error processing HTML content: {e}")
            return html_content
    
    def _format_html_for_text(self, soup):
        """Format HTML content for text widget display."""
        formatted_lines = []
        
        for element in soup.recursiveChildGenerator():
            if hasattr(element, 'name'):
                tag = element.name
                if tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    text = element.get_text().strip()
                    if text:
                        level = int(tag[1])
                        prefix = '=' * (7 - level)
                        formatted_lines.append(f"\n{prefix} {text} {prefix}\n")
                elif tag == 'p':
                    text = element.get_text().strip()
                    if text:
                        formatted_lines.append(f"{text}\n")
                elif tag == 'li':
                    text = element.get_text().strip()
                    if text:
                        formatted_lines.append(f"• {text}")
                elif tag == 'table':
                    # Format tables
                    rows = element.find_all('tr')
                    if rows:
                        formatted_lines.append("\n--- Table ---")
                        for row in rows:
                            cells = row.find_all(['td', 'th'])
                            if cells:
                                row_text = " | ".join(cell.get_text().strip() for cell in cells)
                                formatted_lines.append(row_text)
                        formatted_lines.append("--- End Table ---\n")
        
        return '\n'.join(formatted_lines)
    
    def update_widget_content(self, widget, html_content, file_path=None):
        """Update the content of an HTML widget."""
        try:
            if hasattr(widget, 'set_html'):
                # CEF or tkhtmlview widget
                if file_path:
                    processed_content = self._process_html_content(html_content, file_path)
                else:
                    processed_content = html_content
                widget.set_html(processed_content)
                
            elif hasattr(widget, 'config') and hasattr(widget, 'insert'):
                # Text widget fallback
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    title = soup.find('title')
                    title_text = title.get_text() if title else "HTML Document"
                    
                    body = soup.find('body')
                    if body:
                        formatted_text = self._format_html_for_text(body)
                    else:
                        formatted_text = soup.get_text()
                    
                    widget.config(state="normal")
                    widget.delete("1.0", "end")
                    widget.insert("1.0", f"=== {title_text} ===\n\n{formatted_text}")
                    widget.config(state="disabled")
                    
                except ImportError:
                    widget.config(state="normal")
                    widget.delete("1.0", "end")
                    widget.insert("1.0", html_content)
                    widget.config(state="disabled")
                    
        except Exception as e:
            self.logger.error("HTMLRenderer", f"Failed to update widget content: {e}")
    
    def cleanup(self):
        """Clean up resources."""
        if self.cef_manager:
            self.cef_manager.shutdown()

# Test function
def test_enhanced_html_renderer():
    """Test the enhanced HTML renderer."""
    print("Testing Enhanced HTML Renderer:")
    print("=" * 50)
    
    # Sample HTML with modern features
    test_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Enhanced HTML Test</title>
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0; padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333; min-height: 100vh;
        }
        .container {
            max-width: 800px; margin: 0 auto;
            background: white; border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            padding: 30px; animation: slideIn 0.5s ease-out;
        }
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        h1 { color: #4a90e2; text-align: center; margin-bottom: 30px; }
        .feature-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
        .feature-card {
            background: #f8f9fa; padding: 20px; border-radius: 8px;
            border-left: 4px solid #4a90e2; transition: transform 0.2s;
        }
        .feature-card:hover { transform: translateY(-2px); box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        button {
            background: linear-gradient(45deg, #4a90e2, #357abd);
            color: white; border: none; padding: 12px 24px;
            border-radius: 6px; cursor: pointer; font-size: 16px;
            transition: all 0.3s; margin: 10px 5px;
        }
        button:hover { transform: scale(1.05); box-shadow: 0 5px 15px rgba(74,144,226,0.4); }
        .demo-output { background: #f1f3f4; padding: 15px; border-radius: 5px; margin: 10px 0; min-height: 50px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Enhanced HTML Renderer Test</h1>
        
        <div class="feature-grid">
            <div class="feature-card">
                <h3>Modern CSS</h3>
                <p>Grid layouts, gradients, animations, and transforms work perfectly in CEF.</p>
            </div>
            <div class="feature-card">
                <h3>JavaScript</h3>
                <p>Full ES6+ support with modern browser APIs and frameworks.</p>
            </div>
            <div class="feature-card">
                <h3>Responsive Design</h3>
                <p>Media queries and flexible layouts adapt to different screen sizes.</p>
            </div>
        </div>
        
        <div style="text-align: center; margin: 30px 0;">
            <button onclick="addContent()">Add Dynamic Content</button>
            <button onclick="changeTheme()">Toggle Theme</button>
            <button onclick="showAlert()">Test JavaScript</button>
        </div>
        
        <div id="output" class="demo-output">
            Click buttons above to see JavaScript in action...
        </div>
    </div>
    
    <script>
        let darkTheme = false;
        
        function addContent() {
            const output = document.getElementById('output');
            const timestamp = new Date().toLocaleTimeString();
            output.innerHTML += `<div>✨ Content added at ${timestamp}</div>`;
        }
        
        function changeTheme() {
            darkTheme = !darkTheme;
            const body = document.body;
            if (darkTheme) {
                body.style.background = 'linear-gradient(135deg, #2c3e50 0%, #34495e 100%)';
                body.style.color = '#ecf0f1';
            } else {
                body.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
                body.style.color = '#333';
            }
        }
        
        function showAlert() {
            const output = document.getElementById('output');
            output.innerHTML = '<div style="color: green;">🎉 JavaScript is working perfectly!</div>';
        }
        
        // Initialize with welcome message
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(() => {
                document.getElementById('output').innerHTML = 
                    '<div>🌟 Enhanced HTML renderer loaded successfully!</div>';
            }, 500);
        });
    </script>
</body>
</html>'''
    
    try:
        # Create test application
        root = tk.Tk()
        root.title("Enhanced HTML Renderer Test")
        root.geometry("1000x700")
        
        # Create simple logger
        class SimpleLogger:
            def info(self, component, message):
                print(f"INFO [{component}]: {message}")
            def error(self, component, message):
                print(f"ERROR [{component}]: {message}")
            def warning(self, component, message):
                print(f"WARN [{component}]: {message}")
        
        logger = SimpleLogger()
        
        # Create enhanced renderer
        renderer = EnhancedHTMLRenderer(editor=None, logger=logger)
        
        # Create main frame
        main_frame = ttk.Frame(root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create HTML preview
        html_widget = renderer.create_preview_widget(main_frame, test_html)
        
        print("✅ Enhanced HTML renderer test window created")
        print("🌐 Test the interactive features in the browser widget")
        
        # Auto-close after 10 seconds for testing
        root.after(10000, root.quit)
        root.mainloop()
        
        # Cleanup
        renderer.cleanup()
        root.destroy()
        
        print("✅ Enhanced HTML renderer test completed")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_enhanced_html_renderer()
