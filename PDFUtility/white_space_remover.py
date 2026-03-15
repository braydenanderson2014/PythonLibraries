#!/usr/bin/env python3
# white_space_remover.py - PyQt version of White.py for PDF Utility

import os
import fitz  # PyMuPDF
from PyQt6.QtCore import QThread, pyqtSignal
from PDFLogger import Logger
from settings_controller import SettingsController

class BlankPageInfo:
    """Class to represent a file and its blank pages."""
    def __init__(self, file_path, blank_pages):
        self.file_path = file_path
        self.blank_pages = blank_pages

    def get_file_path(self):
        return self.file_path
    
    def get_blank_pages(self):
        return self.blank_pages

    def __repr__(self):
        return f"BlankPageInfo(file_path={self.file_path}, blank_pages={self.blank_pages})"

class WhiteSpaceScannerThread(QThread):
    """Thread for scanning PDFs for white space"""
    
    # Signals
    progress_file = pyqtSignal(int, int)  # current file, total files
    progress_page = pyqtSignal(int, int)  # current page, total pages
    status_update = pyqtSignal(str)       # status message
    scan_complete = pyqtSignal(list)      # list of BlankPageInfo objects
    
    def __init__(self, file_paths, threshold):
        super().__init__()
        self.file_paths = file_paths
        self.threshold = threshold
        self.cancelled = False
        self.logger = Logger()
    
    def run(self):
        """Run the scanner thread"""
        self.logger.info("WhiteSpaceScanner", "Scanning PDF files for whitespace")
        
        blank_page_info_list = []
        total_files = len(self.file_paths)
        
        for file_idx, file_path in enumerate(self.file_paths):
            if self.cancelled:
                break
                
            self.progress_file.emit(file_idx + 1, total_files)
            self.status_update.emit(f"Scanning {os.path.basename(file_path)}")
            
            try:
                pdf_document = fitz.open(file_path)
                num_pages = pdf_document.page_count
                
                blank_pages = []
                for page_idx in range(num_pages):
                    if self.cancelled:
                        break
                        
                    self.progress_page.emit(page_idx + 1, num_pages)
                    
                    # Detect blank pages
                    page = pdf_document[page_idx]
                    if self._is_page_blank(page):
                        blank_pages.append(page_idx + 1)  # Page numbers are 1-based
                
                blank_page_info_list.append(BlankPageInfo(file_path, blank_pages))
                
            except Exception as e:
                self.logger.error("WhiteSpaceScanner", f"Error scanning {file_path}: {str(e)}")
        
        self.scan_complete.emit(blank_page_info_list)
    
    def _is_page_blank(self, page: fitz.Page) -> bool:
        """
        Heuristic blank-page detector.
        
        • Renders the page at 1/4 size (fast).  
        • Counts how many pixels are ≈ white (all channels ≥ 245).  
        • If white-pixel ratio ≥ self.threshold  → page is considered blank.
          ─ e.g. threshold 0.90 ≈ "90 % of the page is white".
        """
        try:
            # low-dpi render for speed  (about 18 dpi)
            pix = page.get_pixmap(matrix=fitz.Matrix(0.25, 0.25),
                                  colorspace=fitz.csRGB, alpha=False)
            data = pix.samples             # bytes -- 3 × pixels
            
            white_bytes = 0
            # count triplets where r,g,b are all > 245
            for i in range(0, len(data), 3):
                if data[i]   >= 245 and \
                   data[i+1] >= 245 and \
                   data[i+2] >= 245:
                    white_bytes += 3
                    
            white_ratio = white_bytes / len(data)   # we already multiplied by 3 above
            
            return white_ratio >= self.threshold
        except Exception as e:
            self.logger.error("WhiteSpaceScanner", f"Blank-page check failed: {e}")
            # On error treat page as *not* blank so we don't delete content
            return False
    
    def cancel(self):
        """Cancel the scanning process"""
        self.cancelled = True

