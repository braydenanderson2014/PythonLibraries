# File Search Widget - User Guide

## Overview
The File Search Widget provides powerful search capabilities across your file system and PDF content with an enhanced, professional interface. It features a modern dual-panel layout with advanced search criteria on the left and comprehensive results management on the right, seamlessly integrating with other PDF Utility widgets for streamlined workflows.

## Recent Interface Enhancements
- **Modern Dual-Panel Layout**: Search criteria and results displayed side-by-side for improved workflow
- **Professional Styling**: Clean, modern interface with intuitive color coding and clear visual boundaries
- **Enhanced Results Table**: Comprehensive column headers showing Name, Path, Size, Modified Date, Type, and Directory
- **Keep Selection Feature**: Option to maintain search results when performing new searches
- **Progress Tracking**: Real-time search progress with status updates and cancellation options
- **Responsive Design**: Flexible layout that adapts to different window sizes

---

## Quick Start (Basic Users)

### Step 1: Choose Search Location
1. In the **Search Options** panel (left side), click **"Browse"** to select search directory
2. Choose a folder to search in
3. Enable **"Include Subdirectories"** to search nested folders recursively

### Step 2: Configure Search Criteria
1. **Search Location**: Set your target directory path
2. **Filename Criteria**: Configure filename pattern filters
3. **File Type Filter**: Select PDF, Text, Images, Documents, or All files
4. **File Size Filter**: Set minimum and maximum file size limits (optional)
5. **Date Filter**: Enable date-based filtering for recent files (optional)

### Step 3: Enter Search Terms
1. **Filename Search**: Enter part of the filename or use wildcards
2. **Content Search**: Search inside PDF text content
3. **Use patterns**: `*` for any characters, `?` for single character
4. **Case Sensitivity**: Toggle for exact case matching

### Step 4: Execute and Manage Search
1. Click **"Search"** to start the search process
2. Monitor progress in the status bar with real-time updates
3. View comprehensive results in the **Search Results** table (right side)
4. Use **"Keep selection"** checkbox to maintain results across multiple searches
5. **Stop** search anytime using the stop button
6. **Clear** results when needed for a fresh start

### Step 5: Work with Results
1. **Column Headers**: View detailed information (Name, Path, Size, Modified, Type, Directory)
2. **File Actions**: Double-click to open, or use action buttons
3. **Export Results**: Save search results to file for later reference
4. **Integration**: Add found files directly to other PDF Utility widgets

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

## Enhanced Search Results Management

### Professional Results Display
- **Comprehensive Table View**: Detailed file information with sortable columns
  - **Name**: Filename with extension
  - **Path**: Full file path for easy location
  - **Size**: File size in human-readable format
  - **Modified**: Last modification date and time
  - **Type**: File type classification
  - **Directory**: Parent directory name
- **Alternating Row Colors**: Enhanced readability with professional styling
- **Resizable Columns**: Adjust column widths to fit your content
- **Grid Lines**: Clear visual separation for easy data scanning

### Advanced Results Features
- **Keep Selection**: Maintain search results when performing new searches
- **Real-time Progress**: Live updates during search execution with progress bar
- **Search Status**: Detailed status messages showing current search activity
- **Result Count**: Live count of files found during and after search
- **Export Results**: Save comprehensive search results to file for documentation

### File Actions
- **📄 Open File**: Launch file in default application
- **📁 Open Folder**: Show file location in file explorer  
- **➕ Add PDFs to List**: Send selected PDFs directly to other widgets
- **Context Menu**: Right-click for additional file operations
- **Keyboard Shortcuts**: Standard shortcuts for common actions

### Search Management
- **Search Control**: Start, stop, and clear searches with dedicated buttons
- **Progress Monitoring**: Real-time feedback on search progress and performance
- **Status Updates**: Detailed information about search state and results
- **Error Handling**: Clear messaging for search issues or limitations

### Batch Operations
- **Multi-Selection**: Use Ctrl+Click or Shift+Click for multiple file selection
- **Batch Integration**: Add multiple files to Split, Merge, or Converter widgets simultaneously
- **Selective Processing**: Choose specific files from large result sets
- **Workflow Automation**: Chain search results directly into processing workflows

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

## Interface Navigation

### Layout Overview
- **Left Panel - Search Options**: All search criteria and configuration options
  - Search location and directory browsing
  - Filename pattern filters
  - File type and size filters
  - Date-based filtering options
  - Content search parameters
- **Right Panel - Search Results**: Comprehensive results display and management
  - Professional table with sortable columns
  - Keep selection checkbox for workflow continuity
  - Export results functionality
  - File action buttons
- **Status Bar**: Real-time search progress and status information
  - Current search activity updates
  - Progress bar with completion percentage
  - Search statistics and result counts

### User Experience Enhancements
- **Visual Boundaries**: Clear separation between search criteria and results
- **Professional Styling**: Modern color scheme with intuitive visual cues
- **Responsive Design**: Layout adapts to different window sizes
- **Consistent Controls**: Standardized button styling and behavior
- **Progress Feedback**: Real-time updates during search operations

### Keyboard Shortcuts
- **Ctrl+F**: Focus search criteria
- **Enter**: Execute search from any search field
- **Ctrl+A**: Select all results in table
- **Delete**: Clear selected results
- **F5**: Refresh and restart search
- **Ctrl+O**: Open selected file
- **Ctrl+L**: Open file location in explorer
- **Escape**: Stop current search operation

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
