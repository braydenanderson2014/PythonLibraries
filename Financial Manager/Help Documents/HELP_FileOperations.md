# File Operations - User Guide

## Overview
The File Operations system provides essential file management capabilities within PDF Utility. These tools allow you to copy, move, duplicate, and delete files directly from the application, streamlining your document management workflow without switching to external file managers.

---

## Quick Start (Basic Users)

### Accessing File Operations
1. Select files in any widget's file list
2. Go to **Tools** menu → **File Operations**
3. Choose desired operation from submenu

### Basic Operations
- **Copy Files**: Create copies in a new location
- **Duplicate Files**: Create copies in the same directory
- **Delete Files**: Remove files from disk (with confirmation)
- **Show in Explorer**: Open file location in system file manager

### Safety Features
- **Confirmation Dialogs**: Verify before destructive operations
- **Undo Capability**: Reverse recent operations when possible
- **Recycle Bin**: Deleted files go to system recycle bin
- **Progress Tracking**: Monitor operation progress for large files

---

## Copy Operations

### Single File Copy
1. Select a file in any file list
2. Choose **Tools** → **File Operations** → **Copy Files**
3. Select destination directory
4. Confirm copy operation

### Batch File Copy
1. Select multiple files (Ctrl+click or Shift+click)
2. Choose **Tools** → **File Operations** → **Copy Files**
3. Select destination directory
4. All selected files copied to destination

### Advanced Copy Options
- **Preserve Timestamps**: Maintain original file dates
- **Copy Subdirectories**: Include nested folder structure
- **Conflict Resolution**: Handle duplicate names automatically
- **Verification**: Verify copy integrity after operation

### Copy Settings
- **Default Destinations**: Set preferred copy locations
- **Naming Patterns**: How to handle name conflicts
- **Progress Display**: Show detailed progress for large operations
- **Error Handling**: How to handle copy failures

---

## Move Operations

### File Moving
1. Select files to move
2. Choose **Tools** → **File Operations** → **Move Files**
3. Select destination directory
4. Files moved from original location

### Move vs Copy
- **Move**: File removed from original location
- **Copy**: Original file remains unchanged
- **Cut/Paste**: Alternative move operation
- **Cross-Drive**: Automatic copy+delete for different drives

### Safety Considerations
- **Confirmation Required**: Always confirm move operations
- **Backup Recommendation**: Consider backing up important files first
- **Undo Limitation**: Move operations harder to undo than copies
- **Permission Verification**: Ensure write access to destination

---

## Duplicate Operations

### Creating Duplicates
1. Select files to duplicate
2. Choose **Tools** → **File Operations** → **Duplicate Files**
3. Duplicates created in same directory with modified names

### Naming Conventions
- **Default Pattern**: `filename_copy.extension`
- **Numbered Copies**: `filename_copy_1.extension`, `filename_copy_2.extension`
- **Custom Patterns**: Configure your own naming scheme
- **Date Stamps**: Include creation date in duplicate names

### Use Cases
- **Backup Before Processing**: Create safety copies before modification
- **Template Creation**: Duplicate files for use as templates
- **Version Control**: Maintain multiple versions of documents
- **Testing**: Create copies for experimental processing

---

## Delete Operations

### Safe Deletion
1. Select files to delete
2. Choose **Tools** → **File Operations** → **Delete Files**
3. Confirm deletion in dialog
4. Files moved to recycle bin (by default)

### Deletion Options
- **Recycle Bin**: Safe deletion allowing recovery
- **Permanent Delete**: Immediate file removal (use with caution)
- **Confirmation Levels**: Multiple confirmation for important files
- **Batch Deletion**: Delete multiple files simultaneously

### Recovery Options
- **Recycle Bin Recovery**: Restore from system recycle bin
- **Backup Restoration**: Restore from automatic backups
- **Version History**: Access previous versions if available
- **Undo Operation**: Immediate undo for recent deletions

---

## Directory Operations

### Directory Management
- **Create Directories**: Make new folders for organization
- **Copy Directories**: Copy entire folder structures
- **Move Directories**: Relocate folders and contents
- **Delete Directories**: Remove folders and all contents

### Structure Preservation
- **Maintain Hierarchy**: Keep folder organization intact
- **Permission Inheritance**: Preserve directory permissions
- **Metadata Preservation**: Maintain folder properties
- **Link Handling**: Properly handle symbolic links and shortcuts

---

## Batch Operations

### Multi-File Processing
- **Select All**: Process all files in current list
- **Select by Pattern**: Choose files matching criteria
- **Select by Type**: Choose all PDFs, images, etc.
- **Custom Selection**: Manual multi-file selection

