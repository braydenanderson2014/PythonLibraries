import logging
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
    def __init__(self):
        if getattr(self, '_initialized', False):
            return  # Prevent re-initialization
        self._initialized = True
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
        
        # Create file handler
        try:
            self.file_handler = logging.FileHandler("pdf_utility.log", mode='a', encoding='utf-8')
            self.file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(self.file_handler)
        except Exception as e:
            sys.stderr.write(f"Failed to create file handler: {e}\n")
        
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
        self.info("LOGGER", " EVENT: INIT")
        self.info("LOGGER", "=================================================================")

    
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
        self.in_memory_handler.clear_logs()

        # Close and remove all file handlers
        for handler in self.logger.handlers[:]:
            if isinstance(handler, logging.FileHandler):
                handler.close()
                self.logger.removeHandler(handler)

        # Truncate the log file instead of deleting it
        log_file = "pdf_utility.log"
        if os.path.exists(log_file):
            try:
                with open(log_file, "w", encoding="utf-8") as file:
                    file.truncate(0)  # Clear the content of the file
                    print("Log file truncated successfully.")
                    file.close()
            except (PermissionError, OSError) as e:
                sys.stderr.write(f"Failed to truncate log file: {e}\n")
                return  # Exit if the file cannot be truncated

        # Add a new file handler
        try:
            self.file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
            self.file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(self.file_handler)
        except Exception as e:
            sys.stderr.write(f"Failed to create new file handler: {e}\n")

    def cleanup(self):
        """Clean up resources when the program exits"""
        for handler in self.logger.handlers:
            try:
                handler.close()
            except:
                pass