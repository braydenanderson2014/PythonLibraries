#!/usr/bin/env python3
"""
GitHub App Bot Implementation for Issue Reporting
This approach creates issues that appear to be submitted by a bot account
"""

import jwt
import time
import requests
from datetime import datetime, timedelta

class GitHubAppBot:
    """GitHub App implementation for bot-like issue submission"""
    
    def __init__(self, app_id, private_key_path, installation_id):
        self.app_id = app_id
        self.private_key_path = private_key_path
        self.installation_id = installation_id
        self.access_token = None
        self.token_expires = None
    
    def get_jwt_token(self):
        """Generate JWT token for GitHub App authentication"""
        with open(self.private_key_path, 'r') as key_file:
            private_key = key_file.read()
        
        now = int(time.time())
        payload = {
            'iat': now,
            'exp': now + 600,  # 10 minutes
            'iss': self.app_id
        }
        
        return jwt.encode(payload, private_key, algorithm='RS256')
    
    def get_installation_access_token(self):
        """Get installation access token"""
        if self.access_token and self.token_expires and datetime.now() < self.token_expires:
            return self.access_token
        
        jwt_token = self.get_jwt_token()
        
        headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        url = f'https://api.github.com/app/installations/{self.installation_id}/access_tokens'
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        self.access_token = data['token']
        self.token_expires = datetime.now() + timedelta(minutes=50)  # Expires in 1 hour, refresh at 50 min
        
        return self.access_token
    
    def create_issue(self, repo_owner, repo_name, title, body, labels=None):
        """Create issue using GitHub App (appears as bot)"""
        token = self.get_installation_access_token()
        
        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        payload = {
            'title': title,
            'body': body,
            'labels': labels or []
        }
        
        url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/issues'
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        return response.json()

print("🤖 GitHub App Bot Setup Instructions:")
print("=" * 50)
print("1. Go to GitHub Settings → Developer settings → GitHub Apps")
print("2. Click 'New GitHub App'")
print("3. Fill out the form:")
print("   - Name: 'PDF Utility Issue Bot'")
print("   - Homepage URL: Your repo URL")
print("   - Webhook URL: Can be dummy for this use case")
print("   - Repository permissions:")
print("     • Issues: Read & write")
print("     • Metadata: Read")
print("4. Create the app and note the App ID")
print("5. Generate a private key and save it securely")
print("6. Install the app on your repository")
print("7. Note the Installation ID from the installation")
print("8. Update your .env file with:")
print("   GITHUB_APP_ID=your_app_id")
print("   GITHUB_APP_PRIVATE_KEY_PATH=path/to/private-key.pem")
print("   GITHUB_APP_INSTALLATION_ID=your_installation_id")
