# PDF Split Widget - User Guide

## Overview
The PDF Split Widget allows you to split large PDF documents into smaller, more manageable files. This is useful for extracting specific pages, creating separate documents from chapters, or reducing file sizes for easier sharing.

---

## Quick Start (Basic Users)

### Step 1: Add PDF Files
1. Click the **"Add PDF Files"** button
2. Select one or more PDF files from your computer
3. Files will appear in the list on the left side

### Step 2: Choose Split Method
- **Split All Pages**: Creates a separate file for each page
- **Split by Range**: Specify page ranges (e.g., 1-5, 10-15)
- **Split by Page Count**: Split into groups of X pages each

### Step 3: Select Output Location
1. Click **"Browse"** next to "Output Directory"
2. Choose where you want the split files to be saved
3. Default location is the `split_output` folder

### Step 4: Start Splitting
1. Click **"Split Selected Files"**
2. Watch the progress bar
3. Files will be saved to your chosen output directory

---

## Advanced Features

### Range-Based Splitting
**Format**: `start-end, start-end, ...`
**Examples**:
- `1-5` - Pages 1 through 5
- `1-5, 10-15, 20-25` - Multiple ranges
- `1, 3, 5` - Individual pages
- `1-10, 15, 20-30` - Mixed ranges and individual pages

### Batch Processing
- Add multiple PDF files to the list
- All files will be processed with the same split settings
- Each file creates its own set of output files

### Custom Output Naming
Output files are automatically named:
- Format: `{original_name}_page_{page_number}.pdf`
- Example: `document.pdf` → `document_page_1.pdf`, `document_page_2.pdf`

### File Management
- **Remove Files**: Select files in the list and click "Remove Selected"
- **Clear All**: Remove all files from the list
- **Preview**: Double-click files to see their details

---

## Settings Integration

### Default Directories
- Set default split output directory in Settings → General
- Enable "Remember Last Directory" to auto-save your preferred locations

### Performance Settings
- Adjust memory usage limits in Settings → Advanced
- Enable/disable progress animations in Settings → Interface

---

## Tips and Best practices

### For Basic Users:
1. **Start Small**: Try splitting a small PDF first to test settings
2. **Check Output**: Always verify output files before deleting originals
3. **Organize**: Use descriptive output directory names
4. **Backup**: Keep original files safe until you're satisfied with results

### For Advanced Users:
1. **Batch Optimization**: Process similar documents together for efficiency
2. **Range Planning**: Plan your page ranges before starting to avoid re-work
3. **Memory Management**: Monitor system resources when processing large files
4. **Automation**: Use consistent naming conventions for easier file management

---

## Troubleshooting

### Common Issues:

**"File is locked or in use"**
- Close the PDF in any PDF viewers
- Check if another application is using the file
- Restart the application if needed

**"Invalid page range"**
- Ensure ranges don't exceed the PDF's page count
- Use correct format: `1-5` not `1 to 5`
- Separate multiple ranges with commas

**"Output directory not accessible"**
- Check if the directory exists
- Verify you have write permissions
- Choose a different output location

**"Out of memory errors"**
- Split fewer files at once
- Close other applications
- Adjust memory settings in Advanced settings

### Performance Tips:
- Process large files individually rather than in batches
- Use SSD storage for output directories when possible
- Close unnecessary applications during processing
- Monitor system memory usage

---

## Keyboard Shortcuts
- **Ctrl+O**: Add PDF files
- **Delete**: Remove selected files from list
- **Ctrl+A**: Select all files in list
- **F5**: Refresh file list
- **Enter**: Start splitting process

---

## Related Features
- **Merge PDFs**: Combine split files back together
- **Search**: Find specific content before splitting
- **File Operations**: Copy, move, or organize split files
- **Logging**: View detailed processing logs in Settings

---

## Technical Notes
- Supports PDF versions 1.4 through 2.0
- Preserves original PDF metadata when possible
- Uses memory-efficient streaming for large files
- Output files maintain original quality and formatting
