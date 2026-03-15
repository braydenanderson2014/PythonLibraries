"""
Module management for BuildCLI - handles loading, installing, and managing command modules.
"""

import os
import sys
import json
import asyncio
import importlib
import importlib.util
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from urllib.parse import urlparse
import tempfile
import shutil

from core.config import Config
from utils.logger import Logger
from utils.github_integration import GitHubIntegration


class ModuleManager:
    """Manages command modules for BuildCLI."""
    
    def __init__(self, config: Config, logger: Logger):
        self.config = config
        self.logger = logger
        self.loaded_modules: Dict[str, Any] = {}
        self.module_info: Dict[str, Dict[str, Any]] = {}
        self.command_handlers: Dict[str, Callable] = {}
        self.github_integration = GitHubIntegration(config, logger)
        
        # Ensure module directories exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure required directories exist."""
        dirs_to_create = [
            self.config.module_cache_dir,
            self.config.temp_dir,
            os.path.join(os.path.dirname(__file__), '..', 'modules')
        ]
        
        for directory in dirs_to_create:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    async def load_builtin_modules(self):
        """Load built-in modules from the modules directory."""
        modules_dir = Path(__file__).parent.parent / "modules"
        
        if not modules_dir.exists():
            self.logger.info("No built-in modules directory found")
            return
        
        # Load built-in modules
        for module_file in modules_dir.glob("*.py"):
            if module_file.name.startswith("__"):
                continue
            
            module_name = module_file.stem
            try:
                await self._load_module_from_file(str(module_file), module_name)
                self.logger.debug(f"Loaded built-in module: {module_name}")
            except Exception as e:
                self.logger.error(f"Failed to load built-in module {module_name}: {e}")
    
    async def load_cached_modules(self):
        """Load modules from the cache directory."""
        cache_dir = Path(self.config.module_cache_dir)
        
        if not cache_dir.exists():
            return
        
        for module_dir in cache_dir.iterdir():
            if not module_dir.is_dir():
                continue
            
            module_file = module_dir / "module.py"
            if module_file.exists():
                try:
                    await self._load_module_from_file(str(module_file), module_dir.name)
                    self.logger.debug(f"Loaded cached module: {module_dir.name}")
                except Exception as e:
                    self.logger.error(f"Failed to load cached module {module_dir.name}: {e}")
    
    async def _load_module_from_file(self, file_path: str, module_name: str):
        """Load a module from a Python file."""
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load module spec from {file_path}")
        
        module = importlib.util.module_from_spec(spec)
        
        # Add module directory to Python path temporarily
        module_dir = os.path.dirname(file_path)
        if module_dir not in sys.path:
            sys.path.insert(0, module_dir)
        
        try:
            spec.loader.exec_module(module)
            
            # Look for module metadata
            module_info = getattr(module, 'MODULE_INFO', {})
            module_info.setdefault('name', module_name)
            module_info.setdefault('version', '1.0.0')
            module_info.setdefault('description', 'No description available')
            
            self.loaded_modules[module_name] = module
            self.module_info[module_name] = module_info
            
            # Register command handlers
            if hasattr(module, 'register_commands'):
                commands = await module.register_commands()
                for command_name, handler in commands.items():
                    self.command_handlers[command_name] = handler
                    self.logger.debug(f"Registered command: {command_name}")
            
        finally:
            # Remove module directory from Python path
            if module_dir in sys.path:
                sys.path.remove(module_dir)
    
    async def install_module_from_repo(self, module_name: str, repo_url: Optional[str] = None, source_name: str = "primary") -> bool:
        """
        Install a module from a remote repository.
        
        Args:
            module_name: Name of the module to install
            repo_url: Optional repository URL (deprecated, use source_name instead)
            source_name: Name of the configured source to download from
            
        Returns:
            True if installation was successful
        """
        try:
            # Use GitHub integration for module installation
            success = await self.github_integration.download_module(module_name, source_name)
            
            if success:
                # Load the newly installed module
                module_file = os.path.join(self.config.module_cache_dir, module_name, "module.py")
                if os.path.exists(module_file):
                    await self._load_module_from_file(module_file, module_name)
                    return True
            
            # Fallback to legacy method if GitHub integration fails
            if repo_url:
                return await self._legacy_install_module(module_name, repo_url)
            
            return False
        
        except Exception as e:
            self.logger.error(f"Failed to install module {module_name}: {e}")
            return False
    
    async def _legacy_install_module(self, module_name: str, repo_url: str) -> bool:
        """Legacy module installation method."""
        self.logger.info(f"Using legacy installation for module '{module_name}' from {repo_url}")
        
        try:
            # Create temporary directory for download
            with tempfile.TemporaryDirectory() as temp_dir:
                # Clone or download the repository
                if repo_url.endswith('.git') or 'github.com' in repo_url:
                    success = await self._download_from_git(repo_url, temp_dir, module_name)
                else:
                    success = await self._download_from_url(repo_url, temp_dir, module_name)
                
                if not success:
                    return False
                
                # Install the module
                return await self._install_module_files(temp_dir, module_name)
        
        except Exception as e:
            self.logger.error(f"Legacy installation failed for {module_name}: {e}")
            return False
    
    async def _download_from_git(self, repo_url: str, temp_dir: str, module_name: str) -> bool:
        """Download module from a Git repository."""
        try:
            # Try to clone the repository
            process = await asyncio.create_subprocess_exec(
                'git', 'clone', '--depth', '1', repo_url, temp_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                self.logger.error(f"Git clone failed: {stderr.decode()}")
                return False
            
            # Look for the specific module directory
            module_dir = os.path.join(temp_dir, module_name)
            if not os.path.exists(module_dir):
                # Try to find module.py in the root
                if os.path.exists(os.path.join(temp_dir, 'module.py')):
                    return True
                else:
                    self.logger.error(f"Module '{module_name}' not found in repository")
                    return False
            
            return True
            
        except FileNotFoundError:
            self.logger.error("Git not found. Please install Git or provide a direct download URL.")
            return False
        except Exception as e:
            self.logger.error(f"Git download failed: {e}")
            return False
    
    async def _download_from_url(self, url: str, temp_dir: str, module_name: str) -> bool:
        """Download module from a direct URL."""
        # This is a placeholder for HTTP download functionality
        self.logger.error("Direct URL download not yet implemented")
        return False
    
    async def _install_module_files(self, source_dir: str, module_name: str) -> bool:
        """Install module files to the cache directory."""
        try:
            cache_module_dir = os.path.join(self.config.module_cache_dir, module_name)
            
            # Remove existing module if it exists
            if os.path.exists(cache_module_dir):
                shutil.rmtree(cache_module_dir)
            
            # Copy module files
            if os.path.exists(os.path.join(source_dir, module_name)):
                # Module is in a subdirectory
                shutil.copytree(os.path.join(source_dir, module_name), cache_module_dir)
            else:
                # Module files are in the root
                os.makedirs(cache_module_dir)
                for file in os.listdir(source_dir):
                    if file.endswith('.py') or file == 'requirements.txt':
                        shutil.copy2(os.path.join(source_dir, file), cache_module_dir)
            
            # Install module dependencies if requirements.txt exists
            requirements_file = os.path.join(cache_module_dir, 'requirements.txt')
            if os.path.exists(requirements_file):
                await self._install_module_dependencies(requirements_file)
            
            # Load the installed module
            module_file = os.path.join(cache_module_dir, 'module.py')
            if os.path.exists(module_file):
                await self._load_module_from_file(module_file, module_name)
                self.logger.info(f"Successfully installed and loaded module: {module_name}")
                return True
            else:
                self.logger.error(f"No module.py found in installed module: {module_name}")
                return False
        
        except Exception as e:
            self.logger.error(f"Failed to install module files: {e}")
            return False
    
    async def _install_module_dependencies(self, requirements_file: str):
        """Install module dependencies from requirements.txt."""
        try:
            self.logger.info("Installing module dependencies...")
            
            process = await asyncio.create_subprocess_exec(
                sys.executable, '-m', 'pip', 'install', '-r', requirements_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                self.logger.warning(f"Some dependencies failed to install: {stderr.decode()}")
            else:
                self.logger.info("Dependencies installed successfully")
        
        except Exception as e:
            self.logger.warning(f"Failed to install dependencies: {e}")
    
    async def update_remote_modules(self):
        """Update all remote modules from their repositories."""
        cache_dir = Path(self.config.module_cache_dir)
        
        if not cache_dir.exists():
            return
        
        for module_dir in cache_dir.iterdir():
            if not module_dir.is_dir():
                continue
            
            module_info_file = module_dir / "module_info.json"
            if module_info_file.exists():
                try:
                    with open(module_info_file, 'r') as f:
                        info = json.load(f)
                    
                    repo_url = info.get('repository_url')
                    if repo_url:
                        self.logger.info(f"Updating module: {module_dir.name}")
                        await self.install_module_from_repo(module_dir.name, repo_url)
                
                except Exception as e:
                    self.logger.error(f"Failed to update module {module_dir.name}: {e}")
    
    def get_available_modules(self) -> Dict[str, Any]:
        """Get information about all available modules."""
        return self.module_info.copy()
    
    def get_command_handlers(self) -> Dict[str, Callable]:
        """Get all registered command handlers."""
        return self.command_handlers.copy()
    
    def unload_module(self, module_name: str) -> bool:
        """
        Unload a module and its command handlers.
        
        Args:
            module_name: Name of the module to unload
            
        Returns:
            True if module was unloaded successfully
        """
        if module_name not in self.loaded_modules:
            return False
        
        # Remove command handlers
        module = self.loaded_modules[module_name]
        if hasattr(module, 'get_commands'):
            commands = module.get_commands()
            for command_name in commands:
                if command_name in self.command_handlers:
                    del self.command_handlers[command_name]
        
        # Remove module references
        del self.loaded_modules[module_name]
        if module_name in self.module_info:
            del self.module_info[module_name]
        
        self.logger.info(f"Unloaded module: {module_name}")
        return True
    
    async def list_remote_modules(self, source_name: str = "primary") -> List[Dict[str, Any]]:
        """
        List available modules in a remote repository.
        
        Args:
            source_name: Name of the configured source to query
            
        Returns:
            List of available module information dictionaries
        """
        try:
            return await self.github_integration.list_available_modules(source_name)
        except Exception as e:
            self.logger.error(f"Failed to list remote modules: {e}")
            return []
    
    def get_github_sources(self) -> Dict[str, Any]:
        """Get configured GitHub sources."""
        return self.github_integration.github_config.get("module_sources", {})
    
    async def update_module_from_repo(self, module_name: str) -> bool:
        """
        Update an installed module from its repository.
        
        Args:
            module_name: Name of the module to update
            
        Returns:
            True if update was successful
        """
        try:
            return await self.github_integration.update_module(module_name)
        except Exception as e:
            self.logger.error(f"Failed to update module {module_name}: {e}")
            return False