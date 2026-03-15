# BuildCLI Build System

BuildCLI's comprehensive build system provides persistent configuration management for creating executables from Python scripts using multiple build tools including PyInstaller, cx_Freeze, Nuitka, and custom build scripts.

## Key Features

### 🎯 **Configuration Memory System**
- **Persistent Configurations**: Save and reuse build settings across sessions
- **Step-by-Step Building**: Add configuration options incrementally
- **Command Chaining**: Chain multiple build commands in one execution
- **Reset & Restore**: Reset configurations to defaults or delete entirely

### 🔧 **Multi-Build System Support**
- **PyInstaller**: Full support with all major options
- **cx_Freeze**: Framework ready (implementation planned)
- **Nuitka**: Framework ready (implementation planned)
- **Custom Scripts**: Execute custom build workflows

### 📊 **Build Tracking**
- **Build History**: Track build count and timestamps
- **Status Monitoring**: Real-time build progress and logs
- **Configuration Versioning**: Track configuration changes over time

## Quick Start

### 1. Create a Build Configuration
```bash
# Create new configuration with PyInstaller
python main.py build-config my-app pyinstaller
```

### 2. Configure Build Settings (Step by Step)
```bash
# Set source file
python main.py "build-config my-app" "&&" "build-source main.py"

# Set output name and version
python main.py "build-config my-app" "&&" "build-name MyApplication" "&&" "build-version 2.1.0"

# Enable onefile mode and disable console
python main.py "build-config my-app" "&&" "build-onefile true" "&&" "build-console false"
```

### 3. Execute Build
```bash
# Build using active configuration
python main.py "build-config my-app" "&&" "build-execute"
```

## Commands Reference

### Configuration Management

#### `build-config <name> [system]`
Create or switch to a build configuration.

```bash
# Create new configuration
python main.py build-config my-app pyinstaller

# Switch to existing configuration
python main.py build-config existing-app
```

**Parameters:**
- `name`: Configuration name (required)
- `system`: Build system (pyinstaller, cx_freeze, nuitka, custom) - default: pyinstaller

#### `build-list`
List all build configurations with status.

```bash
python main.py build-list
```

**Output Example:**
```
Available build configurations:
  my-app (pyinstaller) ✓ Active
    Source: main.py
    Last build: 2025-09-24T22:32:17.411968
  test-project (pyinstaller)
    Source: test.py
    Last build: Never
```

#### `build-show [config]`
Show detailed configuration information.

```bash
# Show active configuration
python main.py build-show

# Show specific configuration
python main.py "build-config my-app" "&&" "build-show"
```

#### `build-reset [config]`
Reset configuration to defaults.

```bash
# Reset active configuration
python main.py "build-config my-app" "&&" "build-reset"
```

#### `build-delete <config>`
Delete a build configuration.

```bash
python main.py build-delete old-project
```

### Build Settings

#### `build-source <file>`
Set the source Python file to build.

```bash
python main.py "build-config my-app" "&&" "build-source main.py"
```

#### `build-name <name>`
Set the output executable name.

```bash
python main.py "build-config my-app" "&&" "build-name MyApplication"
```

#### `build-version <version>`
Set the version string.

```bash
python main.py "build-config my-app" "&&" "build-version 1.2.0"
```

#### `build-icon <icon_file>`
Set the executable icon.

```bash
python main.py "build-config my-app" "&&" "build-icon app.ico"
```

#### `build-onefile [true|false]`
Enable/disable single-file executable mode.

```bash
# Enable onefile mode
python main.py "build-config my-app" "&&" "build-onefile true"

# Disable onefile mode (creates directory with dependencies)
python main.py "build-config my-app" "&&" "build-onefile false"
```

#### `build-console [true|false]`
Enable/disable console window.

```bash
# Hide console window (for GUI apps)
python main.py "build-config my-app" "&&" "build-console false"

# Show console window
python main.py "build-config my-app" "&&" "build-console true"
```

#### `build-hidden-imports <imports>`
Add hidden imports (comma-separated).

```bash
python main.py "build-config my-app" "&&" "build-hidden-imports requests,numpy,matplotlib"
```

#### `build-data-files <source> <dest>`
Add data files to be included in the executable.

