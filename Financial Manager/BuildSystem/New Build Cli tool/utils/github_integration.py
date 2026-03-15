"""
GitHub integration utilities for BuildCLI module management.
"""

import os
import json
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse


class GitHubIntegration:
    """Handles GitHub repository integration for module management."""
    
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self._setup_github_config()
    
    def _setup_github_config(self):
        """Set up GitHub configuration from config file."""
        github_config = self.config.get("github", {})
        
        # Default configuration
        self.default_config = {
            "authentication": {
                "token": None,
                "username": None
            },
            "sources": [
                {
                    "name": "buildcli-official",
                    "type": "github",
                    "url": "https://github.com/buildcli-official/buildcli-modules",
                    "branch": "main",
                    "enabled": True
                }
            ],
            "security": {
                "verify_checksums": True,
                "allowed_domains": ["github.com", "raw.githubusercontent.com"],
                "require_https": True
            },
            "cache": {
                "enabled": True,
                "ttl_hours": 24,
                "max_size_mb": 100
            }
        }
        
        # Merge with user configuration
        self.github_config = {**self.default_config, **github_config}
        
        # Warn if no authentication token
        if not self.github_config["authentication"]["token"]:
            self.logger.warning("No GitHub authentication token found - API rate limits may apply")
    
    async def list_available_modules(self, source: Optional[str] = None) -> List[Dict[str, Any]]:
        """List available modules from GitHub repositories."""
        # This is a placeholder implementation
        # In a real implementation, you would make HTTP requests to GitHub API
        
        self.logger.debug("Fetching available modules from GitHub repositories")
        
        # Placeholder data
        placeholder_modules = [
            {
                "name": "database",
                "version": "1.0.0",
                "description": "Database management utilities",
                "author": "BuildCLI Team",
                "source": "buildcli-official",
                "download_url": "https://github.com/buildcli-official/buildcli-modules/releases/download/v1.0.0/database.zip"
            },
            {
                "name": "docker",
                "version": "1.2.0",
                "description": "Docker container management",
                "author": "BuildCLI Team",
                "source": "buildcli-official",
                "download_url": "https://github.com/buildcli-official/buildcli-modules/releases/download/v1.2.0/docker.zip"
            },
            {
                "name": "aws-deploy",
                "version": "2.1.0",
                "description": "AWS deployment utilities",
                "author": "BuildCLI Team",
                "source": "buildcli-official",
                "download_url": "https://github.com/buildcli-official/buildcli-modules/releases/download/v2.1.0/aws-deploy.zip"
            }
        ]
        
        return placeholder_modules
    
    async def download_module(self, module_name: str, source: Optional[str] = None) -> Optional[str]:
        """Download a module from GitHub repository."""
        # This is a placeholder implementation
        # In a real implementation, you would:
        # 1. Find the module in the available modules list
        # 2. Download the module zip file from GitHub
        # 3. Extract and validate the module
        # 4. Return the path to the extracted module
        
        self.logger.info(f"Downloading module '{module_name}' from GitHub")
        
        # Placeholder implementation
        self.logger.warning(f"Module download not yet implemented - '{module_name}' download skipped")
        return None
    
    def get_configured_sources(self) -> List[Dict[str, Any]]:
        """Get list of configured GitHub sources."""
        return self.github_config.get("sources", [])
    
    def add_source(self, name: str, url: str, branch: str = "main") -> bool:
        """Add a new GitHub source."""
        sources = self.github_config.get("sources", [])
        
        # Check if source already exists
        for source in sources:
            if source["name"] == name:
                self.logger.warning(f"Source '{name}' already exists")
                return False
        
        # Add new source
        new_source = {
            "name": name,
            "type": "github",
            "url": url,
            "branch": branch,
            "enabled": True
        }
        
        sources.append(new_source)
        self.github_config["sources"] = sources
        
        # Save to config
        github_config = self.config.get("github", {})
        github_config["sources"] = sources
        self.config.set("github", github_config)
        self.config.save_config()
        
        self.logger.info(f"Added GitHub source: {name}")
        return True
    
    def remove_source(self, name: str) -> bool:
        """Remove a GitHub source."""
        sources = self.github_config.get("sources", [])
        
        # Find and remove source
        for i, source in enumerate(sources):
            if source["name"] == name:
                removed_source = sources.pop(i)
                self.github_config["sources"] = sources
                
                # Save to config
                github_config = self.config.get("github", {})
                github_config["sources"] = sources
                self.config.set("github", github_config)
                self.config.save_config()
                
                self.logger.info(f"Removed GitHub source: {name}")
                return True
        
        self.logger.warning(f"Source '{name}' not found")
        return False
    
    def validate_module_security(self, module_path: str) -> bool:
        """Validate module security and integrity."""
        # This is a placeholder for security validation
        # In a real implementation, you would:
        # 1. Verify file checksums
        # 2. Check for malicious code patterns
        # 3. Validate module manifest
        # 4. Ensure module comes from trusted source
        
        self.logger.debug(f"Validating module security: {module_path}")
        
        # Placeholder - always return True for now
        return True
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for GitHub API requests."""
        headers = {
            "User-Agent": "BuildCLI-Module-Manager/1.0",
            "Accept": "application/vnd.github.v3+json"
        }
        
        token = self.github_config["authentication"]["token"]
        if token:
            headers["Authorization"] = f"token {token}"
        
        return headers
    
    def is_url_allowed(self, url: str) -> bool:
        """Check if URL is from an allowed domain."""
        allowed_domains = self.github_config["security"]["allowed_domains"]
        parsed_url = urlparse(url)
        
        return parsed_url.netloc in allowed_domains
    
    async def update_module(self, module_name: str) -> bool:
        """Update an installed module from its repository."""
        # This is a placeholder implementation
        # In a real implementation, you would:
        # 1. Check if module is installed
        # 2. Find the module's source repository
        # 3. Download the latest version
        # 4. Replace the existing module
        # 5. Reload the module
        
        self.logger.info(f"Updating module '{module_name}' from repository")
        
        # Placeholder implementation
        self.logger.warning(f"Module update not yet implemented - '{module_name}' update skipped")
        return False
    
    def create_github_config_template(self) -> Dict[str, Any]:
        """Create a GitHub configuration template."""
        return {
            "authentication": {
                "token": "your_github_personal_access_token_here",
                "username": "your_github_username"
            },
            "sources": [
                {
                    "name": "buildcli-official",
                    "type": "github", 
                    "url": "https://github.com/buildcli-official/buildcli-modules",
                    "branch": "main",
                    "enabled": True
                },
                {
                    "name": "my-custom-modules",
                    "type": "github",
                    "url": "https://github.com/your-username/your-modules-repo",
                    "branch": "main", 
                    "enabled": True
                }
            ],
            "security": {
                "verify_checksums": True,
                "allowed_domains": ["github.com", "raw.githubusercontent.com"],
                "require_https": True
            },
            "cache": {
                "enabled": True,
                "ttl_hours": 24,
                "max_size_mb": 100
            }
        }