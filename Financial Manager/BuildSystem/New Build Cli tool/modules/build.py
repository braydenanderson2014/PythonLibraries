"""
Build System Module for BuildCLI

Provides comprehensive build functionality with configuration memory and support
for multiple build systems including PyInstaller, cx_Freeze, Nuitka, and custom build scripts.

The build system maintains configuration state across commands, allowing users to
build up complex build configurations step by step.
"""

# Module information for BuildCLI
MODULE_INFO = {
    'name': 'build',
    'version': '1.0.0',
    'description': 'Comprehensive build system with configuration memory and multi-system support',
    'author': 'BuildCLI Team',
    'commands': [
        'build-config', 'build-source', 'build-name', 'build-version', 'build-icon',
        'build-onefile', 'build-console', 'build-windowed', 'build-splash', 'build-metadata',
        'build-hidden-imports', 'build-data-files', 'build-execute', 'build-preview',
        'build-collect-files', 'build-advanced-options', 'build-cx-freeze-options',
        'build-nuitka-options', 'build-list', 'build-show', 'build-reset', 'build-delete', 'build-systems'
    ]
}

import asyncio
import json
import os
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import subprocess
import shutil

from utils.logger import Logger

logger = Logger().logger


def parse_args(args: List[str], arg_names: List[str]) -> Dict[str, str]:
    """Parse positional arguments into a dictionary."""
    parsed = {}
    for i, arg_name in enumerate(arg_names):
        if i < len(args):
            parsed[arg_name] = args[i]
    return parsed

@dataclass
class BuildConfig:
    """Comprehensive configuration for a build process with full PyInstaller support."""
    name: str
    build_system: str  # pyinstaller, cx_freeze, nuitka, custom
    
    # Basic file configuration
    source_file: Optional[str] = None
    output_name: Optional[str] = None
    output_dir: Optional[str] = None
    
    # Application metadata
    version: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = None
    company: Optional[str] = None
    copyright: Optional[str] = None
    
    # PyInstaller core options
    icon: Optional[str] = None
    console: bool = True
    onefile: bool = False
    windowed: bool = False  # --windowed / --noconsole
    
    # Advanced PyInstaller options
    hidden_imports: Optional[List[str]] = None
    additional_hooks: Optional[List[str]] = None
    exclude_modules: Optional[List[str]] = None
    collect_submodules: Optional[List[str]] = None
    collect_data: Optional[List[str]] = None
    collect_binaries: Optional[List[str]] = None
    collect_all: Optional[List[str]] = None
    copy_metadata: Optional[List[str]] = None
    recursive_copy_metadata: Optional[List[str]] = None
    
    # File inclusions
    data_files: Optional[List[tuple]] = None  # (source, dest) pairs
    binary_files: Optional[List[tuple]] = None  # (source, dest) pairs
    splash: Optional[str] = None  # Splash screen image
    
    # Build behavior
    upx: bool = False
    upx_exclude: Optional[List[str]] = None
    debug: bool = False
    debug_imports: bool = False
    debug_bootloader: bool = False
    clean: bool = True
    noconfirm: bool = True
    
    # Paths
    distpath: Optional[str] = None
    workpath: Optional[str] = None
    specpath: Optional[str] = None
    paths: Optional[List[str]] = None  # Additional Python paths
    
    # Runtime options
    runtime_tmpdir: Optional[str] = None
    bootloader_ignore_signals: bool = False
    
    # Advanced features
    key: Optional[str] = None  # Encryption key
    noupx: bool = False
    strip: bool = False
    
    # Windows specific
    version_file: Optional[str] = None
    manifest: Optional[str] = None
    resource: Optional[List[str]] = None
    uac_admin: bool = False
    uac_uiaccess: bool = False
    
    # macOS specific  
    osx_bundle_identifier: Optional[str] = None
    target_architecture: Optional[str] = None
    codesign_identity: Optional[str] = None
    osx_entitlements_file: Optional[str] = None
    
    # cx_Freeze specific options
    cx_freeze_base: Optional[str] = None  # Base executable (Console, Win32GUI, etc.)
    cx_freeze_init_script: Optional[str] = None  # Custom init script
    cx_freeze_target_name: Optional[str] = None  # Target executable name
    cx_freeze_shortcut_name: Optional[str] = None  # Windows shortcut name
    cx_freeze_shortcut_dir: Optional[str] = None  # Shortcut directory
    cx_freeze_includes: Optional[List[str]] = None  # Modules to include
    cx_freeze_excludes: Optional[List[str]] = None  # Modules to exclude
    cx_freeze_packages: Optional[List[str]] = None  # Packages to include
    cx_freeze_replace_paths: Optional[List[tuple]] = None  # Path replacements
    cx_freeze_zip_include_packages: Optional[List[str]] = None  # Packages to zip
    cx_freeze_optimize: Optional[int] = None  # Optimization level (0, 1, 2)
    cx_freeze_compress: bool = False  # Compress library
    cx_freeze_create_shared_zip: bool = True  # Create shared zip file
    cx_freeze_include_msvcrt: bool = False  # Include MSVCRT
    cx_freeze_silent: bool = False  # Silent mode
    
    # Nuitka specific options
    nuitka_standalone: bool = False  # Create standalone distribution
    nuitka_onefile: bool = False  # Create single file
    nuitka_output_dir: Optional[str] = None  # Output directory
    nuitka_output_filename: Optional[str] = None  # Output filename
    nuitka_module: bool = False  # Create extension module
    nuitka_package: Optional[str] = None  # Create package
    nuitka_include_plugin_directory: Optional[List[str]] = None  # Plugin directories
    nuitka_include_plugin_files: Optional[List[str]] = None  # Plugin files
    nuitka_user_plugin: Optional[List[str]] = None  # User plugins
    nuitka_plugin_enable: Optional[List[str]] = None  # Enable plugins
    nuitka_plugin_disable: Optional[List[str]] = None  # Disable plugins
    nuitka_follow_imports: bool = True  # Follow all imports
    nuitka_follow_import_to: Optional[List[str]] = None  # Follow specific imports
    nuitka_nofollow_imports: bool = False  # Don't follow any imports
    nuitka_nofollow_import_to: Optional[List[str]] = None  # Don't follow specific imports
    nuitka_include_package: Optional[List[str]] = None  # Include packages
    nuitka_include_module: Optional[List[str]] = None  # Include modules
    nuitka_include_package_data: Optional[List[str]] = None  # Include package data
    nuitka_include_data_files: Optional[List[tuple]] = None  # Include data files
    nuitka_include_data_dir: Optional[List[tuple]] = None  # Include data directories
    nuitka_noinclude_default_mode: Optional[str] = None  # Default inclusion mode
    nuitka_warn_implicit_exceptions: bool = False  # Warn about exceptions
    nuitka_warn_unusual_code: bool = False  # Warn about unusual code
    nuitka_assume_yes_for_downloads: bool = False  # Auto-confirm downloads
    nuitka_disable_console: bool = False  # Disable console window
    nuitka_enable_console: bool = False  # Force enable console
    nuitka_force_stdout_spec: Optional[str] = None  # Force stdout specification
    nuitka_force_stderr_spec: Optional[str] = None  # Force stderr specification
    nuitka_windows_dependency_tool: Optional[str] = None  # Windows dependency tool
    nuitka_mingw64: bool = False  # Use MinGW64
    nuitka_msvc: Optional[str] = None  # MSVC version
    nuitka_jobs: Optional[int] = None  # Parallel compilation jobs
    nuitka_lto: Optional[str] = None  # Link Time Optimization
    nuitka_clang: bool = False  # Use Clang
    nuitka_disable_ccache: bool = False  # Disable ccache
    nuitka_experimental: Optional[List[str]] = None  # Experimental features
    
    # Custom and extensibility
    custom_options: Optional[Dict[str, Any]] = None
    environment_vars: Optional[Dict[str, str]] = None
    pre_build_commands: Optional[List[str]] = None
    post_build_commands: Optional[List[str]] = None
    
    # Scanning integration - collected file paths
    scanned_files: Optional[Dict[str, List[str]]] = None  # File type -> paths mapping
    scan_metadata: Optional[Dict[str, Any]] = None  # Metadata from scanning
    
    # Metadata
    created_date: Optional[str] = None
    last_modified: Optional[str] = None
    last_build: Optional[str] = None
    build_count: int = 0

    def __post_init__(self):
        """Initialize default values for mutable fields."""
        if self.hidden_imports is None:
            self.hidden_imports = []
        if self.additional_hooks is None:
            self.additional_hooks = []
        if self.exclude_modules is None:
            self.exclude_modules = []
        if self.data_files is None:
            self.data_files = []
        if self.binary_files is None:
            self.binary_files = []
        if self.custom_options is None:
            self.custom_options = {}
        if self.environment_vars is None:
            self.environment_vars = {}
        if self.pre_build_commands is None:
            self.pre_build_commands = []
        if self.post_build_commands is None:
            self.post_build_commands = []
        if self.created_date is None:
            self.created_date = datetime.now().isoformat()


