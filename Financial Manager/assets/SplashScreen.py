"""
Modern Splash Screen Component for Financial Manager
Inspired by Adobe-style loading screens with customizable features.

Features:
- Background image support
- Animated progress bar
- Optional percentage display
- Optional status message display
- Smooth animations
- Fully modular and reusable

Usage:
    splash = SplashScreen(
        image_path="path/to/splash.png",
        show_percentage=True,
        show_message=True,
        app_name="Financial Manager",
        version="1.0.0"
    )
    splash.show()
    
    # Update progress
    splash.set_progress(50, "Loading database...")
    
    # Close when done
    splash.finish()
"""

from PyQt6.QtWidgets import (
    QSplashScreen, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QProgressBar, QApplication
)
from PyQt6.QtCore import Qt, QTimer, QRect, QPointF, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QPen, QLinearGradient
import os


class ModernProgressBar(QWidget):
    """
    Custom progress bar with smooth animations and gradient effects.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._progress = 0
        self._target_progress = 0
        self.setFixedHeight(8)
        self.setMinimumWidth(400)
        
        # Animation for smooth progress updates
        self.animation = QPropertyAnimation(self, b"progress")
        self.animation.setDuration(300)  # 300ms for smooth transition
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Colors
        self.bg_color = QColor(40, 40, 40, 180)
        self.progress_gradient_start = QColor(0, 122, 255)  # Blue
        self.progress_gradient_end = QColor(0, 180, 255)    # Light blue
        self.border_color = QColor(60, 60, 60)
    
    @pyqtProperty(float)
    def progress(self):
        return self._progress
    
    @progress.setter
    def progress(self, value):
        self._progress = value
        self.update()
    
    def set_value(self, value):
        """Set progress value with animation (0-100)"""
        value = max(0, min(100, value))
        self._target_progress = value
        self.animation.stop()
        self.animation.setStartValue(self._progress)
        self.animation.setEndValue(value)
        self.animation.start()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        
        # Draw background with rounded corners
        painter.setPen(QPen(self.border_color, 1))
        painter.setBrush(self.bg_color)
        painter.drawRoundedRect(rect, 4, 4)
        
        # Draw progress with gradient
        if self._progress > 0:
            progress_width = int((rect.width() - 2) * (self._progress / 100))
            progress_rect = QRect(1, 1, progress_width, rect.height() - 2)
            
            # Convert QPoint to QPointF for QLinearGradient
            start_point = QPointF(progress_rect.topLeft())
            end_point = QPointF(progress_rect.topRight())
            gradient = QLinearGradient(start_point, end_point)
            gradient.setColorAt(0, self.progress_gradient_start)
            gradient.setColorAt(1, self.progress_gradient_end)
            
            painter.setBrush(gradient)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(progress_rect, 3, 3)
        
        # Ensure painter is properly ended
        painter.end()


class SplashScreen(QSplashScreen):
    """
    Modern splash screen with loading progress, similar to Adobe applications.
    
    Args:
        image_path (str): Path to background image. If None, uses default gradient.
        show_percentage (bool): Show percentage text below progress bar
        show_message (bool): Show status message below progress bar
        app_name (str): Application name to display
        version (str): Version string to display
        width (int): Splash screen width (default: 600)
        height (int): Splash screen height (default: 400)
    """
    
    def __init__(self, 
                 image_path=None,
                 show_percentage=True,
                 show_message=True,
                 app_name="Financial Manager",
                 version="1.0.0",
                 width=600,
                 height=400):
        
        # Create background pixmap
        pixmap = self._create_background(image_path, width, height)
        super().__init__(pixmap)
        
        self.show_percentage = show_percentage
        self.show_message = show_message
        self.app_name = app_name
        self.version = version
        self._current_message = "Initializing..."
        self._current_progress = 0
        
        # Remove window frame
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        
        # Setup UI elements
        self._setup_ui()
        
    def _create_background(self, image_path, width, height):
        """Create background pixmap from image or generate default"""
        if image_path and os.path.exists(image_path):
            # Load custom image
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                # Scale to desired size while maintaining aspect ratio
                pixmap = pixmap.scaled(
                    width, height,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation
                )
                # Crop to exact size
                if pixmap.width() > width or pixmap.height() > height:
                    x = (pixmap.width() - width) // 2
                    y = (pixmap.height() - height) // 2
                    pixmap = pixmap.copy(x, y, width, height)
                return pixmap
        
        # Create default gradient background
        pixmap = QPixmap(width, height)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Create gradient from dark blue to darker blue
        gradient = QLinearGradient(0, 0, 0, height)
        gradient.setColorAt(0, QColor(15, 32, 52))   # Dark blue
        gradient.setColorAt(1, QColor(8, 16, 28))    # Darker blue
        
        painter.fillRect(pixmap.rect(), gradient)
        painter.end()
        
        return pixmap
    
    def _setup_ui(self):
        """Setup UI elements on the splash screen"""
        # Create a container widget for proper layout
        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Spacer to push content to bottom
        layout.addStretch()
        
        # App name and version
        header_layout = QHBoxLayout()
        
        app_label = QLabel(self.app_name)
        app_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 24px;
                font-weight: bold;
                background: transparent;
            }
        """)
        header_layout.addWidget(app_label)
        
        header_layout.addStretch()
        
        version_label = QLabel(f"v{self.version}")
        version_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.6);
                font-size: 12px;
                background: transparent;
            }
        """)
        header_layout.addWidget(version_label)
        
        layout.addLayout(header_layout)
        layout.addSpacing(20)
        
        # Progress bar
        self.progress_bar = ModernProgressBar()
        layout.addWidget(self.progress_bar)
        layout.addSpacing(10)
        
        # Status indicators layout
        status_layout = QHBoxLayout()
        
        # Percentage label (optional)
        self.percentage_label = QLabel("0%")
        self.percentage_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.8);
                font-size: 11px;
                font-weight: bold;
                background: transparent;
            }
        """)
        self.percentage_label.setVisible(self.show_percentage)
        status_layout.addWidget(self.percentage_label)
        
        status_layout.addStretch()
        
        # Message label (optional)
        self.message_label = QLabel(self._current_message)
        self.message_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.7);
                font-size: 11px;
                background: transparent;
            }
        """)
        self.message_label.setVisible(self.show_message)
        status_layout.addWidget(self.message_label)
        
        layout.addLayout(status_layout)
        layout.addSpacing(10)
        
        # Copyright or additional info
        copyright_label = QLabel("© 2026 Financial Manager. All rights reserved.")
        copyright_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.4);
                font-size: 9px;
                background: transparent;
            }
        """)
        copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(copyright_label)
        
        # Set container geometry to cover splash screen
        container.setGeometry(0, 0, self.pixmap().width(), self.pixmap().height())
        container.setStyleSheet("background: transparent;")
    
    def set_progress(self, value, message=None):
        """
        Update progress bar and optionally the status message.
        
        Args:
            value (int): Progress value (0-100)
            message (str, optional): Status message to display
        """
        self._current_progress = value
        self.progress_bar.set_value(value)
        
        if self.show_percentage:
            self.percentage_label.setText(f"{int(value)}%")
        
        if message is not None and self.show_message:
            self._current_message = message
            self.message_label.setText(message)
        
        # Process events to update display
        QApplication.processEvents()
    
    def set_message(self, message):
        """
        Update only the status message without changing progress.
        
        Args:
            message (str): Status message to display
        """
        if self.show_message:
            self._current_message = message
            self.message_label.setText(message)
            QApplication.processEvents()
    
    def get_progress(self):
        """Get current progress value"""
        return self._current_progress
    
    def get_message(self):
        """Get current status message"""
        return self._current_message
    
    def finish(self, main_window=None):
        """
        Close the splash screen with fade out animation.
        
        Args:
            main_window (QWidget, optional): Main window to show after splash
        """
        if main_window:
            super().finish(main_window)
        else:
            self.close()


