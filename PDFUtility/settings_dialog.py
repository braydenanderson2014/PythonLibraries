#!/usr/bin/env python3
# settings_dialog.py - Settings Dialog for PDF Utility

import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QCheckBox,
    QComboBox, QPushButton, QFileDialog, QTabWidget, QGroupBox,
    QFormLayout, QSpinBox, QDialogButtonBox, QMessageBox, QWidget,
    QSlider, QListWidget
)
from PyQt6.QtCore import Qt

import subprocess
import platform
from settings_controller import SettingsController
from PDFLogger import Logger

class SettingsDialog(QDialog):
    """Settings dialog for PDF Utility"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = Logger()
        self.parent = parent
        
        # Use the parent's settings controller if available, otherwise create a new one
        if parent and hasattr(parent, 'settings'):
            self.logger.info("SettingsDialog", "Using parent's settings controller")
            self.settings_controller = parent.settings
        else:
            self.logger.info("SettingsDialog", "Creating new settings controller")
            self.settings_controller = SettingsController()
        
        # Ensure settings are loaded and log the current auto-import status
        self.settings_controller.load_settings()
        enabled = self.settings_controller.get_setting("auto_import", "enabled", False)
        watch_dir = self.settings_controller.get_setting("auto_import", "watch_directory", "")
        self.logger.info("SettingsDialog", f"Current auto-import status: enabled={enabled}, watch_dir={watch_dir}")
        
        self.setWindowTitle("Settings - General (1/9)")
        self.setMinimumWidth(600)  # Increased width for better tab visibility
        self.setMinimumHeight(500)  # Increased height for better content display
        
        self.initUI()
        self.loadSettings()
        
    def initUI(self):
        """Initialize the UI"""
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
        
        # Style the tab widget for better visibility but smaller tabs
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
                border-bottom-color: #c2c7cb;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                min-width: 80px;
                max-width: 120px;
                min-height: 25px;
                padding: 6px 12px;
                margin-right: 1px;
                font-weight: normal;
                font-size: 11px;
                color: #2c3e50;
            }
            
            QTabBar::tab:selected {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #ffffff, stop: 1 #f0f0f0);
                border-color: #3498db;
                border-bottom-color: #f0f0f0;
                color: #3498db;
                font-weight: bold;
            }
            
            QTabBar::tab:hover:!selected {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #e8f4fd, stop: 1 #bedcfa);
                border-color: #85c1e9;
                color: #2980b9;
            }
            
            QTabBar::tab:first {
                margin-left: 0;
            }
            
            QTabBar::tab:last {
                margin-right: 0;
            }
        """)
        
        # Right navigation arrow
        self.next_tab_btn = QPushButton("▶")
        self.next_tab_btn.setFixedSize(40, 40)
        self.next_tab_btn.setStyleSheet("""
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
        self.next_tab_btn.clicked.connect(self.next_tab)
        self.next_tab_btn.setToolTip("Next settings tab")
        
        # Add components to horizontal layout
        tab_container.addWidget(self.prev_tab_btn)
        tab_container.addWidget(self.tabs, 1)  # Give tabs most of the space
        tab_container.addWidget(self.next_tab_btn)
        
        # Create a widget to hold the tab container
        tab_widget = QWidget()
        tab_widget.setLayout(tab_container)
        
        # Create general settings tab
        self.general_tab = QWidget()
        self.createGeneralTab()
        self.tabs.addTab(self.general_tab, "General")
        
        # Create PDF settings tab
        self.pdf_tab = QWidget()
        self.createPDFTab()
        self.tabs.addTab(self.pdf_tab, "PDF")
        
        # Create interface settings tab
        self.interface_tab = QWidget()
        self.createInterfaceTab()
        self.tabs.addTab(self.interface_tab, "Interface")
        
        # Create TTS settings tab
        self.tts_tab = QWidget()
        self.createTTSTab()
        self.tabs.addTab(self.tts_tab, "Text to Speech")
        
        # Create editor settings tab
        self.editor_tab = QWidget()
        self.createEditorTab()
        self.tabs.addTab(self.editor_tab, "Editor")
        
        # Create auto-import settings tab
        self.auto_import_tab = QWidget()
        self.createAutoImportTab()
        self.tabs.addTab(self.auto_import_tab, "Auto-Import")
        
        # Create advanced settings tab
        self.advanced_tab = QWidget()
        self.createAdvancedTab()
        self.tabs.addTab(self.advanced_tab, "Advanced")
        
        # Create logging settings tab
        self.logging_tab = QWidget()
        self.createLoggingTab()
        self.tabs.addTab(self.logging_tab, "Logging")
        
        # Create tutorial settings tab
        self.tutorial_tab = QWidget()
        self.createTutorialTab()
        self.tabs.addTab(self.tutorial_tab, "Tutorials")
        
        # Connect tab change signal to update status
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        # Set initial tab focus to General (tab 0)
        self.tabs.setCurrentIndex(0)
        
        # Add tabs to layout
        layout.addWidget(tab_widget)
        
        # Update button states based on current tab
        self.update_navigation_buttons()
        
        # Add a small hint about tabs at the bottom for first-time users
        hint_label = QLabel("💡 Tip: Click on the tabs above to access different settings categories")
        hint_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-style: italic;
                font-size: 11px;
                padding: 5px;
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 3px;
                margin: 5px 0px;
            }
        """)
        hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint_label)
        
        # Add buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Apply
        )
        
        # Add Restore Defaults button
        self.restore_defaults_button = QPushButton("Restore Defaults")
        self.restore_defaults_button.clicked.connect(self.restore_defaults)
        button_box.addButton(self.restore_defaults_button, QDialogButtonBox.ButtonRole.ResetRole)
        
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.apply_settings)
        layout.addWidget(button_box)
        
    def createGeneralTab(self):
        """Create the general settings tab"""
        layout = QVBoxLayout(self.general_tab)
        
        # General settings group
        general_group = QGroupBox("General Settings")
        general_layout = QFormLayout(general_group)
        
        # Theme selection
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["System", "Light", "Dark"])
        general_layout.addRow("Theme:", self.theme_combo)
        
        # Language selection
        self.language_combo = QComboBox()
        self.language_combo.addItems(["English", "Spanish", "French"])
        general_layout.addRow("Language:", self.language_combo)
        
        # Check for updates
        self.update_check_cb = QCheckBox("Check for updates on startup")
        general_layout.addRow("", self.update_check_cb)
        
        # Recent files limit
        self.recent_files_spin = QSpinBox()
        self.recent_files_spin.setMinimum(0)
        self.recent_files_spin.setMaximum(30)
        self.recent_files_spin.setValue(10)
        general_layout.addRow("Maximum recent files:", self.recent_files_spin)
        
        # Last used directory
        self.last_dir_edit = QLineEdit()
        self.last_dir_edit.setReadOnly(True)
        
        last_dir_layout = QHBoxLayout()
        last_dir_layout.addWidget(self.last_dir_edit)
        
        last_dir_btn = QPushButton("Browse...")
        last_dir_btn.clicked.connect(self.browse_last_dir)
        last_dir_layout.addWidget(last_dir_btn)
        
        last_dir_open_btn = QPushButton("Open")
        last_dir_open_btn.clicked.connect(lambda: self.open_directory(self.last_dir_edit.text()))
        last_dir_layout.addWidget(last_dir_open_btn)
        
        general_layout.addRow("Last used directory:", last_dir_layout)
        
        # Add to layout
        layout.addWidget(general_group)
        layout.addStretch()
        
    def createPDFTab(self):
        """Create the PDF settings tab"""
        layout = QVBoxLayout(self.pdf_tab)
        
        # PDF settings group
        pdf_group = QGroupBox("PDF Settings")
        pdf_layout = QFormLayout(pdf_group)
        
        # Default output directory
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setReadOnly(True)
        
        output_dir_layout = QHBoxLayout()
        output_dir_layout.addWidget(self.output_dir_edit)
        
        output_dir_btn = QPushButton("Browse...")
        output_dir_btn.clicked.connect(self.browse_output_dir)
        output_dir_layout.addWidget(output_dir_btn)
        
        output_open_btn = QPushButton("Open")
        output_open_btn.clicked.connect(lambda: self.open_directory(self.output_dir_edit.text()))
        output_dir_layout.addWidget(output_open_btn)
        
        pdf_layout.addRow("Default output directory:", output_dir_layout)
        
        # Default merge directory
        self.merge_dir_edit = QLineEdit()
        self.merge_dir_edit.setReadOnly(True)
        
        merge_dir_layout = QHBoxLayout()
        merge_dir_layout.addWidget(self.merge_dir_edit)
        
        merge_dir_btn = QPushButton("Browse...")
        merge_dir_btn.clicked.connect(self.browse_merge_dir)
        merge_dir_layout.addWidget(merge_dir_btn)
        
        merge_open_btn = QPushButton("Open")
        merge_open_btn.clicked.connect(lambda: self.open_directory(self.merge_dir_edit.text()))
        merge_dir_layout.addWidget(merge_open_btn)
        
        pdf_layout.addRow("Default merge directory:", merge_dir_layout)
        
        # Default split directory
        self.split_dir_edit = QLineEdit()
        self.split_dir_edit.setReadOnly(True)
        
        split_dir_layout = QHBoxLayout()
        split_dir_layout.addWidget(self.split_dir_edit)
        
        split_dir_btn = QPushButton("Browse...")
        split_dir_btn.clicked.connect(self.browse_split_dir)
        split_dir_layout.addWidget(split_dir_btn)
        
        split_open_btn = QPushButton("Open")
        split_open_btn.clicked.connect(lambda: self.open_directory(self.split_dir_edit.text()))
        split_dir_layout.addWidget(split_open_btn)
        
        pdf_layout.addRow("Default split directory:", split_dir_layout)
        
        # Default behavior checkbox for whitespace removal
        self.remove_white_space_cb = QCheckBox("Remove white space by default")
        self.remove_white_space_cb.setToolTip("Enable automatic white space removal when processing files")
        pdf_layout.addRow("Default behavior:", self.remove_white_space_cb)
        
        # Compression level
        self.compression_combo = QComboBox()
        self.compression_combo.addItems(["None", "Low", "Medium", "High"])
        pdf_layout.addRow("Compression level:", self.compression_combo)
        
        # Add to layout
        layout.addWidget(pdf_group)
        layout.addStretch()
        
    def createInterfaceTab(self):
        """Create the interface settings tab"""
        layout = QVBoxLayout(self.interface_tab)
        
        # Interface settings group
        interface_group = QGroupBox("Interface Settings")
        interface_layout = QFormLayout(interface_group)
        
        # Show toolbar
        self.show_toolbar_cb = QCheckBox("Show toolbar")
        interface_layout.addRow("", self.show_toolbar_cb)
        
        # Show status bar
        self.show_statusbar_cb = QCheckBox("Show status bar")
        interface_layout.addRow("", self.show_statusbar_cb)
        
        # Confirm file delete
        self.confirm_delete_cb = QCheckBox("Confirm file delete")
        interface_layout.addRow("", self.confirm_delete_cb)
        
        # Preview quality
        self.preview_quality_combo = QComboBox()
        self.preview_quality_combo.addItems(["Low", "Medium", "High"])
        interface_layout.addRow("Preview quality:", self.preview_quality_combo)
        
        # Preview size
        self.preview_size_spin = QSpinBox()
        self.preview_size_spin.setMinimum(100)
        self.preview_size_spin.setMaximum(500)
        self.preview_size_spin.setSingleStep(10)
        interface_layout.addRow("Preview size (pixels):", self.preview_size_spin)
        
        # Add to layout
        layout.addWidget(interface_group)
        layout.addStretch()
        
    def createEditorTab(self):
        """Create the PDF Editor settings tab"""
        layout = QVBoxLayout(self.editor_tab)
        
        # Editor settings group
        editor_group = QGroupBox("Editor Settings")
        editor_layout = QFormLayout(editor_group)
        
        # Editor startup options
        startup_group = QGroupBox("Startup Behavior")
        startup_layout = QVBoxLayout(startup_group)
        
        self.editor_auto_open_cb = QCheckBox("Automatically open selected files in editor")
        self.editor_auto_open_cb.setToolTip("When launching the editor, automatically open any files that are currently selected")
        startup_layout.addWidget(self.editor_auto_open_cb)
        
        self.editor_remember_session_cb = QCheckBox("Remember last editing session")
        self.editor_remember_session_cb.setToolTip("Remember which files were open when the editor was last closed")
        startup_layout.addWidget(self.editor_remember_session_cb)
        
        self.editor_confirm_close_cb = QCheckBox("Confirm when closing with unsaved changes")
        self.editor_confirm_close_cb.setToolTip("Ask for confirmation before closing the editor with unsaved changes")
        startup_layout.addWidget(self.editor_confirm_close_cb)
        
        editor_layout.addRow(startup_group)
        
        # Editor appearance group
        appearance_group = QGroupBox("Appearance")
        appearance_layout = QFormLayout(appearance_group)
        
        self.editor_font_combo = QComboBox()
        self.editor_font_combo.addItems(["System Default", "Courier New", "Consolas", "Arial", "Times New Roman"])
        appearance_layout.addRow("Font:", self.editor_font_combo)
        
        self.editor_font_size_spin = QSpinBox()
        self.editor_font_size_spin.setRange(8, 24)
        self.editor_font_size_spin.setValue(12)
        appearance_layout.addRow("Font Size:", self.editor_font_size_spin)
        
        self.editor_syntax_highlighting_cb = QCheckBox("Enable syntax highlighting")
        appearance_layout.addRow("", self.editor_syntax_highlighting_cb)
        
        editor_layout.addRow(appearance_group)
        
        # Launch button
        launch_group = QGroupBox("Launch Editor")
        launch_layout = QVBoxLayout(launch_group)
        
        self.launch_editor_btn = QPushButton("Open PDF Editor")
        self.launch_editor_btn.clicked.connect(self.launch_editor)
        
        # Add help text
        launch_help = QLabel(
            "Opens the PDF editor in a new window. If files are selected in the main application, "
            "they will be automatically opened in the editor if the option above is enabled."
        )
        launch_help.setWordWrap(True)
        launch_help.setStyleSheet("color: gray; font-style: italic;")
        
        launch_layout.addWidget(self.launch_editor_btn)
        launch_layout.addWidget(launch_help)
        
        # Add groups to main layout
        layout.addWidget(editor_group)
        layout.addWidget(launch_group)
        layout.addStretch()
    
    def createTTSTab(self):
        """Create the text-to-speech settings tab"""
        layout = QVBoxLayout(self.tts_tab)
        
        # TTS Rate Group
        rate_group = QGroupBox("Speech Rate")
        rate_layout = QHBoxLayout(rate_group)
        
        self.tts_rate = QSlider(Qt.Orientation.Horizontal)
        self.tts_rate.setRange(50, 300)
        self.tts_rate.setValue(int(self.settings_controller.get_setting("tts", "rate", 150)))
        self.tts_rate_label = QLabel(str(self.tts_rate.value()))
        self.tts_rate.valueChanged.connect(lambda v: self.tts_rate_label.setText(str(v)))
        
        rate_layout.addWidget(self.tts_rate)
        rate_layout.addWidget(self.tts_rate_label)
        
        # TTS Volume Group
        volume_group = QGroupBox("Speech Volume")
        volume_layout = QHBoxLayout(volume_group)
        
        self.tts_volume = QSlider(Qt.Orientation.Horizontal)
        self.tts_volume.setRange(0, 100)
        volume_percent = int(float(self.settings_controller.get_setting("tts", "volume", 1.0)) * 100)
        self.tts_volume.setValue(volume_percent)
        self.tts_volume_label = QLabel(f"{volume_percent}%")
        self.tts_volume.valueChanged.connect(lambda v: self.tts_volume_label.setText(f"{v}%"))
        
        volume_layout.addWidget(self.tts_volume)
        volume_layout.addWidget(self.tts_volume_label)
        
        # TTS Voice Selection Group
        voice_group = QGroupBox("Voice Selection")
        voice_layout = QFormLayout(voice_group)
        
        self.tts_voice_combo = QComboBox()
        # Add default option
        self.tts_voice_combo.addItem("System Default")
        
        # Try to populate with system voices
        try:
            import pyttsx3
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            for voice in voices:
                # Use just the first part of the name (e.g., "Microsoft David Desktop" -> "David")
                voice_name = voice.name.split(' - ')[0]  # Remove language part
                if 'Microsoft' in voice_name:
                    # Extract just the voice name (e.g., "Microsoft David Desktop" -> "David")
                    clean_name = voice_name.replace('Microsoft ', '').replace(' Desktop', '')
                    self.tts_voice_combo.addItem(clean_name, voice.id)  # Store voice ID as data
                else:
                    self.tts_voice_combo.addItem(voice.name, voice.id)
            engine.stop()
        except Exception as e:
            # If there's an error loading voices, add placeholders
            self.logger.error("SettingsDialog", f"Error loading TTS voices: {str(e)}")
            self.tts_voice_combo.addItem("David")
            self.tts_voice_combo.addItem("Zira")
        
        # Get saved voice setting or use default
        saved_voice = self.settings_controller.get_setting("tts", "voice", "System Default")
        
        # Try to find the voice by data (voice ID) first, then by text (display name)
        voice_index = -1
        
        # First, check if saved_voice matches any item's data (voice ID)
        for i in range(self.tts_voice_combo.count()):
            if self.tts_voice_combo.itemData(i) == saved_voice:
                voice_index = i
                break
        
        # If not found by data, try to find by display text
        if voice_index < 0:
            voice_index = self.tts_voice_combo.findText(saved_voice)
        
        # Set the selected voice if found, otherwise keep default selection
        if voice_index >= 0:
            self.tts_voice_combo.setCurrentIndex(voice_index)
        
        voice_layout.addRow("Select Voice:", self.tts_voice_combo)
        
        # Add groups to main layout
        layout.addWidget(rate_group)
        layout.addWidget(volume_group)
        layout.addWidget(voice_group)
        
        # Test TTS button
        test_layout = QHBoxLayout()
        self.test_text_edit = QLineEdit("This is a test of text-to-speech.")
        self.test_button = QPushButton("Test Voice")
        # Connect the button to a method that would play the text
        self.test_button.clicked.connect(self.test_tts_voice)
        
        test_layout.addWidget(self.test_text_edit)
        test_layout.addWidget(self.test_button)
        
        layout.addLayout(test_layout)
        layout.addStretch()
    
    def createAdvancedTab(self):
        """Create the advanced settings tab"""
        layout = QVBoxLayout(self.advanced_tab)
        
        # Advanced settings group
        advanced_group = QGroupBox("Advanced Settings")
        advanced_layout = QFormLayout(advanced_group)
        
        # Parallel processing
        self.parallel_processing_cb = QCheckBox("Enable parallel processing")
        advanced_layout.addRow("", self.parallel_processing_cb)
        
        # Max processes
        self.max_processes_spin = QSpinBox()
        self.max_processes_spin.setMinimum(0)
        self.max_processes_spin.setMaximum(32)
        self.max_processes_spin.setSpecialValueText("Auto")
        advanced_layout.addRow("Maximum processes (0 = auto):", self.max_processes_spin)
        
        # Temp directory
        self.temp_dir_edit = QLineEdit()
        self.temp_dir_edit.setReadOnly(True)
        
        temp_dir_layout = QHBoxLayout()
        temp_dir_layout.addWidget(self.temp_dir_edit)
        
        temp_dir_btn = QPushButton("Browse...")
        temp_dir_btn.clicked.connect(self.browse_temp_dir)
        temp_dir_layout.addWidget(temp_dir_btn)
        
        temp_open_btn = QPushButton("Open")
        temp_open_btn.clicked.connect(lambda: self.open_directory(self.temp_dir_edit.text()))
        temp_dir_layout.addWidget(temp_open_btn)
        
        advanced_layout.addRow("Temporary directory:", temp_dir_layout)
        
        # Log level
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["Debug", "Info", "Warning", "Error"])
        advanced_layout.addRow("Log level:", self.log_level_combo)
        
        # Add to layout
        layout.addWidget(advanced_group)
        layout.addStretch()
        
    def createLoggingTab(self):
        """Create the logging settings tab"""
        layout = QVBoxLayout(self.logging_tab)
        
        # Log File Settings group
        log_file_group = QGroupBox("Log File Settings")
        log_file_layout = QFormLayout(log_file_group)
        
        # Log directory
        self.log_dir_edit = QLineEdit()
        self.log_dir_edit.setReadOnly(True)
        
        log_dir_layout = QHBoxLayout()
        log_dir_layout.addWidget(self.log_dir_edit)
        
        log_dir_btn = QPushButton("Browse...")
        log_dir_btn.clicked.connect(self.browse_log_dir)
        log_dir_layout.addWidget(log_dir_btn)
        
        log_dir_open_btn = QPushButton("Open")
        log_dir_open_btn.clicked.connect(lambda: self.open_directory(self.log_dir_edit.text()))
        log_dir_layout.addWidget(log_dir_open_btn)
        
        log_file_layout.addRow("Log directory:", log_dir_layout)
        
        # Log filename
        self.log_filename_edit = QLineEdit()
        log_file_layout.addRow("Log filename:", self.log_filename_edit)
        
        # Open log file button
        log_file_actions_layout = QHBoxLayout()
        
        self.open_log_btn = QPushButton("Open Log File")
        self.open_log_btn.clicked.connect(self.open_log_file)
        log_file_actions_layout.addWidget(self.open_log_btn)
        
        self.clear_log_btn = QPushButton("Clear Log File")
        self.clear_log_btn.clicked.connect(self.clear_log_file)
        log_file_actions_layout.addWidget(self.clear_log_btn)
        
        log_file_actions_layout.addStretch()
        log_file_layout.addRow("Actions:", log_file_actions_layout)
        
        layout.addWidget(log_file_group)
        
        # Log Management Settings group
        log_mgmt_group = QGroupBox("Log Management")
        log_mgmt_layout = QFormLayout(log_mgmt_group)
        
        # Auto clear logs
        self.auto_clear_logs_cb = QCheckBox("Automatically clear old logs")
        log_mgmt_layout.addRow("", self.auto_clear_logs_cb)
        
        # Clear logs interval
        self.clear_logs_interval_spin = QSpinBox()
        self.clear_logs_interval_spin.setMinimum(0)
        self.clear_logs_interval_spin.setMaximum(365)
        self.clear_logs_interval_spin.setSpecialValueText("Never")
        self.clear_logs_interval_spin.setSuffix(" days")
        log_mgmt_layout.addRow("Clear logs every:", self.clear_logs_interval_spin)
        
        # Max log file size
        self.max_log_size_spin = QSpinBox()
        self.max_log_size_spin.setMinimum(0)
        self.max_log_size_spin.setMaximum(1000)
        self.max_log_size_spin.setSpecialValueText("No limit")
        self.max_log_size_spin.setSuffix(" MB")
        log_mgmt_layout.addRow("Max log file size:", self.max_log_size_spin)
        
        # Keep log backups
        self.keep_log_backups_spin = QSpinBox()
        self.keep_log_backups_spin.setMinimum(0)
        self.keep_log_backups_spin.setMaximum(50)
        self.keep_log_backups_spin.setSpecialValueText("None")
        log_mgmt_layout.addRow("Keep backup files:", self.keep_log_backups_spin)
        
        # Open log in editor
        self.open_log_in_editor_cb = QCheckBox("Open log files in default text editor")
        log_mgmt_layout.addRow("", self.open_log_in_editor_cb)
        
        layout.addWidget(log_mgmt_group)
        
        # Log Information group
        log_info_group = QGroupBox("Log Information")
        log_info_layout = QFormLayout(log_info_group)
        
        # Current log file size
        self.current_log_size_label = QLabel("0.00 MB")
        log_info_layout.addRow("Current log size:", self.current_log_size_label)
        
        # Last cleared
        self.last_cleared_label = QLabel("Never")
        log_info_layout.addRow("Last cleared:", self.last_cleared_label)
        
        # Refresh info button
        self.refresh_log_info_btn = QPushButton("Refresh Info")
        self.refresh_log_info_btn.clicked.connect(self.refresh_log_info)
        log_info_layout.addRow("", self.refresh_log_info_btn)
        
        layout.addWidget(log_info_group)
        layout.addStretch()
    
    def createTutorialTab(self):
        """Create tutorial settings tab"""
        layout = QVBoxLayout(self.tutorial_tab)
        
        # Main tutorial system group
        main_group = QGroupBox("Tutorial System")
        main_layout = QFormLayout(main_group)
        
        # Enable/disable tutorials
        self.enable_tutorials_cb = QCheckBox("Enable interactive tutorials")
        self.enable_tutorials_cb.setToolTip("Enable or disable the entire tutorial system")
        main_layout.addRow("", self.enable_tutorials_cb)
        
        # Auto-start for new users
        self.auto_start_cb = QCheckBox("Auto-start tutorials for new users")
        self.auto_start_cb.setToolTip("Automatically show tutorials when the application starts for the first time")
        main_layout.addRow("", self.auto_start_cb)
        
        # Show first-run tutorials
        self.first_run_cb = QCheckBox("Show first-run tutorials")
        self.first_run_cb.setToolTip("Show tutorials that explain basic application features")
        main_layout.addRow("", self.first_run_cb)
        
        # Show on tab switch
        self.show_on_tab_switch_cb = QCheckBox("Show tutorials when switching to new tabs")
        self.show_on_tab_switch_cb.setToolTip("Automatically show tutorials for widgets when you first switch to their tab")
        main_layout.addRow("", self.show_on_tab_switch_cb)
        
        # Animation speed
        self.animation_speed_combo = QComboBox()
        self.animation_speed_combo.addItems(["slow", "normal", "fast"])
        self.animation_speed_combo.setToolTip("Speed of tutorial animations and transitions")
        main_layout.addRow("Animation speed:", self.animation_speed_combo)
        
        layout.addWidget(main_group)
        
        # Tutorial management group
        manage_group = QGroupBox("Tutorial Management")
        manage_layout = QFormLayout(manage_group)
        
        # Tutorial selection for reset
        tutorial_layout = QHBoxLayout()
        self.tutorial_combo = QComboBox()
        self.tutorial_combo.addItems([
            "main_application",
            "split_widget", 
            "merge_widget",
            "image_converter",
            "search_widget",
            "white_space",
            "text_to_speech",
            "auto_import",
            "settings"
        ])
        tutorial_layout.addWidget(self.tutorial_combo)
        
        self.reset_specific_btn = QPushButton("Reset Selected")
        self.reset_specific_btn.clicked.connect(self.reset_specific_tutorial)
        tutorial_layout.addWidget(self.reset_specific_btn)
        
        manage_layout.addRow("Reset specific tutorial:", tutorial_layout)
        
        # Reset all button
        self.reset_all_btn = QPushButton("Reset All Tutorials")
        self.reset_all_btn.clicked.connect(self.reset_all_tutorials)
        self.reset_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        manage_layout.addRow("", self.reset_all_btn)
        
        layout.addWidget(manage_group)
        
        # Tutorial status group
        status_group = QGroupBox("Tutorial Status")
        status_layout = QFormLayout(status_group)
        
        self.tutorial_status_label = QLabel()
        self.tutorial_status_label.setWordWrap(True)
        status_layout.addRow("", self.tutorial_status_label)
        
        # Refresh status button
        self.refresh_tutorial_status_btn = QPushButton("Refresh Status")
        self.refresh_tutorial_status_btn.clicked.connect(self.update_tutorial_status)
        status_layout.addRow("", self.refresh_tutorial_status_btn)
        
        layout.addWidget(status_group)
        layout.addStretch()
        
        # Connect signals for dependent controls
        self.enable_tutorials_cb.toggled.connect(self.on_tutorial_enable_changed)
        
    def browse_last_dir(self):
        """Browse for last used directory"""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Last Used Directory", self.last_dir_edit.text()
        )
        
        if directory:
            self.last_dir_edit.setText(directory)
            
    def browse_output_dir(self):
        """Browse for output directory"""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Default Output Directory", self.output_dir_edit.text()
        )
        
        if directory:
            self.output_dir_edit.setText(directory)
            
    def browse_merge_dir(self):
        """Browse for merge directory"""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Default Merge Directory", self.merge_dir_edit.text()
        )
        
        if directory:
            self.merge_dir_edit.setText(directory)
            
    def browse_split_dir(self):
        """Browse for split directory"""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Default Split Directory", self.split_dir_edit.text()
        )
        
        if directory:
            self.split_dir_edit.setText(directory)
            
    def browse_temp_dir(self):
        """Browse for temp directory"""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Temporary Directory", self.temp_dir_edit.text()
        )
        
        if directory:
            self.temp_dir_edit.setText(directory)
            
    def browse_log_dir(self):
        """Browse for log directory"""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Log Directory", self.log_dir_edit.text()
        )
        
        if directory:
            self.log_dir_edit.setText(directory)
            
    def open_log_file(self):
        """Open the current log file"""
        success, message = self.settings_controller.open_log_file()
        if not success:
            QMessageBox.warning(self, "Warning", message)
        
    def clear_log_file(self):
        """Clear the current log file"""
        reply = QMessageBox.question(
            self, "Clear Log File",
            "Are you sure you want to clear the log file? This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Import logger and clear logs
                from PDFLogger import Logger
                logger = Logger()
                logger.delete_logs()
                QMessageBox.information(self, "Success", "Log file cleared successfully.")
                self.refresh_log_info()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to clear log file: {str(e)}")
                
    def refresh_log_info(self):
        """Refresh the log information display"""
        try:
            # Update current log size with appropriate formatting
            formatted_size = self.settings_controller.get_log_file_size_formatted()
            self.current_log_size_label.setText(formatted_size)
            
            # Update last cleared info (check if log file exists and get creation time)
            log_file = self.settings_controller.get_log_file_path()
            if os.path.exists(log_file):
                import time
                created_time = os.path.getctime(log_file)
                formatted_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(created_time))
                self.last_cleared_label.setText(f"File created: {formatted_time}")
            else:
                self.last_cleared_label.setText("Log file not found")
                
        except Exception as e:
            self.current_log_size_label.setText("Error")
            self.last_cleared_label.setText("Error")
            
    def createAutoImportTab(self):
        """Create the auto-import settings tab"""
        layout = QVBoxLayout(self.auto_import_tab)
        
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
        layout.addWidget(self.auto_import_enabled_cb)
        
        # Watch directory group
        watch_dir_group = QGroupBox("Watch Directory")
        watch_dir_layout = QFormLayout(watch_dir_group)
        
        self.watch_dir_edit = QLineEdit()
        self.watch_dir_edit.setPlaceholderText("Directory to monitor for new PDF files")
        
        watch_dir_browse_btn = QPushButton("Browse...")
        watch_dir_browse_btn.clicked.connect(self.browse_watch_dir)
        
        watch_dir_input = QHBoxLayout()
        watch_dir_input.addWidget(self.watch_dir_edit)
        watch_dir_input.addWidget(watch_dir_browse_btn)
        
        watch_dir_open_btn = QPushButton("Open")
        watch_dir_open_btn.clicked.connect(lambda: self.open_directory(self.watch_dir_edit.text()))
        watch_dir_input.addWidget(watch_dir_open_btn)
        
        watch_dir_layout.addRow("Watch Directory:", watch_dir_input)
        layout.addWidget(watch_dir_group)
        
        # Processed directory group
        processed_dir_group = QGroupBox("Processed Files")
        processed_dir_layout = QFormLayout(processed_dir_group)
        
        self.move_after_import_cb = QCheckBox("Move files after import")
        self.move_after_import_cb.setToolTip("Move PDF files to another directory after importing them")
        processed_dir_layout.addRow("", self.move_after_import_cb)
        
        self.processed_dir_edit = QLineEdit()
        self.processed_dir_edit.setPlaceholderText("Directory to move processed PDF files to")
        
        processed_dir_browse_btn = QPushButton("Browse...")
        processed_dir_browse_btn.clicked.connect(self.browse_processed_dir)
        
        processed_dir_input = QHBoxLayout()
        processed_dir_input.addWidget(self.processed_dir_edit)
        processed_dir_input.addWidget(processed_dir_browse_btn)
        
        processed_dir_open_btn = QPushButton("Open")
        processed_dir_open_btn.clicked.connect(lambda: self.open_directory(self.processed_dir_edit.text()))
        processed_dir_input.addWidget(processed_dir_open_btn)
        
        processed_dir_layout.addRow("Processed Directory:", processed_dir_input)
        layout.addWidget(processed_dir_group)
        
        # Advanced options group
        advanced_group = QGroupBox("Advanced Options")
        advanced_layout = QFormLayout(advanced_group)
        
        self.auto_process_cb = QCheckBox("Automatically process imported files")
        self.auto_process_cb.setToolTip("Automatically process files after importing them")
        advanced_layout.addRow("", self.auto_process_cb)
        
        self.check_interval_spin = QSpinBox()
        self.check_interval_spin.setRange(1, 60)
        self.check_interval_spin.setSuffix(" seconds")
        self.check_interval_spin.setToolTip("How often to check for new files (in seconds)")
        advanced_layout.addRow("Check Interval:", self.check_interval_spin)
        
        self.processing_delay_spin = QSpinBox()
        self.processing_delay_spin.setRange(1, 30)
        self.processing_delay_spin.setSuffix(" seconds")
        self.processing_delay_spin.setToolTip("Time to wait before moving a file to the processed directory")
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
    
    def browse_watch_dir(self):
        """Browse for watch directory"""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Watch Directory", self.watch_dir_edit.text()
        )
        
        if directory:
            self.watch_dir_edit.setText(directory)
            
    def browse_processed_dir(self):
        """Browse for processed files directory"""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Processed Files Directory", self.processed_dir_edit.text()
        )
        
        if directory:
            self.processed_dir_edit.setText(directory)
            
    def update_auto_import_status(self):
        """Update the auto-import status display"""
        # Check current settings from controller, not just UI
        enabled = self.auto_import_enabled_cb.isChecked()
        watch_dir = self.watch_dir_edit.text()
        
        # Log current state for debugging
        self.logger.info("SettingsDialog", f"Auto-import status: enabled={enabled}, watch_dir={watch_dir}")
        
        if enabled:
            if watch_dir and os.path.exists(watch_dir):
                self.status_value_label.setText("Enabled - Directory exists")
                self.status_value_label.setStyleSheet("color: green; font-weight: bold;")
            elif watch_dir:
                self.status_value_label.setText("Enabled - Directory will be created")
                self.status_value_label.setStyleSheet("color: orange; font-weight: bold;")
            else:
                self.status_value_label.setText("Enabled - No directory specified (monitoring will fail)")
                self.status_value_label.setStyleSheet("color: red; font-weight: bold;")
        else:
            self.status_value_label.setText("Disabled")
            self.status_value_label.setStyleSheet("color: gray; font-weight: bold;")
            
        # Enable/disable fields based on auto-import status
        self.watch_dir_edit.setEnabled(enabled)
        self.processed_dir_edit.setEnabled(enabled)
        self.move_after_import_cb.setEnabled(enabled)
        self.auto_process_cb.setEnabled(enabled)
        self.check_interval_spin.setEnabled(enabled)
            
    def loadSettings(self):
        """Load settings from the settings controller"""
        settings = self.settings_controller.settings
        
        # General settings
        theme = settings.get("general", {}).get("theme", "system").lower()
        theme_index = {"system": 0, "light": 1, "dark": 2}.get(theme, 0)
        self.theme_combo.setCurrentIndex(theme_index)
        
        language = settings.get("general", {}).get("language", "en")
        language_index = {"en": 0, "es": 1, "fr": 2}.get(language, 0)
        self.language_combo.setCurrentIndex(language_index)
        
        self.update_check_cb.setChecked(settings.get("general", {}).get("check_updates", True))
        self.recent_files_spin.setValue(settings.get("general", {}).get("max_recent_files", 10))
        self.last_dir_edit.setText(settings.get("general", {}).get("last_directory", ""))
        
        # PDF settings
        self.output_dir_edit.setText(settings.get("pdf", {}).get("default_output_dir", ""))
        self.merge_dir_edit.setText(settings.get("pdf", {}).get("default_merge_dir", ""))
        self.split_dir_edit.setText(settings.get("pdf", {}).get("default_split_dir", ""))
        self.remove_white_space_cb.setChecked(settings.get("pdf", {}).get("remove_white_space", False))
        
        # Only load the basic whitespace setting - other settings are handled in the WhiteSpaceWidget
        
        compression = settings.get("pdf", {}).get("compression_level", "medium").lower()
        compression_index = {"none": 0, "low": 1, "medium": 2, "high": 3}.get(compression, 2)
        self.compression_combo.setCurrentIndex(compression_index)
        
        # Interface settings
        self.show_toolbar_cb.setChecked(settings.get("interface", {}).get("show_toolbar", True))
        self.show_statusbar_cb.setChecked(settings.get("interface", {}).get("show_statusbar", True))
        self.confirm_delete_cb.setChecked(settings.get("interface", {}).get("confirm_file_delete", True))
        
        preview_quality = settings.get("interface", {}).get("preview_quality", "medium").lower()
        quality_index = {"low": 0, "medium": 1, "high": 2}.get(preview_quality, 1)
        self.preview_quality_combo.setCurrentIndex(quality_index)
        
        self.preview_size_spin.setValue(settings.get("interface", {}).get("preview_size", 200))
        
        # Advanced settings
        self.parallel_processing_cb.setChecked(settings.get("advanced", {}).get("parallel_processing", True))
        self.max_processes_spin.setValue(settings.get("advanced", {}).get("max_processes", 0))
        self.temp_dir_edit.setText(settings.get("advanced", {}).get("temp_dir", ""))
        
        log_level = settings.get("advanced", {}).get("log_level", "info").lower()
        log_level_index = {"debug": 0, "info": 1, "warning": 2, "error": 3}.get(log_level, 1)
        self.log_level_combo.setCurrentIndex(log_level_index)
        
        # TTS settings
        self.tts_rate.setValue(int(settings.get("tts", {}).get("rate", 150)))
        volume_percent = int(float(settings.get("tts", {}).get("volume", 1.0)) * 100)
        self.tts_volume.setValue(volume_percent)
        saved_voice = settings.get("tts", {}).get("voice", "System Default")
        
        # Try to find the voice by data (voice ID) first, then by text (display name)
        voice_index = -1
        
        # First, check if saved_voice matches any item's data (voice ID)
        for i in range(self.tts_voice_combo.count()):
            if self.tts_voice_combo.itemData(i) == saved_voice:
                voice_index = i
                break
        
        # If not found by data, try to find by display text
        if voice_index < 0:
            voice_index = self.tts_voice_combo.findText(saved_voice)
        
        # Set the selected voice if found, otherwise keep default selection
        if voice_index >= 0:
            self.tts_voice_combo.setCurrentIndex(voice_index)
            
        # Editor settings
        self.editor_auto_open_cb.setChecked(settings.get("editor", {}).get("auto_open_selected", True))
        self.editor_remember_session_cb.setChecked(settings.get("editor", {}).get("remember_session", True))
        self.editor_confirm_close_cb.setChecked(settings.get("editor", {}).get("confirm_unsaved_close", True))
        
        editor_font = settings.get("editor", {}).get("font", "System Default")
        font_index = self.editor_font_combo.findText(editor_font)
        if font_index >= 0:
            self.editor_font_combo.setCurrentIndex(font_index)
            
        self.editor_font_size_spin.setValue(settings.get("editor", {}).get("font_size", 12))
        self.editor_syntax_highlighting_cb.setChecked(settings.get("editor", {}).get("syntax_highlighting", True))
        
        # Auto-import settings
        self.auto_import_enabled_cb.setChecked(settings.get("auto_import", {}).get("enabled", False))
        self.watch_dir_edit.setText(settings.get("auto_import", {}).get("watch_directory", ""))
        self.processed_dir_edit.setText(settings.get("auto_import", {}).get("processed_directory", ""))
        self.move_after_import_cb.setChecked(settings.get("auto_import", {}).get("move_after_import", True))
        self.auto_process_cb.setChecked(settings.get("auto_import", {}).get("auto_process", False))
        self.check_interval_spin.setValue(settings.get("auto_import", {}).get("check_interval", 5))
        self.processing_delay_spin.setValue(settings.get("auto_import", {}).get("processing_delay", 3))
        
        # Update auto-import status display
        self.update_auto_import_status()
        
        # Logging settings
        self.log_dir_edit.setText(settings.get("logging", {}).get("log_directory", ""))
        self.log_filename_edit.setText(settings.get("logging", {}).get("log_filename", "pdf_utility.log"))
        self.auto_clear_logs_cb.setChecked(settings.get("logging", {}).get("auto_clear_logs", True))
        self.clear_logs_interval_spin.setValue(settings.get("logging", {}).get("clear_logs_interval", 7))
        self.max_log_size_spin.setValue(settings.get("logging", {}).get("max_log_size_mb", 10))
        self.keep_log_backups_spin.setValue(settings.get("logging", {}).get("keep_log_backups", 3))
        self.open_log_in_editor_cb.setChecked(settings.get("logging", {}).get("open_log_in_editor", True))
        
        # Refresh log information
        self.refresh_log_info()
        
        # Tutorial settings
        if hasattr(self, 'enable_tutorials_cb'):
            tutorial_settings = self.settings_controller.get_setting("tutorials", default={})
            self.enable_tutorials_cb.setChecked(tutorial_settings.get("enabled", True))
            self.auto_start_cb.setChecked(tutorial_settings.get("auto_start", True))
            self.first_run_cb.setChecked(tutorial_settings.get("show_first_run", True))
            self.show_on_tab_switch_cb.setChecked(tutorial_settings.get("show_on_tab_switch", True))
            self.animation_speed_combo.setCurrentText(tutorial_settings.get("animation_speed", "normal"))
            self.update_tutorial_status()
        
    def apply_settings(self):
        """Apply settings to the settings controller"""
        # General settings
        theme_map = {0: "system", 1: "light", 2: "dark"}
        language_map = {0: "en", 1: "es", 2: "fr"}
        
        self.settings_controller.set_setting("general", "theme", theme_map[self.theme_combo.currentIndex()])
        self.settings_controller.set_setting("general", "language", language_map[self.language_combo.currentIndex()])
        self.settings_controller.set_setting("general", "check_updates", self.update_check_cb.isChecked())
        self.settings_controller.set_setting("general", "max_recent_files", self.recent_files_spin.value())
        self.settings_controller.set_setting("general", "last_directory", self.last_dir_edit.text())
        
        # PDF settings
        self.settings_controller.set_setting("pdf", "default_output_dir", self.output_dir_edit.text())
        self.settings_controller.set_setting("pdf", "default_merge_dir", self.merge_dir_edit.text())
        self.settings_controller.set_setting("pdf", "default_split_dir", self.split_dir_edit.text())
        self.settings_controller.set_setting("pdf", "remove_white_space", self.remove_white_space_cb.isChecked())
        
        # Only save the basic whitespace setting - other settings are handled in the WhiteSpaceWidget
        
        compression_map = {0: "none", 1: "low", 2: "medium", 3: "high"}
        self.settings_controller.set_setting("pdf", "compression_level", compression_map[self.compression_combo.currentIndex()])
        
        # Interface settings
        self.settings_controller.set_setting("interface", "show_toolbar", self.show_toolbar_cb.isChecked())
        self.settings_controller.set_setting("interface", "show_statusbar", self.show_statusbar_cb.isChecked())
        self.settings_controller.set_setting("interface", "confirm_file_delete", self.confirm_delete_cb.isChecked())
        
        quality_map = {0: "low", 1: "medium", 2: "high"}
        self.settings_controller.set_setting("interface", "preview_quality", quality_map[self.preview_quality_combo.currentIndex()])
        self.settings_controller.set_setting("interface", "preview_size", self.preview_size_spin.value())
        
        # Advanced settings
        self.settings_controller.set_setting("advanced", "parallel_processing", self.parallel_processing_cb.isChecked())
        self.settings_controller.set_setting("advanced", "max_processes", self.max_processes_spin.value())
        self.settings_controller.set_setting("advanced", "temp_dir", self.temp_dir_edit.text())
        
        log_level_map = {0: "debug", 1: "info", 2: "warning", 3: "error"}
        self.settings_controller.set_setting("advanced", "log_level", log_level_map[self.log_level_combo.currentIndex()])
        
        # TTS settings
        self.settings_controller.set_setting("tts", "rate", self.tts_rate.value())
        self.settings_controller.set_setting("tts", "volume", float(self.tts_volume.value()) / 100.0)
        
        # Save voice ID if available, otherwise save display text for "System Default"
        current_voice_data = self.tts_voice_combo.currentData()
        if current_voice_data:
            # Save the voice ID for proper TTS engine selection
            self.settings_controller.set_setting("tts", "voice", current_voice_data)
        else:
            # For "System Default" or other items without data, save the display text
            self.settings_controller.set_setting("tts", "voice", self.tts_voice_combo.currentText())
        
        # Editor settings
        self.settings_controller.set_setting("editor", "auto_open_selected", self.editor_auto_open_cb.isChecked())
        self.settings_controller.set_setting("editor", "remember_session", self.editor_remember_session_cb.isChecked())
        self.settings_controller.set_setting("editor", "confirm_unsaved_close", self.editor_confirm_close_cb.isChecked())
        self.settings_controller.set_setting("editor", "font", self.editor_font_combo.currentText())
        self.settings_controller.set_setting("editor", "font_size", self.editor_font_size_spin.value())
        self.settings_controller.set_setting("editor", "syntax_highlighting", self.editor_syntax_highlighting_cb.isChecked())
        
        # Auto-import settings
        self.settings_controller.set_setting("auto_import", "enabled", self.auto_import_enabled_cb.isChecked())
        self.settings_controller.set_setting("auto_import", "watch_directory", self.watch_dir_edit.text())
        self.settings_controller.set_setting("auto_import", "processed_directory", self.processed_dir_edit.text())
        self.settings_controller.set_setting("auto_import", "move_after_import", self.move_after_import_cb.isChecked())
        self.settings_controller.set_setting("auto_import", "auto_process", self.auto_process_cb.isChecked())
        self.settings_controller.set_setting("auto_import", "check_interval", self.check_interval_spin.value())
        self.settings_controller.set_setting("auto_import", "processing_delay", self.processing_delay_spin.value())
        
        # Logging settings
        self.settings_controller.set_setting("logging", "log_directory", self.log_dir_edit.text())
        self.settings_controller.set_setting("logging", "log_filename", self.log_filename_edit.text())
        self.settings_controller.set_setting("logging", "auto_clear_logs", self.auto_clear_logs_cb.isChecked())
        self.settings_controller.set_setting("logging", "clear_logs_interval", self.clear_logs_interval_spin.value())
        self.settings_controller.set_setting("logging", "max_log_size_mb", self.max_log_size_spin.value())
        self.settings_controller.set_setting("logging", "keep_log_backups", self.keep_log_backups_spin.value())
        self.settings_controller.set_setting("logging", "open_log_in_editor", self.open_log_in_editor_cb.isChecked())
        
        # Tutorial settings
        if hasattr(self, 'enable_tutorials_cb'):
            self.settings_controller.set_setting("tutorials", "enabled", self.enable_tutorials_cb.isChecked())
            self.settings_controller.set_setting("tutorials", "auto_start", self.auto_start_cb.isChecked())
            self.settings_controller.set_setting("tutorials", "show_first_run", self.first_run_cb.isChecked())
            self.settings_controller.set_setting("tutorials", "show_on_tab_switch", self.show_on_tab_switch_cb.isChecked())
            self.settings_controller.set_setting("tutorials", "animation_speed", self.animation_speed_combo.currentText())
        
        # Save settings
        save_success = self.settings_controller.save_settings()
        
        if save_success:
            # Reload settings to ensure UI reflects current state
            self.settings_controller.load_settings()
            
            # Refresh UI to show current settings
            self.loadSettings()
            
            # Update auto-import status
            self.update_auto_import_status()
            
            QMessageBox.information(self, "Settings Saved", "Settings have been saved successfully.")
        else:
            QMessageBox.warning(self, "Save Error", "An error occurred while saving settings.")
            
    def test_tts_voice(self):
        """Test the selected TTS voice with the entered text"""
        try:
            import pyttsx3
            
            # Get the test text
            test_text = self.test_text_edit.text()
            if not test_text:
                test_text = "This is a test of text-to-speech."
                
            # Initialize the TTS engine
            engine = pyttsx3.init()
            
            # Set voice if not using system default
            selected_voice = self.tts_voice_combo.currentText()
            if selected_voice != "System Default":
                voices = engine.getProperty('voices')
                for voice in voices:
                    if selected_voice in voice.name:
                        engine.setProperty('voice', voice.id)
                        break
            
            # Set rate and volume
            engine.setProperty('rate', self.tts_rate.value())
            engine.setProperty('volume', float(self.tts_volume.value()) / 100.0)
            
            # Speak the text
            engine.say(test_text)
            engine.runAndWait()
            
        except Exception as e:
            QMessageBox.warning(self, "TTS Error", f"An error occurred while testing TTS: {str(e)}")
            self.logger.error("SettingsDialog", f"TTS test error: {str(e)}")
    
    def restore_defaults(self):
        """Restore all settings to default values"""
        # Confirm with the user before restoring defaults
        confirm = QMessageBox.question(
            self,
            "Restore Default Settings",
            "Are you sure you want to restore all settings to their default values?\n\n"
            "This will overwrite all your current settings.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            # Reset settings controller to defaults
            success = self.settings_controller.reset_to_defaults()
            
            if success:
                # Apply default settings to the UI
                self.loadSettings()
                
                # Show confirmation message
                QMessageBox.information(
                    self, 
                    "Default Settings Restored", 
                    "All settings have been restored to their default values."
                )
            else:
                QMessageBox.warning(
                    self,
                    "Error Restoring Defaults",
                    "An error occurred while restoring default settings."
                )
            
    def launch_editor(self):
        """Launch the PDF editor"""
        self.logger.info("SettingsDialog", "Launching PDF editor")
        
        try:
            # Save current settings before launching editor
            self.apply_settings()
            
            # Determine which files to open in the editor
            files_to_open = []
            
            # Check if we should auto-open selected files
            if self.editor_auto_open_cb.isChecked() and hasattr(self.parent, 'get_selected_files'):
                # Get selected files from parent (main application)
                selected_files = self.parent.get_selected_files()
                if selected_files:
                    files_to_open.extend(selected_files)
                    self.logger.info("SettingsDialog", f"Auto-opening {len(selected_files)} selected files in editor")
            
            # Launch the editor - this would typically call a method in the main application
            # or create a new editor instance directly
            if hasattr(self.parent, 'launch_editor'):
                # If the parent has a launch_editor method, use it
                self.parent.launch_editor(files_to_open)
            else:
                # Placeholder for direct editor launch
                self.logger.info("SettingsDialog", "Editor launch method not implemented in parent")
                QMessageBox.information(
                    self, 
                    "Editor Launch", 
                    f"Editor would launch now with {len(files_to_open)} files.\n\n"
                    "This feature is currently under development."
                )
                
                # TODO: Implement direct editor launch here
                # from pdf_editor import PDFEditor
                # editor = PDFEditor(files_to_open)
                # editor.exec()
                
        except Exception as e:
            self.logger.error("SettingsDialog", f"Error launching editor: {str(e)}")
            QMessageBox.warning(self, "Error", f"Could not launch editor:\n\n{str(e)}")
    
    def open_directory(self, path):
        """Open a directory in the file explorer"""
        if not path:
            QMessageBox.warning(self, "Directory Not Set", "Please select a directory first.")
            return
            
        # Check if directory exists, create if it doesn't
        if not os.path.exists(path):
            try:
                os.makedirs(path)
                self.logger.info("SettingsDialog", f"Created directory: {path}")
            except Exception as e:
                self.logger.error("SettingsDialog", f"Error creating directory {path}: {str(e)}")
                QMessageBox.warning(self, "Error", f"Could not create directory: {path}\n\nError: {str(e)}")
                return
        
        # Open the directory in the file explorer
        try:
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.Popen(["open", path])
            else:  # Linux and other Unix-like
                subprocess.Popen(["xdg-open", path])
                
            self.logger.info("SettingsDialog", f"Opened directory: {path}")
        except Exception as e:
            self.logger.error("SettingsDialog", f"Error opening directory {path}: {str(e)}")
            QMessageBox.warning(self, "Error", f"Could not open directory: {path}\n\nError: {str(e)}")
    
    def on_tutorial_enable_changed(self, enabled):
        """Handle tutorial enable/disable state change"""
        # Enable/disable dependent controls
        self.auto_start_cb.setEnabled(enabled)
        self.first_run_cb.setEnabled(enabled)
        self.show_on_tab_switch_cb.setEnabled(enabled)
        self.animation_speed_combo.setEnabled(enabled)
        self.tutorial_combo.setEnabled(enabled)
        self.reset_specific_btn.setEnabled(enabled)
        self.reset_all_btn.setEnabled(enabled)
        self.refresh_tutorial_status_btn.setEnabled(enabled)
    
    def reset_specific_tutorial(self):
        """Reset a specific tutorial"""
        tutorial_name = self.tutorial_combo.currentText()
        
        reply = QMessageBox.question(
            self, 
            "Reset Tutorial",
            f"Are you sure you want to reset the '{tutorial_name}' tutorial?\n\n"
            f"This will mark it as not completed, and it will show again next time.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Reset the specific tutorial
            completed_tutorials = self.settings_controller.get_setting("tutorials", default={}).get("completed", {})
            if tutorial_name in completed_tutorials:
                completed_tutorials[tutorial_name] = False
                self.settings_controller.set_setting("tutorials", "completed", completed_tutorials)
                self.settings_controller.save_settings()
                
                # Update status display
                self.update_tutorial_status()
                
                QMessageBox.information(
                    self, 
                    "Tutorial Reset", 
                    f"The '{tutorial_name}' tutorial has been reset successfully."
                )
    
    def reset_all_tutorials(self):
        """Reset all tutorials"""
        reply = QMessageBox.question(
            self,
            "Reset All Tutorials",
            "Are you sure you want to reset ALL tutorials?\n\n"
            "This will mark all tutorials as not completed, and they will all show again.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Reset all tutorials
            self.settings_controller.reset_tutorial_completion()
            self.settings_controller.save_settings()
            
            # Update status display
            self.update_tutorial_status()
            
            QMessageBox.information(
                self,
                "Tutorials Reset",
                "All tutorials have been reset successfully."
            )
    
    def update_tutorial_status(self):
        """Update the tutorial status display"""
        try:
            # Get tutorial statistics
            stats = self.settings_controller.get_tutorial_statistics()
            
            # Create status text
            status_lines = []
            status_lines.append(f"Total tutorials: {stats['total_tutorials']}")
            status_lines.append(f"Completed: {stats['completed_tutorials']}")
            status_lines.append(f"Remaining: {stats['remaining_tutorials']}")
            
            if stats['completed_tutorials'] > 0:
                completion_percentage = (stats['completed_tutorials'] / stats['total_tutorials']) * 100
                status_lines.append(f"Completion: {completion_percentage:.1f}%")
            
            # Add individual tutorial status
            if stats['tutorial_status']:
                status_lines.append("\nIndividual tutorial status:")
                for tutorial_name, completed in stats['tutorial_status'].items():
                    status_icon = "✓" if completed else "○"
                    display_name = tutorial_name.replace("_", " ").title()
                    status_lines.append(f"  {status_icon} {display_name}")
            
            status_text = "\n".join(status_lines)
            self.tutorial_status_label.setText(status_text)
            
        except Exception as e:
            self.tutorial_status_label.setText(f"Error getting tutorial status: {str(e)}")
    
    def on_tab_changed(self, index):
        """Handle tab change event"""
        tab_count = self.tabs.count()
        current_tab = self.tabs.tabText(index)
        
        # Update window title to show current tab
        self.setWindowTitle(f"Settings - {current_tab} ({index + 1}/{tab_count})")
        
        # Update navigation button states
        self.update_navigation_buttons()
        
        # Log tab change for debugging
        self.logger.info("SettingsDialog", f"Switched to tab: {current_tab} (index {index})")
    
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
    
    def update_navigation_buttons(self):
        """Update the state of navigation buttons"""
        current_index = self.tabs.currentIndex()
        tab_count = self.tabs.count()
        
        # Enable/disable previous button
        self.prev_tab_btn.setEnabled(current_index > 0)
        
        # Enable/disable next button
        self.next_tab_btn.setEnabled(current_index < tab_count - 1)
        
        # Update tooltips with current position
        if current_index > 0:
            prev_tab_name = self.tabs.tabText(current_index - 1)
            self.prev_tab_btn.setToolTip(f"Previous: {prev_tab_name}")
        else:
            self.prev_tab_btn.setToolTip("No previous tab")
            
        if current_index < tab_count - 1:
            next_tab_name = self.tabs.tabText(current_index + 1)
            self.next_tab_btn.setToolTip(f"Next: {next_tab_name}")
        else:
            self.next_tab_btn.setToolTip("No next tab")
    
    def accept(self):
        """Handle OK button"""
        self.apply_settings()
        super().accept()
