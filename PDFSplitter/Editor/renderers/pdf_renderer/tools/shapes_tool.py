# editor/renderers/pdf_renderer/tools/shapes_tool.py
import tkinter as tk
from tkinter import ttk, colorchooser, messagebox
from typing import Optional, Dict, Any, List
import fitz  # PyMuPDF
import math
from ....tool_base import BaseTool

class ShapesTool(BaseTool):
    """Tool for drawing geometric shapes on PDF documents."""
    
    def __init__(self, editor_window):
        super().__init__(editor_window, name="Shapes Tool")
        self.current_shape = "rectangle"
        self.stroke_color = "#000000"
        self.fill_color = "#FFFFFF"
        self.stroke_width = 2
        self.fill_opacity = 0.5
        self.stroke_opacity = 1.0
        self.is_drawing = False
        self.draw_start = None
        self.current_drawing = None
        self.shape_preview = None
        
        self.shape_types = {
            "rectangle": "Rectangle",
            "circle": "Circle",
            "ellipse": "Ellipse",
            "line": "Line",
            "arrow": "Arrow",
            "polygon": "Polygon",
            "freehand": "Freehand"
        }
        
        # Shape-specific settings
        self.arrow_style = "open"  # open, closed, filled
        self.polygon_points = []
        self.freehand_points = []
        
    def activate(self):
        """Activate the shapes tool."""
        super().activate()
        canvas = self.editor.get_current_canvas()
        if canvas:
            canvas.config(cursor="crosshair")
            canvas.bind("<Button-1>", self.on_click)
            canvas.bind("<B1-Motion>", self.on_drag)
            canvas.bind("<ButtonRelease-1>", self.on_release)
            canvas.bind("<Button-3>", self.on_right_click)
            canvas.bind("<Motion>", self.on_motion)
            canvas.bind("<Double-Button-1>", self.on_double_click)
        
        self._create_shapes_toolbar()
        
    def deactivate(self):
        """Deactivate the shapes tool."""
        super().deactivate()
        canvas = self.editor.get_current_canvas()
        if canvas:
            canvas.config(cursor="")
            canvas.unbind("<Button-1>")
            canvas.unbind("<B1-Motion>")
            canvas.unbind("<ButtonRelease-1>")
            canvas.unbind("<Button-3>")
            canvas.unbind("<Motion>")
            canvas.unbind("<Double-Button-1>")
        
        self._cancel_current_drawing()
        self._destroy_shapes_toolbar()
        
    def _create_shapes_toolbar(self):
        """Create toolbar for shapes options."""
        if hasattr(self.editor, 'shapes_toolbar'):
            self.editor.shapes_toolbar.destroy()
            
        self.editor.shapes_toolbar = ttk.Frame(self.editor.toolbar)
        self.editor.shapes_toolbar.pack(side="left", fill="x", padx=5)
        
        # Shape selection
        ttk.Label(self.editor.shapes_toolbar, text="Shape:").pack(side="left", padx=2)
        self.shape_var = tk.StringVar(value=self.current_shape)
        shape_combo = ttk.Combobox(self.editor.shapes_toolbar, textvariable=self.shape_var,
                                  values=list(self.shape_types.keys()), width=10)
        shape_combo.pack(side="left", padx=2)
        shape_combo.bind("<<ComboboxSelected>>", self._on_shape_change)
        
        # Stroke color
        ttk.Label(self.editor.shapes_toolbar, text="Stroke:").pack(side="left", padx=2)
        self.stroke_color_btn = tk.Button(self.editor.shapes_toolbar, bg=self.stroke_color,
                                         width=3, height=1, command=self._choose_stroke_color)
        self.stroke_color_btn.pack(side="left", padx=2)
        
        # Stroke width
        ttk.Label(self.editor.shapes_toolbar, text="Width:").pack(side="left", padx=2)
        self.stroke_width_var = tk.IntVar(value=self.stroke_width)
        stroke_width_spin = ttk.Spinbox(self.editor.shapes_toolbar, from_=1, to=20,
                                       textvariable=self.stroke_width_var, width=5,
                                       command=self._on_stroke_width_change)
        stroke_width_spin.pack(side="left", padx=2)
        
        # Fill color
        ttk.Label(self.editor.shapes_toolbar, text="Fill:").pack(side="left", padx=2)
        self.fill_color_btn = tk.Button(self.editor.shapes_toolbar, bg=self.fill_color,
                                       width=3, height=1, command=self._choose_fill_color)
        self.fill_color_btn.pack(side="left", padx=2)
        
        # Fill opacity
        ttk.Label(self.editor.shapes_toolbar, text="Fill Opacity:").pack(side="left", padx=2)
        self.fill_opacity_var = tk.DoubleVar(value=self.fill_opacity)
        fill_opacity_scale = ttk.Scale(self.editor.shapes_toolbar, from_=0.0, to=1.0,
                                      variable=self.fill_opacity_var, orient="horizontal",
                                      length=60, command=self._on_fill_opacity_change)
        fill_opacity_scale.pack(side="left", padx=2)
        
        # Stroke opacity
        ttk.Label(self.editor.shapes_toolbar, text="Stroke Opacity:").pack(side="left", padx=2)
        self.stroke_opacity_var = tk.DoubleVar(value=self.stroke_opacity)
        stroke_opacity_scale = ttk.Scale(self.editor.shapes_toolbar, from_=0.0, to=1.0,
                                        variable=self.stroke_opacity_var, orient="horizontal",
                                        length=60, command=self._on_stroke_opacity_change)
        stroke_opacity_scale.pack(side="left", padx=2)
        
        # Shape-specific controls
        self.shape_controls_frame = ttk.Frame(self.editor.shapes_toolbar)
        self.shape_controls_frame.pack(side="left", padx=5)
        
        # Clear shapes button
        ttk.Separator(self.editor.shapes_toolbar, orient="vertical").pack(side="left", fill="y", padx=5)
        ttk.Button(self.editor.shapes_toolbar, text="Clear Shapes",
                  command=self._clear_shapes).pack(side="left", padx=2)
        
        self._update_shape_controls()
        
    def _destroy_shapes_toolbar(self):
        """Remove the shapes toolbar."""
        if hasattr(self.editor, 'shapes_toolbar'):
            self.editor.shapes_toolbar.destroy()
            delattr(self.editor, 'shapes_toolbar')
            
    def _update_shape_controls(self):
        """Update shape-specific controls."""
        # Clear existing controls
        for widget in self.shape_controls_frame.winfo_children():
            widget.destroy()
            
        if self.current_shape == "arrow":
            ttk.Label(self.shape_controls_frame, text="Arrow Style:").pack(side="left", padx=2)
            self.arrow_style_var = tk.StringVar(value=self.arrow_style)
            arrow_combo = ttk.Combobox(self.shape_controls_frame, textvariable=self.arrow_style_var,
                                      values=["open", "closed", "filled"], width=8)
            arrow_combo.pack(side="left", padx=2)
            arrow_combo.bind("<<ComboboxSelected>>", self._on_arrow_style_change)
            
        elif self.current_shape == "polygon":
            ttk.Label(self.shape_controls_frame, text="Polygon:").pack(side="left", padx=2)
            ttk.Button(self.shape_controls_frame, text="Finish",
                      command=self._finish_polygon).pack(side="left", padx=2)
            ttk.Button(self.shape_controls_frame, text="Cancel",
                      command=self._cancel_polygon).pack(side="left", padx=2)
            
        elif self.current_shape == "freehand":
            ttk.Label(self.shape_controls_frame, text="Freehand:").pack(side="left", padx=2)
            ttk.Button(self.shape_controls_frame, text="Smooth",
                      command=self._smooth_freehand).pack(side="left", padx=2)
            
    def _choose_stroke_color(self):
        """Choose stroke color."""
        color = colorchooser.askcolor(title="Choose stroke color")
        if color[1]:
            self.stroke_color = color[1]
            self.stroke_color_btn.config(bg=color[1])
            
    def _choose_fill_color(self):
        """Choose fill color."""
        color = colorchooser.askcolor(title="Choose fill color")
        if color[1]:
            self.fill_color = color[1]
            self.fill_color_btn.config(bg=color[1])
            
    def _on_shape_change(self, event=None):
        """Handle shape type change."""
        self.current_shape = self.shape_var.get()
        self._update_shape_controls()
        
    def _on_stroke_width_change(self):
        """Handle stroke width change."""
        self.stroke_width = self.stroke_width_var.get()
        
    def _on_fill_opacity_change(self, value):
        """Handle fill opacity change."""
        self.fill_opacity = float(value)
        
    def _on_stroke_opacity_change(self, value):
        """Handle stroke opacity change."""
        self.stroke_opacity = float(value)
        
    def _on_arrow_style_change(self, event=None):
        """Handle arrow style change."""
        self.arrow_style = self.arrow_style_var.get()
        
    def on_click(self, event):
        """Handle mouse click for shape drawing."""
        page_num = self._get_current_page()
        pdf_x, pdf_y = self.editor.canvas_to_pdf_coords(page_num, event.x, event.y)
        
        if self.current_shape == "polygon":
            self._add_polygon_point(pdf_x, pdf_y)
        elif self.current_shape == "freehand":
            self._start_freehand_drawing(pdf_x, pdf_y)
        else:
            # Start drawing regular shape
            self.is_drawing = True
            self.draw_start = (event.x, event.y)
            self._start_shape_preview(event.x, event.y)
            
    def on_drag(self, event):
        """Handle mouse drag for shape drawing."""
        if self.is_drawing:
            if self.current_shape == "freehand":
                self._continue_freehand_drawing(event.x, event.y)
            else:
                self._update_shape_preview(event.x, event.y)
                
    def on_release(self, event):
        """Handle mouse release for shape drawing."""
        if self.is_drawing:
            self.is_drawing = False
            if self.current_shape == "freehand":
                self._finish_freehand_drawing()
            else:
                self._finish_shape_drawing(event.x, event.y)
                
    def on_right_click(self, event):
        """Handle right-click for shape context menu."""
        if self.current_shape == "polygon":
            self._finish_polygon()
        else:
            self._show_shapes_context_menu(event)
            
    def on_motion(self, event):
        """Handle mouse motion for shape preview."""
        if self.is_drawing and self.current_shape != "freehand":
            self._update_shape_preview(event.x, event.y)
            
    def on_double_click(self, event):
        """Handle double-click for shape finalization."""
        if self.current_shape == "polygon":
            self._finish_polygon()
            
    def _get_current_page(self):
        """Get the current page number."""
        return 0  # Placeholder
        
    def _start_shape_preview(self, x, y):
        """Start shape preview."""
        # This would show a preview of the shape being drawn
        pass
        
    def _update_shape_preview(self, x, y):
        """Update shape preview."""
        # This would update the preview of the shape being drawn
        pass
        
    def _finish_shape_drawing(self, x, y):
        """Finish drawing a shape."""
        if not self.draw_start:
            return
            
        page_num = self._get_current_page()
        start_x, start_y = self.draw_start
        
        # Convert to PDF coordinates
        pdf_start_x, pdf_start_y = self.editor.canvas_to_pdf_coords(page_num, start_x, start_y)
        pdf_end_x, pdf_end_y = self.editor.canvas_to_pdf_coords(page_num, x, y)
        
        # Create shape based on type
        if self.current_shape == "rectangle":
            self._create_rectangle(pdf_start_x, pdf_start_y, pdf_end_x, pdf_end_y)
        elif self.current_shape == "circle":
            self._create_circle(pdf_start_x, pdf_start_y, pdf_end_x, pdf_end_y)
        elif self.current_shape == "ellipse":
            self._create_ellipse(pdf_start_x, pdf_start_y, pdf_end_x, pdf_end_y)
        elif self.current_shape == "line":
            self._create_line(pdf_start_x, pdf_start_y, pdf_end_x, pdf_end_y)
        elif self.current_shape == "arrow":
            self._create_arrow(pdf_start_x, pdf_start_y, pdf_end_x, pdf_end_y)
            
        self.draw_start = None
        
    def _create_rectangle(self, x1, y1, x2, y2):
        """Create a rectangle annotation."""
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
            rect = fitz.Rect(min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
            
            # Create rectangle annotation
            annot = page.add_rect_annot(rect)
            
            # Set properties
            self._set_shape_properties(annot)
            
            # Mark document as modified
            dm.set_modified(True)
            
            # Refresh display
            self.editor.tab_manager.refresh_current_tab()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create rectangle: {str(e)}")
            
    def _create_circle(self, x1, y1, x2, y2):
        """Create a circle annotation."""
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        radius = min(abs(x2 - x1), abs(y2 - y1)) / 2
        
        # Create ellipse with equal width and height
        self._create_ellipse(center_x - radius, center_y - radius,
                           center_x + radius, center_y + radius)
        
    def _create_ellipse(self, x1, y1, x2, y2):
        """Create an ellipse annotation."""
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
            rect = fitz.Rect(min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
            
            # Create ellipse annotation
            annot = page.add_circle_annot(rect)
            
            # Set properties
            self._set_shape_properties(annot)
            
            # Mark document as modified
            dm.set_modified(True)
            
            # Refresh display
            self.editor.tab_manager.refresh_current_tab()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create ellipse: {str(e)}")
            
    def _create_line(self, x1, y1, x2, y2):
        """Create a line annotation."""
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
            point1 = fitz.Point(x1, y1)
            point2 = fitz.Point(x2, y2)
            
            # Create line annotation
            annot = page.add_line_annot(point1, point2)
            
            # Set properties
            self._set_shape_properties(annot)
            
            # Mark document as modified
            dm.set_modified(True)
            
            # Refresh display
            self.editor.tab_manager.refresh_current_tab()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create line: {str(e)}")
            
    def _create_arrow(self, x1, y1, x2, y2):
        """Create an arrow annotation."""
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
            point1 = fitz.Point(x1, y1)
            point2 = fitz.Point(x2, y2)
            
            # Create line annotation with arrow
            annot = page.add_line_annot(point1, point2)
            
            # Set arrow properties
            if self.arrow_style == "open":
                annot.set_line_ends(fitz.PDF_ANNOT_LE_NONE, fitz.PDF_ANNOT_LE_OPEN_ARROW)
            elif self.arrow_style == "closed":
                annot.set_line_ends(fitz.PDF_ANNOT_LE_NONE, fitz.PDF_ANNOT_LE_CLOSED_ARROW)
            elif self.arrow_style == "filled":
                annot.set_line_ends(fitz.PDF_ANNOT_LE_NONE, fitz.PDF_ANNOT_LE_CLOSED_ARROW)
            
            # Set properties
            self._set_shape_properties(annot)
            
            # Mark document as modified
            dm.set_modified(True)
            
            # Refresh display
            self.editor.tab_manager.refresh_current_tab()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create arrow: {str(e)}")
            
    def _add_polygon_point(self, x, y):
        """Add a point to the polygon."""
        self.polygon_points.append((x, y))
        # Update polygon preview
        self._update_polygon_preview()
        
    def _finish_polygon(self):
        """Finish drawing the polygon."""
        if len(self.polygon_points) < 3:
            messagebox.showwarning("Warning", "A polygon needs at least 3 points.")
            return
            
        self._create_polygon(self.polygon_points)
        self.polygon_points = []
        
    def _cancel_polygon(self):
        """Cancel polygon drawing."""
        self.polygon_points = []
        # Clear polygon preview
        
    def _create_polygon(self, points):
        """Create a polygon annotation."""
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
            # Convert points to fitz.Point objects
            fitz_points = [fitz.Point(x, y) for x, y in points]
            
            # Create polygon annotation
            annot = page.add_polygon_annot(fitz_points)
            
            # Set properties
            self._set_shape_properties(annot)
            
            # Mark document as modified
            dm.set_modified(True)
            
            # Refresh display
            self.editor.tab_manager.refresh_current_tab()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create polygon: {str(e)}")
            
    def _start_freehand_drawing(self, x, y):
        """Start freehand drawing."""
        self.freehand_points = [(x, y)]
        self.is_drawing = True
        
    def _continue_freehand_drawing(self, x, y):
        """Continue freehand drawing."""
        page_num = self._get_current_page()
        pdf_x, pdf_y = self.editor.canvas_to_pdf_coords(page_num, x, y)
        self.freehand_points.append((pdf_x, pdf_y))
        
    def _finish_freehand_drawing(self):
        """Finish freehand drawing."""
        if len(self.freehand_points) < 2:
            return
            
        self._create_freehand_path(self.freehand_points)
        self.freehand_points = []
        
    def _create_freehand_path(self, points):
        """Create a freehand path annotation."""
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
            # Convert points to fitz.Point objects
            fitz_points = [fitz.Point(x, y) for x, y in points]
            
            # Create ink annotation for freehand drawing
            annot = page.add_ink_annot([fitz_points])
            
            # Set properties
            self._set_shape_properties(annot)
            
            # Mark document as modified
            dm.set_modified(True)
            
            # Refresh display
            self.editor.tab_manager.refresh_current_tab()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create freehand path: {str(e)}")
            
    def _smooth_freehand(self):
        """Smooth the freehand drawing."""
        # This would implement smoothing algorithm
        messagebox.showinfo("Smooth", "Smoothing freehand drawing.")
        
    def _set_shape_properties(self, annot):
        """Set properties for a shape annotation."""
        # Set stroke color
        stroke_rgb = self._hex_to_rgb(self.stroke_color)
        annot.set_colors({"stroke": stroke_rgb})
        
        # Set fill color if applicable
        if self.fill_opacity > 0:
            fill_rgb = self._hex_to_rgb(self.fill_color)
            annot.set_colors({"fill": fill_rgb})
            
        # Set border width
        annot.set_border(width=self.stroke_width)
        
        # Set opacity
        annot.set_opacity(self.stroke_opacity)
        
        # Update annotation
        annot.update()
        
    def _hex_to_rgb(self, hex_color):
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))
        
    def _update_polygon_preview(self):
        """Update polygon preview."""
        # This would update the visual preview of the polygon
        pass
        
    def _clear_shapes(self):
        """Clear all shapes on the current page."""
        result = messagebox.askyesno("Confirm", "Are you sure you want to remove all shapes on this page?")
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
            # Remove shape annotations
            shape_types = ["Square", "Circle", "Line", "Polygon", "Ink"]
            annotations_to_remove = []
            
            for annot in page.annots():
                if annot.type[1] in shape_types:
                    annotations_to_remove.append(annot)
            
            for annot in annotations_to_remove:
                page.delete_annot(annot)
            
            # Mark document as modified
            dm.set_modified(True)
            
            # Refresh display
            self.editor.tab_manager.refresh_current_tab()
            
            messagebox.showinfo("Success", f"Removed {len(annotations_to_remove)} shapes.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear shapes: {str(e)}")
            
    def _show_shapes_context_menu(self, event):
        """Show context menu for shapes."""
        context_menu = tk.Menu(self.editor.window, tearoff=0)
        context_menu.add_command(label="Rectangle", command=lambda: self._set_shape_type("rectangle"))
        context_menu.add_command(label="Circle", command=lambda: self._set_shape_type("circle"))
        context_menu.add_command(label="Line", command=lambda: self._set_shape_type("line"))
        context_menu.add_command(label="Arrow", command=lambda: self._set_shape_type("arrow"))
        context_menu.add_separator()
        context_menu.add_command(label="Clear All Shapes", command=self._clear_shapes)
        
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
            
    def _set_shape_type(self, shape_type):
        """Set the current shape type."""
        self.current_shape = shape_type
        self.shape_var.set(shape_type)
        self._update_shape_controls()
        
    def _cancel_current_drawing(self):
        """Cancel any current drawing operation."""
        self.is_drawing = False
        self.draw_start = None
        self.current_drawing = None
        self.shape_preview = None
        self.polygon_points = []
        self.freehand_points = []
