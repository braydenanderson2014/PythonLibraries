# Build System v2

A modular, extensible command-based build system for Python projects.

## Features

- **Modular Architecture**: Commands are self-contained modules that can be added/removed easily
- **Dynamic Command Discovery**: Automatically discovers and registers commands from the `modules/` directory
- **Shared Context**: Commands have access to shared configuration, memory, and utilities
- **JSON Memory**: Persistent state storage across build sessions
- **Error Handling**: Comprehensive error handling with verbose mode
- **Interactive Mode**: REPL-style command interface
- **Extensible**: Easy to add new commands by extending the `Command` base class

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run the build system
python build_system.py
```

Dependencies:
- **pyinstaller**: For building executables
- **Pillow**: For image analysis (icon/splash detection)

## Usage

### Interactive Mode

```bash
# Start interactive mode
python build_system.py -i

# Or without arguments
python build_system.py

# In interactive mode:
build> help              # Show available commands
build> list              # List all commands
build> scan              # Run scan command
build> verbose           # Toggle verbose mode
build> exit              # Exit
```

### Command Line Mode

```bash
# Run a single command
python build_system.py scan

# With arguments
python build_system.py scan --target ./src

# With verbose output
python build_system.py -v scan

# Custom config file
python build_system.py -c my_config.json scan
```

## Quick Start Workflow

Here's a typical workflow for building an executable:

```bash
# 1. Start the build system
python build_system.py -i

# 2. Scan your project for Python files and entry points
build> scan-python --find-main

# 3. Scan for icons and splash images
build> scan-icon --target ./assets

# 4. Build your executable
build> build --noconsole --onefile

# 5. Find your executable in the dist/ directory
```

Or in one command:
```bash
python build_system.py scan-python --find-main
python build_system.py scan-icon
python build_system.py build --noconsole
```

## Configuration

Configuration is stored in `build_config.json`:

```json
{
  "project_name": "My Project",
  "memory_file": "build_memory.json",
  "modules_directory": "modules",
  "build_directory": "dist",
  "pyinstaller": {
    "enabled": true,
    "onefile": true,
    "console": true,
    "icon": null,
    "splash": null,
    "name": null,
    "extra_args": []
  },
  "build_icon": null,
  "build_splash": null
}
```

- **build_icon**: Auto-set by `scan-icon` command
- **build_splash**: Auto-set by `scan-icon` command
- **pyinstaller.extra_args**: Additional PyInstaller arguments

## Creating New Commands

To create a new command, create a Python file in the `modules/` directory:

```python
from build_system import Command, BuildContext
from typing import List

class MyCommand(Command):
    """My custom command"""
    
    @classmethod
    def get_name(cls) -> str:
        return "mycommand"
    
    @classmethod
    def get_aliases(cls) -> List[str]:
        return ["mc"]
    
    @classmethod
    def get_description(cls) -> str:
        return "Does something awesome"
    
    @classmethod
    def get_help(cls) -> str:
        return "Detailed help text here"
    
    def execute(self, *args, **kwargs) -> bool:
        # Access shared context
        self.context.log("Executing my command...")
        
        # Get configuration
        value = self.context.get_config('some_key', default='default_value')
        
        # Use persistent memory
        last_run = self.context.get_memory('last_run')
        self.context.set_memory('last_run', 'now')
        
        # Your command logic here
        
        return True  # Return True on success
```

The command will be automatically discovered and registered on next run.

## Built-in Commands

### scan
Scans project files and analyzes project structure.

```bash
build> scan                          # Scan current directory
build> scan --target ./src           # Scan specific directory
build> scan --include .py,.txt       # Only scan specific extensions
build> scan --exclude __pycache__    # Exclude patterns
```

### scan-python (aliases: spy, scan-py)
Scans Python files and extracts dependencies, entry points, etc.

```bash
build> scan-python                # Scan all Python files
build> scan-python --find-main    # Find entry points
```

### scan-icon (aliases: icon, splash)
Scans for suitable icon and splash images for builds.

```bash
build> scan-icon                     # Scan for both icon and splash
build> icon --type icon              # Only scan for icon
build> splash --type splash          # Only scan for splash
build> scan-icon --target ./assets   # Scan specific directory
build> scan-icon --auto              # Auto-select best match
```

When multiple candidates are found, you'll be prompted to select one. Selected images are stored in the configuration and automatically used during builds.

### build (aliases: b, compile)
Builds an executable using PyInstaller with configured settings.

```bash
build> build                           # Auto-detect entry point and build
build> build main.py                   # Build specific file
build> build --entry main.py           # Alternative syntax
build> build --name MyApp --noconsole  # Build GUI app with custom name
build> build --clean --onefile         # Clean build as single file
build> build --icon logo.ico           # Override icon
build> build --dry-run                 # Preview PyInstaller command
```

### clean (aliases: c)
Removes build artifacts and PyInstaller cache.

```bash
build> clean                # Clean build and __pycache__
build> clean --all          # Clean everything
build> clean --cache        # Clean only PyInstaller cache
build> clean --specs        # Remove .spec files
build> clean --dry-run      # Preview what would be deleted
```

## Architecture

### BuildContext
Provides shared functionality to all commands:
- Configuration management
- Persistent memory (JSON storage)
- Logging utilities
- Project root path

### Command
Abstract base class for all commands. Requires:
- `get_name()`: Command name
- `get_description()`: Short description
- `execute()`: Command logic
- Optional: `get_aliases()`, `get_help()`

### CommandRegistry
Manages command discovery, registration, and execution:
- Scans `modules/` directory
- Registers commands and aliases
- Handles command execution with error handling

### BuildSystem
Main coordinator that ties everything together:
- Initializes context and registry
- Provides interactive and CLI modes
- Handles built-in commands (help, list, verbose, exit)

## Memory System

The build system maintains persistent state in `build_memory.json`:

```json
{
  "last_scan": {
    "root": "/path/to/project",
    "python_files": [...],
    "total_files": 42
  },
  "python_scan": {
    "dependencies": ["os", "sys", "json"],
    "entry_points": ["main.py"]
  }
}
```

Commands can read and write to this memory to share state across executions.

## Error Handling

- Commands return `True` on success, `False` on failure
- Exceptions are caught and logged with stack traces in verbose mode
- Invalid commands show helpful error messages
- Missing modules/files are handled gracefully

## Advanced Usage

### Verbose Mode
```bash
python build_system.py -v scan
# Or in interactive mode:
build> verbose  # Toggle
build> scan
```

### Custom Modules Directory
```bash
python build_system.py -m custom_modules scan
```

### Dry Run Mode
```python
# In your command:
if self.context.dry_run:
    self.context.log("Would do something (dry run)")
    return True
```

## Future Enhancements

Planned commands to add:
- `build`: Build executables with PyInstaller
- `clean`: Clean build artifacts
- `test`: Run tests
- `package`: Create distribution packages
- `deploy`: Deploy built artifacts
- `deps`: Manage dependencies

## License

MIT License - See LICENSE file for details
