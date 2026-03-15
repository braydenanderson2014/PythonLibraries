# editor/tools/text_tool.py
import tkinter as tk
from editor.tool_base import BaseTool

class TextTool(BaseTool):
    def __init__(self, editor_window):
        super().__init__(editor_window, name="Text")
        self.start_x = None
        self.start_y = None
        self.text_widget = None

    def activate(self):
        super().activate()
        canvas = self.editor.get_current_canvas()
        canvas.config(cursor="xterm")
        canvas.bind("<Button-1>", self.on_mouse_down)

    def deactivate(self):
        super().deactivate()
        canvas = self.editor.get_current_canvas()
        canvas.config(cursor="")
        canvas.unbind("<Button-1>")

    def on_mouse_down(self, event):
        # When user clicks on a page in edit mode, create a new text overlay at that spot.
        page_num = self.editor.get_current_page_number()
        # Convert canvas coords → PDF coords so we know where to insert on save
        pdf_x, pdf_y = self.editor.canvas_to_pdf_coords(page_num, event.x, event.y)
        # Create a new tk.Text widget (single‐line) at event.x, event.y
        # Insert it—focus it immediately so user types
        self.text_widget = tk.Text(self.editor.get_current_container(), height=1, width=20)
        self.text_widget.place(x=event.x, y=event.y)
        self.text_widget.focus_set()

        # When user leaves or presses Enter, record the annotation:
        def _on_focus_out(evt):
            content = self.text_widget.get("1.0", "end-1c")
            if content.strip():
                # Insert as a new annotation object in DocumentModel
                ann = TextAnnotation(
                    page_number=page_num,
                    x=pdf_x,
                    y=pdf_y,
                    content=content,
                    fontname="helv",
                    fontsize=12
                )
                self.editor.doc_model.tool_annotations.setdefault(page_num, []).append(ann)
                self.editor.doc_model.mark_modified()
            self.text_widget.destroy()
            self.text_widget = None

        self.text_widget.bind("<FocusOut>", _on_focus_out)

class TextAnnotation:
    """
    A simple representation of a new text object (not replacing old span).
    """
    def __init__(self, page_number, x, y, content, fontname, fontsize):
        self.page_number = page_number
        self.x = x  # PDF‐space coords
        self.y = y
        self.content = content
        self.fontname = fontname
        self.fontsize = fontsize

    def commit_to_page(self, page):
        """
        Draw the text into the PDF page stream at (self.x, self.y).
        Note: fitz uses (x, y) with y measured from bottom of page,
        so ensure self.y is in correct coordinate system.
        """
        page.insert_text(
            (self.x, self.y),
            self.content,
            fontname=self.fontname,
            fontsize=self.fontsize,
            color=(0, 0, 0)
        )
