"""
Build Commands Module
Provides commands for building executables with PyInstaller.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
from build_system import Command, BuildContext


class BuildCommand(Command):
    """
    Build executable using PyInstaller with configured settings.
    """
    
    @classmethod
    def get_name(cls) -> str:
        return "build"
    
    @classmethod
    def get_aliases(cls) -> List[str]:
        return ["b", "compile"]
    
    @classmethod
    def get_description(cls) -> str:
        return "Build executable using PyInstaller"
    
    @classmethod
    def get_flags(cls) -> List[str]:
        return ["--entry", "--name", "--onefile", "--onedir", "--console", "--noconsole", "--icon", "--splash", "--clean", "--spec", "--dry-run"]
    
    @classmethod
    def get_help(cls) -> str:
        return """
Build Command
=============

Usage: build [options] <entry_point>

Description:
  Builds an executable using PyInstaller with the configured settings.
  Uses icon/splash from scan-icon command if available.
  
  The command constructs a PyInstaller command based on:
  - Configuration in build_config.json
  - Detected entry point (or specified)
  - Icon/splash settings from scan-icon
  - Additional options provided

Options:
  --entry <file>         Entry point Python file (auto-detected if not specified)
  --name <name>          Output executable name (default: project name)
  --onefile              Build as single file (default from config)
  --onedir               Build as directory
  --console              Show console window (default from config)
  --noconsole            Hide console window (GUI mode)
  --icon <path>          Icon file path (overrides config)
  --splash <path>        Splash image path (overrides config)
  --clean                Clean PyInstaller cache before build
  --spec <file>          Use existing spec file
  --dry-run              Show command without executing

Examples:
  build                           # Auto-detect entry point and build
  build --entry main.py           # Build specific file
  build --name MyApp --noconsole  # Build GUI app with custom name
  build --clean --onefile         # Clean build as single file
  build --dry-run                 # Preview PyInstaller command
