"""
PyInstaller Helper Utilities
Handles path resolution for bundled executables vs development mode
"""

import sys
import os
from pathlib import Path


def get_base_path():
    """
    Get the base path for the application.
    
    When running as PyInstaller bundle:
        - sys._MEIPASS points to the temporary extraction directory
        - Bundled resources are in subdirectories within this path
    
    When running as normal Python:
        - Returns the directory containing main_window.py
    
    Returns:
        Path: The base application directory
    """
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Running as PyInstaller executable
        return Path(sys._MEIPASS)
    else:
        # Running as normal Python script
        # Find the project root (parent of src directory)
        current_file = Path(__file__).resolve()
        return current_file.parent.parent


def get_resource_path(relative_path):
    """
    Get the full path to a resource file.
    
    Args:
        relative_path: Path relative to the resources directory
                      e.g., "store_settings.json" or "icons/app.ico"
    
    Returns:
        Path: Full path to the resource
    """
    base = get_base_path()
    resource_path = base / "resources" / relative_path
    return resource_path


def get_config_dir():
    """
    Get the configuration directory path.
    
    When running as PyInstaller executable:
        - Uses a "config" subdirectory in the user's AppData or home directory
    
    When running as normal Python:
        - Uses the "resources" subdirectory
    
    Returns:
        Path: Full path to config directory
    """
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Running as PyInstaller executable - use AppData or home directory
        if sys.platform == 'win32':
            config_dir = Path(os.getenv('APPDATA')) / "FinancialManager"
        else:
            config_dir = Path.home() / ".financialmanager"
    else:
        # Running as normal Python script
        config_dir = get_base_path() / "resources"
    
    # Create directory if it doesn't exist
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def is_pyinstaller_bundle():
    """
    Check if running as PyInstaller bundle.
    
    Returns:
        bool: True if running as PyInstaller executable, False otherwise
    """
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
