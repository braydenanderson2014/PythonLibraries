"""
SVGRendererController – vector-accurate editor built on pdf2svg ↔ CairoSVG
2025-06-xx
"""

from __future__ import annotations
import io, os, shutil, subprocess, tempfile, tkinter as tk
from pathlib import Path
from typing import Dict, List, Tuple
import lxml.etree as ET
from PIL import Image, ImageTk
import cairosvg                                       # pip install cairosvg
from ttkbootstrap import ttk

from PDFUtility.PDFLogger import Logger
from SettingsController import SettingsController

# ─────────────────────────────────────────────────────────────────────────────
POPPLER_PDF2SVG = "pdf2svg.exe" if os.name == "nt" else "pdf2svg"
TMP = Path(tempfile.gettempdir()) / "pdfutility_svg"
TMP.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
class SVGRendererController:
    """
    Public API identical to PDFRendererController so the main program
    can decide at run-time which backend to instantiate.
    """

    MAX_VISIBLE_TABS = 4           # keep UX identical

    # ─── ctor ────────────────────────────────────────────────────────────
    def __init__(self, root: tk.Tk, selection_indices: Tuple[int, ...],
                 *, read_only: bool = True):
        self.root   = root
        self.sel_i  = selection_indices
        self.read_only = read_only

        self.pdf_files: List[str] = []
        self.status_lbl: tk.Label | None = None
        self.tabs: Dict[str, _SVGTab] = {}

        self.nb: ttk.Notebook | None = None
        self.logger = Logger()

    # ─── setters called by main window ───────────────────────────────────
    def set_pdf_files(self, lst: List[str]):
        self.pdf_files = lst

    def set_selected_indices(self, tup: Tuple[int, ...]):
        self.sel_i = tup

    def set_status_label(self, lbl: tk.Label):
        self.status_lbl = lbl

    # ─── UI entry point (same name) ──────────────────────────────────────
    def render_pdf_ui(self) -> bool:
        targets = [self.pdf_files[i] for i in self.sel_i] if self.sel_i else []
        if not targets:
            tk.messagebox.showinfo("Info", "Select at least 1 PDF to open.")
            return False

        if self.nb is None or not self.nb.winfo_exists():
            self._create_window()

        for path in targets:
            if path in self.tabs and self.tabs[path].frame.winfo_exists():
                self.nb.select(self.tabs[path].frame)
            else:
                tab = _SVGTab(self, self.nb, path, read_only=self.read_only)
                self.tabs[path] = tab
                self._add_tab(tab)

        return True

    # ─── internal helpers (cut-down) ─────────────────────────────────────
    def _create_window(self):
        win = tk.Toplevel(self.root)
        win.title("SVG PDF Editor")
        win.geometry("1200x850")
        win.transient(self.root)

        self.nb = ttk.Notebook(win)
        self.nb.pack(fill=tk.BOTH, expand=True)

    def _add_tab(self, tab: "_SVGTab"):
        self.nb.add(tab.frame, text=os.path.basename(tab.src_pdf))
        self.nb.select(tab.frame)

    # called by _SVGTab when it creates new PDF
    def _register_new_file(self, path: str):
        if path not in self.pdf_files:
            self.pdf_files.append(path)
        if self.status_lbl:
            self.status_lbl.config(text=f"Saved → {os.path.basename(path)}")

    def get_completed_files(self):
        return self.pdf_files


