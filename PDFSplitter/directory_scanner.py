# pdf_directory_scanner.py
import os, time, threading, queue, tkinter as tk
from tkinter import filedialog, messagebox
from typing import Callable, List
from PDFUtility.PDFLogger import Logger
from ProgressDialog import TripleProgressDialog  # your dialog class
from ProgressDialog import QuadrupleProgressDialog  # if you have a custom dialog
from AnimatedProgressDialog import AnimatedProgressDialog  # if you have a custom dialog

class PDFDirectoryScanner:
    """
    Ask the user for a directory, walk it for *.pdf files, show a
    TripleProgressDialog, batch-deliver paths through `on_batch`.
    """

    def __init__(
        self,
        root: tk.Tk,
        on_batch: Callable[[List[str]], None],
        batch_size: int = 300,
        ui_poll_ms: int = 150,
    ):
        self.root = root
        self.on_batch = on_batch
        self.batch_size = max(1, batch_size)
        self.ui_poll_ms = ui_poll_ms
        self.logger = Logger()
        self.logger.info("PDFDirectoryScanner", "=========================================================")
        self.logger.info("PDFDirectoryScanner", "Initializing PDF Directory Scanner")
        self.logger.info("PDFDirectoryScanner", "=========================================================")

        # runtime state
        self._q = queue.Queue()
        self._scan_done = threading.Event()
        self._add_done = threading.Event()

        # counters
        self.files_scanned = 0
        self.folders_scanned = 0
        self.pdfs_found = 0
        self.pdfs_added = 0
        self.total_files = 1  # will be replaced after counting

    # ---------------------------------------------------------------- public
    def start_scan(self):
        folder = filedialog.askdirectory(title="Select Folder to Scan")
        if not folder:
            return
        self.logger.info("PDFDirectoryScanner", f"Starting scan in folder: {folder}")
        self.logger.info("PDFDirectoryScanner", "Now Calculating total files...")

        self.anim_dialog = AnimatedProgressDialog(self.root, title="Calculating total files", message="Please wait...")
        self.anim_dialog.start_animation()

        def count_files():
            file_count = 0
            folder_count = 0
            last_update = time.time()
            for root, dirs, files in os.walk(folder):
                folder_count += 1
                file_count += len(files)
                if time.time() - last_update > 0.1:
                    msg = f"Scanning...\nFolders: {folder_count}  Files: {file_count}"
                    self.root.after(0, lambda m=msg: self.anim_dialog.adjust_message(m))
                    last_update = time.time()
            msg = f"Scanning...\nFolders: {folder_count}  Files: {file_count}"
            self.root.after(0, lambda m=msg: self.anim_dialog.adjust_message(m))
            self.root.after(0, lambda: self._finish_count_files(folder, file_count, folder_count))

        threading.Thread(target=count_files, daemon=True).start()

    def _finish_count_files(self, folder, total_files, total_folders):
        self.total_files = total_files
        self.total_folders = total_folders
        self.anim_dialog.stop_animation()
        self.logger.info("PDFDirectoryScanner", f"Total files calculated: {self.total_files}")
        self.logger.info("PDFDirectoryScanner", f"Total folders calculated: {self.total_folders}")
        self.dlg = QuadrupleProgressDialog(
            self.root,
            title="Scanning PDFs",
            message=f"Scanning\n{folder}"
        )

        threading.Thread(target=self._walk_thread, args=(folder,), daemon=True).start()
        threading.Thread(target=self._add_thread, daemon=True).start()
        self.root.after(self.ui_poll_ms, self._poll_dialog)

    def _walk_thread(self, folder: str):
        for root_dir, _sub, files in os.walk(folder):
            if self.dlg.is_cancelled(): break

            self.folders_scanned += 1
            # Update folders progress (additional bar)
            self.dlg.update_additional_progress(self.folders_scanned, max(self.total_folders, 1))
            self.dlg.update_additional_status(
                f"Folders scanned: {self.folders_scanned}/{self.total_folders}"
            )

            files_in_this_dir = len(files) or 1
            for idx, name in enumerate(files, 1):
                if self.dlg.is_cancelled(): break

                self.files_scanned += 1
                self._update_overall_bar()

                self.dlg.update_current_progress(idx, files_in_this_dir)
                self.dlg.update_current_status(f"{root_dir}\\{name}")

                if name.lower().endswith(".pdf"):
                    self.pdfs_found += 1
                    self._q.put(os.path.join(root_dir, name))
                    self._update_extra_bar()

        self._scan_done.set()

    def _add_thread(self):
        batch: list[str] = []
        while not (self._scan_done.is_set() and self._q.empty()):
            while not self._q.empty() and len(batch) < self.batch_size:
                batch.append(self._q.get())

            if batch:
                self.on_batch(batch)
                self.pdfs_added += len(batch)
                self._update_extra_bar()
                batch = []
            time.sleep(0.05)

        if batch:
            self.on_batch(batch)
            self.pdfs_added += len(batch)
            self._update_extra_bar()

        self._add_done.set()

    # Progress helpers for each bar
    def _update_overall_bar(self):
        self.dlg.update_overall_progress(self.files_scanned, self.total_files)
        self.dlg.update_overall_status(
            f"Files scanned: {self.files_scanned}/{self.total_files}"
        )

    def _update_extra_bar(self):
        # PDFs added vs PDFs found (extra bar)
        self.dlg.update_extra_progress(self.pdfs_added, max(self.pdfs_found, 1))
        self.dlg.update_extra_status(
            f"PDFs found: {self.pdfs_found}  • added: {self.pdfs_added}"
        )

    # Dialog watchdog
    def _poll_dialog(self):
        if self.dlg.is_cancelled():
            self._scan_done.set()
            self._add_done.set()
            self.dlg.close()
            return

        if self._scan_done.is_set() and self._add_done.is_set():
            self.dlg.close()
            messagebox.showinfo(
                "Scan finished",
                f"Folders: {self.folders_scanned}\n"
                f"Files scanned: {self.files_scanned}\n"
                f"PDFs found: {self.pdfs_found}\n"
                f"PDFs added: {self.pdfs_added}"
            )
            return

        self.root.after(self.ui_poll_ms, self._poll_dialog)