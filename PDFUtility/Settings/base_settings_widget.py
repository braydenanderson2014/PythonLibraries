#!/usr/bin/env python3
"""
Base Settings Widget
Provides common functionality for all settings tabs
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

class BaseSettingsWidget(QWidget):
    """Base class for all settings tab widgets"""
    
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
        """Override this method to create the UI for the specific settings tab"""
        pass
        
    def load_settings(self):
        """Override this method to load settings from the controller"""
        pass
        
    def save_settings(self):
        """Override this method to save settings to the controller"""
        pass
        
    def create_group_box(self, title, layout_type=QFormLayout):
        """Helper method to create a theme-aware group box"""
        group_box = QGroupBox(title)
        
        # Use theme-compatible styling with palette colors
        group_box.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid palette(mid);
                border-radius: 5px;
                margin-top: 15px;
                padding-top: 15px;
                background-color: palette(window);
                color: palette(window-text);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: palette(window-text);
                background-color: palette(window);
            }
        """)
        
        layout = layout_type()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Set specific spacing for form layouts
        if hasattr(layout, 'setVerticalSpacing'):
            layout.setVerticalSpacing(15)
        if hasattr(layout, 'setHorizontalSpacing'):
            layout.setHorizontalSpacing(20)
            
        group_box.setLayout(layout)
        return group_box, layout
        
    def create_styled_button(self, text, tooltip=None):
        """Helper method to create a theme-aware button"""
        button = QPushButton(text)
        if tooltip:
            button.setToolTip(tooltip)
            
        # Set proper sizing and theme-compatible styling
        button.setMinimumHeight(35)
        button.setMinimumWidth(80)
        
        # Theme-compatible button styling
        button.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                border: 1px solid palette(mid);
                border-radius: 4px;
                background-color: palette(button);
                color: palette(button-text);
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: palette(highlight);
                color: palette(highlighted-text);
                border-color: palette(highlight);
            }
            QPushButton:pressed {
                background-color: palette(dark);
                color: palette(bright-text);
            }
        """)
        
        return button
        button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #f6f7fa, stop: 1 #dadbde);
                border: 2px solid #c0c0c0;
                border-radius: 4px;
                padding: 6px;
                font-weight: bold;
                color: #2c3e50;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #e8f4fd, stop: 1 #bedcfa);
                border-color: #3498db;
                color: #2980b9;
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #bedcfa, stop: 1 #85c1e9);
            }
        """)
        return button
        
    def browse_directory(self, line_edit, title="Select Directory"):
        """Helper method to browse for a directory"""
        directory = QFileDialog.getExistingDirectory(self, title)
        if directory:
            line_edit.setText(directory)
            self.settings_changed.emit()
            
    def open_directory_browser(self, directory):
        """Open directory in file manager"""
        import os
        import platform
        import subprocess
        
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
            self.logger.error("Settings", f"Failed to open directory {directory}: {e}")
            self.show_warning_message("Error", f"Failed to open directory: {e}")
            
    def browse_file(self, line_edit, title="Select File", file_filter="All Files (*.*)"):
        """Helper method to browse for a file"""
        file_path, _ = QFileDialog.getOpenFileName(self, title, "", file_filter)
        if file_path:
            line_edit.setText(file_path)
            self.settings_changed.emit()
            
    def show_info_message(self, title, message):
        """Helper method to show info message"""
        QMessageBox.information(self, title, message)
        
    def show_warning_message(self, title, message):
        """Helper method to show warning message"""
        QMessageBox.warning(self, title, message)
        
    def show_question_message(self, title, message):
        """Helper method to show question message with Yes/No buttons"""
        reply = QMessageBox.question(self, title, message, 
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        return reply == QMessageBox.StandardButton.Yes
        
    def get_setting(self, section, key, default=None):
        """Helper method to get a setting value"""
        return self.settings_controller.get_setting(section, key, default)
        
    def set_setting(self, section, key, value):
        """Helper method to set a setting value"""
        self.settings_controller.set_setting(section, key, value)
        self.settings_changed.emit()
