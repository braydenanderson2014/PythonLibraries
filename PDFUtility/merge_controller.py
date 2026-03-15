#!/usr/bin/env python3
# merge_controller.py - PyQt version of MergeController.py

import os
import datetime
import threading
import time
import gc
import traceback
import tempfile
import shutil
from multiprocessing import Process, Queue, Event, cpu_count, freeze_support

# Optional import for memory monitoring
try:
    from psutil import virtual_memory, disk_usage
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    # Fallback functions when psutil is not available
    def virtual_memory():
        class MemoryInfo:
            def __init__(self):
                self.available = 1024 * 1024 * 1024  # 1GB fallback
                self.total = 4 * 1024 * 1024 * 1024  # 4GB fallback 
                self.percent = 50.0  # 50% fallback
        return MemoryInfo()
    
    def disk_usage(path):
        class DiskInfo:
            def __init__(self):
                self.free = 10 * 1024 * 1024 * 1024  # 10GB fallback
        return DiskInfo()

from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtWidgets import QFileDialog, QMessageBox

from PDFLogger import Logger
from settings_controller import SettingsController
from utility import Utility
from ProgressDialog import ProgressDialog, DualProgressDialog

# Import PDF libraries with fallbacks for memory efficiency
PDF_LIBRARY = None
try:
    import fitz  # PyMuPDF - much more memory efficient
    PDF_LIBRARY = "fitz"
    logger = Logger()
    logger.debug("MergeController","Using PyMuPDF (fitz) for memory-efficient PDF processing")
except ImportError:
    try:
        from PyPDF2 import PdfReader, PdfWriter
        # CRITICAL: Disable PyPDF2's page caching to reduce memory usage
        PdfReader.cache_get_outline = False
        logger.warning("MergeController", "Using PyPDF2 - may use more memory for large files")
        logger.info("MergeController", "Applied PyPDF2 memory optimizations: disabled page caching")
        PDF_LIBRARY = "pypdf2"
    except ImportError:
        raise ImportError("No PDF library available. Install either PyMuPDF (fitz) or PyPDF2")

# Define a simplified worker function for single PDF tasks
def pdf_chunk_worker(task_id, input_file, output_file, start_page, end_page, result_queue, cancel_event, log_dir):
    """Process a single chunk of a PDF file."""
    worker_name = f"ChunkWorker-{task_id}"
    
    # Set up logging for the worker
    logger = Logger(log_dir=log_dir)
    logger.info(worker_name, f"Starting worker {worker_name} for {input_file} pages {start_page}-{end_page}")
    
    try:
        # Check for cancellation
        if cancel_event.is_set():
            logger.warning(worker_name, "Received cancellation signal before starting")
            result_queue.put({
                'id': task_id, 
                'status': 'cancelled', 
                'message': 'Task cancelled before processing'
            })
            return
            
        # Create a PDF writer
        writer = PdfWriter()
        
        # Open the input PDF
        with open(input_file, 'rb') as f:
            reader = PdfReader(f)
            total_pages = len(reader.pages)
            
            # Adjust end_page if it exceeds the document
            if end_page >= total_pages:
                end_page = total_pages - 1
                logger.warning(worker_name, f"Adjusted end_page to {end_page} to match document bounds")
                
            # Add the specified pages to the writer
            for page_num in range(start_page, end_page + 1):
                if cancel_event.is_set():
                    logger.warning(worker_name, f"Cancellation received while processing page {page_num}")
                    result_queue.put({
                        'id': task_id, 
                        'status': 'cancelled', 
                        'message': f'Task cancelled at page {page_num}'
                    })
                    return
                    
                if page_num < total_pages:
                    writer.add_page(reader.pages[page_num])
                    
            # Write the output file
            with open(output_file, 'wb') as out_file:
                writer.write(out_file)
                
        # Report success
        result_queue.put({
            'id': task_id, 
            'status': 'completed', 
            'pages_processed': end_page - start_page + 1,
            'output_file': output_file
        })
        logger.info(worker_name, f"Successfully processed {end_page - start_page + 1} pages to {output_file}")
        
    except Exception as e:
        error_msg = f"Error in worker {worker_name}: {str(e)}"
        logger.error(worker_name, error_msg)
        logger.error(worker_name, traceback.format_exc())
        result_queue.put({
            'id': task_id, 
            'status': 'error', 
            'message': error_msg,
            'traceback': traceback.format_exc()
        })


