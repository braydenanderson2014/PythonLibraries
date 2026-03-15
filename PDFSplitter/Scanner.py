import ttkbootstrap as ttk
import tkinter as tk
from tkinter import filedialog, messagebox
from ProgressDialog import QuadrupleProgressDialog
import os
import threading
import time
from enum import Enum
from queue import Queue
from PDFUtility.PDFLogger import Logger
from SettingsController import SettingsController

class FileType(Enum):
    PDF = ("PDF Files", [".pdf"])
    IMAGE = ("Image Files", [".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".webp"])
    DOCUMENT = ("Document Files", [".doc", ".docx", ".odt", ".rtf", ".txt"])
    SPREADSHEET = ("Spreadsheet Files", [".xls", ".xlsx", ".ods", ".csv"])
    PRESENTATION = ("Presentation Files", [".ppt", ".pptx", ".odp"])
    ARCHIVE = ("Archive Files", [".zip", ".rar", ".7z", ".tar", ".gz"])
    VIDEO = ("Video Files", [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"])
    AUDIO = ("Audio Files", [".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma"])
    ALL = ("All Files", ["*"])

    def __init__(self, display_name, extensions):
        self.display_name = display_name
        self.extensions = set(ext.lower() for ext in extensions)

    def matches_file(self, filename):
        if "*" in self.extensions:
            return True
        ext = os.path.splitext(filename)[1].lower()
        return ext in self.extensions
class Scanner:
    def __init__(self, root):
        self.root = root
        self.logger = Logger()
        self.scan_dir = None
        self.scan_files = []
        self.scan_count = 0
        self.scan_total = 0
        self.scan_progress = None
        self.file_type = FileType.PDF  # Default to PDF
        self.settingsController = SettingsController(self.root)
        self.settings = self.settingsController.load_settings()

    def set_parent_scan_dir(self, scan_dir):
        self.scan_dir = scan_dir

    def get_scan_dir(self):
        return self.scan_dir
    
    def get_scan_files(self):
        return self.scan_files
    
    def get_scan_count(self):
        return self.scan_count
    
    def get_scan_total(self):
        return self.scan_total
    
    def set_file_type(self, file_type):
        """Set the file type to scan for"""
        if isinstance(file_type, FileType):
            self.file_type = file_type
            self.logger.info("Scanner", f"File type set to: {file_type.display_name}")
        else:
            raise ValueError("file_type must be a FileType enum value")
    
    def get_file_type(self):
        """Get the current file type being scanned for"""
        return self.file_type
    
    def get_file_type_display_name(self):
        """Get the display name of the current file type"""
        return self.file_type.display_name
        
    def get_file_type_extensions(self):
        """Get the extensions for the current file type"""
        return self.file_type.extensions

    def scan_folder(self):
        """Scan folder for files of the specified type dynamically with an optimized queue system for scanning and processing files."""
        folder_path = filedialog.askdirectory(title="Select Folder to Scan")
        self.logger.info("Scanner", f"Scanning folder: {folder_path} for {self.file_type.display_name}")

        if not folder_path:
            self.logger.info("Scanner", "No folder selected")
            return

        # Create quadruple progress dialog
        progress = QuadrupleProgressDialog(
            self.root,
            title=f"Scanning for {self.file_type.display_name}",
            message=f"Scanning folder: {folder_path}"
        )

        # Store results
        result = {"files": [], "error": None}
        file_queue = Queue()  # Queue for found files
        total_scanned = 0  # Tracks ALL files scanned (target files + others)
        total_target_files = 0  # Tracks the number of target files found
        total_files_added = 0  # Tracks files that have been processed and added to the list
        total_files_in_drive = sum([len(files) for _, _, files in os.walk(folder_path)])  # Count total files in drive
        batch_size = 300  # Number of files to process in each batch
        list_update_interval = 30  # Number of files to process before updating UI

        # Ensure total_files_in_drive is at least 1 to avoid division by zero
        total_files_in_drive = max(1, total_files_in_drive)

        # **Threading Events to Track Completion**
        scanning_done = threading.Event()
        adding_done = threading.Event()

        def add_files_to_list():
            """Processes and adds queued files in batches, running in a separate thread without blocking scanning."""
            nonlocal total_files_added
            pending_updates = []

            while not scanning_done.is_set() or not file_queue.empty():
                if progress.is_cancelled():
                    self.logger.info("Scanner", "Scanning cancelled")
                    return

                # Process files in batches
                batch = []
                while not file_queue.empty() and len(batch) < batch_size:
                    batch.append(file_queue.get())
                    self.logger.info("Scanner", f"Adding {self.file_type.display_name.lower()} to batch: {batch[-1]}")

                if batch:
                    # Add batch of files to list
                    for target_file in batch:
                        self.scan_files.append(target_file)
                        total_files_added += 1
                        pending_updates.append(target_file)  # Store for batch UI update
                        if total_files_added % 100 == 0:
                            self.logger.info("Scanner", f"Added {total_files_added} files so far.")

                        progress.update_additional_progress(total_files_added, max(1, total_target_files))  # Avoid /0
                        progress.update_additional_status(f"Added {total_files_added} {self.file_type.display_name.lower()} to list.")

                    # **Batch UI Updates to Prevent Slowdown**
                    if len(pending_updates) >= list_update_interval:
                        self.root.after(100, self.update_listbox)  # Update UI in a separate call
                        pending_updates.clear()  # Reset batch update buffer
                time.sleep(1)  # **Lower priority for adding files to avoid scanner slowdowns**

            # **Mark adding process as complete**
            self.logger.info("Scanner", "Adding process complete")
            adding_done.set()

        def scan_process():
            """Scan folder in background thread while allowing separate file processing."""
            try:
                nonlocal total_scanned, total_target_files  # Ensure we can modify these variables

                progress.update_overall_status("Scanning folders...")
                progress.update_message(f"Scanning for {self.file_type.display_name}...")
                progress.update_overall_progress(0, total_files_in_drive)
                progress.update_current_progress(0, 100)
                progress.update_additional_progress(0, max(1, total_target_files))  # Avoid /0
                progress.update_extra_progress(0, 100)
                self.logger.info("Scanner", "Scanning started")  

                for root, dirs, files in os.walk(folder_path):
                    if progress.is_cancelled():
                        result["error"] = "Operation cancelled by user"
                        self.logger.info("Scanner", "Scanning cancelled by user; Awaiting UI Update...")
                        self.root.after(100, complete_operation)
                        return

                    total_files_in_folder = max(1, len(files))  # Ensure non-zero denominator
                    self.logger.info("Scanner", f"Preparing to process {total_files_in_folder} files")
                    for i, file in enumerate(files):
                        total_scanned += 1  # Increase total scanned files (includes non-target files)
                        self.logger.info("Scanner", f"Total Scanned: {total_scanned}/{total_files_in_drive} files")
                        
                        # Check if file matches the current file type
                        if self.file_type.matches_file(file):
                            total_target_files += 1
                            full_path = os.path.join(root, file)
                            self.logger.info("Scanner", f"Found {self.file_type.display_name.lower()}: {full_path} ({self.file_type.display_name.lower()} {total_target_files}/{total_scanned})")
                            file_queue.put(full_path)  # Queue the file for batch processing

                            # **Update found count, even if it's not added yet**
                            progress.update_additional_progress(total_files_added, max(1, total_target_files))  # Avoid /0
                            progress.update_additional_status(f"Found {total_target_files} {self.file_type.display_name.lower()}")
                            self.logger.info("Scanner", f"Found {self.file_type.display_name.lower()}: {full_path} ({self.file_type.display_name.lower()} {total_target_files}/{total_scanned})")
                        
                        # **Update Progress Bars**
                        progress.update_overall_progress(total_scanned, total_files_in_drive)
                        progress.update_overall_status(f"Scanned {total_scanned}/{total_files_in_drive} files")
                        self.logger.info("Scanner", f"Scanned {total_scanned}/{total_files_in_drive} files")

                        progress.update_current_progress(i + 1, total_files_in_folder)
                        progress.update_current_status(f"Scanning folder: {root} (File {i+1}/{total_files_in_folder})")
                        self.logger.info("Scanner", f"Scanning folder: {root} (File {i+1}/{total_files_in_folder})")

                        progress.update_extra_progress(total_scanned, total_files_in_drive)
                        progress.update_extra_status(f"Completed scanning folder: {root}")
                        self.logger.info("Scanner", f"Completed scanning folder: {root}")

                        self.root.after(50, lambda: None)  # **Reduce delay for smoother scanning**
                        self.logger.info("Scanner", f"Scheduled UI Update for current progress bar")
                    # Reset current progress bar for the next folder
                    progress.reset_current_progress()
                    self.logger.info("Scanner", f"Reset current progress bar for the next folder")

                # **Mark scanning process as complete**
                scanning_done.set()
                self.logger.info("Scanner", "Scanning process complete")

                # Final progress update
                progress.update_overall_progress(total_files_in_drive, total_files_in_drive)
                progress.update_overall_status(f"Scan Complete: {total_scanned}/{total_files_in_drive} files scanned.")
                progress.update_message("Scan complete!")

                self.root.after(100, complete_operation)
                self.root.after(100, self.update_listbox)

            except Exception as e:
                result["error"] = str(e)
                self.logger.error("Scanner", f"Error scanning folder: {result['error']}")
                self.root.after(100, complete_operation)

        def complete_operation():
            """Ensure both scanning and adding are completed before closing the progress dialog."""
            def wait_for_completion():
                self.logger.info("Scanner", "Waiting for both scanning and adding to complete...")
                if scanning_done.is_set() and adding_done.is_set():
                    progress.close()
                    self.status_label.config(
                        text=f"Added {total_files_added} {self.file_type.display_name.lower()} from folder scan (Scanned {total_scanned} files)"
                    )
                    self.logger.info("Scanner", "Closing progress dialog")
                else:
                    self.root.after(200, wait_for_completion)  # **Check again in 200ms**
                    self.logger.info("Scanner", "Scheduled UI Update for progress dialog")
            wait_for_completion()  # Start waiting loop

            # Handle errors
            if result["error"]:
                self.logger.error("Scanner", f"Error scanning folder: {result['error']}")
                messagebox.showerror("Scanner", f"Error scanning folder: {result['error']}")
                return

        # Start scanning and processing threads
        self.scan_thread = threading.Thread(target=scan_process, daemon=True)
        self.scan_thread.start()
        self.add_thread = threading.Thread(target=add_files_to_list, daemon=True)
        self.add_thread.start()  # Separate thread for adding files

    