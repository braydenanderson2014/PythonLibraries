#!/usr/bin/env python3
# utility.py - Common utility functions for PDF operations

import os
import sys
import platform
import datetime
import tempfile
import shutil
from pathlib import Path

class Utility:
    """Utility class for common operations"""
    
    @staticmethod
    def get_app_data_dir():
        """Get the appropriate application data directory based on platform"""
        if platform.system() == "Windows":
            app_data = os.getenv("APPDATA")
            if not app_data:
                app_data = os.path.expanduser("~")
            return os.path.join(app_data, "PDFUtility")
        elif platform.system() == "Darwin":  # macOS
            return os.path.join(os.path.expanduser("~"), "Library", "Application Support", "PDFUtility")
        else:  # Linux and others
            return os.path.join(os.path.expanduser("~"), ".pdfutility")
    
    @staticmethod
    def ensure_dir(directory):
        """Ensure a directory exists, creating it if necessary"""
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        return directory
    
    @staticmethod
    def get_log_dir():
        """Get the directory for log files"""
        log_dir = os.path.join(Utility.get_app_data_dir(), "logs")
        return Utility.ensure_dir(log_dir)
    
    @staticmethod
    def get_config_dir():
        """Get the directory for configuration files"""
        config_dir = os.path.join(Utility.get_app_data_dir(), "config")
        return Utility.ensure_dir(config_dir)
    
    @staticmethod
    def get_temp_dir():
        """Get a temporary directory for the application"""
        temp_dir = os.path.join(tempfile.gettempdir(), "PDFUtility")
        return Utility.ensure_dir(temp_dir)
    
    @staticmethod
    def sanitize_filename(filename):
        """Sanitize a filename by removing invalid characters"""
        # List of invalid characters for filenames
        invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        
        # Replace each invalid character with an underscore
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        return filename
    
    @staticmethod
    def generate_timestamp():
        """Generate a timestamp string for filenames"""
        return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    @staticmethod
    def get_file_size_str(file_path):
        """Get the file size as a human-readable string"""
        if not os.path.exists(file_path):
            return "N/A"
            
        size_bytes = os.path.getsize(file_path)
        
        # Convert to appropriate unit
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024 or unit == 'GB':
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
    
    @staticmethod
    def copy_file(source, destination):
        """Copy a file from source to destination, creating directories as needed"""
        # Ensure destination directory exists
        dest_dir = os.path.dirname(destination)
        if dest_dir:
            os.makedirs(dest_dir, exist_ok=True)
            
        # Copy the file
        shutil.copy2(source, destination)
        return destination
    
    @staticmethod
    def move_file(source, destination):
        """Move a file from source to destination, creating directories as needed"""
        # Ensure destination directory exists
        dest_dir = os.path.dirname(destination)
        if dest_dir:
            os.makedirs(dest_dir, exist_ok=True)
            
        # Move the file
        shutil.move(source, destination)
        return destination
    
    @staticmethod
    def delete_file(file_path):
        """Delete a file if it exists"""
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    
    @staticmethod
    def get_files_by_extension(directory, extensions):
        """Get all files with specific extensions in a directory (recursive)"""
        if not isinstance(extensions, list):
            extensions = [extensions]
            
        # Normalize extensions (ensure they start with a dot)
        extensions = [ext if ext.startswith('.') else f".{ext}" for ext in extensions]
        
        # Find all matching files
        matching_files = []
        for root, _, files in os.walk(directory):
            for file in files:
                if any(file.lower().endswith(ext.lower()) for ext in extensions):
                    matching_files.append(os.path.join(root, file))
                    
        return matching_files
