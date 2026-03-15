# editor/editor_window.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Dict, List
from editor.document_model import DocumentModel
from editor.tab import Tab
def _on_tab_changed(self, tab_id: str):
        """
        Called when the user switches tabs. We should:
         - Deactivate current tool (if any)
         - Update toolbar for the new renderer
         - Possibly disable editing if the new document is read‐only
         - Reset UI (e.g. update page number indicator)
        """
        if self.current_tool:
            self.current_tool.deactivate()
            self.current_tool = None
        
        # Update toolbar for the new tab's renderer
        self.toolbar_manager.update_for_tab(tab_id)
        
        # You could also check if new tab's doc_model.editable is False, then gray‐out tool buttons.port TabManager
from editor.file_api import FileAPI
from editor.tool_base import BaseTool
import os
from directory_scanner import PDFDirectoryScanner
from editor.Utils.document_list_dialog import DocumentListDialog
import markdown   
import json
import atexit
from PDFUtility.PDFLogger import Logger
from SettingsController import SettingsController
from editor.file_types import FileTypeManager
from editor.config_manager import ConfigManager
from editor.toolbar_manager import ToolbarManager
# Ensure the editor session file exists

SESSION_FILE = os.path.join(os.path.expanduser("~"), ".pdfutility_editor_session.json")                   # pip install markdown
try:
    from tkhtmlview import HTMLLabel  # pip install tkhtmlview
    HTML_VIEW_AVAILABLE = True
except ImportError:
    HTML_VIEW_AVAILABLE = False
