#!/usr/bin/env python3
"""
Clean General Settings Widget
Theme-aware implementation with proper sizing
"""

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QFormLayout, QComboBox, QCheckBox,
    QSpinBox, QLineEdit
)
from PyQt6.QtCore import Qt

from Settings.clean_base_settings_widget import CleanBaseSettingsWidget

class CleanGeneralSettingsWidget(CleanBaseSettingsWidget):
    """Clean general settings tab widget"""
    
    def setup_ui(self):
        """Create the general settings UI"""
        # Main layout with proper spacing
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(20)
        
        # General Settings group
        general_group, general_layout = self.create_group_box("General Settings", QFormLayout)
        
        # Theme selection
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["System", "Light", "Dark"])
        self.theme_combo.setMinimumHeight(30)
        self.theme_combo.currentTextChanged.connect(self.on_settings_changed)
        general_layout.addRow("Theme:", self.theme_combo)
        
        # Language selection
        self.language_combo = QComboBox()
        self.language_combo.addItems(["English", "Spanish", "French"])
        self.language_combo.setMinimumHeight(30)
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
        self.recent_files_spin.setMinimumHeight(30)
        self.recent_files_spin.valueChanged.connect(self.on_settings_changed)
        general_layout.addRow("Maximum recent files:", self.recent_files_spin)
        
        # Last used directory section
        self.last_dir_edit = QLineEdit()
        self.last_dir_edit.setReadOnly(True)
        self.last_dir_edit.setMinimumHeight(30)
        self.last_dir_edit.setPlaceholderText("No directory selected")
        
        # Directory buttons
        dir_buttons_layout = QHBoxLayout()
        
        browse_btn = self.create_styled_button("Browse...", "Select default directory")
        browse_btn.clicked.connect(self.browse_last_dir)
        dir_buttons_layout.addWidget(browse_btn)
        
        open_btn = self.create_styled_button("Open", "Open directory in file manager")
        open_btn.clicked.connect(self.open_last_dir)
        dir_buttons_layout.addWidget(open_btn)
        
        # Create a container for the directory row
        dir_container = QVBoxLayout()
        dir_container.addWidget(self.last_dir_edit)
        dir_container.addLayout(dir_buttons_layout)
        
        # Add directory section to form
        general_layout.addRow("Last used directory:", dir_container)
        
        # Add group to main layout
        main_layout.addWidget(general_group)
        
        # Add stretch to push content to top
        main_layout.addStretch()
        
    def load_settings(self):
        """Load general settings from the controller"""
        try:
            # Theme
            theme = self.get_setting("general", "theme", "System")
            index = self.theme_combo.findText(theme, Qt.MatchFlag.MatchFixedString)
            if index >= 0:
                self.theme_combo.setCurrentIndex(index)
            
            # Language  
            language = self.get_setting("general", "language", "English")
            index = self.language_combo.findText(language, Qt.MatchFlag.MatchFixedString)
            if index >= 0:
                self.language_combo.setCurrentIndex(index)
                
            # Update check
            check_updates = self.get_setting("general", "check_updates", True)
            self.update_check_cb.setChecked(check_updates)
            
            # Recent files limit
            max_recent = int(self.get_setting("general", "max_recent_files", 10))
            self.recent_files_spin.setValue(max_recent)
            
            # Last directory
            last_dir = self.get_setting("general", "last_directory", "")
            self.last_dir_edit.setText(last_dir)
            
        except Exception as e:
            self.logger.error("CleanGeneralSettings", f"Error loading settings: {str(e)}")
            
    def save_settings(self):
        """Save general settings to the controller"""
        try:
            self.set_setting("general", "theme", self.theme_combo.currentText())
            self.set_setting("general", "language", self.language_combo.currentText())
            self.set_setting("general", "check_updates", self.update_check_cb.isChecked())
            self.set_setting("general", "max_recent_files", self.recent_files_spin.value())
            self.set_setting("general", "last_directory", self.last_dir_edit.text())
            
        except Exception as e:
            self.logger.error("CleanGeneralSettings", f"Error saving settings: {str(e)}")
            
    def browse_last_dir(self):
        """Browse for last used directory"""
        directory = self.browse_for_directory(
            "Select Default Directory", 
            self.last_dir_edit.text()
        )
        if directory:
            self.last_dir_edit.setText(directory)
            
    def open_last_dir(self):
        """Open the last used directory in file manager"""
        self.open_directory_browser(self.last_dir_edit.text())
            
    def on_settings_changed(self):
        """Handle settings change"""
        self.settings_changed.emit()
