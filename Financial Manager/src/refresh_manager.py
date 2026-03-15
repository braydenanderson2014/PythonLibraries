"""Refresh Manager for coordinating stock data updates.

This module handles scheduling and coordinating periodic refreshes of stock data
from various sources for the watchlist and portfolio systems.
"""

from typing import Callable, List, Optional, Dict
from datetime import timedelta, datetime
import threading
import time
from assets.Logger import Logger
logger = Logger()


class RefreshManager:
    """Manages periodic refresh of stock data for watchlists and portfolios.
    
    This is a singleton-like manager that coordinates data refreshes across
    different parts of the application without requiring tight coupling.
    """
    
    def __init__(self):
        """Initialize the refresh manager."""
        logger.debug("RefreshManager", "Initializing RefreshManager")
        self._refresh_callbacks: Dict[str, Callable] = {}
        self._thread = None
        self._thread_stop = threading.Event()
        self._interval = timedelta(minutes=5)  # Default 5-minute refresh interval
        self._is_running = False
        self._lock = threading.Lock()
    
    def register_callback(self, name: str, callback: Callable):
        """Register a callback to be called during refresh.
        
        Args:
            name: Unique name for this callback
            callback: Function to call with no arguments during refresh
        """
        with self._lock:
            self._refresh_callbacks[name] = callback
            logger.debug("RefreshManager", f"Registered callback: {name}")
    
    def unregister_callback(self, name: str) -> bool:
        """Unregister a callback.
        
        Args:
            name: Name of the callback to remove
            
        Returns:
            True if callback was removed, False if it didn't exist
        """
        with self._lock:
            if name in self._refresh_callbacks:
                del self._refresh_callbacks[name]
                logger.debug("RefreshManager", f"Unregistered callback: {name}")
                return True
            logger.debug("RefreshManager", f"Callback not found: {name}")
            return False
    
    def set_interval(self, interval: timedelta):
        """Set the refresh interval.
        
        Args:
            interval: Time between refreshes
        """
        with self._lock:
            self._interval = interval
            logger.debug("RefreshManager", f"Set refresh interval to {interval}")
    
    def start(self):
        """Start the refresh manager.
        
        Spawns a background thread that calls all registered callbacks
        at the specified interval.
        """
        with self._lock:
            if self._is_running:
                logger.debug("RefreshManager", "RefreshManager already running")
                return
            
            self._is_running = True
            self._thread_stop.clear()
        
        def refresh_loop():
            """Main refresh loop."""
            while not self._thread_stop.is_set():
                try:
                    # Call all registered callbacks
                    with self._lock:
                        callbacks = list(self._refresh_callbacks.values())
                    
                    logger.debug("RefreshManager", f"Executing {len(callbacks)} refresh callbacks")
                    for callback in callbacks:
                        try:
                            callback()
                        except Exception as e:
                            logger.error("RefreshManager", f"Error in refresh callback: {str(e)}")
                    
                except Exception as e:
                    logger.error("RefreshManager", f"Error in refresh loop: {str(e)}")
                
                # Wait for the interval or until stop is signaled
                self._thread_stop.wait(self._interval.total_seconds())
        
        self._thread = threading.Thread(target=refresh_loop, name="RefreshManagerThread", daemon=True)
        self._thread.start()
        logger.info("RefreshManager", "RefreshManager started")
    
    def stop(self):
        """Stop the refresh manager.
        
        Stops the background thread and waits for it to terminate.
        """
        with self._lock:
            if not self._is_running:
                logger.debug("RefreshManager", "RefreshManager not running")
                return
            
            self._is_running = False
        
        self._thread_stop.set()
        
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
        
        logger.info("RefreshManager", "RefreshManager stopped")
    
    def refresh_now(self):
        """Trigger an immediate refresh.
        
        Calls all registered callbacks immediately without waiting for the interval.
        """
        with self._lock:
            callbacks = list(self._refresh_callbacks.values())
        
        logger.debug("RefreshManager", f"Triggering immediate refresh with {len(callbacks)} callbacks")
        for callback in callbacks:
            try:
                callback()
            except Exception as e:
                logger.error("RefreshManager", f"Error in refresh callback: {str(e)}")
    
    def is_running(self) -> bool:
        """Check if the refresh manager is running."""
        return self._is_running


__all__ = ["RefreshManager"]
