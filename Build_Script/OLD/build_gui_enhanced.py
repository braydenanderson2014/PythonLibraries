#!/usr/bin/env python3
"""
PyInstaller Build Tool - GUI with fallback support
Supports PyQt6, tkinter fallback, and console mode
Fast-path optimization for command-line operations
"""

import sys
import os

# Fast-path detection for command-line operations
def should_use_fast_path():
    """Detect if this is a command-line operation that doesn't need GUI imports"""
    if len(sys.argv) <= 1:
        return False  # No arguments, likely GUI mode
    
    # Fast commands that don't need heavy imports
    fast_commands = {
        '--help', '-h', '--version', '--changelog', 
        '--repo-status', '--create-release', '--update', '--downgrade',
        '--show-memory', '--clear-memory', '--clear-mem', '--reset',
        '--show-optimal', '--preview-name', '--activate'
    }
    
    # Check if any fast command is in arguments
    for arg in sys.argv[1:]:
        if arg in fast_commands:
            return True
        # Handle commands with values like --downgrade 1.0.0
        if arg.startswith('--downgrade') or arg.startswith('--version'):
            return True
    
    return False

class ProgrammaticSplashScreen:
    """Custom splash screen that only shows for GUI mode"""
    def __init__(self):
        self.splash_window = None
        self.splash_active = False
    
    def show(self, image_path=None, duration=3000):
        """Show splash screen for GUI mode only"""
        try:
            # Only import PyQt6 when actually needed for splash
            from PyQt6.QtWidgets import QApplication, QSplashScreen, QLabel
            from PyQt6.QtCore import QTimer, Qt
            from PyQt6.QtGui import QPixmap, QFont
            
            # Create minimal QApplication if it doesn't exist
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            # Load splash image
            if image_path and os.path.exists(image_path):
                pixmap = QPixmap(image_path)
            else:
                # Create a simple text-based splash if no image
                pixmap = QPixmap(400, 200)
                pixmap.fill(Qt.GlobalColor.white)
            
            # Create splash screen
            self.splash_window = QSplashScreen(pixmap)
            self.splash_window.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.SplashScreen)
            
            # Add loading text
            font = QFont("Arial", 12)
            self.splash_window.setFont(font)
            self.splash_window.showMessage(
                "Loading PyInstaller Build Tool Enhanced...", 
                Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter,
                Qt.GlobalColor.black
            )
            
            self.splash_window.show()
            self.splash_active = True
            
            # Auto-close after duration
            if duration > 0:
                QTimer.singleShot(duration, self.close)
            
            # Process events to show splash
            app.processEvents()
            
        except ImportError:
            # PyQt6 not available, skip splash
            pass
        except Exception as e:
            # Any other error, skip splash
            pass
    
    def close(self):
        """Close the splash screen"""
        if self.splash_window and self.splash_active:
            try:
                self.splash_window.close()
                self.splash_window = None
                self.splash_active = False
            except:
                pass
    
    def update_message(self, message):
        """Update splash screen message"""
        if self.splash_window and self.splash_active:
            try:
                from PyQt6.QtCore import Qt
                self.splash_window.showMessage(
                    message,
                    Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter,
                    Qt.GlobalColor.black
                )
                # Process events to update display
                if hasattr(QApplication, 'instance'):
                    app = QApplication.instance()
                    if app:
                        app.processEvents()
            except:
                pass

# Global splash instance
splash_screen = ProgrammaticSplashScreen()

# Early fast-path execution before heavy imports
if should_use_fast_path():
    # Only import what's absolutely necessary for command-line operations
    import json
    import argparse
    import urllib.request
    import urllib.parse
    import tempfile
    from datetime import datetime
    from pathlib import Path
    
    # Skip GUI imports entirely
    FAST_PATH_MODE = True
else:
    # GUI mode - show splash screen while loading
    splash_image_path = "Build_Script_splash.png"
    if os.path.exists(splash_image_path):
        splash_screen.show(splash_image_path, duration=0)  # Keep open until we close it
        splash_screen.update_message("Loading GUI components...")
    
    # Full imports for GUI mode
    import json
    import glob
    import argparse
    import subprocess
    import threading
    import time
    import configparser
    from datetime import datetime
    from pathlib import Path
    import venv
    import shutil
    import platform
    import urllib.request
    import urllib.parse
    import tempfile
    import re
    
    FAST_PATH_MODE = False

# Update system configuration
UPDATE_CONFIG = {
    "repo_owner": "your-username",          # Change this to your GitHub username
    "repo_name": "pyinstaller-build-tool", # Change this to your repository name
    "current_version": "2.0.0-enhanced"    # Update this with each release
}

def load_env_config():
    """Load configuration from Build_Script.env file"""
    env_file = os.path.join(os.path.dirname(__file__), "Build_Script.env")
    config = {}
    
    if os.path.exists(env_file):
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip()
                            # Remove quotes if present
                            if value.startswith('"') and value.endswith('"'):
                                value = value[1:-1]
                            elif value.startswith("'") and value.endswith("'"):
                                value = value[1:-1]
                            config[key] = value
        except Exception as e:
            safe_print(f"⚠️  Warning: Could not load Build_Script.env: {e}")
    
    return config

def get_update_config():
    """Get update configuration from environment file or defaults"""
    env_config = load_env_config()
    
    return {
        "repo_owner": env_config.get("GITHUB_REPO_OWNER", "your-username"),
        "repo_name": env_config.get("GITHUB_REPO_NAME", "pyinstaller-build-tool"),
        "current_version": env_config.get("CURRENT_VERSION", "2.0.0-enhanced"),
        "timeout": int(env_config.get("UPDATE_CHECK_TIMEOUT", "10")),
        "auto_confirm": env_config.get("UPDATE_AUTO_CONFIRM", "false").lower() == "true",
        "create_backup": env_config.get("UPDATE_CREATE_BACKUP", "true").lower() == "true"
    }

def get_build_tool_config():
    """Get build tool configuration from environment file or defaults"""
    env_config = load_env_config()
    
    return {
        "name": env_config.get("BUILD_TOOL_NAME", "PyInstaller Build Tool Enhanced"),
        "author": env_config.get("BUILD_TOOL_AUTHOR", "Enhanced Build System"),
        "description": env_config.get("BUILD_TOOL_DESCRIPTION", "Advanced PyInstaller GUI and Console Tool"),
        "debug_mode": env_config.get("DEBUG_MODE", "false").lower() == "true",
        "verbose_output": env_config.get("VERBOSE_OUTPUT", "false").lower() == "true",
        "safe_mode": env_config.get("SAFE_MODE", "true").lower() == "true"
    }

def get_project_defaults():
    """Get project creation defaults from environment file"""
    env_config = load_env_config()
    
    return {
        "version": env_config.get("DEFAULT_PROJECT_VERSION", "1.0.0"),
        "author": env_config.get("DEFAULT_PROJECT_AUTHOR", "Your Name"),
        "venv_name": env_config.get("DEFAULT_VENV_NAME", "build_env"),
        "venv_auto_install": env_config.get("VENV_AUTO_INSTALL", "true").lower() == "true"
    }

def generate_versioned_name(base_name, version=None, include_date=True, date_format="%m%d%Y"):
    """Generate a versioned name with optional date stamp"""
    if not base_name:
        base_name = "Application"
    
    # Clean the base name
    base_name = re.sub(r'[<>:"/\\|?*]', '_', base_name)
    
    parts = [base_name]
    
    # Add version if provided
    if version and version.strip():
        clean_version = re.sub(r'[<>:"/\\|?*]', '_', version.strip())
        parts.append(f"v{clean_version}")
    
    # Add date if requested
    if include_date:
        date_str = datetime.now().strftime(date_format)
        parts.append(date_str)
    
    return "-".join(parts)

def generate_output_paths(base_name, version=None, include_date=True):
    """Generate output paths for dist, work, and spec directories"""
    versioned_name = generate_versioned_name(base_name, version, include_date)
    
    return {
        "dist_name": versioned_name,
        "distpath": f"dist_{versioned_name}",
        "workpath": f"build_{versioned_name}",
        "specpath": f"specs_{versioned_name}"
    }

# Skip heavy imports for fast-path commands
FAST_PATH_MODE = should_use_fast_path()

if not FAST_PATH_MODE:
    # GUI mode - show splash screen while loading
    splash_image_path = "Build_Script_splash.png"
    if os.path.exists(splash_image_path):
        splash_screen.show(splash_image_path, duration=0)  # Keep open until we close it
    else:
        splash_screen.show(duration=0)  # Show default splash

    # Heavy imports only needed for GUI mode
    try:
        splash_screen.update_message("Loading image processing libraries...")
        from PIL import Image
        PIL_AVAILABLE = True
    except ImportError:
        PIL_AVAILABLE = False
        print("Warning: PIL/Pillow not available. ICO to PNG conversion will be disabled.")
    
    # Import the original console builder
    try:
        splash_screen.update_message("Loading console modules...")
        from build_script import PyInstallerBuilder as ConsoleBuilder
    except ImportError:
        print("Warning: build_script.py not found. Console mode may not work.")
        ConsoleBuilder = None
else:
    # Fast-path mode - minimal imports only
    PIL_AVAILABLE = False
    ConsoleBuilder = None

# Try to import GUI libraries in order of preference (only if not fast-path)
GUI_BACKEND = None
GUI_ERROR = None

if not should_use_fast_path():
    # Try PyQt6 first
    try:
        # Update splash screen during import
        splash_screen.update_message("Loading PyQt6 widgets...")
        
        from PyQt6.QtWidgets import (
            QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
            QTabWidget, QGroupBox, QFormLayout, QLineEdit, QPushButton, 
            QCheckBox, QComboBox, QTextEdit, QLabel, QFileDialog, QListWidget,
            QProgressBar, QSplitter, QFrame, QScrollArea, QMessageBox,
            QSlider, QSpinBox, QListWidgetItem, QDialog, QDialogButtonBox,
            QTreeWidget, QTreeWidgetItem, QSizePolicy, QGridLayout
        )
        
        splash_screen.update_message("Loading PyQt6 core modules...")
        
        from PyQt6.QtCore import (
            Qt, QThread, pyqtSignal, QTimer, QMimeData, QSize, QSettings
        )
        from PyQt6.QtGui import (
            QIcon, QPixmap, QDragEnterEvent, QDropEvent, QPalette, QFont, QAction
        )
        GUI_BACKEND = "PyQt6"
        
        splash_screen.update_message("PyQt6 loaded successfully...")
        
    except ImportError as e:
        GUI_ERROR = f"PyQt6 not available: {e}"

    # Try tkinter as fallback
    if GUI_BACKEND is None:
        try:
            import tkinter as tk
            from tkinter import ttk, filedialog, messagebox, scrolledtext
            GUI_BACKEND = "tkinter"
        except ImportError as e:
            GUI_ERROR = f"tkinter not available: {e}"

