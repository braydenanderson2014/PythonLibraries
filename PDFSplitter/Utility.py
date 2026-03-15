from ProgressDialog import DualProgressDialog
import fitz
from SettingsController import SettingsController
from PDFUtility.PDFLogger import Logger
import os
import sys
import platform

class Utility:
    def __init__(self, root):
        self.selection = []
        self.root = root
        self.settings = SettingsController(self.root)
        self.Logger = Logger()
        self.Logger.info("Utility", "==========================================================")
        self.Logger.info("Utility", " EVENT: INIT")
        self.Logger.info("Utility", "==========================================================")
        self.total_pages = 0
        self.total_files = 0
        self.files_scanned = 0
        self.pages_scanned = 0
        self.pdf_files = []

    def get_root(self):
        return self.root

    def get_system_info(self):
        """Get system information."""
        return {
            "System": platform.system(),
            "Release": platform.release(),
            "Version": platform.version(),
            "Architecture": platform.architecture(),
            "Machine": platform.machine(),
            "Processor": platform.processor(),
            "Python": platform.python_version(),
        }

    def count_pages(self, display_progress=True):
        """
        Count the total number of pages in the selected PDF files.

        Args:
            display_progress (bool): Whether to display a progress dialog.

        Returns:
            int: The total number of pages across all selected files.
        """
        if not self.selection:
            return 0

        self.logger.info("SplitController", f"Counting pages in {len(self.selection)} files")

        # Initialize progress tracking
        self.files_scanned = 0
        self.pages_scanned = 0
        self.total_files = len(self.selection)
        self.total_pages = 0

        # Create progress dialog if needed
        progress = DualProgressDialog(self.root, "Counting Pages") if display_progress else None

        for file_idx, file_path in enumerate(self.selection):
            if progress:
                if progress.is_cancelled():
                    break
                progress.update_overall_progress(file_idx, self.total_files)
                progress.update_overall_status(f"Scanning file {file_idx + 1} of {self.total_files}")
                progress.update_message(f"Scanning {file_path}")

            try:
                # Open the PDF file
                doc = fitz.open(file_path)
                num_pages = doc.page_count
                self.pages_scanned += num_pages
                self.files_scanned += 1
                self.total_pages += num_pages
                doc.close()

                if progress:
                    progress.update_current_progress(num_pages, num_pages)  # File-level progress is complete
                    progress.update_current_status(f"File {file_idx + 1} scanned successfully")

            except Exception as e:
                self.logger.error("SplitController", f"Error counting pages in {file_path}: {str(e)}")
                continue

            finally:
                if progress:
                    progress.reset_current_progress()

        if progress:
            progress.close()

        self.logger.info("SplitController", f"Total pages counted: {self.total_pages}")
        return self.total_pages

    def count_files(self):
        if not self.selection:
            return 0
        self.logger.info("SplitController", f"Counting files in {len(self.selection)} files")
        self.total_files = len(self.selection)
        return self.total_files

    def get_total_pages(self):
        return self.total_pages
    
    def get_total_files(self):
        return self.total_files
    
    def get_files_scanned(self):
        return self.files_scanned

    def get_pages_scanned(self):
        return self.pages_scanned
    
    def set_selection(self, selection):
        self.selection = selection
        self.logger.info("Utility", f"Selection set to {len(selection)} files")

    def get_selection(self):
        return self.selection
    
    def get_pdf_files(self):
        return self.pdf_files

    def set_pdf_files(self, pdf_files):
        self.pdf_files = pdf_files

    def format_time_remaining(self,seconds):
        """Format seconds into a human-readable time remaining string"""
        self.Logger.info("Utility","Formatting time remaining")
        if seconds < 60:
            return f"{int(seconds)} seconds"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            seconds_remainder = int(seconds % 60)
            if seconds_remainder > 0:
                return f"{minutes} min {seconds_remainder} sec"
            return f"{minutes} min"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            if minutes > 0:
                return f"{hours} hr {minutes} min"
            else:
                return f"{hours} hr"