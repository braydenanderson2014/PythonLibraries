"""
Account Migration Utility
Handles automatic migration of credentials from JSON to database storage.
"""

import os
import json
from assets.Logger import Logger
from typing import Optional, Tuple

try:
    from .account_unified import UnifiedAccountManager
    from .account_db import AccountDatabaseManager
    from .account import AccountManager as JSONAccountManager
    from .app_paths import ACCOUNT_DB
except ImportError:
    from account_unified import UnifiedAccountManager
    from account_db import AccountDatabaseManager
    from account import AccountManager as JSONAccountManager
    from app_paths import ACCOUNT_DB

logger = Logger()


class AccountMigration:
    """
    Manages automatic migration of user accounts from JSON to database storage.
    """
    
    def __init__(self):
        """Initialize migration utility"""
        self.json_manager = JSONAccountManager()
        self.db_manager = AccountDatabaseManager()
    
    def detect_login_source(self, username: str) -> Optional[str]:
        """
        Detect where a user's credentials came from (JSON or Database)
        
        Args:
            username: Username to check
            
        Returns:
            'json' if found in JSON, 'database' if found in DB, None if not found
        """
        # Check JSON first
        self.json_manager.load()
        if username in self.json_manager.accounts:
            logger.info("Migration", f"User {username} found in JSON storage")
            return 'json'
        
        # Check database
        db_user = self.db_manager.get_user_by_username(username)
        if db_user:
            logger.info("Migration", f"User {username} found in database storage")
            return 'database'
        
        logger.warning("Migration", f"User {username} not found in either storage backend")
        return None
    
    def is_hash_in_database(self, username: str) -> bool:
        """
        Check if a user's password hash is already stored in the database
        
        Args:
            username: Username to check
            
        Returns:
            True if user exists in database, False otherwise
        """
        db_user = self.db_manager.get_user_by_username(username)
        return db_user is not None
    
    def migrate_json_to_database(self, username: str) -> Tuple[bool, str]:
        """
        Migrate a user's credentials from JSON to database.
        
        If the user exists only in JSON:
            1. Add their account to the database
            2. Remove the entry from JSON
            3. Refresh JSON file to reflect changes
            
        If the user exists in both (should not happen normally):
            1. Just remove from JSON
            2. Refresh JSON file
            
        Args:
            username: Username to migrate
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Reload to ensure latest data
            self.json_manager.load()
            logger.debug("Migration", f"Reloaded JSON data for migration of {username}")
            
            # Check if user is in JSON
            if username not in self.json_manager.accounts:
                logger.warning("Migration", f"User {username} not found in JSON storage")
                return False, "User not found in JSON storage"
            
            json_account = self.json_manager.accounts[username]
            
            # Check if already in database
            db_user = self.db_manager.get_user_by_username(username)
            
            if db_user:
                # User already in database, just remove from JSON
                logger.info("Migration", f"User {username} already exists in database, removing JSON entry")
                success = self._remove_and_refresh_json(username)
                if success:
                    return True, f"User {username} already in database. Removed JSON entry and refreshed."
                else:
                    return False, f"User {username} in database but failed to remove JSON entry."
            
            # Migrate to database
            logger.info("Migration", f"Migrating user {username} from JSON to database")
            
            # Extract account data
            account_id = json_account.get('account_id')
            password_hash = json_account.get('password_hash')
            details = json_account.get('details', {})
            
            logger.debug("Migration", f"Extracted account data: id={account_id}, hash_length={len(password_hash) if password_hash else 0}")
            
            # Convert admin status from JSON format to database format
            is_admin = 1 if details.get('role') == 'admin' else 0
            
            # Create account in database with existing hash
            try:
                # Directly insert using password hash since we already have it
                self.db_manager.create_user_with_hash(
                    username=username,
                    password_hash=password_hash,
                    account_id=account_id,
                    is_admin=is_admin,
                    **{k: v for k, v in details.items() if k != 'role'}
                )
                logger.info("Migration", f"Successfully created {username} in database with is_admin={is_admin}")
            except Exception as e:
                logger.error("Migration", f"Failed to create user in database: {e}")
                return False, f"Database migration failed: {str(e)}"
            
            # Remove from JSON and refresh
            success = self._remove_and_refresh_json(username)
            
            if success:
                logger.info("Migration", f"Successfully migrated {username}: removed from JSON and refreshed")
                return True, f"User {username} successfully migrated from JSON to database and cleaned up"
            else:
                logger.error("Migration", f"Failed to clean up JSON for {username} after database migration")
                return False, f"User migrated to database but cleanup failed"
            
        except Exception as e:
            logger.error("Migration", f"Migration error for {username}: {e}")
            import traceback
            logger.debug("Migration", f"Migration error traceback: {traceback.format_exc()}")
            return False, f"Migration failed: {str(e)}"
    
    def _remove_from_json(self, username: str) -> bool:
        """
        Remove a user from JSON storage
        
        Args:
            username: Username to remove
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if username in self.json_manager.accounts:
                del self.json_manager.accounts[username]
                self.json_manager.save()
                logger.info("Migration", f"Removed {username} from JSON storage")
                return True
            logger.warning("Migration", f"User {username} not found in JSON storage for removal")
            return False
        except Exception as e:
            logger.error("Migration", f"Error removing {username} from JSON: {e}")
            return False
    
    def _remove_and_refresh_json(self, username: str) -> bool:
        """
        Remove a user from JSON storage and refresh the system's knowledge of the file.
        
        Steps:
        1. Delete the user entry from JSON
        2. Save the updated JSON file
        3. Reload JSON to confirm changes
        4. Verify user is gone
        
        Args:
            username: Username to remove
            
        Returns:
            True if successful removal and refresh, False otherwise
        """
        try:
            # Ensure we have current data
            self.json_manager.load()
            logger.debug("Migration", f"Reloaded JSON before removal of {username}")
            
            if username not in self.json_manager.accounts:
                logger.warning("Migration", f"User {username} not in JSON, skipping removal")
                return True  # User already gone
            
            # Delete the user
            del self.json_manager.accounts[username]
            logger.debug("Migration", f"Deleted {username} from accounts dict")
            
            # Save to file
            self.json_manager.save()
            logger.debug("Migration", f"Saved updated JSON file (removed {username})")
            
            # Reload from file to verify changes
            self.json_manager.load()
            logger.debug("Migration", f"Reloaded JSON file to verify removal")
            
            # Verify user is actually gone
            if username in self.json_manager.accounts:
                logger.error("Migration", f"Verification failed: {username} still in JSON after removal!")
                return False
            
            logger.info("Migration", f"Verified removal: {username} no longer in JSON storage")
            
            # Check and report file status
            import os
            if os.path.exists(ACCOUNT_DB):
                file_size = os.path.getsize(ACCOUNT_DB)
                logger.debug("Migration", f"JSON file size after cleanup: {file_size} bytes")
            
            return True
            
        except Exception as e:
            logger.error("Migration", f"Error removing and refreshing for {username}: {e}")
            import traceback
            logger.debug("Migration", f"Remove/refresh traceback: {traceback.format_exc()}")
            return False
    
    def verify_migration_cleanup(self, username: str) -> Tuple[bool, str]:
        """
        Verify that a user has been properly cleaned up after migration.
        
        Checks:
        1. User is no longer in JSON
        2. User exists in database
        3. User can be verified with password
        
        Args:
            username: Username to verify
            
        Returns:
            Tuple of (verified: bool, message: str)
        """
        try:
            # Reload to get current state
            self.json_manager.load()
            
            # Check 1: Not in JSON
            if username in self.json_manager.accounts:
                return False, f"Cleanup verification failed: {username} still in JSON storage"
            
            # Check 2: Is in database
            db_user = self.db_manager.get_user_by_username(username)
            if not db_user:
                return False, f"Cleanup verification failed: {username} not found in database"
            
            # Check 3: Has valid account
            if not db_user.get('password_hash'):
                return False, f"Cleanup verification failed: {username} in database but missing password hash"
            
            logger.info("Migration", f"Cleanup verification passed for {username}")
            return True, f"User {username} successfully migrated and cleaned up (verified)"
            
        except Exception as e:
            logger.error("Migration", f"Error verifying cleanup for {username}: {e}")
            return False, f"Verification failed: {str(e)}"
    
    def migrate_all_json_users(self) -> dict:
        """
        Migrate all users from JSON to database
        
        Returns:
            Dictionary with migration results for each user
        """
        self.json_manager.load()
        results = {}
        
        for username in list(self.json_manager.accounts.keys()):
            success, message = self.migrate_json_to_database(username)
            results[username] = {
                'success': success,
                'message': message
            }
            logger.info("Migration", f"Migration result for {username}: {message}")
        
        return results
    
    def get_migration_status(self) -> dict:
        """
        Get current migration status
        
        Returns:
            Dictionary with migration stats
        """
        self.json_manager.load()
        db_stats = self.db_manager.get_stats()
        
        json_users = list(self.json_manager.accounts.keys())
        db_users = [u['username'] for u in self.db_manager.list_users()]
        
        # Find users in both
        in_both = set(json_users) & set(db_users)
        # Find users only in JSON
        json_only = set(json_users) - set(db_users)
        # Find users only in database
        db_only = set(db_users) - set(json_users)
        
        return {
            'json_total': len(json_users),
            'database_total': len(db_users),
            'in_both': list(in_both),
            'json_only': list(json_only),
            'database_only': list(db_only),
            'needs_migration': len(json_only)
        }


