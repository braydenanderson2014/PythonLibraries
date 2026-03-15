# Drag and Drop Debugging Guide

## Issue
The drag and drop functionality was registering drop events but not properly detecting PDF file extensions.

## Solution
The problem was in the file path processing. tkinterdnd2 can provide file paths in various formats that need to be cleaned up before extension detection:

1. **Curly braces**: Some platforms wrap paths in `{}`
2. **Extra whitespace**: Leading/trailing spaces
3. **Multiple separators**: Files can be separated by space, semicolon, etc.
4. **Case sensitivity**: Extensions might be uppercase

## Fixed Methods

### `on_file_drop(event)`
- Better parsing of `event.data`
- Handles multiple file separators
- More robust string processing

### `add_dropped_file(file_path)`
- Cleans up file paths (removes braces, whitespace)
- Uses `os.path.splitext()` for reliable extension detection
- Case-insensitive extension comparison
- File existence checking
- Duplicate prevention
- Better error messages

## Testing Tools

### `debug_drag_drop.py`
A standalone test application that shows exactly what data is received from drag and drop events. Run this to debug issues:

```bash
python debug_drag_drop.py
```

### `test_file_detection.py`
Tests the file extension detection logic with various input formats:

```bash
python test_file_detection.py
```

### `test_drag_drop.pdf`
A simple test PDF file for drag and drop testing.

## Common Issues and Solutions

1. **"File is not a valid PDF" error**
   - Check the file path in logs for extra characters
   - Use the debug tool to see raw event data
   - File might have spaces or special characters

2. **Drag and drop not working at all**
   - Check if tkinterdnd2 is installed: `pip install tkinterdnd2`
   - Look for error messages in the logs
   - Try the debug tool first

3. **Multiple files not detected**
   - The improved parsing handles various separators
   - Check logs to see how files are being split

## Log Messages
The application now provides detailed logging for drag and drop operations:
- Raw event data
- Cleaned file paths
- Extension detection
- File existence checks
- Duplicate detection

Check the application logs for detailed debugging information.
