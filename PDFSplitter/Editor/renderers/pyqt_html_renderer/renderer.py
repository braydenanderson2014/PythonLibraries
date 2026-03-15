# editor/renderers/pyqt_html_renderer/renderer.py

import os
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import tempfile
from pathlib import Path
from bs4 import BeautifulSoup

from ..base import BaseRenderer
from ..pyqt_frame_helper import PyQtWebFrame, PYQT_AVAILABLE
from ...text_document_model import TextDocumentModel  # Import the TextDocumentModel class

class Renderer(BaseRenderer):
    """
    PyQt WebEngine-based HTML renderer that uses WebEngine for
    full HTML rendering with CSS and JavaScript support.
    """
    
    def __init__(self, editor):
        super().__init__(editor)
        self.logger = editor.logger
        self.page_offsets = {}  # tab_id -> list of offsets
        self.temp_files = {}    # tab_id -> temp file path
        
    @classmethod
    def extensions(cls):
        return [".html", ".htm"]

    @classmethod
    def preview_only(cls):
        return False

    @classmethod
    def tools(cls):
        return []
        
    @classmethod
    def supports_dual_tabs(cls) -> bool:
        """Return True if this renderer supports dual tabs."""
        return True

    def open_dual_tabs(self, file_path: str) -> tuple:
        """Open dual tabs for HTML file (editor + preview)."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except Exception as e:
            self.logger.error("PyQtHtmlRenderer", f"Failed to read file {file_path}: {e}")
            return None, None
        
        return self.load_html_dual_tabs(file_path, content)
        
    def load_html_dual_tabs(self, file_path: str, content: str) -> tuple:
        """Create dual tabs with editor and PyQt WebEngine-based preview."""
        
        # Check if PyQt is available first
        if not PYQT_AVAILABLE:
            messagebox.showwarning(
                "PyQt WebEngine Not Available",
                "PyQt WebEngine is not available. Install with: pip install PyQt6 PyQt6-WebEngine.\n\nFalling back to standard HTML renderer."
            )
            # Fallback to the standard HTML renderer
            try:
                from ..html_renderer.renderer import Renderer as FallbackRenderer
                fallback = FallbackRenderer(self.editor)
                return fallback.open_dual_tabs(file_path)
            except Exception:
                self.logger.error("PyQtHtmlRenderer", "Failed to fallback to standard HTML renderer")
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
        """Create an editor tab for the HTML file."""
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
            
            # Implement syntax highlighting if pygments is available
            try:
                from pygments import highlight
                from pygments.lexers import HtmlLexer
                from pygments.formatters import UndefinedFilter
                
                # Apply syntax highlighting (in a real implementation)
                # This is just a placeholder - actual implementation would require more code
                pass
            except ImportError:
                # No syntax highlighting available
                pass
            
            # Auto-update preview on edit
            def on_text_changed(event):
                editor_tab_id = self.editor.tab_manager.get_current_tab_id()
                if editor_tab_id:
                    preview_tab_id = self.editor.tab_manager.tabs[editor_tab_id].get("preview_tab")
                    if preview_tab_id:
                        current_content = text_widget.get("1.0", "end-1c")
                        self._update_html_preview(preview_tab_id, current_content)
                        # Mark as modified
                        self.editor.tab_manager.tabs[editor_tab_id]["doc_model"].modified = True
                        self.editor.tab_manager.mark_tab_dirty(editor_tab_id)
            
            text_widget.bind("<<Modified>>", on_text_changed)
            
            # Create a document model for the HTML file
            doc_model = TextDocumentModel(filepath=file_path)
            
            # Register the tab
            tab_id = self.editor.tab_manager.register_tab_widget(
                tab_frame, 
                display_name=file_path, 
                doc_model=doc_model,
                renderer=self
            )
            
            # Add the text widget to the tab info
            self.editor.tab_manager.tabs[tab_id]["edit_widget"] = text_widget
            
            return tab_id
            
        except Exception as e:
            self.logger.error("PyQtHtmlRenderer", f"Failed to create editor tab: {e}")
            return None

    def _create_preview_tab(self, file_path: str, content: str) -> str:
        """Create a PyQt WebEngine-based preview tab for the HTML file."""
        try:
            # Create a tab frame
            tab_frame = ttk.Frame(self.editor.tab_manager.notebook)
            
            # Fix relative paths for resources in the HTML
            processed_html = self._process_html_resources(file_path, content)
            
            # Create the PyQt WebEngine frame
            browser_frame = PyQtWebFrame(tab_frame, html_content=processed_html)
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
            self.editor.tab_manager.tabs[tab_id]["base_path"] = os.path.dirname(file_path)
            
            # Track the page offsets for navigation
            self.page_offsets[tab_id] = [0]  # Just one page for now
            
            return tab_id
            
        except Exception as e:
            self.logger.error("PyQtHtmlRenderer", f"Failed to create preview tab: {e}")
            return None

    def _process_html_resources(self, file_path: str, html_content: str) -> str:
        """Process HTML content to fix relative paths for resources."""
        try:
            base_path = os.path.dirname(os.path.abspath(file_path))
            
            try:
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Process all <img> tags with relative src
                for img in soup.find_all('img'):
                    if img.get('src') and not img['src'].startswith(('http://', 'https://', 'data:', '/')):
                        img['src'] = f"file://{os.path.join(base_path, img['src']).replace(os.sep, '/')}"
                
                # Process all <link> tags (CSS)
                for link in soup.find_all('link'):
                    if link.get('href') and not link['href'].startswith(('http://', 'https://', 'data:', '/')):
                        link['href'] = f"file://{os.path.join(base_path, link['href']).replace(os.sep, '/')}"
                
                # Process all <script> tags with src
                for script in soup.find_all('script'):
                    if script.get('src') and not script['src'].startswith(('http://', 'https://', 'data:', '/')):
                        script['src'] = f"file://{os.path.join(base_path, script['src']).replace(os.sep, '/')}"
                
                # Add base tag if not present
                if not soup.find('base'):
                    head = soup.find('head')
                    if head:
                        base = soup.new_tag('base')
                        base['href'] = f"file://{base_path.replace(os.sep, '/')}/"
                        head.insert(0, base)
                
                # Return the processed HTML
                return str(soup)
                
            except Exception as e:
                # If BeautifulSoup fails, return the original content
                self.logger.warning("PyQtHtmlRenderer", f"Failed to process HTML resources: {e}")
                return html_content
                
        except Exception as e:
            self.logger.error("PyQtHtmlRenderer", f"Failed to process HTML: {e}")
            return html_content

    def _update_html_preview(self, preview_tab_id: str, html_content: str):
        """Update the preview tab with new HTML content."""
        try:
            tab_info = self.editor.tab_manager.tabs.get(preview_tab_id)
            if not tab_info:
                return
                
            browser = tab_info.get("browser")
            if not browser:
                return
                
            # Process HTML resources
            base_path = tab_info.get("base_path", "")
            if base_path:
                processed_html = self._process_html_resources(os.path.join(base_path, "temp.html"), html_content)
            else:
                processed_html = html_content
                
            browser.set_html(processed_html)
            
        except Exception as e:
            self.logger.error("PyQtHtmlRenderer", f"Failed to update preview: {e}")

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
                    self._update_html_preview(preview_tab_id, content)
        except Exception as e:
            self.logger.error("PyQtHtmlRenderer", f"Failed to refresh preview: {e}")

    def open(self, path: str) -> str:
        """Open HTML file in PyQt WebEngine browser."""
        if not PYQT_AVAILABLE:
            messagebox.showwarning(
                "PyQt WebEngine Not Available",
                "PyQt WebEngine is not available. Install with: pip install PyQt6 PyQt6-WebEngine.\n\nFalling back to standard HTML renderer."
            )
            # Fallback to the standard HTML renderer
            try:
                from ..html_renderer.renderer import Renderer as FallbackRenderer
                fallback = FallbackRenderer(self.editor)
                return fallback.open(path)
            except Exception:
                self.logger.error("PyQtHtmlRenderer", "Failed to fallback to standard HTML renderer")
                return None
        
        try:
            # Read HTML content
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                
            # Create tab
            tab_frame = ttk.Frame(self.editor.tab_manager.notebook)
            
            # Process HTML resources
            processed_html = self._process_html_resources(path, content)
            
            # Create browser widget
            browser_frame = PyQtWebFrame(tab_frame, html_content=processed_html)
            browser_frame.pack(fill="both", expand=True)
            
            # Create a document model for the HTML file
            doc_model = TextDocumentModel(filepath=path)
            
            # Register tab
            tab_id = self.editor.tab_manager.add_tab(
                doc_model,
                self,
                None  # No overlay for HTML
            )
            
            # Update tab info
            self.editor.tab_manager.tabs[tab_id]["browser"] = browser_frame
            self.editor.tab_manager.tabs[tab_id]["preview_widget"] = browser_frame
            self.editor.tab_manager.tabs[tab_id]["base_path"] = os.path.dirname(path)
            
            # Track offsets
            self.page_offsets[tab_id] = [0]  # Just one page for now
            
            return tab_id
            
        except Exception as e:
            self.logger.error("PyQtHtmlRenderer", f"Failed to open file: {e}")
            return None

    def save(self, tab_id: str):
        """Save changes to the HTML file."""
        try:
            tab_info = self.editor.tab_manager.tabs.get(tab_id)
            if not tab_info:
                return False
                
            doc_model = tab_info.get("doc_model")
            if not doc_model or not doc_model.filepath:
                return False
                
            # Find the linked editor tab if this is a preview tab
            if "editor_tab" in tab_info:
                editor_tab_id = tab_info["editor_tab"]
                editor_tab_info = self.editor.tab_manager.tabs.get(editor_tab_id)
                if not editor_tab_info:
                    return False
                    
                edit_widget = editor_tab_info.get("edit_widget")
                if not edit_widget:
                    return False
                    
                content = edit_widget.get("1.0", "end-1c")
            else:
                # This is an editor tab
                edit_widget = tab_info.get("edit_widget")
                if not edit_widget:
                    return False
                    
                content = edit_widget.get("1.0", "end-1c")
                
            # Save the content
            with open(doc_model.filepath, 'w', encoding='utf-8') as f:
                f.write(content)
                
            # Update model
            doc_model.modified = False
            
            # Update UI
            self.editor.tab_manager.mark_tab_dirty(tab_id)
            if "editor_tab" in tab_info:
                self.editor.tab_manager.mark_tab_dirty(tab_info["editor_tab"])
            elif "preview_tab" in tab_info:
                self.editor.tab_manager.mark_tab_dirty(tab_info["preview_tab"])
                
            return True
            
        except Exception as e:
            self.logger.error("PyQtHtmlRenderer", f"Failed to save file: {e}")
            return False

    def save_as(self, tab_id: str, new_path: str):
        """Save the HTML file to a new path."""
        try:
            tab_info = self.editor.tab_manager.tabs.get(tab_id)
            if not tab_info:
                return False
                
            doc_model = tab_info.get("doc_model")
            if not doc_model:
                return False
                
            # Find the linked editor tab if this is a preview tab
            if "editor_tab" in tab_info:
                editor_tab_id = tab_info["editor_tab"]
                editor_tab_info = self.editor.tab_manager.tabs.get(editor_tab_id)
                if not editor_tab_info:
                    return False
                    
                edit_widget = editor_tab_info.get("edit_widget")
                if not edit_widget:
                    return False
                    
                content = edit_widget.get("1.0", "end-1c")
            else:
                # This is an editor tab
                edit_widget = tab_info.get("edit_widget")
                if not edit_widget:
                    return False
                    
                content = edit_widget.get("1.0", "end-1c")
                
            # Save to the new path
            with open(new_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            # Update model
            doc_model.filepath = new_path
            doc_model.modified = False
            
            # Update UI
            self.editor.tab_manager.mark_tab_dirty(tab_id)
            self.editor.tab_manager.refresh_tab_label(tab_id)
            
            if "editor_tab" in tab_info:
                editor_tab_id = tab_info["editor_tab"]
                self.editor.tab_manager.tabs[editor_tab_id]["doc_model"].filepath = new_path
                self.editor.tab_manager.mark_tab_dirty(editor_tab_id)
                self.editor.tab_manager.refresh_tab_label(editor_tab_id)
            elif "preview_tab" in tab_info:
                preview_tab_id = tab_info["preview_tab"]
                self.editor.tab_manager.tabs[preview_tab_id]["preview_path"] = new_path
                self.editor.tab_manager.mark_tab_dirty(preview_tab_id)
                self.editor.tab_manager.refresh_tab_label(preview_tab_id)
                
            return True
            
        except Exception as e:
            self.logger.error("PyQtHtmlRenderer", f"Failed to save file as: {e}")
            return False

    def scroll(self, tab_id: str, direction: str, amount: int):
        """Handle scroll events in the preview."""
        try:
            tab_info = self.editor.tab_manager.tabs.get(tab_id)
            if not tab_info:
                return
            
            browser = tab_info.get("browser")
            if not browser or not hasattr(browser, "web_view") or browser.web_view is None:
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
            browser.web_view.page().runJavaScript(js)
                
        except Exception as e:
            self.logger.error("PyQtHtmlRenderer", f"Scroll failed: {e}")

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