"""
    
    def execute(self, *args, **kwargs) -> bool:
        """Execute the build command"""
        try:
            # Check if PyInstaller is available
            if not self._check_pyinstaller():
                return False
            
            # Parse options
            options = self._parse_build_options(args, kwargs)
            
            # Find or validate entry point
            entry_point = self._get_entry_point(options)
            if not entry_point:
                return False
            
            # Build PyInstaller command
            pyinstaller_cmd = self._build_pyinstaller_command(entry_point, options)
            
            # Display command
            self.context.log("PyInstaller command:")
            print(f"  {' '.join(pyinstaller_cmd)}")
            
            # Dry run check
            if options.get('dry_run'):
                self.context.log("Dry run mode - not executing", "INFO")
                return True
            
            # Execute build
            success = self._execute_build(pyinstaller_cmd, options)
            
            if success:
                self.context.log("Build completed successfully!", "INFO")
                self._save_build_info(entry_point, options)
            else:
                self.context.log("Build failed", "ERROR")
            
            return success
            
        except Exception as e:
            self.context.log(f"Build failed: {e}", "ERROR")
            import traceback
            if self.context.verbose:
                traceback.print_exc()
            return False
    
    def _check_pyinstaller(self) -> bool:
        """Check if PyInstaller is installed"""
        try:
            result = subprocess.run(
                ['pyinstaller', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                self.context.log_verbose(f"PyInstaller version: {version}")
                return True
        except FileNotFoundError:
            pass
        except Exception as e:
            self.context.log_verbose(f"Error checking PyInstaller: {e}")
        
        self.context.log("PyInstaller not found. Install with: pip install pyinstaller", "ERROR")
        return False
    
    def _parse_build_options(self, args: tuple, kwargs: dict) -> Dict[str, Any]:
        """Parse build options from arguments"""
        options = {
            'entry': None,
            'name': None,
            'onefile': None,
            'console': None,
            'icon': None,
            'splash': None,
            'clean': False,
            'spec': None,
            'dry_run': False,
            'extra_args': []
        }
        
        # Parse flags
        if '--clean' in args:
            options['clean'] = True
        if '--dry-run' in args:
            options['dry_run'] = True
        
        # Parse options with values
        i = 0
        while i < len(args):
            arg = args[i]
            
            if arg == '--entry' and i + 1 < len(args):
                options['entry'] = args[i + 1]
                i += 2
            elif arg == '--name' and i + 1 < len(args):
                options['name'] = args[i + 1]
                i += 2
            elif arg == '--icon' and i + 1 < len(args):
                options['icon'] = args[i + 1]
                i += 2
            elif arg == '--splash' and i + 1 < len(args):
                options['splash'] = args[i + 1]
                i += 2
            elif arg == '--spec' and i + 1 < len(args):
                options['spec'] = args[i + 1]
                i += 2
            elif arg == '--onefile':
                options['onefile'] = True
                i += 1
            elif arg == '--onedir':
                options['onefile'] = False
                i += 1
            elif arg == '--console':
                options['console'] = True
                i += 1
            elif arg == '--noconsole':
                options['console'] = False
                i += 1
            elif not arg.startswith('--'):
                # Assume it's the entry point if no --entry was specified
                if options['entry'] is None:
                    options['entry'] = arg
                i += 1
            else:
                i += 1
        
        # Apply defaults from config
        if options['onefile'] is None:
            options['onefile'] = self.context.get_config('pyinstaller', {}).get('onefile', True)
        
        if options['console'] is None:
            options['console'] = self.context.get_config('pyinstaller', {}).get('console', True)
        
        if options['name'] is None:
            options['name'] = self.context.get_config('pyinstaller', {}).get('name') or \
                             self.context.get_config('project_name', 'app')
        
        # Get icon/splash from config if not specified
        if options['icon'] is None:
            options['icon'] = self.context.get_config('build_icon') or \
                             self.context.get_config('pyinstaller', {}).get('icon')
        
        if options['splash'] is None:
            options['splash'] = self.context.get_config('build_splash')
        
        return options
    
    def _get_entry_point(self, options: Dict[str, Any]) -> Optional[Path]:
        """Get or detect entry point file"""
        # Use specified entry point
        if options['entry']:
            entry = Path(options['entry'])
            if not entry.exists():
                self.context.log(f"Error: Entry point '{options['entry']}' not found", "ERROR")
                return None
            return entry
        
        # Check for spec file
        if options['spec']:
            spec_file = Path(options['spec'])
            if not spec_file.exists():
                self.context.log(f"Error: Spec file '{options['spec']}' not found", "ERROR")
                return None
            return spec_file
        
        # Try to auto-detect entry point
        self.context.log("No entry point specified, attempting auto-detection...")
        
        # Check memory for previous scan
        python_scan = self.context.get_memory('python_scan')
        if python_scan and python_scan.get('entry_points'):
            entry_points = [Path(ep) for ep in python_scan['entry_points']]
            
            if len(entry_points) == 1:
                self.context.log(f"Auto-detected entry point: {entry_points[0]}")
                return entry_points[0]
            elif len(entry_points) > 1:
                self.context.log("Multiple entry points found. Please specify one:")
                for i, ep in enumerate(entry_points, 1):
                    print(f"  {i}. {ep}")
                
                try:
                    choice = int(input("Select entry point [1-{}]: ".format(len(entry_points))))
                    if 1 <= choice <= len(entry_points):
                        return entry_points[choice - 1]
                except (ValueError, KeyboardInterrupt):
                    pass
        
        # Look for common entry point names
        common_names = ['main.py', 'app.py', '__main__.py', 'run.py']
        for name in common_names:
            if Path(name).exists():
                self.context.log(f"Found entry point: {name}")
                return Path(name)
        
        self.context.log("Error: Could not detect entry point. Please specify with --entry", "ERROR")
        self.context.log("Tip: Run 'scan-python --find-main' first to find entry points", "INFO")
        return None
    
    def _build_pyinstaller_command(self, entry_point: Path, options: Dict[str, Any]) -> List[str]:
        """Build the PyInstaller command with all options"""
        cmd = ['pyinstaller']
        
        # Using spec file?
        if options['spec'] and entry_point.suffix == '.spec':
            cmd.append(str(entry_point))
            if options['clean']:
                cmd.append('--clean')
            return cmd
        
        # Basic options
        if options['onefile']:
            cmd.append('--onefile')
        else:
            cmd.append('--onedir')
        
        if not options['console']:
            cmd.append('--noconsole')
        else:
            cmd.append('--console')
        
        # Name
        if options['name']:
            cmd.extend(['--name', options['name']])
        
        # Icon
        if options['icon']:
            icon_path = Path(options['icon'])
            if icon_path.exists():
                cmd.extend(['--icon', str(icon_path)])
                self.context.log_verbose(f"Using icon: {icon_path}")
            else:
                self.context.log(f"Warning: Icon file not found: {icon_path}", "WARN")
        
        # Splash (PyInstaller 4.1+)
        if options['splash']:
            splash_path = Path(options['splash'])
            if splash_path.exists():
                cmd.extend(['--splash', str(splash_path)])
                self.context.log_verbose(f"Using splash: {splash_path}")
            else:
                self.context.log(f"Warning: Splash file not found: {splash_path}", "WARN")
        
        # Output directory
        build_dir = self.context.get_config('build_directory', 'dist')
        cmd.extend(['--distpath', build_dir])
        
        # Clean build
        if options['clean']:
            cmd.append('--clean')
        
        # Add extra args from config
        extra_args = self.context.get_config('pyinstaller', {}).get('extra_args', [])
        if extra_args:
            cmd.extend(extra_args)
        
        # Entry point (must be last)
        cmd.append(str(entry_point))
        
        return cmd
    
    def _execute_build(self, cmd: List[str], options: Dict[str, Any]) -> bool:
        """Execute the PyInstaller build command"""
        self.context.log("Starting build process...")
        
        try:
            # Run PyInstaller
            result = subprocess.run(
                cmd,
                cwd=self.context.project_root,
                capture_output=not self.context.verbose,
                text=True
            )
            
            if result.returncode == 0:
                return True
            else:
                self.context.log(f"PyInstaller exited with code {result.returncode}", "ERROR")
                if result.stderr and not self.context.verbose:
                    print(result.stderr)
                return False
                
        except Exception as e:
            self.context.log(f"Error executing PyInstaller: {e}", "ERROR")
            return False
    
    def _save_build_info(self, entry_point: Path, options: Dict[str, Any]):
        """Save build information to memory"""
        build_info = {
            'entry_point': str(entry_point),
            'name': options['name'],
            'onefile': options['onefile'],
            'console': options['console'],
            'icon': options['icon'],
            'splash': options['splash'],
            'timestamp': str(Path.cwd())  # Using as timestamp placeholder
        }
        
        self.context.set_memory('last_build', build_info)
        self.context.log_verbose("Build information saved to memory")


class CleanCommand(Command):
    """Clean build artifacts and PyInstaller cache."""
    
    @classmethod
    def get_name(cls) -> str:
        return "clean"
    
    @classmethod
    def get_aliases(cls) -> List[str]:
        return ["c"]
    
    @classmethod
    def get_description(cls) -> str:
        return "Clean build artifacts and cache files"
    
    @classmethod
    def get_flags(cls) -> List[str]:
        return ["--all", "--dist", "--build", "--spec"]
    
    @classmethod
    def get_help(cls) -> str:
        return """
