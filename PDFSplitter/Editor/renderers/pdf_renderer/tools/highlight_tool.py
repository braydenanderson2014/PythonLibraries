# editor/renderers/pdf_renderer/tools/highlight_tool.py
import tkinter as tk
from tkinter import ttk, colorchooser, messagebox
from typing import Optional, Dict, Any, List
import fitz  # PyMuPDF
from ....tool_base import BaseTool

class HighlightTool(BaseTool):
    """Text highlighting tool for PDF documents."""
    
    def __init__(self, editor_window):
        super().__init__(editor_window, name="Highlight Tool")
        self.highlight_color = "#FFFF00"  # Yellow
        self.highlight_opacity = 0.5
        self.highlight_mode = "word"  # word, line, selection
        self.is_highlighting = False
        self.highlight_start = None
        self.current_highlight = None
        self.highlight_presets = {
            "Yellow": "#FFFF00",
            "Green": "#00FF00",
            "Blue": "#0099FF",
            "Pink": "#FF69B4",
            "Orange": "#FFA500",
            "Purple": "#9966FF",
            "Red": "#FF0000",
            "Gray": "#808080"
        }
        
    def activate(self):
        """Activate the highlight tool."""
        super().activate()
        canvas = self.editor.get_current_canvas()
        if canvas:
            canvas.config(cursor="crosshair")
            canvas.bind("<Button-1>", self.on_click)
            canvas.bind("<B1-Motion>", self.on_drag)
            canvas.bind("<ButtonRelease-1>", self.on_release)
            canvas.bind("<Button-3>", self.on_right_click)
            canvas.bind("<Double-Button-1>", self.on_double_click)
        
        self._create_highlight_toolbar()
        
    def deactivate(self):
        """Deactivate the highlight tool."""
        super().deactivate()
        canvas = self.editor.get_current_canvas()
        if canvas:
            canvas.config(cursor="")
            canvas.unbind("<Button-1>")
            canvas.unbind("<B1-Motion>")
            canvas.unbind("<ButtonRelease-1>")
            canvas.unbind("<Button-3>")
            canvas.unbind("<Double-Button-1>")
        
        self._cancel_current_highlight()
        self._destroy_highlight_toolbar()
        
    def _create_highlight_toolbar(self):
        """Create toolbar for highlighting options."""
        if hasattr(self.editor, 'highlight_toolbar'):
            self.editor.highlight_toolbar.destroy()
            
        self.editor.highlight_toolbar = ttk.Frame(self.editor.toolbar)
        self.editor.highlight_toolbar.pack(side="left", fill="x", padx=5)
        
        # Highlight color presets
        ttk.Label(self.editor.highlight_toolbar, text="Color:").pack(side="left", padx=2)
        
        self.color_frame = ttk.Frame(self.editor.highlight_toolbar)
        self.color_frame.pack(side="left", padx=2)
        
        self.color_buttons = []
        for i, (name, color) in enumerate(self.highlight_presets.items()):
            btn = tk.Button(self.color_frame, bg=color, width=2, height=1,
                           command=lambda c=color: self._set_highlight_color(c))
            btn.grid(row=i//4, column=i%4, padx=1, pady=1)
            self.color_buttons.append(btn)
            
        # Custom color button
        custom_btn = tk.Button(self.color_frame, text="...", width=2, height=1,
                              command=self._choose_custom_color)
        custom_btn.grid(row=2, column=0, padx=1, pady=1)
        
        # Current color indicator
        self.current_color_label = tk.Label(self.editor.highlight_toolbar, 
                                           bg=self.highlight_color, width=3, height=1)
        self.current_color_label.pack(side="left", padx=5)
        
        # Opacity control
        ttk.Label(self.editor.highlight_toolbar, text="Opacity:").pack(side="left", padx=2)
        self.opacity_var = tk.DoubleVar(value=self.highlight_opacity)
        opacity_scale = ttk.Scale(self.editor.highlight_toolbar, from_=0.1, to=1.0,
                                 variable=self.opacity_var, orient="horizontal",
                                 length=80, command=self._on_opacity_change)
        opacity_scale.pack(side="left", padx=2)
        
        self.opacity_label = ttk.Label(self.editor.highlight_toolbar, text=f"{self.highlight_opacity:.1f}")
        self.opacity_label.pack(side="left", padx=2)
        
        # Highlight mode
        ttk.Label(self.editor.highlight_toolbar, text="Mode:").pack(side="left", padx=2)
        self.mode_var = tk.StringVar(value=self.highlight_mode)
        mode_combo = ttk.Combobox(self.editor.highlight_toolbar, textvariable=self.mode_var,
                                 values=["word", "line", "selection"], width=10)
        mode_combo.pack(side="left", padx=2)
        mode_combo.bind("<<ComboboxSelected>>", self._on_mode_change)
        
        # Highlight actions
        ttk.Separator(self.editor.highlight_toolbar, orient="vertical").pack(side="left", fill="y", padx=5)
        
        ttk.Button(self.editor.highlight_toolbar, text="Remove Highlight",
                  command=self._remove_highlight).pack(side="left", padx=2)
        ttk.Button(self.editor.highlight_toolbar, text="Clear All",
                  command=self._clear_all_highlights).pack(side="left", padx=2)
        
        # Highlight styles
        ttk.Separator(self.editor.highlight_toolbar, orient="vertical").pack(side="left", fill="y", padx=5)
        
        ttk.Button(self.editor.highlight_toolbar, text="Underline",
                  command=self._apply_underline).pack(side="left", padx=2)
        ttk.Button(self.editor.highlight_toolbar, text="Strikethrough",
                  command=self._apply_strikethrough).pack(side="left", padx=2)
        
    def _destroy_highlight_toolbar(self):
        """Remove the highlight toolbar."""
        if hasattr(self.editor, 'highlight_toolbar'):
            self.editor.highlight_toolbar.destroy()
            delattr(self.editor, 'highlight_toolbar')
            
    def _set_highlight_color(self, color):
        """Set the highlight color."""
        self.highlight_color = color
        self.current_color_label.config(bg=color)
        
    def _choose_custom_color(self):
        """Choose a custom highlight color."""
        color = colorchooser.askcolor(title="Choose highlight color")
        if color[1]:
            self._set_highlight_color(color[1])
            
    def _on_opacity_change(self, value):
        """Handle opacity change."""
        self.highlight_opacity = float(value)
        self.opacity_label.config(text=f"{self.highlight_opacity:.1f}")
        
    def _on_mode_change(self, event=None):
        """Handle highlight mode change."""
        self.highlight_mode = self.mode_var.get()
        
    def on_click(self, event):
        """Handle mouse click for highlighting."""
        page_num = self._get_current_page()
        pdf_x, pdf_y = self.editor.canvas_to_pdf_coords(page_num, event.x, event.y)
        
        # Check if clicking on existing highlight
        highlight_annot = self._get_highlight_at_position(page_num, pdf_x, pdf_y)
        if highlight_annot:
            self._select_highlight(highlight_annot)
            return
            
        # Start new highlight
        if self.highlight_mode == "word":
            self._highlight_word_at_position(page_num, pdf_x, pdf_y)
        elif self.highlight_mode == "line":
            self._highlight_line_at_position(page_num, pdf_x, pdf_y)
        else:  # selection mode
            self.is_highlighting = True
            self.highlight_start = (event.x, event.y)
            
    def on_drag(self, event):
        """Handle mouse drag for text selection highlighting."""
        if self.is_highlighting and self.highlight_mode == "selection":
            self._update_selection_highlight(event.x, event.y)
            
    def on_release(self, event):
        """Handle mouse release for highlighting."""
        if self.is_highlighting and self.highlight_mode == "selection":
            self.is_highlighting = False
            self._finish_selection_highlight(event.x, event.y)
            
    def on_right_click(self, event):
        """Handle right-click for highlight context menu."""
        page_num = self._get_current_page()
        pdf_x, pdf_y = self.editor.canvas_to_pdf_coords(page_num, event.x, event.y)
        
        highlight_annot = self._get_highlight_at_position(page_num, pdf_x, pdf_y)
        if highlight_annot:
            self._show_highlight_context_menu(event, highlight_annot)
            
    def on_double_click(self, event):
        """Handle double-click for line highlighting."""
        page_num = self._get_current_page()
        pdf_x, pdf_y = self.editor.canvas_to_pdf_coords(page_num, event.x, event.y)
        self._highlight_line_at_position(page_num, pdf_x, pdf_y)
        
    def _get_current_page(self):
        """Get the current page number."""
        return 0  # Placeholder
        
    def _get_highlight_at_position(self, page_num, x, y):
        """Get highlight annotation at the specified position."""
        tab_id = self.editor.tab_manager.get_current_tab_id()
        if not tab_id:
            return None
            
        tab_info = self.editor.tab_manager.tabs[tab_id]
        dm = tab_info.get("doc_model")
        if not dm:
            return None
            
        doc = dm.doc
        page = doc[page_num]
        point = fitz.Point(x, y)
        
        for annot in page.annots():
            if annot.type[1] == "Highlight" and annot.rect.contains(point):
                return annot
                
        return None
        
    def _highlight_word_at_position(self, page_num, x, y):
        """Highlight the word at the specified position."""
        tab_id = self.editor.tab_manager.get_current_tab_id()
        if not tab_id:
            return
            
        tab_info = self.editor.tab_manager.tabs[tab_id]
        dm = tab_info.get("doc_model")
        if not dm:
            return
            
        doc = dm.doc
        page = doc[page_num]
        point = fitz.Point(x, y)
        
        try:
            # Get text blocks
            text_blocks = page.get_text("dict")
            
            # Find the word at the position
            word_rect = None
            for block in text_blocks["blocks"]:
                if block.get("type") == 0:  # Text block
                    for line in block["lines"]:
                        for span in line["spans"]:
                            span_rect = fitz.Rect(span["bbox"])
                            if span_rect.contains(point):
                                # Find the specific word in the span
                                word_rect = self._find_word_rect(span, point)
                                break
                        if word_rect:
                            break
                    if word_rect:
                        break
            
            if word_rect:
                self._create_highlight_annotation(page, word_rect)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to highlight word: {str(e)}")
            
    def _highlight_line_at_position(self, page_num, x, y):
        """Highlight the line at the specified position."""
        tab_id = self.editor.tab_manager.get_current_tab_id()
        if not tab_id:
            return
            
        tab_info = self.editor.tab_manager.tabs[tab_id]
        dm = tab_info.get("doc_model")
        if not dm:
            return
            
        doc = dm.doc
        page = doc[page_num]
        point = fitz.Point(x, y)
        
        try:
            # Get text blocks
            text_blocks = page.get_text("dict")
            
            # Find the line at the position
            line_rect = None
            for block in text_blocks["blocks"]:
                if block.get("type") == 0:  # Text block
                    for line in block["lines"]:
                        line_bbox = line["bbox"]
                        line_rect = fitz.Rect(line_bbox)
                        if line_rect.contains(point):
                            break
                    if line_rect and line_rect.contains(point):
                        break
            
            if line_rect:
                self._create_highlight_annotation(page, line_rect)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to highlight line: {str(e)}")
            
    def _find_word_rect(self, span, point):
        """Find the bounding rectangle of a word within a span."""
        # This is a simplified implementation
        # In practice, you'd need to analyze the text to find word boundaries
        return fitz.Rect(span["bbox"])
        
    def _update_selection_highlight(self, x, y):
        """Update selection highlight visual feedback."""
        if self.highlight_start:
            # Update visual feedback on canvas
            pass
            
    def _finish_selection_highlight(self, x, y):
        """Finish selection highlighting."""
        if not self.highlight_start:
            return
            
        page_num = self._get_current_page()
        start_x, start_y = self.highlight_start
        
        # Convert to PDF coordinates
        pdf_start_x, pdf_start_y = self.editor.canvas_to_pdf_coords(page_num, start_x, start_y)
        pdf_end_x, pdf_end_y = self.editor.canvas_to_pdf_coords(page_num, x, y)
        
        # Create selection rectangle
        selection_rect = fitz.Rect(min(pdf_start_x, pdf_end_x), min(pdf_start_y, pdf_end_y),
                                  max(pdf_start_x, pdf_end_x), max(pdf_start_y, pdf_end_y))
        
        tab_id = self.editor.tab_manager.get_current_tab_id()
        if not tab_id:
            return
            
        tab_info = self.editor.tab_manager.tabs[tab_id]
        dm = tab_info.get("doc_model")
        if not dm:
            return
            
        doc = dm.doc
        page = doc[page_num]
        
        try:
            # Get text within selection
            text_instances = page.get_text("words")
            selected_words = []
            
            for word_info in text_instances:
                word_rect = fitz.Rect(word_info[:4])
                if selection_rect.intersects(word_rect):
                    selected_words.append(word_rect)
            
            # Create highlight for selected text
            if selected_words:
                # Merge overlapping rectangles
                merged_rects = self._merge_rectangles(selected_words)
                for rect in merged_rects:
                    self._create_highlight_annotation(page, rect)
                    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to highlight selection: {str(e)}")
            
        self.highlight_start = None
        
    def _merge_rectangles(self, rectangles):
        """Merge overlapping rectangles."""
        if not rectangles:
            return []
            
        merged = [rectangles[0]]
        
        for rect in rectangles[1:]:
            merged_any = False
            for i, merged_rect in enumerate(merged):
                if rect.intersects(merged_rect):
                    merged[i] = merged_rect | rect
                    merged_any = True
                    break
            
            if not merged_any:
                merged.append(rect)
                
        return merged
        
    def _create_highlight_annotation(self, page, rect):
        """Create a highlight annotation."""
        try:
            # Create highlight annotation
            highlight = page.add_highlight_annot(rect)
            
            # Set color with opacity
            color = self._hex_to_rgb(self.highlight_color)
            highlight.set_colors({"stroke": color, "fill": color})
            highlight.set_opacity(self.highlight_opacity)
            
            # Update annotation
            highlight.update()
            
            # Mark document as modified
            tab_id = self.editor.tab_manager.get_current_tab_id()
            if tab_id:
                tab_info = self.editor.tab_manager.tabs[tab_id]
                dm = tab_info.get("doc_model")
                if dm:
                    dm.set_modified(True)
            
            # Refresh display
            self.editor.tab_manager.refresh_current_tab()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create highlight: {str(e)}")
            
    def _hex_to_rgb(self, hex_color):
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))
        
    def _select_highlight(self, highlight_annot):
        """Select a highlight annotation."""
        # Update toolbar to show highlight properties
        color = highlight_annot.colors.get("fill", [1, 1, 0])
        hex_color = f"#{int(color[0]*255):02x}{int(color[1]*255):02x}{int(color[2]*255):02x}"
        self._set_highlight_color(hex_color)
        
        opacity = highlight_annot.opacity
        self.opacity_var.set(opacity)
        self.highlight_opacity = opacity
        
    def _remove_highlight(self):
        """Remove highlight at current position."""
        messagebox.showinfo("Remove Highlight", "Click on a highlight to remove it.")
        
    def _clear_all_highlights(self):
        """Clear all highlights on the current page."""
        result = messagebox.askyesno("Confirm", "Are you sure you want to remove all highlights on this page?")
        if not result:
            return
            
        page_num = self._get_current_page()
        tab_id = self.editor.tab_manager.get_current_tab_id()
        if not tab_id:
            return
            
        tab_info = self.editor.tab_manager.tabs[tab_id]
        dm = tab_info.get("doc_model")
        if not dm:
            return
            
        doc = dm.doc
        page = doc[page_num]
        
        try:
            # Remove all highlight annotations
            annotations_to_remove = []
            for annot in page.annots():
                if annot.type[1] == "Highlight":
                    annotations_to_remove.append(annot)
            
            for annot in annotations_to_remove:
                page.delete_annot(annot)
            
            # Mark document as modified
            dm.set_modified(True)
            
            # Refresh display
            self.editor.tab_manager.refresh_current_tab()
            
            messagebox.showinfo("Success", f"Removed {len(annotations_to_remove)} highlights.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear highlights: {str(e)}")
            
    def _apply_underline(self):
        """Apply underline style to selected text."""
        messagebox.showinfo("Underline", "Select text to apply underline.")
        
    def _apply_strikethrough(self):
        """Apply strikethrough style to selected text."""
        messagebox.showinfo("Strikethrough", "Select text to apply strikethrough.")
        
    def _show_highlight_context_menu(self, event, highlight_annot):
        """Show context menu for highlight."""
        context_menu = tk.Menu(self.editor.window, tearoff=0)
        context_menu.add_command(label="Change Color", 
                                command=lambda: self._change_highlight_color(highlight_annot))
        context_menu.add_command(label="Change Opacity", 
                                command=lambda: self._change_highlight_opacity(highlight_annot))
        context_menu.add_separator()
        context_menu.add_command(label="Remove Highlight", 
                                command=lambda: self._remove_specific_highlight(highlight_annot))
        context_menu.add_separator()
        context_menu.add_command(label="Add Note", 
                                command=lambda: self._add_highlight_note(highlight_annot))
        
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
            
    def _change_highlight_color(self, highlight_annot):
        """Change the color of a specific highlight."""
        color = colorchooser.askcolor(title="Choose highlight color")
        if color[1]:
            try:
                rgb_color = self._hex_to_rgb(color[1])
                highlight_annot.set_colors({"stroke": rgb_color, "fill": rgb_color})
                highlight_annot.update()
                
                # Mark document as modified
                tab_id = self.editor.tab_manager.get_current_tab_id()
                if tab_id:
                    tab_info = self.editor.tab_manager.tabs[tab_id]
                    dm = tab_info.get("doc_model")
                    if dm:
                        dm.set_modified(True)
                
                # Refresh display
                self.editor.tab_manager.refresh_current_tab()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to change highlight color: {str(e)}")
                
    def _change_highlight_opacity(self, highlight_annot):
        """Change the opacity of a specific highlight."""
        opacity_window = tk.Toplevel(self.editor.window)
        opacity_window.title("Change Highlight Opacity")
        opacity_window.geometry("300x100")
        
        ttk.Label(opacity_window, text="Opacity:").pack(pady=5)
        
        opacity_var = tk.DoubleVar(value=highlight_annot.opacity)
        opacity_scale = ttk.Scale(opacity_window, from_=0.1, to=1.0,
                                 variable=opacity_var, orient="horizontal")
        opacity_scale.pack(fill="x", padx=20, pady=5)
        
        def apply_opacity():
            try:
                highlight_annot.set_opacity(opacity_var.get())
                highlight_annot.update()
                
                # Mark document as modified
                tab_id = self.editor.tab_manager.get_current_tab_id()
                if tab_id:
                    tab_info = self.editor.tab_manager.tabs[tab_id]
                    dm = tab_info.get("doc_model")
                    if dm:
                        dm.set_modified(True)
                
                # Refresh display
                self.editor.tab_manager.refresh_current_tab()
                opacity_window.destroy()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to change opacity: {str(e)}")
        
        ttk.Button(opacity_window, text="Apply", command=apply_opacity).pack(pady=5)
        
    def _remove_specific_highlight(self, highlight_annot):
        """Remove a specific highlight."""
        try:
            page_num = self._get_current_page()
            tab_id = self.editor.tab_manager.get_current_tab_id()
            if not tab_id:
                return
                
            tab_info = self.editor.tab_manager.tabs[tab_id]
            dm = tab_info.get("doc_model")
            if not dm:
                return
                
            doc = dm.doc
            page = doc[page_num]
            
            page.delete_annot(highlight_annot)
            
            # Mark document as modified
            dm.set_modified(True)
            
            # Refresh display
            self.editor.tab_manager.refresh_current_tab()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to remove highlight: {str(e)}")
            
    def _add_highlight_note(self, highlight_annot):
        """Add a note to a highlight."""
        note_window = tk.Toplevel(self.editor.window)
        note_window.title("Add Note to Highlight")
        note_window.geometry("400x200")
        
        ttk.Label(note_window, text="Note:").pack(pady=5)
        
        note_text = tk.Text(note_window, wrap="word", height=8)
        note_text.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Get existing note if any
        existing_note = highlight_annot.info.get("content", "")
        if existing_note:
            note_text.insert("1.0", existing_note)
        
        def save_note():
            try:
                note_content = note_text.get("1.0", "end-1c")
                highlight_annot.set_info(content=note_content)
                highlight_annot.update()
                
                # Mark document as modified
                tab_id = self.editor.tab_manager.get_current_tab_id()
                if tab_id:
                    tab_info = self.editor.tab_manager.tabs[tab_id]
                    dm = tab_info.get("doc_model")
                    if dm:
                        dm.set_modified(True)
                
                note_window.destroy()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save note: {str(e)}")
        
        ttk.Button(note_window, text="Save", command=save_note).pack(pady=5)
        
    def _cancel_current_highlight(self):
        """Cancel any current highlighting operation."""
        self.is_highlighting = False
        self.highlight_start = None
        self.current_highlight = None