class BuildSystemManager:
    """Manages different build systems and configurations."""
    
    SUPPORTED_SYSTEMS = {
        'pyinstaller': 'PyInstaller - Python to executable converter',
        'cx_freeze': 'cx_Freeze - Cross-platform Python to executable',
        'nuitka': 'Nuitka - Python compiler to C++',
        'custom': 'Custom build script execution'
    }
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager
        self.config_dir = Path.home() / '.buildcli' / 'build_configs'
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.current_config: Optional[BuildConfig] = None
        self.active_config_name: Optional[str] = None
        self._load_active_config()
    
    def _get_active_config_file(self) -> Path:
        """Get the active configuration file path."""
        return self.config_dir / "active.txt"
    
    def _save_active_config(self) -> None:
        """Save the active configuration name to disk."""
        try:
            if self.active_config_name:
                with open(self._get_active_config_file(), 'w', encoding='utf-8') as f:
                    f.write(self.active_config_name)
        except Exception:
            pass  # Silently ignore errors
    
    def _load_active_config(self) -> None:
        """Load the active configuration from disk."""
        try:
            active_file = self._get_active_config_file()
            if active_file.exists():
                with open(active_file, 'r', encoding='utf-8') as f:
                    name = f.read().strip()
                if name:
                    config = self.load_config(name)
                    if config:
                        self.current_config = config
                        self.active_config_name = name
        except Exception:
            pass  # Silently ignore errors
    
    def get_config_file(self, name: str) -> Path:
        """Get the configuration file path for a given name."""
        return self.config_dir / f"{name}.json"
    
    def save_config(self, config: BuildConfig) -> bool:
        """Save a build configuration to disk."""
        try:
            config.last_modified = datetime.now().isoformat()
            config_file = self.get_config_file(config.name)
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(config), f, indent=2, default=str)
            
            logger.info(f"Build configuration '{config.name}' saved")
            return True
        except Exception as e:
            logger.error(f"Failed to save build configuration: {e}")
            return False
    
    def load_config(self, name: str) -> Optional[BuildConfig]:
        """Load a build configuration from disk."""
        try:
            config_file = self.get_config_file(name)
            if not config_file.exists():
                return None
                
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            config = BuildConfig(**data)
            logger.info(f"Build configuration '{name}' loaded")
            return config
        except Exception as e:
            logger.error(f"Failed to load build configuration '{name}': {e}")
            return None
    
    def list_configs(self) -> List[str]:
        """List all available build configurations."""
        configs = []
        for config_file in self.config_dir.glob("*.json"):
            configs.append(config_file.stem)
        return sorted(configs)
    
    def delete_config(self, name: str) -> bool:
        """Delete a build configuration."""
        try:
            config_file = self.get_config_file(name)
            if config_file.exists():
                config_file.unlink()
                if self.active_config_name == name:
                    self.current_config = None
                    self.active_config_name = None
                logger.info(f"Build configuration '{name}' deleted")
                return True
            else:
                logger.warning(f"Build configuration '{name}' not found")
                return False
        except Exception as e:
            logger.error(f"Failed to delete build configuration '{name}': {e}")
            return False
    
    def set_active_config(self, name: str, build_system: str = 'pyinstaller') -> BuildConfig:
        """Set or create the active build configuration."""
        config = self.load_config(name)
        if not config:
            config = BuildConfig(name=name, build_system=build_system)
            self.save_config(config)  # Save newly created config to disk
            logger.info(f"Created new build configuration '{name}' using {build_system}")
        else:
            logger.info(f"Loaded existing build configuration '{name}'")
        
        self.current_config = config
        self.active_config_name = name
        self._save_active_config()  # Persist active config choice
        return config
    
    def get_active_config(self) -> Optional[BuildConfig]:
        """Get the currently active build configuration."""
        return self.current_config
    
    def reset_config(self, name: Optional[str] = None) -> bool:
        """Reset the current configuration or create a new one."""
        if name is None and self.active_config_name:
            name = self.active_config_name
        
        if name:
            # Reset to a fresh configuration
            build_system = self.current_config.build_system if self.current_config else 'pyinstaller'
            self.current_config = BuildConfig(name=name, build_system=build_system)
            self.active_config_name = name
            logger.info(f"Reset build configuration '{name}'")
            return True
        else:
            logger.error("No active configuration to reset")
            return False
    
    async def check_build_system_availability(self, system: str) -> bool:
        """Check if a build system is available."""
        try:
            if system == 'pyinstaller':
                try:
                    import PyInstaller
                    return True
                except ImportError:
                    return False
            
            elif system == 'cx_freeze':
                try:
                    import importlib.util
                    return importlib.util.find_spec('cx_Freeze') is not None
                except ImportError:
                    return False
            
            elif system == 'nuitka':
                try:
                    import importlib.util
                    return importlib.util.find_spec('nuitka') is not None
                except ImportError:
                    return False
            
            elif system == 'custom':
                return True  # Custom scripts are always "available"
            
            return False
        except Exception:
            return False
        
        return available_systems
    
    def _build_pyinstaller_command(self, config: BuildConfig) -> List[str]:
        """Build comprehensive PyInstaller command with all options."""
        cmd = [sys.executable, '-m', 'PyInstaller']
        
        # Core build modes
        if config.onefile:
            cmd.append('--onefile')
        if config.windowed or not config.console:
            cmd.append('--windowed')
        
        # Output configuration
        if config.output_name:
            cmd.extend(['--name', config.output_name])
        if config.distpath:
            cmd.extend(['--distpath', config.distpath])
        if config.workpath:
            cmd.extend(['--workpath', config.workpath])
        if config.specpath:
            cmd.extend(['--specpath', config.specpath])
        
        # Icon and splash
        if config.icon and Path(config.icon).exists():
            cmd.extend(['--icon', config.icon])
        if config.splash and Path(config.splash).exists():
            cmd.extend(['--splash', config.splash])
        
        # Import and module handling
        if config.hidden_imports:
            for import_name in config.hidden_imports:
                cmd.extend(['--hidden-import', import_name])
        
        if config.collect_submodules:
            for module in config.collect_submodules:
                cmd.extend(['--collect-submodules', module])
        
        if config.collect_data:
            for package in config.collect_data:
                cmd.extend(['--collect-data', package])
        
        if config.collect_binaries:
            for package in config.collect_binaries:
                cmd.extend(['--collect-binaries', package])
        
        if config.collect_all:
            for package in config.collect_all:
                cmd.extend(['--collect-all', package])
        
        if config.copy_metadata:
            for package in config.copy_metadata:
                cmd.extend(['--copy-metadata', package])
        
        if config.recursive_copy_metadata:
            for package in config.recursive_copy_metadata:
                cmd.extend(['--recursive-copy-metadata', package])
        
        # Hooks and exclusions
        if config.additional_hooks:
            for hook in config.additional_hooks:
                cmd.extend(['--additional-hooks-dir', hook])
        
        if config.exclude_modules:
            for module in config.exclude_modules:
                cmd.extend(['--exclude-module', module])
        
        # File inclusions from scanning or manual
        if config.data_files:
            for src, dst in config.data_files:
                cmd.extend(['--add-data', f"{src}{os.pathsep}{dst}"])
        
        if config.binary_files:
            for src, dst in config.binary_files:
                cmd.extend(['--add-binary', f"{src}{os.pathsep}{dst}"])
        
        # Include scanned files automatically
        if config.scanned_files:
            # Auto-include documentation files
            if 'documentation' in config.scanned_files:
                for doc_file in config.scanned_files['documentation']:
                    cmd.extend(['--add-data', f"{doc_file}{os.pathsep}."])
            
            # Auto-include configuration files
            if 'config' in config.scanned_files:
                for conf_file in config.scanned_files['config']:
                    cmd.extend(['--add-data', f"{conf_file}{os.pathsep}."])
            
            # Auto-include data files
            if 'data' in config.scanned_files:
                for data_file in config.scanned_files['data']:
                    cmd.extend(['--add-data', f"{data_file}{os.pathsep}."])
            
            # Auto-include assets (except already handled icon/splash)
            if 'assets' in config.scanned_files:
                for asset_file in config.scanned_files['assets']:
                    # Skip if already used as icon or splash
                    if (config.icon and os.path.samefile(asset_file, config.icon)):
                        continue
                    if (config.splash and os.path.samefile(asset_file, config.splash)):
                        continue
                    cmd.extend(['--add-data', f"{asset_file}{os.pathsep}assets"])
        
        # Python paths
        if config.paths:
            for path in config.paths:
                cmd.extend(['--paths', path])
        
        # Build behavior
        if config.clean:
            cmd.append('--clean')
        if config.noconfirm:
            cmd.append('--noconfirm')
        
        # Debug options
        if config.debug:
            cmd.append('--debug')
        if config.debug_imports:
            cmd.append('--debug-imports')
        if config.debug_bootloader:
            cmd.append('--debug-bootloader')
        
        # UPX options
        if config.upx:
            cmd.append('--upx-dir')
        if config.noupx:
            cmd.append('--noupx')
        if config.upx_exclude:
            for item in config.upx_exclude:
                cmd.extend(['--upx-exclude', item])
        
        # Advanced options
        if config.strip:
            cmd.append('--strip')
        if config.key:
            cmd.extend(['--key', config.key])
        
        # Runtime options
        if config.runtime_tmpdir:
            cmd.extend(['--runtime-tmpdir', config.runtime_tmpdir])
        if config.bootloader_ignore_signals:
            cmd.append('--bootloader-ignore-signals')
        
        # Windows specific
        if config.version_file and Path(config.version_file).exists():
            cmd.extend(['--version-file', config.version_file])
        if config.manifest and Path(config.manifest).exists():
            cmd.extend(['--manifest', config.manifest])
        if config.resource:
            for resource in config.resource:
                cmd.extend(['--resource', resource])
        if config.uac_admin:
            cmd.append('--uac-admin')
        if config.uac_uiaccess:
            cmd.append('--uac-uiaccess')
        
        # macOS specific
        if config.osx_bundle_identifier:
            cmd.extend(['--osx-bundle-identifier', config.osx_bundle_identifier])
        if config.target_architecture:
            cmd.extend(['--target-arch', config.target_architecture])
        if config.codesign_identity:
            cmd.extend(['--codesign-identity', config.codesign_identity])
        if config.osx_entitlements_file and Path(config.osx_entitlements_file).exists():
            cmd.extend(['--osx-entitlements-file', config.osx_entitlements_file])
        
        # Custom options (for future extensibility)
        if config.custom_options:
            for option, value in config.custom_options.items():
                if value is True:
                    cmd.append(f'--{option}')
                elif value is not False and value is not None:
                    cmd.extend([f'--{option}', str(value)])
        
        # Source file (must be last)
        if config.source_file:
            cmd.append(config.source_file)
        
        return cmd
    
    def _build_cx_freeze_command(self, config: BuildConfig) -> List[str]:
        """Build comprehensive cx_Freeze command with all options."""
        cmd = [sys.executable, '-m', 'cx_Freeze']
        
        # Basic source file
        if config.source_file:
            cmd.append(config.source_file)
        
        # Output options
        if config.output_name or config.cx_freeze_target_name:
            name = config.cx_freeze_target_name or config.output_name
            if name:
                cmd.extend(['--target-name', name])
        
        if config.output_dir or config.distpath:
            dir_path = config.output_dir or config.distpath
            if dir_path:
                cmd.extend(['--target-dir', dir_path])
        
        # Base executable type
        if config.cx_freeze_base:
            cmd.extend(['--base', config.cx_freeze_base])
        elif config.console:
            cmd.extend(['--base', 'Console'])
        elif config.windowed:
            cmd.extend(['--base', 'Win32GUI'])
        
        # Icon
        if config.icon and Path(config.icon).exists():
            cmd.extend(['--icon', config.icon])
        
        # Includes and excludes
        if config.cx_freeze_includes:
            for include in config.cx_freeze_includes:
                cmd.extend(['--include', include])
        
        if config.cx_freeze_excludes:
            for exclude in config.cx_freeze_excludes:
                cmd.extend(['--exclude', exclude])
        
        if config.cx_freeze_packages:
            for package in config.cx_freeze_packages:
                cmd.extend(['--package', package])
        
        # Scanning integration for includes
        if config.scanned_files:
            # Auto-include Python files found during scanning
            if 'python' in config.scanned_files:
                for py_file in config.scanned_files['python']:
                    if py_file != config.source_file:  # Don't include main file twice
                        module_name = Path(py_file).stem
                        cmd.extend(['--include', module_name])
        
        # Data files from scanning or manual
        if config.data_files:
            for src, dst in config.data_files:
                cmd.extend(['--include-file', f"{src}={dst}"])
        
        # Include scanned files automatically
        if config.scanned_files:
            # Auto-include documentation files
            if 'documentation' in config.scanned_files:
                for doc_file in config.scanned_files['documentation']:
                    filename = Path(doc_file).name
                    cmd.extend(['--include-file', f"{doc_file}={filename}"])
            
            # Auto-include configuration files
            if 'config' in config.scanned_files:
                for conf_file in config.scanned_files['config']:
                    filename = Path(conf_file).name
                    cmd.extend(['--include-file', f"{conf_file}={filename}"])
            
            # Auto-include data files
            if 'data' in config.scanned_files:
                for data_file in config.scanned_files['data']:
                    filename = Path(data_file).name
                    cmd.extend(['--include-file', f"{data_file}={filename}"])
        
        # Path replacements
        if config.cx_freeze_replace_paths:
            for old_path, new_path in config.cx_freeze_replace_paths:
                cmd.extend(['--replace-path', f"{old_path}={new_path}"])
        
        # Zip options
        if config.cx_freeze_zip_include_packages:
            for package in config.cx_freeze_zip_include_packages:
                cmd.extend(['--zip-include-package', package])
        
        # Optimization
        if config.cx_freeze_optimize is not None:
            cmd.extend(['--optimize', str(config.cx_freeze_optimize)])
        
        # Compression and zip options
        if config.cx_freeze_compress:
            cmd.append('--compress')
        
        if not config.cx_freeze_create_shared_zip:
            cmd.append('--no-shared-zip')
        
        # MSVCRT
        if config.cx_freeze_include_msvcrt:
            cmd.append('--include-msvcrt')
        
        # Silent mode
        if config.cx_freeze_silent:
            cmd.append('--silent')
        
        # Init script
        if config.cx_freeze_init_script and Path(config.cx_freeze_init_script).exists():
            cmd.extend(['--init-script', config.cx_freeze_init_script])
        
        # Windows shortcuts
        if config.cx_freeze_shortcut_name:
            cmd.extend(['--shortcut-name', config.cx_freeze_shortcut_name])
        
        if config.cx_freeze_shortcut_dir:
            cmd.extend(['--shortcut-dir', config.cx_freeze_shortcut_dir])
        
        # Custom options
        if config.custom_options:
            for option, value in config.custom_options.items():
                if option.startswith('cx_freeze_'):
                    option_name = option.replace('cx_freeze_', '').replace('_', '-')
                    if value is True:
                        cmd.append(f'--{option_name}')
                    elif value is not False and value is not None:
                        cmd.extend([f'--{option_name}', str(value)])
        
        return cmd
    
    def _build_nuitka_command(self, config: BuildConfig) -> List[str]:
        """Build comprehensive Nuitka command with all options."""
        cmd = [sys.executable, '-m', 'nuitka']
        
        # Basic modes
        if config.nuitka_standalone:
            cmd.append('--standalone')
        if config.nuitka_onefile:
            cmd.append('--onefile')
        if config.nuitka_module:
            cmd.append('--module')
        
        # Package mode
        if config.nuitka_package:
            cmd.extend(['--package', config.nuitka_package])
        
        # Output options
        if config.output_dir or config.nuitka_output_dir:
            output_dir = config.nuitka_output_dir or config.output_dir
            if output_dir:
                cmd.extend(['--output-dir', output_dir])
        
        if config.output_name or config.nuitka_output_filename:
            output_name = config.nuitka_output_filename or config.output_name
            if output_name:
                cmd.extend(['--output-filename', output_name])
        
        # Console options
        if config.nuitka_disable_console or config.windowed:
            cmd.append('--disable-console')
        elif config.nuitka_enable_console:
            cmd.append('--enable-console')
        
        # Icon
        if config.icon and Path(config.icon).exists():
            cmd.extend(['--windows-icon-from-ico', config.icon])
        
        # Import following
        if config.nuitka_follow_imports:
            cmd.append('--follow-imports')
        elif config.nuitka_nofollow_imports:
            cmd.append('--nofollow-imports')
        
        if config.nuitka_follow_import_to:
            for module in config.nuitka_follow_import_to:
                cmd.extend(['--follow-import-to', module])
        
        if config.nuitka_nofollow_import_to:
            for module in config.nuitka_nofollow_import_to:
                cmd.extend(['--nofollow-import-to', module])
        
        # Package and module inclusion
        if config.nuitka_include_package:
            for package in config.nuitka_include_package:
                cmd.extend(['--include-package', package])
        
        if config.nuitka_include_module:
            for module in config.nuitka_include_module:
                cmd.extend(['--include-module', module])
        
        if config.nuitka_include_package_data:
            for package in config.nuitka_include_package_data:
                cmd.extend(['--include-package-data', package])
        
        # Data files integration
        if config.nuitka_include_data_files:
            for src, dst in config.nuitka_include_data_files:
                cmd.extend(['--include-data-file', f"{src}={dst}"])
        
        if config.nuitka_include_data_dir:
            for src, dst in config.nuitka_include_data_dir:
                cmd.extend(['--include-data-dir', f"{src}={dst}"])
        
        # Include scanned files automatically
        if config.scanned_files:
            # Auto-include data files
            if 'data' in config.scanned_files:
                for data_file in config.scanned_files['data']:
                    filename = Path(data_file).name
                    cmd.extend(['--include-data-file', f"{data_file}={filename}"])
            
            # Auto-include configuration files
            if 'config' in config.scanned_files:
                for conf_file in config.scanned_files['config']:
                    filename = Path(conf_file).name
                    cmd.extend(['--include-data-file', f"{conf_file}={filename}"])
            
            # Auto-include documentation
            if 'documentation' in config.scanned_files:
                for doc_file in config.scanned_files['documentation']:
                    filename = Path(doc_file).name
                    cmd.extend(['--include-data-file', f"{doc_file}={filename}"])
        
        # Plugins
        if config.nuitka_plugin_enable:
            for plugin in config.nuitka_plugin_enable:
                cmd.extend(['--plugin-enable', plugin])
        
        if config.nuitka_plugin_disable:
            for plugin in config.nuitka_plugin_disable:
                cmd.extend(['--plugin-disable', plugin])
        
        if config.nuitka_user_plugin:
            for plugin in config.nuitka_user_plugin:
                cmd.extend(['--user-plugin', plugin])
        
        # Plugin directories and files
        if config.nuitka_include_plugin_directory:
            for directory in config.nuitka_include_plugin_directory:
                cmd.extend(['--include-plugin-directory', directory])
        
        if config.nuitka_include_plugin_files:
            for files in config.nuitka_include_plugin_files:
                cmd.extend(['--include-plugin-files', files])
        
        # Warning options
        if config.nuitka_warn_implicit_exceptions:
            cmd.append('--warn-implicit-exceptions')
        
        if config.nuitka_warn_unusual_code:
            cmd.append('--warn-unusual-code')
        
        # Auto-downloads
        if config.nuitka_assume_yes_for_downloads:
            cmd.append('--assume-yes-for-downloads')
        
        # Compiler options
        if config.nuitka_jobs:
            cmd.extend(['--jobs', str(config.nuitka_jobs)])
        
        if config.nuitka_lto:
            cmd.extend(['--lto', config.nuitka_lto])
        
        if config.nuitka_clang:
            cmd.append('--clang')
        
        if config.nuitka_mingw64:
            cmd.append('--mingw64')
        
        if config.nuitka_msvc:
            cmd.extend(['--msvc', config.nuitka_msvc])
        
        if config.nuitka_disable_ccache:
            cmd.append('--disable-ccache')
        
        # Windows dependency tool
        if config.nuitka_windows_dependency_tool:
            cmd.extend(['--windows-dependency-tool', config.nuitka_windows_dependency_tool])
        
        # Force stdout/stderr
        if config.nuitka_force_stdout_spec:
            cmd.extend(['--force-stdout-spec', config.nuitka_force_stdout_spec])
        
        if config.nuitka_force_stderr_spec:
            cmd.extend(['--force-stderr-spec', config.nuitka_force_stderr_spec])
        
        # Experimental features
        if config.nuitka_experimental:
            for feature in config.nuitka_experimental:
                cmd.extend(['--experimental', feature])
        
        # Custom options
        if config.custom_options:
            for option, value in config.custom_options.items():
                if option.startswith('nuitka_'):
                    option_name = option.replace('nuitka_', '').replace('_', '-')
                    if value is True:
                        cmd.append(f'--{option_name}')
                    elif value is not False and value is not None:
                        cmd.extend([f'--{option_name}', str(value)])
        
        # Source file (must be last)
        if config.source_file:
            cmd.append(config.source_file)
        
        return cmd
    
    async def build_with_pyinstaller(self, config: BuildConfig) -> bool:
        """Build using PyInstaller with comprehensive option support."""
        if not config.source_file:
            logger.error("Source file not specified for PyInstaller build")
            return False
        
        if not Path(config.source_file).exists():
            logger.error(f"Source file not found: {config.source_file}")
            return False
        
        # Build comprehensive PyInstaller command
        cmd = self._build_pyinstaller_command(config)
        
        logger.info(f"Building with PyInstaller: {' '.join(cmd)}")
        
        try:
            # Set environment variables
            env = os.environ.copy()
            if config.environment_vars:
                env.update(config.environment_vars)
            
            # Run pre-build commands
            if config.pre_build_commands:
                for pre_cmd in config.pre_build_commands:
                    logger.info(f"Running pre-build command: {pre_cmd}")
                    result = subprocess.run(pre_cmd, shell=True, env=env)
                    if result.returncode != 0:
                        logger.error(f"Pre-build command failed: {pre_cmd}")
                        return False
            
            # Run PyInstaller
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                env=env
            )
            
            # Stream output in real-time
            if process.stdout:
                while True:
                    line = await process.stdout.readline()
                    if not line:
                        break
                    print(line.decode().strip())
            
            await process.wait()
            success = process.returncode == 0
            
            if success:
                # Run post-build commands
                if config.post_build_commands:
                    for post_cmd in config.post_build_commands:
                        logger.info(f"Running post-build command: {post_cmd}")
                        result = subprocess.run(post_cmd, shell=True, env=env)
                        if result.returncode != 0:
                            logger.warning(f"Post-build command failed: {post_cmd}")
                
                # Update config
                config.last_build = datetime.now().isoformat()
                config.build_count += 1
                self.save_config(config)
                
                logger.info("PyInstaller build completed successfully")
            else:
                logger.error("PyInstaller build failed")
            
            return success
            
        except Exception as e:
            logger.error(f"Error during PyInstaller build: {e}")
            return False
    
    async def build_with_cx_freeze(self, config: BuildConfig) -> bool:
        """Build using cx_Freeze with comprehensive option support."""
        if not config.source_file:
            logger.error("Source file not specified for cx_Freeze build")
            return False
        
        if not Path(config.source_file).exists():
            logger.error(f"Source file not found: {config.source_file}")
            return False
        
        # Build comprehensive cx_Freeze command
        cmd = self._build_cx_freeze_command(config)
        
        logger.info(f"Building with cx_Freeze: {' '.join(cmd)}")
        
        try:
            # Set environment variables
            env = os.environ.copy()
            if config.environment_vars:
                env.update(config.environment_vars)
            
            # Run pre-build commands
            if config.pre_build_commands:
                for pre_cmd in config.pre_build_commands:
                    logger.info(f"Running pre-build command: {pre_cmd}")
                    result = subprocess.run(pre_cmd, shell=True, env=env)
                    if result.returncode != 0:
                        logger.error(f"Pre-build command failed: {pre_cmd}")
                        return False
            
            # Run cx_Freeze
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                env=env
            )
            
            # Stream output in real-time
            if process.stdout:
                while True:
                    line = await process.stdout.readline()
                    if not line:
                        break
                    print(line.decode().strip())
            
            await process.wait()
            success = process.returncode == 0
            
            if success:
                # Run post-build commands
                if config.post_build_commands:
                    for post_cmd in config.post_build_commands:
                        logger.info(f"Running post-build command: {post_cmd}")
                        result = subprocess.run(post_cmd, shell=True, env=env)
                        if result.returncode != 0:
                            logger.warning(f"Post-build command failed: {post_cmd}")
                
                # Update config
                config.last_build = datetime.now().isoformat()
                config.build_count += 1
                self.save_config(config)
                
                logger.info("cx_Freeze build completed successfully")
            else:
                logger.error("cx_Freeze build failed")
            
            return success
            
        except Exception as e:
            logger.error(f"Error during cx_Freeze build: {e}")
            return False
    
    async def build_with_nuitka(self, config: BuildConfig) -> bool:
        """Build using Nuitka with comprehensive option support."""
        if not config.source_file:
            logger.error("Source file not specified for Nuitka build")
            return False
        
        if not Path(config.source_file).exists():
            logger.error(f"Source file not found: {config.source_file}")
            return False
        
        # Build comprehensive Nuitka command
        cmd = self._build_nuitka_command(config)
        
        logger.info(f"Building with Nuitka: {' '.join(cmd)}")
        
        try:
            # Set environment variables
            env = os.environ.copy()
            if config.environment_vars:
                env.update(config.environment_vars)
            
            # Run pre-build commands
            if config.pre_build_commands:
                for pre_cmd in config.pre_build_commands:
                    logger.info(f"Running pre-build command: {pre_cmd}")
                    result = subprocess.run(pre_cmd, shell=True, env=env)
                    if result.returncode != 0:
                        logger.error(f"Pre-build command failed: {pre_cmd}")
                        return False
            
            # Run Nuitka
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                env=env
            )
            
            # Stream output in real-time
            if process.stdout:
                while True:
                    line = await process.stdout.readline()
                    if not line:
                        break
                    print(line.decode().strip())
            
            await process.wait()
            success = process.returncode == 0
            
            if success:
                # Run post-build commands
                if config.post_build_commands:
                    for post_cmd in config.post_build_commands:
                        logger.info(f"Running post-build command: {post_cmd}")
                        result = subprocess.run(post_cmd, shell=True, env=env)
                        if result.returncode != 0:
                            logger.warning(f"Post-build command failed: {post_cmd}")
                
                # Update config
                config.last_build = datetime.now().isoformat()
                config.build_count += 1
                self.save_config(config)
                
                logger.info("Nuitka build completed successfully")
            else:
                logger.error("Nuitka build failed")
            
            return success
            
        except Exception as e:
            logger.error(f"Error during Nuitka build: {e}")
            return False
    
    async def build_with_custom(self, config: BuildConfig) -> bool:
        """Build using custom script."""
        logger.info("Custom build system not yet implemented")
        return False
    
    async def execute_build(self, config_name: Optional[str] = None) -> bool:
        """Execute a build using the specified or active configuration."""
        if config_name:
            config = self.load_config(config_name)
            if not config:
                logger.error(f"Build configuration '{config_name}' not found")
                return False
        else:
            config = self.get_active_config()
            if not config:
                logger.error("No active build configuration")
                return False
        
        logger.info(f"Starting build with '{config.name}' using {config.build_system}")
        
        # Check if build system is available
        if not await self.check_build_system_availability(config.build_system):
            logger.error(f"Build system '{config.build_system}' is not available")
            return False
        
        # Execute build based on system type
        if config.build_system == 'pyinstaller':
            return await self.build_with_pyinstaller(config)
        elif config.build_system == 'cx_freeze':
            return await self.build_with_cx_freeze(config)
        elif config.build_system == 'nuitka':
            return await self.build_with_nuitka(config)
        elif config.build_system == 'custom':
            return await self.build_with_custom(config)
        else:
            logger.error(f"Unsupported build system: {config.build_system}")
            return False