# Demo/Testing code
if __name__ == "__main__":
    import sys
    import time
    
    app = QApplication(sys.argv)
    
    # Create splash screen (will use default gradient since no image provided)
    splash = SplashScreen(
        image_path=None,  # Set to your image path: "splash_image.png"
        show_percentage=True,
        show_message=True,
        app_name="Financial Manager",
        version="1.0.0",
        width=600,
        height=400
    )
    
    splash.show()
    
    # Simulate loading process
    loading_steps = [
        (10, "Loading configuration..."),
        (20, "Initializing database..."),
        (35, "Loading user preferences..."),
        (50, "Setting up UI components..."),
        (65, "Loading financial data..."),
        (80, "Initializing stock tracker..."),
        (90, "Finalizing setup..."),
        (100, "Ready!")
    ]
    
    def simulate_loading():
        for progress, message in loading_steps:
            splash.set_progress(progress, message)
            time.sleep(0.5)  # Simulate work being done
            QApplication.processEvents()
        
        # Keep splash visible for a moment
        time.sleep(1)
        splash.close()
        
        # Show a simple message to indicate demo is complete
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(None, "Demo Complete", "Splash screen demo finished!")
        app.quit()
    
    # Start simulation after a brief delay
    QTimer.singleShot(500, simulate_loading)
    
    sys.exit(app.exec())
