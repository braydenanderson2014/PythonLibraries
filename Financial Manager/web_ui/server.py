"""
Simple Web UI Server
Serves the web UI static files alongside the Rent Management API
"""

import sys
import os

# Setup paths
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, root_path)
sys.path.insert(0, os.path.join(root_path, 'src'))
sys.path.insert(0, os.path.join(root_path, 'ui'))

from flask import Flask, send_from_directory, render_template_string
from flask_cors import CORS
from src.account import AccountManager
from src.rent_web_server import create_server
from src.rent_web_server_runner import create_api_user
from assets.Logger import Logger

logger = Logger()


def create_web_server(api_port=5000, web_port=5001, debug=False):
    """
    Create and run a web server that serves static UI files
    
    Args:
        api_port: Port for the REST API
        web_port: Port for the web UI
        debug: Enable debug mode
    
    Returns:
        Flask app instance
    """
    
    # Create Flask app for web UI
    web_app = Flask(__name__)
    web_app.config['JSON_SORT_KEYS'] = False
    
    # Enable CORS
    CORS(web_app)
    
    # Get web UI directory
    web_ui_dir = os.path.dirname(os.path.abspath(__file__))
    
    @web_app.route('/')
    def index():
        """Serve index.html"""
        return send_from_directory(web_ui_dir, 'index.html')
    
    @web_app.route('/<path:filename>')
    def static_files(filename):
        """Serve static files (CSS, JS, etc.)"""
        return send_from_directory(web_ui_dir, filename)
    
    @web_app.route('/config')
    def get_config():
        """Get configuration for the web UI"""
        return {
            'api_url': f'http://localhost:{api_port}',
            'web_url': f'http://localhost:{web_port}',
            'version': '1.0.0'
        }
    
    return web_app


def run_full_stack(api_port=5000, web_port=5001, debug=False):
    """
    Run the complete stack:
    - REST API on api_port
    - Web UI on web_port
    
    Args:
        api_port: Port for REST API
        web_port: Port for web UI
        debug: Enable debug mode
    """
    import threading
    import time
    
    logger.info("WebServer", "Starting Rent Management System (API + Web UI)")
    
    try:
        # Start API server in background thread
        logger.info("WebServer", f"Starting API server on port {api_port}...")
        from src.rent_web_server_runner import run_rent_web_server
        
        api_thread = threading.Thread(
            target=run_rent_web_server,
            args=(api_port, debug),
            daemon=True
        )
        api_thread.start()
        time.sleep(1)  # Give API time to start
        
        # Start web UI server in main thread
        logger.info("WebServer", f"Starting Web UI server on port {web_port}...")
        web_app = create_web_server(api_port, web_port, debug)
        
        logger.info("WebServer", "=" * 60)
        logger.info("WebServer", "Rent Management System is running!")
        logger.info("WebServer", f"Web UI:  http://localhost:{web_port}")
        logger.info("WebServer", f"API:     http://localhost:{api_port}")
        logger.info("WebServer", "=" * 60)
        
        web_app.run(
            host='0.0.0.0',
            port=web_port,
            debug=debug,
            use_reloader=False
        )
        
    except KeyboardInterrupt:
        logger.info("WebServer", "Server stopped by user")
    except Exception as e:
        logger.error("WebServer", f"Error: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Rent Management Web Server')
    parser.add_argument('--api-port', type=int, default=5000, help='API port (default: 5000)')
    parser.add_argument('--web-port', type=int, default=5001, help='Web UI port (default: 5001)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--create-user', help='Create API user (format: username:password)')
    
    args = parser.parse_args()
    
    try:
        # Create user if requested
        if args.create_user:
            if ':' not in args.create_user:
                logger.error("WebServer", "Invalid format. Use: --create-user username:password")
                exit(1)
            
            username, password = args.create_user.split(':', 1)
            result = create_api_user(username, password)
            
            if result['success']:
                logger.info("WebServer", f"✓ User created: {username}")
                logger.info("WebServer", f"Account ID: {result['account']['account_id']}")
            else:
                logger.error("WebServer", f"✗ Failed: {result['error']}")
            exit(0)
        
        # Run full stack
        run_full_stack(
            api_port=args.api_port,
            web_port=args.web_port,
            debug=args.debug
        )
        
    except KeyboardInterrupt:
        logger.info("WebServer", "Server stopped")
    except Exception as e:
        logger.error("WebServer", f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
