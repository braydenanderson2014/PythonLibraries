#!/usr/bin/env python3
"""
Test script for enhanced HTML/Markdown renderers.
"""

import tkinter as tk
from tkinter import ttk
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_enhanced_renderers():
    """Test the enhanced rendering capabilities."""
    try:
        from enhanced_web_renderer import EnhancedWebRenderer
    except ImportError:
        print("❌ Enhanced web renderer not found!")
        return False
    
    print("🧪 Testing Enhanced HTML/Markdown Renderers")
    print("=" * 50)
    
    # Create test window
    root = tk.Tk()
    root.title("Enhanced Renderer Test")
    root.geometry("900x700")
    
    # Create notebook for tabs
    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Initialize renderer
    renderer = EnhancedWebRenderer()
    
    # Test HTML content
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            h1 { color: #2c3e50; border-bottom: 2px solid #3498db; }
            h2 { color: #34495e; }
            code { background: #f4f4f4; padding: 2px 4px; border-radius: 3px; }
            .highlight { background: #fff3cd; padding: 10px; border-radius: 5px; }
        </style>
    </head>
    <body>
        <h1>Enhanced HTML Rendering Test</h1>
        <h2>Features</h2>
        <ul>
            <li><strong>Bold text</strong> and <em>italic text</em></li>
            <li>Inline <code>code blocks</code></li>
            <li>Styled content with CSS</li>
        </ul>
        
        <div class="highlight">
            <strong>Highlight:</strong> This content uses enhanced HTML rendering 
            with fallback support for better compatibility.
        </div>
        
        <h2>Code Example</h2>
        <pre><code>
def enhanced_rendering():
    print("Enhanced HTML/Markdown rendering!")
    return "Success"
        </code></pre>
    </body>
    </html>
    """
    
    # Test Markdown content
    markdown_content = """
# Enhanced Markdown Rendering Test

This is a test of the **enhanced Markdown renderer** with improved capabilities.

## Features

- **Bold** and *italic* text formatting
- `Inline code` with proper styling
- Code blocks with syntax highlighting
- Tables and lists
- GitHub-style rendering

### Code Example

```python
def test_markdown_renderer():
    print("Testing enhanced Markdown rendering!")
    
    # Features:
    features = [
        "GitHub-style CSS",
        "Syntax highlighting", 
        "Table support",
        "Browser fallback"
    ]
    
    return features
```

### Table Example

| Feature | Status | Notes |
|---------|--------|-------|
| HTML Rendering | ✅ | tkhtmlview + fallbacks |
| Markdown Conversion | ✅ | markdown library |
| Browser Fallback | ✅ | Opens in default browser |
| Syntax Highlighting | ✅ | Pygments integration |

### Benefits

> Enhanced rendering provides better visual presentation while maintaining 
> compatibility with systems that don't have advanced dependencies installed.

The renderer automatically detects available libraries and uses the best 
option available, falling back gracefully when needed.
"""
    
    # HTML Tab
    html_frame = ttk.Frame(notebook)
    notebook.add(html_frame, text="HTML Test")
    
    try:
        html_widget = renderer.create_html_widget(html_frame, html_content)
        print("✅ HTML widget created successfully")
    except Exception as e:
        print(f"❌ HTML widget creation failed: {e}")
        error_label = ttk.Label(html_frame, text=f"HTML rendering failed: {e}")
        error_label.pack(pady=20)
    
    # Markdown Tab
    md_frame = ttk.Frame(notebook)
    notebook.add(md_frame, text="Markdown Test")
    
    try:
        md_widget = renderer.create_markdown_widget(md_frame, markdown_content)
        print("✅ Markdown widget created successfully")
    except Exception as e:
        print(f"❌ Markdown widget creation failed: {e}")
        error_label = ttk.Label(md_frame, text=f"Markdown rendering failed: {e}")
        error_label.pack(pady=20)
    
    # Info tab
    info_frame = ttk.Frame(notebook)
    notebook.add(info_frame, text="Renderer Info")
    
    info_text = tk.Text(info_frame, wrap=tk.WORD, padx=10, pady=10)
    info_text.pack(fill=tk.BOTH, expand=True)
    
    # Display renderer capabilities
    info_content = f"""
Enhanced Renderer Capabilities:

tkhtmlview available: {renderer.tkhtmlview_available}
webview available: {renderer.webview_available}  
markdown available: {renderer.markdown_available}

Rendering Strategy:
1. Try tkhtmlview for HTML (if available)
2. Fall back to enhanced text widget with HTML parsing
3. For Markdown: convert to HTML first, then render
4. Browser fallback option always available

Features:
- GitHub-style Markdown CSS
- Syntax highlighting for code blocks
- Responsive design
- Table support
- Automatic dependency detection
- Graceful fallbacks

Integration:
- Drop-in replacement for existing renderers
- Maintains backward compatibility
- Enhanced visual presentation
- Better user experience
"""
    
    info_text.insert('1.0', info_content)
    info_text.config(state='disabled')
    
    print("\n🎉 Test window created successfully!")
    print("Close the window when you're done testing.")
    
    # Run the GUI
    root.mainloop()
    
    # Cleanup
    renderer.cleanup()
    print("✅ Cleanup completed")
    
    return True

if __name__ == "__main__":
    success = test_enhanced_renderers()
    if success:
        print("\n🎉 Enhanced renderer test completed successfully!")
    else:
        print("\n❌ Enhanced renderer test failed!")
