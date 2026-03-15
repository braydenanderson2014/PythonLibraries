#!/usr/bin/env python3
"""
PDF Settings Widget
Handles PDF-specific settings like output directories, compression, etc.
"""

import os
import subprocess
import platform
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout, QComboBox, 
    QCheckBox, QLineEdit, QPushButton
)
from PyQt6.QtCore import Qt

from Settings.base_settings_widget import BaseSettingsWidget
from cross_platform_defaults import get_pdf_default_directories

class PDFSettingsWidget(BaseSettingsWidget):
    """PDF settings tab widget"""
    
    def setup_ui(self):
        """Create the PDF settings UI"""
        layout = QVBoxLayout(self)
        
        # PDF settings group
        pdf_group, pdf_layout = self.create_group_box("PDF Settings", QFormLayout)
        
        # Default output directory
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setReadOnly(True)
        self.output_dir_edit.textChanged.connect(self.on_settings_changed)
        
        output_dir_layout = QHBoxLayout()
        output_dir_layout.addWidget(self.output_dir_edit)
        
        output_dir_btn = self.create_styled_button("Browse...", "Select default output directory")
        output_dir_btn.clicked.connect(self.browse_output_dir)
        output_dir_layout.addWidget(output_dir_btn)
        
        output_open_btn = self.create_styled_button("Open", "Open output directory in file manager")
        output_open_btn.clicked.connect(lambda: self.open_directory(self.output_dir_edit.text()))
        output_dir_layout.addWidget(output_open_btn)
        
        pdf_layout.addRow("Default output directory:", output_dir_layout)
        
        # Default merge directory
        self.merge_dir_edit = QLineEdit()
        self.merge_dir_edit.setReadOnly(True)
        self.merge_dir_edit.textChanged.connect(self.on_settings_changed)
        
        merge_dir_layout = QHBoxLayout()
        merge_dir_layout.addWidget(self.merge_dir_edit)
        
        merge_dir_btn = self.create_styled_button("Browse...", "Select default merge directory")
        merge_dir_btn.clicked.connect(self.browse_merge_dir)
        merge_dir_layout.addWidget(merge_dir_btn)
        
        merge_open_btn = self.create_styled_button("Open", "Open merge directory in file manager")
        merge_open_btn.clicked.connect(lambda: self.open_directory(self.merge_dir_edit.text()))
        merge_dir_layout.addWidget(merge_open_btn)
        
        pdf_layout.addRow("Default merge directory:", merge_dir_layout)
        
        # Default split directory
        self.split_dir_edit = QLineEdit()
        self.split_dir_edit.setReadOnly(True)
        self.split_dir_edit.textChanged.connect(self.on_settings_changed)
        
        split_dir_layout = QHBoxLayout()
        split_dir_layout.addWidget(self.split_dir_edit)
        
        split_dir_btn = self.create_styled_button("Browse...", "Select default split directory")
        split_dir_btn.clicked.connect(self.browse_split_dir)
        split_dir_layout.addWidget(split_dir_btn)
        
        split_open_btn = self.create_styled_button("Open", "Open split directory in file manager")
        split_open_btn.clicked.connect(lambda: self.open_directory(self.split_dir_edit.text()))
        split_dir_layout.addWidget(split_open_btn)
        
        pdf_layout.addRow("Default split directory:", split_dir_layout)
        
        # Default behavior checkbox for whitespace removal
        self.remove_white_space_cb = QCheckBox("Remove white space by default")
        self.remove_white_space_cb.setToolTip("Enable automatic white space removal when processing files")
        self.remove_white_space_cb.stateChanged.connect(self.on_settings_changed)
        pdf_layout.addRow("Default behavior:", self.remove_white_space_cb)
        
        # Compression level
        self.compression_combo = QComboBox()
        self.compression_combo.addItems(["None", "Low", "Medium", "High"])
        self.compression_combo.currentTextChanged.connect(self.on_settings_changed)
        pdf_layout.addRow("Compression level:", self.compression_combo)
        
        # Add to layout
        layout.addWidget(pdf_group)
        layout.addStretch()
        
    def load_settings(self):
        """Load PDF settings from the controller"""
        # Get cross-platform defaults
        default_dirs = get_pdf_default_directories()
        
        # Output directory with smart default
        output_dir = self.get_setting("pdf", "default_output_directory", "")
        if not output_dir or not os.path.exists(output_dir):
            output_dir = default_dirs['output']
            # Save the default back to settings
            self.set_setting("pdf", "default_output_directory", output_dir)
        self.output_dir_edit.setText(output_dir)
        
        # Merge directory with smart default
        merge_dir = self.get_setting("pdf", "default_merge_directory", "")
        if not merge_dir or not os.path.exists(merge_dir):
            merge_dir = default_dirs['merge']
            # Save the default back to settings
            self.set_setting("pdf", "default_merge_directory", merge_dir)
        self.merge_dir_edit.setText(merge_dir)
        
        # Split directory with smart default
        split_dir = self.get_setting("pdf", "default_split_directory", "")
        if not split_dir or not os.path.exists(split_dir):
            split_dir = default_dirs['split']
            # Save the default back to settings
            self.set_setting("pdf", "default_split_directory", split_dir)
        self.split_dir_edit.setText(split_dir)
        
        # Remove whitespace default
        remove_whitespace = self.get_setting("pdf", "remove_whitespace_default", False)
        self.remove_white_space_cb.setChecked(remove_whitespace)
        
        # Compression level
        compression = self.get_setting("pdf", "compression_level", "Medium")
        index = self.compression_combo.findText(compression)
        if index >= 0:
            self.compression_combo.setCurrentIndex(index)
            
    def save_settings(self):
        """Save PDF settings to the controller"""
        # Output directory
        self.set_setting("pdf", "default_output_directory", self.output_dir_edit.text())
        
        # Merge directory
        self.set_setting("pdf", "default_merge_directory", self.merge_dir_edit.text())
        
        # Split directory
        self.set_setting("pdf", "default_split_directory", self.split_dir_edit.text())
        
        # Remove whitespace default
        self.set_setting("pdf", "remove_whitespace_default", self.remove_white_space_cb.isChecked())
        
        # Compression level
        self.set_setting("pdf", "compression_level", self.compression_combo.currentText())
        
    def browse_output_dir(self):
        """Browse for default output directory"""
        self.browse_directory(self.output_dir_edit, "Select Default Output Directory")
        
    def browse_merge_dir(self):
        """Browse for default merge directory"""
        self.browse_directory(self.merge_dir_edit, "Select Default Merge Directory")
        
    def browse_split_dir(self):
        """Browse for default split directory"""
        self.browse_directory(self.split_dir_edit, "Select Default Split Directory")
        
    def open_directory(self, directory):
        """Open directory in file manager"""
        if not directory or not os.path.exists(directory):
            self.show_warning_message("Directory Not Found", f"Directory does not exist: {directory}")
            return
            
        try:
            if platform.system() == "Windows":
                os.startfile(directory)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", directory])
            else:  # Linux
                subprocess.run(["xdg-open", directory])
        except Exception as e:
            self.logger.error("PDFSettings", f"Failed to open directory {directory}: {e}")
            self.show_warning_message("Error", f"Failed to open directory: {e}")
            
    def on_settings_changed(self):
        """Handle settings change"""
        self.settings_changed.emit()
