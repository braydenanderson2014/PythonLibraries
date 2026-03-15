"""
Unified Account Manager
Supports both JSON and SQLite database backends with seamless switching
"""

import os
import json
import sys

# Ensure src directory is in path for absolute imports
_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

from assets.Logger import Logger
from typing import Optional, Dict, Any, List

try:
    from .hasher import hash_password, verify_hash, legacy_hash
    from .app_paths import ACCOUNT_DB, get_resource_path
    from .account_db import AccountDatabaseManager
except ImportError:
    from hasher import hash_password, verify_hash, legacy_hash
    from app_paths import ACCOUNT_DB, get_resource_path
    from account_db import AccountDatabaseManager

logger = Logger()


class UnifiedAccountManager:
    """
    Unified account manager that supports both JSON and SQLite backends.
    Automatically switches based on configuration.
    """
    
    # Storage backend types
    BACKEND_JSON = 'json'
    BACKEND_DATABASE = 'database'
    
    def __init__(self, backend: str = None):
        """
        Initialize account manager
        
        Args:
            backend: Storage backend ('json' or 'database'). 
                    If None, reads from config or auto-detects
        """
        self.backend = backend or self._detect_backend()
        self.accounts = {}  # For JSON backend
        self.db_manager = None  # For database backend
        
        if self.backend == self.BACKEND_DATABASE:
            self.db_manager = AccountDatabaseManager()
            logger.info("Account", "Account manager initialized with DATABASE backend")
        else:
            self.load()
            logger.info("Account", "Account manager initialized with JSON backend")
    
    def _detect_backend(self) -> str:
        """
        Auto-detect which backend to use
        
        Returns:
            Backend type (json or database)
        """
        # Check for config file
        config_path = get_resource_path("account_config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    backend = config.get('backend', self.BACKEND_JSON)
                    logger.info("Account", f"Backend loaded from config: {backend}")
                    return backend
            except Exception as e:
                logger.warning("Account", f"Error reading config: {e}")
        
        # Check if database exists and has users
        db_path = get_resource_path("accounts.db")
        if os.path.exists(db_path):
            try:
                db_manager = AccountDatabaseManager(db_path)
                stats = db_manager.get_stats()
                if stats['total_users'] > 0:
                    logger.info("Account", f"Database detected with {stats['total_users']} users")
                    return self.BACKEND_DATABASE
            except Exception as e:
                logger.warning("Account", f"Error checking database: {e}")
        
        # Default to JSON
        logger.info("Account", "Defaulting to JSON backend")
        return self.BACKEND_JSON
    
    def set_backend(self, backend: str, save_config: bool = True):
        """
        Switch storage backend
        
        Args:
            backend: Backend type ('json' or 'database')
            save_config: Whether to save choice to config file
        """
        if backend not in [self.BACKEND_JSON, self.BACKEND_DATABASE]:
            raise ValueError(f"Invalid backend: {backend}")
        
        self.backend = backend
        
        if backend == self.BACKEND_DATABASE:
            self.db_manager = AccountDatabaseManager()
        else:
            self.load()
        
        if save_config:
            config_path = get_resource_path("account_config.json")
            with open(config_path, 'w') as f:
                json.dump({'backend': backend}, f, indent=2)
        
        logger.info("Account", f"Backend switched to: {backend}")
    
    def create_account(self, username: str, password: str, **details) -> Dict[str, Any]:
        """
        Create a new user account
        
        Args:
            username: Username (must be unique)
            password: Plain text password
            **details: Additional account details
            
        Returns:
            Account data dictionary
        """
        if self.backend == self.BACKEND_DATABASE:
            # Generate account_id
            import random
            import string
            account_id = ''.join(random.SystemRandom().choice(
                string.ascii_letters + string.digits) for _ in range(10))
            
            return self.db_manager.create_user(username, password, account_id, **details)
        
        else:  # JSON backend
            if username in self.accounts:
                raise ValueError('Username already exists')
            
            import random
            import string
            account_id = ''.join(random.SystemRandom().choice(
                string.ascii_letters + string.digits) for _ in range(10))
            
            self.accounts[username] = {
                'account_id': account_id,
                'username': username,
                'password_hash': hash_password(password),
                'details': details
            }
            self.save()
            return self.accounts[username]
    
    def get_account(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get account by username
        
        Args:
            username: Username to search for
            
        Returns:
            Account dictionary or None
        """
        if self.backend == self.BACKEND_DATABASE:
            return self.db_manager.get_user_by_username(username)
        else:
            return self.accounts.get(username)
    
    def get_account_by_id(self, account_id: str) -> Optional[Dict[str, Any]]:
        """
        Get account by account ID
        
        Args:
            account_id: Account ID to search for
            
        Returns:
            Account dictionary or None
        """
        if self.backend == self.BACKEND_DATABASE:
            return self.db_manager.get_user_by_account_id(account_id)
        else:
            for acc in self.accounts.values():
                if acc.get('account_id') == account_id:
                    return acc
            return None
    
    def update_account(self, username: str, **details) -> bool:
        """
        Update account details
        
        Args:
            username: Username of account to update
            **details: Fields to update
            
        Returns:
            True if successful
        """
        if self.backend == self.BACKEND_DATABASE:
            return self.db_manager.update_user(username, **details)
        else:
            if username not in self.accounts:
                raise ValueError('Account not found')
            self.accounts[username]['details'].update(details)
            self.save()
            return True
    
    def verify_password(self, username: str, password: str) -> bool:
        """
        Verify user password
        
        Args:
            username: Username
            password: Plain text password to verify
            
        Returns:
            True if password matches, False otherwise
        """
        if self.backend == self.BACKEND_DATABASE:
            result = self.db_manager.verify_password(username, password)
            if result:
                # Update last login
                self.db_manager.update_last_login(username)
            return result
        else:
            acc = self.get_account(username)
            if not acc:
                return False
            
            stored = acc.get('password_hash', '')
            if verify_hash(stored, password):
                # Upgrade legacy hash if needed
                if stored == legacy_hash(password):
                    acc['password_hash'] = hash_password(password)
                    self.save()
                return True
            return False
    
    def change_password(self, username: str, new_password: str) -> bool:
        """
        Change user password
        
        Args:
            username: Username
            new_password: New plain text password
            
        Returns:
            True if successful
        """
        if self.backend == self.BACKEND_DATABASE:
            return self.db_manager.change_password(username, new_password)
        else:
            if username not in self.accounts:
                raise ValueError('Account not found')
            self.accounts[username]['password_hash'] = hash_password(new_password)
            self.save()
            return True
    
    def delete_account(self, username: str) -> bool:
        """
        Delete user account
        
        Args:
            username: Username to delete
            
        Returns:
            True if successful
        """
        if self.backend == self.BACKEND_DATABASE:
            return self.db_manager.delete_user(username)
        else:
            if username not in self.accounts:
                raise ValueError('Account not found')
            del self.accounts[username]
            self.save()
            return True
    
    def list_accounts(self, active_only: bool = True) -> List[str]:
        """
        List all usernames
        
        Args:
            active_only: If True, only return active users (database only)
            
        Returns:
            List of usernames
        """
        if self.backend == self.BACKEND_DATABASE:
            users = self.db_manager.list_users(active_only=active_only)
            return [user['username'] for user in users]
        else:
            return list(self.accounts.keys())
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get account statistics
        
        Returns:
            Dictionary with stats
        """
        if self.backend == self.BACKEND_DATABASE:
            return self.db_manager.get_stats()
        else:
            return {
                'backend': 'json',
                'total_users': len(self.accounts),
                'file_path': ACCOUNT_DB,
                'file_size': os.path.getsize(ACCOUNT_DB) if os.path.exists(ACCOUNT_DB) else 0
            }
    
    # JSON-specific methods
    
    def save(self):
        """Save accounts to JSON file (JSON backend only)"""
        if self.backend != self.BACKEND_JSON:
            logger.warning("Account", "save() called but not using JSON backend")
            return
        
        with open(ACCOUNT_DB, 'w') as f:
            json.dump(self.accounts, f, indent=2)
    
    def load(self):
        """Load accounts from JSON file (JSON backend only)"""
        if self.backend != self.BACKEND_JSON:
            logger.warning("Account", "load() called but not using JSON backend")
            return
        
        if os.path.exists(ACCOUNT_DB):
            with open(ACCOUNT_DB, 'r') as f:
                self.accounts = json.load(f)
        else:
            self.accounts = {}


# Backward compatibility - default instance
_default_manager = None

def get_account_manager(backend: str = None) -> UnifiedAccountManager:
    """Get or create default account manager instance"""
    global _default_manager
    if _default_manager is None or (backend and _default_manager.backend != backend):
        _default_manager = UnifiedAccountManager(backend)
    return _default_manager


# Legacy AccountManager for backward compatibility
class AccountManager(UnifiedAccountManager):
    """
    Legacy AccountManager class for backward compatibility.
    Simply inherits from UnifiedAccountManager with default JSON backend.
    """
    
    def __init__(self):
        """Initialize with JSON backend for backward compatibility"""
        super().__init__(backend=UnifiedAccountManager.BACKEND_JSON)
