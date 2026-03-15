"""
Configuration management for BuildCLI.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    """Configuration manager for BuildCLI."""
    
    def __init__(self, config_file: Optional[str] = None):
        self.version = "1.0.0"
        self.config_file = config_file or self._get_default_config_path()
        self.config_data = self._load_config()
        
        # Default configuration values
        self.defaults = {
            "log_level": "INFO",
            "auto_update_modules": False,
            "remote_module_repo": "https://github.com/your-org/buildcli-modules",
            "module_cache_dir": str(Path.home() / ".buildcli" / "modules"),
            "temp_dir": str(Path.home() / ".buildcli" / "temp"),
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
    
    def _get_default_config_path(self) -> str:
        """Get the default configuration file path."""
        # Use program_configuration directory for local config
        config_dir = Path("program_configuration")
        config_dir.mkdir(exist_ok=True)
        return str(config_dir / "config.json")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load config file {self.config_file}: {e}")
        
        return {}
    
    def save_config(self) -> bool:
        """Save current configuration to file."""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=2)
            return True
        except IOError as e:
            print(f"Error saving config file {self.config_file}: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        # Support nested keys using dot notation
        keys = key.split('.')
        value = self.config_data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                # Fall back to defaults
                default_value = self.defaults
                for dk in keys:
                    if isinstance(default_value, dict) and dk in default_value:
                        default_value = default_value[dk]
                    else:
                        default_value = default
                        break
                return default_value
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        keys = key.split('.')
        config = self.config_data
        
        # Create nested structure if needed
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    @property
    def log_level(self) -> str:
        """Get the log level."""
        return self.get("log_level", "INFO")
    
    @property
    def auto_update_modules(self) -> bool:
        """Get the auto update modules setting."""
        return self.get("auto_update_modules", False)
    
    @property
    def remote_module_repo(self) -> str:
        """Get the remote module repository URL."""
        return self.get("remote_module_repo", self.defaults["remote_module_repo"])
    
    @property
    def module_cache_dir(self) -> str:
        """Get the module cache directory."""
        return self.get("module_cache_dir", self.defaults["module_cache_dir"])
    
    @property
    def temp_dir(self) -> str:
        """Get the temporary directory."""
        return self.get("temp_dir", self.defaults["temp_dir"])
    
    @property
    def parallel_execution(self) -> bool:
        """Get the parallel execution setting."""
        return self.get("parallel_execution", True)
    
    @property
    def max_parallel_commands(self) -> int:
        """Get the maximum number of parallel commands."""
        return self.get("max_parallel_commands", 4)
    
    @property
    def timeout_seconds(self) -> int:
        """Get the command timeout in seconds."""
        return self.get("timeout_seconds", 300)