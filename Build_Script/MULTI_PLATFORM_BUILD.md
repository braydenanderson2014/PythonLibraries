# Multi-Platform PyInstaller Build System

This GitHub Actions workflow provides automated, multi-platform building for Python applications using your build CLI. It supports building for Windows, Linux, and macOS across different architectures (x64, x86, ARM64).

## Features

- 🏗️ **Multi-Platform Builds**: Windows, Linux, macOS
- 🔧 **Multi-Architecture**: x64, x86, ARM64 (where supported)
- ⚙️ **Flexible Configuration**: Repository-specific or workflow-level configuration
- 📦 **Automatic Resource Detection**: Icons, configs, data files, templates
- 🎯 **Smart Main File Detection**: Automatic or manual specification
- 🚀 **Release Automation**: Automatic releases on git tags
- 📊 **Build Artifacts**: Organized and downloadable build outputs

## Quick Start

1. **Copy the workflow file** to your repository:
   ```
   .github/workflows/multi-platform-build.yml
   ```

2. **Create build configuration** (optional):
   ```
   .github/build-config.json
   ```

3. **Push to trigger builds**:
   - Push to `main` or `develop` branches
   - Create a git tag for releases
   - Manual trigger from GitHub Actions tab

## Configuration Options

### Repository Configuration (`.github/build-config.json`)

```json
{
  "name": "MyApp",
  "version": "auto",
  "append_version": true,
  "append_date": false,  
  "windowed": false,
  "main_file": "auto",
  "python_version": "3.13.3",
  "build_type": "onefile",
  "platforms": ["windows", "linux", "macos"],
  "architectures": {
    "windows": ["x64", "x86"],
    "linux": ["x64", "arm64"],
    "macos": ["x64", "arm64"]
  },
  "additional_flags": ["--clean"]
}
```

### Configuration Reference

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `name` | string | Repository name | Application name for builds |
| `version` | string | `"auto"` | Version string or "auto" for tag/date |
| `append_version` | boolean | `true` | Append version to build name |
| `append_date` | boolean | `false` | Append date to build name |
| `windowed` | boolean | `false` | Build without console window |
| `main_file` | string | `"auto"` | Main Python file or "auto" |
| `python_version` | string | `"3.13.3"` | Python version to use |
| `build_type` | string | `"onefile"` | "onefile" or "onedir" |
| `platforms` | array | `["windows", "linux", "macos"]` | Platforms to build |
| `architectures` | object | See above | Architecture per platform |
| `additional_flags` | array | `[]` | Extra build CLI flags |

### Advanced Resource Scanning Configuration

```json
{
  "resource_scanning": {
    "directories": {
      "assets": ["icons", "data", "images"],
      "resources": ["icons", "config", "data"], 
      "config": ["config"],
      "configs": ["config"],
      "data": ["data"],
      "templates": ["templates"],
      "views": ["templates"],
      "docs": ["help"],
      "tutorials": ["help"],
      "help": ["help"],
      "images": ["icons"]
    },
    "filters": {
      "icons": ["icon", "splash", "logo"],
      "config": ["config", "settings"],
      "help": ["tutorial", "guide", "manual"]
    },
    "scan_icons": true,
    "scan_config": true,
    "scan_data": true,
    "scan_templates": true,
    "scan_help": true
  }
}
```

The workflow automatically detects your project structure and uses `--set-root` to ensure the build script in `BuildSystems/`, `scripts/`, or `tools/` can access the entire project. Then it uses targeted scanning with `--contains` filtering to avoid false positives.

## Platform & Architecture Matrix

### Windows
- **x64**: Standard 64-bit Windows
- **x86**: 32-bit Windows (legacy support)
- **Runner**: `windows-latest`

### Linux  
- **x64**: Standard 64-bit Linux
- **arm64**: ARM64 Linux (for ARM servers/devices)
- **Runner**: `ubuntu-latest`

