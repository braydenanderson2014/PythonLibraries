#!/usr/bin/env python3
"""
Test the enhanced AboutDialog with company section
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget

# Add the project directory to the path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

from main_application import AboutDialog

class TestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test About Dialog")
        self.setGeometry(300, 300, 200, 100)
        
        layout = QVBoxLayout()
        
        button = QPushButton("Show About Dialog")
        button.clicked.connect(self.show_about)
        layout.addWidget(button)
        
        self.setLayout(layout)
    
    def show_about(self):
        dialog = AboutDialog(self)
        dialog.exec()

def main():
    app = QApplication(sys.argv)
    
    window = TestWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
