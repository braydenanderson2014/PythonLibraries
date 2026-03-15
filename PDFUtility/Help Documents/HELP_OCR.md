# OCR Widget - User Guide

## Overview
The OCR (Optical Character Recognition) Widget extracts text from scanned PDFs and images. This powerful tool converts non-searchable, image-based documents into editable, searchable text files.

---

## Quick Start (Basic Users)

### Extracting Text from Scanned PDFs

#### Step 1: Add PDF Files
1. Click **"Add PDF Files"**
2. Select one or more scanned PDFs
3. Files appear in the list

#### Step 2: Choose Language
1. Select the document language from the **Language** dropdown
2. Default is English, but many languages are supported
3. Choose the primary language of your documents

#### Step 3: Select Output Format
1. **Text File (.txt)**: Creates a plain text file with extracted content
2. More formats may be available in future versions

#### Step 4: Extract Text
1. Click **"Extract Text with OCR"**
2. Wait for processing (can take time for large documents)
3. Text files are saved to your output directory
4. Preview appears if enabled

---

## Installation Requirements

### Tesseract OCR Engine

OCR functionality requires the Tesseract OCR engine to be installed on your system:

#### Windows Installation
1. Download the installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run the installer (tesseract-ocr-w64-setup.exe)
3. Follow installation wizard
4. Restart PDF Utility

#### Linux Installation
Open terminal and run:
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

For other distributions:
- Fedora: `sudo dnf install tesseract`
- Arch: `sudo pacman -S tesseract`

#### macOS Installation
Using Homebrew:
```bash
brew install tesseract
```

### Installing Additional Languages
By default, only English is installed. To add more languages:

**Windows:**
- Re-run the Tesseract installer
- Select additional language packs during installation

**Linux:**
```bash
sudo apt-get install tesseract-ocr-[lang]
# Example: sudo apt-get install tesseract-ocr-spa  (Spanish)
```

**macOS:**
```bash
brew install tesseract-lang
```

---

## Advanced Features

### Language Support
The OCR widget supports multiple languages:
- English (eng)
- Spanish (spa)
- French (fra)
- German (deu)
- Italian (ita)
- Portuguese (por)
- Russian (rus)
- Chinese Simplified (chi_sim)
- Chinese Traditional (chi_tra)
- Japanese (jpn)
- Korean (kor)
- Arabic (ara)
- Hindi (hin)
- And many more!

### Text Preview
- Preview extracted text before saving
- Useful for verifying accuracy
- Shows results from all processed files
- Can copy or save text directly from preview

### Batch Processing
- Process multiple PDFs at once
- Progress indicator shows current status
- Results saved automatically
- Errors logged but don't stop processing

---

## Best Practices

### Document Quality
For best OCR results:
- **Resolution**: Use PDFs with at least 300 DPI
- **Clarity**: Ensure text is clear and legible
- **Contrast**: High contrast between text and background works best
- **Orientation**: Pages should be right-side up
- **Lighting**: Scans should have even lighting

### File Organization
- Keep original scanned PDFs separate from OCR output
- Use descriptive filenames for easy identification
- Organize by document type or date
- Create backups of important documents

### Language Selection
- Choose the correct language for best accuracy
- For multi-language documents, process separately by language
- Some languages require additional data packs

---

## Common Workflows

### Digitizing Paper Documents
1. Scan physical documents to PDF (300 DPI or higher)
2. Add scanned PDFs to OCR widget
3. Select appropriate language
4. Extract text
5. Review and save results

### Converting Image-based PDFs
1. Add PDF files that contain only images
2. Enable text preview
3. Process with OCR
4. Verify accuracy in preview
5. Save extracted text

### Batch Processing Archives
1. Collect all PDFs needing OCR
2. Add entire batch to widget
3. Select common language
4. Start batch processing
5. Review extraction log

---

## Troubleshooting

### Tesseract Not Found
**Problem**: "Tesseract OCR is not installed" message appears

**Solutions**:
1. Install Tesseract using instructions above
2. Restart PDF Utility after installation
3. On Windows, Tesseract must be in PATH or standard location
4. Click "Check Installation" for detailed instructions

### Poor OCR Accuracy
**Problem**: Extracted text has many errors

