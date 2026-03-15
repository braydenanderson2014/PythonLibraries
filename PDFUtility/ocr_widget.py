#!/usr/bin/env python3
# ocr_widget.py - UI for OCR functionality

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QProgressBar, QGroupBox, QComboBox, QTextEdit, QMessageBox,
    QFileDialog, QCheckBox
)
from PyQt6.QtCore import Qt

from ocr_control import OCRControl
from PDFListWidget import PDFListWidget
from PDFLogger import Logger


class OCRWidget(QWidget):
    """Widget for OCR (Optical Character Recognition) functionality"""
    
    def __init__(self, parent=None, file_list_controller=None):
        super().__init__(parent)
        self.logger = Logger()
        self.ocr_controller = OCRControl(self)
        self.file_list_controller = file_list_controller
        
        # Connect controller signals
        self.ocr_controller.progress_signal.connect(self.update_progress)
        self.ocr_controller.status_signal.connect(self.update_status)
        self.ocr_controller.complete_signal.connect(self.ocr_complete)
        self.ocr_controller.text_extracted_signal.connect(self.display_extracted_text)
        
        # Connect file list controller if provided
        if self.file_list_controller:
            self.file_list_controller.files_updated.connect(self.update_file_list)
        
        self.initUI()
        
    def initUI(self):
        """Initialize the UI elements"""
        main_layout = QVBoxLayout(self)
        
        # Title and description
        title_label = QLabel("OCR - Optical Character Recognition")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        main_layout.addWidget(title_label)
        
        desc_label = QLabel(
            "Extract text from scanned PDFs and images using OCR technology.\n"
            "This works on documents that don't have selectable text."
        )
        desc_label.setWordWrap(True)
        main_layout.addWidget(desc_label)
        
        # Check if Tesseract is available
        if not self.ocr_controller.is_tesseract_available():
            warning_label = QLabel(
                "⚠️ Tesseract OCR is not installed. Click 'Check Installation' for instructions."
            )
            warning_label.setStyleSheet("color: #ff6b6b; font-weight: bold; padding: 10px;")
            main_layout.addWidget(warning_label)
            
            check_btn = QPushButton("Check Installation")
            check_btn.clicked.connect(self.show_installation_instructions)
            main_layout.addWidget(check_btn)
        
        # File list section
        files_group = QGroupBox("PDF Files")
        files_layout = QVBoxLayout(files_group)
        
        # Buttons for file management
        file_buttons_layout = QHBoxLayout()
        
        self.add_files_btn = QPushButton("Add PDF Files")
        self.add_files_btn.clicked.connect(self.add_files)
        self.add_files_btn.setObjectName("ocr_add_files_btn")
        file_buttons_layout.addWidget(self.add_files_btn)
        
        self.remove_files_btn = QPushButton("Remove Selected")
        self.remove_files_btn.clicked.connect(self.remove_selected_files)
        file_buttons_layout.addWidget(self.remove_files_btn)
        
        self.clear_files_btn = QPushButton("Clear All")
        self.clear_files_btn.clicked.connect(self.clear_all_files)
        file_buttons_layout.addWidget(self.clear_files_btn)
        
        files_layout.addLayout(file_buttons_layout)
        
        # File list widget
        self.file_list = PDFListWidget()
        files_layout.addWidget(self.file_list)
        
        main_layout.addWidget(files_group)
        
        # OCR options
        options_group = QGroupBox("OCR Options")
        options_layout = QVBoxLayout(options_group)
        
        # Language selection
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel("Language:"))
        
        self.language_combo = QComboBox()
        self.populate_languages()
        lang_layout.addWidget(self.language_combo)
        lang_layout.addStretch()
        
        options_layout.addLayout(lang_layout)
        
        # Output format
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Output Format:"))
        
        self.format_combo = QComboBox()
        self.format_combo.addItem("Text File (.txt)", "txt")
        # Future: self.format_combo.addItem("Searchable PDF", "searchable_pdf")
        format_layout.addWidget(self.format_combo)
        format_layout.addStretch()
        
        options_layout.addLayout(format_layout)
        
        # Show preview checkbox
        self.preview_checkbox = QCheckBox("Show text preview after extraction")
        self.preview_checkbox.setChecked(True)
        options_layout.addWidget(self.preview_checkbox)
        
        main_layout.addWidget(options_group)
        
        # Process button
        process_layout = QHBoxLayout()
        process_layout.addStretch()
        
        self.process_btn = QPushButton("Extract Text with OCR")
        self.process_btn.clicked.connect(self.process_ocr)
        self.process_btn.setObjectName("ocr_process_btn")
        self.process_btn.setMinimumHeight(40)
        self.process_btn.setStyleSheet("font-size: 14px; font-weight: bold;")
        process_layout.addWidget(self.process_btn)
        
        process_layout.addStretch()
        main_layout.addLayout(process_layout)
        
        # Progress section
        progress_layout = QHBoxLayout()
        self.status_label = QLabel("Ready")
        progress_layout.addWidget(self.status_label)
        main_layout.addLayout(progress_layout)
        
        progress_bar_layout = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_bar_layout.addWidget(self.progress_bar)
        main_layout.addLayout(progress_bar_layout)
        
        # Text preview section (initially hidden)
        self.preview_group = QGroupBox("Extracted Text Preview")
        preview_layout = QVBoxLayout(self.preview_group)
        
        self.text_preview = QTextEdit()
        self.text_preview.setReadOnly(True)
        self.text_preview.setMaximumHeight(200)
        preview_layout.addWidget(self.text_preview)
        
        preview_buttons = QHBoxLayout()
        
        self.save_text_btn = QPushButton("Save Text")
        self.save_text_btn.clicked.connect(self.save_preview_text)
        preview_buttons.addWidget(self.save_text_btn)
        
        self.copy_text_btn = QPushButton("Copy to Clipboard")
        self.copy_text_btn.clicked.connect(self.copy_preview_text)
        preview_buttons.addWidget(self.copy_text_btn)
        
        self.clear_preview_btn = QPushButton("Clear Preview")
        self.clear_preview_btn.clicked.connect(self.clear_preview)
        preview_buttons.addWidget(self.clear_preview_btn)
        
        preview_buttons.addStretch()
        preview_layout.addLayout(preview_buttons)
        
        self.preview_group.setVisible(False)
        main_layout.addWidget(self.preview_group)
        
        main_layout.addStretch()
        
    def populate_languages(self):
        """Populate the language dropdown with available Tesseract languages"""
        self.language_combo.clear()
        
        if self.ocr_controller.is_tesseract_available():
            languages = self.ocr_controller.get_available_languages()
            
            # Common language mappings
            lang_names = {
                'eng': 'English',
                'spa': 'Spanish',
                'fra': 'French',
                'deu': 'German',
                'ita': 'Italian',
                'por': 'Portuguese',
                'rus': 'Russian',
                'chi_sim': 'Chinese (Simplified)',
                'chi_tra': 'Chinese (Traditional)',
                'jpn': 'Japanese',
                'kor': 'Korean',
                'ara': 'Arabic',
                'hin': 'Hindi',
            }
            
            for lang_code in languages:
                lang_name = lang_names.get(lang_code, lang_code.upper())
                self.language_combo.addItem(lang_name, lang_code)
        else:
            self.language_combo.addItem("English (default)", "eng")
            
    def show_installation_instructions(self):
        """Show Tesseract installation instructions"""
        instructions = self.ocr_controller.get_tesseract_installation_instructions()
        QMessageBox.information(self, "Tesseract OCR Installation", instructions)
        
    def add_files(self):
        """Add PDF files to the list"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select PDF Files for OCR",
            "",
            "PDF Files (*.pdf);;All Files (*.*)"
        )
        
        if file_paths:
            for file_path in file_paths:
                # Avoid duplicates
                if self.file_list.findItems(file_path, Qt.MatchFlag.MatchExactly) == []:
                    self.file_list.addItem(file_path)
            self.logger.info("OCRWidget", f"Added {len(file_paths)} file(s)")
            
    def remove_selected_files(self):
        """Remove selected files from the list"""
        selected_items = self.file_list.selectedItems()
        for item in selected_items:
            row = self.file_list.row(item)
            self.file_list.takeItem(row)
        self.logger.info("OCRWidget", f"Removed {len(selected_items)} file(s)")
        
    def clear_all_files(self):
        """Clear all files from the list"""
        self.file_list.clear()
        self.logger.info("OCRWidget", "Cleared all files")
        
    def process_dropped_files(self, files):
        """Process files dropped onto the list widget"""
        # Filter for PDF files only
        pdf_files = [f for f in files if f.lower().endswith('.pdf')]
        
        if pdf_files:
            for file_path in pdf_files:
                # Avoid duplicates
                if self.file_list.findItems(file_path, Qt.MatchFlag.MatchExactly) == []:
                    self.file_list.addItem(file_path)
            self.logger.info("OCRWidget", f"Added {len(pdf_files)} dropped file(s)")
        
    def update_file_list(self, files):
        """Update the file list from the shared file list controller"""
        # Only show PDF files in this widget
        pdf_files = [f for f in files if f.lower().endswith('.pdf')]
        
        self.file_list.clear()
        for file_path in pdf_files:
            self.file_list.addItem(file_path)
            
    def process_ocr(self):
        """Process selected PDFs with OCR"""
        # Get list of PDF files
        pdf_files = []
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            pdf_files.append(item.text())
            
        if not pdf_files:
            QMessageBox.warning(self, "No Files", "Please add PDF files to process.")
            return
            
        # Get selected language
        language = self.language_combo.currentData()
        
        # Get output format
        output_format = self.format_combo.currentData()
        
        # Start OCR processing
        self.ocr_controller.extract_text_from_pdf(pdf_files, output_format, language)
        
    def update_progress(self, current, total):
        """Update the progress bar"""
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress_bar.setValue(percentage)
            
    def update_status(self, status):
        """Update the status label"""
        self.status_label.setText(status)
        
    def ocr_complete(self, success, message):
        """Handle OCR completion"""
        self.progress_bar.setValue(100 if success else 0)
        self.status_label.setText("Complete" if success else "Failed")
        
        if success:
            QMessageBox.information(self, "OCR Complete", message)
        else:
            QMessageBox.warning(self, "OCR Failed", message)
            
    def display_extracted_text(self, file_path, text):
        """Display extracted text in the preview area"""
        if self.preview_checkbox.isChecked():
            self.preview_group.setVisible(True)
            
            # Append to preview (or replace if you prefer)
            current_text = self.text_preview.toPlainText()
            if current_text:
                current_text += f"\n\n{'='*60}\n\n"
            
            current_text += f"File: {os.path.basename(file_path)}\n\n{text}"
            self.text_preview.setPlainText(current_text)
            
    def save_preview_text(self):
        """Save the preview text to a file"""
        text = self.text_preview.toPlainText()
        if not text:
            QMessageBox.warning(self, "No Text", "No text to save.")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Extracted Text",
            "",
            "Text Files (*.txt);;All Files (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                QMessageBox.information(self, "Saved", f"Text saved to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save text: {str(e)}")
                
    def copy_preview_text(self):
        """Copy the preview text to clipboard"""
        text = self.text_preview.toPlainText()
        if text:
            from PyQt6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            QMessageBox.information(self, "Copied", "Text copied to clipboard.")
        else:
            QMessageBox.warning(self, "No Text", "No text to copy.")
            
    def clear_preview(self):
        """Clear the preview text"""
        self.text_preview.clear()
        self.preview_group.setVisible(False)
