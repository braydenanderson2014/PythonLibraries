#!/usr/bin/env python3
# pdf_directory_scanner.py

import os
from typing import Callable, List
from PyQt6.QtCore import QObject, QThread, pyqtSignal, QTimer, QCoreApplication
from PyQt6.QtWidgets import QFileDialog
from AnimatedProgressDialog import AnimatedProgressDialog
from PDFLogger import Logger
from file_list_controller import FileListController


class IncrementalPDFScannerThread(QThread):
    """
    Walks the directory tree incrementally using os.scandir,
    emitting batches of PDF paths plus progress updates.
    """
    batch_ready     = pyqtSignal(list)          # List[str]
    progress_update = pyqtSignal(int, str)      # files_scanned, current_folder
    scan_complete   = pyqtSignal()

    def __init__(self, root: str, batch_size: int = 100):
        super().__init__()
        self.root = root
        self.batch_size = batch_size
        self._cancel = False

    def cancel(self):
        self._cancel = True
        global logger
        logger.info("IncrementalPDFScannerThread", "Scan cancelled by user")

    def run(self):
        global logger
        logger = Logger()
        logger.info("IncrementalPDFScanner", f"Starting scan in '{self.root}'")
        stack = [self.root]
        files_scanned = 0
        batch: List[str] = []

        while stack and not self._cancel:
            current = stack.pop()
            logger.info("IncrementalPDFScanner", f"Descending into '{current}' (stack size now {len(stack)})")
            try:
                # Scan current directory
                with os.scandir(current) as it:
                    for entry in it:
                        if self._cancel:
                            break

                        # If it's a directory, schedule it
                        if entry.is_dir(follow_symlinks=False):
                            logger.info("IncrementalPDFScanner", f" Queued subdir: {entry.path}")
                            stack.append(entry.path)

                        # If it's a file, count & maybe batch it
                        elif entry.is_file(follow_symlinks=False):
                            files_scanned += 1

                            # Every batch_size hits, or if it's a PDF, add it
                            if entry.name.lower().endswith(".pdf"):
                                full_path = entry.path
                                # Quick sanity check
                                try:
                                    if os.path.getsize(full_path) > 100:
                                        batch.append(full_path)
                                except OSError:
                                    pass

                            # When batch builds up, emit it
                            if len(batch) >= self.batch_size:
                                logger.info("IncrementalPDFScanner", f" Emitting batch of {len(batch)} PDFs")
                                self.batch_ready.emit(batch.copy())
                                batch.clear()
                                # let UI breathe
                                QThread.msleep(0)

                            # periodically emit progress
                            if files_scanned % (self.batch_size * 2) == 0:
                                self.progress_update.emit(files_scanned, current)
                                QThread.msleep(0)

            except PermissionError:
                # skip folders we can't enter
                continue

        # Emit any leftover batch
        if batch and not self._cancel:
            self.batch_ready.emit(batch)

        if self._cancel:
            logger.info("IncrementalPDFScanner", "Scan was cancelled by user")
        else:
            logger.info("IncrementalPDFScanner", f"Scan complete, total files: {files_scanned}")

        # Tell wrapper we're done
        self.scan_complete.emit()


class PDFDirectoryScanner(QObject):
    """
    Wrapper that shows an AnimatedProgressDialog and drives
    an IncrementalPDFScannerThread, feeding each batch into
    your FileListController in small chunks so the UI never blocks.
    """
    scan_complete = pyqtSignal()

    def __init__(self, parent, file_list_controller: FileListController, batch_size=100):
        super().__init__(parent)
        self.parent              = parent
        self.file_list_controller = file_list_controller
        self.batch_size          = batch_size
        self.logger              = Logger()
        self._scan_thread        = None
        self._dialog             = None

        # these will hold each incoming batch to process in pieces:
        self._pending_batch: List[str] = []

    def start_scan(self):
        folder = QFileDialog.getExistingDirectory(self.parent, "Select Folder to Scan")
        if not folder:
            return

        self._dialog = AnimatedProgressDialog(
            self.parent,
            title="Scanning Directory…",
            message="Starting…"
        )
        self._dialog.cancelled.connect(self._on_cancel)
        self._dialog.show()

        self._scan_thread = IncrementalPDFScannerThread(folder, self.batch_size)
        self._scan_thread.batch_ready.connect(self._on_raw_batch)
        self._scan_thread.progress_update.connect(self._on_progress)
        self._scan_thread.scan_complete.connect(self._on_complete)
        self._scan_thread.start()

    def _on_raw_batch(self, pdf_paths: List[str]):
        """
        Called from scan thread: stash this batch and
        begin micro‑batching it into the controller.
        """
        self.logger.info("PDFDirectoryScanner", f"Received raw batch of {len(pdf_paths)} files")
        # queue it
        self._pending_batch += pdf_paths
        # if no micro‑batch loop is running, start it
        if len(self._pending_batch) > 0:
            QTimer.singleShot(0, self._flush_micro_batch)

    def _flush_micro_batch(self):
        """
        Process ~10 items at a time on the GUI thread,
        then reschedule itself until pending is empty.
        """
        if not self._pending_batch:
            return

        # take up to 10 paths
        to_add = self._pending_batch[:10]
        del self._pending_batch[:10]

        # add them
        self.file_list_controller.add_files(to_add)
        total = len(self.file_list_controller.get_files())
        
        # Safely update dialog message with null check
        if self._dialog:
            self._dialog.update_message(f"Added {total} files…")

        # Remove dangerous processEvents() call
        # Qt will handle UI updates naturally

        # schedule next slice
        if self._pending_batch:
            QTimer.singleShot(10, self._flush_micro_batch)  # Small delay to prevent overwhelming

    def _on_progress(self, count: int, folder: str):
        text = f"Scanned {count} files…\nIn: {folder}"
        self.logger.info("PDFDirectoryScanner", text)
        if self._dialog:
            self._dialog.update_message(text)
            # Remove dangerous processEvents() call

    def _on_complete(self):
        # ensure any leftover items get flushed
        if self._pending_batch:
            QTimer.singleShot(0, self._flush_micro_batch)

        # once everything’s done, close dialog
        def _finish():
            if self._dialog:
                self._dialog.close()
                self._dialog = None
            self.scan_complete.emit()

        # give one last chance to processEvents before closing
        QTimer.singleShot(0, _finish)

    def _on_cancel(self):
        if self._scan_thread and self._scan_thread.isRunning():
            self._scan_thread.cancel()
        
        # Clean up dialog on cancellation
        if self._dialog:
            self._dialog.close()
            self._dialog = None
            
        # Clear any pending batches
        self._pending_batch.clear()