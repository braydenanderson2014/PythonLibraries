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
    DEFAULT_PAYMENT_TYPES = [
        'Cash', 'Bilt', 'Zelle', 'Bank Transfer', 'Check', 'Venmo',
        'Overpayment Credit', 'Service Credit', 'Other',
    ]
    # Types that cannot be removed by the user
    _PROTECTED_TYPES = frozenset({'Overpayment Credit', 'Service Credit', 'Other'})

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

    # ------------------------------------------------------------------ #
    # Payment type management                                              #
    # ------------------------------------------------------------------ #

    def get_payment_types(self):
        """Return the ordered list of payment types (user-defined + built-ins)."""
        stored = self.settings.get('payment_types')
        if not stored:
            return list(self.DEFAULT_PAYMENT_TYPES)
        result = list(stored)
        for required in ('Overpayment Credit', 'Service Credit', 'Other'):
            if required not in result:
                result.append(required)
        return result

    def add_payment_type(self, type_name):
        """Add a custom payment type.  Returns True if added, False if already exists."""
        type_name = type_name.strip()
        if not type_name:
            return False
        types = self.get_payment_types()
        if type_name in types:
            return False
        try:
            types.insert(types.index('Other'), type_name)
        except ValueError:
            types.append(type_name)
        self.set('payment_types', types)
        logger.info("SettingsController", f"Added payment type: {type_name}")
        return True

    def remove_payment_type(self, type_name):
        """Remove a user-defined payment type.  Returns True if removed."""
        if type_name in self._PROTECTED_TYPES:
            return False
        types = self.get_payment_types()
        if type_name not in types:
            return False
        types.remove(type_name)
        self.set('payment_types', types)
        logger.info("SettingsController", f"Removed payment type: {type_name}")
        return True

    def get_theme_palette(self, theme=None):
        theme_name = (theme or self.get_theme() or 'light').lower()
        if theme_name == 'system':
            theme_name = 'light'

        palettes = {
            'dark': {
                'window_bg': '#181c20',
                'panel_bg': '#23272d',
                'surface_bg': '#2d3238',
                'input_bg': '#1f2329',
                'border': '#434b55',
                'text': '#f3f4f6',
                'muted_text': '#b8c0c8',
                'accent': '#2d8cff',
                'accent_hover': '#1f7bf0',
                'accent_pressed': '#1566d1',
                'success': '#2fa36b',
                'warning': '#d98a1d',
                'danger': '#d84c4c',
                'header_bg': '#343a40',
                'menu_bg': '#23272d',
                'menu_selected_bg': '#2d8cff',
                'button_text': '#ffffff',
            },
            'light': {
                'window_bg': '#f5f7fb',
                'panel_bg': '#ffffff',
                'surface_bg': '#ffffff',
                'input_bg': '#ffffff',
                'border': '#cfd7e3',
                'text': '#1f2937',
                'muted_text': '#5f6b7a',
                'accent': '#0d6efd',
                'accent_hover': '#0b5ed7',
                'accent_pressed': '#0a58ca',
                'success': '#198754',
                'warning': '#d97706',
                'danger': '#dc3545',
                'header_bg': '#e9eef6',
                'menu_bg': '#ffffff',
                'menu_selected_bg': '#dbeafe',
                'button_text': '#ffffff',
            },
            'blue': {
                'window_bg': '#eaf4ff',
                'panel_bg': '#ffffff',
                'surface_bg': '#f5faff',
                'input_bg': '#ffffff',
                'border': '#9ec5fe',
                'text': '#0b3768',
                'muted_text': '#4d6a8c',
                'accent': '#1565c0',
                'accent_hover': '#0d47a1',
                'accent_pressed': '#08306b',
                'success': '#198754',
                'warning': '#ef6c00',
                'danger': '#c62828',
                'header_bg': '#d7e9ff',
                'menu_bg': '#f5faff',
                'menu_selected_bg': '#bbdefb',
                'button_text': '#ffffff',
            },
            'high-contrast': {
                'window_bg': '#000000',
                'panel_bg': '#111111',
                'surface_bg': '#000000',
                'input_bg': '#111111',
                'border': '#ffffff',
                'text': '#ffffff',
                'muted_text': '#f5f5f5',
                'accent': '#ffff00',
                'accent_hover': '#ffd400',
                'accent_pressed': '#ffb300',
                'success': '#00ff00',
                'warning': '#ffff00',
                'danger': '#ff4d4d',
                'header_bg': '#000000',
                'menu_bg': '#000000',
                'menu_selected_bg': '#333333',
                'button_text': '#000000',
            },
        }

        palette = dict(palettes.get(theme_name, palettes['light']))
        palette['theme_name'] = theme_name
        return palette

    def get_main_window_stylesheet(self, theme=None):
        palette = self.get_theme_palette(theme)
        return f'''
            QMainWindow {{
                background-color: {palette['window_bg']};
                color: {palette['text']};
            }}
            QMenuBar {{
                background-color: {palette['menu_bg']};
                color: {palette['text']};
                border-bottom: 1px solid {palette['border']};
            }}
            QMenuBar::item {{
                background: transparent;
                color: {palette['text']};
                padding: 6px 10px;
            }}
            QMenuBar::item:selected {{
                background-color: {palette['menu_selected_bg']};
            }}
            QMenu {{
                background-color: {palette['menu_bg']};
                color: {palette['text']};
                border: 1px solid {palette['border']};
            }}
            QMenu::item {{
                padding: 6px 24px 6px 12px;
            }}
            QMenu::item:selected {{
                background-color: {palette['menu_selected_bg']};
                color: {palette['text']};
            }}
            QTabWidget::pane {{
                border: 1px solid {palette['border']};
                background-color: {palette['panel_bg']};
            }}
            QTabBar::tab {{
                background-color: {palette['header_bg']};
                color: {palette['text']};
                padding: 8px 14px;
                border: 1px solid {palette['border']};
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background-color: {palette['panel_bg']};
                border-bottom-color: {palette['panel_bg']};
            }}
        '''
