"""
Store Location Settings
Manages the default location for the POS system and tax calculations
"""

import json
from pathlib import Path
from typing import Optional, Dict
from assets.Logger import Logger
from src.pyinstaller_helpers import get_config_dir

logger = Logger()

class StoreSettings:
    """Manages store/location settings for POS system"""
    
    @property
    def SETTINGS_FILE(self):
        """Get settings file path (handles PyInstaller bundles)"""
        return get_config_dir() / "store_settings.json"
    
    DEFAULT_SETTINGS = {
        "store_name": "My Store",
        "location": {
            "state": None,
            "city": None,
            "zip_code": None,
            "address": ""
        },
        "tax_settings": {
            "include_state_tax": True,
            "include_federal_tax": False,
            "include_local_tax": True,
            "auto_calculate": True
        }
    }
    
    def __init__(self):
        """Initialize store settings"""
        self.settings = self._load_settings()
    
    def _load_settings(self) -> Dict:
        """Load settings from file or create default"""
        try:
            if self.SETTINGS_FILE.exists():
                with open(self.SETTINGS_FILE, 'r') as f:
                    settings = json.load(f)
                    logger.debug("StoreSettings", "Loaded store settings from file")
                    return settings
        except Exception as e:
            logger.warning("StoreSettings", f"Could not load settings: {e}")
        
        # Create default settings
        logger.info("StoreSettings", "Creating default store settings")
        self._save_settings(self.DEFAULT_SETTINGS.copy())
        return self.DEFAULT_SETTINGS.copy()
    
    def _save_settings(self, settings: Dict) -> bool:
        """Save settings to file"""
        try:
            self.SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(self.SETTINGS_FILE, 'w') as f:
                json.dump(settings, f, indent=2)
            logger.info("StoreSettings", "Saved store settings")
            return True
        except Exception as e:
            logger.error("StoreSettings", f"Could not save settings: {e}")
            return False
    
    def get_location(self) -> Optional[str]:
        """Get current store location (state code or full location string)"""
        state = self.settings.get("location", {}).get("state")
        city = self.settings.get("location", {}).get("city")
        
        if state and city:
            return f"{city}, {state}"
        return state
    
    def set_location(self, state: str = None, city: str = None, zip_code: str = None) -> bool:
        """Set store location"""
        try:
            self.settings["location"] = {
                "state": state,
                "city": city,
                "zip_code": zip_code,
                "address": self.settings["location"].get("address", "")
            }
            return self._save_settings(self.settings)
        except Exception as e:
            logger.error("StoreSettings", f"Could not set location: {e}")
            return False
    
    def set_store_name(self, name: str) -> bool:
        """Set store name"""
        try:
            self.settings["store_name"] = name
            return self._save_settings(self.settings)
        except Exception as e:
            logger.error("StoreSettings", f"Could not set store name: {e}")
            return False
    
    def set_address(self, address: str) -> bool:
        """Set store address"""
        try:
            self.settings["location"]["address"] = address
            return self._save_settings(self.settings)
        except Exception as e:
            logger.error("StoreSettings", f"Could not set address: {e}")
            return False
    
    def get_tax_preferences(self) -> Dict:
        """Get tax calculation preferences"""
        return self.settings.get("tax_settings", self.DEFAULT_SETTINGS["tax_settings"].copy())
    
    def set_tax_preferences(self, preferences: Dict) -> bool:
        """Set tax calculation preferences"""
        try:
            self.settings["tax_settings"] = preferences
            return self._save_settings(self.settings)
        except Exception as e:
            logger.error("StoreSettings", f"Could not set tax preferences: {e}")
            return False
    
    def get_all_settings(self) -> Dict:
        """Get all settings"""
        return self.settings.copy()
    
    def reset_to_defaults(self) -> bool:
        """Reset all settings to defaults"""
        try:
            self.settings = self.DEFAULT_SETTINGS.copy()
            return self._save_settings(self.settings)
        except Exception as e:
            logger.error("StoreSettings", f"Could not reset settings: {e}")
            return False
