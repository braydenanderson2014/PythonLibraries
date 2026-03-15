#!/usr/bin/env python3
"""
Enhanced HTML/Markdown renderer using available libraries.
This solution provides improved rendering without requiring CEF Python.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import tempfile
import os
import webbrowser
import threading
import time
from urllib.parse import urljoin
from pathlib import Path

class EnhancedWebRenderer:
    """Enhanced web content renderer using available libraries."""
    
    def __init__(self, editor=None, logger=None):
        self.editor = editor
        self.logger = logger
        self.temp_files = []
        
        # Try to import optional dependencies
        self.tkhtmlview_available = self._check_tkhtmlview()
        self.webview_available = self._check_webview()
        self.markdown_available = self._check_markdown()
        
    def _check_tkhtmlview(self):
        """Check if tkhtmlview is available."""
        try:
            import tkhtmlview
            return True
        except ImportError:
            return False
    
    def _check_webview(self):
        """Check if webview is available."""
        try:
            import webview
            return True
        except ImportError:
            return False
    
    def _check_markdown(self):
        """Check if markdown is available."""
        try:
            import markdown
            return True
        except ImportError:
            return False
    
    def create_html_widget(self, parent, html_content, file_path=None):
        """
        Create an HTML widget with fallback options.
        
        Args:
            parent: Parent tkinter widget
            html_content: HTML content to display
            file_path: Optional file path for resource resolution
            
        Returns:
            Widget instance
        """
        # Try tkhtmlview first
        if self.tkhtmlview_available:
            return self._create_tkhtmlview_widget(parent, html_content, file_path)
        
        # Try enhanced text widget with HTML parsing
        return self._create_enhanced_text_widget(parent, html_content, file_path)
    
    def create_markdown_widget(self, parent, markdown_content, file_path=None):
        """
        Create a Markdown widget with fallback options.
        
        Args:
            parent: Parent tkinter widget
            markdown_content: Markdown content to display
            file_path: Optional file path for resource resolution
            
        Returns:
            Widget instance
        """
        if self.markdown_available:
            # Convert markdown to HTML first
            html_content = self._convert_markdown_to_html(markdown_content)
            return self.create_html_widget(parent, html_content, file_path)
        else:
            # Fallback to plain text with basic formatting
            return self._create_markdown_text_widget(parent, markdown_content, file_path)
    
    def _create_tkhtmlview_widget(self, parent, html_content, file_path=None):
        """Create tkhtmlview widget."""
        try:
            from tkhtmlview import HTMLScrolledText, RenderHTML
            
            # Create scrolled HTML widget
            html_widget = HTMLScrolledText(parent, html=html_content, height=20, width=80)
            
            # Configure styling
            html_widget.configure(bg='white', fg='black')
            
            return html_widget
            
        except Exception as e:
            if self.logger:
                self.logger.error("EnhancedRenderer", f"tkhtmlview widget creation failed: {e}")
            return self._create_enhanced_text_widget(parent, html_content, file_path)
    
    def _create_enhanced_text_widget(self, parent, html_content, file_path=None):
        """Create enhanced text widget with basic HTML parsing."""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Create scrolled text widget
        text_widget = scrolledtext.ScrolledText(
            frame,
            wrap=tk.WORD,
            width=80,
            height=20,
            bg='white',
            fg='black',
            font=('Arial', 10)
        )
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        # Create toolbar with browser button
        toolbar = ttk.Frame(frame)
        toolbar.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(
            toolbar,
            text="Open in Browser",
            command=lambda: self._open_in_browser(html_content)
        ).pack(side=tk.LEFT)
        
        # Parse and display HTML content
        self._display_parsed_html(text_widget, html_content)
        
        # Store reference for updates
        frame.text_widget = text_widget
        frame.set_html = lambda html: self._display_parsed_html(text_widget, html)
        
        return frame
    
    def _create_markdown_text_widget(self, parent, markdown_content, file_path=None):
        """Create text widget for markdown with basic formatting."""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Create scrolled text widget
        text_widget = scrolledtext.ScrolledText(
            frame,
            wrap=tk.WORD,
            width=80,
            height=20,
            bg='#fafafa',
            fg='#333333',
            font=('Monaco', 10)
        )
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        # Create toolbar
        toolbar = ttk.Frame(frame)
        toolbar.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(
            toolbar,
            text="Convert & Open",
            command=lambda: self._convert_and_open_markdown(markdown_content)
        ).pack(side=tk.LEFT)
        
        # Display markdown with basic formatting
        self._display_formatted_markdown(text_widget, markdown_content)
        
        # Store reference for updates
        frame.text_widget = text_widget
        frame.set_markdown = lambda md: self._display_formatted_markdown(text_widget, md)
        
        return frame
    
    def _convert_markdown_to_html(self, markdown_content):
        """Convert markdown to HTML using markdown library."""
        try:
            import markdown
            from markdown.extensions import tables, fenced_code, codehilite
            
            # Configure markdown with extensions
            md = markdown.Markdown(
                extensions=[
                    'tables',
                    'fenced_code', 
                    'codehilite',
                    'toc',
                    'nl2br'
                ],
                extension_configs={
                    'codehilite': {
                        'css_class': 'highlight',
                        'use_pygments': True
                    }
                }
            )
            
            # Convert to HTML
            html_content = md.convert(markdown_content)
            
            # Add CSS styling
            styled_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 900px;
                        margin: 0 auto;
                        padding: 20px;
                        background: white;
                    }}
                    h1, h2, h3, h4, h5, h6 {{
                        margin-top: 24px;
                        margin-bottom: 16px;
                        font-weight: 600;
                        line-height: 1.25;
                    }}
                    h1 {{ font-size: 2em; border-bottom: 1px solid #eaecef; padding-bottom: 10px; }}
                    h2 {{ font-size: 1.5em; border-bottom: 1px solid #eaecef; padding-bottom: 8px; }}
                    code {{
                        background: #f6f8fa;
                        padding: 2px 4px;
                        border-radius: 3px;
                        font-family: 'SFMono-Regular', Consolas, monospace;
                        font-size: 85%;
                    }}
                    pre {{
                        background: #f6f8fa;
                        border-radius: 6px;
                        padding: 16px;
                        overflow: auto;
                        line-height: 1.45;
                    }}
                    blockquote {{
                        border-left: 4px solid #dfe2e5;
                        padding: 0 16px;
                        color: #6a737d;
                        margin: 0;
                    }}
                    table {{
                        border-collapse: collapse;
                        width: 100%;
                        margin: 16px 0;
                    }}
                    table th, table td {{
                        border: 1px solid #dfe2e5;
                        padding: 8px 12px;
                        text-align: left;
                    }}
                    table th {{
                        background: #f6f8fa;
                        font-weight: 600;
                    }}
                    .highlight {{
                        background: #f6f8fa;
                        border-radius: 3px;
                        padding: 16px;
                        overflow: auto;
                    }}
                </style>
            </head>
            <body>
                {html_content}
            </body>
            </html>
            """
            
            return styled_html
            
        except Exception as e:
            if self.logger:
                self.logger.error("EnhancedRenderer", f"Markdown conversion failed: {e}")
            return f"<pre>{markdown_content}</pre>"
    
    def _display_parsed_html(self, text_widget, html_content):
        """Display HTML content with basic parsing."""
        text_widget.config(state=tk.NORMAL)
        text_widget.delete(1.0, tk.END)
        
        try:
            # Try to parse HTML with BeautifulSoup
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Configure text tags
            text_widget.tag_configure("h1", font=("Arial", 16, "bold"))
            text_widget.tag_configure("h2", font=("Arial", 14, "bold"))
            text_widget.tag_configure("h3", font=("Arial", 12, "bold"))
            text_widget.tag_configure("code", font=("Monaco", 9), background="#f0f0f0")
            text_widget.tag_configure("bold", font=("Arial", 10, "bold"))
            text_widget.tag_configure("italic", font=("Arial", 10, "italic"))
            
            # Extract and format text
            self._parse_html_element(text_widget, soup)
            
        except ImportError:
            # Fallback: strip HTML tags and display plain text
            import re
            plain_text = re.sub(r'<[^>]+>', '', html_content)
            text_widget.insert(tk.END, plain_text)
        
        text_widget.config(state=tk.DISABLED)
    
    def _parse_html_element(self, text_widget, element):
        """Recursively parse HTML elements."""
        if hasattr(element, 'children'):
            for child in element.children:
                if hasattr(child, 'name'):
                    if child.name in ['h1', 'h2', 'h3']:
                        text_widget.insert(tk.END, '\n' + child.get_text() + '\n', child.name)
                    elif child.name == 'code':
                        text_widget.insert(tk.END, child.get_text(), 'code')
                    elif child.name == 'strong' or child.name == 'b':
                        text_widget.insert(tk.END, child.get_text(), 'bold')
                    elif child.name == 'em' or child.name == 'i':
                        text_widget.insert(tk.END, child.get_text(), 'italic')
                    elif child.name == 'p':
                        text_widget.insert(tk.END, child.get_text() + '\n\n')
                    elif child.name == 'br':
                        text_widget.insert(tk.END, '\n')
                    else:
                        self._parse_html_element(text_widget, child)
                else:
                    # Text node
                    text_widget.insert(tk.END, str(child))
    
    def _display_formatted_markdown(self, text_widget, markdown_content):
        """Display markdown with basic formatting."""
        text_widget.config(state=tk.NORMAL)
        text_widget.delete(1.0, tk.END)
        
        # Configure text tags
        text_widget.tag_configure("h1", font=("Arial", 16, "bold"))
        text_widget.tag_configure("h2", font=("Arial", 14, "bold"))
        text_widget.tag_configure("h3", font=("Arial", 12, "bold"))
        text_widget.tag_configure("code", font=("Monaco", 9), background="#f0f0f0")
        text_widget.tag_configure("bold", font=("Arial", 10, "bold"))
        text_widget.tag_configure("italic", font=("Arial", 10, "italic"))
        
        # Parse markdown line by line
        lines = markdown_content.split('\n')
        for line in lines:
            if line.startswith('# '):
                text_widget.insert(tk.END, line[2:] + '\n', 'h1')
            elif line.startswith('## '):
                text_widget.insert(tk.END, line[3:] + '\n', 'h2')
            elif line.startswith('### '):
                text_widget.insert(tk.END, line[4:] + '\n', 'h3')
            elif line.startswith('```'):
                text_widget.insert(tk.END, line + '\n', 'code')
            else:
                # Handle inline formatting
                formatted_line = self._format_inline_markdown(text_widget, line)
                text_widget.insert(tk.END, formatted_line + '\n')
        
        text_widget.config(state=tk.DISABLED)
    
    def _format_inline_markdown(self, text_widget, line):
        """Format inline markdown elements."""
        import re
        
        # Simple patterns for bold and italic
        # This is a basic implementation - a full parser would be more complex
        
        # Replace **bold** with bold formatting
        line = re.sub(r'\*\*(.*?)\*\*', r'\1', line)
        
        # Replace *italic* with italic formatting  
        line = re.sub(r'\*(.*?)\*', r'\1', line)
        
        # Replace `code` with code formatting
        line = re.sub(r'`(.*?)`', r'\1', line)
        
        return line
    
    def _open_in_browser(self, html_content):
        """Open HTML content in default browser."""
        try:
            # Create temporary HTML file
            temp_file = tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.html',
                delete=False,
                encoding='utf-8'
            )
            
            temp_file.write(html_content)
            temp_file.close()
            
            # Track for cleanup
            self.temp_files.append(temp_file.name)
            
            # Open in browser
            webbrowser.open(f'file://{temp_file.name}')
            
            # Schedule cleanup after delay
            threading.Timer(30.0, self._cleanup_temp_file, [temp_file.name]).start()
            
        except Exception as e:
            if self.logger:
                self.logger.error("EnhancedRenderer", f"Browser open failed: {e}")
    
    def _convert_and_open_markdown(self, markdown_content):
        """Convert markdown to HTML and open in browser."""
        html_content = self._convert_markdown_to_html(markdown_content)
        self._open_in_browser(html_content)
    
    def _cleanup_temp_file(self, file_path):
        """Clean up temporary file."""
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
            if file_path in self.temp_files:
                self.temp_files.remove(file_path)
        except Exception:
            pass  # Ignore cleanup errors
    
    def cleanup(self):
        """Clean up all temporary files."""
        for temp_file in self.temp_files[:]:
            self._cleanup_temp_file(temp_file)

