#!/usr/bin/env python3
"""
PyInstaller Build Tool GUI
A modern PyQt interface for the PyInstaller build script with drag-and-drop support
"""

import os
import sys
import subprocess
import glob
import json
import re
import argparse
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QGroupBox, QFormLayout, QLineEdit, QPushButton, 
    QCheckBox, QComboBox, QTextEdit, QLabel, QFileDialog, QListWidget,
    QProgressBar, QSplitter, QFrame, QScrollArea, QMessageBox,
    QSlider, QSpinBox, QListWidgetItem, QDialog, QDialogButtonBox,
    QTreeWidget, QTreeWidgetItem, QSizePolicy, QGridLayout
)
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QMimeData, QSize, QSettings
)
from PyQt6.QtGui import (
    QIcon, QPixmap, QDragEnterEvent, QDropEvent, QPalette, QFont, QAction
)

# Import the original console builder
from build_script import PyInstallerBuilder as ConsoleBuilder

class DropZoneWidget(QWidget):
    """Custom drop zone widget for drag and drop functionality"""
    
    files_dropped = pyqtSignal(list)
    
    def __init__(self, text="Drop files here", accepted_extensions=None):
        super().__init__()
        self.accepted_extensions = accepted_extensions or []
        self.setup_ui(text)
        self.setAcceptDrops(True)
        
    def setup_ui(self, text):
        layout = QVBoxLayout(self)
        
        self.label = QLabel(text)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("""
            QLabel {
                border: 2px dashed #3498db;
                border-radius: 10px;
                padding: 20px;
                color: #7f8c8d;
                font-size: 14px;
                background-color: #f8f9fa;
            }
        """)
        
        layout.addWidget(self.label)
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.label.setStyleSheet("""
                QLabel {
                    border: 2px dashed #2ecc71;
                    border-radius: 10px;
                    padding: 20px;
                    color: #27ae60;
                    font-size: 14px;
                    background-color: #e8f8f5;
                }
            """)
        else:
            event.ignore()
            
    def dragLeaveEvent(self, event):
        self.label.setStyleSheet("""
            QLabel {
                border: 2px dashed #3498db;
                border-radius: 10px;
                padding: 20px;
                color: #7f8c8d;
                font-size: 14px;
                background-color: #f8f9fa;
            }
        """)
        
    def dropEvent(self, event: QDropEvent):
        files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if os.path.isfile(file_path):
                if not self.accepted_extensions or any(file_path.lower().endswith(ext) for ext in self.accepted_extensions):
                    files.append(file_path)
                    
        if files:
            self.files_dropped.emit(files)
            
        self.dragLeaveEvent(event)
        event.acceptProposedAction()

class ModernToggleSwitch(QWidget):
    """Modern toggle switch widget (Apple-style slider)"""
    
    toggled = pyqtSignal(bool)
    
    def __init__(self, text="", checked=False):
        super().__init__()
        self.checked = checked
        self.setup_ui(text)
        
    def setup_ui(self, text):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        if text:
            self.label = QLabel(text)
            layout.addWidget(self.label)
            
        self.switch = QCheckBox()
        self.switch.setChecked(self.checked)
        self.switch.toggled.connect(self.on_toggled)
        
        # Style the checkbox to look like a toggle switch
        self.switch.setStyleSheet("""
            QCheckBox::indicator {
                width: 50px;
                height: 24px;
                border-radius: 12px;
                background-color: #bdc3c7;
                border: 2px solid #95a5a6;
            }
            
            QCheckBox::indicator:checked {
                background-color: #3498db;
                border: 2px solid #2980b9;
            }
            
            QCheckBox::indicator::handle {
                width: 20px;
                height: 20px;
                border-radius: 10px;
                background-color: white;
                border: 1px solid #bdc3c7;
            }
        """)
        
        layout.addWidget(self.switch)
        layout.addStretch()
        
    def on_toggled(self, checked):
        self.checked = checked
        self.toggled.emit(checked)
        
    def setChecked(self, checked):
        self.switch.setChecked(checked)
        self.checked = checked
        
    def isChecked(self):
        return self.checked

