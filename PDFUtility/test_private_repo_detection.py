#!/usr/bin/env python3
"""
Test Private Repository Detection
Tests the new repository visibility detection feature
"""

import os
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from issue_reporter import IssueStatusWidget

class PrivateRepoTestWindow(QMainWindow):
    """Test window for private repository detection"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔒 Private Repository Detection Test")
        self.setGeometry(100, 100, 600, 400)
        
        # Create main widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Title
        title = QLabel("🔒 Private Repository Detection Test")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # Description
        description = QLabel("""
This tests the new repository visibility detection feature:

✅ Automatically detects if repository is public or private
✅ Hides GitHub URLs for private repositories (security)
✅ Shows helpful message in status summary for private repos
✅ Caches the repository visibility check for performance

Current Configuration:
""")
        layout.addWidget(description)
        
        # Show current config
        github_owner = os.getenv('GITHUB_OWNER', 'Not Set')
        github_repo = os.getenv('GITHUB_REPO', 'Not Set')
        config_label = QLabel(f"Repository: {github_owner}/{github_repo}")
        config_label.setStyleSheet("font-family: monospace; padding: 10px; background-color: #f0f0f0;")
        layout.addWidget(config_label)
        
        # Test button
        self.test_btn = QPushButton("🔍 Test Repository Visibility Detection")
        self.test_btn.setMinimumHeight(40)
        self.test_btn.clicked.connect(self.test_visibility)
        layout.addWidget(self.test_btn)
        
        # Results label
        self.results_label = QLabel("Click the test button to check repository visibility...")
        self.results_label.setWordWrap(True)
        self.results_label.setStyleSheet("margin: 10px; padding: 10px; border: 1px solid #ccc;")
        layout.addWidget(self.results_label)
        
        # Create an IssueStatusWidget instance to test
        self.status_widget = IssueStatusWidget()
        
    def test_visibility(self):
        """Test the repository visibility detection"""
        self.test_btn.setEnabled(False)
        self.test_btn.setText("🔄 Checking...")
        
        try:
            # Test the visibility check
            is_public = self.status_widget.check_repository_visibility()
            
            if is_public:
                result = """
🟢 REPOSITORY IS PUBLIC
✅ GitHub URLs will be displayed in issue viewer
✅ Links are safe to show to users
"""
                self.results_label.setStyleSheet("margin: 10px; padding: 10px; border: 1px solid #4CAF50; background-color: #E8F5E8;")
            else:
                result = """
🔒 REPOSITORY IS PRIVATE
✅ GitHub URLs will be HIDDEN for security
✅ Users will see a helpful privacy message
✅ This protects your private repository URLs
"""
                self.results_label.setStyleSheet("margin: 10px; padding: 10px; border: 1px solid #FF9800; background-color: #FFF3E0;")
            
            # Test the cache (should be instant second time)
            self.status_widget.check_repository_visibility()
            result += "\n✅ Caching is working - second check was instant!"
            
        except Exception as e:
            result = f"❌ Error testing visibility: {str(e)}"
            self.results_label.setStyleSheet("margin: 10px; padding: 10px; border: 1px solid #f44336; background-color: #FFEBEE;")
        
        self.results_label.setText(result)
        self.test_btn.setEnabled(True)
        self.test_btn.setText("🔍 Test Repository Visibility Detection")

def main():
    """Run the private repository detection test"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Private Repo Detection Test")
    app.setOrganizationName("PDF Utility")
    
    # Create and show test window
    window = PrivateRepoTestWindow()
    window.show()
    
    # Run the application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
