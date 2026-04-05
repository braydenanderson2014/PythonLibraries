"""
Rent API Authentication & Session Management
Handles user authentication and session tokens for the REST API
"""

import json
import time
import uuid
import hmac
import hashlib
import base64
import struct
import secrets
import urllib.parse
from typing import Optional, Dict, Any
from assets.Logger import Logger

logger = Logger()


def generate_totp_secret(length: int = 20) -> str:
    """Generate a base32 TOTP secret suitable for authenticator apps."""
    raw = secrets.token_bytes(length)
    return base64.b32encode(raw).decode('utf-8').rstrip('=')


def _normalize_base32_secret(secret: str) -> bytes:
    padded = secret.strip().replace(' ', '').upper()
    padding = '=' * ((8 - len(padded) % 8) % 8)
    return base64.b32decode(padded + padding, casefold=True)


def get_totp_code(secret: str, for_time: Optional[int] = None, step: int = 30, digits: int = 6) -> str:
    """Generate TOTP code for a given secret and timestamp."""
    if for_time is None:
        for_time = int(time.time())

    key = _normalize_base32_secret(secret)
    counter = int(for_time // step)
    msg = struct.pack('>Q', counter)
    digest = hmac.new(key, msg, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code = (struct.unpack('>I', digest[offset:offset + 4])[0] & 0x7FFFFFFF) % (10 ** digits)
    return str(code).zfill(digits)


def verify_totp_code(secret: str, code: str, window: int = 1) -> bool:
    """Verify a TOTP code with small clock-skew tolerance."""
    now = int(time.time())
    candidate = str(code).strip()
    if not candidate.isdigit():
        return False

    for offset in range(-window, window + 1):
        if get_totp_code(secret, for_time=now + (offset * 30)) == candidate:
            return True
    return False


def build_totp_uri(secret: str, username: str, issuer: str = 'Financial Manager') -> str:
    """Build an otpauth URI for authenticator app provisioning."""
    safe_issuer = issuer.strip() or 'Financial Manager'
    safe_username = username.strip() or 'user'
    label = urllib.parse.quote(f"{safe_issuer}:{safe_username}")
    query = urllib.parse.urlencode({
        'secret': secret,
        'issuer': safe_issuer,
        'algorithm': 'SHA1',
        'digits': 6,
        'period': 30
    })
    return f"otpauth://totp/{label}?{query}"


def build_totp_qr_url(otpauth_uri: str, size: int = 220) -> str:
    """Build a hosted QR image URL for an otpauth URI."""
    encoded = urllib.parse.quote(otpauth_uri, safe='')
    return f"https://api.qrserver.com/v1/create-qr-code/?size={size}x{size}&data={encoded}"

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
    
    def create_session(
        self,
        user_id: str,
        username: str,
        is_api_only: bool = False,
        is_admin: bool = False,
        is_tenant: bool = False
    ) -> Dict[str, Any]:
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
            'is_admin': is_admin,
            'is_tenant': is_tenant,
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
                    'is_admin': session.get('is_admin', False),
                    'is_tenant': session.get('is_tenant', False),
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
        self.pending_2fa = {}

    def _create_2fa_challenge(self, user_id: str, username: str, is_api_only: bool, is_admin: bool, is_tenant: bool) -> Dict[str, Any]:
        """Create a short-lived 2FA challenge for second-step verification."""
        challenge_id = str(uuid.uuid4())
        self.pending_2fa[challenge_id] = {
            'challenge_id': challenge_id,
            'user_id': user_id,
            'username': username,
            'is_api_only': is_api_only,
            'is_admin': is_admin,
            'is_tenant': is_tenant,
            'created_at': time.time(),
            'expires_in_seconds': 300
        }
        return self.pending_2fa[challenge_id]

    def verify_2fa_and_create_session(self, challenge_id: str, code: str) -> Dict[str, Any]:
        """Verify 2FA challenge and issue API session token."""
        challenge = self.pending_2fa.get(challenge_id)
        if not challenge:
            return {
                'success': False,
                'error': 'Invalid or expired 2FA challenge'
            }

        if time.time() - challenge['created_at'] > challenge['expires_in_seconds']:
            self.pending_2fa.pop(challenge_id, None)
            return {
                'success': False,
                'error': '2FA challenge expired'
            }

        account = self.account_manager.get_account(challenge['username'])
        if not account:
            self.pending_2fa.pop(challenge_id, None)
            return {
                'success': False,
                'error': 'Account not found'
            }

        details = account.get('details') or {}
        secret = details.get('two_factor_secret')
        if not secret:
            return {
                'success': False,
                'error': '2FA secret is not configured for this account'
            }

        if not verify_totp_code(secret, code):
            logger.warning("RentAPIAuthenticator", f"Invalid 2FA code for user: {challenge['username']}")
            return {
                'success': False,
                'error': 'Invalid 2FA code'
            }

        session = self.session_manager.create_session(
            challenge['user_id'],
            challenge['username'],
            is_api_only=challenge['is_api_only'],
            is_admin=challenge['is_admin'],
            is_tenant=challenge['is_tenant']
        )

        self.pending_2fa.pop(challenge_id, None)
        logger.info("RentAPIAuthenticator", f"2FA verified and session created for user: {challenge['username']}")
        return {
            'success': True,
            'token': session['token'],
            'user_id': challenge['user_id'],
            'username': challenge['username'],
            'is_admin': challenge['is_admin'],
            'is_tenant': challenge['is_tenant'],
            'session_expires_in_seconds': self.session_manager.timeout_seconds
        }
    
    def authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
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
            return {
                'success': False,
                'error': 'Invalid username or password'
            }
        
        # Get account details
        account = self.account_manager.get_account(username)
        if not account:
            logger.error("RentAPIAuthenticator", f"Account not found after password verification: {username}")
            return {
                'success': False,
                'error': 'Account not found'
            }
        
        # Check account access privileges
        details = account.get('details') or {}
        if not isinstance(details, dict):
            details = {}
        # New model: explicit online/desktop access toggles.
        # Backward compatibility: existing api_only accounts still work.
        has_online_access = details.get('online_access', None)
        has_desktop_access = details.get('desktop_access', None)
        is_api_only = bool(details.get('api_only', False))

        if has_online_access is None and has_desktop_access is None:
            # Legacy behavior when no explicit privilege flags exist.
            has_online_access = is_api_only
            has_desktop_access = not is_api_only
        else:
            has_online_access = bool(has_online_access)
            has_desktop_access = bool(has_desktop_access)
        
        # If online access is disabled, reject API login.
        if not has_online_access:
            logger.warning("RentAPIAuthenticator", f"User without online access attempted API login: {username}")
            return {
                'success': False,
                'error': 'This account is not enabled for online/API access. Enable Online/API access in User Management.',
                'online_access_required': True
            }
        
        role = details.get('role', 'user')
        is_admin = role == 'admin'
        is_tenant = bool(details.get('tenant_account', False) or role == 'tenant')

        if details.get('setup_pending'):
            return {
                'success': False,
                'error': 'Account setup is not complete. Use the setup link to finish creating your password.'
            }

        if details.get('two_factor_enabled'):
            challenge = self._create_2fa_challenge(
                account['account_id'],
                username,
                is_api_only=not has_desktop_access,
                is_admin=is_admin,
                is_tenant=is_tenant
            )
            return {
                'success': True,
                'two_factor_required': True,
                'challenge_id': challenge['challenge_id'],
                'username': username,
                'message': 'Two-factor authentication code required',
                'challenge_expires_in_seconds': challenge['expires_in_seconds']
            }

        # Create session
        user_id = account['account_id']
        session = self.session_manager.create_session(
            user_id,
            username,
            is_api_only=not has_desktop_access,
            is_admin=is_admin,
            is_tenant=is_tenant
        )
        
        logger.info("RentAPIAuthenticator", f"User authenticated: {username}")
        return {
            'success': True,
            'token': session['token'],
            'user_id': user_id,
            'username': username,
            'is_admin': is_admin,
            'is_tenant': is_tenant,
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
            online_access=True,
            desktop_access=False,
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
