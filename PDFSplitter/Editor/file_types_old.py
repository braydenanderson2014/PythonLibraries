# editor/file_types.py

import os

from editor.file_api import FileAPI
from editor.renderers.base import BaseRenderer
from editor.renderers.PluginManager import PluginManager
class FileTypeManager:
    def __init__(self, editor):
        self.editor    = editor
        # map: extension → (RendererClass, metadata dict)
        self._registry = {}
        self._discover_renderers()

    def _discover_renderers(self):
        for modname in RENDERER_MODULES:
            importlib.import_module(modname)

        # 1) Find the top‐level “editor/renderers” package
        pkg  = importlib.import_module("editor.renderers")
        root = Path(pkg.__file__).parent

        if hasattr(sys, "_MEIPASS"):
            # If running in a PyInstaller bundle, adjust root
            root = Path(sys._MEIPASS) / "editor" / "renderers"

        # 2) Look for subdirectories with settings.json
        for finder, name, ispkg in pkgutil.iter_modules([str(root)]):
            subdir        = root / name
            settings_path = subdir / "settings.json"
            if not settings_path.is_file():
                continue

            # 3) Load & parse settings.json
            try:
                raw = settings_path.read_text(encoding="utf-8").strip()
                if not raw:
                    raise ValueError("empty JSON")
                meta = json.loads(raw)
            except Exception as e:
                self.editor.logger.warning(
                    "PDF Editor",
                    f"Skipping renderer '{name}': cannot parse settings.json ({e})"
                )
                continue

            # 4) Import the Renderer class from <renderer>/renderer.py
            module_name = f"editor.renderers.{name}.renderer"
            try:
                module = importlib.import_module(module_name)
                RendererClass = getattr(module, "Renderer")
                if not issubclass(RendererClass, BaseRenderer):
                    raise TypeError("Renderer must subclass BaseRenderer")
            except Exception as e:
                self.editor.logger.warning(
                    "PDF Editor",
                    f"Skipping renderer '{name}': cannot import Renderer ({e})"
                )
                continue

            # 5) Collect all extensions under either key
            exts = meta.get("extensions",
                    meta.get("supported_extensions", []))
            for ext in exts:
                self._registry[ext.lower()] = (RendererClass, meta)

        # if you want, log what got registered:
        self.editor.logger.info(
            "PDF Editor",
            f"Registered renderers for: {sorted(self._registry.keys())}"
        )

    def open(self, path: str) -> str:
        """
        Delegate to the right Renderer based on extension.
        Returns the new tab_id.
        """
        ext = os.path.splitext(path)[1].lower()
        entry = self._registry.get(ext)
        if not entry:
            raise ValueError(f"No renderer for extension {ext!r}")
        RendererClass, meta = entry

        renderer = RendererClass(self.editor)

        # if this renderer is preview-only → call its preview hook
        if meta.get("preview_only", False):
            tab_id, widget, display_name = renderer.open_preview(path)
            # register the preview tab
            self.editor.tab_manager.register_tab_widget(
                widget.master, display_name=display_name
            )
            info = self.editor.tab_manager.tabs[tab_id]
            info.update({
                "renderer_instance": renderer,
                "renderer_meta":     meta,
                "preview_widget":    widget,
                "preview_path":      path,
                "preview_name":      display_name,
            })
        else:
            # full editor mode
            tab_id = renderer.open(path)   # your on_open hook
            info = self.editor.tab_manager.tabs[tab_id]
            info["renderer_instance"] = renderer
            info["renderer_meta"]     = meta

            # register the DocumentModel if it's a PDF
            if hasattr(renderer, "dm"):
                FileAPI._register_tab(tab_id, renderer.dm)

        # configure edit-mode & toolbars
        editable = not meta.get("preview_only", True)
        if editable and hasattr(self.editor.tab_manager, "enable_edit_mode"):
            self.editor.tab_manager.enable_edit_mode(tab_id)
        if hasattr(self.editor.tab_manager, "configure_tools"):
            self.editor.tab_manager.configure_tools(
                tab_id,
                allowed=meta.get("tools", [])
            )

        return tab_id

    def save(self, tab_id: str):
        info     = self.editor.tab_manager.tabs[tab_id]
        renderer = info.get("renderer_instance")
        if renderer:
            renderer.save(tab_id)

    def save_as(self, tab_id: str, new_path: str):
        info     = self.editor.tab_manager.tabs[tab_id]
        renderer = info.get("renderer_instance")
        if renderer:
            renderer.save_as(tab_id, new_path)

    # — Helpers for building your “Open…” filetypes list ——
    def list_renderers(self):
        """
        Return a list of dicts like:
          [{'name':'PDFRenderer', 'description':'…', 'extensions':['.pdf']}, …]
        """
        by_cls = {}
        for ext, (cls, meta) in self._registry.items():
            if cls not in by_cls:
                exts = meta.get("extensions",
                        meta.get("supported_extensions", []))
                by_cls[cls] = {
                    "name":        meta.get("name", cls.__name__),
                    "description": meta.get("description", ""),
                    "extensions":  list(exts)
                }
            else:
                by_cls[cls]["extensions"].append(ext)
        # dedupe
        for info in by_cls.values():
            info["extensions"] = sorted(set(info["extensions"]))
        return list(by_cls.values())

    def get_open_filetypes(self):
        """
        Build a `filetypes=` structure for askopenfilename:
          [("PDFRenderer (*.pdf)", ("*.pdf",)), …]
        """
        types = []
        for info in self.list_renderers():
            patterns = tuple(f"*{e}" for e in info["extensions"])
            desc     = f"{info['name']} ({', '.join(patterns)})"
            types.append((desc, patterns))
        types.append(("All Files", "*.*"))
        return types