Clean Command
=============

Usage: clean [options]

Description:
  Removes build artifacts, PyInstaller cache, and temporary files.
  
Options:
  --all              Clean everything including dist and build
  --cache            Clean only PyInstaller cache
  --specs            Remove generated .spec files
  --dry-run          Show what would be deleted without deleting

Examples:
  clean                # Clean build and __pycache__
  clean --all          # Clean everything
  clean --dry-run      # Preview what would be deleted
"""
    
    def execute(self, *args, **kwargs) -> bool:
        """Execute clean command"""
        try:
            clean_all = '--all' in args
            clean_cache = '--cache' in args
            clean_specs = '--specs' in args
            dry_run = '--dry-run' in args
            
            if dry_run:
                self.context.log("DRY RUN - No files will be deleted", "INFO")
            
            # Default: clean build and __pycache__ if no specific flags
            if not (clean_all or clean_cache or clean_specs):
                clean_all = True
            
            paths_to_remove = []
            
            # Build directories
            if clean_all:
                build_dir = Path(self.context.get_config('build_directory', 'dist'))
                if build_dir.exists():
                    paths_to_remove.append(build_dir)
                
                if Path('build').exists():
                    paths_to_remove.append(Path('build'))
                
                # __pycache__ directories
                for pycache in Path('.').rglob('__pycache__'):
                    paths_to_remove.append(pycache)
                
                # .pyc files
                for pyc in Path('.').rglob('*.pyc'):
                    paths_to_remove.append(pyc)
            
            # PyInstaller cache
            if clean_all or clean_cache:
                cache_paths = [
                    Path.home() / '.pyinstaller',
                    Path('.') / '.pyinstaller'
                ]
                for cache in cache_paths:
                    if cache.exists():
                        paths_to_remove.append(cache)
            
            # Spec files
            if clean_all or clean_specs:
                for spec in Path('.').glob('*.spec'):
                    paths_to_remove.append(spec)
            
            # Display what will be removed
            if paths_to_remove:
                print(f"\\nFiles/directories to remove:")
                for path in paths_to_remove:
                    print(f"  - {path}")
                
                if not dry_run:
                    # Remove files
                    import shutil
                    for path in paths_to_remove:
                        try:
                            if path.is_dir():
                                shutil.rmtree(path)
                                self.context.log_verbose(f"Removed directory: {path}")
                            else:
                                path.unlink()
                                self.context.log_verbose(f"Removed file: {path}")
                        except Exception as e:
                            self.context.log(f"Error removing {path}: {e}", "WARN")
                    
                    self.context.log(f"Cleaned {len(paths_to_remove)} item(s)", "INFO")
            else:
                self.context.log("Nothing to clean", "INFO")
            
            return True
            
        except Exception as e:
            self.context.log(f"Clean failed: {e}", "ERROR")
            return False