def auto_migrate_on_login(username: str) -> bool:
    """
    Convenience function to automatically migrate a user on successful login.
    
    This function:
    1. Detects where the user's credentials came from
    2. If in JSON: Migrates to database and cleans up JSON
    3. Reloads the unified account manager to recognize the change
    
    Args:
        username: Username that just logged in successfully
        
    Returns:
        True if migration was successful, False otherwise
    """
    try:
        migration = AccountMigration()
        source = migration.detect_login_source(username)
        
        if source == 'json':
            logger.info("Migration", f"User {username} logged in via JSON storage, initiating migration")
            success, message = migration.migrate_json_to_database(username)
            
            if success:
                # Refresh the unified account manager if it exists
                try:
                    # Force reload of unified manager to recognize database backend
                    from .account_unified import get_account_manager
                    manager = get_account_manager()
                    if hasattr(manager, 'load'):
                        manager.load()  # Reload JSON in case still using JSON backend
                    logger.info("Migration", f"Refreshed unified account manager for {username}")
                except Exception as e:
                    logger.debug("Migration", f"Could not refresh unified manager: {e}")
                
                logger.info("Migration", f"Auto-migration successful: {message}")
                return True
            else:
                logger.warning("Migration", f"Auto-migration failed: {message}")
                return False
        
        elif source == 'database':
            logger.debug("Migration", f"User {username} logged in via database, no migration needed")
            return True
        
        else:
            logger.warning("Migration", f"Could not determine login source for {username}")
            return False
            
    except Exception as e:
        logger.error("Migration", f"Error during auto-migration for {username}: {e}")
        import traceback
        logger.debug("Migration", f"Auto-migration error traceback: {traceback.format_exc()}")
        return False
