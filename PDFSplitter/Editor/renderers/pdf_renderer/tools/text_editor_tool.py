# editor/renderers/pdf_renderer/tools/text_editor_tool.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser, font
from typing import Optional, Dict, Any
import fitz  # PyMuPDF
from ....tool_base import BaseTool

class TextEditorTool(BaseTool):
    """Comprehensive text editing tool for PDFs."""
    
    def __init__(self, editor_window):
        super().__init__(editor_window, name="Text Editor")
        self.selected_text = None
        self.text_widget = None
        self.current_font = "Arial"
        self.current_size = 12
        self.current_color = (0, 0, 0)  # RGB
        self.is_editing = False
        self.edit_rect = None
        self.original_text = ""
        
    def activate(self):
        """Activate the text editing tool."""
        super().activate()
        canvas = self.editor.get_current_canvas()
        if canvas:
            canvas.config(cursor="xterm")
            canvas.bind("<Button-1>", self.on_click)
            canvas.bind("<B1-Motion>", self.on_drag)
            canvas.bind("<ButtonRelease-1>", self.on_release)
            canvas.bind("<Double-Button-1>", self.on_double_click)
            canvas.bind("<Button-3>", self.on_right_click)  # Right click for context menu
        
        self._create_text_toolbar()
        
    def deactivate(self):
        """Deactivate the text editing tool."""
        super().deactivate()
        canvas = self.editor.get_current_canvas()
        if canvas:
            canvas.config(cursor="")
            canvas.unbind("<Button-1>")
            canvas.unbind("<B1-Motion>")
            canvas.unbind("<ButtonRelease-1>")
            canvas.unbind("<Double-Button-1>")
            canvas.unbind("<Button-3>")
        
        self._finish_editing()
        self._destroy_text_toolbar()
        
    def _create_text_toolbar(self):
        """Create a toolbar for text editing options."""
        if hasattr(self.editor, 'text_toolbar'):
            self.editor.text_toolbar.destroy()
            
        self.editor.text_toolbar = ttk.Frame(self.editor.toolbar)
        self.editor.text_toolbar.pack(side="left", fill="x", padx=5)
        
        # Font selection
        ttk.Label(self.editor.text_toolbar, text="Font:").pack(side="left", padx=2)
        self.font_var = tk.StringVar(value=self.current_font)
        font_combo = ttk.Combobox(self.editor.text_toolbar, textvariable=self.font_var, 
                                 values=["Arial", "Times New Roman", "Courier New", "Helvetica", "Georgia"],
                                 width=15)
        font_combo.pack(side="left", padx=2)
        font_combo.bind("<<ComboboxSelected>>", self.on_font_change)
        
        # Size selection
        ttk.Label(self.editor.text_toolbar, text="Size:").pack(side="left", padx=2)
        self.size_var = tk.StringVar(value=str(self.current_size))
        size_combo = ttk.Combobox(self.editor.text_toolbar, textvariable=self.size_var,
                                 values=["8", "10", "12", "14", "16", "18", "20", "24", "28", "32"],
                                 width=5)
        size_combo.pack(side="left", padx=2)
        size_combo.bind("<<ComboboxSelected>>", self.on_size_change)
        
        # Color selection
        self.color_button = ttk.Button(self.editor.text_toolbar, text="Color", 
                                      command=self.choose_color)
        self.color_button.pack(side="left", padx=2)
        
        # Text formatting buttons
        ttk.Button(self.editor.text_toolbar, text="B", command=self.toggle_bold).pack(side="left", padx=1)
        ttk.Button(self.editor.text_toolbar, text="I", command=self.toggle_italic).pack(side="left", padx=1)
        ttk.Button(self.editor.text_toolbar, text="U", command=self.toggle_underline).pack(side="left", padx=1)
        
        # Alignment buttons
        ttk.Button(self.editor.text_toolbar, text="←", command=lambda: self.set_alignment("left")).pack(side="left", padx=1)
        ttk.Button(self.editor.text_toolbar, text="↔", command=lambda: self.set_alignment("center")).pack(side="left", padx=1)
        ttk.Button(self.editor.text_toolbar, text="→", command=lambda: self.set_alignment("right")).pack(side="left", padx=1)
        
        # Delete text button
        ttk.Button(self.editor.text_toolbar, text="Delete", command=self.delete_selected_text).pack(side="left", padx=2)
        
    def _destroy_text_toolbar(self):
        """Remove the text toolbar."""
        if hasattr(self.editor, 'text_toolbar'):
            self.editor.text_toolbar.destroy()
            delattr(self.editor, 'text_toolbar')
            
    def on_click(self, event):
        """Handle mouse click for text selection or editing."""
        if self.is_editing:
            self._finish_editing()
            
        # Get current page and PDF coordinates
        page_num = self._get_current_page()
        pdf_x, pdf_y = self.editor.canvas_to_pdf_coords(page_num, event.x, event.y)
        
        # Check if clicking on existing text
        existing_text = self._get_text_at_position(page_num, pdf_x, pdf_y)
        if existing_text:
            self._start_text_editing(existing_text, pdf_x, pdf_y, page_num)
        else:
            self._start_new_text(pdf_x, pdf_y, page_num)
            
    def on_drag(self, event):
        """Handle mouse drag for text selection."""
        if not self.is_editing:
            # Update selection rectangle
            pass
            
    def on_release(self, event):
        """Handle mouse release."""
        pass
        
    def on_double_click(self, event):
        """Handle double-click for word selection."""
        page_num = self._get_current_page()
        pdf_x, pdf_y = self.editor.canvas_to_pdf_coords(page_num, event.x, event.y)
        
        # Select word at position
        word_text = self._get_word_at_position(page_num, pdf_x, pdf_y)
        if word_text:
            self._select_word(word_text)
            
    def on_right_click(self, event):
        """Handle right-click for context menu."""
        if self.selected_text:
            self._show_context_menu(event)
            
    def _get_current_page(self):
        """Get the current page number."""
        # This should be implemented based on your tab manager
        return 0  # Placeholder
        
    def _get_text_at_position(self, page_num, x, y):
        """Get text at the specified position."""
        tab_id = self.editor.tab_manager.get_current_tab_id()
        if not tab_id:
            return None
            
        tab_info = self.editor.tab_manager.tabs[tab_id]
        dm = tab_info.get("doc_model")
        if not dm:
            return None
            
        doc = dm.doc
        page = doc[page_num]
        
        # Get text blocks on the page
        blocks = page.get_text("dict")
        
        # Find text at the clicked position
        for block in blocks["blocks"]:
            if block.get("type") == 0:  # Text block
                bbox = block["bbox"]
                if bbox[0] <= x <= bbox[2] and bbox[1] <= y <= bbox[3]:
                    return block
        return None
        
    def _get_word_at_position(self, page_num, x, y):
        """Get word at the specified position."""
        text_block = self._get_text_at_position(page_num, x, y)
        if not text_block:
            return None
            
        # Find the specific word within the block
        for line in text_block.get("lines", []):
            for span in line.get("spans", []):
                bbox = span["bbox"]
                if bbox[0] <= x <= bbox[2] and bbox[1] <= y <= bbox[3]:
                    return span
        return None
        
    def _start_text_editing(self, text_block, x, y, page_num):
        """Start editing existing text."""
        self.is_editing = True
        self.selected_text = text_block
        self.original_text = text_block.get("text", "")
        
        # Create text widget for editing
        self._create_text_widget(x, y, self.original_text)
        
    def _start_new_text(self, x, y, page_num):
        """Start creating new text."""
        self.is_editing = True
        self.selected_text = None
        self.original_text = ""
        
        # Create text widget for new text
        self._create_text_widget(x, y, "")
        
    def _create_text_widget(self, x, y, initial_text):
        """Create a text widget for editing."""
        canvas = self.editor.get_current_canvas()
        if not canvas:
            return
            
        # Create text widget
        self.text_widget = tk.Text(canvas, wrap="word", font=(self.current_font, self.current_size))
        self.text_widget.insert("1.0", initial_text)
        self.text_widget.focus_set()
        
        # Position the widget
        canvas_window = canvas.create_window(x, y, window=self.text_widget, anchor="nw")
        self.text_widget.canvas_window = canvas_window
        
        # Bind events
        self.text_widget.bind("<FocusOut>", self.on_text_focus_out)
        self.text_widget.bind("<Escape>", self.on_escape)
        self.text_widget.bind("<Return>", self.on_return)
        
    def _finish_editing(self):
        """Finish text editing and apply changes."""
        if not self.is_editing or not self.text_widget:
            return
            
        # Get the edited text
        new_text = self.text_widget.get("1.0", "end-1c")
        
        # Apply the changes to the PDF
        if new_text != self.original_text:
            self._apply_text_changes(new_text)
            
        # Clean up
        canvas = self.editor.get_current_canvas()
        if canvas and hasattr(self.text_widget, 'canvas_window'):
            canvas.delete(self.text_widget.canvas_window)
        
        if self.text_widget:
            self.text_widget.destroy()
            self.text_widget = None
            
        self.is_editing = False
        self.selected_text = None
        
    def _apply_text_changes(self, new_text):
        """Apply text changes to the PDF."""
        tab_id = self.editor.tab_manager.get_current_tab_id()
        if not tab_id:
            return
            
        tab_info = self.editor.tab_manager.tabs[tab_id]
        dm = tab_info.get("doc_model")
        if not dm:
            return
            
        doc = dm.doc
        page_num = self._get_current_page()
        page = doc[page_num]
        
        if self.selected_text:
            # Edit existing text
            # Remove old text
            old_rect = fitz.Rect(self.selected_text["bbox"])
            page.add_redact_annot(old_rect)
            page.apply_redactions()
            
            # Add new text
            if new_text.strip():
                page.insert_text(old_rect.tl, new_text, 
                               fontname=self.current_font,
                               fontsize=self.current_size,
                               color=self.current_color)
        else:
            # Add new text
            if new_text.strip():
                # Get position from text widget
                canvas = self.editor.get_current_canvas()
                if canvas and hasattr(self.text_widget, 'canvas_window'):
                    x, y = canvas.coords(self.text_widget.canvas_window)
                    pdf_x, pdf_y = self.editor.canvas_to_pdf_coords(page_num, x, y)
                    
                    page.insert_text(fitz.Point(pdf_x, pdf_y), new_text,
                                   fontname=self.current_font,
                                   fontsize=self.current_size,
                                   color=self.current_color)
        
        # Mark document as modified
        dm.set_modified(True)
        
        # Refresh the display
        self.editor.tab_manager.refresh_current_tab()
        
    def on_font_change(self, event=None):
        """Handle font change."""
        self.current_font = self.font_var.get()
        if self.text_widget:
            self.text_widget.config(font=(self.current_font, self.current_size))
            
    def on_size_change(self, event=None):
        """Handle font size change."""
        try:
            self.current_size = int(self.size_var.get())
            if self.text_widget:
                self.text_widget.config(font=(self.current_font, self.current_size))
        except ValueError:
            pass
            
    def choose_color(self):
        """Open color chooser dialog."""
        color = colorchooser.askcolor(title="Choose text color")
        if color[0]:  # RGB values
            self.current_color = [c/255.0 for c in color[0]]  # Convert to 0-1 range
            if self.text_widget:
                self.text_widget.config(fg=color[1])
                
    def toggle_bold(self):
        """Toggle bold formatting."""
        # This would need more complex implementation for PDF text formatting
        pass
        
    def toggle_italic(self):
        """Toggle italic formatting."""
        # This would need more complex implementation for PDF text formatting
        pass
        
    def toggle_underline(self):
        """Toggle underline formatting."""
        # This would need more complex implementation for PDF text formatting
        pass
        
    def set_alignment(self, alignment):
        """Set text alignment."""
        # This would need more complex implementation for PDF text formatting
        pass
        
    def delete_selected_text(self):
        """Delete selected text."""
        if self.selected_text:
            self._apply_text_changes("")  # Apply empty text to delete
            
    def on_text_focus_out(self, event):
        """Handle text widget losing focus."""
        self._finish_editing()
        
    def on_escape(self, event):
        """Handle escape key."""
        self._finish_editing()
        
    def on_return(self, event):
        """Handle return key."""
        if event.state & 0x4:  # Ctrl+Return
            self._finish_editing()
        # Otherwise, allow normal return for new lines
        
    def _show_context_menu(self, event):
        """Show context menu for text operations."""
        context_menu = tk.Menu(self.editor.window, tearoff=0)
        context_menu.add_command(label="Copy", command=self.copy_text)
        context_menu.add_command(label="Cut", command=self.cut_text)
        context_menu.add_command(label="Paste", command=self.paste_text)
        context_menu.add_separator()
        context_menu.add_command(label="Delete", command=self.delete_selected_text)
        context_menu.add_separator()
        context_menu.add_command(label="Format...", command=self.format_text)
        
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
            
    def copy_text(self):
        """Copy selected text to clipboard."""
        if self.selected_text:
            text = self.selected_text.get("text", "")
            self.editor.window.clipboard_clear()
            self.editor.window.clipboard_append(text)
            
    def cut_text(self):
        """Cut selected text to clipboard."""
        self.copy_text()
        self.delete_selected_text()
        
    def paste_text(self):
        """Paste text from clipboard."""
        try:
            text = self.editor.window.clipboard_get()
            if self.text_widget:
                self.text_widget.insert("insert", text)
        except tk.TclError:
            pass
            
    def format_text(self):
        """Open text formatting dialog."""
        # This would open a more comprehensive formatting dialog
        pass
        
    def _select_word(self, word_span):
        """Select a word for editing."""
        self.selected_text = word_span
        # Highlight the selected word in the canvas
        # This would need canvas highlighting implementation
