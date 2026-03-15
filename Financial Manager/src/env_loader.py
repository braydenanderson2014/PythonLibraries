"""Load environment variables from env.env file."""

import os
from pathlib import Path


def load_env_file(env_path: str | None = None) -> dict:
    """Load environment variables from .env file.
    
    Parameters
    ----------
    env_path : str | None
        Path to .env file. If None, looks in common locations:
        - resources/env.env
        - .env
        - /etc/.env
    
    Returns
    -------
    dict
        Dictionary of loaded environment variables
    """
    if env_path is None:
        # Try common locations
        possible_paths = [
            Path(__file__).parent / ".." / "resources" / "env.env",
            Path.cwd() / "env.env",
            Path.cwd() / "resources" / "env.env",
            Path.cwd() / ".env",
        ]
        
        for path in possible_paths:
            if path.exists():
                env_path = str(path)
                break
    
    loaded = {}
    
    if env_path and os.path.exists(env_path):
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse KEY=VALUE
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        
                        # Set in environment AND return
                        os.environ[key] = value
                        loaded[key] = value
        except Exception as e:
            print(f"Warning: Could not load env file from {env_path}: {e}")
    
    return loaded


# Auto-load on import
_loaded_vars = load_env_file()
