# pdf_renderer_controller.py  –  complete version (2025-05-31)

from __future__ import annotations

import datetime
import gc
import io
import os
import shutil
import tempfile
import tkinter as tk
from dataclasses import dataclass, field
from typing import List, Tuple, Dict

import fitz                              # PyMuPDF
from PIL import Image, ImageTk
from tkinter import colorchooser, filedialog, messagebox, simpledialog, ttk

from PDFUtility.PDFLogger import Logger
from SettingsController import SettingsController
from Utility import Utility


# ───────────────────────────────────────── helpers ──────────────────────────────────────────
@dataclass
class Annotation:
    """In-memory description of a drawn object."""
    tool: str                                          # pen | line | rect | highlight | textbox
    coords: Tuple[int, int, int, int]                  # x1, y1, x2, y2   (page pixel space)
    color: str
    text: str | None = None                            # only for textbox
    path: List[Tuple[int, int]] = field(default_factory=list)  # pen path
    font_size: int = 10


def _rgb(hex_color: str) -> Tuple[float, float, float]:
    """Convert #rrggbb → floats 0-1 (MuPDF colour format)."""
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i : i + 2], 16) / 255.0 for i in (0, 2, 4))
    return r, g, b


# ───────────────────────────────────────── controller ───────────────────────────────────────
class PDFRendererController:
    """Public controller the main app talks to."""
    MAX_VISIBLE_TABS = 4

    def __init__(self, root: tk.Tk, selection_indices: Tuple[int, ...], *, read_only: bool = True):
        self.root = root
        self.selection_indices = selection_indices
        self.selected_indices: Tuple[int, ...] = tuple()
        self.pdf_files: List[str] = []
        self.status_label: tk.Label | None = None

        self.logger = Logger()
        self.settings_controller = SettingsController(root)
        self.utility = Utility(root)

        self.default_read_only = read_only
        self.notebook: ttk.Notebook | None = None
        self.tabs: Dict[str, _PDFTab] = {}

    # ───── setters ──────────────────────────────────────────────────────────────────────────
    def set_pdf_files(self, files: List[str]):            # keep signature consistent
        self.pdf_files = files

    def set_selected_indices(self, idx: Tuple[int, ...]):
        self.selected_indices = idx

    def set_status_label(self, lbl: tk.Label):
        self.status_label = lbl

    # ───── public entry point ───────────────────────────────────────────────────────────────
    def render_pdf_ui(self) -> bool:
        targets = [self.pdf_files[i] for i in self.selected_indices] if self.selected_indices else []
        if not targets:
            messagebox.showinfo("Info", "Select at least 1 PDF to open.")
            return False

        if self.notebook is None or not self.notebook.winfo_exists():
            self._create_window()

        for path in targets:
            # Already open?
            if path in self.tabs and self.tabs[path].frame.winfo_exists():
                self.notebook.select(self.tabs[path].frame)
            else:
                tab = _PDFTab(self, self.notebook, path, read_only=self.default_read_only)
                self.tabs[path] = tab
                self._add_tab(tab)

        return True

    # ───── internal helpers ────────────────────────────────────────────────────────────────
    def _create_window(self):
        win = tk.Toplevel(self.root)
        win.title("PDF Viewer / Editor")
        win.geometry("1100x850")
        win.transient(self.root)
        self.notebook = ttk.Notebook(win)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        # Dropdown for overflow tabs
        self.tab_dropdown_var = tk.StringVar()
        self.tab_dropdown = ttk.Combobox(win, textvariable=self.tab_dropdown_var, state="readonly")
        self.tab_dropdown.pack(fill=tk.X)
        self.tab_dropdown.pack_forget()  # Hide initially
        self.tab_dropdown.bind("<<ComboboxSelected>>", self._on_dropdown_tab_selected)
        self.notebook.bind("<Button-1>", self._on_tab_click)

        # Context menu for tabs
        self.tab_menu = tk.Menu(self.notebook, tearoff=0)
        self.tab_menu.add_command(label="Close Tab", command=self._close_selected_tab)

    def _close_selected_tab(self):
        tab_id = getattr(self, "_right_clicked_tab", None)
        if tab_id:
            frame = self.notebook.nametowidget(tab_id)
            for tab in self.tabs.values():
                if tab.frame == frame:
                    tab._close_tab()
                    break
    def _on_tab_right_click(self, event):
        # Show context menu on right-click if on a tab
        x, y = event.x, event.y
        for idx, tab_id in enumerate(self.notebook.tabs()):
            bbox = self.notebook.bbox(idx)
            if not bbox:
                continue
            tab_x, tab_y, tab_w, tab_h = bbox
            if tab_x <= x <= tab_x + tab_w and tab_y <= y <= tab_y + tab_h:
                self.notebook.select(tab_id)
                self._right_clicked_tab = tab_id
                self.tab_menu.tk_popup(event.x_root, event.y_root)
                return

    def _on_tab_click(self, event):
        # Detect if click is on the close icon area
        x, y = event.x, event.y
        for idx, tab_id in enumerate(self.notebook.tabs()):
            bbox = self.notebook.bbox(idx)
            if not bbox:
                continue
            tab_x, tab_y, tab_w, tab_h = bbox
            # Assume close icon is at the rightmost 18px of the tab
            if tab_x + tab_w - 18 <= x <= tab_x + tab_w and tab_y <= y <= tab_y + tab_h:
                # Close this tab
                frame = self.notebook.nametowidget(tab_id)
                for tab in self.tabs.values():
                    if tab.frame == frame:
                        tab._close_tab()
                        return
    def _add_tab(self, tab: "_PDFTab"):
        self.tabs[tab.pdf_path] = tab
        self._update_tab_display(select_path=tab.pdf_path)

    def _update_tab_display(self, select_path=None):
        # Remove all tabs from notebook
        for t in self.notebook.tabs():
            self.notebook.forget(t)
        # Determine visible and overflow tabs
        all_paths = list(self.tabs.keys())
        visible_paths = all_paths[:self.MAX_VISIBLE_TABS]
        overflow_paths = all_paths[self.MAX_VISIBLE_TABS:]
        # Add visible tabs
        for path in visible_paths:
            tab = self.tabs[path]
            tab_text = os.path.basename(tab.pdf_path) + ("*" if tab.dirty else "") + "  ×"
            self.notebook.add(tab.frame, text=tab_text)
            # Re-add close button if needed
            self._add_close_button_to_tab(tab)
        # Handle dropdown
        if overflow_paths:
            self.tab_dropdown["values"] = [os.path.basename(self.tabs[p].pdf_path) for p in overflow_paths]
            self.tab_dropdown_paths = overflow_paths
            self.tab_dropdown.pack(fill=tk.X)
        else:
            self.tab_dropdown.pack_forget()
            self.tab_dropdown_paths = []
        # Select the requested tab if present
        if select_path and select_path in visible_paths:
            self.notebook.select(self.tabs[select_path].frame)

    def _on_dropdown_tab_selected(self, event):
        idx = self.tab_dropdown.current()
        if idx < 0 or idx >= len(self.tab_dropdown_paths):
            return
        selected_path = self.tab_dropdown_paths[idx]
        # Swap the first visible tab with the selected overflow tab
        all_paths = list(self.tabs.keys())
        visible_paths = all_paths[:self.MAX_VISIBLE_TABS]
        overflow_paths = all_paths[self.MAX_VISIBLE_TABS:]
        if not visible_paths:
            return
        # Move selected overflow tab to visible, and first visible to overflow
        swap_in = selected_path
        swap_out = visible_paths[0]
        # Reorder
        new_order = [p for p in all_paths if p != swap_in and p != swap_out]
        new_order = [swap_in] + visible_paths[1:] + [swap_out] + overflow_paths[:idx] + overflow_paths[idx+1:]
        # Rebuild tabs dict in new order
        self.tabs = {p: self.tabs[p] for p in new_order}
        self._update_tab_display(select_path=swap_in)
    def _on_dropdown_tab_selected(self, event):
        idx = self.tab_dropdown.current()
        if idx < 0 or idx >= len(self.tab_dropdown_paths):
            return
        selected_path = self.tab_dropdown_paths[idx]
        # Swap the first visible tab with the selected overflow tab
        all_paths = list(self.tabs.keys())
        visible_paths = all_paths[:self.MAX_VISIBLE_TABS]
        overflow_paths = all_paths[self.MAX_VISIBLE_TABS:]
        if not visible_paths:
            return
        # Move selected overflow tab to visible, and first visible to overflow
        swap_in = selected_path
        swap_out = visible_paths[0]
        # Reorder
        new_order = [p for p in all_paths if p != swap_in and p != swap_out]
        new_order = [swap_in] + visible_paths[1:] + [swap_out] + overflow_paths[:idx] + overflow_paths[idx+1:]
        # Rebuild tabs dict in new order
        self.tabs = {p: self.tabs[p] for p in new_order}
        self._update_tab_display(select_path=swap_in)

    def _add_close_button_to_tab(self, tab: "_PDFTab"):
        # Remove any existing close button for this tab
        if hasattr(tab, 'close_btn') and tab.close_btn.winfo_exists():
            tab.close_btn.destroy()
        btn = tk.Button(self.notebook, text="✕", bd=0, padx=2, pady=0, relief="flat", fg="red", font=("Arial", 10, "bold"))
        btn.configure(command=tab._close_tab)
        btn.place(x=0, y=0)
        tab.close_btn = btn
        def position_close_btn(event=None, tab=tab):
            try:
                idx = self.notebook.index(tab.frame)
                tab_bbox = self.notebook.bbox(idx)
                if tab_bbox:
                    x, y, w, h = tab_bbox
                    btn.place(x=x + w - 18, y=y + 2, width=16, height=h - 4)
            except Exception:
                pass
        self.notebook.bind("<Configure>", position_close_btn)
        self.notebook.bind("<<NotebookTabChanged>>", position_close_btn)
        self.notebook.bind("<ButtonRelease-1>", position_close_btn)
        position_close_btn()
    def _refresh_title(self, tab: "_PDFTab"):
    # Update tab label with * for dirty and x for close
       tab_text = os.path.basename(tab.pdf_path) + ("*" if tab.dirty else "") + "  ×"
       self.notebook.tab(tab.frame, text=tab_text)
    # called by child tab
    def _set_dirty(self, tab: "_PDFTab", dirty: bool):
        if tab.dirty != dirty:
            tab.dirty = dirty
            self._refresh_title(tab)
    def _register_new_file(self, path: str):
        if path not in self.pdf_files:
            self.pdf_files.append(path)
        if self.status_label:
            self.status_label.config(text=f"Created {os.path.basename(path)}")

    def get_completed_files(self):
        return self.pdf_files


