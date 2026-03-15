#!/usr/bin/env python3
# tts_widget.py - Text to Speech Widget for PDF Utility

import os
import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QProgressBar, QGroupBox, QFileDialog, QMessageBox,
    QListWidget, QAbstractItemView, QSplitter
)
from PyQt6.QtCore import Qt, QSize, QTimer

from text_to_speech import TextToSpeech
from PDFLogger import Logger
from settings_controller import SettingsController

class TTSWidget(QWidget):
    """Widget for Text-to-Speech functionality"""
    
    def __init__(self, parent=None, file_list_controller=None):
        super().__init__(parent)
        self.logger = Logger()
        self.settings = SettingsController()
        self.file_list_controller = file_list_controller
        
        # Create TextToSpeech engine
        self.tts = TextToSpeech()
        self.tts.set_progress_callback(self.update_progress)
        self.tts.set_status_callback(self.update_status)
        self.tts.set_complete_callback(self.playback_complete)
        
        # Track current state
        self.is_playing = False
        self.is_paused = False
        self.current_pdf = None
        self.total_pages = 0
        self.current_page = 0
        
        # Connect file list controller if provided
        if self.file_list_controller:
            # Only connect if not using shared widget directly
            pass
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI elements"""
        main_layout = QVBoxLayout(self)
        
        # Instructions
        instructions = QLabel(
            "Select a PDF file to convert to speech. The text will be extracted and read aloud."
        )
        instructions.setWordWrap(True)
        main_layout.addWidget(instructions)
        
        # File section
        files_group = QGroupBox("Files")
        files_layout = QVBoxLayout(files_group)
        
        # File management buttons
        files_buttons_layout = QHBoxLayout()
        
        self.add_files_btn = QPushButton("Add Files")
        self.add_files_btn.setToolTip("Add PDF files to the list")
        self.add_files_btn.clicked.connect(self.add_files)
        self.add_files_btn.setObjectName("tts_add_files_btn")  # Set object name for tutorial system
        files_buttons_layout.addWidget(self.add_files_btn)
        
        self.scan_dir_btn = QPushButton("Scan Directory")
        self.scan_dir_btn.setToolTip("Scan directory for PDF files")
        self.scan_dir_btn.clicked.connect(self.scan_directory)
        self.scan_dir_btn.setObjectName("tts_scan_dir_btn")  # Set object name for tutorial system
        files_buttons_layout.addWidget(self.scan_dir_btn)
        
        self.remove_selected_btn = QPushButton("Remove Selected")
        self.remove_selected_btn.setToolTip("Remove selected files from the list")
        self.remove_selected_btn.clicked.connect(self.remove_selected_files)
        self.remove_selected_btn.setObjectName("tts_remove_selected_btn")  # Set object name for tutorial system
        files_buttons_layout.addWidget(self.remove_selected_btn)
        
        self.clear_list_btn = QPushButton("Clear List")
        self.clear_list_btn.setToolTip("Clear the file list")
        self.clear_list_btn.clicked.connect(self.clear_list)
        files_buttons_layout.addWidget(self.clear_list_btn)
        
        files_layout.addLayout(files_buttons_layout)
        
        # File list
        if self.file_list_controller:
            self.file_list = self.file_list_controller.get_list_widget()
            self.file_list.setObjectName("tts_file_list")  # Set object name for tutorial system
        else:
            self.file_list = QListWidget()
            self.file_list.setObjectName("tts_file_list")  # Set object name for tutorial system
            self.file_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
            
        files_layout.addWidget(self.file_list)
        main_layout.addWidget(files_group)
        
        # Playback controls group
        controls_group = QGroupBox("Playback Controls")
        controls_layout = QVBoxLayout(controls_group)
        
        # Now playing section
        now_playing_layout = QHBoxLayout()
        now_playing_layout.addWidget(QLabel("Now Playing:"))
        self.now_playing_label = QLabel("No file selected")
        now_playing_layout.addWidget(self.now_playing_label, 1)
        controls_layout.addLayout(now_playing_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        controls_layout.addWidget(self.progress_bar)
        
        # Playback buttons
        buttons_layout = QHBoxLayout()
        
        self.play_btn = QPushButton("▶ Play")
        self.play_btn.setToolTip("Play the selected PDF")
        self.play_btn.clicked.connect(self.play_selected)
        self.play_btn.setObjectName("tts_play_btn")  # Set object name for tutorial system
        buttons_layout.addWidget(self.play_btn)
        
        self.pause_btn = QPushButton("⏸ Pause")
        self.pause_btn.setToolTip("Pause playback")
        self.pause_btn.clicked.connect(self.pause_playback)
        self.pause_btn.setEnabled(False)
        buttons_layout.addWidget(self.pause_btn)
        
        self.resume_btn = QPushButton("⏵ Resume")
        self.resume_btn.setToolTip("Resume playback")
        self.resume_btn.clicked.connect(self.resume_playback)
        self.resume_btn.setEnabled(False)
        buttons_layout.addWidget(self.resume_btn)
        
        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.setToolTip("Stop playback")
        self.stop_btn.clicked.connect(self.stop_playback)
        self.stop_btn.setEnabled(False)
        buttons_layout.addWidget(self.stop_btn)
        
        controls_layout.addLayout(buttons_layout)
        
        # Navigation buttons
        nav_buttons_layout = QHBoxLayout()
        
        self.rewind_btn = QPushButton("⏮ Previous Page")
        self.rewind_btn.setToolTip("Go to previous page")
        self.rewind_btn.clicked.connect(self.rewind_page)
        self.rewind_btn.setEnabled(False)  # Initially disabled
        nav_buttons_layout.addWidget(self.rewind_btn)
        
        self.skip_btn = QPushButton("⏭ Next Page")
        self.skip_btn.setToolTip("Skip to next page")
        self.skip_btn.clicked.connect(self.skip_page)
        self.skip_btn.setEnabled(False)  # Initially disabled
        nav_buttons_layout.addWidget(self.skip_btn)
        
        controls_layout.addLayout(nav_buttons_layout)
        
        main_layout.addWidget(controls_group)
        
        # Status bar
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Ready")
        status_layout.addWidget(self.status_label)
        main_layout.addLayout(status_layout)
        
    def add_files(self):
        """Add PDF files to the list via file dialog"""
        self.logger.info("TTSWidget", "Adding PDF files to the list")
        
        # Get last directory used or default to user's documents
        last_dir = self.settings.get_setting("general", "last_directory", "")
        if not last_dir or not os.path.exists(last_dir):
            last_dir = os.path.expanduser("~/Documents")
            
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Select PDF Files", last_dir, "PDF Files (*.pdf);;All Files (*.*)"
        )
        
        if not file_paths:
            self.logger.info("TTSWidget", "No files selected")
            return
            
        # Save last directory
        if file_paths:
            last_dir = os.path.dirname(file_paths[0])
            self.settings.set_setting("general", "last_directory", last_dir)
            self.settings.save_settings()
        
        # Add to list
        if self.file_list_controller:
            self.file_list_controller.add_files(file_paths)
        else:
            # If no shared controller, add directly to our listbox
            for path in file_paths:
                if path not in [self.file_list.item(i).text() for i in range(self.file_list.count())]:
                    self.file_list.addItem(path)
    
    def scan_directory(self):
        """Scan a directory for PDF files using the improved directory scanner"""
        # Disable until scan ends
        self.scan_dir_btn.setEnabled(False)   

        # Create the scanner, give it the shared controller,
        # and let it push files straight into that controller
        if self.file_list_controller:
            self.file_list_controller.disable_updates()
        
        from directory_scanner import PDFDirectoryScanner
        self.scanner = PDFDirectoryScanner(
            parent=self,
            file_list_controller=self.file_list_controller,
            batch_size=50
        )   

        # Re‑enable the button and updates when the scan completes
        def on_scan_complete():
            self.scan_dir_btn.setEnabled(True)
            if self.file_list_controller:
                self.file_list_controller.enable_updates()
            self.logger.info("TTSWidget", "Directory scan complete")
            
        self.scanner.scan_complete.connect(on_scan_complete)

        # Kick off the built‑in folder dialog + scan
        self.scanner.start_scan()
    
    def remove_selected_files(self):
        """Remove selected files from the list"""
        self.logger.info("TTSWidget", "Removing selected files from list")
        
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            return
            
        selected_paths = [item.text() for item in selected_items]
        
        # Remove files from list
        if self.file_list_controller:
            self.file_list_controller.remove_files(selected_paths)
        else:
            # If no shared controller, remove directly from our listbox
            for item in selected_items:
                self.file_list.takeItem(self.file_list.row(item))
    
    def clear_list(self):
        """Clear the file list"""
        self.logger.info("TTSWidget", "Clearing file list")
        
        # Confirm with user
        result = QMessageBox.question(
            self,
            "Clear List",
            "Are you sure you want to clear the file list?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if result != QMessageBox.StandardButton.Yes:
            return
        
        # Clear list
        if self.file_list_controller:
            self.file_list_controller.clear_files()
        else:
            # If no shared controller, clear directly
            self.file_list.clear()
            
    def play_selected(self):
        """Play the selected PDF"""
        self.logger.info("TTSWidget", "Playing selected PDF")
        
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select a PDF file to play.")
            return
            
        pdf_path = selected_items[0].text()
        if not pdf_path.lower().endswith('.pdf'):
            QMessageBox.warning(self, "Invalid Selection", "Please select a PDF file.")
            return
            
        if not os.path.exists(pdf_path):
            QMessageBox.warning(self, "File Not Found", f"The file {pdf_path} does not exist.")
            return
        
        # Reload TTS settings to ensure we're using the current voice selection
        self.tts.reload_settings()
        
        # Extract text from PDF
        self.current_pdf = pdf_path
        self.now_playing_label.setText(os.path.basename(pdf_path))
        self.status_label.setText(f"Extracting text from {os.path.basename(pdf_path)}...")
        
        # Extract text in the current thread to avoid UI freezes
        pages = self.tts.extract_text_from_pdf(pdf_path)
        
        if not pages:
            QMessageBox.warning(self, "No Text Found", "No readable text found in the selected PDF.")
            self.status_label.setText("No text found in PDF")
            return
        
        # Store page count for navigation
        self.total_pages = len(pages)
        self.current_page = 0
            
        # Update UI
        self.is_playing = True
        self.is_paused = False
        self.play_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.resume_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        
        # Update navigation buttons
        self.update_navigation_buttons()
        
        # Start playback
        self.tts.start(pages)
    
    def pause_playback(self):
        """Pause the playback"""
        self.logger.info("TTSWidget", "Pausing playback")
        
        if self.is_playing and not self.is_paused:
            self.is_paused = True
            self.pause_btn.setEnabled(False)
            self.resume_btn.setEnabled(True)
            self.tts.pause()
    
    def resume_playback(self):
        """Resume the playback"""
        self.logger.info("TTSWidget", "Resuming playback")
        
        if self.is_playing and self.is_paused:
            self.is_paused = False
            self.pause_btn.setEnabled(True)
            self.resume_btn.setEnabled(False)
            self.tts.resume()
    
    def stop_playback(self):
        """Stop the playback"""
        self.logger.info("TTSWidget", "Stopping playback")
        
        if self.is_playing:
            self.is_playing = False
            self.is_paused = False
            self.play_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)
            self.resume_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            self.progress_bar.setValue(0)
            
            # Reset navigation buttons
            self.rewind_btn.setEnabled(False)
            self.skip_btn.setEnabled(False)
            self.rewind_btn.setToolTip("Go to previous page")
            self.skip_btn.setToolTip("Skip to next page")
            
            self.tts.stop()
            
            # Clean up temp files
            self.tts.cleanup_temp_files()
    
    def skip_page(self):
        """Skip to the next page"""
        self.logger.info("TTSWidget", "Skipping to next page")
        if self.is_playing:
            self.tts.skip()
            # Update navigation buttons after a short delay to allow TTS state to update
            QTimer.singleShot(100, self.update_navigation_buttons)
    
    def rewind_page(self):
        """Go back to the previous page"""
        self.logger.info("TTSWidget", "Rewinding to previous page")
        if self.is_playing:
            self.tts.rewind()
            # Update navigation buttons after a short delay to allow TTS state to update
            QTimer.singleShot(100, self.update_navigation_buttons)
    
    def update_progress(self, progress):
        """Update the progress bar"""
        if self.is_playing:
            self.progress_bar.setValue(int(progress * 100))
            # Update navigation buttons as playback progresses
            self.update_navigation_buttons()
    
    def update_status(self, status_text):
        """Update the status label"""
        self.status_label.setText(status_text)
    
    def update_navigation_buttons(self):
        """Update the state of navigation buttons based on current playback position"""
        if not self.is_playing or self.total_pages <= 1:
            # Disable both buttons if not playing or only one page
            self.rewind_btn.setEnabled(False)
            self.skip_btn.setEnabled(False)
            return
        
        # Get current page from TTS engine
        try:
            current_page_index = self.tts.current_audio_index if hasattr(self.tts, 'current_audio_index') else 0
            
            # Enable/disable previous button
            self.rewind_btn.setEnabled(current_page_index > 0)
            
            # Enable/disable next button  
            self.skip_btn.setEnabled(current_page_index < self.total_pages - 1)
            
            # Update tooltips with page info
            self.rewind_btn.setToolTip(f"Go to previous page ({current_page_index}/{self.total_pages})" if current_page_index > 0 else "No previous page")
            self.skip_btn.setToolTip(f"Skip to next page ({current_page_index + 2}/{self.total_pages})" if current_page_index < self.total_pages - 1 else "No next page")
            
        except Exception as e:
            self.logger.warning("TTSWidget", f"Error updating navigation buttons: {e}")
            # Fallback to safe state
            self.rewind_btn.setEnabled(False)
            self.skip_btn.setEnabled(False)
    
    def playback_complete(self, message):
        """Handle playback completion"""
        self.logger.info("TTSWidget", "Playback complete")
        
        # Reset UI
        self.is_playing = False
        self.is_paused = False
        self.play_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.resume_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        
        # Reset navigation buttons
        self.rewind_btn.setEnabled(False)
        self.skip_btn.setEnabled(False)
        self.rewind_btn.setToolTip("Go to previous page")
        self.skip_btn.setToolTip("Skip to next page")
        
        # Clean up temp files
        self.tts.cleanup_temp_files()
        
        self.status_label.setText(message)
        self.progress_bar.setValue(100)
        
    def closeEvent(self, event):
        """Clean up when widget is closed"""
        # Stop any active playback
        if self.is_playing:
            self.tts.stop()
            self.tts.cleanup_temp_files()
        event.accept()