# Global build manager instance
build_manager = BuildSystemManager()


async def build_config_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Create or switch to a build configuration."""
    # Parse arguments from list format
    parsed = parse_args(args, ['name', 'system'])
    name = parsed.get('name')
    system = parsed.get('system', 'pyinstaller')
    
    if not name:
        logger.error("Build configuration name is required")
        return False
    
    if system not in BuildSystemManager.SUPPORTED_SYSTEMS:
        logger.error(f"Unsupported build system: {system}")
        logger.info(f"Supported systems: {', '.join(BuildSystemManager.SUPPORTED_SYSTEMS.keys())}")
        return False
    
    config = build_manager.set_active_config(name, system)
    print(f"Active build configuration: {config.name} ({config.build_system})")
    return True


async def build_source_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Set the source file for the active build configuration."""
    if not build_manager.current_config:
        logger.error("No active build configuration. Use 'build-config' first.")
        return False
    
    parsed = parse_args(args, ['file'])
    source_file = parsed.get('file')
    if not source_file:
        logger.error("Source file path is required")
        return False
    
    if not Path(source_file).exists():
        logger.error(f"Source file not found: {source_file}")
        return False
    
    build_manager.current_config.source_file = source_file
    build_manager.save_config(build_manager.current_config)
    print(f"Source file set to: {source_file}")
    return True


