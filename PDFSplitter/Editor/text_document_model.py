# editor/text_document_model.py
from typing import Optional

class TextDocumentModel:
    """
    A simple document model for text-based files like HTML, Markdown, etc.
    """
    
    def __init__(self, filepath: Optional[str] = None, content: str = ""):
        self.filepath = filepath
        self.content = content
        self.modified = False
        self.editable = True
        
        # Load content from file if filepath is provided and content is empty
        if filepath and not content:
            try:
                with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                    self.content = f.read()
            except Exception:
                self.content = ""
        
    def mark_modified(self):
        """Mark the document as modified."""
        self.modified = True
        
    def toggle_editable(self, yes_no: bool):
        """Toggle whether the document is editable."""
        self.editable = yes_no
        
    def get_content(self) -> str:
        """Get the document content."""
        return self.content
        
    def set_content(self, content: str):
        """Set the document content and mark as modified."""
        self.content = content
        self.modified = True
        
    def save(self, outpath: Optional[str] = None):
        """
        Save the document to disk.
        If outpath is None and filepath exists, overwrite; else use outpath.
        """
        target = outpath or self.filepath
        if not target:
            raise ValueError("No target path specified for saving.")
        
        with open(target, 'w', encoding='utf-8') as f:
            f.write(self.content)
            
        self.modified = False
        if outpath:
            self.filepath = outpath
