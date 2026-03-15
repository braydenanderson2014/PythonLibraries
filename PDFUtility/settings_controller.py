#!/usr/bin/env python3
# settings_controller.py - Controller for application settings

import os
import json
import platform
from utility import Utility

class SettingsController:
    """Controller for managing application settings - Singleton pattern"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls, parent=None):
        """Ensure only one instance of SettingsController exists"""
        if cls._instance is None:
            cls._instance = super(SettingsController, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, parent=None):
        # Only initialize once
        if self._initialized:
            return
            
        self.parent = parent
        self.utility = Utility()
        self.settings = {}
        
        # Get documents folder path for default settings
        self.documents_path = self.get_documents_path()
        
        # Define default settings
        self.default_settings = {
            "general": {
                "theme": "system",  # system, light, dark
                "language": "en",   # en, es, fr, etc.
                "check_updates": True,
                "recent_files": [],
                "max_recent_files": 10,
                "last_directory": "",
            },
            "pdf": {
                "default_output_dir": os.path.join(self.documents_path, "PDFUtility", "Output"),
                "default_merge_dir": os.path.join(self.documents_path, "PDFUtility", "Merged"),
                "default_split_dir": os.path.join(self.documents_path, "PDFUtility", "Split"),
                "remove_white_space": False,
                "whitespace_threshold": 95,  # 95% whitespace to consider a page blank
                "trim_borders": True,
                "remove_empty_pages": True,
                "consolidate_spaces": False,
                "aggressive_cleaning": False,
                "compression_level": "medium",  # none, low, medium, high
            },
            "interface": {
                "show_toolbar": True,
                "show_statusbar": True,
                "confirm_file_delete": True,
                "preview_quality": "medium",  # low, medium, high
                "preview_size": 200,  # width in pixels
            },
            "tts": {
                "rate": 150,
                "volume": 1.0,
                "voice": "System Default",
            },
            "editor": {
                "auto_open_selected": True,
                "remember_session": True,
                "confirm_unsaved_close": True,
                "font": "System Default",
                "font_size": 12,
                "syntax_highlighting": True,
                "recent_files": [],
                "last_session_files": []
            },
            "auto_import": {
                "enabled": True,
                "watch_directory": os.path.join(self.documents_path, "PDFUtility", "AutoImport"),
                "processed_directory": os.path.join(self.documents_path, "PDFUtility", "Processed"),
                "move_after_import": True,
                "auto_process": False,  # Automatically process imported PDFs
                "check_interval": 5,    # Check interval in seconds
                "processing_delay": 3,  # Delay before moving files (seconds)
            },
            "advanced": {
                "parallel_processing": True,
                "max_processes": 0,  # 0 = auto (based on CPU cores)
                "temp_dir": self.utility.get_temp_dir(),
                "log_level": "info",  # debug, info, warning, error
            },
            "logging": {
                "log_directory": os.path.join(self.documents_path, "PDFUtility", "Logs"),
                "log_filename": "pdf_utility.log",
                "auto_clear_logs": True,
                "clear_logs_interval": 7,  # Clear logs every N days (0 = never)
                "max_log_size_mb": 10,     # Maximum log file size in MB before rotation
                "keep_log_backups": 3,     # Number of backup log files to keep
                "open_log_in_editor": True, # Open log file in default text editor
            },
            "tutorials": {
                "enabled": True,           # Master switch for tutorial system
                "auto_start": True,        # Auto-start tutorials for new users
                "show_first_run": True,    # Show first-run tutorials
                "completed": {},           # Dictionary of completed tutorials
                "show_on_tab_switch": False,  # Show tutorials when switching to new tabs
                "animation_speed": "normal",  # slow, normal, fast
            }
        }
        
        # Get the config file path
        self.config_dir = self.utility.get_config_dir()
        self.config_file = os.path.join(self.config_dir, "settings.json")
        
        # Mark as initialized
        self._initialized = True
        
    def load_settings(self):
        """Load settings from the configuration file, or create default settings if file doesn't exist"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    loaded_settings = json.load(f)
                    
                # Merge loaded settings with defaults (to ensure all settings are present)
                self.settings = self.merge_settings(self.default_settings, loaded_settings)
                
                # Create required directories
                self.ensure_default_directories_exist()
            else:
                # Use default settings
                self.settings = self.default_settings.copy()
                
                # Create required directories
                self.ensure_default_directories_exist()
                
                # Save default settings
                self.save_settings()
                
        except Exception as e:
            # If there's an error loading settings, use defaults
            self.settings = self.default_settings.copy()
            print(f"Error loading settings: {str(e)}")
            
        return self.settings
    
    def save_settings(self):
        """Save current settings to the configuration file"""
        try:
            # Ensure config directory exists
            os.makedirs(self.config_dir, exist_ok=True)
            
            # Write settings to file
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
                
            return True
        except Exception as e:
            print(f"Error saving settings: {str(e)}")
            return False
    
    def get_setting(self, category, key=None, default=None):
        """Get a specific setting value"""
        if key is None:
            # If no key is provided, assume category is the key for top-level settings
            if category in self.settings:
                return self.settings[category]
            return default
        elif category in self.settings and key in self.settings[category]:
            return self.settings[category][key]
        return default
    
    def set_setting(self, category, key=None, value=None):
        """Set a specific setting value"""
        if key is None and value is None:
            # If only category is provided, assume it's a top-level setting
            self.settings[category] = value
            return self.save_settings()
        elif key is None:
            # If only category and value are provided
            self.settings[category] = value
            return self.save_settings()
        
        if category not in self.settings:
            self.settings[category] = {}
            
        self.settings[category][key] = value
        return self.save_settings()
    
    def has_setting(self, category, key=None):
        """Check if a setting exists"""
        if key is None:
            # If no key is provided, check if category exists
            return category in self.settings
        return category in self.settings and key in self.settings[category]
    
    def reset_settings(self):
        """Reset all settings to default values"""
        self.settings = self.default_settings.copy()
        return self.save_settings()
    
    def reset_category(self, category):
        """Reset a specific category of settings to default values"""
        if category in self.default_settings:
            self.settings[category] = self.default_settings[category].copy()
            return self.save_settings()
        return False
    
    def add_recent_file(self, file_path):
        """Add a file to the recent files list"""
        if not file_path:
            return False
            
        # Get the recent files list
        recent_files = self.settings["general"].get("recent_files", [])
        
        # Remove the file if it's already in the list
        if file_path in recent_files:
            recent_files.remove(file_path)
            
        # Add the file to the beginning of the list
        recent_files.insert(0, file_path)
        
        # Limit the number of recent files
        max_files = self.settings["general"].get("max_recent_files", 10)
        if len(recent_files) > max_files:
            recent_files = recent_files[:max_files]
            
        # Update the settings
        self.settings["general"]["recent_files"] = recent_files
        
        # Save the settings
        return self.save_settings()
    
    def clear_recent_files(self):
        """Clear the recent files list"""
        self.settings["general"]["recent_files"] = []
        return self.save_settings()
    
    def get_documents_path(self):
        """
        Get the path to the user's Documents folder, accounting for OneDrive if used.
        Returns the proper path to use for defaults.
        """
        # Get the user's home directory
        home = os.path.expanduser("~")
        
        # Check for OneDrive-redirected Documents folder (Windows specific)
        if platform.system() == "Windows":
            # Common OneDrive locations
            onedrive_paths = [
                os.path.join(home, "OneDrive", "Documents"),
                os.path.join(home, "OneDrive - Personal", "Documents"),
                os.path.join(home, "OneDrive - Business", "Documents"),
                os.path.join(home, "OneDrive - Company Name", "Documents")  # Common for business accounts
            ]
            
            # Check if any of these exist
            for path in onedrive_paths:
                if os.path.exists(path) and os.path.isdir(path):
                    return path
        
        # Fall back to standard Documents folder
        if platform.system() == "Windows":
            return os.path.join(home, "Documents")
        elif platform.system() == "Darwin":  # macOS
            return os.path.join(home, "Documents")
        else:  # Linux and others
            documents = os.path.join(home, "Documents")
            if os.path.exists(documents) and os.path.isdir(documents):
                return documents
            else:
                return home  # Fallback to home directory
    
    def merge_settings(self, default, loaded):
        """Recursively merge loaded settings with default settings"""
        result = default.copy()
        
        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursively merge dictionaries
                result[key] = self.merge_settings(result[key], value)
            else:
                # Override default with loaded value
                result[key] = value
                
        return result
        
    def reset_to_defaults(self):
        """Reset all settings to their default values"""
        # Reset settings to defaults
        self.settings = self.default_settings.copy()
        
        # Create default directories
        self.ensure_default_directories_exist()
        
        # Save settings
        return self.save_settings()
        
    def ensure_default_directories_exist(self):
        """Create any default directories that don't exist"""
        directories = [
            self.settings.get("pdf", {}).get("default_output_dir"),
            self.settings.get("pdf", {}).get("default_merge_dir"),
            self.settings.get("pdf", {}).get("default_split_dir"),
            self.settings.get("auto_import", {}).get("watch_directory"),
            self.settings.get("auto_import", {}).get("processed_directory"),
            self.settings.get("advanced", {}).get("temp_dir"),
            self.settings.get("logging", {}).get("log_directory")
        ]
        
        # Filter out any None or empty values
        directories = [d for d in directories if d]
        
        # Create each directory if it doesn't exist
        for directory in directories:
            try:
                if not os.path.exists(directory):
                    os.makedirs(directory)
            except Exception as e:
                # Log error but continue
                print(f"Failed to create directory {directory}: {str(e)}")
                # Log with utility's logger if available
                if hasattr(self.utility, 'logger'):
                    self.utility.logger.error("SettingsController", f"Failed to create directory {directory}: {str(e)}")
    
    def get_log_file_path(self):
        """Get the full path to the current log file"""
        log_dir = self.get_setting("logging", "log_directory", os.path.join(self.documents_path, "PDFUtility", "Logs"))
        log_filename = self.get_setting("logging", "log_filename", "pdf_utility.log")
        return os.path.join(log_dir, log_filename)
    
    def should_clear_logs(self):
        """Check if logs should be cleared based on settings and last clear time"""
        auto_clear = self.get_setting("logging", "auto_clear_logs", True)
        if not auto_clear:
            return False
            
        clear_interval = self.get_setting("logging", "clear_logs_interval", 7)
        if clear_interval <= 0:
            return False
            
        log_file = self.get_log_file_path()
        if not os.path.exists(log_file):
            return False
            
        # Check file modification time
        try:
            import time
            file_mod_time = os.path.getmtime(log_file)
            current_time = time.time()
            days_since_mod = (current_time - file_mod_time) / (24 * 60 * 60)
            return days_since_mod >= clear_interval
        except Exception:
            return False
    
    def get_log_file_size_mb(self):
        """Get the current log file size in MB"""
        log_file = self.get_log_file_path()
        if os.path.exists(log_file):
            try:
                size_bytes = os.path.getsize(log_file)
                return size_bytes / (1024 * 1024)  # Convert to MB
            except Exception:
                return 0
        return 0
    
    def get_log_file_size_formatted(self):
        """Get the current log file size formatted appropriately (KB or MB)"""
        log_file = self.get_log_file_path()
        if os.path.exists(log_file):
            try:
                size_bytes = os.path.getsize(log_file)
                
                # Convert to KB first
                size_kb = size_bytes / 1024
                
                # If less than 1 MB (1024 KB), show in KB
                if size_kb < 1024:
                    return f"{size_kb:.1f} KB"
                else:
                    # Convert to MB and show in MB
                    size_mb = size_bytes / (1024 * 1024)
                    return f"{size_mb:.2f} MB"
            except Exception:
                return "0 KB"
        return "0 KB"
    
    def should_rotate_log(self):
        """Check if the log file should be rotated based on size"""
        max_size_mb = self.get_setting("logging", "max_log_size_mb", 10)
        if max_size_mb <= 0:
            return False
        return self.get_log_file_size_mb() >= max_size_mb
    
    def open_log_file(self):
        """Open the log file in the default text editor"""
        log_file = self.get_log_file_path()
        if not os.path.exists(log_file):
            return False, "Log file does not exist"
            
        try:
            import subprocess
            import platform
            
            system = platform.system()
            if system == "Windows":
                # Use notepad as fallback, or default text editor
                subprocess.run(["notepad.exe", log_file])
            elif system == "Darwin":  # macOS
                subprocess.run(["open", log_file])
            else:  # Linux and others
                subprocess.run(["xdg-open", log_file])
            return True, "Log file opened successfully"
        except Exception as e:
            return False, f"Failed to open log file: {str(e)}"
    
    def open_log_directory(self):
        """Open the log directory in the file explorer"""
        log_dir = os.path.dirname(self.get_log_file_path())
        if not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir, exist_ok=True)
            except Exception as e:
                return False, f"Failed to create log directory: {str(e)}"
                
        try:
            import subprocess
            import platform
            
            system = platform.system()
            if system == "Windows":
                subprocess.run(["explorer", log_dir])
            elif system == "Darwin":  # macOS
                subprocess.run(["open", log_dir])
            else:  # Linux and others
                subprocess.run(["xdg-open", log_dir])
            return True, "Log directory opened successfully"
        except Exception as e:
            return False, f"Failed to open log directory: {str(e)}"
    
    def update_logger_settings(self, logger_instance=None):
        """Update the logger with current settings"""
        if logger_instance is None:
            try:
                from PDFLogger import Logger
                logger_instance = Logger()
            except ImportError:
                return False, "PDFLogger not available"
        
        try:
            # Update log file location if the logger supports it
            if hasattr(logger_instance, 'update_log_file'):
                log_file_path = self.get_log_file_path()
                logger_instance.update_log_file(log_file_path)
            
            # Update log level
            log_level = self.get_setting("advanced", "log_level", "info")
            if hasattr(logger_instance, 'set_log_level'):
                logger_instance.set_log_level(log_level)
            elif hasattr(logger_instance, 'logger'):
                level_map = {
                    "debug": logging.DEBUG,
                    "info": logging.INFO,
                    "warning": logging.WARNING,
                    "error": logging.ERROR,
                    "critical": logging.CRITICAL
                }
                if log_level.lower() in level_map:
                    import logging
                    logger_instance.logger.setLevel(level_map[log_level.lower()])
            
            return True, "Logger settings updated successfully"
        except Exception as e:
            return False, f"Failed to update logger settings: {str(e)}"
    
    # Tutorial Management Methods
    def is_tutorial_enabled(self):
        """Check if tutorial system is enabled"""
        return self.get_setting("tutorials", "enabled", True)
    
    def should_auto_start_tutorials(self):
        """Check if tutorials should auto-start for new users"""
        return self.get_setting("tutorials", "auto_start", True)
    
    def should_show_first_run_tutorials(self):
        """Check if first-run tutorials should be shown"""
        return self.get_setting("tutorials", "show_first_run", True)
    
    def is_tutorial_completed(self, tutorial_name):
        """Check if a specific tutorial has been completed"""
        completed = self.get_setting("tutorials", "completed", {})
        return completed.get(tutorial_name, False)
    
    def mark_tutorial_completed(self, tutorial_name):
        """Mark a tutorial as completed"""
        completed = self.get_setting("tutorials", "completed", {})
        completed[tutorial_name] = True
        self.set_setting("tutorials", "completed", completed)
        self.save_settings()
    
    def reset_tutorial_completion(self, tutorial_name=None):
        """Reset tutorial completion status"""
        completed = self.get_setting("tutorials", "completed", {})
        if tutorial_name:
            # Reset specific tutorial
            if tutorial_name in completed:
                del completed[tutorial_name]
        else:
            # Reset all tutorials
            completed = {}
        
        self.set_setting("tutorials", "completed", completed)
        self.save_settings()
    
    def get_completed_tutorials(self):
        """Get list of completed tutorials"""
        completed = self.get_setting("tutorials", "completed", {})
        return [name for name, is_completed in completed.items() if is_completed]
    
    def get_tutorial_statistics(self):
        """Get tutorial completion statistics"""
        all_tutorials = [
            "main_application", "split_widget", "merge_widget", 
            "image_converter", "white_space_widget", "tts_widget",
            "search_widget", "settings", "auto_import"
        ]
        completed = self.get_completed_tutorials()
        
        # Create detailed tutorial status
        tutorial_status = {}
        for tutorial in all_tutorials:
            tutorial_status[tutorial] = tutorial in completed
        
        return {
            "total": len(all_tutorials),
            "completed": len(completed),
            "remaining": len(all_tutorials) - len(completed),
            "completed_list": completed,
            "percentage": (len(completed) / len(all_tutorials)) * 100 if all_tutorials else 0,
            # Additional fields expected by settings dialog
            "total_tutorials": len(all_tutorials),
            "completed_tutorials": len(completed),
            "remaining_tutorials": len(all_tutorials) - len(completed),
            "tutorial_status": tutorial_status
        }

    def get_tutorial_status(self):
        """Get tutorial status information for the settings dialog"""
        return self.get_tutorial_statistics()
    
    def reset_tutorial(self, tutorial_name):
        """Reset a specific tutorial"""
        try:
            self.reset_tutorial_completion(tutorial_name)
            return True
        except Exception:
            return False
    
    def reset_all_tutorials(self):
        """Reset all tutorials"""
        try:
            self.reset_tutorial_completion()
            return True
        except Exception:
            return False
            
    def get_log_file_info(self):
        """Get log file information for the settings dialog"""
        log_dir = self.get_setting("logging", "log_directory", os.path.join(os.getcwd(), "logs"))
        log_filename = self.get_setting("logging", "log_filename", "pdf_utility.log")
        log_path = os.path.join(log_dir, log_filename)
        
        info = {
            "log_path": log_path,
            "exists": os.path.exists(log_path),
            "size_mb": 0.0,
            "last_modified": "Never"
        }
        
        if info["exists"]:
            try:
                import time
                size_bytes = os.path.getsize(log_path)
                info["size_mb"] = size_bytes / (1024 * 1024)
                last_modified = os.path.getmtime(log_path)
                info["last_modified"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(last_modified))
            except Exception:
                pass
                
        return info