async def build_name_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Set the output name for the active build configuration."""
    if not build_manager.current_config:
        logger.error("No active build configuration. Use 'build-config' first.")
        return False
    
    parsed = parse_args(args, ['name'])
    name = parsed.get('name')
    if not name:
        logger.error("Output name is required")
        return False
    
    build_manager.current_config.output_name = name
    build_manager.save_config(build_manager.current_config)
    print(f"Output name set to: {name}")
    return True


async def build_version_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Set the version for the active build configuration."""
    if not build_manager.current_config:
        logger.error("No active build configuration. Use 'build-config' first.")
        return False
    
    parsed = parse_args(args, ['version'])
    version = parsed.get('version')
    if not version:
        logger.error("Version is required")
        return False
    
    build_manager.current_config.version = version
    build_manager.save_config(build_manager.current_config)
    print(f"Version set to: {version}")
    return True


async def build_icon_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Set the icon for the active build configuration."""
    if not build_manager.current_config:
        logger.error("No active build configuration. Use 'build-config' first.")
        return False
    
    parsed = parse_args(args, ['icon'])
    icon = parsed.get('icon')
    if not icon:
        logger.error("Icon file path is required")
        return False
    
    if not Path(icon).exists():
        logger.error(f"Icon file not found: {icon}")
        return False
    
    build_manager.current_config.icon = icon
    build_manager.save_config(build_manager.current_config)
    print(f"Icon set to: {icon}")
    return True


async def build_onefile_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Set onefile mode for the active build configuration."""
    if not build_manager.current_config:
        logger.error("No active build configuration. Use 'build-config' first.")
        return False
    
    parsed = parse_args(args, ['enable'])
    onefile = parsed.get('enable', 'true').lower() == 'true'
    build_manager.current_config.onefile = onefile
    build_manager.save_config(build_manager.current_config)
    print(f"Onefile mode: {'enabled' if onefile else 'disabled'}")
    return True


