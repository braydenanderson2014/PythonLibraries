# PyInstaller Build Tool Enhanced - Update System Setup

## Overview
The PyInstaller Build Tool Enhanced now includes a self-updating system that can check for and install updates directly from a GitHub repository.

## Setup Instructions

### 1. Create GitHub Repository
1. Create a new GitHub repository (e.g., `pyinstaller-build-tool`)
2. Upload your enhanced build script to the repository
3. Create releases with tagged versions

### 2. Configure Update System
Edit the `UPDATE_CONFIG` in `build_gui_enhanced.py`:

```python
UPDATE_CONFIG = {
    "repo_owner": "your-github-username",     # Your GitHub username
    "repo_name": "pyinstaller-build-tool",   # Your repository name  
    "current_version": "2.0.0-enhanced"      # Current version number
}
```

### 3. Create Releases
1. Go to your GitHub repository
2. Click "Releases" > "Create a new release"
3. Tag version: `v2.1.0` (or your version number)
4. Release title: `PyInstaller Build Tool Enhanced v2.1.0`
5. Upload your script file (either `.py` or compiled `.exe`)

### 4. Usage
Users can now update with:
```bash
python build_gui_enhanced.py --update
```

## Update Process
1. **Check**: Contacts GitHub API to check for latest release
2. **Compare**: Compares current version with latest available
3. **Download**: Downloads the new version if available
4. **Backup**: Creates automatic backup of current version
5. **Install**: Replaces current script with new version
6. **Rollback**: Restores backup if installation fails

## Features
- ✅ Automatic version checking
- ✅ Secure download from GitHub releases
- ✅ Automatic backup creation
- ✅ Rollback on failure
- ✅ Cross-platform support (Windows/Linux/macOS)
- ✅ Progress indication during download
- ✅ Release notes display

## Security Notes
- Only downloads from official GitHub releases
- Verifies file integrity during download
- Creates backups before any changes
- Uses secure HTTPS connections

## Example Output
```
🚀 PyInstaller Build Tool - Update System
==================================================
🔍 Checking for updates...
   Repository: username/pyinstaller-build-tool
   Current version: 2.0.0-enhanced
   Latest version: 2.1.0
🎉 New version available!
   Release: PyInstaller Build Tool Enhanced v2.1.0
   Release notes:
     - Added self-updating system
     - Enhanced virtual environment management
     - Improved project creation
📥 Downloading update from: https://github.com/...
   Progress: 100%
✅ Download completed!
🔄 Installing update...
   Creating backup: build_gui_enhanced.py.backup.20250803_143052
   Replacing Python script...
✅ Update installed successfully!
💡 Restart the application to use the new version
```

## Repository Structure
```
your-repo/
├── build_gui_enhanced.py          # Main script
├── README.md                      # Documentation
├── CHANGELOG.md                   # Version history
└── releases/                      # Release assets
    ├── v2.0.0/
    ├── v2.1.0/
    └── ...
```

## Version Management
- Use semantic versioning (e.g., 2.1.0)
- Tag releases with `v` prefix (e.g., v2.1.0)
- Update `UPDATE_CONFIG["current_version"]` with each release
- Include clear release notes for users

## Troubleshooting
- **404 Error**: Repository or release not found - check config
- **Network Error**: Check internet connection and GitHub status
- **Permission Error**: Run as administrator or check file permissions
- **Backup Issues**: Ensure write permissions in script directory
