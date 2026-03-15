# editor/renderers/pyqt_frame_helper.py

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import tempfile
from pathlib import Path

# Dict to store global references
_global_refs = {
    'qt_app': None
}

# Check if PyQt6 is available
try:
    from PyQt6.QtCore import QUrl, QTimer, QSize, Qt
    from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QMainWindow
    from PyQt6.QtGui import QPalette, QColor
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

class PyQtWebFrame(ttk.Frame):
    """
    A Tkinter frame that embeds a PyQt WebEngine browser for HTML rendering.
    Uses a fallback approach where the HTML is saved to a file and displayed
    in a separate window that only appears when needed.
    """
    
    def __init__(self, parent, html_content="", html_path=None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.parent = parent
        self.html_content = html_content
        self.html_path = html_path
        self.temp_file = None
        self.preview_window = None
        self.qt_window = None
        
        # Create a preview placeholder in the Tkinter frame
        self.placeholder = ttk.Label(self, 
            text="HTML Preview\n(Click 'Show Preview' to view in external window)",
            justify="center")
        self.placeholder.pack(expand=True, fill="both")
        
        # Add a preview button
        self.preview_button = ttk.Button(self, 
            text="Show Preview", 
            command=self._show_preview)
        self.preview_button.pack(pady=10)
        
        if not PYQT_AVAILABLE:
            self.placeholder.config(text="PyQt WebEngine not available.\nInstall PyQt6 and PyQt6-WebEngine.")
            self.preview_button.config(state="disabled")
            return
            
        try:
            # Create temp file for the content
            if html_content:
                self._create_temp_html_file()
        except Exception as e:
            print(f"PyQt initialization failed: {e}")
            import traceback
            traceback.print_exc()
            self._create_fallback_widget()
            
        # Bind events
        self.bind("<Configure>", self._on_configure)
        self.bind("<Destroy>", self._on_destroy)
    
    def _show_preview(self):
        """Show the HTML preview in a separate window."""
        if not PYQT_AVAILABLE:
            return
        
        try:
            # Initialize PyQt if needed
            self._initialize_pyqt()
            
            # Create or update temp file
            if not self.temp_file and self.html_content:
                self._create_temp_html_file()
            
            # Create a preview window if it doesn't exist
            if self.preview_window is None:
                self._create_preview_window()
            
            # Load the content
            if self.html_path:
                self.preview_window.load(QUrl.fromLocalFile(self.html_path))
            elif self.temp_file:
                self.preview_window.load(QUrl.fromLocalFile(self.temp_file))
            else:
                self.preview_window.setHtml(self.html_content)
                
            # Show the window
            self.qt_window.show()
            self.preview_button.config(text="Refresh Preview")
                
        except Exception as e:
            print(f"Error showing preview: {e}")
            import traceback
            traceback.print_exc()
_global_refs = {
    'qt_app': None
}

# Check if PyQt6 is available
try:
    from PyQt6.QtCore import QUrl, QTimer, QSize, Qt
    from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QMainWindow
    from PyQt6.QtGui import QPalette, QColor
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

class PyQtWebFrame(ttk.Frame):
    """
    A Tkinter frame that embeds a PyQt WebEngine browser for HTML rendering.
    Uses a fallback approach where the HTML is saved to a file and displayed
    in a separate window that only appears when needed.
    """
    
    def __init__(self, parent, html_content="", html_path=None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.parent = parent
        self.html_content = html_content
        self.html_path = html_path
        self.temp_file = None
        self.preview_window = None
        self.qt_window = None
        
        # Create a preview placeholder in the Tkinter frame
        self.placeholder = ttk.Label(self, 
            text="HTML Preview\n(Click 'Show Preview' to view in external window)",
            justify="center")
        self.placeholder.pack(expand=True)
        
        # Add a preview button
        self.preview_button = ttk.Button(self, 
            text="Show Preview", 
            command=self._show_preview)
        self.preview_button.pack(pady=10)
        
        if not PYQT_AVAILABLE:
            self.placeholder.config(text="PyQt WebEngine not available.\nInstall PyQt6 and PyQt6-WebEngine.")
            self.preview_button.config(state="disabled")
            return
            
        try:
            # Create temp file for the content
            if html_content:
                self._create_temp_html_file()
        except Exception as e:
            print(f"PyQt initialization failed: {e}")
            import traceback
            traceback.print_exc()
            self._create_fallback_widget()
            
        # Bind events
        self.bind("<Configure>", self._on_configure)
        self.bind("<Destroy>", self._on_destroy)
    
    def _show_preview(self):
        """Show the HTML preview in a separate window."""
        if not PYQT_AVAILABLE:
            return
        
        try:
            # Initialize PyQt if needed
            self._initialize_pyqt()
            
            # Create or update temp file
            if not self.temp_file and self.html_content:
                self._create_temp_html_file()
            
            # Create a preview window if it doesn't exist
            if self.preview_window is None:
                self._create_preview_window()
            
            # Load the content
            if self.html_path:
                self.preview_window.load(QUrl.fromLocalFile(self.html_path))
            elif self.temp_file:
                self.preview_window.load(QUrl.fromLocalFile(self.temp_file))
            else:
                self.preview_window.setHtml(self.html_content)
                
            # Show the window
            self.qt_window.show()
            self.preview_button.config(text="Refresh Preview")
                
        except Exception as e:
            print(f"Error showing preview: {e}")
            import traceback
            traceback.print_exc()
            traceback.print_exc()
            
    def _initialize_pyqt(self):
        """Initialize PyQt application if not already done."""
        # Use global dict reference for thread safety
        if _global_refs['qt_app'] is None:
            # Check if QApplication already exists
            if QApplication.instance() is None:
                # Pass proper argv list with program name to QApplication
                argv = sys.argv if len(sys.argv) > 0 else ["PDFSplitter"]
                
                # Create application with NoQuitOnLastWindowClosed = False
                # to prevent app from quitting when windows are closed
                _global_refs['qt_app'] = QApplication(argv)
                _global_refs['qt_app'].setQuitOnLastWindowClosed(False)
            else:
                _global_refs['qt_app'] = QApplication.instance()
                
        # Use the global instance
        self.qt_app = _global_refs['qt_app']
    
    def _create_preview_window(self):
        """Create a standalone PyQt WebEngine window for preview."""
        if not PYQT_AVAILABLE:
            return
            
        # Create a QWebEngineView in a separate window
        from PyQt6.QtWidgets import QMainWindow
        
        # Create main window
        window = QMainWindow()
        window.setWindowTitle("HTML Preview")
        window.resize(800, 600)
        
        # Create web view
        self.preview_window = QWebEngineView()
        window.setCentralWidget(self.preview_window)
        
        # Set background color
        palette = self.preview_window.palette()
        palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        self.preview_window.setPalette(palette)
        
        # Update button text when window is closed
        def on_window_closed():
            self.preview_button.config(text="Show Preview")
            
        window.closeEvent = lambda event: on_window_closed()
        
        # Keep reference to the window to prevent garbage collection
        self.qt_window = window
    
    def _on_configure(self, event):
        """Update preview button size when frame is resized."""
        if event.widget == self:
            # Adjust placeholder size
            self.placeholder.config(wraplength=event.width-20)
    
    def _update_placeholder_size(self):
        """Update the size of the placeholder."""
        width = self.winfo_width()
        if width > 20:
            self.placeholder.config(wraplength=width-20)
    
    def _on_configure(self, event):
        """Handle resize events."""
        if event.widget == self:
            self._update_placeholder_size()
    
    def _create_temp_html_file(self):
        """Create a temporary HTML file for the content."""
        if self.temp_file:
            try:
                os.unlink(self.temp_file)
            except:
                pass
        
        # Create temp file
        fd, self.temp_file = tempfile.mkstemp(suffix='.html', text=True)
        
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(self.html_content)
    
    def _create_fallback_widget(self):
        """Create a fallback widget if PyQt is not available."""
        # We've already created a placeholder, just update it
        self.placeholder.config(text="PyQt WebEngine not available.\nInstall PyQt6 and PyQt6-WebEngine.")
        self.preview_button.config(state="disabled")
    
    def _ensure_visibility(self, success=True):
        """Ensure the web view is visible after content loads."""
        if not success or not hasattr(self, "web_view") or self.web_view is None:
            return
            
        # Make sure the web view is properly sized and visible
        self._update_size()
        
        # On Windows, use native API to ensure visibility
        if sys.platform == "win32" and hasattr(self, "tk_win_id"):
            try:
                import ctypes
                from ctypes import windll
                
                qt_win_id = self.web_view.winId()
                
                # Set visibility
                HWND_TOP = 0
                SWP_SHOWWINDOW = 0x0040
                SWP_NOACTIVATE = 0x0010
                SWP_NOMOVE = 0x0002
                SWP_NOSIZE = 0x0001
                
                # Bring to top without activating
                windll.user32.SetWindowPos(
                    int(qt_win_id), HWND_TOP, 
                    0, 0, 0, 0,
                    SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW | SWP_NOACTIVATE
                )
                
                # Make sure child window is visible
                windll.user32.ShowWindow(int(qt_win_id), 5)  # SW_SHOW = 5
            except Exception as e:
                print(f"Error ensuring window visibility: {e}")
                
    def _on_destroy(self, event):
        """Clean up resources when the frame is destroyed."""
        # Only clean up if this is the top-level frame being destroyed
        if event.widget == self:
            # Stop timers first
            if hasattr(self, "_check_loaded_timer") and self._check_loaded_timer is not None:
                try:
                    self._check_loaded_timer.stop()
                    self._check_loaded_timer = None
                except:
                    pass
            
            # Delete temporary file
            if self.temp_file and os.path.exists(self.temp_file):
                try:
                    os.unlink(self.temp_file)
                except:
                    pass
            
            # Detach Qt widgets before closing to prevent Qt errors
            if sys.platform == "win32" and hasattr(self, "qt_container") and self.qt_container is not None:
                try:
                    import ctypes
                    from ctypes import windll
                    
                    # Get container window handle
                    qt_win_id = self.qt_container.winId()
                    
                    # Remove parent relationship (set parent to desktop)
                    windll.user32.SetParent(int(qt_win_id), 0)
                except:
                    pass
            
            # Close Qt widgets - use deleteLater for thread safety
            if hasattr(self, "web_view") and self.web_view is not None:
                try:
                    self.web_view.stop()  # Stop loading
                    self.web_view.deleteLater()
                    self.web_view = None
                except:
                    pass
            
            if hasattr(self, "qt_container") and self.qt_container is not None:
                try:
                    self.qt_container.deleteLater()
                    self.qt_container = None
                except:
                    pass
    
    def set_html(self, html_content):
        """Set new HTML content for the web view."""
        self.html_content = html_content
        
        if not hasattr(self, "web_view") or self.web_view is None:
            return
            
        try:
            # Always use file-based approach for better thread safety
            # Update the temporary file
            if self.temp_file:
                with open(self.temp_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
            else:
                # Create a new temp file
                self._create_temp_html_file()
                
            # Use QTimer to schedule loading for thread safety
            # We can't connect to signals directly as it may cause threading issues
            def load_content():
                if hasattr(self, "web_view") and self.web_view:
                    self.web_view.load(QUrl.fromLocalFile(self.temp_file))
            
            QTimer.singleShot(10, load_content)
            
        except Exception as e:
            print(f"Error setting HTML content: {e}")
            import traceback
            traceback.print_exc()
    
    def load_url(self, url):
        """Load a URL in the web view."""
        if not hasattr(self, "web_view") or self.web_view is None:
            return
            
        self.web_view.load(QUrl(url))
