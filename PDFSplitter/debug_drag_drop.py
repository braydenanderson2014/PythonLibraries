#!/usr/bin/env python3
"""
Simple drag and drop test application to debug file extension detection issues.
"""

import os
import sys
import tkinter as tk
from tkinter import messagebox

def main():
    try:
        from tkinterdnd2 import TkinterDnD, DND_FILES
        
        # Create the main window
        root = TkinterDnD.Tk()
        root.title("Drag and Drop Test")
        root.geometry("600x400")
        
        # Create a text widget to show results
        text = tk.Text(root, wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        def log_message(message):
            """Add a message to the text widget"""
            text.insert(tk.END, message + "\n")
            text.see(tk.END)
            root.update()
        
        def on_drop(event):
            """Handle dropped files"""
            log_message("=== FILE DROP EVENT ===")
            log_message(f"Raw event data: {repr(event.data)}")
            log_message(f"Data type: {type(event.data)}")
            
            # Get the file paths from the event
            file_paths = event.data
            
            # Convert to string if needed
            if not isinstance(file_paths, str):
                file_paths = str(file_paths)
            
            # Clean up the data
            file_paths = file_paths.strip()
            log_message(f"Cleaned data: {repr(file_paths)}")
            
            # Handle multiple files
            possible_separators = [' ', ';', '\n', '\r\n']
            files_list = [file_paths]
            
            for separator in possible_separators:
                if separator in file_paths:
                    files_list = [f.strip() for f in file_paths.split(separator) if f.strip()]
                    log_message(f"Split by '{separator}': {files_list}")
                    break
            
            log_message(f"Final file list: {files_list}")
            
            # Process each file
            for file_path in files_list:
                if file_path.strip():
                    process_file(file_path.strip())
        
        def process_file(file_path):
            """Process a single dropped file"""
            log_message(f"\n--- Processing: {repr(file_path)} ---")
            
            # Clean up the file path
            cleaned_path = str(file_path).strip()
            if cleaned_path.startswith('{') and cleaned_path.endswith('}'):
                cleaned_path = cleaned_path[1:-1]
                log_message(f"Removed braces: {repr(cleaned_path)}")
            
            # Normalize the file path
            normalized_path = os.path.normpath(cleaned_path)
            log_message(f"Normalized: {repr(normalized_path)}")
            
            # Check if file exists
            exists = os.path.exists(normalized_path)
            log_message(f"File exists: {exists}")
            
            # Get extension
            _, ext = os.path.splitext(normalized_path)
            ext_lower = ext.lower()
            log_message(f"Extension: '{ext_lower}'")
            
            # Check if PDF
            is_pdf = ext_lower == '.pdf'
            log_message(f"Is PDF: {is_pdf}")
            
            if is_pdf:
                log_message("✓ Valid PDF file!")
            else:
                log_message(f"✗ Not a PDF file (extension: '{ext_lower}')")
        
        # Set up drag and drop
        text.drop_target_register(DND_FILES)
        text.dnd_bind('<<Drop>>', on_drop)
        
        # Add instructions
        log_message("Drag and Drop Test Application")
        log_message("=" * 40)
        log_message("Drag PDF files onto this window to test file detection.")
        log_message("The application will show detailed information about the dropped files.")
        log_message("")
        
        root.mainloop()
        
    except ImportError as e:
        messagebox.showerror("Error", f"tkinterdnd2 not available: {e}")
        sys.exit(1)
    except Exception as e:
        messagebox.showerror("Error", f"Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
