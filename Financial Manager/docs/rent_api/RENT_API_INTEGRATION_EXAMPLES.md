# Example: Integration with Financial Manager Main Application

## Option 1: Add to main_window.py

```python
# At the top of main_window.py, add imports:
import threading
from src.rent_web_server_runner import run_rent_web_server

# In your MainWindow.__init__() method, add this after initializing RentTracker:

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    
    # ... your existing initialization code ...
    
    # Initialize rent tracker
    self.rent_tracker = RentTracker()
    
    # ===== ADD THIS SECTION =====
    # Start Rent Management Web Server in background
    try:
        self.server_thread = threading.Thread(
            target=run_rent_web_server,
            args=(5000, False),  # port=5000, debug=False
            daemon=True
        )
        self.server_thread.start()
        print("✓ Rent Management Web Server started on port 5000")
        self.statusBar().showMessage("Web API running on port 5000")
    except Exception as e:
        print(f"✗ Failed to start Rent Web Server: {e}")
        # Server is optional - app continues if it fails
    # ===== END ADD SECTION =====
    
    # ... rest of your initialization ...
```

## Option 2: Create a separate launcher script

Create `launch_with_api.py`:

```python
#!/usr/bin/env python3
"""
Launch Financial Manager with Rent Management API
"""

import sys
import os
import threading
from pathlib import Path

# Setup paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / 'src'))
sys.path.insert(0, str(Path(__file__).parent / 'ui'))

from src.rent_web_server_runner import run_rent_web_server
from assets.Logger import Logger

logger = Logger()


def main():
    """Launch both web API and desktop application"""
    
    print("=" * 60)
    print("Financial Manager with Rent Management API")
    print("=" * 60)
    
    # Start web server in background thread
    print("\n📡 Starting Rent Management Web Server...")
    try:
        server_thread = threading.Thread(
            target=run_rent_web_server,
            args=(5000, False),
            daemon=True
        )
        server_thread.start()
        print("✓ Web Server started on http://localhost:5000")
        print("  Available endpoints:")
        print("  - GET  /api/tenants")
        print("  - GET  /api/tenants/<id>")
        print("  - POST /api/tenants/<id>/disputes")
        print()
    except Exception as e:
        logger.error("Main", f"Failed to start web server: {e}")
        print(f"✗ Web Server failed: {e}")
        print("  Continuing with desktop application only...")
        print()
    
    # Launch desktop application
    print("🖥️  Starting Financial Manager...")
    try:
        from financial_tracker import FinancialTracker
        app = FinancialTracker()
        app.run()
    except ImportError:
        # Try alternate import
        try:
            from ui.financial_tracker import FinancialTracker
            app = FinancialTracker()
            app.run()
        except Exception as e:
            print(f"✗ Failed to launch Financial Manager: {e}")
            print("\nTrying to import main window...")
            try:
                from ui.main_window import MainWindow
                from PyQt5.QtWidgets import QApplication
                
                application = QApplication(sys.argv)
                window = MainWindow()
                window.show()
                sys.exit(application.exec_())
            except Exception as e2:
                print(f"✗ Failed to launch UI: {e2}")
                raise


if __name__ == '__main__':
    main()
```

Run with:
```bash
python launch_with_api.py
```

## Option 3: Using environment variables for configuration

Create `.env` file in project root:

```env
# Rent API Configuration
RENT_API_PORT=5000
RENT_API_DEBUG=false
RENT_API_HOST=0.0.0.0

# You can read these in your startup code:
```

Then in your startup code:

```python
import os
from dotenv import load_dotenv

load_dotenv()

port = int(os.getenv('RENT_API_PORT', 5000))
debug = os.getenv('RENT_API_DEBUG', 'false').lower() == 'true'
host = os.getenv('RENT_API_HOST', '0.0.0.0')

server_thread = threading.Thread(
    target=run_rent_web_server,
    args=(port, debug),
    daemon=True
)
server_thread.start()
```

## Option 4: Configuration class

Create `src/rent_api_config.py`:

