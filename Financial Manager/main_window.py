import sys
import os

# Ensure the current directory is in the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QDialog, QMessageBox
from PyQt6.QtCore import QTimer, QThread
from ui.login import LoginDialog
from ui.main_window import MainWindow
from assets.Logger import Logger
from assets.SplashScreenManager import get_splash_manager

logger = Logger()

if __name__ == '__main__':
    import atexit
    import traceback
    
    # Close splash screen if running as PyInstaller bundle
    try:
        import pyi_splash
        # Splash will be closed right before login dialog shows
    except ImportError:
        pyi_splash = None
    
    # Install global exception handler for Qt
    def qt_exception_handler(type_, value, traceback_):
        logger.error("MainWindow", f"Qt Exception: {type_.__name__}: {value}")
        import traceback as tb
        tb.print_exception(type_, value, traceback_)
    
    sys.excepthook = qt_exception_handler
    
    try:
        logger.debug("MainWindow", "Starting application...")
        app = QApplication(sys.argv)
        logger.debug("MainWindow", "QApplication created")
        
        # Get splash image path
        if getattr(sys, 'frozen', False):
            BASE_PATH = sys._MEIPASS
        else:
            BASE_PATH = os.path.dirname(os.path.abspath(__file__))
        
        splash_image_path = os.path.join(BASE_PATH, 'resources', 'Splash.png')
        if not os.path.exists(splash_image_path):
            splash_image_path = None
            logger.warning("MainWindow", f"Splash image not found at {splash_image_path}, using gradient")
        
        # Start splash screen immediately
        splash_manager = get_splash_manager(
            app_name="Financial Manager",
            version="1.0.0",
            image_path=splash_image_path
        )
        splash_manager.start()
        logger.info("MainWindow", "Splash screen started")
        
        # Check Qt version and threading
        logger.debug("MainWindow", f"Qt Version: {app.applicationVersion() if hasattr(app, 'applicationVersion') else 'N/A'}")
        logger.debug("MainWindow", f"Application thread: {app.thread()}")
        logger.debug("MainWindow", f"Current thread: {QThread.currentThread()}")
        
        window = None
        
        def cleanup_on_exit():
            """Cleanup function to be called on exit"""
            logger.debug("MainWindow", "Running cleanup...")
            if window and hasattr(window, 'rent_dashboard_tab'):
                try:
                    rent_tracker = window.rent_dashboard_tab.rent_tracker
                    if hasattr(rent_tracker, 'cleanup'):
                        rent_tracker.cleanup()
                        logger.info("MainWindow", "Emergency cleanup completed")
                except Exception as e:
                    logger.warning("MainWindow", f"Emergency cleanup failed: {e}")
            
            # Close splash screen if still running
            if splash_manager.is_active():
                splash_manager.finish()
        
        # Register cleanup function
        atexit.register(cleanup_on_exit)
        
        # Close PyInstaller splash screen right before showing login
        if pyi_splash:
            pyi_splash.close()
        
        # Pause and hide custom splash screen at login so it doesn't obscure the login dialog
        splash_manager.pause()
        if splash_manager.splash:
            splash_manager.splash.hide()
        logger.info("MainWindow", "Splash screen paused at login")
        
        logger.debug("MainWindow", "Showing login dialog...")
        login_dialog = LoginDialog()
        result = login_dialog.exec()
        logger.debug("MainWindow", f"Login dialog result: {result}")
        
        if result == QDialog.DialogCode.Accepted:
            username = login_dialog.username_edit.text().strip()
            logger.debug("MainWindow", f"Creating MainWindow for user: {username}")
            
            try:
                # Resume splash screen while loading main window
                splash_manager.resume()
                # Show splash screen again (was hidden during login)
                if splash_manager.splash:
                    splash_manager.splash.show()
                logger.info("MainWindow", "Splash screen resumed - loading main window")
                
                window = MainWindow(username)
                logger.debug("MainWindow", "MainWindow created successfully")
                
                logger.debug("MainWindow", "Showing MainWindow...")
                window.show()
                logger.debug("MainWindow", "MainWindow shown")
                
                # Close splash screen when main window is fully loaded
                splash_manager.finish()
                logger.info("MainWindow", "Splash screen finished")
                
                logger.debug("MainWindow", "Starting event loop...")
                
                # Start the Qt event loop with error handling
                logger.debug("MainWindow", "Starting Qt event loop...")
                try:
                    exit_code = app.exec()
                    logger.debug("MainWindow", f"Qt event loop exited with code: {exit_code}")
                except Exception as e:
                    logger.error("MainWindow", f"Exception in Qt event loop: {e}")
                    import traceback
                    traceback.print_exc()
                    exit_code = 1
                    logger.debug("MainWindow", f"Application exited with code: {exit_code}")
                    sys.exit(exit_code)
                    
            except Exception as e:
                logger.error("MainWindow", f"Error creating or showing MainWindow: {e}")
                traceback.print_exc()
                splash_manager.finish()  # Close splash on error
                QMessageBox.critical(None, "Application Error", f"Failed to start application: {str(e)}")
                sys.exit(1)
        else:
            logger.debug("MainWindow", "Login cancelled")
            splash_manager.finish()  # Close splash if login cancelled
            sys.exit(0)
            
    except Exception as e:
        logger.error("MainWindow", f"Critical error in main: {e}")
        traceback.print_exc()
        # Try to close splash on critical error
        try:
            splash_manager = get_splash_manager()
            if splash_manager.is_active():
                splash_manager.finish()
        except:
            pass
        # Try to show error dialog even if QApplication creation failed
        try:
            from PyQt6.QtWidgets import QMessageBox, QApplication
            if not QApplication.instance():
                app = QApplication(sys.argv)
            QMessageBox.critical(None, "Critical Error", f"Application failed to start: {str(e)}")
        except:
            logger.error("MainWindow", "[CRITICAL] Could not show error dialog")
        sys.exit(1)
