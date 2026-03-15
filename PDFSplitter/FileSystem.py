from PDFUtility.PDFLogger import Logger
from ProgressDialog import ProgressDialog
from tkinter import filedialog, messagebox

class FileSystem:
    def __init__(self, root):
        self.root = root
        self.logger = Logger()
        
        self.pdf_files = []  # List to store PDF file paths
        self.status_label = None  # Placeholder for status label, to be set in the GUI
        pass


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
