#!/usr/bin/env python3
"""
Completely Rebuilt Modular Settings Dialog
Clean implementation with proper layout management
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTabWidget, 
    QDialogButtonBox, QWidget, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize

from settings_controller import SettingsController
from PDFLogger import Logger

# Import all the modular settings widgets
from Settings.general_settings_widget import GeneralSettingsWidget
from Settings.pdf_settings_widget import PDFSettingsWidget
from Settings.tts_settings_widget import TTSSettingsWidget
from Settings.editor_settings_widget import EditorSettingsWidget
from Settings.auto_import_settings_widget import AutoImportSettingsWidget
from Settings.advanced_settings_widget import AdvancedSettingsWidget
from Settings.logging_settings_widget import LoggingSettingsWidget
from Settings.tutorial_settings_widget import TutorialSettingsWidget

class RebuildSettingsDialog(QDialog):
    """Completely rebuilt settings dialog with proper layout"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = Logger()
        self.parent = parent
        
        # Use the parent's settings controller if available, otherwise create a new one
        if parent and hasattr(parent, 'settings'):
            self.logger.info("RebuildSettingsDialog", "Using parent's settings controller")
            self.settings_controller = parent.settings
        else:
            self.logger.info("RebuildSettingsDialog", "Creating new settings controller")
            self.settings_controller = SettingsController()
        
        # Ensure settings are loaded
        self.settings_controller.load_settings()
        
        # Set dialog properties
        self.setWindowTitle("Settings")
        self.setModal(True)
        
        # Set a fixed size that works well
        self.setFixedSize(900, 700)
        
        # Keep track of settings widgets for easy access
        self.settings_widgets = {}
        
        self.setup_ui()
        self.load_all_settings()
        
        # Set initial tab title after setup is complete
        self.on_tab_changed(0)  # Trigger title update for first tab
        
    def setup_ui(self):
        """Setup the complete UI with proper layout"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Create navigation area
        nav_layout = QHBoxLayout()
        
        # Previous button
        self.prev_btn = QPushButton("◀ Previous")
        self.prev_btn.setFixedSize(100, 35)
        self.prev_btn.clicked.connect(self.previous_tab)
        nav_layout.addWidget(self.prev_btn)
        
        # Title label area (will be updated based on current tab)
        nav_layout.addStretch(1)
        
        # Next button  
        self.next_btn = QPushButton("Next ▶")
        self.next_btn.setFixedSize(100, 35)
        self.next_btn.clicked.connect(self.next_tab)
        nav_layout.addWidget(self.next_btn)
        
        main_layout.addLayout(nav_layout)
        
        # Create tab widget with proper sizing
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.tabs.setTabsClosable(False)
        self.tabs.setMovable(False)
        
        # Apply clean tab styling
        self.tabs.setStyleSheet("""
            QTabWidget {
                background-color: palette(window);
            }
            QTabWidget::pane {
                border: 1px solid palette(mid);
                background-color: palette(window);
                margin: 0px;
            }
            QTabBar::tab {
                background-color: palette(button);
                border: 1px solid palette(mid);
                border-bottom: none;
                padding: 10px 15px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                min-width: 100px;
                color: palette(button-text);
            }
            QTabBar::tab:selected {
                background-color: palette(window);
                border-bottom: 1px solid palette(window);
                color: palette(window-text);
            }
            QTabBar::tab:hover {
                background-color: palette(highlight);
                color: palette(highlighted-text);
            }
        """)
        
        # Connect tab change signal
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        # Create all settings tabs
        self.create_all_tabs()
        
        # Add tab widget to main layout with stretch
        main_layout.addWidget(self.tabs, 1)
        
        # Create button box
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Apply
        )
        self.button_box.accepted.connect(self.accept_settings)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.apply_settings)
        
        main_layout.addWidget(self.button_box)
        
        # Update navigation buttons
        self.update_navigation_buttons()
        
    def create_all_tabs(self):
        """Create all settings tabs with proper scroll areas"""
        
        # Tab definitions
        tab_definitions = [
            ("General", GeneralSettingsWidget, "general"),
            ("PDF", PDFSettingsWidget, "pdf"),
            ("Text-to-Speech", TTSSettingsWidget, "tts"),
            ("Editor", EditorSettingsWidget, "editor"),
            ("Auto-Import", AutoImportSettingsWidget, "auto_import"),
            ("Advanced", AdvancedSettingsWidget, "advanced"),
            ("Logging", LoggingSettingsWidget, "logging"),
            ("Tutorials", TutorialSettingsWidget, "tutorial")
        ]
        
        for tab_name, widget_class, widget_key in tab_definitions:
            # Create the settings widget
            settings_widget = widget_class(self.settings_controller, self.logger)
            
            # Create a scroll area for the widget
            scroll_area = QScrollArea()
            scroll_area.setWidget(settings_widget)
            scroll_area.setWidgetResizable(True)
            scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            
            # Theme-compatible scroll area styling
            scroll_area.setStyleSheet("""
                QScrollArea {
                    border: none;
                    background-color: palette(window);
                }
                QScrollBar:vertical {
                    background-color: palette(base);
                    border: 1px solid palette(mid);
                    border-radius: 3px;
                    width: 12px;
                }
                QScrollBar::handle:vertical {
                    background-color: palette(button);
                    border-radius: 3px;
                    min-height: 20px;
                }
                QScrollBar::handle:vertical:hover {
                    background-color: palette(highlight);
                }
            """)
            
            # Set size policies
            scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            settings_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            
            # Ensure minimum size for content
            settings_widget.setMinimumSize(750, 400)
            
            # Store widget reference
            self.settings_widgets[widget_key] = settings_widget
            
            # Add tab with scroll area
            self.tabs.addTab(scroll_area, tab_name)
            
        self.logger.info("RebuildSettingsDialog", f"Created {len(self.settings_widgets)} settings tabs")
        
    def load_all_settings(self):
        """Load settings for all modular widgets"""
        for widget_name, widget in self.settings_widgets.items():
            try:
                widget.load_settings()
                self.logger.debug("RebuildSettingsDialog", f"Loaded settings for {widget_name}")
            except Exception as e:
                self.logger.error("RebuildSettingsDialog", f"Error loading settings for {widget_name}: {str(e)}")
                
    def save_all_settings(self):
        """Save settings for all modular widgets"""
        for widget_name, widget in self.settings_widgets.items():
            try:
                widget.save_settings()
                self.logger.debug("RebuildSettingsDialog", f"Saved settings for {widget_name}")
            except Exception as e:
                self.logger.error("RebuildSettingsDialog", f"Error saving settings for {widget_name}: {str(e)}")
                
        # Save settings to file
        self.settings_controller.save_settings()
        self.logger.info("RebuildSettingsDialog", "All settings saved successfully")
        
    def apply_settings(self):
        """Apply settings without closing dialog"""
        self.save_all_settings()
        self.logger.info("RebuildSettingsDialog", "Settings applied")
        
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
        # Update window title with current tab info
        if 0 <= index < self.tabs.count():
            tab_name = self.tabs.tabText(index)
            self.setWindowTitle(f"Settings - {tab_name} ({index + 1}/{self.tabs.count()})")
            
        self.update_navigation_buttons()
        
    def update_navigation_buttons(self):
        """Update navigation button states"""
        current_index = self.tabs.currentIndex()
        self.prev_btn.setEnabled(current_index > 0)
        self.next_btn.setEnabled(current_index < self.tabs.count() - 1)


# Main class for compatibility
class SettingsDialog(RebuildSettingsDialog):
    """Main settings dialog class - now uses rebuilt implementation"""
    pass


# Keep old class name for compatibility
class ModularSettingsDialog(RebuildSettingsDialog):
    """Backward compatibility alias"""
    pass
