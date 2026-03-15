from PDFUtility.PDFLogger import Logger
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import ttkbootstrap as ttk
from SettingsController import SettingsController
from Utility import Utility
from ProgressDialog import ProgressDialog, DualProgressDialog
import fitz
import threading
import time
from threading import Thread
import gc
import datetime
import traceback
import tempfile
import shutil
from multiprocessing import Process, Queue, Event, cpu_count, current_process, freeze_support
from psutil import virtual_memory, disk_usage
from ttkbootstrap import Window

# Root = Window(themename="darkly")
# Root.withdraw()
# SETTINGSCONTROLLER = SettingsController(Root)
# settings_controller = SETTINGSCONTROLLER.load_settings()
# Define a simplified worker function for single PDF tasks
def pdf_chunk_worker(task_id, input_file, output_file, start_page, end_page, result_queue, cancel_event, log_dir):
    """Process a single chunk of a PDF file."""
    worker_name = f"ChunkWorker-{task_id}"
    
    try:
        # Create a log file for debugging
        log_path = os.path.join(log_dir, f"pdf_worker_{task_id}.log")
        with open(log_path, "w") as log:
            log.write(f"{worker_name}: Started\n")
            log.write(f"{worker_name}: Processing {input_file} pages {start_page}-{end_page}\n")
            
            # Create output directory if it doesn't exist
            out_dir = os.path.dirname(output_file)
            if not os.path.exists(out_dir):
                os.makedirs(out_dir, exist_ok=True)
                log.write(f"{worker_name}: Created output directory: {out_dir}\n")
            
            # Open source document
            doc = fitz.open(input_file)
            log.write(f"{worker_name}: Opened source document with {len(doc)} pages\n")
            
            # Create output document
            out_doc = fitz.open()
            log.write(f"{worker_name}: Created new document\n")
            
            # Copy specified pages
            actual_end = min(end_page, len(doc))
            for i in range(start_page, actual_end):
                if cancel_event.is_set():
                    log.write(f"{worker_name}: Cancelled\n")
                    break
                
                # Copy page
                out_doc.insert_pdf(doc, from_page=i, to_page=i)
                log.write(f"{worker_name}: Copied page {i}\n")
            
            # Save and close
            log.write(f"{worker_name}: Saving to {output_file}\n")
            out_doc.save(output_file)
            log.write(f"{worker_name}: File saved successfully\n")
            out_doc.close()
            doc.close()
            
            log.write(f"{worker_name}: Completed successfully\n")
            
            # Report success
            result_queue.put(("success", task_id, output_file, end_page - start_page))
            
    except Exception as e:
        error_msg = f"{worker_name}: Error: {str(e)}\n{traceback.format_exc()}"
        try:
            # Try to write to log file
            log_path = settings_controller.get_setting("log_dir")
            with open(log_path, "a") as log:
                log.write(error_msg)
        except:
            pass
            
        # Report error
        result_queue.put(("error", task_id, input_file, str(e)))

