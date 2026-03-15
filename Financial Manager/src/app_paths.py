"""
Path utilities for Financial Manager
Handles proper file paths for both development and PyInstaller bundled modes
"""

import os
import sys
from pathlib import Path
from assets.Logger import Logger

logger = Logger()
def get_app_data_dir():
    """
    Get the application data directory that persists across runs.
    
    In development: uses ./resources relative to the application
    In PyInstaller bundle: uses user's AppData/Application Support directory
    """
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle
        if sys.platform == 'win32':
            # Windows: Use AppData/Roaming
            app_data = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'FinancialManager')
            logger.info("AppPaths", f"Using Windows AppData directory: {app_data}")
        
        elif sys.platform == 'darwin':
            # macOS: Use Application Support
            app_data = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', 'FinancialManager')
            logger.info("AppPaths", f"Using macOS Application Support directory: {app_data}")
        else:
            # Linux: Use XDG_DATA_HOME or ~/.local/share
            xdg_data_home = os.environ.get('XDG_DATA_HOME', os.path.join(os.path.expanduser('~'), '.local', 'share'))
            app_data = os.path.join(xdg_data_home, 'FinancialManager')
            logger.info("AppPaths", f"Using Linux data directory: {app_data}")
        
        # Create directory if it doesn't exist
        os.makedirs(app_data, exist_ok=True)
        return app_data
    else:
        # Running in development mode - use resources directory relative to project
        # Go up from src/ to project root, then into resources/
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        resources_dir = os.path.join(base_dir, 'resources')
        os.makedirs(resources_dir, exist_ok=True)
        logger.info("AppPaths", f"Using development resources directory: {resources_dir}")
        return resources_dir


def get_resource_path(filename):
    """
    Get the full path for a resource file (database, config, etc.)
    
    Args:
        filename: Name of the resource file (e.g., 'accounts.json')
    
    Returns:
        Full path to the resource file
    """
    try:
        logger.info("AppPaths", f"Getting resource path for: {filename}")
    except:
        # If logger not yet initialized, skip logging
        pass

    return os.path.join(get_app_data_dir(), filename)


# Lazy-loaded paths - computed on first access, not at import time
_paths_cache = {}

def _get_path(key, filename):
    """Helper to lazily compute and cache paths"""
    if key not in _paths_cache:
        _paths_cache[key] = get_resource_path(filename)
    return _paths_cache[key]

# Define path getters as properties using module-level functions
def get_ACCOUNT_DB():
    return _get_path('ACCOUNT_DB', 'accounts.json')

def get_TENANT_DB():
    return _get_path('TENANT_DB', 'tenants.json')

def get_WATCHLIST_DB():
    return _get_path('WATCHLIST_DB', 'watchlists.json')

def get_STOCK_DB():
    return _get_path('STOCK_DB', 'stocks.json')

def get_PORTFOLIO_DB():
    return _get_path('PORTFOLIO_DB', 'portfolios.json')

def get_BANK_DATA_FILE():
    return _get_path('BANK_DATA_FILE', 'bank_data.json')

def get_RECURRING_DATA_FILE():
    return _get_path('RECURRING_DATA_FILE', 'recurring_transactions.json')

def get_USER_FINANCE_SETTINGS_FILE():
    return _get_path('USER_FINANCE_SETTINGS_FILE', 'user_finance_settings.json')

def get_LOANS_DATA_FILE():
    return _get_path('LOANS_DATA_FILE', 'loans.json')

def get_BUDGETS_DATA_FILE():
    return _get_path('BUDGETS_DATA_FILE', 'budgets.json')

def get_BANK_ACCOUNTS_FILE():
    return _get_path('BANK_ACCOUNTS_FILE', 'bank_accounts.json')

def get_BANKING_API_CONFIG_FILE():
    return _get_path('BANKING_API_CONFIG_FILE', 'banking_api_config.json')

def get_LINKED_ACCOUNTS_FILE():
    return _get_path('LINKED_ACCOUNTS_FILE', 'linked_bank_accounts.json')

def get_NOTIFICATION_STATE_FILE():
    return _get_path('NOTIFICATION_STATE_FILE', 'notification_state.json')

def get_SETTINGS_FILE():
    return _get_path('SETTINGS_FILE', 'settings.json')

def get_LOG_FILE():
    return _get_path('LOG_FILE', 'financial_tracker.log')

# For backward compatibility, provide direct access with lazy evaluation
# These will be evaluated on first access
@property
def ACCOUNT_DB():
    return get_ACCOUNT_DB()

