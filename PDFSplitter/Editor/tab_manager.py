# editor/tab_manager.py
import os
import tkinter as tk
from tkinter import ttk
from typing import Dict
from editor.document_model import DocumentModel
from editor.text_overlay import TextOverlay

def _get_filename_from_path(path: str) -> str:
    """Extract filename from path, handling both Unix and Windows paths."""
    if not path:
        return "Untitled"
    
    # Handle both forward and backward slashes
    if '\\' in path:
        return path.split('\\')[-1]
    else:
        return os.path.basename(path)

class TabManager:
    """
    Wraps a ttk.Notebook. Manages multiple open documents, each in its own tab.
    Each tab holds:
      - a scrollable Canvas for showing page images
      - navigation controls (Prev/Next page, zoom slider)
      - a TextOverlay instance for editable spans
      - references to its DocumentModel + PDFRenderer
    """

    def __init__(self, master_frame, on_tab_change_callback=None):
        self.notebook = ttk.Notebook(master_frame)
        self.tabs: Dict[str, Dict] = {}
        # tabs: { tab_id: { container, doc_model?, renderer?, overlay?, canvas?, preview_widget?, preview_path, preview_name, ... } }
        self.on_tab_change_callback = on_tab_change_callback
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        self.notebook.pack(fill="both", expand=True)
    
    def _bind_scroll_events(self, canvas):
        # Mouse wheel (Windows/macOS)
        canvas.bind_all("<MouseWheel>", lambda e: self._handle_scroll_event("up" if e.delta > 0 else "down", abs(e.delta//120)))
        # Mouse wheel (Linux)
        canvas.bind_all("<Button-4>", lambda e: self._handle_scroll_event("up", 1))
        canvas.bind_all("<Button-5>", lambda e: self._handle_scroll_event("down", 1))
        
        # Arrow keys (vertical)
        canvas.bind_all("<Up>", lambda e: self._handle_scroll_event("up", 1))
        canvas.bind_all("<Down>", lambda e: self._handle_scroll_event("down", 1))

        # Arrow keys (horizontal)
        canvas.bind_all("<Left>", lambda e: self._handle_scroll_event("left", 1))
        canvas.bind_all("<Right>", lambda e: self._handle_scroll_event("right", 1))

        # Home/End - these might need special handling
        canvas.bind_all("<Home>", lambda e: self._handle_scroll_event("up", 999))
        canvas.bind_all("<End>", lambda e: self._handle_scroll_event("down", 999))

        # Page Up/Down
        canvas.bind_all("<Prior>", lambda e: self._handle_scroll_event("up", 10))  # Page Up
        canvas.bind_all("<Next>", lambda e: self._handle_scroll_event("down", 10))    # Page Down

    def _handle_scroll_event(self, direction: str, amount: int):
        """Handle scroll events by delegating to the current tab's renderer."""
        current_tab_id = self.get_current_tab_id()
        if not current_tab_id:
            return
        
        tab_info = self.tabs.get(current_tab_id)
        if not tab_info:
            return
        
        # Try to get the renderer from the tab info
        renderer = tab_info.get("renderer")
        if renderer and hasattr(renderer, 'scroll'):
            try:
                renderer.scroll(current_tab_id, direction, amount)
            except Exception as e:
                # Fallback to canvas scrolling if renderer fails
                self._fallback_scroll(current_tab_id, direction, amount)
        else:
            # Fallback to canvas scrolling if no renderer
            self._fallback_scroll(current_tab_id, direction, amount)
    
    def _fallback_scroll(self, tab_id: str, direction: str, amount: int):
        """Fallback scrolling method for when renderer scrolling fails."""
        tab_info = self.tabs.get(tab_id)
        if not tab_info:
            return
        
        # Try to get a scrollable widget
        canvas = tab_info.get("canvas")
        if not canvas:
            # Try preview_widget
            canvas = tab_info.get("preview_widget")
        
        if canvas and hasattr(canvas, 'yview_scroll'):
            if direction == "up":
                canvas.yview_scroll(-amount, "units")
            elif direction == "down":
                canvas.yview_scroll(amount, "units")
        
        if canvas and hasattr(canvas, 'xview_scroll'):
            if direction == "left":
                canvas.xview_scroll(-amount, "units")
            elif direction == "right":
                canvas.xview_scroll(amount, "units")

    def add_tab(self,
                doc_model: DocumentModel,
                renderer,              # a concrete renderer instance
                overlay=None           # optional TextOverlay or custom overlay
    ) -> str:
        """
        Create a new tab driven by the given renderer instance (and overlay).
        Returns the tab_id.
        """
        tab_frame = ttk.Frame(self.notebook)
        tab_id    = str(id(tab_frame))

        # 1) Canvas + scrollbars
        canvas   = tk.Canvas(tab_frame, bg="grey")
        h_scroll = ttk.Scrollbar(tab_frame, orient="horizontal", command=canvas.xview)
        v_scroll = ttk.Scrollbar(tab_frame, orient="vertical",   command=canvas.yview)
        canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        h_scroll.grid(row=1, column=0, sticky="ew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        tab_frame.rowconfigure(0, weight=1)
        tab_frame.columnconfigure(0, weight=1)

        # 2) Overlay (default TextOverlay if none provided)
        if overlay is None:
            overlay = TextOverlay(canvas,
                                  page_number=0,
                                  renderer=renderer,
                                  doc_model=doc_model)

        # 3) Register in our tabs dict
        self.tabs[tab_id] = {
            "container":   tab_frame,
            "doc_model":   doc_model,
            "renderer":    renderer,
            "renderer_instance": renderer,  # For toolbar manager compatibility
            "overlay":     overlay,
            "canvas":      canvas,
            "page_number": 0,
            "zoom":        1.0
        }

        # 4) Set up renderer scrolling
        if hasattr(renderer, 'set_scroll_widget'):
            renderer.set_scroll_widget(canvas)

        # 4) Wire resize & initial draw
        canvas.bind("<Configure>",
                    lambda e, tid=tab_id: self._on_canvas_configure(tid, e))
        canvas.after_idle(
            lambda: self._render_page_in_tab(tab_id, page_number=0, zoom=None)
        )
        self._bind_scroll_events(canvas)
        # 5) Add to the Notebook
        display = _get_filename_from_path(doc_model.filepath or "Untitled") + (" ∗" if doc_model.modified else "")
        self.notebook.add(tab_frame, text=display)
        # Add tooltip with full path
        self._add_tab_tooltip(tab_frame, doc_model.filepath or "Untitled")
        self.notebook.select(tab_frame)
        return tab_id

    def register_tab_widget(self, tab_frame, display_name: str, doc_model=None, preview_path: str = None, renderer=None):
        """
        Register an already-created Frame (tab_frame) as a new tab.
        For previews, doc_model is None, and preview_path must be provided.
        """
        tab_id = str(id(tab_frame))
        info = {"container": tab_frame, "doc_model": doc_model}
        
        # Store renderer if provided
        if renderer:
            info["renderer"] = renderer
            info["renderer_instance"] = renderer  # For toolbar manager compatibility
        
        if doc_model is None and preview_path:
            info.update({
                "preview_path": preview_path,
                "preview_name": display_name
            })
        self.tabs[tab_id] = info
        
        # Display only filename, not full path
        tab_text = _get_filename_from_path(display_name) if display_name else "Untitled"
        self.notebook.add(tab_frame, text=tab_text)
        
        # Add tooltip with full path
        full_path = preview_path if preview_path else display_name
        self._add_tab_tooltip(tab_frame, full_path)
        
        self.notebook.select(tab_frame)
        return tab_id

    def _on_canvas_configure(self, tab_id: str, event):
        info = self.tabs.get(tab_id)
        if not info or info.get("doc_model") is None:
            return
        self._render_page_in_tab(tab_id,
                                 page_number=info["page_number"],
                                 zoom=None)
    
    def _render_page_in_tab(self, tab_id: str, page_number: int, zoom: float):
        info     = self.tabs[tab_id]
        canvas   = info["canvas"]
        renderer = info["renderer"]
        overlay  = info["overlay"]
        doc_model = info["doc_model"]

        # 1) Clear old image & overlays
        canvas.delete("all")
        overlay.clear_overlays()
        # make a fresh list to hold our images
        info["images"] = []

       # 1) if zoom=None → compute a fit-to-width value, but don't overwrite info["zoom"]
        if zoom is None:
            base = renderer.get_page_image(0, zoom=info.get("zoom", 1.0))
            avail_w = canvas.winfo_width() or base.width()
            zoom_to_use = (avail_w * 0.9) / base.width()
        else:
            zoom_to_use = zoom
            # only store when user (or code) explicitly passed a zoom
            info["zoom"] = zoom

        # 3) Render all pages at that zoom, stacking vertically
        y_off = 20
        gap  = 30
        max_w = 0
        for i in range(doc_model.get_page_count()):
            img = renderer.get_page_image(i, zoom=zoom_to_use)
            iw, ih = img.width(), img.height()
            cw = canvas.winfo_width()
            x0 = max((cw - iw)//2, 0)
            if "images" not in info:
                info["images"] = []
            img = renderer.get_page_image(i, zoom=zoom_to_use)
            info["images"].append(img)  # keep a reference to avoid GC
            canvas.create_image(x0, y_off, anchor="nw", image=img)
            y_off += ih + gap
            max_w = max(max_w, iw)
        # 4) Adjust scrollregion
        canvas.config(scrollregion=(
            0, 0,
            max(max_w, canvas.winfo_width()),
            y_off
        ))

        # 5) Scroll back to top/left
        canvas.yview_moveto(0)
        canvas.xview_moveto(0)

        # 6) Save state and rebuild overlays
        info["page_number"] = page_number
        overlay.page_number  = page_number
        overlay.refresh(zoom=zoom_to_use)

    def switch_to_page(self, tab_id: str, page_number: int):
        info = self.tabs[tab_id]
        total = info["doc_model"].get_page_count()
        if 0 <= page_number < total:
            zoom = info["zoom"]
            self._render_page_in_tab(tab_id, page_number, zoom)

    def close_tab(self, tab_id: str):
        info = self.tabs.pop(tab_id, None)
        if info:
            self.notebook.forget(info["container"])
    
    def _on_tab_changed(self, event):
        sel = event.widget.select()
        # Find which tab_id corresponds to sel
        for tid, info in self.tabs.items():
            if info["container"] == sel:
                if self.on_tab_change_callback:
                    self.on_tab_change_callback(tid)
                break

    def mark_tab_dirty(self, tab_id: str):
        info = self.tabs[tab_id]
        dm = info.get("doc_model")
        if dm:
            # PDF case
            base = _get_filename_from_path(dm.filepath) if dm.filepath else "Untitled"
            display = f"{base} ∗" if dm.modified else base
        else:
            # Preview case (text files)
            base = _get_filename_from_path(info.get("preview_name", "Untitled"))
            display = f"{base} ∗" if info.get("modified_text", False) else base
        
        # Update the tab display
        self.notebook.tab(info["container"], text=display)
    
    def refresh_tab_label(self, tab_id: str):
        info = self.tabs[tab_id]
        dm = info.get("doc_model")
        if dm:
            base = _get_filename_from_path(dm.filepath) if dm.filepath else "Untitled"
            display = f"{base} ∗" if dm.modified else base
        else:
            base = _get_filename_from_path(info.get("preview_name", "Untitled"))
            display = f"{base} ∗" if info.get("modified_text", False) else base

        self.notebook.tab(info["container"], text=display)

    def get_current_tab_id(self) -> str:
        sel = self.notebook.select()
        for tid, info in self.tabs.items():
            if str(info["container"]) == sel:
                return tid
        return None

    def get_current_canvas(self):
        tid = self.get_current_tab_id()
        if not tid:
            return None
        return self.tabs[tid]["canvas"]

    def get_current_page_number(self):
        tid = self.get_current_tab_id()
        if not tid:
            return None
        return self.tabs[tid]["page_number"]

    def get_current_doc_model(self):
        tid = self.get_current_tab_id()
        if not tid:
            return None
        return self.tabs[tid]["doc_model"]

    def get_current_overlay(self):
        tid = self.get_current_tab_id()
        if not tid:
            return None
        return self.tabs[tid]["overlay"]

    def _add_tab_tooltip(self, tab_frame, full_path: str):
        """Add a tooltip to a tab that shows the full file path."""
        try:
            # Get the tab index
            tab_index = self.notebook.index(tab_frame)
            
            # Store tooltip reference
            if not hasattr(self, '_tooltip_window'):
                self._tooltip_window = None
            
            # Create tooltip functionality
            def show_tooltip(event):
                # Get the tab at the mouse position
                try:
                    tab_at_pos = self.notebook.identify_tab(event.x, event.y)
                    if tab_at_pos is not None and int(tab_at_pos) == tab_index:
                        # Only show tooltip if mouse is over this specific tab
                        if self._tooltip_window is None:
                            self._tooltip_window = tk.Toplevel(self.notebook)
                            self._tooltip_window.wm_overrideredirect(True)
                            self._tooltip_window.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
                            
                            label = tk.Label(self._tooltip_window, text=full_path, 
                                           background="#ffffe0", relief="solid", borderwidth=1,
                                           font=("tahoma", "8", "normal"))
                            label.pack()
                    else:
                        # Mouse is over a different tab, hide tooltip
                        hide_tooltip(None)
                except Exception:
                    pass
            
            def hide_tooltip(event):
                if self._tooltip_window is not None:
                    self._tooltip_window.destroy()
                    self._tooltip_window = None
            
            # Bind events to the notebook (using add=True to not override existing bindings)
            self.notebook.bind("<Motion>", show_tooltip, add=True)
            self.notebook.bind("<Leave>", hide_tooltip, add=True)
            self.notebook.bind("<Button-1>", hide_tooltip, add=True)  # Hide on click
            
        except Exception as e:
            # If tooltip fails, just continue without it
            pass
