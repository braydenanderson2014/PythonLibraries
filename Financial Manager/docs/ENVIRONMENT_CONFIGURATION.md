# Environment Configuration Guide

## Overview
The PyInstaller Build Tool Enhanced now uses environment-based configuration through the `Build_Script.env` file. This approach provides better security, easier management, and prevents accidental exposure of sensitive information.

## Setup

### 1. Create Environment File
Copy the example file and customize it:
```bash
cp Build_Script.env.example Build_Script.env
```

### 2. Edit Configuration
Open `Build_Script.env` and update the following key settings:

```env
# Required: Your GitHub repository details
GITHUB_REPO_OWNER=your-actual-username
GITHUB_REPO_NAME=your-repository-name
CURRENT_VERSION=2.0.0-enhanced

# Optional: Customize other settings
DEFAULT_PROJECT_AUTHOR=Your Real Name
BUILD_TOOL_NAME=My Custom Build Tool
```

## Configuration Options

### GitHub Repository Settings
- `GITHUB_REPO_OWNER`: Your GitHub username
- `GITHUB_REPO_NAME`: Repository name for the build tool
- `CURRENT_VERSION`: Current version (update this with each release)

### Build Tool Settings
- `BUILD_TOOL_NAME`: Display name for the tool
- `BUILD_TOOL_AUTHOR`: Author name shown in version info
- `BUILD_TOOL_DESCRIPTION`: Tool description

### Update System Settings
- `UPDATE_CHECK_TIMEOUT`: Timeout for update checks (seconds)
- `UPDATE_AUTO_CONFIRM`: Auto-confirm updates (true/false)
- `UPDATE_CREATE_BACKUP`: Create backups before updates (true/false)

### Virtual Environment Settings
- `DEFAULT_VENV_NAME`: Default virtual environment name
- `VENV_AUTO_INSTALL`: Auto-install in virtual environments (true/false)

### Project Creation Defaults
- `DEFAULT_PROJECT_VERSION`: Default version for new projects
- `DEFAULT_PROJECT_AUTHOR`: Default author for new projects

### Advanced Settings
- `DEBUG_MODE`: Enable debug output (true/false)
- `VERBOSE_OUTPUT`: Enable verbose logging (true/false)
- `SAFE_MODE`: Enable safety checks (true/false)

## Security Benefits

### 1. Separation of Concerns
- Configuration is separate from code
- Easier to manage different environments (dev/prod)
- No hardcoded values in source code

### 2. Git Safety
- Add `Build_Script.env` to `.gitignore`
- Keep `Build_Script.env.example` in version control
- No accidental exposure of sensitive data

### 3. Easy Customization
- Each developer can have their own settings
- No need to modify source code for configuration
- Team can share example file for consistency

## Usage Examples

### Check Current Configuration
```bash
python build_gui_enhanced.py --version
```

### Update with Custom Repository
Edit `Build_Script.env`:
```env
GITHUB_REPO_OWNER=mycompany
GITHUB_REPO_NAME=our-build-tool
```

Then run:
```bash
python build_gui_enhanced.py --update
```

### Create Projects with Custom Defaults
Edit `Build_Script.env`:
```env
DEFAULT_PROJECT_AUTHOR=Development Team
DEFAULT_PROJECT_VERSION=0.1.0
```

Then run:
```bash
python build_gui_enhanced.py --new MyProject
```

## Fallback Behavior

If `Build_Script.env` is not found, the tool will:
1. Use built-in default values
2. Show a warning in version output
3. Continue to function normally
4. Display helpful setup instructions

## Best Practices

### 1. Repository Setup
```bash
# In your project directory:
cp Build_Script.env.example Build_Script.env
echo "Build_Script.env" >> .gitignore
git add Build_Script.env.example
git commit -m "Add environment configuration"
```

### 2. Team Distribution
- Include `Build_Script.env.example` in repository
- Document required settings in README
- Each team member creates their own `Build_Script.env`

### 3. Version Management
- Update `CURRENT_VERSION` before releases
- Keep example file updated with new options
- Document breaking changes in configuration

## Troubleshooting

### Configuration Not Loading
- Check file exists: `Build_Script.env`
- Verify file format (KEY=value)
- Check for syntax errors in file

### Wrong Repository
- Verify `GITHUB_REPO_OWNER` and `GITHUB_REPO_NAME`
- Check repository exists and is public
- Ensure releases are published

### Updates Not Working
- Check internet connectivity
- Verify GitHub repository access
- Check `UPDATE_CHECK_TIMEOUT` setting

## Migration from Old System

If upgrading from the old hardcoded configuration:
1. Create `Build_Script.env` from example
2. Copy your old settings to the new file
3. Remove old `UPDATE_CONFIG` from code (if customized)
4. Test with `--version` command