# Simpler approach: just define them as computed properties at module level
# by wrapping in a function that gets called on import
ACCOUNT_DB = None
TENANT_DB = None
WATCHLIST_DB = None
STOCK_DB = None
PORTFOLIO_DB = None
BANK_DATA_FILE = None
RECURRING_DATA_FILE = None
USER_FINANCE_SETTINGS_FILE = None
LOANS_DATA_FILE = None
BUDGETS_DATA_FILE = None
BANK_ACCOUNTS_FILE = None
BANKING_API_CONFIG_FILE = None
LINKED_ACCOUNTS_FILE = None
NOTIFICATION_STATE_FILE = None
SETTINGS_FILE = None
LOG_FILE = None
RULES_FILE = None
AUTOMATION_STATE_FILE = None
AUTOMATION_SETTINGS_FILE = None
ACTION_QUEUE_FILE = None
USER_DB = None

def _initialize_paths():
    """Initialize all paths - call this after Logger is ready"""
    global ACCOUNT_DB, TENANT_DB, WATCHLIST_DB, STOCK_DB, PORTFOLIO_DB
    global BANK_DATA_FILE, RECURRING_DATA_FILE, USER_FINANCE_SETTINGS_FILE
    global LOANS_DATA_FILE, BUDGETS_DATA_FILE, BANK_ACCOUNTS_FILE
    global BANKING_API_CONFIG_FILE, LINKED_ACCOUNTS_FILE, NOTIFICATION_STATE_FILE
    global SETTINGS_FILE, LOG_FILE
    global RULES_FILE, AUTOMATION_STATE_FILE, AUTOMATION_SETTINGS_FILE, ACTION_QUEUE_FILE, USER_DB
    
    ACCOUNT_DB = get_resource_path('accounts.json')
    TENANT_DB = get_resource_path('tenants.json')
    WATCHLIST_DB = get_resource_path('watchlists.json')
    STOCK_DB = get_resource_path('stocks.json')
    PORTFOLIO_DB = get_resource_path('portfolios.json')
    BANK_DATA_FILE = get_resource_path('bank_data.json')
    RECURRING_DATA_FILE = get_resource_path('recurring_transactions.json')
    USER_FINANCE_SETTINGS_FILE = get_resource_path('user_finance_settings.json')
    LOANS_DATA_FILE = get_resource_path('loans.json')
    BUDGETS_DATA_FILE = get_resource_path('budgets.json')
    BANK_ACCOUNTS_FILE = get_resource_path('bank_accounts.json')
    BANKING_API_CONFIG_FILE = get_resource_path('banking_api_config.json')
    LINKED_ACCOUNTS_FILE = get_resource_path('linked_bank_accounts.json')
    NOTIFICATION_STATE_FILE = get_resource_path('notification_state.json')
    SETTINGS_FILE = get_resource_path('settings.json')
    LOG_FILE = get_resource_path('financial_tracker.log')
    RULES_FILE = get_resource_path('transaction_rules.json')
    AUTOMATION_STATE_FILE = get_resource_path('automation_state.json')
    AUTOMATION_SETTINGS_FILE = get_resource_path('automation_settings.json')
    ACTION_QUEUE_FILE = get_resource_path('action_queue.json')
    USER_DB = get_resource_path('users.db')

# Attachments directory (not a file)
ATTACHMENTS_DIR = os.path.join(get_app_data_dir(), 'attachments')


def get_app_info():
    """Get information about the application runtime environment"""
    info = {
        'frozen': getattr(sys, 'frozen', False),
        'app_data_dir': get_app_data_dir(),
        'platform': sys.platform,
    }
    
    if getattr(sys, 'frozen', False):
        info['bundle_dir'] = getattr(sys, '_MEIPASS', None)
    
    return info


def print_path_info():
    """Debug utility to print current path configuration"""
    info = get_app_info()
    logger.info("AppPaths", "=== Financial Manager Path Configuration ===")
    logger.info("AppPaths", f"Running as bundle: {info['frozen']}")
    logger.info("AppPaths", f"Platform: {info['platform']}")
    logger.info("AppPaths", f"App data directory: {info['app_data_dir']}")
    if 'bundle_dir' in info:
        logger.info("AppPaths", f"Bundle extraction dir: {info['bundle_dir']}")
    logger.info("AppPaths", "\nDatabase locations:")
    logger.info("AppPaths", f"  Accounts: {ACCOUNT_DB}")
    logger.info("AppPaths", f"  Tenants: {TENANT_DB}")
    logger.info("AppPaths", f"  Watchlists: {WATCHLIST_DB}")
    logger.info("AppPaths", f"  Stocks: {STOCK_DB}")
    logger.info("AppPaths", f"  Portfolios: {PORTFOLIO_DB}")
    logger.info("AppPaths", f"  Bank Data: {BANK_DATA_FILE}")
    logger.info("AppPaths", f"  Recurring Transactions: {RECURRING_DATA_FILE}")
    logger.info("AppPaths", f"  User Finance Settings: {USER_FINANCE_SETTINGS_FILE}")
    logger.info("AppPaths", f"  Loans: {LOANS_DATA_FILE}")
    logger.info("AppPaths", "=" * 45)

if __name__ == '__main__':
    print_path_info()