```bash
# Include config file
python main.py "build-config my-app" "&&" "build-data-files config.json ."

# Include entire directory
python main.py "build-config my-app" "&&" "build-data-files assets/ assets/"
```

### Build Execution

#### `build-execute [config]`
Execute the build process.

```bash
# Build active configuration
python main.py "build-config my-app" "&&" "build-execute"

# Build specific configuration
python main.py build-execute my-app
```

#### `build-systems`
List available build systems and their status.

```bash
python main.py build-systems
```

**Output Example:**
```
Available Build Systems:
  pyinstaller: PyInstaller - Python to executable converter - ✓ Available
  cx_freeze: cx_Freeze - Cross-platform Python to executable - ✗ Not Available
  nuitka: Nuitka - Python compiler to C++ - ✗ Not Available
  custom: Custom build script execution - ✓ Available
```

## Configuration Workflow Examples

### Complete Build Setup (Single Chain)
```bash
python main.py "build-config my-app pyinstaller" "&&" \
"build-source main.py" "&&" \
"build-name MyApplication" "&&" \
"build-version 1.0.0" "&&" \
"build-onefile true" "&&" \
"build-console false" "&&" \
"build-icon app.ico" "&&" \
"build-execute"
```

### GUI Application Build
```bash
python main.py "build-config gui-app" "&&" \
"build-source gui_main.py" "&&" \
"build-name GuiApplication" "&&" \
"build-console false" "&&" \
"build-onefile true" "&&" \
"build-icon gui.ico" "&&" \
"build-data-files assets/ assets/" "&&" \
"build-execute"
```

### Console Application with Dependencies
```bash
python main.py "build-config cli-tool" "&&" \
"build-source cli.py" "&&" \
"build-name CliTool" "&&" \
"build-console true" "&&" \
"build-onefile true" "&&" \
"build-hidden-imports click,requests,colorama" "&&" \
"build-execute"
```

### Scientific Application
```bash
python main.py "build-config science-app" "&&" \
"build-source analysis.py" "&&" \
"build-name DataAnalyzer" "&&" \
"build-onefile false" "&&" \
"build-hidden-imports numpy,pandas,matplotlib,scipy" "&&" \
"build-data-files data/ data/" "&&" \
"build-execute"
```

## Configuration File Structure

Build configurations are stored in `~/.buildcli/build_configs/` as JSON files:

```json
{
  "name": "my-app",
  "build_system": "pyinstaller",
  "source_file": "main.py",
  "output_name": "MyApplication",
  "output_dir": null,
  "version": "1.0.0",
  "description": null,
  "author": null,
  "icon": "app.ico",
  "console": false,
  "onefile": true,
  "hidden_imports": ["requests", "numpy"],
  "additional_hooks": [],
  "exclude_modules": [],
  "data_files": [["config.json", "."], ["assets/", "assets/"]],
  "binary_files": [],
  "upx": false,
  "debug": false,
  "clean": true,
  "distpath": null,
  "workpath": null,
  "specpath": null,
  "custom_options": {},
  "environment_vars": {},
  "pre_build_commands": [],
  "post_build_commands": [],
  "created_date": "2025-09-24T22:30:06.462197",
  "last_modified": "2025-09-24T22:32:17.411980",
  "last_build": "2025-09-24T22:32:17.411968",
  "build_count": 1
}
```

## PyInstaller Integration

### Supported Options

BuildCLI supports all major PyInstaller options:

- **Basic Options**: `--onefile`, `--windowed`, `--console`, `--clean`
- **Output Control**: `--name`, `--distpath`, `--workpath`, `--specpath`
- **Icon**: `--icon`
- **Imports**: `--hidden-import`, `--additional-hooks-dir`, `--exclude-module`
- **Data Files**: `--add-data`, `--add-binary`
- **Advanced**: `--upx-dir`, `--debug`

### Command Translation

BuildCLI commands are translated to PyInstaller arguments:

```bash
# BuildCLI Configuration
build-onefile true
build-console false
build-name MyApp
build-icon app.ico
build-hidden-imports requests,numpy

# Equivalent PyInstaller Command
pyinstaller --onefile --windowed --name MyApp --icon app.ico \
  --hidden-import requests --hidden-import numpy main.py
```

