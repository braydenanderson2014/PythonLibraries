# editor/renderers/cef_markdown_renderer/renderer.py

import os
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import markdown
import tempfile

from ..base import BaseRenderer
from cef_browser_widget import CEFBrowserFrame, CEFManager, CEF_AVAILABLE

class Renderer(BaseRenderer):
    """
    CEF-based Markdown renderer that uses Chromium Embedded Framework for
    high-quality rendering of Markdown content with full CSS and JavaScript support.
    """
    
    def __init__(self, editor):
        super().__init__(editor)
        self.logger = editor.logger
        self.cef_manager = CEFManager()
        self.cef_manager.initialize()
        self.page_offsets = {}  # tab_id -> list of offsets
        self.temp_files = {}    # tab_id -> temp file path
        
        # Default CSS for markdown rendering
        self.default_css = """
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
        }
        
        h1, h2, h3, h4, h5, h6 {
            color: #0066cc;
            margin-top: 24px;
            margin-bottom: 16px;
            font-weight: 600;
        }
        
        h1 { font-size: 2em; border-bottom: 1px solid #eee; padding-bottom: 10px; }
        h2 { font-size: 1.5em; border-bottom: 1px solid #eee; padding-bottom: 8px; }
        
        code {
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
            background-color: rgba(27, 31, 35, 0.05);
            border-radius: 3px;
            padding: 0.2em 0.4em;
            font-size: 85%;
        }
        
        pre {
            background-color: #f6f8fa;
            border-radius: 3px;
            padding: 16px;
            overflow: auto;
        }
        
        pre code {
            background-color: transparent;
            padding: 0;
        }
        
        blockquote {
            border-left: 4px solid #ddd;
            padding: 0 15px;
            color: #777;
        }
        
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 16px 0;
        }
        
        table th, table td {
            border: 1px solid #ddd;
            padding: 6px 13px;
        }
        
        table tr {
            background-color: #fff;
            border-top: 1px solid #ccc;
        }
        
        table tr:nth-child(2n) {
            background-color: #f6f8fa;
        }
        
        img {
            max-width: 100%;
            height: auto;
        }
        
        a {
            color: #0366d6;
            text-decoration: none;
        }
        
        a:hover {
            text-decoration: underline;
        }
        
        @media (prefers-color-scheme: dark) {
            body {
                background-color: #222;
                color: #eee;
            }
            
            h1, h2, h3, h4, h5, h6 {
                color: #58a6ff;
            }
            
            h1, h2 {
                border-bottom-color: #333;
            }
            
            code {
                background-color: rgba(240, 246, 252, 0.15);
            }
            
            pre {
                background-color: #161b22;
            }
            
            blockquote {
                border-left-color: #444;
                color: #aaa;
            }
            
            table th, table td {
                border-color: #444;
            }
            
            table tr {
                background-color: #222;
                border-top-color: #444;
            }
            
            table tr:nth-child(2n) {
                background-color: #161b22;
            }
            
            a {
                color: #58a6ff;
            }
        }
        """

    @classmethod
    def extensions(cls):
        return [".md", ".markdown"]

    @classmethod
    def preview_only(cls):
        return True

    @classmethod
    def tools(cls):
        return []
        
    @classmethod
    def supports_dual_tabs(cls) -> bool:
        """Return True if this renderer supports dual tabs."""
        return True

    def open_dual_tabs(self, file_path: str) -> tuple[str, str]:
        """Open dual tabs for markdown file (editor + preview)."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except Exception as e:
            self.logger.error("CefMarkdownRenderer", f"Failed to read file {file_path}: {e}")
            return None, None
        
        return self.load_markdown_dual_tabs(file_path, content)
        
    def load_markdown_dual_tabs(self, file_path: str, content: str) -> tuple[str, str]:
        """Create dual tabs with editor and CEF-based preview."""
        
        # Check if CEF is available first
        if not CEF_AVAILABLE:
            messagebox.showwarning(
                "CEF Python Not Available",
                "CEF Python is not available. Install with: pip install cefpython3.\n\nFalling back to standard markdown renderer."
            )
            # Fallback to the standard markdown renderer
            try:
                from ..markdown_renderer.renderer import Renderer as FallbackRenderer
                fallback = FallbackRenderer(self.editor)
                return fallback.open_dual_tabs(file_path)
            except Exception:
                self.logger.error("CefMarkdownRenderer", "Failed to fallback to standard markdown renderer")
                return None, None
        
        # 1. Create editor tab
        editor_tab_id = self._create_editor_tab(file_path, content)
        if not editor_tab_id:
            return None, None
            
        # 2. Create preview tab
        preview_tab_id = self._create_preview_tab(file_path, content)
        if not preview_tab_id:
            return editor_tab_id, None
            
        # 3. Link them together for live updates
        self.editor.tab_manager.tabs[editor_tab_id]["preview_tab"] = preview_tab_id
        self.editor.tab_manager.tabs[preview_tab_id]["editor_tab"] = editor_tab_id
        
        return editor_tab_id, preview_tab_id

    def _create_editor_tab(self, file_path: str, content: str) -> str:
        """Create an editor tab for the markdown file."""
        try:
            # Create a text editor tab
            tab_frame = ttk.Frame(self.editor.tab_manager.notebook)
            
            # Create a proper scrollable text widget
            text_widget = tk.Text(
                tab_frame,
                wrap="word",
                undo=True,
                padx=10,
                pady=10,
                font=('Consolas', 10)
            )
            
            # Add scrollbars
            v_scroll = ttk.Scrollbar(tab_frame, orient="vertical", command=text_widget.yview)
            h_scroll = ttk.Scrollbar(tab_frame, orient="horizontal", command=text_widget.xview)
            text_widget.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
            
            # Pack everything
            text_widget.grid(row=0, column=0, sticky="nsew")
            v_scroll.grid(row=0, column=1, sticky="ns")
            h_scroll.grid(row=1, column=0, sticky="ew")
            
            tab_frame.grid_rowconfigure(0, weight=1)
            tab_frame.grid_columnconfigure(0, weight=1)
            
            # Insert the content
            text_widget.insert("1.0", content)
            text_widget.see("1.0")
            
            # Auto-update preview on edit
            def on_text_changed(event):
                editor_tab_id = self.editor.tab_manager.get_current_tab_id()
                if editor_tab_id:
                    preview_tab_id = self.editor.tab_manager.tabs[editor_tab_id].get("preview_tab")
                    if preview_tab_id:
                        current_content = text_widget.get("1.0", "end-1c")
                        self._update_markdown_preview(preview_tab_id, current_content)
                        # Mark as modified
                        self.editor.tab_manager.tabs[editor_tab_id]["doc_model"].modified = True
                        self.editor.tab_manager.mark_tab_dirty(editor_tab_id)
            
            text_widget.bind("<<Modified>>", on_text_changed)
            
            # Register the tab
            tab_id = self.editor.tab_manager.register_tab_widget(
                tab_frame, 
                display_name=file_path, 
                doc_model=self.editor.file_api.get_document_model(file_path),
                renderer=self
            )
            
            # Add the text widget to the tab info
            self.editor.tab_manager.tabs[tab_id]["edit_widget"] = text_widget
            
            return tab_id
            
        except Exception as e:
            self.logger.error("CefMarkdownRenderer", f"Failed to create editor tab: {e}")
            return None

    def _create_preview_tab(self, file_path: str, content: str) -> str:
        """Create a CEF-based preview tab for the markdown file."""
        try:
            # Create a tab frame
            tab_frame = ttk.Frame(self.editor.tab_manager.notebook)
            
            # Create the CEF browser frame
            html_content = self._convert_markdown_to_html(content)
            browser_frame = CEFBrowserFrame(tab_frame, html_content=html_content)
            browser_frame.pack(fill="both", expand=True)
            
            # Register the tab
            preview_name = f"Preview: {os.path.basename(file_path)}"
            tab_id = self.editor.tab_manager.register_tab_widget(
                tab_frame, 
                display_name=preview_name, 
                preview_path=file_path,
                renderer=self
            )
            
            # Add browser to tab info
            self.editor.tab_manager.tabs[tab_id]["browser"] = browser_frame
            self.editor.tab_manager.tabs[tab_id]["preview_widget"] = browser_frame
            
            # Track the page offsets for navigation
            self.page_offsets[tab_id] = [0]  # Just one page for now
            
            return tab_id
            
        except Exception as e:
            self.logger.error("CefMarkdownRenderer", f"Failed to create preview tab: {e}")
            return None

    def _convert_markdown_to_html(self, markdown_content: str) -> str:
        """Convert markdown content to HTML with our styling."""
        try:
            # Convert markdown to HTML
            html_content = markdown.markdown(
                markdown_content,
                extensions=[
                    'markdown.extensions.extra',
                    'markdown.extensions.codehilite',
                    'markdown.extensions.toc',
                    'markdown.extensions.tables',
                    'markdown.extensions.fenced_code',
                    'markdown.extensions.nl2br',
                    'markdown.extensions.sane_lists'
                ]
            )
            
            # Wrap in full HTML document with our CSS
            full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Markdown Preview</title>
    <style>
    {self.default_css}
    </style>
</head>
<body>
    <div class="markdown-body">
    {html_content}
    </div>
</body>
</html>
"""
            return full_html
            
        except Exception as e:
            self.logger.error("CefMarkdownRenderer", f"Markdown conversion failed: {e}")
            return f"<html><body><h1>Error rendering markdown</h1><p>{str(e)}</p></body></html>"

    def _update_markdown_preview(self, preview_tab_id: str, markdown_content: str):
        """Update the preview tab with new markdown content."""
        try:
            tab_info = self.editor.tab_manager.tabs.get(preview_tab_id)
            if not tab_info:
                return
                
            browser = tab_info.get("browser")
            if not browser:
                return
                
            html_content = self._convert_markdown_to_html(markdown_content)
            browser.set_html(html_content)
            
        except Exception as e:
            self.logger.error("CefMarkdownRenderer", f"Failed to update preview: {e}")

    def refresh_preview(self, editor_tab_id: str):
        """Refresh the preview tab based on editor content."""
        try:
            info = self.editor.tab_manager.tabs[editor_tab_id]
            preview_tab_id = info.get("preview_tab")
            
            if preview_tab_id:
                # Get current content from editor
                editor_widget = info.get("edit_widget")
                if editor_widget:
                    content = editor_widget.get("1.0", "end-1c")
                    self._update_markdown_preview(preview_tab_id, content)
        except Exception as e:
            self.logger.error("CefMarkdownRenderer", f"Failed to refresh preview: {e}")

    def open(self, path: str) -> str:
        """Open markdown file in preview-only mode."""
        if not CEF_AVAILABLE:
            messagebox.showwarning(
                "CEF Python Not Available",
                "CEF Python is not available. Install with: pip install cefpython3.\n\nFalling back to standard markdown renderer."
            )
            # Fallback to the standard markdown renderer
            try:
                from ..markdown_renderer.renderer import Renderer as FallbackRenderer
                fallback = FallbackRenderer(self.editor)
                return fallback.open(path)
            except Exception:
                self.logger.error("CefMarkdownRenderer", "Failed to fallback to standard markdown renderer")
                return None
        
        try:
            # Read markdown content
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                
            # Create tab
            tab_frame = ttk.Frame(self.editor.tab_manager.notebook)
            
            # Create browser widget
            html_content = self._convert_markdown_to_html(content)
            browser_frame = CEFBrowserFrame(tab_frame, html_content=html_content)
            browser_frame.pack(fill="both", expand=True)
            
            # Register tab
            tab_id = self.editor.tab_manager.add_tab(
                self.editor.file_api.get_document_model(path),
                self,
                None  # No overlay for markdown
            )
            
            # Update tab info
            self.editor.tab_manager.tabs[tab_id]["browser"] = browser_frame
            self.editor.tab_manager.tabs[tab_id]["preview_widget"] = browser_frame
            
            # Track offsets
            self.page_offsets[tab_id] = [0]  # Just one page for now
            
            return tab_id
            
        except Exception as e:
            self.logger.error("CefMarkdownRenderer", f"Failed to open file: {e}")
            return None

    def scroll(self, tab_id: str, direction: str, amount: int):
        """Handle scroll events in the preview."""
        try:
            tab_info = self.editor.tab_manager.tabs.get(tab_id)
            if not tab_info:
                return
            
            browser = tab_info.get("browser")
            if not browser or not browser.browser:
                return
                
            # Define JavaScript for scrolling
            js_amount = amount * 100  # Adjust based on desired scrolling speed
            
            if direction == "up":
                js = f"window.scrollBy(0, -{js_amount});"
            elif direction == "down":
                js = f"window.scrollBy(0, {js_amount});"
            elif direction == "left":
                js = f"window.scrollBy(-{js_amount}, 0);"
            elif direction == "right":
                js = f"window.scrollBy({js_amount}, 0);"
            else:
                return
                
            # Execute JavaScript in the browser
            browser.browser.ExecuteJavascript(js)
                
        except Exception as e:
            self.logger.error("CefMarkdownRenderer", f"Scroll failed: {e}")

    def cleanup(self):
        """Clean up resources when closing tabs."""
        # Remove any temporary files
        for temp_file in self.temp_files.values():
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except:
                pass
        self.temp_files.clear()
