# Image Converter Widget - User Guide

## Overview
The Image Converter Widget transforms various image formats into PDFs and converts PDFs to images. This tool is essential for digitizing documents, creating PDF portfolios from images, or extracting visual content from PDFs.

---

## Quick Start (Basic Users)

### Converting Images to PDF

#### Step 1: Add Image Files
1. Click **"Add Image Files"**
2. Select images (JPG, PNG, BMP, TIFF, GIF, WebP)
3. Images appear in the list with thumbnails

#### Step 2: Arrange Images
- **Drag and Drop**: Reorder images as needed
- **Use Arrow Buttons**: Move selected images up/down
- **Image order determines PDF page order**

#### Step 3: Choose Settings
1. **Output Format**: Select "PDF"
2. **Page Size**: Choose A4, Letter, or Custom
3. **Quality**: High, Medium, or Low
4. **Output Directory**: Where to save the PDF

#### Step 4: Convert
1. Click **"Convert to PDF"**
2. Wait for processing to complete
3. Find your PDF in the output directory

### Converting PDF to Images

#### Step 1: Add PDF Files
1. Click **"Add PDF Files"**
2. Select one or more PDF documents
3. Files appear with page count information

#### Step 2: Choose Image Settings
1. **Output Format**: PNG, JPG, TIFF, or BMP
2. **Resolution (DPI)**: 150, 300, 600, or custom
3. **Quality**: For JPG format only
4. **Color Mode**: RGB, Grayscale, or Black & White

#### Step 3: Select Pages
- **All Pages**: Convert entire PDF
- **Page Range**: Specify pages (e.g., 1-5, 10, 15-20)
- **Current Page**: Convert single page only

#### Step 4: Convert
1. Click **"Convert to Images"**
2. Monitor progress for large files
3. Images saved as separate files

---

## Advanced Features

### Batch Processing
- **Multiple PDFs**: Convert several PDFs to images simultaneously
- **Multiple Images**: Create separate PDFs from different image groups
- **Mixed Operations**: Queue both image→PDF and PDF→image conversions

### Image Enhancement
- **Auto-Crop**: Remove excess white space from images
- **Rotation**: Correct image orientation before PDF conversion
- **Scaling**: Resize images to fit standard page sizes
- **Color Correction**: Basic brightness and contrast adjustments

### PDF Page Management
- **Page Selection**: Choose specific pages for conversion
- **Range Processing**: Convert large PDFs in chunks
- **Quality Control**: Preview before batch processing
- **Memory Management**: Handle large files efficiently

### Output Customization
- **Naming Patterns**: Control how output files are named
- **Directory Structure**: Organize outputs by source or type
- **Compression**: Balance quality vs. file size
- **Metadata**: Preserve or add document information

---

## Format Support

### Input Image Formats
- **JPEG/JPG**: High compatibility, lossy compression
- **PNG**: Transparency support, lossless compression
- **TIFF**: Professional quality, multiple pages supported
- **BMP**: Uncompressed, large file sizes
- **GIF**: Animation support (first frame only)
- **WebP**: Modern format, excellent compression

### Output Image Formats
- **PNG**: Best for text and graphics, supports transparency
- **JPEG**: Best for photographs, smaller file sizes
- **TIFF**: Best for archival quality, professional use
- **BMP**: Uncompressed, maximum compatibility

### PDF Specifications
- **Version**: Creates PDF 1.4 compatible files
- **Color Spaces**: RGB, CMYK, Grayscale, Monochrome
- **Compression**: JPEG, ZIP, or uncompressed
- **Page Sizes**: Standard (A4, Letter) or custom dimensions

---

## Settings and Configuration

### Image Quality Settings
- **High Quality (300+ DPI)**: For professional printing
- **Medium Quality (150-300 DPI)**: For screen viewing and basic printing
- **Low Quality (<150 DPI)**: For web use and small file sizes

### PDF Creation Options
- **Page Orientation**: Portrait, Landscape, or Auto-detect
- **Margins**: Standard, Narrow, or Custom
- **Image Fitting**: Stretch, Fit, or Center on page
- **Background**: White, Transparent, or Custom color

