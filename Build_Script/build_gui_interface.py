#!/usr/bin/env python3
"""
PyQt6-based GUI Interface for PyInstaller Build Tool
This GUI relies on the CLI core (build_cli.py) for all functionality
"""

import sys
import os
import subprocess
import json
import threading
from pathlib import Path

try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QTabWidget, QLabel, QLineEdit, QPushButton, QTextEdit, QComboBox,
        QCheckBox, QFileDialog, QProgressBar, QSplitter, QTreeWidget,
        QTreeWidgetItem, QGroupBox, QFormLayout, QSpinBox, QMessageBox,
        QStatusBar, QMenuBar, QToolBar, QFrame, QScrollArea, QGridLayout,
        QSplashScreen
    )
    from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QProcess
    from PyQt6.QtGui import QIcon, QFont, QTextCursor, QAction, QPixmap
    GUI_AVAILABLE = True
except ImportError:
    print("❌ PyQt6 not installed!")
    print("Install with: pip install PyQt6")
    GUI_AVAILABLE = False
    sys.exit(1)

class CLIInterface:
    """Interface to communicate with the CLI core"""
    
    def __init__(self, cli_path="./build_cli.py"):
        self.cli_path = cli_path
        
    def execute_command(self, command, callback=None):
        """Execute a CLI command and return the result"""
        try:
            if isinstance(command, str):
                cmd = [sys.executable, self.cli_path] + command.split()
            else:
                cmd = [sys.executable, self.cli_path] + command
            
            if callback:
                # Asynchronous execution
                thread = CLIThread(cmd, callback)
                thread.start()
                return thread
            else:
                # Synchronous execution
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True, 
                    cwd=os.path.dirname(self.cli_path)
                )
                return {
                    'returncode': result.returncode,
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
        except Exception as e:
            return {
                'returncode': 1,
                'stdout': '',
                'stderr': str(e)
            }
    
    def get_memory_status(self):
        """Get current memory status from CLI"""
        result = self.execute_command("--show-memory")
        return result
    
    def scan_files(self, scan_type, **kwargs):
        """Scan files using CLI"""
        cmd = ["--scan", scan_type]
        if kwargs.get('append'):
            cmd.append("--append")
        if kwargs.get('contains'):
            cmd.extend(["--contains", kwargs['contains']])
        if kwargs.get('scan_dir'):
            cmd.extend(["--scan-dir", kwargs['scan_dir']])
        
        result = self.execute_command(cmd)
        return result

class CLIThread(QThread):
    """Thread for executing CLI commands asynchronously"""
    finished = pyqtSignal(dict)
    output_ready = pyqtSignal(str)
    
    def __init__(self, command, callback=None):
        super().__init__()
        self.command = command
        self.callback = callback
        
    def run(self):
        try:
            process = subprocess.Popen(
                self.command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Read output line by line
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    self.output_ready.emit(output.strip())
            
            # Get remaining output
            stdout, stderr = process.communicate()
            
            result = {
                'returncode': process.returncode,
                'stdout': stdout,
                'stderr': stderr
            }
            
            self.finished.emit(result)
            
            if self.callback:
                self.callback(result)
                
        except Exception as e:
            result = {
                'returncode': 1,
                'stdout': '',
                'stderr': str(e)
            }
            self.finished.emit(result)

class ProjectConfigTab(QWidget):
    """Tab for project configuration"""
    
    def __init__(self, cli_interface):
        super().__init__()
        self.cli = cli_interface
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Application Settings Group
        app_group = QGroupBox("Application Settings")
        app_layout = QFormLayout()
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter application name...")
        app_layout.addRow("Application Name:", self.name_edit)
        
        self.version_edit = QLineEdit()
        self.version_edit.setPlaceholderText("e.g., 1.0.0")
        app_layout.addRow("Version:", self.version_edit)
        
        # Main file selection
        main_file_layout = QHBoxLayout()
        self.main_file_edit = QLineEdit()
        self.main_file_edit.setPlaceholderText("Select main Python file...")
        self.browse_main_btn = QPushButton("Browse")
        self.auto_detect_btn = QPushButton("Auto-Detect")
        
        main_file_layout.addWidget(self.main_file_edit)
        main_file_layout.addWidget(self.browse_main_btn)
        main_file_layout.addWidget(self.auto_detect_btn)
        
        app_layout.addRow("Main File:", main_file_layout)
        
        # Icon file selection
        icon_layout = QHBoxLayout()
        self.icon_edit = QLineEdit()
        self.icon_edit.setPlaceholderText("Optional: Select icon file...")
        self.browse_icon_btn = QPushButton("Browse")
        self.auto_icon_btn = QPushButton("Auto-Detect")
        
        icon_layout.addWidget(self.icon_edit)
        icon_layout.addWidget(self.browse_icon_btn)
        icon_layout.addWidget(self.auto_icon_btn)
        
        app_layout.addRow("Icon File:", icon_layout)
        
        app_group.setLayout(app_layout)
        layout.addWidget(app_group)
        
        # Build Options Group
        build_group = QGroupBox("Build Options")
        build_layout = QFormLayout()
        
        self.onefile_cb = QCheckBox("Create single executable file")
        self.onefile_cb.setChecked(True)
        build_layout.addRow("Package Mode:", self.onefile_cb)
        
        self.windowed_cb = QCheckBox("Windowed mode (no console)")
        build_layout.addRow("Interface:", self.windowed_cb)
        
        self.include_date_cb = QCheckBox("Include date in filename")
        self.include_date_cb.setChecked(True)
        build_layout.addRow("Date Stamp:", self.include_date_cb)
        
        self.clean_build_cb = QCheckBox("Clean build (remove old files)")
        self.clean_build_cb.setChecked(True)
        build_layout.addRow("Clean Build:", self.clean_build_cb)
        
        self.debug_cb = QCheckBox("Debug mode (verbose output)")
        build_layout.addRow("Debug:", self.debug_cb)
        
        # Version Control
        self.no_version_cb = QCheckBox("Don't append version to filename")
        build_layout.addRow("Version Control:", self.no_version_cb)
        
        build_group.setLayout(build_layout)
        layout.addWidget(build_group)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.load_config_btn = QPushButton("Load Configuration")
        self.save_config_btn = QPushButton("Save Configuration")
        self.reset_config_btn = QPushButton("Reset to Defaults")
        
        button_layout.addWidget(self.load_config_btn)
        button_layout.addWidget(self.save_config_btn)
        button_layout.addWidget(self.reset_config_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
        self.setLayout(layout)
        
        # Connect signals
        self.connect_signals()
        
    def connect_signals(self):
        """Connect all signals to their handlers"""
        self.browse_main_btn.clicked.connect(self.browse_main_file)
        self.auto_detect_btn.clicked.connect(self.auto_detect_main)
        self.browse_icon_btn.clicked.connect(self.browse_icon_file)
        self.auto_icon_btn.clicked.connect(self.auto_detect_icon)
        
        self.load_config_btn.clicked.connect(self.load_configuration)
        self.save_config_btn.clicked.connect(self.save_configuration)
        self.reset_config_btn.clicked.connect(self.reset_configuration)
        
    def browse_main_file(self):
        """Browse for main Python file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Main Python File",
            "",
            "Python Files (*.py *.pyw);;All Files (*)"
        )
        if file_path:
            self.main_file_edit.setText(file_path)
            
    def auto_detect_main(self):
        """Auto-detect main Python file using CLI"""
        def callback(result):
            if result['returncode'] == 0:
                # Parse the output to find the detected main file
                lines = result['stdout'].split('\n')
                for line in lines:
                    if "Auto-detected main file:" in line:
                        main_file = line.split(":")[-1].strip()
                        self.main_file_edit.setText(main_file)
                        break
        
        self.cli.execute_command("--main auto", callback)
        
    def browse_icon_file(self):
        """Browse for icon file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Icon File",
            "",
            "Icon Files (*.ico *.png *.jpg *.jpeg *.svg);;All Files (*)"
        )
        if file_path:
            self.icon_edit.setText(file_path)
            
    def auto_detect_icon(self):
        """Auto-detect icon file"""
        # Look for common icon files
        icon_extensions = ['.ico', '.png', '.jpg', '.jpeg', '.svg']
        icon_names = ['icon', 'logo', 'app']
        
        for ext in icon_extensions:
            for name in icon_names:
                icon_path = f"{name}{ext}"
                if os.path.exists(icon_path):
                    self.icon_edit.setText(icon_path)
                    return
        
        QMessageBox.information(self, "Auto-Detect Icon", "No icon file found automatically.")
        
    def get_configuration(self):
        """Get current configuration from GUI"""
        config = {
            'name': self.name_edit.text().strip(),
            'version': self.version_edit.text().strip(),
            'main_file': self.main_file_edit.text().strip(),
            'icon': self.icon_edit.text().strip(),
            'onefile': self.onefile_cb.isChecked(),
            'windowed': self.windowed_cb.isChecked(),
            'include_date': self.include_date_cb.isChecked(),
            'clean': self.clean_build_cb.isChecked(),
            'debug': self.debug_cb.isChecked(),
            'no_version_append': self.no_version_cb.isChecked()
        }
        return config
        
    def set_configuration(self, config):
        """Set GUI from configuration"""
        self.name_edit.setText(config.get('name', ''))
        self.version_edit.setText(config.get('version', ''))
        self.main_file_edit.setText(config.get('main_file', ''))
        self.icon_edit.setText(config.get('icon', ''))
        
        self.onefile_cb.setChecked(config.get('onefile', True))
        self.windowed_cb.setChecked(config.get('windowed', False))
        self.include_date_cb.setChecked(config.get('include_date', True))
        self.clean_build_cb.setChecked(config.get('clean', True))
        self.debug_cb.setChecked(config.get('debug', False))
        self.no_version_cb.setChecked(config.get('no_version_append', False))
        
    def load_configuration(self):
        """Load configuration from CLI memory"""
        def callback(result):
            try:
                # Parse CLI output to get configuration
                if result['returncode'] == 0:
                    QMessageBox.information(self, "Load Configuration", "Configuration loaded from CLI memory!")
                else:
                    QMessageBox.warning(self, "Load Configuration", "Failed to load configuration from CLI.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error loading configuration: {str(e)}")
        
        self.cli.execute_command("--show-memory", callback)
        
    def save_configuration(self):
        """Save current configuration to CLI"""
        config = self.get_configuration()
        
        # Send configuration to CLI using individual commands
        commands = []
        
        if config['name']:
            commands.append(f"--name {config['name']}")
        if config['version']:
            commands.append(f"--set-version {config['version']}")
        if config['main_file']:
            commands.append(f"--main {config['main_file']}")
            
        if commands:
            # Execute commands sequentially
            cmd_str = " ".join(commands)
            
            def callback(result):
                if result['returncode'] == 0:
                    QMessageBox.information(self, "Save Configuration", "Configuration saved successfully!")
                else:
                    QMessageBox.warning(self, "Save Configuration", f"Failed to save configuration:\n{result['stderr']}")
            
            self.cli.execute_command(cmd_str, callback)
        else:
            QMessageBox.information(self, "Save Configuration", "No configuration to save.")
            
    def reset_configuration(self):
        """Reset configuration to defaults"""
        reply = QMessageBox.question(
            self,
            "Reset Configuration",
            "Are you sure you want to reset all settings to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            default_config = {
                'name': '',
                'version': '',
                'main_file': '',
                'icon': '',
                'onefile': True,
                'windowed': False,
                'include_date': True,
                'clean': True,
                'debug': False,
                'no_version_append': False
            }
            self.set_configuration(default_config)

class FileScanTab(QWidget):
    """Tab for file scanning operations"""
    
    def __init__(self, cli_interface):
        super().__init__()
        self.cli = cli_interface
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Scan controls
        controls_group = QGroupBox("Scan Options")
        controls_layout = QFormLayout()
        
        self.scan_type_combo = QComboBox()
        self.scan_type_combo.addItems([
            "python", "icons", "images", "config", "data", "templates",
            "docs", "help", "splash", "json", "tutorials", "project"
        ])
        controls_layout.addRow("Scan Type:", self.scan_type_combo)
        
        # Scan directory
        scan_dir_layout = QHBoxLayout()
        self.scan_dir_edit = QLineEdit()
        self.scan_dir_edit.setPlaceholderText("Leave empty for current directory")
        self.browse_dir_btn = QPushButton("Browse")
        
        scan_dir_layout.addWidget(self.scan_dir_edit)
        scan_dir_layout.addWidget(self.browse_dir_btn)
        
        controls_layout.addRow("Scan Directory:", scan_dir_layout)
        
        # Filters
        self.contains_edit = QLineEdit()
        self.contains_edit.setPlaceholderText("Filter files containing this text...")
        controls_layout.addRow("Contains Filter:", self.contains_edit)
        
        self.append_cb = QCheckBox("Append to existing results")
        controls_layout.addRow("Mode:", self.append_cb)
        
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)
        
        # Control buttons
        button_layout = QHBoxLayout()
        self.scan_btn = QPushButton("Start Scan")
        self.clear_btn = QPushButton("Clear Results")
        self.export_btn = QPushButton("Export Results")
        
        button_layout.addWidget(self.scan_btn)
        button_layout.addWidget(self.clear_btn)
        button_layout.addWidget(self.export_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # Results area
        self.results_tree = QTreeWidget()
        self.results_tree.setHeaderLabels(["File Path", "Size", "Modified"])
        layout.addWidget(self.results_tree)
        
        # Status
        self.status_label = QLabel("Ready to scan")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        
        # Connect signals
        self.connect_signals()
        
    def connect_signals(self):
        """Connect signals to handlers"""
        self.browse_dir_btn.clicked.connect(self.browse_directory)
        self.scan_btn.clicked.connect(self.start_scan)
        self.clear_btn.clicked.connect(self.clear_results)
        self.export_btn.clicked.connect(self.export_results)
        
    def browse_directory(self):
        """Browse for scan directory"""
        directory = QFileDialog.getExistingDirectory(self, "Select Directory to Scan")
        if directory:
            self.scan_dir_edit.setText(directory)
            
    def start_scan(self):
        """Start file scanning"""
        scan_type = self.scan_type_combo.currentText()
        scan_dir = self.scan_dir_edit.text().strip()
        contains = self.contains_edit.text().strip()
        append = self.append_cb.isChecked()
        
        self.status_label.setText("Scanning files...")
        self.scan_btn.setEnabled(False)
        
        kwargs = {}
        if scan_dir:
            kwargs['scan_dir'] = scan_dir
        if contains:
            kwargs['contains'] = contains
        if append:
            kwargs['append'] = True
            
        def callback(result):
            self.scan_btn.setEnabled(True)
            if result['returncode'] == 0:
                self.status_label.setText("Scan completed successfully")
                self.parse_scan_results(result['stdout'])
            else:
                self.status_label.setText("Scan failed")
                QMessageBox.warning(self, "Scan Error", f"Scan failed:\n{result['stderr']}")
        
        self.cli.scan_files(scan_type, **kwargs)
        
    def parse_scan_results(self, output):
        """Parse scan results from CLI output"""
        # Clear existing results
        if not self.append_cb.isChecked():
            self.results_tree.clear()
        
        # Parse output for file paths
        lines = output.split('\n')
        for line in lines:
            if line.strip().startswith('📄'):
                file_path = line.strip()[2:].strip()  # Remove emoji
                if os.path.exists(file_path):
                    stat = os.stat(file_path)
                    item = QTreeWidgetItem([
                        file_path,
                        f"{stat.st_size:,} bytes",
                        str(Path(file_path).stat().st_mtime)
                    ])
                    self.results_tree.addTopLevelItem(item)
        
        # Update status
        count = self.results_tree.topLevelItemCount()
        self.status_label.setText(f"Found {count} files")
        
    def clear_results(self):
        """Clear scan results"""
        self.results_tree.clear()
        self.status_label.setText("Results cleared")
        
    def export_results(self):
        """Export scan results"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Scan Results",
            "scan_results.txt",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    f.write("File Scan Results\n")
                    f.write("=" * 50 + "\n")
                    
                    for i in range(self.results_tree.topLevelItemCount()):
                        item = self.results_tree.topLevelItem(i)
                        f.write(f"{item.text(0)}\n")
                        f.write(f"  Size: {item.text(1)}\n")
                        f.write(f"  Modified: {item.text(2)}\n\n")
                
                QMessageBox.information(self, "Export Complete", f"Results exported to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export results:\n{str(e)}")

class BuildTab(QWidget):
    """Tab for build operations"""
    
    def __init__(self, cli_interface):
        super().__init__()
        self.cli = cli_interface
        self.current_process = None
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Build controls
        controls_group = QGroupBox("Build Options")
        controls_layout = QHBoxLayout()
        
        self.quick_build_btn = QPushButton("Quick Build")
        self.quick_build_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        
        self.full_build_btn = QPushButton("Full Build")
        self.full_build_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        
        self.preview_btn = QPushButton("Preview Command")
        self.stop_btn = QPushButton("Stop Build")
        self.stop_btn.setEnabled(False)
        
        controls_layout.addWidget(self.quick_build_btn)
        controls_layout.addWidget(self.full_build_btn)
        controls_layout.addWidget(self.preview_btn)
        controls_layout.addWidget(self.stop_btn)
        controls_layout.addStretch()
        
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Build output
        self.output_text = QTextEdit()
        self.output_text.setFont(QFont("Consolas", 9))
        self.output_text.setReadOnly(True)
        layout.addWidget(self.output_text)
        
        # Status bar
        self.status_label = QLabel("Ready to build")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        
        # Connect signals
        self.connect_signals()
        
    def connect_signals(self):
        """Connect signals to handlers"""
        self.quick_build_btn.clicked.connect(self.quick_build)
        self.full_build_btn.clicked.connect(self.full_build)
        self.preview_btn.clicked.connect(self.preview_command)
        self.stop_btn.clicked.connect(self.stop_build)
        
    def quick_build(self):
        """Start quick build"""
        self.start_build("quick")
        
    def full_build(self):
        """Start full build"""
        self.start_build("build")
        
    def start_build(self, build_type):
        """Start build process"""
        self.output_text.clear()
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.status_label.setText(f"Starting {build_type} build...")
        
        self.quick_build_btn.setEnabled(False)
        self.full_build_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        
        def callback(result):
            self.progress_bar.setVisible(False)
            self.quick_build_btn.setEnabled(True)
            self.full_build_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            
            if result['returncode'] == 0:
                self.status_label.setText("Build completed successfully!")
                self.output_text.append("\n🎉 BUILD SUCCESSFUL! 🎉")
                QMessageBox.information(self, "Build Complete", "Build completed successfully!\nCheck the 'dist' folder for your executable.")
            else:
                self.status_label.setText("Build failed")
                self.output_text.append(f"\n❌ BUILD FAILED\nError: {result['stderr']}")
                QMessageBox.warning(self, "Build Failed", f"Build failed:\n{result['stderr']}")
        
        # Execute build command
        self.current_process = self.cli.execute_command(f"--start {build_type}", callback)
        
        # Connect to output signal for real-time updates
        if hasattr(self.current_process, 'output_ready'):
            self.current_process.output_ready.connect(self.append_output)
            
    def append_output(self, text):
        """Append text to output area"""
        self.output_text.append(text)
        # Auto-scroll to bottom
        cursor = self.output_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.output_text.setTextCursor(cursor)
        
    def preview_command(self):
        """Preview the build command that would be executed"""
        def callback(result):
            if result['returncode'] == 0:
                # Extract command from output
                lines = result['stdout'].split('\n')
                command_lines = []
                capture = False
                
                for line in lines:
                    if "Build Command Preview:" in line:
                        capture = True
                        continue
                    elif capture and line.strip():
                        if line.startswith('pyinstaller'):
                            command_lines.append(line)
                        elif line.strip().startswith('--'):
                            command_lines.append(line)
                        elif "Build Summary:" in line:
                            break
                
                command_text = '\n'.join(command_lines) if command_lines else "No command available"
                
                QMessageBox.information(
                    self, 
                    "Build Command Preview", 
                    f"Command that would be executed:\n\n{command_text}"
                )
            else:
                QMessageBox.warning(self, "Preview Error", "Could not generate command preview")
        
        # Get current config and preview
        self.cli.execute_command("--start build --preview", callback)
        
    def stop_build(self):
        """Stop current build process"""
        if self.current_process and hasattr(self.current_process, 'terminate'):
            self.current_process.terminate()
            self.status_label.setText("Build stopped by user")
            self.progress_bar.setVisible(False)
            self.quick_build_btn.setEnabled(True)
            self.full_build_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            
        self.main_window = QMainWindow()
        self.main_window.setWindowTitle("PyInstaller Build Tool - GUI Interface")
        self.main_window.setMinimumSize(800, 600)
        
        # Central widget
        central_widget = QWidget()
        self.main_window.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        
        # Welcome message
        welcome_label = QLabel("🚀 PyInstaller Build Tool - GUI Interface")
        welcome_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 20px;")
        layout.addWidget(welcome_label)
        
        # Info label
        info_label = QLabel("""
        This is the GUI interface module that was downloaded on-demand.
        
        Features:
        • Modular architecture with separate CLI and GUI components
        • Fast CLI launcher with minimal dependencies  
        • On-demand GUI module downloading
        • GitHub integration for repository management
        • Environment-based configuration system
        
        The full GUI interface is under development.
        Use the CLI interface for current functionality.
        """)
        info_label.setWordWrap(True)
        info_label.setStyleSheet("margin: 20px; line-height: 1.4;")
        layout.addWidget(info_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cli_button = QPushButton("Launch CLI Help")
        cli_button.clicked.connect(self.show_cli_help)
        button_layout.addWidget(cli_button)
        
        repo_button = QPushButton("Check Repository Status")
        repo_button.clicked.connect(self.check_repo_status)
        button_layout.addWidget(repo_button)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.main_window.close)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
        return True
    
    def show_cli_help(self):
        """Show CLI help information"""
        try:
            from Build_Script.build_gui_core import BuildToolCore
            core = BuildToolCore()
            
            msg = QMessageBox(self.main_window)
            msg.setWindowTitle("CLI Commands")
            msg.setText("CLI Interface Commands:")
            msg.setDetailedText("""
Available CLI Commands:

--help, -h            Show help message
--gui                 Launch GUI interface
--version             Show version information  
--repo-status         Check GitHub repository status
--download-gui        Download/update GUI module
--changelog           Show recent changes
--update              Check for updates

Examples:
build_cli --repo-status    Check repository status
build_cli --version        Show version info
build_cli --gui            Launch this GUI interface

For the fastest performance, use the CLI commands directly.
            """)
            msg.exec()
            
        except Exception as e:
            QMessageBox.warning(self.main_window, "Error", f"Could not load CLI help: {e}")
    
    def check_repo_status(self):
        """Check repository status and display in GUI"""
        try:
            from Build_Script.build_gui_core import BuildToolCore
            core = BuildToolCore()
            
            # Show progress dialog
            progress = QMessageBox(self.main_window)
            progress.setWindowTitle("Checking Repository...")
            progress.setText("Fetching repository status from GitHub...")
            progress.setStandardButtons(QMessageBox.StandardButton.NoButton)
            progress.show()
            
            # Process events to show the dialog
            QApplication.processEvents()
            
            status = core.check_repository_status()
            progress.close()
            
            if "error" in status:
                QMessageBox.critical(self.main_window, "Error", f"Failed to check repository: {status['error']}")
                return
            
            # Format status information
            status_text = f"""
Repository: {status.get('name', 'Unknown')}
Description: {status.get('description', 'No description')}
⭐ Stars: {status.get('stars', 0)} | 🍴 Forks: {status.get('forks', 0)}
Language: {status.get('language', 'Unknown')}
Size: {status.get('size', 0)} KB
Last Updated: {status.get('updated_at', 'Unknown')}
            """
            
            if 'recent_commits' in status and status['recent_commits']:
                status_text += "\n\n📝 Recent Commits:\n"
                for commit in status['recent_commits'][:3]:
                    status_text += f"• {commit['sha']} - {commit['message']}\n"
            
            if 'latest_release' in status:
                release = status['latest_release']
                if release.get('tag_name', 'None') != 'None':
                    status_text += f"\n\n🚀 Latest Release: {release['tag_name']}\n"
                    status_text += f"Published: {release.get('published_at', 'Unknown')}"
            
            msg = QMessageBox(self.main_window)
            msg.setWindowTitle("Repository Status")
            msg.setText("📊 GitHub Repository Status")
            msg.setDetailedText(status_text)
            msg.exec()
            
        except Exception as e:
            QMessageBox.critical(self.main_window, "Error", f"Failed to check repository status: {e}")

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.cli = CLIInterface()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("PyInstaller Build Tool - GUI")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Create central widget with tabs
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Add tabs
        self.project_tab = ProjectConfigTab(self.cli)
        self.scan_tab = FileScanTab(self.cli)
        self.build_tab = BuildTab(self.cli)
        
        self.tab_widget.addTab(self.project_tab, "🏗️ Project Config")
        self.tab_widget.addTab(self.scan_tab, "🔍 File Scanner")
        self.tab_widget.addTab(self.build_tab, "🚀 Build")
        
        layout.addWidget(self.tab_widget)
        
        # Set style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QTabWidget::pane {
                border: 1px solid #c0c0c0;
                background-color: white;
            }
            QTabBar::tab {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                            stop: 0 #f0f0f0, stop: 1 #d0d0d0);
                border: 1px solid #c0c0c0;
                padding: 8px 12px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom-color: white;
            }
            QPushButton {
                padding: 6px 12px;
                border: 1px solid #c0c0c0;
                border-radius: 4px;
                background-color: #f8f8f8;
            }
            QPushButton:hover {
                background-color: #e8e8e8;
            }
            QPushButton:pressed {
                background-color: #d8d8d8;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #c0c0c0;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
    def create_menu_bar(self):
        """Create application menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        new_action = QAction('New Project', self)
        new_action.setShortcut('Ctrl+N')
        new_action.triggered.connect(self.new_project)
        file_menu.addAction(new_action)
        
        open_action = QAction('Open Configuration', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_configuration)
        file_menu.addAction(open_action)
        
        save_action = QAction('Save Configuration', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_configuration)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu('Tools')
        
        console_action = QAction('Open CLI Console', self)
        console_action.triggered.connect(self.open_console)
        tools_menu.addAction(console_action)
        
        memory_action = QAction('Show Memory Status', self)
        memory_action.triggered.connect(self.show_memory_status)
        tools_menu.addAction(memory_action)
        
        clear_memory_action = QAction('Clear Memory', self)
        clear_memory_action.triggered.connect(self.clear_memory)
        tools_menu.addAction(clear_memory_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def new_project(self):
        """Create new project"""
        reply = QMessageBox.question(
            self,
            "New Project",
            "Clear all current settings and start fresh?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.project_tab.reset_configuration()
            self.scan_tab.clear_results()
            self.build_tab.output_text.clear()
            self.status_bar.showMessage("New project created")
            
    def open_configuration(self):
        """Open configuration file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Configuration",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    config = json.load(f)
                self.project_tab.set_configuration(config)
                self.status_bar.showMessage(f"Configuration loaded from {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load configuration:\n{str(e)}")
                
    def save_configuration(self):
        """Save configuration file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Configuration",
            "build_config.json",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                config = self.project_tab.get_configuration()
                with open(file_path, 'w') as f:
                    json.dump(config, f, indent=2)
                self.status_bar.showMessage(f"Configuration saved to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save configuration:\n{str(e)}")
                
    def open_console(self):
        """Open CLI console in terminal"""
        try:
            if sys.platform.startswith('win'):
                subprocess.Popen(['cmd', '/k', 'python', 'build_cli.py', '--console'])
            else:
                subprocess.Popen(['x-terminal-emulator', '-e', 'python3', 'build_cli.py', '--console'])
        except Exception as e:
            QMessageBox.warning(self, "Console Error", f"Failed to open console:\n{str(e)}")
            
    def show_memory_status(self):
        """Show CLI memory status"""
        def callback(result):
            QMessageBox.information(
                self,
                "Memory Status",
                f"CLI Memory Status:\n\n{result['stdout']}"
            )
        
        self.cli.execute_command("--show-memory", callback)
        
    def clear_memory(self):
        """Clear CLI memory"""
        reply = QMessageBox.question(
            self,
            "Clear Memory",
            "Clear all stored data in CLI memory?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            def callback(result):
                if result['returncode'] == 0:
                    QMessageBox.information(self, "Clear Memory", "Memory cleared successfully!")
                else:
                    QMessageBox.warning(self, "Clear Memory", "Failed to clear memory")
            
            self.cli.execute_command("--clear-memory", callback)
            
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About PyInstaller Build Tool",
            """
            <h3>PyInstaller Build Tool - GUI Interface</h3>
            <p>A modern GUI interface for PyInstaller with advanced features.</p>
            <p><b>Version:</b> 2.0.0</p>
            <p><b>Author:</b> Build Tool Team</p>
            <p><b>License:</b> MIT</p>
            
            <p>This GUI interfaces with the CLI core for all operations.</p>
            <p>The CLI remains independent and can be used separately.</p>
            """
        )

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("PyInstaller Build Tool")
    app.setApplicationVersion("2.0.0")
    
    # Check if CLI is available
    cli_path = "./build_cli.py"
    if not os.path.exists(cli_path):
        cli_path = "build_cli.py"
        if not os.path.exists(cli_path):
            QMessageBox.critical(
                None,
                "CLI Not Found",
                "Could not find build_cli.py!\n\nMake sure the CLI core is in the same directory as the GUI."
            )
            sys.exit(1)
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

def launch_gui():
    """Launch the GUI interface"""
    if not GUI_AVAILABLE:
        print("❌ PyQt6 not available - cannot launch GUI")
        return False
        
    try:
        print("🚀 Starting PyInstaller Build Tool GUI...")
        main()
        return True
    except Exception as e:
        print(f"❌ Failed to launch GUI: {e}")
        return False

if __name__ == "__main__":
    success = launch_gui()
    sys.exit(0 if success else 1)
