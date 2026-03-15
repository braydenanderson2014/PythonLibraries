"""
Settings Manager for Hunger Games Simulator
Handles loading, validation, and access to game settings.
"""

import json
import os
from typing import Dict, Any, Optional

class SettingsManager:
    """Manages game settings from settings.json file."""

    DEFAULT_SETTINGS = {
        "game_mode": "console",
        "phase_delays": {
            "base_delay": 3.0,
            "morning": 1.0,
            "afternoon": 1.2,
            "evening": 1.5,
            "environmental": 2.0,
            "randomness": 0.25,
            "progression_factor": 0.05
        },
        "tribute_settings": {
            "max_tributes": 24,
            "max_per_district": 2,
            "enforce_gender_balance": True,
            "allow_custom_tributes": True,
            "districts": 12
        },
        "game_rules": {
            "context_filter_enabled": True,
            "work_friendly_mode": True,
            "auto_save_enabled": True,
            "sponsor_gifts_enabled": True,
            "alliances_enabled": True,
            "sanity_decay_enabled": True
        },
        "output_settings": {
            "web_output_file": "data/web_output.json",
            "log_file": "data/game_log.txt",
            "verbose_logging": False,
            "real_time_updates": True
        },
        "difficulty_settings": {
            "arena_event_frequency": 0.02,
            "resource_decay_rate": 1.0,
            "combat_lethality": 1.0,
            "environmental_harshness": 1.0
        },
        "web_settings": {
            "host": "localhost",
            "port": 8080,
            "max_connections": 100,
            "update_interval": 0.1
        }
    }

    def __init__(self, settings_file: str = "settings.json"):
        self.settings_file = settings_file
        self.settings = self._load_settings()

    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from file, merging with defaults."""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    user_settings = json.load(f)
                # Deep merge user settings with defaults
                return self._deep_merge(self.DEFAULT_SETTINGS.copy(), user_settings)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load settings file: {e}")
                print("Using default settings.")
                return self.DEFAULT_SETTINGS.copy()
        else:
            print(f"Settings file '{self.settings_file}' not found. Creating with defaults.")
            self.save_settings()
            return self.DEFAULT_SETTINGS.copy()

    def _deep_merge(self, base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()
        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def save_settings(self) -> None:
        """Save current settings to file."""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save settings file: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value by key (supports dot notation)."""
        keys = key.split('.')
        value = self.settings
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any) -> None:
        """Set a setting value by key (supports dot notation)."""
        keys = key.split('.')
        settings = self.settings
        for k in keys[:-1]:
            if k not in settings or not isinstance(settings[k], dict):
                settings[k] = {}
            settings = settings[k]
        settings[keys[-1]] = value
        self.save_settings()

    def get_game_mode(self) -> str:
        """Get the current game mode."""
        return self.get('game_mode', 'console')

    def is_web_mode(self) -> bool:
        """Check if running in web mode."""
        return self.get_game_mode() == 'web'

    def get_phase_delay(self, phase: str = 'base_delay') -> float:
        """Get phase delay for specific phase."""
        return self.get(f'phase_delays.{phase}', 3.0)

    def get_max_tributes(self) -> int:
        """Get maximum number of tributes."""
        return self.get('tribute_settings.max_tributes', 24)

    def get_max_per_district(self) -> int:
        """Get maximum tributes per district."""
        return self.get('tribute_settings.max_per_district', 2)

    def enforce_gender_balance(self) -> bool:
        """Check if gender balance should be enforced."""
        return self.get('tribute_settings.enforce_gender_balance', True)

    def get_web_output_file(self) -> str:
        """Get web output file path."""
        return self.get('output_settings.web_output_file', 'data/web_output.json')

    def get_log_file(self) -> str:
        """Get log file path."""
        return self.get('output_settings.log_file', 'data/game_log.txt')

    def verbose_logging_enabled(self) -> bool:
        """Check if verbose logging is enabled."""
        return self.get('output_settings.verbose_logging', False)

    def real_time_updates_enabled(self) -> bool:
        """Check if real-time updates are enabled."""
        return self.get('output_settings.real_time_updates', True)

# Global settings manager instance
settings_manager = SettingsManager()