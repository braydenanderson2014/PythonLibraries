import configparser
import os
import glob
import shutil
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PyPDF2 import PdfReader, PdfWriter
import config
from ad_system import AdSystem
import subprocess
from PIL import Image, ImageTk
import threading
from threading import Thread
import time
from ImageControl import ImageControl
from PlaybackControlDialog import PlaybackControlDialog
from ProgressDialog import ProgressDialog
from ProgressDialog import DualProgressDialog
from ProgressDialog import TripleProgressDialog
from ProgressDialog import QuadrupleProgressDialog
from MergeController import MergeController
from SplitController import SplitController
import gc
import fitz
from MarkdownParser import MarkdownParser
from markdown import markdown
from queue import Queue
from PDFUtility.PDFLogger import Logger
from TextToSpeech import TextToSpeech
from SettingsController import SettingsController
import ttkbootstrap as ttk
from ttkbootstrap import Style
from ttkbootstrap import Window
from SystemChecker import SystemChecker
from directory_scanner import PDFDirectoryScanner
import multiprocessing as mp
from PDFRenderer import PDFRendererController
from MDRenderer import show_readme
import pathlib
import tkinterdnd2
from White import White
from AnimatedProgressDialog import AnimatedProgressDialog
from search import SearchDialog
from editor.editor_window import EditorWindow
# TODO: Add Estimated time to completion for scan folder
# TODO: Add Rotation support
# TODO: Add support to add blank pages.
# TODO: Add Ability to read pdf's
# TODO: Add Feature to count pages and show how many pages are there in a pdf.
# FIXME: Fix White Page Removal

# TODO: Add warning if a file has the same name but is in two different locations during scanning.
# FIXME: Linux - Possibly Mac too - Module 'os' has no attribute 'startfile'
# Issue should now be solved: Windows (Possibly all others) - Index out of range error on remove selected. Not sure why this would be.
# This creates a cascade failure where all other buttons stop working because index is out of range.
# Additional problem detected with this. if after you clear selection and get this error, then choose clear selection. 
# Even if you make a new selection, the system no longer works correctly.
# TODO: Scan folder for pictures/Files to convert to convert to pdf.
# TODO: Add a Simplify/Summarize PDF feature that uses AI to summarize the content of the PDF.



class PDFUtility:
    def __init__(self, root):
        self.logger = Logger()
        self.shutdown_flag = threading.Event()
        self.logger.info("PDFUtility", "=================================================================")
        self.logger.info("PDFUtility"," EVENT: INIT")
        self.logger.info("PDFUtility","=================================================================")
        self.root = root
        self.style = Style(theme='darkly')
        self.pdf_files = []
        self.settingsController = SettingsController(self.root)
        self.settings = self.settingsController.load_settings()
        self.logger.info("PDFUtility","Settings loaded")
        self.system_checker = SystemChecker(root)
        self.logger.info("PDFUtility",f"Settings: {self.settings}")
        self.auto_clean_up()
        self.settings["current_cleanup_run_count"] = str(int(self.settings["current_cleanup_run_count"]) + 1)
        self.settingsController.save_runtime_settings_with_args(self.settings)
        # We're using direct tkinterdnd2 integration instead of DragDropHandler
        self.setup_ui()
        self.setup_key_bindings()
        self.logger.info("PDFUtility","UI setup complete")
        # Initialize ad system after UI setup
        # self.ad_system = AdSystem(self.ad_frame)
        self.logger.info("PDFUtility","Ad system initialized")
        self.tts = TextToSpeech(rate=int(self.settings["text_to_speech_rate"]), volume=float(self.settings["text_to_speech_volume"]))

    def open_playback_control(self):
        PlaybackControlDialog(self.root, self.tts, self)
    def search_ui(self):
        def _after_search(found_pdfs, found_images):
            # update list with any brand-new PDFs (avoid duplicates)
            self.pdf_files = list({*self.pdf_files, *found_pdfs})
            self.update_listbox()

            if found_images:
                if messagebox.askyesno(
                        "Convert images?",
                        f"Found {len(found_images)} image file(s).\n"
                        "Convert them to PDF now?"):
                    img_ctl = ImageControl(self.root, ())
                    img_ctl.set_pdf_files(self.pdf_files)
                    new_pdfs = img_ctl.convert_image_to_pdf(found_images)
                    # merge results back into master list
                    self.pdf_files.extend(new_pdfs)
                    self.update_listbox()

        SearchDialog(self.root, self.pdf_files, self.listbox, _after_search).show()
    def clean_up_Logs(self):
        self.logger.info("PDFUtility","Cleaning up logs")
        self.logger.delete_logs()

    def auto_clean_up(self):
        # implement settings check to see how many times since last cleanup the program has ran.
        if self.settings["current_cleanup_run_count"] >= self.settings["cleanup_run_count"]:
            self.logger.info("PDFUtility","Auto cleaning up logs")
            self.settings["current_cleanup_run_count"] = 0
            self.settingsController.save_runtime_settings_with_args(self.settings)
            self.clean_up_Logs()

    def merge_pdf_ui(self):
        """
        Merge selected PDF files into a single document.
        Updated implementation with proper multiprocessing integration.
        """
        if not self.listbox.curselection():
            messagebox.showinfo("Info", "Please select at least 2 PDF files to merge")
            return
        
        try:
            # Disable the merge button while operation is in progress
            if hasattr(self, 'merge_button'):
                self.merge_button.config(state="disabled")
            
            # Update status to show operation is starting
            if hasattr(self, 'status_label'):
                self.status_label.config(text="Starting PDF merge operation...")
            # Initialize the merge controller with the selection indices
            merge_controller = MergeController(self.root, self.listbox.curselection())
            # Set the selected indices for processing
            merge_controller.set_selected_indices(self.listbox.curselection())
            self.logger.info("PDFUtility", "Setting current PDF indices")
            # Set the actual PDF files list
            merge_controller.set_pdf_files(self.pdf_files)
            
            # Set status label for updates
            if hasattr(self, 'status_label'):
                merge_controller.set_status_label(self.status_label)
            
            # Start the merge process
            success = merge_controller.merge_pdf_ui()
            
            # Check if merge was started successfully
            if success:
                # Schedule function to check for completion and update file list
                self.root.after(500, self._check_merge_completion, merge_controller)
                
            else:
                # Re-enable merge button if operation didn't start
                if hasattr(self, 'merge_button'):
                    self.merge_button.config(state="normal")
                
        except Exception as e:
            # Handle any unexpected errors
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            self.logger.error("PDFUtility", f"Error in merge_pdf_ui (main): {str(e)}")
            
            # Re-enable merge button
            if hasattr(self, 'merge_button'):
                self.merge_button.config(state="normal")
            
    def _check_merge_completion(self, merge_controller):
        """
        Check if the merge operation is complete and update the UI.
        This is called periodically until the merge dialog closes.
        """
        # Check if merge dialog is still visible (operation in progress)
        merge_in_progress = False
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Toplevel) and widget.winfo_exists():
                title = widget.title()
                if "Merging PDFs" in title:
                    merge_in_progress = True
                    break
                
        if merge_in_progress:
            # Still in progress, check again later
            self.root.after(1000, self._check_merge_completion, merge_controller)
        else:
            # Merge completed or was cancelled, update file list
            new_files = merge_controller.get_completed_files()
            print(f"New files: {new_files}")
            
                 # Only add new files that aren't already in our list
            self.pdf_files = new_files     
            self.update_listbox()
            
            # Re-enable merge button
            if hasattr(self, 'merge_button'):
                self.merge_button.config(state="normal")

    # ---------------------------------------------------------------------------
