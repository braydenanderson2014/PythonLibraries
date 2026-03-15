# editor/renderers/pdf_renderer/renderer.py
import json
import fitz
import tkinter as tk
from pathlib import Path
from ..base import BaseRenderer
from ...document_model    import DocumentModel
from ...file_api          import FileAPI
from PDFUtility.PDFLogger import Logger
import importlib

def import_required_modules(required_files, base_package="editor"):
    modules = {}
    for file in required_files:
        module_name = file.replace(".py", "")
        full_module = f"{base_package}.{module_name}"
        modules[module_name] = importlib.import_module(full_module)
    return modules


def call_hook(modules, hook_name, *args, **kwargs):
    for module in modules.values():
        if hasattr(module, hook_name):
            func = getattr(module, hook_name)
            return func(*args, **kwargs)
    raise ImportError(f"Function {hook_name} not found in required modules.")


class Renderer(BaseRenderer):
        # cache the JSON so class-methods can access it
    _meta = None

    @classmethod
    def _load_meta(cls):
        if cls._meta is None:
            p = Path(__file__).parent / "settings.json"
            cls._meta = json.loads(p.read_text(encoding="utf-8"))
        return cls._meta

    @classmethod
    def extensions(cls):
        # fulfill the abstract requirement
        return cls._load_meta().get(
            "supported_extensions",
            cls._load_meta().get("extensions", [])
        )

    @classmethod
    def imports(cls):
        # fulfill the abstract requirement
        return cls._load_meta().get(
            "required_files",
            cls._load_meta().get("required_files", [])
        )
        

    @classmethod
    def preview_only(cls):
        # abstract hook for “is this read-only?”
        return bool(cls._load_meta().get("preview_mode", True))

    @classmethod
    def tools(cls):
        # abstract hook for “which tools should appear”
        return cls._load_meta().get("function_hooks", {}).get("tools", 
               cls._load_meta().get("tools", []))

    def __init__(self, editor):
        super().__init__(editor)
        self.logger = Logger()
        # ── 1) Load our settings.json ─────────────────────────────────────
        settings_path = Path(__file__).parent / "settings.json"
        with open(settings_path, "r", encoding="utf-8") as f:
            self.meta = json.load(f)

        # ── 2) Load Required Files ──────────────────────────────   
        self.imports = list(self.meta.get("required_files", []))

        # ── 3) Pull out the most‐used flags ──────────────────────────────
        self.locked             = bool(self.meta.get("locked", True))
        self.preview_only       = bool(self.meta.get("preview_mode", True))
        self.editable_default   = bool(self.meta.get("editable", False))
        self.zoom_default       = float(self.meta.get("zoom_default", 1.0))
        self.show_annotations   = bool(self.meta.get("show_annotations", True))
        self.show_thumbnails    = bool(self.meta.get("show_thumbnails", True))
        self.allow_text_selection = bool(self.meta.get("allow_text_selection", False))
        self.theme              = self.meta.get("theme", "light")

        # Hooks → map logical actions to our methods
        self.hooks = self.meta.get("function_hooks", {})

        # We'll keep our DocumentModel here once opened
        self.dm = None


    # ── 4) Dynamic dispatch based on hooks ──────────────────────────────

    def open(self, path: str) -> str:
        """
        Called by FileTypeManager.open().
        Dispatches to whatever your settings.json says.
        """
        fn = self.hooks.get("on_open", "load_pdf_document")
        return getattr(self, fn)(path)

    def save(self, tab_id: str):
        fn = self.hooks.get("on_save", "save_pdf_document")
        return getattr(self, fn)(tab_id)

    def save_as(self, tab_id: str, new_path: str):
        fn = self.hooks.get("on_save", "save_pdf_document")
        # if your hook prefers separate save_as logic, adjust the key
        return getattr(self, fn)(tab_id, new_path)

    def toggle_edit(self, tab_id: str):
        fn = self.hooks.get("on_toggle_edit", "toggle_edit_mode")
        return getattr(self, fn)(tab_id)

    def annotate(self, tab_id: str, annotation):
        fn = self.hooks.get("on_annotate", "add_annotation")
        return getattr(self, fn)(tab_id, annotation)


    # ── 5) The actual implementations ──────────────────────────────────

    def load_pdf_document(self, path: str) -> str:
        # Create & remember our DocumentModel
        self.dm = DocumentModel(filepath=path)
        
        # Ask TabManager for a new tab, passing *this* renderer instance
        tab_id = self.editor.tab_manager.add_tab(self.dm, renderer=self)

        # Register so Save/SaveAs works
        FileAPI._register_tab(tab_id, self.dm)

        return tab_id

    def save_pdf_document(self, tab_id: str, outpath: str = None):
        """
        Called for both save() and save_as() if you route them here.
        If outpath is None, does an in-place save.
        """
        if not self.dm:
            return
        if outpath:
            self.dm.filepath = outpath
        self.dm.save(outpath=outpath)

        # Refresh the tab label in case the name changed
        self.editor.tab_manager.refresh_tab_label(tab_id)

    def toggle_edit_mode(self, tab_id: str):
        """
        Switch between preview/read-only vs. edit mode.
        Honours the `locked` flag in settings.json.
        """
        if self.locked:
            # editor is locked → do nothing
            return

        info = self.editor.tab_manager.tabs[tab_id]
        dm   = info["doc_model"]
        # flip the editable flag in our DocumentModel
        dm.toggle_editable(not dm.editable)

        # and refresh any overlays
        ov = info.get("overlay")
        if ov:
            ov.refresh(zoom=info["zoom"])

    def add_annotation(self, tab_id: str, annotation):
        """
        Example annotation hook; you could call this when tools fire.
        """
        if not self.dm:
            return
        page = self.dm.get_page(annotation.page_number)
        annotation.commit_to_page(page)

    # ── 6) The low-level rendering call ────────────────────────────────

    def get_page_image(self, page_number: int, zoom: float):
        """
        TabManager will call this to draw each page.
        """
        if self.dm is None:
            raise RuntimeError("PDF not loaded yet")

        page = self.dm.get_page(page_number)
        mat  = fitz.Matrix(zoom, zoom)
        pix  = page.get_pixmap(matrix=mat, alpha=False)
        self.logger.debug("PDF RENDERER", f"pixmap size: {pix.width} {pix.height}")

        data = pix.tobytes("ppm")

        return tk.PhotoImage(data=data)

    def scroll(self, tab_id: str, direction: str, amount: int):
        """Scroll the PDF document by a certain delta."""
        info = self.editor.tab_manager.tabs[tab_id]
        
        # Get the preview widget (canvas or frame)
        preview_widget = info.get("preview_widget")
        if not preview_widget:
            return
        
        # If it's a canvas with scrollbars, scroll it
        if hasattr(preview_widget, 'yview_scroll'):
            if direction == "up":
                preview_widget.yview_scroll(-amount, "units")
            elif direction == "down":
                preview_widget.yview_scroll(amount, "units")
        
        if hasattr(preview_widget, 'xview_scroll'):
            if direction == "left":
                preview_widget.xview_scroll(-amount, "units")
            elif direction == "right":
                preview_widget.xview_scroll(amount, "units")