# ───────────────────────── per-document tab ────────────────────────────────
class _SVGTab:
    """One PDF (converted to temporary SVG list)."""

    SCALE = 1.25           # same zoom you used before

    def __init__(self, ctl: SVGRendererController,
                 nb: ttk.Notebook, src_pdf: str, *, read_only: bool):
        self.ctl       = ctl
        self.src_pdf   = src_pdf
        self.read_only = read_only
        self.dirty     = False

        self.tmp_dir   = TMP / f"{os.path.basename(src_pdf)}_{os.getpid()}"
        if self.tmp_dir.exists(): shutil.rmtree(self.tmp_dir, True)
        self.tmp_dir.mkdir()

        self.svg_paths: List[Path] = self._pdf_to_svgs(src_pdf)
        self.page_dom: List[ET.ElementTree] = [ET.parse(p) for p in self.svg_paths]
        self.page_imgs: List[ImageTk.PhotoImage] = []   # raster preview cache

        # UI
        self.frame = ttk.Frame(nb)
        self._build_toolbar()
        self._build_canvas()
        self._render_all_pages()
        self._update_states()

    # ─── convert helpers ────────────────────────────────────────────────
    def _pdf_to_svgs(self, pdf: str) -> List[Path]:
        page_count = int(subprocess.check_output(
            [POPPLER_PDF2SVG, pdf, "-", "1"],
            stderr=subprocess.STDOUT, text=True
        ).split()[-1])  # pdf2svg prints “writing page 1...”

        out = []
        for i in range(1, page_count + 1):
            svg_path = self.tmp_dir / f"page_{i}.svg"
            subprocess.check_call([POPPLER_PDF2SVG, pdf, str(svg_path), str(i)])
            out.append(svg_path)
        return out

    # ─── GUI builders (short version) ───────────────────────────────────
    def _build_toolbar(self):
        tb = ttk.Frame(self.frame); tb.pack(fill=tk.X)
        ttk.Button(tb, text="Save", command=self._save).pack(side=tk.LEFT)
        ttk.Button(tb, text="Save As", command=self._save_as).pack(side=tk.LEFT)
        ttk.Button(tb, text="Enable Edit" if self.read_only else "Lock",
                   command=self._toggle_edit).pack(side=tk.LEFT, padx=12)

    def _build_canvas(self):
        self.cvs = tk.Canvas(self.frame, bg="white")
        vs = ttk.Scrollbar(self.frame, orient=tk.VERTICAL, command=self.cvs.yview)
        self.cvs.configure(yscrollcommand=vs.set)
        self.cvs.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        vs.pack(fill=tk.Y, side=tk.RIGHT)

        self.page_container = ttk.Frame(self.cvs)
        self.cvs.create_window((0,0), window=self.page_container, anchor="nw")
        self.page_container.bind(
            "<Configure>", lambda e: self.cvs.configure(scrollregion=self.cvs.bbox("all"))
        )

    def _render_all_pages(self):
        """Rasterises each SVG page to a PhotoImage for quick display."""
        for p in self.svg_paths:
            png_bytes = cairosvg.svg2png(url=str(p), scale=self.SCALE)
            img = Image.open(io.BytesIO(png_bytes))
            self.page_imgs.append(ImageTk.PhotoImage(img))
            tk.Label(self.page_container, image=self.page_imgs[-1])\
              .pack(pady=8)

    # ─── state helpers ──────────────────────────────────────────────────
    def _toggle_edit(self):
        self.read_only = not self.read_only
        # (update toolbar button text, enable canvas bindings, etc.)

    def _update_states(self): ...
        # enable/disable toolbar buttons – left as exercise

    # ─── save helpers ───────────────────────────────────────────────────
    def _write_back_pdf(self, dest: str):
        """Merge possibly edited SVGs back to one PDF via CairoSVG."""
        out_pdf = cairosvg.svg2pdf  # alias for brevity
        tmp_files = []
        for svg in self.svg_paths:
            tmp = svg.with_suffix(".pdf")
            out_pdf(url=str(svg), write_to=str(tmp))
            tmp_files.append(tmp)

        # concatenate pages
        merged = fitz.open()
        for p in tmp_files:
            merged.insert_pdf(fitz.open(p))
        merged.save(dest)
        merged.close()
        for p in tmp_files: p.unlink()

    def _save(self):
        if not self.dirty: return
        self._write_back_pdf(self.src_pdf)
        self.dirty = False
        self.ctl._register_new_file(self.src_pdf)

    def _save_as(self):
        fn = filedialog.asksaveasfilename(
            parent=self.frame, defaultextension=".pdf",
            initialfile=os.path.basename(self.src_pdf).replace(".pdf","_edited.pdf")
        )
        if not fn: return
        self._write_back_pdf(fn)
        self.dirty = False
        self.ctl._register_new_file(fn)

    # ─── close cleanup etc. (omitted for brevity) ───────────────────────
