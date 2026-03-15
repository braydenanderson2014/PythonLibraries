#!/usr/bin/env python3
# directory_monitor.py - Monitor directories for new PDF files

import os
import time
import threading
import shutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from PyQt6.QtCore import QObject, pyqtSignal

from PDFLogger import Logger
from settings_controller import SettingsController

class PDFFileHandler(FileSystemEventHandler):
    """Handler for PDF file events"""
    
    def __init__(self, controller):
        self.controller = controller
        self.logger = Logger()
        
    def on_created(self, event):
        """Handle file creation events"""
        if not event.is_directory and event.src_path.lower().endswith('.pdf'):
            self.logger.info("DirectoryMonitor", f"New PDF detected: {event.src_path}")
            self.controller.process_new_pdf(event.src_path)

class DirectoryMonitor(QObject):
    """
    Monitor directories for new PDF files and automatically process them
    """
    
    # Signal emitted when new PDFs are detected
    new_pdfs_signal = pyqtSignal(list)  # list of PDF paths
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = Logger()
        
        # Use parent's settings controller if available
        if parent and hasattr(parent, 'settings'):
            self.logger.info("DirectoryMonitor", "Using parent's settings controller")
            self.settings_controller = parent.settings
        else:
            self.logger.info("DirectoryMonitor", "Creating new settings controller")
            self.settings_controller = SettingsController()
        
        # Ensure settings are loaded
        self.settings_controller.load_settings()
        
        self.is_monitoring = False
        self.observer = None
        self.monitor_thread = None
        self.processing_files = set()  # Track files currently being processed
        
        self.logger.info("DirectoryMonitor", "=========================================================")
        self.logger.info("DirectoryMonitor", "Initializing Directory Monitor")
        self.logger.info("DirectoryMonitor", "=========================================================")
        
        # Log current auto-import settings
        enabled = self.settings_controller.get_setting("auto_import", "enabled", False)
        watch_dir = self.settings_controller.get_setting("auto_import", "watch_directory", "")
        self.logger.info("DirectoryMonitor", f"Auto-import enabled: {enabled}")
        self.logger.info("DirectoryMonitor", f"Watch directory: {watch_dir}")
        
    def start_monitoring(self):
        """Start monitoring directories for new PDFs"""
        if self.is_monitoring:
            self.logger.warning("DirectoryMonitor", "Already monitoring directories")
            return False
            
        # Check if monitoring is enabled in settings
        enabled = self.settings_controller.get_setting("auto_import", "enabled", False)
        self.logger.info("DirectoryMonitor", f"Auto-import enabled setting: {enabled}")
        if not enabled:
            self.logger.error("DirectoryMonitor", "Cannot start monitoring: Auto-import is disabled in settings")
            return False
            
        # Get watch directory from settings
        watch_dir = self.settings_controller.get_setting("auto_import", "watch_directory")
        self.logger.info("DirectoryMonitor", f"Watch directory setting: '{watch_dir}'")
        if not watch_dir:
            self.logger.error("DirectoryMonitor", "Cannot start monitoring: No watch directory specified in settings")
            return False
            
        # Create watch directory if it doesn't exist
        if not os.path.exists(watch_dir):
            try:
                os.makedirs(watch_dir, exist_ok=True)
                self.logger.info("DirectoryMonitor", f"Created watch directory: {watch_dir}")
            except Exception as e:
                self.logger.error("DirectoryMonitor", f"Error creating watch directory: {str(e)}")
                return False
                
        # Check processed directory and create if needed
        processed_dir = self.settings_controller.get_setting("auto_import", "processed_directory")
        if processed_dir and not os.path.exists(processed_dir):
            try:
                os.makedirs(processed_dir, exist_ok=True)
                self.logger.info("DirectoryMonitor", f"Created processed directory: {processed_dir}")
            except Exception as e:
                self.logger.warning("DirectoryMonitor", f"Error creating processed directory: {str(e)}")
                # Don't return False here as this is non-critical
            
        try:
            # Start the monitoring thread
            self.monitor_thread = threading.Thread(
                target=self._monitoring_thread,
                args=(watch_dir,),
                daemon=True
            )
            self.monitor_thread.start()
            
            self.is_monitoring = True
            self.logger.info("DirectoryMonitor", f"Started monitoring directory: {watch_dir}")
            return True
            
        except Exception as e:
            self.logger.error("DirectoryMonitor", f"Error starting directory monitor: {str(e)}")
            return False
            
    def stop_monitoring(self):
        """Stop monitoring directories"""
        if not self.is_monitoring:
            return
            
        try:
            if self.observer:
                self.observer.stop()
                self.observer.join()
                self.observer = None
                
            self.is_monitoring = False
            self.logger.info("DirectoryMonitor", "Stopped monitoring directories")
            
        except Exception as e:
            self.logger.error("DirectoryMonitor", f"Error stopping directory monitor: {str(e)}")
            
    def _monitoring_thread(self, watch_dir):
        """Thread function that sets up and runs the directory observer"""
        try:
            self.logger.info("DirectoryMonitor", f"Monitoring thread started for {watch_dir}")
            
            # Set up observer with our custom event handler
            self.observer = Observer()
            event_handler = PDFFileHandler(self)
            self.observer.schedule(event_handler, watch_dir, recursive=True)
            
            # Check for existing PDFs before starting
            self._check_existing_pdfs(watch_dir)
            
            # Start the observer
            self.observer.start()
            
            # Keep thread alive until observer is stopped
            while self.is_monitoring and self.observer.is_alive():
                time.sleep(1)
                
        except Exception as e:
            self.logger.error("DirectoryMonitor", f"Error in monitoring thread: {str(e)}")
            
        finally:
            if self.observer:
                self.observer.stop()
                self.observer.join()
                
    def _check_existing_pdfs(self, watch_dir):
        """Check for existing PDF files in the watch directory"""
        try:
            existing_pdfs = []
            
            for root, _, files in os.walk(watch_dir):
                for file in files:
                    if file.lower().endswith('.pdf'):
                        pdf_path = os.path.join(root, file)
                        existing_pdfs.append(pdf_path)
            
            if existing_pdfs:
                self.logger.info("DirectoryMonitor", f"Found {len(existing_pdfs)} existing PDFs in watch directory")
                for pdf in existing_pdfs:
                    self.process_new_pdf(pdf)
                    
        except Exception as e:
            self.logger.error("DirectoryMonitor", f"Error checking existing PDFs: {str(e)}")
            
    def process_new_pdf(self, pdf_path):
        """Process a newly detected PDF file"""
        try:
            # Check if file still exists (it might have been moved/deleted)
            if not os.path.exists(pdf_path):
                self.logger.warning("DirectoryMonitor", f"PDF no longer exists: {pdf_path}")
                return
                
            # Check if we should move files after processing
            move_files = self.settings_controller.get_setting("auto_import", "move_after_import", False)
            processed_dir = self.settings_controller.get_setting("auto_import", "processed_directory")
            
            # Add to list of new PDFs (signal will be received by the application)
            self.new_pdfs_signal.emit([pdf_path])
            self.logger.info("DirectoryMonitor", f"Added new PDF to processing queue: {pdf_path}")
            
            # Add to processing set
            self.processing_files.add(pdf_path)
            
            # Move file if setting enabled and processed directory is specified
            if move_files and processed_dir:
                # Create a separate thread to handle moving the file after a delay
                # This gives the application time to process the file
                move_thread = threading.Thread(
                    target=self._delayed_file_move,
                    args=(pdf_path, processed_dir),
                    daemon=True
                )
                move_thread.start()
            else:
                # If we're not moving the file, remove it from processing set
                self.processing_files.discard(pdf_path)
                
        except Exception as e:
            self.logger.error("DirectoryMonitor", f"Error processing new PDF {pdf_path}: {str(e)}")
            self.processing_files.discard(pdf_path)
            
    def _delayed_file_move(self, pdf_path, processed_dir):
        """Move a file to the processed directory after a delay to ensure processing completes"""
        try:
            # Wait for a reasonable time to allow processing to complete
            # Default is 3 seconds, but can be configured in settings
            delay = self.settings_controller.get_setting("auto_import", "processing_delay", 3)
            self.logger.info("DirectoryMonitor", f"Waiting {delay} seconds before moving file: {pdf_path}")
            time.sleep(delay)
            
            # Check if file still exists (it might have been moved/deleted)
            if not os.path.exists(pdf_path):
                self.logger.warning("DirectoryMonitor", f"PDF no longer exists for moving: {pdf_path}")
                self.processing_files.discard(pdf_path)
                return
                
            # Create processed directory if it doesn't exist
            if not os.path.exists(processed_dir):
                os.makedirs(processed_dir, exist_ok=True)
                self.logger.info("DirectoryMonitor", f"Created processed directory: {processed_dir}")
                
            dest_path = os.path.join(processed_dir, os.path.basename(pdf_path))
            
            # Handle duplicate filenames
            counter = 1
            base_name, ext = os.path.splitext(os.path.basename(pdf_path))
            
            while os.path.exists(dest_path):
                dest_path = os.path.join(processed_dir, f"{base_name}_{counter}{ext}")
                counter += 1
                
            # Move the file
            shutil.move(pdf_path, dest_path)
            self.logger.info("DirectoryMonitor", f"Moved PDF from {pdf_path} to {dest_path}")
            
        except Exception as e:
            self.logger.error("DirectoryMonitor", f"Error in delayed file move for {pdf_path}: {str(e)}")
        finally:
            # Remove from processing set
            self.processing_files.discard(pdf_path)
