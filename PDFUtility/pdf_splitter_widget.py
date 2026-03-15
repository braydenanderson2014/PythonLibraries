#!/usr/bin/env python3
# pdf_splitter_widget.py - UI for PDF Splitting functionality

import os
import sys
from enum import Enum
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSpinBox,
    QComboBox, QRadioButton, QButtonGroup, QLineEdit, QFileDialog,
    QProgressBar, QListWidget, QAbstractItemView, QGroupBox, QFormLayout,
    QTabWidget, QSplitter, QDialog, QDialogButtonBox, QCheckBox, QScrollArea,
    QMessageBox, QInputDialog, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QSize, QCoreApplication
from PyQt6.QtGui import QIcon

from pdf_splitter_controller import PDFSplitterController, SplitMode
from PDFLogger import Logger
from PDFListWidget import PDFListWidget


class PageRangeDialog(QDialog):
    """Dialog for specifying page ranges"""
    
    def __init__(self, parent=None, total_pages=0):
        super().__init__(parent)
        self.total_pages = total_pages
        self.page_ranges = []
        self.initUI()
        
    def initUI(self):
        """Initialize the dialog UI"""
        self.setWindowTitle("Specify Page Ranges")
        self.setMinimumWidth(400)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Information label
        info_label = QLabel(f"Total pages in document: {self.total_pages}")
        layout.addWidget(info_label)
        
        instruction_label = QLabel("Enter page ranges (e.g., 1-5, 8-10)")
        layout.addWidget(instruction_label)
        
        # Table for page ranges
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Start Page", "End Page"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        # Buttons for adding/removing ranges
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add Range")
        add_btn.clicked.connect(self.add_range)
        btn_layout.addWidget(add_btn)
        
        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self.remove_range)
        btn_layout.addWidget(remove_btn)
        layout.addLayout(btn_layout)
        
        # Add initial empty row
        self.add_range()
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def add_range(self):
        """Add a new page range row"""
        row_count = self.table.rowCount()
        self.table.insertRow(row_count)
        
        # Create spinboxes for start and end page
        start_spin = QSpinBox()
        start_spin.setMinimum(1)
        start_spin.setMaximum(self.total_pages)
        self.table.setCellWidget(row_count, 0, start_spin)
        
        end_spin = QSpinBox()
        end_spin.setMinimum(1)
        end_spin.setMaximum(self.total_pages)
        end_spin.setValue(min(start_spin.value() + 1, self.total_pages))
        self.table.setCellWidget(row_count, 1, end_spin)
        
        # Connect start_spin to update end_spin minimum
        start_spin.valueChanged.connect(lambda val: end_spin.setMinimum(val))
        
    def remove_range(self):
        """Remove the selected page range row"""
        selected_rows = set()
        for item in self.table.selectedItems():
            selected_rows.add(item.row())
        
        # Remove rows in reverse order to avoid index shifting
        for row in sorted(selected_rows, reverse=True):
            self.table.removeRow(row)
        
    def validate_and_accept(self):
        """Validate inputs and accept the dialog"""
        page_ranges = []
        
        for row in range(self.table.rowCount()):
            start_spin = self.table.cellWidget(row, 0)
            end_spin = self.table.cellWidget(row, 1)
            
            if start_spin and end_spin:
                start_page = start_spin.value()
                end_page = end_spin.value()
                
                if start_page <= end_page:
                    page_ranges.append((start_page, end_page))
        
        if not page_ranges:
            QMessageBox.warning(self, "Warning", "Please specify at least one valid page range")
            return
        
        self.page_ranges = page_ranges
        self.accept()
        
    def get_page_ranges(self):
        """Get the specified page ranges"""
        return self.page_ranges

