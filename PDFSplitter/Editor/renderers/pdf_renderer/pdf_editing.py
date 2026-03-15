import fitz  # PyMuPDF
import tkinter as tk

class PDFEditingHelper:
    """
    Helper class for advanced PDF editing (Word-like).
    """

    def __init__(self, renderer, settings):
        """
        renderer: instance of your PdfRenderer
        settings: dict loaded from settings.json
        """
        self.renderer = renderer
        self.settings = settings

    def insert_text_at_cursor(self, page_number, position, text, font="helv", fontsize=12, color=(0, 0, 0)):
        """
        Insert text at a given position on a page.
        position: (x, y) in PDF coordinates
        """
        doc = self.renderer.doc_model.doc
        page = doc[page_number]
        page.insert_text(position, text, fontname=font, fontsize=fontsize, color=color)
        doc.saveIncr()  # Save incrementally

    def delete_selected_text(self, page_number, rect):
        """
        Remove text in the given rectangle (rect: fitz.Rect or (x0, y0, x1, y1)).
        """
        doc = self.renderer.doc_model.doc
        page = doc[page_number]
        page.add_redact_annot(rect)
        page.apply_redactions()
        doc.saveIncr()

    def format_selected_text(self, page_number, rect, font="helv", fontsize=12, color=(0, 0, 0)):
        """
        Change formatting of text in the given rectangle.
        """
        # PyMuPDF does not support direct text formatting changes.
        # You would need to extract, remove, and re-insert text.
        # This is a placeholder for future expansion.
        pass

    # Add more methods as needed for cut/copy/paste, paragraph handling, etc.
    def set_font(self, font):
        return    
# --- Hook functions for settings.json ---

    def insert_text_at_cursor(renderer, settings, page_number, position, text, font="helv", fontsize=12, color=(0,0,0)):
        helper = PDFEditingHelper(renderer, settings)
        return helper.insert_text_at_cursor(page_number, position, text, font, fontsize, color)

    def delete_selected_text(renderer, settings, page_number, rect):
        helper = PDFEditingHelper(renderer, settings)
        return helper.delete_selected_text(page_number, rect)

    def format_selected_text(renderer, settings, page_number, rect, font="helv", fontsize=12, color=(0,0,0)):
        helper = PDFEditingHelper(renderer, settings)
        return helper.format_selected_text(page_number, rect, font, fontsize, color)

