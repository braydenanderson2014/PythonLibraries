from abc import ABC, abstractmethod
from typing import List, Dict, Type, Optional, Tuple
import os 
import json


class BaseRenderer(ABC):
    """
    All renderers subclass this.
    Each lives in its own folder with a settings.json.
    """

    def __init__(self, editor):
        self.editor = editor

    @classmethod
    @abstractmethod
    def extensions(cls) -> List[str]:
        """List of file extensions (".pdf", ".txt", etc)."""

    @classmethod
    def preview_only(cls) -> bool:
        """Override if this type is read-only."""
        return False

    @classmethod
    def supports_dual_tabs(cls) -> bool:
        """Override if this renderer supports dual editor/preview tabs."""
        return False

    @classmethod
    def tools(cls) -> List[str]:
        """Tool names to enable in this tab."""
        return []

    @abstractmethod
    def open(self, path: str) -> str:
        """
        Open the file in a new tab.
        Returns the tab_id.
        """

    def open_dual_tabs(self, path: str) -> Tuple[str, str]:
        """
        Open file with dual tabs (editor + preview).
        Returns (editor_tab_id, preview_tab_id).
        Override this method if supports_dual_tabs() returns True.
        """
        raise NotImplementedError("Dual tabs not supported by this renderer")

    def save(self, tab_id: str):
        """If editable, save changes back to disk (default: no-op)."""

    def save_as(self, tab_id: str, new_path: str):
        """If editable, save-as to a new path (default: no-op)."""

    @abstractmethod
    def scroll(self, tab_id: str, direction: str, amount: int):
        """
        Scroll the document by a certain delta.
        """

    def open_preview(self, path: str):
        """
        For preview-only renderers. Should return (tab_id, widget, display_name).
        Default implementation falls back to regular open().
        """
        tab_id = self.open(path)
        # This is a fallback - preview renderers should override this
        return tab_id, None, os.path.basename(path)

    def refresh_preview(self, editor_tab_id: str, preview_tab_id: str):
        """
        Refresh preview tab when editor tab is modified.
        Only called for renderers that support dual tabs.
        """
        pass

    @classmethod
    def register_renderer(cls, renderer_class: Type['BaseRenderer']):
        """Legacy method for backward compatibility."""
        if not hasattr(cls, '_renderers'):
            cls._renderers = {}
        for ext in renderer_class.extensions():
            cls._renderers[ext] = renderer_class

    @classmethod
    def load_metadata(cls, settings_path: str) -> Dict:
        """Load metadata from settings.json file."""
        with open(settings_path, 'r', encoding='utf-8') as f:
            return json.load(f)