class PageListDialog(QDialog):
    """Dialog for specifying individual pages"""
    
    def __init__(self, parent=None, total_pages=0):
        super().__init__(parent)
        self.total_pages = total_pages
        self.selected_pages = []
        self.initUI()
        
    def initUI(self):
        """Initialize the dialog UI"""
        self.setWindowTitle("Select Pages")
        self.setMinimumWidth(300)
        self.setMinimumHeight(400)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Information label
        info_label = QLabel(f"Total pages in document: {self.total_pages}")
        layout.addWidget(info_label)
        
        instruction_label = QLabel("Select pages to extract/remove:")
        layout.addWidget(instruction_label)
        
        # Create checkbox container with scrolling
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        
        scroll_content = QWidget()
        self.checkboxes_layout = QVBoxLayout(scroll_content)
        
        # Add checkboxes for pages
        for i in range(1, self.total_pages + 1):
            cb = QCheckBox(f"Page {i}")
            self.checkboxes_layout.addWidget(cb)
        
        scroll_area.setWidget(scroll_content)
        
        # Quick select buttons
        quick_select_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self.select_all)
        quick_select_layout.addWidget(select_all_btn)
        
        select_none_btn = QPushButton("Select None")
        select_none_btn.clicked.connect(self.select_none)
        quick_select_layout.addWidget(select_none_btn)
        
        select_odd_btn = QPushButton("Odd Pages")
        select_odd_btn.clicked.connect(self.select_odd)
        quick_select_layout.addWidget(select_odd_btn)
        
        select_even_btn = QPushButton("Even Pages")
        select_even_btn.clicked.connect(self.select_even)
        quick_select_layout.addWidget(select_even_btn)
        
        layout.addLayout(quick_select_layout)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def select_all(self):
        """Select all pages"""
        for i in range(self.checkboxes_layout.count()):
            checkbox = self.checkboxes_layout.itemAt(i).widget()
            if isinstance(checkbox, QCheckBox):
                checkbox.setChecked(True)
    
    def select_none(self):
        """Deselect all pages"""
        for i in range(self.checkboxes_layout.count()):
            checkbox = self.checkboxes_layout.itemAt(i).widget()
            if isinstance(checkbox, QCheckBox):
                checkbox.setChecked(False)
    
    def select_odd(self):
        """Select odd-numbered pages"""
        for i in range(self.checkboxes_layout.count()):
            checkbox = self.checkboxes_layout.itemAt(i).widget()
            if isinstance(checkbox, QCheckBox):
                page_num = i + 1  # Page numbers are 1-indexed
                checkbox.setChecked(page_num % 2 == 1)
    
    def select_even(self):
        """Select even-numbered pages"""
        for i in range(self.checkboxes_layout.count()):
            checkbox = self.checkboxes_layout.itemAt(i).widget()
            if isinstance(checkbox, QCheckBox):
                page_num = i + 1  # Page numbers are 1-indexed
                checkbox.setChecked(page_num % 2 == 0)
    
    def validate_and_accept(self):
        """Validate inputs and accept the dialog"""
        selected_pages = []
        
        for i in range(self.checkboxes_layout.count()):
            checkbox = self.checkboxes_layout.itemAt(i).widget()
            if isinstance(checkbox, QCheckBox) and checkbox.isChecked():
                page_num = i + 1  # Convert to 1-indexed
                selected_pages.append(page_num)
        
        if not selected_pages:
            QMessageBox.warning(self, "Warning", "Please select at least one page")
            return
        
        self.selected_pages = selected_pages
        self.accept()
        
    def get_selected_pages(self):
        """Get the selected pages"""
        return self.selected_pages

