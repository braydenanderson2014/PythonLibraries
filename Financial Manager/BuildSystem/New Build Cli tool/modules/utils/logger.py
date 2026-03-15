"""
Logging utilities for BuildCLI.
"""

import logging
import sys
from typing import Optional
from pathlib import Path


class Logger:
    """Custom logger for BuildCLI with configurable output levels."""
    
    def __init__(self, level: str = "INFO", log_file: Optional[str] = None):
        self.logger = logging.getLogger("BuildCLI")
        self.logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler (optional)
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def debug(self, message: str) -> None:
        """Log a debug message."""
        self.logger.debug(message)
    
    def info(self, message: str) -> None:
        """Log an info message."""
        self.logger.info(message)
    
    def warning(self, message: str) -> None:
        """Log a warning message."""
        self.logger.warning(message)
    
    def error(self, message: str) -> None:
        """Log an error message."""
        self.logger.error(message)
    
    def critical(self, message: str) -> None:
        """Log a critical message."""
        self.logger.critical(message)
    
    def set_level(self, level: str) -> None:
        """Set the logging level."""
        numeric_level = getattr(logging, level.upper(), logging.INFO)
        self.logger.setLevel(numeric_level)
        
        # Update handler levels
        for handler in self.logger.handlers:
            if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
                handler.setLevel(numeric_level)
    
    def add_file_handler(self, log_file: str) -> None:
        """Add a file handler to the logger."""
        # Check if file handler already exists
        for handler in self.logger.handlers:
            if isinstance(handler, logging.FileHandler) and handler.baseFilename == str(Path(log_file).resolve()):
                return
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
    
    def remove_file_handlers(self) -> None:
        """Remove all file handlers from the logger."""
        handlers_to_remove = [
            handler for handler in self.logger.handlers
            if isinstance(handler, logging.FileHandler)
        ]
        
        for handler in handlers_to_remove:
            self.logger.removeHandler(handler)
            handler.close()


# Global logger instance
_global_logger: Optional[Logger] = None


def get_logger(level: str = "INFO") -> Logger:
    """Get or create the global logger instance."""
    global _global_logger
    
    if _global_logger is None:
        _global_logger = Logger(level)
    
    return _global_logger


def set_global_log_level(level: str) -> None:
    """Set the global log level."""
    global _global_logger
    
    if _global_logger is not None:
        _global_logger.set_level(level)