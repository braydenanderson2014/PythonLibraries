"""
PyQt Compatibility Layer
========================

This module provides a compatibility layer between PyQt6 and PyQt5.
It attempts to import PyQt6 first, and falls back to PyQt5 with appropriate
compatibility mappings when PyQt6 is not available.

Usage:
    Instead of:
        from PyQt6.QtWidgets import QWidget, QLabel
        from PyQt6.QtCore import Qt, QTimer
        from PyQt6.QtGui import QPixmap, QIcon
    
    Use:
        from pyqt_compatibility import QtWidgets, QtCore, QtGui
        # Then use: QtWidgets.QWidget, QtCore.Qt, QtGui.QPixmap, etc.
    
    Or for backward compatibility:
        from pyqt_compatibility import *
        # This will populate the namespace with PyQt6-style imports
"""

import sys
import warnings

# Global flag to track which PyQt version we're using
USING_PYQT6 = False
USING_PYQT5 = False
PYQT_VERSION = None

def get_pyqt_version():
    """Return the PyQt version being used"""
    return PYQT_VERSION

def is_pyqt6():
    """Return True if using PyQt6"""
    return USING_PYQT6

def is_pyqt5():
    """Return True if using PyQt5"""
    return USING_PYQT5

# Try importing PyQt6 first
try:
    from PyQt6 import QtWidgets, QtCore, QtGui
    try:
        from PyQt6 import QtOpenGL
    except ImportError:
        QtOpenGL = None
        warnings.warn("PyQt6.QtOpenGL not available", ImportWarning)
    
    try:
        from PyQt6 import QtQuick
    except ImportError:
        QtQuick = None
        warnings.warn("PyQt6.QtQuick not available", ImportWarning)
    
    USING_PYQT6 = True
    PYQT_VERSION = "PyQt6"
    
    print("✅ Using PyQt6 for GUI")
    
except ImportError as e:
    print(f"⚠️ PyQt6 not available: {e}")
    
    # Fallback to PyQt5
    try:
        from PyQt5 import QtWidgets, QtCore, QtGui
        try:
            from PyQt5 import QtOpenGL
        except ImportError:
            QtOpenGL = None
            warnings.warn("PyQt5.QtOpenGL not available", ImportWarning)
        
        try:
            from PyQt5 import QtQuick
        except ImportError:
            QtQuick = None
            warnings.warn("PyQt5.QtQuick not available", ImportWarning)
        
        USING_PYQT5 = True
        PYQT_VERSION = "PyQt5"
        
        print("✅ Using PyQt5 for GUI (PyQt6 fallback)")
        
        # PyQt5 compatibility adjustments
        # In PyQt6, some enums moved from QtCore to other modules
        # We need to maintain PyQt6-style access patterns
        
        # Ensure Qt enums are available in the expected locations
        if hasattr(QtCore.Qt, 'AlignmentFlag'):
            # PyQt6 style - enums are in their own classes
            pass
        else:
            # PyQt5 style - maintain compatibility by ensuring expected names exist
            # Most code should work without changes, but we can add specific fixes here
            pass
            
    except ImportError as e:
        print(f"❌ PyQt5 also not available: {e}")
        print("🔄 Falling back to tkinter for basic GUI functionality")
        
        # Create dummy modules for non-GUI builds
        class DummyModule:
            def __getattr__(self, name):
                raise ImportError(f"Neither PyQt6 nor PyQt5 available. Cannot use {name}")
        
        QtWidgets = DummyModule()
        QtCore = DummyModule()
        QtGui = DummyModule()
        QtOpenGL = None
        QtQuick = None
        
        PYQT_VERSION = None

