# Virtual Test Environment System

BuildCLI's Virtual Test Environment System provides comprehensive support for creating, managing, and automating test environments using multiple virtualization platforms including Windows Sandbox, VirtualBox, Hyper-V, and Docker.

## Features

### Supported Platforms
- **Windows Sandbox**: Lightweight, disposable Windows environments
- **VirtualBox**: Cross-platform desktop virtualization
- **Hyper-V**: Microsoft's native hypervisor technology
- **Docker**: Containerized application environments

### Core Capabilities
- **Environment Lifecycle Management**: Create, start, stop, delete virtual environments
- **Command Execution**: Run commands inside virtual environments
- **File Transfer**: Copy files to and from virtual environments
- **Template System**: Use predefined or custom environment templates
- **Status Monitoring**: Real-time status tracking of environments
- **Export/Import**: Save and share environment configurations

## Commands

### Environment Management

#### `vtest-create <name> <platform> [--template <template>] [options]`
Create a new virtual test environment.

```bash
# Create Windows Sandbox environment
python main.py "vtest-create test-env windows_sandbox"

# Create VirtualBox VM with custom settings
python main.py "vtest-create vm1 virtualbox --memory 4096 --cpus 4 --disk_size 40960"

# Create Docker container with Ubuntu
python main.py "vtest-create container1 docker --image ubuntu:22.04 --ports 8080:80"
```

#### `vtest-list`
List all virtual test environments with status information.

```bash
python main.py vtest-list
```

#### `vtest-start <name>`
Start a virtual test environment.

```bash
python main.py vtest-start test-env
```

#### `vtest-stop <name>`
Stop a virtual test environment.

```bash
python main.py vtest-stop test-env
```

#### `vtest-delete <name> [--force]`
Delete a virtual test environment.

```bash
# Safe deletion (requires confirmation)
python main.py vtest-delete test-env

# Force deletion
python main.py "vtest-delete test-env --force"
```

### Environment Interaction

#### `vtest-run <name> <command>`
Execute a command inside a virtual environment.

```bash
# Run command in Windows Sandbox
python main.py vtest-run test-env "dir C:\\"

# Run command in Docker container
python main.py vtest-run container1 "ls -la /home"

# Run command in VirtualBox VM (requires guest additions)
python main.py "vtest-run vm1 python --version --username user --password pass"
```

#### `vtest-copy <name> <source> <destination>`
Copy files to a virtual environment.

```bash
# Copy file to Docker container
python main.py vtest-copy container1 "./test.py" "/tmp/test.py"

# Copy directory to VirtualBox VM
python main.py vtest-copy vm1 "./build/" "C:\\Temp\\build\\"
```

#### `vtest-status [name]`
Show status of virtual environments.

```bash
# Show status of all environments
python main.py vtest-status

# Show status of specific environment
python main.py vtest-status test-env
```

### Platform-Specific Commands

#### Windows Sandbox Shortcuts
```bash
# Create Windows Sandbox environment
python main.py "sandbox-create test-sandbox"

# Run Windows Sandbox environment
python main.py sandbox-run test-sandbox
```

#### VirtualBox Shortcuts
```bash
# Create VirtualBox VM
python main.py "vbox-create test-vm"

# Run VirtualBox VM
python main.py vbox-run test-vm
```

### Configuration and Templates

#### `vtest-templates`
List available platforms and template information.

```bash
python main.py vtest-templates
```

#### `vtest-config`
Show virtual test environment system configuration.

```bash
python main.py vtest-config
```

#### `vtest-export <name> [output_file]`
Export environment configuration to file.

```bash
python main.py vtest-export test-env test-env-config.json
```

## Platform-Specific Configuration

### Windows Sandbox

Windows Sandbox environments support the following options:

```bash
python main.py "vtest-create sandbox1 windows_sandbox \
    --vgpu Enable \
    --networking Disable \
    --audio_input Enable \
    --clipboard_redirection Enable"
```

