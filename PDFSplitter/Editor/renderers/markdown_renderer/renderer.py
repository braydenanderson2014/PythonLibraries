# editor/renderers/md_renderer/renderer.py

import os, markdown
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from ..base import BaseRenderer

# Enhanced markdown rendering capabilities
try:
    from enhanced_web_renderer import EnhancedWebRenderer
    ENHANCED_RENDERING = True
except ImportError:
    ENHANCED_RENDERING = False


# requires `pip install tkhtmlview`
try:
    from tkhtmlview import HTMLLabel
    HTML_OK = True
except ImportError:
    HTML_OK = False

class Renderer(BaseRenderer):
    @classmethod
    def extensions(cls):
        return [".md"]

    @classmethod
    def preview_only(cls):
        return True

    @classmethod
    def tools(cls):
        return []

    def supports_dual_tabs(self) -> bool:
        """Return True if this renderer supports dual tabs."""
        return True

    def open_dual_tabs(self, file_path: str) -> tuple[str, str]:
        """Open dual tabs for markdown file (editor + preview)."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except Exception as e:
            self.logger.error("MarkdownRenderer", f"Failed to read file {file_path}: {e}")
            return None, None
        
        return self.load_markdown_dual_tabs(file_path, content)

    def refresh_preview(self, editor_tab_id: str):
        """Refresh the preview tab based on editor content."""
        info = self.editor.tab_manager.tabs[editor_tab_id]
        preview_tab_id = info.get("preview_tab")
        
        if preview_tab_id:
            # Get current content from editor
            editor_widget = info.get("edit_widget")
            if editor_widget:
                content = editor_widget.get("1.0", "end-1c")
                self._update_markdown_preview(preview_tab_id, content)

    def open(self, path: str) -> str:
        if not HTML_OK:
            messagebox.showwarning(
                "tkhtmlview missing",
                "Install tkhtmlview to preview Markdown."
            )
            return None 

        tab_frame = ttk.Frame(self.editor.tab_manager.notebook)
        
        # Create a proper scrollable container
        container_frame = ttk.Frame(tab_frame)
        container_frame.pack(fill="both", expand=True)
        
        # Create scrollbar first
        v_scrollbar = ttk.Scrollbar(container_frame, orient="vertical")
        v_scrollbar.pack(side="right", fill="y")
        
        # Read the raw markdown
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            raw = f.read()  

        # Split into pages for internal tracking
        PAGE_DELIMITER = "---PAGEBREAK---"
        if PAGE_DELIMITER in raw:
            pages = raw.split(PAGE_DELIMITER)
        else:
            lines = raw.splitlines()
            page_size = 40
            pages = ['\n'.join(lines[i:i+page_size]) for i in range(0, len(lines), page_size)]  

        # Store page start indices (by character offset)
        page_offsets = []
        offset = 0
        for page in pages:
            page_offsets.append(offset)
            offset += len(page) + 1  # +1 for the delimiter or newline  

        # Render markdown as HTML
        html = markdown.markdown(raw)
        
        # Create HTMLLabel with proper scrolling
        try:
            from tkhtmlview import HTMLScrolledText
            lbl = HTMLScrolledText(container_frame, html=html)
            lbl.pack(side="left", fill="both", expand=True)
            # Configure scrollbar
            lbl.configure(yscrollcommand=v_scrollbar.set)
            v_scrollbar.configure(command=lbl.yview)
        except ImportError:
            # Fallback to HTMLLabel with manual scrolling setup
            lbl = HTMLLabel(container_frame, html=html, yscrollcommand=v_scrollbar.set)
            lbl.pack(side="left", fill="both", expand=True)
            v_scrollbar.configure(command=lbl.yview) 

        display = os.path.basename(path)
        tab_id = self.editor.tab_manager.register_tab_widget(
            tab_frame,
            display_name=display,
            doc_model=None,
            preview_path=path,
            renderer=self
        )
        info = self.editor.tab_manager.tabs[tab_id]
        info["preview_widget"] = lbl
        info["preview_path"] = path
        info["pages"] = pages
        info["page_offsets"] = page_offsets
        info["current_page"] = 0

        return tab_id

    def open_dual_tabs(self, path: str) -> tuple[str, str]:
        """
        Open Markdown file with dual tabs (editor + preview).
        Returns (editor_tab_id, preview_tab_id).
        """
        # Read the file content
        try:
            content = Path(path).read_text("utf-8", errors="replace")
        except Exception as e:
            self.logger.error("MarkdownRenderer", f"Failed to read file {path}: {e}")
            return None, None
            
        return self.load_markdown_dual_tabs(path, content)

    def load_markdown_dual_tabs(self, file_path: str, content: str) -> tuple[str, str]:
        """Load markdown file in dual tabs (editor + preview)."""
        # Get tab IDs
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        editor_tab_id = f"{base_name}_editor"
        preview_tab_id = f"{base_name}_preview"
        
        # Create editor tab frame
        editor_tab_frame = ttk.Frame(self.editor.tab_manager.notebook)
        editor_tab_id = self.editor.tab_manager.register_tab_widget(
            editor_tab_frame,
            display_name=f"{base_name} (Editor)",
            preview_path=file_path,
            renderer=self
        )
        
        # Create preview tab frame  
        preview_tab_frame = ttk.Frame(self.editor.tab_manager.notebook)
        preview_tab_id = self.editor.tab_manager.register_tab_widget(
            preview_tab_frame,
            display_name=f"{base_name} (Preview)",
            preview_path=file_path,
            renderer=self
        )
        
        # Set up the editor tab with text editing capabilities
        editor_info = self.editor.tab_manager.tabs[editor_tab_id]
        editor_info["edit_mode"] = True
        editor_info["renderer"] = self
        
        # Create text editor widget for the editor tab
        editor_text = tk.Text(editor_tab_frame, wrap="word", font=("Monaco", 10))
        editor_text.pack(fill="both", expand=True)
        editor_text.insert("1.0", content)
        
        # Add scrollbar to editor
        editor_scrollbar = ttk.Scrollbar(editor_tab_frame, orient="vertical", command=editor_text.yview)
        editor_text.configure(yscrollcommand=editor_scrollbar.set)
        editor_scrollbar.pack(side="right", fill="y")
        
        # Store editor widget reference
        editor_info["edit_widget"] = editor_text
        editor_info["widget"] = editor_text
        
        # Set up live preview update
        def update_preview(*args):
            if preview_info.get("preview_widget"):
                try:
                    new_content = editor_text.get("1.0", "end-1c")
                    html_content = markdown.markdown(new_content)
                    
                    preview_widget = preview_info["preview_widget"]
                    if hasattr(preview_widget, 'set_html'):
                        preview_widget.set_html(html_content)
                    elif hasattr(preview_widget, 'config'):
                        # For Text widget fallback
                        preview_widget.config(state="normal")
                        preview_widget.delete("1.0", "end")
                        preview_widget.insert("1.0", html_content)
                        preview_widget.config(state="disabled")
                except Exception as e:
                    pass  # Silently ignore errors during preview update
        
        # Bind content change event for live preview
        editor_text.bind("<KeyRelease>", update_preview)
        editor_text.bind("<<Modified>>", update_preview)
        
        # Set up the preview tab with markdown rendering
        preview_info = self.editor.tab_manager.tabs[preview_tab_id]
        preview_info["edit_mode"] = False
        preview_info["renderer"] = self
        
        # Create markdown preview widget with proper scrolling
        try:
            # Convert markdown to HTML
            html_content = markdown.markdown(content)
            
            if HTML_OK:
                # Create a container for the preview
                preview_container = ttk.Frame(preview_tab_frame)
                preview_container.pack(fill="both", expand=True)
                
                # Create scrollbar
                preview_scrollbar = ttk.Scrollbar(preview_container, orient="vertical")
                preview_scrollbar.pack(side="right", fill="y")
                
                # Try to use HTMLScrolledText for better scrolling
                try:
                    from tkhtmlview import HTMLScrolledText
                    preview_widget = HTMLScrolledText(preview_container, html=html_content)
                    preview_widget.pack(side="left", fill="both", expand=True)
                    preview_widget.configure(yscrollcommand=preview_scrollbar.set)
                    preview_scrollbar.configure(command=preview_widget.yview)
                except ImportError:
                    # Fallback to HTMLLabel with manual scrolling
                    from tkhtmlview import HTMLLabel
                    preview_widget = HTMLLabel(preview_container, html=html_content, 
                                             yscrollcommand=preview_scrollbar.set)
                    preview_widget.pack(side="left", fill="both", expand=True)
                    preview_scrollbar.configure(command=preview_widget.yview)
            else:
                # Fallback to text widget
                from tkinter import scrolledtext
                preview_widget = scrolledtext.ScrolledText(preview_tab_frame, wrap="word", 
                                                         font=("Monaco", 10), state="disabled")
                preview_widget.pack(fill="both", expand=True)
                preview_widget.config(state="normal")
                preview_widget.insert("1.0", html_content)
                preview_widget.config(state="disabled")
                
            preview_info["preview_widget"] = preview_widget
            preview_info["widget"] = preview_widget
            
        except Exception as e:
            # Fallback to text widget if markdown conversion fails
            from tkinter import scrolledtext
            preview_text = scrolledtext.ScrolledText(preview_tab_frame, wrap="word", 
                                                   font=("Monaco", 10), state="disabled")
            preview_text.pack(fill="both", expand=True)
            preview_text.config(state="normal")
            preview_text.insert("1.0", content)
            preview_text.config(state="disabled")
            preview_info["preview_widget"] = preview_text
            preview_info["widget"] = preview_text
        
        # Link the tabs together
        editor_info["preview_tab"] = preview_tab_id
        preview_info["editor_tab"] = editor_tab_id
        
        return editor_tab_id, preview_tab_id
        
    def _setup_editor_tab(self, tab_id: str, file_path: str, content: str):
        """Set up the editor tab with text editing widget."""
        info = self.editor.tab_manager.tabs[tab_id]
        
        # Create text editor widget
        import tkinter as tk
        from tkinter import scrolledtext
        
        edit_widget = scrolledtext.ScrolledText(
            self.editor.tab_manager.notebook,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg="white",
            fg="black"
        )
        
        edit_widget.insert("1.0", content)
        edit_widget.edit_modified(False)
        
        # Store widget reference
        info["edit_widget"] = edit_widget
        info["widget"] = edit_widget
        
        # Set up live preview
        preview_tab_id = info.get("preview_tab")
        if preview_tab_id:
            def on_text_change(event=None):
                # Get current content and update preview
                current_content = edit_widget.get("1.0", "end-1c")
                self._update_markdown_preview(preview_tab_id, current_content)
            edit_widget.bind('<KeyRelease>', on_text_change)
            edit_widget.bind('<Button-1>', on_text_change)
                
    def _setup_preview_tab(self, tab_id: str, file_path: str, content: str):
        """Set up the preview tab with markdown rendering."""
        info = self.editor.tab_manager.tabs[tab_id]
        
        # Create the preview widget using the same approach as the original open method
        if not HTML_OK:
            # Fallback to text widget if HTML widget not available
            import tkinter as tk
            from tkinter import scrolledtext
            preview_widget = scrolledtext.ScrolledText(
                self.editor.tab_manager.notebook,
                wrap=tk.WORD,
                font=("Consolas", 10),
                bg="white",
                fg="black",
                state="disabled"
            )
            info["preview_widget"] = preview_widget
            info["widget"] = preview_widget
        else:
            # Create the full markdown preview setup
            tab_frame = ttk.Frame(self.editor.tab_manager.notebook)
            canvas = tk.Canvas(tab_frame)
            scrollbar = ttk.Scrollbar(tab_frame, orient="vertical", command=canvas.yview)
            canvas.configure(yscrollcommand=scrollbar.set)
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Store references
            info["canvas"] = canvas
            info["scrollbar"] = scrollbar
            info["widget"] = tab_frame
            
        # Set up the preview content
        self._update_markdown_preview(tab_id, content)
        
    def _update_markdown_preview(self, tab_id: str, content: str):
        """Update the markdown preview content for a tab."""
        info = self.editor.tab_manager.tabs[tab_id]
        
        if not HTML_OK:
            # Update text widget fallback
            preview_widget = info.get("preview_widget")
            if preview_widget:
                preview_widget.config(state="normal")
                preview_widget.delete("1.0", "end")
                preview_widget.insert("1.0", content)
                preview_widget.config(state="disabled")
        else:
            # Update HTML preview
            canvas = info.get("canvas")
            if canvas:
                # Clear existing content
                canvas.delete("all")
                
                # Process the markdown content
                PAGE_DELIMITER = "---PAGEBREAK---"
                if PAGE_DELIMITER in content:
                    pages = content.split(PAGE_DELIMITER)
                else:
                    lines = content.splitlines()
                    page_size = 40
                    pages = ['\n'.join(lines[i:i+page_size]) for i in range(0, len(lines), page_size)]
                
                # Store page information
                page_offsets = []
                offset = 0
                for page in pages:
                    page_offsets.append(offset)
                    offset += len(page) + 1
                
                info["page_offsets"] = page_offsets
                info["pages"] = pages
                
                # Render HTML
                html = markdown.markdown(content)
                html_frame = ttk.Frame(canvas)
                lbl = HTMLLabel(html_frame, html=html)
                lbl.pack(fill="both", expand=True)
                html_frame.update_idletasks()
                
                # Add to canvas
                window_id = canvas.create_window((0, 0), window=html_frame, anchor="nw")
                html_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
                
                # Store widget reference
                info["preview_widget"] = lbl
