#!/usr/bin/env python3
# pdf_merger_widget.py - UI for PDF Merging functionality

import os
import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QCheckBox,
    QLineEdit, QFileDialog, QProgressBar, QAbstractItemView, QGroupBox,
    QFormLayout, QMessageBox
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import QApplication

from AnimatedProgressDialog import AnimatedProgressDialog
from directory_scanner import PDFDirectoryScanner
from merge_controller import MergeController
from PDFListWidget import PDFListWidget
from PDFLogger import Logger

class PDFMergerWidget(QWidget):
    """Widget for PDF merging functionality"""
    
    def __init__(self, parent=None, file_list_controller=None, settings_controller=None):
        super().__init__(parent)
        self.logger = Logger()
        self.merge_controller = MergeController(self)
        self.file_list_controller = file_list_controller
        
        # Initialize settings controller
        if settings_controller:
            self.settings_controller = settings_controller
        else:
            from settings_controller import SettingsController
            self.settings_controller = SettingsController()
            self.settings_controller.load_settings()
        
        # Connect controller signals
        self.merge_controller.progress_signal.connect(self.update_progress)
        self.merge_controller.status_signal.connect(self.update_status)
        self.merge_controller.complete_signal.connect(self.merge_complete)
        
        # Connect file list controller if provided
        if self.file_list_controller:
            # Remove duplicate connection - this will be set up in initUI
            pass
            
        self.initUI()
        
    def initUI(self):
        """Initialize the UI elements"""
        main_layout = QVBoxLayout(self)
        
        # PDF selection section
        pdf_group = QGroupBox("PDF Selection")
        pdf_layout = QVBoxLayout(pdf_group)
        
        pdf_buttons_layout = QHBoxLayout()
        self.add_pdf_btn = QPushButton("Add PDFs")
        self.add_pdf_btn.setObjectName("merge_add_pdf_btn")  # Set object name for tutorial system
        self.add_pdf_btn.clicked.connect(self.add_pdfs)
        pdf_buttons_layout.addWidget(self.add_pdf_btn)
        
        self.add_folder_btn = QPushButton("Scan Directory")
        self.add_folder_btn.clicked.connect(self.add_folder)
        pdf_buttons_layout.addWidget(self.add_folder_btn)
        
        self.remove_pdf_btn = QPushButton("Remove Selected")
        self.remove_pdf_btn.clicked.connect(self.remove_selected_pdfs)
        pdf_buttons_layout.addWidget(self.remove_pdf_btn)
        
        self.clear_pdfs_btn = QPushButton("Clear All")
        self.clear_pdfs_btn.clicked.connect(self.clear_all_pdfs)
        pdf_buttons_layout.addWidget(self.clear_pdfs_btn)
        
        pdf_layout.addLayout(pdf_buttons_layout)
        
        # PDF list with reordering buttons
        list_layout = QHBoxLayout()
        
        # Reordering buttons
        reorder_layout = QVBoxLayout()
        self.move_up_btn = QPushButton("↑")
        self.move_up_btn.clicked.connect(self.move_pdf_up)
        self.move_up_btn.setFixedSize(QSize(30, 30))
        reorder_layout.addWidget(self.move_up_btn)
        
        self.move_down_btn = QPushButton("↓")
        self.move_down_btn.clicked.connect(self.move_pdf_down)
        self.move_down_btn.setFixedSize(QSize(30, 30))
        reorder_layout.addWidget(self.move_down_btn)
        
        reorder_layout.addStretch()
        
        # PDF list
        self.pdf_list = PDFListWidget()
        self.pdf_list.setObjectName("merge_pdf_list")  # Set object name for tutorial system
        # whenever the controller adds a few, append them
        self.file_list_controller.items_appended.connect(self.pdf_list.addItems)

        # whenever the controller does a full reset/clear, rebuild
        self.file_list_controller.files_updated.connect(self._on_full_update)

        self.pdf_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.pdf_list.setAcceptDrops(True)
        
        list_layout.addLayout(reorder_layout)
        list_layout.addWidget(self.pdf_list)
        
        pdf_layout.addLayout(list_layout)
        
        # Add to main layout
        main_layout.addWidget(pdf_group)
        
        # Merge options section
        options_group = QGroupBox("Merge Options")
        options_layout = QVBoxLayout(options_group)
        
        # Output file name
        output_name_layout = QFormLayout()
        self.output_name_edit = QLineEdit("Merged_Document")
        self.output_name_edit.setObjectName("output_name_edit")  # Set object name for tutorial system
        output_name_layout.addRow("Output File Name:", self.output_name_edit)
        options_layout.addLayout(output_name_layout)
        
        # Output directory
        output_dir_layout = QFormLayout()
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setReadOnly(True)
        
        output_dir_container = QHBoxLayout()
        output_dir_container.addWidget(self.output_dir_edit)
        
        self.browse_output_btn = QPushButton("Browse...")
        self.browse_output_btn.clicked.connect(self.browse_output_dir)
        output_dir_container.addWidget(self.browse_output_btn)
        
        output_dir_layout.addRow("Output Directory:", output_dir_container)
        options_layout.addLayout(output_dir_layout)
        
        # White space removal option
        self.remove_white_space_cb = QCheckBox("Remove white space (optimizes file size)")
        self.remove_white_space_cb.setChecked(True)
        options_layout.addWidget(self.remove_white_space_cb)
        
        # Add to main layout
        main_layout.addWidget(options_group)
        
        # Progress section
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        progress_bar_layout = QHBoxLayout()
        progress_bar_layout.addWidget(QLabel("Progress:"))
        self.progress_bar = QProgressBar()
        progress_bar_layout.addWidget(self.progress_bar)
        progress_layout.addLayout(progress_bar_layout)
        
        self.status_label = QLabel("Ready")
        progress_layout.addWidget(self.status_label)
        
        main_layout.addWidget(progress_group)
        
        # Action buttons
        actions_layout = QHBoxLayout()
        
        self.merge_btn = QPushButton("Merge PDFs")
        self.merge_btn.setObjectName("merge_btn")  # Set object name for tutorial system
        self.merge_btn.clicked.connect(self.start_merge)
        actions_layout.addWidget(self.merge_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.cancel_merge)
        self.cancel_btn.setEnabled(False)
        actions_layout.addWidget(self.cancel_btn)
        
        self.open_output_btn = QPushButton("Open Output Folder")
        self.open_output_btn.clicked.connect(self.open_output_folder)
        actions_layout.addWidget(self.open_output_btn)
        
        main_layout.addLayout(actions_layout)
        
        # Set default output directory from settings
        default_merge_dir = self.settings_controller.get_setting(
            "pdf", "default_merge_dir", 
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "merge_output")
        )
        self.output_dir_edit.setText(default_merge_dir)
        
        # Ensure the directory exists
        os.makedirs(default_merge_dir, exist_ok=True)
        
    def _on_full_update(self, files: list[str]):
        self.pdf_list.clear()
        self.pdf_list.addItems(files)


    def add_pdfs(self):
        """Add PDFs to the list via file dialog"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Select PDFs to Merge", "", "PDF Files (*.pdf)"
        )
        
        if file_paths:
            # Filter for valid PDFs
            valid_files = self.merge_controller.validate_pdfs(file_paths)
            
            # Add to list
            for pdf_file in valid_files:
                if self.pdf_list.findItems(pdf_file, Qt.MatchFlag.MatchExactly) == []:
                    self.pdf_list.addItem(pdf_file)
            
            # Update shared file list if controller exists
            if self.file_list_controller:
                self.file_list_controller.add_files(valid_files)
            
            # Report invalid files
            invalid_count = len(file_paths) - len(valid_files)
            if invalid_count > 0:
                QMessageBox.warning(
                    self, 
                    "Invalid PDFs", 
                    f"{invalid_count} file(s) were not valid PDF files and were skipped."
                )
                
    def add_folder(self):
        # Disable until scan ends
        self.add_folder_btn.setEnabled(False)   

        # Create the scanner, give it the shared controller,
        # and let it push files straight into that controller
        self.file_list_controller.disable_updates()
        self.scanner = PDFDirectoryScanner(
            parent=self,
            file_list_controller=self.file_list_controller,
            batch_size=50
        )   

        # Re‑enable the button and updates when the scan completes
        def on_scan_complete():
            self.add_folder_btn.setEnabled(True)
            self.file_list_controller.enable_updates()
            
        self.scanner.scan_complete.connect(on_scan_complete)

        # Kick off the built‑in folder dialog + scan
        self.scanner.start_scan()

                
    def remove_selected_pdfs(self):
        """Remove selected PDFs from the list"""
        for item in self.pdf_list.selectedItems():
            self.pdf_list.takeItem(self.pdf_list.row(item))
            
    def clear_all_pdfs(self):
        """Clear all PDFs from the list"""
        self.pdf_list.clear()
        
        # Update shared file list if controller exists
        if self.file_list_controller:
            self.file_list_controller.clear_files()
            
    def move_pdf_up(self):
        """Move selected PDF up in the list"""
        current_row = self.pdf_list.currentRow()
        if current_row > 0:
            item = self.pdf_list.takeItem(current_row)
            self.pdf_list.insertItem(current_row - 1, item)
            self.pdf_list.setCurrentRow(current_row - 1)
            
    def move_pdf_down(self):
        """Move selected PDF down in the list"""
        current_row = self.pdf_list.currentRow()
        if current_row < self.pdf_list.count() - 1 and current_row >= 0:
            item = self.pdf_list.takeItem(current_row)
            self.pdf_list.insertItem(current_row + 1, item)
            self.pdf_list.setCurrentRow(current_row + 1)
            
    def browse_output_dir(self):
        """Browse for output directory"""
        current_dir = self.output_dir_edit.text()
        directory = QFileDialog.getExistingDirectory(
            self, "Select Output Directory", current_dir
        )
        
        if directory:
            self.output_dir_edit.setText(directory)
            
    def start_merge(self):
        """Start the merge operation"""
        # Get the PDF files in order
        pdf_files = []
        for i in range(self.pdf_list.count()):
            pdf_files.append(self.pdf_list.item(i).text())
        
        if len(pdf_files) < 2:
            QMessageBox.warning(
                self, 
                "Not Enough PDFs", 
                "Please add at least two PDF files to merge."
            )
            return
        
        # Get output settings
        output_name = self.output_name_edit.text().strip()
        if not output_name:
            QMessageBox.warning(
                self, 
                "No Output Name", 
                "Please specify an output file name."
            )
            return
        
        output_dir = self.output_dir_edit.text()
        if not output_dir:
            QMessageBox.warning(
                self, 
                "No Output Directory", 
                "Please specify an output directory."
            )
            return
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Get whether to remove white space
        remove_white_space = self.remove_white_space_cb.isChecked()
        
        # Construct full output path
        output_filename = os.path.join(output_dir, output_name)
        
        # Start merge
        self.merge_controller.merge_pdfs(
            pdf_files,
            output_filename,
            remove_white_space
        )
        
        # Update UI state
        self.update_ui_for_merge_started()
        
    def cancel_merge(self):
        """Cancel the current merge operation"""
        if self.merge_controller.cancel_merge():
            self.status_label.setText("Cancelling merge operation...")
            
    def update_progress(self, current, total):
        """Update the progress bar"""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        
    def update_status(self, status):
        """Update the status label"""
        self.status_label.setText(status)
        
    def merge_complete(self, success, output_file):
        """Handle merge completion"""
        self.update_ui_for_merge_completed()
        
        if success:
            message = f"Merge complete. Output file: {os.path.basename(output_file)}"
            self.status_label.setText(message)
            
            # Ask if user wants to open the output folder
            result = QMessageBox.question(
                self,
                "Merge Complete",
                f"{message}\n\nWould you like to open the output folder?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if result == QMessageBox.StandardButton.Yes:
                self.open_output_folder()
        else:
            message = "Merge failed. See log for details."
            self.status_label.setText(message)
            QMessageBox.critical(self, "Merge Error", message)
            
    def open_output_folder(self):
        """Open the output folder in the system file explorer"""
        output_dir = self.output_dir_edit.text()
        if not output_dir or not os.path.exists(output_dir):
            QMessageBox.warning(
                self,
                "Invalid Directory",
                "The output directory does not exist."
            )
            return
        
        # Open folder in system file explorer
        if os.name == 'nt':  # Windows
            os.startfile(output_dir)
        elif os.name == 'posix':  # macOS and Linux
            import subprocess
            if sys.platform == 'darwin':  # macOS
                subprocess.call(['open', output_dir])
            else:  # Linux
                subprocess.call(['xdg-open', output_dir])
                
    def update_ui_for_merge_started(self):
        """Update UI state when merge starts"""
        self.merge_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.add_pdf_btn.setEnabled(False)
        self.add_folder_btn.setEnabled(False)
        self.remove_pdf_btn.setEnabled(False)
        self.clear_pdfs_btn.setEnabled(False)
        self.move_up_btn.setEnabled(False)
        self.move_down_btn.setEnabled(False)
        self.browse_output_btn.setEnabled(False)
        self.output_name_edit.setEnabled(False)
        self.remove_white_space_cb.setEnabled(False)
        
    def update_ui_for_merge_completed(self):
        """Update UI state when merge completes"""
        self.merge_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.add_pdf_btn.setEnabled(True)
        self.add_folder_btn.setEnabled(True)
        self.remove_pdf_btn.setEnabled(True)
        self.clear_pdfs_btn.setEnabled(True)
        self.move_up_btn.setEnabled(True)
        self.move_down_btn.setEnabled(True)
        self.browse_output_btn.setEnabled(True)
        self.output_name_edit.setEnabled(True)
        self.remove_white_space_cb.setEnabled(True)
