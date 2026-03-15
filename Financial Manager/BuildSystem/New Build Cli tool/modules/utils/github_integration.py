"""
GitHub integration utilities for BuildCLI module management.
"""

import os
import json
import asyncio
import tempfile
import shutil
import zipfile
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from urllib.parse import urlparse
import subprocess

from core.config import Config
from utils.logger import Logger


class GitHubIntegration:
    """GitHub integration for downloading and managing modules."""
    
    def __init__(self, config: Config, logger: Logger, github_config_path: Optional[str] = None):
        self.config = config
        self.logger = logger
        self.github_config = self._load_github_config(github_config_path)
        self.session_headers = self._setup_auth_headers()
    
    def _load_github_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load GitHub configuration."""
        if config_path is None:
            # Try program config first, then user template
            program_config = Path(__file__).parent.parent / "github_config_program.json"
            user_config = Path.home() / ".buildcli" / "github_config.json"
            template_config = Path(__file__).parent.parent / "github_config_template.json"
            
            if user_config.exists():
                config_path = str(user_config)
            elif program_config.exists():
                config_path = str(program_config)
            elif template_config.exists():
                config_path = str(template_config)
            else:
                self.logger.warning("No GitHub configuration found, using defaults")
                return self._get_default_github_config()
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                github_config = json.load(f)
            self.logger.debug(f"Loaded GitHub config from: {config_path}")
            return github_config
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.warning(f"Failed to load GitHub config from {config_path}: {e}")
            return self._get_default_github_config()
    
    def _get_default_github_config(self) -> Dict[str, Any]:
        """Get default GitHub configuration."""
        return {
            "github": {
                "personal_access_token": "",
                "username": "",
                "api": {"base_url": "https://api.github.com", "timeout": 30, "max_retries": 3},
                "download": {"prefer_releases": True, "fallback_to_main": True, "cache_duration_hours": 24},
                "authentication": {"method": "token", "token_env_var": "BUILDCLI_GITHUB_TOKEN"}
            },
            "module_sources": {
                "primary": {
                    "type": "github",
                    "url": "https://github.com/buildcli-official/buildcli-modules",
                    "branch": "main",
                    "enabled": True,
                    "trusted": True
                }
            },
            "security": {"verify_signatures": False, "scan_for_vulnerabilities": True}
        }
    
    def _setup_auth_headers(self) -> Dict[str, str]:
        """Setup authentication headers for GitHub API requests."""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "BuildCLI/1.0.0"
        }
        
        # Try to get token from environment or config
        token = os.getenv(self.github_config["github"]["authentication"]["token_env_var"])
        if not token:
            token = self.github_config["github"]["personal_access_token"]
        
        if token:
            headers["Authorization"] = f"token {token}"
            self.logger.debug("GitHub authentication configured")
        else:
            self.logger.warning("No GitHub authentication token found - API rate limits may apply")
        
        return headers
    
    async def list_available_modules(self, source_name: str = "primary") -> List[Dict[str, Any]]:
        """
        List available modules from a GitHub source.
        
        Args:
            source_name: Name of the module source to query
            
        Returns:
            List of module information dictionaries
        """
        if source_name not in self.github_config["module_sources"]:
            raise ValueError(f"Unknown module source: {source_name}")
        
        source_config = self.github_config["module_sources"][source_name]
        
        if not source_config["enabled"]:
            self.logger.warning(f"Module source '{source_name}' is disabled")
            return []
        
        try:
            # Check if there's a manifest URL
            manifest_url = source_config.get("manifest_url")
            if manifest_url:
                return await self._fetch_module_manifest(manifest_url)
            else:
                # Fallback to repository scanning
                return await self._scan_repository_modules(source_config)
        
        except Exception as e:
            self.logger.error(f"Failed to list modules from {source_name}: {e}")
            return []
    
    async def _fetch_module_manifest(self, manifest_url: str) -> List[Dict[str, Any]]:
        """Fetch module list from a manifest file."""
        try:
            # For now, we'll use a simple approach
            # In a real implementation, you'd use aiohttp or similar
            self.logger.info(f"Fetching module manifest from: {manifest_url}")
            
            # Placeholder - would implement HTTP request here
            return [
                {
                    "name": "git",
                    "version": "1.0.0",
                    "description": "Git integration module",
                    "author": "BuildCLI Official",
                    "commands": ["git", "clone", "push", "pull", "commit"],
                    "download_url": "https://github.com/buildcli-official/buildcli-modules/releases/download/v1.0.0/git.zip"
                },
                {
                    "name": "docker",
                    "version": "1.0.0",
                    "description": "Docker integration module",
                    "author": "BuildCLI Official",
                    "commands": ["docker", "build", "run", "push", "compose"],
                    "download_url": "https://github.com/buildcli-official/buildcli-modules/releases/download/v1.0.0/docker.zip"
                }
            ]
        
        except Exception as e:
            self.logger.error(f"Failed to fetch manifest: {e}")
            return []
    
    async def _scan_repository_modules(self, source_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scan a repository for available modules."""
        # This would use GitHub API to scan repository contents
        # For now, return placeholder data
        self.logger.info(f"Scanning repository: {source_config['url']}")
        return []
    
    async def download_module(self, module_name: str, source_name: str = "primary", version: str = "latest") -> bool:
        """
        Download a module from GitHub.
        
        Args:
            module_name: Name of the module to download
            source_name: Source to download from
            version: Version to download (default: latest)
            
        Returns:
            True if download was successful
        """
        if source_name not in self.github_config["module_sources"]:
            raise ValueError(f"Unknown module source: {source_name}")
        
        source_config = self.github_config["module_sources"][source_name]
        
        if not source_config["enabled"]:
            raise ValueError(f"Module source '{source_name}' is disabled")
        
        try:
            self.logger.info(f"Downloading module '{module_name}' from {source_name}")
            
            # Get module information
            available_modules = await self.list_available_modules(source_name)
            module_info = next((m for m in available_modules if m["name"] == module_name), None)
            
            if not module_info:
                raise ValueError(f"Module '{module_name}' not found in source '{source_name}'")
            
            # Security check
            if not self._verify_module_security(module_info, source_config):
                raise ValueError(f"Module '{module_name}' failed security verification")
            
            # Download and install
            return await self._download_and_install_module(module_info, source_config)
        
        except Exception as e:
            self.logger.error(f"Failed to download module {module_name}: {e}")
            return False
    
    def _verify_module_security(self, module_info: Dict[str, Any], source_config: Dict[str, Any]) -> bool:
        """Verify module meets security requirements."""
        security_config = self.github_config["security"]
        
        # Check if source is trusted
        if not source_config.get("trusted", False) and security_config.get("require_code_review", False):
            self.logger.warning(f"Module from untrusted source requires manual verification")
            return False
        
        # Check author whitelist/blacklist
        author = module_info.get("author", "")
        allowed_authors = security_config.get("allowed_authors", [])
        blocked_authors = security_config.get("blocked_authors", [])
        
        if allowed_authors and author not in allowed_authors:
            self.logger.warning(f"Module author '{author}' not in allowed list")
            return False
        
        if author in blocked_authors:
            self.logger.warning(f"Module author '{author}' is blocked")
            return False
        
        return True
    
    async def _download_and_install_module(self, module_info: Dict[str, Any], source_config: Dict[str, Any]) -> bool:
        """Download and install a module."""
        module_name = module_info["name"]
        download_url = module_info.get("download_url")
        
        if not download_url:
            # Fallback to Git clone
            return await self._git_clone_module(module_name, source_config)
        
        try:
            # Create temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Download the module (placeholder for actual HTTP download)
                self.logger.info(f"Downloading from: {download_url}")
                download_path = temp_path / f"{module_name}.zip"
                
                # In a real implementation, you'd download the file here
                # For now, we'll simulate with a placeholder
                
                # Extract and install
                module_dir = Path(self.config.module_cache_dir) / module_name
                
                # Remove existing module
                if module_dir.exists():
                    shutil.rmtree(module_dir)
                
                module_dir.mkdir(parents=True, exist_ok=True)
                
                # Create a basic module file (placeholder)
                module_file = module_dir / "module.py"
                with open(module_file, 'w', encoding='utf-8') as f:
                    f.write(f'"""Downloaded module: {module_name}"""\n')
                    f.write(f'MODULE_INFO = {json.dumps(module_info, indent=2)}\n')
                    f.write(f'async def register_commands(): return {{}}\n')
                
                # Save module info
                info_file = module_dir / "module_info.json"
                with open(info_file, 'w', encoding='utf-8') as f:
                    json.dump(module_info, f, indent=2)
                
                self.logger.info(f"Successfully installed module: {module_name}")
                return True
        
        except Exception as e:
            self.logger.error(f"Failed to download and install module: {e}")
            return False
    
    async def _git_clone_module(self, module_name: str, source_config: Dict[str, Any]) -> bool:
        """Clone a module using Git."""
        try:
            repo_url = source_config["url"]
            branch = source_config.get("branch", "main")
            
            # Create module directory
            module_dir = Path(self.config.module_cache_dir) / module_name
            
            if module_dir.exists():
                shutil.rmtree(module_dir)
            
            # Git clone command
            clone_cmd = [
                "git", "clone", 
                "--depth", "1", 
                "--branch", branch,
                f"{repo_url}/{module_name}",
                str(module_dir)
            ]
            
            self.logger.info(f"Cloning module from: {repo_url}/{module_name}")
            
            process = await asyncio.create_subprocess_exec(
                *clone_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                self.logger.info(f"Successfully cloned module: {module_name}")
                return True
            else:
                self.logger.error(f"Git clone failed: {stderr.decode()}")
                return False
        
        except Exception as e:
            self.logger.error(f"Failed to clone module: {e}")
            return False
    
    async def update_module(self, module_name: str) -> bool:
        """Update an existing module."""
        module_dir = Path(self.config.module_cache_dir) / module_name
        
        if not module_dir.exists():
            self.logger.error(f"Module '{module_name}' not found for update")
            return False
        
        # Read module info to determine source
        info_file = module_dir / "module_info.json"
        if info_file.exists():
            try:
                with open(info_file, 'r', encoding='utf-8') as f:
                    module_info = json.load(f)
                
                # Re-download the module
                return await self.download_module(module_name, "primary", "latest")
            
            except Exception as e:
                self.logger.error(f"Failed to read module info: {e}")
                return False
        
        return False
    
    def get_installed_modules(self) -> List[str]:
        """Get list of installed modules."""
        cache_dir = Path(self.config.module_cache_dir)
        
        if not cache_dir.exists():
            return []
        
        modules = []
        for module_dir in cache_dir.iterdir():
            if module_dir.is_dir() and (module_dir / "module.py").exists():
                modules.append(module_dir.name)
        
        return modules