class FileSearchWidget(QWidget):
    """Widget for searching and selecting files with auto-detection"""
    
    file_selected = pyqtSignal(str)
    
    def __init__(self, title="Select File", file_filter="All Files (*)", search_patterns=None):
        super().__init__()
        self.title = title
        self.file_filter = file_filter
        self.search_patterns = search_patterns or []
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        
        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText("File path or drop file here")
        layout.addWidget(self.line_edit)
        
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.clicked.connect(self.browse_file)
        layout.addWidget(self.browse_btn)
        
        self.auto_detect_btn = QPushButton("Auto-detect")
        self.auto_detect_btn.clicked.connect(self.auto_detect)
        layout.addWidget(self.auto_detect_btn)
        
        # Make the line edit accept drops
        self.line_edit.setAcceptDrops(True)
        self.line_edit.dragEnterEvent = self.dragEnterEvent
        self.line_edit.dropEvent = self.dropEvent
        
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            
    def dropEvent(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if os.path.isfile(file_path):
                self.line_edit.setText(file_path)
                self.file_selected.emit(file_path)
                break
        event.acceptProposedAction()
        
    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, self.title, "", self.file_filter)
        if file_path:
            self.line_edit.setText(file_path)
            self.file_selected.emit(file_path)
            
    def auto_detect(self):
        """Auto-detect file based on search patterns"""
        for pattern in self.search_patterns:
            files = glob.glob(pattern)
            if files:
                # Select the first match
                file_path = files[0]
                self.line_edit.setText(file_path)
                self.file_selected.emit(file_path)
                QMessageBox.information(self, "Auto-detect", f"Found: {file_path}")
                return
                
        QMessageBox.information(self, "Auto-detect", "No matching files found.")
        
    def get_file_path(self):
        return self.line_edit.text().strip()
        
    def set_file_path(self, path):
        self.line_edit.setText(path)

class BuildThread(QThread):
    """Thread for running the build process"""
    
    progress_update = pyqtSignal(str)
    build_complete = pyqtSignal(bool, str)
    
    def __init__(self, command):
        super().__init__()
        self.command = command
        
    def run(self):
        try:
            self.progress_update.emit("Starting build process...")
            
            # Execute the PyInstaller command
            process = subprocess.Popen(
                self.command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                universal_newlines=True
            )
            
            # Read output line by line
            for line in iter(process.stdout.readline, ''):
                if line:
                    self.progress_update.emit(line.strip())
                    
            process.wait()
            
            if process.returncode == 0:
                self.build_complete.emit(True, "Build completed successfully!")
            else:
                self.build_complete.emit(False, f"Build failed with return code {process.returncode}")
                
        except Exception as e:
            self.build_complete.emit(False, f"Build error: {str(e)}")

