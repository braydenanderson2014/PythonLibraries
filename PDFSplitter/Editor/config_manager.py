# editor/config_manager.py

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

class ConfigManager:
    """
    Manages application and renderer configuration.
    PyInstaller-compatible configuration management.
    """
    
    def __init__(self, editor):
        self.editor = editor
        self.config_dir = Path.home() / ".pdfutility"
        self.config_file = self.config_dir / "editor_config.json"
        self.renderer_configs = {}
        
        self._ensure_config_dir()
        self._load_config()
    
    def _ensure_config_dir(self):
        """Ensure configuration directory exists."""
        self.config_dir.mkdir(exist_ok=True)
    
    def _load_config(self):
        """Load configuration from disk."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.renderer_configs = config.get("renderers", {})
                    return config
            except Exception as e:
                self.editor.logger.warning(
                    "ConfigManager",
                    f"Could not load config: {e}"
                )
        return {}
    
    def save_config(self):
        """Save current configuration to disk."""
        config = {
            "renderers": self.renderer_configs,
            "version": "1.0.0"
        }
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            self.editor.logger.error(
                "ConfigManager",
                f"Could not save config: {e}"
            )
    
    def get_renderer_config(self, renderer_name: str) -> Dict[str, Any]:
        """Get configuration for a specific renderer."""
        return self.renderer_configs.get(renderer_name, {})
    
    def set_renderer_config(self, renderer_name: str, config: Dict[str, Any]):
        """Set configuration for a specific renderer."""
        self.renderer_configs[renderer_name] = config
        self.save_config()
    
    def update_renderer_config(self, renderer_name: str, updates: Dict[str, Any]):
        """Update specific settings for a renderer."""
        if renderer_name not in self.renderer_configs:
            self.renderer_configs[renderer_name] = {}
        
        self.renderer_configs[renderer_name].update(updates)
        self.save_config()
    
    def reset_renderer_config(self, renderer_name: str):
        """Reset renderer configuration to defaults."""
        if renderer_name in self.renderer_configs:
            del self.renderer_configs[renderer_name]
            self.save_config()
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a global setting."""
        config = self._load_config()
        return config.get(key, default)
    
    def set_setting(self, key: str, value: Any):
        """Set a global setting."""
        config = self._load_config()
        config[key] = value
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            self.editor.logger.error(
                "ConfigManager",
                f"Could not save setting {key}: {e}"
            )
