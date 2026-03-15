#!/usr/bin/env python3
"""
GUI Interface Module for PyInstaller Build Tool
Heavy PyQt6 imports contained in this separate module
Downloaded on-demand when GUI functionality is needed
"""

import sys
import os
import json
import platform
from pathlib import Path

# Heavy GUI imports (only loaded when GUI is actually needed)
try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
        QTabWidget, QGroupBox, QFormLayout, QLineEdit, QPushButton, 
        QCheckBox, QComboBox, QTextEdit, QLabel, QFileDialog, QListWidget,
        QProgressBar, QSplitter, QFrame, QScrollArea, QMessageBox,
        QSlider, QSpinBox, QListWidgetItem, QDialog, QDialogButtonBox,
        QTreeWidget, QTreeWidgetItem, QSizePolicy, QGridLayout,
        QSplashScreen
    )
    
    from PyQt6.QtCore import (
        Qt, QThread, pyqtSignal, QTimer, QMimeData, QSize, QSettings
    )
    from PyQt6.QtGui import (
        QIcon, QPixmap, QDragEnterEvent, QDropEvent, QPalette, QFont, QAction
    )
    GUI_AVAILABLE = True
    
except ImportError as e:
    print(f"❌ PyQt6 not available: {e}")
    print("Install with: pip install PyQt6")
    GUI_AVAILABLE = False

class MinimalGUI:
    """Minimal GUI interface for demonstration"""
    
    def __init__(self):
        self.app = None
        self.main_window = None
        
    def create_main_window(self):
        """Create the main application window"""
        if not GUI_AVAILABLE:
            return False
            
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
            from build_gui_core import BuildToolCore
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
            from build_gui_core import BuildToolCore
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

def launch_gui():
    """Launch the GUI interface"""
    if not GUI_AVAILABLE:
        print("❌ GUI not available. PyQt6 is required.")
        print("Install with: pip install PyQt6")
        return False
    
    try:
        # Create QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Set application properties
        app.setApplicationName("PyInstaller Build Tool")
        app.setApplicationVersion("1.0.0-modular")
        app.setOrganizationName("Enhanced Build System")
        
        # Create and show splash screen
        splash_pixmap = QPixmap(400, 200)
        splash_pixmap.fill(Qt.GlobalColor.white)
        splash = QSplashScreen(splash_pixmap)
        splash.showMessage("Loading GUI Interface...", Qt.AlignmentFlag.AlignCenter)
        splash.show()
        app.processEvents()
        
        # Create main GUI
        gui = MinimalGUI()
        gui.app = app
        
        if not gui.create_main_window():
            splash.close()
            return False
        
        # Show main window and close splash
        gui.main_window.show()
        splash.finish(gui.main_window)
        
        print("✅ GUI interface launched successfully")
        
        # Start event loop
        return app.exec() == 0
        
    except Exception as e:
        print(f"❌ Failed to launch GUI: {e}")
        return False

if __name__ == "__main__":
    success = launch_gui()
    sys.exit(0 if success else 1)
