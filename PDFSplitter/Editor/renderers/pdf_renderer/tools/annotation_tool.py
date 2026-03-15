# editor/renderers/pdf_renderer/tools/annotation_tool.py
import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
from typing import Optional, Dict, Any, List
import fitz  # PyMuPDF
from ....tool_base import BaseTool

class AnnotationTool(BaseTool):
    """Comprehensive annotation tool for PDFs."""
    
    def __init__(self, editor_window):
        super().__init__(editor_window, name="Annotation Tool")
        self.annotation_type = "highlight"  # highlight, underline, strikeout, squiggly, note, stamp
        self.annotation_color = (1, 1, 0)  # Yellow
        self.annotation_opacity = 0.5
        self.selected_annotation = None
        self.drawing = False
        self.draw_start = None
        self.current_selection = []
        
    def activate(self):
        """Activate the annotation tool."""
        super().activate()
        canvas = self.editor.get_current_canvas()
        if canvas:
            canvas.config(cursor="hand2")
            canvas.bind("<Button-1>", self.on_click)
            canvas.bind("<B1-Motion>", self.on_drag)
            canvas.bind("<ButtonRelease-1>", self.on_release)
            canvas.bind("<Button-3>", self.on_right_click)
            canvas.bind("<Double-Button-1>", self.on_double_click)
        
        self._create_annotation_toolbar()
        
    def deactivate(self):
        """Deactivate the annotation tool."""
        super().deactivate()
        canvas = self.editor.get_current_canvas()
        if canvas:
            canvas.config(cursor="")
            canvas.unbind("<Button-1>")
            canvas.unbind("<B1-Motion>")
            canvas.unbind("<ButtonRelease-1>")
            canvas.unbind("<Button-3>")
            canvas.unbind("<Double-Button-1>")
        
        self._destroy_annotation_toolbar()
        
    def _create_annotation_toolbar(self):
        """Create toolbar for annotation options."""
        if hasattr(self.editor, 'annotation_toolbar'):
            self.editor.annotation_toolbar.destroy()
            
        self.editor.annotation_toolbar = ttk.Frame(self.editor.toolbar)
        self.editor.annotation_toolbar.pack(side="left", fill="x", padx=5)
        
        # Annotation type selection
        ttk.Label(self.editor.annotation_toolbar, text="Type:").pack(side="left", padx=2)
        self.type_var = tk.StringVar(value=self.annotation_type)
        type_combo = ttk.Combobox(self.editor.annotation_toolbar, textvariable=self.type_var,
                                 values=["highlight", "underline", "strikeout", "squiggly", "note", "stamp"],
                                 width=10)
        type_combo.pack(side="left", padx=2)
        type_combo.bind("<<ComboboxSelected>>", self.on_type_change)
        
        # Color selection
        self.color_button = ttk.Button(self.editor.annotation_toolbar, text="Color", 
                                      command=self.choose_color)
        self.color_button.pack(side="left", padx=2)
        
        # Opacity control
        ttk.Label(self.editor.annotation_toolbar, text="Opacity:").pack(side="left", padx=2)
        self.opacity_var = tk.DoubleVar(value=self.annotation_opacity)
        opacity_scale = ttk.Scale(self.editor.annotation_toolbar, from_=0.1, to=1.0,
                                 variable=self.opacity_var, orient="horizontal", length=100)
        opacity_scale.pack(side="left", padx=2)
        opacity_scale.bind("<Motion>", self.on_opacity_change)
        
        # Quick annotation buttons
        ttk.Button(self.editor.annotation_toolbar, text="📝", 
                  command=lambda: self.set_annotation_type("note")).pack(side="left", padx=1)
        ttk.Button(self.editor.annotation_toolbar, text="🔍", 
                  command=lambda: self.set_annotation_type("highlight")).pack(side="left", padx=1)
        ttk.Button(self.editor.annotation_toolbar, text="📌", 
                  command=lambda: self.set_annotation_type("stamp")).pack(side="left", padx=1)
        
        # Delete annotation button
        ttk.Button(self.editor.annotation_toolbar, text="Delete", 
                  command=self.delete_selected_annotation).pack(side="left", padx=2)
        
        # Clear all annotations button
        ttk.Button(self.editor.annotation_toolbar, text="Clear All", 
                  command=self.clear_all_annotations).pack(side="left", padx=2)
        
    def _destroy_annotation_toolbar(self):
        """Remove the annotation toolbar."""
        if hasattr(self.editor, 'annotation_toolbar'):
            self.editor.annotation_toolbar.destroy()
            delattr(self.editor, 'annotation_toolbar')
            
    def on_click(self, event):
        """Handle mouse click for annotation."""
        page_num = self._get_current_page()
        pdf_x, pdf_y = self.editor.canvas_to_pdf_coords(page_num, event.x, event.y)
        
        # Check if clicking on existing annotation
        clicked_annotation = self._get_annotation_at_position(page_num, pdf_x, pdf_y)
        if clicked_annotation:
            self._select_annotation(clicked_annotation)
        else:
            self._clear_selection()
            
            # Start new annotation
            if self.annotation_type == "note":
                self._create_note_annotation(pdf_x, pdf_y, page_num)
            elif self.annotation_type == "stamp":
                self._create_stamp_annotation(pdf_x, pdf_y, page_num)
            else:
                # Start drawing annotation
                self.drawing = True
                self.draw_start = (pdf_x, pdf_y)
                self.current_selection = [fitz.Point(pdf_x, pdf_y)]
                
    def on_drag(self, event):
        """Handle mouse drag for annotation selection."""
        if self.drawing:
            page_num = self._get_current_page()
            pdf_x, pdf_y = self.editor.canvas_to_pdf_coords(page_num, event.x, event.y)
            self.current_selection.append(fitz.Point(pdf_x, pdf_y))
            
            # Update visual feedback
            self._update_selection_visual()
            
    def on_release(self, event):
        """Handle mouse release to finish annotation."""
        if self.drawing:
            self.drawing = False
            
            if len(self.current_selection) > 1:
                page_num = self._get_current_page()
                self._create_selection_annotation(page_num, self.current_selection)
                
            self.current_selection = []
            
    def on_double_click(self, event):
        """Handle double-click for annotation properties."""
        if self.selected_annotation:
            self._show_annotation_properties()
            
    def on_right_click(self, event):
        """Handle right-click for context menu."""
        page_num = self._get_current_page()
        pdf_x, pdf_y = self.editor.canvas_to_pdf_coords(page_num, event.x, event.y)
        
        clicked_annotation = self._get_annotation_at_position(page_num, pdf_x, pdf_y)
        if clicked_annotation:
            self._select_annotation(clicked_annotation)
            self._show_context_menu(event)
        else:
            self._show_add_annotation_menu(event)
            
    def _get_current_page(self):
        """Get the current page number."""
        return 0  # Placeholder
        
    def _get_annotation_at_position(self, page_num, x, y):
        """Get annotation at the specified position."""
        tab_id = self.editor.tab_manager.get_current_tab_id()
        if not tab_id:
            return None
            
        tab_info = self.editor.tab_manager.tabs[tab_id]
        dm = tab_info.get("doc_model")
        if not dm:
            return None
            
        doc = dm.doc
        page = doc[page_num]
        
        # Get annotations on the page
        annotations = page.annots()
        
        for annot in annotations:
            if annot.rect.contains(fitz.Point(x, y)):
                return {
                    "annotation": annot,
                    "page": page_num,
                    "rect": annot.rect,
                    "type": annot.type[1],  # Get annotation type name
                    "content": annot.content
                }
        return None
        
    def _select_annotation(self, annotation_info):
        """Select an annotation for editing."""
        self.selected_annotation = annotation_info
        self._highlight_selected_annotation()
        
    def _clear_selection(self):
        """Clear annotation selection."""
        self.selected_annotation = None
        self._remove_selection_highlight()
        
    def _highlight_selected_annotation(self):
        """Highlight the selected annotation."""
        if not self.selected_annotation:
            return
            
        # Draw selection rectangle around the annotation
        # This would need canvas implementation
        pass
        
    def _remove_selection_highlight(self):
        """Remove selection highlight."""
        # Remove selection rectangle from canvas
        pass
        
    def _update_selection_visual(self):
        """Update visual feedback during annotation drawing."""
        # Update canvas visual feedback
        pass
        
    def _create_note_annotation(self, x, y, page_num):
        """Create a note annotation."""
        # Show dialog to get note content
        note_dialog = tk.Toplevel(self.editor.window)
        note_dialog.title("Add Note")
        note_dialog.geometry("400x300")
        note_dialog.transient(self.editor.window)
        note_dialog.grab_set()
        
        # Center the dialog
        note_dialog.update_idletasks()
        x_pos = (note_dialog.winfo_screenwidth() - note_dialog.winfo_width()) // 2
        y_pos = (note_dialog.winfo_screenheight() - note_dialog.winfo_height()) // 2
        note_dialog.geometry(f"+{x_pos}+{y_pos}")
        
        # Content
        ttk.Label(note_dialog, text="Enter note content:").pack(pady=5)
        
        text_frame = ttk.Frame(note_dialog)
        text_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        text_widget = tk.Text(text_frame, wrap="word", width=40, height=10)
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Buttons
        button_frame = ttk.Frame(note_dialog)
        button_frame.pack(pady=10)
        
        def save_note():
            content = text_widget.get("1.0", "end-1c")
            if content.strip():
                self._add_note_to_pdf(x, y, page_num, content)
            note_dialog.destroy()
            
        ttk.Button(button_frame, text="Save", command=save_note).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Cancel", command=note_dialog.destroy).pack(side="left", padx=5)
        
        text_widget.focus_set()
        
    def _add_note_to_pdf(self, x, y, page_num, content):
        """Add a note annotation to the PDF."""
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
            # Create note annotation
            point = fitz.Point(x, y)
            annot = page.add_text_annot(point, content)
            annot.set_info(content=content)
            annot.update()
            
            # Mark document as modified
            dm.set_modified(True)
            
            # Refresh display
            self.editor.tab_manager.refresh_current_tab()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add note: {str(e)}")
            
    def _create_stamp_annotation(self, x, y, page_num):
        """Create a stamp annotation."""
        # Show stamp selection dialog
        stamp_dialog = tk.Toplevel(self.editor.window)
        stamp_dialog.title("Select Stamp")
        stamp_dialog.geometry("300x200")
        stamp_dialog.transient(self.editor.window)
        stamp_dialog.grab_set()
        
        # Center the dialog
        stamp_dialog.update_idletasks()
        x_pos = (stamp_dialog.winfo_screenwidth() - stamp_dialog.winfo_width()) // 2
        y_pos = (stamp_dialog.winfo_screenheight() - stamp_dialog.winfo_height()) // 2
        stamp_dialog.geometry(f"+{x_pos}+{y_pos}")
        
        # Stamp options
        ttk.Label(stamp_dialog, text="Select stamp type:").pack(pady=5)
        
        stamp_var = tk.StringVar(value="Approved")
        stamps = ["Approved", "Rejected", "Reviewed", "Confidential", "Draft", "Final"]
        
        for stamp in stamps:
            ttk.Radiobutton(stamp_dialog, text=stamp, variable=stamp_var, value=stamp).pack(anchor="w", padx=20)
            
        # Buttons
        button_frame = ttk.Frame(stamp_dialog)
        button_frame.pack(pady=10)
        
        def add_stamp():
            stamp_text = stamp_var.get()
            self._add_stamp_to_pdf(x, y, page_num, stamp_text)
            stamp_dialog.destroy()
            
        ttk.Button(button_frame, text="Add", command=add_stamp).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Cancel", command=stamp_dialog.destroy).pack(side="left", padx=5)
        
    def _add_stamp_to_pdf(self, x, y, page_num, stamp_text):
        """Add a stamp annotation to the PDF."""
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
            # Create stamp annotation
            rect = fitz.Rect(x, y, x + 100, y + 30)
            annot = page.add_stamp_annot(rect, stamp=0)  # Custom stamp
            annot.set_info(content=stamp_text)
            annot.update()
            
            # Mark document as modified
            dm.set_modified(True)
            
            # Refresh display
            self.editor.tab_manager.refresh_current_tab()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add stamp: {str(e)}")
            
    def _create_selection_annotation(self, page_num, selection_points):
        """Create annotation from selection points."""
        if not selection_points:
            return
            
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
            # Create bounding rectangle from selection points
            min_x = min(p.x for p in selection_points)
            max_x = max(p.x for p in selection_points)
            min_y = min(p.y for p in selection_points)
            max_y = max(p.y for p in selection_points)
            
            rect = fitz.Rect(min_x, min_y, max_x, max_y)
            
            # Create annotation based on type
            if self.annotation_type == "highlight":
                annot = page.add_highlight_annot(rect)
            elif self.annotation_type == "underline":
                annot = page.add_underline_annot(rect)
            elif self.annotation_type == "strikeout":
                annot = page.add_strikeout_annot(rect)
            elif self.annotation_type == "squiggly":
                annot = page.add_squiggly_annot(rect)
            else:
                return
                
            # Set annotation properties
            annot.set_colors({"stroke": self.annotation_color})
            annot.set_opacity(self.annotation_opacity)
            annot.update()
            
            # Mark document as modified
            dm.set_modified(True)
            
            # Refresh display
            self.editor.tab_manager.refresh_current_tab()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create annotation: {str(e)}")
            
    def set_annotation_type(self, annotation_type):
        """Set the annotation type."""
        self.annotation_type = annotation_type
        if hasattr(self, 'type_var'):
            self.type_var.set(annotation_type)
            
    def on_type_change(self, event=None):
        """Handle annotation type change."""
        self.annotation_type = self.type_var.get()
        
    def choose_color(self):
        """Open color chooser dialog."""
        color = colorchooser.askcolor(title="Choose annotation color")
        if color[0]:  # RGB values
            self.annotation_color = [c/255.0 for c in color[0]]  # Convert to 0-1 range
            
    def on_opacity_change(self, event=None):
        """Handle opacity change."""
        self.annotation_opacity = self.opacity_var.get()
        
    def delete_selected_annotation(self):
        """Delete the selected annotation."""
        if not self.selected_annotation:
            messagebox.showwarning("No Selection", "Please select an annotation to delete.")
            return
            
        result = messagebox.askyesno("Confirm", "Are you sure you want to delete this annotation?")
        if result:
            self._delete_annotation(self.selected_annotation)
            
    def _delete_annotation(self, annotation_info):
        """Delete an annotation from the PDF."""
        tab_id = self.editor.tab_manager.get_current_tab_id()
        if not tab_id:
            return
            
        tab_info = self.editor.tab_manager.tabs[tab_id]
        dm = tab_info.get("doc_model")
        if not dm:
            return
            
        doc = dm.doc
        page = doc[annotation_info["page"]]
        
        try:
            # Delete annotation
            page.delete_annot(annotation_info["annotation"])
            
            # Mark document as modified
            dm.set_modified(True)
            
            # Clear selection
            self._clear_selection()
            
            # Refresh display
            self.editor.tab_manager.refresh_current_tab()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete annotation: {str(e)}")
            
    def clear_all_annotations(self):
        """Clear all annotations from the current page."""
        result = messagebox.askyesno("Confirm", "Are you sure you want to clear all annotations from this page?")
        if not result:
            return
            
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
        
        try:
            # Delete all annotations
            annotations = list(page.annots())
            for annot in annotations:
                page.delete_annot(annot)
                
            # Mark document as modified
            dm.set_modified(True)
            
            # Clear selection
            self._clear_selection()
            
            # Refresh display
            self.editor.tab_manager.refresh_current_tab()
            
            messagebox.showinfo("Success", f"Cleared {len(annotations)} annotations from the page.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear annotations: {str(e)}")
            
    def _show_annotation_properties(self):
        """Show annotation properties dialog."""
        if not self.selected_annotation:
            return
            
        # Create properties dialog
        props_window = tk.Toplevel(self.editor.window)
        props_window.title("Annotation Properties")
        props_window.geometry("400x300")
        props_window.transient(self.editor.window)
        props_window.grab_set()
        
        # Center the dialog
        props_window.update_idletasks()
        x_pos = (props_window.winfo_screenwidth() - props_window.winfo_width()) // 2
        y_pos = (props_window.winfo_screenheight() - props_window.winfo_height()) // 2
        props_window.geometry(f"+{x_pos}+{y_pos}")
        
        # Properties
        ttk.Label(props_window, text="Annotation Properties", font=("Arial", 12, "bold")).pack(pady=5)
        
        # Type
        ttk.Label(props_window, text=f"Type: {self.selected_annotation['type']}").pack(anchor="w", padx=10)
        
        # Content (editable)
        ttk.Label(props_window, text="Content:").pack(anchor="w", padx=10)
        content_text = tk.Text(props_window, height=5, width=40)
        content_text.pack(padx=10, pady=5, fill="both", expand=True)
        content_text.insert("1.0", self.selected_annotation.get("content", ""))
        
        # Buttons
        button_frame = ttk.Frame(props_window)
        button_frame.pack(pady=10)
        
        def save_properties():
            new_content = content_text.get("1.0", "end-1c")
            self._update_annotation_content(self.selected_annotation, new_content)
            props_window.destroy()
            
        ttk.Button(button_frame, text="Save", command=save_properties).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Cancel", command=props_window.destroy).pack(side="left", padx=5)
        
    def _update_annotation_content(self, annotation_info, new_content):
        """Update annotation content."""
        try:
            annotation_info["annotation"].set_info(content=new_content)
            annotation_info["annotation"].update()
            
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
            messagebox.showerror("Error", f"Failed to update annotation: {str(e)}")
            
    def _show_context_menu(self, event):
        """Show context menu for annotation operations."""
        context_menu = tk.Menu(self.editor.window, tearoff=0)
        context_menu.add_command(label="Edit", command=self._show_annotation_properties)
        context_menu.add_command(label="Delete", command=self.delete_selected_annotation)
        context_menu.add_separator()
        context_menu.add_command(label="Copy", command=self._copy_annotation)
        context_menu.add_command(label="Properties", command=self._show_annotation_properties)
        
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
            
    def _show_add_annotation_menu(self, event):
        """Show context menu for adding annotations."""
        context_menu = tk.Menu(self.editor.window, tearoff=0)
        context_menu.add_command(label="Add Note", command=lambda: self._create_note_annotation_at_event(event))
        context_menu.add_command(label="Add Stamp", command=lambda: self._create_stamp_annotation_at_event(event))
        
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
            
    def _create_note_annotation_at_event(self, event):
        """Create note annotation at event position."""
        page_num = self._get_current_page()
        pdf_x, pdf_y = self.editor.canvas_to_pdf_coords(page_num, event.x, event.y)
        self._create_note_annotation(pdf_x, pdf_y, page_num)
        
    def _create_stamp_annotation_at_event(self, event):
        """Create stamp annotation at event position."""
        page_num = self._get_current_page()
        pdf_x, pdf_y = self.editor.canvas_to_pdf_coords(page_num, event.x, event.y)
        self._create_stamp_annotation(pdf_x, pdf_y, page_num)
        
    def _copy_annotation(self):
        """Copy selected annotation."""
        if self.selected_annotation:
            # This would implement annotation copying
            pass
