# SettingsController.py - PyQt version
# This is a simplified version of the original SettingsController, adapted for PyQt

import os
import json
import configparser
import pathlib
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QFileDialog, QCheckBox, QComboBox, QTabWidget, QSpinBox, QGroupBox,
    QFormLayout, QSlider, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette, QColor

class SettingsDialog(QDialog):
    """Settings dialog for the PDF Utility application"""
    
    def __init__(self, parent=None, settings=None):
        super().__init__(parent)
        self.parent = parent
        self.settings = settings or {}
        self.setWindowTitle("PDF Utility Settings")
        self.setMinimumWidth(500)
        
        # Create the main layout
        self.main_layout = QVBoxLayout(self)
        
        # Create tabs for different settings categories
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)
        
        # Create General tab
        self.create_general_tab()
        
        # Create PDF tab
        self.create_pdf_tab()
        
        # Create Theme tab
        self.create_theme_tab()
        
        # Create Text to Speech tab
        self.create_tts_tab()
        
        # Add buttons
        self.create_buttons()
        
    def create_general_tab(self):
        """Create the general settings tab"""
        general_tab = QWidget()
        layout = QFormLayout(general_tab)
        
        # Output directory setting
        output_dir_group = QGroupBox("Output Directory")
        output_dir_layout = QHBoxLayout(output_dir_group)
        
        self.output_dir = QLineEdit(self.settings.get("output_directory", ""))
        output_dir_layout.addWidget(self.output_dir)
        
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.browse_output_dir)
        output_dir_layout.addWidget(browse_button)
        
        layout.addRow(output_dir_group)
        
        # Auto cleanup settings
        cleanup_group = QGroupBox("Log Cleanup")
        cleanup_layout = QFormLayout(cleanup_group)
        
        self.cleanup_count = QSpinBox()
        self.cleanup_count.setRange(1, 100)
        self.cleanup_count.setValue(int(self.settings.get("cleanup_run_count", "10")))
        cleanup_layout.addRow("Run cleanup every N starts:", self.cleanup_count)
        
        layout.addRow(cleanup_group)
        
        # File handling options
        options_group = QGroupBox("File Options")
        options_layout = QFormLayout(options_group)
        
        self.select_on_add = QCheckBox()
        self.select_on_add.setChecked(self.settings.get("select_on_add", "True") == "True")
        options_layout.addRow("Select files when added:", self.select_on_add)
        
        layout.addRow(options_group)
        
        self.tab_widget.addTab(general_tab, "General")
        
    def create_pdf_tab(self):
        """Create the PDF settings tab"""
        pdf_tab = QWidget()
        layout = QFormLayout(pdf_tab)
        
        # White page removal settings
        white_group = QGroupBox("White Page Detection")
        white_layout = QFormLayout(white_group)
        
        self.white_threshold = QSpinBox()
        self.white_threshold.setRange(200, 255)
        self.white_threshold.setValue(int(self.settings.get("remove_white_threshold", "230")))
        white_layout.addRow("White threshold (200-255):", self.white_threshold)
        
        self.white_coverage = QSpinBox()
        self.white_coverage.setRange(80, 100)
        self.white_coverage.setValue(int(self.settings.get("remove_white_page_coverage_threshold", "98")))
        white_layout.addRow("Page coverage % threshold:", self.white_coverage)
        
        layout.addRow(white_group)
        
        self.tab_widget.addTab(pdf_tab, "PDF Processing")
        
    def create_theme_tab(self):
        """Create the theme settings tab"""
        theme_tab = QWidget()
        layout = QFormLayout(theme_tab)
        
        # Theme selection
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["light", "dark", "system"])
        current_theme = self.settings.get("theme", "dark")
        self.theme_combo.setCurrentText(current_theme)
        layout.addRow("Application Theme:", self.theme_combo)
        
        # Enable custom colors checkbox
        self.custom_colors_checkbox = QCheckBox("Enable custom colors")
        self.custom_colors_checkbox.setChecked(self.settings.get("use_custom_colors", "False") == "True")
        self.custom_colors_checkbox.toggled.connect(self._toggle_custom_colors)
        layout.addRow(self.custom_colors_checkbox)
        
        # Custom color options
        color_group = QGroupBox("Custom Theme Colors")
        color_layout = QFormLayout(color_group)
        
        # We'll use colored buttons in the future
        # For now, we'll just use text fields for RGB values
        self.bg_color = QLineEdit(self.settings.get("custom_bg_color", "#2D2D30"))
        self.text_color = QLineEdit(self.settings.get("custom_text_color", "#FFFFFF"))
        self.accent_color = QLineEdit(self.settings.get("custom_accent_color", "#007ACC"))
        
        color_layout.addRow("Background Color:", self.bg_color)
        color_layout.addRow("Text Color:", self.text_color)
        color_layout.addRow("Accent Color:", self.accent_color)
        
        layout.addRow(color_group)
        
        # CSS customization option (future enhancement)
        self.custom_css_checkbox = QCheckBox("Use custom CSS (coming soon)")
        self.custom_css_checkbox.setEnabled(False)  # Disabled for now
        layout.addRow(self.custom_css_checkbox)
        
        # Initialize state
        self._toggle_custom_colors(self.custom_colors_checkbox.isChecked())
        
        self.tab_widget.addTab(theme_tab, "Appearance")
    
    def _toggle_custom_colors(self, enabled):
        """Toggle the custom colors fields"""
        self.bg_color.setEnabled(enabled)
        self.text_color.setEnabled(enabled)
        self.accent_color.setEnabled(enabled)
        
    def create_tts_tab(self):
        """Create the text-to-speech settings tab"""
        tts_tab = QWidget()
        layout = QFormLayout(tts_tab)
        
        # TTS Rate
        rate_group = QGroupBox("Speech Rate")
        rate_layout = QHBoxLayout(rate_group)
        
        self.tts_rate = QSlider(Qt.Orientation.Horizontal)
        self.tts_rate.setRange(50, 300)
        self.tts_rate.setValue(int(self.settings.get("text_to_speech_rate", "150")))
        self.tts_rate_label = QLabel(str(self.tts_rate.value()))
        self.tts_rate.valueChanged.connect(lambda v: self.tts_rate_label.setText(str(v)))
        
        rate_layout.addWidget(self.tts_rate)
        rate_layout.addWidget(self.tts_rate_label)
        
        layout.addRow(rate_group)
        
        # TTS Volume
        volume_group = QGroupBox("Speech Volume")
        volume_layout = QHBoxLayout(volume_group)
        
        self.tts_volume = QSlider(Qt.Orientation.Horizontal)
        self.tts_volume.setRange(0, 100)
        volume_percent = int(float(self.settings.get("text_to_speech_volume", "1.0")) * 100)
        self.tts_volume.setValue(volume_percent)
        self.tts_volume_label = QLabel(f"{volume_percent}%")
        self.tts_volume.valueChanged.connect(lambda v: self.tts_volume_label.setText(f"{v}%"))
        
        volume_layout.addWidget(self.tts_volume)
        volume_layout.addWidget(self.tts_volume_label)
        
        layout.addRow(volume_group)
        
        self.tab_widget.addTab(tts_tab, "Text to Speech")
        
    def create_buttons(self):
        """Create the dialog buttons"""
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.accept)
        button_layout.addWidget(self.save_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        self.main_layout.addLayout(button_layout)
    
    def browse_output_dir(self):
        """Open file dialog to choose output directory"""
        dir_path = QFileDialog.getExistingDirectory(
            self, 
            "Select Output Directory",
            self.output_dir.text()
        )
        if dir_path:
            self.output_dir.setText(dir_path)
    
    def get_settings(self):
        """Get the current settings from the dialog controls"""
        settings = {}
        settings["output_directory"] = self.output_dir.text()
        settings["cleanup_run_count"] = str(self.cleanup_count.value())
        settings["theme"] = self.theme_combo.currentText()
        settings["text_to_speech_rate"] = str(self.tts_rate.value())
        settings["text_to_speech_volume"] = str(self.tts_volume.value() / 100.0)
        settings["remove_white_threshold"] = str(self.white_threshold.value())
        settings["remove_white_page_coverage_threshold"] = str(self.white_coverage.value())
        settings["select_on_add"] = str(self.select_on_add.isChecked())
        
        # Theme customization settings
        settings["use_custom_colors"] = str(self.custom_colors_checkbox.isChecked())
        settings["custom_bg_color"] = self.bg_color.text()
        settings["custom_text_color"] = self.text_color.text()
        settings["custom_accent_color"] = self.accent_color.text()
        
        return settings


class SettingsController:
    """Manages application settings for the PyQt version of PDF Utility"""
    
    def __init__(self, parent=None):
        """Initialize the settings controller with default settings"""
        self.parent = parent
        self.settings_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")
        self.default_settings = {
            "output_directory": os.path.join(os.path.dirname(os.path.abspath(__file__)), "output"),
            "current_cleanup_run_count": "0",
            "cleanup_run_count": "10",
            "theme": "dark",
            "text_to_speech_rate": "150",
            "text_to_speech_volume": "1.0",
            "remove_white_threshold": "230",
            "remove_white_page_coverage_threshold": "98",
            "select_on_add": "True",
            # Theme customization settings
            "use_custom_colors": "False",
            "custom_bg_color": "#2D2D30",
            "custom_text_color": "#FFFFFF",
            "custom_accent_color": "#007ACC"
        }
        
        # Create output directory if it doesn't exist
        os.makedirs(self.default_settings["output_directory"], exist_ok=True)
    
    def load_settings(self):
        """Load settings from file or create with defaults if file doesn't exist"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                
                # Ensure all default settings exist (for compatibility with older versions)
                for key, value in self.default_settings.items():
                    if key not in settings:
                        settings[key] = value
                
                return settings
            except Exception as e:
                print(f"Error loading settings: {e}")
                return self.default_settings.copy()
        else:
            # Create settings file with defaults
            self.save_settings(self.default_settings)
            return self.default_settings.copy()
    
    def save_settings(self, settings):
        """Save settings to file"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    def save_runtime_settings_with_args(self, settings):
        """Save specific runtime settings"""
        current_settings = self.load_settings()
        
        # Update settings with provided values
        for key, value in settings.items():
            current_settings[key] = value
        
        # Save updated settings
        return self.save_settings(current_settings)
    
    def open_settings_dialog(self):
        """Open the settings dialog"""
        # Get the current settings
        current_settings = self.load_settings()
        
        # Create and show the dialog
        dialog = SettingsDialog(self.parent, current_settings)
        result = dialog.exec()
        
        # If user clicked Save, update the settings
        if result == QDialog.DialogCode.Accepted:
            new_settings = dialog.get_settings()
            self.save_settings(new_settings)
            return new_settings
        
        return None
        
    def apply_theme(self, app):
        """Apply the selected theme to the application"""
        settings = self.load_settings()
        theme = settings.get("theme", "dark")
        
        if theme == "dark":
            self._apply_dark_theme(app, settings)
        elif theme == "light":
            self._apply_light_theme(app)
        elif theme == "system":
            # Use system theme (default Qt behavior)
            pass
    
    def _apply_dark_theme(self, app, settings):
        """Apply dark theme to the application"""
        from PyQt6.QtGui import QColor
        
        dark_palette = app.palette()
        
        # Check if custom colors are enabled
        use_custom_colors = settings.get("use_custom_colors", "False") == "True"
        
        if use_custom_colors:
            # Parse custom colors
            try:
                bg_color = QColor(settings.get("custom_bg_color", "#2D2D30"))
                text_color = QColor(settings.get("custom_text_color", "#FFFFFF"))
                accent_color = QColor(settings.get("custom_accent_color", "#007ACC"))
                
                # Apply custom colors
                dark_palette.setColor(QPalette.ColorRole.Window, bg_color)
                dark_palette.setColor(QPalette.ColorRole.WindowText, text_color)
                dark_palette.setColor(QPalette.ColorRole.Base, QColor(bg_color).darker(120))
                dark_palette.setColor(QPalette.ColorRole.AlternateBase, bg_color)
                dark_palette.setColor(QPalette.ColorRole.ToolTipBase, bg_color)
                dark_palette.setColor(QPalette.ColorRole.ToolTipText, text_color)
                dark_palette.setColor(QPalette.ColorRole.Text, text_color)
                dark_palette.setColor(QPalette.ColorRole.Button, bg_color)
                dark_palette.setColor(QPalette.ColorRole.ButtonText, text_color)
                dark_palette.setColor(QPalette.ColorRole.Link, accent_color)
                dark_palette.setColor(QPalette.ColorRole.Highlight, accent_color)
                dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor("white"))
            except Exception as e:
                print(f"Error parsing custom colors: {e}")
                # Fall back to default dark theme if there's an error
                self._apply_default_dark_theme(dark_palette)
        else:
            # Apply default dark theme
            self._apply_default_dark_theme(dark_palette)
        
        app.setPalette(dark_palette)
    
    def _apply_default_dark_theme(self, palette):
        """Apply default dark theme colors to the palette"""
        # Set dark theme colors - using proper QPalette color role enum
        palette.setColor(QPalette.ColorRole.Window, QColor(45, 45, 48))
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Base, QColor(30, 30, 30))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(50, 50, 55))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(45, 45, 48))
        palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Button, QColor(60, 60, 65))
        palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Link, QColor(0, 122, 204))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 122, 204))
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
        
    def _apply_light_theme(self, app):
        """Apply light theme to the application"""
        # Create a light palette instead of using the default
        light_palette = QPalette()
        
        # Set light theme colors
        light_palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
        light_palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.black)
        light_palette.setColor(QPalette.ColorRole.Base, Qt.GlobalColor.white)
        light_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(245, 245, 245))
        light_palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        light_palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.black)
        light_palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.black)
        light_palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
        light_palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.black)
        light_palette.setColor(QPalette.ColorRole.Link, QColor(0, 0, 255))
        light_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        light_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
        
        app.setPalette(light_palette)
