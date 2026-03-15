#!/usr/bin/env python3
"""
PyQt6 GUI Interface for PyInstaller Build Tool
A separate GUI application that works with the existing CLI tool
"""

import sys
import os
import json
import subprocess
import threading
import time
import tempfile
from pathlib import Path
from datetime import datetime

# PyQt6 imports
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QFormLayout, QLineEdit, QPushButton, QCheckBox,
    QComboBox, QTextEdit, QLabel, QFileDialog, QProgressBar,
    QSplitter, QFrame, QMessageBox, QTabWidget, QScrollArea,
    QGridLayout, QSizePolicy, QDialog, QDialogButtonBox
)
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QSize
)
from PyQt6.QtGui import (
    QIcon, QPixmap, QFont, QAction
)

class CLIProgressMonitor(QThread):
    """Monitor CLI progress from JSON file"""
    progress_updated = pyqtSignal(dict)
    finished = pyqtSignal()

    def __init__(self, progress_file):
        super().__init__()
        self.progress_file = progress_file
        self.running = True
        self.last_progress = {}

    def run(self):
        """Monitor progress file for updates"""
        while self.running:
            try:
                if os.path.exists(self.progress_file):
                    with open(self.progress_file, 'r') as f:
                        progress = json.load(f)

                    # Only emit if progress changed
                    if progress != self.last_progress:
                        self.last_progress = progress.copy()
                        self.progress_updated.emit(progress)

                time.sleep(0.5)  # Check every 500ms

            except (json.JSONDecodeError, FileNotFoundError, KeyError):
                # File might be being written, continue
                time.sleep(0.5)
            except Exception as e:
                print(f"Progress monitoring error: {e}")
                time.sleep(1)

        self.finished.emit()

    def stop(self):
        """Stop monitoring"""
        self.running = False

