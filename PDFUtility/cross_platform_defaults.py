#!/usr/bin/env python3
"""
Cross-platform default directory utility
Handles default directories for Windows, macOS, and Linux with OneDrive compensation
"""

import os
import platform
from pathlib import Path

def get_default_documents_dir():
    """Get the default Documents directory, accounting for OneDrive"""
    system = platform.system()
    
    if system == "Windows":
        # Check for OneDrive Documents folder first
        onedrive_docs = os.path.expanduser("~/OneDrive/Documents")
        if os.path.exists(onedrive_docs):
            return onedrive_docs
        
        # Fall back to regular Documents
        return os.path.expanduser("~/Documents")
        
    elif system == "Darwin":  # macOS
        # Check for OneDrive Documents folder first
        onedrive_docs = os.path.expanduser("~/OneDrive/Documents")
        if os.path.exists(onedrive_docs):
            return onedrive_docs
            
        # Fall back to regular Documents
        return os.path.expanduser("~/Documents")
        
    else:  # Linux and others
        # Linux typically doesn't have OneDrive integration, but check just in case
        onedrive_docs = os.path.expanduser("~/OneDrive/Documents")
        if os.path.exists(onedrive_docs):
            return onedrive_docs
            
        # Standard XDG Documents directory
        return os.path.expanduser("~/Documents")

def get_default_downloads_dir():
    """Get the default Downloads directory"""
    system = platform.system()
    
    if system == "Windows":
        # Check for OneDrive Downloads folder first
        onedrive_downloads = os.path.expanduser("~/OneDrive/Downloads")
        if os.path.exists(onedrive_downloads):
            return onedrive_downloads
            
        # Fall back to regular Downloads
        return os.path.expanduser("~/Downloads")
        
    elif system == "Darwin":  # macOS
        # Check for OneDrive Downloads folder first
        onedrive_downloads = os.path.expanduser("~/OneDrive/Downloads")
        if os.path.exists(onedrive_downloads):
            return onedrive_downloads
            
        # Fall back to regular Downloads
        return os.path.expanduser("~/Downloads")
        
    else:  # Linux and others
        # Check OneDrive first
        onedrive_downloads = os.path.expanduser("~/OneDrive/Downloads")
        if os.path.exists(onedrive_downloads):
            return onedrive_downloads
            
        # Standard XDG Downloads directory
        return os.path.expanduser("~/Downloads")

def get_default_desktop_dir():
    """Get the default Desktop directory"""
    system = platform.system()
    
    if system == "Windows":
        # Check for OneDrive Desktop folder first
        onedrive_desktop = os.path.expanduser("~/OneDrive/Desktop")
        if os.path.exists(onedrive_desktop):
            return onedrive_desktop
            
        # Fall back to regular Desktop
        return os.path.expanduser("~/Desktop")
        
    elif system == "Darwin":  # macOS
        # Check for OneDrive Desktop folder first
        onedrive_desktop = os.path.expanduser("~/OneDrive/Desktop")
        if os.path.exists(onedrive_desktop):
            return onedrive_desktop
            
        # Fall back to regular Desktop
        return os.path.expanduser("~/Desktop")
        
    else:  # Linux and others
        # Check OneDrive first
        onedrive_desktop = os.path.expanduser("~/OneDrive/Desktop")
        if os.path.exists(onedrive_desktop):
            return onedrive_desktop
            
        # Standard XDG Desktop directory
        return os.path.expanduser("~/Desktop")

def create_pdf_utility_folders():
    """Create PDF Utility specific folders in Documents"""
    docs_dir = get_default_documents_dir()
    pdf_utility_dir = os.path.join(docs_dir, "PDF Utility")
    
    folders = {
        'base': pdf_utility_dir,
        'output': os.path.join(pdf_utility_dir, "Output"),
        'merged': os.path.join(pdf_utility_dir, "Merged"),
        'split': os.path.join(pdf_utility_dir, "Split"),
    }
    
    # Create folders if they don't exist
    for folder_name, folder_path in folders.items():
        try:
            os.makedirs(folder_path, exist_ok=True)
        except Exception as e:
            print(f"Warning: Could not create {folder_name} folder at {folder_path}: {e}")
    
    return folders

def get_pdf_default_directories():
    """Get default directories for PDF operations with fallbacks"""
    try:
        # Try to create PDF Utility specific folders
        folders = create_pdf_utility_folders()
        return {
            'output': folders['output'],
            'merge': folders['merged'], 
            'split': folders['split']
        }
    except Exception:
        # Fall back to standard directories
        docs_dir = get_default_documents_dir()
        return {
            'output': docs_dir,
            'merge': docs_dir,
            'split': docs_dir
        }

if __name__ == "__main__":
    # Test the functions
    print(f"Platform: {platform.system()}")
    print(f"Documents: {get_default_documents_dir()}")
    print(f"Downloads: {get_default_downloads_dir()}")
    print(f"Desktop: {get_default_desktop_dir()}")
    
    pdf_dirs = get_pdf_default_directories()
    print(f"PDF Output: {pdf_dirs['output']}")
    print(f"PDF Merge: {pdf_dirs['merge']}")
    print(f"PDF Split: {pdf_dirs['split']}")