**Mapped Folders**: Configure shared directories between host and sandbox:
```bash
python main.py "vtest-create sandbox1 windows_sandbox \
    --mapped_folders '[{\"host\":\"C:\\\\Projects\",\"sandbox\":\"C:\\\\Shared\",\"readonly\":false}]'"
```

**Logon Commands**: Execute commands when sandbox starts:
```bash
python main.py "vtest-create sandbox1 windows_sandbox \
    --logon_command '{\"command\":\"powershell.exe -Command \\\"Write-Host Welcome\\\"\"}'"
```

### VirtualBox

VirtualBox VMs support comprehensive configuration options:

```bash
python main.py "vtest-create vm1 virtualbox \
    --memory 4096 \
    --cpus 4 \
    --disk_size 40960"
```

**Available Options**:
- `--memory`: RAM in MB (default: 2048)
- `--cpus`: Number of CPU cores (default: 2)
- `--disk_size`: Hard disk size in MB (default: 20480)

### Docker

Docker containers support flexible configuration:

```bash
python main.py "vtest-create container1 docker \
    --image ubuntu:22.04 \
    --ports 8080:80,3000:3000 \
    --volumes ./data:/app/data,./config:/etc/myapp \
    --interactive true"
```

**Available Options**:
- `--image`: Docker image to use (default: ubuntu:latest)
- `--ports`: Port mappings (format: host:container)
- `--volumes`: Volume mappings (format: host:container)
- `--interactive`: Enable interactive mode (default: true)
- `--command`: Custom command to run in container

### Hyper-V

Hyper-V support is planned for future releases.

## Workflow Examples

### Automated Testing Pipeline

```bash
# Create test environment and run tests
python main.py "vtest-create test-env docker --image python:3.11" "&&" \
"vtest-copy test-env ./src /app/src" "&&" \
"vtest-copy test-env ./requirements.txt /app/" "&&" \
"vtest-run test-env 'cd /app && pip install -r requirements.txt'" "&&" \
"vtest-run test-env 'cd /app && python -m pytest src/tests/'" "&&" \
"vtest-delete test-env --force"
```

### Windows Application Testing

```bash
# Create Windows Sandbox for application testing
python main.py "sandbox-create win-test" "&&" \
"vtest-copy win-test ./myapp.exe C:\\Temp\\myapp.exe" "&&" \
"sandbox-run win-test"
```

### Multi-Environment Testing

```bash
# Test on multiple platforms
python main.py "vtest-create test-ubuntu docker --image ubuntu:22.04" "&&" \
"vtest-create test-alpine docker --image alpine:latest" "&&" \
"vtest-run test-ubuntu 'python --version'" "&&" \
"vtest-run test-alpine 'python --version'" "&&" \
"vtest-delete test-ubuntu --force" "&&" \
"vtest-delete test-alpine --force"
```

## File Structure

```
~/.buildcli/vtest/
├── templates/           # Environment templates
│   ├── windows/        # Windows Sandbox templates
│   ├── virtualbox/     # VirtualBox templates
│   └── docker/         # Docker templates
└── instances/          # Environment instances
    ├── env1/
    │   ├── environment.json    # Environment metadata
    │   └── platform-specific-files
    └── env2/
        └── environment.json
```

## Configuration File Format

Environment configurations are stored as JSON:

```json
{
  "name": "test-env",
  "platform": "docker",
  "template": "ubuntu:22.04",
  "created_date": "2025-09-24T21:00:00.000000",
  "status": "running",
  "config": {
    "image": "ubuntu:22.04",
    "ports": ["8080:80"],
    "volumes": ["./data:/app/data"],
    "interactive": true
  }
}
```

## Platform Requirements

### Windows Sandbox
- **OS**: Windows 10 Pro/Enterprise/Education (Build 18305+) or Windows 11
- **Feature**: "Windows Sandbox" feature must be enabled
- **Virtualization**: Hardware virtualization support required

