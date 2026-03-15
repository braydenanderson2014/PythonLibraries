# PDF Merge Widget - User Guide

## Overview
The PDF Merge Widget combines multiple PDF documents into a single file. This is perfect for creating comprehensive reports, combining related documents, or consolidating scattered files into one organized document.

---

## Quick Start (Basic Users)

### Step 1: Add PDF Files
1. Click the **"Add PDF Files"** button
2. Select multiple PDF files (hold Ctrl to select multiple)
3. Files appear in the merge list with their page counts

### Step 2: Arrange File Order
- **Drag and Drop**: Drag files up or down to reorder them
- **Move Up/Down Buttons**: Select a file and use arrow buttons
- **Final order determines the page sequence in merged PDF**

### Step 3: Choose Output Settings
1. **Output Filename**: Enter name for the merged PDF
2. **Output Directory**: Choose where to save the file
3. **Default location**: `merge_output` folder

### Step 4: Start Merging
1. Click **"Merge Files"**
2. Monitor the progress bar
3. Merged file will be saved to your chosen location

---

## Advanced Features

### Page Range Selection
**Per-File Page Ranges**:
- Right-click any file in the list
- Select "Set Page Range"
- Specify which pages to include from that file
- Format: `1-5, 10-15` or `1, 3, 5`

### File Reordering
- **Drag and Drop**: Most intuitive method
- **Keyboard**: Use Ctrl+Up/Down arrows
- **Context Menu**: Right-click for move options
- **Preview**: Shows final page order before merging

### Merge Strategies
1. **Simple Merge**: Combine all pages in order
2. **Selective Merge**: Choose specific pages from each file
3. **Interleaved Merge**: Alternate pages from different files
4. **Custom Order**: Complete control over page sequence

### Memory Optimization
- **Smart Processing**: Automatically detects large files
- **Streaming Mode**: Processes files without loading everything into memory
- **Batch Limits**: Prevents memory overload during large merges
- **Progress Tracking**: Real-time memory usage monitoring

---

## Settings Integration

### Default Locations
- Set default merge output directory in Settings → General
- Configure automatic file naming patterns
- Enable/disable confirmation dialogs

### Performance Tuning
- **Memory Limits**: Adjust in Settings → Advanced
- **Processing Threads**: Control CPU usage
- **Temporary Files**: Configure temp directory location

### Quality Settings
- **Compression**: Maintain, reduce, or optimize file size
- **Metadata**: Preserve or merge document properties
- **Bookmarks**: Handle navigation elements

---

## Tips and Best Practices

### For Basic Users:
1. **Check Order**: Always preview file order before merging
2. **Test Small**: Start with a few small files to learn the interface
3. **Naming**: Use descriptive names for merged files
4. **Backup**: Keep original files until you verify the merge

### For Advanced Users:
1. **Page Planning**: Map out exactly which pages you need before starting
2. **Memory Management**: Monitor system resources for large merges
3. **Batch Processing**: Group similar merge operations together
4. **Quality Control**: Verify merged files maintain expected formatting

### Optimization Tips:
- **File Size**: Merge files of similar sizes for better performance
- **Page Count**: Be aware that very large merges may take longer
- **Directory Structure**: Organize source files for easy access
- **Naming Conventions**: Use consistent patterns for output files

---

## File Management

### Source File Operations
- **Add Multiple**: Select many files at once
- **Remove Selected**: Delete files from merge list (not from disk)
- **Clear All**: Empty the entire merge list
- **Refresh**: Update file information and page counts

### Output Management
- **Auto-Naming**: Generates names based on source files
- **Custom Names**: Specify exact output filename
- **Duplicate Handling**: Automatically handles naming conflicts
- **Directory Creation**: Creates output directories if needed

---

## Troubleshooting

### Common Issues:

**"Cannot open PDF file"**
- File may be password-protected
- File might be corrupted
- Try opening in a PDF viewer first
- Check file permissions

**"Merge failed - out of memory"**
- Reduce number of files being merged
- Close other applications
- Split large merges into smaller batches
- Adjust memory limits in Settings

**"Page ranges invalid"**
- Check that page numbers exist in the source file
- Use correct format: `1-5, 10` not `1 to 5, 10`
- Verify page counts are accurate

**"Output file locked"**
- Close the output file if open in another program
- Check directory permissions
- Choose a different output location

### Performance Issues:
- **Slow Processing**: Check available RAM and disk space
- **High CPU Usage**: Reduce concurrent operations
- **Large Files**: Use streaming mode for files >100MB
- **Network Drives**: Copy files locally before merging

---

## Advanced Techniques

### Complex Page Selection
```
File 1: pages 1-10, 20-25
File 2: pages 5-15
File 3: all pages
File 4: pages 1, 5, 10
```

### Batch Merging Workflow
1. Organize source files in folders by merge group
2. Process one group at a time
3. Use consistent naming for outputs
4. Verify each merge before proceeding

### Quality Assurance
- **Page Count Verification**: Check math before merging
- **Content Preview**: Spot-check critical pages
- **File Size Monitoring**: Ensure reasonable output sizes
- **Metadata Review**: Verify document properties

---

## Keyboard Shortcuts
- **Ctrl+O**: Add PDF files
- **Ctrl+A**: Select all files
- **Delete**: Remove selected files
- **Ctrl+Up/Down**: Move files in list
- **Enter**: Start merge process
- **F5**: Refresh file list

---

## Integration Features
- **Search Integration**: Find files using the Search widget
- **Auto-Import**: Automatically detect new PDFs for merging
- **File Operations**: Copy, move, or organize merged files
- **Logging**: Detailed merge operation logs

---

## Technical Specifications
- **Supported Formats**: PDF 1.4 through 2.0
- **Maximum Files**: Limited by available system memory
- **Maximum Pages**: No theoretical limit (practical limit ~10,000 pages)
- **Metadata Handling**: Preserves and merges document properties
- **Bookmark Support**: Maintains navigation structure when possible
- **Compression**: Maintains original compression or applies optimization