### Memory Management
- **Streaming Mode**: For large image collections
- **Batch Size**: Process images in groups to conserve memory
- **Temporary Files**: Automatic cleanup of processing files
- **Progress Monitoring**: Real-time memory and disk usage

---

## Tips and Best Practices

### For Basic Users:
1. **File Organization**: Keep related images in the same folder
2. **Quality Planning**: Choose resolution based on intended use
3. **Format Selection**: Use PNG for text, JPG for photos
4. **Test First**: Try with a few files before batch processing

### For Advanced Users:
1. **Resolution Strategy**: Match output resolution to intended use
2. **Color Space**: Consider CMYK for print, RGB for screen
3. **Compression Balance**: Optimize file size vs. quality
4. **Workflow Integration**: Use with other PDF Utility tools

### Optimization Tips:
- **Sort Images**: Arrange logically before conversion
- **Consistent Sizing**: Use images of similar dimensions
- **Color Consistency**: Match color spaces across images
- **Preview Results**: Check output quality before large batches

---

## Common Workflows

### Digitizing Documents
1. Scan documents as high-quality images
2. Add all images to converter
3. Arrange in proper order
4. Convert to single PDF
5. Use OCR software for searchable text

### Creating Image Portfolios
1. Collect images from various sources
2. Standardize resolution and format
3. Arrange by category or chronology
4. Convert to PDF with descriptive names
5. Add bookmarks using PDF editor

### Extracting PDF Content
1. Open PDF in converter
2. Select specific pages or ranges
3. Choose appropriate image format
4. Set resolution for intended use
5. Process and organize output images

---

## Troubleshooting

### Common Issues:

**"Image file not supported"**
- Check file extension matches actual format
- Try opening image in another program first
- Convert image to supported format
- Check for file corruption

**"PDF conversion failed"**
- Verify PDF is not password-protected
- Check available disk space
- Try converting fewer pages at once
- Close PDF if open in another application

**"Output images are too large/small"**
- Adjust DPI settings for appropriate size
- Check source image resolution
- Modify scaling options
- Consider different output format

**"Out of memory during conversion"**
- Process fewer files at once
- Reduce output resolution
- Close other applications
- Free up system memory

### Quality Issues:
- **Blurry Images**: Increase DPI or use original resolution
- **Large File Sizes**: Reduce quality or use compression
- **Color Problems**: Check color space settings
- **Layout Issues**: Verify page size and margin settings

---

## Advanced Techniques

### Batch Image Processing
```
Workflow Example:
1. Sort images by document type
2. Set consistent naming convention
3. Process each document type separately
4. Combine PDFs using Merge widget
5. Organize final outputs
```

### Resolution Guidelines
- **Scanning Text**: 300 DPI minimum
- **Photo Archives**: 600 DPI for preservation
- **Web Display**: 150 DPI sufficient
- **Professional Print**: 300-600 DPI

### Color Management
- **sRGB**: Standard for web and general use
- **Adobe RGB**: Extended color space for professional work
- **Grayscale**: For text documents and archives
- **Monochrome**: For line art and simple diagrams

---

## Keyboard Shortcuts
- **Ctrl+O**: Add image files
- **Ctrl+Shift+O**: Add PDF files
- **Delete**: Remove selected files
- **Ctrl+Up/Down**: Move files in list
- **Enter**: Start conversion
- **F5**: Refresh file list

---

## Integration Features
- **File List Sharing**: Uses shared file controller with other widgets
- **Search Integration**: Find images and PDFs using Search widget
- **Auto-Import**: Automatically detect new image files
- **Batch Operations**: Works with File Operations menu

---

## Technical Specifications
- **Maximum Image Size**: Limited by available system memory
- **Supported Color Depths**: 1-bit, 8-bit, 16-bit, 24-bit, 32-bit
- **PDF Output**: Compliant with PDF/A standards when configured
- **Processing Speed**: Optimized for both single files and batch operations
- **Memory Usage**: Efficient streaming for large files
- **Concurrent Operations**: Supports background processing
