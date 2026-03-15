#!/usr/bin/env python3
"""
Modular Settings Dialog for PDF Utility
Uses individual widget files for each settings tab
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTabWidget, 
    QDialogButtonBox, QMessageBox
)
from PyQt6.QtCore import Qt

from settings_controller import SettingsController
from PDFLogger import Logger

# Import all the modular settings widgets
from Settings.general_settings_widget import GeneralSettingsWidget
from Settings.pdf_settings_widget import PDFSettingsWidget
from Settings.interface_settings_widget import InterfaceSettingsWidget
from Settings.tts_settings_widget import TTSSettingsWidget
from Settings.editor_settings_widget import EditorSettingsWidget
from Settings.auto_import_settings_widget import AutoImportSettingsWidget
from Settings.advanced_settings_widget import AdvancedSettingsWidget
from Settings.logging_settings_widget import LoggingSettingsWidget
from Settings.tutorial_settings_widget import TutorialSettingsWidget

class ModularSettingsDialog(QDialog):
    """Modular Settings dialog using individual widget files"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = Logger()
        self.parent = parent
        
        # Use the parent's settings controller if available, otherwise create a new one
        if parent and hasattr(parent, 'settings'):
            self.logger.info("ModularSettingsDialog", "Using parent's settings controller")
            self.settings_controller = parent.settings
        else:
            self.logger.info("ModularSettingsDialog", "Creating new settings controller")
            self.settings_controller = SettingsController()
        
        # Ensure settings are loaded
        self.settings_controller.load_settings()
        
        self.setWindowTitle("Settings - General (1/9)")
        self.setMinimumWidth(700)
        self.setMinimumHeight(600)
        self.resize(800, 650)  # Set a good default size
        
        # Keep track of settings widgets for easy access
        self.settings_widgets = {}
        
        self.init_ui()
        self.load_all_settings()
        
    def init_ui(self):
        """Initialize the modular UI"""
        layout = QVBoxLayout(self)
        
        # Create tab widget with navigation
        tab_container = QHBoxLayout()
        
        # Left navigation arrow
        self.prev_tab_btn = QPushButton("◀")
        self.prev_tab_btn.setFixedSize(40, 40)
        self.prev_tab_btn.setStyleSheet("""
            QPushButton {
                font-size: 18px;
                font-weight: bold;
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #f6f7fa, stop: 1 #dadbde);
                border: 2px solid #c0c0c0;
                border-radius: 20px;
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
            QPushButton:disabled {
                color: #bdc3c7;
                background: #ecf0f1;
                border-color: #d5d8dc;
            }
        """)
        self.prev_tab_btn.clicked.connect(self.previous_tab)
        self.prev_tab_btn.setToolTip("Previous settings tab")
        
        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #c0c0c0;
                border-radius: 5px;
                margin-top: -1px;
            }
            QTabBar::tab {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #f6f7fa, stop: 1 #dadbde);
                border: 2px solid #c0c0c0;
                border-bottom-color: #c0c0c0;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                min-width: 80px;
                max-width: 120px;
                padding: 4px 8px;
                margin-right: 2px;
                font-size: 11px;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #ffffff, stop: 0.4 #f0f8ff, stop: 1 #e1f5fe);
                border-color: #3498db;
                border-bottom-color: #ffffff;
                color: #2980b9;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #e8f4fd, stop: 1 #bedcfa);
            }
        """)
        
        # Right navigation arrow
        self.next_tab_btn = QPushButton("▶")
        self.next_tab_btn.setFixedSize(40, 40)
        self.next_tab_btn.setStyleSheet(self.prev_tab_btn.styleSheet())
        self.next_tab_btn.clicked.connect(self.next_tab)
        self.next_tab_btn.setToolTip("Next settings tab")
        
        # Add widgets to tab container
        tab_container.addWidget(self.prev_tab_btn)
        tab_container.addWidget(self.tabs, 1)  # Give tabs all the space
        tab_container.addWidget(self.next_tab_btn)
        
        layout.addLayout(tab_container, 1)  # Give tab container most of the space
        
        # Create and add modular settings widgets
        self.create_settings_tabs()
        
        # Connect tab change signal
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        # Button box
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Apply
        )
        self.button_box.accepted.connect(self.accept_settings)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.apply_settings)
        layout.addWidget(self.button_box)
        
        # Update navigation buttons
        self.update_navigation_buttons()
        
    def create_settings_tabs(self):
        """Create all settings tabs using modular widgets"""
        
        # General Settings
        general_widget = GeneralSettingsWidget(self.settings_controller, self.logger)
        self.settings_widgets['general'] = general_widget
        self.tabs.addTab(general_widget, "General")
        
        # PDF Settings
        pdf_widget = PDFSettingsWidget(self.settings_controller, self.logger)
        self.settings_widgets['pdf'] = pdf_widget
        self.tabs.addTab(pdf_widget, "PDF")
        
        # Interface Settings
        interface_widget = InterfaceSettingsWidget(self.settings_controller, self.logger)
        self.settings_widgets['interface'] = interface_widget
        self.tabs.addTab(interface_widget, "Interface")
        
        # Text-to-Speech Settings
        tts_widget = TTSSettingsWidget(self.settings_controller, self.logger)
        self.settings_widgets['tts'] = tts_widget
        self.tabs.addTab(tts_widget, "Text to Speech")
        
        # Editor Settings
        editor_widget = EditorSettingsWidget(self.settings_controller, self.logger)
        self.settings_widgets['editor'] = editor_widget
        self.tabs.addTab(editor_widget, "Editor")
        
        # Auto-Import Settings
        auto_import_widget = AutoImportSettingsWidget(self.settings_controller, self.logger)
        self.settings_widgets['auto_import'] = auto_import_widget
        self.tabs.addTab(auto_import_widget, "Auto-Import")
        
        # Advanced Settings
        advanced_widget = AdvancedSettingsWidget(self.settings_controller, self.logger)
        self.settings_widgets['advanced'] = advanced_widget
        self.tabs.addTab(advanced_widget, "Advanced")
        
        # Logging Settings
        logging_widget = LoggingSettingsWidget(self.settings_controller, self.logger)
        self.settings_widgets['logging'] = logging_widget
        self.tabs.addTab(logging_widget, "Logging")
        
        # Tutorial Settings
        tutorial_widget = TutorialSettingsWidget(self.settings_controller, self.logger)
        self.settings_widgets['tutorial'] = tutorial_widget
        self.tabs.addTab(tutorial_widget, "Tutorials")
        
        self.logger.info("ModularSettingsDialog", f"Created {len(self.settings_widgets)} modular settings widgets")
        
    def load_all_settings(self):
        """Load settings for all modular widgets"""
        for widget_name, widget in self.settings_widgets.items():
            try:
                widget.load_settings()
                self.logger.debug("ModularSettingsDialog", f"Loaded settings for {widget_name}")
            except Exception as e:
                self.logger.error("ModularSettingsDialog", f"Error loading settings for {widget_name}: {str(e)}")
                
    def save_all_settings(self):
        """Save settings for all modular widgets"""
        for widget_name, widget in self.settings_widgets.items():
            try:
                widget.save_settings()
                self.logger.debug("ModularSettingsDialog", f"Saved settings for {widget_name}")
            except Exception as e:
                self.logger.error("ModularSettingsDialog", f"Error saving settings for {widget_name}: {str(e)}")
                
        # Save settings to file
        self.settings_controller.save_settings()
        self.logger.info("ModularSettingsDialog", "All settings saved successfully")
        
    def apply_settings(self):
        """Apply settings without closing dialog"""
        self.save_all_settings()
        self.logger.info("ModularSettingsDialog", "Settings applied")
        
    def accept_settings(self):
        """Accept and save settings, then close dialog"""
        self.save_all_settings()
        self.accept()
        
    def previous_tab(self):
        """Navigate to previous tab"""
        current_index = self.tabs.currentIndex()
        if current_index > 0:
            self.tabs.setCurrentIndex(current_index - 1)
            
    def next_tab(self):
        """Navigate to next tab"""
        current_index = self.tabs.currentIndex()
        if current_index < self.tabs.count() - 1:
            self.tabs.setCurrentIndex(current_index + 1)
            
    def on_tab_changed(self, index):
        """Handle tab change"""
        tab_names = [
            "General", "PDF", "Interface", "Text to Speech", "Editor",
            "Auto-Import", "Advanced", "Logging", "Tutorials"
        ]
        
        if 0 <= index < len(tab_names):
            self.setWindowTitle(f"Settings - {tab_names[index]} ({index + 1}/{len(tab_names)})")
            
        self.update_navigation_buttons()
        
    def update_navigation_buttons(self):
        """Update navigation button states"""
        current_index = self.tabs.currentIndex()
        self.prev_tab_btn.setEnabled(current_index > 0)
        self.next_tab_btn.setEnabled(current_index < self.tabs.count() - 1)


# For backward compatibility, keep the original class name as an alias
class SettingsDialog(ModularSettingsDialog):
    """Backward compatibility alias for ModularSettingsDialog"""
    pass
