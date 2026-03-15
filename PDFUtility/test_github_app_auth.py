#!/usr/bin/env python3
"""
GitHub App Authentication Test
Tests the new GitHub App authentication system
"""

import os
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QTextEdit
from github_app_auth import get_github_app_auth, is_github_app_configured

class GitHubAppTestWindow(QMainWindow):
    """Test window for GitHub App authentication"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🤖 GitHub App Authentication Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Create main widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Title
        title = QLabel("🤖 GitHub App Authentication Test")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # Description
        description = QLabel("""
This tests the new GitHub App authentication system:

✅ JWT token generation from private key
✅ Installation access token retrieval
✅ GitHub API authentication
✅ Repository access validation

Current GitHub App Configuration:
""")
        layout.addWidget(description)
        
        # Show current config
        app_id = os.getenv('GITHUB_APP_ID', 'Not Set')
        private_key_path = os.getenv('GITHUB_APP_PRIVATE_KEY_PATH', 'Not Set')
        installation_id = os.getenv('GITHUB_APP_INSTALLATION_ID', 'Not Set')
        
        config_text = f"""App ID: {app_id}
Private Key: {private_key_path}
Installation ID: {installation_id}
Repository: {os.getenv('GITHUB_OWNER', 'Not Set')}/{os.getenv('GITHUB_REPO', 'Not Set')}"""
        
        config_label = QLabel(config_text)
        config_label.setStyleSheet("font-family: monospace; padding: 10px; background-color: palette(base); border: 1px solid palette(mid);")
        layout.addWidget(config_label)
        
        # Test button
        self.test_btn = QPushButton("🧪 Test GitHub App Authentication")
        self.test_btn.setMinimumHeight(40)
        self.test_btn.clicked.connect(self.test_github_app)
        layout.addWidget(self.test_btn)
        
        # Results text area
        self.results_text = QTextEdit()
        self.results_text.setPlainText("Click the test button to test GitHub App authentication...")
        self.results_text.setMaximumHeight(300)
        layout.addWidget(self.results_text)
        
    def test_github_app(self):
        """Test the GitHub App authentication"""
        self.test_btn.setEnabled(False)
        self.test_btn.setText("🔄 Testing...")
        self.results_text.clear()
        
        try:
            # Test if GitHub App is configured
            if not is_github_app_configured():
                self.results_text.append("❌ GitHub App is not properly configured")
                self.results_text.append("\nRequired environment variables:")
                self.results_text.append("- GITHUB_APP_ID")
                self.results_text.append("- GITHUB_APP_PRIVATE_KEY_PATH")
                self.results_text.append("- GITHUB_APP_INSTALLATION_ID")
                return
            
            self.results_text.append("✅ GitHub App configuration found")
            
            # Get GitHub App auth instance
            github_app_auth = get_github_app_auth()
            if not github_app_auth:
                self.results_text.append("❌ Failed to initialize GitHub App authentication")
                return
            
            self.results_text.append("✅ GitHub App authentication initialized")
            
            # Test authentication
            self.results_text.append("\n🧪 Testing authentication...")
            test_result = github_app_auth.test_authentication()
            
            if test_result['success']:
                self.results_text.append("✅ Authentication successful!")
                self.results_text.append(f"\nApp Details:")
                self.results_text.append(f"- App Name: {test_result['app_name']}")
                self.results_text.append(f"- App ID: {test_result['app_id']}")
                self.results_text.append(f"- Owner: {test_result['owner']}")
                self.results_text.append(f"- Access Token Length: {test_result['access_token_length']} characters")
                
                # Test API access
                self.results_text.append("\n🧪 Testing GitHub API access...")
                try:
                    headers = github_app_auth.get_authenticated_headers()
                    self.results_text.append("✅ Authentication headers generated successfully")
                    
                    # Test repository access
                    import requests
                    github_owner = os.getenv('GITHUB_OWNER', '')
                    github_repo = os.getenv('GITHUB_REPO', '')
                    
                    if github_owner and github_repo:
                        repo_url = f"https://api.github.com/repos/{github_owner}/{github_repo}"
                        response = requests.get(repo_url, headers=headers, timeout=10)
                        
                        if response.status_code == 200:
                            repo_data = response.json()
                            self.results_text.append("✅ Repository access successful")
                            self.results_text.append(f"- Repository: {repo_data['full_name']}")
                            self.results_text.append(f"- Private: {repo_data.get('private', 'Unknown')}")
                            self.results_text.append(f"- Permissions: {repo_data.get('permissions', {})}")
                        else:
                            self.results_text.append(f"⚠️ Repository access failed: {response.status_code}")
                    
                except Exception as e:
                    self.results_text.append(f"⚠️ API test failed: {str(e)}")
                
                self.results_text.append("\n🎉 GitHub App is ready to use!")
                
            else:
                self.results_text.append(f"❌ Authentication failed: {test_result['error']}")
        
        except Exception as e:
            self.results_text.append(f"❌ Test failed with error: {str(e)}")
            import traceback
            self.results_text.append(f"\nTraceback:\n{traceback.format_exc()}")
        
        finally:
            self.test_btn.setEnabled(True)
            self.test_btn.setText("🧪 Test GitHub App Authentication")

def main():
    """Run the GitHub App authentication test"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("GitHub App Authentication Test")
    app.setOrganizationName("PDF Utility")
    
    # Create and show test window
    window = GitHubAppTestWindow()
    window.show()
    
    # Run the application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
