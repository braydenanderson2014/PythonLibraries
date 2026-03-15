# Settings Configuration - User Guide

## Overview
The Settings system in PDF Utility allows you to customize every aspect of the application's behavior. From default directories to advanced performance tuning, these settings ensure the application works exactly how you need it to.

---

## Quick Start (Basic Users)

### Accessing Settings
1. Go to **Tools** menu → **Settings**
2. Or use keyboard shortcut **Ctrl+S**
3. Settings dialog opens with multiple tabs

### Essential Settings to Configure
1. **General Tab**: Set default directories
2. **PDF Tab**: Configure PDF processing options
3. **Interface Tab**: Adjust appearance and behavior
4. **Auto-Import Tab**: Set up automatic file detection

### Saving Settings
1. Click **"Apply"** to save without closing
2. Click **"OK"** to save and close
3. Click **"Cancel"** to discard changes

---

## General Settings

### Default Directories
- **Input Directory**: Default location for selecting files
- **Output Directory**: Where processed files are saved
- **Temporary Directory**: Location for temporary processing files
- **Backup Directory**: Where original files are backed up

### File Management
- **Remember Last Directory**: Save last used locations
- **Auto-Create Directories**: Create output folders automatically
- **File Naming Patterns**: Default naming for processed files
- **Duplicate Handling**: How to handle files with same names

### Application Behavior
- **Startup Behavior**: What tab to show on application start
- **Confirmation Dialogs**: Enable/disable warning messages
- **Auto-Save Settings**: Automatically save configuration changes
- **Session Restore**: Remember open files between sessions

---

## PDF Processing Settings

### Quality and Compression
- **Default Quality**: High, Medium, or Low processing quality
- **Compression Level**: Balance file size vs. quality
- **Image Handling**: How to process embedded images
- **Metadata Preservation**: Keep or remove document properties

### Processing Options
- **Memory Limit**: Maximum RAM usage for processing
- **Processing Threads**: Number of CPU cores to use
- **Batch Size**: How many files to process simultaneously
- **Timeout Settings**: Maximum time for operations

### Advanced PDF Options
- **PDF Version**: Output PDF version compatibility
- **Security Settings**: Default encryption and permissions
- **Form Handling**: How to process PDF forms
- **Annotation Processing**: Keep, remove, or modify annotations

---

## Interface Settings

### Appearance
- **Theme**: Light, Dark, or System theme
- **Font Size**: Interface text size
- **Icon Size**: Toolbar and button icon sizes
- **Color Scheme**: Customize interface colors

### Behavior
- **Window Settings**: Default size and position
- **Tab Behavior**: How tabs open and close
- **List Display**: File list appearance and sorting
- **Progress Indicators**: Style of progress bars and animations

### Accessibility
- **High Contrast**: Enhanced visibility options
- **Keyboard Navigation**: Full keyboard control settings
- **Screen Reader**: Compatibility with assistive technologies
- **Font Options**: Special fonts for readability

---

## Text to Speech Settings

### Voice Configuration
- **Default Voice**: System voice for TTS
- **Speech Rate**: Default speaking speed
- **Volume Level**: Default audio volume
- **Voice Quality**: Balance speed vs. clarity

### Reading Preferences
- **Auto-Advance**: Automatically move between pages
- **Pause Duration**: Length of pauses between sections
- **Highlight Text**: Visual indication of current text
- **Background Reading**: Continue while using other features

### Advanced TTS
- **Language Detection**: Automatic language switching
- **Pronunciation**: Custom pronunciation rules
- **Error Handling**: How to handle unreadable text
- **Audio Export**: Settings for saving audio files

---

## Auto-Import Settings

### Directory Monitoring
- **Watch Directory**: Folder to monitor for new files
- **Include Subdirectories**: Monitor nested folders
- **File Types**: Which file types to auto-import
- **Processing Delay**: Wait time before importing new files

### Import Behavior
- **Auto-Add to Widgets**: Automatically add to specific widgets
- **Notification Settings**: Alerts for new files
- **Duplicate Handling**: How to handle files with same names
- **Processing Rules**: Automatic actions for imported files

### Advanced Monitoring
- **Network Drives**: Monitor shared network folders
- **External Devices**: Watch USB drives and external media
- **Cloud Sync**: Monitor cloud storage folders
- **Performance**: Resource usage for monitoring

---

## Logging Settings

