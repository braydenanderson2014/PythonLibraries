#!/usr/bin/env python3
"""
Update System for PDF Utility
Checks GitHub releases for updates and provides download functionality
"""

import os
import sys
import json
import requests
import webbrowser
from packaging import version
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QProgressBar, QMessageBox
)
from PyQt6.QtCore import QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

try:
    from dotenv import load_dotenv
except ImportError:
    # Fallback if python-dotenv is not available
    def load_dotenv():
        pass

# Load environment variables
load_dotenv()

class UpdateChecker(QThread):
    """Background thread to check for updates"""
    update_available = pyqtSignal(dict)  # Emits update info
    no_update = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.github_owner = os.getenv('GITHUB_OWNER', 'your-username')
        self.github_repo = os.getenv('GITHUB_REPO', 'pdf-utility') 
        self.github_token = os.getenv('GITHUB_TOKEN', '')
        self.current_version = os.getenv('CURRENT_VERSION', '1.0.0')
        self.check_url = os.getenv('UPDATE_CHECK_URL', '').format(
            owner=self.github_owner, 
            repo=self.github_repo
        )
        
    def run(self):
        """Check for updates in background thread"""
        try:
            headers = {}
            if self.github_token:
                headers['Authorization'] = f'token {self.github_token}'
                
            response = requests.get(self.check_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            release_info = response.json()
            latest_version = release_info['tag_name'].lstrip('v')
            
            if version.parse(latest_version) > version.parse(self.current_version):
                update_info = {
                    'version': latest_version,
                    'name': release_info['name'],
                    'body': release_info['body'],
                    'download_url': release_info['html_url'],
                    'published_at': release_info['published_at'],
                    'assets': release_info.get('assets', [])
                }
                self.update_available.emit(update_info)
            else:
                self.no_update.emit()
                
        except requests.exceptions.RequestException as e:
            self.error_occurred.emit(f"Network error: {str(e)}")
        except json.JSONDecodeError as e:
            self.error_occurred.emit(f"Invalid response format: {str(e)}")
        except Exception as e:
            self.error_occurred.emit(f"Unexpected error: {str(e)}")

class UpdateDialog(QDialog):
    """Dialog to show update information and download options"""
    
    def __init__(self, update_info, parent=None):
        super().__init__(parent)
        self.update_info = update_info
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the update dialog UI"""
        self.setWindowTitle("Update Available")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel(f"Update Available: {self.update_info['name']}")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Version info
        version_info = QLabel(f"New Version: {self.update_info['version']}")
        layout.addWidget(version_info)
        
        # Release notes
        notes_label = QLabel("Release Notes:")
        layout.addWidget(notes_label)
        
        notes_text = QTextEdit()
        notes_text.setPlainText(self.update_info['body'])
        notes_text.setReadOnly(True)
        notes_text.setMaximumHeight(200)
        layout.addWidget(notes_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        download_btn = QPushButton("Download Update")
        download_btn.clicked.connect(self.download_update)
        button_layout.addWidget(download_btn)
        
        later_btn = QPushButton("Remind Me Later")
        later_btn.clicked.connect(self.reject)
        button_layout.addWidget(later_btn)
        
        skip_btn = QPushButton("Skip This Version")
        skip_btn.clicked.connect(self.skip_version)
        button_layout.addWidget(skip_btn)
        
        layout.addLayout(button_layout)
        
    def download_update(self):
        """Open browser to download update"""
        webbrowser.open(self.update_info['download_url'])
        self.accept()
        
    def skip_version(self):
        """Skip this version and don't check again"""
        # Store skipped version in settings
        try:
            settings_file = os.path.join(os.path.dirname(__file__), 'settings.json')
            settings = {}
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
            
            settings['skipped_version'] = self.update_info['version']
            
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
                
        except Exception as e:
            print(f"Error saving skipped version: {e}")
            
        self.accept()

class UpdateManager:
    """Main update manager class"""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.checker = None
        self.auto_check_timer = QTimer()
        self.auto_check_timer.timeout.connect(self.check_for_updates_silent)
        
        # Setup automatic checking
        check_interval = int(os.getenv('UPDATE_CHECK_INTERVAL', '86400')) * 1000  # Convert to milliseconds
        if check_interval > 0:
            self.auto_check_timer.start(check_interval)
            
    def check_for_updates_silent(self):
        """Check for updates silently (for automatic checks)"""
        if self.should_skip_check():
            return
            
        self.checker = UpdateChecker()
        self.checker.update_available.connect(self.handle_update_available)
        self.checker.error_occurred.connect(self.handle_error_silent)
        self.checker.start()
        
    def check_for_updates_manual(self):
        """Check for updates manually (user initiated)"""
        if self.checker and self.checker.isRunning():
            return
            
        self.checker = UpdateChecker()
        self.checker.update_available.connect(self.handle_update_available)
        self.checker.no_update.connect(self.handle_no_update)
        self.checker.error_occurred.connect(self.handle_error_manual)
        self.checker.start()
        
    def should_skip_check(self):
        """Check if we should skip checking (version already skipped)"""
        try:
            settings_file = os.path.join(os.path.dirname(__file__), 'settings.json')
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                    skipped_version = settings.get('skipped_version', '')
                    current_version = os.getenv('CURRENT_VERSION', '1.0.0')
                    return version.parse(skipped_version) >= version.parse(current_version)
        except:
            pass
        return False
        
    def handle_update_available(self, update_info):
        """Handle when update is available"""
        dialog = UpdateDialog(update_info, self.parent)
        dialog.exec()
        
    def handle_no_update(self):
        """Handle when no update is available (manual check)"""
        QMessageBox.information(
            self.parent,
            "No Updates",
            "You are running the latest version of PDF Utility!"
        )
        
    def handle_error_silent(self, error_message):
        """Handle errors during silent check"""
        # Log error but don't show to user
        print(f"Update check error: {error_message}")
        
    def handle_error_manual(self, error_message):
        """Handle errors during manual check"""
        QMessageBox.warning(
            self.parent,
            "Update Check Failed",
            f"Could not check for updates:\n{error_message}"
        )

def get_update_manager(parent=None):
    """Factory function to get update manager instance"""
    return UpdateManager(parent)
