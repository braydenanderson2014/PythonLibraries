#!/usr/bin/env python3
# ProgressDialog.py - PyQt version of progress dialogs

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QProgressBar, QWidget
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal

class ProgressDialog(QDialog):
    """Base progress dialog with progress bar and cancel button"""
    
    cancelled = pyqtSignal()
    
    def __init__(self, parent=None, title="Processing", message="Operation in progress..."):
        """Create a progress dialog with a progress bar and cancel button"""
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(500, 250)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        
        # Flag to track cancellation
        self._cancelled = False
        
        # Create main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Create message label
        self.message_label = QLabel(message)
        self.message_label.setWordWrap(True)
        main_layout.addWidget(self.message_label)
        main_layout.addSpacing(15)
        
        # Create progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)
        
        # Create status label
        self.status_label = QLabel("Initializing...")
        main_layout.addWidget(self.status_label)
        main_layout.addSpacing(20)
        
        # Create cancel button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.handle_cancel)
        button_layout.addWidget(self.cancel_button)
        
        main_layout.addLayout(button_layout)
    
    def set_progress(self, value, maximum=100):
        """Update the progress bar"""
        if maximum > 0:
            self.progress_bar.setMaximum(maximum)
            self.progress_bar.setValue(value)
    
    def update_progress(self, current, total):
        """Update the progress bar based on current and total values"""
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress_bar.setValue(percentage)
    
    def update_message(self, message):
        """Update the main message"""
        self.message_label.setText(message)
    
    def update_status(self, status):
        """Update the status text"""
        self.status_label.setText(status)
    
    def handle_cancel(self):
        """Handle cancel button click"""
        self._cancelled = True
        self.cancelled.emit()
    
    def is_cancelled(self):
        """Check if the operation was cancelled"""
        return self._cancelled
    
    def close_dialog(self):
        """Close the dialog"""
        self.accept()


class DualProgressDialog(ProgressDialog):
    """Progress dialog with two progress indicators"""
    
    def __init__(self, parent=None, title="Processing", message="Operation in progress..."):
        super().__init__(parent, title, message)
        
        # Extend the layout for additional progress bars
        layout = self.layout()
        
        # Add second progress bar
        self.progress_label2 = QLabel("Progress 2:")
        layout.insertWidget(3, self.progress_label2)
        
        self.progress_bar2 = QProgressBar()
        self.progress_bar2.setRange(0, 100)
        self.progress_bar2.setValue(0)
        layout.insertWidget(4, self.progress_bar2)
        
        # Rename the first progress label
        self.progress_label1 = QLabel("Progress 1:")
        layout.insertWidget(1, self.progress_label1)
    
    def set_progress_labels(self, label1, label2):
        """Set the labels for the progress bars"""
        self.progress_label1.setText(label1)
        self.progress_label2.setText(label2)
    
    def update_progress1(self, current, total):
        """Update the first progress bar"""
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress_bar.setValue(percentage)
    
    def update_progress2(self, current, total):
        """Update the second progress bar"""
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress_bar2.setValue(percentage)


class TripleProgressDialog(DualProgressDialog):
    """Progress dialog with three progress indicators"""
    
    def __init__(self, parent=None, title="Processing", message="Operation in progress..."):
        super().__init__(parent, title, message)
        
        # Extend the layout for the third progress bar
        layout = self.layout()
        
        # Add third progress bar
        self.progress_label3 = QLabel("Progress 3:")
        layout.insertWidget(5, self.progress_label3)
        
        self.progress_bar3 = QProgressBar()
        self.progress_bar3.setRange(0, 100)
        self.progress_bar3.setValue(0)
        layout.insertWidget(6, self.progress_bar3)
    
    def set_progress_labels(self, label1, label2, label3):
        """Set the labels for the progress bars"""
        super().set_progress_labels(label1, label2)
        self.progress_label3.setText(label3)
    
    def update_progress3(self, current, total):
        """Update the third progress bar"""
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress_bar3.setValue(percentage)


class QuadrupleProgressDialog(TripleProgressDialog):
    """Progress dialog with four progress indicators"""
    
    def __init__(self, parent=None, title="Processing", message="Operation in progress..."):
        super().__init__(parent, title, message)
        
        # Add fourth progress bar
        layout = self.layout()
        
        self.progress_label4 = QLabel("Progress 4:")
        layout.insertWidget(7, self.progress_label4)
        
        self.progress_bar4 = QProgressBar()
        self.progress_bar4.setRange(0, 100)
        self.progress_bar4.setValue(0)
        layout.insertWidget(8, self.progress_bar4)
    
    def set_progress_labels(self, label1, label2, label3, label4):
        """Set the labels for the progress bars"""
        super().set_progress_labels(label1, label2, label3)
        self.progress_label4.setText(label4)
    
    def update_progress4(self, current, total):
        """Update the fourth progress bar"""
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress_bar4.setValue(percentage)
