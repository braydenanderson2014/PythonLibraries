#!/usr/bin/env python3
"""
General Settings Widget
Handles general application settings like theme, language, updates, etc.
"""

import os
import subprocess
import platform
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout, QComboBox, 
    QCheckBox, QSpinBox, QLineEdit, QPushButton
)
from PyQt6.QtCore import Qt

from Settings.base_settings_widget import BaseSettingsWidget

class GeneralSettingsWidget(BaseSettingsWidget):
    """General settings tab widget"""
    
    def setup_ui(self):
        """Create the general settings UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)  # Add margins
        layout.setSpacing(15)  # Add spacing between groups
        
        # General settings group
        general_group, general_layout = self.create_group_box("General Settings", QFormLayout)
        general_layout.setVerticalSpacing(10)  # Add vertical spacing
        general_layout.setHorizontalSpacing(15)  # Add horizontal spacing
        
        # Theme selection
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["System", "Light", "Dark"])
        self.theme_combo.currentTextChanged.connect(self.on_settings_changed)
        general_layout.addRow("Theme:", self.theme_combo)
        
        # Language selection
        self.language_combo = QComboBox()
        self.language_combo.addItems(["English", "Spanish", "French"])
        self.language_combo.currentTextChanged.connect(self.on_settings_changed)
        general_layout.addRow("Language:", self.language_combo)
        
        # Check for updates
        self.update_check_cb = QCheckBox("Check for updates on startup")
        self.update_check_cb.stateChanged.connect(self.on_settings_changed)
        general_layout.addRow("", self.update_check_cb)
        
        # Recent files limit
        self.recent_files_spin = QSpinBox()
        self.recent_files_spin.setMinimum(0)
        self.recent_files_spin.setMaximum(30)
        self.recent_files_spin.setValue(10)
        self.recent_files_spin.valueChanged.connect(self.on_settings_changed)
        general_layout.addRow("Maximum recent files:", self.recent_files_spin)
        
        # Last used directory
        self.last_dir_edit = QLineEdit()
        self.last_dir_edit.setReadOnly(True)
        
        last_dir_layout = QHBoxLayout()
        last_dir_layout.addWidget(self.last_dir_edit)
        
        last_dir_btn = self.create_styled_button("Browse...", "Select default directory")
        last_dir_btn.clicked.connect(self.browse_last_dir)
        last_dir_layout.addWidget(last_dir_btn)
        
        last_dir_open_btn = self.create_styled_button("Open", "Open directory in file manager")
        last_dir_open_btn.clicked.connect(lambda: self.open_directory(self.last_dir_edit.text()))
        last_dir_layout.addWidget(last_dir_open_btn)
        
        general_layout.addRow("Last used directory:", last_dir_layout)
        
        # Add to layout
        layout.addWidget(general_group)
        layout.addStretch()
        
    def load_settings(self):
        """Load general settings from the controller"""
        # Theme
        theme = self.get_setting("ui", "theme", "System")
        index = self.theme_combo.findText(theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
            
        # Language
        language = self.get_setting("ui", "language", "English")
        index = self.language_combo.findText(language)
        if index >= 0:
            self.language_combo.setCurrentIndex(index)
            
        # Update check
        check_updates = self.get_setting("general", "check_updates_on_startup", True)
        self.update_check_cb.setChecked(check_updates)
        
        # Recent files
        recent_files_count = self.get_setting("general", "max_recent_files", 10)
        self.recent_files_spin.setValue(recent_files_count)
        
        # Last directory
        last_dir = self.get_setting("general", "last_used_directory", "")
        self.last_dir_edit.setText(last_dir)
        
    def save_settings(self):
        """Save general settings to the controller"""
        # Theme
        self.set_setting("ui", "theme", self.theme_combo.currentText())
        
        # Language
        self.set_setting("ui", "language", self.language_combo.currentText())
        
        # Update check
        self.set_setting("general", "check_updates_on_startup", self.update_check_cb.isChecked())
        
        # Recent files
        self.set_setting("general", "max_recent_files", self.recent_files_spin.value())
        
        # Last directory
        self.set_setting("general", "last_used_directory", self.last_dir_edit.text())
        
    def browse_last_dir(self):
        """Browse for last used directory"""
        self.browse_directory(self.last_dir_edit, "Select Default Directory")
        
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
            self.logger.error("GeneralSettings", f"Failed to open directory {directory}: {e}")
            self.show_warning_message("Error", f"Failed to open directory: {e}")
            
    def on_settings_changed(self):
        """Handle settings change"""
        self.settings_changed.emit()
