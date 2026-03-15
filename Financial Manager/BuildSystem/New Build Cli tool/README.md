# BuildCLI

A modular command-line interface tool with command chaining support, designed for build automation and extensibility.

## Features

- **Command Chaining**: Support for both related (`&&`) and unrelated (`||`) command chaining
- **Modular Architecture**: Easily extensible with custom modules
- **Virtual Environment Management**: Complete Python venv system with package management
- **PyInstaller Integration**: Built-in support for creating executables
- **Dynamic Module Loading**: Download and install modules from repositories
- **Parallel Execution**: Run independent commands in parallel
- **Dry Run Mode**: Test commands without executing them
- **Comprehensive Logging**: Configurable logging levels and output

## Quick Start

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd buildcli
```

2. Install dependencies (optional):
```bash
pip install -r requirements.txt
```

3. Run directly:
```bash
python main.py --help
```

### Building an Executable

#### Windows
```cmd
build.bat
```

#### Linux/Mac
```bash
chmod +x build.sh
./build.sh
```

## Usage

### Basic Commands

```bash
# Single command
buildcli echo "Hello World"

# Command with modifiers
buildcli build --release

# Command chaining with AND (stop on failure)
buildcli clean && build --debug

# Command chaining with OR (stop on success)
buildcli test || build --force

# Multiple chained commands
buildcli clean && build --release && deploy

# Virtual environment workflow
buildcli venv-create myproject && pip-install flask requests --venv myproject

# Parallel execution
buildcli --parallel build test lint

# Dry run mode
buildcli --dry-run clean && build
```

### Built-in Commands

#### System Commands
- `echo <message>` - Print a message
- `run <command>` - Execute a system command
- `python [args]` - Run Python scripts or interactive session
- `pip [args]` - Manage Python packages
- `help` - Show help information
- `list-modules` - List available modules
- `install-module <name> [source]` - Install a module from repository
- `list-remote-modules [source]` - List available modules from repositories
- `update-module <name>` - Update an installed module
- `list-sources` - List configured module sources

#### Configuration Commands
- `config-init` - Initialize BuildCLI configuration
- `config-show [github]` - Show current configuration
- `config-set <key> <value>` - Set a configuration value
- `config-get <key>` - Get a configuration value
- `config-reset --force` - Reset configuration to defaults
- `github-config-init` - Initialize GitHub configuration from template

#### Build Commands
- `build [script]` - Build executable with PyInstaller
- `build-exe [script]` - Build executable (alias for build)
- `clean-build` - Remove build artifacts
- `analyze [script]` - Analyze dependencies

### Virtual Environment Commands

- `venv-create <name>` - Create virtual environment
- `venv-list` - List all virtual environments
- `venv-activate <name>` - Activate virtual environment
- `venv-deactivate` - Deactivate current virtual environment
- `venv-remove <name>` - Remove virtual environment
- `venv-repair <name>` - Repair corrupted virtual environment
- `venv-replace <name> <version>` - Replace with different Python version
- `pip-install <packages>` - Install packages in virtual environment
- `pip-scan [path]` - Scan project for dependencies
- `python-install <version>` - Download and install Python version

### Command Modifiers

#### Global Modifiers
- `--verbose` - Enable verbose output
- `--quiet` - Suppress non-error output
- `--dry-run` - Show what would be executed
- `--parallel` - Enable parallel execution
- `--sequential` - Force sequential execution

#### Build-specific Modifiers
- `--one-file` - Create single executable file (default: true)
- `--console` - Console application (default: true)
- `--debug` - Enable debug mode
- `--icon <file>` - Set executable icon
- `--clean` - Clean build before building
- `--dist-dir <dir>` - Output directory (default: dist)
- `--build-dir <dir>` - Build directory (default: build)

## Architecture

### Core Components

- **main.py** - Entry point and main CLI application
- **core/cli_parser.py** - Command line argument parsing
- **core/command_queue.py** - Command queuing and execution
- **core/module_manager.py** - Module loading and management
- **core/config.py** - Configuration management
- **utils/logger.py** - Logging utilities

### Module System

BuildCLI uses a modular architecture where functionality is provided by modules. Each module can register commands and provide implementations.

#### Built-in Modules

1. **system.py** - Basic system commands (echo, run, python, pip, etc.)
2. **pyinstaller_module.py** - PyInstaller integration for building executables
3. **venv.py** - Virtual environment and package management
4. **config.py** - Configuration management commands

#### Creating Custom Modules

Create a Python file in the `modules/` directory:

```python
"""
Example custom module for BuildCLI.
"""

MODULE_INFO = {
    'name': 'example',
    'version': '1.0.0',
    'description': 'Example module',
    'author': 'Your Name',
    'commands': ['hello', 'goodbye']
}