### macOS
- **x64**: Intel-based Macs
- **arm64**: Apple Silicon Macs (M1, M2, M3+)
- **Runners**: `macos-13` (Intel), `macos-14` (ARM)

## Version Handling

### Automatic Versioning
- **Git Tags**: Uses tag name (removes 'v' prefix)
- **Branches**: Uses current date (YYYY.MM.DD)
- **Manual**: Set specific version in config

### Version Examples
```bash
# Create a release
git tag v1.2.3
git push origin v1.2.3

# Results in builds named: MyApp-1.2.3-windows-x64.exe
```

## Workflow Triggers

### Automatic Triggers
```yaml
on:
  push:
    branches: [ main, develop ]    # Build on push
    tags: [ 'v*' ]                # Build and release on tags
  pull_request:
    branches: [ main ]            # Test builds on PRs
```

### Manual Trigger
```yaml
workflow_dispatch:
  inputs:
    platforms: 'windows,linux'           # Override platforms
    build_config: '{"windowed": true}'   # Override config
```

## Build Artifacts

### File Naming Convention
```
AppName-Version-Platform-Architecture[.extension]
```

### Examples
- `MyApp-1.2.3-windows-x64.exe`
- `MyApp-1.2.3-linux-arm64`
- `MyApp-1.2.3-macos-x64.tar.gz`

### Artifact Types
- **Windows**: `.exe` (onefile) or `.zip` (onedir)
- **Linux**: Binary (onefile) or `.tar.gz` (onedir)  
- **macOS**: Binary (onefile) or `.tar.gz` (onedir)

## Advanced Features

### Enhanced Resource Detection
The workflow uses intelligent, targeted scanning with `--set-root`, enhanced `--contains` filtering, and naming convention recognition:

#### **Directory Structure Recognition**
- 📁 **Project Root Setup**: Automatically detects if build script is in subdirectory (`BuildSystems/`, `scripts/`, `tools/`) and sets project root appropriately
- 🎯 **Relative Path Scanning**: Uses `./assets`, `./config`, `./docs` etc. for precise targeting

#### **Multi-Level Filtering System**
1. **Priority 1: Prefix-Based Naming** (Most Reliable)
   - `TUTORIAL_welcome.json`, `HELP_howtofunction.json`, `SPLASH_mainsplash.png`
   - `ICON_applogo.png`, `CONFIG_settings.json`, `DATA_userdata.csv`
   
2. **Priority 2: Filename Contains** (Enhanced filtering)
   - Searches filenames first, then file contents for text files
   - `icon_app.png`, `splash_screen.png`, `user_guide.md`
   
3. **Priority 3: Content Search** (For text files)
   - Searches inside tutorials, help, and config files for keywords
   - Works with `.json`, `.xml`, `.md`, `.txt`, `.html` files

#### **Folder-First Scanning Approach**
- � **Tutorials**: Scans `./tutorials/` folder first, then looks for `TUTORIAL_` prefixed files
- � **Help Files**: Scans `./help/` and `./docs/` folders, then looks for `HELP_` prefixed files  
- 🎨 **Assets**: Prioritizes dedicated asset folders before scanning for prefixed files

#### **Smart Resource Categories**
- 🎨 **Icons & Splash**: 
  - Folders: `./assets/`, `./resources/`, `./images/`
  - Prefixes: `ICON_`, `SPLASH_`, `LOGO_`, `BANNER_`
  - Filters: `icon`, `splash`, `logo`
  - Types: `.png`, `.jpg`, `.ico`, `.svg`
- ⚙️ **Configuration**:
  - Folders: `./config/`, `./configs/`
  - Prefixes: `CONFIG_`, `SETTINGS_`, `CFG_`
  - Filters: `config`, `settings`
  - Types: `.json`, `.yaml`, `.toml`, `.ini`
- 📚 **Tutorials & Help**:
  - Folders: `./tutorials/`, `./help/`, `./docs/`
  - Prefixes: `TUTORIAL_`, `HELP_`, `GUIDE_`, `MANUAL_`
  - Filters: `tutorial`, `help`, `guide`, `howto`
  - Types: `.json`, `.xml`, `.md`, `.html`, `.pdf`
