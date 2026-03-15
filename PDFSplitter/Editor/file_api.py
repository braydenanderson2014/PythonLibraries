# editor/file_api.py
from typing import Dict, Optional
from .document_model import DocumentModel

class FileAPI:
    """
    A simple registry so external code can refer to an open tab by its ID,
    and call public methods (save, get bytes, etc.).
    """
    _registry: Dict[str, DocumentModel] = {}

    @classmethod
    def _register_tab(cls, tab_id: str, doc_model: DocumentModel):
        cls._registry[tab_id] = doc_model

    @classmethod
    def _unregister_tab(cls, tab_id: str):
        if tab_id in cls._registry:
            del cls._registry[tab_id]

    @classmethod
    def open_document(cls, path: str, editor_window) -> str:
        """
        Programmatically open a PDF in a new tab. Returns the tab_id.
        The caller must pass in the EditorWindow instance so we can re‐use
        the same flow as if the user clicked “Open…”.
        """
        dm = DocumentModel(filepath=path)
        tab_id = editor_window.tab_manager.add_tab(dm)
        cls._register_tab(tab_id, dm)
        return tab_id

    @classmethod
    def save_document(cls, tab_id: str, path: Optional[str] = None) -> bool:
        """
        Save the document corresponding to tab_id.
        If path is None, overwrite original; else save as new.
        Returns True on success, False on failure.
        """
        dm = cls._registry.get(tab_id)
        if not dm:
            return False
        if path:
            dm.filepath = path
            dm.save(outpath=path)
        else:
            dm.save()
        return True

    @classmethod
    def get_document_bytes(cls, tab_id: str) -> Optional[bytes]:
        """
        Package the current PDF (with applied edits) into raw bytes and return.
        """
        dm = cls._registry.get(tab_id)
        if not dm:
            return None
        # We can save into a BytesIO object instead of to disk:
        import io
        buf = io.BytesIO()
        dm.doc.save(buf, deflate=True)
        buf.seek(0)
        return buf.read()

    @classmethod
    def get_document_model(cls, file_path: str) -> Optional[DocumentModel]:
        """
        Get or create a DocumentModel for the given file path.
        This is used by renderers that need access to document models.
        """
        # For now, create a basic DocumentModel for non-PDF files
        # In the future, this could be enhanced to support different document types
        try:
            dm = DocumentModel(filepath=file_path)
            return dm
        except Exception:
            # For non-PDF files, create a minimal document model
            return None
