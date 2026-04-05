"""
Rent Management Web Server with Authentication
REST API for rent management with user authentication.
Only loads RentTracker AFTER successful user login.
"""

import sys
import os
import time
import secrets

# Setup paths - add root first so assets can be found
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, root_path)
sys.path.insert(0, os.path.join(root_path, 'src'))
sys.path.insert(0, os.path.join(root_path, 'ui'))

# Now import after paths are set
from src.account import AccountManager, generate_account_id
from src.account_db import AccountDatabaseManager
from src.rent_tracker import RentTracker
from src.rent_web_server import create_server
from src.rent_api_auth import create_api_only_user
from assets.Logger import Logger

logger = Logger()


class UnifiedApiAccountManager:
    """Account provider for API auth: database first, JSON fallback."""

    def __init__(self):
        self.db_manager = AccountDatabaseManager()
        self.json_manager = AccountManager()

    @staticmethod
    def _normalize_db_account(db_user):
        if not db_user:
            return None
        details = db_user.get('details') or {}
        if not isinstance(details, dict):
            details = {}

        normalized_details = dict(details)
        if 'role' not in normalized_details:
            normalized_details['role'] = 'admin' if db_user.get('is_admin') == 1 else 'user'

        return {
            'account_id': db_user.get('account_id'),
            'username': db_user.get('username'),
            'details': normalized_details
        }

    def get_account(self, username):
        db_user = self.db_manager.get_user_by_username(username)
        if db_user:
            return self._normalize_db_account(db_user)

        return self.json_manager.get_account(username)

    def verify_password(self, username, password):
        db_user = self.db_manager.get_user_by_username(username)
        if db_user:
            ok = self.db_manager.verify_password(username, password)
            if ok:
                self.db_manager.update_last_login(username)
            return ok

        return self.json_manager.verify_password(username, password)

    def create_account(self, username, password, **details):
        # Keep both stores in sync for compatibility during transition.
        account = None
        db_user = self.db_manager.get_user_by_username(username)

        if db_user:
            raise ValueError('Username already exists')

        json_user = self.json_manager.get_account(username)
        if json_user:
            raise ValueError('Username already exists')

        account_id = generate_account_id()
        self.db_manager.create_user(username, password, account_id, **details)

        # JSON creation is best-effort to preserve compatibility.
        try:
            account = self.json_manager.create_account(username, password, **details)
            account['account_id'] = account_id
            self.json_manager.accounts[username]['account_id'] = account_id
            self.json_manager.save()
        except Exception as e:
            logger.warning("RentWebServer", f"JSON mirror create failed for user {username}: {e}")

        if account:
            return account

        db_created = self.db_manager.get_user_by_username(username)
        return self._normalize_db_account(db_created)

    def create_pending_account(self, username, email=None, full_name=None, phone=None, **details):
        """Create account without a user-chosen password; setup completed via tokenized link."""
        setup_token = secrets.token_urlsafe(32)
        setup_expires_at = int(time.time()) + (7 * 24 * 60 * 60)
        temporary_password = secrets.token_urlsafe(18)

        payload = dict(details)
        payload.update({
            'email': email,
            'full_name': full_name,
            'phone': phone,
            'setup_pending': True,
            'setup_token': setup_token,
            'setup_expires_at': setup_expires_at,
            'setup_created_at': int(time.time())
        })

        account = self.create_account(username, temporary_password, **payload)
        return {
            'account': account,
            'setup_token': setup_token,
            'setup_expires_at': setup_expires_at
        }

    def _find_account_by_setup_token(self, setup_token):
        # Database first
        try:
            users = self.db_manager.list_users(active_only=False)
            for user in users:
                details = user.get('details') or {}
                if details.get('setup_token') == setup_token:
                    return {
                        'backend': 'database',
                        'username': user.get('username'),
                        'account': self._normalize_db_account(user),
                        'raw': user
                    }
        except Exception as e:
            logger.warning("RentWebServer", f"Setup token DB lookup failed: {e}")

        # JSON fallback
        for username, account in self.json_manager.accounts.items():
            details = account.get('details') or {}
            if details.get('setup_token') == setup_token:
                return {
                    'backend': 'json',
                    'username': username,
                    'account': account,
                    'raw': account
                }

        return None

    def get_setup_info(self, setup_token):
        record = self._find_account_by_setup_token(setup_token)
        if not record:
            return {'success': False, 'error': 'Invalid setup token'}

        details = (record['account'] or {}).get('details') or {}
        if not details.get('setup_pending', False):
            return {
                'success': False,
                'error': 'Setup link already used. Request a new setup link from admin.'
            }

        expires_at = int(details.get('setup_expires_at', 0) or 0)
        if expires_at and int(time.time()) > expires_at:
            return {'success': False, 'error': 'Setup token has expired'}

        return {
            'success': True,
            'username': record['account'].get('username'),
            'email': details.get('email', ''),
            'full_name': details.get('full_name', ''),
            'phone': details.get('phone', ''),
            'online_access': bool(details.get('online_access', False)),
            'tenant_account': bool(details.get('tenant_account', details.get('role') == 'tenant')),
            'setup_expires_at': expires_at
        }

    def complete_setup(self, setup_token, password, enable_two_factor=False):
        record = self._find_account_by_setup_token(setup_token)
        if not record:
            return {'success': False, 'error': 'Invalid setup token'}

        account = record['account'] or {}
        details = account.get('details') or {}
        expires_at = int(details.get('setup_expires_at', 0) or 0)
        if expires_at and int(time.time()) > expires_at:
            return {'success': False, 'error': 'Setup token has expired'}

        username = account.get('username')
        if not username:
            return {'success': False, 'error': 'Account data is invalid'}

        if not details.get('setup_pending', False):
            return {
                'success': False,
                'error': 'Setup link already used. Request a new setup link from admin.'
            }

        updated_details = dict(details)
        updated_details['setup_pending'] = False
        updated_details.pop('setup_token', None)
        updated_details.pop('setup_expires_at', None)
        updated_details.pop('setup_created_at', None)

        two_factor_secret = None
        two_factor_uri = None
        two_factor_qr_url = None

        if enable_two_factor:
            from src.rent_api_auth import generate_totp_secret, build_totp_uri, build_totp_qr_url
            updated_details['two_factor_enabled'] = True
            two_factor_secret = generate_totp_secret()
            updated_details['two_factor_secret'] = two_factor_secret
            two_factor_uri = build_totp_uri(two_factor_secret, username)
            two_factor_qr_url = build_totp_qr_url(two_factor_uri)
        else:
            updated_details['two_factor_enabled'] = False
            updated_details.pop('two_factor_secret', None)

        # Consume setup token and synchronize across both backends to prevent token reuse.
        db_user = self.db_manager.get_user_by_username(username)
        if db_user:
            self.db_manager.change_password(username, password)
            self.db_manager.set_user_details(username, updated_details)

        json_user = self.json_manager.get_account(username)
        if json_user:
            self.json_manager.change_password(username, password)
            self.json_manager.accounts[username]['details'] = updated_details
            self.json_manager.save()

        refreshed = self.get_account(username)
        response = {
            'success': True,
            'username': username,
            'account': refreshed
        }
        if updated_details.get('two_factor_enabled'):
            response['two_factor_secret'] = two_factor_secret
            response['two_factor_uri'] = two_factor_uri
            response['two_factor_qr_url'] = two_factor_qr_url
        return response