#  SPLIT  –  companion to merge_pdf_ui()
# ---------------------------------------------------------------------------

    def split_pdf_ui(self):
        """
        Split one or more selected PDFs using the new SplitController.
        Mirrors the flow of merge_pdf_ui so the rest of the app behaves identically.
        """
        # Need at least one file selected
        if not self.listbox.curselection():
            messagebox.showinfo("Info", "Please select at least 1 PDF file to split")
            return

        try:
            # Disable the split button during the operation
            if hasattr(self, "split_button"):
                self.split_button.config(state="disabled")

            # UI feedback
            if hasattr(self, "status_label"):
                self.status_label.config(text="Starting PDF split operation...")

            # Instantiate the controller
            split_controller = SplitController(self.root, self.listbox.curselection())
            split_controller.set_selected_indices(self.listbox.curselection())
            split_controller.set_pdf_files(self.pdf_files)

            if hasattr(self, "status_label"):
                split_controller.set_status_label(self.status_label)

            # Launch the split-UI flow
            started = split_controller.split_pdf_ui()

            if started:
                # Poll until the dialog disappears
                self.root.after(
                    500, self._check_split_completion, split_controller
                )
            else:
                # Re-enable immediately if nothing actually started
                if hasattr(self, "split_button"):
                    self.split_button.config(state="normal")

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
            self.logger.error("PDFUtility", f"Error in split_pdf_ui: {e}")
            if hasattr(self, "split_button"):
                self.split_button.config(state="normal")


    def _check_split_completion(self, split_controller):
        """
        Periodically called until the DualProgressDialog titled
        'Splitting PDFs' is closed, signalling completion or cancellation.
        """
        split_in_progress = any(
            isinstance(w, tk.Toplevel) and w.winfo_exists() and w.title().startswith("Splitting PDFs")
            for w in self.root.winfo_children()
        )

        if split_in_progress:
            # Still running – schedule next check
            self.root.after(1000, self._check_split_completion, split_controller)
            return

        # Finished (or cancelled) – refresh file list
        new_files = split_controller.get_completed_files()
        self.pdf_files = new_files
        self.update_listbox()

        # Re-enable the split button
        if hasattr(self, "split_button"):
            self.split_button.config(state="normal")


    def extract_text_from_pdf(self, pdf_file):
        # Implement text extraction from PDF by pages
        self.logger.info("PDFUtility","Extracting text from PDF")
        doc = fitz.open(pdf_file)
        pages = []
        for page in doc:
            pages.append(page.get_text())
        self.logger.info("PDFUtility", f"Extracted text from PDF, PDF has {len(pages)} pages")
        doc.close()
        return pages



    def extract_title(self, pdf_reader):
        """
        Attempts to extract a title from the PDF metadata or first page.
        """
        self.logger.info("PDFUtility","Extracting title")
        title = getattr(pdf_reader.metadata, 'title', None)
        if not title and len(pdf_reader.pages) > 0:
            text = pdf_reader.pages[0].extract_text()
            if text:
                title = text.split('\n')[0].strip()[:50]
                self.logger.info("PDFUtility",f"Title extracted: {title}")
        return title if title else "Untitled"

    def remove_white_ui(self):
        """Start the ‘remove blank pages’ workflow via the White controller."""
        if not self.listbox.curselection():
            messagebox.showinfo("Info", "Please select at least 1 PDF file to clean")
            return

        try:
            self.remove_white_button.config(state="disabled")
            if hasattr(self, "status_label"):
                self.status_label.config(text="Scanning for blank pages…")

            # Convert listbox indices → real paths
            sel_files = [self.pdf_files[i] for i in self.listbox.curselection()]

            # Instantiate controller
            white_ctl = White(self.root, sel_files)
            white_ctl.set_pdf_files(self.pdf_files)          # give full list
            if hasattr(self, "status_label"):
                white_ctl.set_status_label(self.status_label)

            # run in background so GUI stays live
            threading.Thread(target=white_ctl.remove_white_page, daemon=True).start()

            # poll until the dual-progress dialog disappears
            self.root.after(500, self._check_white_completion, white_ctl)

        except Exception as e:
            self.logger.error("PDFUtility", f"Error in remove_white_ui: {e}")
            messagebox.showerror("Error", str(e))
            self.remove_white_button.config(state="normal")
    

    def _check_white_completion(self, white_ctl):
        """
        Called every ½ s until *Scanning PDF Files* / *Removing White Pages*
        dialogs are closed → then refresh listbox & re-enable button.
        """
        still_open = any(
            isinstance(w, tk.Toplevel) and w.winfo_exists() and
            w.title().startswith(("Scanning PDF Files", "Removing White Pages"))
            for w in self.root.winfo_children()
        )

        if still_open:
            self.root.after(1000, self._check_white_completion, white_ctl)
            return

        # update list with any newly-created *_no_whitespace.pdf*
        self.pdf_files = white_ctl.get_completed_files()
        self.update_listbox()
        self.remove_white_button.config(state="normal")

    def repair_pdf(self, input_pdf, output_pdf=None):
        """
        Attempts to repair a PDF file using PyMuPDF.
        Addresses common issues like corrupted xref tables, stream errors, and broken pages.

        Args:
            input_pdf: Path to the potentially damaged PDF
            output_pdf: Path to save the repaired PDF (if None, uses input name + "_repaired.pdf")

        Returns:
            Path to the repaired PDF file
        """
        self.logger.info("PDFUtility","Repairing PDF")
        # Create default output path if not provided
        if output_pdf is None:
            base_name = os.path.splitext(input_pdf)[0]
            output_pdf = f"{base_name}_repaired.pdf"
            self.logger.debug("PDFUtility",f"Output PDF: {output_pdf}")

        try:
            self.logger.info("PDFUtility","Opening PDF to determine if repair is needed")
            # Open the PDF with repair mode enabled
            doc = fitz.open(input_pdf)

            # Check if the document needs repair
            needs_repair = False

            # Get document metadata and check for errors
            try:
                self.logger.info("PDFUtility","Reading metadata")
                metadata = doc.metadata
            except:
                self.logger.exception("PDFUtility","Error reading metadata, document needs repair")
                needs_repair = True

            # Try to access each page to find broken ones
            broken_pages = []
            self.logger.info("PDFUtility","Checking each page for errors")
            for page_num in range(len(doc)):
                try:
                    page = doc[page_num]
                    # Try to access page content to verify it works
                    _ = page.get_text("dict")
                    _ = page.get_drawings()
                    self.logger.info("PDFUtility",f"Page {page_num + 1} appears valid")
                except:
                    self.logger.exception("PDFUtility",f"Error accessing page {page_num + 1}, page is broken")
                    broken_pages.append(page_num)
                    needs_repair = True

            self.logger.info("PDFUtility","Creating new clean versions of the document")
            # If document needs repair, create a clean version
            if needs_repair or broken_pages:
                # Create a new document
                new_doc = fitz.open()

                # Copy each valid page to the new document
                for page_num in range(len(doc)):
                    if page_num not in broken_pages:
                        try:
                            self.logger.info("PDFUtility",f"Copying page {page_num + 1} to new document")
                            new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
                        except:
                            self.logger.exception("PDFUtility",f"Error copying page {page_num + 1}, skipping")
                            # Skip pages that can't be copied
                            pass
                        
                # Save the repaired document
                self.logger.info("PDFUtility","Saving repaired document")
                new_doc.save(output_pdf, garbage=4, clean=True, deflate=True)
                new_doc.close()
            else:
                self.logger.info("PDFUtility","Document is clean, no repair needed... applying optimization options")
                # If no issues found, save with optimization options
                doc.save(output_pdf, garbage=4, clean=True, deflate=True)

            # Close the original document
            doc.close()

            self.logger.info("PDFUtility","PDF repaired successfully")
            # Verify the repaired document can be opened
            check_doc = fitz.open(output_pdf)
            page_count = len(check_doc)
            self.logger.info("PDFUtility",f"Repaired PDF has {page_count} pages")
            check_doc.close()

            return output_pdf

        except Exception as e:
            # Clean up on error
            gc.collect()
            self.logger.error("PDFUtility",f"Error repairing PDF: {str(e)}")
            raise Exception(f"Error repairing PDF: {str(e)}")


    def split_pdf(self, input_pdf, output_folder, progress_callback=None, batch_size=None):
        """
        Splits a PDF document into separate PDF files for each page using PyMuPDF.
        Returns a list of created files.

        Args:
            input_pdf: Path to the input PDF
            output_folder: Folder to save split pages
            progress_callback: Function to call with page progress (page_num, total_pages)
            batch_size: Not used in PyMuPDF version but kept for compatibility
        """
        # Ensure output folder exists
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            self.logger.info("PDFUtility",f"Created output folder: {output_folder}")

        created_files = []

        try:
            self.logger.info("PDFUtility","Opening PDF to determine total pages")
            # Open the PDF
            doc = fitz.open(input_pdf)
            total_pages = len(doc)

            # Get document title for filenames
            self.logger.info("PDFUtility","Extracting PDF title")
            pdf_title = doc.metadata.get("title", "")
            if not pdf_title:
                # Try to extract from first page text
                self.logger.info("PDFUtility","Title not found in metadata, extracting from first page")
                if total_pages > 0:
                    self.logger.info("PDFUtility","Extracting text from first page")
                    text = doc[0].get_text()
                    if text:
                        self.logger.info("PDFUtility","Text found, extracting title")
                        lines = text.split('\n')
                        if lines:
                            self.logger.info("PDFUtility","Title extracted")
                            pdf_title = lines[0].strip()[:50]

            # Use filename if we still don't have a title
            if not pdf_title:
                self.logger.info("PDFUtility","Title not found, using filename")
                pdf_title = os.path.splitext(os.path.basename(input_pdf))[0]

            # Replace invalid filename characters
            for char in ['<', '>', ':', '"', '/', '\\', '|', '?', '*']:
                self.logger.info("PDFUtility",f"Replacing invalid characters for filename: {char}")
                pdf_title = pdf_title.replace(char, '_')

            # Process each page
            for page_num in range(total_pages):
                self.logger.info("PDFUtility",f"Processing page {page_num + 1}/{total_pages}")
                # Report progress
                if progress_callback:
                    self.logger.info("PDFUtility",f"Progress callback: {page_num}/{total_pages}")
                    progress_callback(page_num, total_pages)

                self.logger.info("PDFUtility","Creating new document for page")
                # Create a new document for this page
                new_doc = fitz.open()

                # Copy the page
                self.logger.info("PDFUtility",f"Copying page {page_num + 1} to new document")
                new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

                # Save as a separate file
                self.logger.info("PDFUtility","Saving new document")
                output_filename = os.path.join(output_folder, f"{pdf_title}_Page_{page_num + 1}.pdf")
                new_doc.save(output_filename)
                new_doc.close()
                self.logger.info("PDFUtility",f"Page saved: {output_filename}, adding to list")
                created_files.append(output_filename)

            self.logger.info("PDFUtility","All pages processed, closing document")
            # Clean up
            doc.close()

            # Final progress update
            if progress_callback and total_pages > 0:
                self.logger.info("PDFUtility","Final progress callback")
                progress_callback(total_pages, total_pages)

            return created_files

        except Exception as e:
            # Clean up on error
            gc.collect()
            self.logger.error("PDFUtility",f"Error splitting PDF: {str(e)}")
            raise Exception(f"Error splitting PDF: {str(e)}")

    def view_help(self):
        readme = pathlib.Path(__file__).with_name("README.md")
        self.editor = EditorWindow(self.root)
        self.editor.render_readme_file(readme)


        #show_readme(self.root, str(readme))
    
    def apply_theme(self):
        self.logger.info("PDFUtility","Applying theme")
        if self.theme == "dark":
            self.style.theme_use("darkly")
        else:
            self.style.theme_use("default")

    def add_files(self):
        self.logger.info("PDFUtility","Adding files")
        """Add PDF files with progress bar and duplicate prevention"""
        new_files = filedialog.askopenfilenames(title="Select PDF files to add", filetypes=[("PDF Files", "*.pdf")])
        if not new_files or len(new_files) == 0:
            self.logger.info("PDFUtility","No files selected")
            return

        # If only a few files, add them directly without progress bar
        if len(new_files) < 5:
            self.logger.info("PDFUtility","Adding files directly (No Progress Bar)")
            self._add_files_direct(new_files)
            return

        # Create progress dialog for larger file sets
        progress = ProgressDialog(
            self.root, 
            title="Adding PDF Files", 
            message=f"Adding {len(new_files)} PDF files..."
        )
        self.update_buttons()
        # Store results
        result = {"added": [], "skipped": []}

        def process_files():
            """Process files in background thread"""
            self.logger.info("PDFUtility","Processing files in background thread")
            try:
                total_files = len(new_files)
                self.logger.info("PDFUtility",f"Processing {total_files} files")
                current_files = [os.path.normpath(f) for f in self.pdf_files]

                for i, file_path in enumerate(new_files):
                    # Update progress
                    progress.update_progress(i, total_files)
                    self.logger.info("PDFUtility",f"Processing: {os.path.basename(file_path)}")
                    progress.update_status(f"Processing: {os.path.basename(file_path)}")

                    # Normalize path for comparison
                    normalized_path = os.path.normpath(file_path)

                    # Check if file already exists in the list
                    if normalized_path in current_files:
                        self.logger.info("PDFUtility",f"Skipping duplicate file: {file_path}")
                        result["skipped"].append(file_path)
                    else:
                        result["added"].append(file_path)
                        self.logger.info("PDFUtility",f"Added file: {file_path}")
                        current_files.append(normalized_path)  # Add to our check list

                # Final update
                progress.update_progress(total_files, total_files)
                progress.update_message("Processing complete!")
                progress.update_status("Finalizing...")

                # Schedule UI update on main thread
                self.root.after(100, complete_operation)

            except Exception as e:
                self.logger.exception("PDFUtility",f"Error adding files: {str(e)}")
                self.root.after(100, lambda: complete_operation(error=str(e)))

        def complete_operation(error=None):
            """Complete the operation on the main thread"""
            # Close progress dialog
            self.logger.info("PDFUtility","Closing progress dialog")
            progress.close()

            if error:
                self.logger.error("PDFUtility",f"Error adding files: {error}")
                messagebox.showerror("Error", f"Error adding files: {error}")
                return

            # Add files to list
            if result["added"]:
                self.logger.info("PDFUtility",f"Adding {len(result['added'])} files to list")
                self.pdf_files.extend(result["added"])
                self.update_listbox()

            # Show status message
            if result["added"] and result["skipped"]:
                self.logger.info("PDFUtility",f"Added {len(result['added'])} files, skipped {len(result['skipped'])} duplicates")
                self.status_label.config(text=f"Added {len(result['added'])} file(s), skipped {len(result['skipped'])} duplicate(s)")
            elif result["added"]:
                self.status_label.config(text=f"Added {len(result['added'])} file(s)")
                self.logger.info("PDFUtility",f"Added {len(result['added'])} files")
            elif result["skipped"]:
                self.status_label.config(text=f"Skipped {len(result['skipped'])} duplicate file(s)")
                self.logger.info("PDFUtility",f"Skipped {len(result['skipped'])} duplicates")

        # Start processing in background thread
        threading.Thread(target=process_files, daemon=True).start()

    def _add_files_direct(self, new_files):
        """Add a small number of files directly without a progress bar"""
        self.logger.info("PDFUtility","Adding files directly (NO Progress Bar)")
        # Check for duplicates
        added_count = 0
        skipped_count = 0

        for file_path in new_files:
            # Normalize path for comparison
            normalized_path = os.path.normpath(file_path)

            # Check if file already exists in the list
            if normalized_path in [os.path.normpath(f) for f in self.pdf_files]:
                skipped_count += 1
                self.logger.info("PDFUtility",f"Skipping duplicate file: {file_path}")
                continue

            # If not a duplicate, add to list
            self.pdf_files.append(normalized_path)
            self.logger.info("PDFUtility",f"Added file: {file_path}")
            added_count += 1

            self.logger.info("PDFUtility",f"Added {added_count} files, skipped {skipped_count} duplicates")

        # Update the listbox
        self.update_listbox()

        # Show status message
        if added_count > 0 and skipped_count > 0:
            self.status_label.config(text=f"Added {added_count} file(s), skipped {skipped_count} duplicate(s)")
        elif added_count > 0:
            self.status_label.config(text=f"Added {added_count} file(s)")
        elif skipped_count > 0:
            self.status_label.config(text=f"Skipped {skipped_count} duplicate file(s)")
        self.logger.info("PDFUtility",f"Added {added_count} files, skipped {skipped_count} duplicates")

    def remove_file(self):
        selected = self.listbox.curselection()
        if not selected:
            self.logger.info("PDFUtility", "No files selected for removal")
            return

        for index in sorted(selected, reverse=True):
            self.logger.info("PDFUtility", f"Removing file: {self.pdf_files[index]} from UI Listbox")
            del self.pdf_files[index]

        self.update_listbox()
        self.logger.info("PDFUtility", "File(s) removed successfully")

    def remove_files(self, files_to_remove):
        """Remove specified files from the listbox and update the display"""
        for file in files_to_remove:
            if file in self.pdf_files:
                self.pdf_files.remove(file)
                self.logger.info("PDFUtility",f"Removed file: {file} from UI Listbox")
        self.update_listbox()

    
    def duplicate_file(self):
        """Create a duplicate of the selected PDF file with progress bar"""
        selected = self.listbox.curselection()
        if not selected:
            self.logger.info("PDFUtility","No files selected")
            return
        # Create progress dialog
        progress = ProgressDialog(
            self.root, 
            title="Duplicating PDFs", 
            message=f"Duplicating {len(selected)} PDF file(s)..."
        )

        # Store results
        result = {"new_files": [], "errors": []}
        self.logger.info("PDFUtility",f"Duplicating {len(selected)} files")

        def process_files():
            """Process files in background thread"""
            try:
                total_files = len(selected)

                for i, index in enumerate(selected):
                    original_path = self.pdf_files[index]

                    # Update progress
                    progress.update_progress(i, total_files)
                    progress.update_status(f"Processing: {os.path.basename(original_path)}")

                    try:
                        # Get duplicate name
                        new_path, new_filename = self.get_duplicate_name(original_path)

                        # Create output directory if it doesn't exist
                        output_dir = os.path.dirname(new_path)
                        os.makedirs(output_dir, exist_ok=True)

                        # Copy the file
                        shutil.copy2(original_path, new_path)
                        result["new_files"].append((new_path, new_filename))
                        self.logger.info("PDFUtility",f"Duplicated file: {original_path} -> {new_path}")
                    except Exception as e:
                        result["errors"].append((original_path, str(e)))
                        self.logger.error("PDFUtility",f"Error duplicating file: {original_path}: {str(e)}")

                # Final update
                progress.update_progress(total_files, total_files)
                progress.update_message("Duplication complete!")
                progress.update_status("Finalizing...")

                # Schedule UI update on main thread
                self.root.after(100, complete_operation)

            except Exception as e:
                result["errors"].append(("General error", str(e)))
                self.logger.error("PDFUtility",f"Error duplicating files: {str(e)}")
                self.root.after(100, complete_operation)

        def complete_operation():
            """Complete the operation on the main thread"""
            # Close progress dialog
            progress.close()

            # Update file list
            if result["new_files"]:
                for new_path, _ in result["new_files"]:
                    self.pdf_files.append(new_path)
                    self.logger.info("PDFUtility",f"Added duplicate file: {new_path}")
                self.update_listbox()

            # Show result
            if result["errors"]:
                error_msg = "\n".join([f"{os.path.basename(f)}: {e}" for f, e in result["errors"]])
                messagebox.showerror("Error", f"Errors occurred during duplication:\n{error_msg}")
                self.logger.info("PDFUtility",f"Errors occurred during duplication: {error_msg}")
            elif result["new_files"]:
                if len(result["new_files"]) == 1:
                    self.status_label.config(text=f"Created duplicate: {result['new_files'][0][1]}")
                    self.logger.info("PDFUtility",f"Created duplicate: {result['new_files'][0][1]}")
                else:
                    self.status_label.config(text=f"Created {len(result['new_files'])} duplicates")
                    self.logger.info("PDFUtility",f"Created {len(result['new_files'])} duplicates")
        # Start processing in background thread
        threading.Thread(target=process_files, daemon=True).start()
    
    def get_duplicate_name(self, original_path):
        """
        Generate a new filename for a duplicate file.
        Returns the full new path and just the filename portion.

        Args:
            original_path (str): Original file path

        Returns:
            tuple: (new_full_path, new_filename)
        """
        self.logger.info("PDFUtility",f"Getting duplicate name for: {original_path}")
        # Get the original filename without path
        original_filename = os.path.basename(original_path)
        base, ext = os.path.splitext(original_filename)

        # Generate new filename 

        # Get output directory from settings or use default
        output_dir = self.settings.get("output_directory", os.getcwd())
        self.logger.info("PDFUtility",f"Output directory: {output_dir}")
        # Start counter for copy number
        counter = 1
        while True:
            new_filename = f"{base}_copy{counter}{ext}"
            new_full_path = os.path.join(output_dir, new_filename)

            if not os.path.exists(new_full_path):
                self.logger.info("PDFUtility",f"File does not exist: {new_full_path} + {new_filename}")
                return new_full_path, new_filename
            self.logger.info("PDFUtility",f"File already exists: {new_full_path} + {new_filename}")
            counter += 1

    
    def rename_pdf(self):
        """Rename the selected PDF file"""
        self.logger.info("PDFUtility","Renaming PDF...")
        selected = self.listbox.curselection()
        if not selected:
            self.logger.info("PDFUtility","No PDF selected for renaming")
            return
        
        old_path = self.pdf_files[selected[0]]
        old_dir = os.path.dirname(old_path)
        old_name = os.path.basename(old_path)
        self.logger.info("PDFUtility",f"Selected PDF for renaming: {old_path}")
        self.logger.info("PDFUtility",f"Old name: {old_name}")
        self.logger.info("PDFUtility",f"Old directory: {old_dir}")
        # Create dialog for new name
        dialog = tk.Toplevel(self.root)
        dialog.title("Rename PDF")
        dialog.geometry("400x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="Enter new name:").pack(pady=10)
        entry = tk.Entry(dialog, width=40)
        entry.insert(0, old_name)
        entry.pack(pady=10)
        entry.select_range(0, len(old_name)-4)  # Select everything except .pdf
        
        def do_rename():
            new_name = entry.get()
            self.logger.info("PDFUtility",f"New name entered: {new_name}")
            if not new_name.lower().endswith('.pdf'):
                new_name += '.pdf'
                self.logger.info("PDFUtility",f"Appending .pdf to new name: {new_name}")
            new_path = os.path.join(old_dir, new_name)
            self.logger.info("PDFUtility",f"New path: {new_path}")   
            try:
                os.rename(old_path, new_path)
                self.remove_files([old_path])
                self.logger.info("PDFUtility",f"PDF renamed from {old_path} to {new_path}")
                self.logger.info("PDFUtility",f"PDF removed from listbox")
                self.pdf_files.append(new_path)
                self.update_listbox()
                dialog.destroy()
                self.status_label.config(text=f"Renamed: {old_name} → {new_name}")
            except OSError as e:
                messagebox.showerror("Error", f"Could not rename file: {str(e)}")
                self.logger.error("PDFUtility",f"Error renaming PDF: {str(e)}")
                dialog.lift()
        
        ttk.Button(dialog, text="Rename", command=do_rename).pack(pady=10)
        
        # Center the dialog on the main window
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - dialog.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")

    def delete_pdf(self, Event=None):
        """Delete the selected PDF files with progress bar"""
        selected = self.listbox.curselection()
        if not selected:
            self.logger.info("PDFUtility","No PDF selected for deletion")
            return

        files_to_delete = [self.pdf_files[idx] for idx in selected]
        self.logger.info("PDFUtility",f"Deleting {len(files_to_delete)} PDF file(s)")
        # Confirm deletion
        if len(files_to_delete) == 1:
            message = f"Are you sure you want to delete {os.path.basename(files_to_delete[0])}?"
        else:
            message = f"Are you sure you want to delete {len(files_to_delete)} files?"

        if not messagebox.askyesno("Confirm Delete", message):
            self.logger.info("PDFUtility","Deletion cancelled")
            return

        # Create progress dialog
        progress = ProgressDialog(
            self.root, 
            title="Deleting PDFs", 
            message=f"Deleting {len(files_to_delete)} PDF file(s)..."
        )

        # Store results
        result = {"deleted": [], "failed": []}
        self.logger.debug("PDFUtility",f"Deleting {len(files_to_delete)} files")
        self.logger.debug("PDFUtility",f"Result: {result}")
        def delete_process():
            """Delete files in background thread"""
            try:
                total_files = len(files_to_delete)
                self.logger.info("PDFUtility",f"Deleting {total_files} files")
                for i, file_path in enumerate(files_to_delete):
                    # Update progress
                    progress.update_progress(i, total_files)
                    progress.update_status(f"Deleting: {os.path.basename(file_path)}")

                    try:
                        os.remove(file_path)
                        result["deleted"].append(file_path)
                        self.logger.info("PDFUtility",f"Deleted {file_path}")
                    except Exception as e:
                        result["failed"].append((file_path, str(e)))
                        self.logger.error("PDFUtility","Failed to delete {file_path}: {str(e)}")

                # Final update
                progress.update_progress(total_files, total_files)
                progress.update_message("Deletion complete!")
                progress.update_status("Finalizing...")

                # Schedule UI update on main thread
                self.root.after(100, complete_operation)

            except Exception as e:
                result["failed"].append(("General error", str(e)))
                self.logger.error("PDFUtility","General error: {str(e)}")
                self.root.after(100, complete_operation)

        def complete_operation():
            """Complete the operation on the main thread"""
            # Close progress dialog
            progress.close()

            # Remove from list and update display
            self.remove_files(files_to_delete)
            self.logger.info("PDFUtility",f"Deleted {len(files_to_delete)} files from listbox")
            # Show status
            if not result["failed"]:
                self.status_label.config(text=f"Deleted {len(result['deleted'])} file(s)")
            else:
                error_msg = "\n".join(f"{os.path.basename(f)}: {e}" for f, e in result["failed"])
                messagebox.showerror("PDFUtility", f"Failed to delete some files:\n{error_msg}")

        # Start processing in background thread
        threading.Thread(target=delete_process, daemon=True).start()

    
    def view_experimental(self):
        """Open the experimental features dialog"""
        self.logger.info("PDFUtility","Opening experimental features dialog")
        self.editor = EditorWindow(self.root)
        self.spotter_thread = threading.Thread(
            target=self.watch_for_files_in_editor, 
            daemon=True
        )
        self.spotter_thread.start()
        selection = self.listbox.curselection()

        if selection:
            self.editor.set_external_file_list_selection(selection, self.pdf_files)
        else:
            if len(self.pdf_files) > 0:
                self.editor.set_external_file_list(self.pdf_files)

    def watch_for_files_in_editor(self):
        while True:
            if not self.editor.is_alive:
                self.spotter_thread.join()
            if self.editor.get_has_files(): 
                files = self.editor.get_editor_files()
                for file in files:
                    if file not in self.pdf_files:
                        self.logger.info("PDFUtility",f"Adding new file from editor: {file}")
                        self.pdf_files.append(file)
                        self.update_listbox()
            time.sleep(1)

    def copy_file_path(self):
        """Copy the selected file paths to clipboard"""
        self.logger.info("PDFUtility","Copying file paths to clipboard")
        selected = self.listbox.curselection()
        if not selected:
            messagebox.showinfo("Info", "Please select at least one PDF file to copy")
            self.logger.info("PDFUtility","No files selected for copying")
            return

        # Get selected file paths
        file_paths = [self.pdf_files[i] for i in selected]
        if not file_paths:
            messagebox.showinfo("Info", "No files selected for copying")
            self.logger.info("PDFUtility","No files selected for copying")
            return

        # Join paths with newline
        paths_str = "\n".join(file_paths)
        self.root.clipboard_clear()
        self.root.clipboard_append(paths_str)
        self.logger.info("PDFUtility","File paths copied to clipboard")

    def copy_file(self):
        """Copy the selected file to system clipboard for pasting in file managers"""
        self.logger.info("PDFUtility", "Copying file to system clipboard")
        selected = self.listbox.curselection()
        if not selected:
            messagebox.showinfo("Info", "Please select exactly one PDF file to copy")
            self.logger.info("PDFUtility", "No files selected for copying")
            return
        
        if len(selected) > 1:
            messagebox.showinfo("Info", "Please select only one file to copy")
            self.logger.info("PDFUtility", "Multiple files selected for copying")
            return

        # Get selected file path
        file_path = self.pdf_files[selected[0]]
        if not os.path.exists(file_path):
            messagebox.showerror("Error", f"File not found: {file_path}")
            self.logger.error("PDFUtility", f"File not found: {file_path}")
            return

        try:
            # Platform-specific file copying to clipboard
            if sys.platform.startswith('win'):
                # Windows: Use PowerShell to copy file to clipboard
                import subprocess
                powershell_cmd = f'Set-Clipboard -Path "{file_path}"'
                subprocess.run(['powershell', '-Command', powershell_cmd], check=True)
                messagebox.showinfo("Success", f"File copied to clipboard:\n{os.path.basename(file_path)}")
                self.logger.info("PDFUtility", f"File copied to clipboard: {file_path}")
            
            elif sys.platform.startswith('darwin'):
                # macOS: Use osascript to copy file to clipboard
                import subprocess
                apple_script = f'''
                tell application "Finder"
                    set the clipboard to (POSIX file "{file_path}")
                end tell
                '''
                subprocess.run(['osascript', '-e', apple_script], check=True)
                messagebox.showinfo("Success", f"File copied to clipboard:\n{os.path.basename(file_path)}")
                self.logger.info("PDFUtility", f"File copied to clipboard: {file_path}")
            
            else:
                # Linux: Copy file path to clipboard as fallback
                self.root.clipboard_clear()
                self.root.clipboard_append(file_path)
                messagebox.showinfo("Info", f"File path copied to clipboard:\n{file_path}\n\nNote: On Linux, only the file path is copied to clipboard.")
                self.logger.info("PDFUtility", f"File path copied to clipboard (Linux): {file_path}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy file to clipboard:\n{str(e)}")
            self.logger.error("PDFUtility", f"Failed to copy file to clipboard: {str(e)}")

    def paste_files(self):
        """Paste files from clipboard - supports file paths and file URIs"""
        self.logger.info("PDFUtility", "Attempting to paste files from clipboard")
        
        try:
            # Get clipboard content
            clipboard_content = self.root.clipboard_get()
            if not clipboard_content.strip():
                messagebox.showinfo("Info", "Clipboard is empty")
                self.logger.info("PDFUtility", "Clipboard is empty")
                return
            
            # Parse clipboard content for file paths
            lines = clipboard_content.strip().split('\n')
            valid_files = []
            invalid_paths = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Handle file:// URIs
                if line.startswith('file://'):
                    from urllib.parse import urlparse, unquote
                    parsed = urlparse(line)
                    file_path = unquote(parsed.path)
                    # On Windows, remove leading slash from /C:/path format
                    if sys.platform.startswith('win') and file_path.startswith('/') and len(file_path) > 1 and file_path[2] == ':':
                        file_path = file_path[1:]
                else:
                    file_path = line
                
                # Normalize path
                file_path = os.path.normpath(file_path)
                
                # Check if file exists and is a PDF
                if os.path.exists(file_path) and os.path.isfile(file_path):
                    if file_path.lower().endswith('.pdf'):
                        if file_path not in self.pdf_files:
                            valid_files.append(file_path)
                        else:
                            self.logger.info("PDFUtility", f"File already in list: {file_path}")
                    else:
                        invalid_paths.append(f"{file_path} (not a PDF)")
                else:
                    invalid_paths.append(f"{file_path} (file not found)")
            
            # Add valid files to the list
            if valid_files:
                for file_path in valid_files:
                    self.pdf_files.append(file_path)
                    self.logger.info("PDFUtility", f"Added file from clipboard: {file_path}")
                
                self.update_listbox()
                
                success_msg = f"Successfully added {len(valid_files)} file(s) from clipboard"
                if invalid_paths:
                    success_msg += f"\n\nSkipped {len(invalid_paths)} invalid path(s):\n" + "\n".join(invalid_paths[:5])
                    if len(invalid_paths) > 5:
                        success_msg += f"\n... and {len(invalid_paths) - 5} more"
                
                messagebox.showinfo("Success", success_msg)
                self.logger.info("PDFUtility", f"Successfully pasted {len(valid_files)} files from clipboard")
            
            else:
                if invalid_paths:
                    error_msg = "No valid PDF files found in clipboard.\n\nInvalid paths:\n" + "\n".join(invalid_paths[:10])
                    if len(invalid_paths) > 10:
                        error_msg += f"\n... and {len(invalid_paths) - 10} more"
                else:
                    error_msg = "No valid file paths found in clipboard.\n\nSupported formats:\n- Full file paths\n- file:// URIs\n- Multiple paths separated by newlines"
                
                messagebox.showinfo("Info", error_msg)
                self.logger.info("PDFUtility", "No valid files found in clipboard")
        
        except tk.TclError:
            messagebox.showinfo("Info", "Unable to read from clipboard")
            self.logger.info("PDFUtility", "Unable to read from clipboard")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to paste files from clipboard:\n{str(e)}")
            self.logger.error("PDFUtility", f"Failed to paste files from clipboard: {str(e)}")


    def open_filepath(self):
        """Open the selected file path in the default application (cross-platform)"""
        self.logger.info("PDFUtility", "Opening file path in default application")
        selected = self.listbox.curselection()
        if not selected:
            messagebox.showinfo("Info", "Please select at least one PDF file to open")
            self.logger.info("PDFUtility", "No files selected for opening")
            return

        # Get selected file paths
        file_paths = [self.pdf_files[i] for i in selected]
        if not file_paths:
            messagebox.showinfo("Info", "No files selected for opening")
            self.logger.info("PDFUtility", "No files selected for opening")
            return

        # Open file path in default application
        for file_path in file_paths:
            try:
                self.logger.info("PDFUtility", f"Opening file: {file_path}")
                if sys.platform.startswith('win'):
                    os.startfile(file_path)
                elif sys.platform == 'darwin':
                    subprocess.call(['open', file_path])
                else:
                    subprocess.call(['xdg-open', file_path])
            except Exception as e:
                self.logger.error("PDFUtility", f"Error opening file {file_path}: {str(e)}")
                messagebox.showerror("Error", f"Could not open file {file_path}: {str(e)}")

    def get_selection(self):
        """Get selected files from listbox"""
        self.logger.info("PDFUtility","Getting selected files")
        return [self.pdf_files[i] for i in self.listbox.curselection()]
     
    def repair_pdf_ui(self):
        """Repair selected PDF files with progress tracking"""
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            messagebox.showinfo("Info", "Please select PDF files to repair")
            self.logger.info("PDFUtility","No PDF files selected for repair")
            return

        # Create progress dialog
        progress = ProgressDialog(
            self.root, 
            title="Repairing PDFs", 
            message=f"Preparing to repair {len(selected_indices)} PDF file(s)..."
        )

        # Store results
        result = {
            "repaired_files": [], 
            "errors": [], 
            "cancelled": False
        }

        def process_files():
            """Process files in background thread"""
            self.logger.info("PDFUtility","Processing files in background thread")
            try:
                total_files = len(selected_indices)
                self.logger.info("PDFUtility",f"Processing {total_files} files")
                for i, index in enumerate(selected_indices):
                    # Check for cancellation
                    if progress.is_cancelled():
                        result["cancelled"] = True
                        self.logger.info("PDFUtility","Operation cancelled")
                        self.root.after(100, complete_operation)
                        return

                    pdf_file = self.pdf_files[index]
                    file_name = os.path.basename(pdf_file)
                    self.logger.info("PDFUtility",f"Processing file {i+1}/{total_files}: {file_name}")

                    # Update progress
                    progress.update_progress(i, total_files)
                    progress.update_status(f"Repairing: {file_name}")
                    progress.update_message(f"Repairing file {i+1} of {total_files}")

                    try:
                        # Get repair directory - use same folder as original
                        repair_dir = os.path.dirname(pdf_file)
                        if not repair_dir:
                            repair_dir = os.path.dirname(os.path.abspath(pdf_file))
                        self.logger.info("PDFUtility",f"Repair directory: {repair_dir}")

                        # Create output filename
                        base_name, ext = os.path.splitext(file_name)
                        repaired_file = os.path.join(repair_dir, f"{base_name}_repaired{ext}")
                        self.logger.info("PDFUtility",f"Repaired file filename: {repaired_file}")

                        # Repair the PDF
                        output_path = self.repair_pdf(pdf_file, repaired_file)
                        result["repaired_files"].append(output_path)
                        self.logger.info("PDFUtility",f"Repaired file: {output_path}")

                    except Exception as e:
                        result["errors"].append((pdf_file, str(e)))
                        self.logger.error("PDFUtility",f"Error repairing file: {pdf_file}: {str(e)}")

                # Final update
                if not result["cancelled"]:
                    progress.update_progress(total_files, total_files)
                    progress.update_message("Repair complete!")
                    progress.update_status("Finalizing...")
                    self.logger.info("PDFUtility","Repair complete!")

                # Schedule UI update on main thread
                self.root.after(100, complete_operation)

            except Exception as e:
                result["errors"].append(("General error", str(e)))
                self.logger.error("PDFUtility",f"Error processing files: {str(e)}")
                self.root.after(100, complete_operation)

        def complete_operation():
            """Complete the operation on the main thread"""
            # Close progress dialog
            progress.close()

            # Handle cancellation
            if result["cancelled"]:
                self.status_label.config(text="Repair operation cancelled")
                self.logger.info("PDFUtility","Repair operation cancelled")
                return

            # Update file list with repaired files
            if result["repaired_files"]:
                self.pdf_files.extend(result["repaired_files"])
                self.logger.info("PDFUtility",f"Added {len(result['repaired_files'])} repaired files to list")
                self.update_listbox()

            # Show result
            if result["errors"]:
                error_msg = "\n".join([f"{os.path.basename(f)}: {e}" for f, e in result["errors"]])
                self.logger.warning("PDFUtility",f"Errors occurred during repair:\n{error_msg}")
                messagebox.showerror("PDFUtility", f"Errors occurred during repair:\n{error_msg}")

            if len(result["repaired_files"]) > 0:
                self.status_label.config(text=f"Repaired {len(result['repaired_files'])} PDF file(s)")
                self.logger.info("PDFUtility",f"Repaired {len(result['repaired_files'])} PDF file(s)")
            else:
                self.status_label.config(text="No files were successfully repaired")
                self.logger.warning("PDFUtility","No files were successfully repaired")

        # Start processing in background thread
        Thread(target=process_files, daemon=True).start()

    def update_listbox(self):
        self.logger.info("PDFUtility", "Updating listbox")
        # Only add new items
        current_size = self.listbox.size()
        if current_size < len(self.pdf_files):
            for f in self.pdf_files[current_size:]:
                self.listbox.insert(tk.END, f)
        elif current_size > len(self.pdf_files):
            # If files were removed, clear and repopulate
            self.listbox.delete(0, tk.END)
            for f in self.pdf_files:
                self.listbox.insert(tk.END, f)
        # else: sizes match, do nothing
        self.update_buttons()

    def update_buttons(self):
        self.logger.info("PDFUtility","Updating buttons")
        # Always update based on selection
        selected_count = len(self.listbox.curselection())

        if self.pdf_files:
            # Enable buttons that should be available when files exist,
            self.select_all_button.config(state=tk.NORMAL) 
            # regardless of selection
            if len(self.pdf_files) > 1:
                self.sort_button.config(state=tk.NORMAL)
                
            # Buttons that require selection
            self.split_button.config(state=tk.NORMAL if selected_count > 0 else tk.DISABLED)
            self.view_button.config(state=tk.NORMAL if selected_count >= 1 else tk.DISABLED)
            self.rename_button.config(state=tk.NORMAL if selected_count == 1 else tk.DISABLED)
            self.delete_button.config(state=tk.NORMAL if selected_count >= 1 else tk.DISABLED)
            self.duplicate_button.config(state=tk.NORMAL if selected_count >= 1 else tk.DISABLED)
            self.repair_button.config(state=tk.NORMAL if selected_count >= 1 else tk.DISABLED)
            self.remove_white_button.config(state=tk.NORMAL if selected_count >= 1 else tk.DISABLED)
            self.merge_button.config(state=tk.NORMAL if selected_count > 1 else tk.DISABLED)
            self.read_button.config(state=tk.NORMAL if selected_count >= 1 else tk.DISABLED)
            self.copy_path_button.config(state=tk.NORMAL if selected_count == 1 else tk.DISABLED)
            self.open_path_button.config(state=tk.NORMAL if selected_count == 1 else tk.DISABLED)
            self.copy_file_button.config(state=tk.NORMAL if selected_count == 1 else tk.DISABLED)
            if selected_count >= 1:
                self.remove_selected.config(state=tk.NORMAL)
                self.clear_selection_button.config(state=tk.NORMAL)
                self.convert_pdf_to_image_button.config(state=tk.NORMAL)
            else:
                self.remove_selected.config(state=tk.DISABLED)
                self.clear_selection_button.config(state=tk.DISABLED)
                self.convert_pdf_to_image_button.config(state=tk.DISABLED)
        else:
            # Disable all buttons when no files exist
            self.split_button.config(state=tk.DISABLED)
            self.merge_button.config(state=tk.DISABLED)
            self.view_button.config(state=tk.DISABLED)
            self.rename_button.config(state=tk.DISABLED)
            self.delete_button.config(state=tk.DISABLED)
            self.remove_selected.config(state=tk.DISABLED)
            self.select_all_button.config(state=tk.DISABLED)
            self.clear_selection_button.config(state=tk.DISABLED)
            self.duplicate_button.config(state=tk.DISABLED)
            self.repair_button.config(state=tk.DISABLED)
            self.remove_white_button.config(state=tk.DISABLED)
            self.read_button.config(state=tk.DISABLED)
            self.sort_button.config(state=tk.DISABLED)
            self.convert_pdf_to_image_button.config(state=tk.DISABLED)
            self.copy_path_button.config(state=tk.DISABLED)
            self.open_path_button.config(state=tk.DISABLED)
            self.copy_file_button.config(state=tk.DISABLED)

        # Update status message based on selection
        if selected_count > 0:
            self.status_label.config(text=f"{selected_count} file(s) selected")

    

    # inside your main UI class …

    def view_pdfs(self):
        """Open selected PDFs in read-only mode."""
        if not self.listbox.curselection():
            messagebox.showinfo("Info", "Select at least 1 PDF to view.")
            return

        renderer = PDFRendererController(
            self.root,
            self.listbox.curselection(),
            read_only=True             # passive view mode
        )
        renderer.set_pdf_files(self.pdf_files)
        renderer.set_selected_indices(self.listbox.curselection())
        if hasattr(self, "status_label"):
            renderer.set_status_label(self.status_label)

        if renderer.render_pdf_ui():
            self.root.after(500, self._refresh_after_render, renderer)


    def edit_pdfs(self):
        """Open selected PDFs with editing enabled."""
        if not self.listbox.curselection():
            messagebox.showinfo("Info", "Select at least 1 PDF to edit.")
            return

        renderer = PDFRendererController(
            self.root,
            self.listbox.curselection(),
            read_only=False            # editing enabled from start
        )
        renderer.set_pdf_files(self.pdf_files)
        renderer.set_selected_indices(self.listbox.curselection())
        if hasattr(self, "status_label"):
            renderer.set_status_label(self.status_label)

        if renderer.render_pdf_ui():
            self.root.after(500, self._refresh_after_render, renderer)


    def _refresh_after_render(self, renderer):
        """
        Called after the renderer window closes to pull back any new files.
        """
        # If the notebook window is still open keep checking
        if renderer.notebook and renderer.notebook.winfo_exists():
            self.root.after(1000, self._refresh_after_render, renderer)
            return

        # Update our master list with anything the renderer exported
        self.pdf_files = renderer.get_completed_files()
        self.update_listbox()


    def toggle_selection(self, event):
        """Handle selection of clicked item"""
        self.logger.info("PDFUtility","Toggling selection")
        clicked_index = self.listbox.nearest(event.y)

        # Check if Ctrl or Shift is pressed
        ctrl_pressed = (event.state & 0x4)  # Control
        shift_pressed = (event.state & 0x1)  # Shift

        if ctrl_pressed:
            self.logger.debug("PDFUtility", "Ctrl key pressed")
            # With Ctrl: Toggle the clicked item's selection
            if clicked_index in self.listbox.curselection():
                self.listbox.selection_clear(clicked_index)
            else:
                self.listbox.selection_set(clicked_index)
        elif shift_pressed:
            self.logger.debug("PDFUtility","Shift key pressed")
            # With Shift: Select range from last selection to current click
            if self.listbox.curselection():  # If there's a previous selection
                last_selected = self.listbox.curselection()[-1]
                start = min(last_selected, clicked_index)
                end = max(last_selected, clicked_index)
                self.listbox.selection_clear(0, tk.END)
                for i in range(start, end + 1):
                    self.listbox.selection_set(i)
        else:
            # Regular click: If item is already the only selection, keep it selected
            current_selection = self.listbox.curselection()
            if len(current_selection) == 1 and current_selection[0] == clicked_index:
                return
            # Otherwise, clear and select only the clicked item
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(clicked_index)

        # Update status and buttons
        selected_count = len(self.listbox.curselection())
        if selected_count > 0:
            self.status_label.config(text=f"{selected_count} file(s) selected")
        else:
            self.status_label.config(text="")

        self.update_buttons()

    def setup_key_bindings(self):
        """Set up key bindings for Ctrl+A, Ctrl+D, Ctrl+C, and Ctrl+V."""
        self.root.bind('<Control-a>', self.select_all)
        self.root.bind('<Control-d>', self.delete_pdf)
        self.root.bind('<Control-c>', self.keyboard_copy_file)
        self.root.bind('<Control-v>', self.keyboard_paste_files)

    def keyboard_copy_file(self, event=None):
        """Handle Ctrl+C keyboard shortcut for copying files"""
        selected_count = len(self.listbox.curselection())
        if selected_count == 1:
            self.copy_file()
        return 'break'  # Prevent default behavior

    def keyboard_paste_files(self, event=None):
        """Handle Ctrl+V keyboard shortcut for pasting files"""
        self.paste_files()
        return 'break'  # Prevent default behavior

    def clear_selection(self):
        """Clear all selected items"""
        self.logger.info("PDFUtility","Clearing selection")
        self.listbox.selection_clear(0, tk.END)
        self.update_buttons()
        self.status_label.config(text="")

    def browse_output_dir(self, entry):
        self.logger.info("PDFUtility","Browsing output directory")
        path = filedialog.askdirectory(title="Select Output Directory")
        if path:
            entry.delete(0, tk.END)
            entry.insert(0, path)

    

    
    def browse_directory(self, entry, title):
        """Open directory browser and update entry"""
        self.logger.info("PDFUtility","Browsing directory")
        directory = filedialog.askdirectory(title)
        if directory:
            entry.delete(0, tk.END)
            entry.insert(0, directory)        

    def browse_directory(self, entry):
        """Open directory browser and update entry"""
        self.logger.info("PDFUtility","Browsing directory")
        directory = filedialog.askdirectory(title="Select Directory")
        if directory:
            entry.delete(0, tk.END)
            entry.insert(0, directory)

    
    def open_settings(self):
        self.logger.info("PDFUtility","Opening settings")
        self.settingsController.open_settings()

    def on_close(self):
        """Handle program exit and clean up resources."""
        self.logger.info("PDFUtility", "Shutting down...")
        self.shutdown_flag.set()  # Signal threads to stop
        self.tts.shutdown()  # Stop TTS
        self.shutdown() # Shut down threads
        time.sleep(0.5)  # Give threads time to exit gracefully
        for t in threading.enumerate():
            self.logger.debug("PDFUtility", f"Remaining thread: {t.name}, daemon: {t.daemon}")
        self.logger.fatal("PDFUtility", "You have killed me you murderer!")
        self.root.quit()
        self.root.update_idletasks()
        self.root.destroy()  # Close the main window

    def shutdown(self):
        """Shuts down all threads and cleans up resources."""
        self.logger.info("PDFUtility", "Shutting down PDFUtility module")

        # Signal threads to stop
        self.shutdown_flag.set()

        # Join any threads started in this class
        if hasattr(self, 'scan_thread') and self.scan_thread.is_alive():
            self.logger.info("PDFUtility", "Waiting for scan thread to terminate")
            self.scan_thread.join(timeout=1.0)

        if hasattr(self, 'add_thread') and self.add_thread.is_alive():
            self.logger.info("PDFUtility", "Waiting for add thread to terminate")
            self.add_thread.join(timeout=1.0)

        # Clean up other resources
        self.logger.cleanup()

    def convert_image_to_pdf(self):
        self.logger.info("PDFUtility","Converting image to PDF")
        selection = self.listbox.curselection()
        imagecontroller = ImageControl(self.root, selection)
        new_pdfs = imagecontroller.convert_image_to_pdf()
        self.logger.debug("PDFUtility",f"New PDFs created: {new_pdfs}")
        if new_pdfs:
            self.logger.info("PDFUtility",f"New PDFs created: {new_pdfs}")
            for new_pdf in new_pdfs:
                self.pdf_files.append(new_pdf)
            self.update_listbox()

    def convert_pdf_to_image(self):
        self.logger.info("PDFUtility","Converting PDF to image")
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "No PDF files selected for conversion")
            return
        
        # Get the actual file paths from the selection indices
        selected_files = [self.pdf_files[i] for i in selection]
        imagecontroller = ImageControl(self.root, selected_files)
        imagecontroller.start_converting_to_img()

    def scan_folder(self):
        scanner = PDFDirectoryScanner(
            self.root,                               # your tk.Tk()
            on_batch=lambda batch: self.pdf_files.extend(batch) or self.update_listbox()
        )
        scanner.start_scan()  

    def bind_scroll_events(self, widget):
        # Mouse wheel (vertical)
        widget.bind_all("<MouseWheel>", lambda e: widget.yview_scroll(int(-1*(e.delta/120)), "units"))  # Windows/macOS
        widget.bind_all("<Button-4>", lambda e: widget.yview_scroll(-1, "units"))  # Linux scroll up
        widget.bind_all("<Button-5>", lambda e: widget.yview_scroll(1, "units"))   # Linux scroll down

        # Arrow keys (vertical)
        widget.bind_all("<Up>", lambda e: widget.yview_scroll(-1, "units"))
        widget.bind_all("<Down>", lambda e: widget.yview_scroll(1, "units"))

        # Arrow keys (horizontal)
        widget.bind_all("<Left>", lambda e: widget.xview_scroll(-1, "units"))
        widget.bind_all("<Right>", lambda e: widget.xview_scroll(1, "units"))
        
        # Home/End
        widget.bind_all("<Home>", lambda e: widget.yview_moveto(0))
        widget.bind_all("<End>", lambda e: widget.yview_moveto(1))
    
        # Page Up/Down
        widget.bind_all("<Prior>", lambda e: widget.yview_scroll(-1, "pages"))  # Page Up
        widget.bind_all("<Next>", lambda e: widget.yview_scroll(1, "pages"))    # Page Down

    def setup_ui(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)  # Handle window close

        self.logger.info("PDFUtility", "Setting up user interface")
        self.root.title("PDF Utility")
        self.root.geometry("1200x700")
        self.settings = self.settingsController.load_settings()
    
        # Set ttkbootstrap theme
        theme_name = "flatly" if self.settings["theme"] == "Light" else "darkly"
        self.style.theme_use(theme_name)
    
        # Set background color
        bg_color = "white" if self.settings["theme"] == "Light" else "black"
        self.root.configure(bg=bg_color)
    
        # Configure main grid
        self.root.columnconfigure(0, weight=8)
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(1, weight=2)
        self.root.minsize(1000, 600)
    
        # --- Main Content Frame ---
        main_content = ttk.Frame(self.root)
        main_content.grid(row=0, column=0, rowspan=3, sticky="nsew", padx=10, pady=10)
        main_content.columnconfigure(0, weight=1)
        main_content.rowconfigure(1, weight=2)
    
        # --- Header (Title + Settings Button) ---
        header_frame = ttk.Frame(main_content)
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.columnconfigure(1, weight=1)
    
        # Settings button
        self.settings_icon = ttk.Button(header_frame, text="⚙", command=self.open_settings, width=3)
        self.settings_icon.grid(row=0, column=0, pady=10, padx=10, sticky="w")
    
        # Title label
        ttk.Label(header_frame, text="PDF Files", font=("Arial", 14)).grid(row=0, column=1, pady=10, sticky="ew")
    
        # --- Listbox Frame ---
        list_frame = ttk.Frame(main_content)
        list_frame.grid(row=1, column=0, sticky="nsew")
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)
    
        scrollbar_y = ttk.Scrollbar(list_frame, orient="vertical")
        scrollbar_x = ttk.Scrollbar(list_frame, orient="horizontal")
    
        self.listbox = tk.Listbox(list_frame, selectmode=tk.EXTENDED, yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set, activestyle='none')
        self.listbox.grid(row=0, column=0, sticky="nsew")
    
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")
    
        scrollbar_y.config(command=self.listbox.yview)
        scrollbar_x.config(command=self.listbox.xview)
    
        self.bind_scroll_events(self.listbox)  # Bind scroll events to the listbox
        
        # We'll use manual drag and drop implementation instead of the handler
        
        # --- Tab System ---
        tab_control = ttk.Notebook(main_content)
        tab_control.grid(row=2, column=0, sticky="nsew", pady=10)
    
        tab_main = ttk.Frame(tab_control)
        tab_sorting = ttk.Frame(tab_control)
        tab_reading = ttk.Frame(tab_control)
        tab_extras = ttk.Frame(tab_control)
    
        tab_control.add(tab_main, text="Main Tools")
        tab_control.add(tab_sorting, text="Sorting")
        tab_control.add(tab_reading, text="Reading")
        tab_control.add(tab_extras, text="Extras")
    
        # --- Main Tools Tab Buttons ---
        ttk.Button(tab_main, text="Add Files", command=self.add_files, width=15).grid(row=0, column=0, padx=5, pady=5)
        self.remove_selected = ttk.Button(tab_main, text="Remove Selected", command=self.remove_file, width=15, state="disabled")
        self.remove_selected.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(tab_main, text="Scan Folder", command=self.scan_folder, width=15).grid(row=0, column=2, padx=5, pady=5)
    
        self.split_button = ttk.Button(tab_main, text="Split PDF", command=self.split_pdf_ui, width=15, state="disabled")
        self.split_button.grid(row=1, column=0, pady=5, padx=5)
    
        self.merge_button = ttk.Button(tab_main, text="Merge PDFs", command=self.merge_pdf_ui, width=15, state="disabled")
        self.merge_button.grid(row=1, column=1, pady=5, padx=5)
    
        self.repair_button = ttk.Button(tab_main, text="Repair PDF", command=self.repair_pdf_ui, width=15, state="disabled")
        self.repair_button.grid(row=1, column=2, pady=5, padx=5)
    
        # --- Sorting Tab ---
        # --- Sorting Tab ---
        self.sort_button = ttk.Button(tab_sorting, text="Sort Files", command=self.sort_files_alphabetically, width=15)
        self.sort_button.grid(row=0, column=0, padx=5, pady=5)

        self.rename_button = ttk.Button(tab_sorting, text="Rename PDF", command=self.rename_pdf, width=15, state="disabled")
        self.rename_button.grid(row=0, column=1, padx=5, pady=5)

        self.select_all_button = ttk.Button(tab_sorting, text="Select All", command=self.select_all, width=15, state="disabled")
        self.select_all_button.grid(row=0, column=2, padx=5, pady=5)

        self.clear_selection_button = ttk.Button(tab_sorting, text="Clear Selection", command=self.clear_selection, width=15, state="disabled")
        self.clear_selection_button.grid(row=0, column=3, padx=5, pady=5)

        self.copy_path_button = ttk.Button(tab_sorting, text="Copy File Path", command=self.copy_file_path, width=15, state="disabled")
        self.copy_path_button.grid(row=1, column=0, padx=5, pady=5)

        self.open_path_button = ttk.Button(tab_sorting, text="Open File Path", command=self.open_filepath, width=15, state="disabled")
        self.open_path_button.grid(row=1, column=1, padx=5, pady=5)

        self.search_button = ttk.Button(tab_sorting, text="Search For PDF", command=self.search_ui, width=15)
        self.search_button.grid(row=1, column=2, padx=5, pady=5)

        self.copy_file_button = ttk.Button(tab_sorting, text="Copy File", command=self.copy_file, width=15, state="disabled")
        self.copy_file_button.grid(row=1, column=3, padx=5, pady=5)

        self.paste_files_button = ttk.Button(tab_sorting, text="Paste Files", command=self.paste_files, width=15)
        self.paste_files_button.grid(row=2, column=0, padx=5, pady=5)
        
        # --- Reading Tab ---
        self.read_button = ttk.Button(tab_reading, text="Read PDF", command=self.open_playback_control, width=15)
        self.read_button.grid(row=0, column=0, padx=5, pady=5)
        self.view_button = ttk.Button(tab_reading, text="View PDF", command=self.view_pdfs, width=15, state="disabled")
        self.view_button.grid(row=0, column=1, padx=5, pady=5)
        self.experimental_view_button = ttk.Button(tab_reading, text="Experimental View", command=self.view_experimental, width=16, state="enabled")
        self.experimental_view_button.grid(row=0, column=2, padx=5, pady=5)
    
        # --- Extras Tab ---
        ttk.Button(tab_extras, text="Convert Images", command=self.convert_image_to_pdf, width=15).grid(row=0, column=0, padx=5, pady=5)
        self.convert_pdf_to_image_button = ttk.Button(tab_extras, text="Convert PDFs", command=self.convert_pdf_to_image, width=15, state="disabled")
        self.convert_pdf_to_image_button.grid(row=0, column=3, padx=5, pady=5)  # Add this line
        self.remove_white_button = ttk.Button(tab_extras, text="Remove White Pages", command=self.remove_white_ui, width=18, state="disabled")
        self.remove_white_button.grid(row=0, column=1, padx=5, pady=5)
        self.duplicate_button = ttk.Button(tab_extras, text="Duplicate PDF", command=self.duplicate_file, width=15, state="disabled")
        self.duplicate_button.grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(tab_extras, text="Help", command=self.view_help, width=15).grid(row=1, column=0, pady=5, padx=5)
        self.delete_button = ttk.Button(tab_extras, text="Delete PDF", command=self.delete_pdf, width=15, state="disabled")
        self.delete_button.grid(row=1, column=1, pady=5)
    
        # --- Status Label ---
        self.status_label = ttk.Label(main_content, text="", font=("Arial", 10))
        self.status_label.grid(row=3, column=0, pady=5)
    
        # Bind events
        self.listbox.bind('<Button-1>', self.toggle_selection)
        self.listbox.bind('<<ListboxSelect>>', lambda e: self.update_buttons())
    
        # Save references
        self.main_content = main_content
        self.list_frame = list_frame
    
        # Apply Theme
        #self.apply_theme()
    
        # Update buttons after setup
        self.update_buttons()

        # --- Drag and Drop Support ---
        self.logger.info("PDFUtility","Enabling drag and drop support")
        try:
            from tkinterdnd2 import DND_FILES, DND_ALL
            self.listbox.drop_target_register(DND_FILES, DND_ALL)
            self.listbox.dnd_bind('<<Drop>>', self.on_file_drop)
            self.logger.info("PDFUtility","Drag and drop enabled successfully")
        except Exception as e:
            self.logger.warning("PDFUtility",f"Failed to enable drag and drop: {e}")
            self.status_label.config(text="Drag and drop not available")

    def on_file_drop(self, event):
        """Handle dropped files"""
        self.logger.info("PDFUtility","Files dropped")
        
        # Get the file paths from the event
        file_paths = event.data
        self.logger.info("PDFUtility",f"Raw drop data: {file_paths} (type: {type(file_paths)})")
        
        # Convert to string if needed
        if not isinstance(file_paths, str):
            file_paths = str(file_paths)
        
        # Clean up the data - sometimes it comes with extra formatting
        file_paths = file_paths.strip()
        
        # Parse file paths correctly - tkinterdnd2 wraps file paths with spaces in curly braces
        files_list = []
        
        # Check if the entire string is wrapped in curly braces (single file with spaces)
        if file_paths.startswith('{') and file_paths.endswith('}') and file_paths.count('{') == 1:
            # Single file with spaces wrapped in curly braces
            files_list = [file_paths[1:-1]]  # Remove the wrapping braces
        else:
            # Multiple files or files without spaces
            # Split by spaces, but handle files wrapped in curly braces
            import re
            # Pattern to match files wrapped in curly braces or standalone files
            pattern = r'\{([^}]+)\}|(\S+)'
            matches = re.findall(pattern, file_paths)
            
            for match in matches:
                # match[0] is the content inside braces, match[1] is standalone file
                file_path = match[0] if match[0] else match[1]
                if file_path.strip():
                    files_list.append(file_path.strip())
        
        self.logger.info("PDFUtility",f"Parsed file list: {files_list}")
        
        # Process each file
        for file_path in files_list:
            if file_path.strip():  # Make sure it's not empty
                self.add_dropped_file(file_path.strip())

    def add_dropped_file(self, file_path):
        """Add a single file from a drop event"""
        self.logger.info("PDFUtility",f"Adding dropped file: {file_path}")
        
        # Clean up the file path - remove any remaining curly braces and extra whitespace
        cleaned_path = str(file_path).strip()
        
        # Remove curly braces if they exist (shouldn't happen with new parsing, but just in case)
        while cleaned_path.startswith('{') and cleaned_path.endswith('}'):
            cleaned_path = cleaned_path[1:-1].strip()
        
        # Normalize the file path
        normalized_path = os.path.normpath(cleaned_path)
        
        self.logger.info("PDFUtility",f"Cleaned file path: {normalized_path}")
        
        # Check if the file exists
        if not os.path.exists(normalized_path):
            self.logger.warning("PDFUtility",f"File does not exist: {normalized_path}")
            messagebox.showwarning("File Not Found", f"File does not exist: {normalized_path}")
            return
        
        # Get the file extension more robustly
        _, ext = os.path.splitext(normalized_path)
        ext_lower = ext.lower()
        
        self.logger.info("PDFUtility",f"File extension detected: '{ext_lower}'")
        
        # Check if it's a PDF file
        if ext_lower == '.pdf':
            self.logger.info("PDFUtility",f"Valid PDF file: {normalized_path}")
            # Check for duplicates
            if normalized_path not in [os.path.normpath(f) for f in self.pdf_files]:
                self.pdf_files.append(normalized_path)
                self.update_listbox()
                self.status_label.config(text=f"Added: {os.path.basename(normalized_path)}")
            else:
                self.logger.info("PDFUtility",f"File already in list: {normalized_path}")
                self.status_label.config(text=f"File already in list: {os.path.basename(normalized_path)}")
        else:
            # Not a PDF file, show warning
            self.logger.warning("PDFUtility",f"Invalid file type (not PDF): {normalized_path} (extension: '{ext_lower}')")
            messagebox.showwarning("Invalid File Type", 
                f"File is not a valid PDF: {os.path.basename(normalized_path)}\n"
                f"Extension detected: '{ext_lower}'\n"
                f"Please select PDF files only.")

    def sort_files_alphabetically(self):
        """Sort PDF files alphabetically"""
        self.logger.info("PDFUtility","Sorting PDF files alphabetically")
        self.pdf_files.sort()
        self.update_listbox()

    def select_all(self, Event=None):
        """Select all PDF files in the listbox"""
        self.logger.info("PDFUtility","Selecting all PDF files in the listbox")
        for i in range(self.listbox.size()):
            self.listbox.select_set(i)
        self.update_buttons()

    
def main():
    try:
        # Try to use tkinterdnd2 for drag and drop support
        from tkinterdnd2 import TkinterDnD
        root = TkinterDnD.Tk()
        
        # Apply ttkbootstrap theme
        style = Style(theme="darkly")
        print("Using TkinterDnD window with drag and drop support")
    except Exception as e:
        print(f"Drag and drop not available: {e}")
        # Fallback to regular window
        root = Window(themename="darkly")  # or "flatly" for light mode
        
    app = PDFUtility(root)
    root.mainloop()

if __name__ == "__main__":
    mp.freeze_support()     # <-- required for PyInstaller
    mp.set_start_method("spawn", force=True)
    main()