class ConsoleMemory:
    """Memory system for console mode to store scan results and configuration"""
    
    def __init__(self, memory_file="build_console_memory.json"):
        self.memory_file = memory_file
        self.memory = self.load_memory()
    
    def load_memory(self):
        """Load memory from file"""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load console memory: {e}")
        
        return {
            "scan_results": {},
            "build_config": {},
            "last_scan_type": None,
            "last_updated": None
        }
    
    def save_memory(self):
        """Save memory to file"""
        try:
            self.memory["last_updated"] = datetime.now().isoformat()
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(self.memory, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving console memory: {e}")
    
    def store_scan_results(self, scan_type, results, append=False):
        """Store scan results in memory"""
        if append and scan_type in self.memory["scan_results"]:
            # Append new results to existing ones
            existing = self.memory["scan_results"][scan_type]
            combined = list(set(existing + results))  # Remove duplicates
            self.memory["scan_results"][scan_type] = combined
        else:
            # Replace existing results
            self.memory["scan_results"][scan_type] = results
        
        self.memory["last_scan_type"] = scan_type
        self.save_memory()
    
    def get_scan_results(self, scan_type=None):
        """Get scan results from memory"""
        if scan_type:
            return self.memory["scan_results"].get(scan_type, [])
        return self.memory["scan_results"]
    
    def store_config(self, config_data):
        """Store build configuration in memory"""
        self.memory["build_config"].update(config_data)
        self.save_memory()
    
    def get_config(self):
        """Get build configuration from memory"""
        return self.memory["build_config"]
    
    def clear_memory(self, section=None):
        """Clear memory section or all memory"""
        if section:
            if section in self.memory:
                self.memory[section] = {} if section in ["scan_results", "build_config"] else None
        else:
            self.memory = {
                "scan_results": {},
                "build_config": {},
                "last_scan_type": None,
                "last_updated": None
            }
        self.save_memory()
    
    def show_memory_status(self):
        """Display current memory status"""
        print("📋 Console Memory Status:")
        print("=" * 40)
        
        if self.memory["last_updated"]:
            print(f"Last Updated: {self.memory['last_updated']}")
        
        scan_results = self.memory["scan_results"]
        if scan_results:
            print(f"\\nStored Scan Results:")
            for scan_type, files in scan_results.items():
                print(f"  📁 {scan_type}: {len(files)} files")
        else:
            print("\\nNo scan results stored")
        
        config = self.memory["build_config"]
        if config:
            print(f"\\nStored Configuration Keys: {list(config.keys())}")
        else:
            print("\\nNo configuration stored")
    
    def remove_file_from_memory(self, filename):
        """Remove a specific file from memory by filename"""
        removed_count = 0
        removed_from_types = []
        
        for scan_type, files in self.memory["scan_results"].items():
            # Find files that match the filename (could be basename or full path)
            files_to_remove = []
            for file_path in files:
                if filename in file_path or os.path.basename(file_path) == filename:
                    files_to_remove.append(file_path)
            
            # Remove the matching files
            for file_to_remove in files_to_remove:
                if file_to_remove in files:
                    files.remove(file_to_remove)
                    removed_count += 1
                    if scan_type not in removed_from_types:
                        removed_from_types.append(scan_type)
        
        if removed_count > 0:
            self.save_memory()
            print(f"✅ Removed {removed_count} files matching '{filename}' from types: {', '.join(removed_from_types)}")
            return True
        else:
            print(f"❌ No files found matching '{filename}' in memory")
            return False
    
    def remove_type_from_memory(self, scan_type):
        """Remove all files of a specific type from memory"""
        if scan_type in self.memory["scan_results"]:
            file_count = len(self.memory["scan_results"][scan_type])
            del self.memory["scan_results"][scan_type]
            self.save_memory()
            print(f"✅ Removed {file_count} files of type '{scan_type}' from memory")
            return True
        else:
            print(f"❌ No files of type '{scan_type}' found in memory")
            available_types = list(self.memory["scan_results"].keys())
            if available_types:
                print(f"Available types: {', '.join(available_types)}")
            return False
    
    def reset_memory(self):
        """Reset all memory completely"""
        self.memory = {
            "scan_results": {},
            "build_config": {},
            "last_scan_type": None,
            "last_updated": None
        }
        self.save_memory()
        print("✅ Memory reset completely")
        return True

class EnhancedConsoleBuilder:
    """Enhanced console builder with additional GUI-friendly methods"""
    
    def __init__(self):
        self.console_builder = ConsoleBuilder() if ConsoleBuilder else None
        self.file_patterns = self.load_file_patterns()
        self.custom_patterns = {}
    
    def load_file_patterns(self):
        """Load file patterns from JSON configuration"""
        try:
            patterns_file = os.path.join(os.path.dirname(__file__), "enhanced_file_patterns.json")
            if os.path.exists(patterns_file):
                with open(patterns_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load enhanced file patterns: {e}")
        
        # Fallback to basic patterns
        return {
            "file_patterns": {
                "help_files": {
                    "patterns": ["HELP_*.md", "HELP_*.txt", "README*.md"],
                    "directories": [".", "help", "docs"]
                },
                "config_files": {
                    "patterns": ["config.json", "settings.json", "*.config.json"],
                    "directories": [".", "config"]
                }
            }
        }
    
    def load_custom_patterns_from_file(self, filepath):
        """Load custom search patterns from a JSON file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                custom_data = json.load(f)
                if "custom_patterns" in custom_data:
                    self.custom_patterns.update(custom_data["custom_patterns"])
                    return True
                elif "file_patterns" in custom_data:
                    # If it's a full patterns file, merge it
                    for category, config in custom_data["file_patterns"].items():
                        if category not in self.file_patterns.get("file_patterns", {}):
                            self.file_patterns.setdefault("file_patterns", {})[category] = config
                    return True
        except Exception as e:
            print(f"Error loading custom patterns: {e}")
        return False
    
    def find_files_by_pattern(self, category, additional_patterns=None, additional_dirs=None):
        """Find files by category pattern with optional additional patterns"""
        patterns_config = self.file_patterns.get("file_patterns", {}).get(category, {})
        patterns = patterns_config.get("patterns", [])
        directories = patterns_config.get("directories", ["."])
        
        # Add additional patterns if provided
        if additional_patterns:
            patterns.extend(additional_patterns)
        
        # Add additional directories if provided
        if additional_dirs:
            directories.extend(additional_dirs)
        
        found_files = []
        
        for directory in directories:
            if os.path.exists(directory):
                for pattern in patterns:
                    search_path = os.path.join(directory, pattern)
                    matching_files = glob.glob(search_path)
                    for file_path in matching_files:
                        if os.path.isfile(file_path):
                            found_files.append(file_path)
        
        # Remove duplicates and sort
        return sorted(list(set(found_files)))
    
    def find_files_by_custom_pattern(self, custom_pattern, search_dirs=None):
        """Find files by custom user-provided pattern"""
        if search_dirs is None:
            search_dirs = ["."]
        
        found_files = []
        patterns = custom_pattern.split(";") if ";" in custom_pattern else [custom_pattern]
        
        for directory in search_dirs:
            if os.path.exists(directory):
                for pattern in patterns:
                    pattern = pattern.strip()
                    if not pattern:
                        continue
                    
                    # Handle both glob patterns and exact filenames
                    if "*" in pattern or "?" in pattern:
                        search_path = os.path.join(directory, pattern)
                        matching_files = glob.glob(search_path)
                    else:
                        # Exact filename
                        search_path = os.path.join(directory, pattern)
                        matching_files = [search_path] if os.path.isfile(search_path) else []
                    
                    for file_path in matching_files:
                        if os.path.isfile(file_path):
                            found_files.append(file_path)
        
        return sorted(list(set(found_files)))
    
    def find_common_files(self, file_type):
        """Find common files by type using predefined common names"""
        common_names = self.file_patterns.get("custom_searches", {}).get("common_names", {})
        filenames = common_names.get(file_type, [])
        
        found_files = []
        search_dirs = [".", "src", "app", "bin", "scripts", "assets", "resources"]
        
        for directory in search_dirs:
            if os.path.exists(directory):
                for filename in filenames:
                    file_path = os.path.join(directory, filename)
                    if os.path.isfile(file_path):
                        found_files.append(file_path)
        
        return found_files
            
    def get_console_builder(self):
        return self.console_builder
        
    def find_help_files(self):
        """Find help files using enhanced patterns including PREFIX-based naming"""
        if self.console_builder and hasattr(self.console_builder, 'find_help_files'):
            # Use original method and combine with enhanced patterns
            original_files = self.console_builder.find_help_files()
        else:
            original_files = []
        
        # Enhanced patterns including PREFIX-based naming
        enhanced_patterns = [
            "HELP_*.md", "HELP_*.txt", "README*.md",  # Traditional patterns
            "HELP-*.md", "HELP-*.txt", "HELP-*.json",  # PREFIX-based patterns
            "*help*.md", "*help*.txt"  # Additional help patterns
        ]
        enhanced_files = self.find_files_by_custom_pattern(";".join(enhanced_patterns))
        
        # Combine original and enhanced results, remove duplicates
        combined = list(set(original_files + enhanced_files))
        return sorted(combined)
    
    def find_tutorial_files(self):
        """Find tutorial files using enhanced patterns including PREFIX-based naming"""
        if self.console_builder and hasattr(self.console_builder, 'find_tutorial_files'):
            original_files = self.console_builder.find_tutorial_files()
        else:
            original_files = []
        
        # Enhanced patterns for tutorial files including PREFIX-based naming
        tutorial_patterns = [
            "tutorial*.py", "help_system*.py", "*tutorial*.py",  # Traditional patterns
            "TUTORIAL-*.py", "TUTORIAL-*.json", "TUTORIAL-*.md", "TUTORIAL-*.txt",  # PREFIX-based patterns
            "TUTORIAL_*.py", "TUTORIAL_*.json", "TUTORIAL_*.md", "TUTORIAL_*.txt"   # Alternative PREFIX format
        ]
        
        enhanced_files = self.find_files_by_custom_pattern(";".join(tutorial_patterns))
        
        # Combine original and enhanced results, remove duplicates
        combined = list(set(original_files + enhanced_files))
        return sorted(combined)
    
    def find_changelog_files(self):
        """Find changelog files using enhanced patterns"""
        if self.console_builder and hasattr(self.console_builder, 'find_changelog_files'):
            original_files = self.console_builder.find_changelog_files()
            enhanced_files = self.find_files_by_pattern("documentation_files", 
                                                       additional_patterns=["CHANGELOG*", "changelog*"])
            combined = list(set(original_files + enhanced_files))
            return sorted(combined)
        else:
            return self.find_files_by_pattern("documentation_files", 
                                             additional_patterns=["CHANGELOG*", "changelog*"])
    
    def find_config_files(self):
        """Find configuration files using enhanced patterns including PREFIX-based naming"""
        # Use enhanced patterns including PREFIX-based naming
        config_patterns = [
            "config.json", "settings.json", "*.config.json",  # Traditional patterns
            "app_config.json", "demo_config.json", "build_config.json",  # App-specific patterns
            "CONFIG-*.json", "CONFIG-*.yaml", "CONFIG-*.yml",  # PREFIX-based patterns
            "CONFIG_*.json", "CONFIG_*.yaml", "CONFIG_*.yml"   # Alternative PREFIX format
        ]
        
        return self.find_files_by_custom_pattern(";".join(config_patterns))
    
    def find_data_files(self):
        """Find data files using enhanced patterns including PREFIX-based naming"""
        # Enhanced patterns including PREFIX-based naming
        data_patterns = [
            "*.json", "*.xml", "*.yaml", "*.yml", "*.csv", "*.txt",  # Traditional patterns
            "*.db", "*.sqlite", "*.data",  # Database and data files
            "DATA-*.json", "DATA-*.xml", "DATA-*.csv", "DATA-*.txt",  # PREFIX-based patterns
            "DATA_*.json", "DATA_*.xml", "DATA_*.csv", "DATA_*.txt"   # Alternative PREFIX format
        ]
        
        return self.find_files_by_custom_pattern(";".join(data_patterns))
    
    def find_asset_files(self):
        """Find asset files using enhanced patterns"""
        return self.find_files_by_pattern("asset_files")
    
    def find_documentation_files(self):
        """Find documentation files using enhanced patterns"""
        return self.find_files_by_pattern("documentation_files")
    
    def find_template_files(self):
        """Find template files using enhanced patterns"""
        return self.find_files_by_pattern("template_files")
    
    def find_language_files(self):
        """Find language/localization files using enhanced patterns"""
        return self.find_files_by_pattern("language_files")
    
    def find_script_files(self):
        """Find script files using enhanced patterns"""
        return self.find_files_by_pattern("script_files")
    
    def find_main_files(self):
        """Find potential main entry files"""
        return self.find_common_files("main_files")
    
    def find_icon_files(self):
        """Find potential icon files"""
        icon_files = []
        
        # First try the common files method
        common_files = self.find_common_files("icon_files")
        icon_files.extend(common_files)
        
        # Always search for additional icons using patterns
        icon_patterns = ["*.ico", "icon.*", "app.*", "logo.*", "main.*"]
        search_dirs = [".", "assets", "icons", "images", "resources"]
        
        for directory in search_dirs:
            if os.path.exists(directory):
                for pattern in icon_patterns:
                    if "*" in pattern or "?" in pattern:
                        search_path = os.path.join(directory, pattern)
                        found_files = glob.glob(search_path)
                        # Filter for common icon formats and avoid PNG files for icons
                        for file_path in found_files:
                            if file_path.lower().endswith(('.ico',)):
                                icon_files.append(file_path)
                    else:
                        # Exact filename
                        file_path = os.path.join(directory, pattern)
                        if os.path.isfile(file_path) and file_path.lower().endswith('.ico'):
                            icon_files.append(file_path)
        
        # Add specific common icon names
        specific_icons = ["Build_Script.ico", "PDF_Utility.ico", "app.ico", "main.ico", "icon.ico"]
        for icon_name in specific_icons:
            if os.path.isfile(icon_name):
                icon_files.append(icon_name)
        
        # Remove duplicates and normalize paths, return sorted list
        unique_files = []
        seen_files = set()
        for f in icon_files:
            if os.path.isfile(f):
                normalized = os.path.normpath(f)
                if normalized not in seen_files:
                    seen_files.add(normalized)
                    unique_files.append(f)
        
        return sorted(unique_files)
    
    def find_splash_files(self):
        """Find potential splash screen files"""
        # First try the common files method
        splash_files = self.find_common_files("splash_files")
        
        # If that doesn't work, use fallback patterns
        if not splash_files:
            splash_patterns = ["splash.*", "logo.*", "*splash*", "*.png", "*.jpg", "*.bmp"]
            search_dirs = [".", "assets", "images", "resources", "splash"]
            
            for directory in search_dirs:
                if os.path.exists(directory):
                    for pattern in splash_patterns:
                        if "*" in pattern or "?" in pattern:
                            search_path = os.path.join(directory, pattern)
                            found_files = glob.glob(search_path)
                            # Filter for common image formats
                            for file_path in found_files:
                                if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                                    splash_files.append(file_path)
                        else:
                            # Exact filename
                            file_path = os.path.join(directory, pattern)
                            if os.path.isfile(file_path):
                                splash_files.append(file_path)
        
        # Remove duplicates and return sorted list
        return sorted(list(set([f for f in splash_files if os.path.isfile(f)])))
    
    def convert_ico_to_png(self, ico_path, output_path=None, size=None):
        """Convert ICO file to PNG format for splash screen use"""
        if not PIL_AVAILABLE:
            print("Error: PIL/Pillow is required for ICO to PNG conversion")
            print("Install with: pip install Pillow")
            return None
        
        try:
            if not os.path.exists(ico_path):
                print(f"Error: ICO file not found: {ico_path}")
                return None
            
            # Generate output path if not provided
            if output_path is None:
                base_name = os.path.splitext(os.path.basename(ico_path))[0]
                output_path = f"{base_name}_splash.png"
            
            # Open ICO file
            with Image.open(ico_path) as img:
                # Convert to RGBA if not already
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # Resize if size specified
                if size:
                    if isinstance(size, (int, float)):
                        size = (int(size), int(size))
                    img = img.resize(size, Image.Resampling.LANCZOS)
                
                # Save as PNG
                img.save(output_path, 'PNG')
                print(f"✅ Converted {ico_path} to {output_path}")
                return output_path
                
        except Exception as e:
            print(f"Error converting ICO to PNG: {e}")
            return None
    
    def find_and_convert_icons_for_splash(self, output_dir="converted_splash"):
        """Find ICO files and convert them to PNG for splash screen use"""
        if not PIL_AVAILABLE:
            print("ICO to PNG conversion requires PIL/Pillow")
            return []
        
        # Find ICO files
        ico_files = []
        ico_patterns = ["*.ico", "*.ICO"]
        search_dirs = [".", "assets", "icons", "images", "resources"]
        
        for directory in search_dirs:
            if os.path.exists(directory):
                for pattern in ico_patterns:
                    search_path = os.path.join(directory, pattern)
                    ico_files.extend(glob.glob(search_path))
        
        if not ico_files:
            print("No ICO files found for conversion")
            return []
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        converted_files = []
        for ico_file in ico_files:
            base_name = os.path.splitext(os.path.basename(ico_file))[0]
            output_path = os.path.join(output_dir, f"{base_name}_splash.png")
            
            result = self.convert_ico_to_png(ico_file, output_path)
            if result:
                converted_files.append(result)
        
        return converted_files
    
    def get_ico_info(self, ico_path):
        """Get information about ICO file sizes and formats"""
        if not PIL_AVAILABLE:
            return None
        
        try:
            with Image.open(ico_path) as img:
                # ICO files can contain multiple sizes
                sizes = []
                try:
                    # Try to get all sizes in the ICO
                    for i in range(100):  # Arbitrary limit
                        img.seek(i)
                        sizes.append(img.size)
                except EOFError:
                    pass
                
                return {
                    "file": ico_path,
                    "format": img.format,
                    "mode": img.mode,
                    "sizes": sizes,
                    "recommended_splash_size": max(sizes) if sizes else None
                }
        except Exception as e:
            print(f"Error reading ICO file info: {e}")
            return None
    
    def build_pyinstaller_command(self, config):
        """Build PyInstaller command from configuration"""
        command = ["pyinstaller"]
        
        # Basic options
        if config.get("onefile", False):
            command.append("--onefile")
        if config.get("windowed", False):
            command.append("--windowed")
        if config.get("clean", False):
            command.append("--clean")
        if config.get("debug", False):
            command.append("--debug=all")
        if config.get("uac_admin", False):
            command.append("--uac-admin")
        if config.get("console", False):
            command.append("--console")
            
        # Paths
        if config.get("icon"):
            icon_path = config["icon"]
            # Convert to absolute path if relative
            if not os.path.isabs(icon_path):
                icon_path = os.path.abspath(icon_path)
            command.extend(["--icon", icon_path])
        if config.get("splash"):
            splash_file = config["splash"]
            # Convert to absolute path if relative
            if not os.path.isabs(splash_file):
                splash_file = os.path.abspath(splash_file)
            
            # Note: Splash timeout is handled in the spec file generation, not in command line
            command.extend(["--splash", splash_file])
        if config.get("distpath"):
            command.extend(["--distpath", config["distpath"]])
        if config.get("workpath"):
            command.extend(["--workpath", config["workpath"]])
        if config.get("specpath"):
            command.extend(["--specpath", config["specpath"]])
            
        # Hidden imports
        for imp in config.get("hidden_imports", []):
            if imp.strip():
                command.extend(["--hidden-import", imp.strip()])
                
        # Additional data - fix OS-specific path separator and use correct PyInstaller syntax
        path_separator = ";" if os.name == "nt" else ":"  # Windows uses ; Linux/Mac uses :
        for data in config.get("add_data", []):
            if data.strip():
                # Check if data already has proper format (SOURCE:DEST or SOURCE;DEST)
                data_item = data.strip()
                
                # Parse source and destination
                if ":" in data_item or ";" in data_item:
                    # Split existing format
                    if ":" in data_item:
                        source, dest = data_item.split(":", 1)
                    else:
                        source, dest = data_item.split(";", 1)
                else:
                    # If no separator, assume it's source file and destination is current dir
                    source = data_item
                    dest = "."
                
                # Convert source to absolute path if it's relative
                if not os.path.isabs(source):
                    source = os.path.abspath(source)
                
                # Verify source file exists
                if not os.path.exists(source):
                    print(f"Warning: Data file not found: {source}")
                    continue
                
                # Build the corrected data item with OS-appropriate separator
                corrected_data_item = f"{source}{path_separator}{dest}"
                
                # Use the correct PyInstaller syntax: --add-data=SOURCE:DEST
                command.append(f"--add-data={corrected_data_item}")
                
        # Main entry point
        if config.get("main_entry"):
            main_entry = config["main_entry"]
            # Convert to absolute path if relative
            if not os.path.isabs(main_entry):
                main_entry = os.path.abspath(main_entry)
            command.append(main_entry)
            
        return command
        
    def execute_build(self, command, progress_callback=None):
        """Execute build with optional progress callback"""
        try:
            if progress_callback:
                progress_callback("Starting build process...")
                
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                universal_newlines=True
            )
            
            output_lines = []
            for line in iter(process.stdout.readline, ''):
                if line:
                    line = line.strip()
                    output_lines.append(line)
                    if progress_callback:
                        progress_callback(line)
                        
            process.wait()
            
            success = process.returncode == 0
            message = "Build completed successfully!" if success else f"Build failed with return code {process.returncode}"
            
            return success, message, output_lines
            
        except Exception as e:
            return False, f"Build error: {str(e)}", []

# GUI Implementation based on available backend
if GUI_BACKEND == "PyQt6":
    class BuildThread(QThread):
        """Thread for handling build process without blocking UI"""
        progress_signal = pyqtSignal(str)
        finished_signal = pyqtSignal(bool, str, list)
        
        def __init__(self, command, builder):
            super().__init__()
            self.command = command
            self.builder = builder
        
        def run(self):
            """Run the build process in the thread"""
            def progress_callback(message):
                self.progress_signal.emit(message)
            
            success, message, output = self.builder.execute_build(self.command, progress_callback)
            self.finished_signal.emit(success, message, output)
    
    class PyInstallerGUI(QMainWindow):
        """PyQt6-based GUI for PyInstaller Build Tool"""
        
        def __init__(self):
            super().__init__()
            self.builder = EnhancedConsoleBuilder()
            self.setup_ui()
            self.setup_defaults()
            
        def setup_ui(self):
            """Set up the user interface"""
            self.setWindowTitle("PyInstaller Build Tool")
            self.setGeometry(100, 100, 1000, 800)
            
            # Set window icon to Build_Script.ico if it exists
            if os.path.exists("Build_Script.ico"):
                self.setWindowIcon(QIcon("Build_Script.ico"))
            
            # Create central widget and main layout
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            layout = QVBoxLayout(central_widget)
            
            # Create tab widget
            self.tab_widget = QTabWidget()
            layout.addWidget(self.tab_widget)
            
            # Create tabs
            self.create_basic_tab()
            self.create_files_tab()
            self.create_build_tab()
            
            # Create status bar
            self.statusBar().showMessage("Ready")
            
        def setup_defaults(self):
            """Set up default values for the form"""
            # Set default icon field to Build_Script.ico if it exists (for building other programs)
            default_icon = "Build_Script.ico"
            if os.path.exists(default_icon):
                self.icon_file.setText(default_icon)
            
        def create_basic_tab(self):
            """Create basic configuration tab"""
            tab = QWidget()
            self.tab_widget.addTab(tab, "Basic Configuration")
            
            layout = QVBoxLayout(tab)
            
            # Program info group
            info_group = QGroupBox("Program Information")
            info_layout = QFormLayout(info_group)
            
            self.program_name = QLineEdit()
            self.program_name.setPlaceholderText("Enter program name")
            info_layout.addRow("Program Name:", self.program_name)
            
            self.version = QLineEdit()
            self.version.setPlaceholderText("1.0.0")
            info_layout.addRow("Version:", self.version)
            
            # Versioning options
            versioning_layout = QHBoxLayout()
            self.include_date = QCheckBox("Include Date")
            self.include_date.setChecked(True)
            self.include_date.setToolTip("Add current date to build folder names")
            versioning_layout.addWidget(self.include_date)
            
            self.date_format = QComboBox()
            self.date_format.addItems([
                "%m%d%Y (01032025)",
                "%Y%m%d (20250103)",
                "%d%m%Y (03012025)",
                "%Y-%m-%d (2025-01-03)",
                "%m-%d-%Y (01-03-2025)"
            ])
            self.date_format.setToolTip("Choose date format for build names")
            versioning_layout.addWidget(self.date_format)
            
            preview_name_btn = QPushButton("Preview")
            preview_name_btn.clicked.connect(self.preview_build_name)
            preview_name_btn.setToolTip("Preview the generated build name")
            versioning_layout.addWidget(preview_name_btn)
            
            versioning_layout.addStretch()
            info_layout.addRow("Build Naming:", versioning_layout)
            
            # Main script with auto-detect
            self.main_script = QLineEdit()
            self.main_script.setPlaceholderText("Select main Python file")
            script_layout = QHBoxLayout()
            script_layout.addWidget(self.main_script)
            
            main_script_btn = QPushButton("Browse...")
            main_script_btn.clicked.connect(self.browse_main_script)
            script_layout.addWidget(main_script_btn)
            
            auto_detect_btn = QPushButton("Auto-detect")
            auto_detect_btn.clicked.connect(self.auto_detect_main)
            script_layout.addWidget(auto_detect_btn)
            
            info_layout.addRow("Main Script:", script_layout)
            layout.addWidget(info_group)
            
            # Build options group
            options_group = QGroupBox("Build Options")
            options_layout = QFormLayout(options_group)
            
            self.one_file = QCheckBox("One File")
            self.one_file.setChecked(True)
            options_layout.addRow(self.one_file)
            
            self.windowed = QCheckBox("Windowed (no console)")
            self.windowed.setChecked(True)
            options_layout.addRow(self.windowed)
            
            self.clean_build = QCheckBox("Clean build")
            self.clean_build.setChecked(True)
            options_layout.addRow(self.clean_build)
            
            self.debug = QCheckBox("Debug mode")
            options_layout.addRow(self.debug)
            
            self.uac_admin = QCheckBox("UAC Admin (Windows)")
            options_layout.addRow(self.uac_admin)
            
            layout.addWidget(options_group)
            
            # Visual assets group
            visual_group = QGroupBox("Visual Assets")
            visual_layout = QFormLayout(visual_group)
            
            # Icon file
            self.icon_file = QLineEdit()
            self.icon_file.setPlaceholderText("Select icon file (.ico recommended)")
            icon_layout = QHBoxLayout()
            icon_layout.addWidget(self.icon_file)
            
            icon_browse_btn = QPushButton("Browse...")
            icon_browse_btn.clicked.connect(self.browse_icon)
            icon_layout.addWidget(icon_browse_btn)
            
            auto_icon_btn = QPushButton("Auto-find")
            auto_icon_btn.clicked.connect(self.auto_find_icon)
            icon_layout.addWidget(auto_icon_btn)
            
            visual_layout.addRow("Icon File:", icon_layout)
            
            # Splash screen
            self.splash_file = QLineEdit()
            self.splash_file.setPlaceholderText("Select splash screen (.png recommended)")
            splash_layout = QHBoxLayout()
            splash_layout.addWidget(self.splash_file)
            
            splash_browse_btn = QPushButton("Browse...")
            splash_browse_btn.clicked.connect(self.browse_splash)
            splash_layout.addWidget(splash_browse_btn)
            
            auto_splash_btn = QPushButton("Auto-find")
            auto_splash_btn.clicked.connect(self.auto_find_splash)
            splash_layout.addWidget(auto_splash_btn)
            
            convert_ico_btn = QPushButton("Convert ICO→PNG")
            convert_ico_btn.clicked.connect(self.convert_icon_to_splash)
            splash_layout.addWidget(convert_ico_btn)
            
            visual_layout.addRow("Splash Screen:", splash_layout)
            
            # Splash timeout
            timeout_layout = QHBoxLayout()
            self.splash_timeout = QLineEdit()
            self.splash_timeout.setPlaceholderText("5000 (milliseconds, 0 to disable)")
            self.splash_timeout.setText("5000")
            self.splash_timeout.setToolTip("Duration in milliseconds to show splash screen.\nUse 0 to disable auto-close (manual close only).\nRecommended: 3000-8000ms")
            timeout_layout.addWidget(self.splash_timeout)
            
            timeout_help_btn = QPushButton("?")
            timeout_help_btn.setMaximumWidth(25)
            timeout_help_btn.clicked.connect(self.show_splash_timeout_help)
            timeout_layout.addWidget(timeout_help_btn)
            
            auto_timeout_btn = QPushButton("Auto")
            auto_timeout_btn.setMaximumWidth(40)
            auto_timeout_btn.clicked.connect(self.auto_set_splash_timeout)
            auto_timeout_btn.setToolTip("Automatically set timeout based on project size")
            timeout_layout.addWidget(auto_timeout_btn)
            
            visual_layout.addRow("Splash Timeout (ms):", timeout_layout)
            
            layout.addWidget(visual_group)
            
            # ICO conversion tools
            ico_group = QGroupBox("ICO Conversion Tools")
            ico_layout = QHBoxLayout(ico_group)
            
            convert_all_btn = QPushButton("Convert All ICOs")
            convert_all_btn.clicked.connect(self.convert_all_icons)
            ico_layout.addWidget(convert_all_btn)
            
            ico_info_btn = QPushButton("Show ICO Info")
            ico_info_btn.clicked.connect(self.show_ico_info)
            ico_layout.addWidget(ico_info_btn)
            
            convert_single_btn = QPushButton("Convert Single ICO")
            convert_single_btn.clicked.connect(self.convert_single_ico)
            ico_layout.addWidget(convert_single_btn)
            
            layout.addWidget(ico_group)
            layout.addStretch()
            
        def create_files_tab(self):
            """Create files management tab"""
            tab = QWidget()
            self.tab_widget.addTab(tab, "Files & Resources")
            
            layout = QVBoxLayout(tab)
            
            # Files list with enhanced controls
            files_group = QGroupBox("Additional Files & Resources")
            files_layout = QVBoxLayout(files_group)
            
            self.files_list = QListWidget()
            self.files_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
            files_layout.addWidget(self.files_list)
            
            # Manual file management buttons
            manual_buttons = QHBoxLayout()
            add_file_btn = QPushButton("Add File")
            add_file_btn.clicked.connect(self.add_file)
            manual_buttons.addWidget(add_file_btn)
            
            add_folder_btn = QPushButton("Add Folder")
            add_folder_btn.clicked.connect(self.add_folder)
            manual_buttons.addWidget(add_folder_btn)
            
            remove_btn = QPushButton("Remove Selected")
            remove_btn.clicked.connect(self.remove_file)
            manual_buttons.addWidget(remove_btn)
            
            clear_all_btn = QPushButton("Clear All")
            clear_all_btn.clicked.connect(self.clear_all_files)
            manual_buttons.addWidget(clear_all_btn)
            
            manual_buttons.addStretch()
            files_layout.addLayout(manual_buttons)
            
            layout.addWidget(files_group)
            
            # Auto-detection section
            auto_group = QGroupBox("Auto-Detection & Smart Search")
            auto_layout = QVBoxLayout(auto_group)
            
            # Common file types - Row 1
            auto_row1 = QHBoxLayout()
            
            help_btn = QPushButton("Help Files")
            help_btn.clicked.connect(self.detect_help_files)
            auto_row1.addWidget(help_btn)
            
            tutorial_btn = QPushButton("Tutorial Files")
            tutorial_btn.clicked.connect(self.detect_tutorial_files)
            auto_row1.addWidget(tutorial_btn)
            
            config_btn = QPushButton("Config Files")
            config_btn.clicked.connect(self.detect_config_files)
            auto_row1.addWidget(config_btn)
            
            data_btn = QPushButton("Data Files")
            data_btn.clicked.connect(self.detect_data_files)
            auto_row1.addWidget(data_btn)
            
            assets_btn = QPushButton("Assets")
            assets_btn.clicked.connect(self.detect_asset_files)
            auto_row1.addWidget(assets_btn)
            
            auto_row1.addStretch()
            auto_layout.addLayout(auto_row1)
            
            # Additional file types - Row 2
            auto_row2 = QHBoxLayout()
            
            docs_btn = QPushButton("Documentation")
            docs_btn.clicked.connect(self.detect_documentation_files)
            auto_row2.addWidget(docs_btn)
            
            templates_btn = QPushButton("Templates")
            templates_btn.clicked.connect(self.detect_template_files)
            auto_row2.addWidget(templates_btn)
            
            lang_btn = QPushButton("Language Files")
            lang_btn.clicked.connect(self.detect_language_files)
            auto_row2.addWidget(lang_btn)
            
            scripts_btn = QPushButton("Scripts")
            scripts_btn.clicked.connect(self.detect_script_files)
            auto_row2.addWidget(scripts_btn)
            
            auto_row2.addStretch()
            auto_layout.addLayout(auto_row2)
            
            layout.addWidget(auto_group)
            
            # Custom search section
            search_group = QGroupBox("Custom Pattern Search")
            search_layout = QVBoxLayout(search_group)
            
            # Pattern input
            pattern_layout = QHBoxLayout()
            pattern_layout.addWidget(QLabel("Pattern:"))
            
            self.custom_pattern = QLineEdit()
            self.custom_pattern.setPlaceholderText("e.g., *.json, help*.txt, data/**/*.csv")
            pattern_layout.addWidget(self.custom_pattern)
            
            search_btn = QPushButton("Search")
            search_btn.clicked.connect(self.search_custom_pattern)
            pattern_layout.addWidget(search_btn)
            
            search_layout.addLayout(pattern_layout)
            
            # Advanced search buttons
            advanced_layout = QHBoxLayout()
            
            load_patterns_btn = QPushButton("Load Patterns JSON")
            load_patterns_btn.clicked.connect(self.load_custom_patterns)
            advanced_layout.addWidget(load_patterns_btn)
            
            find_unused_btn = QPushButton("Find Unused Files")
            find_unused_btn.clicked.connect(self.find_unused_files)
            advanced_layout.addWidget(find_unused_btn)
            
            advanced_layout.addStretch()
            search_layout.addLayout(advanced_layout)
            
            layout.addWidget(search_group)
            
            # Hidden imports section
            imports_group = QGroupBox("Hidden Imports")
            imports_layout = QVBoxLayout(imports_group)
            
            self.hidden_imports = QTextEdit()
            self.hidden_imports.setPlaceholderText("Enter hidden imports, one per line (e.g., pandas, numpy)")
            self.hidden_imports.setMaximumHeight(80)
            imports_layout.addWidget(self.hidden_imports)
            
            imports_buttons = QHBoxLayout()
            
            detect_imports_btn = QPushButton("Auto-detect Imports")
            detect_imports_btn.clicked.connect(self.auto_detect_imports)
            imports_buttons.addWidget(detect_imports_btn)
            
            common_imports_btn = QPushButton("Add Common Imports")
            common_imports_btn.clicked.connect(self.add_common_imports)
            imports_buttons.addWidget(common_imports_btn)
            
            imports_buttons.addStretch()
            imports_layout.addLayout(imports_buttons)
            
            layout.addWidget(imports_group)
            layout.addStretch()
            
        def create_build_tab(self):
            """Create build and output tab"""
            tab = QWidget()
            self.tab_widget.addTab(tab, "Build & Output")
            
            layout = QVBoxLayout(tab)
            
            # Build command preview
            preview_group = QGroupBox("Build Command Preview")
            preview_layout = QVBoxLayout(preview_group)
            
            self.command_preview = QTextEdit()
            self.command_preview.setReadOnly(True)
            self.command_preview.setMaximumHeight(120)
            self.command_preview.setPlaceholderText("Build command will appear here...")
            preview_layout.addWidget(self.command_preview)
            
            preview_buttons = QHBoxLayout()
            
            update_preview_btn = QPushButton("Update Preview")
            update_preview_btn.clicked.connect(self.update_command_preview)
            preview_buttons.addWidget(update_preview_btn)
            
            copy_cmd_btn = QPushButton("Copy Command")
            copy_cmd_btn.clicked.connect(self.copy_command)
            preview_buttons.addWidget(copy_cmd_btn)
            
            save_config_btn = QPushButton("Save Config")
            save_config_btn.clicked.connect(self.save_config)
            preview_buttons.addWidget(save_config_btn)
            
            load_config_btn = QPushButton("Load Config")
            load_config_btn.clicked.connect(self.load_config)
            preview_buttons.addWidget(load_config_btn)
            
            preview_buttons.addStretch()
            preview_layout.addLayout(preview_buttons)
            
            layout.addWidget(preview_group)
            
            # Build controls
            build_controls = QHBoxLayout()
            
            quick_build_btn = QPushButton("Quick Build")
            quick_build_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }")
            quick_build_btn.clicked.connect(self.quick_build)
            build_controls.addWidget(quick_build_btn)
            
            self.build_btn = QPushButton("Build Application")
            self.build_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; font-weight: bold; }")
            self.build_btn.clicked.connect(self.start_build)
            build_controls.addWidget(self.build_btn)
            
            build_controls.addStretch()
            layout.addLayout(build_controls)
            
            # Output area
            output_group = QGroupBox("Build Output")
            output_layout = QVBoxLayout(output_group)
            
            self.output_text = QTextEdit()
            self.output_text.setReadOnly(True)
            self.output_text.setFont(QFont("Consolas", 9))
            output_layout.addWidget(self.output_text)
            
            # Progress bar and status
            status_layout = QHBoxLayout()
            
            self.progress_bar = QProgressBar()
            self.progress_bar.setVisible(False)
            status_layout.addWidget(self.progress_bar)
            
            self.status_label = QLabel("Ready to build")
            status_layout.addWidget(self.status_label)
            
            output_layout.addLayout(status_layout)
            
            # Output controls
            output_controls = QHBoxLayout()
            
            clear_output_btn = QPushButton("Clear Output")
            clear_output_btn.clicked.connect(self.clear_output)
            output_controls.addWidget(clear_output_btn)
            
            save_log_btn = QPushButton("Save Log")
            save_log_btn.clicked.connect(self.save_build_log)
            output_controls.addWidget(save_log_btn)
            
            open_dist_btn = QPushButton("Open Dist Folder")
            open_dist_btn.clicked.connect(self.open_dist_folder)
            output_controls.addWidget(open_dist_btn)
            
            output_controls.addStretch()
            output_layout.addLayout(output_controls)
            
            layout.addWidget(output_group)
            
        def show_splash_timeout_help(self):
            """Show help for splash timeout feature"""
            help_text = """Splash Screen Timeout Help:

• Timeout Value: Duration in milliseconds (1000ms = 1 second)
• Default: 5000ms (5 seconds)
• Range: 1000-30000ms recommended

Special Values:
• 0: Splash screen stays until user closes it manually
• Empty: Uses PyInstaller default (no timeout)

Examples:
• 3000 = 3 seconds (quick startup)
• 5000 = 5 seconds (standard)
• 8000 = 8 seconds (slower systems)
• 0 = Manual close only

Note: The splash screen will automatically close when your application's main window appears, regardless of timeout."""
            
            QMessageBox.information(self, "Splash Timeout Help", help_text)
        
        def auto_set_splash_timeout(self):
            """Automatically set splash timeout based on project complexity"""
            try:
                # Calculate project size and complexity
                main_script = self.main_script.text().strip()
                file_count = self.files_list.count()
                import_count = len([imp for imp in self.hidden_imports.toPlainText().split('\n') if imp.strip()])
                
                # Base timeout
                timeout = 3000  # 3 seconds base
                
                # Add time based on file count
                timeout += min(file_count * 200, 2000)  # Max 2 seconds for files
                
                # Add time based on imports
                timeout += min(import_count * 100, 1500)  # Max 1.5 seconds for imports
                
                # Check main script size if available
                if main_script and os.path.exists(main_script):
                    file_size = os.path.getsize(main_script)
                    if file_size > 100000:  # Large script (>100KB)
                        timeout += 1000
                    elif file_size > 50000:  # Medium script (>50KB)
                        timeout += 500
                
                # Cap the timeout
                timeout = min(timeout, 10000)  # Max 10 seconds
                timeout = max(timeout, 2000)   # Min 2 seconds
                
                self.splash_timeout.setText(str(timeout))
                self.show_info_message("Auto Timeout", f"Set splash timeout to {timeout}ms based on project complexity")
                
            except Exception as e:
                self.show_error_message("Auto Timeout", f"Error calculating timeout: {e}")
        
        def browse_main_script(self):
            """Browse for main script file"""
            filename, _ = QFileDialog.getOpenFileName(
                self, "Select Main Script", "", "Python Files (*.py);;All Files (*)"
            )
            if filename:
                self.main_script.setText(filename)
                
        def auto_detect_main(self):
            """Auto-detect main entry point"""
            import glob
            main_files = []
            patterns = ["main.py", "app.py", "__main__.py", "*.py"]
            
            for pattern in patterns[:3]:  # Check exact filenames first
                if os.path.exists(pattern):
                    main_files.append(pattern)
            
            # If no exact matches, find all .py files
            if not main_files:
                main_files = glob.glob("*.py")
            
            if len(main_files) == 1:
                self.main_script.setText(main_files[0])
                self.show_info_message("Auto-detect", f"Found main file: {main_files[0]}")
            elif len(main_files) > 1:
                self.show_file_selection_dialog(main_files, "Select Main Script", self.main_script)
            else:
                self.show_info_message("Auto-detect", "No main files found. Please select manually.")
        
        def browse_icon(self):
            """Browse for icon file"""
            filename, _ = QFileDialog.getOpenFileName(
                self, "Select Icon File", "", 
                "Icon Files (*.ico *.png *.jpg);;ICO Files (*.ico);;PNG Files (*.png);;All Files (*)"
            )
            if filename:
                self.icon_file.setText(filename)
        
        def auto_find_icon(self):
            """Auto-find icon files and show all available options"""
            # Use the enhanced icon search to find all available icons
            icon_files = self.builder.find_icon_files()
            
            if not icon_files:
                # Manual search for common icon patterns as fallback
                icon_patterns = ["*.ico", "icon.png", "app.ico", "main.ico", "logo.ico"]
                found_icons = []
                for pattern in icon_patterns:
                    found_icons.extend(glob.glob(pattern))
                icon_files = found_icons
            
            if len(icon_files) == 1:
                # Single file found, set it directly
                self.icon_file.setText(icon_files[0])
                self.show_info_message("Auto-find", f"Found icon: {icon_files[0]}")
            elif len(icon_files) > 1:
                # Multiple files found, show selection dialog
                self.show_file_selection_dialog(icon_files, "Select Icon File", self.icon_file)
            else:
                self.show_info_message("Auto-find", "No icon files found")
        
        def show_file_selection_dialog(self, files, title, target_field):
            """Show a dialog to select from multiple found files"""
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QDialogButtonBox
            
            dialog = QDialog(self)
            dialog.setWindowTitle(title)
            dialog.setModal(True)
            dialog.resize(500, 150)
            
            layout = QVBoxLayout(dialog)
            
            # Information label
            info_label = QLabel(f"Found {len(files)} files. Please select one:")
            layout.addWidget(info_label)
            
            # Combo box with files
            combo = QComboBox()
            combo.addItems(files)
            layout.addWidget(combo)
            
            # Buttons
            button_box = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
            )
            button_box.accepted.connect(dialog.accept)
            button_box.rejected.connect(dialog.reject)
            layout.addWidget(button_box)
            
            # Show dialog and handle result
            if dialog.exec() == QDialog.DialogCode.Accepted:
                selected_file = combo.currentText()
                target_field.setText(selected_file)
                self.show_info_message("File Selected", f"Selected: {selected_file}")
        
        def show_multi_file_selection_dialog(self, files, title):
            """Show a dialog to select multiple files from a list"""
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QListWidget, QDialogButtonBox, QAbstractItemView
            
            dialog = QDialog(self)
            dialog.setWindowTitle(title)
            dialog.setModal(True)
            dialog.resize(600, 400)
            
            layout = QVBoxLayout(dialog)
            
            # Information label
            info_label = QLabel(f"Found {len(files)} files. Select which ones to add (Ctrl+click for multiple):")
            layout.addWidget(info_label)
            
            # List widget with files
            file_list = QListWidget()
            file_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
            file_list.addItems(files)
            # Select all by default
            file_list.selectAll()
            layout.addWidget(file_list)
            
            # Buttons
            button_layout = QHBoxLayout()
            
            select_all_btn = QPushButton("Select All")
            select_all_btn.clicked.connect(file_list.selectAll)
            button_layout.addWidget(select_all_btn)
            
            select_none_btn = QPushButton("Select None")
            select_none_btn.clicked.connect(file_list.clearSelection)
            button_layout.addWidget(select_none_btn)
            
            button_layout.addStretch()
            layout.addLayout(button_layout)
            
            button_box = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
            )
            button_box.accepted.connect(dialog.accept)
            button_box.rejected.connect(dialog.reject)
            layout.addWidget(button_box)
            
            # Show dialog and handle result
            if dialog.exec() == QDialog.DialogCode.Accepted:
                selected_items = file_list.selectedItems()
                selected_files = [item.text() for item in selected_items]
                
                # Check for duplicates before adding
                existing_items = [self.files_list.item(i).text() for i in range(self.files_list.count())]
                
                added_count = 0
                for file_path in selected_files:
                    if file_path not in existing_items:
                        self.files_list.addItem(file_path)
                        added_count += 1
                
                if added_count > 0:
                    self.show_info_message("Files Added", f"Added {added_count} files to the list")
                else:
                    self.show_info_message("No Files Added", "All selected files were already in the list")
        
        def browse_splash(self):
            """Browse for splash screen file"""
            filename, _ = QFileDialog.getOpenFileName(
                self, "Select Splash Screen", "", 
                "Image Files (*.png *.jpg *.bmp);;PNG Files (*.png);;All Files (*)"
            )
            if filename:
                self.splash_file.setText(filename)
        
        def auto_find_splash(self):
            """Auto-find splash screen files"""
            splash_files = self.builder.find_splash_files()
            
            if len(splash_files) == 1:
                # Single file found, set it directly
                self.splash_file.setText(splash_files[0])
                self.show_info_message("Auto-find", f"Found splash: {splash_files[0]}")
            elif len(splash_files) > 1:
                # Multiple files found, show selection dialog
                self.show_file_selection_dialog(splash_files, "Select Splash Screen File", self.splash_file)
            else:
                self.show_info_message("Auto-find", "No splash files found")
        
        def convert_icon_to_splash(self):
            """Convert the current icon to PNG for splash screen use"""
            icon_path = self.icon_file.text().strip()
            if not icon_path:
                self.show_warning_message("Convert ICO", "Please select an icon file first")
                return
            
            if not icon_path.lower().endswith('.ico'):
                self.show_warning_message("Convert ICO", "Selected file is not an ICO file")
                return
            
            try:
                import os
                base_name = os.path.splitext(os.path.basename(icon_path))[0]
                output_path = f"{base_name}_splash.png"
                
                result = self.builder.convert_ico_to_png(icon_path, output_path)
                if result:
                    self.splash_file.setText(result)
                    self.show_info_message("Convert ICO", f"Icon converted successfully!\nSplash screen set to: {result}")
                else:
                    self.show_error_message("Convert ICO", "Failed to convert icon")
            except Exception as e:
                self.show_error_message("Convert ICO", f"Error converting icon: {e}")
        
        def convert_all_icons(self):
            """Convert all ICO files found in the project to PNG"""
            try:
                converted_files = self.builder.find_and_convert_icons_for_splash()
                if converted_files:
                    file_list = "\n".join(converted_files)
                    message = f"Converted {len(converted_files)} ICO files:\n{file_list}"
                    
                    if len(converted_files) == 1:
                        reply = QMessageBox.question(
                            self, "Set Splash", 
                            f"{message}\n\nSet {converted_files[0]} as splash screen?",
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                        )
                        if reply == QMessageBox.StandardButton.Yes:
                            self.splash_file.setText(converted_files[0])
                    else:
                        self.show_info_message("Convert ICOs", f"{message}\n\nSelect one manually for splash screen.")
                else:
                    self.show_info_message("Convert ICOs", "No ICO files found to convert")
            except Exception as e:
                self.show_error_message("Convert ICOs", f"Error converting icons: {e}")
        
        def show_ico_info(self):
            """Show information about ICO files in the project"""
            try:
                import glob
                ico_files = glob.glob("*.ico") + glob.glob("**/*.ico", recursive=True)
                
                if not ico_files:
                    self.show_info_message("ICO Info", "No ICO files found in the project")
                    return
                
                info_text = "ICO Files Information:\n" + "="*40 + "\n"
                
                for ico_file in ico_files:
                    ico_info = self.builder.get_ico_info(ico_file)
                    if ico_info:
                        info_text += f"\nFile: {ico_info['file']}\n"
                        info_text += f"Format: {ico_info['format']}\n"
                        info_text += f"Mode: {ico_info['mode']}\n"
                        info_text += f"Available sizes: {ico_info['sizes']}\n"
                        if ico_info['recommended_splash_size']:
                            info_text += f"Recommended splash size: {ico_info['recommended_splash_size']}\n"
                        info_text += "-" * 30 + "\n"
                
                # Show in a dialog
                dialog = QDialog(self)
                dialog.setWindowTitle("ICO Files Information")
                dialog.setModal(True)
                dialog.resize(600, 400)
                
                layout = QVBoxLayout(dialog)
                text_widget = QTextEdit()
                text_widget.setPlainText(info_text)
                text_widget.setReadOnly(True)
                layout.addWidget(text_widget)
                
                button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
                button_box.accepted.connect(dialog.accept)
                layout.addWidget(button_box)
                
                dialog.exec()
                
            except Exception as e:
                self.show_error_message("ICO Info", f"Error analyzing ICO files: {e}")
        
        def convert_single_ico(self):
            """Convert a single selected ICO file to PNG"""
            try:
                ico_file, _ = QFileDialog.getOpenFileName(
                    self, "Select ICO file to convert",
                    "", "ICO Files (*.ico);;All Files (*)"
                )
                
                if not ico_file:
                    return
                
                import os
                base_name = os.path.splitext(os.path.basename(ico_file))[0]
                output_file, _ = QFileDialog.getSaveFileName(
                    self, "Save PNG as",
                    f"{base_name}_splash.png",
                    "PNG Files (*.png);;All Files (*)"
                )
                
                if output_file:
                    result = self.builder.convert_ico_to_png(ico_file, output_file)
                    if result:
                        reply = QMessageBox.question(
                            self, "Convert Success", 
                            f"ICO converted to PNG successfully!\n\nSet as splash screen?",
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                        )
                        if reply == QMessageBox.StandardButton.Yes:
                            self.splash_file.setText(result)
                    else:
                        self.show_error_message("Convert ICO", "Failed to convert ICO file")
            except Exception as e:
                self.show_error_message("Convert ICO", f"Error converting ICO: {e}")
                
        def add_file(self):
            """Add a file to the files list"""
            filename, _ = QFileDialog.getOpenFileName(
                self, "Add File", "", "All Files (*)"
            )
            if filename:
                self.files_list.addItem(filename)
                
        def add_folder(self):
            """Add a folder to the files list"""
            folder = QFileDialog.getExistingDirectory(self, "Add Folder")
            if folder:
                self.files_list.addItem(f"Folder: {folder}")
                
        def remove_file(self):
            """Remove selected file from the list"""
            for item in self.files_list.selectedItems():
                self.files_list.takeItem(self.files_list.row(item))
        
        def clear_all_files(self):
            """Clear all files from the list"""
            reply = QMessageBox.question(
                self, "Clear Files", 
                "Are you sure you want to clear all files?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.files_list.clear()
        
        # Auto-detection methods
        def detect_help_files(self):
            """Auto-detect help files"""
            help_files = self.builder.find_help_files()
            if len(help_files) == 1:
                # Single file found, add it directly
                self.files_list.addItem(help_files[0])
                self.show_info_message("Auto-detect", f"Found 1 help file: {help_files[0]}")
            elif len(help_files) > 1:
                # Multiple files found, show selection dialog
                self.show_multi_file_selection_dialog(help_files, "Select Help Files to Add")
            else:
                self.show_info_message("Auto-detect", "No help files found")
        
        def detect_tutorial_files(self):
            """Auto-detect tutorial files"""
            tutorial_files = self.builder.find_tutorial_files()
            if len(tutorial_files) == 1:
                # Single file found, add it directly
                self.files_list.addItem(tutorial_files[0])
                self.show_info_message("Auto-detect", f"Found 1 tutorial file: {tutorial_files[0]}")
            elif len(tutorial_files) > 1:
                # Multiple files found, show selection dialog
                self.show_multi_file_selection_dialog(tutorial_files, "Select Tutorial Files to Add")
            else:
                self.show_info_message("Auto-detect", "No tutorial files found")
        
        def detect_config_files(self):
            """Auto-detect config files"""
            config_files = self.builder.find_config_files()
            if len(config_files) == 1:
                self.files_list.addItem(config_files[0])
                self.show_info_message("Auto-detect", f"Found 1 config file: {config_files[0]}")
            elif len(config_files) > 1:
                self.show_multi_file_selection_dialog(config_files, "Select Config Files to Add")
            else:
                self.show_info_message("Auto-detect", "No config files found")
        
        def detect_data_files(self):
            """Auto-detect data files"""
            data_files = self.builder.find_data_files()
            if len(data_files) == 1:
                self.files_list.addItem(data_files[0])
                self.show_info_message("Auto-detect", f"Found 1 data file: {data_files[0]}")
            elif len(data_files) > 1:
                self.show_multi_file_selection_dialog(data_files, "Select Data Files to Add")
            else:
                self.show_info_message("Auto-detect", "No data files found")
        
        def detect_asset_files(self):
            """Auto-detect asset files"""
            asset_files = self.builder.find_asset_files()
            if len(asset_files) == 1:
                self.files_list.addItem(asset_files[0])
                self.show_info_message("Auto-detect", f"Found 1 asset file: {asset_files[0]}")
            elif len(asset_files) > 1:
                self.show_multi_file_selection_dialog(asset_files, "Select Asset Files to Add")
            else:
                self.show_info_message("Auto-detect", "No asset files found")
        
        def detect_documentation_files(self):
            """Auto-detect documentation files"""
            doc_files = self.builder.find_documentation_files()
            if len(doc_files) == 1:
                self.files_list.addItem(doc_files[0])
                self.show_info_message("Auto-detect", f"Found 1 documentation file: {doc_files[0]}")
            elif len(doc_files) > 1:
                self.show_multi_file_selection_dialog(doc_files, "Select Documentation Files to Add")
            else:
                self.show_info_message("Auto-detect", "No documentation files found")
        
        def detect_template_files(self):
            """Auto-detect template files"""
            template_files = self.builder.find_template_files()
            if len(template_files) == 1:
                self.files_list.addItem(template_files[0])
                self.show_info_message("Auto-detect", f"Found 1 template file: {template_files[0]}")
            elif len(template_files) > 1:
                self.show_multi_file_selection_dialog(template_files, "Select Template Files to Add")
            else:
                self.show_info_message("Auto-detect", "No template files found")
        
        def detect_language_files(self):
            """Auto-detect language files"""
            lang_files = self.builder.find_language_files()
            if len(lang_files) == 1:
                self.files_list.addItem(lang_files[0])
                self.show_info_message("Auto-detect", f"Found 1 language file: {lang_files[0]}")
            elif len(lang_files) > 1:
                self.show_multi_file_selection_dialog(lang_files, "Select Language Files to Add")
            else:
                self.show_info_message("Auto-detect", "No language files found")
        
        def detect_script_files(self):
            """Auto-detect script files"""
            script_files = self.builder.find_script_files()
            if len(script_files) == 1:
                self.files_list.addItem(script_files[0])
                self.show_info_message("Auto-detect", f"Found 1 script file: {script_files[0]}")
            elif len(script_files) > 1:
                self.show_multi_file_selection_dialog(script_files, "Select Script Files to Add")
            else:
                self.show_info_message("Auto-detect", "No script files found")
        
        def search_custom_pattern(self):
            """Search for files using custom pattern"""
            pattern = self.custom_pattern.text().strip()
            if not pattern:
                self.show_warning_message("Search", "Please enter a search pattern")
                return
            
            try:
                found_files = self.builder.find_files_by_custom_pattern(pattern)
                if len(found_files) == 1:
                    # Check for duplicates before adding
                    existing_items = [self.files_list.item(i).text() for i in range(self.files_list.count())]
                    if found_files[0] not in existing_items:
                        self.files_list.addItem(found_files[0])
                        self.show_info_message("Custom Search", f"Found and added 1 file: {found_files[0]}")
                    else:
                        self.show_info_message("Custom Search", f"Found 1 file (already in list): {found_files[0]}")
                elif len(found_files) > 1:
                    self.show_multi_file_selection_dialog(found_files, f"Select Files Matching '{pattern}'")
                else:
                    self.show_info_message("Custom Search", f"No files found matching pattern: {pattern}")
            except Exception as e:
                self.show_error_message("Search Error", f"Error searching for pattern: {e}")
        
        def load_custom_patterns(self):
            """Load custom search patterns from JSON file"""
            filename, _ = QFileDialog.getOpenFileName(
                self, "Select Custom Patterns JSON File",
                "", "JSON Files (*.json);;All Files (*)"
            )
            
            if filename:
                try:
                    if self.builder.load_custom_patterns_from_file(filename):
                        self.show_info_message("Load Patterns", "Custom patterns loaded successfully")
                    else:
                        self.show_warning_message("Load Patterns", "Failed to load custom patterns")
                except Exception as e:
                    self.show_error_message("Load Error", f"Error loading patterns file: {e}")
        
        def find_unused_files(self):
            """Find potentially unused files in the project"""
            # This is a placeholder - you could implement logic to find files not referenced in code
            self.show_info_message("Find Unused", "Unused file detection feature coming soon!")
        
        def auto_detect_imports(self):
            """Auto-detect hidden imports from the main script"""
            main_script = self.main_script.text().strip()
            if not main_script:
                self.show_warning_message("Auto-detect Imports", "Please select a main script first")
                return
            
            try:
                import ast
                import os
                
                if not os.path.exists(main_script):
                    self.show_warning_message("Auto-detect Imports", "Main script file not found")
                    return
                
                with open(main_script, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                imports = set()
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.add(alias.name.split('.')[0])
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            imports.add(node.module.split('.')[0])
                
                # Filter out standard library modules (basic list)
                stdlib_modules = {'os', 'sys', 'json', 'time', 'datetime', 're', 'math', 'random', 'collections', 'itertools'}
                third_party_imports = imports - stdlib_modules
                
                if third_party_imports:
                    current_imports = self.hidden_imports.toPlainText()
                    new_imports = '\n'.join(sorted(third_party_imports))
                    if current_imports:
                        self.hidden_imports.setPlainText(current_imports + '\n' + new_imports)
                    else:
                        self.hidden_imports.setPlainText(new_imports)
                    
                    self.show_info_message("Auto-detect Imports", f"Added {len(third_party_imports)} potential hidden imports")
                else:
                    self.show_info_message("Auto-detect Imports", "No third-party imports detected")
                    
            except Exception as e:
                self.show_error_message("Auto-detect Imports", f"Error analyzing imports: {e}")
        
        def add_common_imports(self):
            """Add commonly needed hidden imports"""
            common_imports = [
                "PIL", "numpy", "pandas", "matplotlib", "scipy", "sklearn",
                "requests", "urllib3", "certifi", "charset_normalizer",
                "PyQt6", "tkinter", "sqlite3"
            ]
            
            current_imports = self.hidden_imports.toPlainText()
            new_imports = '\n'.join(common_imports)
            if current_imports:
                self.hidden_imports.setPlainText(current_imports + '\n' + new_imports)
            else:
                self.hidden_imports.setPlainText(new_imports)
            
            self.show_info_message("Add Common Imports", f"Added {len(common_imports)} common hidden imports")
        
        def update_command_preview(self):
            """Update the build command preview"""
            config = self.get_current_config()
            command = self.builder.build_pyinstaller_command(config)
            self.command_preview.setPlainText(" ".join(command))
        
        def copy_command(self):
            """Copy the build command to clipboard"""
            command_text = self.command_preview.toPlainText()
            if command_text:
                try:
                    # Try to use QApplication clipboard
                    clipboard = QApplication.clipboard()
                    clipboard.setText(command_text)
                    self.show_info_message("Copy Command", "Build command copied to clipboard")
                except Exception as e:
                    self.show_info_message("Copy Command", f"Command text:\n{command_text}")
        
        def quick_build(self):
            """Perform quick build with auto-detection"""
            if not self.main_script.text():
                self.auto_detect_main()
            if not self.main_script.text():
                self.show_error_message("Quick Build", "Could not find main script file")
                return
            self.start_build()
        
        def clear_output(self):
            """Clear the output text"""
            self.output_text.clear()
        
        def save_build_log(self):
            """Save build log to file"""
            filename, _ = QFileDialog.getSaveFileName(
                self, "Save Build Log", "build_log.txt", "Text Files (*.txt);;All Files (*)"
            )
            if filename:
                try:
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(self.output_text.toPlainText())
                    self.show_info_message("Save Log", f"Build log saved to {filename}")
                except Exception as e:
                    self.show_error_message("Save Log", f"Error saving log: {e}")
        
        def open_dist_folder(self):
            """Open the dist folder in file explorer"""
            import os
            import subprocess
            import platform
            
            dist_path = "dist"
            if os.path.exists(dist_path):
                try:
                    if platform.system() == "Windows":
                        os.startfile(dist_path)
                    elif platform.system() == "Darwin":  # macOS
                        subprocess.run(["open", dist_path])
                    else:  # Linux
                        subprocess.run(["xdg-open", dist_path])
                except Exception as e:
                    self.show_error_message("Open Folder", f"Error opening dist folder: {e}")
            else:
                self.show_warning_message("Open Folder", "Dist folder not found. Build the application first.")
        
        def get_current_config(self):
            """Get current configuration from the UI"""
            # Get date format choice
            date_format_text = self.date_format.currentText()
            date_format = date_format_text.split(" ")[0]  # Extract format before example
            
            # Generate versioned paths if enabled
            include_date = self.include_date.isChecked()
            output_paths = generate_output_paths(
                self.program_name.text() or "Application",
                self.version.text(),
                include_date
            ) if include_date else {}
            
            config = {
                "program_name": self.program_name.text(),
                "version": self.version.text(),
                "main_entry": self.main_script.text(),
                "icon": self.icon_file.text(),
                "splash": self.splash_file.text(),
                "splash_timeout": self.splash_timeout.text(),
                "onefile": self.one_file.isChecked(),
                "windowed": self.windowed.isChecked(),
                "clean": self.clean_build.isChecked(),
                "debug": self.debug.isChecked(),
                "uac_admin": self.uac_admin.isChecked(),
                "hidden_imports": [imp.strip() for imp in self.hidden_imports.toPlainText().split('\n') if imp.strip()],
                "add_data": []
            }
            
            # Add versioned output paths if date is included
            if include_date and output_paths:
                config.update({
                    "distpath": output_paths["distpath"],
                    "workpath": output_paths["workpath"], 
                    "specpath": output_paths["specpath"],
                    "versioned_name": output_paths["dist_name"]
                })
            
            # Process additional files
            import os
            path_separator = ";" if os.name == "nt" else ":"
            
            for i in range(self.files_list.count()):
                item_text = self.files_list.item(i).text()
                if item_text.startswith("Folder: "):
                    folder_path = item_text[8:]  # Remove "Folder: " prefix
                    config["add_data"].append(f"{folder_path}{path_separator}.")
                elif os.path.isfile(item_text):
                    config["add_data"].append(f"{item_text}{path_separator}.")
                elif os.path.isdir(item_text):
                    config["add_data"].append(f"{item_text}{path_separator}.")
            
            return config
        
        def save_config(self):
            """Save configuration to JSON file"""
            filename, _ = QFileDialog.getSaveFileName(
                self, "Save Configuration", "build_config.json", "JSON Files (*.json);;All Files (*)"
            )
            if filename:
                try:
                    import json
                    config = self.get_current_config()
                    
                    # Also save UI state
                    ui_state = {
                        "files_list": [self.files_list.item(i).text() for i in range(self.files_list.count())]
                    }
                    config["ui_state"] = ui_state
                    
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(config, f, indent=2)
                    
                    self.show_info_message("Save Config", f"Configuration saved to {filename}")
                except Exception as e:
                    self.show_error_message("Save Config", f"Error saving configuration: {e}")
        
        def load_config(self):
            """Load configuration from JSON file"""
            filename, _ = QFileDialog.getOpenFileName(
                self, "Load Configuration", "", "JSON Files (*.json);;All Files (*)"
            )
            if filename:
                try:
                    import json
                    with open(filename, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    
                    # Set UI values
                    self.program_name.setText(config.get("program_name", ""))
                    self.version.setText(config.get("version", ""))
                    self.main_script.setText(config.get("main_entry", ""))
                    self.icon_file.setText(config.get("icon", ""))
                    self.splash_file.setText(config.get("splash", ""))
                    self.splash_timeout.setText(config.get("splash_timeout", "5000"))
                    
                    self.one_file.setChecked(config.get("onefile", True))
                    self.windowed.setChecked(config.get("windowed", True))
                    self.clean_build.setChecked(config.get("clean", True))
                    self.debug.setChecked(config.get("debug", False))
                    self.uac_admin.setChecked(config.get("uac_admin", False))
                    
                    # Set hidden imports
                    hidden_imports = config.get("hidden_imports", [])
                    self.hidden_imports.setPlainText('\n'.join(hidden_imports))
                    
                    # Restore files list
                    self.files_list.clear()
                    if "ui_state" in config and "files_list" in config["ui_state"]:
                        for file_item in config["ui_state"]["files_list"]:
                            self.files_list.addItem(file_item)
                    
                    self.show_info_message("Load Config", f"Configuration loaded from {filename}")
                except Exception as e:
                    self.show_error_message("Load Config", f"Error loading configuration: {e}")
                
        def start_build(self):
            """Start the build process"""
            if not self.main_script.text():
                self.show_error_message("Build Error", "Please select a main script file")
                return
                
            config = self.get_current_config()
            command = self.builder.build_pyinstaller_command(config)
            
            # Update command preview
            self.command_preview.setPlainText(" ".join(command))
            
            # Clear output and prepare UI
            self.output_text.clear()
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
            self.build_btn.setEnabled(False)
            self.build_btn.setText("Building...")
            self.status_label.setText("Building application...")
            
            # Create and start build thread
            self.build_thread = BuildThread(command, self.builder)
            self.build_thread.progress_signal.connect(self.on_build_progress)
            self.build_thread.finished_signal.connect(self.on_build_finished)
            self.build_thread.start()
        
        def on_build_progress(self, message):
            """Handle build progress updates"""
            self.output_text.append(message)
            self.output_text.ensureCursorVisible()
            if len(message) > 50:
                self.status_label.setText(message[:50] + "...")
            else:
                self.status_label.setText(message)
        
        def on_build_finished(self, success, message, output):
            """Handle build completion"""
            self.progress_bar.setVisible(False)
            self.build_btn.setEnabled(True)
            self.build_btn.setText("Build Application")
            
            # Show completion message
            self.output_text.append("\n" + "="*50)
            self.output_text.append(message)
            self.output_text.append("="*50)
            
            if success:
                self.status_label.setText("Build completed successfully!")
                QMessageBox.information(self, "Build Complete", "Application built successfully!")
            else:
                self.status_label.setText("Build failed!")
                QMessageBox.critical(self, "Build Failed", f"Build failed: {message}")
        
        # Utility methods for showing messages
        def show_info_message(self, title, message):
            QMessageBox.information(self, title, message)
        
        def show_warning_message(self, title, message):
            QMessageBox.warning(self, title, message)
        
        def preview_build_name(self):
            """Preview the generated build name"""
            try:
                # Get current settings
                program_name = self.program_name.text() or "Application"
                version = self.version.text()
                include_date = self.include_date.isChecked()
                date_format_text = self.date_format.currentText()
                date_format = date_format_text.split(" ")[0]  # Extract format before example
                
                # Generate preview
                if include_date:
                    output_paths = generate_output_paths(program_name, version, include_date)
                    versioned_name = output_paths["dist_name"]
                    
                    preview_text = f"""Build Name Preview:

Final executable name: {versioned_name}.exe
Distribution folder: {output_paths["distpath"]}
Build folder: {output_paths["workpath"]}
Spec folder: {output_paths["specpath"]}

Example current date: {datetime.now().strftime(date_format)}"""
                else:
                    base_name = generate_versioned_name(program_name, version, False)
                    preview_text = f"""Build Name Preview:

Final executable name: {base_name}.exe
Distribution folder: dist
Build folder: build
Spec folder: (default)

Date stamping is disabled."""
                
                QMessageBox.information(self, "Build Name Preview", preview_text)
                
            except Exception as e:
                self.show_error_message("Preview Error", f"Error generating preview: {e}")
        
        def show_error_message(self, title, message):
            QMessageBox.critical(self, title, message)
    
elif GUI_BACKEND == "tkinter":
    # Tkinter implementation removed - PyQt6 is preferred
    class TkinterBuildGUI:
        def __init__(self):
            print("Tkinter GUI not implemented. Please use PyQt6 or console mode.")
            
        def run(self):
            print("Tkinter GUI not available. Install PyQt6 for GUI mode.")
            return False
    class TkinterBuildGUI:
        """Tkinter-based GUI for PyInstaller Build Tool"""
        
        def __init__(self):
            self.builder = EnhancedConsoleBuilder()
            self.root = tk.Tk()
            self.setup_ui()
            
        def setup_ui(self):
            self.root.title("PyInstaller Build Tool")
            self.root.geometry("900x700")
            
            # Create notebook for tabs
            notebook = ttk.Notebook(self.root)
            notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Basic tab
            self.create_basic_tab(notebook)
            
            # Files tab
            self.create_files_tab(notebook)
            
            # Build tab
            self.create_build_tab(notebook)
            
            # Footer buttons
            self.create_footer()
            
        def create_basic_tab(self, notebook):
            """Create basic configuration tab"""
            frame = ttk.Frame(notebook)
            notebook.add(frame, text="Basic Configuration")
            
            # Program info
            info_frame = ttk.LabelFrame(frame, text="Program Information")
            info_frame.pack(fill=tk.X, padx=5, pady=5)
            
            ttk.Label(info_frame, text="Program Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
            self.program_name_var = tk.StringVar()
            ttk.Entry(info_frame, textvariable=self.program_name_var, width=40).grid(row=0, column=1, padx=5, pady=2)
            
            ttk.Label(info_frame, text="Version:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
            self.version_var = tk.StringVar()
            ttk.Entry(info_frame, textvariable=self.version_var, width=40).grid(row=1, column=1, padx=5, pady=2)
            
            # Main entry
            entry_frame = ttk.LabelFrame(frame, text="Main Entry Point")
            entry_frame.pack(fill=tk.X, padx=5, pady=5)
            
            ttk.Label(entry_frame, text="Python File:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
            self.main_entry_var = tk.StringVar()
            ttk.Entry(entry_frame, textvariable=self.main_entry_var, width=50).grid(row=0, column=1, padx=5, pady=2)
            
            ttk.Button(entry_frame, text="Browse", command=self.browse_main_entry).grid(row=0, column=2, padx=5, pady=2)
            ttk.Button(entry_frame, text="Auto-detect", command=self.auto_detect_main).grid(row=0, column=3, padx=5, pady=2)
            
            # Build options
            options_frame = ttk.LabelFrame(frame, text="Build Options")
            options_frame.pack(fill=tk.X, padx=5, pady=5)
            
            self.onefile_var = tk.BooleanVar(value=True)
            self.windowed_var = tk.BooleanVar(value=True)
            self.clean_var = tk.BooleanVar(value=True)
            self.debug_var = tk.BooleanVar(value=False)
            
            ttk.Checkbutton(options_frame, text="One File", variable=self.onefile_var).grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
            ttk.Checkbutton(options_frame, text="Windowed (No Console)", variable=self.windowed_var).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
            ttk.Checkbutton(options_frame, text="Clean Build", variable=self.clean_var).grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
            ttk.Checkbutton(options_frame, text="Debug Mode", variable=self.debug_var).grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
            
            # Icon and splash
            visual_frame = ttk.LabelFrame(frame, text="Visual Assets")
            visual_frame.pack(fill=tk.X, padx=5, pady=5)
            
            ttk.Label(visual_frame, text="Icon File:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
            self.icon_var = tk.StringVar()
            ttk.Entry(visual_frame, textvariable=self.icon_var, width=50).grid(row=0, column=1, padx=5, pady=2)
            ttk.Button(visual_frame, text="Browse", command=self.browse_icon).grid(row=0, column=2, padx=5, pady=2)
            
            ttk.Label(visual_frame, text="Splash Screen:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
            self.splash_var = tk.StringVar()
            ttk.Entry(visual_frame, textvariable=self.splash_var, width=50).grid(row=1, column=1, padx=5, pady=2)
            ttk.Button(visual_frame, text="Browse", command=self.browse_splash).grid(row=1, column=2, padx=5, pady=2)
            ttk.Button(visual_frame, text="Convert ICO", command=self.convert_icon_to_splash).grid(row=1, column=3, padx=5, pady=2)
            
            # ICO conversion section
            ico_frame = ttk.LabelFrame(visual_frame, text="ICO to PNG Conversion")
            ico_frame.grid(row=2, column=0, columnspan=4, sticky=tk.EW, padx=5, pady=5)
            
            ttk.Button(ico_frame, text="Convert All ICOs", command=self.convert_all_icons).pack(side=tk.LEFT, padx=5, pady=5)
            ttk.Button(ico_frame, text="Show ICO Info", command=self.show_ico_info).pack(side=tk.LEFT, padx=5, pady=5)
            ttk.Button(ico_frame, text="Convert Single ICO", command=self.convert_single_ico).pack(side=tk.LEFT, padx=5, pady=5)
            
        def create_files_tab(self, notebook):
            """Create files and resources tab"""
            frame = ttk.Frame(notebook)
            notebook.add(frame, text="Files & Resources")
            
            # Additional files
            files_frame = ttk.LabelFrame(frame, text="Additional Files")
            files_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # List of additional files
            self.files_listbox = tk.Listbox(files_frame, height=10)
            scrollbar = ttk.Scrollbar(files_frame, orient=tk.VERTICAL)
            self.files_listbox.config(yscrollcommand=scrollbar.set)
            scrollbar.config(command=self.files_listbox.yview)
            
            self.files_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
            
            # Buttons for file management
            files_buttons_frame = ttk.Frame(files_frame)
            files_buttons_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
            
            ttk.Button(files_buttons_frame, text="Add Files", command=self.add_files).pack(side=tk.LEFT, padx=2)
            ttk.Button(files_buttons_frame, text="Add Folder", command=self.add_folder).pack(side=tk.LEFT, padx=2)
            ttk.Button(files_buttons_frame, text="Remove Selected", command=self.remove_selected).pack(side=tk.LEFT, padx=2)
            ttk.Button(files_buttons_frame, text="Clear All", command=self.clear_files).pack(side=tk.LEFT, padx=2)
            
            # Auto-detection buttons
            auto_frame = ttk.LabelFrame(frame, text="Auto-Detection & Manual Search")
            auto_frame.pack(fill=tk.X, padx=5, pady=5)
            
            # Row 1: Common auto-detection
            auto_row1 = ttk.Frame(auto_frame)
            auto_row1.pack(fill=tk.X, padx=5, pady=2)
            ttk.Button(auto_row1, text="Help Files", command=self.detect_help_files).pack(side=tk.LEFT, padx=2)
            ttk.Button(auto_row1, text="Tutorial Files", command=self.detect_tutorial_files).pack(side=tk.LEFT, padx=2)
            ttk.Button(auto_row1, text="Config Files", command=self.detect_config_files).pack(side=tk.LEFT, padx=2)
            ttk.Button(auto_row1, text="Data Files", command=self.detect_data_files).pack(side=tk.LEFT, padx=2)
            ttk.Button(auto_row1, text="Assets", command=self.detect_asset_files).pack(side=tk.LEFT, padx=2)
            
            # Row 2: Additional file types
            auto_row2 = ttk.Frame(auto_frame)
            auto_row2.pack(fill=tk.X, padx=5, pady=2)
            ttk.Button(auto_row2, text="Documentation", command=self.detect_documentation_files).pack(side=tk.LEFT, padx=2)
            ttk.Button(auto_row2, text="Templates", command=self.detect_template_files).pack(side=tk.LEFT, padx=2)
            ttk.Button(auto_row2, text="Language Files", command=self.detect_language_files).pack(side=tk.LEFT, padx=2)
            ttk.Button(auto_row2, text="Scripts", command=self.detect_script_files).pack(side=tk.LEFT, padx=2)
            
            # Row 3: Manual search and custom patterns
            manual_frame = ttk.LabelFrame(auto_frame, text="Manual Search")
            manual_frame.pack(fill=tk.X, padx=5, pady=5)
            
            # Custom pattern input
            pattern_frame = ttk.Frame(manual_frame)
            pattern_frame.pack(fill=tk.X, padx=5, pady=2)
            ttk.Label(pattern_frame, text="Pattern:").pack(side=tk.LEFT)
            self.custom_pattern_var = tk.StringVar()
            pattern_entry = ttk.Entry(pattern_frame, textvariable=self.custom_pattern_var, width=30)
            pattern_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            ttk.Button(pattern_frame, text="Search", command=self.search_custom_pattern).pack(side=tk.LEFT, padx=2)
            
            # File buttons and JSON upload
            file_frame = ttk.Frame(manual_frame)
            file_frame.pack(fill=tk.X, padx=5, pady=2)
            ttk.Button(file_frame, text="Load Patterns JSON", command=self.load_custom_patterns).pack(side=tk.LEFT, padx=2)
            ttk.Button(file_frame, text="Add Individual Files", command=self.add_individual_files).pack(side=tk.LEFT, padx=2)
            ttk.Button(file_frame, text="Clear All", command=self.clear_all_files).pack(side=tk.LEFT, padx=2)
            
        def create_build_tab(self, notebook):
            """Create build execution tab"""
            frame = ttk.Frame(notebook)
            notebook.add(frame, text="Build")
            
            # Command preview
            preview_frame = ttk.LabelFrame(frame, text="Build Command Preview")
            preview_frame.pack(fill=tk.X, padx=5, pady=5)
            
            self.command_text = scrolledtext.ScrolledText(preview_frame, height=5, wrap=tk.WORD)
            self.command_text.pack(fill=tk.X, padx=5, pady=5)
            
            ttk.Button(preview_frame, text="Update Preview", command=self.update_command_preview).pack(pady=5)
            
            # Build output
            output_frame = ttk.LabelFrame(frame, text="Build Output")
            output_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            self.output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, state=tk.DISABLED)
            self.output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Progress bar
            self.progress_var = tk.StringVar(value="Ready to build")
            self.progress_label = ttk.Label(output_frame, textvariable=self.progress_var)
            self.progress_label.pack(pady=2)
            
        def create_footer(self):
            """Create footer with action buttons"""
            footer_frame = ttk.Frame(self.root)
            footer_frame.pack(fill=tk.X, padx=10, pady=5)
            
            ttk.Button(footer_frame, text="Load Config", command=self.load_config).pack(side=tk.LEFT, padx=5)
            ttk.Button(footer_frame, text="Save Config", command=self.save_config).pack(side=tk.LEFT, padx=5)
            
            ttk.Button(footer_frame, text="Quick Build", command=self.quick_build).pack(side=tk.RIGHT, padx=5)
            self.build_button = ttk.Button(footer_frame, text="Build", command=self.start_build)
            self.build_button.pack(side=tk.RIGHT, padx=5)
            
        # Event handlers
        def browse_main_entry(self):
            filename = filedialog.askopenfilename(title="Select Main Python File", filetypes=[("Python files", "*.py")])
            if filename:
                self.main_entry_var.set(filename)
                
        def auto_detect_main(self):
            patterns = ["main.py", "app.py", "__main__.py", "*.py"]
            for pattern in patterns:
                files = glob.glob(pattern)
                if files:
                    self.main_entry_var.set(files[0])
                    messagebox.showinfo("Auto-detect", f"Found: {files[0]}")
                    return
            messagebox.showinfo("Auto-detect", "No main file found")
            
        def browse_icon(self):
            filename = filedialog.askopenfilename(title="Select Icon File", filetypes=[("Icon files", "*.ico *.png")])
            if filename:
                self.icon_var.set(filename)
                
        def browse_splash(self):
            filename = filedialog.askopenfilename(title="Select Splash Screen", filetypes=[("Image files", "*.png *.jpg *.bmp")])
            if filename:
                self.splash_var.set(filename)
        
        def convert_icon_to_splash(self):
            """Convert the current icon to PNG for splash screen use"""
            icon_path = self.icon_var.get().strip()
            if not icon_path:
                messagebox.showwarning("Convert ICO", "Please select an icon file first")
                return
            
            if not icon_path.lower().endswith('.ico'):
                messagebox.showwarning("Convert ICO", "Selected file is not an ICO file")
                return
            
            try:
                # Generate output filename
                base_name = os.path.splitext(os.path.basename(icon_path))[0]
                output_path = f"{base_name}_splash.png"
                
                result = self.builder.convert_ico_to_png(icon_path, output_path)
                if result:
                    self.splash_var.set(result)
                    messagebox.showinfo("Convert ICO", f"Icon converted successfully!\nSplash screen set to: {result}")
                else:
                    messagebox.showerror("Convert ICO", "Failed to convert icon")
            except Exception as e:
                messagebox.showerror("Convert ICO", f"Error converting icon: {e}")
        
        def convert_all_icons(self):
            """Convert all ICO files found in the project to PNG for splash screens"""
            try:
                if not PIL_AVAILABLE:
                    messagebox.showerror("Convert ICOs", "PIL/Pillow is required for ICO conversion.\nInstall with: pip install Pillow")
                    return
                
                converted_files = self.builder.find_and_convert_icons_for_splash()
                if converted_files:
                    file_list = "\\n".join(converted_files)
                    messagebox.showinfo("Convert ICOs", f"Converted {len(converted_files)} ICO files:\\n{file_list}")
                    
                    # Ask if user wants to set one as splash screen
                    if len(converted_files) == 1:
                        if messagebox.askyesno("Set Splash", f"Set {converted_files[0]} as splash screen?"):
                            self.splash_var.set(converted_files[0])
                    elif len(converted_files) > 1:
                        messagebox.showinfo("Multiple Files", "Multiple PNG files created. Select one manually for splash screen.")
                else:
                    messagebox.showinfo("Convert ICOs", "No ICO files found to convert")
                    
            except Exception as e:
                messagebox.showerror("Convert ICOs", f"Error converting icons: {e}")
        
        def show_ico_info(self):
            """Show information about ICO files in the project"""
            try:
                if not PIL_AVAILABLE:
                    messagebox.showwarning("ICO Info", "PIL/Pillow is required to analyze ICO files")
                    return
                
                # Find ICO files
                ico_files = glob.glob("*.ico") + glob.glob("**/*.ico", recursive=True)
                
                if not ico_files:
                    messagebox.showinfo("ICO Info", "No ICO files found in the project")
                    return
                
                info_text = "ICO Files Information:\\n" + "="*40 + "\\n"
                
                for ico_file in ico_files:
                    ico_info = self.builder.get_ico_info(ico_file)
                    if ico_info:
                        info_text += f"\\nFile: {ico_info['file']}\\n"
                        info_text += f"Format: {ico_info['format']}\\n"
                        info_text += f"Mode: {ico_info['mode']}\\n"
                        info_text += f"Available sizes: {ico_info['sizes']}\\n"
                        if ico_info['recommended_splash_size']:
                            info_text += f"Recommended splash size: {ico_info['recommended_splash_size']}\\n"
                        info_text += "-" * 30 + "\\n"
                
                # Show in a scrollable dialog
                info_window = tk.Toplevel(self.root)
                info_window.title("ICO Files Information")
                info_window.geometry("600x400")
                
                text_widget = scrolledtext.ScrolledText(info_window, wrap=tk.WORD)
                text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                text_widget.insert(tk.END, info_text)
                text_widget.config(state=tk.DISABLED)
                
            except Exception as e:
                messagebox.showerror("ICO Info", f"Error analyzing ICO files: {e}")
        
        def convert_single_ico(self):
            """Convert a single selected ICO file to PNG"""
            try:
                ico_file = filedialog.askopenfilename(
                    title="Select ICO file to convert",
                    filetypes=[("ICO files", "*.ico"), ("All files", "*.*")]
                )
                
                if not ico_file:
                    return
                
                # Ask for output location
                base_name = os.path.splitext(os.path.basename(ico_file))[0]
                output_file = filedialog.asksaveasfilename(
                    title="Save PNG as",
                    defaultextension=".png",
                    initialvalue=f"{base_name}_splash.png",
                    filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
                )
                
                if output_file:
                    result = self.builder.convert_ico_to_png(ico_file, output_file)
                    if result:
                        if messagebox.askyesno("Convert Success", f"ICO converted to PNG successfully!\\n\\nSet as splash screen?"):
                            self.splash_var.set(result)
                        messagebox.showinfo("Convert ICO", f"File saved as: {result}")
                    else:
                        messagebox.showerror("Convert ICO", "Failed to convert ICO file")
                        
            except Exception as e:
                messagebox.showerror("Convert ICO", f"Error converting ICO: {e}")
                
        def add_files(self):
            filenames = filedialog.askopenfilenames(title="Select Additional Files")
            for filename in filenames:
                self.files_listbox.insert(tk.END, filename)
                
        def add_folder(self):
            folder = filedialog.askdirectory(title="Select Additional Folder")
            if folder:
                self.files_listbox.insert(tk.END, folder)
                
        def remove_selected(self):
            selected = self.files_listbox.curselection()
            for index in reversed(selected):
                self.files_listbox.delete(index)
                
        def clear_files(self):
            self.files_listbox.delete(0, tk.END)
            
        def detect_help_files(self):
            help_files = self.builder.find_help_files()
            for file in help_files:
                self.files_listbox.insert(tk.END, file)
            messagebox.showinfo("Auto-detect", f"Found {len(help_files)} help files")
            
        def detect_tutorial_files(self):
            tutorial_files = self.builder.find_tutorial_files()
            for file in tutorial_files:
                self.files_listbox.insert(tk.END, file)
            messagebox.showinfo("Auto-detect", f"Found {len(tutorial_files)} tutorial files")
            
        def detect_config_files(self):
            config_files = self.builder.find_config_files()
            for file in config_files:
                self.files_listbox.insert(tk.END, file)
            messagebox.showinfo("Auto-detect", f"Found {len(config_files)} config files")
        
        def detect_data_files(self):
            """Auto-detect data files and add to list"""
            data_files = self.builder.find_data_files()
            for file in data_files:
                self.files_listbox.insert(tk.END, file)
            messagebox.showinfo("Auto-detect", f"Found {len(data_files)} data files")
        
        def detect_asset_files(self):
            """Auto-detect asset files and add to list"""
            asset_files = self.builder.find_asset_files()
            for file in asset_files:
                self.files_listbox.insert(tk.END, file)
            messagebox.showinfo("Auto-detect", f"Found {len(asset_files)} asset files")
        
        def detect_documentation_files(self):
            """Auto-detect documentation files and add to list"""
            doc_files = self.builder.find_documentation_files()
            for file in doc_files:
                self.files_listbox.insert(tk.END, file)
            messagebox.showinfo("Auto-detect", f"Found {len(doc_files)} documentation files")
        
        def detect_template_files(self):
            """Auto-detect template files and add to list"""
            template_files = self.builder.find_template_files()
            for file in template_files:
                self.files_listbox.insert(tk.END, file)
            messagebox.showinfo("Auto-detect", f"Found {len(template_files)} template files")
        
        def detect_language_files(self):
            """Auto-detect language/localization files and add to list"""
            lang_files = self.builder.find_language_files()
            for file in lang_files:
                self.files_listbox.insert(tk.END, file)
            messagebox.showinfo("Auto-detect", f"Found {len(lang_files)} language files")
        
        def detect_script_files(self):
            """Auto-detect script files and add to list"""
            script_files = self.builder.find_script_files()
            for file in script_files:
                self.files_listbox.insert(tk.END, file)
            messagebox.showinfo("Auto-detect", f"Found {len(script_files)} script files")
        
        def search_custom_pattern(self):
            """Search for files using custom pattern"""
            pattern = self.custom_pattern_var.get().strip()
            if not pattern:
                messagebox.showwarning("Search", "Please enter a search pattern")
                return
            
            try:
                found_files = self.builder.find_files_by_custom_pattern(pattern)
                for file in found_files:
                    self.files_listbox.insert(tk.END, file)
                messagebox.showinfo("Custom Search", f"Found {len(found_files)} files matching pattern: {pattern}")
            except Exception as e:
                messagebox.showerror("Search Error", f"Error searching for pattern: {e}")
        
        def load_custom_patterns(self):
            """Load custom search patterns from JSON file"""
            filename = filedialog.askopenfilename(
                title="Select Custom Patterns JSON File",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                try:
                    if self.builder.load_custom_patterns_from_file(filename):
                        messagebox.showinfo("Load Patterns", "Custom patterns loaded successfully")
                    else:
                        messagebox.showerror("Load Patterns", "Failed to load custom patterns")
                except Exception as e:
                    messagebox.showerror("Load Error", f"Error loading patterns file: {e}")
        
        def add_individual_files(self):
            """Add individual files manually"""
            filenames = filedialog.askopenfilenames(
                title="Select Files to Add",
                filetypes=[("All files", "*.*")]
            )
            
            for filename in filenames:
                self.files_listbox.insert(tk.END, filename)
            
            if filenames:
                messagebox.showinfo("Add Files", f"Added {len(filenames)} files")
        
        def clear_all_files(self):
            """Clear all files from the data files list"""
            if messagebox.askyesno("Clear Files", "Are you sure you want to clear all data files?"):
                self.files_listbox.delete(0, tk.END)
            
        def update_command_preview(self):
            config = self.get_current_config()
            command = self.builder.build_pyinstaller_command(config)
            self.command_text.delete(1.0, tk.END)
            self.command_text.insert(1.0, " ".join(command))
            
        def get_current_config(self):
            """Get current configuration"""
            config = {
                "program_name": self.program_name_var.get(),
                "version": self.version_var.get(),
                "main_entry": self.main_entry_var.get(),
                "icon": self.icon_var.get(),
                "splash": self.splash_var.get(),
                "onefile": self.onefile_var.get(),
                "windowed": self.windowed_var.get(),
                "clean": self.clean_var.get(),
                "debug": self.debug_var.get(),
                "hidden_imports": [],
                "add_data": []
            }
            
            # Use OS-appropriate path separator
            path_separator = ";" if os.name == "nt" else ":"
            
            # Add additional files
            for i in range(self.files_listbox.size()):
                file_path = self.files_listbox.get(i)
                if os.path.isfile(file_path):
                    config["add_data"].append(f"{file_path}{path_separator}.")
                elif os.path.isdir(file_path):
                    config["add_data"].append(f"{file_path}{path_separator}{os.path.basename(file_path)}")
                    
            return config
            
        def quick_build(self):
            """Perform quick build with auto-detection"""
            if not self.main_entry_var.get():
                self.auto_detect_main()
            self.start_build()
            
        def start_build(self):
            """Start the build process"""
            if not self.main_entry_var.get():
                messagebox.showerror("Error", "Please select a main Python file")
                return
                
            config = self.get_current_config()
            command = self.builder.build_pyinstaller_command(config)
            
            # Update command preview
            self.command_text.delete(1.0, tk.END)
            self.command_text.insert(1.0, " ".join(command))
            
            # Clear output
            self.output_text.config(state=tk.NORMAL)
            self.output_text.delete(1.0, tk.END)
            self.output_text.config(state=tk.DISABLED)
            
            # Disable build button
            self.build_button.config(state=tk.DISABLED, text="Building...")
            
            # Start build in thread (simplified for tkinter)
            self.root.after(100, lambda: self.execute_build_async(command))
            
        def execute_build_async(self, command):
            """Execute build asynchronously"""
            def progress_callback(message):
                self.output_text.config(state=tk.NORMAL)
                self.output_text.insert(tk.END, message + "\\n")
                self.output_text.see(tk.END)
                self.output_text.config(state=tk.DISABLED)
                self.progress_var.set(message[:50] + "..." if len(message) > 50 else message)
                self.root.update()
                
            success, message, output = self.builder.execute_build(command, progress_callback)
            
            # Re-enable build button
            self.build_button.config(state=tk.NORMAL, text="Build")
            
            # Show completion message
            self.output_text.config(state=tk.NORMAL)
            self.output_text.insert(tk.END, f"\\n{'='*50}\\n")
            self.output_text.insert(tk.END, message + "\\n")
            self.output_text.insert(tk.END, f"{'='*50}\\n")
            self.output_text.config(state=tk.DISABLED)
            
            if success:
                self.progress_var.set("Build completed successfully!")
                messagebox.showinfo("Build Complete", "Build completed successfully!")
            else:
                self.progress_var.set("Build failed!")
                messagebox.showerror("Build Failed", f"Build failed:\\n{message}")
                
        def save_config(self):
            """Save configuration to file"""
            filename = filedialog.asksaveasfilename(title="Save Configuration", filetypes=[("JSON files", "*.json")])
            if filename:
                config = self.get_current_config()
                try:
                    with open(filename, 'w') as f:
                        json.dump(config, f, indent=4)
                    messagebox.showinfo("Save Config", "Configuration saved successfully!")
                except Exception as e:
                    messagebox.showerror("Save Error", f"Failed to save configuration:\\n{str(e)}")
                    
        def load_config(self):
            """Load configuration from file"""
            filename = filedialog.askopenfilename(title="Load Configuration", filetypes=[("JSON files", "*.json")])
            if filename:
                try:
                    with open(filename, 'r') as f:
                        config = json.load(f)
                    self.set_config(config)
                    messagebox.showinfo("Load Config", "Configuration loaded successfully!")
                except Exception as e:
                    messagebox.showerror("Load Error", f"Failed to load configuration:\\n{str(e)}")
                    
        def set_config(self, config):
            """Set configuration from dictionary"""
            self.program_name_var.set(config.get("program_name", ""))
            self.version_var.set(config.get("version", ""))
            self.main_entry_var.set(config.get("main_entry", ""))
            self.icon_var.set(config.get("icon", ""))
            self.splash_var.set(config.get("splash", ""))
            self.onefile_var.set(config.get("onefile", True))
            self.windowed_var.set(config.get("windowed", True))
            self.clean_var.set(config.get("clean", True))
            self.debug_var.set(config.get("debug", False))
            
        def run(self):
            """Run the GUI"""
            self.root.mainloop()

def show_version_info():
    """Display version information"""
    build_config = get_build_tool_config()
    update_config = get_update_config()
    
    safe_print(f"🚀 {build_config['name']}")
    safe_print("=" * 50)
    safe_print(f"Version: {update_config['current_version']}")
    safe_print(f"Author: {build_config['author']}")
    safe_print(f"Description: {build_config['description']}")
    safe_print("Features:")
    safe_print("  • Enhanced file detection and pattern matching")
    safe_print("  • ICO to PNG conversion with PIL/Pillow")
    safe_print("  • Memory-based console operations")
    safe_print("  • Multi-file selection dialogs")
    safe_print("  • Custom pattern search capabilities")
    safe_print("  • Configuration import/export")
    safe_print("  • Self-updating system")
    safe_print("  • Virtual environment management")
    safe_print("  • Project creation and scaffolding")
    safe_print("\nDependencies:")
    safe_print(f"  • PyQt6: {'✅ Available' if GUI_BACKEND == 'PyQt6' else '❌ Not available'}")
    safe_print(f"  • PIL/Pillow: {'✅ Available' if PIL_AVAILABLE else '❌ Not available'}")
    safe_print(f"  • Console Builder: {'✅ Available' if ConsoleBuilder else '❌ Not available'}")
    
    # Show environment file status
    env_file = os.path.join(os.path.dirname(__file__), "Build_Script.env")
    if os.path.exists(env_file):
        safe_print(f"\n📁 Configuration: ✅ Build_Script.env loaded")
        safe_print(f"   Repository: {update_config['repo_owner']}/{update_config['repo_name']}")
    else:
        safe_print(f"\n📁 Configuration: ⚠️  Build_Script.env not found (using defaults)")

def show_changelog():
    """Display changelog information"""
    print("📋 PyInstaller Build Tool - Changelog")
    print("=" * 50)
    
    # Try to find and read changelog files
    changelog_files = []
    changelog_patterns = ["CHANGELOG*", "changelog*", "*CHANGELOG*", "*.md"]
    
    for pattern in changelog_patterns:
        changelog_files.extend(glob.glob(pattern))
    
    # Remove duplicates and filter for actual changelog files
    changelog_files = list(set([f for f in changelog_files if 'changelog' in f.lower()]))
    
    if changelog_files:
        print(f"Found {len(changelog_files)} changelog file(s):")
        for file in changelog_files[:3]:  # Show max 3 files
            print(f"\\n📄 {file}:")
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[:20]  # Show first 20 lines
                    for line in lines:
                        print(f"  {line.rstrip()}")
                if len(f.readlines()) > 20:
                    print("  ... (truncated)")
            except Exception as e:
                print(f"  Error reading file: {e}")
    else:
        print("\\n📝 Enhanced Build Tool Updates:")
        print("\\n🆕 Version 2.0.0-enhanced:")
        print("  • Added comprehensive file scanning system")
        print("  • Implemented console memory management")
        print("  • Enhanced GUI with multi-file selection dialogs")
        print("  • Added ICO to PNG conversion tools")
        print("  • Improved pattern matching and search capabilities")
        print("  • Added configuration import/export functionality")
        print("  • Enhanced command-line argument system")
        print("  • Added --scan, --append, --import-config, --start options")

def show_optimal_structure():
    """Display optimal project structure and naming schemes for auto-detection"""
    print("🏗️  Optimal Project Structure for Auto-Detection")
    print("=" * 60)
    print()
    
    print("📁 Recommended Directory Structure:")
    print("""
MyProject/
├── main.py                    # Main entry point (auto-detected)
├── app.py                     # Alternative main entry
├── __main__.py                # Alternative main entry
├── 
├── assets/                    # Asset files directory
│   ├── *.ico                  # Icon files
│   ├── *.png, *.jpg, *.bmp    # Image files
│   └── splash.*               # Splash screen files
├── 
├── config/                    # Configuration directory
│   ├── config.json            # Main config file
│   ├── settings.json          # Settings file
│   └── *.config.json          # Additional config files
├── 
├── data/                      # Data files directory
│   ├── *.json, *.xml, *.yaml  # Data files
│   ├── *.csv, *.txt           # Text data files
│   └── *.db, *.sqlite         # Database files
├── 
├── docs/                      # Documentation directory
│   ├── README*.md             # Readme files
│   ├── CHANGELOG*             # Changelog files
│   └── *.md, *.rst, *.txt     # Documentation files
├── 
├── help/                      # Help files directory
│   ├── HELP_*.md              # Help documentation
│   ├── HELP_*.txt             # Help text files
│   └── tutorial*.py           # Tutorial scripts
├── 
├── templates/                 # Template files directory
│   ├── *.jinja, *.j2          # Jinja templates
│   ├── *.html, *.xml          # Markup templates
│   └── email.*                # Email templates
├── 
├── language/                  # Localization directory
│   ├── messages_*.json        # Language files
│   ├── locale_*.json          # Locale files
│   └── lang_*.json            # Language translations
├── 
├── scripts/                   # Additional scripts directory
│   ├── *.py                   # Python scripts
│   ├── *.bat, *.sh            # Shell scripts
│   └── build_*.py             # Build scripts
├── 
├── resources/                 # Resources directory
│   ├── icons/                 # Icon subdirectory
│   ├── images/                # Images subdirectory
│   └── fonts/                 # Fonts subdirectory
└── 
└── Build_Script.ico           # Default icon for build tool
""")
    
    print("🎯 Optimal File Naming Schemes:")
    print("-" * 50)
    print()
    
    print("📄 Main Entry Points (auto-detected priority):")
    print("  1. main.py           # Highest priority")
    print("  2. app.py            # Second priority")
    print("  3. __main__.py       # Third priority")
    print("  4. *.py              # All Python files (user selects)")
    print()
    
    print("🎨 Icon Files (*.ico format preferred):")
    print("  • Build_Script.ico   # Default for build tool itself")
    print("  • PDF_Utility.ico    # Application-specific icon")
    print("  • app.ico            # Generic application icon")
    print("  • main.ico           # Main application icon")
    print("  • icon.ico           # Generic icon name")
    print("  • logo.ico           # Logo-based icon")
    print()
    
    print("🖼️  Splash Screen Files (PNG/JPG preferred):")
    print("  • splash.png         # Main splash screen")
    print("  • logo.png           # Logo-based splash")
    print("  • Build_Script_splash.png  # Generated from ICO")
    print("  • *splash*.png       # Any file containing 'splash'")
    print()
    
    print("⚙️  Configuration Files:")
    print("  • config.json        # Main configuration")
    print("  • settings.json      # Application settings")
    print("  • *.config.json      # Specific config files")
    print("  • app_config.json    # Application-specific config")
    print("  • demo_config.json   # Demo configuration")
    print("  • build_config.json  # Build configuration")
    print()
    
    print("📚 Help/Documentation Files:")
    print("  🔍 PREFIX-based naming for smart recognition:")
    print("  • HELP-project.md    # Help for 'project' component")
    print("  • HELP-splitter.txt  # Help for 'splitter' feature")
    print("  • HELP_*.md          # Traditional help files")
    print("  • HELP_*.txt         # Traditional text help files")
    print("  • README*.md         # Readme documentation")
    print("  • CHANGELOG*         # Changelog files")
    print()
    
    print("🎓 Tutorial Files (auto-detectable):")
    print("  🔍 PREFIX-based naming for smart recognition:")
    print("  • TUTORIAL-splitter.json    # Tutorial data for splitter")
    print("  • TUTORIAL-merger.py        # Tutorial script for merger")
    print("  • TUTORIAL-config.md        # Tutorial docs for config")
    print("  • tutorial*.py              # Traditional tutorial scripts")
    print("  • help_system*.py           # Help system implementations")
    print("  • *tutorial*.py             # Any tutorial-named scripts")
    print()
    
    print("🌐 Language/Localization Files:")
    print("  • messages_en.json   # English messages")
    print("  • messages_es.json   # Spanish messages")
    print("  • locale_*.json      # Locale-specific files")
    print("  • lang_*.json        # Language translations")
    print()
    
    print("📦 Data Files:")
    print("  • *.json             # JSON data files")
    print("  • *.xml              # XML data files")
    print("  • *.yaml, *.yml      # YAML configuration")
    print("  • *.csv              # CSV data files")
    print("  • *.txt              # Text data files")
    print("  • enhanced_file_patterns.json  # File pattern definitions")
    print()
    
    print("🎨 Template Files:")
    print("  • *.jinja, *.j2      # Jinja2 templates")
    print("  • *.html             # HTML templates")
    print("  • email.*            # Email templates")
    print("  • index.template     # Index templates")
    print()
    
    print("🔧 Smart Naming Convention Rules:")
    print("-" * 50)
    print("  📝 PREFIX-component.extension format:")
    print("     HELP-feature.md    → Auto-detected as help file")
    print("     TUTORIAL-tool.json → Auto-detected as tutorial file")
    print("     CONFIG-app.json    → Auto-detected as config file")
    print("     DATA-users.csv     → Auto-detected as data file")
    print()
    print("  📁 Directory-based organization:")
    print("     help/HELP-*.md     → Organized help files")
    print("     docs/TUTORIAL-*.*  → Organized tutorial files")
    print("     config/CONFIG-*.*  → Organized config files")
    print()
    print("  🎯 Component-specific naming:")
    print("     splitter-related:   HELP-splitter.*, TUTORIAL-splitter.*")
    print("     merger-related:     HELP-merger.*, TUTORIAL-merger.*")
    print("     config-related:     HELP-config.*, TUTORIAL-config.*")
    print()
    
    print("💡 Pro Tips for Auto-Detection:")
    print("-" * 40)
    print("  🔍 Use descriptive, consistent naming")
    print("  📁 Organize files in logical directories")
    print("  🎯 Place main files in project root")
    print("  🔧 Use standard file extensions")
    print("  📝 Follow naming conventions shown above")
    print("  🚀 Test with --scan-project to verify detection")
    print()
    
    print("🧪 Testing Auto-Detection:")
    print("-" * 40)
    print("  python build_gui_enhanced.py --scan-project")
    print("  python build_gui_enhanced.py --scan=icons --scan=config")
    print("  python build_gui_enhanced.py --scan=help --scan=tutorials")
    print("  python build_gui_enhanced.py --scan-distant=\"./assets\" --type=icons")
    print("  python build_gui_enhanced.py --scan-distant=\"./docs\" --type=tutorials")
    print("  python build_gui_enhanced.py --show-memory")
    print()
    
    print("📋 Supported Scan Types:")
    print("-" * 40)
    scan_types = [
        "icons", "config", "help", "tutorials", "data", "assets", "docs", 
        "templates", "scripts", "language", "splash", "main",
        "json", "xml", "yaml", "images", "python", "text", "project"
    ]
    for i, scan_type in enumerate(scan_types):
        if i % 4 == 0:
            print("  ", end="")
        print(f"{scan_type:<12}", end="")
        if (i + 1) % 4 == 0 or i == len(scan_types) - 1:
            print()

def list_virtual_environments():
    """List available virtual environments in current directory and common locations"""
    venvs = []
    
    # Check current directory for common venv names
    common_venv_names = ['venv', 'env', 'build_env', 'build_script_env', '.venv', '.env']
    for name in common_venv_names:
        if os.path.exists(name) and os.path.isdir(name):
            # Check if it's actually a virtual environment
            if os.name == 'nt':  # Windows
                python_path = os.path.join(name, "Scripts", "python.exe")
            else:  # Unix/Linux/Mac
                python_path = os.path.join(name, "bin", "python")
            
            if os.path.exists(python_path):
                venvs.append(name)
    
    # Check for any directory containing Scripts/python.exe or bin/python
    for item in os.listdir('.'):
        if os.path.isdir(item) and item not in venvs:
            if os.name == 'nt':
                python_path = os.path.join(item, "Scripts", "python.exe")
            else:
                python_path = os.path.join(item, "bin", "python")
            
            if os.path.exists(python_path):
                venvs.append(item)
    
    return venvs

def remove_virtual_environment(venv_path=None):
    """Remove virtual environment(s)"""
    if venv_path == "virtual" or venv_path is None:
        # Remove all virtual environments
        venvs = list_virtual_environments()
        if not venvs:
            safe_print("ℹ️ No virtual environments found to remove")
            return True
        
        safe_print(f"🗑️ Found {len(venvs)} virtual environments:")
        for venv in venvs:
            safe_print(f"   • {venv}")
        
        confirm = input("❓ Remove all virtual environments? (y/N): ").strip().lower()
        if confirm in ['y', 'yes']:
            for venv in venvs:
                try:
                    shutil.rmtree(venv)
                    safe_print(f"✅ Removed virtual environment: {venv}")
                except Exception as e:
                    safe_print(f"❌ Error removing {venv}: {e}")
        else:
            safe_print("🚫 Virtual environment removal cancelled")
    else:
        # Remove specific virtual environment
        if os.path.exists(venv_path) and os.path.isdir(venv_path):
            try:
                shutil.rmtree(venv_path)
                safe_print(f"✅ Removed virtual environment: {venv_path}")
                return True
            except Exception as e:
                safe_print(f"❌ Error removing virtual environment {venv_path}: {e}")
                return False
        else:
            safe_print(f"❌ Virtual environment not found: {venv_path}")
            return False
    
    return True

def activate_virtual_environment(venv_path=None):
    """Provide activation instructions for virtual environment"""
    if venv_path is None:
        # Find available virtual environments
        venvs = list_virtual_environments()
        if not venvs:
            safe_print("❌ No virtual environments found")
            safe_print("💡 Create one with: --install-needed --virtual")
            return False
        elif len(venvs) == 1:
            venv_path = venvs[0]
        else:
            safe_print(f"📁 Found {len(venvs)} virtual environments:")
            for i, venv in enumerate(venvs, 1):
                safe_print(f"   {i}. {venv}")
            
            choice = input("Select environment (number or name): ").strip()
            
            if choice.isdigit() and 1 <= int(choice) <= len(venvs):
                venv_path = venvs[int(choice) - 1]
            elif choice in venvs:
                venv_path = choice
            else:
                safe_print("❌ Invalid selection")
                return False
    
    if not os.path.exists(venv_path):
        safe_print(f"❌ Virtual environment not found: {venv_path}")
        return False
    
    # Provide activation instructions
    safe_print(f"🚀 Virtual Environment: {venv_path}")
    safe_print("=" * 50)
    
    if os.name == 'nt':  # Windows
        activate_script = os.path.join(venv_path, "Scripts", "activate.bat")
        python_path = os.path.join(venv_path, "Scripts", "python.exe")
        
        safe_print("📋 Activation Commands:")
        safe_print(f"   Command Prompt: {activate_script}")
        safe_print(f"   PowerShell:     {venv_path}\\Scripts\\Activate.ps1")
        safe_print(f"   Direct Python:  {python_path}")
        
    else:  # Unix/Linux/Mac
        activate_script = os.path.join(venv_path, "bin", "activate")
        python_path = os.path.join(venv_path, "bin", "python")
        
        safe_print("📋 Activation Commands:")
        safe_print(f"   Bash/Zsh:      source {activate_script}")
        safe_print(f"   Direct Python: {python_path}")
    
    safe_print("\n🔧 Usage Examples:")
    safe_print(f"   {python_path} build_gui_enhanced.py --scan-project")
    safe_print(f"   {python_path} build_gui_enhanced.py --start")
    
    return True

def detect_target_file_packages(target_file):
    """Detect required packages for a specific target file"""
    if not os.path.exists(target_file):
        safe_print(f"❌ Target file not found: {target_file}")
        return []
    
    safe_print(f"🔍 Analyzing target file: {target_file}")
    
    # Common import to package mappings
    import_to_package = {
        'PyQt6': 'PyQt6',
        'PyQt5': 'PyQt5',
        'tkinter': '',  # Built-in
        'PIL': 'Pillow',
        'cv2': 'opencv-python',
        'numpy': 'numpy',
        'pandas': 'pandas',
        'requests': 'requests',
        'flask': 'Flask',
        'django': 'Django',
        'sqlalchemy': 'SQLAlchemy',
        'matplotlib': 'matplotlib',
        'seaborn': 'seaborn',
        'scipy': 'scipy',
        'sklearn': 'scikit-learn',
        'tensorflow': 'tensorflow',
        'torch': 'torch',
        'bs4': 'beautifulsoup4',
        'lxml': 'lxml',
        'yaml': 'PyYAML',
        'jinja2': 'Jinja2',
        'click': 'click',
        'dateutil': 'python-dateutil',
        'psutil': 'psutil',
        'cryptography': 'cryptography',
        'paramiko': 'paramiko',
        'openpyxl': 'openpyxl',
        'xlrd': 'xlrd',
        'docx': 'python-docx',
        'reportlab': 'reportlab',
        'fpdf': 'fpdf2',
        'win32api': 'pywin32',
        'win32gui': 'pywin32',
        'win32con': 'pywin32'
    }
    
    detected_packages = set()
    
    try:
        with open(target_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Look for import statements
            import re
            import_patterns = [
                r'import\s+([a-zA-Z_][a-zA-Z0-9_]*)',
                r'from\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            ]
            
            for pattern in import_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    if match in import_to_package:
                        package = import_to_package[match]
                        if package:  # Skip built-ins
                            detected_packages.add(package)
                            
    except Exception as e:
        safe_print(f"❌ Error analyzing target file: {e}")
        return []
    
    # Always include PyInstaller as it's needed for building
    detected_packages.add('pyinstaller')
    
    if detected_packages:
        safe_print(f"📦 Detected {len(detected_packages)} packages from target file:")
        for package in sorted(detected_packages):
            safe_print(f"   • {package}")
    else:
        safe_print("ℹ️ No additional packages detected from target file")
    
    return list(detected_packages)

def handle_remove_operation(remove_item, memory):
    """Handle removal operations including virtual environments"""
    if remove_item.lower() in ['virtual', 'venv', 'env']:
        # Remove virtual environments
        return remove_virtual_environment()
    elif os.path.exists(remove_item) and os.path.isdir(remove_item):
        # Check if it's a virtual environment
        if os.name == 'nt':
            python_path = os.path.join(remove_item, "Scripts", "python.exe")
        else:
            python_path = os.path.join(remove_item, "bin", "python")
        
        if os.path.exists(python_path):
            # It's a virtual environment
            return remove_virtual_environment(remove_item)
        else:
            safe_print(f"❌ Not a virtual environment: {remove_item}")
            return False
    else:
        # Handle file removal from memory (existing functionality)
        memory.remove_file_from_memory(remove_item)
        return True

def get_github_releases(repo_owner, repo_name, limit=10):
    """Get list of releases from GitHub repository"""
    try:
        api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases"
        
        req = urllib.request.Request(api_url)
        req.add_header('User-Agent', 'PyInstaller-Build-Tool-Enhanced')
        
        # Add GitHub API token if available
        env_config = load_env_config()
        github_token = env_config.get('GITHUB_API_TOKEN')
        if github_token and github_token != 'your_github_token_here':
            req.add_header('Authorization', f'token {github_token}')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                
                releases = []
                for release in data[:limit]:  # Limit number of releases
                    version = release.get('tag_name', '').lstrip('v')
                    name = release.get('name', '')
                    published_at = release.get('published_at', '')
                    assets = release.get('assets', [])
                    prerelease = release.get('prerelease', False)
                    
                    # Find suitable assets
                    suitable_assets = []
                    for asset in assets:
                        asset_name = asset.get('name', '').lower()
                        if asset_name.endswith('.exe') or asset_name.endswith('.py'):
                            suitable_assets.append(asset)
                    
                    releases.append({
                        'version': version,
                        'name': name,
                        'published_at': published_at,
                        'prerelease': prerelease,
                        'assets': suitable_assets,
                        'download_url': suitable_assets[0].get('browser_download_url') if suitable_assets else None
                    })
                
                return releases
            else:
                safe_print(f"❌ Failed to get releases: HTTP {response.status}")
                return []
                
    except Exception as e:
        safe_print(f"❌ Error getting releases: {e}")
        return []

def get_github_repository_info(repo_owner, repo_name):
    """Get repository information from GitHub API"""
    try:
        api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
        
        req = urllib.request.Request(api_url)
        req.add_header('User-Agent', 'PyInstaller-Build-Tool-Enhanced')
        
        # Add GitHub API token if available
        env_config = load_env_config()
        github_token = env_config.get('GITHUB_API_TOKEN')
        if github_token and github_token != 'your_github_token_here':
            req.add_header('Authorization', f'token {github_token}')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                return {
                    'name': data.get('name'),
                    'full_name': data.get('full_name'),
                    'description': data.get('description'),
                    'private': data.get('private', False),
                    'created_at': data.get('created_at'),
                    'updated_at': data.get('updated_at'),
                    'default_branch': data.get('default_branch'),
                    'has_releases': data.get('has_releases', False)
                }
            else:
                return None
                
    except Exception as e:
        safe_print(f"❌ Error getting repository info: {e}")
        return None

def get_github_commits(repo_owner, repo_name, limit=5):
    """Get recent commits from GitHub repository"""
    try:
        api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/commits"
        
        req = urllib.request.Request(api_url)
        req.add_header('User-Agent', 'PyInstaller-Build-Tool-Enhanced')
        
        # Add GitHub API token if available
        env_config = load_env_config()
        github_token = env_config.get('GITHUB_API_TOKEN')
        if github_token and github_token != 'your_github_token_here':
            req.add_header('Authorization', f'token {github_token}')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                
                commits = []
                for commit in data[:limit]:
                    commit_info = commit.get('commit', {})
                    commits.append({
                        'sha': commit.get('sha', '')[:8],  # Short SHA
                        'message': commit_info.get('message', '').split('\n')[0],  # First line only
                        'author': commit_info.get('author', {}).get('name', 'Unknown'),
                        'date': commit_info.get('author', {}).get('date', '')
                    })
                
                return commits
            else:
                return []
                
    except Exception as e:
        safe_print(f"❌ Error getting commits: {e}")
        return []

def check_repository_status(repo_owner, repo_name):
    """Check repository status and provide helpful information"""
    safe_print("🔍 Checking repository status...")
    
    # Get repository info
    repo_info = get_github_repository_info(repo_owner, repo_name)
    if not repo_info:
        safe_print("❌ Repository not found or not accessible")
        safe_print("   Please check:")
        safe_print("   • Repository name and owner in Build_Script.env")
        safe_print("   • GitHub token permissions")
        safe_print("   • Repository exists and is accessible")
        return False
    
    safe_print(f"✅ Repository found: {repo_info['full_name']}")
    if repo_info['description']:
        safe_print(f"   Description: {repo_info['description']}")
    
    safe_print(f"   Private: {'Yes' if repo_info['private'] else 'No'}")
    safe_print(f"   Default branch: {repo_info['default_branch']}")
    
    # Check for releases
    if not repo_info['has_releases']:
        safe_print("⚠️  No releases found in repository")
        safe_print("   To enable update system:")
        safe_print("   1. Go to your repository on GitHub")
        safe_print("   2. Click 'Releases' → 'Create a new release'")
        safe_print("   3. Tag version: v1.0.0")
        safe_print("   4. Upload your build tool file as an asset")
        
        # Show recent commits as alternative
        safe_print("\n📝 Recent commits:")
        commits = get_github_commits(repo_owner, repo_name, 3)
        if commits:
            for commit in commits:
                safe_print(f"   {commit['sha']} - {commit['message']} ({commit['author']})")
        else:
            safe_print("   No commits found")
    else:
        safe_print("✅ Repository has releases - update system ready")
    
    return True

def create_initial_release_guide():
    """Provide a step-by-step guide for creating the first release"""
    safe_print("\n🚀 Ready to create your first release? Here's how:")
    safe_print("=" * 50)
    
    env_config = load_env_config()
    repo_owner = env_config.get("GITHUB_REPO_OWNER", "your-username")
    repo_name = env_config.get("GITHUB_REPO_NAME", "your-repo")
    current_version = env_config.get("CURRENT_VERSION", "1.0.0")
    
    safe_print(f"📍 Repository: https://github.com/{repo_owner}/{repo_name}")
    safe_print(f"📦 Suggested version: v{current_version}")
    
    safe_print("\n📋 Step-by-step instructions:")
    safe_print("1. Open your repository in a web browser")
    safe_print("2. Click the 'Releases' section (usually on the right side)")
    safe_print("3. Click 'Create a new release' button")
    safe_print("4. Fill in the release form:")
    safe_print(f"   • Tag version: v{current_version}")
    safe_print(f"   • Release title: PyInstaller Build Tool Enhanced v{current_version}")
    safe_print("   • Description: Initial release of enhanced build tool")
    safe_print("5. Upload assets:")
    safe_print("   • Drag and drop 'build_gui_enhanced.py' file")
    safe_print("   • Or create a .zip with all tool files")
    safe_print("6. Click 'Publish release'")
    
    safe_print("\n💡 Pro tips:")
    safe_print("• Use semantic versioning (v1.0.0, v1.1.0, v2.0.0)")
    safe_print("• Include release notes describing new features")
    safe_print("• Mark as 'pre-release' if it's a beta version")
    safe_print("• The update system will automatically detect new releases")
    
    safe_print(f"\n🔗 Quick link: https://github.com/{repo_owner}/{repo_name}/releases/new")
    
    return True

def handle_downgrade_command(target_version, repo_owner=None, repo_name=None):
    """Handle the --downgrade command"""
    env_config = load_env_config()
    repo_owner = repo_owner or env_config.get("GITHUB_REPO_OWNER", "your-username")
    repo_name = repo_name or env_config.get("GITHUB_REPO_NAME", "your-repo")
    current_version = env_config.get("CURRENT_VERSION", "1.0.0")
    
    safe_print("🔄 PyInstaller Build Tool - Downgrade System")
    safe_print("=" * 50)
    safe_print(f"   Current version: {current_version}")
    safe_print(f"   Target version: {target_version}")
    
    # Get available releases
    safe_print("🔍 Fetching available releases...")
    releases = get_github_releases(repo_owner, repo_name)
    
    if not releases:
        safe_print("❌ Could not fetch releases from repository")
        return False
    
    # Find target version
    target_release = None
    for release in releases:
        if release['version'] == target_version:
            target_release = release
            break
    
    if not target_release:
        safe_print(f"❌ Version {target_version} not found in available releases")
        safe_print("📋 Available versions:")
        for release in releases[:5]:  # Show first 5
            status = "📌 Current" if release['version'] == current_version else "📦 Available"
            prerelease_tag = " (Pre-release)" if release['prerelease'] else ""
            safe_print(f"   {status}: {release['version']}{prerelease_tag} - {release['name']}")
        return False
    
    # Check if downgrading
    if target_version == current_version:
        safe_print("✅ You already have this version installed")
        return True
    
    download_url = target_release.get('download_url')
    if not download_url:
        safe_print(f"❌ No suitable download found for version {target_version}")
        return False
    
    safe_print(f"⚠️  WARNING: You are about to downgrade from {current_version} to {target_version}")
    safe_print("   This may remove newer features and could cause compatibility issues")
    safe_print("   A backup of your current version will be created")
    
    # Auto-confirm for demo (in real usage, you might want user input)
    response = "y"  # Auto-confirm
    
    if response.lower() in ['y', 'yes']:
        # Extract filename from URL
        filename = os.path.basename(urllib.parse.urlparse(download_url).path)
        if not filename:
            filename = f"build_gui_enhanced_v{target_version}.py"
        
        # Download and install
        downloaded_file = download_update(download_url, filename)
        if not downloaded_file:
            return False
        
        # Install (same process as update)
        success = install_update(downloaded_file)
        if success:
            safe_print(f"✅ Successfully downgraded to version {target_version}")
            safe_print("💡 You may need to restart the application")
        
        return success
    else:
        safe_print("📄 Downgrade cancelled by user")
        return False

def check_for_updates(repo_owner=None, repo_name=None, current_version=None, timeout=10):
    """Check GitHub repository for newer versions"""
    # Use environment config if parameters not provided
    if not all([repo_owner, repo_name, current_version]):
        update_config = get_update_config()
        repo_owner = repo_owner or update_config["repo_owner"]
        repo_name = repo_name or update_config["repo_name"]
        current_version = current_version or update_config["current_version"]
        timeout = update_config["timeout"]
    
    try:
        # GitHub API endpoint for latest release
        api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
        
        safe_print("🔍 Checking for updates...")
        safe_print(f"   Repository: {repo_owner}/{repo_name}")
        safe_print(f"   Current version: {current_version}")
        
        # Make request to GitHub API
        req = urllib.request.Request(api_url)
        req.add_header('User-Agent', 'PyInstaller-Build-Tool-Enhanced')
        
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                
                latest_version = data.get('tag_name', '').lstrip('v')
                release_name = data.get('name', '')
                release_notes = data.get('body', '')
                assets = data.get('assets', [])
                
                safe_print(f"   Latest version: {latest_version}")
                
                # Compare versions (simple string comparison for now)
                if latest_version and latest_version != current_version:
                    safe_print("🎉 New version available!")
                    safe_print(f"   Release: {release_name}")
                    if release_notes:
                        safe_print(f"   Release notes:")
                        # Truncate long release notes
                        notes_lines = release_notes.split('\n')[:5]
                        for line in notes_lines:
                            safe_print(f"     {line}")
                        if len(release_notes.split('\n')) > 5:
                            safe_print("     ...")
                    
                    # Find suitable asset (exe or py file)
                    suitable_assets = []
                    for asset in assets:
                        name = asset.get('name', '').lower()
                        if name.endswith('.exe') or name.endswith('.py'):
                            suitable_assets.append(asset)
                    
                    return {
                        'update_available': True,
                        'latest_version': latest_version,
                        'release_name': release_name,
                        'release_notes': release_notes,
                        'assets': suitable_assets,
                        'download_url': suitable_assets[0].get('browser_download_url') if suitable_assets else None
                    }
                else:
                    safe_print("✅ You have the latest version!")
                    return {'update_available': False, 'latest_version': latest_version}
            else:
                safe_print(f"❌ Failed to check for updates: HTTP {response.status}")
                return {'update_available': False, 'error': f'HTTP {response.status}'}
                
    except urllib.error.URLError as e:
        safe_print(f"❌ Network error checking for updates: {e}")
        return {'update_available': False, 'error': str(e)}
    except json.JSONDecodeError as e:
        safe_print(f"❌ Error parsing update information: {e}")
        return {'update_available': False, 'error': str(e)}
    except Exception as e:
        safe_print(f"❌ Unexpected error checking for updates: {e}")
        return {'update_available': False, 'error': str(e)}

def download_update(download_url, filename):
    """Download the update file"""
    try:
        safe_print(f"📥 Downloading update from: {download_url}")
        
        # Create temporary directory for download
        temp_dir = tempfile.mkdtemp(prefix="build_tool_update_")
        temp_file = os.path.join(temp_dir, filename)
        
        # Download with progress indication
        def show_progress(block_num, block_size, total_size):
            if total_size > 0:
                percent = min(100, (block_num * block_size * 100) // total_size)
                if percent % 10 == 0:  # Show every 10%
                    safe_print(f"   Progress: {percent}%")
        
        urllib.request.urlretrieve(download_url, temp_file, reporthook=show_progress)
        safe_print("✅ Download completed!")
        
        return temp_file
        
    except Exception as e:
        safe_print(f"❌ Download failed: {e}")
        return None

def install_update(downloaded_file):
    """Install the downloaded update"""
    try:
        current_script = os.path.abspath(__file__)
        script_dir = os.path.dirname(current_script)
        script_name = os.path.basename(current_script)
        
        # Create backup
        backup_name = f"{script_name}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_path = os.path.join(script_dir, backup_name)
        
        safe_print("🔄 Installing update...")
        safe_print(f"   Creating backup: {backup_name}")
        
        # Backup current version
        shutil.copy2(current_script, backup_path)
        
        # Determine if we're updating a .py or .exe file
        if current_script.endswith('.exe'):
            # For compiled executable
            safe_print("   Replacing executable...")
            
            # On Windows, we can't replace a running exe directly
            if platform.system().lower() == 'windows':
                # Create update script that will run after this process exits
                update_script = os.path.join(script_dir, "update_helper.bat")
                with open(update_script, 'w') as f:
                    f.write(f"""@echo off
timeout /t 2 /nobreak >nul
copy /y "{downloaded_file}" "{current_script}"
if errorlevel 1 (
    echo Update failed, restoring backup...
    copy /y "{backup_path}" "{current_script}"
    echo Backup restored.
) else (
    echo Update completed successfully!
    del "{backup_path}"
)
del "{downloaded_file}"
del "%~f0"
""")
                
                safe_print("✅ Update will complete after restart")
                safe_print(f"   Run: {update_script}")
                safe_print("   Or restart the application to complete update")
                return True
            else:
                # Unix-like systems
                shutil.copy2(downloaded_file, current_script)
                os.chmod(current_script, 0o755)
        else:
            # For Python script
            safe_print("   Replacing Python script...")
            shutil.copy2(downloaded_file, current_script)
        
        # Clean up
        os.remove(downloaded_file)
        os.rmdir(os.path.dirname(downloaded_file))
        
        safe_print("✅ Update installed successfully!")
        safe_print("💡 Restart the application to use the new version")
        
        return True
        
    except Exception as e:
        safe_print(f"❌ Update installation failed: {e}")
        
        # Try to restore backup
        try:
            if 'backup_path' in locals() and os.path.exists(backup_path):
                shutil.copy2(backup_path, current_script)
                safe_print("✅ Backup restored successfully")
        except Exception as restore_error:
            safe_print(f"❌ Failed to restore backup: {restore_error}")
            
        return False

def handle_update_command():
    """Handle the --update command"""
    # Get configuration from environment file
    update_config = get_update_config()
    
    safe_print("🚀 PyInstaller Build Tool - Update System")
    safe_print("=" * 50)
    
    # First check repository status
    repo_owner = update_config.get("repo_owner", "your-username")
    repo_name = update_config.get("repo_name", "your-repo")
    
    if not check_repository_status(repo_owner, repo_name):
        return False
    
    # Check for updates
    update_info = check_for_updates()
    
    if not update_info.get('update_available'):
        if 'error' in update_info:
            safe_print(f"❌ Update check failed: {update_info['error']}")
            return False
        else:
            safe_print("✅ No updates available")
            return True
    
    # Update available
    download_url = update_info.get('download_url')
    if not download_url:
        safe_print("❌ No suitable download found in the latest release")
        safe_print("💡 Please check the GitHub repository manually")
        return False
    
    # Ask for confirmation based on environment setting
    auto_confirm = update_config.get("auto_confirm", False)
    
    if not auto_confirm:
        safe_print("🤔 Do you want to download and install the update?")
        safe_print("   This will replace the current version")
        safe_print("   A backup will be created automatically")
        
        # In a real implementation, you would want user input here
        # For now, we'll use the environment setting
        response = "y"
    else:
        safe_print("🔄 Auto-confirming update based on environment settings...")
        response = "y"
    
    if response.lower() in ['y', 'yes']:
        # Extract filename from URL
        filename = os.path.basename(urllib.parse.urlparse(download_url).path)
        if not filename or filename == '':
            filename = f"build_gui_enhanced_v{update_info['latest_version']}.py"
        
        # Download update
        downloaded_file = download_update(download_url, filename)
        if not downloaded_file:
            return False
        
        # Install update
        return install_update(downloaded_file)
    else:
        safe_print("📄 Update cancelled by user")
        return False

def add_to_system_path():
    """Add the current build script directory to system PATH"""
    import platform
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    system = platform.system().lower()
    
    safe_print(f"🔧 Adding build script to system PATH...")
    safe_print(f"   📁 Script location: {script_dir}")
    
    if system == "windows":
        try:
            import winreg
            
            # Get current user PATH
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_ALL_ACCESS)
            try:
                current_path, _ = winreg.QueryValueEx(key, "PATH")
            except FileNotFoundError:
                current_path = ""
            
            # Check if already in PATH
            if script_dir.lower() in current_path.lower():
                safe_print("✅ Build script directory already in PATH")
                winreg.CloseKey(key)
                return True
            
            # Add to PATH
            new_path = f"{current_path};{script_dir}" if current_path else script_dir
            winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, new_path)
            winreg.CloseKey(key)
            
            # Notify system of environment change
            import ctypes
            ctypes.windll.user32.SendMessageW(0xFFFF, 0x001A, 0, "Environment")
            
            safe_print("✅ Successfully added to PATH (user environment)")
            safe_print("💡 Restart your terminal to use 'build_gui_enhanced.py' from anywhere")
            safe_print("🔧 Usage examples:")
            safe_print("   build_gui_enhanced.py --scan-project")
            safe_print("   build_gui_enhanced.py --new MyProject")
            safe_print("   build_gui_enhanced.py --install-needed --virtual")
            
            return True
            
        except Exception as e:
            safe_print(f"❌ Failed to add to Windows PATH: {e}")
            safe_print("💡 Manual alternative:")
            safe_print(f"   1. Open System Properties > Environment Variables")
            safe_print(f"   2. Add '{script_dir}' to your PATH variable")
            return False
            
    else:
        # Unix-like systems
        shell_configs = [
            os.path.expanduser("~/.bashrc"),
            os.path.expanduser("~/.zshrc"),
            os.path.expanduser("~/.profile")
        ]
        
        path_export = f'export PATH="$PATH:{script_dir}"'
        added_to = []
        
        for config_file in shell_configs:
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r') as f:
                        content = f.read()
                    
                    if script_dir not in content:
                        with open(config_file, 'a') as f:
                            f.write(f"\n# Added by PyInstaller Build Tool Enhanced\n{path_export}\n")
                        added_to.append(config_file)
                except Exception as e:
                    safe_print(f"⚠️  Warning: Could not modify {config_file}: {e}")
        
        if added_to:
            safe_print(f"✅ Added to PATH in: {', '.join(added_to)}")
            safe_print("💡 Run 'source ~/.bashrc' or restart your terminal")
            safe_print("🔧 Usage examples:")
            safe_print("   build_gui_enhanced.py --scan-project")
            safe_print("   build_gui_enhanced.py --new MyProject")
            safe_print("   build_gui_enhanced.py --install-needed --virtual")
            return True
        else:
            safe_print("❌ No shell configuration files found to modify")
            safe_print("💡 Manual alternative:")
            safe_print(f"   Add 'export PATH=\"$PATH:{script_dir}\"' to your shell config")
            return False

def handle_install_target_packages(target_file, venv_path=None):
    """Install packages needed for a specific target file"""
    if not os.path.exists(target_file):
        safe_print(f"❌ Target file not found: {target_file}")
        return False
    
    safe_print(f"🔍 Analyzing dependencies for: {target_file}")
    packages = detect_target_file_packages(target_file)
    
    if not packages:
        safe_print(f"✅ No additional packages needed for {target_file}")
        return True
    
    safe_print(f"📦 Found {len(packages)} package dependencies:")
    for pkg in packages:
        safe_print(f"   • {pkg}")
    
    return install_packages(packages, venv_path)

def is_virtual_environment(path):
    """Check if a directory is a virtual environment"""
    if not os.path.isdir(path):
        return False
    
    # Check for common virtual environment indicators
    indicators = [
        os.path.join(path, "Scripts", "activate.bat"),  # Windows
        os.path.join(path, "bin", "activate"),          # Unix-like
        os.path.join(path, "pyvenv.cfg"),               # Modern venv
        os.path.join(path, "Scripts", "python.exe"),    # Windows Python
        os.path.join(path, "bin", "python"),            # Unix Python
    ]
    
    return any(os.path.exists(indicator) for indicator in indicators)

def create_optimal_project_structure(project_name, location="."):
    """Create an optimal project structure with comprehensive setup"""
    project_path = os.path.join(location, project_name)
    
    try:
        # Create main project directory
        os.makedirs(project_path, exist_ok=True)
        
        # Create directory structure
        directories = [
            "src",
            "assets",
            "assets/icons", 
            "assets/images",
            "assets/data",
            "config",
            "docs",
            "tests",
            "templates"
        ]
        
        for directory in directories:
            os.makedirs(os.path.join(project_path, directory), exist_ok=True)
        
        # Create main application file
        main_py_content = f'''"""
{project_name} - Main Application Entry Point
Generated by PyInstaller Build Tool Enhanced
"""

import sys
import os
from pathlib import Path

def main():
    """Main application entry point"""
    print(f"🚀 Starting {project_name}...")
    
    # Add your application logic here
    print("✅ Application started successfully!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''
        
        with open(os.path.join(project_path, "src", "main.py"), "w", encoding="utf-8") as f:
            f.write(main_py_content)
        
        # Create requirements.txt
        requirements_content = '''# Core dependencies
pyqt6>=6.4.0
pillow>=9.0.0
requests>=2.28.0

# Development dependencies  
pytest>=7.0.0
black>=22.0.0
flake8>=4.0.0

# Build dependencies
pyinstaller>=5.0.0
'''
        
        with open(os.path.join(project_path, "requirements.txt"), "w", encoding="utf-8") as f:
            f.write(requirements_content)
        
        # Create build configuration
        build_config = {
            "project_name": project_name,
            "version": "1.0.0",
            "author": "Generated Project",
            "description": f"Enhanced {project_name} application",
            "main_script": "src/main.py",
            "icon": "assets/icons/app.ico",
            "data_files": [
                ("assets/data", "data"),
                ("config", "config"),
                ("templates", "templates")
            ],
            "hidden_imports": [],
            "exclude_modules": ["tkinter", "matplotlib"],
            "build_options": {
                "one_file": True,
                "console": False,
                "debug": False
            }
        }
        
        import json
        with open(os.path.join(project_path, "build_config.json"), "w", encoding="utf-8") as f:
            json.dump(build_config, f, indent=2)
        
        # Create README.md
        readme_content = f'''# {project_name}

## Description
Enhanced {project_name} application built with PyInstaller Build Tool Enhanced.

## Project Structure
```
TestProject/
├── src/                    # Main source code
│   └── main.py            # Application entry point
├── assets/                # Static assets
│   ├── icons/            # Application icons
│   ├── images/           # Images and graphics  
│   └── data/             # Data files
├── config/               # Configuration files
├── docs/                 # Documentation
├── tests/                # Unit tests
├── templates/            # Template files
├── requirements.txt      # Python dependencies
├── build_config.json     # Build configuration
└── README.md            # This file
```

## Getting Started

### 1. Set up development environment
```bash
cd {project_name}
python -m venv venv
venv\\Scripts\\activate  # Windows
# or
source venv/bin/activate  # Unix-like

pip install -r requirements.txt
```

### 2. Run the application
```bash
python src/main.py
```

### 3. Build executable
```bash
# Install build tool (if not already installed)
pip install pyinstaller

# Build with enhanced tool
python build_gui.py --import-config build_config.json --start
```

## Development

### Testing
```bash
pytest tests/
```

### Code Formatting
```bash
black src/
flake8 src/
```

### Building
The project includes an enhanced build configuration that handles:
- Automatic dependency detection
- Asset bundling
- Icon conversion
- Multi-platform builds
- Virtual environment support

## License
Add your license information here.
'''
        
        with open(os.path.join(project_path, "README.md"), "w", encoding="utf-8") as f:
            f.write(readme_content)
        
        # Create .gitignore
        gitignore_content = '''# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# Virtual environments
venv/
env/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Logs
*.log

# Build artifacts
build_output/
'''
        
        with open(os.path.join(project_path, ".gitignore"), "w", encoding="utf-8") as f:
            f.write(gitignore_content)
        
        # Create sample configuration file
        sample_config = {
            "application": {
                "name": project_name,
                "version": "1.0.0",
                "debug": False
            },
            "logging": {
                "level": "INFO",
                "file": "logs/app.log"
            }
        }
        
        with open(os.path.join(project_path, "config", "config.json"), "w", encoding="utf-8") as f:
            json.dump(sample_config, f, indent=2)
        
        return project_path
        
    except Exception as e:
        safe_print(f"❌ Failed to create project structure: {e}")
        return None

def handle_remove_operation(remove_item, memory):
    """Enhanced remove operation handling"""
    # Check if it's a virtual environment removal
    if remove_item == 'virtual':
        envs = list_virtual_environments()
        if envs:
            for env in envs:
                if remove_virtual_environment(env):
                    safe_print(f"✅ Removed virtual environment: {env}")
                else:
                    safe_print(f"❌ Failed to remove virtual environment: {env}")
        else:
            safe_print("❌ No virtual environments found to remove")
        return True
    
    # Check if it's a specific virtual environment
    if os.path.exists(remove_item) and is_virtual_environment(remove_item):
        if remove_virtual_environment(remove_item):
            safe_print(f"✅ Removed virtual environment: {remove_item}")
            return True
        else:
            safe_print(f"❌ Failed to remove virtual environment: {remove_item}")
            return False
    else:
        # Handle file removal from memory (existing functionality)
        memory.remove_file_from_memory(remove_item)
        return True

def create_virtual_environment(venv_path=None):
    """Create a virtual environment"""
    if venv_path is None:
        venv_path = "build_env"
    
    if os.path.exists(venv_path):
        safe_print(f"📁 Virtual environment already exists at: {venv_path}")
        return venv_path
    
    try:
        safe_print(f"🔧 Creating virtual environment at: {venv_path}")
        venv.create(venv_path, with_pip=True)
        safe_print(f"✅ Virtual environment created successfully")
        return venv_path
    except Exception as e:
        safe_print(f"❌ Error creating virtual environment: {e}")
        return None

def get_pip_command(venv_path=None):
    """Get the appropriate pip command for the environment"""
    if venv_path and os.path.exists(venv_path):
        # Use virtual environment pip
        if os.name == 'nt':  # Windows
            pip_path = os.path.join(venv_path, "Scripts", "pip.exe")
        else:  # Unix/Linux/Mac
            pip_path = os.path.join(venv_path, "bin", "pip")
        
        if os.path.exists(pip_path):
            return pip_path
    
    # Fall back to system pip
    return "pip"

def get_python_command(venv_path=None):
    """Get the appropriate python command for the environment"""
    if venv_path and os.path.exists(venv_path):
        # Use virtual environment python
        if os.name == 'nt':  # Windows
            python_path = os.path.join(venv_path, "Scripts", "python.exe")
        else:  # Unix/Linux/Mac
            python_path = os.path.join(venv_path, "bin", "python")
        
        if os.path.exists(python_path):
            return python_path
    
    # Fall back to system python
    return sys.executable

def detect_required_packages():
    """Detect required packages by scanning Python files"""
    safe_print("🔍 Analyzing Python files to detect required packages...")
    
    # Common import to package mappings
    import_to_package = {
        'PyQt6': 'PyQt6',
        'PyQt5': 'PyQt5',
        'tkinter': '',  # Built-in
        'PIL': 'Pillow',
        'cv2': 'opencv-python',
        'numpy': 'numpy',
        'pandas': 'pandas',
        'requests': 'requests',
        'flask': 'Flask',
        'django': 'Django',
        'sqlalchemy': 'SQLAlchemy',
        'matplotlib': 'matplotlib',
        'seaborn': 'seaborn',
        'scipy': 'scipy',
        'sklearn': 'scikit-learn',
        'tensorflow': 'tensorflow',
        'torch': 'torch',
        'bs4': 'beautifulsoup4',
        'lxml': 'lxml',
        'yaml': 'PyYAML',
        'jinja2': 'Jinja2',
        'click': 'click',
        'dateutil': 'python-dateutil',
        'psutil': 'psutil',
        'cryptography': 'cryptography',
        'paramiko': 'paramiko',
        'openpyxl': 'openpyxl',
        'xlrd': 'xlrd',
        'docx': 'python-docx',
        'reportlab': 'reportlab',
        'fpdf': 'fpdf2',
        'win32api': 'pywin32',
        'win32gui': 'pywin32',
        'win32con': 'pywin32'
    }
    
    detected_packages = set()
    python_files = glob.glob("*.py") + glob.glob("**/*.py", recursive=True)
    
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Look for import statements
                import re
                import_patterns = [
                    r'import\s+([a-zA-Z_][a-zA-Z0-9_]*)',
                    r'from\s+([a-zA-Z_][a-zA-Z0-9_]*)',
                ]
                
                for pattern in import_patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        if match in import_to_package:
                            package = import_to_package[match]
                            if package:  # Skip built-ins
                                detected_packages.add(package)
                                
        except Exception as e:
            safe_print(f"   ⚠️  Warning: Could not analyze {file_path}: {e}")
    
    # Always include PyInstaller as it's needed for building
    detected_packages.add('pyinstaller')
    
    if detected_packages:
        safe_print(f"📦 Detected {len(detected_packages)} required packages:")
        for package in sorted(detected_packages):
            safe_print(f"   • {package}")
    else:
        safe_print("ℹ️ No additional packages detected")
    
    return list(detected_packages)

def install_packages(packages, requirements_file=None, venv_path=None):
    """Install packages using pip"""
    pip_cmd = get_pip_command(venv_path)
    
    if venv_path:
        safe_print(f"🔧 Installing packages in virtual environment: {venv_path}")
    else:
        safe_print("🔧 Installing packages in system environment")
    
    if requirements_file and os.path.exists(requirements_file):
        safe_print(f"📋 Installing from requirements file: {requirements_file}")
        try:
            cmd = [pip_cmd, "install", "-r", requirements_file]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            safe_print("✅ Requirements file installation completed")
            return True
        except subprocess.CalledProcessError as e:
            safe_print(f"❌ Error installing from requirements file: {e}")
            safe_print(f"   Output: {e.output}")
            return False
    
    if packages:
        safe_print(f"📦 Installing {len(packages)} packages...")
        failed_packages = []
        
        for package in packages:
            try:
                safe_print(f"   Installing {package}...")
                cmd = [pip_cmd, "install", package]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                safe_print(f"   ✅ {package} installed successfully")
            except subprocess.CalledProcessError as e:
                safe_print(f"   ❌ Failed to install {package}: {e}")
                failed_packages.append(package)
        
        if failed_packages:
            safe_print(f"⚠️  {len(failed_packages)} packages failed to install:")
            for package in failed_packages:
                safe_print(f"   • {package}")
            return False
        else:
            safe_print(f"✅ All {len(packages)} packages installed successfully")
            return True
    
    return True

def get_build_script_dependencies():
    """Get the dependencies needed for this build script to work"""
    dependencies = [
        'pyinstaller',  # Core dependency for building
        'PyQt6',        # Primary GUI backend
        'Pillow',       # For ICO to PNG conversion
        'psutil',       # For system monitoring
        'colorama',     # For colored terminal output
    ]
    
    optional_dependencies = [
        'tkinter',      # Built-in GUI fallback (usually included)
        'pathlib',      # Usually built-in in Python 3.4+
        'argparse',     # Built-in argument parsing
    ]
    
    return dependencies, optional_dependencies

def handle_install_packages(requirements_file=None, auto_detect=False, venv_path=None, target_file=None):
    """Handle package installation with optional target file analysis"""
    packages = []
    
    if target_file and not auto_detect and not requirements_file:
        # ONLY analyze target file (no project-wide detection)
        safe_print(f"🎯 Analyzing ONLY target file: {target_file}")
        target_packages = detect_target_file_packages(target_file)
        if target_packages:
            packages.extend(target_packages)
            safe_print(f"📦 Found {len(target_packages)} packages in target file:")
            for pkg in target_packages:
                safe_print(f"   • {pkg}")
        else:
            safe_print("✅ No additional packages needed for target file")
    elif auto_detect:
        # Auto-detect from entire project
        safe_print("🔍 Auto-detecting packages from entire project...")
        detected_packages = detect_required_packages()
        packages.extend(detected_packages)
        if detected_packages:
            safe_print(f"📦 Auto-detected {len(detected_packages)} packages from project:")
            for pkg in detected_packages:
                safe_print(f"   • {pkg}")
        
        # Also analyze target file if specified
        if target_file:
            safe_print(f"🎯 Additionally analyzing target file: {target_file}")
            target_packages = detect_target_file_packages(target_file)
            if target_packages:
                packages.extend(target_packages)
                safe_print(f"📦 Found {len(target_packages)} additional packages from target:")
                for pkg in target_packages:
                    safe_print(f"   • {pkg}")
    elif requirements_file:
        # Install from requirements file
        if os.path.exists(requirements_file):
            safe_print(f"📦 Installing from requirements file: {requirements_file}")
            return install_packages([], requirements_file=requirements_file, venv_path=venv_path)
        else:
            safe_print(f"❌ Requirements file not found: {requirements_file}")
            return False
    
    if packages:
        # Remove duplicates while preserving order
        unique_packages = list(dict.fromkeys(packages))
        safe_print(f"📦 Installing {len(unique_packages)} unique packages...")
        return install_packages(unique_packages, venv_path)
    else:
        safe_print("✅ No packages to install")
        return True

def handle_install_needed(venv_path=None):
    """Install dependencies needed for this build script"""
    safe_print("🚀 Installing dependencies needed for build script...")
    
    if venv_path:
        # Create virtual environment if requested
        venv_result = create_virtual_environment(venv_path)
        if not venv_result:
            safe_print("❌ Failed to create virtual environment, continuing with system install")
            venv_path = None
    
    # Get required dependencies
    dependencies, optional_dependencies = get_build_script_dependencies()
    
    safe_print(f"📋 Required dependencies for build script:")
    for dep in dependencies:
        safe_print(f"   • {dep}")
    
    # Install required dependencies
    success = install_packages(dependencies, venv_path=venv_path)
    
    if success:
        safe_print("✅ Build script dependencies installed successfully!")
        safe_print("🎉 You can now use the build script with full functionality")
        
        if venv_path:
            python_cmd = get_python_command(venv_path)
            safe_print(f"💡 To use the virtual environment, run:")
            safe_print(f"   {python_cmd} build_gui_enhanced.py [options]")
    else:
        safe_print("❌ Some dependencies failed to install")
        safe_print("💡 You may need to install them manually or check your internet connection")
    
    return success

def safe_print(*args, **kwargs):
    """Print function that handles Unicode encoding issues for file output"""
    message = ' '.join(str(arg) for arg in args)
    
    try:
        print(message, **kwargs)
    except UnicodeEncodeError:
        # If direct print fails, use cleaned version
        clean_message = clean_output_for_file(message)
        print(clean_message, **kwargs)

def clean_output_for_file(text):
    """Clean text output for file writing to avoid encoding issues"""
    # Replace common emoji characters with ASCII equivalents
    emoji_replacements = {
        '🔍': '[SEARCH]',
        '✅': '[SUCCESS]',
        '❌': '[ERROR]',
        '📁': '[FOLDER]',
        '💾': '[SAVE]',
        'ℹ️': '[INFO]',
        '⚠️': '[WARNING]',
        '🎯': '[TARGET]',
        '🚀': '[ROCKET]',
        '📋': '[CLIPBOARD]',
        '🔧': '[TOOL]',
        '💡': '[IDEA]',
        '🧪': '[TEST]',
        '🎨': '[ART]',
        '📄': '[PAGE]',
        '🌐': '[WORLD]',
        '📦': '[PACKAGE]',
        '🏗️': '[CONSTRUCTION]',
        '🖼️': '[PICTURE]',
        '⚙️': '[GEAR]',
        '📚': '[BOOKS]',
        '🎓': '[GRADUATION]',
        '📝': '[MEMO]',
        '👋': '[WAVE]',
        '🗑️': '[TRASH]',
        '🎉': '[PARTY]',
        '🔄': '[ARROWS]',
        '📥': '[INBOX_TRAY]',
        '📤': '[OUTBOX_TRAY]'
    }
    
    for emoji, replacement in emoji_replacements.items():
        text = text.replace(emoji, replacement)
    
    return text

class OutputRedirector:
    """Handle output redirection for >> and --and>> operators"""
    
    def __init__(self):
        self.output_file = None
        self.show_console = True
        self.original_stdout = sys.stdout
        self.file_handle = None
    
    def setup_redirection(self, args_list):
        """Parse command line for output redirection operators and set up redirection"""
        # Join all arguments into a single string to parse operators
        full_command = ' '.join(args_list)
        
        # Check for --and>> operator (console + file output)
        if '--and>>' in full_command:
            parts = full_command.split('--and>>')
            if len(parts) == 2:
                command_part = parts[0].strip()
                file_part = parts[1].strip()
                self.output_file = file_part
                self.show_console = True
                # Return the command part without the redirection
                return command_part.split()
        
        # Check for >> operator (file output only)
        elif '>>' in full_command:
            parts = full_command.split('>>')
            if len(parts) == 2:
                command_part = parts[0].strip()
                file_part = parts[1].strip()
                self.output_file = file_part
                self.show_console = False
                # Return the command part without the redirection
                return command_part.split()
        
        # No redirection operators found
        return args_list
    
    def start_capture(self):
        """Start capturing output based on redirection settings"""
        if self.output_file:
            try:
                # Open file for writing (append mode)
                self.file_handle = open(self.output_file, 'a', encoding='utf-8')
                
                if self.show_console:
                    # --and>> operator: write to both console and file
                    sys.stdout = TeeOutput(self.original_stdout, self.file_handle)
                else:
                    # >> operator: write only to file (with Unicode cleaning)
                    sys.stdout = FileOutput(self.file_handle)
                
                # Add separator and timestamp to file
                if self.show_console:
                    print(f"\n{'='*60}")
                    print(f"Output captured at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"{'='*60}")
                else:
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    self.file_handle.write(f"\n{'='*60}\n")
                    self.file_handle.write(f"Output captured at: {timestamp}\n")
                    self.file_handle.write(f"{'='*60}\n")
                    
            except Exception as e:
                print(f"Error setting up output redirection: {e}")
                sys.stdout = self.original_stdout
    
    def stop_capture(self):
        """Stop capturing output and restore original stdout"""
        if self.output_file:
            try:
                if self.show_console:
                    print(f"{'='*60}")
                    print(f"Output saved to: {self.output_file}")
                    print(f"{'='*60}")
                else:
                    self.file_handle.write(f"{'='*60}\n")
                    self.file_handle.write(f"Output saved to: {self.output_file}\n")
                    self.file_handle.write(f"{'='*60}\n")
                
                # Restore original stdout
                sys.stdout = self.original_stdout
                
                # Close file handle
                if self.file_handle:
                    self.file_handle.close()
                    
                # Print confirmation to console if file-only mode was used
                if not self.show_console:
                    print(f"✅ Output saved to: {self.output_file}")
                    
            except Exception as e:
                print(f"Error closing output redirection: {e}")
                sys.stdout = self.original_stdout

class FileOutput:
    """Output class that writes to file with proper Unicode handling"""
    
    def __init__(self, file_handle):
        self.file_handle = file_handle
    
    def write(self, text):
        # Clean text for file output to avoid encoding issues
        clean_text = clean_output_for_file(text)
        self.file_handle.write(clean_text)
        self.file_handle.flush()
    
    def flush(self):
        self.file_handle.flush()

class TeeOutput:
    """Output class that writes to both console and file"""
    
    def __init__(self, console, file_handle):
        self.console = console
        self.file_handle = file_handle
    
    def write(self, text):
        # Write original text to console (with emojis)
        self.console.write(text)
        # Write cleaned text to file (ASCII safe)
        clean_text = clean_output_for_file(text)
        self.file_handle.write(clean_text)
        self.file_handle.flush()  # Ensure immediate write to file
    
    def flush(self):
        self.console.flush()
        self.file_handle.flush()

def filter_files_by_content(files, contains_text):
    """Filter files to only include those that contain the specified text"""
    if not contains_text:
        return files
    
    filtered_files = []
    contains_text_lower = contains_text.lower()
    
    safe_print(f"🔍 Filtering files that contain: '{contains_text}' (case-insensitive)")
    
    for file_path in files:
        try:
            # Skip binary files like ICO, PNG, etc.
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext in ['.ico', '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.exe', '.dll', '.bin']:
                continue
            
            # Try to read file content
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().lower()
                    if contains_text_lower in content:
                        filtered_files.append(file_path)
                        safe_print(f"   ✅ {file_path} - contains '{contains_text}'")
                    else:
                        safe_print(f"   ❌ {file_path} - does not contain '{contains_text}'")
            except UnicodeDecodeError:
                # Try with different encoding
                try:
                    with open(file_path, 'r', encoding='latin-1') as f:
                        content = f.read().lower()
                        if contains_text_lower in content:
                            filtered_files.append(file_path)
                            safe_print(f"   ✅ {file_path} - contains '{contains_text}'")
                        else:
                            safe_print(f"   ❌ {file_path} - does not contain '{contains_text}'")
                except Exception:
                    safe_print(f"   ⚠️  {file_path} - could not read file (binary or encoding issue)")
                    
        except Exception as e:
            safe_print(f"   ⚠️  {file_path} - error reading file: {e}")
    
    safe_print(f"🎯 Filtered {len(files)} files down to {len(filtered_files)} files containing '{contains_text}'")
    return filtered_files

def handle_scan_operation(scan_type, append_mode, memory, contains_filter=None):
    """Handle file scanning operations"""
    builder = EnhancedConsoleBuilder()
    
    print(f"🔍 Scanning for {scan_type} files...")
    
    # Map scan types to builder methods
    scan_methods = {
        'icons': builder.find_icon_files,
        'icon': builder.find_icon_files,
        'json': lambda: builder.find_files_by_custom_pattern("*.json"),
        'config': builder.find_config_files,
        'help': builder.find_help_files,
        'tutorials': builder.find_tutorial_files,
        'tutorial': builder.find_tutorial_files,
        'data': builder.find_data_files,
        'assets': builder.find_asset_files,
        'docs': builder.find_documentation_files,
        'documentation': builder.find_documentation_files,
        'templates': builder.find_template_files,
        'scripts': builder.find_script_files,
        'language': builder.find_language_files,
        'splash': builder.find_splash_files,
        'main': builder.find_main_files,
        'xml': lambda: builder.find_files_by_custom_pattern("*.xml"),
        'yaml': lambda: builder.find_files_by_custom_pattern("*.yaml;*.yml"),
        'images': lambda: builder.find_files_by_custom_pattern("*.png;*.jpg;*.jpeg;*.bmp;*.gif;*.ico"),
        'python': lambda: builder.find_files_by_custom_pattern("*.py"),
        'text': lambda: builder.find_files_by_custom_pattern("*.txt;*.md;*.rst")
    }
    
    if scan_type.lower() not in scan_methods:
        print(f"❌ Unknown scan type: {scan_type}")
        print(f"Available types: {', '.join(scan_methods.keys())}")
        return 1
    
    try:
        # Perform the scan
        files = scan_methods[scan_type.lower()]()
        
        # Apply content filter if specified
        if contains_filter:
            files = filter_files_by_content(files, contains_filter)
        
        if files:
            print(f"✅ Found {len(files)} {scan_type} files:")
            for i, file in enumerate(files, 1):
                print(f"  {i:2d}. {file}")
            
            # Store in memory
            memory.store_scan_results(scan_type.lower(), files, append_mode)
            
            action = "Appended to" if append_mode else "Stored in"
            print(f"\\n💾 {action} console memory")
            
        else:
            if contains_filter:
                print(f"ℹ️ No {scan_type} files found containing '{contains_filter}'")
            else:
                print(f"ℹ️ No {scan_type} files found")
            
        return 0
        
    except Exception as e:
        print(f"❌ Error during scan: {e}")
        return 1

def perform_project_scan(builder):
    """Perform a comprehensive project scan to find all common file types"""
    print("🔍 Performing comprehensive project scan...")
    all_files = []
    
    # Define project scan types
    project_scan_types = {
        'icons': builder.find_icon_files,
        'config': builder.find_config_files,
        'help': builder.find_help_files,
        'tutorials': builder.find_tutorial_files,
        'data': builder.find_data_files,
        'assets': builder.find_asset_files,
        'docs': builder.find_documentation_files,
        'templates': builder.find_template_files,
        'scripts': builder.find_script_files,
        'language': builder.find_language_files,
        'splash': builder.find_splash_files,
        'main': builder.find_main_files
    }
    
    # Collect all files from all types
    for scan_type, scan_method in project_scan_types.items():
        try:
            files = scan_method()
            if files:
                print(f"  📁 Found {len(files)} {scan_type} files")
                all_files.extend(files)
        except Exception as e:
            print(f"    ⚠️  Warning: Failed to scan {scan_type}: {e}")
    
    # Remove duplicates and return sorted list
    unique_files = list(set(all_files))
    print(f"✅ Project scan complete: {len(unique_files)} unique files found")
    return sorted(unique_files)

def handle_scan_operation_with_directory(scan_type, append_mode, memory, scan_directory=None, contains_filter=None):
    """Handle file scanning operations with custom directory support and content filtering"""
    builder = EnhancedConsoleBuilder()
    
    if scan_directory is None:
        scan_directory = os.getcwd()
    
    # Store current directory and change to scan directory
    original_dir = os.getcwd()
    if scan_directory != original_dir:
        os.chdir(scan_directory)
    
    try:
        safe_print(f"🔍 Scanning for {scan_type} files...")
        
        # Map scan types to builder methods
        scan_methods = {
            'icons': builder.find_icon_files,
            'icon': builder.find_icon_files,
            'json': lambda: builder.find_files_by_custom_pattern("*.json"),
            'config': builder.find_config_files,
            'help': builder.find_help_files,
            'tutorials': builder.find_tutorial_files,
            'tutorial': builder.find_tutorial_files,
            'data': builder.find_data_files,
            'assets': builder.find_asset_files,
            'docs': builder.find_documentation_files,
            'documentation': builder.find_documentation_files,
            'templates': builder.find_template_files,
            'scripts': builder.find_script_files,
            'language': builder.find_language_files,
            'splash': builder.find_splash_files,
            'main': builder.find_main_files,
            'xml': lambda: builder.find_files_by_custom_pattern("*.xml"),
            'yaml': lambda: builder.find_files_by_custom_pattern("*.yaml;*.yml"),
            'images': lambda: builder.find_files_by_custom_pattern("*.png;*.jpg;*.jpeg;*.bmp;*.gif;*.ico"),
            'python': lambda: builder.find_files_by_custom_pattern("*.py"),
            'text': lambda: builder.find_files_by_custom_pattern("*.txt;*.md;*.rst"),
            'project': lambda: perform_project_scan(builder)
        }
        
        if scan_type.lower() not in scan_methods:
            safe_print(f"❌ Unknown scan type: {scan_type}")
            safe_print(f"Available types: {', '.join(scan_methods.keys())}")
            return 1
        
        # Perform the scan
        files = scan_methods[scan_type.lower()]()
        
        # Convert relative paths to absolute paths based on scan directory
        absolute_files = []
        for file in files:
            if os.path.isabs(file):
                absolute_files.append(file)
            else:
                absolute_files.append(os.path.join(scan_directory, file))
        
        # Apply content filter if specified
        if contains_filter:
            absolute_files = filter_files_by_content(absolute_files, contains_filter)
        
        if absolute_files:
            safe_print(f"✅ Found {len(absolute_files)} {scan_type} files:")
            for i, file in enumerate(absolute_files, 1):
                # Show relative path if within scan directory for cleaner display
                display_path = os.path.relpath(file, scan_directory) if file.startswith(scan_directory) else file
                safe_print(f"  {i:2d}. {display_path}")
            
            # Store in memory with absolute paths
            memory.store_scan_results(scan_type.lower(), absolute_files, append_mode)
            
            action = "Appended to" if append_mode else "Stored in"
            safe_print(f"\\n💾 {action} console memory")
            
        else:
            if contains_filter:
                safe_print(f"ℹ️ No {scan_type} files found in {scan_directory} containing '{contains_filter}'")
            else:
                safe_print(f"ℹ️ No {scan_type} files found in {scan_directory}")
            
        return 0
        
    except Exception as e:
        safe_print(f"❌ Error during scan: {e}")
        return 1
    finally:
        # Always restore original directory
        if scan_directory != original_dir:
            os.chdir(original_dir)

def handle_import_config(config_file, memory):
    """Handle configuration import"""
    if not os.path.exists(config_file):
        print(f"❌ Configuration file not found: {config_file}")
        return 1
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        print(f"📥 Importing configuration from {config_file}...")
        
        # Store configuration in memory
        memory.store_config(config_data)
        
        print("✅ Configuration imported successfully")
        print(f"Imported keys: {list(config_data.keys())}")
        
        return 0
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in configuration file: {e}")
        return 1
    except Exception as e:
        print(f"❌ Error importing configuration: {e}")
        return 1

def handle_export_config(output_file, memory):
    """Handle configuration export"""
    try:
        config_data = memory.get_config()
        
        if not config_data:
            print("ℹ️ No configuration data to export")
            return 1
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        
        print(f"📤 Configuration exported to {output_file}")
        print(f"Exported keys: {list(config_data.keys())}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error exporting configuration: {e}")
        return 1

def handle_start_build(memory, include_date=True):
    """Handle build start using stored memory"""
    print("🚀 Starting build process with stored memory...")
    
    # Get stored configuration and scan results
    config = memory.get_config()
    scan_results = memory.get_scan_results()
    
    if not config and not scan_results:
        print("❌ No configuration or scan results found in memory")
        print("💡 Use --scan to scan for files or --import-config to load configuration")
        return 1
    
    try:
        builder = EnhancedConsoleBuilder()
        
        # Display what we have in memory
        print("\\n📋 Memory Contents:")
        if config:
            print(f"  Configuration: {list(config.keys())}")
        if scan_results:
            for scan_type, files in scan_results.items():
                print(f"  {scan_type}: {len(files)} files")
        
        # Generate versioned output paths
        program_name = config.get("program_name", "MyApp")
        version = config.get("version", "1.0.0")
        
        output_paths = generate_output_paths(program_name, version, include_date)
        print(f"\\n📁 Build will be created as: {output_paths['dist_name']}")
        print(f"   Distribution folder: {output_paths['distpath']}")
        print(f"   Work folder: {output_paths['workpath']}")
        print(f"   Spec folder: {output_paths['specpath']}")
        
        # Create a basic build configuration
        build_config = {
            "program_name": program_name,
            "version": version,
            "main_entry": config.get("main_entry", ""),
            "onefile": config.get("onefile", True),
            "windowed": config.get("windowed", True),
            "clean": config.get("clean", True),
            "debug": config.get("debug", False),
            "hidden_imports": config.get("hidden_imports", []),
            "add_data": [],
            **output_paths  # Add versioned paths
        }
        
        # Add scan results to build data
        for scan_type, files in scan_results.items():
            if scan_type == "icons" and files:
                build_config["icon"] = files[0]  # Use first icon found
            elif scan_type == "splash" and files:
                build_config["splash"] = files[0]  # Use first splash found
            else:
                # Add other files to add_data
                build_config["add_data"].extend(files)
        
        # If no main entry specified, try to find one
        if not build_config["main_entry"]:
            main_files = scan_results.get("main", [])
            if not main_files:
                main_files = builder.find_main_files()
            
            if main_files:
                build_config["main_entry"] = main_files[0]
                print(f"📄 Using main file: {main_files[0]}")
            else:
                print("❌ No main entry file found")
                return 1
        
        # Build the PyInstaller command
        command = builder.build_pyinstaller_command(build_config)
        
        print("\\n🔧 PyInstaller Command:")
        print(" ".join(command))
        
        # Ask for confirmation
        response = input("\\n❓ Execute this build? (y/N): ").strip().lower()
        
        if response in ['y', 'yes']:
            print("\\n🚀 Starting build process...")
            
            def progress_callback(message):
                print(f"  {message}")
            
            success, message, output = builder.execute_build(command, progress_callback)
            
            if success:
                print(f"\\n✅ {message}")
            else:
                print(f"\\n❌ {message}")
                if output:
                    print("\\nBuild output:")
                    for line in output[-20:]:  # Show last 20 lines
                        print(f"  {line}")
            
            return 0 if success else 1
        else:
            print("🚫 Build cancelled")
            return 0
            
    except Exception as e:
        print(f"❌ Error during build process: {e}")
        return 1

def run_console_mode(memory=None):
    """Run the enhanced console mode with memory support"""
    if ConsoleBuilder is None:
        print("Error: Console mode not available. build_script.py not found.")
        return False
    
    if memory is None:
        memory = ConsoleMemory()
    
    try:
        # Create enhanced builder
        enhanced_builder = EnhancedConsoleBuilder()
        
        print("🚀 Enhanced PyInstaller Build Tool - Console Mode")
        print("=" * 60)
        print()
        
        # Show memory status if there's data
        if memory.memory["scan_results"] or memory.memory["build_config"]:
            print("💾 Memory Status:")
            memory.show_memory_status()
            print()
        
        # Show enhanced menu
        while True:
            print("🔧 Enhanced Console Options:")
            print()
            print("📁 File Scanning:")
            print("  1.  Auto-detect Help Files")
            print("  2.  Auto-detect Config Files") 
            print("  3.  Auto-detect Data Files")
            print("  4.  Auto-detect Asset Files")
            print("  5.  Auto-detect Documentation Files")
            print("  6.  Auto-detect Template Files")
            print("  7.  Auto-detect Language Files")
            print("  8.  Auto-detect Script Files")
            print("  9.  Find Icon Files")
            print("  10. Find Splash Files")
            print("  11. Search by Custom Pattern")
            print()
            print("⚙️ Configuration:")
            print("  12. Load Custom Patterns from JSON")
            print("  13. Import Build Configuration")
            print("  14. Export Build Configuration")
            print("  15. Show Current Configuration")
            print()
            print("🎨 ICO Tools:")
            print("  16. ICO to PNG Conversion Tools")
            print("  17. Show ICO File Information")
            print()
            print("💾 Memory Management:")
            print("  18. Show Memory Status")
            print("  19. Clear Memory (with options)")
            print("  20. Save Current Session")
            print()
            print("🚀 Build Operations:")
            print("  21. Build with Current Memory")
            print("  22. Quick Build (auto-detect everything)")
            print("  23. Run Original Console Builder")
            print()
            print("  24. Exit")
            print()
            
            choice = input("Select option (1-24): ").strip()
            
            # File scanning operations
            if choice == "1":
                files = enhanced_builder.find_help_files()
                print(f"\\n📄 Found {len(files)} help files:")
                for i, f in enumerate(files, 1):
                    print(f"  {i:2d}. {f}")
                if files:
                    store_choice = input("\\n💾 Store in memory? (Y/n): ").strip().lower()
                    if store_choice != 'n':
                        append_choice = input("Append to existing? (y/N): ").strip().lower()
                        memory.store_scan_results("help", files, append_choice == 'y')
                        print("✅ Stored in memory")
                    
            elif choice == "2":
                files = enhanced_builder.find_config_files()
                print(f"\\n⚙️ Found {len(files)} config files:")
                for i, f in enumerate(files, 1):
                    print(f"  {i:2d}. {f}")
                if files:
                    store_choice = input("\\n💾 Store in memory? (Y/n): ").strip().lower()
                    if store_choice != 'n':
                        append_choice = input("Append to existing? (y/N): ").strip().lower()
                        memory.store_scan_results("config", files, append_choice == 'y')
                        print("✅ Stored in memory")
                    
            elif choice == "3":
                files = enhanced_builder.find_data_files()
                print(f"\\n💾 Found {len(files)} data files:")
                for i, f in enumerate(files, 1):
                    print(f"  {i:2d}. {f}")
                if files:
                    store_choice = input("\\n💾 Store in memory? (Y/n): ").strip().lower()
                    if store_choice != 'n':
                        append_choice = input("Append to existing? (y/N): ").strip().lower()
                        memory.store_scan_results("data", files, append_choice == 'y')
                        print("✅ Stored in memory")
                    
            elif choice == "4":
                files = enhanced_builder.find_asset_files()
                print(f"\\n🎨 Found {len(files)} asset files:")
                for i, f in enumerate(files, 1):
                    print(f"  {i:2d}. {f}")
                if files:
                    store_choice = input("\\n💾 Store in memory? (Y/n): ").strip().lower()
                    if store_choice != 'n':
                        append_choice = input("Append to existing? (y/N): ").strip().lower()
                        memory.store_scan_results("assets", files, append_choice == 'y')
                        print("✅ Stored in memory")
                    
            elif choice == "5":
                files = enhanced_builder.find_documentation_files()
                print(f"\\n📚 Found {len(files)} documentation files:")
                for i, f in enumerate(files, 1):
                    print(f"  {i:2d}. {f}")
                if files:
                    store_choice = input("\\n💾 Store in memory? (Y/n): ").strip().lower()
                    if store_choice != 'n':
                        append_choice = input("Append to existing? (y/N): ").strip().lower()
                        memory.store_scan_results("docs", files, append_choice == 'y')
                        print("✅ Stored in memory")
                    
            elif choice == "6":
                files = enhanced_builder.find_template_files()
                print(f"\\n📝 Found {len(files)} template files:")
                for i, f in enumerate(files, 1):
                    print(f"  {i:2d}. {f}")
                if files:
                    store_choice = input("\\n💾 Store in memory? (Y/n): ").strip().lower()
                    if store_choice != 'n':
                        append_choice = input("Append to existing? (y/N): ").strip().lower()
                        memory.store_scan_results("templates", files, append_choice == 'y')
                        print("✅ Stored in memory")
                    
            elif choice == "7":
                files = enhanced_builder.find_language_files()
                print(f"\\n🌍 Found {len(files)} language files:")
                for i, f in enumerate(files, 1):
                    print(f"  {i:2d}. {f}")
                if files:
                    store_choice = input("\\n💾 Store in memory? (Y/n): ").strip().lower()
                    if store_choice != 'n':
                        append_choice = input("Append to existing? (y/N): ").strip().lower()
                        memory.store_scan_results("language", files, append_choice == 'y')
                        print("✅ Stored in memory")
                    
            elif choice == "8":
                files = enhanced_builder.find_script_files()
                print(f"\\n📜 Found {len(files)} script files:")
                for i, f in enumerate(files, 1):
                    print(f"  {i:2d}. {f}")
                if files:
                    store_choice = input("\\n💾 Store in memory? (Y/n): ").strip().lower()
                    if store_choice != 'n':
                        append_choice = input("Append to existing? (y/N): ").strip().lower()
                        memory.store_scan_results("scripts", files, append_choice == 'y')
                        print("✅ Stored in memory")
                        
            elif choice == "9":
                files = enhanced_builder.find_icon_files()
                print(f"\\n🖼️ Found {len(files)} icon files:")
                for i, f in enumerate(files, 1):
                    print(f"  {i:2d}. {f}")
                if files:
                    store_choice = input("\\n💾 Store in memory? (Y/n): ").strip().lower()
                    if store_choice != 'n':
                        append_choice = input("Append to existing? (y/N): ").strip().lower()
                        memory.store_scan_results("icons", files, append_choice == 'y')
                        print("✅ Stored in memory")
                        
            elif choice == "10":
                files = enhanced_builder.find_splash_files()
                print(f"\\n🎨 Found {len(files)} splash files:")
                for i, f in enumerate(files, 1):
                    print(f"  {i:2d}. {f}")
                if files:
                    store_choice = input("\\n💾 Store in memory? (Y/n): ").strip().lower()
                    if store_choice != 'n':
                        append_choice = input("Append to existing? (y/N): ").strip().lower()
                        memory.store_scan_results("splash", files, append_choice == 'y')
                        print("✅ Stored in memory")
                        
            elif choice == "11":
                pattern = input("\\nEnter search pattern (e.g., '*.json;*.yaml' or 'config*'): ").strip()
                if pattern:
                    dirs = input("Enter search directories (press Enter for default): ").strip()
                    search_dirs = dirs.split(";") if dirs else None
                    files = enhanced_builder.find_files_by_custom_pattern(pattern, search_dirs)
                    print(f"\\n🔍 Found {len(files)} files matching pattern '{pattern}':")
                    for i, f in enumerate(files, 1):
                        print(f"  {i:2d}. {f}")
                    if files:
                        scan_type = input("\\nEnter scan type name for memory storage: ").strip()
                        if scan_type:
                            store_choice = input("💾 Store in memory? (Y/n): ").strip().lower()
                            if store_choice != 'n':
                                append_choice = input("Append to existing? (y/N): ").strip().lower()
                                memory.store_scan_results(scan_type, files, append_choice == 'y')
                                print("✅ Stored in memory")
                                
            elif choice == "12":
                json_file = input("\\nEnter path to JSON patterns file: ").strip()
                if json_file and os.path.exists(json_file):
                    if enhanced_builder.load_custom_patterns_from_file(json_file):
                        print("✅ Custom patterns loaded successfully")
                    else:
                        print("❌ Failed to load custom patterns")
                else:
                    print("❌ File not found")
                    
            elif choice == "13":
                config_file = input("\\nEnter path to configuration JSON file: ").strip()
                if config_file:
                    result = handle_import_config(config_file, memory)
                    if result == 0:
                        print("✅ Configuration imported successfully")
                    
            elif choice == "14":
                output_file = input("\\nEnter output file path for configuration: ").strip()
                if output_file:
                    result = handle_export_config(output_file, memory)
                    if result == 0:
                        print("✅ Configuration exported successfully")
                        
            elif choice == "15":
                config = memory.get_config()
                if config:
                    print("\\n⚙️ Current Configuration:")
                    for key, value in config.items():
                        print(f"  {key}: {value}")
                else:
                    print("\\nℹ️ No configuration stored")
                    
            elif choice == "16":
                # ICO to PNG Conversion submenu (keeping existing code but enhanced)
                print("\\n🎨 ICO to PNG Conversion Options:")
                print("1. Convert all ICO files to PNG")
                print("2. Convert specific ICO file")
                print("3. Back to main menu")
                
                ico_choice = input("Select ICO option (1-3): ").strip()
                
                if ico_choice == "1":
                    if not PIL_AVAILABLE:
                        print("❌ PIL/Pillow is required for ICO conversion")
                        print("Install with: pip install Pillow")
                    else:
                        converted_files = enhanced_builder.find_and_convert_icons_for_splash()
                        if converted_files:
                            print(f"✅ Converted {len(converted_files)} ICO files:")
                            for i, f in enumerate(converted_files, 1):
                                print(f"  {i:2d}. {f}")
                            store_choice = input("\\n💾 Store converted files in memory as splash files? (Y/n): ").strip().lower()
                            if store_choice != 'n':
                                memory.store_scan_results("splash", converted_files)
                                print("✅ Stored in memory")
                        else:
                            print("ℹ️ No ICO files found to convert")
                            
                elif ico_choice == "2":
                    if not PIL_AVAILABLE:
                        print("❌ PIL/Pillow is required for ICO conversion")
                        print("Install with: pip install Pillow")
                    else:
                        ico_file = input("Enter ICO file path: ").strip()
                        if ico_file and os.path.exists(ico_file):
                            output_file = input("Enter output PNG file path (or press Enter for auto): ").strip()
                            output_file = output_file if output_file else None
                            
                            result = enhanced_builder.convert_ico_to_png(ico_file, output_file)
                            if result:
                                print(f"✅ Converted to: {result}")
                                store_choice = input("💾 Store in memory as splash file? (Y/n): ").strip().lower()
                                if store_choice != 'n':
                                    memory.store_scan_results("splash", [result])
                                    print("✅ Stored in memory")
                            else:
                                print("❌ Conversion failed")
                        else:
                            print("❌ ICO file not found")
                            
            elif choice == "17":
                if not PIL_AVAILABLE:
                    print("❌ PIL/Pillow is required to analyze ICO files")
                else:
                    ico_files = glob.glob("*.ico") + glob.glob("**/*.ico", recursive=True)
                    if ico_files:
                        print("\\n🖼️ ICO Files Information:")
                        print("=" * 40)
                        for ico_file in ico_files:
                            ico_info = enhanced_builder.get_ico_info(ico_file)
                            if ico_info:
                                print(f"\\nFile: {ico_info['file']}")
                                print(f"Format: {ico_info['format']}")
                                print(f"Mode: {ico_info['mode']}")
                                print(f"Available sizes: {ico_info['sizes']}")
                                if ico_info['recommended_splash_size']:
                                    print(f"Recommended splash size: {ico_info['recommended_splash_size']}")
                                print("-" * 30)
                    else:
                        print("ℹ️ No ICO files found")
                        
            elif choice == "18":
                memory.show_memory_status()
                
            elif choice == "19":
                print("\\n🗑️ Clear Memory Options:")
                print("1. Clear all memory")
                print("2. Clear scan results only")
                print("3. Clear build configuration only")
                print("4. Clear specific scan type")
                print("5. Cancel")
                
                clear_choice = input("Select clear option (1-5): ").strip()
                
                if clear_choice == "1":
                    confirm = input("Are you sure you want to clear ALL memory? (y/N): ").strip().lower()
                    if confirm == 'y':
                        memory.clear_memory()
                        print("✅ All memory cleared")
                elif clear_choice == "2":
                    memory.clear_memory("scan_results")
                    print("✅ Scan results cleared")
                elif clear_choice == "3":
                    memory.clear_memory("build_config")
                    print("✅ Build configuration cleared")
                elif clear_choice == "4":
                    scan_types = list(memory.get_scan_results().keys())
                    if scan_types:
                        print(f"Available scan types: {', '.join(scan_types)}")
                        scan_type = input("Enter scan type to clear: ").strip()
                        if scan_type in scan_types:
                            memory.memory["scan_results"].pop(scan_type, None)
                            memory.save_memory()
                            print(f"✅ Cleared {scan_type} scan results")
                        else:
                            print("❌ Invalid scan type")
                    else:
                        print("ℹ️ No scan results to clear")
                        
            elif choice == "20":
                memory.save_memory()
                print("✅ Current session saved to memory")
                
            elif choice == "21":
                result = handle_start_build(memory)
                if result == 0:
                    print("\\n🎉 Build process completed")
                    
            elif choice == "22":
                print("\\n🚀 Quick Build - Auto-detecting everything...")
                
                # Auto-detect main files
                main_files = enhanced_builder.find_main_files()
                if not main_files:
                    main_files = glob.glob("*.py")
                
                if not main_files:
                    print("❌ No Python files found for building")
                else:
                    # Store quick scan results
                    memory.store_scan_results("main", main_files)
                    memory.store_scan_results("icons", enhanced_builder.find_icon_files())
                    memory.store_scan_results("splash", enhanced_builder.find_splash_files())
                    memory.store_scan_results("help", enhanced_builder.find_help_files())
                    memory.store_scan_results("config", enhanced_builder.find_config_files())
                    
                    # Set basic configuration
                    quick_config = {
                        "program_name": os.path.splitext(os.path.basename(main_files[0]))[0],
                        "version": "1.0.0",
                        "main_entry": main_files[0],
                        "onefile": True,
                        "windowed": True,
                        "clean": True
                    }
                    memory.store_config(quick_config)
                    
                    print("✅ Auto-detection complete")
                    result = handle_start_build(memory)
                    if result == 0:
                        print("\\n🎉 Quick build completed")
                
            elif choice == "23":
                # Run original console builder
                print("\\n🔄 Switching to original console builder...")
                original_builder = ConsoleBuilder()
                return original_builder.run()
                
            elif choice == "24":
                print("\\n👋 Goodbye!")
                return True
                
            else:
                print("❌ Invalid option. Please try again.")
            
            print()
            input("Press Enter to continue...")
            print()
        
    except Exception as e:
        print(f"Error running enhanced console mode: {e}")
        print("Falling back to original console mode...")
        try:
            original_builder = ConsoleBuilder()
            return original_builder.run()
        except Exception as e2:
            print(f"Error running original console mode: {e2}")
            return False
def run_gui_mode():
    """Run GUI mode with appropriate backend"""
    if GUI_BACKEND is None:
        print(f"Error: No GUI backend available. {GUI_ERROR}")
        print("\\nTo install PyQt6: pip install PyQt6")
        print("Or use console mode: python build_gui.py --console")
        return False
        
    print(f"Starting GUI with {GUI_BACKEND} backend...")
    
    if GUI_BACKEND == "PyQt6":
        from PyQt6.QtWidgets import QApplication
        app = QApplication(sys.argv)
        
        # Set application properties
        app.setApplicationName("PyInstaller Build Tool GUI")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("PyInstaller GUI")
        
        # Update splash message
        splash_screen.update_message("Initializing main window...")
        
        # Create and show main window
        window = PyInstallerGUI()
        
        # Close splash screen before showing main window
        splash_screen.close()
        
        window.show()
        
        return app.exec()
        
    elif GUI_BACKEND == "tkinter":
        try:
            gui = TkinterBuildGUI()
            gui.run()
            return True
        except Exception as e:
            print(f"Error running tkinter GUI: {e}")
            return False
            
    return False

def is_console_available():
    """Check if console/terminal is available for output"""
    try:
        # Try to get console window handle (Windows)
        if hasattr(sys, 'stdin') and hasattr(sys.stdin, 'fileno'):
            try:
                sys.stdin.fileno()
                return True
            except:
                pass
        
        # Check if we're in a console environment
        if hasattr(sys, 'stdout') and hasattr(sys.stdout, 'isatty'):
            return sys.stdout.isatty()
        
        # Fallback: try to write to stdout
        try:
            sys.stdout.write('')
            return True
        except:
            return False
    except:
        return False

def allocate_console():
    """Allocate a console window for output (Windows only)"""
    try:
        import ctypes
        if hasattr(ctypes, 'windll'):
            # Allocate console
            ctypes.windll.kernel32.AllocConsole()
            
            # Redirect stdout, stderr, stdin to console
            import io
            sys.stdout = io.TextIOWrapper(io.FileIO(ctypes.windll.kernel32.GetStdHandle(-11), 'w'))
            sys.stderr = io.TextIOWrapper(io.FileIO(ctypes.windll.kernel32.GetStdHandle(-12), 'w'))
            sys.stdin = io.TextIOWrapper(io.FileIO(ctypes.windll.kernel32.GetStdHandle(-10), 'r'))
            
            return True
    except:
        pass
    return False

def handle_fast_path_commands():
    """Handle command-line operations without loading GUI components"""
    try:
        parser = argparse.ArgumentParser(
            description="PyInstaller Build Tool - Enhanced (Fast Mode)",
            add_help=False  # Disable automatic help to avoid conflicts
        )
        
        # Add only the fast-path command arguments
        parser.add_argument("-h", "--help", action="help", help="Show this help message and exit")
        parser.add_argument("--version", type=str, nargs='?', const='show', metavar="VERSION",
                           help="Show tool version (no args) or set app version for build")
        parser.add_argument("--changelog", action="store_true", help="Show changelog")
        parser.add_argument("--repo-status", action="store_true",
                           help="Check GitHub repository status and configuration")
        parser.add_argument("--create-release", action="store_true",
                           help="Show guide for creating your first GitHub release")
        parser.add_argument("--update", action="store_true",
                           help="Check for and install updates from GitHub repository")
        parser.add_argument("--downgrade", type=str, metavar="VERSION",
                           help="Downgrade to specific version (e.g., --downgrade 1.0.0)")
        parser.add_argument("--show-memory", action="store_true", help="Display current memory status")
        parser.add_argument("--clear-memory", type=str, nargs='?', const='all', metavar="SECTION",
                           help="Clear memory (all, scan_results, build_config)")
        parser.add_argument("--clear-mem", action="store_true", 
                           help="Clear all memory completely (alias for --clear-memory=all)")
        parser.add_argument("--reset", action="store_true", 
                           help="Reset all memory completely (alias for --clear-mem)")
        parser.add_argument("--show-optimal", action="store_true",
                           help="Display optimal project structure and naming schemes")
        parser.add_argument("--preview-name", action="store_true",
                           help="Preview the generated build name without building")
        parser.add_argument("--activate", type=str, nargs='?', const='show', metavar="VENV_PATH",
                           help="Show activation instructions for virtual environment")
        
        args = parser.parse_args()
        
        # Handle fast-path commands
        if args.version:
            if args.version == 'show':
                show_version_info()
            else:
                safe_print(f"Version set to: {args.version}")
            return 0
            
        if args.changelog:
            show_changelog()
            return 0
            
        if args.repo_status:
            env_config = load_env_config()
            repo_owner = env_config.get("GITHUB_REPO_OWNER", "your-username")
            repo_name = env_config.get("GITHUB_REPO_NAME", "your-repo")
            
            safe_print("📊 GitHub Repository Status Check")
            safe_print("=" * 40)
            success = check_repository_status(repo_owner, repo_name)
            return 0 if success else 1
            
        if args.create_release:
            success = create_initial_release_guide()
            return 0 if success else 1
            
        if args.update:
            success = handle_update_command()
            return 0 if success else 1
            
        if args.downgrade:
            success = handle_downgrade_command(args.downgrade)
            return 0 if success else 1
            
        if args.show_memory:
            safe_print("🧠 Memory Status (Fast Mode)")
            safe_print("=" * 30)
            safe_print("Note: Full memory display requires full mode. Use without --show-memory for GUI.")
            return 0
            
        if args.clear_memory or args.clear_mem or args.reset:
            safe_print("🧹 Memory Clear (Fast Mode)")
            safe_print("Note: Memory operations require full mode. Use GUI or console mode for memory management.")
            return 0
            
        if args.show_optimal:
            show_optimal_structure()
            return 0
            
        if args.preview_name:
            safe_print("📋 Name Preview (Fast Mode)")
            safe_print("Note: Name preview requires full configuration. Use GUI mode for complete preview.")
            return 0
            
        if args.activate:
            safe_print("🔧 Virtual Environment Activation")
            safe_print("Note: Virtual environment management requires full mode.")
            return 0
        
        # If no recognized fast-path command, show help
        parser.print_help()
        return 0
        
    except Exception as e:
        safe_print(f"❌ Error in fast-path mode: {e}")
        return 1

def main():
    """Main entry point with enhanced argument parsing and output redirection support"""
    
    # Fast-path optimization: Handle simple commands without loading GUI
    if globals().get('FAST_PATH_MODE', False):
        return handle_fast_path_commands()
    
    # Check if we have command line arguments (indicating console usage)
    has_args = len(sys.argv) > 1
    
    # If we have arguments but no console, try to allocate one (Windows)
    if has_args and not is_console_available():
        allocate_console()
    
    # Handle output redirection before argument parsing
    redirector = OutputRedirector()
    processed_args = redirector.setup_redirection(sys.argv[1:])
    
    # Start output capture if redirection was specified
    redirector.start_capture()
    
    parser = argparse.ArgumentParser(
        description="PyInstaller Build Tool - Enhanced GUI and Console Mode with Output Redirection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python build_gui.py                                                    # Run GUI mode (default)
  python build_gui.py --console                                          # Run interactive console mode  
  python build_gui.py --scan=icons --scan=json --append                 # Scan for icons AND json files, append both
  python build_gui.py --scan-distant="C:/MyProject" --type=config       # Scan for config files in distant folder
  python build_gui.py --scan-distant="../assets" --type=splash --type=icons # Scan multiple types in distant folder
  python build_gui.py --scan-distant="../../../project" --type=project  # Scan entire project in distant folder
  python build_gui.py --set-root=C:/MyProject --scan-project            # Set root and auto-scan entire project
  python build_gui.py --scan=help --scan=data                           # Scan help and data files in current directory
  python build_gui.py --scan=config --contains="database"               # Scan config files containing "database"
  python build_gui.py --scan=python --contains="import sqlite"          # Scan Python files importing sqlite
  python build_gui.py --scan=tutorials --contains="splitter"            # Scan tutorial files mentioning splitter
  python build_gui.py --install-needed                                  # Install build script dependencies
  python build_gui.py --install-needed --virtual                        # Install dependencies in virtual environment
  python build_gui.py --install requirements.txt                        # Install from requirements file
  python build_gui.py --install                                         # Auto-detect and install needed packages
  python build_gui.py --install --virtual my_env                        # Install in custom virtual environment
  python build_gui.py --install --target main.py                        # Install dependencies for specific file
  python build_gui.py --activate                                        # Show virtual environment activation
  python build_gui.py --activate my_env                                 # Show activation for specific environment
  python build_gui.py --new MyProject                                   # Create new project with optimal structure
  python build_gui.py --new MyProject --location C:/Projects            # Create project in specific location
  python build_gui.py --remove virtual                                  # Remove all virtual environments
  python build_gui.py --remove my_env                                   # Remove specific virtual environment
  python build_gui.py --remove="config.json"                            # Remove specific file from memory
  python build_gui.py --remove-type=json                                # Remove all JSON files from memory
  python build_gui.py --clear-mem --scan-project                        # Clear memory and scan project
  python build_gui.py --reset --show-memory                             # Reset memory and show status
  python build_gui.py --import-config config.json --start                # Import config and start build
  python build_gui.py --set-name="MyApp" --set-version="2.0" --no-date --preview-name --start
  python build_gui.py --version --changelog                              # Show version and changelog
  python build_gui.py --test --show-memory                               # Test backends and show memory
  python build_gui.py --show-optimal                                     # Show optimal project structure guide
  
Output Redirection Examples:
  python build_gui.py --show-optimal >> optimal_structure.txt          # Save output to file only
  python build_gui.py --scan=tutorials --show-memory --and>> results.txt  # Show on console AND save to file
  python build_gui.py --scan-project --and>> project_scan.log             # Display and log project scan
  python build_gui.py --show-optimal --and>> help.txt                     # Display optimal structure and save to file
  python build_gui.py --scan=config --contains="database" --and>> db_configs.txt  # Filter and log results
  
Package Installation Examples:
  python build_gui.py --install-needed                                  # Install PyInstaller, PyQt6, Pillow, etc.
  python build_gui.py --install-needed --virtual                        # Install in virtual environment (build_env)
  python build_gui.py --install-needed --virtual my_project_env         # Install in custom virtual environment
  python build_gui.py --install requirements.txt                        # Install from requirements file
  python build_gui.py --install requirements.txt --virtual              # Install requirements in virtual environment
  python build_gui.py --install                                         # Auto-detect and install project packages
  python build_gui.py --install --virtual                               # Auto-detect and install in virtual environment
  python build_gui.py --install --target src/main.py                    # Auto-detect and install deps for target file
  python build_gui.py --install-needed --target src/main.py             # Install build deps for target file
  
System Integration Examples:
  python build_gui.py --add-to-path                                     # Add build script to system PATH
  python build_gui.py --version                                         # Show tool version
  python build_gui.py --version 2.1.0                                   # Set application version for build
  python build_gui.py --update                                          # Check for and install updates from GitHub
  python build_gui.py --downgrade 1.0.0                                 # Downgrade to specific version
  
Project Creation Examples:
  python build_gui.py --new MyAwesomeApp                                # Create project in current directory
  python build_gui.py --new MyAwesomeApp --location C:/Projects         # Create project in specific location
  python build_gui.py --name MyApp --location ~/Documents               # Alternative syntax for project creation
  
Virtual Environment Management:
  python build_gui.py --activate                                        # Show available virtual environments
  python build_gui.py --activate my_env                                 # Show activation for specific environment
  python build_gui.py --remove virtual                                  # Remove all virtual environments
  python build_gui.py --remove my_env                                   # Remove specific virtual environment
  
Note: --type flag can only be used with --scan-distant for distant directory scanning
      --scan flag is used for scanning in current directory (or --set-root directory)
      --clear-mem and --reset are aliases for complete memory reset
      --contains flag filters scan results to files containing the specified text (case-insensitive)
      >> operator saves output to file only, --and>> shows on console AND saves to file
        """
        )
    
    # Remove mutually exclusive groups - allow multiple flags
    
    # Mode options (no longer mutually exclusive)
    parser.add_argument("--console", action="store_true", help="Run in interactive console mode")
    parser.add_argument("--gui", action="store_true", help="Run in GUI mode")
    parser.add_argument("--test", action="store_true", help="Test available backends")
    parser.add_argument("--version", type=str, nargs='?', const='show', metavar="VERSION",
                       help="Show tool version (no args) or set app version for build")
    parser.add_argument("--add-to-path", action="store_true", 
                       help="Add build script directory to system PATH")
    parser.add_argument("--update", action="store_true",
                       help="Check for and install updates from GitHub repository")
    parser.add_argument("--repo-status", action="store_true",
                       help="Check GitHub repository status and configuration")
    parser.add_argument("--create-release", action="store_true",
                       help="Show guide for creating your first GitHub release")
    parser.add_argument("--downgrade", type=str, metavar="VERSION",
                       help="Downgrade to specific version (e.g., --downgrade 1.0.0)")
    parser.add_argument("--target", type=str, metavar="FILE",
                       help="Target file reference for other operations (use with --install, --scan, etc.)")
    parser.add_argument("--changelog", action="store_true", help="Show changelog")
    
    # Scanning options
    parser.add_argument("--scan", action="append", type=str, metavar="TYPE", 
                       help="Scan for files of specified type (icons, json, config, help, tutorials, data, assets, docs, templates, scripts, language, splash, main). Can be used multiple times: --scan=icons --scan=json")
    parser.add_argument("--scan-distant", type=str, metavar="PATH",
                       help="Specify folder path to scan for distant directory scanning. Must be used with --type flag. Example: --scan-distant=\"C:/users/public/documents\" --type=json")
    parser.add_argument("--type", action="append", type=str, metavar="TYPE",
                       help="Specify file type to scan for when using --scan-distant. Can be used multiple times: --type=icons --type=json --type=tutorials --type=project. Must be used with --scan-distant flag.")
    parser.add_argument("--contains", type=str, metavar="TEXT",
                       help="Filter scan results to only include files that contain the specified text (case-insensitive). Works with all scan operations.")
    parser.add_argument("--set-root", type=str, metavar="PATH",
                       help="Set the project root directory for building (changes working directory)")
    parser.add_argument("--scan-project", action="store_true",
                       help="Auto-scan the entire project for all common file types (icons, config, data, assets, docs, etc.)")
    parser.add_argument("--append", action="store_true", 
                       help="Append scan results to existing memory instead of replacing")
    
    # Configuration options
    parser.add_argument("--import-config", type=str, metavar="FILE",
                       help="Import build configuration from JSON file")
    parser.add_argument("--export-config", type=str, metavar="FILE",
                       help="Export current memory configuration to JSON file")
    
    # Installation options
    parser.add_argument("--install", type=str, nargs='?', const='auto', metavar="REQUIREMENTS_FILE",
                       help="Install packages from requirements file, or auto-detect if no file specified")
    parser.add_argument("--install-needed", action="store_true",
                       help="Install dependencies needed for this build script to work (PyInstaller, PyQt6, etc.)")
    parser.add_argument("--virtual", type=str, nargs='?', const='build_env', metavar="VENV_PATH",
                       help="Create/use virtual environment for installations (default: build_env)")
    parser.add_argument("--activate", type=str, nargs='?', const='auto', metavar="VENV_PATH",
                       help="Show activation instructions for virtual environment")
    
    # Project creation options
    parser.add_argument("--new", type=str, metavar="PROJECT_NAME",
                       help="Create new project with optimal structure")
    parser.add_argument("--location", type=str, metavar="PATH",
                       help="Location to create new project (use with --new)")
    parser.add_argument("--name", type=str, metavar="NAME",
                       help="Project name (alias for --new for clarity)")
    
    # Build options
    parser.add_argument("--start", action="store_true",
                       help="Start build process using stored memory configuration")
    parser.add_argument("--clear-memory", type=str, nargs='?', const='all', metavar="SECTION",
                       help="Clear memory (all, scan_results, build_config)")
    parser.add_argument("--clear-mem", action="store_true",
                       help="Clear all memory completely (alias for --clear-memory=all)")
    parser.add_argument("--reset", action="store_true",
                       help="Reset all memory completely (alias for --clear-mem)")
    parser.add_argument("--remove", type=str, metavar="FILENAME",
                       help="Remove a specific file from memory by filename")
    parser.add_argument("--remove-type", type=str, metavar="TYPE",
                       help="Remove all files of a specific type from memory (e.g., --remove-type=json)")
    parser.add_argument("--show-memory", action="store_true",
                       help="Display current memory status")
    parser.add_argument("--show-optimal", action="store_true",
                       help="Display optimal project structure and naming schemes for auto-detection")
    
    # Versioning options
    parser.add_argument("--set-version", type=str, metavar="VERSION",
                       help="Set version for build (e.g., 1.0.0)")
    parser.add_argument("--set-name", type=str, metavar="NAME",
                       help="Set program name for build")
    parser.add_argument("--no-date", action="store_true",
                       help="Disable date stamping in build names")
    parser.add_argument("--preview-name", action="store_true",
                       help="Preview the generated build name without building")
    
    # Parse the processed arguments (after output redirection handling)
    args = parser.parse_args(processed_args)
    
    # Initialize memory system
    memory = ConsoleMemory()
    
    # Track if any flags were processed
    processed_flags = False
    
    # Handle version display and setting
    if args.version is not None:
        if args.version == 'show':
            # Show tool version
            show_version_info()
        else:
            # Set app version for build
            memory.store_config({"version": args.version})
            safe_print(f"✅ Set application version to: {args.version}")
        processed_flags = True
    
    # Handle add to PATH
    if args.add_to_path:
        add_to_system_path()
        processed_flags = True
    
    # Handle update command
    if args.update:
        # Uses configuration from environment file
        success = handle_update_command()
        processed_flags = True
        if success:
            safe_print("🎉 Update process completed successfully!")
        return 0 if success else 1
    
    # Handle repository status check
    if args.repo_status:
        env_config = load_env_config()
        repo_owner = env_config.get("GITHUB_REPO_OWNER", "your-username")
        repo_name = env_config.get("GITHUB_REPO_NAME", "your-repo")
        
        safe_print("📊 GitHub Repository Status Check")
        safe_print("=" * 40)
        success = check_repository_status(repo_owner, repo_name)
        processed_flags = True
        return 0 if success else 1
    
    # Handle create release guide
    if args.create_release:
        success = create_initial_release_guide()
        processed_flags = True
        return 0 if success else 1
    
    # Handle downgrade command
    if args.downgrade:
        success = handle_downgrade_command(args.downgrade)
        processed_flags = True
        if success:
            safe_print("🎉 Downgrade process completed successfully!")
        return 0 if success else 1
    
    # Handle changelog display
    if args.changelog:
        show_changelog()
        processed_flags = True
    
    # Handle memory operations
    if args.clear_memory:
        section = args.clear_memory if args.clear_memory != 'all' else None
        memory.clear_memory(section)
        print(f"✅ Cleared memory {'section: ' + section if section else 'completely'}")
        processed_flags = True
    
    if args.clear_mem or args.reset:
        memory.reset_memory()
        processed_flags = True
    
    if args.remove:
        memory.remove_file_from_memory(args.remove)
        processed_flags = True
    
    if args.remove_type:
        memory.remove_type_from_memory(args.remove_type)
        processed_flags = True
    
    if args.show_memory:
        memory.show_memory_status()
        processed_flags = True
    
    if args.show_optimal:
        show_optimal_structure()
        processed_flags = True
    
    # Handle versioning operations
    if args.set_version:
        memory.store_config({"version": args.set_version})
        print(f"✅ Set version to: {args.set_version}")
        processed_flags = True
    
    if args.set_name:
        memory.store_config({"program_name": args.set_name})
        print(f"✅ Set program name to: {args.set_name}")
        processed_flags = True
    
    if args.preview_name:
        config = memory.get_config()
        program_name = config.get("program_name", "MyApp")
        version = config.get("version", "1.0.0")
        include_date = not args.no_date
        
        if include_date:
            output_paths = generate_output_paths(program_name, version, include_date)
            print("📁 Build Name Preview:")
            print(f"   Final executable: {output_paths['dist_name']}.exe")
            print(f"   Distribution folder: {output_paths['distpath']}")
            print(f"   Work folder: {output_paths['workpath']}")
            print(f"   Spec folder: {output_paths['specpath']}")
        else:
            base_name = generate_versioned_name(program_name, version, False)
            print("📁 Build Name Preview:")
            print(f"   Final executable: {base_name}.exe")
            print(f"   Distribution folder: dist")
            print(f"   Work folder: build")
            print(f"   Spec folder: (default)")
        processed_flags = True
    
    # Handle root directory change first (affects all subsequent operations)
    if args.set_root:
        if os.path.exists(args.set_root):
            original_dir = os.getcwd()
            os.chdir(args.set_root)
            print(f"📁 Changed working directory to: {args.set_root}")
            print(f"   Previous directory: {original_dir}")
            processed_flags = True
        else:
            print(f"❌ Error: Root directory not found: {args.set_root}")
            return 1
    
    # Handle scanning operations
    
    # Validate scan-distant and type flag usage
    if args.type and not args.scan_distant:
        print("❌ Error: --type flag can only be used with --scan-distant flag")
        print("   Example: --scan-distant=\"C:/users/public/documents\" --type=json")
        return 1
    
    if args.scan_distant and not args.type:
        print("❌ Error: --scan-distant flag must be used with --type flag")
        print("   Example: --scan-distant=\"C:/users/public/documents\" --type=json")
        return 1
    
    # Set scan directory (for --scan operations, use current directory; for --scan-distant operations, use specified path)
    scan_directory = os.getcwd()
    distant_directory = None
    
    # Validate distant directory if specified
    if args.scan_distant:
        if not os.path.exists(args.scan_distant):
            safe_print(f"❌ Error: Distant scan directory not found: {args.scan_distant}")
            return 1
        distant_directory = args.scan_distant
        safe_print(f"📁 Distant scanning will be performed in: {distant_directory}")
    
    if args.scan:
        # Regular scan operations in current directory
        for scan_type in args.scan:
            safe_print(f"🔍 Processing scan: {scan_type} in {scan_directory}")
            handle_scan_operation_with_directory(scan_type, args.append, memory, scan_directory, args.contains)
        processed_flags = True
    
    # Handle distant scanning with --type
    if args.type and args.scan_distant:
        # Distant scan operations in specified directory
        for scan_type in args.type:
            safe_print(f"🔍 Processing distant type scan: {scan_type} in {distant_directory}")
            handle_scan_operation_with_directory(scan_type, args.append, memory, distant_directory, args.contains)
        processed_flags = True
    
    # Handle project-wide scanning
    if args.scan_project:
        project_scan_directory = os.getcwd()  # Project scanning always uses current directory
        safe_print(f"🔍 Auto-scanning entire project in {project_scan_directory}")
        project_scan_types = ["icons", "config", "data", "assets", "docs", "templates", "scripts", "language", "splash", "main", "help"]
        for scan_type in project_scan_types:
            safe_print(f"  📁 Scanning for {scan_type}...")
            try:
                handle_scan_operation_with_directory(scan_type, True, memory, project_scan_directory, args.contains)  # Always append for project scan
            except Exception as e:
                safe_print(f"    ⚠️  Warning: Failed to scan {scan_type}: {e}")
        safe_print("✅ Project scan completed")
        processed_flags = True
    
    # Handle configuration operations
    if args.import_config:
        handle_import_config(args.import_config, memory)
        processed_flags = True
    
    if args.export_config:
        handle_export_config(args.export_config, memory)
        processed_flags = True
    
    # Handle installation operations
    if args.install_needed:
        venv_path = args.virtual if args.virtual else None
        handle_install_needed(venv_path)
        processed_flags = True
    
    if args.install is not None:
        venv_path = args.virtual if args.virtual else None
        target_file = args.target if args.target else None
        
        if target_file:
            # If target file specified, ONLY analyze that file
            safe_print(f"🎯 Target mode: Analyzing only {target_file}")
            handle_install_packages(target_file=target_file, venv_path=venv_path)
        elif args.install == 'auto':
            # Auto-detect packages from entire project
            handle_install_packages(auto_detect=True, venv_path=venv_path)
        else:
            # Install from requirements file
            handle_install_packages(requirements_file=args.install, venv_path=venv_path)
        processed_flags = True
    
    # Validate that --target is used with other flags
    if args.target and not any([args.install, args.install_needed, args.scan, args.scan_project]):
        safe_print("❌ Error: --target flag must be used with other operations")
        safe_print("💡 Usage examples:")
        safe_print("   --target src/main.py --install          # Install deps for target file")
        safe_print("   --target src/main.py --scan=python      # Scan with target as reference")
        safe_print("   --target src/main.py --install-needed   # Install build deps for target")
        return 1
    
    # Handle virtual environment activation
    if args.activate is not None:
        if args.activate == 'auto':
            # Show all available virtual environments
            envs = list_virtual_environments()
            if envs:
                safe_print("🐍 Available Virtual Environments:")
                for env in envs:
                    safe_print(f"   📁 {env}")
                    safe_print(f"      Activation: {activate_virtual_environment(env)}")
            else:
                safe_print("❌ No virtual environments found in current directory")
        else:
            # Show activation for specific environment
            activation_cmd = activate_virtual_environment(args.activate)
            safe_print(f"🐍 Virtual Environment Activation:")
            safe_print(f"   📁 Environment: {args.activate}")
            safe_print(f"   🔧 Command: {activation_cmd}")
        processed_flags = True
    
    # Handle project creation
    project_name = args.new or args.name
    if project_name:
        location = args.location or "."
        project_path = create_optimal_project_structure(project_name, location)
        if project_path:
            safe_print(f"✅ Project '{project_name}' created successfully!")
            safe_print(f"   📁 Location: {project_path}")
            safe_print(f"   🚀 Next steps:")
            safe_print(f"      cd {project_path}")
            safe_print(f"      python build_gui.py --install-needed --virtual")
        processed_flags = True
    
    # Enhanced remove operation handling
    if args.remove:
        if args.remove == 'virtual':
            # Remove all virtual environments
            envs = list_virtual_environments()
            if envs:
                for env in envs:
                    if remove_virtual_environment(env):
                        safe_print(f"✅ Removed virtual environment: {env}")
                    else:
                        safe_print(f"❌ Failed to remove virtual environment: {env}")
            else:
                safe_print("❌ No virtual environments found to remove")
        elif os.path.exists(args.remove) and os.path.isdir(args.remove):
            # Check if it's a virtual environment directory
            if is_virtual_environment(args.remove):
                if remove_virtual_environment(args.remove):
                    safe_print(f"✅ Removed virtual environment: {args.remove}")
                else:
                    safe_print(f"❌ Failed to remove virtual environment: {args.remove}")
            else:
                # Regular directory removal
                handle_remove_operation(args.remove, memory)
        else:
            # Original remove functionality for files/memory
            handle_remove_operation(args.remove, memory)
        processed_flags = True
    
    # Handle build start
    if args.start:
        include_date = not args.no_date
        handle_start_build(memory, include_date)
        processed_flags = True
    
    # Test mode
    if args.test:
        print("=" * 60)
        print("  PyInstaller Build Tool - Backend Test")
        print("=" * 60)
        
        print(f"Console Builder: {'✅ Available' if ConsoleBuilder else '❌ Not available'}")
        print(f"GUI Backend: {'✅ ' + GUI_BACKEND if GUI_BACKEND else '❌ ' + str(GUI_ERROR)}")
        
        if GUI_BACKEND:
            print(f"\\n🎉 GUI mode available with {GUI_BACKEND}")
        if ConsoleBuilder:
            print("🎉 Console mode available")
            
        if not GUI_BACKEND and not ConsoleBuilder:
            print("\\n⚠️  No backends available!")
            return 1
        processed_flags = True
    
    # Determine mode - only if no early exit flags or explicit mode requested
    if args.console:
        success = run_console_mode(memory)
        result = 0 if success else 1
    elif args.gui or not processed_flags:
        # Default to GUI mode if --gui specified or no flags processed, fallback to console if GUI not available
        if GUI_BACKEND:
            success = run_gui_mode()
            result = 0 if success else 1
        else:
            print(f"GUI not available: {GUI_ERROR}")
            print("Falling back to console mode...")
            success = run_console_mode(memory)
            result = 0 if success else 1
    else:
        # If flags were processed but no mode specified, exit gracefully
        result = 0
    
    # Always restore output redirection before returning
    redirector.stop_capture()
    return result

if __name__ == "__main__":
    sys.exit(main())
