#!/usr/bin/env python3
# image_control.py - Image Control functionality for PDF Utility

import os
import threading
import time
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtWidgets import QFileDialog, QMessageBox

from PIL import Image
from PyPDF2 import PdfReader, PdfWriter
import fitz  # PyMuPDF for PDF handling

from PDFLogger import Logger
from ProgressDialog import ProgressDialog
from AnimatedProgressDialog import AnimatedProgressDialog
from settings_controller import SettingsController
from utility import Utility
from image_directory_scanner import ImageDirectoryScanner, FileType

class ImageControl(QObject):
    """Controller for image-related operations in PDF Utility"""
    
    # Define signals for progress reporting
    progress_signal = pyqtSignal(int, int)     # current, total
    status_signal = pyqtSignal(str)            # status message
    complete_signal = pyqtSignal(bool, str)    # success, message
    converted_signal = pyqtSignal(list)        # list of converted files
    files_found_signal = pyqtSignal(list)      # list of files found during scan
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.logger = Logger()
        self.settings_controller = SettingsController()
        self.utility = Utility()
        self.directory_scanner = ImageDirectoryScanner(parent)
        
        # Initialize state variables
        self.conversion_in_progress = False
        self.cancel_requested = False
        self.pdf_files = []
        
        self.logger.info("ImageControl", "=========================================================")
        self.logger.info("ImageControl", "Initializing Image Control")
        self.logger.info("ImageControl", "=========================================================")
        
    def convert_images_to_pdf(self, image_files=None):
        """Convert selected image files to PDF with progress tracking"""
        if self.conversion_in_progress:
            self.logger.warning("ImageControl", "Conversion already in progress")
            self.complete_signal.emit(False, "Conversion already in progress")
            return []
            
        self.conversion_in_progress = True
        self.cancel_requested = False
        
        if not image_files:
            # Ask user to select images
            file_paths, _ = QFileDialog.getOpenFileNames(
                self.parent,
                "Select Images to Convert",
                "",
                "Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.tiff);;All Files (*.*)"
            )
            
            if not file_paths:
                self.logger.info("ImageControl", "No images selected for conversion")
                self.complete_signal.emit(False, "No images selected for conversion")
                self.conversion_in_progress = False
                return []
                
            image_files = file_paths
            
        # Start conversion in a separate thread
        convert_thread = threading.Thread(
            target=self._convert_images_process,
            args=(image_files,),
            daemon=True
        )
        convert_thread.start()
        
        return []  # Return empty list initially, files will be emitted via signal
        
    def _convert_images_process(self, image_files):
        """Internal method to handle the image conversion process in a background thread"""
        converted_files = []
        errors = []
        
        try:
            # Create progress dialog
            progress_dialog = ProgressDialog(
                self.parent,
                "Converting Images to PDF",
                f"Converting {len(image_files)} image(s) to PDF..."
            )
            
            # Connect signals
            self.progress_signal.connect(progress_dialog.update_progress)
            self.status_signal.connect(progress_dialog.update_status)
            progress_dialog.cancelled.connect(self._handle_cancel)
            
            progress_dialog.show()
            
            total_files = len(image_files)
            self.logger.info("ImageControl", f"Starting conversion of {total_files} images to PDF")
            
            # Get output directory from settings
            output_dir = self.settings_controller.get_setting("pdf", "default_output_dir")
            os.makedirs(output_dir, exist_ok=True)
            
            for i, image_path in enumerate(image_files):
                if self.cancel_requested:
                    self.logger.info("ImageControl", "Conversion cancelled by user")
                    break
                    
                try:
                    self.status_signal.emit(f"Converting: {os.path.basename(image_path)}")
                    
                    # Open and convert image
                    image = Image.open(image_path)
                    if image.mode != 'RGB':
                        image = image.convert('RGB')
                        
                    # Create output path
                    pdf_path = os.path.join(output_dir, os.path.splitext(os.path.basename(image_path))[0] + '.pdf')
                    
                    # Save as PDF
                    image.save(pdf_path, 'PDF', resolution=100.0)
                    converted_files.append(pdf_path)
                    
                    self.logger.info("ImageControl", f"Converted {image_path} to {pdf_path}")
                    
                except Exception as e:
                    self.logger.error("ImageControl", f"Error converting {image_path}: {str(e)}")
                    errors.append(f"{os.path.basename(image_path)}: {str(e)}")
                    
                self.progress_signal.emit(i + 1, total_files)
                
            if not self.cancel_requested:
                self.status_signal.emit("Conversion complete")
                
            # Close dialog safely from main thread
            QTimer.singleShot(0, progress_dialog.close)
            
            # Disconnect signals to prevent memory leaks
            try:
                self.progress_signal.disconnect(progress_dialog.update_progress)
                self.status_signal.disconnect(progress_dialog.update_status)
                progress_dialog.cancelled.disconnect(self._handle_cancel)
            except:
                pass  # Ignore if signals already disconnected
            
            # Show completion message
            if self.cancel_requested:
                message = "Image conversion cancelled."
            else:
                message = f"Successfully converted {len(converted_files)} image(s) to PDF."
                if errors:
                    message += f"\n{len(errors)} error(s) occurred."
                    
            self.complete_signal.emit(len(errors) == 0, message)
            
            # Emit converted files
            if converted_files:
                self.converted_signal.emit(converted_files)
                
        except Exception as e:
            self.logger.error("ImageControl", f"Error in conversion process: {str(e)}")
            self.complete_signal.emit(False, f"Error converting images: {str(e)}")
            
        finally:
            self.conversion_in_progress = False
            
    def pdf_to_images(self, pdf_file=None):
        """Convert PDF to images"""
        if self.conversion_in_progress:
            self.logger.warning("ImageControl", "Conversion already in progress")
            self.complete_signal.emit(False, "Conversion already in progress")
            return
            
        self.conversion_in_progress = True
        self.cancel_requested = False
        
        # If no PDF provided, ask user to select one
        if not pdf_file:
            file_path, _ = QFileDialog.getOpenFileName(
                self.parent,
                "Select PDF to Convert",
                "",
                "PDF Files (*.pdf)"
            )
            
            if not file_path:
                self.logger.info("ImageControl", "No PDF selected for conversion")
                self.complete_signal.emit(False, "No PDF selected for conversion")
                self.conversion_in_progress = False
                return
                
            pdf_file = file_path
            
        # Start animated progress dialog
        animated_dialog = AnimatedProgressDialog(
            self.parent, 
            "Converting PDF to Images", 
            "Please wait while the PDF is being converted to images..."
        )
        animated_dialog.show()
        
        # Start conversion in a separate thread
        convert_thread = threading.Thread(
            target=self._pdf_to_images_process,
            args=(pdf_file, animated_dialog),
            daemon=True
        )
        convert_thread.start()
        
    def _pdf_to_images_process(self, pdf_file, animated_dialog):
        """Internal method to handle the PDF to image conversion process in a background thread"""
        try:
            self.logger.info("ImageControl", f"Converting PDF {pdf_file} to images")
            
            # Get output directory from settings
            output_dir = self.settings_controller.get_setting("pdf", "default_output_dir")
            os.makedirs(output_dir, exist_ok=True)
            
            # Open PDF
            pdf_document = fitz.open(pdf_file)
            base_name = os.path.splitext(os.path.basename(pdf_file))[0]
            total_pages = len(pdf_document)
            
            if total_pages == 0:
                self.logger.warning("ImageControl", "PDF has no pages")
                self.complete_signal.emit(False, "PDF has no pages")
                QTimer.singleShot(0, animated_dialog.close)
                self.conversion_in_progress = False
                return
                
            self.logger.info("ImageControl", f"PDF has {total_pages} pages")
            
            # Set up list for converted images
            converted_images = []
            
            # Convert each page
            for page_num in range(total_pages):
                if self.cancel_requested:
                    self.logger.info("ImageControl", "Conversion cancelled by user")
                    break
                    
                try:
                    # Update progress message
                    animated_dialog.set_message_safe(f"Converting page {page_num + 1} of {total_pages}...")
                    
                    # Load page and render at high resolution
                    page = pdf_document.load_page(page_num)
                    mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for higher quality
                    pix = page.get_pixmap(matrix=mat)
                    
                    # Determine output filename
                    if total_pages == 1:
                        image_path = os.path.join(output_dir, f"{base_name}.png")
                    else:
                        image_path = os.path.join(output_dir, f"{base_name}_page_{page_num + 1}.png")
                        
                    # Save image
                    pix.save(image_path)
                    converted_images.append(image_path)
                    
                    self.logger.info("ImageControl", f"Saved page {page_num + 1} as {image_path}")
                    
                except Exception as e:
                    self.logger.error("ImageControl", f"Error converting page {page_num + 1}: {str(e)}")
                    
            # Clean up
            pdf_document.close()
            
            # Close progress dialog safely from main thread
            QTimer.singleShot(0, animated_dialog.close)
            
            # Show completion message
            if self.cancel_requested:
                message = "PDF to image conversion cancelled."
            else:
                message = f"Successfully converted PDF to {len(converted_images)} image(s)."
                
            self.complete_signal.emit(len(converted_images) > 0, message)
            
            # Display result in message box
            QMessageBox.information(self.parent, "Conversion Complete", message)
            
        except Exception as e:
            self.logger.error("ImageControl", f"Error in PDF to image conversion: {str(e)}")
            self.complete_signal.emit(False, f"Error converting PDF to images: {str(e)}")
            
            # Close dialog safely from main thread
            QTimer.singleShot(0, animated_dialog.close)
            
            # Show error message
            QMessageBox.critical(self.parent, "Conversion Error", f"Error converting PDF to images: {str(e)}")
            
        finally:
            self.conversion_in_progress = False
            
    def _handle_cancel(self):
        """Handle cancellation"""
        if self.conversion_in_progress:
            self.cancel_requested = True
            self.logger.info("ImageControl", "Cancellation requested")
            return True
        return False
        
    def scan_directory_for_images(self, directory=None, file_type=FileType.IMAGE):
        """Scan directory for image files using the directory scanner"""
        self.directory_scanner.set_file_type(file_type)
        
        # Connect scanner signals if not already connected
        self.directory_scanner.complete_signal.connect(self._handle_scan_complete)
        
        # Start scanning
        return self.directory_scanner.scan_folder(directory)
        
    def scan_directory_for_pdfs(self, directory=None):
        """Scan directory for PDF files using the directory scanner"""
        return self.scan_directory_for_images(directory, FileType.PDF)
        
    def _handle_scan_complete(self, success, message, file_list):
        """Handle completion of directory scan"""
        self.logger.info("ImageControl", f"Directory scan complete: {message}")
        
        if success and file_list:
            self.logger.info("ImageControl", f"Found {len(file_list)} files")
            self.files_found_signal.emit(file_list)
        else:
            self.logger.warning("ImageControl", f"Directory scan failed or found no files: {message}")
            
        # Forward the message to the UI
        self.status_signal.emit(message)
