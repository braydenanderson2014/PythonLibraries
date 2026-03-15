#!/usr/bin/env python3
# ocr_control.py - OCR Control functionality for PDF Utility

import os
import sys
import platform
import subprocess
import threading
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtWidgets import QFileDialog, QMessageBox

try:
    import pytesseract
    from pdf2image import convert_from_path
    from PIL import Image
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False

import fitz  # PyMuPDF

from PDFLogger import Logger
from ProgressDialog import ProgressDialog
from settings_controller import SettingsController


class OCRControl(QObject):
    """Controller for OCR operations in PDF Utility"""
    
    # Define signals for progress reporting
    progress_signal = pyqtSignal(int, int)     # current, total
    status_signal = pyqtSignal(str)            # status message
    complete_signal = pyqtSignal(bool, str)    # success, message
    text_extracted_signal = pyqtSignal(str, str)  # file_path, extracted_text
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.logger = Logger()
        self.settings_controller = SettingsController()
        
        # Initialize state variables
        self.ocr_in_progress = False
        self.cancel_requested = False
        
        # Check if Tesseract is available
        self.tesseract_available = self._check_tesseract_installation()
        
        self.logger.info("OCRControl", "=========================================================")
        self.logger.info("OCRControl", "Initializing OCR Control")
        self.logger.info("OCRControl", f"Pytesseract available: {PYTESSERACT_AVAILABLE}")
        self.logger.info("OCRControl", f"Tesseract installed: {self.tesseract_available}")
        self.logger.info("OCRControl", "=========================================================")
        
    def _check_tesseract_installation(self):
        """Check if Tesseract OCR is installed on the system"""
        if not PYTESSERACT_AVAILABLE:
            self.logger.warning("OCRControl", "pytesseract package not installed")
            return False
            
        try:
            # Try to get Tesseract version
            # On Windows, check common installation paths
            if platform.system() == 'Windows':
                common_paths = [
                    r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                    r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                    r'C:\Users\Public\tesseract\tesseract.exe',
                ]
                
                for path in common_paths:
                    if os.path.exists(path):
                        pytesseract.pytesseract.tesseract_cmd = path
                        self.logger.info("OCRControl", f"Found Tesseract at: {path}")
                        break
            
            # Test if Tesseract works
            version = pytesseract.get_tesseract_version()
            self.logger.info("OCRControl", f"Tesseract version: {version}")
            return True
            
        except Exception as e:
            self.logger.error("OCRControl", f"Tesseract not found or not working: {str(e)}")
            return False
            
    def is_tesseract_available(self):
        """Check if Tesseract is available for OCR operations"""
        return PYTESSERACT_AVAILABLE and self.tesseract_available
        
    def get_tesseract_installation_instructions(self):
        """Get platform-specific instructions for installing Tesseract"""
        system = platform.system()
        
        if system == 'Windows':
            return (
                "Tesseract OCR is not installed.\n\n"
                "To install on Windows:\n"
                "1. Download the installer from:\n"
                "   https://github.com/UB-Mannheim/tesseract/wiki\n"
                "2. Run the installer and follow the instructions\n"
                "3. Restart PDF Utility after installation"
            )
        elif system == 'Linux':
            return (
                "Tesseract OCR is not installed.\n\n"
                "To install on Linux:\n"
                "Open a terminal and run:\n"
                "   sudo apt-get update\n"
                "   sudo apt-get install tesseract-ocr\n"
                "\n"
                "For other distributions, use your package manager:\n"
                "   Fedora: sudo dnf install tesseract\n"
                "   Arch: sudo pacman -S tesseract\n"
                "\n"
                "Restart PDF Utility after installation"
            )
        elif system == 'Darwin':  # macOS
            return (
                "Tesseract OCR is not installed.\n\n"
                "To install on macOS:\n"
                "1. Install Homebrew if you haven't already:\n"
                "   /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"\n"
                "2. Install Tesseract:\n"
                "   brew install tesseract\n"
                "\n"
                "Restart PDF Utility after installation"
            )
        else:
            return (
                "Tesseract OCR is not installed.\n\n"
                "Please visit https://github.com/tesseract-ocr/tesseract\n"
                "for installation instructions for your platform."
            )
            
    def extract_text_from_pdf(self, pdf_files=None, output_format='txt', language='eng'):
        """Extract text from PDF files using OCR
        
        Args:
            pdf_files: List of PDF file paths or None to show file dialog
            output_format: 'txt' for text file, 'searchable_pdf' for searchable PDF
            language: Tesseract language code (e.g., 'eng', 'spa', 'fra')
        """
        if not self.is_tesseract_available():
            self.logger.error("OCRControl", "Tesseract OCR is not available")
            self.complete_signal.emit(False, "Tesseract OCR is not installed")
            
            # Show installation instructions
            instructions = self.get_tesseract_installation_instructions()
            QMessageBox.warning(self.parent, "Tesseract Not Found", instructions)
            return
            
        if self.ocr_in_progress:
            self.logger.warning("OCRControl", "OCR already in progress")
            self.complete_signal.emit(False, "OCR already in progress")
            return
            
        self.ocr_in_progress = True
        self.cancel_requested = False
        
        if not pdf_files:
            # Ask user to select PDFs
            file_paths, _ = QFileDialog.getOpenFileNames(
                self.parent,
                "Select PDF Files for OCR",
                "",
                "PDF Files (*.pdf);;All Files (*.*)"
            )
            
            if not file_paths:
                self.logger.info("OCRControl", "No PDFs selected for OCR")
                self.complete_signal.emit(False, "No PDFs selected for OCR")
                self.ocr_in_progress = False
                return
                
            pdf_files = file_paths
            
        # Start OCR in a separate thread
        ocr_thread = threading.Thread(
            target=self._ocr_process,
            args=(pdf_files, output_format, language),
            daemon=True
        )
        ocr_thread.start()
        
    def _ocr_process(self, pdf_files, output_format, language):
        """Internal method to handle the OCR process in a background thread"""
        processed_files = []
        errors = []
        
        try:
            # Create progress dialog
            progress_dialog = ProgressDialog(
                self.parent,
                "Processing PDFs with OCR",
                f"Extracting text from {len(pdf_files)} PDF(s)..."
            )
            
            # Connect signals
            self.progress_signal.connect(progress_dialog.update_progress)
            self.status_signal.connect(progress_dialog.update_status)
            progress_dialog.cancelled.connect(self._handle_cancel)
            
            progress_dialog.show()
            
            total_files = len(pdf_files)
            self.logger.info("OCRControl", f"Starting OCR on {total_files} PDF(s)")
            
            # Get output directory from settings
            output_dir = self.settings_controller.get_setting("pdf", "default_output_dir")
            os.makedirs(output_dir, exist_ok=True)
            
            for i, pdf_path in enumerate(pdf_files):
                if self.cancel_requested:
                    self.logger.info("OCRControl", "OCR cancelled by user")
                    break
                    
                try:
                    pdf_name = os.path.basename(pdf_path)
                    self.status_signal.emit(f"Processing: {pdf_name}")
                    self.logger.info("OCRControl", f"OCR processing: {pdf_path}")
                    
                    # Extract text using OCR
                    extracted_text = self._extract_text_with_ocr(pdf_path, language)
                    
                    if extracted_text:
                        # Save extracted text
                        base_name = os.path.splitext(pdf_name)[0]
                        output_path = os.path.join(output_dir, f"{base_name}_ocr.txt")
                        
                        with open(output_path, 'w', encoding='utf-8') as f:
                            f.write(extracted_text)
                            
                        processed_files.append(output_path)
                        self.text_extracted_signal.emit(pdf_path, extracted_text)
                        self.logger.info("OCRControl", f"Text extracted to: {output_path}")
                    else:
                        errors.append(f"{pdf_name}: No text extracted")
                        self.logger.warning("OCRControl", f"No text extracted from {pdf_path}")
                    
                except Exception as e:
                    self.logger.error("OCRControl", f"Error processing {pdf_path}: {str(e)}")
                    errors.append(f"{os.path.basename(pdf_path)}: {str(e)}")
                    
                self.progress_signal.emit(i + 1, total_files)
                
            if not self.cancel_requested:
                self.status_signal.emit("OCR processing complete")
                
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
                message = "OCR processing cancelled."
            else:
                message = f"Successfully processed {len(processed_files)} PDF(s) with OCR."
                if errors:
                    message += f"\n{len(errors)} error(s) occurred."
                    
            self.complete_signal.emit(len(errors) == 0, message)
            
        except Exception as e:
            self.logger.error("OCRControl", f"Error in OCR process: {str(e)}")
            self.complete_signal.emit(False, f"Error processing PDFs: {str(e)}")
            
        finally:
            self.ocr_in_progress = False
            
    def _extract_text_with_ocr(self, pdf_path, language='eng'):
        """Extract text from a PDF using OCR
        
        Args:
            pdf_path: Path to PDF file
            language: Tesseract language code
            
        Returns:
            str: Extracted text
        """
        all_text = []
        
        try:
            # First, try to extract text directly (for text-based PDFs)
            pdf_document = fitz.open(pdf_path)
            has_text = False
            
            for page_num in range(len(pdf_document)):
                page = pdf_document.load_page(page_num)
                text = page.get_text()
                
                # Check if page has meaningful text
                if text.strip():
                    has_text = True
                    all_text.append(f"--- Page {page_num + 1} ---\n{text}\n")
                    
            pdf_document.close()
            
            # If PDF already has text, return it
            if has_text:
                self.logger.info("OCRControl", f"PDF {pdf_path} already contains text")
                return '\n'.join(all_text)
                
            # Otherwise, perform OCR on images
            self.logger.info("OCRControl", f"Performing OCR on {pdf_path}")
            
            # Convert PDF to images
            images = convert_from_path(pdf_path, dpi=300)
            
            for i, image in enumerate(images):
                if self.cancel_requested:
                    break
                    
                # Perform OCR on the image
                text = pytesseract.image_to_string(image, lang=language)
                all_text.append(f"--- Page {i + 1} ---\n{text}\n")
                
            return '\n'.join(all_text)
            
        except Exception as e:
            self.logger.error("OCRControl", f"Error extracting text from {pdf_path}: {str(e)}")
            raise
            
    def _handle_cancel(self):
        """Handle cancellation"""
        if self.ocr_in_progress:
            self.cancel_requested = True
            self.logger.info("OCRControl", "Cancellation requested")
            return True
        return False
        
    def get_available_languages(self):
        """Get list of available Tesseract languages"""
        if not self.is_tesseract_available():
            return []
            
        try:
            langs = pytesseract.get_languages()
            self.logger.info("OCRControl", f"Available languages: {langs}")
            return langs
        except Exception as e:
            self.logger.error("OCRControl", f"Error getting languages: {str(e)}")
            return ['eng']  # Default to English
