"""
Virtual Environment management module for BuildCLI.
"""

import os
import sys
import json
import asyncio
import subprocess
import shutil
import urllib.request
import zipfile
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Callable, Optional, Tuple
import re


MODULE_INFO = {
    'name': 'venv',
    'version': '1.0.0',
    'description': 'Virtual environment management for BuildCLI',
    'author': 'BuildCLI',
    'commands': ['venv-create', 'venv-activate', 'venv-deactivate', 'venv-remove', 'venv-list', 'venv-repair', 'venv-replace', 'pip-install', 'pip-scan', 'python-install']
}


class VenvManager:
    """Manages virtual environments for BuildCLI."""
    
    def __init__(self, config_manager):
        self.config = config_manager
        self.venv_dir = Path.home() / ".buildcli" / "venvs"
        self.python_dir = Path.home() / ".buildcli" / "python"
        self.active_venv = None
        
        # Ensure directories exist
        self.venv_dir.mkdir(parents=True, exist_ok=True)
        self.python_dir.mkdir(parents=True, exist_ok=True)
    
    async def create_venv(self, name: str, python_version: Optional[str] = None, force: bool = False) -> bool:
        """Create a new virtual environment."""
        venv_path = self.venv_dir / name
        
        if venv_path.exists() and not force:
            print(f"Virtual environment '{name}' already exists. Use --force to overwrite.")
            return False
        
        if venv_path.exists() and force:
            print(f"Removing existing virtual environment '{name}'...")
            shutil.rmtree(venv_path)
        
        # Determine Python executable
        python_exe = await self._get_python_executable(python_version)
        if not python_exe:
            return False
        
        print(f"Creating virtual environment '{name}' with Python {python_version or 'system'}...")
        
        try:
            # Create virtual environment
            process = await asyncio.create_subprocess_exec(
                python_exe, '-m', 'venv', str(venv_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                print(f"Failed to create virtual environment: {stderr.decode()}")
                return False
            
            # Store environment info
            venv_info = {
                'name': name,
                'python_version': python_version or self._get_python_version(python_exe),
                'python_executable': python_exe,
                'created_date': self._get_current_timestamp(),
                'path': str(venv_path),
                'packages': []
            }
            
            self._save_venv_info(name, venv_info)
            print(f"✓ Virtual environment '{name}' created successfully")
            return True
        
        except Exception as e:
            print(f"Error creating virtual environment: {e}")
            return False
    
    async def _get_python_executable(self, version: Optional[str] = None) -> Optional[str]:
        """Get Python executable, installing if necessary."""
        if version is None:
            # Use system Python
            return sys.executable
        
        # Check if requested version is already available
        python_exe = self._find_python_version(version)
        if python_exe:
            return python_exe
        
        # Download and install Python version
        print(f"Python {version} not found. Downloading and installing...")
        return await self._install_python_version(version)
    
    def _find_python_version(self, version: str) -> Optional[str]:
        """Find Python executable for specific version."""
        # Check local Python directory first
        local_python = self.python_dir / f"python{version}" / "python.exe"
        if local_python.exists():
            return str(local_python)
        
        # Check system PATH
        possible_names = [
            f"python{version}",
            f"python{version.replace('.', '')}",
            "python"
        ]
        
        for name in possible_names:
            python_exe = shutil.which(name)
            if python_exe:
                actual_version = self._get_python_version(python_exe)
                if actual_version.startswith(version):
                    return python_exe
        
        return None
    
    def _get_python_version(self, python_exe: str) -> str:
        """Get Python version from executable."""
        try:
            result = subprocess.run(
                [python_exe, '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Extract version from "Python 3.9.7" format
                version_match = re.search(r'Python (\d+\.\d+\.\d+)', result.stdout)
                if version_match:
                    return version_match.group(1)
        except Exception:
            pass
        
        return "unknown"
    
    async def _install_python_version(self, version: str) -> Optional[str]:
        """Download and install specific Python version."""
        print(f"Installing Python {version}...")
        
        # This is a simplified implementation
        # In production, you'd want more robust Python installation
        try:
            if sys.platform == "win32":
                return await self._install_python_windows(version)
            else:
                return await self._install_python_unix(version)
        except Exception as e:
            print(f"Failed to install Python {version}: {e}")
            return None
    
    async def _install_python_windows(self, version: str) -> Optional[str]:
        """Install Python on Windows."""
        # Simplified Windows Python installation
        # In practice, you'd download from python.org
        print(f"Python {version} installation on Windows not yet implemented")
        print("Please install Python manually or use system Python")
        return None
    
    async def _install_python_unix(self, version: str) -> Optional[str]:
        """Install Python on Unix systems."""
        # Simplified Unix Python installation
        # In practice, you'd use pyenv or compile from source
        print(f"Python {version} installation on Unix not yet implemented")
        print("Please install Python manually or use system Python")
        return None
    
    def list_venvs(self) -> List[Dict[str, Any]]:
        """List all virtual environments."""
        venvs = []
        
        if not self.venv_dir.exists():
            return venvs
        
        for venv_path in self.venv_dir.iterdir():
            if venv_path.is_dir():
                info = self._load_venv_info(venv_path.name)
                if info:
                    venvs.append(info)
                else:
                    # Create basic info for environments without metadata
                    venvs.append({
                        'name': venv_path.name,
                        'path': str(venv_path),
                        'python_version': 'unknown',
                        'created_date': 'unknown',
                        'packages': []
                    })
        
        return venvs
    
    async def activate_venv(self, name: str) -> bool:
        """Activate a virtual environment."""
        venv_path = self.venv_dir / name
        
        if not venv_path.exists():
            print(f"Virtual environment '{name}' not found")
            return False
        
        # Store active environment
        self.active_venv = name
        self.config.set("active_venv", name)
        self.config.save_config()
        
        # Get activation script path
        if sys.platform == "win32":
            activate_script = venv_path / "Scripts" / "activate.bat"
        else:
            activate_script = venv_path / "bin" / "activate"
        
        print(f"✓ Virtual environment '{name}' activated")
        print(f"To activate in your shell, run: {activate_script}")
        
        # Set environment variables for subprocess calls
        venv_python = self._get_venv_python(name)
        if venv_python:
            os.environ["VIRTUAL_ENV"] = str(venv_path)
            os.environ["PATH"] = f"{venv_python.parent}{os.pathsep}{os.environ.get('PATH', '')}"
        
        return True
    
    def deactivate_venv(self) -> bool:
        """Deactivate the current virtual environment."""
        if not self.active_venv:
            print("No virtual environment is currently active")
            return False
        
        print(f"✓ Deactivated virtual environment '{self.active_venv}'")
        
        # Clear environment variables
        if "VIRTUAL_ENV" in os.environ:
            del os.environ["VIRTUAL_ENV"]
        
        self.active_venv = None
        self.config.set("active_venv", None)
        self.config.save_config()
        
        return True
    
    async def remove_venv(self, name: str, force: bool = False) -> bool:
        """Remove a virtual environment."""
        venv_path = self.venv_dir / name
        
        if not venv_path.exists():
            print(f"Virtual environment '{name}' not found")
            return False
        
        if not force:
            print(f"This will permanently delete virtual environment '{name}'")
            print("Use --force to confirm deletion")
            return False
        
        try:
            if self.active_venv == name:
                self.deactivate_venv()
            
            shutil.rmtree(venv_path)
            
            # Remove from config
            venvs = self.config.get("virtual_environments", {})
            if name in venvs:
                del venvs[name]
                self.config.set("virtual_environments", venvs)
                self.config.save_config()
            
            print(f"✓ Virtual environment '{name}' removed")
            return True
        
        except Exception as e:
            print(f"Error removing virtual environment: {e}")
            return False
    
    async def repair_venv(self, name: str) -> bool:
        """Repair a virtual environment."""
        venv_info = self._load_venv_info(name)
        if not venv_info:
            print(f"Virtual environment '{name}' not found")
            return False
        
        print(f"Repairing virtual environment '{name}'...")
        
        # Recreate the environment
        python_version = venv_info.get('python_version')
        success = await self.create_venv(name, python_version, force=True)
        
        if success:
            # Reinstall packages
            packages = venv_info.get('packages', [])
            if packages:
                print("Reinstalling packages...")
                await self.pip_install_packages(name, packages)
        
        return success
    
    async def replace_venv(self, name: str, new_python_version: str) -> bool:
        """Replace a virtual environment with a different Python version."""
        print(f"Replacing virtual environment '{name}' with Python {new_python_version}...")
        
        # Get current packages
        venv_info = self._load_venv_info(name)
        packages = venv_info.get('packages', []) if venv_info else []
        
        # Remove old environment
        success = await self.remove_venv(name, force=True)
        if not success:
            return False
        
        # Create new environment
        success = await self.create_venv(name, new_python_version)
        if not success:
            return False
        
        # Reinstall packages
        if packages:
            print("Reinstalling packages...")
            await self.pip_install_packages(name, packages)
        
        return True
    
    def _get_venv_python(self, name: str) -> Optional[Path]:
        """Get Python executable path for virtual environment."""
        venv_path = self.venv_dir / name
        
        if sys.platform == "win32":
            python_exe = venv_path / "Scripts" / "python.exe"
        else:
            python_exe = venv_path / "bin" / "python"
        
        return python_exe if python_exe.exists() else None
    
    async def pip_install_packages(self, venv_name: str, packages: List[str]) -> bool:
        """Install packages in virtual environment."""
        python_exe = self._get_venv_python(venv_name)
        if not python_exe:
            print(f"Virtual environment '{venv_name}' not found")
            return False
        
        print(f"Installing packages in '{venv_name}': {', '.join(packages)}")
        
        try:
            # Install packages
            cmd = [str(python_exe), '-m', 'pip', 'install'] + packages
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            
            # Stream output
            if process.stdout:
                while True:
                    line = await process.stdout.readline()
                    if not line:
                        break
                    print(line.decode().strip())
            
            await process.wait()
            
            if process.returncode == 0:
                # Update package list
                self._update_venv_packages(venv_name, packages)
                print("✓ Packages installed successfully")
                return True
            else:
                print("✗ Package installation failed")
                return False
        
        except Exception as e:
            print(f"Error installing packages: {e}")
            return False
    
    async def pip_install_requirements(self, venv_name: str, requirements_file: str) -> bool:
        """Install packages from requirements.txt file."""
        if not os.path.exists(requirements_file):
            print(f"Requirements file not found: {requirements_file}")
            return False
        
        python_exe = self._get_venv_python(venv_name)
        if not python_exe:
            print(f"Virtual environment '{venv_name}' not found")
            return False
        
        print(f"Installing requirements from {requirements_file} in '{venv_name}'...")
        
        try:
            cmd = [str(python_exe), '-m', 'pip', 'install', '-r', requirements_file]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            
            # Stream output
            if process.stdout:
                while True:
                    line = await process.stdout.readline()
                    if not line:
                        break
                    print(line.decode().strip())
            
            await process.wait()
            
            if process.returncode == 0:
                print("✓ Requirements installed successfully")
                return True
            else:
                print("✗ Requirements installation failed")
                return False
        
        except Exception as e:
            print(f"Error installing requirements: {e}")
            return False
    
    async def scan_project_dependencies(self, project_path: str = ".") -> List[str]:
        """Scan project for Python dependencies."""
        print(f"Scanning project at {project_path} for dependencies...")
        
        dependencies = set()
        project_dir = Path(project_path)
        
        # Common patterns for import statements
        import_patterns = [
            r'^import\s+(\w+)',
            r'^from\s+(\w+)',
        ]
        
        # Scan Python files
        for py_file in project_dir.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                for line in content.split('\n'):
                    line = line.strip()
                    for pattern in import_patterns:
                        match = re.match(pattern, line)
                        if match:
                            module_name = match.group(1)
                            # Skip standard library and relative imports
                            if not module_name.startswith('.') and module_name not in self._get_stdlib_modules():
                                dependencies.add(module_name)
            
            except Exception as e:
                print(f"Warning: Could not scan {py_file}: {e}")
        
        # Filter to actual PyPI packages
        filtered_deps = []
        for dep in dependencies:
            if await self._is_pypi_package(dep):
                filtered_deps.append(dep)
        
        print(f"Found {len(filtered_deps)} potential dependencies:")
        for dep in sorted(filtered_deps):
            print(f"  - {dep}")
        
        return sorted(filtered_deps)
    
    def _get_stdlib_modules(self) -> set:
        """Get standard library module names."""
        # This is a simplified list - in practice you'd want a more comprehensive list
        return {
            'os', 'sys', 'json', 'time', 'datetime', 'pathlib', 'subprocess',
            'asyncio', 'threading', 'multiprocessing', 'collections', 'itertools',
            'functools', 'operator', 're', 'math', 'random', 'statistics',
            'urllib', 'http', 'email', 'html', 'xml', 'csv', 'sqlite3',
            'logging', 'unittest', 'argparse', 'configparser', 'pickle',
            'base64', 'hashlib', 'hmac', 'secrets', 'uuid', 'tempfile',
            'shutil', 'glob', 'fnmatch', 'io', 'struct', 'codecs'
        }
    
    async def _is_pypi_package(self, package_name: str) -> bool:
        """Check if a package is available on PyPI."""
        # This is a simplified check - in practice you'd query PyPI API
        # For now, assume non-stdlib modules are PyPI packages
        return package_name not in self._get_stdlib_modules()
    
    def _save_venv_info(self, name: str, info: Dict[str, Any]) -> None:
        """Save virtual environment information."""
        venvs = self.config.get("virtual_environments", {})
        venvs[name] = info
        self.config.set("virtual_environments", venvs)
        self.config.save_config()
    
    def _load_venv_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Load virtual environment information."""
        venvs = self.config.get("virtual_environments", {})
        return venvs.get(name)
    
    def _update_venv_packages(self, name: str, packages: List[str]) -> None:
        """Update package list for virtual environment."""
        venv_info = self._load_venv_info(name)
        if venv_info:
            existing_packages = set(venv_info.get('packages', []))
            existing_packages.update(packages)
            venv_info['packages'] = list(existing_packages)
            self._save_venv_info(name, venv_info)
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp string."""
        from datetime import datetime
        return datetime.now().isoformat()


# Global manager instance
_venv_manager = None


def get_venv_manager():
    """Get global virtual environment manager."""
    global _venv_manager
    if _venv_manager is None:
        from core.config import Config
        config = Config()
        _venv_manager = VenvManager(config)
    return _venv_manager


# Command implementations
async def venv_create_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Create virtual environment command."""
    if not args:
        print("Usage: venv-create <name> [--version <python_version>] [--force]")
        return False
    
    name = args[0]
    python_version = modifiers.get('version')
    force = modifiers.get('force', False)
    
    if modifiers.get('dry_run', False):
        print(f"[DRY RUN] Would create virtual environment '{name}' with Python {python_version or 'system'}")
        return True
    
    manager = get_venv_manager()
    return await manager.create_venv(name, python_version, force)


async def venv_activate_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Activate virtual environment command."""
    if not args:
        print("Usage: venv-activate <name>")
        return False
    
    name = args[0]
    
    if modifiers.get('dry_run', False):
        print(f"[DRY RUN] Would activate virtual environment '{name}'")
        return True
    
    manager = get_venv_manager()
    return await manager.activate_venv(name)


async def venv_deactivate_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Deactivate virtual environment command."""
    if modifiers.get('dry_run', False):
        print("[DRY RUN] Would deactivate current virtual environment")
        return True
    
    manager = get_venv_manager()
    return manager.deactivate_venv()


async def venv_remove_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Remove virtual environment command."""
    if not args:
        print("Usage: venv-remove <name> [--force]")
        return False
    
    name = args[0]
    force = modifiers.get('force', False)
    
    if modifiers.get('dry_run', False):
        print(f"[DRY RUN] Would remove virtual environment '{name}'")
        return True
    
    manager = get_venv_manager()
    return await manager.remove_venv(name, force)


async def venv_list_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """List virtual environments command."""
    manager = get_venv_manager()
    venvs = manager.list_venvs()
    
    if not venvs:
        print("No virtual environments found")
        return True
    
    print(f"Found {len(venvs)} virtual environment(s):")
    print()
    
    for venv in venvs:
        active_marker = " (active)" if venv['name'] == manager.active_venv else ""
        print(f"  {venv['name']}{active_marker}")
        print(f"    Python: {venv.get('python_version', 'unknown')}")
        print(f"    Path: {venv['path']}")
        print(f"    Created: {venv.get('created_date', 'unknown')}")
        packages = venv.get('packages', [])
        if packages:
            print(f"    Packages: {len(packages)} installed")
        print()
    
    return True


async def venv_repair_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Repair virtual environment command."""
    if not args:
        print("Usage: venv-repair <name>")
        return False
    
    name = args[0]
    
    if modifiers.get('dry_run', False):
        print(f"[DRY RUN] Would repair virtual environment '{name}'")
        return True
    
    manager = get_venv_manager()
    return await manager.repair_venv(name)


async def venv_replace_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Replace virtual environment command."""
    if len(args) < 2:
        print("Usage: venv-replace <name> <new_python_version>")
        return False
    
    name = args[0]
    new_version = args[1]
    
    if modifiers.get('dry_run', False):
        print(f"[DRY RUN] Would replace virtual environment '{name}' with Python {new_version}")
        return True
    
    manager = get_venv_manager()
    return await manager.replace_venv(name, new_version)


async def pip_install_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Pip install command."""
    manager = get_venv_manager()
    
    # Check if we have an active virtual environment
    if not manager.active_venv:
        # Try to get from command arguments
        venv_name = modifiers.get('venv')
        if not venv_name:
            print("No active virtual environment. Specify with --venv <name> or activate one first.")
            return False
    else:
        venv_name = manager.active_venv
    
    if not args:
        print("Usage: pip-install <package1> [package2] ... [--venv <venv_name>]")
        print("   or: pip-install --requirements <requirements.txt> [--venv <venv_name>]")
        return False
    
    if modifiers.get('dry_run', False):
        if modifiers.get('requirements'):
            print(f"[DRY RUN] Would install requirements from {modifiers['requirements']} in '{venv_name}'")
        else:
            print(f"[DRY RUN] Would install packages {args} in '{venv_name}'")
        return True
    
    # Install from requirements file
    if modifiers.get('requirements'):
        return await manager.pip_install_requirements(venv_name, modifiers['requirements'])
    
    # Install individual packages
    return await manager.pip_install_packages(venv_name, args)


async def pip_scan_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Pip scan command."""
    project_path = args[0] if args else "."
    
    if modifiers.get('dry_run', False):
        print(f"[DRY RUN] Would scan project at {project_path} for dependencies")
        return True
    
    manager = get_venv_manager()
    dependencies = await manager.scan_project_dependencies(project_path)
    
    # Optionally install found dependencies
    if modifiers.get('install', False) and dependencies:
        venv_name = modifiers.get('venv') or manager.active_venv
        if venv_name:
            print(f"\nInstalling found dependencies in '{venv_name}'...")
            return await manager.pip_install_packages(venv_name, dependencies)
        else:
            print("\nNo active virtual environment to install packages")
    
    return True


async def python_install_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Python install command."""
    if not args:
        print("Usage: python-install <version>")
        print("Example: python-install 3.9.7")
        return False
    
    version = args[0]
    
    if modifiers.get('dry_run', False):
        print(f"[DRY RUN] Would install Python {version}")
        return True
    
    manager = get_venv_manager()
    python_exe = await manager._install_python_version(version)
    
    if python_exe:
        print(f"✓ Python {version} installed successfully at {python_exe}")
        return True
    else:
        print(f"✗ Failed to install Python {version}")
        return False


# Command registration function
async def register_commands() -> Dict[str, Callable]:
    """Register all commands provided by this module."""
    return {
        'venv-create': venv_create_command,
        'venv-activate': venv_activate_command,
        'venv-deactivate': venv_deactivate_command,
        'venv-remove': venv_remove_command,
        'venv-list': venv_list_command,
        'venv-repair': venv_repair_command,
        'venv-replace': venv_replace_command,
        'pip-install': pip_install_command,
        'pip-scan': pip_scan_command,
        'python-install': python_install_command,
    }


# Alternative function name for compatibility
def get_commands() -> List[str]:
    """Get list of command names provided by this module."""
    return MODULE_INFO['commands']