class EditorWindow:
    def __init__(self, master):
        self.master = master
        self.settings_controller = SettingsController(master)
        self.settings = self.settings_controller.load_settings()
        self.logger = Logger()
        self.logger.info("EditorWindow", "Initializing MyPDFEditor...")
        
        # Initialize configuration manager
        self.config_manager = ConfigManager(self)
        
        self.window = tk.Toplevel(master)
        try:
            self.window.state('zoomed')  # Works on Windows
        except Exception:
            # Fallback for other platforms
            screen_w = self.window.winfo_screenwidth()
            screen_h = self.window.winfo_screenheight()
            self.window.geometry(f"{screen_w}x{screen_h}+0+0")
        self.window.title("MyPDFEditor")
        self._setup_menu()
        
        # Create toolbar manager instead of old toolbar
        self.toolbar_manager = ToolbarManager(self.window, self.logger)
        
        self.tab_manager = TabManager(self.window, on_tab_change_callback=self._on_tab_changed)
        self.filetypes = FileTypeManager(self)

        
        self.current_tool: BaseTool = None
        self.selected_files: list[str] = []
        # track files already loaded
        self.opened_paths = set()
        # temporary storage while scanning
        self._scan_results = []
        self._scanner = None
        self.open_tabs: List[Dict[str,str]] = []
        self.has_files = False  # whether we have any files in editor Memory
        # load any previous session
        self._load_session()
        # ensure we save on exit
        atexit.register(self._save_session)
        self.is_alive = True
        self.window.bind('<Control-s>', lambda event: self._save_file())
        self.window.bind('<Control-S>', lambda event: self._save_file())
        self.window.bind('<Command-s>', lambda event: self._save_file())  # For macOS
        self.window.bind('<Command-S>', lambda event: self._save_file())  # For macOS

    
    def _load_session(self):
        if os.path.exists(SESSION_FILE):
            try:
                with open(SESSION_FILE, "r") as f:
                    tabs = json.load(f)
                for info in tabs:
                    path, kind = info["path"], info["kind"]
                    if os.path.exists(path):
                        if kind == "pdf":
                            dm = DocumentModel(filepath=path)
                            tid = self.tab_manager.add_tab(dm)
                            FileAPI._register_tab(tid, dm)
                        else:
                            self._open_preview_tab(path, editable=(kind=="txt"))
                        self.open_tabs.append(info)
            except Exception:
                pass  # ignore corrupt session

    def _save_session(self):
        with open(SESSION_FILE, "w") as f:
            json.dump(self.open_tabs, f, indent=2)
        self.is_alive = False  # mark as not alive to stop any background tasks

    def _setup_menu(self):
        menubar = tk.Menu(self.window)
        # File menu
        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="New", command=self._new_file)
        file_menu.add_command(label="Open...", command=self._open_file)
        file_menu.add_command(label="Save", command=self._save_file)
        file_menu.add_command(label="Save As...", command=self._save_as)
        file_menu.add_command(label="Scan Directory...", command=self._scan_directory)
        file_menu.add_command(label="Add PDFs from Main", command=self._load_from_main)
        file_menu.add_separator()
        file_menu.add_command(label="Close Tab", command=self._close_tab)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.master.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=False)
        edit_menu.add_command(label="Toggle Read-only/Edit Mode", command=self._toggle_edit_mode)
        menubar.add_cascade(label="Edit", menu=edit_menu)

        # Tools menu – will be injected with plugin names
        self.tools_menu = tk.Menu(menubar, tearoff=False)
        menubar.add_cascade(label="Tools", menu=self.tools_menu)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(label="About", command=self._about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.window.config(menu=menubar)

    def _setup_toolbar(self):
        """
        Create a toolbar Frame under the menu, and load any tool plugins found in editor/tools/.
        Each plugin is a subclass of BaseTool. For each, create a ToggleButton (or regular Button)
        that calls self.select_tool(plugin_name).
        """
        self.toolbar = ttk.Frame(self.window, padding=2)
        self.toolbar.pack(side="top", fill="x")

        # Dynamically import all modules in editor/tools/ and find BaseTool subclasses
        import pkgutil, importlib
        from editor.tools import __path__ as tools_path

        self.available_tools = {}
        for finder, name, ispkg in pkgutil.iter_modules(tools_path):
            module = importlib.import_module(f"editor.tools.{name}")
            for attr in dir(module):
                cls = getattr(module, attr)
                try:
                    if issubclass(cls, BaseTool) and cls is not BaseTool:
                        # Instantiate it (passing self as the editor window)
                        tool_instance = cls(self)
                        self.available_tools[tool_instance.name] = tool_instance
                except Exception:
                    continue

        # Create a button for each available tool
        for tool_name, tool_obj in self.available_tools.items():
            btn = ttk.Button(self.toolbar, text=tool_name, command=lambda tn=tool_name: self.select_tool(tn))
            btn.pack(side="left", padx=2)

    def select_tool(self, tool_name: str):
        """
        Deactivate any current tool, then activate the chosen one.  
        """
        canvas = self.tab_manager.get_current_canvas()
        if canvas is None:
            messagebox.showwarning(
                "No document open",
                "Please open or create a PDF before selecting a tool."
            )
            return

        dm = self.tab_manager.get_current_doc_model()
        if not dm.editable:
            messagebox.showinfo(
                "Read-only mode",
                "Toggle to Edit Mode before using tools."
            )
            return
        if self.current_tool:
            self.current_tool.deactivate()
        tool = self.available_tools.get(tool_name)
        if tool:
            tool.activate()
            self.current_tool = tool

    def _on_tab_changed(self, tab_id: str):
        """
        Called when the user switches tabs. We should:
         - Deactivate current tool (if any)
         - Possibly disable editing if the new document is read‐only
         - Reset UI (e.g. update page number indicator)
        """
        if self.current_tool:
            self.current_tool.deactivate()
            self.current_tool = None
        # You could also check if new tab’s doc_model.editable is False, then gray‐out tool buttons.

    # — File Menu Callbacks —
    def _new_file(self):
        tab_id = self.filetypes.open("")  
        # register it for session restore as “pdf”
        self._register_open_tab("", "pdf")
    def _register_open_tab(self, path: str, kind: str):
        # remove any existing entry
        self.open_tabs = [t for t in self.open_tabs if t["path"] != path]
        # append at end
        self.open_tabs.append({"path": path, "kind": kind})

    def _open_file(self):
        filetypes = self.filetypes.get_open_filetypes()
        path = filedialog.askopenfilename(
            title="Open File",
            filetypes=filetypes
        )
        if not path:
            return

        try:
            tab_id = self.filetypes.open(path)
        except ValueError as e:
            messagebox.showwarning("Unsupported File", str(e))
            return

        # record for session restore
        ext = os.path.splitext(path)[1].lower()
        kind = {".txt":"txt", ".md":"preview", ".html":"preview"}.get(ext, "pdf")
        self._register_open_tab(path, kind)


    def _save_file(self):
        tid = self.tab_manager.get_current_tab_id()
        if not tid:
            return
        self.filetypes.save(tid)

    def _save_as(self):
        tid = self.tab_manager.get_current_tab_id()
        if not tid:
            return

        # ask user for new path (extension will be inferred per renderer if you like)
        # here we simply let the user pick any filename
        newpath = filedialog.asksaveasfilename(defaultextension="",
                                               filetypes=[("All Files", "*.*")])
        if not newpath:
            return

        self.filetypes.save_as(tid, newpath)
    def _close_tab(self):
        tab_id = self.tab_manager.get_current_tab_id()
        if not tab_id:
            return
        dm = self.tab_manager.get_current_doc_model()
        if dm:
            if dm.modified:
                ans = messagebox.askyesnocancel("Unsaved Changes", "Save changes before closing?")
                if ans is None:
                    return  # cancel
                if ans:
                    self._save_file()
        self.tab_manager.close_tab(tab_id)
        FileAPI._unregister_tab(tab_id)

    # — Edit Menu Callbacks —
    def _toggle_edit_mode(self):
        tab_id = self.tab_manager.get_current_tab_id()
        if not tab_id:
            return
        dm = self.tab_manager.get_current_doc_model()
        dm.toggle_editable(not dm.editable)
        overlay = self.tab_manager.get_current_overlay()
        if overlay:
            overlay.refresh(zoom=self.tab_manager.tabs[tab_id]["zoom"])

    # — Help Menu —
    def _about(self):
        messagebox.showinfo("About", "MyPDFEditor v0.1\nBuilt with Tkinter & PyMuPDF")

    # — Coordinate conversion utilities —
    def canvas_to_pdf_coords(self, page_number: int, x_canvas: int, y_canvas: int):
        """
        Convert (x_canvas, y_canvas) → PDF coordinate at bottom‐left origin.
        Need to know the zoom and the original page height (in px).
        """
        info = self.tab_manager.tabs[self.tab_manager.get_current_tab_id()]
        zoom = info["zoom"]
        page = info["renderer"].doc_model.get_page(page_number)
        page_height = page.bound().y1  # in PDF pts

        pdf_x = x_canvas / zoom
        # y_canvas is measured from top of canvas. PDF’s y is from bottom, so:
        pdf_y = (page_height - (y_canvas / zoom))
        return pdf_x, pdf_y

    def get_current_canvas(self):
        """
        Get the current canvas object for the active tab.
        """
        return self.tab_manager.get_current_canvas()

    def _load_from_main(self):
        """
        Placeholder if the host program wants to push a list in:
        you could pop open the same dialog around the existing list.
        """
        if not self.selected_files:
            messagebox.showinfo("No files", "No files have been provided by the main program yet.")
            return

        DocumentListDialog(
            master=self.window,
            files=self.selected_files,
            title="Select from main program",
            on_select=self._on_files_selected
        )

    def set_external_file_list(self, files: list[str]):
        """
        Called by the main PDFUtility program to hand the editor
        a list of filepaths to choose from.
        """
        DocumentListDialog(
            master=self.window,
            files=[f for f in files if f not in self.opened_paths],
            title="Select files from main program",
            on_select=self._on_files_selected
        )

    def set_external_file_list_silent(self, files: list[str]):
        self.selected_files += [f for f in files if f not in self.opened_paths]

    def set_external_file_list_selection(self, indices, pdf_files):
        # indices: list of ints from listbox.curselection()
        # pdf_files: the list of file paths shown in the listbox
        filepaths = [pdf_files[i] for i in indices if pdf_files[i] not in self.opened_paths]
        for f in filepaths:
            if f not in self.selected_files:
                self.selected_files.append(f)
        self._on_files_selected(filepaths)

    def render_readme_file(self, path: str):
        self._on_files_selected([path])

    def get_external_file_list(self) -> list[str]:
        """
        Returns the list of filepaths provided by the main program.
        """
        return self.selected_files

    def _scan_directory(self):
        # clear old results
        self._scan_results.clear()

        # create scanner and remember it
        self._scanner = PDFDirectoryScanner(
            root=self.window,
            on_batch=self._on_scan_batch,
            batch_size=200,
            ui_poll_ms=100
        )
        self._scanner.start_scan()

        # start polling for scan‐completion
        self.window.after(200, self._poll_scan_complete)

    def _on_scan_batch(self, batch: list[str]):
        # accumulate every batch
        self._scan_results.extend(batch)

    def _poll_scan_complete(self):
        # check both the walk and add threads are done
        if self._scanner._scan_done.is_set() and self._scanner._add_done.is_set():
            # only show dialog if we actually found something
            if self._scan_results:
                DocumentListDialog(
                    master=self.window,
                    files=self._scan_results,
                    title="Select scanned PDFs",
                    on_select=self._on_files_selected
                )
                self.has_files = True
                for path in self._scan_results:
                    self.selected_files.append(path)
                
        else:
            # not done yet → check again in 200ms
            self.window.after(200, self._poll_scan_complete)

    def get_editor_files(self):
        return self._scan_results
    
    def get_has_files(self):
        """
        Returns whether the editor has any files loaded in memory.
        This is used to determine if the editor can be closed or not.
        """
        if len(self._scan_results) > 0: 
            self.has_files = True
        else:
            self.has_files = False
        return self.has_files

    def _on_files_selected(self, files):
        for path in files:
            if path in self.opened_paths:
                continue

            try:
                tab_id = self.filetypes.open(path)
            except ValueError as e:
                self.logger.warning("EditorWindow", f"Cannot open {path}: {e}")
                continue

            self.opened_paths.add(path)
            ext = os.path.splitext(path)[1].lower()
            kind = {".txt":"txt", ".md":"preview", ".html":"preview"}.get(ext, "pdf")
            self._register_open_tab(path, kind)

    def _on_txt_modified(self, event, path):
        widget = event.widget
        tid = self.tab_manager.get_current_tab_id()
        info = self.tab_manager.tabs[tid]
        # Always mark dirty if content is different from file
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                original = f.read()
        except Exception:
            original = ""
        current = widget.get("1.0", "end-1c")
        if current != original:
            self.tab_manager.mark_tab_dirty(tid)
            info["modified_text"] = True
        else:
            info["modified_text"] = False
        widget.edit_modified(False)
    
    def _open_preview_tab(self, path: str, editable: bool = False):
        """Opens a read-only preview of txt/md/html in its own tab."""
        ext = os.path.splitext(path)[1].lower()
        tab_frame = ttk.Frame(self.tab_manager.notebook)
        # Create a container frame with a scrollbar
        container = ttk.Frame(tab_frame)
        container.pack(fill="both", expand=True)
        vscroll = ttk.Scrollbar(container, orient="vertical")
        vscroll.pack(side="right", fill="y")

        if ext == ".txt" or not HTML_VIEW_AVAILABLE:
            # Plain text (editable only when requested)
            text = tk.Text(container, wrap="word", yscrollcommand=vscroll.set)
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                text.insert("1.0", f.read())
            # editable for .txt files, read-only elsewhere
            state = "normal" if editable else "disabled"
            text.configure(state=state)
            text.pack(fill="both", expand=True)
            vscroll.config(command=text.yview)

            if editable:
                # limit tools: only allow text edits
                text.bind("<<Modified>>", lambda e, p=path: self._on_txt_modified(e, p))
                text.bind("<KeyRelease>", lambda e, p=path: self._on_txt_modified(e, p))

        elif ext == ".md":
            # Markdown → HTML → HTMLLabel
            raw = ""
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                raw = f.read()
            html = markdown.markdown(raw)
            html_lbl = HTMLLabel(container, html=html, yscrollcommand=vscroll.set)
            html_lbl.pack(fill="both", expand=True)
            vscroll.config(command=html_lbl.yview)

        elif ext == ".html":
            # Direct HTML render
            html_lbl = HTMLLabel(container, html=open(path, "r", encoding="utf-8").read(),
                                 yscrollcommand=vscroll.set)
            html_lbl.pack(fill="both", expand=True)
            vscroll.config(command=html_lbl.yview)

        else:
            # unsupported; show a warning
            messagebox.showwarning("Unsupported", f"No previewer for *{ext}* files")
            tab_frame.destroy()
            return

        # Add the tab just like a PDF tab
        display = os.path.basename(path)
        tab_id = self.tab_manager.register_tab_widget(
            tab_frame,
            display_name=display,
            doc_model=None,
            preview_path=path
        )
        # Ensure modified_text is initialized
        self.tab_manager.tabs[tab_id]["modified_text"] = False
        self.tab_manager.tabs[tab_id]["preview_widget"] = text if ext == ".txt" or not HTML_VIEW_AVAILABLE else None