## Advanced Features

### Environment Variables
Set environment variables for the build process:

```python
# In configuration JSON
"environment_vars": {
  "PYTHONPATH": "/custom/path",
  "BUILD_ENV": "production"
}
```

### Pre/Post Build Commands
Execute commands before and after building:

```python
# In configuration JSON
"pre_build_commands": [
  "python setup_resources.py",
  "pip install -r requirements.txt"
],
"post_build_commands": [
  "python sign_executable.py",
  "python create_installer.py"
]
```

### Custom Build Options
Add PyInstaller-specific options:

```python
# In configuration JSON
"custom_options": {
  "--log-level": "DEBUG",
  "--noconfirm": true,
  "--distpath": "custom_dist"
}
```

## Build System Extensibility

### Adding New Build Systems

The build system is designed for extensibility. To add a new build system:

1. Add entry to `SUPPORTED_SYSTEMS`
2. Implement availability check in `check_build_system_availability`
3. Create build method (e.g., `build_with_new_system`)
4. Add to execution logic in `execute_build`

### Custom Build Scripts

Use the 'custom' build system for non-standard build processes:

```bash
python main.py "build-config custom-build custom" "&&" \
"build-source build_script.py" "&&" \
"build-execute"
```

## Troubleshooting

### Common Issues

#### Build System Not Available
```bash
# Check available systems
python main.py build-systems

# Install missing build tool
pip install pyinstaller  # or cx_freeze, nuitka
```

#### Hidden Import Issues
```bash
# Add missing imports
python main.py "build-config my-app" "&&" \
"build-hidden-imports missing_module,another_module"
```

#### Data Files Not Found
```bash
# Verify source paths exist
python main.py "build-config my-app" "&&" \
"build-data-files ./existing_file.txt ."
```

#### Build Fails
```bash
# Check configuration
python main.py "build-config my-app" "&&" "build-show"

# Reset and reconfigure
python main.py "build-config my-app" "&&" "build-reset"
```

### Debug Mode

Enable debug output in PyInstaller builds by modifying configuration:

```python
# In configuration JSON
"debug": true
```

## Integration with Other BuildCLI Features

### With Virtual Environments
```bash
# Create venv and build
python main.py "venv-create my-project" "&&" \
"pip-install pyinstaller --venv my-project" "&&" \
"build-config my-app" "&&" \
"build-source main.py" "&&" \
"build-execute"
```

### With Configuration Management
```bash
# Set default build system
python main.py config-set build.default_system pyinstaller

# Set default output directory
python main.py config-set build.default_output_dir ./dist
```

### With Virtual Test Environments
```bash
# Build and test in container
python main.py "build-config my-app" "&&" \
"build-execute" "&&" \
"vtest-create test-env docker" "&&" \
"vtest-copy test-env ./dist/MyApp.exe /app/" "&&" \
"vtest-run test-env ./MyApp.exe"
```

## Performance Tips

### Faster Builds
- Use `--clean false` for incremental builds (modify config JSON)
- Exclude unnecessary modules with `build-exclude-modules`
- Use UPX compression sparingly (larger executables, slower startup)

### Smaller Executables
- Use `--onefile false` for smaller total size (but multiple files)
- Exclude unused modules
- Use Nuitka for compiled builds (when available)

### Development Workflow
- Keep separate configurations for development and production
- Use debug mode during development
- Create build scripts for complex workflows

## Future Enhancements

### Planned Features
- **cx_Freeze Integration**: Full implementation of cx_Freeze support
- **Nuitka Integration**: Native compilation support
- **Build Templates**: Predefined configurations for common scenarios
- **Batch Builds**: Build multiple configurations simultaneously
- **Build Profiles**: Environment-specific build settings (dev, test, prod)
- **Auto-detection**: Automatic dependency and import detection
- **Build Optimization**: Intelligent size and performance optimization
- **Cross-platform Builds**: Build for different platforms from one machine

### Plugin System
Future versions will support plugins for:
- Custom build systems
- Pre/post-build processors
- Output formatters
- Distribution packaging

The BuildCLI build system provides a comprehensive, persistent, and extensible solution for creating Python executables with memory-based configuration management and support for multiple build technologies.