**Solutions**:
1. Check document quality (resolution, clarity)
2. Verify correct language is selected
3. Try re-scanning at higher resolution
4. Clean up source images (contrast, brightness)
5. Ensure text is not too small or distorted

### Slow Processing
**Problem**: OCR takes a long time

**Solutions**:
1. This is normal for large documents
2. Process documents in smaller batches
3. High DPI images take longer (but give better results)
4. Be patient - quality OCR requires time

### Missing Languages
**Problem**: Desired language not in dropdown

**Solutions**:
1. Install additional language data for Tesseract
2. See "Installing Additional Languages" section
3. Restart PDF Utility after adding languages

### Memory Issues
**Problem**: Program crashes or freezes during OCR

**Solutions**:
1. Process fewer files at once
2. Close other applications to free memory
3. Check available disk space
4. Restart program and try again with smaller batch

---

## Tips and Best Practices

### OCR Quality Tips
- 📸 **Scan at 300 DPI minimum** for good results
- 🎯 **Choose correct language** before processing
- 👀 **Review results** in preview before saving
- 📝 **Proofread important documents** after OCR
- 🔄 **Re-scan unclear pages** for better accuracy

### Performance Tips
- ⚡ **Batch similar documents** together
- 💾 **Ensure sufficient disk space** for output
- 🎨 **Adjust scan settings** for clearer source images
- 🔍 **Use appropriate resolution** - higher isn't always better

### Organization Tips
- 📁 **Maintain folder structure** for easy retrieval
- 🏷️ **Use consistent naming** for OCR output files
- 📋 **Keep processing logs** for reference
- 🔐 **Backup original files** before processing

---

## Technical Specifications

### Supported Input
- PDF files (any size)
- Image-based or scanned PDFs
- Mixed text/image PDFs
- Multi-page documents

### Output Formats
- Plain text files (.txt)
- UTF-8 encoding for international characters
- Preserves basic page structure
- Future: Searchable PDF output

### Limitations
- OCR accuracy depends on source quality
- Handwritten text may not be recognized
- Complex layouts may affect text order
- Special formatting not preserved
- Processing time increases with document size

### System Requirements
- Tesseract OCR engine installed
- Sufficient RAM (500MB+ recommended)
- Disk space for output files
- Python packages: pytesseract, pdf2image

---

## Integration Features

### File List Controller
- Shares PDF list with other widgets
- Maintains file state across tabs
- Supports drag-and-drop operations

### Settings Integration
- Uses default output directory from settings
- Respects system language preferences
- Saves recent language selection

### Tutorial System
- Built-in tutorial for first-time users
- Step-by-step guidance through features
- Accessible from Help menu

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+O | Add PDF Files |
| Delete | Remove Selected Files |
| Ctrl+A | Select All Files |
| Ctrl+Shift+C | Copy Preview Text |
| Ctrl+S | Save Preview Text |

---

## Frequently Asked Questions

**Q: Is OCR 100% accurate?**
A: No, accuracy depends on source document quality. High-quality scans typically achieve 95%+ accuracy, but handwriting and poor scans will have lower accuracy.

**Q: Can I OCR handwritten documents?**
A: Tesseract is designed for printed text. Handwriting recognition requires specialized tools and is not currently supported.

**Q: How long does OCR take?**
A: Processing time varies: 
- Single page: 1-5 seconds
- 10 pages: 10-50 seconds  
- 100 pages: 2-8 minutes
Higher resolution and complex layouts take longer.

**Q: What languages are supported?**
A: Over 100 languages are available for Tesseract. The widget shows languages installed on your system. Install additional language packs as needed.

**Q: Can I process password-protected PDFs?**
A: PDFs must be decrypted before OCR processing. Use PDF editing software to remove password protection first.

**Q: Will OCR work on photos of documents?**
A: Yes, if the photo is clear and high-resolution. For best results, use dedicated scanning apps or scanners instead of phone cameras.

---

## Support and Resources

### Getting Help
- Use the Help menu → "Report an Issue" for problems
- Check the tutorial system for guided walkthroughs
- Review logs for error details

### External Resources
- Tesseract Documentation: https://github.com/tesseract-ocr/tesseract
- OCR Best Practices: Various online guides
- Language Data: https://github.com/tesseract-ocr/tessdata

### Community
- Report bugs through the issue reporting system
- Request features via the feedback system
- Share tips and workflows with other users

---

*Last updated: February 2026*
