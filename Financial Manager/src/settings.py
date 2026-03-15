import os
import json
try:
    from . import app_paths
    from assets.Logger import Logger
except ImportError:
    # Handle absolute import when imported as a top-level module
    import app_paths
    from assets.Logger import Logger

logger = Logger()

# Initialize app_paths after logger is ready
app_paths._initialize_paths()

class SettingsController:
    DEFAULTS = {
        'uac_enabled': True,
        'uac_duration_seconds': 300,  # 5 minutes
        'theme': 'system',  # Options: 'dark', 'light', 'system'
        'default_rent_amount': 1200.0,
        'default_deposit_amount': 1200.0,
        'default_due_day': '1',
        'log_file_path': app_paths.LOG_FILE,
        'max_log_size_mb': 10,
        'log_backup_count': 3,
    }
    THEMES = ['dark', 'light', 'system', 'blue', 'high-contrast']
    
    def __init__(self):
        logger.debug("SettingsController", "Initializing SettingsController")
        self.settings = dict(self.DEFAULTS)
        self.load()
        logger.info("SettingsController", "SettingsController initialized")

    def set(self, key, value):
        logger.debug("SettingsController", f"Setting {key} = {value}")
        self.settings[key] = value
        self.save()

    def get(self, key):
        value = self.settings.get(key, self.DEFAULTS.get(key))
        logger.debug("SettingsController", f"Getting {key} = {value}")
        return value

    def save(self):
        try:
            with open(app_paths.SETTINGS_FILE, 'w') as f:
                json.dump(self.settings, f, indent=2)
            logger.debug("SettingsController", f"Settings saved to {app_paths.SETTINGS_FILE}")
        except Exception as e:
            logger.error("SettingsController", f"Failed to save settings: {str(e)}")

    def load(self):
        try:
            if os.path.exists(app_paths.SETTINGS_FILE):
                with open(app_paths.SETTINGS_FILE, 'r') as f:
                    self.settings = json.load(f)
                logger.debug("SettingsController", f"Settings loaded from {app_paths.SETTINGS_FILE}")
            else:
                logger.debug("SettingsController", f"Settings file not found, using defaults")
                self.settings = dict(self.DEFAULTS)
        except Exception as e:
            logger.warning("SettingsController", f"Error loading settings: {str(e)}, using defaults")
            self.settings = dict(self.DEFAULTS)

    def set_theme(self, theme):
        logger.debug("SettingsController", f"Setting theme to {theme}")
        if theme in self.THEMES:
            self.set('theme', theme)
            logger.info("SettingsController", f"Theme changed to {theme}")
        else:
            error_msg = f"Theme '{theme}' is not supported. Supported themes: {self.THEMES}"
            logger.error("SettingsController", error_msg)
            raise ValueError(error_msg)

    def get_theme(self):
        theme = self.get('theme')
        logger.debug("SettingsController", f"Current theme: {theme}")
        return theme
