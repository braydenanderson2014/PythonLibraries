"""
Account Database Manager for Financial Manager
Handles user accounts with SQLite database backend
"""

import sqlite3
from assets.Logger import Logger
from typing import Optional, Dict, Any, List
from datetime import datetime
import os

try:
    from .app_paths import get_resource_path
    from .hasher import hash_password, verify_hash
except ImportError:
    from app_paths import get_resource_path
    from hasher import hash_password, verify_hash

logger = Logger()


class AccountDatabaseManager:
    """
    Manages user accounts in SQLite database.
    Provides CRUD operations for user authentication and profile management.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize account database manager
        
        Args:
            db_path: Path to database file. If None, uses default from app_paths
        """
        if db_path is None:
            self.db_path = get_resource_path("accounts.db")
        else:
            self.db_path = db_path
        
        self._init_database()
        logger.info("Account DB", f"Account database initialized: {self.db_path}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    
    def _init_database(self):
        """Initialize database schema"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id TEXT UNIQUE NOT NULL,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    email TEXT,
                    full_name TEXT,
                    phone TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active INTEGER DEFAULT 1,
                    is_admin INTEGER DEFAULT 0,
                    profile_picture TEXT,
                    theme_preference TEXT DEFAULT 'light',
                    currency TEXT DEFAULT 'USD',
                    timezone TEXT DEFAULT 'UTC',
                    language TEXT DEFAULT 'en',
                    details TEXT
                )
            """)
            
            # Create indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_username 
                ON users(username)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_account_id 
                ON users(account_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_email 
                ON users(email)
            """)
            
            conn.commit()
            logger.info("Account DB", "Account database schema initialized")
            
        except Exception as e:
            conn.rollback()
            logger.error("Account DB", f"Error initializing database: {e}")
            raise
        finally:
            conn.close()
    
    def create_user(self, username: str, password: str, account_id: str, **details) -> Dict[str, Any]:
        """
        Create a new user account
        
        Args:
            username: Username (must be unique)
            password: Plain text password (will be hashed)
            account_id: Unique account ID
            **details: Additional user details (email, full_name, phone, etc.)
            
        Returns:
            Dictionary with user data
            
        Raises:
            ValueError: If username already exists
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Check if username exists
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                raise ValueError(f"Username '{username}' already exists")
            
            # Check if account_id exists
            cursor.execute("SELECT id FROM users WHERE account_id = ?", (account_id,))
            if cursor.fetchone():
                raise ValueError(f"Account ID '{account_id}' already exists")
            
            # Hash password
            password_hash = hash_password(password)
            
            # Extract known fields
            email = details.get('email')
            full_name = details.get('full_name')
            phone = details.get('phone')
            # Handle both 'is_admin' and 'role' parameters (role='admin' -> is_admin=1)
            is_admin = details.get('is_admin', 0)
            if isinstance(is_admin, str):
                is_admin = 1 if is_admin.lower() == 'admin' else 0
            if 'role' in details and not details.get('is_admin'):
                role = details.get('role', 'user')
                is_admin = 1 if role == 'admin' else 0
            
            theme_preference = details.get('theme_preference', 'light')
            currency = details.get('currency', 'USD')
            timezone = details.get('timezone', 'UTC')
            language = details.get('language', 'en')
            
            # Store remaining details as JSON
            import json
            remaining_details = {k: v for k, v in details.items() 
                               if k not in ['email', 'full_name', 'phone', 'is_admin', 'role',
                                          'theme_preference', 'currency', 'timezone', 'language']}
            details_json = json.dumps(remaining_details) if remaining_details else None
            
            # Insert user
            cursor.execute("""
                INSERT INTO users (
                    account_id, username, password_hash, email, full_name, phone,
                    is_admin, theme_preference, currency, timezone, language, details
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (account_id, username, password_hash, email, full_name, phone,
                  is_admin, theme_preference, currency, timezone, language, details_json))
            
            user_id = cursor.lastrowid
            conn.commit()
            
            logger.info("Account DB", f"User created: {username} (ID: {user_id})")
            
            # Return user data
            return self.get_user_by_username(username)
            
        except Exception as e:
            conn.rollback()
            logger.error("Account DB", f"Error creating user: {e}")
            raise
        finally:
            conn.close()
    
    def create_user_with_hash(self, username: str, password_hash: str, account_id: str, **details) -> Dict[str, Any]:
        """
        Create a new user account with an existing password hash.
        Used for migrating users from JSON storage to database.
        
        Args:
            username: Username (must be unique)
            password_hash: Pre-hashed password (from JSON storage)
            account_id: Unique account ID
            **details: Additional user details (email, full_name, phone, etc.)
            
        Returns:
            Dictionary with user data
            
        Raises:
            ValueError: If username already exists
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Check if username exists
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                raise ValueError(f"Username '{username}' already exists")
            
            # Check if account_id exists
            cursor.execute("SELECT id FROM users WHERE account_id = ?", (account_id,))
            if cursor.fetchone():
                raise ValueError(f"Account ID '{account_id}' already exists")
            
            # Extract known fields
            email = details.get('email')
            full_name = details.get('full_name')
            phone = details.get('phone')
            # Handle both 'is_admin' and 'role' parameters (role='admin' -> is_admin=1)
            is_admin = details.get('is_admin', 0)
            if isinstance(is_admin, str):
                is_admin = 1 if is_admin.lower() == 'admin' else 0
            if 'role' in details and not details.get('is_admin'):
                role = details.get('role', 'user')
                is_admin = 1 if role == 'admin' else 0
            
            theme_preference = details.get('theme_preference', 'light')
            currency = details.get('currency', 'USD')
            timezone = details.get('timezone', 'UTC')
            language = details.get('language', 'en')
            
            # Store remaining details as JSON
            import json
            remaining_details = {k: v for k, v in details.items() 
                               if k not in ['email', 'full_name', 'phone', 'is_admin', 'role',
                                          'theme_preference', 'currency', 'timezone', 'language']}
            details_json = json.dumps(remaining_details) if remaining_details else None
            
            # Insert user with existing password hash
            cursor.execute("""
                INSERT INTO users (
                    account_id, username, password_hash, email, full_name, phone,
                    is_admin, theme_preference, currency, timezone, language, details
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (account_id, username, password_hash, email, full_name, phone,
                  is_admin, theme_preference, currency, timezone, language, details_json))
            
            user_id = cursor.lastrowid
            conn.commit()
            
            logger.info("Account DB", f"User created from hash: {username} (ID: {user_id})")
            
            # Return user data
            return self.get_user_by_username(username)
            
        except Exception as e:
            conn.rollback()
            logger.error("Account DB", f"Error creating user with hash: {e}")
            raise
        finally:
            conn.close()
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get user by username
        
        Args:
            username: Username to search for
            
        Returns:
            User dictionary or None if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            
            if row:
                user = dict(row)
                # Parse details JSON
                if user.get('details'):
                    import json
                    user['details'] = json.loads(user['details'])
                else:
                    user['details'] = {}
                return user
            return None
            
        finally:
            conn.close()
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user by ID
        
        Args:
            user_id: User ID to search for
            
        Returns:
            User dictionary or None if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            
            if row:
                user = dict(row)
                # Parse details JSON
                if user.get('details'):
                    import json
                    user['details'] = json.loads(user['details'])
                else:
                    user['details'] = {}
                return user
            return None
            
        finally:
            conn.close()
    
    def get_user_by_account_id(self, account_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user by account ID
        
        Args:
            account_id: Account ID to search for
            
        Returns:
            User dictionary or None if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM users WHERE account_id = ?", (account_id,))
            row = cursor.fetchone()
            
            if row:
                user = dict(row)
                # Parse details JSON
                if user.get('details'):
                    import json
                    user['details'] = json.loads(user['details'])
                else:
                    user['details'] = {}
                return user
            return None
            
        finally:
            conn.close()
    
    def verify_password(self, username: str, password: str) -> bool:
        """
        Verify user password
        
        Args:
            username: Username
            password: Plain text password to verify
            
        Returns:
            True if password matches, False otherwise
        """
        user = self.get_user_by_username(username)
        if not user:
            return False
        
        stored_hash = user.get('password_hash', '')
        return verify_hash(stored_hash, password)
    
    def update_user(self, username: str, **updates) -> bool:
        """
        Update user account
        
        Args:
            username: Username of user to update
            **updates: Fields to update
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If user not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Check user exists
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            if not user:
                raise ValueError(f"User '{username}' not found")
            
            # Handle 'role' parameter conversion to is_admin
            if 'role' in updates:
                role = updates.pop('role')
                if not updates.get('is_admin'):
                    updates['is_admin'] = 1 if role == 'admin' else 0
            
            # Build update query
            update_fields = []
            params = []
            
            # Known fields
            known_fields = ['email', 'full_name', 'phone', 'is_active', 'is_admin',
                          'profile_picture', 'theme_preference', 'currency', 'timezone', 'language']
            
            for field in known_fields:
                if field in updates:
                    update_fields.append(f"{field} = ?")
                    params.append(updates[field])
            
            # Handle details separately
            if any(k not in known_fields for k in updates.keys()):
                # Get existing details
                user_data = self.get_user_by_username(username)
                existing_details = user_data.get('details', {})
                
                # Merge new details
                for key, value in updates.items():
                    if key not in known_fields:
                        existing_details[key] = value
                
                import json
                update_fields.append("details = ?")
                params.append(json.dumps(existing_details))
            
            # Add updated_at
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            
            if update_fields:
                params.append(username)
                query = f"UPDATE users SET {', '.join(update_fields)} WHERE username = ?"
                cursor.execute(query, params)
                conn.commit()
                
                logger.info("Account DB", f"User updated: {username}")
                return True
            
            return False
            
        except Exception as e:
            conn.rollback()
            logger.error("Account DB", f"Error updating user: {e}")
            raise
        finally:
            conn.close()
    
    def change_password(self, username: str, new_password: str) -> bool:
        """
        Change user password
        
        Args:
            username: Username
            new_password: New plain text password (will be hashed)
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If user not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Check user exists
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if not cursor.fetchone():
                raise ValueError(f"User '{username}' not found")
            
            # Hash new password
            password_hash = hash_password(new_password)
            
            # Update password
            cursor.execute("""
                UPDATE users 
                SET password_hash = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE username = ?
            """, (password_hash, username))
            
            conn.commit()
            logger.info("Account DB", f"Password changed for user: {username}")
            return True
            
        except Exception as e:
            conn.rollback()
            logger.error("Account DB", f"Error changing password: {e}")
            raise
        finally:
            conn.close()
    
    def update_last_login(self, username: str) -> bool:
        """
        Update last login timestamp
        
        Args:
            username: Username
            
        Returns:
            True if successful
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE users 
                SET last_login = CURRENT_TIMESTAMP 
                WHERE username = ?
            """, (username,))
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error("Account DB", f"Error updating last login: {e}")
            return False
        finally:
            conn.close()
    
    def delete_user(self, username: str) -> bool:
        """
        Delete user account
        
        Args:
            username: Username to delete
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If user not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if not cursor.fetchone():
                raise ValueError(f"User '{username}' not found")
            
            cursor.execute("DELETE FROM users WHERE username = ?", (username,))
            conn.commit()
            
            logger.info("Account DB", f"User deleted: {username}")
            return True
            
        except Exception as e:
            conn.rollback()
            logger.error("Account DB", f"Error deleting user: {e}")
            raise
        finally:
            conn.close()
    
    def list_users(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """
        List all users
        
        Args:
            active_only: If True, only return active users
            
        Returns:
            List of user dictionaries
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            if active_only:
                cursor.execute("SELECT * FROM users WHERE is_active = 1 ORDER BY username")
            else:
                cursor.execute("SELECT * FROM users ORDER BY username")
            
            rows = cursor.fetchall()
            users = []
            
            for row in rows:
                user = dict(row)
                # Parse details JSON
                if user.get('details'):
                    import json
                    user['details'] = json.loads(user['details'])
                else:
                    user['details'] = {}
                users.append(user)
            
            return users
            
        finally:
            conn.close()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get database statistics
        
        Returns:
            Dictionary with statistics
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            stats = {}
            
            # Total users
            cursor.execute("SELECT COUNT(*) as count FROM users")
            stats['total_users'] = cursor.fetchone()['count']
            
            # Active users
            cursor.execute("SELECT COUNT(*) as count FROM users WHERE is_active = 1")
            stats['active_users'] = cursor.fetchone()['count']
            
            # Admin users
            cursor.execute("SELECT COUNT(*) as count FROM users WHERE is_admin = 1")
            stats['admin_users'] = cursor.fetchone()['count']
            
            # Recent logins (last 30 days)
            cursor.execute("""
                SELECT COUNT(*) as count FROM users 
                WHERE last_login >= datetime('now', '-30 days')
            """)
            stats['recent_logins'] = cursor.fetchone()['count']
            
            # Database size
            stats['db_size'] = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            stats['db_path'] = self.db_path
            
            return stats
            
        finally:
            conn.close()
