#!/usr/bin/env python3
"""
Clean Base Settings Widget - Theme Aware
No hardcoded styling, works with system themes
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QCheckBox,
    QComboBox, QPushButton, QFileDialog, QGroupBox, QFormLayout, 
    QSpinBox, QMessageBox, QSlider, QListWidget, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from settings_controller import SettingsController
from PDFLogger import Logger

class CleanBaseSettingsWidget(QWidget):
    """Clean base class for settings widgets - theme aware"""
    
    # Signal emitted when settings need to be saved
    settings_changed = pyqtSignal()
    
    def __init__(self, settings_controller=None, logger=None, parent=None):
        super().__init__(parent)
        
        # Set size policy to expand
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Use provided logger or create new one
        if logger:
            self.logger = logger
        else:
            self.logger = Logger()
        
        # Use provided settings controller or create new one
        if settings_controller:
            self.settings_controller = settings_controller
        else:
            self.settings_controller = SettingsController()
            
        self.parent = parent
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """Override this method to create the widget's UI"""
        pass
        
    def load_settings(self):
        """Override this method to load settings from the controller"""
        pass
        
    def save_settings(self):
        """Override this method to save settings to the controller"""
        pass
        
    def create_group_box(self, title, layout_type=QFormLayout):
        """Helper method to create a clean group box - no hardcoded styling"""
        group_box = QGroupBox(title)
        
        # Use minimal, theme-compatible styling
        group_box.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        layout = layout_type()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        # Set specific spacing for form layouts
        if hasattr(layout, 'setVerticalSpacing'):
            layout.setVerticalSpacing(12)
        if hasattr(layout, 'setHorizontalSpacing'):
            layout.setHorizontalSpacing(15)
            
        group_box.setLayout(layout)
        return group_box, layout
        
    def create_styled_button(self, text, tooltip=None):
        """Helper method to create a clean button"""
        button = QPushButton(text)
        if tooltip:
            button.setToolTip(tooltip)
            
        # Minimal styling that works with themes
        button.setMinimumHeight(30)
        return button
        
    def get_setting(self, section, key, default=None):
        """Helper method to get a setting"""
        return self.settings_controller.get_setting(section, key, default)
        
    def set_setting(self, section, key, value):
        """Helper method to set a setting"""
        self.settings_controller.set_setting(section, key, value)
        
    def browse_for_directory(self, title, current_dir=""):
        """Helper method to browse for a directory"""
        directory = QFileDialog.getExistingDirectory(
            self, title, current_dir or ""
        )
        return directory if directory else None
        
    def open_directory_browser(self, path):
        """Helper method to open directory in file manager"""
        if not path or not os.path.exists(path):
            self.show_warning_message("Directory Error", "Directory does not exist.")
            return
            
        try:
            import subprocess
            import platform
            
            if platform.system() == 'Windows':
                subprocess.run(['explorer', path])
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', path])
            else:  # Linux
                subprocess.run(['xdg-open', path])
        except Exception as e:
            self.logger.error("CleanBaseSettingsWidget", f"Error opening directory: {str(e)}")
            
    def show_info_message(self, title, message):
        """Show an information message"""
        QMessageBox.information(self, title, message)
        
    def show_warning_message(self, title, message):
        """Show a warning message"""
        QMessageBox.warning(self, title, message)
        
    def show_question_message(self, title, message):
        """Show a question message and return True if Yes was clicked"""
        reply = QMessageBox.question(
            self, title, message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes
        
    def on_settings_changed(self):
        """Handle settings change"""
        self.settings_changed.emit()