async def build_console_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Set console mode for the active build configuration."""
    if not build_manager.current_config:
        logger.error("No active build configuration. Use 'build-config' first.")
        return False
    
    parsed = parse_args(args, ['enable'])
    console = parsed.get('enable', 'true').lower() == 'true'
    build_manager.current_config.console = console
    build_manager.save_config(build_manager.current_config)
    print(f"Console mode: {'enabled' if console else 'disabled'}")
    return True


async def build_hidden_import_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Add hidden imports to the active build configuration."""
    if not build_manager.current_config:
        logger.error("No active build configuration. Use 'build-config' first.")
        return False
    
    parsed = parse_args(args, ['imports'])
    imports = parsed.get('imports', '')
    if not imports:
        logger.error("Hidden imports are required")
        return False
    
    # Split by comma and add to list
    import_list = [imp.strip() for imp in imports.split(',')]
    if build_manager.current_config.hidden_imports is None:
        build_manager.current_config.hidden_imports = []
    for imp in import_list:
        if imp not in build_manager.current_config.hidden_imports:
            build_manager.current_config.hidden_imports.append(imp)
    
    build_manager.save_config(build_manager.current_config)
    print(f"Added hidden imports: {', '.join(import_list)}")
    return True


async def build_data_files_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Add data files to the active build configuration."""
    if not build_manager.current_config:
        logger.error("No active build configuration. Use 'build-config' first.")
        return False
    
    parsed = parse_args(args, ['source', 'dest'])
    source = parsed.get('source')
    dest = parsed.get('dest')
    
    if not source or not dest:
        logger.error("Both source and destination are required")
        return False
    
    if not Path(source).exists():
        logger.error(f"Source file/directory not found: {source}")
        return False
    
    data_file = (source, dest)
    if build_manager.current_config.data_files is None:
        build_manager.current_config.data_files = []
    if data_file not in build_manager.current_config.data_files:
        build_manager.current_config.data_files.append(data_file)
    
    build_manager.save_config(build_manager.current_config)
    print(f"Added data file mapping: {source} -> {dest}")
    return True


async def build_execute_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Execute the build using the active or specified configuration."""
    parsed = parse_args(args, ['config'])
    config_name = parsed.get('config')
    return await build_manager.execute_build(config_name)


