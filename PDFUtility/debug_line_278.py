#!/usr/bin/env python3
"""
Debug script to check the exact content at line 278
"""

def debug_line_278():
    """Check what's actually on line 278 of main_application.py"""
    print("🔍 Debugging line 278 in main_application.py...")
    
    try:
        with open('main_application.py', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if len(lines) >= 278:
            print(f"Line 278: {lines[277].strip()}")  # Lines are 0-indexed
            print(f"Line 279: {lines[278].strip()}")
            print(f"Line 280: {lines[279].strip()}")
            print(f"Line 281: {lines[280].strip()}")
            print(f"Line 282: {lines[281].strip()}")
            print(f"Line 283: {lines[282].strip()}")
        else:
            print(f"File only has {len(lines)} lines")
        
        # Find where PDFViewerWidget is created
        for i, line in enumerate(lines):
            if 'PDFViewerWidget(' in line:
                print(f"\nFound PDFViewerWidget creation at line {i+1}:")
                print(f"  {line.strip()}")
                break
        
        # Find where status_bar is created
        for i, line in enumerate(lines):
            if 'self.status_bar = QStatusBar()' in line:
                print(f"\nFound status_bar creation at line {i+1}:")
                print(f"  {line.strip()}")
                break
        
    except Exception as e:
        print(f"Error reading file: {e}")

if __name__ == "__main__":
    debug_line_278()
