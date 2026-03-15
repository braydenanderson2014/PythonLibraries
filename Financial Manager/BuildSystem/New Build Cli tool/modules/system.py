"""
Built-in system commands module for BuildCLI.
"""

import asyncio
import subprocess
import sys
from typing import Dict, List, Any, Callable


MODULE_INFO = {
    'name': 'system',
    'version': '1.0.0',
    'description': 'Built-in system commands and utilities',
    'author': 'BuildCLI',
    'commands': ['echo', 'run', 'python', 'pip', 'help', 'list-modules', 'install-module', 'list-remote-modules', 'update-module', 'list-sources']
}


async def echo_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Echo command - prints the provided arguments."""
    message = ' '.join(args)
    print(message)
    return message


async def run_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Run command - executes a system command."""
    if not args:
        raise ValueError("No command provided to run")
    
    command = args[0]
    command_args = args[1:] if len(args) > 1 else []
    
    # Handle dry-run mode
    if modifiers.get('dry_run', False):
        print(f"[DRY RUN] Would execute: {command} {' '.join(command_args)}")
        return True
    
    try:
        # Create subprocess
        process = await asyncio.create_subprocess_exec(
            command, *command_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        # Print output
        if stdout:
            print(stdout.decode('utf-8', errors='replace').strip())
        
        if stderr and process.returncode != 0:
            print(f"Error: {stderr.decode('utf-8', errors='replace').strip()}", file=sys.stderr)
        
        return process.returncode == 0
    
    except FileNotFoundError:
        raise ValueError(f"Command not found: {command}")
    except Exception as e:
        raise RuntimeError(f"Failed to execute command: {e}")


async def python_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Python command - executes Python code or scripts."""
    if not args:
        # Start interactive Python session
        command_args = [sys.executable]
    else:
        command_args = [sys.executable] + args
    
    return await run_command(command_args, modifiers)


async def pip_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Pip command - manages Python packages."""
    command_args = [sys.executable, '-m', 'pip'] + args
    return await run_command(command_args, modifiers)


async def help_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Help command - displays help information."""
    # This will be handled by the CLI parser, but we include it for completeness
    print("BuildCLI - A modular build tool")
    print("\nAvailable commands depend on loaded modules.")
    print("Use 'list-modules' to see available modules and their commands.")
    return True


async def list_modules_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """List modules command - displays available modules."""
    # Get module manager from the global context if available
    import sys
    module_manager = getattr(sys.modules.get('__main__'), '_module_manager', None)
    
    print("Available modules:")
    
    if module_manager and hasattr(module_manager, 'module_info'):
        for module_name, info in module_manager.module_info.items():
            description = info.get('description', 'No description available')
            print(f"  {module_name} - {description}")
    else:
        print("  system - Built-in system commands")
        print("  (Unable to access module manager for full list)")
    
    print("\nUse 'install-module <name>' to install additional modules from repository.")
    return True


async def install_module_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Install module command - installs a module from repository."""
    if not args:
        raise ValueError("Module name required")
    
    module_name = args[0]
    source_name = args[1] if len(args) > 1 else "primary"
    
    print(f"Installing module: {module_name}")
    print(f"From source: {source_name}")
    
    # This would integrate with the module manager
    # For now, just return a placeholder
    print(f"Module installation initiated for: {module_name}")
    print("Note: GitHub integration is configured but requires actual HTTP implementation")
    return True


async def list_remote_modules_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """List remote modules command - displays available modules from repositories."""
    source_name = args[0] if args else "primary"
    
    print(f"Listing remote modules from source: {source_name}")
    print("\nAvailable modules:")
    print("  git                  - Git integration module")
    print("  docker               - Docker integration module") 
    print("  nodejs               - Node.js build tools")
    print("  python-tools         - Python development utilities")
    print("\nNote: This is a placeholder list. GitHub integration configured but requires HTTP implementation.")
    return True


async def update_module_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Update module command - updates an installed module."""
    if not args:
        raise ValueError("Module name required")
    
    module_name = args[0]
    
    print(f"Updating module: {module_name}")
    print("Note: Module update feature configured but requires full GitHub integration")
    return True


async def list_sources_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """List sources command - displays configured module sources."""
    print("Configured module sources:")
    print("  primary              - Official BuildCLI modules (trusted)")
    print("  community            - Community contributed modules")
    print("  verified             - Verified third-party modules (trusted)")
    print("\nNote: Sources are configured in github_config_program.json")
    return True


# Command registration function
async def register_commands() -> Dict[str, Callable]:
    """Register all commands provided by this module."""
    return {
        'echo': echo_command,
        'run': run_command,
        'python': python_command,
        'pip': pip_command,
        'help': help_command,
        'list-modules': list_modules_command,
        'install-module': install_module_command,
        'list-remote-modules': list_remote_modules_command,
        'update-module': update_module_command,
        'list-sources': list_sources_command,
    }


# Alternative function name for compatibility
def get_commands() -> List[str]:
    """Get list of command names provided by this module."""
    return MODULE_INFO['commands']