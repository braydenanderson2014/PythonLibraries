#!/usr/bin/env python3
"""
GitHub App Authentication Handler
Handles JWT token generation and installation access tokens for GitHub Apps
"""

import os
import time
import jwt
import requests
from datetime import datetime, timedelta, timezone
from pathlib import Path

class GitHubAppAuth:
    """GitHub App authentication handler"""
    
    def __init__(self):
        """Initialize GitHub App authentication"""
        self.app_id = os.getenv('GITHUB_APP_ID')
        self.private_key_path = os.getenv('GITHUB_APP_PRIVATE_KEY_PATH')
        self.installation_id = os.getenv('GITHUB_APP_INSTALLATION_ID')
        
        # Cache for installation access token
        self._access_token = None
        self._token_expires_at = None
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self):
        """Validate GitHub App configuration"""
        missing_items = []
        
        if not self.app_id:
            missing_items.append("GITHUB_APP_ID")
        if not self.private_key_path:
            missing_items.append("GITHUB_APP_PRIVATE_KEY_PATH")
        if not self.installation_id:
            missing_items.append("GITHUB_APP_INSTALLATION_ID")
        
        if missing_items:
            raise ValueError(f"GitHub App configuration incomplete: Missing {', '.join(missing_items)}")
        
        # Check if private key file exists
        key_path = Path(self.private_key_path)
        if not key_path.exists():
            raise FileNotFoundError(f"GitHub App private key file not found: {self.private_key_path}")
    
    def _load_private_key(self):
        """Load the private key from file"""
        try:
            with open(self.private_key_path, 'r') as key_file:
                return key_file.read()
        except Exception as e:
            raise Exception(f"Failed to load private key: {e}")
    
    def _generate_jwt_token(self):
        """Generate a JWT token for GitHub App authentication"""
        try:
            private_key = self._load_private_key()
            
            # JWT payload
            now = int(time.time())
            payload = {
                'iat': now - 60,  # Issued at (1 minute ago to account for clock skew)
                'exp': now + (10 * 60),  # Expires in 10 minutes (GitHub max)
                'iss': int(self.app_id)  # Issuer (GitHub App ID)
            }
            
            # Generate JWT token
            token = jwt.encode(payload, private_key, algorithm='RS256')
            return token
            
        except Exception as e:
            raise Exception(f"Failed to generate JWT token: {e}")
    
    def _get_installation_access_token(self):
        """Get an installation access token using JWT"""
        try:
            jwt_token = self._generate_jwt_token()
            
            # Request installation access token
            url = f"https://api.github.com/app/installations/{self.installation_id}/access_tokens"
            headers = {
                'Authorization': f'Bearer {jwt_token}',
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'PDF-Utility-Issue-Bot/1.0'
            }
            
            response = requests.post(url, headers=headers, timeout=30)
            
            if response.status_code == 201:
                data = response.json()
                token = data['token']
                expires_at = datetime.fromisoformat(data['expires_at'].replace('Z', '+00:00'))
                return token, expires_at
            else:
                raise Exception(f"Failed to get installation access token: {response.status_code} - {response.text}")
                
        except Exception as e:
            raise Exception(f"Failed to get installation access token: {e}")
    
    def get_access_token(self):
        """Get a valid installation access token (cached if still valid)"""
        # Check if we have a cached token that's still valid
        if (self._access_token and self._token_expires_at and 
            datetime.now(timezone.utc) < self._token_expires_at - timedelta(minutes=5)):
            return self._access_token
        
        # Get a new token
        self._access_token, self._token_expires_at = self._get_installation_access_token()
        return self._access_token
    
    def get_authenticated_headers(self):
        """Get headers with authentication for GitHub API requests"""
        token = self.get_access_token()
        return {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'PDF-Utility-Issue-Bot/1.0'
        }
    
    def is_configured(self):
        """Check if GitHub App is properly configured"""
        try:
            self._validate_config()
            return True
        except (ValueError, FileNotFoundError):
            return False
    
    def test_authentication(self):
        """Test GitHub App authentication by getting app info"""
        try:
            # Test JWT generation
            jwt_token = self._generate_jwt_token()
            
            # Test app access
            url = "https://api.github.com/app"
            headers = {
                'Authorization': f'Bearer {jwt_token}',
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'PDF-Utility-Issue-Bot/1.0'
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                app_data = response.json()
                
                # Test installation access token
                access_token = self.get_access_token()
                
                return {
                    'success': True,
                    'app_name': app_data.get('name', 'Unknown'),
                    'app_id': app_data.get('id', 'Unknown'),
                    'owner': app_data.get('owner', {}).get('login', 'Unknown'),
                    'access_token_length': len(access_token) if access_token else 0
                }
            else:
                return {
                    'success': False,
                    'error': f"Failed to authenticate: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Authentication test failed: {str(e)}"
            }

# Global instance for easy access
github_app_auth = None

def get_github_app_auth():
    """Get the global GitHub App authentication instance"""
    global github_app_auth
    if github_app_auth is None:
        try:
            github_app_auth = GitHubAppAuth()
        except Exception as e:
            print(f"Warning: GitHub App authentication not available: {e}")
            github_app_auth = None
    return github_app_auth

def is_github_app_configured():
    """Check if GitHub App is properly configured"""
    auth = get_github_app_auth()
    return auth is not None and auth.is_configured()