### Log Configuration
- **Log Level**: Detail level (Error, Warning, Info, Debug)
- **Log Location**: Where to save log files
- **Log Rotation**: When to create new log files
- **Log Retention**: How long to keep old logs

### Debug Options
- **Performance Logging**: Track operation times
- **Memory Logging**: Monitor memory usage
- **Error Details**: Verbose error information
- **User Activity**: Track user actions for support

### Log Management
- **Auto-Cleanup**: Automatically delete old logs
- **Compression**: Compress old log files
- **Export Logs**: Save logs for technical support
- **Log Viewer**: Built-in log file viewer

---

## Advanced Settings

### Performance Tuning
- **Memory Management**: Advanced memory allocation settings
- **CPU Optimization**: Processor usage optimization
- **Disk I/O**: File read/write optimization
- **Network Settings**: Remote file access configuration

### Security Options
- **File Permissions**: Default security settings
- **Encryption**: Data protection options
- **Privacy**: User data handling preferences
- **Backup Security**: Protection for backup files

### Development Options
- **Debug Mode**: Enable developer features
- **Plugin Support**: Third-party extension settings
- **API Access**: External application integration
- **Experimental Features**: Beta functionality options

---

## Settings Backup and Restore

### Export Settings
1. Go to Advanced tab
2. Click **"Export Settings"**
3. Choose location to save settings file
4. Settings saved as `.json` file

### Import Settings
1. Go to Advanced tab
2. Click **"Import Settings"**
3. Select previously exported settings file
4. Confirm import and restart application

### Reset to Defaults
1. Go to Advanced tab
2. Click **"Reset All Settings"**
3. Confirm reset operation
4. All settings return to default values

---

## Tips and Best Practices

### For Basic Users:
1. **Start Simple**: Configure only essential settings first
2. **Test Changes**: Try settings with small files first
3. **Backup Settings**: Export settings before making major changes
4. **Document Changes**: Note what you changed for troubleshooting

### For Advanced Users:
1. **Performance Tuning**: Adjust settings based on your hardware
2. **Workflow Optimization**: Configure settings for your specific use cases
3. **Regular Review**: Periodically review and update settings
4. **Multiple Profiles**: Use different settings for different projects

### Setting Recommendations:

#### For General Use:
- Medium quality settings
- Moderate memory usage
- Standard interface theme
- Basic logging enabled

#### For Power Users:
- High quality settings
- Maximum memory allocation
- Advanced keyboard shortcuts
- Detailed logging enabled

#### For Shared Systems:
- Conservative memory usage
- Standard directories only
- Minimal logging
- Reset settings on exit

---

## Troubleshooting Settings

### Common Issues:

**"Settings not saving"**
- Check file permissions in settings directory
- Ensure application isn't running as administrator unnecessarily
- Try exporting and re-importing settings
- Reset to defaults and reconfigure

**"Performance problems after changing settings"**
- Review memory and CPU settings
- Check temporary directory space
- Reduce batch processing sizes
- Monitor resource usage

**"Interface problems"**
- Reset interface settings to defaults
- Check display scaling settings
- Try different theme options
- Clear interface cache

**"Auto-import not working"**
- Verify directory permissions
- Check file type filters
- Ensure monitoring service is running
- Test with small directory first

---

## Settings Migration

### Upgrading Versions
- Settings automatically migrated to new versions
- Backup created before migration
- New features get default values
- Custom settings preserved when possible

### Moving Between Computers
1. Export settings from old computer
2. Install PDF Utility on new computer
3. Import settings file
4. Verify all settings transferred correctly

### Sharing Configurations
- Export settings for team use
- Create standard configuration templates
- Document custom settings for troubleshooting
- Version control settings files for teams

---

## Keyboard Shortcuts for Settings
- **Ctrl+S**: Open settings dialog
- **Ctrl+Tab**: Switch between settings tabs
- **Enter**: Apply current settings
- **Escape**: Cancel and close settings
- **F1**: Context help for current setting

---

## Integration with Other Features
- **Widget Settings**: Widget-specific settings saved globally
- **File Operations**: Settings affect all file operations
- **Search Configuration**: Search behavior controlled by settings
- **Logging Integration**: All operations respect logging settings

---

## Technical Notes
- Settings stored in JSON format for easy editing
- Real-time validation prevents invalid configurations
- Settings changes apply immediately where possible
- Backup settings created automatically before major changes
- Cross-platform compatibility for settings files
