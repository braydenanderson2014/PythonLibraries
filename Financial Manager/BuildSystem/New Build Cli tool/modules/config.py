"""
Configuration management module for BuildCLI.
"""

import json
import os
import shutil
from pathlib import Path
from typing import Dict, List, Any, Callable


MODULE_INFO = {
    'name': 'config',
    'version': '1.0.0',
    'description': 'Configuration management for BuildCLI',
    'author': 'BuildCLI',
    'commands': ['config-init', 'config-show', 'config-set', 'config-get', 'config-reset', 'github-config-init']
}


async def config_init_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Initialize BuildCLI configuration."""
    config_dir = Path.home() / ".buildcli"
    config_file = config_dir / "config.json"
    
    if config_file.exists() and not modifiers.get('force', False):
        print(f"Configuration already exists at: {config_file}")
        print("Use --force to overwrite existing configuration")
        return False
    
    # Create configuration directory
    config_dir.mkdir(exist_ok=True)
    
    # Default configuration
    default_config = {
        "log_level": "INFO",
        "auto_update_modules": False,
        "remote_module_repo": "https://github.com/buildcli-official/buildcli-modules",
        "module_cache_dir": str(config_dir / "modules"),
        "temp_dir": str(config_dir / "temp"),
        "parallel_execution": True,
        "max_parallel_commands": 4,
        "timeout_seconds": 300,
        "pyinstaller": {
            "one_file": True,
            "console": True,
            "icon": None,
            "add_data": [],
            "hidden_imports": []
        }
    }
    
    if modifiers.get('dry_run', False):
        print(f"[DRY RUN] Would create config file at: {config_file}")
        print(f"[DRY RUN] Configuration: {json.dumps(default_config, indent=2)}")
        return True
    
    # Write configuration file
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(default_config, f, indent=2)
    
    print(f"✓ Configuration initialized at: {config_file}")
    print("Edit this file to customize BuildCLI settings")
    
    return True


async def github_config_init_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Initialize GitHub configuration from template."""
    config_dir = Path.home() / ".buildcli"
    github_config_file = config_dir / "github_config.json"
    
    # Find template file
    template_file = Path(__file__).parent.parent / "github_config_template.json"
    
    if not template_file.exists():
        print("GitHub configuration template not found")
        return False
    
    if github_config_file.exists() and not modifiers.get('force', False):
        print(f"GitHub configuration already exists at: {github_config_file}")
        print("Use --force to overwrite existing configuration")
        return False
    
    if modifiers.get('dry_run', False):
        print(f"[DRY RUN] Would copy template to: {github_config_file}")
        return True
    
    # Create configuration directory
    config_dir.mkdir(exist_ok=True)
    
    # Copy template
    shutil.copy2(template_file, github_config_file)
    
    print(f"✓ GitHub configuration template copied to: {github_config_file}")
    print("Edit this file to configure GitHub integration:")
    print("  - Set your personal access token")
    print("  - Configure module sources")
    print("  - Adjust security settings")
    
    return True


async def config_show_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Show current configuration."""
    config_file = Path.home() / ".buildcli" / "config.json"
    
    if not config_file.exists():
        print("No configuration file found. Run 'config-init' to create one.")
        return False
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        if args and args[0] == 'github':
            # Show GitHub config
            github_config_file = Path.home() / ".buildcli" / "github_config.json"
            if github_config_file.exists():
                with open(github_config_file, 'r', encoding='utf-8') as f:
                    github_config = json.load(f)
                print("GitHub Configuration:")
                print(json.dumps(github_config, indent=2))
            else:
                print("No GitHub configuration found. Run 'github-config-init' to create one.")
            return True
        
        print("BuildCLI Configuration:")
        print(json.dumps(config, indent=2))
        return True
    
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error reading configuration: {e}")
        return False


async def config_set_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Set a configuration value."""
    if len(args) < 2:
        print("Usage: config-set <key> <value>")
        print("Example: config-set log_level DEBUG")
        return False
    
    key = args[0]
    value = args[1]
    
    config_file = Path.home() / ".buildcli" / "config.json"
    
    if not config_file.exists():
        print("No configuration file found. Run 'config-init' to create one.")
        return False
    
    try:
        # Load existing config
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Handle nested keys (dot notation)
        keys = key.split('.')
        current = config
        
        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        # Convert value to appropriate type
        if value.lower() in ['true', 'false']:
            value = value.lower() == 'true'
        elif value.isdigit():
            value = int(value)
        elif value.replace('.', '').isdigit():
            value = float(value)
        
        # Set the value
        current[keys[-1]] = value
        
        if modifiers.get('dry_run', False):
            print(f"[DRY RUN] Would set {key} = {value}")
            return True
        
        # Save config
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        
        print(f"✓ Set {key} = {value}")
        return True
    
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error updating configuration: {e}")
        return False


async def config_get_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Get a configuration value."""
    if not args:
        print("Usage: config-get <key>")
        print("Example: config-get log_level")
        return False
    
    key = args[0]
    config_file = Path.home() / ".buildcli" / "config.json"
    
    if not config_file.exists():
        print("No configuration file found. Run 'config-init' to create one.")
        return False
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Handle nested keys (dot notation)
        keys = key.split('.')
        current = config
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                print(f"Configuration key not found: {key}")
                return False
        
        print(f"{key} = {current}")
        return True
    
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error reading configuration: {e}")
        return False


async def config_reset_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Reset configuration to defaults."""
    config_file = Path.home() / ".buildcli" / "config.json"
    
    if not config_file.exists():
        print("No configuration file found.")
        return False
    
    if not modifiers.get('force', False):
        print("This will reset all configuration to defaults.")
        print("Use --force to confirm reset")
        return False
    
    if modifiers.get('dry_run', False):
        print("[DRY RUN] Would reset configuration to defaults")
        return True
    
    # Remove existing config and reinitialize
    config_file.unlink()
    return await config_init_command([], modifiers)


# Command registration function
async def register_commands() -> Dict[str, Callable]:
    """Register all commands provided by this module."""
    return {
        'config-init': config_init_command,
        'config-show': config_show_command,
        'config-set': config_set_command,
        'config-get': config_get_command,
        'config-reset': config_reset_command,
        'github-config-init': github_config_init_command,
    }


# Alternative function name for compatibility
def get_commands() -> List[str]:
    """Get list of command names provided by this module."""
    return MODULE_INFO['commands']