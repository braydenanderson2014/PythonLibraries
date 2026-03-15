# Commercial PDF Utility - Configuration Guide

## 🎯 Overview
Your PDF Utility has been successfully configured for commercial distribution with the following changes:

### ✅ Features Removed
- **PDF Editor Tab**: Commented out in main_application.py (lines 268-273)
- **Settings Menu**: Commented out in main_application.py (lines 363-367)

### ✅ Features Added
- **Update System**: Automatic GitHub-based update checking
- **Check for Updates Menu**: Added to Help menu
- **Environment Configuration**: .env file for easy setup

## 🔧 Required Configuration

### 1. Update .env File
Edit the `.env` file with your repository details:

```env
# GitHub Repository Configuration
GITHUB_OWNER=YOUR_GITHUB_USERNAME
GITHUB_REPO=YOUR_REPO_NAME
GITHUB_TOKEN=your_github_personal_access_token

# Update Check Settings  
UPDATE_CHECK_URL=https://api.github.com/repos/{owner}/{repo}/releases/latest
UPDATE_DOWNLOAD_URL=https://github.com/{owner}/{repo}/releases/latest/download/
UPDATE_CHECK_INTERVAL=86400

# Version Information
CURRENT_VERSION=1.0.0
APP_NAME=PDF Utility

# Update File Names (adjust based on your release naming)
WINDOWS_EXECUTABLE=PDFUtility-Setup.exe
WINDOWS_PORTABLE=PDFUtility-Portable.zip
```

### 2. GitHub Personal Access Token (Optional but Recommended)
1. Go to GitHub Settings > Developer Settings > Personal Access Tokens
2. Generate a new token with `public_repo` scope
3. Add it to the `GITHUB_TOKEN` field in .env
4. This increases API rate limits and allows private repositories

### 3. Release Process
For the update system to work, follow this release process:

1. **Tag your releases** in GitHub (e.g., v1.0.1, v1.1.0)
2. **Create releases** with release notes in the body
3. **Upload your executables** as release assets
4. **Update CURRENT_VERSION** in .env before building new versions

## 🚀 How the Update System Works

### Automatic Checking
- Checks for updates every 24 hours (configurable)
- Runs silently in the background
- Only shows dialog if update is available

### Manual Checking
- Users can check via "Help > Check for Updates"
- Shows immediate feedback
- Displays "no updates" message if current

### Update Dialog Features
- Shows version information
- Displays release notes
- "Download Update" - opens browser to release page
- "Remind Me Later" - dismisses dialog
- "Skip This Version" - won't show this version again

## 📁 New Files Created

### `update_system.py`
Main update functionality:
- `UpdateChecker` - Background thread for checking updates
- `UpdateDialog` - UI for showing update information  
- `UpdateManager` - Main coordinator class

### `.env`
Configuration file for:
- GitHub repository details
- Update check settings
- Version information
- File naming conventions

## 🔨 Building for Distribution

### 1. Update Version
Before each build, update the version in `.env`:
```env
CURRENT_VERSION=1.0.1
```

### 2. Build with PyInstaller
Use your existing build script:
```bash
python build_script.py
```

### 3. Create GitHub Release
1. Push your code to GitHub
2. Create a new release with tag (e.g., v1.0.1)
3. Upload the built executable
4. Add release notes describing changes

## 🎯 Features for Commercial Use

### Professional Appearance
- Removed development/settings features
- Clean, focused interface
- Professional update system

### Easy Updates
- Automatic update notifications
- One-click download process
- Version skipping capability

### Configurable
- Easy repository switching
- Customizable update intervals
- Flexible file naming

## 🔍 Testing

To test the update system:

1. **Set a lower version** in .env (e.g., 0.9.0)
2. **Create a release** on GitHub with higher version
3. **Run the application** and check for updates manually
4. **Verify** the update dialog appears with correct information

## 📈 Distribution Strategy

### Version Numbering
- Use semantic versioning (e.g., 1.0.0)
- Increment appropriately:
  - Major: Breaking changes (2.0.0)
  - Minor: New features (1.1.0)  
  - Patch: Bug fixes (1.0.1)

### Release Notes
- Keep them user-friendly
- Highlight new features and fixes
- Mention any known issues

### File Naming
- Use consistent naming in releases
- Update .env file naming if changed
- Consider platform-specific names

## 🛡️ Security Notes

- GitHub tokens should be kept private
- Consider using organization accounts for commercial releases
- Monitor API rate limits for high-volume applications

## 📞 Support

For any issues with the update system or commercial configuration:
1. Check the .env file configuration
2. Verify GitHub repository settings
3. Test with manual update checks
4. Review console output for error messages
