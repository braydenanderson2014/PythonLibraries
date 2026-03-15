# File Search Widget - User Guide

## Overview
The File Search Widget provides powerful search capabilities across your file system and PDF content. It helps you quickly locate files by name, content, or metadata, and integrates seamlessly with other PDF Utility widgets for streamlined workflows.

---

## Quick Start (Basic Users)

### Step 1: Choose Search Location
1. Click **"Browse"** to select search directory
2. Choose a folder to search in
3. Enable **"Include Subdirectories"** to search nested folders

### Step 2: Enter Search Terms
1. **Filename Search**: Enter part of the filename
2. **Content Search**: Search inside PDF text
3. **Use wildcards**: `*` for any characters, `?` for single character

### Step 3: Configure Search Options
1. **File Types**: Select PDF, images, or all files
2. **Search Mode**: Filename only, content only, or both
3. **Case Sensitivity**: Enable for exact case matching

### Step 4: Execute Search
1. Click **"Search"**
2. View results in the list below
3. Double-click files to open or use action buttons

---

## Advanced Search Features

### Search Modes

#### Filename Search
- **Exact Match**: Find files with exact name
- **Partial Match**: Find files containing search term
- **Wildcard Search**: Use `*` and `?` for pattern matching
- **Case Sensitivity**: Optional case-sensitive matching

#### Content Search
- **Full Text**: Search entire content of PDF files
- **Keyword Search**: Find specific words or phrases
- **Phrase Search**: Use quotes for exact phrases
- **Boolean Search**: Combine terms with AND, OR, NOT

#### Combined Search
- **Filename AND Content**: Both criteria must match
- **Filename OR Content**: Either criterion can match
- **Advanced Filters**: Combine multiple search criteria

### File Type Filtering

#### Supported File Types
- **PDF Files**: Full content and metadata search
- **Image Files**: Filename and basic metadata search
- **All Files**: Comprehensive file system search
- **Custom Extensions**: Specify exact file types

#### Advanced Filtering
- **File Size**: Filter by minimum/maximum file size
- **Date Modified**: Search by modification date ranges
- **Metadata**: Search PDF properties (title, author, subject)
- **Page Count**: Filter PDFs by number of pages

### Search Operators

#### Wildcard Patterns
- `*.pdf` - All PDF files
- `report*` - Files starting with "report"
- `*2024*` - Files containing "2024"
- `????.pdf` - PDF files with 4-character names

#### Boolean Operators
- `contract AND legal` - Files containing both terms
- `invoice OR receipt` - Files containing either term
- `manual NOT draft` - Files with "manual" but not "draft"
- `"annual report"` - Exact phrase search

---

## Search Configuration

### Directory Selection
- **Root Directory**: Set main search location
- **Include Subdirectories**: Recursive search option
- **Exclude Directories**: Skip specific folders
- **Network Drives**: Search across network locations

### Performance Settings
- **Search Depth**: Limit subdirectory levels
- **File Limit**: Maximum results to display
- **Timeout Settings**: Prevent overly long searches
- **Memory Usage**: Control resource consumption

### Content Indexing
- **Index Creation**: Build searchable content index
- **Index Updates**: Automatic or manual index refresh
- **Index Storage**: Configure index file location
- **Index Optimization**: Periodic index maintenance

---

## Search Results Management

### Results Display
- **List View**: Detailed file information in table format
- **Thumbnail View**: Visual preview of PDF pages
- **Sort Options**: By name, size, date, relevance
- **Filter Results**: Further narrow down displayed results

### File Actions
- **Open File**: Launch in default application
- **Open Location**: Show file in file explorer
- **Add to Widget**: Send to Split, Merge, or other widgets
- **Copy Path**: Copy file path to clipboard

### Batch Operations
- **Select Multiple**: Use Ctrl+Click or Shift+Click
- **Batch Add**: Add multiple files to other widgets
- **Export List**: Save search results to file
- **Print List**: Print search results

---

## Integration with Other Widgets

### Direct Integration
- **Split Widget**: Send found PDFs directly to splitter
- **Merge Widget**: Add search results to merge queue
- **Converter**: Send images or PDFs to converter
- **White Space**: Process found PDFs for blank page removal

### Workflow Enhancement
- **Search → Split**: Find documents, then split specific pages
- **Search → Merge**: Locate related files for merging
- **Search → Convert**: Find images to convert to PDF
- **Search → Clean**: Find and clean problematic documents

