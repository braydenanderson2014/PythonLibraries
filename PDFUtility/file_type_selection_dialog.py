#!/usr/bin/env python3
# file_type_selection_dialog.py - Dialog for selecting file types to scan

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QListWidget, QAbstractItemView, QDialogButtonBox, QCheckBox,
    QLineEdit, QFormLayout, QGroupBox
)
from PyQt6.QtCore import Qt

class FileTypeSelectionDialog(QDialog):
    """Dialog for selecting file types to scan for"""
    
    def __init__(self, parent=None, title="Select File Types"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)
        
        # Common file types for images
        self.common_image_types = [
            ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif",
            ".webp", ".svg", ".ico", ".psd", ".raw", ".cr2", ".nef"
        ]
        
        # Common file types for documents
        self.common_document_types = [
            ".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", 
            ".xls", ".xlsx", ".ppt", ".pptx", ".csv"
        ]
        
        # Common file types for media
        self.common_media_types = [
            ".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a",
            ".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv"
        ]
        
        self.selected_types = []
        self.init_ui()
        
    def init_ui(self):
        """Initialize the dialog UI"""
        layout = QVBoxLayout(self)
        
        # Instructions
        instructions = QLabel("Select file types to scan for, or enter custom extensions:")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Preset categories
        categories_group = QGroupBox("Common File Types")
        categories_layout = QVBoxLayout(categories_group)
        
        # Image files section
        image_layout = QHBoxLayout()
        image_label = QLabel("Images:")
        image_label.setMinimumWidth(80)
        image_layout.addWidget(image_label)
        
        self.image_list = QListWidget()
        self.image_list.addItems(self.common_image_types)
        self.image_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.image_list.setMaximumHeight(100)
        image_layout.addWidget(self.image_list)
        categories_layout.addLayout(image_layout)
        
        # Document files section
        doc_layout = QHBoxLayout()
        doc_label = QLabel("Documents:")
        doc_label.setMinimumWidth(80)
        doc_layout.addWidget(doc_label)
        
        self.doc_list = QListWidget()
        self.doc_list.addItems(self.common_document_types)
        self.doc_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.doc_list.setMaximumHeight(100)
        doc_layout.addWidget(self.doc_list)
        categories_layout.addLayout(doc_layout)
        
        # Media files section
        media_layout = QHBoxLayout()
        media_label = QLabel("Media:")
        media_label.setMinimumWidth(80)
        media_layout.addWidget(media_label)
        
        self.media_list = QListWidget()
        self.media_list.addItems(self.common_media_types)
        self.media_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.media_list.setMaximumHeight(100)
        media_layout.addWidget(self.media_list)
        categories_layout.addLayout(media_layout)
        
        layout.addWidget(categories_group)
        
        # Custom extension input
        custom_group = QGroupBox("Custom Extensions")
        custom_layout = QFormLayout(custom_group)
        
        self.custom_input = QLineEdit()
        self.custom_input.setPlaceholderText("e.g., .txt, .log, .xml (comma-separated)")
        custom_layout.addRow("Custom types:", self.custom_input)
        
        layout.addWidget(custom_group)
        
        # Quick selection buttons
        quick_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("Select All Images")
        select_all_btn.clicked.connect(self.select_all_images)
        quick_layout.addWidget(select_all_btn)
        
        select_docs_btn = QPushButton("Select All Documents")
        select_docs_btn.clicked.connect(self.select_all_documents)
        quick_layout.addWidget(select_docs_btn)
        
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self.clear_all)
        quick_layout.addWidget(clear_btn)
        
        layout.addLayout(quick_layout)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # No default selection - let user choose
        # self.select_all_images()  # Removed automatic selection
        
    def select_all_images(self):
        """Select all image file types and clear others"""
        self.clear_all()  # Clear everything first
        self.image_list.selectAll()
        
    def select_all_documents(self):
        """Select all document file types and clear others"""
        self.clear_all()  # Clear everything first  
        self.doc_list.selectAll()
        
    def clear_all(self):
        """Clear all selections"""
        self.image_list.clearSelection()
        self.doc_list.clearSelection()
        self.media_list.clearSelection()
        self.custom_input.clear()
        
    def get_selected_types(self):
        """Get the list of selected file types"""
        selected_types = []
        
        # Get selected from each category
        for item in self.image_list.selectedItems():
            selected_types.append(item.text())
            
        for item in self.doc_list.selectedItems():
            selected_types.append(item.text())
            
        for item in self.media_list.selectedItems():
            selected_types.append(item.text())
        
        # Get custom types
        custom_text = self.custom_input.text().strip()
        if custom_text:
            custom_types = [t.strip() for t in custom_text.split(",")]
            for custom_type in custom_types:
                if custom_type and not custom_type.startswith("."):
                    custom_type = "." + custom_type
                if custom_type and custom_type not in selected_types:
                    selected_types.append(custom_type)
        
        return selected_types
        
    def accept(self):
        """Accept the dialog and store selected types"""
        self.selected_types = self.get_selected_types()
        if not self.selected_types:
            # Show warning but don't prevent closing
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self, 
                "No Selection", 
                "No file types selected. Scanner will look for all files."
            )
        super().accept()