class PDFSplitterWidget(QWidget):
    """Widget for PDF splitting functionality"""
    
    def __init__(self, parent=None, file_list_controller=None, settings_controller=None):
        super().__init__(parent)
        self.logger = Logger()
        self.splitter_controller = PDFSplitterController(self)
        self.file_list_controller = file_list_controller
        
        # Initialize settings controller
        if settings_controller:
            self.settings_controller = settings_controller
        else:
            from settings_controller import SettingsController
            self.settings_controller = SettingsController()
            self.settings_controller.load_settings()
        
        # Connect controller signals
        self.splitter_controller.progress_signal.connect(self.update_progress)
        self.splitter_controller.status_signal.connect(self.update_status)
        self.splitter_controller.complete_signal.connect(self.split_complete)
        self.splitter_controller.file_progress_signal.connect(self.update_file_progress)
        self.splitter_controller.batch_complete_signal.connect(self.batch_file_complete)
        
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
        self.add_pdf_btn.setObjectName("split_add_pdf_btn")  # Set object name for tutorial system
        self.add_pdf_btn.clicked.connect(self.add_pdfs)
        pdf_buttons_layout.addWidget(self.add_pdf_btn)
        
        self.add_folder_btn = QPushButton("Scan Directory")
        self.add_folder_btn.setObjectName("split_add_folder_btn")  # Set object name for tutorial system
        self.add_folder_btn.clicked.connect(self.add_folder)
        pdf_buttons_layout.addWidget(self.add_folder_btn)
        
        self.remove_pdf_btn = QPushButton("Remove Selected")
        self.remove_pdf_btn.clicked.connect(self.remove_selected_pdfs)
        pdf_buttons_layout.addWidget(self.remove_pdf_btn)
        
        self.clear_pdfs_btn = QPushButton("Clear All")
        self.clear_pdfs_btn.clicked.connect(self.clear_all_pdfs)
        pdf_buttons_layout.addWidget(self.clear_pdfs_btn)
        
        pdf_layout.addLayout(pdf_buttons_layout)
        
        # PDF list
        self.pdf_list = PDFListWidget()
        self.pdf_list.setObjectName("split_pdf_list")  # Set object name for tutorial system
        # Connect file list controller signals if available
        if self.file_list_controller:
            # whenever the controller adds a few, append them
            self.file_list_controller.items_appended.connect(self.pdf_list.addItems)
            # whenever the controller does a full reset/clear, rebuild
            self.file_list_controller.files_updated.connect(self._on_full_update)
        
        self.pdf_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.pdf_list.setAcceptDrops(True)
        pdf_layout.addWidget(self.pdf_list)
        
        # Add to main layout
        main_layout.addWidget(pdf_group)
        
        # Split options section
        options_group = QGroupBox("Split Options")
        options_layout = QVBoxLayout(options_group)
        
        # Split mode selection
        mode_layout = QFormLayout()
        self.split_mode_combo = QComboBox()
        self.split_mode_combo.setObjectName("split_mode_combo")  # Set object name for tutorial system
        
        # Add split modes to combo box
        for mode, description in self.splitter_controller.get_available_split_modes():
            self.split_mode_combo.addItem(description, mode)
        
        self.split_mode_combo.currentIndexChanged.connect(self.split_mode_changed)
        mode_layout.addRow("Split Mode:", self.split_mode_combo)
        options_layout.addLayout(mode_layout)
        
        # Option-specific settings (stacked based on selected mode)
        self.options_container = QWidget()
        self.options_layout = QFormLayout(self.options_container)
        options_layout.addWidget(self.options_container)
        
        # Initial option for BY_PAGE_COUNT mode
        self.pages_per_file_spin = QSpinBox()
        self.pages_per_file_spin.setMinimum(1)
        self.pages_per_file_spin.setMaximum(1000)
        self.pages_per_file_spin.setValue(1)
        self.options_layout.addRow("Pages per file:", self.pages_per_file_spin)
        
        # Output options
        output_layout = QFormLayout()
        
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setReadOnly(True)
        
        output_dir_layout = QHBoxLayout()
        output_dir_layout.addWidget(self.output_dir_edit)
        
        self.browse_output_btn = QPushButton("Browse...")
        self.browse_output_btn.setObjectName("split_browse_output_btn")  # Set object name for tutorial system
        self.browse_output_btn.clicked.connect(self.browse_output_dir)
        output_dir_layout.addWidget(self.browse_output_btn)
        
        output_layout.addRow("Output Directory:", output_dir_layout)
        options_layout.addLayout(output_layout)
        
        # Add to main layout
        main_layout.addWidget(options_group)
        
        # Progress section
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        # File progress (for batch processing)
        file_progress_layout = QHBoxLayout()
        file_progress_layout.addWidget(QLabel("File Progress:"))
        self.file_progress_bar = QProgressBar()
        file_progress_layout.addWidget(self.file_progress_bar)
        progress_layout.addLayout(file_progress_layout)
        
        # Page progress
        page_progress_layout = QHBoxLayout()
        page_progress_layout.addWidget(QLabel("Page Progress:"))
        self.page_progress_bar = QProgressBar()
        page_progress_layout.addWidget(self.page_progress_bar)
        progress_layout.addLayout(page_progress_layout)
        
        # Status label
        self.status_label = QLabel("Ready")
        progress_layout.addWidget(self.status_label)
        
        # Add to main layout
        main_layout.addWidget(progress_group)
        
        # Action buttons
        actions_layout = QHBoxLayout()
        
        self.split_btn = QPushButton("Split PDF(s)")
        self.split_btn.setObjectName("split_btn")  # Set object name for tutorial system
        self.split_btn.clicked.connect(self.start_split)
        actions_layout.addWidget(self.split_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.cancel_split)
        self.cancel_btn.setEnabled(False)
        actions_layout.addWidget(self.cancel_btn)
        
        self.open_output_btn = QPushButton("Open Output Folder")
        self.open_output_btn.clicked.connect(self.open_output_folder)
        actions_layout.addWidget(self.open_output_btn)
        
        main_layout.addLayout(actions_layout)
        
        # Set default output directory from settings
        default_split_dir = self.settings_controller.get_setting(
            "pdf", "default_split_dir", 
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "split_output")
        )
        self.output_dir_edit.setText(default_split_dir)
        
        # Ensure the directory exists
        os.makedirs(default_split_dir, exist_ok=True)
        
        # Initialize UI state
        self.split_mode_changed(0)
        
    def split_mode_changed(self, index):
        """Update the UI based on the selected split mode"""
        # Clear existing option widgets
        while self.options_layout.count() > 0:
            item = self.options_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Get the selected mode
        mode = self.split_mode_combo.currentData()
        
        # Add mode-specific options
        if mode == SplitMode.BY_PAGE_COUNT:
            self.pages_per_file_spin = QSpinBox()
            self.pages_per_file_spin.setMinimum(1)
            self.pages_per_file_spin.setMaximum(1000)
            self.pages_per_file_spin.setValue(1)
            self.options_layout.addRow("Pages per file:", self.pages_per_file_spin)
        
        elif mode == SplitMode.BY_RANGES:
            self.ranges_btn = QPushButton("Specify Page Ranges...")
            self.ranges_btn.clicked.connect(self.specify_page_ranges)
            self.options_layout.addRow("Page Ranges:", self.ranges_btn)
            
            self.ranges_label = QLabel("No ranges specified")
            self.options_layout.addRow("", self.ranges_label)
            self.page_ranges = []
        
        elif mode == SplitMode.EXTRACT_PAGES:
            self.pages_btn = QPushButton("Select Pages...")
            self.pages_btn.clicked.connect(self.select_pages_to_extract)
            self.options_layout.addRow("Pages to Extract:", self.pages_btn)
            
            self.pages_label = QLabel("No pages selected")
            self.options_layout.addRow("", self.pages_label)
            self.selected_pages = []
        
        elif mode == SplitMode.EVERY_N_PAGES:
            self.every_n_spin = QSpinBox()
            self.every_n_spin.setMinimum(1)
            self.every_n_spin.setMaximum(1000)
            self.every_n_spin.setValue(2)
            self.options_layout.addRow("Extract every N pages:", self.every_n_spin)
            
            self.start_at_spin = QSpinBox()
            self.start_at_spin.setMinimum(0)
            self.start_at_spin.setMaximum(1000)
            self.start_at_spin.setValue(0)
            self.options_layout.addRow("Start at page (0-indexed):", self.start_at_spin)
        
        elif mode == SplitMode.REMOVE_PAGES:
            self.remove_btn = QPushButton("Select Pages to Remove...")
            self.remove_btn.clicked.connect(self.select_pages_to_remove)
            self.options_layout.addRow("Pages to Remove:", self.remove_btn)
            
            self.remove_label = QLabel("No pages selected for removal")
            self.options_layout.addRow("", self.remove_label)
            self.pages_to_remove = []
        
        # No special options needed for SPLIT_EVERY_PAGE
        
    def _on_full_update(self, files: list[str]):
        """Handle full update of file list from controller"""
        self.pdf_list.clear()
        self.pdf_list.addItems(files)
        
    def add_pdfs(self):
        """Add PDFs to the list via file dialog"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Select PDFs to Split", "", "PDF Files (*.pdf)"
        )
        
        if file_paths:
            # Filter for valid PDFs
            valid_files = self.splitter_controller.validate_pdfs(file_paths)
            
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
        """Add all PDFs from a folder using the directory scanner"""
        # Disable until scan ends
        self.add_folder_btn.setEnabled(False)   

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
            self.add_folder_btn.setEnabled(True)
            if self.file_list_controller:
                self.file_list_controller.enable_updates()
            self.status_label.setText("Directory scan complete")
            
        self.scanner.scan_complete.connect(on_scan_complete)

        # Kick off the built‑in folder dialog + scan
        self.scanner.start_scan()
    
    def _validate_pdf_batch_threaded(self, pdf_batch, progress_callback=None, cancel_check=None):
        """Validate a batch of PDF files in a worker thread"""
        valid_batch = []
        total_files = len(pdf_batch)
        
        for index, pdf_file in enumerate(pdf_batch):
            # Check for cancellation
            if cancel_check and cancel_check():
                break
                
            # Update progress
            if progress_callback:
                filename = os.path.basename(pdf_file)
                progress_callback(f"Validating {index + 1}/{total_files}: {filename}")
                
            try:
                if self.splitter_controller.is_valid_pdf(pdf_file):
                    valid_batch.append(pdf_file)
            except Exception as e:
                # Log validation error but continue processing other files
                error_msg = f"Error validating {os.path.basename(pdf_file)}: {str(e)}"
                self.logger.warning("PDFSplitterWidget", error_msg)
                continue
        
        return valid_batch
    
    def _handle_validation_complete(self, valid_batch, progress_dialog):
        """Handle completion of threaded PDF validation"""
        try:
            # Close the progress dialog
            progress_dialog.close()
            
            # Add valid files to the list
            added_count = 0
            for pdf_file in valid_batch:
                if self.pdf_list.findItems(pdf_file, Qt.MatchFlag.MatchExactly) == []:
                    self.pdf_list.addItem(pdf_file)
                    added_count += 1
            
            # Update shared file list if controller exists
            if self.file_list_controller:
                self.file_list_controller.add_files(valid_batch)
                    
            # Update status
            status_msg = f"Added {added_count} valid PDFs from batch of {len(valid_batch)} validated"
            self.status_label.setText(status_msg)
            self.logger.info("PDFSplitterWidget", f"Batch processing complete: {status_msg}")
            
        except Exception as e:
            error_msg = f"Error processing validation results: {str(e)}"
            self.status_label.setText(error_msg)
            self.logger.error("PDFSplitterWidget", error_msg)
    
    def _handle_validation_error(self, error_message, progress_dialog):
        """Handle error during threaded PDF validation"""
        progress_dialog.close()
        error_msg = f"PDF validation failed: {error_message}"
        self.status_label.setText(error_msg)
        self.logger.error("PDFSplitterWidget", error_msg)
        QMessageBox.warning(self, "Validation Error", error_msg)
    
    def _handle_validation_cancelled(self, progress_dialog):
        """Handle cancellation of threaded PDF validation"""
        progress_dialog.close()
        self.status_label.setText("PDF validation cancelled")
        self.logger.info("PDFSplitterWidget", "PDF validation cancelled by user")
                
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
            
    def browse_output_dir(self):
        """Browse for output directory"""
        current_dir = self.output_dir_edit.text()
        directory = QFileDialog.getExistingDirectory(
            self, "Select Output Directory", current_dir
        )
        
        if directory:
            self.output_dir_edit.setText(directory)
            
    def specify_page_ranges(self):
        """Open dialog to specify page ranges"""
        # Get selected PDF file to determine total pages
        selected_items = self.pdf_list.selectedItems()
        
        if not selected_items:
            QMessageBox.warning(
                self, 
                "No PDF Selected", 
                "Please select a PDF file to get its page count for range specification."
            )
            return
        
        pdf_file = selected_items[0].text()
        total_pages = self.splitter_controller.get_pdf_page_count(pdf_file)
        
        if total_pages == 0:
            QMessageBox.warning(
                self, 
                "Invalid PDF", 
                "Could not determine page count for the selected PDF."
            )
            return
        
        # Show the dialog
        dialog = PageRangeDialog(self, total_pages)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.page_ranges = dialog.get_page_ranges()
            
            # Update the label
            range_str = ", ".join([f"{start}-{end}" for start, end in self.page_ranges])
            self.ranges_label.setText(f"Ranges: {range_str}")
            
    def select_pages_to_extract(self):
        """Open dialog to select pages to extract"""
        # Get selected PDF file to determine total pages
        selected_items = self.pdf_list.selectedItems()
        
        if not selected_items:
            QMessageBox.warning(
                self, 
                "No PDF Selected", 
                "Please select a PDF file to get its page count for page selection."
            )
            return
        
        pdf_file = selected_items[0].text()
        total_pages = self.splitter_controller.get_pdf_page_count(pdf_file)
        
        if total_pages == 0:
            QMessageBox.warning(
                self, 
                "Invalid PDF", 
                "Could not determine page count for the selected PDF."
            )
            return
        
        # Show the dialog
        dialog = PageListDialog(self, total_pages)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.selected_pages = dialog.get_selected_pages()
            
            # Update the label
            if len(self.selected_pages) > 5:
                pages_str = ", ".join([str(p) for p in self.selected_pages[:5]]) + f"... ({len(self.selected_pages)} total)"
            else:
                pages_str = ", ".join([str(p) for p in self.selected_pages])
                
            self.pages_label.setText(f"Selected pages: {pages_str}")
            
    def select_pages_to_remove(self):
        """Open dialog to select pages to remove"""
        # Get selected PDF file to determine total pages
        selected_items = self.pdf_list.selectedItems()
        
        if not selected_items:
            QMessageBox.warning(
                self, 
                "No PDF Selected", 
                "Please select a PDF file to get its page count for page selection."
            )
            return
        
        pdf_file = selected_items[0].text()
        total_pages = self.splitter_controller.get_pdf_page_count(pdf_file)
        
        if total_pages == 0:
            QMessageBox.warning(
                self, 
                "Invalid PDF", 
                "Could not determine page count for the selected PDF."
            )
            return
        
        # Show the dialog
        dialog = PageListDialog(self, total_pages)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.pages_to_remove = dialog.get_selected_pages()
            
            # Update the label
            if len(self.pages_to_remove) > 5:
                pages_str = ", ".join([str(p) for p in self.pages_to_remove[:5]]) + f"... ({len(self.pages_to_remove)} total)"
            else:
                pages_str = ", ".join([str(p) for p in self.pages_to_remove])
                
            self.remove_label.setText(f"Pages to remove: {pages_str}")
            
    def start_split(self):
        """Start the split operation"""
        # Get the PDF files
        pdf_files = []
        for i in range(self.pdf_list.count()):
            pdf_files.append(self.pdf_list.item(i).text())
        
        if not pdf_files:
            QMessageBox.warning(
                self, 
                "No PDFs", 
                "Please add at least one PDF file to split."
            )
            return
        
        # Get the output directory
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
        
        # Get the split mode
        split_mode = self.split_mode_combo.currentData()
        
        # Prepare split parameters based on the selected mode
        split_params = {}
        
        if split_mode == SplitMode.BY_PAGE_COUNT:
            split_params = {'pages_per_file': self.pages_per_file_spin.value()}
            
        elif split_mode == SplitMode.BY_RANGES:
            if not hasattr(self, 'page_ranges') or not self.page_ranges:
                QMessageBox.warning(
                    self, 
                    "No Page Ranges", 
                    "Please specify at least one page range."
                )
                return
            split_params = {'ranges': self.page_ranges}
            
        elif split_mode == SplitMode.EXTRACT_PAGES:
            if not hasattr(self, 'selected_pages') or not self.selected_pages:
                QMessageBox.warning(
                    self, 
                    "No Pages Selected", 
                    "Please select at least one page to extract."
                )
                return
            split_params = {'pages': self.selected_pages}
            
        elif split_mode == SplitMode.EVERY_N_PAGES:
            split_params = {
                'n': self.every_n_spin.value(),
                'start_at': self.start_at_spin.value()
            }
            
        elif split_mode == SplitMode.REMOVE_PAGES:
            if not hasattr(self, 'pages_to_remove') or not self.pages_to_remove:
                QMessageBox.warning(
                    self, 
                    "No Pages Selected", 
                    "Please select at least one page to remove."
                )
                return
            split_params = {'pages': self.pages_to_remove}
        
        # Start the split operation
        if len(pdf_files) == 1:
            # Single file mode
            self.splitter_controller.split_pdf(
                pdf_files[0],
                output_dir,
                split_mode,
                split_params
            )
        else:
            # Batch mode
            self.splitter_controller.batch_split_pdfs(
                pdf_files,
                output_dir,
                split_mode,
                split_params
            )
        
        # Update UI state
        self.update_ui_for_split_started()
        
    def cancel_split(self):
        """Cancel the current split operation"""
        if self.splitter_controller.cancel_split():
            self.status_label.setText("Cancelling split operation...")
            
    def update_progress(self, current, total):
        """Update the page progress bar"""
        self.page_progress_bar.setMaximum(total)
        self.page_progress_bar.setValue(current)
        
    def update_file_progress(self, current, total, filename):
        """Update the file progress bar for batch processing"""
        self.file_progress_bar.setMaximum(total)
        self.file_progress_bar.setValue(current)
        self.status_label.setText(f"Processing file {current}/{total}: {filename}")
        
    def update_status(self, status):
        """Update the status label"""
        self.status_label.setText(status)
        
    def split_complete(self, success, message):
        """Handle split completion"""
        self.update_ui_for_split_completed()
        
        if success:
            self.status_label.setText(message)
            
            # Ask if user wants to open the output folder
            result = QMessageBox.question(
                self,
                "Split Complete",
                f"{message}\n\nWould you like to open the output folder?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if result == QMessageBox.StandardButton.Yes:
                self.open_output_folder()
        else:
            self.status_label.setText(f"Error: {message}")
            QMessageBox.critical(self, "Split Error", message)
            
    def batch_file_complete(self, output_files):
        """Handle completion of a single file in batch mode"""
        # This method is called when a single file in a batch is processed
        pass
        
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
                
    def update_ui_for_split_started(self):
        """Update UI state when split starts"""
        self.split_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.add_pdf_btn.setEnabled(False)
        self.add_folder_btn.setEnabled(False)
        self.remove_pdf_btn.setEnabled(False)
        self.clear_pdfs_btn.setEnabled(False)
        self.browse_output_btn.setEnabled(False)
        
    def update_ui_for_split_completed(self):
        """Update UI state when split completes"""
        self.split_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.add_pdf_btn.setEnabled(True)
        self.add_folder_btn.setEnabled(True)
        self.remove_pdf_btn.setEnabled(True)
        self.clear_pdfs_btn.setEnabled(True)
        self.browse_output_btn.setEnabled(True)
