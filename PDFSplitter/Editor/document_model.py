import fitz
from typing import List, Dict, Tuple, Optional

class DocumentModel:
    def __init__(self, filepath: Optional[str] = None):
        self.filepath = filepath
        self.modified = False
        self.modified = (filepath is None)
        self.editable = False
        self.doc: fitz.Document

        if self.filepath:
          self.doc = fitz.open(self.filepath)
        else:
          self.doc = fitz.open()
          self.doc.new_page(width=612, height=792)

        self._render_cache: Dict[int, Dict[float, any]] = {}

        self.text_edits: Dict[Tuple[int,int,int], Dict[str, any]] = {}

        self.tool_annotations: Dict[int, List[any]] = {}

    def mark_modified(self):
        self.modified = True

    def toggle_editable(self, yes_no: bool):
        self.editable = yes_no

    def get_page_count(self) -> int:
        return self.doc.page_count

    def get_page(self, page_number: int) -> fitz.Page:
        return self.doc.load_page(page_number)

    def save(self, outpath: Optional[str] = None):
        """
        Apply all in‐memory text_edits and tool_annotations to the PDF
        and write to disk.
        If outpath is None and filepath exists, overwrite; else use outpath.
        """
        target = outpath or self.filepath
        if not target:
            raise ValueError("No target path specified for saving.")

        for (page_num, block_idx, span_idx), edit_info in self.text_edits.items():
            page = self.get_page(page_num)
            # 1) Erase the original text bounding box by drawing a white rectangle
            bbox = edit_info["bbox"]   # (x0, y0, x1, y1) in PDF coords
            page.draw_rect(bbox, color=(1,1,1), fill=(1,1,1))
            # 2) Insert the new text:
            new_text = edit_info["new_text"]
            fontname = edit_info.get("fontname", "helv")
            fontsize = edit_info.get("fontsize", 12)
            # fitz coordinates: point = bottom-left corner
            # If you stored (x0, y0) as PDF coords, just use those (but convert to PyMuPDF’s convention).
            page.insert_text(
                (bbox[0], bbox[3] - fontsize),  # y‐coord is top of original box minus font height
                new_text,
                fontname=fontname,
                fontsize=fontsize,
                color=(0,0,0)
            )

        # Next, tell each tool to commit its annotations:
        for page_num, annotations in self.tool_annotations.items():
            page = self.get_page(page_num)
            for ann in annotations:
                ann.commit_to_page(page)

        # Finally, save the PDF.
        self.doc.save(target, deflate=True)
        self.clear_edits()  # resets modified flag
