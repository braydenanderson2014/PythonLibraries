# editor/file_types.py

import os

from .file_api import FileAPI
from .renderers.base import BaseRenderer
from .renderers.PluginManager import PluginManager

class FileTypeManager:
    def __init__(self, editor):
        self.editor = editor
        self.plugin_manager = PluginManager(editor)
        # map: extension → (RendererClass, metadata dict)
        self._registry = {}
        self._discover_renderers()

    def _discover_renderers(self):
        """Use PluginManager to load all renderers."""
        self._registry = self.plugin_manager.load_all_renderers()
        
        # Log what got registered:
        self.editor.logger.info(
            "PDF Editor",
            f"Registered renderers for: {sorted(self._registry.keys())}"
        )

    def open(self, path: str) -> str:
        """
        Delegate to the right Renderer based on extension.
        Returns the new tab_id (or primary tab_id for dual tabs).
        """
        ext = os.path.splitext(path)[1].lower()
        entry = self._registry.get(ext)
        if not entry:
            raise ValueError(f"No renderer for extension {ext!r}")
        RendererClass, meta = entry

        renderer = RendererClass(self.editor)

        # Check if renderer supports dual tabs
        if renderer.supports_dual_tabs() and meta.get("dual_tabs", False):
            return self._open_dual_tabs(renderer, path, meta)
        
        # if this renderer is preview-only → call its preview hook
        elif meta.get("preview_only", False):
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

    def _open_dual_tabs(self, renderer, path: str, meta: dict) -> str:
        """
        Open file with dual tabs using the renderer's dual tab support.
        Returns the editor tab_id (primary tab).
        """
        try:
            editor_tab_id, preview_tab_id = renderer.open_dual_tabs(path)
            
            # Update both tabs with renderer information
            for tab_id in [editor_tab_id, preview_tab_id]:
                info = self.editor.tab_manager.tabs[tab_id]
                info["renderer_instance"] = renderer
                info["renderer_meta"] = meta
                
                # Configure tools for editor tab only
                if tab_id == editor_tab_id:
                    if hasattr(self.editor.tab_manager, "enable_edit_mode"):
                        self.editor.tab_manager.enable_edit_mode(tab_id)
                    if hasattr(self.editor.tab_manager, "configure_tools"):
                        self.editor.tab_manager.configure_tools(
                            tab_id,
                            allowed=meta.get("tools", [])
                        )
            
            # Store dual tab relationship
            editor_info = self.editor.tab_manager.tabs[editor_tab_id]
            preview_info = self.editor.tab_manager.tabs[preview_tab_id]
            
            editor_info["dual_tab_partner"] = preview_tab_id
            preview_info["dual_tab_partner"] = editor_tab_id
            
            return editor_tab_id
            
        except Exception as e:
            # Fallback to single tab if dual tabs fail
            self.editor.logger.warning(
                "FileTypeManager", 
                f"Dual tab creation failed for {path}: {e}. Falling back to single tab."
            )
            return renderer.open(path)

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

    # — Helpers for building your "Open…" filetypes list ——
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
