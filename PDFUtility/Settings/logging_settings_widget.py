#!/usr/bin/env python3
"""
Logging Settings Widget
Handles logging settings like log directory, file management, and information display.
"""

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout, QLineEdit, QPushButton,
    QCheckBox, QSpinBox, QLabel
)

from Settings.base_settings_widget import BaseSettingsWidget

class LoggingSettingsWidget(BaseSettingsWidget):
    """Logging settings tab widget"""
    
    def setup_ui(self):
        """Create the logging settings UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)  # Add proper spacing
        
        # Log File Settings group
        log_file_group, log_file_layout = self.create_group_box("Log File Settings", QFormLayout)
        log_file_layout.setVerticalSpacing(8)  # Consistent spacing
        
        # Log directory
        self.log_dir_edit = QLineEdit()
        self.log_dir_edit.setReadOnly(True)
        self.log_dir_edit.textChanged.connect(self.on_settings_changed)
        
        log_dir_layout = QHBoxLayout()
        log_dir_layout.addWidget(self.log_dir_edit)
        
        log_dir_btn = self.create_styled_button("Browse", "Browse for log directory")
        log_dir_btn.setMaximumWidth(80)  # Consistent button width
        log_dir_btn.clicked.connect(self.browse_log_dir)
        log_dir_layout.addWidget(log_dir_btn)
        
        log_dir_open_btn = self.create_styled_button("Open", "Open log directory in file manager")
        log_dir_open_btn.setMaximumWidth(60)  # Consistent button width
        log_dir_open_btn.clicked.connect(lambda: self.open_directory_browser(self.log_dir_edit.text()))
        log_dir_layout.addWidget(log_dir_open_btn)
        
        log_file_layout.addRow("Log directory:", log_dir_layout)
        
        # Log filename
        self.log_filename_edit = QLineEdit()
        self.log_filename_edit.setPlaceholderText("e.g., pdf_utility.log")
        self.log_filename_edit.textChanged.connect(self.on_settings_changed)
        log_file_layout.addRow("Log filename:", self.log_filename_edit)
        
        # Open log file button
        log_file_actions_layout = QHBoxLayout()
        
        self.open_log_btn = self.create_styled_button("Open Log", "Open the current log file")
        self.open_log_btn.setMaximumWidth(100)
        self.open_log_btn.clicked.connect(self.open_log_file)
        log_file_actions_layout.addWidget(self.open_log_btn)
        
        self.clear_log_btn = self.create_styled_button("Clear Log", "Clear the current log file")
        self.clear_log_btn.setMaximumWidth(100)
        self.clear_log_btn.clicked.connect(self.clear_log_file)
        log_file_actions_layout.addWidget(self.clear_log_btn)
        
        log_file_actions_layout.addStretch()
        log_file_layout.addRow("", log_file_actions_layout)  # No label for action buttons
        
        layout.addWidget(log_file_group)
        
        # Log Management Settings group (simplified)
        log_mgmt_group, log_mgmt_layout = self.create_group_box("Log Management", QFormLayout)
        log_mgmt_layout.setVerticalSpacing(8)
        
        # Auto clear logs
        self.auto_clear_logs_cb = QCheckBox("Automatically clear old logs")
        self.auto_clear_logs_cb.setToolTip("Automatically clear log files after a specified interval")
        self.auto_clear_logs_cb.toggled.connect(self.on_settings_changed)
        log_mgmt_layout.addRow("", self.auto_clear_logs_cb)
        
        # Clear logs interval
        self.clear_logs_interval_spin = QSpinBox()
        self.clear_logs_interval_spin.setMinimum(1)
        self.clear_logs_interval_spin.setMaximum(365)
        self.clear_logs_interval_spin.setValue(30)
        self.clear_logs_interval_spin.setSuffix(" days")
        self.clear_logs_interval_spin.setToolTip("Number of days after which logs should be cleared")
        self.clear_logs_interval_spin.valueChanged.connect(self.on_settings_changed)
        log_mgmt_layout.addRow("Clear after:", self.clear_logs_interval_spin)
        
        # Max log file size
        self.max_log_size_spin = QSpinBox()
        self.max_log_size_spin.setMinimum(1)
        self.max_log_size_spin.setMaximum(100)
        self.max_log_size_spin.setValue(10)
        self.max_log_size_spin.setSuffix(" MB")
        self.max_log_size_spin.setToolTip("Maximum size of a single log file")
        self.max_log_size_spin.valueChanged.connect(self.on_settings_changed)
        log_mgmt_layout.addRow("Max file size:", self.max_log_size_spin)
        log_mgmt_layout.addRow("Max file size:", self.max_log_size_spin)
        
        layout.addWidget(log_mgmt_group)
        
        # Log Information group (simplified)
        log_info_group, log_info_layout = self.create_group_box("Log Information", QFormLayout)
        log_info_layout.setVerticalSpacing(8)
        
        # Current log file size
        self.current_log_size_label = QLabel("0.00 MB")
        self.current_log_size_label.setStyleSheet("font-weight: bold;")
        log_info_layout.addRow("Current size:", self.current_log_size_label)
        
        # Refresh info button
        self.refresh_log_info_btn = self.create_styled_button("Refresh", "Refresh log file information")
        self.refresh_log_info_btn.setMaximumWidth(80)
        self.refresh_log_info_btn.clicked.connect(self.refresh_log_info)
        log_info_layout.addRow("", self.refresh_log_info_btn)
        
        layout.addWidget(log_info_group)
        layout.addStretch()
        
    def load_settings(self):
        """Load logging settings from the controller"""
        # Log directory
        log_dir = self.get_setting("logging", "log_directory", "logs")
        self.log_dir_edit.setText(log_dir)
        
        # Log filename
        log_filename = self.get_setting("logging", "log_filename", "pdf_utility.log")
        self.log_filename_edit.setText(log_filename)
        
        # Auto clear logs
        auto_clear = self.get_setting("logging", "auto_clear_logs", False)
        self.auto_clear_logs_cb.setChecked(auto_clear)
        
        # Clear logs interval
        clear_interval = int(self.get_setting("logging", "clear_logs_interval", 30))
        self.clear_logs_interval_spin.setValue(clear_interval)
        
        # Max log file size
        max_size = int(self.get_setting("logging", "max_log_size", 10))
        self.max_log_size_spin.setValue(max_size)
        
        # Refresh log info on load
        self.refresh_log_info()
        
    def save_settings(self):
        """Save logging settings to the controller"""
        self.set_setting("logging", "log_directory", self.log_dir_edit.text())
        self.set_setting("logging", "log_filename", self.log_filename_edit.text())
        self.set_setting("logging", "auto_clear_logs", self.auto_clear_logs_cb.isChecked())
        self.set_setting("logging", "clear_logs_interval", self.clear_logs_interval_spin.value())
        self.set_setting("logging", "max_log_size", self.max_log_size_spin.value())
        
    def browse_log_dir(self):
        """Browse for log directory"""
        directory = self.browse_for_directory(
            "Select Log Directory", 
            self.log_dir_edit.text()
        )
        if directory:
            self.log_dir_edit.setText(directory)
            
    def open_log_file(self):
        """Open the current log file"""
        try:
            # This would typically call the settings controller's method
            success, message = self.settings_controller.open_log_file()
            if not success:
                self.show_warning_message("Open Log File", message)
        except Exception as e:
            self.logger.error("LoggingSettings", f"Error opening log file: {str(e)}")
            self.show_warning_message("Open Log File Error", f"Failed to open log file: {str(e)}")
            
    def clear_log_file(self):
        """Clear the current log file"""
        try:
            # Confirm action
            if self.show_question_message("Clear Log File", "Are you sure you want to clear the log file?"):
                success, message = self.settings_controller.clear_log_file()
                if success:
                    self.show_info_message("Clear Log File", "Log file cleared successfully.")
                    self.refresh_log_info()
                else:
                    self.show_warning_message("Clear Log File", message)
        except Exception as e:
            self.logger.error("LoggingSettings", f"Error clearing log file: {str(e)}")
            self.show_warning_message("Clear Log File Error", f"Failed to clear log file: {str(e)}")
            
    def refresh_log_info(self):
        """Refresh log file information"""
        try:
            # Get log file info from settings controller
            log_info = self.settings_controller.get_log_file_info()
            
            # Update current log size
            if 'size_mb' in log_info:
                self.current_log_size_label.setText(f"{log_info['size_mb']:.2f} MB")
            else:
                self.current_log_size_label.setText("0.00 MB")
                
        except Exception as e:
            self.logger.error("LoggingSettings", f"Error refreshing log info: {str(e)}")
            self.current_log_size_label.setText("Error")
            
    def on_settings_changed(self):
        """Handle settings change"""
        self.settings_changed.emit()
