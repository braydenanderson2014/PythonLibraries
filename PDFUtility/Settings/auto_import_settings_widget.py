#!/usr/bin/env python3
"""
Auto-Import Settings Widget
Handles auto-import settings like watch directory, processed directory, and advanced options.
"""

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout, QCheckBox, QLineEdit,
    QPushButton, QSpinBox, QLabel
)

from Settings.base_settings_widget import BaseSettingsWidget

class AutoImportSettingsWidget(BaseSettingsWidget):
    """Auto-Import settings tab widget"""
    
    def setup_ui(self):
        """Create the auto-import settings UI"""
        layout = QVBoxLayout(self)
        
        # Status display
        status_layout = QHBoxLayout()
        status_label = QLabel("Current Status:")
        self.status_value_label = QLabel()
        self.status_value_label.setStyleSheet("font-weight: bold;")
        status_layout.addWidget(status_label)
        status_layout.addWidget(self.status_value_label)
        status_layout.addStretch()
        layout.addLayout(status_layout)
        
        # Enable auto-import
        self.auto_import_enabled_cb = QCheckBox("Enable Auto-Import")
        self.auto_import_enabled_cb.setToolTip("Enable automatic monitoring of a directory for new PDF files")
        self.auto_import_enabled_cb.toggled.connect(self.update_auto_import_status)
        self.auto_import_enabled_cb.toggled.connect(self.on_settings_changed)
        layout.addWidget(self.auto_import_enabled_cb)
        
        # Watch directory group
        watch_dir_group, watch_dir_layout = self.create_group_box("Watch Directory", QFormLayout)
        
        self.watch_dir_edit = QLineEdit()
        self.watch_dir_edit.setPlaceholderText("Directory to monitor for new PDF files")
        self.watch_dir_edit.textChanged.connect(self.on_settings_changed)
        
        watch_dir_browse_btn = self.create_styled_button("Browse...", "Browse for watch directory")
        watch_dir_browse_btn.clicked.connect(self.browse_watch_dir)
        
        watch_dir_input = QHBoxLayout()
        watch_dir_input.addWidget(self.watch_dir_edit)
        watch_dir_input.addWidget(watch_dir_browse_btn)
        
        watch_dir_open_btn = self.create_styled_button("Open", "Open watch directory in file manager")
        watch_dir_open_btn.clicked.connect(lambda: self.open_directory_browser(self.watch_dir_edit.text()))
        watch_dir_input.addWidget(watch_dir_open_btn)
        
        watch_dir_layout.addRow("Watch Directory:", watch_dir_input)
        layout.addWidget(watch_dir_group)
        
        # Processed directory group
        processed_dir_group, processed_dir_layout = self.create_group_box("Processed Files", QFormLayout)
        
        self.move_after_import_cb = QCheckBox("Move files after import")
        self.move_after_import_cb.setToolTip("Move PDF files to another directory after importing them")
        self.move_after_import_cb.toggled.connect(self.on_settings_changed)
        processed_dir_layout.addRow("", self.move_after_import_cb)
        
        self.processed_dir_edit = QLineEdit()
        self.processed_dir_edit.setPlaceholderText("Directory to move processed PDF files to")
        self.processed_dir_edit.textChanged.connect(self.on_settings_changed)
        
        processed_dir_browse_btn = self.create_styled_button("Browse...", "Browse for processed directory")
        processed_dir_browse_btn.clicked.connect(self.browse_processed_dir)
        
        processed_dir_input = QHBoxLayout()
        processed_dir_input.addWidget(self.processed_dir_edit)
        processed_dir_input.addWidget(processed_dir_browse_btn)
        
        processed_dir_open_btn = self.create_styled_button("Open", "Open processed directory in file manager")
        processed_dir_open_btn.clicked.connect(lambda: self.open_directory_browser(self.processed_dir_edit.text()))
        processed_dir_input.addWidget(processed_dir_open_btn)
        
        processed_dir_layout.addRow("Processed Directory:", processed_dir_input)
        layout.addWidget(processed_dir_group)
        
        # Advanced options group
        advanced_group, advanced_layout = self.create_group_box("Advanced Options", QFormLayout)
        
        self.auto_process_cb = QCheckBox("Automatically process imported files")
        self.auto_process_cb.setToolTip("Automatically process files after importing them")
        self.auto_process_cb.toggled.connect(self.on_settings_changed)
        advanced_layout.addRow("", self.auto_process_cb)
        
        self.check_interval_spin = QSpinBox()
        self.check_interval_spin.setRange(1, 60)
        self.check_interval_spin.setSuffix(" seconds")
        self.check_interval_spin.setToolTip("How often to check for new files (in seconds)")
        self.check_interval_spin.valueChanged.connect(self.on_settings_changed)
        advanced_layout.addRow("Check Interval:", self.check_interval_spin)
        
        self.processing_delay_spin = QSpinBox()
        self.processing_delay_spin.setRange(1, 30)
        self.processing_delay_spin.setSuffix(" seconds")
        self.processing_delay_spin.setToolTip("Time to wait before moving a file to the processed directory")
        self.processing_delay_spin.valueChanged.connect(self.on_settings_changed)
        advanced_layout.addRow("Processing Delay:", self.processing_delay_spin)
        
        layout.addWidget(advanced_group)
        
        # Add help text
        help_text = QLabel(
            "The auto-import feature monitors a directory for new PDF files and " +
            "automatically adds them to the application. Files can be moved to a " +
            "different directory after processing. The processing delay setting controls " +
            "how long to wait before moving a file to the processed directory, giving " +
            "the application time to fully process it."
        )
        help_text.setWordWrap(True)
        help_text.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(help_text)
        
        layout.addStretch()
        
    def load_settings(self):
        """Load auto-import settings from the controller"""
        # Auto-import enabled
        enabled = self.get_setting("auto_import", "enabled", False)
        self.auto_import_enabled_cb.setChecked(enabled)
        
        # Watch directory
        watch_dir = self.get_setting("auto_import", "watch_directory", "")
        self.watch_dir_edit.setText(watch_dir)
        
        # Move after import
        move_files = self.get_setting("auto_import", "move_after_import", False)
        self.move_after_import_cb.setChecked(move_files)
        
        # Processed directory
        processed_dir = self.get_setting("auto_import", "processed_directory", "")
        self.processed_dir_edit.setText(processed_dir)
        
        # Auto process
        auto_process = self.get_setting("auto_import", "auto_process", False)
        self.auto_process_cb.setChecked(auto_process)
        
        # Check interval
        check_interval = int(self.get_setting("auto_import", "check_interval", 5))
        self.check_interval_spin.setValue(check_interval)
        
        # Processing delay
        processing_delay = int(self.get_setting("auto_import", "processing_delay", 3))
        self.processing_delay_spin.setValue(processing_delay)
        
        # Update status
        self.update_auto_import_status()
        
    def save_settings(self):
        """Save auto-import settings to the controller"""
        self.set_setting("auto_import", "enabled", self.auto_import_enabled_cb.isChecked())
        self.set_setting("auto_import", "watch_directory", self.watch_dir_edit.text())
        self.set_setting("auto_import", "move_after_import", self.move_after_import_cb.isChecked())
        self.set_setting("auto_import", "processed_directory", self.processed_dir_edit.text())
        self.set_setting("auto_import", "auto_process", self.auto_process_cb.isChecked())
        self.set_setting("auto_import", "check_interval", self.check_interval_spin.value())
        self.set_setting("auto_import", "processing_delay", self.processing_delay_spin.value())
        
    def browse_watch_dir(self):
        """Browse for watch directory"""
        directory = self.browse_for_directory(
            "Select Watch Directory", 
            self.watch_dir_edit.text()
        )
        if directory:
            self.watch_dir_edit.setText(directory)
            
    def browse_processed_dir(self):
        """Browse for processed directory"""
        directory = self.browse_for_directory(
            "Select Processed Directory", 
            self.processed_dir_edit.text()
        )
        if directory:
            self.processed_dir_edit.setText(directory)
            
    def update_auto_import_status(self):
        """Update the auto-import status display"""
        if self.auto_import_enabled_cb.isChecked():
            if self.watch_dir_edit.text().strip():
                self.status_value_label.setText("Enabled")
                self.status_value_label.setStyleSheet("font-weight: bold; color: green;")
            else:
                self.status_value_label.setText("Enabled (No watch directory)")
                self.status_value_label.setStyleSheet("font-weight: bold; color: orange;")
        else:
            self.status_value_label.setText("Disabled")
            self.status_value_label.setStyleSheet("font-weight: bold; color: red;")
            
    def on_settings_changed(self):
        """Handle settings change"""
        self.update_auto_import_status()
        self.settings_changed.emit()
