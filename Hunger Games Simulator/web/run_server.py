#!/usr/bin/env python3
"""
Launcher script for the Hunger Games Simulator web interface.
Provides proper error handling and logging for the Flask application.
"""

import sys
import os
import logging
from app import app

def setup_logging():
    """Configure logging for the web application"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('web_interface.log')
        ]
    )

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import flask
        import flask_cors
        print("✓ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def main():
    """Main launcher function"""
    print("Hunger Games Simulator - Web Interface")
    print("=" * 40)

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)

    # Check if we're in the right directory
    if not os.path.exists('templates/index.html'):
        print("✗ Error: templates/index.html not found")
        print("Please run this script from the web directory")
        sys.exit(1)

    # Start the server
    try:
        logger.info("Starting Hunger Games Simulator web interface...")
        print("Server starting on http://localhost:5000")
        print("Press Ctrl+C to stop")
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        print("\nServer stopped")
    except Exception as e:
        logger.error(f"Server error: {e}")
        print(f"✗ Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()