class PyInstallerGUI(QMainWindow):
    """Main GUI window for PyInstaller Build Tool"""
    
    def __init__(self):
        super().__init__()
        self.console_builder = ConsoleBuilder()
        self.settings = QSettings("PyInstallerGUI", "BuildTool")
        self.build_thread = None
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        self.setWindowTitle("PyInstaller Build Tool GUI")
        self.setMinimumSize(1000, 700)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Header
        header = self.create_header()
        main_layout.addWidget(header)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_basic_tab()
        self.create_advanced_tab()
        self.create_files_tab()
        self.create_changelog_tab()
        self.create_build_tab()
        
        # Footer with action buttons
        footer = self.create_footer()
        main_layout.addWidget(footer)
        
        # Status bar
        self.statusBar().showMessage("Ready to build")
        
    def create_header(self):
        """Create the header section"""
        header = QFrame()
        header.setFrameStyle(QFrame.Shape.StyledPanel)
        header.setStyleSheet("""
            QFrame {
                background-color: #3498db;
                color: white;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout(header)
        
        title = QLabel("PyInstaller Build Tool")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: white;")
        layout.addWidget(title)
        
        subtitle = QLabel("Modern GUI for creating executable files from Python scripts")
        subtitle.setStyleSheet("color: #ecf0f1; font-size: 12px;")
        layout.addWidget(subtitle)
        
        return header
        
    def create_basic_tab(self):
        """Create the basic configuration tab"""
        widget = QScrollArea()
        content = QWidget()
        layout = QVBoxLayout(content)
        
        # Program Information
        program_group = QGroupBox("Program Information")
        program_layout = QFormLayout(program_group)
        
        self.program_name_edit = QLineEdit()
        self.program_name_edit.setPlaceholderText("Enter program name")
        program_layout.addRow("Program Name:", self.program_name_edit)
        
        self.version_edit = QLineEdit()
        self.version_edit.setPlaceholderText("e.g., 1.0.0")
        program_layout.addRow("Version:", self.version_edit)
        
        self.build_status_combo = QComboBox()
        self.build_status_combo.addItems(["Stable", "Beta", "Alpha", "Development", "Release Candidate"])
        program_layout.addRow("Build Status:", self.build_status_combo)
        
        layout.addWidget(program_group)
        
        # Main Entry Point
        entry_group = QGroupBox("Main Entry Point")
        entry_layout = QVBoxLayout(entry_group)
        
        self.main_entry_widget = FileSearchWidget(
            "Select Main Python File",
            "Python Files (*.py)",
            ["*.py", "main.py", "app.py", "__main__.py"]
        )
        entry_layout.addWidget(self.main_entry_widget)
        
        layout.addWidget(entry_group)
        
        # Build Options
        options_group = QGroupBox("Build Options")
        options_layout = QGridLayout(options_group)
        
        # Row 0
        self.onefile_switch = ModernToggleSwitch("One File", True)
        options_layout.addWidget(self.onefile_switch, 0, 0)
        
        self.windowed_switch = ModernToggleSwitch("Windowed (No Console)", True)
        options_layout.addWidget(self.windowed_switch, 0, 1)
        
        # Row 1
        self.clean_switch = ModernToggleSwitch("Clean Build", True)
        options_layout.addWidget(self.clean_switch, 1, 0)
        
        self.debug_switch = ModernToggleSwitch("Debug Mode", False)
        options_layout.addWidget(self.debug_switch, 1, 1)
        
        # Row 2
        self.uac_switch = ModernToggleSwitch("UAC Admin", False)
        options_layout.addWidget(self.uac_switch, 2, 0)
        
        self.console_switch = ModernToggleSwitch("Show Console", False)
        options_layout.addWidget(self.console_switch, 2, 1)
        
        layout.addWidget(options_group)
        
        # Icon and Splash
        visual_group = QGroupBox("Visual Assets")
        visual_layout = QFormLayout(visual_group)
        
        self.icon_widget = FileSearchWidget(
            "Select Icon File",
            "Icon Files (*.ico *.png *.jpg)",
            ["*.ico", "icon.ico", "icon.png", "assets/*.ico", "images/*.ico"]
        )
        visual_layout.addRow("Icon File:", self.icon_widget)
        
        self.splash_widget = FileSearchWidget(
            "Select Splash Screen",
            "Image Files (*.png *.jpg *.bmp)",
            ["*.png", "splash.png", "splash.jpg", "assets/*.png", "images/*.png"]
        )
        visual_layout.addRow("Splash Screen:", self.splash_widget)
        
        layout.addWidget(visual_group)
        
        widget.setWidget(content)
        self.tab_widget.addTab(widget, "Basic")
        
    def create_advanced_tab(self):
        """Create the advanced configuration tab"""
        widget = QScrollArea()
        content = QWidget()
        layout = QVBoxLayout(content)
        
        # PyInstaller Options
        pyinstaller_group = QGroupBox("PyInstaller Advanced Options")
        pyinstaller_layout = QFormLayout(pyinstaller_group)
        
        self.distpath_edit = QLineEdit()
        self.distpath_edit.setPlaceholderText("dist")
        pyinstaller_layout.addRow("Output Directory:", self.distpath_edit)
        
        self.workpath_edit = QLineEdit()
        self.workpath_edit.setPlaceholderText("build")
        pyinstaller_layout.addRow("Work Directory:", self.workpath_edit)
        
        self.specpath_edit = QLineEdit()
        self.specpath_edit.setPlaceholderText(".")
        pyinstaller_layout.addRow("Spec File Directory:", self.specpath_edit)
        
        layout.addWidget(pyinstaller_group)
        
        # Optimization Options
        optimization_group = QGroupBox("Optimization")
        optimization_layout = QGridLayout(optimization_group)
        
        self.optimize_switch = ModernToggleSwitch("Optimize Bytecode", True)
        optimization_layout.addWidget(self.optimize_switch, 0, 0)
        
        self.strip_switch = ModernToggleSwitch("Strip Debug Symbols", False)
        optimization_layout.addWidget(self.strip_switch, 0, 1)
        
        self.upx_switch = ModernToggleSwitch("UPX Compression", False)
        optimization_layout.addWidget(self.upx_switch, 1, 0)
        
        self.bootloader_ignore_switch = ModernToggleSwitch("Ignore Bootloader Signals", False)
        optimization_layout.addWidget(self.bootloader_ignore_switch, 1, 1)
        
        layout.addWidget(optimization_group)
        
        # Hidden Imports and Paths
        imports_group = QGroupBox("Hidden Imports and Paths")
        imports_layout = QVBoxLayout(imports_group)
        
        # Hidden imports
        hidden_imports_label = QLabel("Hidden Imports (one per line):")
        imports_layout.addWidget(hidden_imports_label)
        
        self.hidden_imports_edit = QTextEdit()
        self.hidden_imports_edit.setMaximumHeight(100)
        self.hidden_imports_edit.setPlaceholderText("Enter module names that should be included\\ne.g.:\\npyqt6\\nrequests\\nnumpy")
        imports_layout.addWidget(self.hidden_imports_edit)
        
        # Additional paths
        paths_label = QLabel("Additional Paths (one per line):")
        imports_layout.addWidget(paths_label)
        
        self.add_paths_edit = QTextEdit()
        self.add_paths_edit.setMaximumHeight(100)
        self.add_paths_edit.setPlaceholderText("Enter additional search paths\\ne.g.:\\n./lib\\n./modules\\n/usr/local/lib/python3.x/site-packages")
        imports_layout.addWidget(self.add_paths_edit)
        
        layout.addWidget(imports_group)
        
        widget.setWidget(content)
        self.tab_widget.addTab(widget, "Advanced")
        
    def create_files_tab(self):
        """Create the files and resources tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Additional Files Section
        files_group = QGroupBox("Additional Files and Resources")
        files_layout = QVBoxLayout(files_group)
        
        # Drop zone for additional files
        self.files_drop_zone = DropZoneWidget("Drop additional files here\\n(data files, configs, resources, etc.)")
        self.files_drop_zone.files_dropped.connect(self.add_additional_files)
        files_layout.addWidget(self.files_drop_zone)
        
        # List widget for additional files
        self.additional_files_list = QListWidget()
        self.additional_files_list.setMaximumHeight(150)
        files_layout.addWidget(self.additional_files_list)
        
        # Buttons for file management
        files_buttons_layout = QHBoxLayout()
        
        add_files_btn = QPushButton("Add Files")
        add_files_btn.clicked.connect(self.browse_additional_files)
        files_buttons_layout.addWidget(add_files_btn)
        
        add_folder_btn = QPushButton("Add Folder")
        add_folder_btn.clicked.connect(self.browse_additional_folder)
        files_buttons_layout.addWidget(add_folder_btn)
        
        remove_files_btn = QPushButton("Remove Selected")
        remove_files_btn.clicked.connect(self.remove_selected_files)
        files_buttons_layout.addWidget(remove_files_btn)
        
        clear_files_btn = QPushButton("Clear All")
        clear_files_btn.clicked.connect(self.clear_additional_files)
        files_buttons_layout.addWidget(clear_files_btn)
        
        files_buttons_layout.addStretch()
        files_layout.addLayout(files_buttons_layout)
        
        layout.addWidget(files_group)
        
        # Auto-detection section
        auto_detect_group = QGroupBox("Auto-Detection")
        auto_detect_layout = QVBoxLayout(auto_detect_group)
        
        auto_detect_buttons_layout = QGridLayout()
        
        detect_help_btn = QPushButton("Detect HELP Files")
        detect_help_btn.clicked.connect(self.auto_detect_help_files)
        auto_detect_buttons_layout.addWidget(detect_help_btn, 0, 0)
        
        detect_tutorial_btn = QPushButton("Detect Tutorial Files")
        detect_tutorial_btn.clicked.connect(self.auto_detect_tutorial_files)
        auto_detect_buttons_layout.addWidget(detect_tutorial_btn, 0, 1)
        
        detect_config_btn = QPushButton("Detect Config Files")
        detect_config_btn.clicked.connect(self.auto_detect_config_files)
        auto_detect_buttons_layout.addWidget(detect_config_btn, 1, 0)
        
        detect_assets_btn = QPushButton("Detect Assets")
        detect_assets_btn.clicked.connect(self.auto_detect_assets)
        auto_detect_buttons_layout.addWidget(detect_assets_btn, 1, 1)
        
        auto_detect_layout.addLayout(auto_detect_buttons_layout)
        layout.addWidget(auto_detect_group)
        
        self.tab_widget.addTab(widget, "Files & Resources")
        
    def create_changelog_tab(self):
        """Create the changelog management tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Changelog Selection
        changelog_selection_group = QGroupBox("Changelog Selection")
        changelog_selection_layout = QVBoxLayout(changelog_selection_group)
        
        self.changelog_widget = FileSearchWidget(
            "Select Changelog File",
            "Markdown/Text Files (*.md *.txt *.rst)",
            ["changelog.md", "CHANGELOG.md", "changelog.txt", "CHANGELOG.txt"]
        )
        changelog_selection_layout.addWidget(self.changelog_widget)
        
        # Auto-detect button
        detect_changelog_btn = QPushButton("Auto-detect Changelog")
        detect_changelog_btn.clicked.connect(self.auto_detect_changelog)
        changelog_selection_layout.addWidget(detect_changelog_btn)
        
        layout.addWidget(changelog_selection_group)
        
        # Changelog Content
        changelog_content_group = QGroupBox("Changelog Content")
        changelog_content_layout = QVBoxLayout(changelog_content_group)
        
        # Version info
        version_layout = QHBoxLayout()
        version_layout.addWidget(QLabel("Version:"))
        self.changelog_version_edit = QLineEdit()
        self.changelog_version_edit.setPlaceholderText("Auto-detected from Basic tab")
        version_layout.addWidget(self.changelog_version_edit)
        changelog_content_layout.addLayout(version_layout)
        
        # Tabs for different types of changelog entries
        self.changelog_tabs = QTabWidget()
        
        # New Features
        features_widget = QWidget()
        features_layout = QVBoxLayout(features_widget)
        self.new_features_edit = QTextEdit()
        self.new_features_edit.setPlaceholderText("Enter new features (one per line)...")
        features_layout.addWidget(self.new_features_edit)
        self.changelog_tabs.addTab(features_widget, "New Features")
        
        # Improvements
        improvements_widget = QWidget()
        improvements_layout = QVBoxLayout(improvements_widget)
        self.improvements_edit = QTextEdit()
        self.improvements_edit.setPlaceholderText("Enter improvements (one per line)...")
        improvements_layout.addWidget(self.improvements_edit)
        self.changelog_tabs.addTab(improvements_widget, "Improvements")
        
        # Bug Fixes
        bugfixes_widget = QWidget()
        bugfixes_layout = QVBoxLayout(bugfixes_widget)
        self.resolved_issues_edit = QTextEdit()
        self.resolved_issues_edit.setPlaceholderText("Enter resolved issues (one per line)...")
        bugfixes_layout.addWidget(self.resolved_issues_edit)
        self.changelog_tabs.addTab(bugfixes_widget, "Bug Fixes")
        
        # Known Issues
        known_issues_widget = QWidget()
        known_issues_layout = QVBoxLayout(known_issues_widget)
        self.known_issues_edit = QTextEdit()
        self.known_issues_edit.setPlaceholderText("Enter known issues (one per line)...")
        known_issues_layout.addWidget(self.known_issues_edit)
        self.changelog_tabs.addTab(known_issues_widget, "Known Issues")
        
        # Build Notes
        build_notes_widget = QWidget()
        build_notes_layout = QVBoxLayout(build_notes_widget)
        self.build_notes_edit = QTextEdit()
        self.build_notes_edit.setPlaceholderText("Enter build notes...")
        build_notes_layout.addWidget(self.build_notes_edit)
        self.changelog_tabs.addTab(build_notes_widget, "Build Notes")
        
        changelog_content_layout.addWidget(self.changelog_tabs)
        
        # Changelog actions
        changelog_actions_layout = QHBoxLayout()
        
        generate_changelog_btn = QPushButton("Generate Changelog")
        generate_changelog_btn.clicked.connect(self.generate_changelog)
        changelog_actions_layout.addWidget(generate_changelog_btn)
        
        preview_changelog_btn = QPushButton("Preview Changelog")
        preview_changelog_btn.clicked.connect(self.preview_changelog)
        changelog_actions_layout.addWidget(preview_changelog_btn)
        
        save_changelog_btn = QPushButton("Save Changelog")
        save_changelog_btn.clicked.connect(self.save_changelog)
        changelog_actions_layout.addWidget(save_changelog_btn)
        
        changelog_actions_layout.addStretch()
        changelog_content_layout.addLayout(changelog_actions_layout)
        
        layout.addWidget(changelog_content_group)
        
        self.tab_widget.addTab(widget, "Changelog")
        
    def create_build_tab(self):
        """Create the build execution tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Build Preview
        preview_group = QGroupBox("Build Command Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        self.build_command_edit = QTextEdit()
        self.build_command_edit.setReadOnly(True)
        self.build_command_edit.setMaximumHeight(150)
        self.build_command_edit.setStyleSheet("background-color: #2c3e50; color: #ecf0f1; font-family: monospace;")
        preview_layout.addWidget(self.build_command_edit)
        
        update_preview_btn = QPushButton("Update Preview")
        update_preview_btn.clicked.connect(self.update_build_preview)
        preview_layout.addWidget(update_preview_btn)
        
        layout.addWidget(preview_group)
        
        # Build Output
        output_group = QGroupBox("Build Output")
        output_layout = QVBoxLayout(output_group)
        
        self.build_output_edit = QTextEdit()
        self.build_output_edit.setReadOnly(True)
        self.build_output_edit.setStyleSheet("background-color: #2c3e50; color: #ecf0f1; font-family: monospace;")
        output_layout.addWidget(self.build_output_edit)
        
        # Progress bar
        self.build_progress = QProgressBar()
        self.build_progress.setVisible(False)
        output_layout.addWidget(self.build_progress)
        
        layout.addWidget(output_group)
        
        self.tab_widget.addTab(widget, "Build")
        
    def create_footer(self):
        """Create the footer with action buttons"""
        footer = QFrame()
        footer.setFrameStyle(QFrame.Shape.StyledPanel)
        
        layout = QHBoxLayout(footer)
        
        # Left side buttons
        load_config_btn = QPushButton("Load Config")
        load_config_btn.clicked.connect(self.load_config)
        layout.addWidget(load_config_btn)
        
        save_config_btn = QPushButton("Save Config")
        save_config_btn.clicked.connect(self.save_config)
        layout.addWidget(save_config_btn)
        
        layout.addStretch()
        
        # Right side buttons
        quick_build_btn = QPushButton("Quick Build")
        quick_build_btn.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold; padding: 8px;")
        quick_build_btn.clicked.connect(self.quick_build)
        layout.addWidget(quick_build_btn)
        
        self.build_btn = QPushButton("Build")
        self.build_btn.setStyleSheet("background-color: #3498db; color: white; font-weight: bold; padding: 8px;")
        self.build_btn.clicked.connect(self.start_build)
        layout.addWidget(self.build_btn)
        
        return footer
        
    # Event handlers and utility methods
    def add_additional_files(self, files):
        """Add files to the additional files list"""
        for file_path in files:
            item = QListWidgetItem(file_path)
            self.additional_files_list.addItem(item)
            
    def browse_additional_files(self):
        """Browse for additional files"""
        files, _ = QFileDialog.getOpenFileNames(self, "Select Additional Files", "", "All Files (*)")
        self.add_additional_files(files)
        
    def browse_additional_folder(self):
        """Browse for additional folder"""
        folder = QFileDialog.getExistingDirectory(self, "Select Additional Folder")
        if folder:
            item = QListWidgetItem(folder)
            self.additional_files_list.addItem(item)
            
    def remove_selected_files(self):
        """Remove selected files from the list"""
        for item in self.additional_files_list.selectedItems():
            self.additional_files_list.takeItem(self.additional_files_list.row(item))
            
    def clear_additional_files(self):
        """Clear all additional files"""
        self.additional_files_list.clear()
        
    def auto_detect_help_files(self):
        """Auto-detect help files"""
        help_files = self.console_builder.find_help_files()
        self.add_additional_files(help_files)
        if help_files:
            QMessageBox.information(self, "Auto-detect", f"Found {len(help_files)} help files")
        else:
            QMessageBox.information(self, "Auto-detect", "No help files found")
            
    def auto_detect_tutorial_files(self):
        """Auto-detect tutorial files"""
        tutorial_files = self.console_builder.find_tutorial_files()
        self.add_additional_files(tutorial_files)
        if tutorial_files:
            QMessageBox.information(self, "Auto-detect", f"Found {len(tutorial_files)} tutorial files")
        else:
            QMessageBox.information(self, "Auto-detect", "No tutorial files found")
            
    def auto_detect_config_files(self):
        """Auto-detect config files"""
        config_patterns = ["*.json", "*.ini", "*.cfg", "*.conf", "*.yaml", "*.yml", "settings.*"]
        config_files = []
        for pattern in config_patterns:
            config_files.extend(glob.glob(pattern))
        
        self.add_additional_files(config_files)
        if config_files:
            QMessageBox.information(self, "Auto-detect", f"Found {len(config_files)} config files")
        else:
            QMessageBox.information(self, "Auto-detect", "No config files found")
            
    def auto_detect_assets(self):
        """Auto-detect asset files"""
        asset_patterns = ["assets/*", "images/*", "icons/*", "resources/*", "data/*"]
        asset_files = []
        for pattern in asset_patterns:
            for file_path in glob.glob(pattern):
                if os.path.isfile(file_path):
                    asset_files.append(file_path)
        
        self.add_additional_files(asset_files)
        if asset_files:
            QMessageBox.information(self, "Auto-detect", f"Found {len(asset_files)} asset files")
        else:
            QMessageBox.information(self, "Auto-detect", "No asset files found")
            
    def auto_detect_changelog(self):
        """Auto-detect changelog file"""
        changelog_files = self.console_builder.find_changelog_files()
        if changelog_files:
            self.changelog_widget.set_file_path(changelog_files[0])
            QMessageBox.information(self, "Auto-detect", f"Found changelog: {changelog_files[0]}")
        else:
            QMessageBox.information(self, "Auto-detect", "No changelog files found")
            
    def generate_changelog(self):
        """Generate changelog content"""
        # This would integrate with the console builder's changelog functionality
        QMessageBox.information(self, "Generate Changelog", "Changelog generation feature coming soon!")
        
    def preview_changelog(self):
        """Preview the changelog"""
        # Show a preview dialog
        QMessageBox.information(self, "Preview Changelog", "Changelog preview feature coming soon!")
        
    def save_changelog(self):
        """Save the changelog"""
        # Save the changelog to file
        QMessageBox.information(self, "Save Changelog", "Changelog save feature coming soon!")
        
    def update_build_preview(self):
        """Update the build command preview"""
        command = self.build_pyinstaller_command()
        self.build_command_edit.setPlainText(" ".join(command))
        
    def build_pyinstaller_command(self):
        """Build the PyInstaller command based on current settings"""
        command = ["pyinstaller"]
        
        # Basic options
        if self.onefile_switch.isChecked():
            command.append("--onefile")
        if self.windowed_switch.isChecked():
            command.append("--windowed")
        if self.clean_switch.isChecked():
            command.append("--clean")
        if self.debug_switch.isChecked():
            command.append("--debug=all")
        if self.uac_switch.isChecked():
            command.append("--uac-admin")
        if self.console_switch.isChecked():
            command.append("--console")
            
        # Icon
        icon_path = self.icon_widget.get_file_path()
        if icon_path:
            command.extend(["--icon", icon_path])
            
        # Splash
        splash_path = self.splash_widget.get_file_path()
        if splash_path:
            command.extend(["--splash", splash_path])
            
        # Advanced options
        if self.distpath_edit.text().strip():
            command.extend(["--distpath", self.distpath_edit.text().strip()])
        if self.workpath_edit.text().strip():
            command.extend(["--workpath", self.workpath_edit.text().strip()])
        if self.specpath_edit.text().strip():
            command.extend(["--specpath", self.specpath_edit.text().strip()])
            
        # Hidden imports
        hidden_imports = self.hidden_imports_edit.toPlainText().strip().split('\\n')
        for imp in hidden_imports:
            if imp.strip():
                command.extend(["--hidden-import", imp.strip()])
                
        # Additional paths
        add_paths = self.add_paths_edit.toPlainText().strip().split('\\n')
        for path in add_paths:
            if path.strip():
                command.extend(["--add-data", f"{path.strip()};."])
                
        # Additional files
        for i in range(self.additional_files_list.count()):
            file_path = self.additional_files_list.item(i).text()
            if os.path.isfile(file_path):
                command.extend(["--add-data", f"{file_path};."])
            elif os.path.isdir(file_path):
                command.extend(["--add-data", f"{file_path};{os.path.basename(file_path)}"])
                
        # Main entry point
        main_entry = self.main_entry_widget.get_file_path()
        if main_entry:
            command.append(main_entry)
            
        return command
        
    def quick_build(self):
        """Perform a quick build with auto-detection"""
        # Auto-detect main entry if not set
        if not self.main_entry_widget.get_file_path():
            self.main_entry_widget.auto_detect()
            
        # Auto-detect icon if not set
        if not self.icon_widget.get_file_path():
            self.icon_widget.auto_detect()
            
        # Start build
        self.start_build()
        
    def start_build(self):
        """Start the build process"""
        if not self.main_entry_widget.get_file_path():
            QMessageBox.warning(self, "Build Error", "Please select a main entry point (Python file)")
            return
            
        # Update preview first
        self.update_build_preview()
        
        # Get the command
        command = self.build_pyinstaller_command()
        
        # Switch to build tab
        self.tab_widget.setCurrentIndex(4)  # Build tab
        
        # Clear output
        self.build_output_edit.clear()
        
        # Show progress bar
        self.build_progress.setVisible(True)
        self.build_progress.setRange(0, 0)  # Indeterminate
        
        # Disable build button
        self.build_btn.setEnabled(False)
        self.build_btn.setText("Building...")
        
        # Start build thread
        self.build_thread = BuildThread(command)
        self.build_thread.progress_update.connect(self.on_build_progress)
        self.build_thread.build_complete.connect(self.on_build_complete)
        self.build_thread.start()
        
    def on_build_progress(self, message):
        """Handle build progress updates"""
        self.build_output_edit.append(message)
        # Auto-scroll to bottom
        scrollbar = self.build_output_edit.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def on_build_complete(self, success, message):
        """Handle build completion"""
        # Hide progress bar
        self.build_progress.setVisible(False)
        
        # Re-enable build button
        self.build_btn.setEnabled(True)
        self.build_btn.setText("Build")
        
        # Show completion message
        self.build_output_edit.append(f"\\n{'='*50}")
        self.build_output_edit.append(message)
        self.build_output_edit.append(f"{'='*50}")
        
        # Status bar
        if success:
            self.statusBar().showMessage("Build completed successfully!")
            QMessageBox.information(self, "Build Complete", "Build completed successfully!")
        else:
            self.statusBar().showMessage("Build failed!")
            QMessageBox.critical(self, "Build Failed", f"Build failed:\\n{message}")
            
    def save_settings(self):
        """Save current settings"""
        self.settings.setValue("program_name", self.program_name_edit.text())
        self.settings.setValue("version", self.version_edit.text())
        self.settings.setValue("build_status", self.build_status_combo.currentText())
        self.settings.setValue("main_entry", self.main_entry_widget.get_file_path())
        self.settings.setValue("icon_path", self.icon_widget.get_file_path())
        self.settings.setValue("splash_path", self.splash_widget.get_file_path())
        
        # Build options
        self.settings.setValue("onefile", self.onefile_switch.isChecked())
        self.settings.setValue("windowed", self.windowed_switch.isChecked())
        self.settings.setValue("clean", self.clean_switch.isChecked())
        self.settings.setValue("debug", self.debug_switch.isChecked())
        self.settings.setValue("uac", self.uac_switch.isChecked())
        self.settings.setValue("console", self.console_switch.isChecked())
        
        # Advanced options
        self.settings.setValue("distpath", self.distpath_edit.text())
        self.settings.setValue("workpath", self.workpath_edit.text())
        self.settings.setValue("specpath", self.specpath_edit.text())
        self.settings.setValue("hidden_imports", self.hidden_imports_edit.toPlainText())
        self.settings.setValue("add_paths", self.add_paths_edit.toPlainText())
        
        # Additional files
        files_list = []
        for i in range(self.additional_files_list.count()):
            files_list.append(self.additional_files_list.item(i).text())
        self.settings.setValue("additional_files", files_list)
        
    def load_settings(self):
        """Load saved settings"""
        self.program_name_edit.setText(self.settings.value("program_name", ""))
        self.version_edit.setText(self.settings.value("version", ""))
        
        build_status = self.settings.value("build_status", "Stable")
        index = self.build_status_combo.findText(build_status)
        if index >= 0:
            self.build_status_combo.setCurrentIndex(index)
            
        self.main_entry_widget.set_file_path(self.settings.value("main_entry", ""))
        self.icon_widget.set_file_path(self.settings.value("icon_path", ""))
        self.splash_widget.set_file_path(self.settings.value("splash_path", ""))
        
        # Build options
        self.onefile_switch.setChecked(self.settings.value("onefile", True, type=bool))
        self.windowed_switch.setChecked(self.settings.value("windowed", True, type=bool))
        self.clean_switch.setChecked(self.settings.value("clean", True, type=bool))
        self.debug_switch.setChecked(self.settings.value("debug", False, type=bool))
        self.uac_switch.setChecked(self.settings.value("uac", False, type=bool))
        self.console_switch.setChecked(self.settings.value("console", False, type=bool))
        
        # Advanced options
        self.distpath_edit.setText(self.settings.value("distpath", ""))
        self.workpath_edit.setText(self.settings.value("workpath", ""))
        self.specpath_edit.setText(self.settings.value("specpath", ""))
        self.hidden_imports_edit.setPlainText(self.settings.value("hidden_imports", ""))
        self.add_paths_edit.setPlainText(self.settings.value("add_paths", ""))
        
        # Additional files
        files_list = self.settings.value("additional_files", [])
        if files_list:
            for file_path in files_list:
                item = QListWidgetItem(file_path)
                self.additional_files_list.addItem(item)
                
    def save_config(self):
        """Save configuration to file"""
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Configuration", "", "JSON Files (*.json)")
        if file_path:
            config = self.get_current_config()
            try:
                with open(file_path, 'w') as f:
                    json.dump(config, f, indent=4)
                QMessageBox.information(self, "Save Config", "Configuration saved successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Failed to save configuration:\\n{str(e)}")
                
    def load_config(self):
        """Load configuration from file"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Load Configuration", "", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    config = json.load(f)
                self.set_config(config)
                QMessageBox.information(self, "Load Config", "Configuration loaded successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Load Error", f"Failed to load configuration:\\n{str(e)}")
                
    def get_current_config(self):
        """Get current configuration as dictionary"""
        # This would collect all current settings into a dictionary
        # Implementation details would mirror the save_settings method
        pass
        
    def set_config(self, config):
        """Set configuration from dictionary"""
        # This would apply configuration from a dictionary
        # Implementation details would mirror the load_settings method
        pass
        
    def closeEvent(self, event):
        """Handle window close event"""
        self.save_settings()
        super().closeEvent(event)

def main():
    """Main entry point"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="PyInstaller Build Tool")
    parser.add_argument("--console", action="store_true", help="Run in console mode")
    parser.add_argument("--gui", action="store_true", help="Run in GUI mode (default)")
    args = parser.parse_args()
    
    # Determine mode
    if args.console:
        # Run console version
        console_builder = ConsoleBuilder()
        console_builder.run()
    else:
        # Run GUI version (default)
        app = QApplication(sys.argv)
        
        # Set application properties
        app.setApplicationName("PyInstaller Build Tool GUI")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("PyInstaller GUI")
        
        # Create and show main window
        window = PyInstallerGUI()
        window.show()
        
        sys.exit(app.exec())

if __name__ == "__main__":
    main()
