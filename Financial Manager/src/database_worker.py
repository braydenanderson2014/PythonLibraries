"""
Database Worker - Handles database operations in background threads
"""
from PyQt6.QtCore import QThread, pyqtSignal, QObject
from typing import Callable, Any, Dict, Optional
import traceback
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from assets.Logger import Logger
except ImportError:
    class Logger:
        def debug(self, tag, msg): print(f"[DEBUG] {tag}: {msg}")
        def info(self, tag, msg): print(f"[INFO] {tag}: {msg}")
        def error(self, tag, msg): print(f"[ERROR] {tag}: {msg}")

logger = Logger()


class DatabaseWorker(QThread):
    """Worker thread for executing database operations without blocking UI"""
    
    # Signals
    operation_completed = pyqtSignal(object)  # Emits result of operation
    operation_failed = pyqtSignal(str)        # Emits error message
    progress_updated = pyqtSignal(int, str)   # Emits (percentage, message)
    
    def __init__(self, operation: Callable, *args, **kwargs):
        """
        Initialize database worker
        
        Args:
            operation: Function to execute in background thread
            *args: Positional arguments for the operation
            **kwargs: Keyword arguments for the operation
        """
        super().__init__()
        self.operation = operation
        self.args = args
        self.kwargs = kwargs
        self._cancelled = False
    
    def run(self):
        """Execute the database operation in background thread"""
        try:
            logger.debug("DatabaseWorker", f"Starting operation: {self.operation.__name__}")
            
            # Execute the operation
            result = self.operation(*self.args, **self.kwargs)
            
            # Check if cancelled before emitting
            if not self._cancelled:
                logger.debug("DatabaseWorker", f"Operation completed: {self.operation.__name__}")
                self.operation_completed.emit(result)
            else:
                logger.debug("DatabaseWorker", "Operation was cancelled")
                
        except Exception as e:
            error_msg = f"Database operation failed: {str(e)}\n{traceback.format_exc()}"
            logger.error("DatabaseWorker", error_msg)
            if not self._cancelled:
                self.operation_failed.emit(str(e))
    
    def cancel(self):
        """Cancel the operation"""
        logger.debug("DatabaseWorker", "Cancelling operation")
        self._cancelled = True


class ProgressiveDatabaseWorker(QThread):
    """Worker thread with progress reporting for multi-step database operations"""
    
    # Signals
    operation_completed = pyqtSignal(object)
    operation_failed = pyqtSignal(str)
    progress_updated = pyqtSignal(int, str)  # (percentage, message)
    
    def __init__(self, operation: Callable, progress_callback: Optional[Callable] = None, *args, **kwargs):
        """
        Initialize progressive database worker
        
        Args:
            operation: Function to execute. Should accept a progress_callback parameter
            progress_callback: Optional callback for progress updates
            *args: Positional arguments for the operation
            **kwargs: Keyword arguments for the operation
        """
        super().__init__()
        self.operation = operation
        self.progress_callback = progress_callback
        self.args = args
        self.kwargs = kwargs
        self._cancelled = False
    
    def run(self):
        """Execute the database operation with progress reporting"""
        try:
            logger.debug("ProgressiveDatabaseWorker", f"Starting operation: {self.operation.__name__}")
            
            # Create progress callback wrapper
            def report_progress(percentage: int, message: str = ""):
                if not self._cancelled:
                    self.progress_updated.emit(percentage, message)
                    if self.progress_callback:
                        self.progress_callback(percentage, message)
            
            # Add progress callback to kwargs
            self.kwargs['progress_callback'] = report_progress
            
            # Execute the operation
            result = self.operation(*self.args, **self.kwargs)
            
            # Check if cancelled before emitting
            if not self._cancelled:
                logger.debug("ProgressiveDatabaseWorker", f"Operation completed: {self.operation.__name__}")
                self.operation_completed.emit(result)
            else:
                logger.debug("ProgressiveDatabaseWorker", "Operation was cancelled")
                
        except Exception as e:
            error_msg = f"Database operation failed: {str(e)}\n{traceback.format_exc()}"
            logger.error("ProgressiveDatabaseWorker", error_msg)
            if not self._cancelled:
                self.operation_failed.emit(str(e))
    
    def cancel(self):
        """Cancel the operation"""
        logger.debug("ProgressiveDatabaseWorker", "Cancelling operation")
        self._cancelled = True


class DatabaseOperationManager:
    """
    Manager for coordinating database operations with progress dialogs
    Simplifies the pattern of showing a progress dialog during database operations
    """
    
    @staticmethod
    def execute_with_progress(
        parent_widget,
        operation: Callable,
        on_success: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
        dialog_title: str = "Working...",
        dialog_message: str = "Processing database operation...",
        show_progress: bool = False,
        *args,
        **kwargs
    ):
        """
        Execute a database operation with a progress dialog
        
        Args:
            parent_widget: Parent QWidget for the progress dialog
            operation: Function to execute
            on_success: Callback when operation succeeds (receives result)
            on_error: Callback when operation fails (receives error message)
            dialog_title: Title for progress dialog
            dialog_message: Message for progress dialog
            show_progress: If True, use ProgressiveDatabaseWorker for operations that report progress
            *args: Arguments for the operation
            **kwargs: Keyword arguments for the operation
        
        Returns:
            The database worker thread (can be used to check status or cancel)
        """
        from assets.AnimatedProgressDialog import AnimatedProgressDialog
        
        # Create progress dialog
        progress_dialog = AnimatedProgressDialog.get_instance(
            parent=parent_widget,
            title=dialog_title,
            message=dialog_message
        )
        
        # Choose worker type based on progress reporting need
        if show_progress:
            worker = ProgressiveDatabaseWorker(operation, *args, **kwargs)
            
            # Connect progress updates
            def update_progress(percentage, message):
                if message:
                    progress_dialog.update_message(f"{dialog_message}\n{message}")
            
            worker.progress_updated.connect(update_progress)
        else:
            worker = DatabaseWorker(operation, *args, **kwargs)
        
        # Connect completion signals
        def on_completed(result):
            progress_dialog.close()
            if on_success:
                on_success(result)
            logger.debug("DatabaseOperationManager", "Operation completed successfully")
        
        def on_failed(error):
            progress_dialog.close()
            if on_error:
                on_error(error)
            else:
                # Default error handling - show message box
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(
                    parent_widget,
                    "Database Error",
                    f"An error occurred during the database operation:\n\n{error}"
                )
            logger.error("DatabaseOperationManager", f"Operation failed: {error}")
        
        worker.operation_completed.connect(on_completed)
        worker.operation_failed.connect(on_failed)
        
        # Connect dialog cancel to worker cancel
        progress_dialog.cancelled.connect(worker.cancel)
        
        # Start the worker
        worker.start()
        
        # Show the dialog
        progress_dialog.show()
        
        return worker
