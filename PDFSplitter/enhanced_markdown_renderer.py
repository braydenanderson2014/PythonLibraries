#!/usr/bin/env python3
"""
Enhanced Markdown renderer using CEF Python for better preview rendering.
Converts Markdown to HTML and displays using CEF for full styling support.
"""

import os
import tkinter as tk
from tkinter import ttk
import tempfile

try:
    import markdown
    from markdown.extensions import codehilite, tables, toc
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False

try:
    from cef_browser_widget import CEFBrowserFrame, CEFManager, CEF_AVAILABLE
except ImportError:
    CEF_AVAILABLE = False

class EnhancedMarkdownRenderer:
    """
    Enhanced Markdown renderer with CEF Python support.
    Converts Markdown to HTML and renders with full CSS styling.
    """
    
    def __init__(self, editor, logger):
        self.editor = editor
        self.logger = logger
        self.cef_manager = None
        
        if CEF_AVAILABLE:
            self.cef_manager = CEFManager()
            self.cef_manager.initialize()
            self.logger.info("MarkdownRenderer", "CEF Python available - using Chrome rendering engine")
        else:
            self.logger.info("MarkdownRenderer", "CEF Python not available - using fallback rendering")
    
    def create_preview_widget(self, parent_frame, markdown_content, file_path=None):
        """
        Create a Markdown preview widget using the best available renderer.
        
        Args:
            parent_frame: The tkinter frame to contain the widget
            markdown_content: The Markdown content to convert and display
            file_path: Optional file path for relative resource resolution
            
        Returns:
            The created widget instance
        """
        
        # Convert Markdown to HTML
        html_content = self._convert_markdown_to_html(markdown_content)
        
        if CEF_AVAILABLE and self.cef_manager and self.cef_manager.is_available():
            return self._create_cef_widget(parent_frame, html_content, file_path)
        else:
            return self._create_fallback_widget(parent_frame, html_content, markdown_content)
    
    def _convert_markdown_to_html(self, markdown_content):
        """Convert Markdown content to styled HTML."""
        if not MARKDOWN_AVAILABLE:
            # If markdown library not available, return content wrapped in HTML
            return f'''<!DOCTYPE html>
<html>
<head>
    <title>Markdown Preview</title>
    <style>{self._get_basic_styles()}</style>
</head>
<body>
    <div class="markdown-body">
        <pre>{markdown_content}</pre>
    </div>
</body>
</html>'''
        
        try:
            # Configure markdown with extensions
            md = markdown.Markdown(
                extensions=[
                    'codehilite',
                    'tables',
                    'toc',
                    'fenced_code',
                    'footnotes',
                    'attr_list',
                    'def_list',
                    'abbr',
                    'md_in_html'
                ],
                extension_configs={
                    'codehilite': {
                        'use_pygments': True,
                        'css_class': 'highlight'
                    },
                    'toc': {
                        'permalink': True
                    }
                }
            )
            
            # Convert markdown to HTML
            html_body = md.convert(markdown_content)
            
            # Wrap in full HTML document with styling
            full_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Markdown Preview</title>
    <style>
        {self._get_github_styles()}
        {self._get_syntax_highlighting_styles()}
    </style>
</head>
<body>
    <div class="markdown-body">
        {html_body}
    </div>
</body>
</html>'''
            
            return full_html
            
        except Exception as e:
            self.logger.error("MarkdownRenderer", f"Error converting markdown: {e}")
            # Fallback to basic HTML
            return f'''<!DOCTYPE html>
<html>
<head>
    <title>Markdown Preview</title>
    <style>{self._get_basic_styles()}</style>
</head>
<body>
    <div class="markdown-body">
        <pre>{markdown_content}</pre>
    </div>
