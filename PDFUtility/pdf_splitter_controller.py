#!/usr/bin/env python3
# pdf_splitter_controller.py - PyQt version of SplitController.py

import os
import threading
import time
import gc
import traceback
import datetime
import tempfile
import shutil
import math
from enum import Enum
from multiprocessing import Process, Queue, Event, cpu_count

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QInputDialog

from PDFLogger import Logger
from settings_controller import SettingsController
from utility import Utility
from ProgressDialog import ProgressDialog, DualProgressDialog

# Import PyPDF2 for PDF processing
from PyPDF2 import PdfReader, PdfWriter

# Define split modes
class SplitMode(Enum):
    BY_PAGE_COUNT = 1    # Split into chunks with equal number of pages
    BY_RANGES = 2        # Split by specific page ranges
    EXTRACT_PAGES = 3    # Extract specific individual pages
    EVERY_N_PAGES = 4    # Extract every Nth page
    REMOVE_PAGES = 5     # Remove specific pages and keep the rest
    SPLIT_EVERY_PAGE = 6 # Split into individual pages

class PDFSplitterController(QObject):
    """Controller for splitting PDF files in PyQt"""
    
    # Define signals for progress reporting
    progress_signal = pyqtSignal(int, int)  # current, total
    status_signal = pyqtSignal(str)         # status message
    complete_signal = pyqtSignal(bool, str) # success, message
    file_progress_signal = pyqtSignal(int, int, str)  # current file, total files, filename
    batch_complete_signal = pyqtSignal(list)  # list of output files when a batch is complete
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = Logger()
        self.settings_controller = SettingsController()
        self.settings = self.settings_controller.load_settings()
        self.utility = Utility()
        self.parent = parent
        
        # Initialize state variables
        self.split_in_progress = False
        self.cancel_requested = False
        self.output_files = []
        self.temp_dir = None
        self.split_mode = SplitMode.BY_PAGE_COUNT
        self.current_pdf_file = None
        
        # Worker process management
        self.worker_processes = []
        self.result_queue = Queue()
        self.cancel_event = Event()
        
        # Batch processing state
        self.batch_processing = False
        self.batch_files = []
        self.batch_current_index = 0
        
        # Maximum number of pages to process at once (for memory management)
        self.max_pages_per_batch = 1000
        
    def split_pdf(self, pdf_file, output_directory=None, split_mode=SplitMode.BY_PAGE_COUNT, 
               split_params=None, prefix=""):
        """
        Split a PDF file according to the specified mode
        
        Args:
            pdf_file (str): Path to the PDF file to split
            output_directory (str, optional): Directory for output files
            split_mode (SplitMode): The mode to use for splitting
            split_params (dict): Parameters specific to the split mode:
                - BY_PAGE_COUNT: {'pages_per_file': int}
                - BY_RANGES: {'ranges': [(start1, end1), (start2, end2), ...]}
                - EXTRACT_PAGES: {'pages': [page1, page2, ...]}
                - EVERY_N_PAGES: {'n': int, 'start_at': int}
                - REMOVE_PAGES: {'pages': [page1, page2, ...]}
                - SPLIT_EVERY_PAGE: {} (no additional parameters needed)
            prefix (str): Prefix for output filenames
            
        Returns:
            list: Paths to the split PDF files (empty until process completes)
        """
        if not pdf_file or not os.path.exists(pdf_file):
            self.logger.warning("PDFSplitterController", f"Invalid PDF file: {pdf_file}")
            self.complete_signal.emit(False, f"Invalid PDF file: {os.path.basename(pdf_file) if pdf_file else 'None'}")
            return []
            
        if self.split_in_progress:
            self.logger.warning("PDFSplitterController", "Split operation already in progress")
            self.complete_signal.emit(False, "Split operation already in progress")
            return []
            
        # Set default parameters if not provided
        if split_params is None:
            if split_mode == SplitMode.BY_PAGE_COUNT:
                split_params = {'pages_per_file': 1}
            elif split_mode == SplitMode.EVERY_N_PAGES:
                split_params = {'n': 1, 'start_at': 0}
            else:
                split_params = {}
                
        # Initialize state for this operation
        self.split_in_progress = True
        self.cancel_requested = False
        self.cancel_event.clear()
        self.output_files = []
        self.split_mode = split_mode
        self.current_pdf_file = pdf_file
        
        # Generate default output directory if not provided
        if not output_directory:
            output_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "split_output")
        
        # Ensure output directory exists
        os.makedirs(output_directory, exist_ok=True)
        
        # Generate default prefix if not provided
        if not prefix:
            prefix = os.path.splitext(os.path.basename(pdf_file))[0]
        
        # Start the split process in a separate thread to keep UI responsive
        split_thread = threading.Thread(
            target=self._split_process,
            args=(pdf_file, output_directory, split_mode, split_params, prefix),
            daemon=True
        )
        split_thread.start()
        
        return []  # Empty list initially, will be filled as files are created
        
    def batch_split_pdfs(self, pdf_files, output_directory=None, split_mode=SplitMode.BY_PAGE_COUNT,
                         split_params=None):
        """
        Split multiple PDF files using the same settings
        
        Args:
            pdf_files (list): List of PDF file paths to split
            output_directory (str, optional): Directory for output files
            split_mode (SplitMode): The mode to use for splitting
            split_params (dict): Parameters specific to the split mode
            
        Returns:
            list: Paths to the split PDF files (empty until process completes)
        """
        if not pdf_files:
            self.logger.warning("PDFSplitterController", "No PDF files provided for splitting")
            self.complete_signal.emit(False, "No PDF files provided for splitting")
            return []
            
        if self.split_in_progress:
            self.logger.warning("PDFSplitterController", "Split operation already in progress")
            self.complete_signal.emit(False, "Split operation already in progress")
            return []
            
        # Set default parameters if not provided
        if split_params is None:
            if split_mode == SplitMode.BY_PAGE_COUNT:
                split_params = {'pages_per_file': 1}
            elif split_mode == SplitMode.EVERY_N_PAGES:
                split_params = {'n': 1, 'start_at': 0}
            else:
                split_params = {}
        
        # Initialize state for batch processing
        self.split_in_progress = True
        self.cancel_requested = False
        self.cancel_event.clear()
        self.output_files = []
        self.split_mode = split_mode
        self.batch_processing = True
        self.batch_files = pdf_files.copy()
        self.batch_current_index = 0
        
        # Generate default output directory if not provided
        if not output_directory:
            output_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "split_output")
        
        # Ensure output directory exists
        os.makedirs(output_directory, exist_ok=True)
        
        # Start the batch processing in a separate thread
        batch_thread = threading.Thread(
            target=self._process_batch,
            args=(output_directory, split_mode, split_params),
            daemon=True
        )
        batch_thread.start()
        
        return []  # Empty list initially, will be filled as files are created
        
    def _process_batch(self, output_directory, split_mode, split_params):
        """Process a batch of PDF files"""
        try:
            total_files = len(self.batch_files)
            self.logger.info("PDFSplitterController", f"Starting batch processing of {total_files} PDF files")
            self.status_signal.emit(f"Starting batch processing of {total_files} PDF files...")
            
            for i, pdf_file in enumerate(self.batch_files):
                if self.cancel_requested:
                    self.logger.info("PDFSplitterController", "Batch processing cancelled")
                    self.complete_signal.emit(False, "Batch processing cancelled")
                    self.split_in_progress = False
                    self.batch_processing = False
                    return
                
                self.batch_current_index = i
                self.current_pdf_file = pdf_file
                self.file_progress_signal.emit(i + 1, total_files, os.path.basename(pdf_file))
                self.status_signal.emit(f"Processing file {i + 1}/{total_files}: {os.path.basename(pdf_file)}")
                
                # Generate file-specific prefix
                prefix = os.path.splitext(os.path.basename(pdf_file))[0]
                
                # Process this file
                file_output_files = []
                try:
                    # Call the appropriate split method based on the mode
                    if split_mode == SplitMode.BY_PAGE_COUNT:
                        file_output_files = self._split_by_page_count(
                            pdf_file, output_directory, split_params['pages_per_file'], prefix
                        )
                    elif split_mode == SplitMode.BY_RANGES:
                        file_output_files = self._split_by_ranges(
                            pdf_file, output_directory, split_params.get('ranges', []), prefix
                        )
                    elif split_mode == SplitMode.EXTRACT_PAGES:
                        file_output_files = self._extract_pages(
                            pdf_file, output_directory, split_params.get('pages', []), prefix
                        )
                    elif split_mode == SplitMode.EVERY_N_PAGES:
                        file_output_files = self._extract_every_n_pages(
                            pdf_file, output_directory, 
                            split_params.get('n', 1), 
                            split_params.get('start_at', 0), 
                            prefix
                        )
                    elif split_mode == SplitMode.REMOVE_PAGES:
                        file_output_files = self._remove_pages(
                            pdf_file, output_directory, split_params.get('pages', []), prefix
                        )
                    elif split_mode == SplitMode.SPLIT_EVERY_PAGE:
                        file_output_files = self._split_every_page(
                            pdf_file, output_directory, prefix
                        )
                    
                    # Add the output files to the overall list
                    self.output_files.extend(file_output_files)
                    
                    # Signal that this file's processing is complete
                    self.batch_complete_signal.emit(file_output_files)
                    
                except Exception as e:
                    self.logger.error("PDFSplitterController", f"Error processing {pdf_file}: {str(e)}")
                    self.logger.error("PDFSplitterController", traceback.format_exc())
                    # Continue with next file despite errors
            
            # Batch processing complete
            self.status_signal.emit(f"Batch processing complete: processed {total_files} PDF files")
            self.complete_signal.emit(True, f"Successfully split {total_files} PDF files into {len(self.output_files)} output files")
            
        except Exception as e:
            self.logger.error("PDFSplitterController", f"Error in batch processing: {str(e)}")
            self.logger.error("PDFSplitterController", traceback.format_exc())
            self.complete_signal.emit(False, f"Error in batch processing: {str(e)}")
            
        finally:
            # Clean up
            self.split_in_progress = False
            self.batch_processing = False
            self._cleanup_temp_dir()
            gc.collect()
        
    def _split_process(self, pdf_file, output_directory, split_mode, split_params, prefix):
        """Internal method to handle the split process in a background thread"""
        try:
            self.logger.info("PDFSplitterController", f"Starting split of {pdf_file} with mode {split_mode}")
            self.status_signal.emit(f"Starting split of {os.path.basename(pdf_file)}...")
            
            # Create a temporary directory for intermediate files
            self.temp_dir = tempfile.mkdtemp(prefix="pdf_split_")
            
            # Call the appropriate split method based on the mode
            if split_mode == SplitMode.BY_PAGE_COUNT:
                output_files = self._split_by_page_count(
                    pdf_file, output_directory, split_params['pages_per_file'], prefix
                )
            elif split_mode == SplitMode.BY_RANGES:
                output_files = self._split_by_ranges(
                    pdf_file, output_directory, split_params.get('ranges', []), prefix
                )
            elif split_mode == SplitMode.EXTRACT_PAGES:
                output_files = self._extract_pages(
                    pdf_file, output_directory, split_params.get('pages', []), prefix
                )
            elif split_mode == SplitMode.EVERY_N_PAGES:
                output_files = self._extract_every_n_pages(
                    pdf_file, output_directory, 
                    split_params.get('n', 1), 
                    split_params.get('start_at', 0), 
                    prefix
                )
            elif split_mode == SplitMode.REMOVE_PAGES:
                output_files = self._remove_pages(
                    pdf_file, output_directory, split_params.get('pages', []), prefix
                )
            elif split_mode == SplitMode.SPLIT_EVERY_PAGE:
                output_files = self._split_every_page(
                    pdf_file, output_directory, prefix
                )
            
            # Final progress update
            self.status_signal.emit(f"Split complete: created {len(output_files)} files")
            
            self.logger.info("PDFSplitterController", f"Successfully split PDF into {len(output_files)} files")
            self.complete_signal.emit(True, f"Successfully split {os.path.basename(pdf_file)} into {len(output_files)} files")
                
        except Exception as e:
            self.logger.error("PDFSplitterController", f"Error in split process: {str(e)}")
            self.logger.error("PDFSplitterController", traceback.format_exc())
            self.complete_signal.emit(False, f"Error splitting PDF: {str(e)}")
            
        finally:
            # Clean up
            self.split_in_progress = False
            self._cleanup_temp_dir()
            gc.collect()
            
    def _split_by_page_count(self, pdf_file, output_directory, pages_per_file, prefix):
        """Split a PDF into chunks with a specified number of pages per chunk"""
        output_files = []
        
        try:
            # Open the input PDF to get total page count
            with open(pdf_file, 'rb') as f:
                reader = PdfReader(f)
                total_pages = len(reader.pages)
                
                if total_pages == 0:
                    self.logger.warning("PDFSplitterController", "PDF file has no pages")
                    return output_files
                    
                self.logger.info("PDFSplitterController", f"PDF has {total_pages} pages")
                self.status_signal.emit(f"Splitting PDF with {total_pages} pages...")
                
                # Calculate number of output files
                file_count = math.ceil(total_pages / pages_per_file)
                
                # For very large files, process in batches to manage memory
                if total_pages > self.max_pages_per_batch:
                    # Process in batches
                    batch_count = math.ceil(total_pages / self.max_pages_per_batch)
                    self.logger.info("PDFSplitterController", 
                                    f"Large PDF detected. Processing in {batch_count} batches")
                    
                    # Close the initial reader to free memory
                    reader = None
                    
                    # Process each batch
                    for batch in range(batch_count):
                        if self.cancel_requested:
                            self.logger.info("PDFSplitterController", "Split cancelled during batch processing")
                            return output_files
                        
                        batch_start = batch * self.max_pages_per_batch
                        batch_end = min((batch + 1) * self.max_pages_per_batch, total_pages)
                        self.logger.info("PDFSplitterController", 
                                        f"Processing batch {batch+1}/{batch_count}, pages {batch_start+1}-{batch_end}")
                        
                        # Reopen the PDF for each batch to avoid memory issues
                        with open(pdf_file, 'rb') as f:
                            reader = PdfReader(f)
                            
                            # Process this batch of pages
                            for i in range(batch_start, batch_end, pages_per_file):
                                if self.cancel_requested:
                                    return output_files
                                
                                # Calculate page range for this output file
                                start_page = i
                                end_page = min(i + pages_per_file, total_pages)
                                
                                # Create output file
                                output_path = self._create_file_from_pages(
                                    reader, start_page, end_page, 
                                    os.path.join(output_directory, f"{prefix}_part{i//pages_per_file+1:04d}.pdf"),
                                    total_pages
                                )
                                
                                if output_path:
                                    output_files.append(output_path)
                else:
                    # Standard processing for smaller files
                    for i in range(0, total_pages, pages_per_file):
                        if self.cancel_requested:
                            self.logger.info("PDFSplitterController", "Split cancelled")
                            return output_files
                        
                        # Calculate page range for this file
                        start_page = i
                        end_page = min(i + pages_per_file, total_pages)
                        
                        # Create output file
                        output_path = self._create_file_from_pages(
                            reader, start_page, end_page, 
                            os.path.join(output_directory, f"{prefix}_part{i//pages_per_file+1:04d}.pdf"),
                            total_pages
                        )
                        
                        if output_path:
                            output_files.append(output_path)
                
        except Exception as e:
            self.logger.error("PDFSplitterController", f"Error in split by page count: {str(e)}")
            self.logger.error("PDFSplitterController", traceback.format_exc())
            raise
            
        return output_files
        
    def _split_by_ranges(self, pdf_file, output_directory, ranges, prefix):
        """Split a PDF into multiple files based on page ranges"""
        output_files = []
        
        try:
            # Validate ranges format
            if not ranges:
                self.logger.warning("PDFSplitterController", "No page ranges specified")
                return output_files
                
            # Open the input PDF
            with open(pdf_file, 'rb') as f:
                reader = PdfReader(f)
                total_pages = len(reader.pages)
                
                if total_pages == 0:
                    self.logger.warning("PDFSplitterController", "PDF file has no pages")
                    return output_files
                    
                self.logger.info("PDFSplitterController", f"PDF has {total_pages} pages")
                self.status_signal.emit(f"Splitting PDF with {total_pages} pages by ranges...")
                
                # Process each range
                for i, (start, end) in enumerate(ranges):
                    if self.cancel_requested:
                        self.logger.info("PDFSplitterController", "Split cancelled")
                        return output_files
                    
                    # Convert to 0-indexed and validate range
                    start_page = max(0, start - 1)  # Convert from 1-indexed to 0-indexed
                    end_page = min(total_pages, end)  # end is already the correct page number
                    
                    if start_page >= total_pages or end_page <= start_page:
                        self.logger.warning("PDFSplitterController", 
                                           f"Invalid range: {start}-{end} for PDF with {total_pages} pages")
                        continue
                    
                    # Create output file
                    output_path = self._create_file_from_pages(
                        reader, start_page, end_page, 
                        os.path.join(output_directory, f"{prefix}_pages{start:04d}-{end:04d}.pdf"),
                        total_pages
                    )
                    
                    if output_path:
                        output_files.append(output_path)
                
        except Exception as e:
            self.logger.error("PDFSplitterController", f"Error in split by ranges: {str(e)}")
            self.logger.error("PDFSplitterController", traceback.format_exc())
            raise
            
        return output_files
        
    def _extract_pages(self, pdf_file, output_directory, pages, prefix):
        """Extract specific pages from a PDF"""
        output_files = []
        
        try:
            # Validate pages format
            if not pages:
                self.logger.warning("PDFSplitterController", "No pages specified for extraction")
                return output_files
                
            # Open the input PDF
            with open(pdf_file, 'rb') as f:
                reader = PdfReader(f)
                total_pages = len(reader.pages)
                
                if total_pages == 0:
                    self.logger.warning("PDFSplitterController", "PDF file has no pages")
                    return output_files
                    
                self.logger.info("PDFSplitterController", f"PDF has {total_pages} pages")
                self.status_signal.emit(f"Extracting {len(pages)} pages from PDF...")
                
                # Create a single output file with all the specified pages
                writer = PdfWriter()
                extracted_count = 0
                page_numbers = []
                
                # Process each page
                for i, page_num in enumerate(sorted(pages)):
                    if self.cancel_requested:
                        self.logger.info("PDFSplitterController", "Extraction cancelled")
                        return output_files
                    
                    # Convert to 0-indexed and validate
                    page_idx = page_num - 1  # Convert from 1-indexed to 0-indexed
                    
                    if 0 <= page_idx < total_pages:
                        writer.add_page(reader.pages[page_idx])
                        extracted_count += 1
                        page_numbers.append(page_num)
                        
                        # Update progress
                        self.progress_signal.emit(i + 1, len(pages))
                        if (i + 1) % 10 == 0:
                            self.status_signal.emit(f"Extracted {i + 1}/{len(pages)} pages")
                    else:
                        self.logger.warning("PDFSplitterController", 
                                           f"Invalid page number: {page_num} for PDF with {total_pages} pages")
                
                # Write the output file if we extracted any pages
                if extracted_count > 0:
                    page_str = "_".join([str(p) for p in page_numbers[:5]])
                    if len(page_numbers) > 5:
                        page_str += f"_and_{len(page_numbers)-5}_more"
                        
                    output_path = os.path.join(output_directory, f"{prefix}_extracted_pages_{page_str}.pdf")
                    
                    with open(output_path, 'wb') as output_file:
                        writer.write(output_file)
                    
                    output_files.append(output_path)
                    self.logger.info("PDFSplitterController", f"Created {output_path} with {extracted_count} pages")
                
        except Exception as e:
            self.logger.error("PDFSplitterController", f"Error in extract pages: {str(e)}")
            self.logger.error("PDFSplitterController", traceback.format_exc())
            raise
            
        return output_files
        
    def _extract_every_n_pages(self, pdf_file, output_directory, n, start_at, prefix):
        """Extract every Nth page from a PDF"""
        output_files = []
        
        try:
            if n <= 0:
                self.logger.warning("PDFSplitterController", "Invalid N value for extracting every N pages")
                return output_files
                
            # Open the input PDF
            with open(pdf_file, 'rb') as f:
                reader = PdfReader(f)
                total_pages = len(reader.pages)
                
                if total_pages == 0:
                    self.logger.warning("PDFSplitterController", "PDF file has no pages")
                    return output_files
                    
                self.logger.info("PDFSplitterController", f"PDF has {total_pages} pages")
                self.status_signal.emit(f"Extracting every {n}th page from PDF...")
                
                # Calculate which pages to extract
                pages_to_extract = []
                for i in range(start_at, total_pages, n):
                    pages_to_extract.append(i)
                
                # Create output file
                writer = PdfWriter()
                extracted_count = 0
                
                # Add pages to the output
                for i, page_idx in enumerate(pages_to_extract):
                    if self.cancel_requested:
                        self.logger.info("PDFSplitterController", "Extraction cancelled")
                        return output_files
                    
                    writer.add_page(reader.pages[page_idx])
                    extracted_count += 1
                    
                    # Update progress
                    self.progress_signal.emit(i + 1, len(pages_to_extract))
                    if (i + 1) % 10 == 0:
                        self.status_signal.emit(f"Extracted {i + 1}/{len(pages_to_extract)} pages")
                
                # Write the output file if we extracted any pages
                if extracted_count > 0:
                    output_path = os.path.join(output_directory, f"{prefix}_every_{n}th_page.pdf")
                    
                    with open(output_path, 'wb') as output_file:
                        writer.write(output_file)
                    
                    output_files.append(output_path)
                    self.logger.info("PDFSplitterController", f"Created {output_path} with {extracted_count} pages")
                
        except Exception as e:
            self.logger.error("PDFSplitterController", f"Error in extract every N pages: {str(e)}")
            self.logger.error("PDFSplitterController", traceback.format_exc())
            raise
            
        return output_files
        
    def _remove_pages(self, pdf_file, output_directory, pages, prefix):
        """Remove specific pages from a PDF and save the result"""
        output_files = []
        
        try:
            # Open the input PDF
            with open(pdf_file, 'rb') as f:
                reader = PdfReader(f)
                total_pages = len(reader.pages)
                
                if total_pages == 0:
                    self.logger.warning("PDFSplitterController", "PDF file has no pages")
                    return output_files
                    
                self.logger.info("PDFSplitterController", f"PDF has {total_pages} pages")
                self.status_signal.emit(f"Removing {len(pages)} pages from PDF...")
                
                # Convert page numbers to 0-indexed
                pages_to_remove = set([p - 1 for p in pages if 0 < p <= total_pages])
                
                # Create output file
                writer = PdfWriter()
                kept_count = 0
                
                # Add all pages except the ones to remove
                for i in range(total_pages):
                    if self.cancel_requested:
                        self.logger.info("PDFSplitterController", "Operation cancelled")
                        return output_files
                    
                    if i not in pages_to_remove:
                        writer.add_page(reader.pages[i])
                        kept_count += 1
                    
                    # Update progress
                    self.progress_signal.emit(i + 1, total_pages)
                    if (i + 1) % 10 == 0:
                        self.status_signal.emit(f"Processed {i + 1}/{total_pages} pages")
                
                # Write the output file if we kept any pages
                if kept_count > 0:
                    output_path = os.path.join(output_directory, f"{prefix}_with_pages_removed.pdf")
                    
                    with open(output_path, 'wb') as output_file:
                        writer.write(output_file)
                    
                    output_files.append(output_path)
                    self.logger.info("PDFSplitterController", f"Created {output_path} with {kept_count} pages")
                
        except Exception as e:
            self.logger.error("PDFSplitterController", f"Error in remove pages: {str(e)}")
            self.logger.error("PDFSplitterController", traceback.format_exc())
            raise
            
        return output_files
        
    def _split_every_page(self, pdf_file, output_directory, prefix):
        """Split a PDF into individual pages"""
        return self._split_by_page_count(pdf_file, output_directory, 1, prefix)
        
    def _create_file_from_pages(self, reader, start_page, end_page, output_path, total_pages):
        """Helper method to create a PDF file from a range of pages"""
        try:
            # Create a new writer
            writer = PdfWriter()
            
            # Add the pages to the writer
            for j in range(start_page, end_page):
                if self.cancel_requested:
                    self.logger.info("PDFSplitterController", "Operation cancelled while adding pages")
                    return None
                
                writer.add_page(reader.pages[j])
                
                # Update progress periodically
                self.progress_signal.emit(j + 1, total_pages)
                if (j + 1) % 10 == 0:
                    self.status_signal.emit(f"Processing page {j + 1}/{total_pages}")
            
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Write the output file
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
            
            self.logger.info("PDFSplitterController", f"Created {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error("PDFSplitterController", f"Error creating file from pages: {str(e)}")
            return None
            
    def get_pdf_page_count(self, pdf_file):
        """
        Get the total number of pages in a PDF file
        
        Args:
            pdf_file (str): Path to the PDF file
            
        Returns:
            int: Number of pages, or 0 if the file is invalid/doesn't exist
        """
        if not pdf_file or not os.path.exists(pdf_file):
            self.logger.warning("PDFSplitterController", f"PDF file does not exist: {pdf_file}")
            return 0
            
        try:
            with open(pdf_file, 'rb') as f:
                reader = PdfReader(f)
                page_count = len(reader.pages)
                self.logger.info("PDFSplitterController", f"PDF {os.path.basename(pdf_file)} has {page_count} pages")
                return page_count
        except Exception as e:
            self.logger.error("PDFSplitterController", f"Error getting page count for {pdf_file}: {str(e)}")
            return 0
            
    def is_valid_page_range(self, start_page, end_page, total_pages):
        """
        Check if a page range is valid
        
        Args:
            start_page (int): Starting page (1-indexed)
            end_page (int): Ending page (1-indexed)
            total_pages (int): Total pages in the PDF
            
        Returns:
            bool: True if range is valid, False otherwise
        """
        if start_page < 1 or end_page > total_pages or start_page > end_page:
            return False
        return True
        
    def is_valid_pdf(self, pdf_file):
        """
        Check if a file is a valid PDF with robust error handling
        
        Args:
            pdf_file (str): Path to the PDF file
            
        Returns:
            bool: True if file is a valid PDF, False otherwise
        """
        if not pdf_file or not os.path.exists(pdf_file):
            return False
            
        if not pdf_file.lower().endswith('.pdf'):
            return False
            
        try:
            # Check file size first - avoid tiny or huge files that might be corrupted
            file_size = os.path.getsize(pdf_file)
            if file_size < 100:  # Too small to be a valid PDF
                self.logger.warning("PDFSplitterController", f"PDF file too small: {pdf_file} ({file_size} bytes)")
                return False
            if file_size > 500 * 1024 * 1024:  # > 500MB might cause memory issues
                self.logger.warning("PDFSplitterController", f"PDF file very large: {pdf_file} ({file_size} bytes)")
                # Still allow large files but log warning
            
            # Quick header check - valid PDF should start with %PDF-
            with open(pdf_file, 'rb') as f:
                header = f.read(8)
                if not header.startswith(b'%PDF-'):
                    self.logger.warning("PDFSplitterController", f"Invalid PDF header: {pdf_file}")
                    return False
            
            # Try to read with PyPDF2 with strict error handling
            with open(pdf_file, 'rb') as f:
                try:
                    reader = PdfReader(f, strict=False)  # Use non-strict mode for corrupted PDFs
                    # Try to access the number of pages to verify it's readable
                    page_count = len(reader.pages)
                    
                    # Additional validation - check if we can access at least the first page
                    if page_count > 0:
                        first_page = reader.pages[0]
                        # Try to access page content (this might catch more corruption issues)
                        try:
                            page_content = first_page.extract_text()
                        except:
                            # Page content extraction failed, but PDF structure seems OK
                            pass
                    
                    return True
                    
                except Exception as pdf_error:
                    # Handle specific PyPDF2 errors more gracefully
                    error_msg = str(pdf_error).lower()
                    
                    if 'startxref' in error_msg:
                        self.logger.warning("PDFSplitterController", f"PDF has startxref issues (corrupted): {pdf_file}")
                    elif 'xref' in error_msg:
                        self.logger.warning("PDFSplitterController", f"PDF has xref table issues: {pdf_file}")
                    elif 'eof' in error_msg or 'end of file' in error_msg:
                        self.logger.warning("PDFSplitterController", f"PDF appears truncated: {pdf_file}")
                    elif 'decrypt' in error_msg or 'password' in error_msg:
                        self.logger.warning("PDFSplitterController", f"PDF is password protected: {pdf_file}")
                    else:
                        self.logger.warning("PDFSplitterController", f"PDF validation failed: {pdf_file} - {str(pdf_error)}")
                    
                    return False
                    
        except PermissionError:
            self.logger.error("PDFSplitterController", f"Permission denied accessing PDF: {pdf_file}")
            return False
        except FileNotFoundError:
            self.logger.error("PDFSplitterController", f"PDF file not found: {pdf_file}")
            return False
        except Exception as e:
            self.logger.error("PDFSplitterController", f"Unexpected error validating PDF: {pdf_file} - {str(e)}")
            return False
            
    def validate_pdfs(self, pdf_files):
        """
        Validate a list of PDF files and return only the valid ones
        
        Args:
            pdf_files (list): List of PDF file paths
            
        Returns:
            list: List of valid PDF file paths
        """
        valid_files = []
        invalid_files = []
        
        for pdf_file in pdf_files:
            if self.is_valid_pdf(pdf_file):
                valid_files.append(pdf_file)
            else:
                invalid_files.append(pdf_file)
                
        if invalid_files:
            self.logger.warning("PDFSplitterController", f"Found {len(invalid_files)} invalid PDF files")
            
        return valid_files
    
    def cancel_split(self):
        """Cancel the current split operation"""
        if self.split_in_progress:
            self.logger.info("PDFSplitterController", "Cancel requested for split operation")
            self.cancel_requested = True
            self.cancel_event.set()  # Signal worker processes to stop
            self.status_signal.emit("Cancelling split operation...")
            return True
        return False
        
    def get_output_files(self):
        """Get the list of output files from the most recent split operation"""
        return self.output_files
        
    def get_current_file(self):
        """Get the path to the currently processing PDF file"""
        return self.current_pdf_file
        
    def get_batch_progress(self):
        """Get the current batch processing progress"""
        if not self.batch_processing:
            return (0, 0)
        return (self.batch_current_index + 1, len(self.batch_files))
        
    def is_processing(self):
        """Check if a split operation is in progress"""
        return self.split_in_progress
        
    def _cleanup_temp_dir(self):
        """Clean up the temporary directory created during splitting"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                self.temp_dir = None
            except Exception as e:
                self.logger.error("PDFSplitterController", f"Error cleaning up temp dir: {str(e)}")
                
    def get_available_split_modes(self):
        """Get a list of available split modes with descriptions"""
        return [
            (SplitMode.BY_PAGE_COUNT, "Split into chunks with equal number of pages"),
            (SplitMode.BY_RANGES, "Split by specific page ranges"),
            (SplitMode.EXTRACT_PAGES, "Extract specific individual pages"),
            (SplitMode.EVERY_N_PAGES, "Extract every Nth page"),
            (SplitMode.REMOVE_PAGES, "Remove specific pages and keep the rest"),
            (SplitMode.SPLIT_EVERY_PAGE, "Split into individual pages")
        ]
        
    @pyqtSlot()
    def handle_task_complete(self):
        """Handle task completion signal from worker processes"""
        while not self.result_queue.empty():
            result = self.result_queue.get()
            if result['status'] == 'completed':
                self.logger.info("PDFSplitterController", f"Task {result['id']} completed successfully")
                if 'output_file' in result:
                    self.output_files.append(result['output_file'])
            elif result['status'] == 'error':
                self.logger.error("PDFSplitterController", f"Task {result['id']} failed: {result['message']}")
            elif result['status'] == 'cancelled':
                self.logger.info("PDFSplitterController", f"Task {result['id']} was cancelled: {result['message']}")
                
    def _cleanup_worker_processes(self):
        """Clean up any worker processes"""
        if self.worker_processes:
            for process in self.worker_processes:
                if process.is_alive():
                    process.terminate()
            self.worker_processes = []