### VirtualBox
- **Software**: Oracle VirtualBox installed and accessible via `vboxmanage`
- **OS**: Windows, macOS, or Linux
- **Resources**: Sufficient RAM and disk space for VMs

### Hyper-V
- **OS**: Windows 10 Pro/Enterprise/Education or Windows Server
- **Feature**: "Hyper-V" feature must be enabled
- **Hardware**: SLAT-capable processor required

### Docker
- **Software**: Docker Desktop or Docker Engine installed
- **OS**: Windows, macOS, or Linux
- **Access**: Docker command accessible from PATH

## Security Considerations

### Isolation
- Each virtual environment is isolated from the host system
- Network isolation can be configured per platform
- File system access is controlled through volume/folder mappings

### Resource Management
- CPU and memory limits can be configured
- Disk space usage is monitored and limited
- Automatic cleanup prevents resource exhaustion

### Access Control
- Guest OS credentials are managed separately
- File sharing is explicit and controlled
- Network access can be restricted or disabled

## Troubleshooting

### Platform Not Available
```bash
# Check platform availability
python main.py vtest-templates

# Common solutions:
# 1. Enable required Windows features
# 2. Install virtualization software
# 3. Check hardware virtualization support
```

### Environment Won't Start
```bash
# Check environment status
python main.py vtest-status env-name

# Common solutions:
# 1. Ensure host platform is running
# 2. Check resource availability
# 3. Verify environment configuration
```

### Command Execution Fails
```bash
# Check environment is running
python main.py vtest-status env-name

# Platform-specific requirements:
# - VirtualBox: Requires Guest Additions
# - Docker: Container must be running
# - Windows Sandbox: Limited direct command support
```

### File Copy Issues
```bash
# Verify environment is accessible
python main.py vtest-status env-name

# Platform-specific notes:
# - Windows Sandbox: Use mapped folders
# - VirtualBox: Requires Guest Additions
# - Docker: Standard docker cp functionality
```

## Advanced Usage

### Custom Templates

Create custom environment templates in `~/.buildcli/vtest/templates/`:

```json
{
  "name": "python-dev",
  "platform": "docker",
  "config": {
    "image": "python:3.11-slim",
    "volumes": ["./src:/app"],
    "ports": ["8000:8000"],
    "command": "bash"
  }
}
```

### Automated Cleanup

```bash
# Clean up all stopped environments
python main.py vtest-list | grep "stopped" | awk '{print $1}' | xargs -I {} python main.py vtest-delete {} --force
```

### Environment Snapshots (VirtualBox)

```bash
# Export environment configuration for recreation
python main.py vtest-export my-vm my-vm-config.json
```

## Integration with BuildCLI

The virtual test environment system integrates seamlessly with other BuildCLI features:

### With Virtual Environments (venv)
```bash
# Create Python venv and test in container
python main.py "venv-create test-project" "&&" \
"pip-install pytest --venv test-project" "&&" \
"vtest-create container1 docker --image python:3.11" "&&" \
"vtest-copy container1 ~/.buildcli/venvs/test-project /app/venv" "&&" \
"vtest-run container1 'source /app/venv/bin/activate && pytest'"
```

### With PyInstaller
```bash
# Build executable and test in clean environment
python main.py "build-exe myapp.py" "&&" \
"vtest-create test-win windows_sandbox" "&&" \
"vtest-copy test-win ./dist/myapp.exe C:\\Temp\\myapp.exe" "&&" \
"sandbox-run test-win"
```

### With Configuration Management
```bash
# Use configuration for environment settings
python main.py "config-set vtest.default_platform docker" "&&" \
"config-set vtest.default_image ubuntu:22.04"
```

This virtual test environment system provides a comprehensive solution for testing applications across multiple platforms and virtualization technologies, all integrated within the BuildCLI ecosystem.