"""
Rent API Authentication & Session Management
Handles user authentication and session tokens for the REST API
"""

import json
import time
import uuid
from typing import Optional, Dict, Any
from assets.Logger import Logger

logger = Logger()

class SessionManager:
    """Manages API session tokens and authentication"""
    
    def __init__(self, timeout_seconds=3600):
        """
        Initialize session manager
        
        Args:
            timeout_seconds: Session timeout in seconds (default: 1 hour)
        """
        self.sessions = {}  # token -> session_data
        self.timeout_seconds = timeout_seconds
    
    def create_session(self, user_id: str, username: str, is_api_only: bool = False) -> Dict[str, Any]:
        """
        Create a new authentication session
        
        Args:
            user_id: User account ID
            username: Username
            is_api_only: Whether this is an API-only user (can't access desktop app)
        
        Returns:
            Session data with token
        """
        token = str(uuid.uuid4())
        session = {
            'token': token,
            'user_id': user_id,
            'username': username,
            'is_api_only': is_api_only,
            'created_at': time.time(),
            'last_accessed': time.time()
        }
        self.sessions[token] = session
        logger.info("SessionManager", f"Created session for user: {username} (token: {token[:8]}...)")
        return session
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify an authentication token is valid
        
        Args:
            token: Session token to verify
        
        Returns:
            Session data if valid, None if invalid or expired
        """
        if token not in self.sessions:
            logger.warning("SessionManager", f"Invalid token: {token[:8]}...")
            return None
        
        session = self.sessions[token]
        elapsed = time.time() - session['created_at']
        
        if elapsed > self.timeout_seconds:
            logger.warning("SessionManager", f"Session expired for user: {session['username']}")
            del self.sessions[token]
            return None
        
        # Update last accessed time
        session['last_accessed'] = time.time()
        return session
    
    def revoke_token(self, token: str) -> bool:
        """Revoke a session token"""
        if token in self.sessions:
            username = self.sessions[token]['username']
            del self.sessions[token]
            logger.info("SessionManager", f"Revoked session for user: {username}")
            return True
        return False
    
    def get_active_sessions(self) -> Dict[str, Any]:
        """Get all active sessions (admin info only)"""
        active = {}
        current_time = time.time()
        
        for token, session in list(self.sessions.items()):
            elapsed = current_time - session['created_at']
            if elapsed <= self.timeout_seconds:
                active[token] = {
                    'username': session['username'],
                    'user_id': session['user_id'],
                    'is_api_only': session['is_api_only'],
                    'duration_seconds': int(elapsed)
                }
        
        return active


class RentAPIAuthenticator:
    """Authenticates users for the Rent Management API"""
    
    def __init__(self, account_manager, session_manager: SessionManager):
        """
        Initialize authenticator
        
        Args:
            account_manager: AccountManager instance
            session_manager: SessionManager instance
        """
        self.account_manager = account_manager
        self.session_manager = session_manager
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate a user and create a session
        
        Args:
            username: Username
            password: Password (plaintext)
        
        Returns:
            Session data with token if successful, None if failed
        """
        # Verify username and password
        if not self.account_manager.verify_password(username, password):
            logger.warning("RentAPIAuthenticator", f"Authentication failed for user: {username}")
            return None
        
        # Get account details
        account = self.account_manager.get_account(username)
        if not account:
            logger.error("RentAPIAuthenticator", f"Account not found after password verification: {username}")
            return None
        
        # Check if this is an API-only account
        details = account.get('details', {})
        is_api_only = details.get('api_only', False)
        
        # If not API-only, reject from API login
        # (they should use desktop app instead)
        if not is_api_only:
            logger.warning("RentAPIAuthenticator", f"Non-API user attempted API login: {username}")
            return {
                'success': False,
                'error': 'This account is not enabled for API access. Please use the desktop application.',
                'api_only_required': True
            }
        
        # Create session
        user_id = account['account_id']
        session = self.session_manager.create_session(user_id, username, is_api_only=True)
        
        logger.info("RentAPIAuthenticator", f"User authenticated: {username}")
        return {
            'success': True,
            'token': session['token'],
            'user_id': user_id,
            'username': username,
            'session_expires_in_seconds': self.session_manager.timeout_seconds
        }
    
    def verify_session(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify a session token
        
        Args:
            token: Session token
        
        Returns:
            Session data if valid, None if invalid
        """
        return self.session_manager.verify_token(token)


def create_api_only_user(account_manager, username: str, password: str, role: str = 'api_user') -> Dict[str, Any]:
    """
    Create an API-only user account (cannot access desktop app)
    
    Args:
        account_manager: AccountManager instance
        username: Username for API access
        password: Password (plaintext)
        role: User role (default: 'api_user')
    
    Returns:
        Created account data
    """
    try:
        account = account_manager.create_account(
            username, 
            password,
            role=role,
            api_only=True,
            description=f"API-only account for remote access"
        )
        logger.info("RentAPIAuth", f"Created API-only account: {username}")
        return {
            'success': True,
            'account': account,
            'message': f"API user '{username}' created successfully"
        }
    except ValueError as e:
        logger.error("RentAPIAuth", f"Failed to create API user: {e}")
        return {
            'success': False,
            'error': str(e)
        }