</body>
</html>'''
    
    def _get_github_styles(self):
        """Get GitHub-style CSS for markdown rendering."""
        return '''
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif;
            font-size: 16px;
            line-height: 1.5;
            word-wrap: break-word;
            margin: 0;
            padding: 0;
            background-color: #ffffff;
        }
        
        .markdown-body {
            box-sizing: border-box;
            min-width: 200px;
            max-width: 980px;
            margin: 0 auto;
            padding: 45px;
        }
        
        .markdown-body h1, .markdown-body h2, .markdown-body h3, 
        .markdown-body h4, .markdown-body h5, .markdown-body h6 {
            margin-top: 24px;
            margin-bottom: 16px;
            font-weight: 600;
            line-height: 1.25;
        }
        
        .markdown-body h1 {
            font-size: 2em;
            padding-bottom: 0.3em;
            border-bottom: 1px solid #eaecef;
        }
        
        .markdown-body h2 {
            font-size: 1.5em;
            padding-bottom: 0.3em;
            border-bottom: 1px solid #eaecef;
        }
        
        .markdown-body h3 { font-size: 1.25em; }
        .markdown-body h4 { font-size: 1em; }
        .markdown-body h5 { font-size: 0.875em; }
        .markdown-body h6 { font-size: 0.85em; color: #6a737d; }
        
        .markdown-body p {
            margin-top: 0;
            margin-bottom: 16px;
        }
        
        .markdown-body ul, .markdown-body ol {
            padding-left: 2em;
            margin-top: 0;
            margin-bottom: 16px;
        }
        
        .markdown-body li {
            margin-bottom: 0.25em;
        }
        
        .markdown-body blockquote {
            margin: 0;
            padding: 0 1em;
            color: #6a737d;
            border-left: 0.25em solid #dfe2e5;
        }
        
        .markdown-body table {
            border-spacing: 0;
            border-collapse: collapse;
            margin-top: 0;
            margin-bottom: 16px;
            width: 100%;
            overflow: auto;
        }
        
        .markdown-body table th, .markdown-body table td {
            padding: 6px 13px;
            border: 1px solid #dfe2e5;
        }
        
        .markdown-body table th {
            background-color: #f6f8fa;
            font-weight: 600;
        }
        
        .markdown-body table tr:nth-child(2n) {
            background-color: #f6f8fa;
        }
        
        .markdown-body code {
            padding: 0.2em 0.4em;
            margin: 0;
            font-size: 85%;
            background-color: rgba(27,31,35,0.05);
            border-radius: 3px;
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
        }
        
        .markdown-body pre {
            padding: 16px;
            overflow: auto;
            font-size: 85%;
            line-height: 1.45;
            background-color: #f6f8fa;
            border-radius: 6px;
            margin-top: 0;
            margin-bottom: 16px;
        }
        
        .markdown-body pre code {
            display: inline;
            max-width: auto;
            padding: 0;
            margin: 0;
            overflow: visible;
            line-height: inherit;
            word-wrap: normal;
            background-color: transparent;
            border: 0;
        }
        
        .markdown-body a {
            color: #0366d6;
            text-decoration: none;
        }
        
        .markdown-body a:hover {
            text-decoration: underline;
        }
        
        .markdown-body hr {
            height: 0.25em;
            padding: 0;
            margin: 24px 0;
            background-color: #e1e4e8;
            border: 0;
        }
        
        .markdown-body img {
            max-width: 100%;
            height: auto;
            box-sizing: content-box;
        }
        '''
    
    def _get_syntax_highlighting_styles(self):
        """Get syntax highlighting CSS styles."""
        return '''
        .highlight { background: #f8f8f8; }
        .highlight .c { color: #999988; font-style: italic; } /* Comment */
        .highlight .k { color: #000000; font-weight: bold; } /* Keyword */
        .highlight .o { color: #000000; font-weight: bold; } /* Operator */
        .highlight .ch { color: #999988; font-style: italic; } /* Comment.Hashbang */
        .highlight .cm { color: #999988; font-style: italic; } /* Comment.Multiline */
        .highlight .cp { color: #999999; font-weight: bold; font-style: italic; } /* Comment.Preproc */
        .highlight .cpf { color: #999988; font-style: italic; } /* Comment.PreprocFile */
        .highlight .c1 { color: #999988; font-style: italic; } /* Comment.Single */
        .highlight .cs { color: #999999; font-weight: bold; font-style: italic; } /* Comment.Special */
        .highlight .gd { color: #000000; background-color: #ffdddd; } /* Generic.Deleted */
        .highlight .ge { color: #000000; font-style: italic; } /* Generic.Emph */
        .highlight .gr { color: #aa0000; } /* Generic.Error */
        .highlight .gh { color: #999999; } /* Generic.Heading */
        .highlight .gi { color: #000000; background-color: #ddffdd; } /* Generic.Inserted */
        .highlight .go { color: #888888; } /* Generic.Output */
        .highlight .gp { color: #555555; } /* Generic.Prompt */
        .highlight .gs { font-weight: bold; } /* Generic.Strong */
        .highlight .gu { color: #aaaaaa; } /* Generic.Subheading */
        .highlight .gt { color: #aa0000; } /* Generic.Traceback */
        .highlight .kc { color: #000000; font-weight: bold; } /* Keyword.Constant */
        .highlight .kd { color: #000000; font-weight: bold; } /* Keyword.Declaration */
        .highlight .kn { color: #000000; font-weight: bold; } /* Keyword.Namespace */
        .highlight .kp { color: #000000; font-weight: bold; } /* Keyword.Pseudo */
        .highlight .kr { color: #000000; font-weight: bold; } /* Keyword.Reserved */
        .highlight .kt { color: #445588; font-weight: bold; } /* Keyword.Type */
        .highlight .m { color: #009999; } /* Literal.Number */
        .highlight .s { color: #d01040; } /* Literal.String */
        .highlight .na { color: #008080; } /* Name.Attribute */
        .highlight .nb { color: #0086B3; } /* Name.Builtin */
        .highlight .nc { color: #445588; font-weight: bold; } /* Name.Class */
        .highlight .no { color: #008080; } /* Name.Constant */
        .highlight .nd { color: #3c5d5d; font-weight: bold; } /* Name.Decorator */
        .highlight .ni { color: #800080; } /* Name.Entity */
        .highlight .ne { color: #990000; font-weight: bold; } /* Name.Exception */
        .highlight .nf { color: #990000; font-weight: bold; } /* Name.Function */
        .highlight .nl { color: #990000; font-weight: bold; } /* Name.Label */
        .highlight .nn { color: #555555; } /* Name.Namespace */
        .highlight .nt { color: #000080; } /* Name.Tag */
        .highlight .nv { color: #008080; } /* Name.Variable */
        .highlight .ow { color: #000000; font-weight: bold; } /* Operator.Word */
        .highlight .w { color: #bbbbbb; } /* Text.Whitespace */
        .highlight .mb { color: #009999; } /* Literal.Number.Bin */
        .highlight .mf { color: #009999; } /* Literal.Number.Float */
        .highlight .mh { color: #009999; } /* Literal.Number.Hex */
        .highlight .mi { color: #009999; } /* Literal.Number.Integer */
        .highlight .mo { color: #009999; } /* Literal.Number.Oct */
        .highlight .sa { color: #d01040; } /* Literal.String.Affix */
        .highlight .sb { color: #d01040; } /* Literal.String.Backtick */
        .highlight .sc { color: #d01040; } /* Literal.String.Char */
        .highlight .dl { color: #d01040; } /* Literal.String.Delimiter */
        .highlight .sd { color: #d01040; } /* Literal.String.Doc */
        .highlight .s2 { color: #d01040; } /* Literal.String.Double */
        .highlight .se { color: #d01040; } /* Literal.String.Escape */
        .highlight .sh { color: #d01040; } /* Literal.String.Heredoc */
        .highlight .si { color: #d01040; } /* Literal.String.Interpol */
        .highlight .sx { color: #d01040; } /* Literal.String.Other */
        .highlight .sr { color: #009926; } /* Literal.String.Regex */
        .highlight .s1 { color: #d01040; } /* Literal.String.Single */
        .highlight .ss { color: #990073; } /* Literal.String.Symbol */
        .highlight .bp { color: #999999; } /* Name.Builtin.Pseudo */
        .highlight .fm { color: #990000; font-weight: bold; } /* Name.Function.Magic */
        .highlight .vc { color: #008080; } /* Name.Variable.Class */
        .highlight .vg { color: #008080; } /* Name.Variable.Global */
        .highlight .vi { color: #008080; } /* Name.Variable.Instance */
        .highlight .vm { color: #008080; } /* Name.Variable.Magic */
        .highlight .il { color: #009999; } /* Literal.Number.Integer.Long */
        '''
    
    def _get_basic_styles(self):
        """Get basic fallback styles."""
        return '''
        body { font-family: Arial, sans-serif; padding: 20px; line-height: 1.6; }
        pre { background: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }
        code { background: #f4f4f4; padding: 2px 4px; border-radius: 3px; }
        .markdown-body { max-width: 900px; margin: 0 auto; }
        '''
    
    def _create_cef_widget(self, parent_frame, html_content, file_path=None):
        """Create CEF-based markdown preview widget."""
        try:
            # Create CEF browser frame
            cef_widget = CEFBrowserFrame(parent_frame, html_content=html_content)
            cef_widget.pack(fill="both", expand=True)
            
            self.logger.info("MarkdownRenderer", "Created CEF browser widget for markdown")
            return cef_widget
            
        except Exception as e:
            self.logger.error("MarkdownRenderer", f"Failed to create CEF widget: {e}")
            return self._create_fallback_widget(parent_frame, html_content, "")
    
    def _create_fallback_widget(self, parent_frame, html_content, markdown_content):
        """Create fallback markdown preview widget."""
        try:
            # Try tkhtmlview first
            from tkhtmlview import HTMLScrolledText
            
            widget = HTMLScrolledText(parent_frame, html=html_content)
            widget.pack(fill="both", expand=True)
            
            self.logger.info("MarkdownRenderer", "Created tkhtmlview widget for markdown")
            return widget
            
        except ImportError:
            # Final fallback to text widget
            from tkinter import scrolledtext
            
            text_widget = scrolledtext.ScrolledText(
                parent_frame,
                wrap="word",
                font=("Consolas", 10),
                bg="#ffffff",
                fg="#000000"
            )
            text_widget.pack(fill="both", expand=True)
            
            # Show processed markdown or original content
            if MARKDOWN_AVAILABLE:
                try:
                    import markdown
                    md = markdown.Markdown()
                    html = md.convert(markdown_content)
                    
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html, 'html.parser')
                    formatted_text = soup.get_text()
                    
                    text_widget.insert("1.0", formatted_text)
                except:
                    text_widget.insert("1.0", markdown_content)
            else:
                text_widget.insert("1.0", markdown_content)
            
            text_widget.config(state="disabled")
            self.logger.info("MarkdownRenderer", "Created text widget fallback for markdown")
            return text_widget
    
    def update_widget_content(self, widget, markdown_content):
        """Update the content of a markdown widget."""
        try:
            html_content = self._convert_markdown_to_html(markdown_content)
            
            if hasattr(widget, 'set_html'):
                # CEF or tkhtmlview widget
                widget.set_html(html_content)
                
            elif hasattr(widget, 'config') and hasattr(widget, 'insert'):
                # Text widget fallback
                if MARKDOWN_AVAILABLE:
                    try:
                        import markdown
                        md = markdown.Markdown()
                        html = md.convert(markdown_content)
                        
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(html, 'html.parser')
                        formatted_text = soup.get_text()
                        
                        widget.config(state="normal")
                        widget.delete("1.0", "end")
                        widget.insert("1.0", formatted_text)
                        widget.config(state="disabled")
                    except:
                        widget.config(state="normal")
                        widget.delete("1.0", "end")
                        widget.insert("1.0", markdown_content)
                        widget.config(state="disabled")
                else:
                    widget.config(state="normal")
                    widget.delete("1.0", "end")
                    widget.insert("1.0", markdown_content)
                    widget.config(state="disabled")
                    
        except Exception as e:
            self.logger.error("MarkdownRenderer", f"Failed to update widget content: {e}")
    
    def cleanup(self):
        """Clean up resources."""
        if self.cef_manager:
            self.cef_manager.shutdown()

# Test function
def test_enhanced_markdown_renderer():
    """Test the enhanced markdown renderer."""
    print("Testing Enhanced Markdown Renderer:")
    print("=" * 50)
    
    # Sample Markdown content
    test_markdown = '''# Enhanced Markdown Renderer Test

This is a comprehensive test of the **enhanced Markdown renderer** with CEF Python support.

## Features

### Text Formatting
- **Bold text** and *italic text*
- ~~Strikethrough text~~
- `Inline code` formatting
- [Links to external sites](https://github.com)

### Code Blocks

```python
def hello_world():
    """A simple Python function."""
    print("Hello, World!")
    return "Success"

# Call the function
result = hello_world()
```

```javascript
// JavaScript example
function greetUser(name) {
    console.log(`Hello, ${name}!`);
    return `Welcome, ${name}`;
}

greetUser("Developer");
```

### Lists

#### Unordered List
- First item
- Second item with **bold**
- Third item with `code`
  - Nested item 1
  - Nested item 2

#### Ordered List
1. First numbered item
2. Second numbered item
3. Third numbered item

### Tables

| Feature | CEF Support | Fallback Support |
|---------|-------------|------------------|
| CSS Styling | ✅ Full | ⚠️ Limited |
| JavaScript | ✅ Full | ❌ None |
| Animations | ✅ Full | ❌ None |
| Modern HTML5 | ✅ Full | ⚠️ Partial |

### Blockquotes

> This is a blockquote example.
> 
> It can span multiple lines and contain **formatting**.
> 
> > Nested blockquotes are also supported.

### Horizontal Rule

---

## Math and Special Characters

The enhanced renderer supports various special characters and symbols:

- Greek letters: α, β, γ, δ, ε
- Mathematical symbols: ∑, ∏, ∫, ∞, ≤, ≥
- Arrows: ←, →, ↑, ↓, ↔
- Checkmarks: ✓, ✗, ✅, ❌

## Conclusion

The CEF Python integration provides:

1. **Full CSS3 support** - All modern styling works
2. **Complete JavaScript execution** - Interactive content possible  
3. **Better typography** - Superior font rendering
4. **Responsive design** - Proper media query support
5. **Standards compliance** - Latest HTML5/CSS3/ES6+ support

This makes the editor much more capable for modern web content!
'''
    
    try:
        # Create test application
        root = tk.Tk()
        root.title("Enhanced Markdown Renderer Test")
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
        renderer = EnhancedMarkdownRenderer(editor=None, logger=logger)
        
        # Create main frame
        main_frame = ttk.Frame(root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create markdown preview
        markdown_widget = renderer.create_preview_widget(main_frame, test_markdown)
        
        print("✅ Enhanced Markdown renderer test window created")
        print("📝 Check the rendered markdown with full styling support")
        
        # Auto-close after 10 seconds for testing
        root.after(10000, root.quit)
        root.mainloop()
        
        # Cleanup
        renderer.cleanup()
        root.destroy()
        
        print("✅ Enhanced Markdown renderer test completed")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_enhanced_markdown_renderer()