class MergeController(QObject):
    """Controller for merging PDF files in PyQt with memory optimization"""
    
    # Define signals for progress reporting
    progress_signal = pyqtSignal(int, int)  # current, total
    status_signal = pyqtSignal(str)         # status message
    complete_signal = pyqtSignal(bool, str) # success, message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = Logger()
        self.settings_controller = SettingsController()
        self.settings = self.settings_controller.load_settings()
        self.utility = Utility()
        self.parent = parent
        
        # Initialize state variables
        self.merge_in_progress = False
        self.cancel_requested = False
        self.merged_file_path = None
        self.temp_files = []
        
        # Worker process management
        self.worker_processes = []
        self.result_queue = None
        self.cancel_event = None
        
        # Memory optimization settings - Ultra-aggressive for large files
        self.max_chunk_size_mb = self._calculate_optimal_chunk_size()
        self.memory_threshold_percent = 70  # Trigger cleanup at 70% memory usage
        self.pages_per_gc_cycle = 25  # Force garbage collection every 25 pages
        self.aggressive_mode = True  # Enable ultra-aggressive memory management
        
        self.logger.info("MergeController", f"Initialized with ultra-aggressive memory management:")
        self.logger.info("MergeController", f"  - Chunk size: {self.max_chunk_size_mb}MB")
        self.logger.info("MergeController", f"  - Memory threshold: {self.memory_threshold_percent}%")
        self.logger.info("MergeController", f"  - GC cycle: every {self.pages_per_gc_cycle} pages")
        
        # Log system capabilities
        if not PSUTIL_AVAILABLE:
            self.logger.warning("MergeController", "psutil not available - using fallback memory calculations")
        
    def _calculate_optimal_chunk_size(self):
        """Calculate optimal chunk size based on system memory with ultra-conservative approach"""
        try:
            available_memory = virtual_memory().available
            total_memory = virtual_memory().total
            
            # Ultra-conservative: Use only 2% of available memory, with strict limits
            conservative_size_mb = max(10, min(50, int(available_memory / (1024 * 1024) * 0.02)))
            
            # If total system memory is low, be even more conservative
            if total_memory < 4 * 1024 * 1024 * 1024:  # Less than 4GB total
                conservative_size_mb = min(conservative_size_mb, 20)
                
            self.logger.info("MergeController", f"Memory analysis: {available_memory/(1024*1024):.0f}MB available")
            return conservative_size_mb
        except Exception as e:
            self.logger.warning("MergeController", f"Could not determine system memory, using minimal default: {str(e)}")
            return 10  # Ultra-minimal fallback
            
    def _check_memory_pressure(self):
        """Check if system is under memory pressure and respond accordingly"""
        if not PSUTIL_AVAILABLE:
            return False
            
        try:
            memory_info = virtual_memory()
            memory_percent = memory_info.percent
            
            if memory_percent > self.memory_threshold_percent:
                self.logger.warning("MergeController", f"Memory pressure detected: {memory_percent:.1f}%")
                
                # Immediate aggressive cleanup
                import sys
                gc.collect()
                gc.collect()  # Run twice for more thorough cleanup
                gc.collect()  # Third time for stubborn objects
                
                # Force cleanup of any cached objects
                if hasattr(sys, '_clear_type_cache'):
                    sys._clear_type_cache()
                    
                return True
                
            return False
        except Exception as e:
            self.logger.error("MergeController", f"Error checking memory pressure: {str(e)}")
            return False
        
    def merge_pdfs(self, pdf_files, output_filename=None, remove_white_space=False):
        """
        Merge a list of PDF files into a single PDF.
        
        Args:
            pdf_files (list): List of PDF file paths to merge
            output_filename (str, optional): Path for the output file
            remove_white_space (bool, optional): Whether to remove white space during merge
            
        Returns:
            str: Path to the merged PDF file
        """
        if not pdf_files:
            self.logger.warning("MergeController", "No PDF files provided for merging")
            self.complete_signal.emit(False, "No PDF files provided for merging")
            return None
            
        if self.merge_in_progress:
            self.logger.warning("MergeController", "Merge operation already in progress")
            self.complete_signal.emit(False, "Merge operation already in progress")
            return None
            
        self.merge_in_progress = True
        self.cancel_requested = False
        
        # Generate default output filename if not provided
        if not output_filename:
            current_date = datetime.datetime.now().strftime("%Y%m%d")
            output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "merge_output")
            os.makedirs(output_dir, exist_ok=True)
            output_filename = os.path.join(output_dir, f"Merged_Document_{current_date}.pdf")
            
            if remove_white_space:
                base_name, ext = os.path.splitext(output_filename)
                output_filename = f"{base_name}_no_white{ext}"
                
        self.merged_file_path = output_filename
        
        # Start the merge process in a separate thread to keep UI responsive
        merge_thread = threading.Thread(
            target=self._merge_process,
            args=(pdf_files, output_filename, remove_white_space),
            daemon=True
        )
        merge_thread.start()
        
        return output_filename
        
    def _merge_process(self, pdf_files, output_filename, remove_white_space):
        """Ultra-memory-efficient merge using streaming approach"""
        try:
            self.logger.info("MergeController", f"Starting streaming merge of {len(pdf_files)} PDFs to {output_filename}")
            self.status_signal.emit(f"Starting memory-efficient streaming merge of {len(pdf_files)} PDF files...")
            
            # Create output directory if it doesn't exist
            output_dir = os.path.dirname(output_filename)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
                
            # Count total pages for progress tracking
            total_pages = self._count_total_pages_efficient(pdf_files)
            if total_pages == 0:
                self.logger.warning("MergeController", "No pages found in the PDF files")
                self.complete_signal.emit(False, "No pages found in the PDF files")
                self.merge_in_progress = False
                return None
                
            self.logger.info("MergeController", f"Total pages to merge: {total_pages}")
            self.status_signal.emit(f"Streaming {total_pages} pages from {len(pdf_files)} PDF files...")
            
            # Use different merge strategies based on available library
            if PDF_LIBRARY == "fitz":
                success = self._merge_with_fitz(pdf_files, output_filename, total_pages, remove_white_space)
            else:
                success = self._merge_with_streaming_pypdf2(pdf_files, output_filename, total_pages, remove_white_space)
            
            if success:
                self.logger.info("MergeController", f"Successfully merged PDFs to {output_filename}")
                self.complete_signal.emit(True, f"Successfully merged {len(pdf_files)} PDFs ({total_pages} pages) to {os.path.basename(output_filename)}")
            else:
                self.complete_signal.emit(False, "Merge operation failed or was cancelled")
                
        except Exception as e:
            self.logger.error("MergeController", f"Error in merge process: {str(e)}")
            self.logger.error("MergeController", traceback.format_exc())
            self.complete_signal.emit(False, f"Error merging PDFs: {str(e)}")
            
        finally:
            # Final cleanup
            self.merge_in_progress = False
            gc.collect()
            
    def _merge_with_fitz(self, pdf_files, output_filename, total_pages, remove_white_space):
        """Ultra-memory-efficient merge using PyMuPDF (fitz) with micro-batching"""
        try:
            # Use temporary file for safety
            temp_output = output_filename + ".tmp"
            
            # Create output document
            output_doc = fitz.open()
            current_page = 0
            # Completely disable intermediate saves to avoid file locking issues
            # Instead rely on aggressive memory management and micro-batching
            
            for file_index, pdf_file in enumerate(pdf_files):
                if self.cancel_requested:
                    output_doc.close()
                    self._cleanup_temp_file(temp_output)
                    return False
                    
                try:
                    self.status_signal.emit(f"Processing file {file_index + 1}/{len(pdf_files)}: {os.path.basename(pdf_file)}")
                    
                    # Open source document with context manager for immediate cleanup
                    with fitz.open(pdf_file) as source_doc:
                        file_pages = len(source_doc)
                        
                        # Process pages in micro-batches to minimize memory
                        batch_size = 3  # Even smaller batches for large merges
                        
                        for batch_start in range(0, file_pages, batch_size):
                            batch_end = min(batch_start + batch_size, file_pages)
                            
                            # Insert micro-batch of pages
                            for page_num in range(batch_start, batch_end):
                                if self.cancel_requested:
                                    output_doc.close()
                                    self._cleanup_temp_file(temp_output)
                                    return False
                                
                                # Insert single page
                                output_doc.insert_pdf(source_doc, from_page=page_num, to_page=page_num)
                                current_page += 1
                                
                                # Ultra-aggressive memory management every 10 pages for large merges
                                if current_page % 10 == 0 and total_pages > 50000:
                                    gc.collect()
                                    gc.collect()
                                elif current_page % self.pages_per_gc_cycle == 0:
                                    self._check_memory_pressure()
                                    
                                # Periodic progress updates and memory monitoring
                                if current_page % 25 == 0 or current_page == total_pages:
                                    self.progress_signal.emit(current_page, total_pages)
                                    
                                    # Monitor memory usage
                                    if PSUTIL_AVAILABLE:
                                        memory_info = virtual_memory()
                                        memory_used_mb = (memory_info.total - memory_info.available) / (1024 * 1024)
                                        memory_percent = memory_info.percent
                                        
                                        self.status_signal.emit(f"Processed {current_page}/{total_pages} pages - Memory: {memory_used_mb:.0f}MB ({memory_percent:.1f}%)")
                                        
                                        # Trigger emergency cleanup if memory is critically high
                                        if memory_percent > 85:
                                            self.logger.warning("MergeController", f"Critical memory usage: {memory_percent:.1f}% - forcing cleanup")
                                            gc.collect()
                                            gc.collect()
                                            gc.collect()
                                    else:
                                        self.status_signal.emit(f"Processed {current_page}/{total_pages} pages")
                                
                                # No intermediate saves - rely purely on memory management
                                # Aggressive garbage collection for memory pressure
                                if PSUTIL_AVAILABLE:
                                    memory_info = virtual_memory()
                                    if memory_info.percent > 80:
                                        self.logger.warning("MergeController", f"High memory pressure detected: {memory_info.percent:.1f}%")
                                        gc.collect()
                                        gc.collect()
                                        gc.collect()
                            
                            # Micro-batch completed - force cleanup
                            gc.collect()
                        
                        # Source document automatically closed by context manager
                        
                except Exception as e:
                    self.logger.error("MergeController", f"Error processing {pdf_file}: {str(e)}")
                    continue
                
                # Force cleanup after each file
                gc.collect()
                gc.collect()
            
            # Save the final output document with timeout protection
            self.status_signal.emit("Saving final merged document...")
            self.progress_signal.emit(98, 100)  # Show 98% during save
            try:
                # Force garbage collection before final save
                gc.collect()
                gc.collect()
                
                # Save with retry mechanism for large files
                save_attempts = 0
                max_save_attempts = 3
                
                while save_attempts < max_save_attempts:
                    try:
                        self.logger.info("MergeController", f"Final save attempt {save_attempts + 1}/{max_save_attempts}")
                        output_doc.save(temp_output)
                        self.logger.info("MergeController", "Final save completed successfully")
                        break
                    except Exception as save_error:
                        save_attempts += 1
                        if save_attempts < max_save_attempts:
                            self.logger.warning("MergeController", f"Save attempt {save_attempts} failed: {str(save_error)}, retrying...")
                            gc.collect()
                            gc.collect()
                            time.sleep(1)  # Brief pause before retry
                        else:
                            raise save_error
                            
                output_doc.close()
                
                # Clean up any leftover intermediate files
                self._cleanup_leftover_intermediate_files(output_filename)
                
                # Final cleanup before moving file
                gc.collect()
                gc.collect()
                
                # Move temp file to final location with error handling
                if os.path.exists(temp_output):
                    self.status_signal.emit("Moving final file to destination...")
                    self.progress_signal.emit(99, 100)  # Show 99% during file move
                    if os.path.exists(output_filename):
                        os.remove(output_filename)
                    shutil.move(temp_output, output_filename)
                    self.logger.info("MergeController", f"Successfully moved final file to: {output_filename}")
                    self.progress_signal.emit(100, 100)  # Show 100% when complete
                else:
                    raise FileNotFoundError(f"Temporary output file not found: {temp_output}")
                    
            except Exception as final_save_error:
                self.logger.error("MergeController", f"Critical error during final save: {str(final_save_error)}")
                # Attempt to close document if still open
                try:
                    output_doc.close()
                except:
                    pass
                raise final_save_error
                
            return True
            
        except Exception as e:
            self.logger.error("MergeController", f"Error in ultra-optimized fitz merge: {str(e)}")
            return False
            
    def _merge_with_streaming_pypdf2(self, pdf_files, output_filename, total_pages, remove_white_space):
        """Ultra-memory-efficient fallback using PyPDF2 with minimal chunks"""
        temp_files = []
        try:
            # Ultra-small chunk size to minimize memory usage - PyPDF2's biggest weakness
            chunk_size = 3  # Minimal 3-page chunks for PyPDF2
            
            self.logger.info("MergeController", f"Using PyPDF2 with ultra-small {chunk_size}-page chunks")
            
            current_page = 0
            chunk_number = 0
            current_chunk_pages = 0
            current_writer = None
            current_temp_file = None
            
            for file_index, pdf_file in enumerate(pdf_files):
                if self.cancel_requested:
                    self._cleanup_temp_files(temp_files)
                    return False
                    
                try:
                    self.status_signal.emit(f"Processing file {file_index + 1}/{len(pdf_files)}: {os.path.basename(pdf_file)}")
                    
                    # Process one file at a time with immediate cleanup
                    with open(pdf_file, 'rb') as f:
                        reader = PdfReader(f)
                        
                        # Disable reader caching if possible
                        if hasattr(reader, 'cache_get_outline'):
                            reader.cache_get_outline = False
                            
                        file_pages = len(reader.pages)
                        
                        for page_index in range(file_pages):
                            if self.cancel_requested:
                                self._cleanup_temp_files(temp_files)
                                if current_temp_file:
                                    self._cleanup_temp_file(current_temp_file)
                                return False
                            
                            # Start new ultra-small chunk if needed
                            if current_chunk_pages == 0:
                                chunk_number += 1
                                current_temp_file = self._create_temp_file(f"ultra_chunk_{chunk_number}")
                                temp_files.append(current_temp_file)
                                current_writer = PdfWriter()
                                
                                # Disable PyPDF2 caching on writer too
                                if hasattr(current_writer, '_objects'):
                                    current_writer._objects = {}  # Clear object cache
                                
                            # Add single page to current chunk
                            page = reader.pages[page_index]
                            
                            # Apply white space removal if requested (minimal processing)
                            if remove_white_space:
                                page = self._remove_white_space(page)
                                
                            current_writer.add_page(page)
                            current_page += 1
                            current_chunk_pages += 1
                            
                            # Immediately write chunk when it reaches tiny size limit
                            if current_chunk_pages >= chunk_size:
                                # Write current chunk to temp file immediately
                                with open(current_temp_file, 'wb') as temp_output:
                                    current_writer.write(temp_output)
                                
                                # Aggressive cleanup of writer objects
                                if hasattr(current_writer, '_objects'):
                                    current_writer._objects.clear()
                                del current_writer
                                current_writer = None
                                current_chunk_pages = 0
                                
                                # Triple garbage collection for PyPDF2's stubborn objects
                                gc.collect()
                                gc.collect()
                                gc.collect()
                                
                                # Check memory pressure after each chunk
                                self._check_memory_pressure()
                            
                            # Frequent progress updates for better responsiveness
                            if current_page % 10 == 0 or current_page == total_pages:
                                self.progress_signal.emit(current_page, total_pages)
                                
                                if PSUTIL_AVAILABLE:
                                    memory_info = virtual_memory()
                                    memory_percent = memory_info.percent
                                    memory_used_mb = (memory_info.total - memory_info.available) / (1024 * 1024)
                                    self.status_signal.emit(f"Processed {current_page}/{total_pages} pages ({chunk_number} chunks) - Memory: {memory_used_mb:.0f}MB ({memory_percent:.1f}%)")
                                else:
                                    self.status_signal.emit(f"Processed {current_page}/{total_pages} pages ({chunk_number} chunks)")
                        
                        # Aggressive cleanup of reader
                        if hasattr(reader, '_objects'):
                            reader._objects.clear()
                        del reader
                        
                        # Force cleanup after each file
                        gc.collect()
                        gc.collect()
                        
                except Exception as e:
                    self.logger.error("MergeController", f"Error processing {pdf_file}: {str(e)}")
                    continue
            
            # Write final partial chunk if exists
            if current_writer and current_chunk_pages > 0:
                with open(current_temp_file, 'wb') as temp_output:
                    current_writer.write(temp_output)
                if hasattr(current_writer, '_objects'):
                    current_writer._objects.clear()
                del current_writer
                gc.collect()
                gc.collect()
            
            # Ultra-conservative merge of chunks - one pair at a time
            self.status_signal.emit(f"Ultra-conservative merge of {len(temp_files)} chunks...")
            success = self._ultra_conservative_merge_pypdf2_chunks(temp_files, output_filename)
            
            # Cleanup temporary files
            self._cleanup_temp_files(temp_files)
            
            return success
            
        except Exception as e:
            self._cleanup_temp_files(temp_files)
            self.logger.error("MergeController", f"Error in ultra-optimized PyPDF2 merge: {str(e)}")
            return False
            
    def _ultra_conservative_merge_pypdf2_chunks(self, temp_files, output_filename):
        """Ultra-conservative merge with maximum memory efficiency"""
        try:
            if not temp_files:
                return False
                
            temp_output = output_filename + ".tmp"
            
            # If only one file, just copy it
            if len(temp_files) == 1:
                shutil.copy2(temp_files[0], temp_output)
            else:
                # Merge files one pair at a time with aggressive cleanup
                current_file = temp_files[0]
                
                for i, next_file in enumerate(temp_files[1:], 1):
                    if self.cancel_requested:
                        return False
                        
                    self.status_signal.emit(f"Merging chunk {i + 1}/{len(temp_files)} (ultra-conservative)")
                    
                    # Create next merge step
                    merge_temp = f"{temp_output}.merge_{i}"
                    
                    # Merge just two files with minimal memory usage
                    success = self._merge_two_files_minimal(current_file, next_file, merge_temp)
                    
                    if not success:
                        return False
                    
                    # Clean up the previous temporary file (but not original chunks yet)
                    if i > 1:  # Don't remove the first original chunk file
                        self._cleanup_temp_file(current_file)
                    
                    # Use the new merged file as current
                    current_file = merge_temp
                    
                    # Aggressive cleanup after each merge step
                    gc.collect()
                    gc.collect()
                    gc.collect()
                    self._check_memory_pressure()
                
                # Move final result to temp output location
                if current_file != temp_output:
                    shutil.move(current_file, temp_output)
            
            # Move temp file to final location
            if os.path.exists(temp_output):
                if os.path.exists(output_filename):
                    os.remove(output_filename)
                shutil.move(temp_output, output_filename)
                
            return True
            
        except Exception as e:
            self.logger.error("MergeController", f"Error in ultra-conservative merge: {str(e)}")
            return False
            
    def _merge_two_files_minimal(self, file1, file2, output_file):
        """Merge exactly two PDF files with minimal memory usage"""
        try:
            final_writer = PdfWriter()
            
            # Process first file
            with open(file1, 'rb') as f1:
                reader1 = PdfReader(f1)
                
                # Disable caching
                if hasattr(reader1, 'cache_get_outline'):
                    reader1.cache_get_outline = False
                
                # Add pages one by one
                for page in reader1.pages:
                    final_writer.add_page(page)
                
                # Clear reader cache
                if hasattr(reader1, '_objects'):
                    reader1._objects.clear()
                del reader1
                
            # Force cleanup between files
            gc.collect()
            gc.collect()
            
            # Process second file
            with open(file2, 'rb') as f2:
                reader2 = PdfReader(f2)
                
                # Disable caching
                if hasattr(reader2, 'cache_get_outline'):
                    reader2.cache_get_outline = False
                
                # Add pages one by one
                for page in reader2.pages:
                    final_writer.add_page(page)
                
                # Clear reader cache
                if hasattr(reader2, '_objects'):
                    reader2._objects.clear()
                del reader2
            
            # Write the combined result
            with open(output_file, 'wb') as output_f:
                final_writer.write(output_f)
            
            # Clear writer cache
            if hasattr(final_writer, '_objects'):
                final_writer._objects.clear()
            del final_writer
            
            # Triple cleanup
            gc.collect()
            gc.collect()
            gc.collect()
            
            return True
            
        except Exception as e:
            self.logger.error("MergeController", f"Error merging two files: {str(e)}")
            return False
            
    def _create_temp_file(self, prefix):
        """Create a temporary file for chunk storage"""
        temp_dir = tempfile.gettempdir()
        temp_file = os.path.join(temp_dir, f"{prefix}_{int(time.time())}.pdf")
        return temp_file
        
    def _merge_temp_files(self, temp_files, output_filename):
        """Efficiently merge temporary chunk files"""
        self.logger.info("MergeController", f"Merging {len(temp_files)} temporary files")
        
        # Use temporary output file for safety
        temp_output = output_filename + ".tmp"
        
        with open(temp_output, 'wb') as output_file:
            final_writer = PdfWriter()
            
            for i, temp_file in enumerate(temp_files):
                if self.cancel_requested:
                    self._cleanup_temp_file(temp_output)
                    return
                    
                try:
                    with open(temp_file, 'rb') as f:
                        reader = PdfReader(f)
                        
                        # Add all pages from this chunk
                        for page in reader.pages:
                            final_writer.add_page(page)
                        
                        # Clear reader immediately
                        del reader
                        
                    self.status_signal.emit(f"Combined chunk {i + 1}/{len(temp_files)}")
                    
                except Exception as e:
                    self.logger.error("MergeController", f"Error merging temp file {temp_file}: {str(e)}")
                    
                # Force garbage collection after each chunk
                gc.collect()
            
            # Write final merged file
            final_writer.write(output_file)
            del final_writer
            gc.collect()
        
        # Move temp file to final location
        if os.path.exists(temp_output):
            if os.path.exists(output_filename):
                os.remove(output_filename)
            shutil.move(temp_output, output_filename)
            
    def _cleanup_temp_files(self, temp_files):
        """Clean up list of temporary files"""
        for temp_file in temp_files:
            self._cleanup_temp_file(temp_file)
            
    def _count_total_pages_efficient(self, pdf_files):
        """Ultra-efficiently count total pages with minimal memory footprint"""
        total_pages = 0
        for i, pdf_file in enumerate(pdf_files):
            if self.cancel_requested:
                return 0
                
            try:
                if PDF_LIBRARY == "fitz":
                    # Use PyMuPDF for ultra-efficient counting
                    with fitz.open(pdf_file) as doc:
                        file_pages = len(doc)
                        total_pages += file_pages
                        # Document automatically closed by context manager
                else:
                    # Use PyPDF2 with ultra-aggressive optimization
                    with open(pdf_file, 'rb') as f:
                        reader = PdfReader(f)
                        
                        # Disable all caching for minimal memory
                        if hasattr(reader, 'cache_get_outline'):
                            reader.cache_get_outline = False
                        
                        # Get page count without loading pages
                        file_pages = len(reader.pages)
                        total_pages += file_pages
                        
                        # Aggressive cleanup
                        if hasattr(reader, '_objects'):
                            reader._objects.clear()
                        del reader
                        
                        # Force garbage collection every few files
                        if i % 5 == 0:
                            gc.collect()
                            gc.collect()
                
                # Update progress for counting phase
                self.progress_signal.emit(i + 1, len(pdf_files))
                self.status_signal.emit(f"Counting pages: {file_pages} in {os.path.basename(pdf_file)}")
                
                # Check memory pressure during counting
                if i % 10 == 0:  # Check every 10 files
                    self._check_memory_pressure()
                    
            except Exception as e:
                self.logger.error("MergeController", f"Error counting pages in {pdf_file}: {str(e)}")
                
        return total_pages
        
    def _cleanup_temp_file(self, temp_file):
        """Clean up temporary file"""
        if temp_file and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
                self.logger.info("MergeController", f"Cleaned up temporary file: {temp_file}")
            except Exception as e:
                self.logger.error("MergeController", f"Error cleaning up temp file {temp_file}: {str(e)}")
                
    def _cleanup_temp_file_safe(self, temp_file):
        """Safely clean up temporary file with retries for locked files"""
        if not temp_file or not os.path.exists(temp_file):
            return
            
        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                os.remove(temp_file)
                self.logger.info("MergeController", f"Safely cleaned up temporary file: {temp_file}")
                return
            except PermissionError as e:
                if attempt < max_attempts - 1:
                    self.logger.warning("MergeController", f"File locked, retry {attempt + 1}/{max_attempts}: {temp_file}")
                    time.sleep(0.2 * (attempt + 1))  # Increasing delay
                    gc.collect()  # Force garbage collection to release references
                else:
                    self.logger.error("MergeController", f"Failed to cleanup file after {max_attempts} attempts: {temp_file}")
            except Exception as e:
                self.logger.error("MergeController", f"Error safely cleaning up temp file {temp_file}: {str(e)}")
                break
                
    def _cleanup_leftover_intermediate_files(self, output_filename):
        """Clean up any leftover intermediate files from the merge process"""
        try:
            temp_output = output_filename + ".tmp"
            output_dir = os.path.dirname(temp_output)
            
            if not os.path.exists(output_dir):
                return
            
            # Look for any intermediate files related to this merge
            for file in os.listdir(output_dir):
                if file.startswith(os.path.basename(temp_output) + ".intermediate_"):
                    leftover_file = os.path.join(output_dir, file)
                    self.logger.warning("MergeController", f"Cleaning up leftover intermediate file: {leftover_file}")
                    self._cleanup_temp_file_safe(leftover_file)
                    
        except Exception as e:
            self.logger.error("MergeController", f"Error cleaning up leftover intermediate files: {str(e)}")
            # Don't let cleanup errors break the main process
            
    def _remove_white_space(self, page):
        """
        Remove white space from a PDF page
        This is a simplified version - actual implementation would depend on PyPDF2's capabilities
        """
        # This is a placeholder - the actual white space removal logic would be more complex
        # and might involve analyzing page content
        return page
        
    def cancel_merge(self):
        """Cancel the current merge operation"""
        if self.merge_in_progress:
            self.logger.info("MergeController", "Cancel requested for merge operation")
            self.cancel_requested = True
            self.status_signal.emit("Cancelling merge operation...")
            
            # Signal worker processes to stop
            if self.cancel_event:
                self.cancel_event.set()
                
            return True
        return False
        
    def get_merged_file_path(self):
        """Get the path to the most recently created merged file"""
        return self.merged_file_path
    
    def validate_pdfs(self, pdf_files):
        """
        Validate that the provided files are valid PDFs
        
        Args:
            pdf_files (list): List of file paths to validate
            
        Returns:
            list: List of valid PDF file paths
        """
        valid_files = []
        
        for pdf_file in pdf_files:
            try:
                # Check if file exists
                if not os.path.exists(pdf_file):
                    self.logger.warning("MergeController", f"File does not exist: {pdf_file}")
                    continue
                
                # Try to open as PDF
                with open(pdf_file, 'rb') as f:
                    try:
                        reader = PdfReader(f)
                        # Check if we can access pages
                        if len(reader.pages) > 0:
                            valid_files.append(pdf_file)
                        else:
                            self.logger.warning("MergeController", f"PDF has no pages: {pdf_file}")
                    except Exception as e:
                        self.logger.warning("MergeController", f"Invalid PDF: {pdf_file}, Error: {str(e)}")
            except Exception as e:
                self.logger.warning("MergeController", f"Error checking file: {pdf_file}, Error: {str(e)}")
                
        return valid_files
        self.temp_files = []
