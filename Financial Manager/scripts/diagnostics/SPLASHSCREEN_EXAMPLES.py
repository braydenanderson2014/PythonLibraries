"""
Examples of how to use the SplashScreen integration with Logger
"""

# Example 1: Using Logger (signals are emitted automatically)
# ============================================================
from assets.Logger import Logger

logger = Logger()

# These log messages are automatically sent to the splash screen
logger.info("Database", "Connecting to database...")
logger.debug("UI", "Initializing user interface...")
logger.info("StockTracker", "Loading stock data...")

# The splash screen will intercept and display these automatically


# Example 2: Manually controlling splash screen progress
# ======================================================
from assets.SplashScreenManager import get_splash_manager

splash_manager = get_splash_manager()

# Update progress with explicit message
splash_manager.set_progress(25, "Loading financial data...")
splash_manager.set_progress(50, "Initializing dashboard...")
splash_manager.set_progress(75, "Setting up charts...")

# Pause and resume
splash_manager.pause()  # Freeze animation
splash_manager.resume()  # Continue animation

# Check status
if splash_manager.is_active():
    current_progress = splash_manager.get_progress()
    print(f"Current progress: {current_progress}%")

# Close when done
splash_manager.finish()


# Example 3: Using in a module during startup
# =============================================
import sys
import os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(PROJECT_ROOT)

from assets.Logger import Logger
from assets.SplashScreenManager import get_splash_manager

def initialize_application():
    """Initialize application with splash screen feedback"""
    logger = Logger()
    splash = get_splash_manager()
    
    logger.info("Init", "Starting initialization...")  # Shows on splash
    
    # Database initialization
    logger.info("Init", "Connecting to database...")
    # ... do work ...
    splash.set_progress(30, "Database connected")
    
    # Configuration loading
    logger.info("Init", "Loading configuration...")
    # ... do work ...
    splash.set_progress(50, "Configuration loaded")
    
    # Data loading
    logger.info("Init", "Loading financial data...")
    # ... do work ...
    splash.set_progress(80, "Data loaded")
    
    logger.info("Init", "Initialization complete!")
    splash.set_progress(95, "Ready!")


# Example 4: Adding custom log listener (for advanced use)
# =========================================================
from assets.Logger import Logger

logger = Logger()

def my_custom_listener(title, level, message):
    """Custom handler for log messages"""
    print(f"[{title}] {level}: {message}")
    # Could update UI elements, send to remote server, etc.

# Connect listener
if hasattr(logger, 'connect_log_listener'):
    logger.connect_log_listener(my_custom_listener)

# Now all log messages go to both the file and your custom listener
logger.info("MyModule", "This message goes to multiple places!")


# Example 5: Error handling with splash screen
# =============================================
from assets.Logger import Logger
from assets.SplashScreenManager import get_splash_manager

try:
    logger = Logger()
    splash = get_splash_manager()
    
    logger.debug("Operation", "Starting operation...")
    splash.set_progress(50, "Processing...")
    
    # Simulate some work
    result = 10 / 0  # This will raise an error
    
except Exception as e:
    logger.error("Operation", f"Error occurred: {e}")
    splash.set_progress(100, "Error!")
    # Handle error appropriately
finally:
    if splash.is_active():
        splash.finish()


# Example 6: Integration with threaded operations
# ================================================
import threading
from assets.Logger import Logger

def background_task():
    """Long-running task that reports progress via logs"""
    logger = Logger()
    
    for i in range(5):
        logger.info("BackgroundTask", f"Processing step {i+1} of 5...")
        # Do actual work
        import time
        time.sleep(1)

# Start background task
logger = Logger()
logger.info("Main", "Starting background task...")
task_thread = threading.Thread(target=background_task, daemon=True)
task_thread.start()

# Main thread continues (splash screen updates from log messages)
# The log messages from background_thread will update the splash screen


# Tips and Best Practices
# =======================
"""
1. LOG MESSAGES FOR SPLASH UPDATES
   - Use logger.info() or logger.debug() for operations
   - Messages automatically appear on splash screen
   - No need to manually call splash_manager.set_progress()

2. SPLASH MANAGER PAUSE/RESUME
   - Pause at login: splash_manager.pause()
   - Resume when loading: splash_manager.resume()
   - Finish when ready: splash_manager.finish()

3. AVOID DUPLICATE UPDATES
   - Either use Logger signals OR explicit progress updates
   - Mixing both can cause too many updates
   - Let the Logger do the work!

4. THREAD SAFETY
   - Logger is thread-safe (singleton)
   - All Qt signals are emitted on the main thread
   - Safe to call logger from worker threads

5. CUSTOM MESSAGES
   - Map your operations to meaningful messages
   - User sees: "Loading database..." not "step_1_complete"
   - Keep messages clear and informative
"""
