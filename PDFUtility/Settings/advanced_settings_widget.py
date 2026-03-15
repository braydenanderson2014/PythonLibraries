#!/usr/bin/env python3
"""
Advanced Settings Widget
Handles advanced settings like parallel processing, temp directory, log level.
"""

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout, QCheckBox, QSpinBox,
    QLineEdit, QPushButton, QComboBox
)

from Settings.base_settings_widget import BaseSettingsWidget

class AdvancedSettingsWidget(BaseSettingsWidget):
    """Advanced settings tab widget"""
    
    def setup_ui(self):
        """Create the advanced settings UI"""
        layout = QVBoxLayout(self)
        
        # Advanced settings group
        advanced_group, advanced_layout = self.create_group_box("Advanced Settings", QFormLayout)
        
        # Temp directory
        self.temp_dir_edit = QLineEdit()
        self.temp_dir_edit.setReadOnly(True)
        self.temp_dir_edit.textChanged.connect(self.on_settings_changed)
        
        temp_dir_layout = QHBoxLayout()
        temp_dir_layout.addWidget(self.temp_dir_edit)
        
        temp_dir_btn = self.create_styled_button("Browse...", "Browse for temporary directory")
        temp_dir_btn.clicked.connect(self.browse_temp_dir)
        temp_dir_layout.addWidget(temp_dir_btn)
        
        temp_open_btn = self.create_styled_button("Open", "Open temporary directory in file manager")
        temp_open_btn.clicked.connect(lambda: self.open_directory_browser(self.temp_dir_edit.text()))
        temp_dir_layout.addWidget(temp_open_btn)
        
        advanced_layout.addRow("Temporary directory:", temp_dir_layout)
        
        # Add to layout
        layout.addWidget(advanced_group)
        layout.addStretch()
        
    def load_settings(self):
        """Load advanced settings from the controller"""
        # Temp directory
        temp_dir = self.get_setting("advanced", "temp_directory", "")
        if not temp_dir:
            # Use system temp directory as default
            import tempfile
            temp_dir = tempfile.gettempdir()
        self.temp_dir_edit.setText(temp_dir)
            
    def save_settings(self):
        """Save advanced settings to the controller"""
        self.set_setting("advanced", "temp_directory", self.temp_dir_edit.text())
        
    def browse_temp_dir(self):
        """Browse for temp directory"""
        directory = self.browse_for_directory(
            "Select Temporary Directory", 
            self.temp_dir_edit.text()
        )
        if directory:
            self.temp_dir_edit.setText(directory)
            
    def on_settings_changed(self):
        """Handle settings change"""
        self.settings_changed.emit()