async def build_list_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """List all build configurations."""
    configs = build_manager.list_configs()
    if not configs:
        print("No build configurations found.")
        return True
    
    print("Available build configurations:")
    for config_name in configs:
        config = build_manager.load_config(config_name)
        if config:
            status = "✓ Active" if config_name == build_manager.active_config_name else ""
            print(f"  {config_name} ({config.build_system}) {status}")
            if config.source_file:
                print(f"    Source: {config.source_file}")
            if config.last_build:
                print(f"    Last build: {config.last_build}")
    
    return True


async def build_show_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Show details of the active or specified build configuration."""
    parsed = parse_args(args, ['config'])
    config_name = parsed.get('config') or build_manager.active_config_name
    
    if not config_name:
        logger.error("No active build configuration")
        return False
    
    config = build_manager.load_config(config_name)
    if not config:
        logger.error(f"Build configuration '{config_name}' not found")
        return False
    
    print(f"Build Configuration: {config.name}")
    print(f"  Build System: {config.build_system}")
    print(f"  Source File: {config.source_file or 'Not set'}")
    print(f"  Output Name: {config.output_name or 'Not set'}")
    print(f"  Version: {config.version or 'Not set'}")
    print(f"  Icon: {config.icon or 'Not set'}")
    print(f"  Console Mode: {config.console}")
    print(f"  Onefile Mode: {config.onefile}")
    
    if config.hidden_imports:
        print(f"  Hidden Imports: {', '.join(config.hidden_imports)}")
    
    if config.data_files:
        print("  Data Files:")
        for src, dst in config.data_files:
            print(f"    {src} -> {dst}")
    
    print(f"  Created: {config.created_date}")
    print(f"  Last Modified: {config.last_modified}")
    print(f"  Last Build: {config.last_build or 'Never'}")
    print(f"  Build Count: {config.build_count}")
    
    return True


async def build_reset_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Reset the active build configuration."""
    parsed = parse_args(args, ['config'])
    config_name = parsed.get('config')
    
    if build_manager.reset_config(config_name):
        name = config_name or build_manager.active_config_name
        print(f"Build configuration '{name}' has been reset")
        return True
    else:
        return False


async def build_delete_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Delete a build configuration."""
    parsed = parse_args(args, ['config'])
    config_name = parsed.get('config')
    if not config_name:
        logger.error("Configuration name is required")
        return False
    
    if build_manager.delete_config(config_name):
        print(f"Build configuration '{config_name}' deleted")
        return True
    else:
        return False


async def build_systems_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """List available build systems and their status."""
    print("Available Build Systems:")
    
    for system, description in BuildSystemManager.SUPPORTED_SYSTEMS.items():
        available = await build_manager.check_build_system_availability(system)
        status = "✓ Available" if available else "✗ Not Available"
        print(f"  {system}: {description} - {status}")
    
    return True


async def build_preview_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Preview the build command that would be executed."""
    parsed = parse_args(args, ['config'])
    config_name = parsed.get('config')
    
    config = build_manager.load_config(config_name) if config_name else build_manager.current_config
    if not config:
        if config_name:
            print(f"Build configuration '{config_name}' not found")
        else:
            print("No active build configuration. Use 'build-config <name>' to create one.")
        return False
    
    print(f"Build Command Preview for '{config.name}':")
    print(f"Build System: {config.build_system}")
    print()
    
    if config.build_system == 'pyinstaller':
        cmd = build_manager._build_pyinstaller_command(config)
        print("PyInstaller Command:")
        print(" ".join(cmd))
        
        # Show breakdown of command components  
        print("\nCommand Breakdown:")
        print(f"  Python: {cmd[0]}")
        print(f"  Module: {cmd[1]} {cmd[2]}")
        
        options = cmd[3:-1]  # Exclude python, -m, PyInstaller and source file
        if options:
            print("  Options:")
            i = 0
            while i < len(options):
                option = options[i]
                if option.startswith('--') and i + 1 < len(options) and not options[i + 1].startswith('--'):
                    print(f"    {option} {options[i + 1]}")
                    i += 2
                else:
                    print(f"    {option}")
                    i += 1
        
        print(f"  Source: {cmd[-1]}")
    
    elif config.build_system == 'cx_freeze':
        cmd = build_manager._build_cx_freeze_command(config)
        print("cx_Freeze Command:")
        print(" ".join(cmd))
        
        # Show breakdown of command components
        print("\nCommand Breakdown:")
        print(f"  Python: {cmd[0]}")
        print(f"  Module: {cmd[1]} {cmd[2]}")
        
        # Find source file (first non-option argument after python -m cx_Freeze)
        source_file = cmd[3] if len(cmd) > 3 else None
        options = cmd[4:] if len(cmd) > 4 else []
        
        if source_file:
            print(f"  Source: {source_file}")
        
        if options:
            print("  Options:")
            i = 0
            while i < len(options):
                option = options[i]
                if option.startswith('--') and i + 1 < len(options) and not options[i + 1].startswith('--'):
                    print(f"    {option} {options[i + 1]}")
                    i += 2
                else:
                    print(f"    {option}")
                    i += 1
    
    elif config.build_system == 'nuitka':
        cmd = build_manager._build_nuitka_command(config)
        print("Nuitka Command:")
        print(" ".join(cmd))
        
        # Show breakdown of command components
        print("\nCommand Breakdown:")
        print(f"  Python: {cmd[0]}")
        print(f"  Module: {cmd[1]} {cmd[2]}")
        
        # Find source file (usually last argument)
        source_file = cmd[-1] if cmd and not cmd[-1].startswith('--') else None
        options = cmd[3:-1] if source_file else cmd[3:]
        
        if options:
            print("  Options:")
            i = 0
            while i < len(options):
                option = options[i]
                if option.startswith('--') and i + 1 < len(options) and not options[i + 1].startswith('--'):
                    print(f"    {option} {options[i + 1]}")
                    i += 2
                else:
                    print(f"    {option}")
                    i += 1
        
        if source_file:
            print(f"  Source: {source_file}")
        
    else:
        print(f"Preview not yet implemented for {config.build_system}")
    
    return True