```python
"""Configuration for Rent Management API"""

import os
from pathlib import Path


class RentAPIConfig:
    """Configuration management for Rent API"""
    
    # Server settings
    HOST = os.getenv('RENT_API_HOST', '0.0.0.0')
    PORT = int(os.getenv('RENT_API_PORT', 5000))
    DEBUG = os.getenv('RENT_API_DEBUG', 'false').lower() == 'true'
    
    # CORS settings
    CORS_ORIGINS = os.getenv('RENT_API_CORS_ORIGINS', '*').split(',')
    
    # Authentication (future)
    AUTH_ENABLED = os.getenv('RENT_API_AUTH', 'false').lower() == 'true'
    
    # Persistence (future)
    DISPUTES_PERSIST = os.getenv('RENT_API_PERSIST_DISPUTES', 'false').lower() == 'true'
    PERSISTENCE_PATH = Path(os.getenv('RENT_API_DATA_PATH', './data'))
    
    @classmethod
    def get_server_url(cls):
        """Get server URL for client connections"""
        protocol = 'https' if cls.DEBUG is False else 'http'
        return f"{protocol}://{cls.HOST}:{cls.PORT}"


# Usage:
# from src.rent_api_config import RentAPIConfig
# server = create_server(rt, host=RentAPIConfig.HOST, port=RentAPIConfig.PORT)
```

## Option 5: Conditional startup (production check)

```python
import os
import sys
import threading
from src.rent_web_server_runner import run_rent_web_server

def is_production():
    """Check if running in production mode"""
    return os.getenv('ENVIRONMENT', 'development') == 'production'


def startup_web_api():
    """Conditionally start web API based on configuration"""
    
    # Only start in certain conditions
    if os.getenv('DISABLE_API') == 'true':
        print("Web API disabled via environment variable")
        return
    
    if is_production():
        port = 8000  # Use different port in production
        debug = False
    else:
        port = 5000  # Development port
        debug = True
    
    try:
        server_thread = threading.Thread(
            target=run_rent_web_server,
            args=(port, debug),
            daemon=True
        )
        server_thread.start()
        print(f"✓ Web API started on port {port}")
    except Exception as e:
        print(f"✗ Web API failed to start: {e}")
        if is_production():
            raise  # Fatal in production
        else:
            pass  # Continue in development


# In your main initialization:
if __name__ == '__main__':
    startup_web_api()
    # ... rest of app startup ...
```

## Checking Server Status

```python
import requests
from assets.Logger import Logger

logger = Logger()


def verify_api_server(host='localhost', port=5000, timeout=5):
    """Verify API server is running"""
    try:
        response = requests.get(
            f'http://{host}:{port}/api/health',
            timeout=timeout
        )
        if response.status_code == 200:
            logger.info("API", "✓ Web API server is healthy")
            return True
    except requests.ConnectionError:
        logger.warning("API", "✗ Web API server not responding")
        return False
    except Exception as e:
        logger.error("API", f"Error checking API: {e}")
        return False


# In your startup:
if verify_api_server():
    print("Web API is ready for connections")
else:
    print("Web API not available - desktop mode only")
```

## Testing the Integration

After integration, test with:

```bash
# 1. Start the app normally
python launch_with_api.py

# 2. In another terminal, test the API
curl http://localhost:5000/api/health

# 3. Or use the Python client
python -c "
from src.rent_web_client import create_client
client = create_client('http://localhost:5000')
print('Health:', client.health_check())
success, tenants = client.get_all_tenants()
print(f'Tenants: {len(tenants)} found')
"
```

## Troubleshooting Integration

### Server starts but desktop UI doesn't load
- Ensure all imports work correctly
- Check that rent_tracker initializes without errors
- Verify all required modules are installed

### Desktop UI works but server doesn't start
- Check if port 5000 is already in use
- Try running with `--port 8000` instead
- Enable debug mode to see error details

### Both work but no communication
- Verify the client is using correct URL
- Check firewall settings
- Ensure CORS is properly enabled

---

## Notes

- The web server runs in a daemon thread, so it stops when the app closes
- Server startup is optional - app continues even if server fails
- No modifications to existing rent_tracker code
- Desktop UI and API share the same data (read-only from API side)

