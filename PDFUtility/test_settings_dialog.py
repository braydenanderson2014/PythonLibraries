#!/usr/bin/env python3
# test_settings_dialog.py - Test the enhanced settings dialog with arrow navigation

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget, QLabel
from settings_dialog import SettingsDialog

class TestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Enhanced Settings Dialog Test")
        self.setGeometry(100, 100, 400, 300)
        
        layout = QVBoxLayout()
        
        title = QLabel("Settings Dialog with Arrow Navigation Test")
        title.setStyleSheet("font-size: 14px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        description = QLabel("This test shows the new settings dialog with:\n"
                           "• Smaller, more compact tabs\n"
                           "• Left/right arrow navigation buttons\n"
                           "• Dynamic button states and tooltips\n"
                           "• Improved visual styling")
        description.setStyleSheet("margin: 10px; color: #666;")
        layout.addWidget(description)
        
        button = QPushButton("Open Enhanced Settings Dialog")
        button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 14px;
                border-radius: 6px;
                margin: 20px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        button.clicked.connect(self.open_settings)
        layout.addWidget(button)
        
        self.setLayout(layout)
    
    def open_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = TestWindow()
    window.show()
    
    sys.exit(app.exec())