### File List Sharing
- **Shared Controller**: Integrates with main file list
- **Cross-Widget**: Files added in search appear in other widgets
- **State Persistence**: Maintains file selections across widgets
- **Unified Management**: Central file handling across application

---

## Tips and Best Practices

### For Basic Users:
1. **Start Broad**: Begin with simple search terms
2. **Use Directories**: Limit search scope to relevant folders
3. **Check Spellings**: Verify search terms are correct
4. **Preview Results**: Use thumbnail view to verify correct files

### For Advanced Users:
1. **Build Indexes**: Create content indexes for faster repeated searches
2. **Use Operators**: Master boolean and wildcard searches
3. **Save Searches**: Remember useful search patterns
4. **Optimize Performance**: Adjust settings for your system

### Search Strategy:
1. **Hierarchical Search**: Start general, then get specific
2. **Multiple Criteria**: Combine filename and content searches
3. **Date Ranges**: Use date filters for recent documents
4. **Size Filters**: Find large files that might need processing

---

## Common Search Patterns

### Document Discovery
```
Search Examples:
- "contract" - Find all contracts
- "*.pdf" AND "2024" - Recent PDF files
- "invoice OR receipt" - Financial documents
- "report*" - All report files
```

### Content-Based Searches
```
Content Examples:
- "quarterly report" - Exact phrase in content
- "budget AND forecast" - Both terms in document
- "summary" NOT "draft" - Summaries excluding drafts
- "page 1 of" - Multi-page documents
```

### Maintenance Tasks
```
Utility Examples:
- Large files: Size > 50MB
- Old files: Modified < 6 months ago
- Blank documents: Page count = 1
- Unprocessed: Not in output directories
```

---

## Troubleshooting

### Common Issues:

**"No results found"**
- Check search directory path
- Verify file types are included
- Try broader search terms
- Check spelling and case sensitivity

**"Search is very slow"**
- Limit search scope to specific directories
- Reduce search depth
- Build content index for faster searches
- Close other applications

**"Content search not working"**
- PDFs may be image-based (no text)
- File may be password-protected
- Content indexing may need to be enabled
- Try OCR processing first

**"Too many results"**
- Add more specific search terms
- Use boolean operators to narrow search
- Apply file type or date filters
- Increase search precision

### Performance Optimization:
- **Indexing**: Build indexes for frequently searched directories
- **Scope Limitation**: Search specific folders rather than entire drives
- **File Type Filtering**: Limit to relevant file types
- **Regular Maintenance**: Clean up search indexes periodically

---

## Advanced Techniques

### Search Automation
1. **Saved Searches**: Create reusable search templates
2. **Scheduled Searches**: Automatic periodic searches
3. **Watch Folders**: Monitor directories for new files
4. **Batch Processing**: Chain searches with other operations

### Content Analysis
1. **Keyword Density**: Analyze term frequency in documents
2. **Document Similarity**: Find related documents
3. **Metadata Extraction**: Search by document properties
4. **Version Control**: Find different versions of documents

### Integration Workflows
```
Example Workflow:
1. Search for "invoice 2024"
2. Filter by date range
3. Add results to Merge widget
4. Create consolidated invoice PDF
5. Use TTS to review final document
```

---

## Keyboard Shortcuts
- **Ctrl+F**: Focus search box
- **Enter**: Execute search
- **Ctrl+A**: Select all results
- **Delete**: Remove selected from results
- **F5**: Refresh search results
- **Ctrl+O**: Open selected file
- **Ctrl+L**: Open file location

---

## Search Index Management

### Index Creation
- **Initial Setup**: First-time index building
- **Incremental Updates**: Add new files to existing index
- **Full Rebuild**: Complete index regeneration
- **Selective Indexing**: Index specific file types only

### Index Maintenance
- **Size Monitoring**: Track index size and growth
- **Performance Tuning**: Optimize index for speed
- **Cleanup**: Remove outdated index entries
- **Backup**: Protect index files from loss

---

## Technical Specifications
- **Search Speed**: Sub-second filename searches, variable content search times
- **Index Size**: Typically 5-10% of original content size
- **File Support**: PDF, images, and most text-based files
- **Memory Usage**: Efficient streaming for large result sets
- **Network Support**: Search across mapped network drives
- **Unicode Support**: Full international character support