async def hello_command(args, modifiers):
    """Hello command implementation."""
    name = args[0] if args else "World"
    print(f"Hello, {name}!")
    return True

async def goodbye_command(args, modifiers):
    """Goodbye command implementation."""
    name = args[0] if args else "World"
    print(f"Goodbye, {name}!")
    return True

async def register_commands():
    """Register commands provided by this module."""
    return {
        'hello': hello_command,
        'goodbye': goodbye_command,
    }
```

### Command Chaining

BuildCLI supports sophisticated command chaining:

- **Sequential** - Commands run one after another
- **AND (`&&`)** - Stop execution if any command fails
- **OR (`||`)** - Stop execution when first command succeeds

Example:
```bash
buildcli clean && build --release && test || echo "Build or test failed"
```

### Configuration

BuildCLI uses JSON configuration files for both general settings and GitHub integration:

### Main Configuration
Located at `~/.buildcli/config.json`. Initialize with `buildcli config-init`:

```json
{
  "log_level": "INFO",
  "auto_update_modules": false,
  "remote_module_repo": "https://github.com/your-org/buildcli-modules",
  "module_cache_dir": "~/.buildcli/modules",
  "temp_dir": "~/.buildcli/temp",
  "parallel_execution": true,
  "max_parallel_commands": 4,
  "timeout_seconds": 300,
  "pyinstaller": {
    "one_file": true,
    "console": true,
    "icon": null,
    "add_data": [],
    "hidden_imports": []
  }
}
```

### GitHub Configuration
Located at `~/.buildcli/github_config.json`. Initialize with `buildcli github-config-init`:

```json
{
  "github": {
    "personal_access_token": "",
    "username": "your_username",
    "api": {
      "base_url": "https://api.github.com",
      "timeout": 30,
      "max_retries": 3
    }
  },
  "module_sources": {
    "primary": {
      "type": "github",
      "url": "https://github.com/buildcli-official/buildcli-modules",
      "branch": "main",
      "enabled": true,
      "trusted": true
    }
  },
  "security": {
    "verify_signatures": false,
    "allowed_authors": [],
    "scan_for_vulnerabilities": true
  }
}
```

See [GITHUB_CONFIG.md](GITHUB_CONFIG.md) for detailed GitHub configuration documentation.

## Development

### Project Structure

```
buildcli/
├── main.py                 # Entry point
├── core/                   # Core functionality
│   ├── __init__.py
│   ├── cli_parser.py      # Argument parsing
│   ├── command_queue.py   # Command execution
│   ├── config.py          # Configuration
│   └── module_manager.py  # Module management
├── utils/                  # Utilities
│   ├── __init__.py
│   └── logger.py          # Logging
├── modules/                # Built-in modules
│   ├── system.py          # System commands
│   └── pyinstaller_module.py # PyInstaller integration
├── build.bat              # Windows build script
├── build.sh               # Linux/Mac build script
├── buildcli.spec          # PyInstaller spec file
├── requirements.txt       # Dependencies
├── setup.py              # Installation script
└── README.md             # This file
```

### Testing

```bash
# Test the CLI directly
python main.py echo "Test message"

# Test command chaining
python main.py echo "Step 1" && echo "Step 2"

# Test build functionality
python main.py build main.py --dry-run

# Test with built executable
./dist/buildcli echo "Hello from executable"
```

### Adding New Features

1. **New Commands**: Add to existing modules or create new modules
2. **New Modifiers**: Extend the CLI parser to recognize new options
3. **New Chain Types**: Extend the command queue execution logic
4. **New Module Sources**: Extend the module manager for additional sources

## PyInstaller Integration

BuildCLI includes comprehensive PyInstaller integration:

### Features
- One-file executable creation
- Automatic dependency detection
- Custom icon support
- Data file inclusion
- Hidden import handling
- Build artifact cleanup

### Usage
```bash
# Build current project
buildcli build

# Build with custom options
buildcli build main.py --icon app.ico --add-data "data/*;data"

# Clean build artifacts
buildcli clean-build

# Analyze dependencies
buildcli analyze main.py
```

### Advanced PyInstaller Options

The PyInstaller module supports all major PyInstaller options through modifiers:

- `--one-file` / `--one-dir` - Output format
- `--console` / `--windowed` - Application type
- `--icon <file>` - Executable icon
- `--add-data <src;dest>` - Include data files
- `--hidden-import <module>` - Force import inclusion
- `--exclude-module <module>` - Exclude modules
- `--upx` / `--no-upx` - UPX compression
- `--debug` - Debug mode

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Future Enhancements

- Web-based module repository
- Plugin marketplace
- Visual command builder
- Real-time execution monitoring
- Configuration profiles
- Command history and favorites
- Bash/PowerShell completion
- Docker integration
- Cloud deployment modules