- 📊 **Data Files**: 
  - Folders: `./data/`, `./assets/`
  - Prefixes: `DATA_`, `DB_`, `DATASET_`
  - Types: `.csv`, `.json`, `.db`, `.xml`

#### **Benefits of Enhanced Filtering**
- ✅ **No False Positives**: Won't grab files from virtual environments or dependencies
- ✅ **Naming Convention Support**: Recognizes `TUTORIAL_`, `HELP_`, `SPLASH_` file prefixes
- ✅ **Folder-First Priority**: Scans dedicated folders before looking for scattered files
- ✅ **Multi-Layer Filtering**: Filename → Content → Extension matching
- ✅ **GitHub Actions Compatible**: Works perfectly with subdirectory build scripts

### Main File Detection
Automatic detection tries these files in order:
1. `main.py`
2. `app.py`  
3. `__main__.py`
4. `run.py`
5. `{app_name}.py`

### Dependency Installation
Supports multiple dependency formats:
- `requirements.txt`
- `Pipfile` (with Pipenv)
- `pyproject.toml`

## Usage Examples

### Basic Python CLI App
```json
{
  "name": "MyCLI",
  "windowed": false,
  "build_type": "onefile",
  "platforms": ["windows", "linux", "macos"]
}
```

### GUI Application
```json
{
  "name": "MyGUI", 
  "windowed": true,
  "build_type": "onefile",
  "main_file": "gui_main.py",
  "platforms": ["windows", "macos"]
}
```

### Server Application (Linux Only)
```json
{
  "name": "MyServer",
  "windowed": false,
  "platforms": ["linux"],
  "architectures": {
    "linux": ["x64", "arm64"]
  }
}
```

### Windows-Specific Build
```json
{
  "name": "WindowsApp",
  "windowed": true,
  "platforms": ["windows"], 
  "architectures": {
    "windows": ["x64", "x86"]
  },
  "additional_flags": ["--add-data", "assets:assets"]
}
```

## Troubleshooting

### Build Failures
1. **Check Python version compatibility**
2. **Verify dependencies install correctly**
3. **Ensure main file exists and is valid**
4. **Check build CLI output for errors**

### Missing Dependencies
Add to `requirements.txt`:
```
pyinstaller>=6.0
# Your app dependencies here
```

### Architecture Issues
- ARM builds require native runners (may have limited availability)
- Cross-compilation is not supported
- Some Python packages may not support all architectures

## Customization

### Per-Platform Settings
You can add platform-specific configuration:
```json
{
  "platform_specific": {
    "windows": {
      "additional_flags": ["--add-data", "windows_only:data"]
    },
    "linux": {
      "additional_flags": ["--add-data", "linux_only:data"]  
    },
    "macos": {
      "additional_flags": ["--add-data", "macos_only:data"]
    }
  }
}
```

### Custom Build Steps
Modify the workflow to add custom steps:
```yaml
- name: Custom pre-build step
  run: |
    echo "Running custom commands..."
    # Your custom commands here

- name: Build application
  # ... existing build step
```

## Security Considerations

- Builds run in isolated GitHub runners
- No secrets required for basic builds
- Artifacts are stored in GitHub (30-day retention)
- Release creation requires `GITHUB_TOKEN` (automatically provided)

## Getting Started Checklist

- [ ] Copy workflow file to `.github/workflows/`
- [ ] Create `.github/build-config.json` (optional)
- [ ] Ensure your app has a clear main file
- [ ] Add `requirements.txt` or similar
- [ ] Push to trigger first build
- [ ] Check Actions tab for build results
- [ ] Create a git tag to test releases

## Support

For issues with:
- **Workflow**: Check GitHub Actions documentation
- **Build CLI**: Refer to build CLI documentation  
- **PyInstaller**: Check PyInstaller documentation
- **Platform-specific**: Check runner documentation
