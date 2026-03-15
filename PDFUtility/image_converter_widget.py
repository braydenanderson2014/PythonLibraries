#!/usr/bin/env python3
# image_converter_widget.py - UI for Image Conversion functionality

import os
import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QCheckBox,
    QLineEdit, QFileDialog, QProgressBar, QAbstractItemView, QGroupBox,
    QFormLayout, QMessageBox, QListWidget
)
from PyQt6.QtCore import Qt, QSize

from image_control import ImageControl
from PDFListWidget import PDFListWidget
from PDFLogger import Logger

class ImageConverterWidget(QWidget):
    """Widget for Image Conversion functionality"""
    
    def __init__(self, parent=None, file_list_controller=None):
        super().__init__(parent)
        self.logger = Logger()
        self.image_controller = ImageControl(self)
        self.scanner = None  # Track current scanner
        self.scan_session_id = 0  # Track scan sessions to prevent stale results
        self.file_list_controller = file_list_controller  # For sharing PDFs only
        
        # Connect controller signals
        self.image_controller.progress_signal.connect(self.update_progress)
        self.image_controller.status_signal.connect(self.update_status)
        self.image_controller.complete_signal.connect(self.conversion_complete)
        self.image_controller.converted_signal.connect(self.add_converted_files)
        self.image_controller.files_found_signal.connect(self.add_found_files)
        
        self.initUI()
        
    def initUI(self):
        """Initialize the UI elements"""
        main_layout = QVBoxLayout(self)
        
        # File section
        files_group = QGroupBox("Files")
        files_layout = QVBoxLayout(files_group)
        
        files_buttons_layout = QHBoxLayout()
        self.add_images_btn = QPushButton("Add Images")
        self.add_images_btn.setObjectName("image_add_images_btn")  # Set object name for tutorial system
        self.add_images_btn.clicked.connect(self.add_images)
        files_buttons_layout.addWidget(self.add_images_btn)
        
        self.add_folder_btn = QPushButton("Scan Directory")
        self.add_folder_btn.setObjectName("image_add_folder_btn")  # Set object name for tutorial system
        self.add_folder_btn.clicked.connect(self.add_folder)
        files_buttons_layout.addWidget(self.add_folder_btn)
        
        self.remove_selected_btn = QPushButton("Remove Selected")
        self.remove_selected_btn.setObjectName("image_remove_selected_btn")  # Set object name for tutorial system
        self.remove_selected_btn.clicked.connect(self.remove_selected_files)
        files_buttons_layout.addWidget(self.remove_selected_btn)
        
        self.clear_all_btn = QPushButton("Clear All")
        self.clear_all_btn.clicked.connect(self.clear_all_files)
        self.clear_all_btn.setObjectName("image_clear_all_btn")  # Set object name for tutorial system
        files_buttons_layout.addWidget(self.clear_all_btn)
        
        self.copy_pdfs_btn = QPushButton("Copy PDFs to Other Widgets")
        self.copy_pdfs_btn.clicked.connect(self.copy_pdfs_to_shared_list)
        self.copy_pdfs_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }")
        self.copy_pdfs_btn.setToolTip("Copy only PDF files from this widget to the shared file lists in other widgets")
        self.copy_pdfs_btn.setObjectName("image_copy_pdfs_btn")  # Set object name for tutorial system
        files_buttons_layout.addWidget(self.copy_pdfs_btn)
        
        files_layout.addLayout(files_buttons_layout)
        
        # File list (independent - not shared with other widgets)
        self.file_list = QListWidget()
        self.file_list.setObjectName("image_file_list")  # Set object name for tutorial system
        self.file_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.file_list.setAcceptDrops(True)
        files_layout.addWidget(self.file_list)
        
        # Hidden PDFListWidget for sharing with other widgets (PDFs only)
        if self.file_list_controller:
            self.shared_pdf_list = PDFListWidget()
            self.shared_pdf_list.setVisible(False)  # Hide it from UI
            self.file_list_controller.items_appended.connect(self.shared_pdf_list.addItems)
            self.file_list_controller.files_updated.connect(self._on_shared_list_update)
            files_layout.addWidget(self.shared_pdf_list)  # Add to layout but hidden
        
        main_layout.addWidget(files_group)
        
        # Conversion options
        options_group = QGroupBox("Conversion Options")
        options_layout = QVBoxLayout(options_group)
        
        # PDF to Image options
        pdf_to_image_layout = QHBoxLayout()
        self.pdf_to_img_btn = QPushButton("Convert PDF to Images")
        self.pdf_to_img_btn.clicked.connect(self.convert_pdf_to_images)
        self.pdf_to_img_btn.setObjectName("image_pdf_to_img_btn")  # Set object name for tutorial system
        pdf_to_image_layout.addWidget(self.pdf_to_img_btn)
        
        options_layout.addLayout(pdf_to_image_layout)
        
        # Image to PDF options
        img_to_pdf_layout = QHBoxLayout()
        self.img_to_pdf_btn = QPushButton("Convert Images to PDF")
        self.img_to_pdf_btn.clicked.connect(self.convert_images_to_pdf)
        self.img_to_pdf_btn.setObjectName("image_img_to_pdf_btn")  # Set object name for tutorial system
        img_to_pdf_layout.addWidget(self.img_to_pdf_btn)
        
        options_layout.addLayout(img_to_pdf_layout)
        
        main_layout.addWidget(options_group)
        
        # Status and progress
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Ready")
        status_layout.addWidget(self.status_label)
        main_layout.addLayout(status_layout)
        
        progress_layout = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        main_layout.addLayout(progress_layout)

    def _on_shared_list_update(self, files: list[str]):
        """Handle full update of shared PDF list (keep it hidden)"""
        if hasattr(self, 'shared_pdf_list'):
            self.shared_pdf_list.clear()
            self.shared_pdf_list.addItems(files)

    def copy_pdfs_to_shared_list(self):
        """Copy only PDF files from the local list to the shared controller"""
        if not self.file_list_controller:
            QMessageBox.information(self, "No Shared Controller", "No shared file list controller available.")
            return
            
        # Get all files from the local list
        all_files = []
        for i in range(self.file_list.count()):
            all_files.append(self.file_list.item(i).text())
        
        # Filter for PDF files only
        pdf_files = [f for f in all_files if f.lower().endswith('.pdf')]
        
        if not pdf_files:
            QMessageBox.information(self, "No PDFs", "No PDF files found to copy to other widgets.")
            return
        
        # Add PDF files to the shared controller
        self.file_list_controller.add_files(pdf_files)
        
        # Update status
        self.status_label.setText(f"Copied {len(pdf_files)} PDF file(s) to other widgets")
        self.logger.info("ImageConverter", f"Copied {len(pdf_files)} PDF files to shared controller")

    def add_images(self):
        """Add images to the list via file dialog"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Select Images", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.tiff);;All Files (*.*)"
        )
        
        if file_paths:
            # Add to list (only to this widget's list, not shared)
            for file_path in file_paths:
                if self.file_list.findItems(file_path, Qt.MatchFlag.MatchExactly) == []:
                    self.file_list.addItem(file_path)
                
    def add_folder(self):
        """Add files from a folder using the file type directory scanner"""
        # Stop any existing scanner first
        self._stop_current_scanner()
        
        # Increment session ID to invalidate any pending results
        self.scan_session_id += 1
        current_session = self.scan_session_id
        
        # Show file type selection dialog
        from file_type_selection_dialog import FileTypeSelectionDialog
        
        dialog = FileTypeSelectionDialog(self, "Select File Types to Scan")
        if dialog.exec() != dialog.DialogCode.Accepted:
            return
            
        selected_types = dialog.get_selected_types()
        if not selected_types:
            # Default to common image types if nothing selected
            selected_types = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"]
        
        # Debug logging
        self.logger.info("ImageConverter", f"Selected file types for scan: {selected_types}")
        
        # Disable until scan ends
        self.add_folder_btn.setEnabled(False)   

        # Create a session-aware file collector for this widget only
        class ImageFileCollector:
            def __init__(self, widget, session_id):
                self.widget = widget
                self.session_id = session_id
                self.files = []
                self._cancelled = False
                
            def add_files(self, file_list):
                """Add files to our local list only if session is still valid"""
                # Check if this collector has been cancelled
                if self._cancelled:
                    self.widget.logger.info("ImageFileCollector", "Ignoring files - collector cancelled")
                    return
                    
                # Check if this session is still active
                if self.widget.scan_session_id != self.session_id:
                    self.widget.logger.info("ImageFileCollector", f"Ignoring stale results from session {self.session_id}")
                    return
                
                # Debug: Log what files are being added
                self.widget.logger.info("ImageFileCollector", f"Adding {len(file_list)} files: {file_list[:5]}{'...' if len(file_list) > 5 else ''}")
                    
                self.files.extend(file_list)
                # Add directly to the widget's list
                for file_path in file_list:
                    if self.widget.file_list.findItems(file_path, Qt.MatchFlag.MatchExactly) == []:
                        self.widget.file_list.addItem(file_path)
            
            def get_files(self):
                return self.files
            
            def disable_updates(self):
                pass  # No-op for independent widget
            
            def enable_updates(self):
                pass  # No-op for independent widget
            
            def cancel(self):
                """Cancel this collector to prevent further file additions"""
                self._cancelled = True
        
        collector = ImageFileCollector(self, current_session)
        
        from file_type_directory_scanner import FileDirectoryScanner
        
        # Use first selected type as the primary pattern (for progress messages)
        primary_type = selected_types[0] if selected_types else ".jpg"
        self.scanner = FileDirectoryScanner(
            parent=self,
            file_list_controller=collector,  # Use our local collector
            batch_size=50,
            file_pattern=primary_type
        )   
        
        # Set all selected types for multi-type scanning
        self.scanner.set_selected_types(selected_types)

        # Re‑enable the button when the scan completes
        def on_scan_complete():
            # Only process completion if this is still the current session
            if self.scan_session_id == current_session:
                self.add_folder_btn.setEnabled(True)
                types_str = ", ".join(selected_types)
                self.status_label.setText(f"Directory scan complete for: {types_str}")
            else:
                self.logger.info("ImageConverter", f"Ignoring completion from stale session {current_session}")
            
        self.scanner.scan_complete.connect(on_scan_complete)

        # Kick off the built‑in folder dialog + scan
        self.scanner.start_scan()
    
    def _stop_current_scanner(self):
        """Stop any currently running scanner"""
        if self.scanner:
            try:
                # Cancel the file list controller if it has a cancel method
                if hasattr(self.scanner, 'file_list_controller') and hasattr(self.scanner.file_list_controller, 'cancel'):
                    self.scanner.file_list_controller.cancel()
                    self.logger.info("ImageConverter", "Cancelled file collector")
                
                # Cancel the scanner if it's running
                if hasattr(self.scanner, '_scan_thread') and self.scanner._scan_thread:
                    if self.scanner._scan_thread.isRunning():
                        self.scanner._scan_thread.cancel()
                        self.logger.info("ImageConverter", "Cancelled running scanner thread")
                
                # Close any dialog
                if hasattr(self.scanner, '_dialog') and self.scanner._dialog:
                    self.scanner._dialog.close()
                    self.scanner._dialog = None
                    
            except Exception as e:
                self.logger.error("ImageConverter", f"Error stopping scanner: {e}")
            
            self.scanner = None
        
        # Re-enable the scan button
        self.add_folder_btn.setEnabled(True)
    
    def add_found_files(self, file_list):
        """Add files found by the directory scanner"""
        # Note: This method is connected to image_controller signals,
        # not the directory scanner, so no session check needed here
        if not file_list:
            self.status_label.setText("No image files found in folder")
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            return
            
        # Add to list (only this widget's list)
        for file_path in file_list:
            if self.file_list.findItems(file_path, Qt.MatchFlag.MatchExactly) == []:
                self.file_list.addItem(file_path)
            
        self.status_label.setText(f"Added {len(file_list)} image(s) from folder")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
            
    def remove_selected_files(self):
        """Remove selected files from the list"""
        selected_items = self.file_list.selectedItems()
        
        for item in selected_items:
            self.file_list.takeItem(self.file_list.row(item))
            
    def clear_all_files(self):
        """Clear all files from the list and stop any running scans"""
        # Stop any running scanner first
        self._stop_current_scanner()
        
        # Increment session ID to invalidate any pending results
        self.scan_session_id += 1
        
        # Clear the file list
        self.file_list.clear()
        
        # Reset status
        self.status_label.setText("Ready")
        self.progress_bar.setValue(0)
        
        self.logger.info("ImageConverter", f"Cleared all files and started new session {self.scan_session_id}")
    
    def closeEvent(self, event):
        """Handle widget close event"""
        self._stop_current_scanner()
        super().closeEvent(event)
    
    def __del__(self):
        """Cleanup when widget is destroyed"""
        try:
            self._stop_current_scanner()
        except:
            pass  # Ignore errors during cleanup
            
    def convert_images_to_pdf(self):
        """Convert selected images to PDF"""
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select images to convert.")
            return
            
        image_paths = [item.text() for item in selected_items]
        self.image_controller.convert_images_to_pdf(image_paths)
        
    def convert_pdf_to_images(self):
        """Convert selected PDF to images"""
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a PDF file to convert.")
            return
            
        pdf_path = selected_items[0].text()
        if not pdf_path.lower().endswith('.pdf'):
            QMessageBox.warning(self, "Invalid Selection", "Please select a PDF file.")
            return
            
        self.image_controller.pdf_to_images(pdf_path)
        
    def update_progress(self, current, total):
        """Update the progress bar"""
        percentage = int(current / total * 100) if total > 0 else 0
        self.progress_bar.setValue(percentage)
        
    def update_status(self, status_text):
        """Update the status label"""
        self.status_label.setText(status_text)
        
    def conversion_complete(self, success, message):
        """Handle conversion completion"""
        if success:
            self.status_label.setText("Conversion complete")
            self.progress_bar.setValue(100)
        else:
            self.status_label.setText("Conversion failed")
        
        QMessageBox.information(self, "Conversion Result", message)
        
    def add_converted_files(self, file_paths):
        """Add converted files to the list"""
        for file_path in file_paths:
            if self.file_list.findItems(file_path, Qt.MatchFlag.MatchExactly) == []:
                self.file_list.addItem(file_path)
            
        self.status_label.setText(f"Added {len(file_paths)} converted file(s)")
