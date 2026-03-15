#!/usr/bin/env python3
# AnimatedProgressDialog.py - PyQt version of animated progress dialog

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget
)
from PyQt6.QtCore import Qt, QTimer, QPointF, pyqtSignal, QThread, QObject
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QPainterPath

class SpinnerThread(QThread):
    """Emits `tick()` every `interval_ms` milliseconds, in its own thread."""
    tick = pyqtSignal()

    def __init__(self, interval_ms: int = 100):
        super().__init__()
        self.interval = interval_ms
        self._running = True

    def run(self):
        while self._running:
            # Sleep entirely in this background thread
            QThread.msleep(self.interval)
            # Emit the tick back into the GUI thread
            self.tick.emit()

    def stop(self):
        self._running = False


class AnimatedProgressDialog(QDialog):
    """Dialog with animated spinner for operations with indeterminate progress
    
    This dialog implements singleton pattern to ensure only one progress dialog
    is active at a time, preventing multiple overlapping dialogs.
    """
    
    # Class variable to track the active instance
    _active_instance = None
    
    # Add cancelled signal that can be connected to
    cancelled = pyqtSignal()
    operation_completed = pyqtSignal(object)  # Emitted when threaded operation completes
    operation_failed = pyqtSignal(str)        # Emitted when threaded operation fails
    
    @classmethod
    def get_instance(cls, parent=None, title="Working...", message="Please wait..."):
        """Get the singleton instance, creating it if necessary"""
        if cls._active_instance is None or not cls._active_instance.isVisible():
            # Create new instance
            cls._active_instance = cls._create_new_instance(parent, title, message)
        else:
            # Update existing instance
            cls._active_instance.setWindowTitle(title)
            cls._active_instance.update_message(message)
            
        return cls._active_instance
    
    @classmethod
    def _create_new_instance(cls, parent=None, title="Working...", message="Please wait..."):
        """Create a new instance directly (bypasses singleton logic)"""
        from PyQt6.QtWidgets import QDialog
        instance = QDialog.__new__(cls)  # Use QDialog.__new__ for Qt classes
        instance._initialized = False  # Set this before calling __init__
        instance.__init__(parent, title, message)
        return instance
    
    def __new__(cls, parent=None, title="Working...", message="Please wait..."):
        # Route through get_instance for singleton behavior
        return cls.get_instance(parent, title, message)
    
    def __init__(self, parent=None, title="Working...", message="Please wait..."):
        # Prevent re-initialization of existing instance
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        # Call super().__init__ FIRST, before setting _initialized
        super().__init__(parent)
        
        # Mark as initialized after super class is properly initialized
        self._initialized = True
        
        self.setWindowTitle(title)
        self.setFixedSize(400, 320)  # Fixed size to prevent growing/shrinking
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        
        # Worker thread for long-running operations
        self.worker_thread = None
        
        # Remove window decoration if desired
        # self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        # Spinner setup
        self.spinner_positions = 8
        self.spinner_index = 0
        self.radius = 40
        self.dot_radius = 7
        
        # Create main layout with fixed spacing
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)  # Fixed spacing between elements
        
        # Title label with fixed height
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 15pt; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFixedHeight(30)  # Fixed height for consistent layout
        main_layout.addWidget(title_label)
        
        # Message label with fixed height to prevent layout changes
        self.message_label = QLabel(message)
        self.message_label.setStyleSheet("font-size: 12pt;")
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.setWordWrap(True)  # Allow text wrapping
        self.message_label.setFixedHeight(60)  # Fixed height for consistent layout
        main_layout.addWidget(self.message_label)
        
        # Fixed-size spinner widget
        self.spinner_widget = SpinnerWidget(self)
        self.spinner_widget.setFixedSize(120, 120)  # Fixed size animation area
        main_layout.addWidget(self.spinner_widget, 0, Qt.AlignmentFlag.AlignCenter)  # Center without stretch
        
        # Cancel button with fixed height
        button_layout = QHBoxLayout()
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setFixedHeight(30)  # Fixed button height
        self.cancel_button.clicked.connect(self._on_cancel)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)
        
        # Add spacing to fill remaining space consistently
        main_layout.addStretch()
        
        # --- Replace the QTimer with a dedicated thread! ---
        self._spinner_thread = SpinnerThread(interval_ms=100)
        # Connect the spinner thread back to the GUI slot
        self._spinner_thread.tick.connect(self.update_spinner)
        self._spinner_thread.start()
    
    def update_spinner(self):
        """Update spinner animation frame"""
        self.spinner_widget.next_frame()
    
    def update_message(self, message):
        """Update the message text"""
        self.message_label.setText(message)
    
    @classmethod
    def get_or_create_instance(cls, parent=None, title="Working...", message="Please wait..."):
        """Get the existing instance or create a new one if none exists"""
        return cls.get_instance(parent, title, message)
    
    @classmethod
    def close_existing_instance(cls):
        """Force close any existing instance"""
        if cls._active_instance is not None:
            cls._active_instance.close()
            cls._active_instance = None
    
    @classmethod
    def has_active_instance(cls):
        """Check if there's an active instance"""
        return cls._active_instance is not None and cls._active_instance.isVisible()
    

    
    def _on_operation_finished(self, result):
        """Handle completion of threaded operation"""
        self.operation_completed.emit(result)
        
    def _on_operation_error(self, error_message):
        """Handle error in threaded operation"""
        self.operation_failed.emit(error_message)
    
    def _on_cancel(self):
        """Handle cancel button click"""
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.cancel()
            self.worker_thread.wait(1000)  # Wait up to 1 second for cleanup
            
        self.cancelled.emit()
        self.close()
    
    def closeEvent(self, event):
        # 1) Stop your spinner thread first
        if hasattr(self, "_spinner_thread"):
            self._spinner_thread.stop()
            self._spinner_thread.wait()

        # 2) Then stop any worker thread
        if getattr(self, "worker_thread", None) and self.worker_thread.isRunning():
            self.worker_thread.cancel()
            self.worker_thread.wait(1000)

        # 3) Clear the singleton
        if AnimatedProgressDialog._active_instance is self:
            AnimatedProgressDialog._active_instance = None

        super().closeEvent(event)



class SpinnerWidget(QWidget):
    """Custom widget that draws an animated spinner"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(120, 120)  # Fixed size to prevent any resizing
        
        self.spinner_positions = 8
        self.current_position = 0
        self.dot_colors = []
        
        # Generate colors for dots (from darker to lighter)
        base_color = QColor(0, 120, 215)  # Windows blue
        for i in range(self.spinner_positions):
            # Make alpha fade from 255 (opaque) to 40 (mostly transparent)
            alpha = 255 - (i * 215 // self.spinner_positions)
            color = QColor(base_color)
            color.setAlpha(alpha)
            self.dot_colors.append(color)
    
    def next_frame(self):
        """Advance to next animation frame"""
        self.current_position = (self.current_position + 1) % self.spinner_positions
        self.update()  # Request a repaint
    
    def paintEvent(self, event):
        """Draw the spinner"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate center point
        center_x = self.width() / 2
        center_y = self.height() / 2
        radius = min(center_x, center_y) - 10
        
        # Draw each dot
        for i in range(self.spinner_positions):
            # Calculate position in the circle
            angle = 2 * 3.14159 * i / self.spinner_positions
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            
            # Get color for this position
            color_index = (i + self.current_position) % self.spinner_positions
            color = self.dot_colors[color_index]
            
            # Draw dot
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(QPointF(x, y), 7, 7)


# Add math import at the top level so it's available in the SpinnerWidget class
import math