async def build_collect_files_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Collect file paths from scanning system and integrate with build config."""
    parsed = parse_args(args, ['config', 'scan_result_file'])
    config_name = parsed.get('config')
    scan_file = parsed.get('scan_result_file', 'scan_cache.json')
    
    config = build_manager.load_config(config_name) if config_name else build_manager.current_config
    if not config:
        if config_name:
            print(f"Build configuration '{config_name}' not found")
        else:
            print("No active build configuration. Use 'build-config <name>' to create one.")
        return False
    
    # Try to load scan results from cache
    scan_cache_dir = Path.home() / '.buildcli' / 'scan_cache'
    scan_cache_file = scan_cache_dir / scan_file
    
    if not scan_cache_file.exists():
        print(f"Scan cache file not found: {scan_cache_file}")
        print("Run 'scan-project <path>' first to generate scan data")
        return False
    
    try:
        with open(scan_cache_file, 'r') as f:
            scan_data = json.load(f)
        
        # Extract file mappings from scan data
        scanned_files = {}
        for scan_result in scan_data.values():
            if 'file_mappings' in scan_result:
                for mapping in scan_result['file_mappings']:
                    file_type = mapping.get('type', 'unknown')
                    file_path = mapping.get('path')
                    
                    if file_path:
                        if file_type not in scanned_files:
                            scanned_files[file_type] = []
                        scanned_files[file_type].append(file_path)
        
        # Update config with scanned files
        config.scanned_files = scanned_files
        config.scan_metadata = scan_data
        
        # Auto-apply some scan results
        applied_changes = []
        
        # Set icon if found and not already set
        if not config.icon and 'icon' in scanned_files and scanned_files['icon']:
            config.icon = scanned_files['icon'][0]
            applied_changes.append(f"Icon: {config.icon}")
        
        # Set splash if found and not already set
        if not config.splash and 'splash' in scanned_files and scanned_files['splash']:
            config.splash = scanned_files['splash'][0]
            applied_changes.append(f"Splash: {config.splash}")
        
        # Add data files if not already present
        existing_data = set(src for src, _ in (config.data_files or []))
        new_data_files = []
        
        for file_type in ['data', 'config', 'documentation']:
            if file_type in scanned_files:
                for file_path in scanned_files[file_type]:
                    if file_path not in existing_data:
                        new_data_files.append((file_path, '.'))
                        applied_changes.append(f"Data file: {file_path}")
        
        if new_data_files:
            if config.data_files:
                config.data_files.extend(new_data_files)
            else:
                config.data_files = new_data_files
        
        # Save updated config
        build_manager.save_config(config)
        
        print(f"Collected files from scan results and updated '{config.name}':")
        print(f"  File types found: {list(scanned_files.keys())}")
        print(f"  Total files: {sum(len(files) for files in scanned_files.values())}")
        
        if applied_changes:
            print("\nAuto-applied changes:")
            for change in applied_changes:
                print(f"  + {change}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error loading scan results: {e}")
        return False


async def build_advanced_options_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Set advanced PyInstaller options for build configuration."""
    if len(args) < 2:
        print("Usage: build-advanced-options <config> <option> [value]")
        print("\nAvailable options:")
        print("  debug-imports, debug-bootloader, strip, noupx")
        print("  collect-submodules <module>, collect-data <package>")
        print("  collect-binaries <package>, collect-all <package>")
        print("  runtime-tmpdir <path>, key <encryption_key>")
        print("  uac-admin, uac-uiaccess")
        return False
    
    config_name = args[0]
    option = args[1]
    value = args[2] if len(args) > 2 else None
    
    config = build_manager.load_config(config_name) if config_name else build_manager.current_config
    if not config:
        if config_name:
            print(f"Build configuration '{config_name}' not found")
        else:
            print("No active build configuration. Use 'build-config <name>' to create one.")
        return False
    
    # Handle different option types
    if option == 'debug-imports':
        config.debug_imports = True
        print(f"Enabled debug imports for '{config_name}'")
    
    elif option == 'debug-bootloader':
        config.debug_bootloader = True
        print(f"Enabled debug bootloader for '{config_name}'")
    
    elif option == 'strip':
        config.strip = True
        print(f"Enabled strip for '{config_name}'")
    
    elif option == 'noupx':
        config.noupx = True
        print(f"Disabled UPX for '{config_name}'")
    
    elif option == 'collect-submodules' and value:
        if not config.collect_submodules:
            config.collect_submodules = []
        config.collect_submodules.append(value)
        print(f"Added collect-submodules '{value}' to '{config_name}'")
    
    elif option == 'collect-data' and value:
        if not config.collect_data:
            config.collect_data = []
        config.collect_data.append(value)
        print(f"Added collect-data '{value}' to '{config_name}'")
    
    elif option == 'collect-binaries' and value:
        if not config.collect_binaries:
            config.collect_binaries = []
        config.collect_binaries.append(value)
        print(f"Added collect-binaries '{value}' to '{config_name}'")
    
    elif option == 'collect-all' and value:
        if not config.collect_all:
            config.collect_all = []
        config.collect_all.append(value)
        print(f"Added collect-all '{value}' to '{config_name}'")
    
    elif option == 'runtime-tmpdir' and value:
        config.runtime_tmpdir = value
        print(f"Set runtime-tmpdir to '{value}' for '{config_name}'")
    
    elif option == 'key' and value:
        config.key = value
        print(f"Set encryption key for '{config_name}'")
    
    elif option == 'uac-admin':
        config.uac_admin = True
        print(f"Enabled UAC admin for '{config_name}'")
    
    elif option == 'uac-uiaccess':
        config.uac_uiaccess = True
        print(f"Enabled UAC UI access for '{config_name}'")
    
    else:
        print(f"Unknown or invalid option: {option}")
        return False
    
    # Save updated config
    build_manager.save_config(config)
    return True


async def build_splash_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Set splash screen for active build configuration."""
    if not args:
        print("Usage: build-splash <splash_image_path>")
        return False
    
    splash_path = args[0]
    if not Path(splash_path).exists():
        print(f"Splash image not found: {splash_path}")
        return False
    
    config = build_manager.current_config
    if not config:
        print("No active build configuration. Use 'build-config <name>' to create one.")
        return False
    
    config.splash = splash_path
    build_manager.save_config(config)
    print(f"Splash screen set to: {splash_path}")
    return True


async def build_windowed_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Set windowed mode (no console) for active build configuration."""
    config = build_manager.current_config
    if not config:
        print("No active build configuration. Use 'build-config <name>' to create one.")
        return False
    
    enable = True
    if args and args[0].lower() in ['false', 'no', '0', 'off']:
        enable = False
    
    config.windowed = enable
    config.console = not enable  # windowed is opposite of console
    build_manager.save_config(config)
    
    mode = "windowed (no console)" if enable else "console"
    print(f"Build mode set to: {mode}")
    return True


async def build_metadata_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Set metadata (description, author, company, copyright) for active build configuration."""
    if len(args) < 2:
        print("Usage: build-metadata <field> <value>")
        print("Fields: description, author, company, copyright")
        return False
    
    field = args[0].lower()
    value = " ".join(args[1:])
    
    config = build_manager.current_config
    if not config:
        print("No active build configuration. Use 'build-config <name>' to create one.")
        return False
    
    if field == 'description':
        config.description = value
    elif field == 'author':
        config.author = value
    elif field == 'company':
        config.company = value
    elif field == 'copyright':
        config.copyright = value
    else:
        print(f"Unknown metadata field: {field}")
        print("Available fields: description, author, company, copyright")
        return False
    
    build_manager.save_config(config)
    print(f"Set {field} to: {value}")
    return True


async def build_cx_freeze_options_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Set cx_Freeze specific options for build configuration."""
    if len(args) < 2:
        print("Usage: build-cx-freeze-options <config> <option> [value]")
        print("\nAvailable options:")
        print("  base <Console|Win32GUI|Service>  - Set base executable type")
        print("  include <module>                 - Include module")
        print("  exclude <module>                 - Exclude module")
        print("  package <package>                - Include package")
        print("  optimize <0|1|2>                - Set optimization level")
        print("  compress                         - Enable compression")
        print("  no-shared-zip                    - Disable shared zip")
        print("  include-msvcrt                   - Include MSVCRT")
        print("  silent                           - Silent mode")
        return False
    
    config_name = args[0]
    option = args[1]
    value = args[2] if len(args) > 2 else None
    
    config = build_manager.load_config(config_name) if config_name else build_manager.current_config
    if not config:
        if config_name:
            print(f"Build configuration '{config_name}' not found")
        else:
            print("No active build configuration. Use 'build-config <name>' to create one.")
        return False
    
    # Handle different option types
    if option == 'base' and value:
        config.cx_freeze_base = value
        print(f"Set cx_Freeze base to '{value}' for '{config.name}'")
    
    elif option == 'include' and value:
        if not config.cx_freeze_includes:
            config.cx_freeze_includes = []
        config.cx_freeze_includes.append(value)
        print(f"Added cx_Freeze include '{value}' to '{config.name}'")
    
    elif option == 'exclude' and value:
        if not config.cx_freeze_excludes:
            config.cx_freeze_excludes = []
        config.cx_freeze_excludes.append(value)
        print(f"Added cx_Freeze exclude '{value}' to '{config.name}'")
    
    elif option == 'package' and value:
        if not config.cx_freeze_packages:
            config.cx_freeze_packages = []
        config.cx_freeze_packages.append(value)
        print(f"Added cx_Freeze package '{value}' to '{config.name}'")
    
    elif option == 'optimize' and value:
        try:
            config.cx_freeze_optimize = int(value)
            print(f"Set cx_Freeze optimization to {value} for '{config.name}'")
        except ValueError:
            print("Optimization level must be 0, 1, or 2")
            return False
    
    elif option == 'compress':
        config.cx_freeze_compress = True
        print(f"Enabled cx_Freeze compression for '{config.name}'")
    
    elif option == 'no-shared-zip':
        config.cx_freeze_create_shared_zip = False
        print(f"Disabled cx_Freeze shared zip for '{config.name}'")
    
    elif option == 'include-msvcrt':
        config.cx_freeze_include_msvcrt = True
        print(f"Enabled cx_Freeze MSVCRT inclusion for '{config.name}'")
    
    elif option == 'silent':
        config.cx_freeze_silent = True
        print(f"Enabled cx_Freeze silent mode for '{config.name}'")
    
    else:
        print(f"Unknown or invalid cx_Freeze option: {option}")
        return False
    
    # Save updated config
    build_manager.save_config(config)
    return True


