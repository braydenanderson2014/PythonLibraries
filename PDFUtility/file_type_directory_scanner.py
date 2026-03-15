#!/usr/bin/env python3
# generic_directory_scanner.py

import os
from typing import List
from PyQt6.QtCore import QObject, QThread, pyqtSignal, QTimer
from PyQt6.QtWidgets import QFileDialog
from AnimatedProgressDialog import AnimatedProgressDialog
from PDFLogger import Logger
from file_list_controller import FileListController


class IncrementalFileScannerThread(QThread):
    """
    Walks a directory tree incrementally using os.scandir,
    emitting batches of matching file paths plus progress updates.
    """
    batch_ready     = pyqtSignal(list)          # List[str]
    progress_update = pyqtSignal(int, str)      # files_scanned, current_folder
    scan_complete   = pyqtSignal()

    def __init__(self, root: str, batch_size: int, file_patterns: list):
        super().__init__()
        self.root = root
        self.batch_size = batch_size
        # Handle both single pattern (string) and multiple patterns (list)
        if isinstance(file_patterns, str):
            file_patterns = [file_patterns]
            
        # normalize extensions: ensure they start with a dot, lowercased
        self.file_extensions = []
        for pattern in file_patterns:
            ext = pattern.strip().lower()
            if not ext.startswith("."):
                ext = "." + ext
            self.file_extensions.append(ext)

        self._cancel = False

    def cancel(self):
        self._cancel = True
        Logger().info("IncrementalFileScannerThread", "Scan cancelled by user")

    def run(self):
        logger = Logger()
        ext_list = ", ".join(self.file_extensions)
        logger.info("IncrementalFileScanner", f"Starting scan in '{self.root}' for files: {ext_list}")
        logger.info("IncrementalFileScanner", f"File extensions to match: {self.file_extensions}")
        stack = [self.root]
        files_scanned = 0
        batch: List[str] = []

        while stack and not self._cancel:
            current = stack.pop()
            logger.info("IncrementalFileScanner", f"Descending into '{current}' (stack size={len(stack)})")
            try:
                with os.scandir(current) as it:
                    for entry in it:
                        if self._cancel:
                            break

                        if entry.is_dir(follow_symlinks=False):
                            stack.append(entry.path)

                        elif entry.is_file(follow_symlinks=False):
                            files_scanned += 1

                            # match by any of the extensions
                            file_name_lower = entry.name.lower()
                            matches = any(file_name_lower.endswith(ext) for ext in self.file_extensions)
                            
                            # Debug logging for file matching
                            if matches:
                                logger.debug("IncrementalFileScanner", f"File {entry.name} matches extensions {self.file_extensions}")
                            
                            if matches:
                                # Debug log for file matches
                                if files_scanned <= 10:  # Only log first 10 matches to avoid spam
                                    logger.info("IncrementalFileScanner", f"MATCHED: {entry.name} with extensions {self.file_extensions}")
                                
                                full_path = entry.path
                                # sanity check
                                try:
                                    if os.path.getsize(full_path) > 100:
                                        batch.append(full_path)
                                except OSError:
                                    pass

                            # emit when batch threshold reached
                            if len(batch) >= self.batch_size:
                                logger.info("IncrementalFileScanner", f" Emitting batch of {len(batch)} files")
                                self.batch_ready.emit(batch.copy())
                                batch.clear()
                                QThread.msleep(0)

                            # periodic progress
                            if files_scanned % (self.batch_size * 2) == 0:
                                self.progress_update.emit(files_scanned, current)
                                QThread.msleep(0)

            except PermissionError:
                continue

        # leftover batch
        if batch and not self._cancel:
            self.batch_ready.emit(batch)

        if not self._cancel:
            logger.info("IncrementalFileScanner", f"Scan complete, total files: {files_scanned}")
        self.scan_complete.emit()