class WhiteSpaceRemoverThread(QThread):
    """Thread for removing white pages from PDFs"""
    
    # Signals
    progress_file = pyqtSignal(int, int)  # current file, total files
    progress_page = pyqtSignal(int, int)  # current page, total pages
    status_update = pyqtSignal(str)       # status message
    file_completed = pyqtSignal(str)      # path to new file
    removal_complete = pyqtSignal()       # removal process complete
    
    def __init__(self, blank_page_info_list, output_dir=None, file_added_callback=None):
        super().__init__()
        self.blank_page_info_list = blank_page_info_list
        self.output_dir = output_dir
        self.file_added_callback = file_added_callback
        self.cancelled = False
        self.logger = Logger()
        self.new_files = []
    
    def run(self):
        """Run the remover thread"""
        self.logger.info("WhiteSpaceRemover", "Removing blank pages from PDFs")
        
        total_files = len(self.blank_page_info_list)
        
        for file_idx, blank_info in enumerate(self.blank_page_info_list):
            if self.cancelled:
                break
                
            file_path = blank_info.get_file_path()
            blank_pages = blank_info.get_blank_pages()
            
            if not blank_pages:  # Skip if no blank pages
                continue
                
            self.progress_file.emit(file_idx + 1, total_files)
            self.status_update.emit(f"Processing {os.path.basename(file_path)}")
            
            try:
                pdf_document = fitz.open(file_path)
                
                # Determine output path
                if self.output_dir:
                    base_name = os.path.basename(file_path)
                    name, ext = os.path.splitext(base_name)
                    output_pdf_path = os.path.join(self.output_dir, f"{name}_no_white{ext}")
                else:
                    output_pdf_path = os.path.splitext(file_path)[0] + "_no_white.pdf"
                
                # Create new PDF without blank pages
                new_pdf = fitz.open()
                total_pages = pdf_document.page_count
                
                for i in range(total_pages):
                    if self.cancelled:
                        break
                    
                    self.progress_page.emit(i + 1, total_pages)
                    
                    # Only copy non-blank pages
                    if (i + 1) not in blank_pages:
                        new_pdf.insert_pdf(pdf_document, from_page=i, to_page=i)
                
                # Save the new PDF
                os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)
                new_pdf.save(output_pdf_path)
                new_pdf.close()
                pdf_document.close()
                
                self.logger.info("WhiteSpaceRemover", f"Saved cleaned PDF to {output_pdf_path}")
                
                # Add to list of new files
                self.new_files.append(output_pdf_path)
                
                # Call the callback if provided
                if self.file_added_callback:
                    self.file_added_callback(output_pdf_path)
                
                # Emit signal with new file path
                self.file_completed.emit(output_pdf_path)
                
            except Exception as e:
                self.logger.error("WhiteSpaceRemover", f"Error processing {file_path}: {str(e)}")
        
        self.removal_complete.emit()
    
    def cancel(self):
        """Cancel the removal process"""
        self.cancelled = True
    
    def get_new_files(self):
        """Get the list of newly created files"""
        return self.new_files

class WhiteSpaceRemover:
    """Controller for white space detection and removal in PDF files"""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.logger = Logger()
        self.settings_controller = SettingsController()
        
        # Load settings
        self.settings = self.settings_controller.load_settings()
        self.threshold = self.settings.get("pdf", {}).get("white_threshold", 0.5)
        
        # Progress dialog references
        self.scanning_progress = None
        self.removing_progress = None
        
        # Thread references
        self.scanner_thread = None
        self.remover_thread = None
        
        # Track results
        self.blank_page_info_list = []
        self.new_files = []
        
        # Callback for file additions
        self.file_added_callback = None
        
        self.logger.info("WhiteSpaceRemover", "=========================================================")
        self.logger.info("WhiteSpaceRemover", "Initializing White Space Remover")
        self.logger.info("WhiteSpaceRemover", "=========================================================")
    
    def scan_for_white_space(self, file_paths, threshold):
        """
        Scan the selected PDF files for whitespace
        
        Args:
            file_paths (list): List of PDF file paths to scan
            threshold (float): Threshold for blank page detection
        
        Returns:
            list: List of BlankPageInfo objects
        """
        self.logger.info("WhiteSpaceRemover", "Starting white space scan")
        
        # Create and configure scanner thread
        self.scanner_thread = WhiteSpaceScannerThread(file_paths, threshold)
        
        # Start the scanner thread
        self.scanner_thread.start()
        
        return []
    
    def remove_white_pages(self, blank_page_info_list, output_dir=None):
        """Remove white pages from PDFs based on scan results"""
        self.logger.info("WhiteSpaceRemover", "Starting removal of white pages")
        
        # Create and configure remover thread
        self.remover_thread = WhiteSpaceRemoverThread(blank_page_info_list, output_dir, self.file_added_callback)
        
        # Start the remover thread
        self.remover_thread.start()
    
    def set_file_added_callback(self, callback):
        """Set callback function to be called when a new file is created
        
        Args:
            callback: Function that takes a file path as parameter
        """
        self.file_added_callback = callback
        self.logger.info("WhiteSpaceRemover", "File added callback set")
    
    def get_new_files(self):
        """Get list of newly created files"""
        return self.new_files