async def build_nuitka_options_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Set Nuitka specific options for build configuration."""
    if len(args) < 2:
        print("Usage: build-nuitka-options <config> <option> [value]")
        print("\nAvailable options:")
        print("  standalone                       - Create standalone distribution")
        print("  onefile                         - Create single file")
        print("  follow-imports                  - Follow all imports")
        print("  nofollow-imports               - Don't follow any imports")
        print("  include-package <package>       - Include package")
        print("  include-module <module>         - Include module")
        print("  plugin-enable <plugin>          - Enable plugin")
        print("  plugin-disable <plugin>         - Disable plugin")
        print("  jobs <number>                   - Parallel compilation jobs")
        print("  lto <yes|no|auto>              - Link Time Optimization")
        print("  clang                           - Use Clang compiler")
        print("  mingw64                         - Use MinGW64")
        print("  disable-console                 - Disable console window")
        print("  experimental <feature>          - Enable experimental feature")
        return False
    
    config_name = args[0]
    option = args[1]
    value = args[2] if len(args) > 2 else None
    
    config = build_manager.load_config(config_name) if config_name else build_manager.current_config
    if not config:
        if config_name:
            print(f"Build configuration '{config_name}' not found")
        else:
            print("No active build configuration. Use 'build-config <name>' to create one.")
        return False
    
    # Handle different option types
    if option == 'standalone':
        config.nuitka_standalone = True
        print(f"Enabled Nuitka standalone for '{config.name}'")
    
    elif option == 'onefile':
        config.nuitka_onefile = True
        print(f"Enabled Nuitka onefile for '{config.name}'")
    
    elif option == 'follow-imports':
        config.nuitka_follow_imports = True
        config.nuitka_nofollow_imports = False
        print(f"Enabled Nuitka follow-imports for '{config.name}'")
    
    elif option == 'nofollow-imports':
        config.nuitka_nofollow_imports = True
        config.nuitka_follow_imports = False
        print(f"Enabled Nuitka nofollow-imports for '{config.name}'")
    
    elif option == 'include-package' and value:
        if not config.nuitka_include_package:
            config.nuitka_include_package = []
        config.nuitka_include_package.append(value)
        print(f"Added Nuitka include-package '{value}' to '{config.name}'")
    
    elif option == 'include-module' and value:
        if not config.nuitka_include_module:
            config.nuitka_include_module = []
        config.nuitka_include_module.append(value)
        print(f"Added Nuitka include-module '{value}' to '{config.name}'")
    
    elif option == 'plugin-enable' and value:
        if not config.nuitka_plugin_enable:
            config.nuitka_plugin_enable = []
        config.nuitka_plugin_enable.append(value)
        print(f"Added Nuitka plugin-enable '{value}' to '{config.name}'")
    
    elif option == 'plugin-disable' and value:
        if not config.nuitka_plugin_disable:
            config.nuitka_plugin_disable = []
        config.nuitka_plugin_disable.append(value)
        print(f"Added Nuitka plugin-disable '{value}' to '{config.name}'")
    
    elif option == 'jobs' and value:
        try:
            config.nuitka_jobs = int(value)
            print(f"Set Nuitka jobs to {value} for '{config.name}'")
        except ValueError:
            print("Jobs must be a number")
            return False
    
    elif option == 'lto' and value:
        if value in ['yes', 'no', 'auto']:
            config.nuitka_lto = value
            print(f"Set Nuitka LTO to '{value}' for '{config.name}'")
        else:
            print("LTO value must be 'yes', 'no', or 'auto'")
            return False
    
    elif option == 'clang':
        config.nuitka_clang = True
        print(f"Enabled Nuitka Clang for '{config.name}'")
    
    elif option == 'mingw64':
        config.nuitka_mingw64 = True
        print(f"Enabled Nuitka MinGW64 for '{config.name}'")
    
    elif option == 'disable-console':
        config.nuitka_disable_console = True
        print(f"Enabled Nuitka disable-console for '{config.name}'")
    
    elif option == 'experimental' and value:
        if not config.nuitka_experimental:
            config.nuitka_experimental = []
        config.nuitka_experimental.append(value)
        print(f"Added Nuitka experimental '{value}' to '{config.name}'")
    
    else:
        print(f"Unknown or invalid Nuitka option: {option}")
        return False
    
    # Save updated config
    build_manager.save_config(config)
    return True


async def register_commands():
    """Register build commands with the CLI."""
    return {
        'build-config': build_config_command,
        'build-source': build_source_command,
        'build-name': build_name_command,
        'build-version': build_version_command,
        'build-icon': build_icon_command,
        'build-onefile': build_onefile_command,
        'build-console': build_console_command,
        'build-hidden-imports': build_hidden_import_command,
        'build-data-files': build_data_files_command,
        'build-execute': build_execute_command,
        'build-list': build_list_command,
        'build-show': build_show_command,
        'build-reset': build_reset_command,
        'build-delete': build_delete_command,
        'build-systems': build_systems_command,
        'build-preview': build_preview_command,
        'build-collect-files': build_collect_files_command,
        'build-advanced-options': build_advanced_options_command,
        'build-splash': build_splash_command,
        'build-windowed': build_windowed_command,
        'build-metadata': build_metadata_command,
        'build-cx-freeze-options': build_cx_freeze_options_command,
        'build-nuitka-options': build_nuitka_options_command,
    }


# Register commands with the CLI (legacy format for documentation)
COMMANDS = {
    'build-config': {
        'function': build_config_command,
        'description': 'Create or switch to a build configuration',
        'args': {
            'name': {'help': 'Configuration name'},
            'system': {'help': 'Build system (pyinstaller, cx_freeze, nuitka, custom)', 'default': 'pyinstaller'}
        }
    },
    'build-source': {
        'function': build_source_command,
        'description': 'Set source file for active build configuration',
        'args': {
            'file': {'help': 'Source file path'}
        }
    },
    'build-name': {
        'function': build_name_command,
        'description': 'Set output name for active build configuration',
        'args': {
            'name': {'help': 'Output executable name'}
        }
    },
    'build-version': {
        'function': build_version_command,
        'description': 'Set version for active build configuration',
        'args': {
            'version': {'help': 'Version string (e.g., 1.0.0)'}
        }
    },
    'build-icon': {
        'function': build_icon_command,
        'description': 'Set icon for active build configuration',
        'args': {
            'icon': {'help': 'Icon file path (.ico)'}
        }
    },
    'build-onefile': {
        'function': build_onefile_command,
        'description': 'Enable/disable onefile mode',
        'args': {
            'enable': {'help': 'true/false', 'default': 'true'}
        }
    },
    'build-console': {
        'function': build_console_command,
        'description': 'Enable/disable console mode',
        'args': {
            'enable': {'help': 'true/false', 'default': 'true'}
        }
    },
    'build-hidden-imports': {
        'function': build_hidden_import_command,
        'description': 'Add hidden imports to build configuration',
        'args': {
            'imports': {'help': 'Comma-separated list of module names'}
        }
    },
    'build-data-files': {
        'function': build_data_files_command,
        'description': 'Add data files to build configuration',
        'args': {
            'source': {'help': 'Source file/directory path'},
            'dest': {'help': 'Destination path in executable'}
        }
    },
    'build-execute': {
        'function': build_execute_command,
        'description': 'Execute build using active or specified configuration',
        'args': {
            'config': {'help': 'Configuration name (optional)'}
        }
    },
    'build-list': {
        'function': build_list_command,
        'description': 'List all build configurations',
        'args': {}
    },
    'build-show': {
        'function': build_show_command,
        'description': 'Show build configuration details',
        'args': {
            'config': {'help': 'Configuration name (optional, uses active if not specified)'}
        }
    },
    'build-reset': {
        'function': build_reset_command,
        'description': 'Reset build configuration to defaults',
        'args': {
            'config': {'help': 'Configuration name (optional, uses active if not specified)'}
        }
    },
    'build-delete': {
        'function': build_delete_command,
        'description': 'Delete a build configuration',
        'args': {
            'config': {'help': 'Configuration name'}
        }
    },
    'build-systems': {
        'function': build_systems_command,
        'description': 'List available build systems and their status',
        'args': {}
    }
}