class FileDirectoryScanner(QObject):
    """
    Wrapper that shows an AnimatedProgressDialog and drives an
    IncrementalFileScannerThread, feeding each batch into your
    FileListController in small chunks so the UI never blocks.
    """
    scan_complete = pyqtSignal()

    def __init__(
        self,
        parent,
        file_list_controller: FileListController,
        batch_size: int = 100,
        file_pattern: str = ".pdf"
    ):
        super().__init__(parent)
        self.parent               = parent
        self.file_list_controller = file_list_controller
        self.batch_size           = batch_size
        
        # Handle both single pattern (string) and multiple patterns (list)
        if isinstance(file_pattern, str):
            file_pattern = [file_pattern]
        
        # normalize extensions once here
        self.file_patterns = []
        for pattern in file_pattern:
            ext = pattern.strip().lower()
            if not ext.startswith("."):
                ext = "." + ext
            self.file_patterns.append(ext)
            
        self.logger               = Logger()
        self._scan_thread         = None
        self._dialog              = None
        self._pending_batch: List[str] = []
        
        # Support for external multi-type specification
        self.selected_types = None

    def set_selected_types(self, selected_types: List[str]):
        """Set the file types to scan for (overrides default file_patterns)."""
        self.selected_types = selected_types

    def start_scan(self):
        # ask for folder
        folder = QFileDialog.getExistingDirectory(self.parent, "Select Folder to Scan")
        if not folder:
            return

        # Determine which file patterns to use
        if self.selected_types:
            file_patterns = self.selected_types
            Logger().info("FileDirectoryScanner", f"Using selected_types: {self.selected_types}")
        else:
            file_patterns = self.file_patterns
            Logger().info("FileDirectoryScanner", f"Using default file_patterns: {self.file_patterns}")
        
        # normalize and prepare extensions
        file_extensions = []
        for pattern in file_patterns:
            ext = pattern.strip().lower()
            if not ext.startswith("."):
                ext = "." + ext
            file_extensions.append(ext)

        Logger().info("FileDirectoryScanner", f"Final file_extensions for scan: {file_extensions}")

        # show spinner dialog
        self._dialog = AnimatedProgressDialog(
            self.parent,
            title=f"Scanning for files…",
            message="Initializing…"
        )
        self._dialog.cancelled.connect(self._on_cancel)
        self._dialog.show()

        # spawn thread
        self._scan_thread = IncrementalFileScannerThread(
            folder, self.batch_size, file_extensions  # Pass list of patterns
        )
        self._scan_thread.batch_ready.connect(self._on_raw_batch)
        self._scan_thread.progress_update.connect(self._on_progress)
        self._scan_thread.scan_complete.connect(self._on_complete)
        self._scan_thread.start()

    def _on_raw_batch(self, paths: List[str]):
        self.logger.info("FileDirectoryScanner", f"Received raw batch of {len(paths)} files")
        self._pending_batch += paths
        if self._pending_batch:
            QTimer.singleShot(0, self._flush_micro_batch)

    def _flush_micro_batch(self):
        if not self._pending_batch:
            return

        to_add = self._pending_batch[:10]
        del self._pending_batch[:10]

        self.file_list_controller.add_files(to_add)
        total = len(self.file_list_controller.get_files())
        if self._dialog:
            self._dialog.update_message(f"Added {total} files…")

        if self._pending_batch:
            QTimer.singleShot(10, self._flush_micro_batch)

    def _on_progress(self, count: int, folder: str):
        text = f"Scanned {count} files…\nIn: {folder}"
        self.logger.info("FileDirectoryScanner", text)
        if self._dialog:
            self._dialog.update_message(text)

    def _on_complete(self):
        if self._pending_batch:
            QTimer.singleShot(0, self._flush_micro_batch)
        def _finish():
            if self._dialog:
                self._dialog.close()
                self._dialog = None
            self.scan_complete.emit()
        QTimer.singleShot(0, _finish)

    def _on_cancel(self):
        if self._scan_thread and self._scan_thread.isRunning():
            self._scan_thread.cancel()
