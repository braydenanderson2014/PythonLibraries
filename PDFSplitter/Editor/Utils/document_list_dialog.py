# editor/document_list_dialog.py
import tkinter as tk
from tkinter import ttk, messagebox

class DocumentListDialog:
    """
    A simple Toplevel dialog that shows a list of file paths in a Listbox
    with multiple selection (Ctrl-Click, Shift-Click, Ctrl-A).  
    Returns the selected subset via a callback.
    """

    def __init__(self, master, files: list[str], title="Select documents", on_select=None):
        """
        master: parent window
        files: list of filepaths to display
        on_select: function(selected_list) called if user clicks OK
        """
        self.on_select = on_select
        self.top = tk.Toplevel(master)
        self.top.title(title)
        self.top.grab_set()   # modal
        self.top.geometry("600x400")

        frame = ttk.Frame(self.top, padding=10)
        frame.pack(fill="both", expand=True)

        label = ttk.Label(frame, text="Choose one or more PDFs:")
        label.pack(anchor="w")

        # listbox with scrollbar
        lb_frame = ttk.Frame(frame)
        lb_frame.pack(fill="both", expand=True, pady=5)
        scrollbar = ttk.Scrollbar(lb_frame, orient="vertical")
        self.listbox = tk.Listbox(
            lb_frame,
            selectmode="extended",
            yscrollcommand=scrollbar.set
        )
        scrollbar.config(command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.pack(side="left", fill="both", expand=True)

        for f in files:
            self.listbox.insert("end", f)

        # button row
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", pady=5)
        ok = ttk.Button(btn_frame, text="OK", command=self._on_ok)
        cancel = ttk.Button(btn_frame, text="Cancel", command=self._on_cancel)
        ok.pack(side="right", padx=5)
        cancel.pack(side="right")

        # bind Ctrl-A
        self.listbox.bind("<Control-a>", self._select_all)
        self._bind_scroll_events(self.listbox)


    def _bind_scroll_events(self, canvas):
        # Mouse wheel (Windows/macOS)
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        # Mouse wheel (Linux)
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))
        
        # Arrow keys (vertical)
        canvas.bind_all("<Up>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Down>", lambda e: canvas.yview_scroll(1, "units"))

        # Arrow keys (horizontal)
        canvas.bind_all("<Left>", lambda e: canvas.xview_scroll(-1, "units"))
        canvas.bind_all("<Right>", lambda e: canvas.xview_scroll(1, "units"))

        # Home/End
        canvas.bind_all("<Home>", lambda e: canvas.yview_moveto(0))
        canvas.bind_all("<End>", lambda e: canvas.yview_moveto(1))

        # Page Up/Down
        canvas.bind_all("<Prior>", lambda e: canvas.yview_scroll(-1, "pages"))  # Page Up
        canvas.bind_all("<Next>", lambda e: canvas.yview_scroll(1, "pages"))    # Page Down

    def _select_all(self, event=None):
        self.listbox.select_set(0, "end")
        return "break"

    def _on_ok(self):
        sel = [ self.listbox.get(i) for i in self.listbox.curselection() ]
        if not sel:
            messagebox.showwarning("No selection", "Please select at least one document.")
            return
        if self.on_select:
            self.on_select(sel)
        self.top.destroy()

    def _on_cancel(self):
        self.top.destroy()
