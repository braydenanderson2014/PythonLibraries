"""
Splash Screen Manager
Handles the lifecycle of the splash screen during application startup.

Features:
- Starts immediately when application launches
- Pauses when UI reaches login
- Resumes when main window finishes loading
- Listens to logger messages for progress updates
- Automatically closes when main window is shown
"""

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QApplication
from assets.SplashScreen import SplashScreen
from assets.Logger import Logger
import time

logger = Logger()


class SplashScreenManager:
    """Manages the lifecycle of the splash screen during startup"""
    
    def __init__(self, app_name="Financial Manager", version="1.0.0", image_path=None):
        """
        Initialize the splash screen manager
        
        Args:
            app_name: Application name to display
            version: Version string to display
            image_path: Optional path to splash image
        """
        self.app_name = app_name
        self.version = version
        self.image_path = image_path
        self.splash = None
        self.is_paused = False
        self.is_running = False
        self.progress_value = 0
        self.loading_steps = [
            (5, "Initializing application..."),
            (15, "Loading configuration..."),
            (25, "Initializing database..."),
            (40, "Loading user preferences..."),
            (60, "Setting up UI components..."),
        ]
        self.current_step = 0
        self.step_timer = None
        self.logger = Logger()
        
        # Connect to logger signals for progress updates
        if hasattr(self.logger, 'connect_log_listener'):
            try:
                self.logger.connect_log_listener(self._on_log_message)
            except Exception as e:
                self.logger.warning("SplashScreenManager", f"Could not connect log listener: {e}")
    
    def start(self):
        """Start the splash screen immediately"""
        try:
            self.logger.debug("SplashScreenManager", "Starting splash screen...")
            
            self.splash = SplashScreen(
                image_path=self.image_path,
                show_percentage=True,
                show_message=True,
                app_name=self.app_name,
                version=self.version,
                width=600,
                height=400
            )
            
            # Show the splash screen
            self.splash.show()
            QApplication.processEvents()
            
            self.is_running = True
            self.progress_value = 0
            
            # Start automatic progress animation
            self._start_progress_animation()
            
            self.logger.info("SplashScreenManager", "Splash screen started")
            
        except Exception as e:
            self.logger.error("SplashScreenManager", f"Failed to start splash screen: {e}")
    
    def _start_progress_animation(self):
        """Start animating progress through loading steps"""
        self.step_timer = QTimer()
        self.step_timer.timeout.connect(self._animate_progress)
        self.step_timer.start(500)  # Update every 500ms
    
    def _animate_progress(self):
        """Animate progress through predefined steps"""
        if not self.is_paused and self.current_step < len(self.loading_steps):
            progress, message = self.loading_steps[self.current_step]
            self.set_progress(progress, message)
            self.current_step += 1
        elif self.current_step >= len(self.loading_steps):
            # Keep at 90% until explicitly finished
            if self.splash and not self.is_paused:
                self.set_progress(90, "Ready to login...")
    
    def pause(self):
        """Pause the splash screen (typically when UI reaches login)"""
        if not self.is_paused and self.splash:
            self.is_paused = True
            if self.step_timer:
                self.step_timer.stop()
            self.logger.info("SplashScreenManager", "Splash screen paused at login")
    
    def resume(self):
        """Resume the splash screen (typically when main window starts loading)"""
        if self.is_paused and self.splash:
            self.is_paused = False
            self.logger.info("SplashScreenManager", "Splash screen resumed - loading main window")
            
            # Continue with new messages
            self.set_progress(60, "Initializing user interface...")
            QApplication.processEvents()
            
            self.set_progress(75, "Loading financial data...")
            QApplication.processEvents()
            
            self.set_progress(90, "Loading dashboard...")
            QApplication.processEvents()
    
    def set_progress(self, value, message=None):
        """
        Update splash screen progress
        
        Args:
            value: Progress value (0-100)
            message: Optional status message
        """
        if self.splash and self.is_running:
            try:
                self.progress_value = value
                self.splash.set_progress(value, message)
                QApplication.processEvents()
                # Don't log progress updates to avoid infinite recursion
                # with log signal listeners
            except Exception as e:
                self.logger.warning("SplashScreenManager", f"Error updating progress: {e}")
    
    def finish(self):
        """Finish and close the splash screen"""
        if self.splash and self.is_running:
            try:
                # Stop animation
                if self.step_timer:
                    self.step_timer.stop()
                
                # Final progress update
                self.set_progress(100, "Done!")
                
                # Give it a moment to show completion
                QApplication.processEvents()
                time.sleep(0.2)
                
                # Close the splash screen
                self.splash.finish()
                self.is_running = False
                
                self.logger.info("SplashScreenManager", "Splash screen closed")
                
            except Exception as e:
                self.logger.error("SplashScreenManager", f"Error finishing splash screen: {e}")
    
    def _on_log_message(self, title, level, message):
        """Handle log messages from the logger
        
        This method is called whenever a log message is emitted,
        allowing the splash screen to stay updated with application progress.
        """
        # Update progress based on specific messages
        if not self.is_paused and self.splash:
            try:
                # Map log messages to progress updates
                if "Database" in message or "database" in message.lower():
                    self.set_progress(20, f"{message}")
                elif "UI" in message or "interface" in message.lower() or "component" in message.lower():
                    self.set_progress(40, f"{message}")
                elif "Stock" in message or "financial" in message.lower():
                    self.set_progress(55, f"{message}")
                elif "Ready" in message or "Complete" in message:
                    self.set_progress(95, f"{message}")
            except Exception:
                pass  # Silently ignore errors in log message handling
    
    def is_active(self):
        """Check if splash screen is currently running"""
        return self.is_running and self.splash is not None
    
    def get_progress(self):
        """Get current progress value"""
        return self.progress_value


# Global instance for easy access
_splash_manager_instance = None


def get_splash_manager(app_name="Financial Manager", version="1.0.0", image_path=None):
    """Get or create the global splash screen manager instance"""
    global _splash_manager_instance
    if _splash_manager_instance is None:
        _splash_manager_instance = SplashScreenManager(app_name, version, image_path)
    return _splash_manager_instance