# For backward compatibility, populate the namespace with common PyQt6 imports
# This allows existing code to work with minimal changes
if USING_PYQT6 or USING_PYQT5:
    # Common widgets
    QWidget = QtWidgets.QWidget
    QApplication = QtWidgets.QApplication
    QMainWindow = QtWidgets.QMainWindow
    QDialog = QtWidgets.QDialog
    QLabel = QtWidgets.QLabel
    QLineEdit = QtWidgets.QLineEdit
    QPushButton = QtWidgets.QPushButton
    QCheckBox = QtWidgets.QCheckBox
    QRadioButton = QtWidgets.QRadioButton
    QComboBox = QtWidgets.QComboBox
    QSpinBox = QtWidgets.QSpinBox
    QDoubleSpinBox = QtWidgets.QDoubleSpinBox
    QSlider = QtWidgets.QSlider
    QProgressBar = QtWidgets.QProgressBar
    QTextEdit = QtWidgets.QTextEdit
    QPlainTextEdit = QtWidgets.QPlainTextEdit
    QListWidget = QtWidgets.QListWidget
    QTreeWidget = QtWidgets.QTreeWidget
    QTableWidget = QtWidgets.QTableWidget
    QTabWidget = QtWidgets.QTabWidget
    QScrollArea = QtWidgets.QScrollArea
    QSplitter = QtWidgets.QSplitter
    QGroupBox = QtWidgets.QGroupBox
    QFrame = QtWidgets.QFrame
    QVBoxLayout = QtWidgets.QVBoxLayout
    QHBoxLayout = QtWidgets.QHBoxLayout
    QGridLayout = QtWidgets.QGridLayout
    QFormLayout = QtWidgets.QFormLayout
    QStackedLayout = QtWidgets.QStackedLayout
    QMenuBar = QtWidgets.QMenuBar
    QMenu = QtWidgets.QMenu
    QAction = QtGui.QAction
    QToolBar = QtWidgets.QToolBar
    QStatusBar = QtWidgets.QStatusBar
    QFileDialog = QtWidgets.QFileDialog
    QMessageBox = QtWidgets.QMessageBox
    QInputDialog = QtWidgets.QInputDialog
    QColorDialog = QtWidgets.QColorDialog
    QFontDialog = QtWidgets.QFontDialog
    
    # Common core classes
    Qt = QtCore.Qt
    QTimer = QtCore.QTimer
    QThread = QtCore.QThread
    QObject = QtCore.QObject
    QSize = QtCore.QSize
    QPoint = QtCore.QPoint
    QRect = QtCore.QRect
    QUrl = QtCore.QUrl
    
    # Common GUI classes
    QPixmap = QtGui.QPixmap
    QIcon = QtGui.QIcon
    QFont = QtGui.QFont
    QColor = QtGui.QColor
    QPainter = QtGui.QPainter
    QPen = QtGui.QPen
    QBrush = QtGui.QBrush
    
    # Signals (different between PyQt5 and PyQt6)
    if USING_PYQT6:
        pyqtSignal = QtCore.pyqtSignal
        pyqtSlot = QtCore.pyqtSlot
    else:  # PyQt5
        pyqtSignal = QtCore.pyqtSignal
        pyqtSlot = QtCore.pyqtSlot

# Utility functions for code that needs to handle differences
def create_application(args=None):
    """Create a QApplication with appropriate arguments for the PyQt version"""
    if args is None:
        args = sys.argv
    
    if USING_PYQT6 or USING_PYQT5:
        return QApplication(args)
    else:
        # Fallback to tkinter
        import tkinter as tk
        return tk.Tk()

def show_message_box(parent, title, message, icon=None):
    """Show a message box compatible with both PyQt versions"""
    if USING_PYQT6 or USING_PYQT5:
        msg_box = QMessageBox(parent)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        if icon:
            msg_box.setIcon(icon)
        return msg_box.exec()
    else:
        # Fallback to tkinter
        import tkinter.messagebox as msgbox
        return msgbox.showinfo(title, message)

# Export key information
__all__ = [
    'QtWidgets', 'QtCore', 'QtGui', 'QtOpenGL', 'QtQuick',
    'USING_PYQT6', 'USING_PYQT5', 'PYQT_VERSION',
    'get_pyqt_version', 'is_pyqt6', 'is_pyqt5',
    'create_application', 'show_message_box',
    # Common classes for backward compatibility
    'QWidget', 'QApplication', 'QMainWindow', 'QDialog', 'QLabel',
    'QLineEdit', 'QPushButton', 'QCheckBox', 'QRadioButton', 'QComboBox',
    'Qt', 'QTimer', 'QThread', 'QObject', 'QSize', 'QPoint', 'QRect',
    'QPixmap', 'QIcon', 'QFont', 'QColor', 'QPainter', 'QPen', 'QBrush',
    'pyqtSignal', 'pyqtSlot'
]

# Print compatibility information
if __name__ == "__main__":
    print(f"PyQt Compatibility Layer Status:")
    print(f"  Version: {PYQT_VERSION}")
    print(f"  PyQt6: {USING_PYQT6}")
    print(f"  PyQt5: {USING_PYQT5}")
    print(f"  OpenGL: {QtOpenGL is not None}")
    print(f"  Quick: {QtQuick is not None}")
