#!/usr/bin/env python3
# white_space_widget.py - Widget for white space removal functionality

import os
import warnings
import io
import contextlib

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGroupBox, QFileDialog, QMessageBox, QListWidget, QAbstractItemView,
    QProgressBar, QSlider, QCheckBox, QDialog, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from white_space_remover import WhiteSpaceRemover
from PDFLogger import Logger
from settings_controller import SettingsController
from progress_dialog import DualProgressDialog

class WhiteSpaceWidget(QWidget):
    """Widget for white space removal functionality"""

    def __init__(self, file_list_controller=None):
        super().__init__()

        self.logger = Logger()
        self.settings = SettingsController()
        self.file_list_controller = file_list_controller
        
        # Track processing state
        self.is_processing = False
        self.white_space_remover = None
        self.progress_dialog = None
        
        # Load settings
        self.threshold = self.settings.get_setting("pdf", "white_threshold", 0.95)

        self.init_ui()

    def init_ui(self):
        """Initialize the UI elements"""
        main_layout = QVBoxLayout(self)

        # Instructions
        instructions = QLabel(
            "Select PDF files to remove blank pages. Files with blank pages removed will be saved with '_no_white' suffix."
        )
        instructions.setWordWrap(True)
        main_layout.addWidget(instructions)

        # File section
        files_group = QGroupBox("Files")
        files_layout = QVBoxLayout(files_group)

        # File management buttons
        files_buttons_layout = QHBoxLayout()

        self.add_files_btn = QPushButton("Add Files")
        self.add_files_btn.setToolTip("Add PDF files to the list")
        self.add_files_btn.clicked.connect(self.add_files)
        self.add_files_btn.setObjectName("ws_add_files_btn")  # Set object name for tutorial system
        files_buttons_layout.addWidget(self.add_files_btn)

        self.scan_dir_btn = QPushButton("Scan Directory")
        self.scan_dir_btn.setToolTip("Scan directory for PDF files")
        self.scan_dir_btn.clicked.connect(self.add_folder)
        self.scan_dir_btn.setObjectName("ws_scan_dir_btn")  # Set object name for tutorial system
        files_buttons_layout.addWidget(self.scan_dir_btn)

        self.remove_selected_btn = QPushButton("Remove Selected")
        self.remove_selected_btn.setToolTip("Remove selected files from the list")
        self.remove_selected_btn.clicked.connect(self.remove_selected)
        self.remove_selected_btn.setObjectName("ws_remove_selected_btn")  # Set object name for tutorial system
        files_buttons_layout.addWidget(self.remove_selected_btn)

        self.clear_list_btn = QPushButton("Clear List")
        self.clear_list_btn.setToolTip("Clear the file list")
        self.clear_list_btn.clicked.connect(self.clear_list)
        files_buttons_layout.addWidget(self.clear_list_btn)

        files_layout.addLayout(files_buttons_layout)

        # File list
        
        self.file_list = QListWidget()
        self.file_list.setObjectName("ws_file_list")  # Set object name for tutorial system
        # Connect file list controller signals if available
        if self.file_list_controller:
            # whenever the controller adds a few, append them
            self.file_list_controller.items_appended.connect(self.file_list.addItems)
            # whenever the controller does a full reset/clear, rebuild
            self.file_list_controller.files_updated.connect(self._on_full_update)
        
        self.file_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
            
        files_layout.addWidget(self.file_list)
        main_layout.addWidget(files_group)
        
        # Settings section
        settings_group = QGroupBox("Settings")
        settings_layout = QVBoxLayout(settings_group)
        
        # Threshold section
        threshold_layout = QVBoxLayout()
        
        # Threshold label and value
        threshold_header_layout = QHBoxLayout()
        threshold_label = QLabel("Blank Page Threshold:")
        threshold_header_layout.addWidget(threshold_label)
        
        self.threshold_value_label = QLabel(f"{self.threshold:.2f}")
        self.threshold_value_label.setStyleSheet("font-weight: bold; color: #0066cc;")
        threshold_header_layout.addWidget(self.threshold_value_label)
        threshold_header_layout.addStretch()
        threshold_layout.addLayout(threshold_header_layout)
        
        # Threshold slider
        slider_layout = QHBoxLayout()
        aggressive_label = QLabel("Aggressive")
        aggressive_label.setStyleSheet("font-size: 9pt; color: gray;")
        slider_layout.addWidget(aggressive_label)
        
        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setMinimum(10)   # 0.1
        self.threshold_slider.setMaximum(100)  # 1.0
        self.threshold_slider.setValue(int(self.threshold * 100))
        self.threshold_slider.setTracking(True)
        self.threshold_slider.valueChanged.connect(self.update_threshold)
        slider_layout.addWidget(self.threshold_slider)
        
        conservative_label = QLabel("Conservative")
        conservative_label.setStyleSheet("font-size: 9pt; color: gray;")
        slider_layout.addWidget(conservative_label)
        threshold_layout.addLayout(slider_layout)
        
        # Threshold help text
        threshold_help = QLabel(
            "Higher values require pages to be more empty to be considered blank. "
            "Lower values are more aggressive and may remove pages with light content."
        )
        threshold_help.setWordWrap(True)
        threshold_help.setStyleSheet("color: gray; font-style: italic; font-size: 9pt;")
        threshold_layout.addWidget(threshold_help)
        
        settings_layout.addLayout(threshold_layout)
        
        # Processing mode section
        mode_layout = QVBoxLayout()
        mode_layout.addSpacing(10)
        
        # Mode checkbox
        self.scan_only_mode = QCheckBox("Scan Only (Find and Report Blank Pages)")
        self.scan_only_mode.setToolTip(
            "When checked: Only scan and report which files have blank pages\n"
            "When unchecked: Scan and automatically remove blank pages"
        )
        self.scan_only_mode.setChecked(self.settings.get_setting("pdf", "scan_only_mode", False))
        self.scan_only_mode.stateChanged.connect(self.update_process_button_text)
        mode_layout.addWidget(self.scan_only_mode)
        
        # Mode help text
        mode_help = QLabel(
            "Scan Only mode will show you which files contain blank pages without modifying them. "
            "Uncheck to automatically create new files with blank pages removed."
        )
        mode_help.setWordWrap(True)
        mode_help.setStyleSheet("color: gray; font-style: italic; font-size: 9pt;")
        mode_layout.addWidget(mode_help)
        
        settings_layout.addLayout(mode_layout)
        main_layout.addWidget(settings_group)

        # Processing button
        self.process_btn = QPushButton("Scan for Blank Pages")
        self.process_btn.setToolTip("Process the listed PDFs")
        self.process_btn.clicked.connect(self.remove_white_space)
        self.process_btn.setObjectName("ws_process_btn")  # Set object name for tutorial system
        self.update_process_button_text()  # Set initial text based on mode
        main_layout.addWidget(self.process_btn)
    
    
    def is_valid_pdf(self, pdf_file):
        """
        Check if a file is a valid PDF
        
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
            # Check if file starts with PDF signature
            with open(pdf_file, 'rb') as f:
                header = f.read(8)
                if not header.startswith(b'%PDF-'):
                    return False
            
            # For batch processing, just check the header - avoid PyPDF2 validation
            # to prevent console spam from corrupted PDFs
            return True
                        
        except Exception as e:
            self.logger.debug("WhiteSpaceWidget", f"PDF validation failed for {pdf_file}: {str(e)}")
            return False
            
    def validate_pdfs(self, pdf_files):
        """
        Validate a list of PDF files and return only the valid ones
        
        This method does thorough validation including PDF header checking.
        Used during actual processing, not during directory scanning to avoid UI freezing.
        
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
            self.logger.warning("WhiteSpaceWidget", f"Found {len(invalid_files)} invalid PDF files")
            
        return valid_files
    
    
    def add_folder(self):
        """Add all PDFs from a folder using the directory scanner"""
        # Disable until scan ends
        self.scan_dir_btn.setEnabled(False)   

        # Create the scanner, give it the shared controller,
        # and let it push files straight into that controller
        if self.file_list_controller:
            self.file_list_controller.disable_updates()
        
        from directory_scanner import PDFDirectoryScanner
        self.scanner = PDFDirectoryScanner(
            parent=self,
            file_list_controller=self.file_list_controller,
            batch_size=50
        )   

        # Re‑enable the button and updates when the scan completes
        def on_scan_complete():
            self.scan_dir_btn.setEnabled(True)
            if self.file_list_controller:
                self.file_list_controller.enable_updates()
            self.logger.info("WhiteSpaceWidget", "Directory scan complete")
            
        self.scanner.scan_complete.connect(on_scan_complete)

        # Kick off the built‑in folder dialog + scan
        self.scanner.start_scan()

    def _on_full_update(self, files: list[str]):
        """Handle full update of file list from controller"""
        self.file_list.clear()
        self.file_list.addItems(files)

    def update_threshold(self):
        """Update the threshold value when slider changes"""
        self.threshold = self.threshold_slider.value() / 100.0
        self.threshold_value_label.setText(f"{self.threshold:.2f}")
        # Auto-save to settings
        self.settings.set_setting("pdf", "white_threshold", self.threshold)
        self.settings.save_settings()
        self.logger.info("WhiteSpaceWidget", f"Threshold updated to {self.threshold}")
    
    def update_process_button_text(self):
        """Update the process button text based on mode"""
        if self.scan_only_mode.isChecked():
            self.process_btn.setText("Scan for Blank Pages")
            self.process_btn.setToolTip("Scan PDFs and report which files contain blank pages")
        else:
            self.process_btn.setText("Remove White Space")
            self.process_btn.setToolTip("Scan PDFs and remove blank pages from files that contain them")
        
        # Save mode to settings
        self.settings.set_setting("pdf", "scan_only_mode", self.scan_only_mode.isChecked())
        self.settings.save_settings()

    def add_files(self):
        """Add PDF files to the list"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select PDF Files",
            "",
            "PDF Files (*.pdf);;All Files (*.*)"
        )
        
        if file_paths:
            if self.file_list_controller:
                self.file_list_controller.add_files(file_paths)
            else:
                self.file_list.addItems(file_paths)

    def remove_selected(self):
        """Remove selected files from the list"""
        if self.file_list_controller:
            selected_items = [item.text() for item in self.file_list.selectedItems()]
            if selected_items:
                self.file_list_controller.remove_files(selected_items)
        else:
            for item in self.file_list.selectedItems():
                self.file_list.takeItem(self.file_list.row(item))

    def clear_list(self):
        """Clear the file list"""
        if self.file_list_controller:
            self.file_list_controller.clear_files()
        else:
            self.file_list.clear()
    
    def remove_white_space(self):
        """Handle removing white space from PDFs"""
        if self.is_processing:
            QMessageBox.information(self, "Processing", "White space removal is already in progress.")
            return
            
        # Get file list
        if self.file_list_controller:
            all_files = self.file_list_controller.get_files()
        else:
            all_files = [self.file_list.item(i).text() for i in range(self.file_list.count())]

        if not all_files:
            QMessageBox.information(self, "No Files", "Please add files to the list before processing.")
            return

        # Validate files exist
        valid_files = []
        for file_path in all_files:
            if os.path.exists(file_path):
                valid_files.append(file_path)
            else:
                self.logger.warning("WhiteSpaceWidget", f"File not found: {file_path}")

        if not valid_files:
            QMessageBox.warning(self, "Warning", "None of the files could be found.")
            return

        self.logger.info("WhiteSpaceWidget", f"Starting processing of {len(valid_files)} files with threshold {self.threshold}")

        # Set processing state
        self.is_processing = True
        self.process_btn.setText("Processing...")
        self.process_btn.setEnabled(False)

        try:
            # Create WhiteSpaceRemover instance
            self.white_space_remover = WhiteSpaceRemover(self)
            
            # Set callback to add new files to the list
            if self.file_list_controller:
                self.white_space_remover.set_file_added_callback(self.file_list_controller.add_file)

            # Create progress dialog
            self.progress_dialog = DualProgressDialog(
                self,
                title="Processing PDFs", 
                message="Scanning for blank pages...",
                allow_cancel=True
            )

            # Create scanner thread but don't start it yet
            from white_space_remover import WhiteSpaceScannerThread
            self.white_space_remover.scanner_thread = WhiteSpaceScannerThread(valid_files, self.threshold)

            # Connect signals for scanning BEFORE starting the thread
            self.white_space_remover.scanner_thread.progress_file.connect(
                lambda current, total: self.progress_dialog.update_overall_progress((current/total)*100)
            )
            self.white_space_remover.scanner_thread.progress_page.connect(
                lambda current, total: self.progress_dialog.update_current_progress((current/total)*100)
            )
            self.white_space_remover.scanner_thread.status_update.connect(self.progress_dialog.update_message)
            self.white_space_remover.scanner_thread.scan_complete.connect(self.on_scan_complete)

            # Connect cancel button
            self.progress_dialog.cancel = self.cancel_processing

            # NOW start the scanner thread
            self.white_space_remover.scanner_thread.start()
            self.logger.info("WhiteSpaceWidget", "Scanner thread started successfully")
            
        except Exception as e:
            self.logger.error("WhiteSpaceWidget", f"Error starting white space processing: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to start processing: {str(e)}")
            self.reset_processing_state()
        
    def on_scan_complete(self, blank_page_info_list):
        """Handle completion of the scanning process"""
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None

        # Count total blank pages found
        total_blank_pages = sum(len(info.get_blank_pages()) for info in blank_page_info_list)
        total_files_with_blanks = sum(1 for info in blank_page_info_list if info.get_blank_pages())

        self.logger.info(
            "WhiteSpaceWidget", 
            f"Scan complete. Found {total_blank_pages} blank pages in {total_files_with_blanks} file(s)."
        )

        # Show results to user
        if total_blank_pages == 0:
            QMessageBox.information(
                self, 
                "Scan Complete", 
                "No blank pages were found in the selected PDF files."
            )
            self.reset_processing_state()
            return

        # Handle scan-only mode
        if self.scan_only_mode.isChecked():
            # Create detailed report for scan-only mode
            report_lines = [f"Found {total_blank_pages} blank pages in {total_files_with_blanks} file(s):\n"]
            
            for info in blank_page_info_list:
                if info.get_blank_pages():
                    file_name = os.path.basename(info.get_file_path())
                    blank_pages = info.get_blank_pages()
                    if len(blank_pages) == 1:
                        report_lines.append(f"• {file_name}: Page {blank_pages[0]}")
                    else:
                        pages_str = ", ".join(map(str, blank_pages))
                        report_lines.append(f"• {file_name}: Pages {pages_str}")
            
            report_text = "\n".join(report_lines)
            
            QMessageBox.information(
                self,
                "Blank Pages Report",
                report_text
            )
            self.reset_processing_state()
            return

        # Ask if user wants to remove the blank pages (removal mode)
        reply = QMessageBox.question(
            self,
            "Blank Pages Found",
            f"Found {total_blank_pages} blank pages in {total_files_with_blanks} file(s).\n\n"
            "Do you want to remove these blank pages?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.start_removal_process(blank_page_info_list)
        else:
            self.reset_processing_state()
    
    def start_removal_process(self, blank_page_info_list):
        """Start the removal process"""
        # Get output directory from settings
        output_dir = self.settings.get_setting("pdf", "default_output_dir")

        # Create progress dialog for removal
        self.progress_dialog = DualProgressDialog(
            self,
            title="Removing Blank Pages", 
            message="Processing PDFs...",
            allow_cancel=True
        )

        # Create remover thread but don't start it yet
        from white_space_remover import WhiteSpaceRemoverThread
        self.white_space_remover.remover_thread = WhiteSpaceRemoverThread(blank_page_info_list, output_dir, self.white_space_remover.file_added_callback)

        # Connect signals for removal BEFORE starting the thread
        self.white_space_remover.remover_thread.progress_file.connect(
            lambda current, total: self.progress_dialog.update_overall_progress((current/total)*100)
        )
        self.white_space_remover.remover_thread.progress_page.connect(
            lambda current, total: self.progress_dialog.update_current_progress((current/total)*100)
        )
        self.white_space_remover.remover_thread.status_update.connect(self.progress_dialog.update_message)
        self.white_space_remover.remover_thread.file_completed.connect(self.on_file_completed)
        self.white_space_remover.remover_thread.removal_complete.connect(self.on_removal_complete)

        # Connect cancel button
        self.progress_dialog.cancel = self.cancel_processing

        # NOW start the remover thread
        self.white_space_remover.remover_thread.start()
    
    def on_file_completed(self, file_path):
        """Handle completion of a single file"""
        self.logger.info("WhiteSpaceWidget", f"File completed: {file_path}")
    
    def on_removal_complete(self):
        """Handle completion of the removal process"""
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None

        total_files = len(self.white_space_remover.get_new_files())

        if total_files > 0:
            message = f"Successfully created {total_files} new PDF{'s' if total_files > 1 else ''} with blank pages removed."
            QMessageBox.information(self, "Process Complete", message)
        else:
            QMessageBox.information(self, "Process Complete", "No files were processed.")

        self.reset_processing_state()
    
    def cancel_processing(self):
        """Cancel the current processing"""
        if self.white_space_remover:
            if hasattr(self.white_space_remover, 'scanner_thread') and self.white_space_remover.scanner_thread:
                self.white_space_remover.scanner_thread.cancel()
            if hasattr(self.white_space_remover, 'remover_thread') and self.white_space_remover.remover_thread:
                self.white_space_remover.remover_thread.cancel()
        
        # Cancel current scanner if exists
        if hasattr(self, '_current_scanner') and self._current_scanner:
            try:
                self._current_scanner.scan_complete.disconnect()
            except:
                pass  # Ignore if already disconnected
            self._current_scanner = None
        
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        
        self.reset_processing_state()
        
    def reset_processing_state(self):
        """Reset the processing state"""
        self.is_processing = False
        self.update_process_button_text()  # Restore original text based on mode
        self.process_btn.setEnabled(True)
        self.white_space_remover = None
