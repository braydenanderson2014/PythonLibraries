#!/usr/bin/env python3
"""
Clean Settings Dialog Test
Uses clean widgets to test theme compatibility and layout
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTabWidget, 
    QDialogButtonBox, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt

from settings_controller import SettingsController
from PDFLogger import Logger

# Import clean widgets
from Settings.clean_general_settings_widget import CleanGeneralSettingsWidget

class CleanSettingsTestDialog(QDialog):
    """Test dialog for clean widgets"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = Logger()
        self.parent = parent
        
        # Use settings controller
        if parent and hasattr(parent, 'settings'):
            self.settings_controller = parent.settings
        else:
            self.settings_controller = SettingsController()
        
        self.settings_controller.load_settings()
        
        # Set dialog properties
        self.setWindowTitle("Clean Settings Test Dialog")
        self.setModal(True)
        self.setFixedSize(800, 600)
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the clean test UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Title
        title_layout = QHBoxLayout()
        title_layout.addStretch()
        
        # Create tab widget
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        
        # Clean styling - minimal and theme-friendly
        self.tabs.setStyleSheet("""
            QTabWidget {
                background-color: transparent;
            }
            QTabWidget::pane {
                border: 1px solid palette(mid);
                background-color: palette(window);
            }
            QTabBar::tab {
                background-color: palette(button);
                border: 1px solid palette(mid);
                border-bottom: none;
                padding: 10px 15px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: palette(window);
                border-bottom: 1px solid palette(window);
            }
            QTabBar::tab:hover {
                background-color: palette(highlight);
                color: palette(highlighted-text);
            }
        """)
        
        # Add clean general settings widget
        clean_general_widget = CleanGeneralSettingsWidget(self.settings_controller, self.logger)
        
        scroll_area = QScrollArea()
        scroll_area.setWidget(clean_general_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Clean scroll area styling
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: palette(window);
            }
        """)
        
        self.tabs.addTab(scroll_area, "General (Clean)")
        
        main_layout.addWidget(self.tabs, 1)
        
        # Button box
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        
        main_layout.addWidget(self.button_box)


# Test function
def test_clean_widgets():
    """Test the clean widgets"""
    import sys
    from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel
    
    app = QApplication(sys.argv)
    
    # Create test window
    main_window = QMainWindow()
    main_window.setWindowTitle("Clean Widget Test")
    main_window.setGeometry(300, 300, 400, 200)
    
    central_widget = QWidget()
    layout = QVBoxLayout(central_widget)
    
    title = QLabel("🧪 Clean Settings Widget Test")
    title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
    layout.addWidget(title)
    
    description = QLabel("Tests theme-aware settings widgets")
    layout.addWidget(description)
    
    test_button = QPushButton("Open Clean Settings Dialog")
    
    def open_clean_settings():
        dialog = CleanSettingsTestDialog(main_window)
        dialog.exec()
    
    test_button.clicked.connect(open_clean_settings)
    layout.addWidget(test_button)
    
    main_window.setCentralWidget(central_widget)
    main_window.show()
    
    return app.exec()

if __name__ == "__main__":
    import sys
    print("🧪 Testing Clean Settings Widgets...")
    try:
        sys.exit(test_clean_widgets())
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