class CLIDetector:
    """Detect available CLI executables and modules"""

    def __init__(self):
        self.cli_options = []

    def detect_cli_options(self):
        """Find all available ways to run the CLI"""
        self.cli_options = []

        # Current directory
        current_dir = Path.cwd()

        # 1. Check for Python module (build_cli.py)
        cli_py = current_dir / "build_cli.py"
        if cli_py.exists():
            self.cli_options.append({
                'name': 'Python Module (build_cli.py)',
                'command': [sys.executable, str(cli_py)],
                'type': 'python',
                'path': str(cli_py)
            })

        # 2. Check for built executables in dist directory
        dist_dir = current_dir / "dist"
        if dist_dir.exists():
            for exe_file in dist_dir.glob("*.exe"):
                if "build_cli" in exe_file.name.lower():
                    self.cli_options.append({
                        'name': f'Executable ({exe_file.name})',
                        'command': [str(exe_file)],
                        'type': 'executable',
                        'path': str(exe_file)
                    })

        # 3. Check for executable in current directory
        for exe_file in current_dir.glob("build_cli*.exe"):
            self.cli_options.append({
                'name': f'Local Executable ({exe_file.name})',
                'command': [str(exe_file)],
                'type': 'executable',
                'path': str(exe_file)
            })

        # 4. Check if build_cli is in PATH
        try:
            result = subprocess.run(['where', 'build_cli.exe'] if os.name == 'nt' else ['which', 'build_cli'],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                path_cmd = result.stdout.strip().split('\n')[0]
                if path_cmd and os.path.exists(path_cmd):
                    self.cli_options.append({
                        'name': 'PATH Executable (build_cli)',
                        'command': [path_cmd],
                        'type': 'executable',
                        'path': path_cmd
                    })
        except:
            pass

        return self.cli_options

class BuildGUIMain(QMainWindow):
    """Main GUI window for the build tool"""

    # Signal for thread-safe output updates
    update_output_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.cli_detector = CLIDetector()
        self.cli_process = None
        self.progress_monitor = None
        self.progress_file = os.path.join(tempfile.gettempdir(), 'build_cli_progress.json')

        self.init_ui()
        self.detect_cli_options()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("PyInstaller Build Tool - GUI Interface")
        self.setMinimumSize(1000, 700)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)

        # Title
        title_label = QLabel("🚀 PyInstaller Build Tool")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; margin: 10px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # Create splitter for main content
        splitter = QSplitter(Qt.Orientation.Vertical)
        main_layout.addWidget(splitter)

        # Top section - CLI selection and build options
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)

        # CLI Selection
        cli_group = QGroupBox("CLI Selection")
        cli_layout = QVBoxLayout(cli_group)

        self.cli_combo = QComboBox()
        self.cli_combo.currentIndexChanged.connect(self.on_cli_selected)
        cli_layout.addWidget(QLabel("Available CLI Options:"))
        cli_layout.addWidget(self.cli_combo)

        self.refresh_cli_btn = QPushButton("🔄 Refresh CLI Options")
        self.refresh_cli_btn.clicked.connect(self.detect_cli_options)
        cli_layout.addWidget(self.refresh_cli_btn)

        top_layout.addWidget(cli_group)

        # Build Options
        options_group = QGroupBox("Build Options")
        options_layout = QGridLayout(options_group)

        # Build type
        options_layout.addWidget(QLabel("Build Type:"), 0, 0)
        self.build_type_combo = QComboBox()
        self.build_type_combo.addItems([
            "Select build type...",
            "Single Executable (--onefile)",
            "Directory Bundle (--onedir)",
            "Windows Executable (--windows)",
            "Console Application (--console)",
            "Custom Options"
        ])
        options_layout.addWidget(self.build_type_combo, 0, 1)

        # Entry point
        options_layout.addWidget(QLabel("Entry Point:"), 1, 0)
        self.entry_point_edit = QLineEdit("main_application.py")
        options_layout.addWidget(self.entry_point_edit, 1, 1)

        self.entry_browse_btn = QPushButton("📁 Browse")
        self.entry_browse_btn.clicked.connect(self.browse_entry_point)
        options_layout.addWidget(self.entry_browse_btn, 1, 2)

        # Output directory
        options_layout.addWidget(QLabel("Output Directory:"), 2, 0)
        self.output_dir_edit = QLineEdit("dist")
        options_layout.addWidget(self.output_dir_edit, 2, 1)

        self.output_browse_btn = QPushButton("📁 Browse")
        self.output_browse_btn.clicked.connect(self.browse_output_dir)
        options_layout.addWidget(self.output_browse_btn, 2, 2)

        # Additional options
        options_layout.addWidget(QLabel("Additional Options:"), 3, 0)
        self.additional_options_edit = QLineEdit("--clean --noconfirm")
        options_layout.addWidget(self.additional_options_edit, 3, 1, 1, 2)

        # Checkboxes
        self.debug_checkbox = QCheckBox("Debug Mode (--debug)")
        self.clean_checkbox = QCheckBox("Clean Build (--clean)")
        self.noconfirm_checkbox = QCheckBox("No Confirm (--noconfirm)")

        options_layout.addWidget(self.debug_checkbox, 4, 0)
        options_layout.addWidget(self.clean_checkbox, 4, 1)
        options_layout.addWidget(self.noconfirm_checkbox, 4, 2)

        top_layout.addWidget(options_group)

        # Control buttons
        controls_layout = QHBoxLayout()

        self.build_btn = QPushButton("🚀 Build")
        self.build_btn.clicked.connect(self.start_build)
        self.build_btn.setStyleSheet("font-size: 14px; padding: 10px;")
        controls_layout.addWidget(self.build_btn)

        self.stop_btn = QPushButton("⏹️ Stop")
        self.stop_btn.clicked.connect(self.stop_build)
        self.stop_btn.setEnabled(False)
        controls_layout.addWidget(self.stop_btn)

        self.clear_btn = QPushButton("🧹 Clear Output")
        self.clear_btn.clicked.connect(self.clear_output)
        controls_layout.addWidget(self.clear_btn)

        top_layout.addLayout(controls_layout)

        splitter.addWidget(top_widget)

        # Bottom section - Progress and output
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)

        # Progress section
        progress_group = QGroupBox("Build Progress")
        progress_layout = QVBoxLayout(progress_group)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)

        # Progress info
        progress_info_layout = QHBoxLayout()

        self.progress_label = QLabel("Ready")
        progress_info_layout.addWidget(self.progress_label)

        progress_info_layout.addStretch()

        self.elapsed_label = QLabel("Elapsed: 00:00:00")
        progress_info_layout.addWidget(self.elapsed_label)

        self.eta_label = QLabel("ETA: --:--:--")
        progress_info_layout.addWidget(self.eta_label)

        progress_layout.addLayout(progress_info_layout)

        bottom_layout.addWidget(progress_group)

        # Output console
        output_group = QGroupBox("Build Output")
        output_layout = QVBoxLayout(output_group)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Consolas", 9))
        output_layout.addWidget(self.output_text)

        bottom_layout.addWidget(output_group)

        splitter.addWidget(bottom_widget)

        # Set splitter proportions
        splitter.setSizes([400, 300])

        # Status bar
        from PyQt6.QtWidgets import QStatusBar
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        # Timer for updating elapsed time
        self.elapsed_timer = QTimer()
        self.elapsed_timer.timeout.connect(self.update_elapsed_time)
        self.start_time = None

    def detect_cli_options(self):
        """Detect available CLI options"""
        self.cli_combo.clear()
        options = self.cli_detector.detect_cli_options()

        if not options:
            self.cli_combo.addItem("❌ No CLI options found")
            self.build_btn.setEnabled(False)
            QMessageBox.warning(self, "No CLI Found",
                              "Could not find build_cli.py or any built executables.\n\n"
                              "Please ensure build_cli.py exists in the current directory\n"
                              "or build the CLI executable first.")
            return

        for option in options:
            self.cli_combo.addItem(f"✅ {option['name']}", option)

        self.cli_combo.setCurrentIndex(0)
        self.build_btn.setEnabled(True)

        self.status_bar.showMessage(f"Found {len(options)} CLI option(s)")

    def on_cli_selected(self):
        """Handle CLI selection change"""
        current_data = self.cli_combo.currentData()
        if current_data:
            cli_info = f"Selected: {current_data['name']}"
            if current_data['type'] == 'python':
                cli_info += " (Python module)"
            else:
                cli_info += " (Executable)"
            self.status_bar.showMessage(cli_info)

    def browse_entry_point(self):
        """Browse for entry point file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Entry Point", "", "Python Files (*.py);;All Files (*)")
        if file_path:
            # Convert to relative path if in current directory
            try:
                rel_path = os.path.relpath(file_path, os.getcwd())
                if not rel_path.startswith('..'):
                    self.entry_point_edit.setText(rel_path)
                else:
                    self.entry_point_edit.setText(file_path)
            except:
                self.entry_point_edit.setText(file_path)

    def browse_output_dir(self):
        """Browse for output directory"""
        dir_path = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if dir_path:
            try:
                rel_path = os.path.relpath(dir_path, os.getcwd())
                if not rel_path.startswith('..'):
                    self.output_dir_edit.setText(rel_path)
                else:
                    self.output_dir_edit.setText(dir_path)
            except:
                self.output_dir_edit.setText(dir_path)

    def start_build(self):
        """Start the build process"""
        cli_option = self.cli_combo.currentData()
        if not cli_option:
            QMessageBox.warning(self, "No CLI Selected", "Please select a CLI option first.")
            return

        # Build command
        command = cli_option['command'].copy()

        # Add build arguments
        entry_point = self.entry_point_edit.text().strip()
        if entry_point:
            command.extend(['--entry', entry_point])

        output_dir = self.output_dir_edit.text().strip()
        if output_dir:
            command.extend(['--output', output_dir])

        # Add build type specific options
        build_type = self.build_type_combo.currentText()
        if build_type == "Single Executable (--onefile)":
            command.append('--onefile')
        elif build_type == "Directory Bundle (--onedir)":
            command.append('--onedir')
        elif build_type == "Windows Executable (--windows)":
            command.append('--windows')
        elif build_type == "Console Application (--console)":
            command.append('--console')

        # Add checkbox options
        if self.debug_checkbox.isChecked():
            command.append('--debug')
        if self.clean_checkbox.isChecked():
            command.append('--clean')
        if self.noconfirm_checkbox.isChecked():
            command.append('--noconfirm')

        # Add additional options
        additional = self.additional_options_edit.text().strip()
        if additional:
            command.extend(additional.split())

        # Start build
        self.start_build_process(command)

    def start_build_process(self, command):
        """Start the CLI build process"""
        try:
            self.output_text.clear()
            self.progress_bar.setValue(0)
            self.progress_label.setText("Starting build...")
            self.start_time = datetime.now()

            self.output_text.append(f"🚀 Starting build with command:")
            self.output_text.append(f"   {' '.join(command)}")
            self.output_text.append("")

            # Start progress monitoring
            self.progress_monitor = CLIProgressMonitor(self.progress_file)
            self.progress_monitor.progress_updated.connect(self.on_progress_update)
            self.progress_monitor.start()

            # Start CLI process
            self.cli_process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                cwd=os.getcwd()
            )

            # Start output reading thread
            threading.Thread(target=self.read_process_output, daemon=True).start()

            # Update UI
            self.build_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.elapsed_timer.start(1000)  # Update every second

            self.status_bar.showMessage("Build in progress...")

        except Exception as e:
            QMessageBox.critical(self, "Build Error", f"Failed to start build: {e}")

    def read_process_output(self):
        """Read process output in a separate thread"""
        try:
            if self.cli_process and self.cli_process.stdout:
                for line in iter(self.cli_process.stdout.readline, ''):
                    if line.strip():
                        # Use signal to update GUI from thread
                        self.update_output_signal.emit(line.strip())
        except:
            pass
        finally:
            if self.cli_process and self.cli_process.stdout:
                self.cli_process.stdout.close()
            self.on_process_finished()

    def on_progress_update(self, progress):
        """Handle progress updates from CLI"""
        try:
            percent = progress.get('progress_percent', 0)
            self.progress_bar.setValue(int(percent))

            current_task = progress.get('current_task', 'Building...')
            self.progress_label.setText(current_task)

            # Update ETA
            eta_seconds = progress.get('estimated_remaining', 0)
            if eta_seconds > 0:
                eta_str = time.strftime('%H:%M:%S', time.gmtime(eta_seconds))
                self.eta_label.setText(f"ETA: {eta_str}")
            else:
                self.eta_label.setText("ETA: --:--:--")

        except Exception as e:
            print(f"Progress update error: {e}")

    def update_elapsed_time(self):
        """Update elapsed time display"""
        if self.start_time:
            elapsed = datetime.now() - self.start_time
            elapsed_str = str(elapsed).split('.')[0]  # Remove microseconds
            self.elapsed_label.setText(f"Elapsed: {elapsed_str}")

    def on_process_finished(self):
        """Handle process completion"""
        self.elapsed_timer.stop()

        if self.progress_monitor:
            self.progress_monitor.stop()
            self.progress_monitor.wait()

        self.build_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

        if self.cli_process:
            return_code = self.cli_process.returncode
            if return_code == 0:
                self.status_bar.showMessage("Build completed successfully")
                self.progress_label.setText("Build completed successfully")
                self.progress_bar.setValue(100)
            else:
                self.status_bar.showMessage(f"Build failed (exit code: {return_code})")
                self.progress_label.setText("Build failed")

    def stop_build(self):
        """Stop the current build process"""
        if self.cli_process and self.cli_process.poll() is None:
            try:
                self.cli_process.terminate()
                self.output_text.append("\n⚠️ Build stopped by user")
                self.status_bar.showMessage("Build stopped")
            except:
                self.cli_process.kill()

        if self.progress_monitor:
            self.progress_monitor.stop()

        self.build_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.elapsed_timer.stop()

    def clear_output(self):
        """Clear the output console"""
        self.output_text.clear()
        self.progress_bar.setValue(0)
        self.progress_label.setText("Ready")
        self.elapsed_label.setText("Elapsed: 00:00:00")
        self.eta_label.setText("ETA: --:--:--")

    # Signal for thread-safe output updates
    update_output_signal = pyqtSignal(str)

    def append_output(self, text):
        """Append text to output (thread-safe)"""
        self.output_text.append(text)
        # Auto-scroll to bottom
        cursor = self.output_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.output_text.setTextCursor(cursor)

def launch_gui():
    """Launch the GUI application"""
    app = QApplication(sys.argv)

    # Set application properties
    app.setApplicationName("PyInstaller Build Tool GUI")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Build Tool")

    # Create and show main window
    window = BuildGUIMain()
    window.update_output_signal.connect(window.append_output)
    window.show()

    return app.exec()

if __name__ == "__main__":
    # Check for help flag
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h', '--version', '-v']:
        print("PyInstaller Build Tool - GUI Interface")
        print("=====================================")
        print()
        print("A PyQt6 graphical interface for the PyInstaller Build Tool CLI.")
        print()
        print("Usage:")
        print("  python build_gui.py              Launch the GUI interface")
        print("  python build_gui.py --help       Show this help message")
        print("  python build_gui.py --version    Show version information")
        print()
        print("Features:")
        print("  • Automatic CLI detection (Python module or executable)")
        print("  • Real-time build progress monitoring")
        print("  • Build configuration options")
        print("  • Live output console")
        print("  • Progress tracking with ETA")
        print()
        print("Requirements:")
        print("  • PyQt6 (pip install PyQt6)")
        print("  • build_cli.py in same directory or dist/ folder")
        print()
        sys.exit(0)
    
    try:
        sys.exit(launch_gui())
    except KeyboardInterrupt:
        print("\n⚠️ GUI interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ GUI error: {e}")
        sys.exit(1)