class MergeController:
    def __init__(self, root, selection_indices):
        self.selection_indices = selection_indices  # These are the indices from the listbox
        self.selected_indices = []  # Will be populated with set_selected_indices
        self.root = root
        self.settings_controller = SettingsController(self.root)
        
        self.settings = self.settings_controller.load_settings()
        self.logger = Logger()
        self.utility = Utility(self.root)
        self.logger.info("MergeController", "==========================================================")
        self.logger.info("MergeController", " EVENT: INIT")
        self.logger.info("MergeController", "==========================================================")
        self.pdf_files = []  # This will hold the actual file paths
        self.status_label = None
        self.cancel_event = None
        self.workers = []
        self.temp_dir = None
        self.result_queue = None
        self.chunk_size = 20  # Number of pages per chunk - reduced for better stability
        

    def set_status_label(self, status_label):
        self.status_label = status_label

    def set_selection(self, selection):
        """
        Update the selected files based on the provided selection.
        In the main program, this is called with listbox indices, not file paths.
        We'll store these indices for reference, but actual file paths should be
        set separately with set_pdf_files.
        """
        # Store the selection indices, but don't overwrite pdf_files
        self.selection_indices = selection
        self.logger.info("MergeController", f"Selection indices updated: {self.selection_indices}")
        
    def set_pdf_files(self, pdf_files):
        """Set the actual PDF file paths that correspond to the selection indices."""
        self.pdf_files = pdf_files
        self.logger.info("MergeController", f"PDF files list updated: {len(self.pdf_files)} files")

    def set_selected_indices(self, selected_indices):
        """Update the selected indices list for the PDF files to merge."""
        self.selected_indices = selected_indices
        self.logger.info("MergeController", f"Selected indices updated: {self.selected_indices}")

    def get_selected_files(self):
        """Return the list of selected PDF files based on the indices."""
        if not self.selected_indices or not self.pdf_files:
            return []
        
        # Make sure we don't try to access indices that are out of range
        valid_files = []
        for index in self.selected_indices:
            if 0 <= index < len(self.pdf_files):
                valid_files.append(self.pdf_files[index])
            else:
                self.logger.warning("MergeController", f"Invalid index {index} for pdf_files list of length {len(self.pdf_files)}")
        
        return valid_files

    def get_completed_files(self):
        """Return the list of PDF files, including any newly merged files."""
        return self.pdf_files

    def merge_pdf_ui(self):
        """Main entry point for merging PDFs with UI feedback."""
        self.logger.info("MergeController", "Starting PDF merge operation")
        
        # Enable multiprocessing freeze support
        freeze_support()
        
        # Validate selection
        selected_files = self.get_selected_files()
        if len(selected_files) < 2:
            messagebox.showinfo("Info", "Please select at least 2 PDF files to merge")
            self.logger.info("MergeController", "Please select at least 2 PDF files to merge")
            return False

        # Get merge directory from settings_controller
    
        merge_directory = self.settings_controller.get_setting("merge_directory")
        self.logger.info("MergeController", f"Using merge directory: {merge_directory}")
        if not merge_directory:
            merge_directory = os.path.join(os.getcwd(), "merge_output")
            self.logger.warning("MergeController", "Merge directory not set, using default: merge_output")
        os.makedirs(merge_directory, exist_ok=True)

        # Get filename from user
        self.logger.info("MergeController", "Getting merge filename from user")
        output_pdf = self.get_merge_filename(merge_directory)
        if not output_pdf:
            self.logger.info("MergeController", "User canceled")
            return False
        self.logger.info("MergeController", f"Got merge filename: {output_pdf}")

        # Initialize cancel event
        self.cancel_event = Event()
        
        # Create progress dialog
        self.progress = DualProgressDialog(
            self.root,
            title="Merging PDFs", 
            message="Analyzing PDFs..."
        )
        
        # Connect cancel button to our cancel method
        original_cancel = self.progress.cancel
        def custom_cancel():
            original_cancel()  # Call the original cancel method
            self.cancel_merge()  # Call our custom cancel method
        self.progress.cancel = custom_cancel

        # Start the chunked merge operation
        Thread(target=self.run_chunked_merge, args=(selected_files, output_pdf), daemon=True).start()
        
        # Return True to indicate the operation started successfully
        return True

    def cancel_merge(self):
        """Cancel the merge operation."""
        self.logger.info("MergeController", "User requested cancellation")
        if self.cancel_event:
            self.logger.info("MergeController", "Setting cancel event")
            self.cancel_event.set()
            
            # Update UI to show cancellation is in progress
            if self.status_label:
                self.status_label.config(text="Cancelling merge operation...")
                
            # Update progress dialog
            if hasattr(self, 'progress') and self.progress:
                self.progress.update_overall_status("Cancelling - please wait...")
                self.progress.update_current_status("Terminating worker processes...")
            
        return True
    
    def _cleanup(self):
        """Clean up resources used in the merge operation."""
        self.logger.info("MergeController", "Cleaning up resources")
        
        # Terminate any running workers
        for proc in self.workers:
            if proc and proc.is_alive():
                try:
                    proc.terminate()
                    self.logger.info("MergeController", f"Terminated worker process {proc.pid}")
                except:
                    pass
        
        # Clear workers list
        self.workers = []
        
        # Clean up temporary directory - only if we have one and we're done with it
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                self.logger.info("MergeController", f"Removed temporary directory: {self.temp_dir}")
                self.temp_dir = None
            except Exception as e:
                self.logger.error("MergeController", f"Error removing temp directory: {str(e)}")

    def get_merge_filename(self, merge_directory):
        """
        Display a dialog to get the merge filename from the user.
        Returns the full file path or None if canceled.
        """
        # Create date suffix
        date_suffix = datetime.datetime.now().strftime('%Y%m%d')

        # Create dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Merged PDF Name")
        dialog.transient(self.root)
        dialog.grab_set()

        # Create main frame with padding
        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Add explanation label
        ttk.Label(
            main_frame, 
            text="Enter a name for the merged PDF file:", 
            font=("Arial", 11)
        ).pack(anchor="w", pady=(0, 10))

        # Create entry frame
        entry_frame = ttk.Frame(main_frame)
        entry_frame.pack(fill=tk.X, pady=5)

        # Add entry field
        name_var = tk.StringVar(value="Merged_Document")
        name_entry = ttk.Entry(entry_frame, textvariable=name_var, width=30)
        name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Add suffix label
        suffix_label = ttk.Label(entry_frame, text=f"_{date_suffix}.pdf")
        suffix_label.pack(side=tk.LEFT, padx=(5, 0))

        # Add help text
        ttk.Label(
            main_frame, 
            text="The file will be saved in your configured merge directory:", 
            font=("Arial", 9)
        ).pack(anchor="w", pady=(15, 0))

        ttk.Label(
            main_frame, 
            text=merge_directory,
            font=("Arial", 9),
            foreground="blue"
        ).pack(anchor="w", pady=(0, 15))

        # Create button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # Define result dictionary
        result = {"filename": None}

        def on_ok():
            """User clicked OK"""
            base_name = name_var.get().strip()
            if not base_name:
                messagebox.showerror("Error", "Please enter a file name.")
                dialog.lift()
                return

            # Create full path
            filename = f"{base_name}_{date_suffix}.pdf"
            full_path = os.path.join(merge_directory, filename)

            # Check if file exists
            if os.path.exists(full_path):
                overwrite = messagebox.askyesno(
                    "File Exists", 
                    f"The file '{filename}' already exists. Do you want to overwrite it?"
                )
                if not overwrite:
                    dialog.lift()
                    return
            result["filename"] = full_path
            dialog.destroy()

        def on_cancel():
            """User clicked Cancel"""
            dialog.destroy()

        # Add buttons
        ttk.Button(button_frame, text="OK", command=on_ok, width=10).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=on_cancel, width=10).pack(side=tk.RIGHT, padx=5)

        # Select all text in entry for easy editing
        name_entry.select_range(0, tk.END)
        name_entry.focus_set()

        # Dynamically calculate the required height
        dialog.update_idletasks()  # Ensure all widgets are rendered
        width = max(400, dialog.winfo_reqwidth())
        height = dialog.winfo_reqheight()

        # Center the dialog
        x = self.root.winfo_x() + (self.root.winfo_width() - width) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - height) // 2
        dialog.geometry(f"{width}x{height}+{x}+{y}")

        # Wait for dialog to close
        self.root.wait_window(dialog)

        return result["filename"]

    def run_chunked_merge(self, files, output_pdf):
        """
        Merge PDFs using a chunked approach to avoid memory issues.
        Each chunk is processed in a separate process.
        """
        try:
            self.logger.info("MergeController", f"Starting chunked merge with {len(files)} files")
            start_time = time.time()
            
            # Create temporary directory
            self.temp_dir = tempfile.mkdtemp(prefix="pdf_merge_")
            self.logger.info("MergeController", f"Created temporary directory: {self.temp_dir}")
            
            # Step 1: Analyze PDFs to count pages
            self.progress.update_message("Analyzing PDFs...")
            pdf_info = self._analyze_pdfs(files)
            
            if self.cancel_event.is_set():
                self._cleanup()
                self.progress.close()
                return
            
            # Step 2: Prepare the chunks
            self.progress.update_message("Preparing to process PDF chunks...")
            chunks = self._prepare_chunks(pdf_info)
            
            if not chunks or self.cancel_event.is_set():
                self._cleanup()
                self.progress.close()
                return
                
            # Step 3: Process chunks
            self.result_queue = Queue()
            completed_chunks = self._process_chunks(chunks, start_time)
            
            if self.cancel_event.is_set():
                self.logger.info("MergeController", "Merge operation was cancelled")
                if self.progress:
                    self.progress.close()
                self._cleanup()
                return
                
            if not completed_chunks:
                self.logger.error("MergeController", "No chunks were completed successfully")
                self.root.after(0, lambda: messagebox.showerror(
                    "Error", "Failed to process any PDF chunks."
                ))
                self._cleanup()
                if self.progress:
                    self.progress.close()
                return
                
            # Step 4: Merge chunks into final document
            if not self.cancel_event.is_set():
                self.logger.info("MergeController", f"All chunks processed. Merging {len(completed_chunks)} chunks into final PDF")
                self.progress.update_message("Combining chunks into final document...")
                success = self._merge_chunks(completed_chunks, output_pdf)
                
                if success:
                    self._handle_successful_merge(output_pdf)
                else:
                    self.logger.error("MergeController", "Failed to merge chunks into final document")
                    self.root.after(0, lambda: messagebox.showerror(
                        "Error", "Failed to create the final merged document."
                    ))
            
            # Step 5: Clean up
            if self.progress:
                self.progress.close()
            self._cleanup()
            
        except Exception as e:
            error_details = traceback.format_exc()
            self.logger.error("MergeController", f"Error in merge operation: {str(e)}\n{error_details}")
            self.root.after(0, lambda: messagebox.showerror("Error", f"Merge failed: {str(e)}"))
            
            if hasattr(self, 'progress') and self.progress:
                self.progress.close()
                
            if self.status_label:
                self.status_label.config(text="Merge operation failed")
                
            self._cleanup()

    def _analyze_pdfs(self, files):
        """
        Analyze PDF files to get page counts.
        Returns a list of (file_path, page_count) tuples.
        """
        pdf_info = []
        total_files = len(files)
        
        for i, pdf_file in enumerate(files):
            if self.cancel_event.is_set():
                break
                
            filename = os.path.basename(pdf_file)
            self.progress.update_current_status(f"Analyzing file {i+1}/{total_files}: {filename}")
            self.progress.update_overall_progress((i / total_files) * 100)
            
            try:
                self.logger.info("MergeController", f"Analyzing PDF: {pdf_file}")
                doc = fitz.open(pdf_file)
                page_count = len(doc)
                pdf_info.append((pdf_file, page_count))
                self.logger.info("MergeController", f"PDF {filename} has {page_count} pages")
                doc.close()
                gc.collect()
            except Exception as e:
                self.logger.error("MergeController", f"Error analyzing {filename}: {str(e)}")
                self.root.after(0, lambda: messagebox.showerror(
                    "Error", f"Error analyzing {filename}: {str(e)}"
                ))
                return []
                
        return pdf_info
        
    def _prepare_chunks(self, pdf_info):
        """
        Prepare a list of chunks to process.
        Each chunk represents a range of pages from a PDF file.
        """
        chunks = []
        chunk_id = 0
        
        for file_path, page_count in pdf_info:
            # Split large PDFs into chunks
            for start_page in range(0, page_count, self.chunk_size):
                end_page = min(start_page + self.chunk_size, page_count)
                
                # Create temp output path for this chunk
                out_path = os.path.join(self.temp_dir, f"chunk_{chunk_id}.pdf")
                
                # Add to chunks list
                chunks.append({
                    'id': chunk_id,
                    'input': file_path,
                    'output': out_path,
                    'start_page': start_page,
                    'end_page': end_page,
                    'size': end_page - start_page
                })
                
                chunk_id += 1
                
        self.logger.info("MergeController", f"Prepared {len(chunks)} chunks for processing")
        return chunks
        
    # The full updated code is too long to display inline, so let's focus on updating the most critical function: `_process_chunks`.

    # Updated _process_chunks function with proper throttling and improved memory management
    def _process_chunks(self, chunks, start_time):
        """
        Process all chunks using a capped number of worker processes.
        Returns a list of completed chunk files in correct order.
        """
        max_workers = max(1, min(cpu_count() - 1, 4))
        total_chunks = len(chunks)
        self.logger.info("MergeController", f"Using {max_workers} worker processes")

        self.progress.update_message("Processing PDF chunks...")
        self.progress.update_overall_status(f"Processing {total_chunks} chunks...")
        self.progress.update_current_status("Starting chunk processing...")

        completed_chunks = [None] * total_chunks  # Ensure correct order
        self.workers = [None] * total_chunks  # Track workers by chunk id

        chunk_dir = self.settings_controller.get_setting("temporary_file_location") or os.path.dirname(chunks[0]['output']) if chunks else tempfile.gettempdir()

        def has_enough_space():
            usage = disk_usage(chunk_dir)
            available_mb = usage.free / (1024 ** 2)
            self.logger.debug("MergeController", f"Disk space available: {available_mb:.2f} MB")
            return available_mb > 200  # Require at least 200MB free

        def start_worker(chunk):
            if not has_enough_space():
                self.logger.error("MergeController", "Insufficient disk space to continue processing.")
                self.cancel_event.set()
                return
            safe_settings = {
                "log_dir": self.settings_controller.get_setting("log_dir")
            }
            p = Process(
                target=pdf_chunk_worker,
                args=(
                    chunk['id'],
                    chunk['input'],
                    chunk['output'],
                    chunk['start_page'],
                    chunk['end_page'],
                    self.result_queue,
                    self.cancel_event,
                    self.settings_controller.get_setting("log_dir")
                )
            )
            p.daemon = True
            p.start()
            self.workers[chunk['id']] = p
            self.logger.info("MergeController", f"Started worker for chunk {chunk['id']} ({chunk['start_page']}-{chunk['end_page']} of {os.path.basename(chunk['input'])})")

        chunk_index = 0
        active_chunks = set()
        last_update_time = time.time()

        while chunk_index < total_chunks or active_chunks:
            if self.cancel_event.is_set():
                break

            # Start new workers if under cap
            while len(active_chunks) < max_workers and chunk_index < total_chunks:
                chunk = chunks[chunk_index]
                start_worker(chunk)
                if not self.cancel_event.is_set():
                    active_chunks.add(chunk['id'])
                    chunk_index += 1

            # Process finished results
            while not self.result_queue.empty():
                try:
                    status, chunk_id, chunk_path, size = self.result_queue.get_nowait()
                    active_chunks.discard(chunk_id)
                    if status == "success" and os.path.exists(chunk_path):
                        completed_chunks[chunk_id] = chunk_path
                        percent = (sum(c is not None for c in completed_chunks) / total_chunks) * 100
                        self.progress.update_overall_progress(percent)
                        self.progress.update_current_status(f"Completed chunk {chunk_id + 1}/{total_chunks}")
                        self.logger.info("MergeController", f"Chunk {chunk_id} completed. Progress: {chunk_id + 1}/{total_chunks}")
                    else:
                        self.logger.error("MergeController", f"Error in chunk {chunk_id}: {size}")
                        self.progress.update_additional_message(f"Chunk {chunk_id} error: {size}")

                except Exception as e:
                    self.logger.error("MergeController", f"Error processing result queue: {str(e)}")

            # Cleanup dead workers
            for i in list(active_chunks):
                p = self.workers[i]
                if p is not None and not p.is_alive():
                    self.logger.warning("MergeController", f"Worker {i} died unexpectedly")
                    active_chunks.discard(i)

            # Force GC periodically
            if time.time() - last_update_time > 5:
                gc.collect()
                memory = virtual_memory()
                self.logger.debug("MergeController", f"Memory available: {memory.available / (1024**2):.2f} MB")
                last_update_time = time.time()

            time.sleep(0.1)  # Small delay to prevent busy looping

        # DO NOT DELETE CHUNK FILES HERE — let merge finalize first!
        return [chunk for chunk in completed_chunks if chunk is not None]


    def _merge_chunks(self, chunk_files, output_path):
        """
        Merge all the chunk files into a single output PDF.
        This runs in the main process to ensure stability.
        """
        try:
            self.logger.info("MergeController", f"Merging {len(chunk_files)} chunks into final document")
            self.progress.update_current_status(f"Combining {len(chunk_files)} chunks...")
            
            # Create output document
            out_doc = fitz.open()
            
            # Add each chunk
            for i, chunk_file in enumerate(chunk_files):
                if self.cancel_event.is_set():
                    out_doc.close()
                    return False
                
                try:
                    # Open chunk
                    chunk_doc = fitz.open(chunk_file)
                    
                    # Add all pages
                    out_doc.insert_pdf(chunk_doc)
                    
                    # Close chunk
                    chunk_doc.close()
                    
                    # Update progress
                    percent = ((i + 1) / len(chunk_files)) * 100
                    self.progress.update_current_progress(percent)
                    self.progress.update_current_status(f"Merged chunk {i+1}/{len(chunk_files)}")
                    
                except Exception as e:
                    self.logger.error("MergeController", f"Error adding chunk {i}: {str(e)}")
                    raise
            
            # Save final document
            self.progress.update_current_status("Saving final document...")
            
            # Make sure the output directory exists
            output_dir = os.path.dirname(output_path)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
                
            out_doc.save(output_path)
            out_doc.close()
            self.pdf_files.append(output_path)
            self.logger.info("MergeController", f"Successfully saved merged PDF to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error("MergeController", f"Error merging chunks: {str(e)}")
            return False
    
    def _handle_successful_merge(self, merged_file):
        """Handle successful completion of the merge operation."""
        if not os.path.exists(merged_file):
            self.logger.error("MergeController", "Merge completed but output file wasn't created")
            self.root.after(0, lambda: messagebox.showerror(
                "Error", 
                "Merge completed but the output file wasn't created."
            ))
            return
            
        try:
            # Verify the file with PyMuPDF
            doc = fitz.open(merged_file)
            page_count = len(doc)
            self.logger.info("MergeController", f"Successfully merged PDF with {page_count} pages")
            doc.close()
            # Add to file list
            self.pdf_files.append(merged_file)
            self.logger.info("MergeController", f"Added merged file to PDF list: {merged_file}")
            
            # Verify no duplicates in the pdf_files list
            unique_files = list(set(self.pdf_files))
            if len(unique_files) < len(self.pdf_files):
                self.logger.warning("MergeController", "Duplicate files found in pdf_files list, removing duplicates")
                self.pdf_files = unique_files
                
            # Update status label
            if self.status_label:
                message = f"Merged {len(self.selected_indices)} PDFs to {os.path.basename(merged_file)} ({page_count} pages)"
                self.status_label.config(text=message)
                self.logger.info("MergeController", f"Updated status label: {message}")
                
            # Show success message
            self.root.after(0, lambda: messagebox.showinfo(
                "Success", 
                f"Successfully merged {len(self.selected_indices)} PDFs into {os.path.basename(merged_file)} with {page_count} pages."
            ))
            
        except Exception as e:
            error_details = traceback.format_exc()
            self.logger.error("MergeController", f"Error verifying merged file: {str(e)}\n{error_details}")
            self.root.after(0, lambda: messagebox.showerror(
                "Error", 
                f"Error verifying merged file: {str(e)}"
            ))