#!/usr/bin/env python3
"""
Enhanced PDFLogger with proper file size rotation
"""

import logging
from logging.handlers import RotatingFileHandler
from io import StringIO, TextIOWrapper
import os
import sys
import atexit

class InMemoryLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.log_stream = StringIO()

    def emit(self, record):
        if self.log_stream.closed:
            # Create a new StringIO if the current one is closed
            self.log_stream = StringIO()
            
        self.log_entry = self.format(record)
        self.log_stream.write(self.log_entry + '\n')

    def get_logs(self):
        if self.log_stream.closed:
            return "Log stream was closed"
        return self.log_stream.getvalue()

    def clear_logs(self):
        if not self.log_stream.closed:
            self.log_stream.close()
        self.log_stream = StringIO()
        
    def close(self):
        if not self.log_stream.closed:
            self.log_stream.close()
        super().close()

class EncodedStreamHandler(logging.StreamHandler):
    def __init__(self, stream=None, encoding=None):
        self.encoding = encoding
        
        if encoding and stream and hasattr(stream, 'buffer'):
            stream = TextIOWrapper(stream.buffer, encoding=encoding)
            
        super().__init__(stream)

    def emit(self, record):
        if self.stream and not getattr(self.stream, 'closed', False):
            try:
                msg = self.format(record)
                self.stream.write(msg + self.terminator)
                self.flush()
            except Exception:
                self.handleError(record)

class Logger:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance
        
    def __init__(self, log_dir=None):
        if getattr(self, '_initialized', False):
            return  # Prevent re-initialization
        self._initialized = True
        
        # Get log settings from settings controller
        self.log_file_path, self.max_size_mb, self.backup_count = self._get_log_settings(log_dir)
        
        # Create logger with name
        self.logger = logging.getLogger('pdf_utility')
        self.logger.setLevel(logging.DEBUG)
        
        # Clear any existing handlers to avoid duplicates
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        # Create in-memory handler
        self.in_memory_handler = InMemoryLogHandler()
        self.in_memory_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(self.in_memory_handler)
        
        # Create rotating file handler using settings
        try:
            # Ensure log directory exists
            os.makedirs(os.path.dirname(self.log_file_path), exist_ok=True)
            
            # Convert MB to bytes for RotatingFileHandler
            max_bytes = int(self.max_size_mb * 1024 * 1024)
            
            self.file_handler = RotatingFileHandler(
                self.log_file_path, 
                mode='a', 
                maxBytes=max_bytes, 
                backupCount=self.backup_count,
                encoding='utf-8'
            )
            self.file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(self.file_handler)
        except Exception as e:
            sys.stderr.write(f"Failed to create rotating file handler: {e}\n")
        
        # Create stdout handler
        try:
            self.stream_handler = EncodedStreamHandler(sys.stdout, encoding='utf-8')
            self.stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(self.stream_handler)
        except Exception as e:
            sys.stderr.write(f"Failed to create stream handler: {e}\n")
        
        # Register clean-up to happen at exit
        atexit.register(self.cleanup)
        
        self.info("LOGGER", "=================================================================")
        self.info("LOGGER", f" EVENT: INIT - Log file: {self.log_file_path}")
        self.info("LOGGER", f" LOG ROTATION: Max size {self.max_size_mb}MB, {self.backup_count} backups")
        self.info("LOGGER", "=================================================================")
        
    def _get_log_settings(self, log_dir=None):
        """Get the log settings from settings controller or use fallbacks"""
        try:
            # Try to import and use settings controller
            from settings_controller import SettingsController
            settings = SettingsController()
            settings.load_settings()
            
            log_file_path = settings.get_log_file_path()
            max_size_mb = settings.get_setting("logging", "max_log_size", 10)  # Get from widget settings
            backup_count = settings.get_setting("logging", "backup_count", 3)  # Default to 3 backups
            
            return log_file_path, max_size_mb, backup_count
        except Exception as e:
            # Fallback settings
            if log_dir:
                log_file_path = os.path.join(log_dir, "pdf_utility.log")
            else:
                log_file_path = "pdf_utility.log"
            return log_file_path, 10, 3  # Default: 10MB, 3 backups

    def log(self, title, message):
        self.logger.info(f"[{title}]: {message}")

    def error(self, title, message):
        self.logger.error(f"[{title}]: {message}")

    def warning(self, title, message):
        self.logger.warning(f"[{title}]: {message}")

    def debug(self, title, message):
        self.logger.debug(f"[{title}]: {message}")

    def critical(self, title, message):
        self.logger.critical(f"[{title}]: {message}")

    def info(self, title, message):
        self.logger.info(f"[{title}]: {message}")

    def exception(self, title, message):
        self.logger.exception(f"[{title}]: {message}")

    def fatal(self, title, message):
        self.logger.fatal(f"[{title}]: {message}")

    def get_logs(self):
        return self.in_memory_handler.get_logs()
    
    def delete_logs(self):
        """Clear in-memory logs and truncate log file"""
        self.in_memory_handler.clear_logs()

        # Close and remove all file handlers
        for handler in self.logger.handlers[:]:
            if isinstance(handler, (logging.FileHandler, RotatingFileHandler)):
                handler.close()
                self.logger.removeHandler(handler)

        # Truncate the log file instead of deleting it
        if os.path.exists(self.log_file_path):
            try:
                with open(self.log_file_path, "w", encoding="utf-8") as file:
                    file.truncate(0)  # Clear the content of the file
                    print("Log file truncated successfully.")
            except (PermissionError, OSError) as e:
                sys.stderr.write(f"Failed to truncate log file: {e}\n")
                return  # Exit if the file cannot be truncated

        # Recreate the rotating file handler
        try:
            max_bytes = int(self.max_size_mb * 1024 * 1024)
            self.file_handler = RotatingFileHandler(
                self.log_file_path, 
                mode='a', 
                maxBytes=max_bytes, 
                backupCount=self.backup_count,
                encoding='utf-8'
            )
            self.file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(self.file_handler)
        except Exception as e:
            sys.stderr.write(f"Failed to create new rotating file handler: {e}\n")

    def get_current_log_size_mb(self):
        """Get current log file size in MB"""
        try:
            if os.path.exists(self.log_file_path):
                size_bytes = os.path.getsize(self.log_file_path)
                return size_bytes / (1024 * 1024)
        except Exception:
            pass
        return 0.0

    def manually_rotate_if_needed(self):
        """Manually check and rotate log if needed (backup method)"""
        try:
            current_size = self.get_current_log_size_mb()
            if current_size >= self.max_size_mb:
                # Force rotation by triggering the rotating handler
                if hasattr(self.file_handler, 'doRollover'):
                    self.file_handler.doRollover()
                    self.info("LOGGER", f"Log rotated - was {current_size:.2f}MB, limit {self.max_size_mb}MB")
        except Exception as e:
            self.error("LOGGER", f"Failed to rotate log: {e}")

    def cleanup(self):
        """Clean up resources when the program exits"""
        for handler in self.logger.handlers:
            try:
                handler.close()
            except:
                pass

# For backward compatibility
PDFLogger = Logger
