
# editor/renderers/pdf_renderer/tools/image_manager_tool.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional, Dict, Any
import fitz  # PyMuPDF
from PIL import Image, ImageTk
import io
import os
from ....tool_base import BaseTool

class ImageManagerTool(BaseTool):
    """Comprehensive image management tool for PDFs."""
    
    def __init__(self, editor_window):
        super().__init__(editor_window, name="Image Manager")
        self.selected_image = None
        self.drag_start = None
        self.resize_handle = None
        self.selection_rect = None
        self.is_dragging = False
        self.is_resizing = False
        
    def activate(self):
        """Activate the image management tool."""
        super().activate()
        canvas = self.editor.get_current_canvas()
        if canvas:
            canvas.config(cursor="crosshair")
            canvas.bind("<Button-1>", self.on_click)
            canvas.bind("<B1-Motion>", self.on_drag)
            canvas.bind("<ButtonRelease-1>", self.on_release)
            canvas.bind("<Button-3>", self.on_right_click)
            canvas.bind("<Double-Button-1>", self.on_double_click)
        
        self._create_image_toolbar()
        
    def deactivate(self):
        """Deactivate the image management tool."""
        super().deactivate()
        canvas = self.editor.get_current_canvas()
        if canvas:
            canvas.config(cursor="")
            canvas.unbind("<Button-1>")
            canvas.unbind("<B1-Motion>")
            canvas.unbind("<ButtonRelease-1>")
            canvas.unbind("<Button-3>")
            canvas.unbind("<Double-Button-1>")
        
        self._clear_selection()
        self._destroy_image_toolbar()
        
    def _create_image_toolbar(self):
        """Create toolbar for image operations."""
        if hasattr(self.editor, 'image_toolbar'):
            self.editor.image_toolbar.destroy()
            
        self.editor.image_toolbar = ttk.Frame(self.editor.toolbar)
        self.editor.image_toolbar.pack(side="left", fill="x", padx=5)
        
        # Add image button
        ttk.Button(self.editor.image_toolbar, text="Add Image", 
                  command=self.add_image).pack(side="left", padx=2)
        
        # Remove image button
        ttk.Button(self.editor.image_toolbar, text="Remove Image", 
                  command=self.remove_selected_image).pack(side="left", padx=2)
        
        # Replace image button
        ttk.Button(self.editor.image_toolbar, text="Replace Image", 
                  command=self.replace_selected_image).pack(side="left", padx=2)
        
        # Resize controls
        ttk.Label(self.editor.image_toolbar, text="Scale:").pack(side="left", padx=2)
        self.scale_var = tk.DoubleVar(value=1.0)
        scale_spin = ttk.Spinbox(self.editor.image_toolbar, from_=0.1, to=5.0, 
                               increment=0.1, textvariable=self.scale_var,
                               width=8, command=self.scale_selected_image)
        scale_spin.pack(side="left", padx=2)
        
        # Rotation controls
        ttk.Label(self.editor.image_toolbar, text="Rotate:").pack(side="left", padx=2)
        ttk.Button(self.editor.image_toolbar, text="↻", 
                  command=lambda: self.rotate_selected_image(90)).pack(side="left", padx=1)
        ttk.Button(self.editor.image_toolbar, text="↺", 
                  command=lambda: self.rotate_selected_image(-90)).pack(side="left", padx=1)
        
        # Alignment controls
        ttk.Label(self.editor.image_toolbar, text="Align:").pack(side="left", padx=2)
        ttk.Button(self.editor.image_toolbar, text="←", 
                  command=lambda: self.align_image("left")).pack(side="left", padx=1)
        ttk.Button(self.editor.image_toolbar, text="↔", 
                  command=lambda: self.align_image("center")).pack(side="left", padx=1)
        ttk.Button(self.editor.image_toolbar, text="→", 
                  command=lambda: self.align_image("right")).pack(side="left", padx=1)
        
        # Layer controls
        ttk.Label(self.editor.image_toolbar, text="Layer:").pack(side="left", padx=2)
        ttk.Button(self.editor.image_toolbar, text="Front", 
                  command=self.bring_to_front).pack(side="left", padx=1)
        ttk.Button(self.editor.image_toolbar, text="Back", 
                  command=self.send_to_back).pack(side="left", padx=1)
        
    def _destroy_image_toolbar(self):
        """Remove the image toolbar."""
        if hasattr(self.editor, 'image_toolbar'):
            self.editor.image_toolbar.destroy()
            delattr(self.editor, 'image_toolbar')
            
    def on_click(self, event):
        """Handle mouse click for image selection."""
        page_num = self._get_current_page()
        pdf_x, pdf_y = self.editor.canvas_to_pdf_coords(page_num, event.x, event.y)
        
        # Check if clicking on existing image
        clicked_image = self._get_image_at_position(page_num, pdf_x, pdf_y)
        if clicked_image:
            self._select_image(clicked_image)
            self.drag_start = (event.x, event.y)
            self.is_dragging = True
        else:
            self._clear_selection()
            # Start area selection for new image
            self.selection_start = (event.x, event.y)
            
    def on_drag(self, event):
        """Handle mouse drag for moving or resizing images."""
        if self.is_dragging and self.selected_image:
            # Move selected image
            dx = event.x - self.drag_start[0]
            dy = event.y - self.drag_start[1]
            self._move_image(dx, dy)
            self.drag_start = (event.x, event.y)
        elif hasattr(self, 'selection_start'):
            # Update selection rectangle
            self._update_selection_rect(event.x, event.y)
            
    def on_release(self, event):
        """Handle mouse release."""
        if self.is_dragging:
            self.is_dragging = False
            self._apply_image_move()
        elif hasattr(self, 'selection_start'):
            # Finish area selection
            self._finish_area_selection(event.x, event.y)
            
    def on_double_click(self, event):
        """Handle double-click for image properties."""
        if self.selected_image:
            self._show_image_properties()
            
    def on_right_click(self, event):
        """Handle right-click for context menu."""
        page_num = self._get_current_page()
        pdf_x, pdf_y = self.editor.canvas_to_pdf_coords(page_num, event.x, event.y)
        
        clicked_image = self._get_image_at_position(page_num, pdf_x, pdf_y)
        if clicked_image:
            self._select_image(clicked_image)
            self._show_context_menu(event)
        else:
            self._show_add_image_menu(event)
            
    def _get_current_page(self):
        """Get the current page number."""
        return 0  # Placeholder
        
    def _get_image_at_position(self, page_num, x, y):
        """Get image at the specified position."""
        tab_id = self.editor.tab_manager.get_current_tab_id()
        if not tab_id:
            return None
            
        tab_info = self.editor.tab_manager.tabs[tab_id]
        dm = tab_info.get("doc_model")
        if not dm:
            return None
            
        doc = dm.doc
        page = doc[page_num]
        
        # Get images on the page
        image_list = page.get_images()
        
        for img_index, img in enumerate(image_list):
            # Get image rect
            img_rect = page.get_image_bbox(img[0])
            if img_rect.contains(fitz.Point(x, y)):
                return {
                    "index": img_index,
                    "xref": img[0],
                    "bbox": img_rect,
                    "page": page_num
                }
        return None
        
    def _select_image(self, image_info):
        """Select an image for editing."""
        self.selected_image = image_info
        self._highlight_selected_image()
        
        # Update scale control
        if hasattr(self, 'scale_var'):
            # Calculate current scale based on image size
            # This is a simplified calculation
            self.scale_var.set(1.0)
            
    def _clear_selection(self):
        """Clear image selection."""
        self.selected_image = None
        self._remove_selection_highlight()
        
    def _highlight_selected_image(self):
        """Highlight the selected image."""
        if not self.selected_image:
            return
            
        # Draw selection rectangle around the image
        # This would need canvas implementation
        pass
        
    def _remove_selection_highlight(self):
        """Remove selection highlight."""
        # Remove selection rectangle from canvas
        pass
        
    def _update_selection_rect(self, x, y):
        """Update the selection rectangle during drag."""
        # Update canvas selection rectangle
        pass
        
    def _finish_area_selection(self, x, y):
        """Finish area selection and show image placement dialog."""
        if not hasattr(self, 'selection_start'):
            return
            
        start_x, start_y = self.selection_start
        width = abs(x - start_x)
        height = abs(y - start_y)
        
        if width > 10 and height > 10:  # Minimum size
            # Show dialog to select image file
            self._show_add_image_dialog(min(start_x, x), min(start_y, y), width, height)
            
        delattr(self, 'selection_start')
        
    def add_image(self):
        """Add a new image to the PDF."""
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.tiff"),
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg *.jpeg"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            # Get current page center for default placement
            canvas = self.editor.get_current_canvas()
            if canvas:
                center_x = canvas.winfo_width() // 2
                center_y = canvas.winfo_height() // 2
                self._place_image(file_path, center_x, center_y, 200, 200)
                
    def _show_add_image_dialog(self, x, y, width, height):
        """Show dialog to add image in selected area."""
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.tiff"),
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg *.jpeg"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self._place_image(file_path, x, y, width, height)
            
    def _place_image(self, file_path, x, y, width, height):
        """Place image at specified location."""
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
        
        # Convert canvas coordinates to PDF coordinates
        pdf_x, pdf_y = self.editor.canvas_to_pdf_coords(page_num, x, y)
        pdf_width, pdf_height = self.editor.canvas_to_pdf_coords(page_num, width, height)
        
        # Create rectangle for image placement
        rect = fitz.Rect(pdf_x, pdf_y, pdf_x + pdf_width, pdf_y + pdf_height)
        
        try:
            # Insert image
            page.insert_image(rect, filename=file_path)
            
            # Mark document as modified
            dm.set_modified(True)
            
            # Refresh display
            self.editor.tab_manager.refresh_current_tab()
            
            messagebox.showinfo("Success", "Image added successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add image: {str(e)}")
            
    def remove_selected_image(self):
        """Remove the selected image."""
        if not self.selected_image:
            messagebox.showwarning("No Selection", "Please select an image to remove.")
            return
            
        result = messagebox.askyesno("Confirm", "Are you sure you want to remove this image?")
        if result:
            self._remove_image(self.selected_image)
            
    def _remove_image(self, image_info):
        """Remove an image from the PDF."""
        tab_id = self.editor.tab_manager.get_current_tab_id()
        if not tab_id:
            return
            
        tab_info = self.editor.tab_manager.tabs[tab_id]
        dm = tab_info.get("doc_model")
        if not dm:
            return
            
        doc = dm.doc
        page = doc[image_info["page"]]
        
        try:
            # Remove image by covering it with a white rectangle
            page.add_redact_annot(image_info["bbox"])
            page.apply_redactions()
            
            # Mark document as modified
            dm.set_modified(True)
            
            # Clear selection
            self._clear_selection()
            
            # Refresh display
            self.editor.tab_manager.refresh_current_tab()
            
            messagebox.showinfo("Success", "Image removed successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to remove image: {str(e)}")
            
    def replace_selected_image(self):
        """Replace the selected image with a new one."""
        if not self.selected_image:
            messagebox.showwarning("No Selection", "Please select an image to replace.")
            return
            
        file_path = filedialog.askopenfilename(
            title="Select Replacement Image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.tiff"),
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg *.jpeg"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self._replace_image(self.selected_image, file_path)
            
    def _replace_image(self, image_info, new_file_path):
        """Replace an image with a new one."""
        tab_id = self.editor.tab_manager.get_current_tab_id()
        if not tab_id:
            return
            
        tab_info = self.editor.tab_manager.tabs[tab_id]
        dm = tab_info.get("doc_model")
        if not dm:
            return
            
        doc = dm.doc
        page = doc[image_info["page"]]
        
        try:
            # Remove old image
            page.add_redact_annot(image_info["bbox"])
            page.apply_redactions()
            
            # Add new image in same location
            page.insert_image(image_info["bbox"], filename=new_file_path)
            
            # Mark document as modified
            dm.set_modified(True)
            
            # Refresh display
            self.editor.tab_manager.refresh_current_tab()
            
            messagebox.showinfo("Success", "Image replaced successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to replace image: {str(e)}")
            
    def scale_selected_image(self):
        """Scale the selected image."""
        if not self.selected_image:
            return
            
        scale_factor = self.scale_var.get()
        self._scale_image(self.selected_image, scale_factor)
        
    def _scale_image(self, image_info, scale_factor):
        """Scale an image by the specified factor."""
        # This would involve removing and re-inserting the image at new size
        # Complex implementation needed
        pass
        
    def rotate_selected_image(self, angle):
        """Rotate the selected image."""
        if not self.selected_image:
            return
            
        # This would involve image rotation using PIL/PyMuPDF
        # Complex implementation needed
        pass
        
    def align_image(self, alignment):
        """Align the selected image."""
        if not self.selected_image:
            return
            
        # This would move the image to aligned position
        # Implementation needed
        pass
        
    def bring_to_front(self):
        """Bring selected image to front."""
        if not self.selected_image:
            return
            
        # This would involve layer management
        # Complex implementation needed
        pass
        
    def send_to_back(self):
        """Send selected image to back."""
        if not self.selected_image:
            return
            
        # This would involve layer management
        # Complex implementation needed
        pass
        
    def _move_image(self, dx, dy):
        """Move image by delta x and y."""
        # Update visual position during drag
        pass
        
    def _apply_image_move(self):
        """Apply the image move to the PDF."""
        if not self.selected_image:
            return
            
        # This would involve removing and re-inserting the image
        # Complex implementation needed
        pass
        
    def _show_image_properties(self):
        """Show image properties dialog."""
        if not self.selected_image:
            return
            
        # Create properties dialog
        props_window = tk.Toplevel(self.editor.window)
        props_window.title("Image Properties")
        props_window.geometry("400x300")
        
        # Add property controls
        ttk.Label(props_window, text="Image Properties", font=("Arial", 12, "bold")).pack(pady=5)
        
        # Size information
        ttk.Label(props_window, text="Size:").pack(anchor="w", padx=10)
        bbox = self.selected_image["bbox"]
        size_text = f"Width: {bbox.width:.1f}, Height: {bbox.height:.1f}"
        ttk.Label(props_window, text=size_text).pack(anchor="w", padx=20)
        
        # Position information
        ttk.Label(props_window, text="Position:").pack(anchor="w", padx=10)
        pos_text = f"X: {bbox.x0:.1f}, Y: {bbox.y0:.1f}"
        ttk.Label(props_window, text=pos_text).pack(anchor="w", padx=20)
        
        # Buttons
        button_frame = ttk.Frame(props_window)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="OK", command=props_window.destroy).pack(side="left", padx=5)
        
    def _show_context_menu(self, event):
        """Show context menu for image operations."""
        context_menu = tk.Menu(self.editor.window, tearoff=0)
        context_menu.add_command(label="Remove", command=self.remove_selected_image)
        context_menu.add_command(label="Replace", command=self.replace_selected_image)
        context_menu.add_separator()
        context_menu.add_command(label="Properties", command=self._show_image_properties)
        context_menu.add_separator()
        context_menu.add_command(label="Bring to Front", command=self.bring_to_front)
        context_menu.add_command(label="Send to Back", command=self.send_to_back)
        
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
            
    def _show_add_image_menu(self, event):
        """Show context menu for adding images."""
        context_menu = tk.Menu(self.editor.window, tearoff=0)
        context_menu.add_command(label="Add Image Here", command=self.add_image)
        
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
