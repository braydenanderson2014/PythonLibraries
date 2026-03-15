# Virtual Environment Management System

BuildCLI now includes a comprehensive virtual environment management system that allows you to create, manage, and work with Python virtual environments seamlessly.

## Features

### Virtual Environment Management
- **Create** virtual environments with specific Python versions
- **Activate/Deactivate** environments for shell usage
- **List** all available virtual environments
- **Remove** environments with confirmation
- **Repair** corrupted environments
- **Replace** environments with different Python versions

### Package Management
- **Install packages** from PyPI using pip
- **Install from requirements.txt** files
- **Scan projects** for dependencies automatically
- **Track installed packages** per environment

### Python Version Management
- **Download and install** specific Python versions (framework included)
- **System Python** detection and usage
- **Version-specific** virtual environments

## Commands

### Virtual Environment Commands

#### `venv-create <name> [--version <python_version>] [--force]`
Create a new virtual environment.

```bash
# Create with system Python
python main.py venv-create myproject

# Create with specific Python version
python main.py "venv-create myproject --version 3.9"

# Force overwrite existing environment
python main.py "venv-create myproject --force"
```

#### `venv-list`
List all virtual environments with details.

```bash
python main.py venv-list
```

#### `venv-activate <name>`
Activate a virtual environment.

```bash
python main.py venv-activate myproject
```

#### `venv-deactivate`
Deactivate the current virtual environment.

```bash
python main.py venv-deactivate
```

#### `venv-remove <name> [--force]`
Remove a virtual environment.

```bash
# Safe removal (requires confirmation)
python main.py venv-remove myproject

# Force removal
python main.py "venv-remove myproject --force"
```

#### `venv-repair <name>`
Repair a corrupted virtual environment.

```bash
python main.py venv-repair myproject
```

#### `venv-replace <name> <new_python_version>`
Replace an environment with a different Python version.

```bash
python main.py venv-replace myproject 3.11
```

### Package Management Commands

#### `pip-install <package1> [package2] ... [--venv <venv_name>]`
Install packages in a virtual environment.

```bash
# Install in active environment
python main.py pip-install requests flask

# Install in specific environment
python main.py "pip-install requests flask --venv myproject"
```

#### `pip-install --requirements <requirements.txt> [--venv <venv_name>]`
Install packages from a requirements file.

```bash
# Install from requirements.txt in active environment
python main.py "pip-install --requirements requirements.txt"

# Install in specific environment
python main.py "pip-install --requirements requirements.txt --venv myproject"
```

#### `pip-scan [project_path] [--install] [--venv <venv_name>]`
Scan a project for Python dependencies.

```bash
# Scan current directory
python main.py pip-scan

# Scan specific directory
python main.py pip-scan /path/to/project

# Scan and install found dependencies
python main.py "pip-scan --install --venv myproject"
```

### Python Installation Commands

#### `python-install <version>`
Download and install a specific Python version.

```bash
python main.py python-install 3.9.7
```

## Configuration

The virtual environment system stores all configuration in the `program_configuration/config.json` file. This includes:

- Virtual environment metadata
- Active environment tracking
- Package installation history
- Python version information

### Configuration Structure

```json
{
  "virtual_environments": {
    "myproject": {
      "name": "myproject",
      "python_version": "3.13.7",
      "python_executable": "C:\\Python313\\python.exe",
      "created_date": "2025-09-24T20:47:37.491678",
      "path": "C:\\Users\\user\\.buildcli\\venvs\\myproject",
      "packages": ["requests", "flask"]
    }
  },
  "active_venv": "myproject"
}
```

## File Structure

Virtual environments are stored in:
- **Windows**: `C:\\Users\\<user>\\.buildcli\\venvs\\`
- **Unix/Linux**: `~/.buildcli/venvs/`

Python installations are stored in:
- **Windows**: `C:\\Users\\<user>\\.buildcli\\python\\`
- **Unix/Linux**: `~/.buildcli/python/`

## Command Chaining Examples

The virtual environment system works seamlessly with BuildCLI's command chaining:

```bash
# Create environment and install packages
python main.py "venv-create myproject" "&&" "pip-install requests flask --venv myproject"

# Scan project and install dependencies
python main.py "pip-scan --install" "&&" "venv-list"

# Create, activate, and install requirements
python main.py "venv-create webproject" "&&" "venv-activate webproject" "&&" "pip-install --requirements requirements.txt --venv webproject"
```

## Integration with Other Modules

### PyInstaller Integration
Virtual environments work with the PyInstaller module:

```bash
# Build executable with virtual environment
python main.py "venv-activate myproject" "&&" "build-exe --name myapp"
```

### Configuration Integration
Environment settings are managed through the config system:

```bash
# View current configuration including virtual environments
python main.py config-show

# Set default virtual environment
python main.py "config-set active_venv myproject"
```

## Troubleshooting

### Common Issues

1. **Python Version Not Found**
   - Use `python-install <version>` to download the required version
   - Check system PATH for Python installations

2. **Virtual Environment Creation Fails**
   - Ensure Python venv module is available
   - Check permissions in the target directory
   - Use `--force` flag to overwrite existing environments

3. **Package Installation Fails**
   - Verify virtual environment is properly created
   - Check internet connection for PyPI access
   - Ensure pip is available in the virtual environment

4. **Environment Not Found**
   - Use `venv-list` to see available environments
   - Check the environment name spelling
   - Repair corrupted environments with `venv-repair`

### Debugging

Enable debug logging to see detailed operation information:

```bash
python main.py --log-level DEBUG venv-create myproject
```

## Best Practices

1. **Environment Naming**: Use descriptive names that match your project
2. **Python Versions**: Specify exact versions for reproducible environments
3. **Requirements Files**: Use requirements.txt for consistent package management
4. **Regular Cleanup**: Remove unused environments to save disk space
5. **Backup Configuration**: Keep the program_configuration directory in version control

## Security Considerations

- Virtual environments are isolated from system Python
- Package installations are contained within environments
- Configuration files store metadata only, not sensitive information
- Python installations are downloaded from official sources only

## Advanced Usage

### Custom Python Installations
```bash
# Install specific Python version and create environment
python main.py "python-install 3.9.7" "&&" "venv-create legacy-project --version 3.9.7"
```

### Batch Environment Management
```bash
# Create multiple environments for different projects
python main.py "venv-create web-frontend" "&&" "venv-create api-backend --version 3.10" "&&" "venv-create data-analysis --version 3.11"
```

### Project-Specific Workflows
```bash
# Complete project setup workflow
python main.py "venv-create myproject" "&&" "pip-install --requirements requirements.txt --venv myproject" "&&" "venv-activate myproject" "&&" "echo Project environment ready"
```