### Batch Operation Features
- **Progress Monitoring**: Real-time status for all operations
- **Error Collection**: Continue processing despite individual failures
- **Summary Reports**: Detailed results of batch operations
- **Cancellation**: Stop batch operations in progress

### Performance Optimization
- **Parallel Processing**: Multiple operations simultaneously
- **Memory Management**: Efficient handling of large file sets
- **Disk Optimization**: Minimize disk I/O during operations
- **Priority Control**: Important operations processed first

---

## Integration Features

### Widget Integration
- **Shared File Lists**: Operations work across all widgets
- **State Synchronization**: File changes reflected everywhere
- **Processing Chains**: Combine file operations with processing
- **Workflow Enhancement**: Seamless integration with PDF operations

### Search Integration
- **Search Results**: Operate on search results directly
- **Filter Operations**: Apply operations to filtered file sets
- **Find and Process**: Locate files then operate on them
- **Bulk Management**: Manage large result sets efficiently

### Auto-Import Integration
- **Imported File Operations**: Automatically process imported files
- **Workflow Automation**: Chain operations with auto-import
- **Rule-Based Operations**: Automatic operations based on file properties
- **Monitoring Integration**: Track file operations in auto-import logs

---

## Tips and Best Practices

### For Basic Users:
1. **Always Confirm**: Verify operations before executing
2. **Test Small**: Try operations on a few files first
3. **Backup Important**: Create backups before major operations
4. **Use Recycle Bin**: Prefer safe deletion over permanent removal

### For Advanced Users:
1. **Batch Efficiently**: Group similar operations for better performance
2. **Monitor Resources**: Watch system resources during large operations
3. **Plan Workflows**: Design efficient file management workflows
4. **Error Handling**: Develop strategies for handling operation failures

### Safety Practices:
- **Regular Backups**: Maintain current backups of important files
- **Test Destinations**: Verify destination directories exist and are writable
- **Verify Results**: Check operation results before deleting originals
- **Document Changes**: Keep records of major file reorganizations

---

## Error Handling

### Common Errors
- **Permission Denied**: Insufficient rights to access files/directories
- **File in Use**: Cannot operate on files open in other applications
- **Disk Full**: Insufficient space for copy/move operations
- **Network Issues**: Problems accessing network drives

### Error Resolution
- **Retry Logic**: Automatic retry for temporary failures
- **Alternative Actions**: Suggest alternative operations when possible
- **Error Reporting**: Detailed information about operation failures
- **Recovery Options**: Ways to complete partially failed operations

### Prevention Strategies
- **Pre-Operation Checks**: Verify conditions before starting operations
- **Resource Monitoring**: Check disk space and memory before large operations
- **Permission Verification**: Ensure proper access rights
- **Conflict Detection**: Identify potential issues before they occur

---

## Advanced Features

### Scripting Support
- **Command Line Interface**: Execute operations from scripts
- **API Integration**: Programmatic access to file operations
- **Automation**: Schedule regular file operations
- **Custom Operations**: Define specialized file handling procedures

### Network Operations
- **Remote File Access**: Operations on network shares and remote drives
- **Cloud Integration**: Work with cloud storage services
- **Synchronization**: Keep local and remote files synchronized
- **Cached Operations**: Optimize performance for network files

### Security Features
- **Access Control**: Respect file and directory permissions
- **Audit Logging**: Track all file operations for security
- **Encryption Support**: Handle encrypted files appropriately
- **Secure Deletion**: Securely overwrite sensitive files

---

## Keyboard Shortcuts
- **Ctrl+C**: Copy selected files
- **Ctrl+X**: Cut selected files
- **Ctrl+V**: Paste files
- **Delete**: Delete selected files
- **Ctrl+D**: Duplicate selected files
- **F5**: Refresh file list
- **Ctrl+A**: Select all files

---

## Performance Considerations

### Large File Handling
- **Streaming Operations**: Efficient processing of large files
- **Progress Monitoring**: Track progress for long operations
- **Memory Management**: Prevent memory issues during large operations
- **Disk Optimization**: Minimize fragmentation and optimize I/O

### System Impact
- **Resource Monitoring**: Track CPU, memory, and disk usage
- **Background Processing**: Non-blocking operations when possible
- **Priority Management**: Balance operation speed with system responsiveness
- **Throttling**: Automatically slow operations if system becomes busy

---

## Technical Specifications
- **File Size Limits**: No theoretical limits (practical limits based on available storage)
- **Concurrent Operations**: Multiple operations can run simultaneously
- **Network Support**: Full support for UNC paths and mapped drives
- **Unicode Support**: Proper handling of international file names
- **Metadata Preservation**: Maintains file timestamps and attributes
- **Error Recovery**: Robust error handling and recovery mechanisms