# Factory function for easy integration
def create_enhanced_renderer(editor=None, logger=None):
    """Create an enhanced renderer instance."""
    return EnhancedWebRenderer(editor, logger)

# Test function
def test_enhanced_renderer():
    """Test the enhanced renderer functionality."""
    print("Testing Enhanced Web Renderer...")
    
    renderer = create_enhanced_renderer()
    
    # Test HTML content
    html_test = """
    <h1>Test HTML</h1>
    <p>This is a <strong>test</strong> of the enhanced HTML renderer.</p>
    <code>print("Hello, World!")</code>
    """
    
    # Test Markdown content
    markdown_test = """
# Test Markdown

This is a **test** of the enhanced Markdown renderer.

## Features

- Basic formatting
- Code blocks
- Headers

```python
print("Hello, World!")
```
"""
    
    root = tk.Tk()
    root.title("Enhanced Renderer Test")
    root.geometry("800x600")
    
    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True)
    
    # HTML tab
    html_frame = ttk.Frame(notebook)
    notebook.add(html_frame, text="HTML")
    html_widget = renderer.create_html_widget(html_frame, html_test)
    
    # Markdown tab
    md_frame = ttk.Frame(notebook)
    notebook.add(md_frame, text="Markdown")
    md_widget = renderer.create_markdown_widget(md_frame, markdown_test)
    
    print("✅ Enhanced renderer test window created")
    print("Close the window to continue...")
    
    root.mainloop()
    
    # Cleanup
    renderer.cleanup()
    print("✅ Cleanup completed")

if __name__ == "__main__":
    test_enhanced_renderer()
