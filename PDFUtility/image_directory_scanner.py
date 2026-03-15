#!/usr/bin/env python3
# image_directory_scanner.py - Directory Scanner for Image Controller

import os
import threading
import time
from enum import Enum
from queue import Queue
from PyQt6.QtCore import QObject, pyqtSignal

from PDFLogger import Logger
from settings_controller import SettingsController
from ProgressDialog import ProgressDialog, DualProgressDialog

class FileType(Enum):
    """Enumeration of file types that can be scanned for"""
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

class ImageDirectoryScanner(QObject):
    """Directory scanner for the Image Controller"""
    
    # Define signals for progress reporting
    progress_signal = pyqtSignal(int, int)     # current, total
    sub_progress_signal = pyqtSignal(int, int) # current, total
    status_signal = pyqtSignal(str)            # status message
    complete_signal = pyqtSignal(bool, str, list)    # success, message, files_list
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.logger = Logger()
        self.settings_controller = SettingsController()
        self.settings = self.settings_controller.load_settings()
        
        # Initialize state variables
        self.scan_dir = None
        self.scan_files = []
        self.scan_count = 0
        self.scan_total = 0
        self.file_type = FileType.IMAGE  # Default to IMAGE
        self.cancel_requested = False
        self.scanning_in_progress = False

    def set_scan_dir(self, scan_dir):
        """Set the directory to scan"""
        self.scan_dir = scan_dir

    def get_scan_dir(self):
        """Get the current scan directory"""
        return self.scan_dir
    
    def get_scan_files(self):
        """Get the list of files found during the scan"""
        return self.scan_files
    
    def get_scan_count(self):
        """Get the count of files processed"""
        return self.scan_count
    
    def get_scan_total(self):
        """Get the total count of files to process"""
        return self.scan_total
    
    def set_file_type(self, file_type):
        """Set the file type to scan for"""
        if isinstance(file_type, FileType):
            self.file_type = file_type
            self.logger.info("ImageDirectoryScanner", f"File type set to: {file_type.display_name}")
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

    def scan_folder(self, folder_path=None):
        """Scan folder for files of the specified type"""
        if self.scanning_in_progress:
            self.logger.warning("ImageDirectoryScanner", "Scanning already in progress")
            return False
            
        self.scanning_in_progress = True
        self.cancel_requested = False
        self.scan_files = []
        
        # If no folder path provided, use the scan_dir
        if not folder_path:
            from PyQt6.QtWidgets import QFileDialog
            folder_path = QFileDialog.getExistingDirectory(
                self.parent,
                "Select Folder to Scan",
                self.scan_dir or ""
            )
            
        if not folder_path:
            self.logger.info("ImageDirectoryScanner", "No folder selected")
            self.scanning_in_progress = False
            return False
            
        self.scan_dir = folder_path
        self.logger.info("ImageDirectoryScanner", f"Scanning folder: {folder_path} for {self.file_type.display_name}")
        
        # Start scanning in a separate thread
        scan_thread = threading.Thread(
            target=self._scan_process,
            args=(folder_path,),
            daemon=True
        )
        scan_thread.start()
        
        return True
        
    def _scan_process(self, folder_path):
        """Internal method to handle the scanning process in a background thread"""
        try:
            # Create progress dialog
            progress_dialog = DualProgressDialog(
                self.parent,
                f"Scanning for {self.file_type.display_name}",
                f"Scanning folder: {folder_path}"
            )
            
            # Connect signals
            self.progress_signal.connect(progress_dialog.update_overall_progress)
            self.sub_progress_signal.connect(progress_dialog.update_current_progress)
            self.status_signal.connect(progress_dialog.update_status)
            progress_dialog.cancelled.connect(self._handle_cancel)
            
            progress_dialog.show()
            
            # Variables to track progress
            file_queue = Queue()  # Queue for found files
            total_scanned = 0  # All files scanned
            total_target_files = 0  # Target file type found
            total_files_added = 0  # Files added to list
            
            # Count total files in folder tree (for progress reporting)
            self.status_signal.emit("Counting files in folder...")
            total_files_in_folder = sum([len(files) for _, _, files in os.walk(folder_path)])
            total_files_in_folder = max(1, total_files_in_folder)  # Avoid division by zero
            
            self.logger.info("ImageDirectoryScanner", f"Total files to scan: {total_files_in_folder}")
            self.status_signal.emit(f"Found {total_files_in_folder} total files to scan")
            
            # Prepare for batch processing
            batch_size = 300
            all_files = []
            
            # Scan for files
            self.status_signal.emit("Scanning for files...")
            for root, _, files in os.walk(folder_path):
                if self.cancel_requested:
                    self.logger.info("ImageDirectoryScanner", "Scanning cancelled")
                    break
                    
                for file in files:
                    total_scanned += 1
                    
                    if self.file_type.matches_file(file):
                        total_target_files += 1
                        full_path = os.path.join(root, file)
                        all_files.append(full_path)
                        
                    # Update progress
                    if total_scanned % 100 == 0:
                        self.progress_signal.emit(total_scanned, total_files_in_folder)
                        self.status_signal.emit(f"Scanned {total_scanned} of {total_files_in_folder} files...")
                        self.logger.info("ImageDirectoryScanner", f"Scanned {total_scanned}/{total_files_in_folder}, found {total_target_files} matching files")
            
            # Done scanning
            self.progress_signal.emit(total_files_in_folder, total_files_in_folder)
            self.status_signal.emit(f"Scan complete. Adding all {len(all_files)} {self.file_type.display_name.lower()} at once")
            self.logger.info("ImageDirectoryScanner", f"Scan complete. Adding all {len(all_files)} {self.file_type.display_name.lower()} at once")
            
            # Add all files at once
            self.scan_files = all_files
            
            # Emit complete signal with found files
            if self.cancel_requested:
                self.complete_signal.emit(False, "Scanning cancelled", [])
            else:
                self.complete_signal.emit(True, f"Found {len(all_files)} {self.file_type.display_name.lower()}", all_files)
            
            # Close progress dialog
            progress_dialog.close()
            
        except Exception as e:
            self.logger.error("ImageDirectoryScanner", f"Error scanning directory: {str(e)}")
            self.complete_signal.emit(False, f"Error scanning directory: {str(e)}", [])
            
        finally:
            self.scanning_in_progress = False
            
    def _handle_cancel(self):
        """Handle cancellation of scanning"""
        if self.scanning_in_progress:
            self.cancel_requested = True
            self.logger.info("ImageDirectoryScanner", "Cancellation requested")
            return True
        return False
