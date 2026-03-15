# editor/renderers/pdf_renderer/tools/selection_tool.py
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict, Any, List
import fitz  # PyMuPDF
from ....tool_base import BaseTool

class SelectionTool(BaseTool):
    """General selection tool for PDF elements."""
    
    def __init__(self, editor_window):
        super().__init__(editor_window, name="Selection Tool")
        self.selected_elements = []
        self.selection_rect = None
        self.drag_start = None
        self.is_selecting = False
        self.is_dragging = False
        self.selection_type = "rectangle"  # rectangle, lasso, text
        
    def activate(self):
        """Activate the selection tool."""
        super().activate()
        canvas = self.editor.get_current_canvas()
        if canvas:
            canvas.config(cursor="crosshair")
            canvas.bind("<Button-1>", self.on_click)
            canvas.bind("<B1-Motion>", self.on_drag)
            canvas.bind("<ButtonRelease-1>", self.on_release)
            canvas.bind("<Button-3>", self.on_right_click)
            canvas.bind("<Control-a>", self.select_all)
            canvas.bind("<Delete>", self.delete_selected)
            canvas.bind("<Escape>", self.clear_selection)
        
        self._create_selection_toolbar()
        
    def deactivate(self):
        """Deactivate the selection tool."""
        super().deactivate()
        canvas = self.editor.get_current_canvas()
        if canvas:
            canvas.config(cursor="")
            canvas.unbind("<Button-1>")
            canvas.unbind("<B1-Motion>")
            canvas.unbind("<ButtonRelease-1>")
            canvas.unbind("<Button-3>")
            canvas.unbind("<Control-a>")
            canvas.unbind("<Delete>")
            canvas.unbind("<Escape>")
        
        self.clear_selection()
        self._destroy_selection_toolbar()
        
    def _create_selection_toolbar(self):
        """Create toolbar for selection options."""
        if hasattr(self.editor, 'selection_toolbar'):
            self.editor.selection_toolbar.destroy()
            
        self.editor.selection_toolbar = ttk.Frame(self.editor.toolbar)
        self.editor.selection_toolbar.pack(side="left", fill="x", padx=5)
        
        # Selection type
        ttk.Label(self.editor.selection_toolbar, text="Mode:").pack(side="left", padx=2)
        self.selection_var = tk.StringVar(value=self.selection_type)
        selection_combo = ttk.Combobox(self.editor.selection_toolbar, textvariable=self.selection_var,
                                     values=["rectangle", "lasso", "text"], width=10)
        selection_combo.pack(side="left", padx=2)
        selection_combo.bind("<<ComboboxSelected>>", self.on_selection_type_change)
        
        # Selection actions
        ttk.Button(self.editor.selection_toolbar, text="Select All", 
                  command=self.select_all).pack(side="left", padx=2)
        ttk.Button(self.editor.selection_toolbar, text="Clear", 
                  command=self.clear_selection).pack(side="left", padx=2)
        ttk.Button(self.editor.selection_toolbar, text="Delete", 
                  command=self.delete_selected).pack(side="left", padx=2)
        
        # Clipboard operations
        ttk.Button(self.editor.selection_toolbar, text="Copy", 
                  command=self.copy_selected).pack(side="left", padx=2)
        ttk.Button(self.editor.selection_toolbar, text="Cut", 
                  command=self.cut_selected).pack(side="left", padx=2)
        ttk.Button(self.editor.selection_toolbar, text="Paste", 
                  command=self.paste_clipboard).pack(side="left", padx=2)
        
        # Transform operations
        ttk.Button(self.editor.selection_toolbar, text="Move", 
                  command=self.move_selected).pack(side="left", padx=2)
        ttk.Button(self.editor.selection_toolbar, text="Resize", 
                  command=self.resize_selected).pack(side="left", padx=2)
        
        # Selection info
        self.selection_info = ttk.Label(self.editor.selection_toolbar, text="No selection")
        self.selection_info.pack(side="left", padx=5)
        
    def _destroy_selection_toolbar(self):
        """Remove the selection toolbar."""
        if hasattr(self.editor, 'selection_toolbar'):
            self.editor.selection_toolbar.destroy()
            delattr(self.editor, 'selection_toolbar')
            
    def on_click(self, event):
        """Handle mouse click for selection."""
        page_num = self._get_current_page()
        pdf_x, pdf_y = self.editor.canvas_to_pdf_coords(page_num, event.x, event.y)
        
        # Check if clicking on selected element
        clicked_element = self._get_element_at_position(page_num, pdf_x, pdf_y)
        if clicked_element and clicked_element in self.selected_elements:
            # Start dragging selected elements
            self.is_dragging = True
            self.drag_start = (event.x, event.y)
        else:
            # Clear selection and start new selection
            if not (event.state & 0x4):  # Ctrl not pressed
                self.clear_selection()
                
            if clicked_element:
                # Select single element
                self._add_to_selection(clicked_element)
            else:
                # Start area selection
                self.is_selecting = True
                self.selection_start = (event.x, event.y)
                
    def on_drag(self, event):
        """Handle mouse drag for selection or moving."""
        if self.is_dragging:
            # Move selected elements
            dx = event.x - self.drag_start[0]
            dy = event.y - self.drag_start[1]
            self._move_selected_elements(dx, dy)
            self.drag_start = (event.x, event.y)
        elif self.is_selecting:
            # Update selection rectangle
            self._update_selection_rectangle(event.x, event.y)
            
    def on_release(self, event):
        """Handle mouse release."""
        if self.is_dragging:
            self.is_dragging = False
            self._apply_element_move()
        elif self.is_selecting:
            self.is_selecting = False
            self._finish_area_selection(event.x, event.y)
            
    def on_right_click(self, event):
        """Handle right-click for context menu."""
        page_num = self._get_current_page()
        pdf_x, pdf_y = self.editor.canvas_to_pdf_coords(page_num, event.x, event.y)
        
        clicked_element = self._get_element_at_position(page_num, pdf_x, pdf_y)
        if clicked_element:
            if clicked_element not in self.selected_elements:
                self.clear_selection()
                self._add_to_selection(clicked_element)
            self._show_context_menu(event)
        else:
            self._show_general_context_menu(event)
            
    def _get_current_page(self):
        """Get the current page number."""
        return 0  # Placeholder
        
    def _get_element_at_position(self, page_num, x, y):
        """Get element at the specified position."""
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
        
        # Check for annotations
        for annot in page.annots():
            if annot.rect.contains(point):
                return {
                    "type": "annotation",
                    "element": annot,
                    "page": page_num,
                    "rect": annot.rect
                }
        
        # Check for images
        image_list = page.get_images()
        for img_index, img in enumerate(image_list):
            img_rect = page.get_image_bbox(img[0])
            if img_rect.contains(point):
                return {
                    "type": "image",
                    "element": img,
                    "page": page_num,
                    "rect": img_rect,
                    "index": img_index
                }
        
        # Check for text
        text_blocks = page.get_text("dict")
        for block in text_blocks["blocks"]:
            if block.get("type") == 0:  # Text block
                bbox = fitz.Rect(block["bbox"])
                if bbox.contains(point):
                    return {
                        "type": "text",
                        "element": block,
                        "page": page_num,
                        "rect": bbox
                    }
        
        return None
        
    def _add_to_selection(self, element):
        """Add element to selection."""
        if element not in self.selected_elements:
            self.selected_elements.append(element)
            self._update_selection_visual()
            self._update_selection_info()
            
    def _remove_from_selection(self, element):
        """Remove element from selection."""
        if element in self.selected_elements:
            self.selected_elements.remove(element)
            self._update_selection_visual()
            self._update_selection_info()
            
    def clear_selection(self, event=None):
        """Clear all selections."""
        self.selected_elements = []
        self._update_selection_visual()
        self._update_selection_info()
        
    def select_all(self, event=None):
        """Select all elements on the current page."""
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
        
        self.selected_elements = []
        
        # Select all annotations
        for annot in page.annots():
            self._add_to_selection({
                "type": "annotation",
                "element": annot,
                "page": page_num,
                "rect": annot.rect
            })
        
        # Select all images
        image_list = page.get_images()
        for img_index, img in enumerate(image_list):
            img_rect = page.get_image_bbox(img[0])
            self._add_to_selection({
                "type": "image",
                "element": img,
                "page": page_num,
                "rect": img_rect,
                "index": img_index
            })
        
        # Select all text blocks
        text_blocks = page.get_text("dict")
        for block in text_blocks["blocks"]:
            if block.get("type") == 0:  # Text block
                bbox = fitz.Rect(block["bbox"])
                self._add_to_selection({
                    "type": "text",
                    "element": block,
                    "page": page_num,
                    "rect": bbox
                })
        
    def delete_selected(self, event=None):
        """Delete selected elements."""
        if not self.selected_elements:
            return
            
        result = messagebox.askyesno("Confirm", 
                                   f"Are you sure you want to delete {len(self.selected_elements)} selected elements?")
        if result:
            self._delete_selected_elements()
            
    def _delete_selected_elements(self):
        """Delete the selected elements."""
        tab_id = self.editor.tab_manager.get_current_tab_id()
        if not tab_id:
            return
            
        tab_info = self.editor.tab_manager.tabs[tab_id]
        dm = tab_info.get("doc_model")
        if not dm:
            return
            
        doc = dm.doc
        
        try:
            for element in self.selected_elements:
                page = doc[element["page"]]
                
                if element["type"] == "annotation":
                    page.delete_annot(element["element"])
                elif element["type"] == "image":
                    # Remove image by covering with white rectangle
                    page.add_redact_annot(element["rect"])
                    page.apply_redactions()
                elif element["type"] == "text":
                    # Remove text by covering with white rectangle
                    page.add_redact_annot(element["rect"])
                    page.apply_redactions()
            
            # Mark document as modified
            dm.set_modified(True)
            
            # Clear selection
            self.clear_selection()
            
            # Refresh display
            self.editor.tab_manager.refresh_current_tab()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete elements: {str(e)}")
            
    def copy_selected(self):
        """Copy selected elements to clipboard."""
        if not self.selected_elements:
            messagebox.showwarning("No Selection", "Please select elements to copy.")
            return
            
        # This would implement element copying
        # For now, just show info
        messagebox.showinfo("Copy", f"Copying {len(self.selected_elements)} elements to clipboard.")
        
    def cut_selected(self):
        """Cut selected elements to clipboard."""
        if not self.selected_elements:
            messagebox.showwarning("No Selection", "Please select elements to cut.")
            return
            
        self.copy_selected()
        self.delete_selected()
        
    def paste_clipboard(self):
        """Paste elements from clipboard."""
        # This would implement element pasting
        messagebox.showinfo("Paste", "Pasting elements from clipboard.")
        
    def move_selected(self):
        """Start move mode for selected elements."""
        if not self.selected_elements:
            messagebox.showwarning("No Selection", "Please select elements to move.")
            return
            
        # This would implement interactive move mode
        messagebox.showinfo("Move", "Move mode activated. Click and drag to move elements.")
        
    def resize_selected(self):
        """Start resize mode for selected elements."""
        if not self.selected_elements:
            messagebox.showwarning("No Selection", "Please select elements to resize.")
            return
            
        # This would implement interactive resize mode
        messagebox.showinfo("Resize", "Resize mode activated. Use handles to resize elements.")
        
    def on_selection_type_change(self, event=None):
        """Handle selection type change."""
        self.selection_type = self.selection_var.get()
        
    def _update_selection_rectangle(self, x, y):
        """Update selection rectangle during drag."""
        if hasattr(self, 'selection_start'):
            # Update visual feedback on canvas
            pass
            
    def _finish_area_selection(self, x, y):
        """Finish area selection."""
        if not hasattr(self, 'selection_start'):
            return
            
        start_x, start_y = self.selection_start
        
        # Create selection rectangle
        min_x, max_x = min(start_x, x), max(start_x, x)
        min_y, max_y = min(start_y, y), max(start_y, y)
        
        # Convert to PDF coordinates
        page_num = self._get_current_page()
        pdf_min_x, pdf_min_y = self.editor.canvas_to_pdf_coords(page_num, min_x, min_y)
        pdf_max_x, pdf_max_y = self.editor.canvas_to_pdf_coords(page_num, max_x, max_y)
        
        selection_rect = fitz.Rect(pdf_min_x, pdf_min_y, pdf_max_x, pdf_max_y)
        
        # Find elements in selection rectangle
        self._select_elements_in_rect(selection_rect)
        
        delattr(self, 'selection_start')
        
    def _select_elements_in_rect(self, rect):
        """Select elements within the given rectangle."""
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
        
        # Select annotations in rectangle
        for annot in page.annots():
            if rect.intersects(annot.rect):
                self._add_to_selection({
                    "type": "annotation",
                    "element": annot,
                    "page": page_num,
                    "rect": annot.rect
                })
        
        # Select images in rectangle
        image_list = page.get_images()
        for img_index, img in enumerate(image_list):
            img_rect = page.get_image_bbox(img[0])
            if rect.intersects(img_rect):
                self._add_to_selection({
                    "type": "image",
                    "element": img,
                    "page": page_num,
                    "rect": img_rect,
                    "index": img_index
                })
        
        # Select text blocks in rectangle
        text_blocks = page.get_text("dict")
        for block in text_blocks["blocks"]:
            if block.get("type") == 0:  # Text block
                bbox = fitz.Rect(block["bbox"])
                if rect.intersects(bbox):
                    self._add_to_selection({
                        "type": "text",
                        "element": block,
                        "page": page_num,
                        "rect": bbox
                    })
        
    def _move_selected_elements(self, dx, dy):
        """Move selected elements by delta."""
        # Update visual position during drag
        pass
        
    def _apply_element_move(self):
        """Apply the element move to the PDF."""
        # This would implement the actual move operation
        pass
        
    def _update_selection_visual(self):
        """Update visual feedback for selection."""
        # This would update canvas highlighting
        pass
        
    def _update_selection_info(self):
        """Update selection information display."""
        if hasattr(self, 'selection_info'):
            count = len(self.selected_elements)
            if count == 0:
                self.selection_info.config(text="No selection")
            elif count == 1:
                element_type = self.selected_elements[0]["type"]
                self.selection_info.config(text=f"1 {element_type} selected")
            else:
                self.selection_info.config(text=f"{count} elements selected")
                
    def _show_context_menu(self, event):
        """Show context menu for selected elements."""
        context_menu = tk.Menu(self.editor.window, tearoff=0)
        context_menu.add_command(label="Copy", command=self.copy_selected)
        context_menu.add_command(label="Cut", command=self.cut_selected)
        context_menu.add_command(label="Delete", command=self.delete_selected)
        context_menu.add_separator()
        context_menu.add_command(label="Move", command=self.move_selected)
        context_menu.add_command(label="Resize", command=self.resize_selected)
        context_menu.add_separator()
        context_menu.add_command(label="Properties", command=self._show_element_properties)
        
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
            
    def _show_general_context_menu(self, event):
        """Show general context menu."""
        context_menu = tk.Menu(self.editor.window, tearoff=0)
        context_menu.add_command(label="Select All", command=self.select_all)
        context_menu.add_command(label="Paste", command=self.paste_clipboard)
        
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
            
    def _show_element_properties(self):
        """Show properties dialog for selected elements."""
        if not self.selected_elements:
            return
            
        # For now, just show basic info
        props_window = tk.Toplevel(self.editor.window)
        props_window.title("Element Properties")
        props_window.geometry("400x300")
        
        ttk.Label(props_window, text="Selected Elements", font=("Arial", 12, "bold")).pack(pady=5)
        
        # List selected elements
        listbox = tk.Listbox(props_window)
        listbox.pack(fill="both", expand=True, padx=10, pady=10)
        
        for i, element in enumerate(self.selected_elements):
            element_type = element["type"]
            rect = element["rect"]
            info = f"{i+1}. {element_type.capitalize()} at ({rect.x0:.1f}, {rect.y0:.1f})"
            listbox.insert("end", info)
        
        ttk.Button(props_window, text="Close", command=props_window.destroy).pack(pady=5)