# ───────────────────────────────────── per-PDF tab class ───────────────────────────────────
class _PDFTab:
    """Implements all GUI actions for a single document."""

    # ═════ initialisation ════════════════════════════════════════════════════════════════
    def __init__(self, ctl: PDFRendererController, nb: ttk.Notebook, pdf_path: str, *, read_only: bool):
        self.ctl = ctl
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        self.page_count = len(self.doc)

        self.idx = 0
        self.read_only = read_only
        self.dirty = False

        self.annos_by_page: Dict[int, List[Annotation]] = {}
        self.render_cache: Dict[int, ImageTk.PhotoImage] = {}

        # drawing state
        self.tool = "pen"
        self.color = "#000000"
        self.font_size = 10
        self._drag_start: Tuple[int, int] | None = None
        self._pen_path: List[Tuple[int, int]] = []

        # UI!
        self.frame = ttk.Frame(nb)
        self._build_toolbar()
        self._build_canvas()
        self._update_states()
        self._show_page(0)

    # ═════ UI builders ═══════════════════════════════════════════════════════════════════
    def _build_toolbar(self):
        tb = ttk.Frame(self.frame)
        tb.pack(fill=tk.X, pady=2)
        self.logger = Logger()
          # File menu
        menubar = tk.Menu(self.frame)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Open PDF...", command=self._open_pdf_dialog)
        filemenu.add_command(label="Open from Program...", command=self._open_from_program)
        filemenu.add_separator()
        filemenu.add_command(label="Save", command=self._save_inline)
        filemenu.add_command(label="Save As...", command=self._save_copy)
        filemenu.add_separator()
        filemenu.add_command(label="Print...", command=self._print_doc)
        filemenu.add_separator()
        filemenu.add_command(label="Close Tab", command=self._close_tab)
        menubar.add_cascade(label="File", menu=filemenu)
        self.frame.master.master.config(menu=menubar)  # Set menu on the Toplevel

        # navigation
        ttk.Button(tb, text="◀", width=3, command=self._prev_tab).pack(side=tk.LEFT)
        self.page_lbl = ttk.Label(tb, text="Page 1 / 1")  # Will update dynamically
        self.page_lbl.pack(side=tk.LEFT, padx=4)
        ttk.Button(tb, text="▶", width=3, command=self._next_tab).pack(side=tk.LEFT)

    
        ttk.Separator(tb, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=4)

        # tools
        for name, label in [
            ("pen", "Pen"),
            ("line", "Line"),
            ("rect", "Rect"),
            ("highlight", "High"),
            ("textbox", "Text"),
        ]:
            btn = ttk.Button(tb, text=label, command=lambda n=name: self._set_tool(n))
            setattr(self, f"{name}_btn", btn)
            btn.pack(side=tk.LEFT)

        self.e_seg_btn = ttk.Button(tb, text="E-Seg", command=lambda: self._set_tool("erase_seg"))
        self.e_seg_btn.pack(side=tk.LEFT)

        ttk.Separator(tb, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=4)

        # colour / font
        ttk.Button(tb, text="Color", command=self._pick_color).pack(side=tk.LEFT)
        ttk.Label(tb, text="Font sz:").pack(side=tk.LEFT, padx=(6, 0))
        self.font_spin = ttk.Spinbox(tb, from_=6, to=72, width=4, command=self._update_font)
        self.font_spin.set(str(self.font_size))
        self.font_spin.pack(side=tk.LEFT)

        ttk.Separator(tb, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=4)

        # file
        self.save_btn = ttk.Button(tb, text="Save", command=self._save_inline)
        self.saveas_btn = ttk.Button(tb, text="Save As", command=self._save_copy)
        self.print_btn = ttk.Button(tb, text="Print", command=self._print_doc)
        for b in (self.save_btn, self.saveas_btn, self.print_btn):
            b.pack(side=tk.LEFT)

        ttk.Separator(tb, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=4)

        self.edit_toggle = ttk.Button(tb, text="Enable Edit" if self.read_only else "Lock", command=self._toggle_edit)
        self.edit_toggle.pack(side=tk.LEFT)

        ttk.Separator(tb, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=4)

        ttk.Button(tb, text="×", width=3, command=self._close_tab).pack(side=tk.RIGHT)

    def _prev_tab(self):
        nb = self.frame.master
        idx = nb.index(self.frame)
        if idx > 0:
            nb.select(idx - 1)

    def _next_tab(self):
        nb = self.frame.master
        idx = nb.index(self.frame)
        if idx < nb.index("end") - 1:
            nb.select(idx + 1)

    def _open_pdf_dialog(self):
        file_path = filedialog.askopenfilename(
            parent=self.frame,
            filetypes=[("PDF files", "*.pdf")],
            title="Open PDF"
        )
        if file_path:
            self.ctl.set_pdf_files(self.ctl.pdf_files + [file_path])
            self.ctl.selected_indices = (len(self.ctl.pdf_files) - 1,)
            self.ctl.render_pdf_ui()

    def _open_from_program(self):
        if not self.ctl.pdf_files:
            messagebox.showinfo("Info", "No PDFs loaded in the program.")
            return

        # Create modal dialog
        dialog = tk.Toplevel(self.frame)
        dialog.title("Select PDF(s) to Open")
        dialog.transient(self.frame)
        dialog.grab_set()
        dialog.geometry("500x350")

        tk.Label(dialog, text="Select PDF(s) to open:").pack(pady=(10, 0))

        # Listbox with extended selection
        listbox = tk.Listbox(dialog, selectmode="extended", width=70, height=12)
        listbox.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Populate listbox
        for f in self.ctl.pdf_files:
            listbox.insert(tk.END, os.path.basename(f))

        # Select handler
        def on_open():
            indices = listbox.curselection()
            if not indices:
                messagebox.showinfo("Info", "No PDF selected.")
                return
            self.ctl.selected_indices = tuple(indices)
            dialog.destroy()
            self.ctl.render_pdf_ui()

        # Double-click to open
        listbox.bind("<Double-Button-1>", lambda e: on_open())

        # Keyboard shortcuts
        def on_ctrl_a(event):
            listbox.select_set(0, tk.END)
            return "break"
        listbox.bind("<Control-a>", on_ctrl_a)
        listbox.bind("<Control-A>", on_ctrl_a)

        # Button frame
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=(0, 10))
        ttk.Button(btn_frame, text="Open", command=on_open).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

        # Focus and wait
        listbox.focus_set()
        dialog.wait_window()

    def _build_canvas(self):
        cont = ttk.Frame(self.frame)
        cont.pack(fill=tk.BOTH, expand=True)
    
        # Scrollable canvas for all pages
        self.canvas = tk.Canvas(cont, bg="#ffffff")
        self.canvas.grid(row=0, column=0, sticky="nsew")
        cont.rowconfigure(0, weight=1)
        cont.columnconfigure(0, weight=1)
    
        vbar = ttk.Scrollbar(cont, orient=tk.VERTICAL, command=self.canvas.yview)
        vbar.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=vbar.set)
    
        # Frame inside canvas for page images
        self.pages_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.pages_frame, anchor="nw")
    
        self.pages_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
    
        self._show_all_pages()
        
        self.canvas.bind("<ButtonPress-1>", self._on_mouse_down)
        self.canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_up)

        # Bind scroll and arrow keys
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", self._on_mousewheel)  # Linux scroll up
        self.canvas.bind("<Button-5>", self._on_mousewheel)  # Linux scroll down
        self.canvas.bind("<Up>", self._on_up)
        self.canvas.bind("<Down>", self._on_down)
        self.canvas.focus_set()

        # Track visible page
        self.canvas.bind("<Configure>", lambda e: self._update_visible_page())

    
    def _show_all_pages(self):
        # Clear previous images
        for widget in self.pages_frame.winfo_children():
            widget.destroy()
        self.render_cache.clear()
        self.page_labels = []

        for i in range(self.page_count):
            if i not in self.render_cache:
                pix = self.doc.load_page(i).get_pixmap(matrix=fitz.Matrix(1.25, 1.25))
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                self.render_cache[i] = ImageTk.PhotoImage(img)
            lbl = tk.Label(self.pages_frame, image=self.render_cache[i])
            lbl.pack(pady=10)
            self.page_labels.append(lbl)
        self._update_visible_page()

    def _update_visible_page(self):
        # Find which page is most visible in the canvas
        canvas_y = self.canvas.canvasy(0)
        best_idx = 0
        min_dist = float('inf')
        for i, lbl in enumerate(self.page_labels):
            y = lbl.winfo_y()
            dist = abs(y - canvas_y)
            if dist < min_dist:
                min_dist = dist
                best_idx = i
        self.idx = best_idx
        self.page_lbl.config(text=f"Page {self.idx + 1} / {self.page_count}")

    def _on_mousewheel(self, event):
        # Windows/Mac: event.delta, Linux: event.num
        if hasattr(event, 'delta'):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        elif event.num == 4:
            self.canvas.yview_scroll(-3, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(3, "units")
        self._update_visible_page()

    def _on_up(self, event):
        # Scroll to previous page
        if self.idx > 0:
            target = self.page_labels[self.idx - 1]
            self.canvas.yview_moveto(target.winfo_y() / self.pages_frame.winfo_height())
            self._update_visible_page()

    def _on_down(self, event):
        # Scroll to next page
        if self.idx < self.page_count - 1:
            target = self.page_labels[self.idx + 1]
            self.canvas.yview_moveto(target.winfo_y() / self.pages_frame.winfo_height())
            self._update_visible_page()

    # ═════ state helpers ══════════════════════════════════════════════════════════════════
    def _update_states(self):
        state = tk.NORMAL if not self.read_only else tk.DISABLED
        for btn in (
            self.pen_btn,
            self.line_btn,
            self.rect_btn,
            self.highlight_btn,
            self.textbox_btn,
            self.e_seg_btn,
            self.save_btn,
            self.saveas_btn,
        ):
            btn.config(state=state)

    def _set_tool(self, name: str):
        self.tool = name

    def _pick_color(self):
        col = colorchooser.askcolor(color=self.color)[1]
        if col:
            self.color = col

    def _update_font(self):
        try:
            self.font_size = int(self.font_spin.get())
        except ValueError:
            pass

    def _toggle_edit(self):
        self.read_only = not self.read_only
        self.edit_toggle.config(text="Enable Edit" if self.read_only else "Lock")
        self._update_states()

    # ═════ navigation & rendering ═════════════════════════════════════════════════════════
    def _show_page(self, i: int):
        if not (0 <= i < self.page_count):
            return
        self.idx = i
        self.page_lbl.config(text=f"{i + 1} / {self.page_count}")

        if i not in self.render_cache:
            # Render at 1.25x, RGB
            pix = self.doc.load_page(i).get_pixmap(matrix=fitz.Matrix(1.25, 1.25))
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            self.render_cache[i] = ImageTk.PhotoImage(img)

        self.canvas.delete("all")
        self.canvas.create_image(0, 0, image=self.render_cache[i], anchor="nw", tags="page")
        self.canvas.config(scrollregion=(0, 0, self.render_cache[i].width(), self.render_cache[i].height()))
        self._redraw_annos()

    # ═════ drawing event handlers ═════════════════════════════════════════════════════════
    def _on_mouse_down(self, ev):
        if self.read_only:
            return
        self._drag_start = (self.canvas.canvasx(ev.x), self.canvas.canvasy(ev.y))
        if self.tool == "pen":
            self._pen_path = [self._drag_start]
        elif self.tool == "textbox":
            # Check hit existing textbox
            hit = self._textbox_hit(ev.x, ev.y)
            if hit:
                new_text = simpledialog.askstring("Edit Text", "Text:", initialvalue=hit.text, parent=self.frame)
                if new_text is not None:
                    hit.text = new_text
                    self._redraw_annos()
                    self.ctl._set_dirty(self, True)
            else:
                # create immediately (no drag)
                self._create_textbox(self._drag_start)
                self._drag_start = None

        elif self.tool == "erase_seg":
            self._erase_at(ev.x, ev.y)

    def _on_mouse_drag(self, ev):
        if self.read_only or not self._drag_start:
            return
        if self.tool == "pen":
            self._pen_path.append((self.canvas.canvasx(ev.x), self.canvas.canvasy(ev.y)))
            # draw live preview
            if len(self._pen_path) > 1:
                self.canvas.create_line(*self._pen_path[-2], *self._pen_path[-1], fill=self.color, width=2, tags="live")
        else:
            # live rectangle/line/highlight preview
            self.canvas.delete("live")
            x1, y1 = self._drag_start
            x2, y2 = self.canvas.canvasx(ev.x), self.canvas.canvasy(ev.y)
            if self.tool == "line":
                self.canvas.create_line(x1, y1, x2, y2, fill=self.color, width=2, tags="live")
            else:
                dash = (2, 2) if self.tool == "highlight" else ()
                self.canvas.create_rectangle(x1, y1, x2, y2, outline=self.color, dash=dash, tags="live")

    def _on_mouse_up(self, ev):
        if self.read_only or not self._drag_start:
            return

        x1, y1 = self._drag_start
        x2, y2 = self.canvas.canvasx(ev.x), self.canvas.canvasy(ev.y)
        self.canvas.delete("live")
        self._drag_start = None

        if self.tool == "pen" and len(self._pen_path) > 1:
            anno = Annotation(tool="pen", coords=(0, 0, 0, 0), color=self.color, path=self._pen_path.copy())
        elif self.tool == "line":
            anno = Annotation(tool="line", coords=(x1, y1, x2, y2), color=self.color)
        elif self.tool == "rect":
            anno = Annotation(tool="rect", coords=(x1, y1, x2, y2), color=self.color)
        elif self.tool == "highlight":
            anno = Annotation(tool="highlight", coords=(x1, y1, x2, y2), color="#ffff00")
        else:
            return

        self._add_anno(anno)

    # ═════ annotation helpers ═════════════════════════════════════════════════════════════
    def _add_anno(self, anno: Annotation):
        self.annos_by_page.setdefault(self.idx, []).append(anno)
        self._redraw_annos()
        self.ctl._set_dirty(self, True)

    def _erase_at(self, x: int, y: int):
        cx, cy = self.canvas.canvasx(x), self.canvas.canvasy(y)
        rem = None
        for anno in reversed(self.annos_by_page.get(self.idx, [])):
            if anno.tool == "pen":
                # bounding box of path
                xs, ys = zip(*anno.path)
                bb = (min(xs), min(ys), max(xs), max(ys))
            else:
                bb = anno.coords
            if bb[0] - 4 <= cx <= bb[2] + 4 and bb[1] - 4 <= cy <= bb[3] + 4:
                rem = anno
                break
        if rem:
            self.annos_by_page[self.idx].remove(rem)
            self._redraw_annos()
            self.ctl._set_dirty(self, True)

    def _textbox_hit(self, x: int, y: int) -> Annotation | None:
        cx, cy = self.canvas.canvasx(x), self.canvas.canvasy(y)
        for anno in self.annos_by_page.get(self.idx, []):
            if anno.tool == "textbox":
                x1, y1, x2, y2 = anno.coords
                if x1 <= cx <= x2 and y1 <= cy <= y2:
                    return anno
        return None

    def _create_textbox(self, pos: Tuple[int, int]):
        txt = simpledialog.askstring("Text", "Text:", parent=self.frame)
        if txt:
            x, y = pos
            # crude width/height estimate
            w = len(txt) * self.font_size * 0.6
            h = self.font_size * 1.4
            anno = Annotation(
                tool="textbox",
                coords=(x, y, x + w, y + h),
                color=self.color,
                text=txt,
                font_size=self.font_size,
            )
            self._add_anno(anno)

    # ═════ redraw overlay ══════════════════════════════════════════════════════════════════
    def _redraw_annos(self):
        self.canvas.delete("anno")
        for page, annos in self.annos_by_page.items():
            if page != self.idx:
                continue
            for a in annos:
                if a.tool == "pen":
                    self.canvas.create_line(*sum(a.path, ()), fill=a.color, width=2, tags="anno")
                elif a.tool == "line":
                    self.canvas.create_line(*a.coords, fill=a.color, width=2, tags="anno")
                elif a.tool == "rect":
                    self.canvas.create_rectangle(*a.coords, outline=a.color, width=2, tags="anno")
                elif a.tool == "highlight":
                    self.canvas.create_rectangle(*a.coords, outline="", fill=a.color, stipple="gray50", tags="anno")
                elif a.tool == "textbox":
                    x1, y1, x2, y2 = a.coords
                    self.canvas.create_text(
                        (x1 + x2) / 2,
                        (y1 + y2) / 2,
                        text=a.text,
                        fill=a.color,
                        font=("Arial", a.font_size),
                        tags="anno",
                    )

    # ═════ file actions ═══════════════════════════════════════════════════════════════════
    def _save_inline(self):
        if not self.dirty:
            return
        try:
            self._write_back(self.pdf_path, incremental=True)
            self.ctl._set_dirty(self, False)
        except Exception as e:
            # Fall back to full save
            tmp = tempfile.mktemp(suffix=".pdf")
            self._write_back(tmp, incremental=False)
            shutil.move(tmp, self.pdf_path)
            self.ctl._set_dirty(self, False)
            messagebox.showinfo("Info", "File saved (full rewrite) because incremental save failed.")
            self.logger.error("PDFRenderer", f"Failed to save inline: {e}")
    def _save_copy(self):
        dest = filedialog.asksaveasfilename(
            parent=self.frame,
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile=os.path.basename(self.pdf_path).replace(".pdf", "_edited.pdf"),
        )
        if not dest:
            return
        self._write_back(dest, incremental=False)
        self.ctl._register_new_file(dest)
        self.ctl._set_dirty(self, False)

    def _write_back(self, path: str, *, incremental: bool):
        # clone the original to avoid modifying open file handle
        if incremental:
            doc = self.doc
        else:
            doc = fitz.open()          # empty
            doc.insert_pdf(self.doc)   # copy existing pages

        # Apply annos
        for page_no, annos in self.annos_by_page.items():
            page = doc[page_no]
            for a in annos:
                if a.tool == "pen":
                    shape = page.new_shape()
                    shape.draw_polyline(a.path)
                    shape.finish(color=_rgb(a.color), width=2)
                elif a.tool == "line":
                    shape = page.new_shape()
                    shape.draw_line(a.coords[:2], a.coords[2:])
                    shape.finish(color=_rgb(a.color), width=2)
                elif a.tool == "rect":
                    shape = page.new_shape()
                    shape.draw_rect(a.coords)
                    shape.finish(color=_rgb(a.color), width=2)
                elif a.tool == "highlight":
                    page.add_highlight_annot(a.coords)
                elif a.tool == "textbox":
                    page.insert_textbox(
                        a.coords,
                        a.text,
                        fontsize=a.font_size,
                        fontname="helv",
                        color=_rgb(a.color),
                    )

        doc.save(path, incremental=incremental)
        if not incremental:
            doc.close()

    def _print_doc(self):
        try:
            if os.name == "nt":
                # Use system print dialog on Windows
                import win32api
                import win32print
                win32api.ShellExecute(
                    0,
                    "print",
                    self.pdf_path,
                    None,
                    ".",
                    0
                )
            else:
                # Try to use lpr or system dialog on Unix
                import subprocess
                subprocess.run(["lpr", self.pdf_path])
        except Exception as e:
            messagebox.showerror("Error", f"Could not print: {e}")
    # ═════ close / cleanup ═════════════════════════════════════════════════════════════════
    def _close_tab(self):
        if self.dirty:
            resp = messagebox.askyesnocancel("Unsaved", "Save changes before closing?")
            if resp is None:          # cancel
                return
            if resp:                 # yes
                self._save_inline()
        # remove tab
        nb = self.frame.master
        nb.forget(self.frame)
        self.doc.close()
        del self.ctl.tabs[self.pdf_path]
        self.ctl._update_tab_display()
        if not nb.tabs():
            nb.master.destroy()
    def __del__(self):
        try:
            self.doc.close()
        except Exception:
            pass
        self.render_cache.clear()
        gc.collect()
