#!/usr/bin/env python3
# progress_dialog.py - Progress dialog for PDF Utility

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QProgressBar,
    QPushButton, QLabel
)
from PyQt6.QtCore import Qt

class DualProgressDialog(QDialog):
    """
    A dialog showing two progress bars:
    - One for overall progress
    - One for current file/operation progress
    """
    
    def __init__(self, parent=None, title="Operation in Progress", message="Please wait...", allow_cancel=True):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(450)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.cancelled = False
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        # Message label
        self.message_label = QLabel(message)
        self.message_label.setWordWrap(True)
        layout.addWidget(self.message_label)
        
        # Overall progress section
        layout.addSpacing(10)
        layout.addWidget(QLabel("Overall Progress:"))
        
        self.overall_progress_bar = QProgressBar()
        self.overall_progress_bar.setRange(0, 100)
        layout.addWidget(self.overall_progress_bar)
        
        self.overall_status_label = QLabel("Starting...")
        layout.addWidget(self.overall_status_label)
        
        # Current progress section
        layout.addSpacing(10)
        layout.addWidget(QLabel("Current Progress:"))
        
        self.current_progress_bar = QProgressBar()
        self.current_progress_bar.setRange(0, 100)
        layout.addWidget(self.current_progress_bar)
        
        self.current_status_label = QLabel("Preparing...")
        layout.addWidget(self.current_status_label)
        
        # Cancel button (if allowed)
        if allow_cancel:
            layout.addSpacing(10)
            button_layout = QHBoxLayout()
            
            self.cancel_button = QPushButton("Cancel")
            self.cancel_button.clicked.connect(self.cancel)
            button_layout.addStretch()
            button_layout.addWidget(self.cancel_button)
            button_layout.addStretch()
            
            layout.addLayout(button_layout)
        
        # Show the dialog
        self.show()
    
    def update_overall_progress(self, progress):
        """Update the overall progress bar (percentage value)"""
        self.overall_progress_bar.setValue(int(progress))
    
    def update_current_progress(self, progress):
        """Update the current progress bar (percentage value)"""
        self.current_progress_bar.setValue(int(progress))
    
    def update_overall_status(self, status):
        """Update the overall status text"""
        self.overall_status_label.setText(status)
    
    def update_current_status(self, status):
        """Update the current status text"""
        self.current_status_label.setText(status)
    
    def update_message(self, message):
        """Update the main message"""
        self.message_label.setText(message)
    
    def reset_current_progress(self):
        """Reset the current progress bar and status"""
        self.current_progress_bar.setValue(0)
        self.current_status_label.setText("Preparing...")
    
    def cancel(self):
        """Handle cancel button click"""
        self.cancelled = True
        self.overall_status_label.setText("Cancelling...")
    
    def is_cancelled(self):
        """Check if operation was cancelled"""
        return self.cancelled
    
    def close(self):
        """Close the dialog"""
        self.accept()

class QuadrupleProgressDialog(DualProgressDialog):
    """
    An extended progress dialog with four progress bars:
    - Overall progress
    - Current file progress
    - Sub-operation 1 progress
    - Sub-operation 2 progress
    """
    
    def __init__(self, parent=None, title="Operation in Progress", message="Please wait...", allow_cancel=True):
        # Initialize with the base dialog
        super().__init__(parent, title, message, allow_cancel=False)  # We'll add our own cancel button
        
        # Get the layout
        layout = self.layout()
        
        # Add sub-operation 1 progress
        layout.addSpacing(10)
        layout.addWidget(QLabel("Sub-operation 1:"))
        
        self.sub1_progress_bar = QProgressBar()
        self.sub1_progress_bar.setRange(0, 100)
        layout.addWidget(self.sub1_progress_bar)
        
        self.sub1_status_label = QLabel("Waiting...")
        layout.addWidget(self.sub1_status_label)
        
        # Add sub-operation 2 progress
        layout.addSpacing(10)
        layout.addWidget(QLabel("Sub-operation 2:"))
        
        self.sub2_progress_bar = QProgressBar()
        self.sub2_progress_bar.setRange(0, 100)
        layout.addWidget(self.sub2_progress_bar)
        
        self.sub2_status_label = QLabel("Waiting...")
        layout.addWidget(self.sub2_status_label)
        
        # Add cancel button if allowed
        if allow_cancel:
            layout.addSpacing(10)
            button_layout = QHBoxLayout()
            
            self.cancel_button = QPushButton("Cancel")
            self.cancel_button.clicked.connect(self.cancel)
            button_layout.addStretch()
            button_layout.addWidget(self.cancel_button)
            button_layout.addStretch()
            
            layout.addLayout(button_layout)
        
        # Reset the size
        self.adjustSize()
    
    def update_sub1_progress(self, progress):
        """Update the sub-operation 1 progress bar"""
        self.sub1_progress_bar.setValue(int(progress))
    
    def update_sub2_progress(self, progress):
        """Update the sub-operation 2 progress bar"""
        self.sub2_progress_bar.setValue(int(progress))
    
    def update_sub1_status(self, status):
        """Update the sub-operation 1 status text"""
        self.sub1_status_label.setText(status)
    
    def update_sub2_status(self, status):
        """Update the sub-operation 2 status text"""
        self.sub2_status_label.setText(status)
    
    def reset_sub1_progress(self):
        """Reset the sub-operation 1 progress and status"""
        self.sub1_progress_bar.setValue(0)
        self.sub1_status_label.setText("Waiting...")
    
    def reset_sub2_progress(self):
        """Reset the sub-operation 2 progress and status"""
        self.sub2_progress_bar.setValue(0)
        self.sub2_status_label.setText("Waiting...")
