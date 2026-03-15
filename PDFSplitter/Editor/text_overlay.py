# editor/text_overlay.py
import tkinter as tk
from tkinter import font as tkfont

class TextOverlay:
    """
    Manages overlaying editable widgets on top of a Canvas‐rendered PDF page.
    Each overlay corresponds to one “span” (a contiguous run of text with a single font/size).
    """

    def __init__(self, parent_canvas: tk.Canvas, page_number: int, renderer: "PDFRenderer", doc_model):
        self.canvas = parent_canvas
        self.page_number = page_number
        self.renderer = renderer
        self.doc_model = doc_model

        # Keep references to all overlay widgets (so they don’t get garbage‐collected)
        self._overlays: List[tk.Text] = []

        # Once page is rendered, call self._place_overlays()
        # in edit mode, otherwise do nothing (or hide them).

    def _place_overlays(self, zoom: float = 1.0):
        """
        Inspect the page’s text blocks, create an editable tk.Text (or tk.Entry)
        for each span, positioned correctly.  
        Only call if doc_model.editable is True.
        """
        blocks = self.renderer.get_page_text_blocks(self.page_number)

        for block_idx, block in enumerate(blocks):
            if "lines" not in block:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"]
                    fontname = span["font"]
                    fontsize = int(span["size"])
                    bbox = span["bbox"]  # [x0, y0, x1, y1] in PDF coords

                    # Skip empty strings or whitespace‐only
                    if not text.strip():
                        continue

                    # Convert PDF (bottom‐left origin) to Canvas (top‐left origin):
                    x0_pdf, y0_pdf, x1_pdf, y1_pdf = bbox
                    page = self.renderer.doc_model.get_page(self.page_number)
                    page_height = page.bound().y1  # in PDF coords

                    # PDF's y0 is distance from bottom; Canvas’s y = (page_height - y1_pdf)*zoom
                    # Similarly, x0_canvas = x0_pdf * zoom
                    x_canvas = x0_pdf * zoom
                    y_canvas = (page_height - y1_pdf) * zoom

                    width = (x1_pdf - x0_pdf) * zoom
                    height = (y1_pdf - y0_pdf) * zoom

                    # Create a small (single‐line) Text widget or Entry at that position:
                    txt_widget = tk.Text(
                        self.canvas.master,  # we might need to parent it to the same container as the canvas
                        wrap="none",
                        height=1,
                        width=max(1, int(len(text) * (fontsize / 10))),  # heuristic width
                    )

                    # Match font roughly (assuming we have it installed):
                    tk_font = tkfont.Font(family=fontname, size=int(fontsize * zoom))
                    txt_widget.configure(font=tk_font, bd=0, highlightthickness=0)
                    txt_widget.insert("1.0", text)
                    txt_widget.configure(state=tk.NORMAL if self.doc_model.editable else tk.DISABLED)

                    # Place it absolutely on top of the Canvas:
                    self.canvas.create_window(
                        x_canvas, y_canvas,
                        window=txt_widget,
                        anchor="nw",
                        width=width,
                        height=height
                    )

                    # When the user edits or leaves the widget, record the edit:
                    def _on_focus_out(event, bn=block_idx, ln=span["line"], sn=span["span"]):
                        new_text = txt_widget.get("1.0", "end-1c")
                        if new_text != text:
                            # Mark document modified
                            self.doc_model.mark_modified()
                            # Record bounding box (in PDF coords) to self.doc_model.text_edits
                            self.doc_model.text_edits[(self.page_number, bn, sn)] = {
                                "new_text": new_text,
                                "bbox": bbox,
                                "fontname": fontname,
                                "fontsize": fontsize,
                            }
                            # Update tab label via TabManager (we’ll have a callback)
                    txt_widget.bind("<FocusOut>", _on_focus_out)

                    self._overlays.append(txt_widget)

    def clear_overlays(self):
        """
        Destroys all overlay widgets (e.g. when switching pages or closing the doc).
        """
        for w in self._overlays:
            w.destroy()
        self._overlays.clear()

    def refresh(self, zoom: float = 1.0):
        """
        Called when entering edit mode or changing zoom/page: 
        clear old overlays → re‐place if editable.
        """
        self.clear_overlays()
        if self.doc_model.editable:
            self._place_overlays(zoom=zoom)