def run_rent_web_server(port=5000, debug=False):
    """
    Run the rent management web server with authentication
    
    The server does NOT load RentTracker on startup. Instead:
    1. Users login with API-only credentials
    2. RentTracker is initialized per authenticated session
    3. Desktop app users cannot access the API
    
    Args:
        port: Port to run server on (default: 5000)
        debug: Enable debug mode (default: False)
    
    Example:
        from src.rent_web_server_runner import run_rent_web_server
        import threading
        
        server_thread = threading.Thread(
            target=run_rent_web_server,
            args=(5000, False),
            daemon=True
        )
        server_thread.start()
    """
    try:
        # Load unified account manager (DB-first, JSON fallback) for authentication
        logger.info("RentWebServer", "Loading unified account manager for authentication...")
        account_manager = UnifiedApiAccountManager()
        logger.info("RentWebServer", "Unified account manager loaded successfully")
        
        # Create and run server (WITHOUT rent_tracker - it will be loaded on login)
        logger.info("RentWebServer", f"Starting Rent Management Web Server on port {port}")
        logger.info("RentWebServer", "Authentication required - RentTracker loaded per session")
        
        server = create_server(
            account_manager=account_manager,
            rent_tracker=None,  # Don't load RentTracker yet
            host='0.0.0.0',
            port=port,
            debug=debug
        )
        
        server.run()
        
    except Exception as e:
        logger.error("RentWebServer", f"Failed to start rent web server: {e}")
        import traceback
        traceback.print_exc()
        raise


def get_server_instance(account_manager, port=5000):
    """
    Get server instance without running it
    
    Args:
        account_manager: AccountManager for authentication
        port: Port for server
    
    Returns:
        RentManagementServer instance (no RentTracker until auth)
    """
    return create_server(
        account_manager=account_manager,
        rent_tracker=None,
        host='0.0.0.0',
        port=port,
        debug=False
    )


def create_api_user(username: str, password: str) -> dict:
    """
    Helper to create an API-only user account
    
    Args:
        username: Username
        password: Password
    
    Returns:
        Result dict with success status
    
    Example:
        result = create_api_user('api_user_1', 'securepassword')
        if result['success']:
            print(f"Created: {result['account']['account_id']}")
    """
    try:
        account_manager = UnifiedApiAccountManager()
        return create_api_only_user(account_manager, username, password)
    except Exception as e:
        logger.error("RentWebServer", f"Failed to create API user: {e}")
        return {
            'success': False,
            'error': str(e)
        }


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Rent Management Web Server')
    parser.add_argument('--port', type=int, default=5000, help='Port to run server on')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--create-user', help='Create an API-only user (format: username:password)')
    
    args = parser.parse_args()
    
    try:
        # If creating a user, do that instead
        if args.create_user:
            if ':' not in args.create_user:
                logger.error("RentWebServer", "Invalid format. Use: --create-user username:password")
                exit(1)
            
            username, password = args.create_user.split(':', 1)
            result = create_api_user(username, password)
            
            if result['success']:
                logger.info("RentWebServer", f"✓ User created: {username}")
                logger.info("RentWebServer", f"Account ID: {result['account']['account_id']}")
            else:
                logger.error("RentWebServer", f"✗ Failed: {result['error']}")
            exit(0)
        
        # Otherwise run the server
        run_rent_web_server(port=args.port, debug=args.debug)
        
    except KeyboardInterrupt:
        logger.info("RentWebServer", "Server stopped by user")
    except Exception as e:
        logger.error("RentWebServer", f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
