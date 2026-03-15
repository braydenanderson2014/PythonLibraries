#!/usr/bin/env python3
"""
Simple drag and drop test for debugging file extension detection.
"""

import os
import sys

def test_file_extension_detection(test_files):
    """Test file extension detection with various inputs."""
    print("=== File Extension Detection Test ===")
    
    for file_path in test_files:
        print(f"\nTesting: {repr(file_path)}")
        
        # Clean up the file path - remove curly braces and extra whitespace
        cleaned_path = str(file_path).strip()
        if cleaned_path.startswith('{') and cleaned_path.endswith('}'):
            cleaned_path = cleaned_path[1:-1]
        
        # Normalize the file path
        normalized_path = os.path.normpath(cleaned_path)
        
        print(f"  Cleaned: {repr(normalized_path)}")
        
        # Get the file extension more robustly
        _, ext = os.path.splitext(normalized_path)
        ext_lower = ext.lower()
        
        print(f"  Extension: '{ext_lower}'")
        print(f"  Is PDF: {ext_lower == '.pdf'}")
        print(f"  File exists: {os.path.exists(normalized_path)}")

def main():
    # Test various file path formats that tkinterdnd2 might produce
    test_files = [
        "test.pdf",
        "/path/to/test.pdf",
        "{/path/to/test.pdf}",
        " /path/to/test.pdf ",
        "test.PDF",
        "test.txt",
        "/path/to/Document.pdf",
        "{C:\\Users\\Test\\Desktop\\document.pdf}",
        "C:\\Users\\Test\\Desktop\\document.pdf",
        "/home/user/Documents/file.pdf",
        "file with spaces.pdf",
        "{file with spaces.pdf}",
    ]
    
    test_file_extension_detection(test_files)

if __name__ == "__main__":
    main()
