# editor/renderers/text_renderer/renderer.py

import os
import tkinter as tk
from tkinter import ttk, messagebox
from ..base   import BaseRenderer

class Renderer(BaseRenderer):
    @classmethod
    def extensions(cls):
        return [".txt"]

    @classmethod
    def preview_only(cls):
        return False

    @classmethod
    def tools(cls):
        return ["Text"]

    def open(self, path: str) -> str:
        # Build the preview frame
        tab_frame = ttk.Frame(self.editor.tab_manager.notebook)
        text = tk.Text(tab_frame, wrap="word")
        text.pack(fill="both", expand=True)

        # Load file
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                text.insert("1.0", f.read())
        except Exception as e:
            messagebox.showerror("Error", f"Cannot open {path}:\n{e}")
            tab_frame.destroy()
            raise

        # Track modifications
        def _on_mod(evt):
            if text.edit_modified():
                tid = self.editor.tab_manager.get_current_tab_id()
                self.editor.tab_manager.mark_tab_dirty(tid)
                text.edit_modified(False)
        text.bind("<<Modified>>", _on_mod)

        # Register the tab
        display = os.path.basename(path)
        tab_id = self.editor.tab_manager.register_tab_widget(
            tab_frame,
            display_name=display,
            doc_model=None,
            preview_path=path,
            renderer=self
        )
        info = self.editor.tab_manager.tabs[tab_id]
        info["preview_widget"] = text
        info["preview_path"]   = path
        info["preview_name"]   = display
        info["modified_text"]  = False

        return tab_id

    def save(self, tab_id: str):
        info   = self.editor.tab_manager.tabs[tab_id]
        text   = info["preview_widget"]
        path   = info["preview_path"]
        data   = text.get("1.0", "end-1c")
        with open(path, "w", encoding="utf-8") as f:
            f.write(data)
        info["modified_text"] = False
        self.editor.tab_manager.refresh_tab_label(tab_id)

    def save_as(self, tab_id: str, new_path: str):
        info = self.editor.tab_manager.tabs[tab_id]
        text = info["preview_widget"]
        data = text.get("1.0", "end-1c")
        with open(new_path, "w", encoding="utf-8") as f:
            f.write(data)
        # update tab info
        info["preview_path"] = new_path
        info["preview_name"] = os.path.basename(new_path)
        info["modified_text"] = False
        self.editor.tab_manager.refresh_tab_label(tab_id)

    def scroll(self, tab_id: str, direction: str, amount: int):
        """Scroll the text widget by a certain delta."""
        info = self.editor.tab_manager.tabs[tab_id]
        text = info["preview_widget"]
        
        if direction == "up":
            text.yview_scroll(-amount, "units")
        elif direction == "down":
            text.yview_scroll(amount, "units")
        elif direction == "left":
            text.xview_scroll(-amount, "units")
        elif direction == "right":
            text.xview_scroll(amount, "units")
