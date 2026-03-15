"""
Rent Management Web Server with Authentication
REST API for rent management with user authentication.
Only loads RentTracker AFTER successful user login.
"""

import sys
import os

# Setup paths - add root first so assets can be found
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, root_path)
sys.path.insert(0, os.path.join(root_path, 'src'))
sys.path.insert(0, os.path.join(root_path, 'ui'))

# Now import after paths are set
from src.account import AccountManager
from src.rent_tracker import RentTracker
from src.rent_web_server import create_server
from src.rent_api_auth import create_api_only_user
from assets.Logger import Logger

logger = Logger()


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
        # Load account manager (for authentication)
        logger.info("RentWebServer", "Loading AccountManager for authentication...")
        account_manager = AccountManager()
        logger.info("RentWebServer", "AccountManager loaded successfully")
        
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
        account_manager = AccountManager()
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
