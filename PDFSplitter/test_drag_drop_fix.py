#!/usr/bin/env python3
"""
Test script to verify the drag and drop file path parsing fix.
"""

import re
import os

def parse_file_paths(file_paths):
    """
    Parse file paths from tkinterdnd2 drop event data.
    This is the new parsing logic that handles files with spaces correctly.
    """
    if not isinstance(file_paths, str):
        file_paths = str(file_paths)
    
    file_paths = file_paths.strip()
    files_list = []
    
    # Check if the entire string is wrapped in curly braces (single file with spaces)
    if file_paths.startswith('{') and file_paths.endswith('}') and file_paths.count('{') == 1:
        # Single file with spaces wrapped in curly braces
        files_list = [file_paths[1:-1]]  # Remove the wrapping braces
    else:
        # Multiple files or files without spaces
        # Split by spaces, but handle files wrapped in curly braces
        pattern = r'\{([^}]+)\}|(\S+)'
        matches = re.findall(pattern, file_paths)
        
        for match in matches:
            # match[0] is the content inside braces, match[1] is standalone file
            file_path = match[0] if match[0] else match[1]
            if file_path.strip():
                files_list.append(file_path.strip())
    
    return files_list

def test_cases():
    """Test various file path scenarios."""
    test_cases = [
        # Single file with spaces (your original problem)
        "{C:/Users/brayd/OneDrive/Documents/GitHub/ArduinoArrayList/Fundraiser by Brayden Anderson _ Support Brayden's Arduino Code Development.pdf}",
        
        # Single file without spaces
        "C:/Users/brayd/Documents/simple.pdf",
        
        # Multiple files without spaces
        "C:/Users/brayd/Documents/file1.pdf C:/Users/brayd/Documents/file2.pdf",
        
        # Multiple files with spaces
        "{C:/Users/brayd/Documents/file with spaces.pdf} {C:/Users/brayd/Documents/another file.pdf}",
        
        # Mix of files with and without spaces
        "C:/Users/brayd/Documents/simple.pdf {C:/Users/brayd/Documents/file with spaces.pdf}",
        
        # Single file with spaces and special characters
        "{C:/Users/brayd/OneDrive/Documents/GitHub/ArduinoArrayList/Fundraiser by Brayden Anderson _ Support Brayden's Arduino Code Development.pdf}",
    ]
    
    print("Testing file path parsing:")
    print("=" * 80)
    
    for i, test_input in enumerate(test_cases, 1):
        print(f"\nTest {i}:")
        print(f"Input: {test_input}")
        
        result = parse_file_paths(test_input)
        print(f"Output: {result}")
        
        # Validate the result
        for file_path in result:
            if not file_path.strip():
                print(f"  ❌ Empty file path detected!")
            else:
                print(f"  ✅ Valid file path: {file_path}")

if __name__ == "__main__":
    test_cases()
