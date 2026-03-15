from __future__ import annotations
import os, threading, tkinter as tk, fitz
from tkinter import filedialog, messagebox
from ttkbootstrap import ttk
from AnimatedProgressDialog import AnimatedProgressDialog    # your spinner
import pathlib
def _short(path: str, max_chars: int = 25) -> str:
    
    if len(path) <= max_chars:
        return path

    parts = list(pathlib.Path(path).parts)   # make it mutable
    shown: list[str] = []

    # build from the right-hand side until we’d exceed the limit
    while parts and len(os.path.join("…", *reversed(shown))) < max_chars:
        shown.append(parts.pop())

    shown.reverse()
    return os.path.join("…", *shown)
class SearchDialog:
    """
    Parameters
    ----------
    root          : Tk parent window
    pdf_files     : list[str]  – the list already loaded in the main UI
    listbox       : tk.Listbox – so we honour “Only selected”
    on_finish     : Callable[[list[str], list[str]], None]
                    receives (found_pdfs, found_images)
    """

    def __init__(self, root, pdf_files, listbox, on_finish):
        self.root          = root
        self.pdf_files     = pdf_files or []
        self.listbox       = listbox
        self.on_finish_cb  = on_finish

    # ────────────────────────────────────────────────────────────────────
    def show(self):
        self._build()
    # ────────────────────────────────────────────────────────────────────
    def _build(self):
        win = tk.Toplevel(self.root)
        win.title("Search")
        try:
            win.state('zoomed')  # This works on Windows and some other platforms
        except Exception:
            # Fallback: set geometry to screen size
            screen_w = win.winfo_screenwidth()
            screen_h = win.winfo_screenheight()
            win.geometry(f"{screen_w}x{screen_h}+0+0")
        win.transient(self.root)
        win.grab_set()

        # ===================== top controls =============================
        tf = ttk.Frame(win, padding=4); tf.pack(fill=tk.X, pady=4)

        ttk.Label(tf, text="Search:").pack(side=tk.LEFT, padx=4)
        term_v = tk.StringVar()
        tk.Entry(tf, textvariable=term_v, width=32)\
          .pack(side=tk.LEFT, padx=4)

        mode_v = tk.StringVar(value="program" if self.pdf_files else "system")
        ttk.Radiobutton(tf, text="Loaded files",
                        variable=mode_v, value="program",
                        state=tk.NORMAL if self.pdf_files else tk.DISABLED)\
           .pack(side=tk.LEFT, padx=6)
        ttk.Radiobutton(tf, text="Directory",
                        variable=mode_v, value="system")\
           .pack(side=tk.LEFT)

        dir_v  = tk.StringVar(value=os.path.expanduser("~"))
        dir_ent = ttk.Entry(tf, textvariable=dir_v,
                            width=26, state=tk.DISABLED)
        dir_ent.pack(side=tk.LEFT, padx=4)
        browse = ttk.Button(tf, text="Browse…", width=8,
                            command=lambda: self._pick_dir(dir_v))
        browse.pack(side=tk.LEFT)

        # ---------- options ------------
        opt = ttk.Frame(tf); opt.pack(side=tk.LEFT, padx=12)

        content_v  = tk.BooleanVar(master=win, value=False)
        sel_only_v = tk.BooleanVar(master=win, value=False)
        recurse_v  = tk.BooleanVar(master=win, value=True)
        case_v     = tk.BooleanVar(master=win, value=False)
        ext_v = tk.StringVar(master=win, value="*.pdf")   # default pattern


        ttk.Checkbutton(opt, text="Content (PDF)", variable=content_v)\
           .grid(row=0, column=0, sticky="w")
        sel_chk = ttk.Checkbutton(opt, text="Only selected",
                                  variable=sel_only_v, state=tk.DISABLED)
        sel_chk.grid(row=1, column=0, sticky="w")
        ttk.Checkbutton(opt, text="Match case", variable=case_v)\
           .grid(row=0, column=1, sticky="w", padx=8)
        ttk.Checkbutton(opt, text="Recurse sub-folders", variable=recurse_v)\
           .grid(row=1, column=1, sticky="w", padx=8)

        ttk.Label(opt, text="Extensions (comma):")\
           .grid(row=0, column=2, padx=(16,2))
        ttk.Entry(opt, textvariable=ext_v, width=18)\
           .grid(row=0, column=3)

        # ---------- enable / disable states ----------
        def _dir_state(*_):
            st = tk.NORMAL if mode_v.get()=="system" else tk.DISABLED
            dir_ent.configure(state=st); browse.configure(state=st)
        mode_v.trace_add("write", _dir_state); _dir_state()

        def _sel_state(*_):
            sel_chk.configure(state=(tk.NORMAL if
                        content_v.get() and mode_v.get()=="program"
                        else tk.DISABLED))
            if sel_chk["state"]==tk.DISABLED:
                sel_only_v.set(False)
        content_v.trace_add("write", _sel_state)
        mode_v.trace_add("write", _sel_state)
        _sel_state()

        # ---------- “Search” button ----------
        ttk.Button(tf, text="Search",
                   command=lambda: self._start_search(
                       term_v, mode_v, dir_v, content_v, sel_only_v,
                       recurse_v, case_v, ext_v, res_box, win))\
           .pack(side=tk.RIGHT, padx=10)

        # ===================== results list =============================
        ttk.Label(win, text="Results:").pack(anchor="w", padx=6)
        res_box = tk.Listbox(win, width=100, height=22)
        res_box.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)
        res_box.bind("<Double-1>",
                     lambda e: self._open_from_list(res_box))

        self.term_v = term_v   # remember for later close detection
        self.win    = win
        self.res    = res_box

    # ------------------------------------------------------------------
    def _pick_dir(self, var):
        p = filedialog.askdirectory(title="Choose folder")
        if p: var.set(p)

    # ------------------------------------------------------------------
    def _start_search(self, term_v, mode_v, dir_v, content_v, sel_only_v,
                      recurse_v, case_v, ext_v, res_box, win):

        wanted = term_v.get().strip()
        if not wanted:
            return
        res_box.delete(0, tk.END)

        spinner = AnimatedProgressDialog(win, title="Searching…",
                                         message="Initialising…")
        spinner.start_animation()

        pdf_hits, img_hits = [], []
        wanted_cmp  = (lambda x: x) if case_v.get() else (lambda x: x.lower())
        term        = wanted_cmp(wanted)
        extensions  = [e.strip().lstrip("*.") for e in ext_v.get().split(",") if e.strip()]
        extensions  = [f".{e.lower()}" for e in extensions] or [".pdf"]
        img_exts    = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff"}

        # -------------------------------------- threaded worker
        def work():
            try:
                if mode_v.get()=="program":
                    files = self.pdf_files
                    if content_v.get() and sel_only_v.get() and self.listbox:
                        files = [self.pdf_files[i] for i in self.listbox.curselection()] or files

                    for f in files:
                        spinner.set_message_safe(f"Searching { _short(os.path.basename(f)) }")
                        if not content_v.get():
                            if term in wanted_cmp(os.path.basename(f)):
                                pdf_hits.append(f)
                        else:
                            try:
                                d = fitz.open(f)
                                for p in d:
                                    if term in wanted_cmp(p.get_text()):
                                        pdf_hits.append(f"{f}  (page {p.number+1})")
                                        break
                                d.close()
                            except Exception as e:
                                pdf_hits.append(f"{f}  ({e})")
                # --- directory mode -------------------------------------------------
                else:
                    root   = dir_v.get()
                    walker = os.walk(root) if recurse_v.get() else [(root,[],os.listdir(root))]
                    for cur,_,files in walker:
                        spinner.set_message_safe(f"Searching { _short(cur) }")
                        for fn in files:
                            lo = fn.lower()
                            if not any(lo.endswith(x) for x in extensions):
                                continue
                            full = os.path.join(cur, fn)

                            # ----------- name search
                            if not content_v.get():
                                if term in wanted_cmp(fn):
                                    (pdf_hits if lo.endswith(".pdf") else img_hits).append(full)
                                continue

                            # ----------- content search
                            if not lo.endswith(".pdf"):
                                continue
                            try:
                                d = fitz.open(full)
                                for p in d:
                                    if term in wanted_cmp(p.get_text()):
                                        pdf_hits.append(f"{full}  (page {p.number+1})")
                                        break
                                d.close()
                            except Exception as e:
                                pdf_hits.append(f"{full}  ({e})")

            finally:
                spinner.stop_animation()
                win.after(0, lambda: self._finish(pdf_hits, img_hits))

        threading.Thread(target=work, daemon=True).start()

    # ------------------------------------------------------------------
    def _finish(self, pdfs, images):
        self.res.delete(0, tk.END)
        for ln in (pdfs + images) or ["No results"]:
            self.res.insert(tk.END, ln)

        # hand off to main app when user closes window
        def _on_close():
            self.win.destroy()
            self.on_finish_cb(pdfs, images)
        self.win.protocol("WM_DELETE_WINDOW", _on_close)

    # ------------------------------------------------------------------
    def _open_from_list(self, box):
        sel = box.curselection()
        if not sel: return
        path = box.get(sel[0]).split("  (page")[0]
        if os.path.isfile(path) and hasattr(self.root, "view_pdf"):
            self.root.view_pdf(path)
