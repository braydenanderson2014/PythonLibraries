"""
Set Commands Module
Provides commands for setting build configuration variables like icons, splash screens, etc.
Can parse and use data from scan results.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
from build_system import Command, BuildContext

# Try to import PIL for image validation
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class SetCommand(Command):
    """
    Set configuration variables for the build process.
    Can use scan results to auto-detect resources.
    """
    
    @classmethod
    def get_name(cls) -> str:
        return "set"
    
    @classmethod
    def get_aliases(cls) -> List[str]:
        return ["config", "configure"]
    
    @classmethod
    def get_description(cls) -> str:
        return "Set build configuration variables (icon, splash, name, etc.)"
    
    @classmethod
    def get_flags(cls) -> List[str]:
        return ["--auto", "--auto-all", "--force", "--validate", "--list"]
    
    @classmethod
    def get_help(cls) -> str:
        return """
Set Command
===========

Usage: set <variable> <value> [options]

Description:
  Set configuration variables for the build process. Can automatically
  detect resources from scan results or accept manual paths.

Variables:
  icon <path>         Set application icon file (.ico, .png, .icns)
  splash <path>       Set splash screen image
  name <name>         Set application name
  version <version>   Set application version
  author <author>     Set application author
  description <text>  Set application description
  main <path>         Set main entry point file
  
  # Build-specific options
  onefile <bool>      Package as single file (true/false)
  console <bool>      Show console window (true/false)
  windowed <bool>     Windowed mode, no console (true/false)

Options:
  --auto              Auto-detect from scan results
  --force             Overwrite existing configuration
  --validate          Validate file existence/format
  --list              List all current settings

Examples:
  set icon ./assets/icon.ico           # Set icon file
  set icon --auto                      # Auto-detect icon from scan
  set name "My Application"            # Set app name
  set version 1.0.0                    # Set version
  set onefile true                     # Enable single file packaging
  set --list                           # Show all current settings
  
  # Batch setting from scan results
  set --auto-all                       # Auto-configure all from scan
"""
    
    def execute(self, *args, **kwargs) -> bool:
        """Execute the set command"""
        try:
            # Handle special flags
            if '--list' in args or kwargs.get('list'):
                return self._list_settings()
            
            if '--auto-all' in args or kwargs.get('auto_all'):
                return self._auto_configure_all()
            
            # Parse variable and value
            if len(args) < 2:
                self.context.log("Error: Missing variable or value", "ERROR")
                self.context.log("Usage: set <variable> <value>", "INFO")
                return False
            
            variable = args[0]
            value = args[1] if len(args) > 1 else kwargs.get('value')
            
            # Check for auto-detect flag
            auto_detect = '--auto' in args or kwargs.get('auto', False)
            force = '--force' in args or kwargs.get('force', False)
            validate = '--validate' in args or kwargs.get('validate', True)
            
            if auto_detect:
                return self._auto_detect_and_set(variable, force=force)
            
            # Manual setting
            return self._set_variable(variable, value, force=force, validate=validate)
            
        except Exception as e:
            self.context.log(f"Error executing set command: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return False
    
    def _list_settings(self) -> bool:
        """List all current configuration settings"""
        self.context.log("\n" + "="*60)
        self.context.log("Current Build Configuration")
        self.context.log("="*60 + "\n")
        
        # Application settings
        app_settings = {
            'name': 'Application Name',
            'version': 'Version',
            'author': 'Author',
            'description': 'Description',
            'main': 'Entry Point'
        }
        
        self.context.log("Application Settings:")
        self.context.log("-" * 40)
        for key, label in app_settings.items():
            value = self.context.get_config(key, 'Not set')
            self.context.log(f"  {label:20s}: {value}")
        
        # Resource settings
        self.context.log("\nResource Settings:")
        self.context.log("-" * 40)
        resource_settings = {
            'icon': 'Icon File',
            'splash': 'Splash Screen',
        }
        
        for key, label in resource_settings.items():
            value = self.context.get_config(key, 'Not set')
            if value != 'Not set' and os.path.exists(value):
                value = f"{value} ✓"
            elif value != 'Not set':
                value = f"{value} ✗ (not found)"
            self.context.log(f"  {label:20s}: {value}")
        
        # Build settings
        self.context.log("\nBuild Settings:")
        self.context.log("-" * 40)
        build_settings = {
            'onefile': 'Single File Mode',
            'console': 'Show Console',
            'windowed': 'Windowed Mode',
        }
        
        for key, label in build_settings.items():
            value = self.context.get_config(key, 'Not set')
            self.context.log(f"  {label:20s}: {value}")
        
        self.context.log("\n" + "="*60 + "\n")
        return True
    
    def _set_variable(self, variable: str, value: Any, force: bool = False, validate: bool = True) -> bool:
        """Set a configuration variable"""
        variable = variable.lower()
        
        # Check if already set
        if not force and self.context.get_config(variable) is not None:
            self.context.log(f"Warning: '{variable}' is already set to '{self.context.get_config(variable)}'", "WARN")
            self.context.log("Use --force to overwrite", "INFO")
            return False
        
        # Handle different variable types
        if variable in ['icon', 'splash', 'main']:
            return self._set_file_path(variable, value, validate)
        
        elif variable in ['onefile', 'console', 'windowed']:
            return self._set_boolean(variable, value)
        
        elif variable in ['name', 'version', 'author', 'description']:
            return self._set_string(variable, value)
        
        else:
            # Generic setting
            self.context.set_config(variable, value)
            self.context.log(f"Set {variable} = {value}")
            self._save_config()
            return True
    
    def _set_file_path(self, variable: str, path: str, validate: bool = True) -> bool:
        """Set a file path variable with validation"""
        path_obj = Path(path).resolve()
        
        if validate:
            if not path_obj.exists():
                self.context.log(f"Error: File not found: {path}", "ERROR")
                return False
            
            # Validate file type
            if variable == 'icon':
                if not self._validate_icon(path_obj):
                    self.context.log(f"Error: Invalid icon file format", "ERROR")
                    return False
            
            elif variable == 'splash':
                if not self._validate_image(path_obj):
                    self.context.log(f"Error: Invalid image file format", "ERROR")
                    return False
            
            elif variable == 'main':
                if path_obj.suffix != '.py':
                    self.context.log(f"Warning: Main entry point should be a .py file", "WARN")
        
        self.context.set_config(variable, str(path_obj))
        self.context.log(f"Set {variable} = {path_obj}")
        self._save_config()
        return True
    
    def _set_boolean(self, variable: str, value: Any) -> bool:
        """Set a boolean variable"""
        if isinstance(value, bool):
            bool_value = value
        elif isinstance(value, str):
            bool_value = value.lower() in ['true', 'yes', '1', 'on', 'enabled']
        else:
            bool_value = bool(value)
        
        self.context.set_config(variable, bool_value)
        self.context.log(f"Set {variable} = {bool_value}")
        self._save_config()
        return True
    
    def _set_string(self, variable: str, value: Any) -> bool:
        """Set a string variable"""
        str_value = str(value)
        self.context.set_config(variable, str_value)
        self.context.log(f"Set {variable} = {str_value}")
        self._save_config()
        return True
    
    def _auto_detect_and_set(self, variable: str, force: bool = False) -> bool:
        """Auto-detect variable value from scan results"""
        scan_results = self.context.get_memory('last_scan')
        
        if not scan_results:
            self.context.log("Error: No scan results found. Run 'scan' command first.", "ERROR")
            return False
        
        variable = variable.lower()
        
        if variable == 'icon':
            return self._auto_detect_icon(scan_results, force)
        
        elif variable == 'splash':
            return self._auto_detect_splash(scan_results, force)
        
        elif variable == 'main':
            return self._auto_detect_main(scan_results, force)
        
        elif variable == 'name':
            return self._auto_detect_name(scan_results, force)
        
        else:
            self.context.log(f"Error: Auto-detection not supported for '{variable}'", "ERROR")
            return False
    
    def _auto_detect_icon(self, scan_results: Dict, force: bool = False) -> bool:
        """Auto-detect icon file from scan results"""
        self.context.log("Auto-detecting icon file...")
        
        # Look for common icon file names and extensions
        icon_patterns = [
            'icon.ico', 'icon.png', 'icon.icns',
            'app_icon.ico', 'app_icon.png',
            'application.ico', 'logo.ico'
        ]
        
        icon_extensions = ['.ico', '.png', '.icns']
        
        # Check files from scan results
        files = scan_results.get('files', [])
        
        # First, try exact matches
        for pattern in icon_patterns:
            for file_info in files:
                if Path(file_info['path']).name.lower() == pattern.lower():
                    return self._set_file_path('icon', file_info['path'], validate=True)
        
        # Then, look in common directories
        for file_info in files:
            file_path = Path(file_info['path'])
            if file_path.suffix.lower() in icon_extensions:
                # Prefer files in assets, resources, or icons directories
                if any(part in file_path.parts for part in ['assets', 'resources', 'icons', 'img', 'images']):
                    if 'icon' in file_path.name.lower():
                        return self._set_file_path('icon', str(file_path), validate=True)
        
        # Last resort: any icon file
        for file_info in files:
            file_path = Path(file_info['path'])
            if file_path.suffix.lower() in icon_extensions:
                self.context.log(f"Found potential icon: {file_path}", "INFO")
                return self._set_file_path('icon', str(file_path), validate=True)
        
        self.context.log("No icon file found in scan results", "WARN")
        return False
    
    def _auto_detect_splash(self, scan_results: Dict, force: bool = False) -> bool:
        """Auto-detect splash screen from scan results"""
        self.context.log("Auto-detecting splash screen...")
        
        splash_patterns = [
            'splash.png', 'splash.jpg', 'splash_screen.png',
            'loading.png', 'startup.png'
        ]
        
        image_extensions = ['.png', '.jpg', '.jpeg', '.bmp']
        
        files = scan_results.get('files', [])
        
        # Try exact matches
        for pattern in splash_patterns:
            for file_info in files:
                if Path(file_info['path']).name.lower() == pattern.lower():
                    return self._set_file_path('splash', file_info['path'], validate=True)
        
        # Look for splash in name
        for file_info in files:
            file_path = Path(file_info['path'])
            if file_path.suffix.lower() in image_extensions:
                if 'splash' in file_path.name.lower() or 'loading' in file_path.name.lower():
                    return self._set_file_path('splash', str(file_path), validate=True)
        
        self.context.log("No splash screen found in scan results", "WARN")
        return False
    
    def _auto_detect_main(self, scan_results: Dict, force: bool = False) -> bool:
        """Auto-detect main entry point from scan results"""
        self.context.log("Auto-detecting main entry point...")
        
        # Check if scan-python was run
        python_scan = self.context.get_memory('python_scan')
        if python_scan and python_scan.get('entry_points'):
            entry_points = python_scan['entry_points']
            if len(entry_points) == 1:
                return self._set_file_path('main', entry_points[0], validate=True)
            elif len(entry_points) > 1:
                self.context.log(f"Multiple entry points found:", "INFO")
                for i, ep in enumerate(entry_points, 1):
                    self.context.log(f"  {i}. {ep}", "INFO")
                self.context.log("Please specify which one to use", "INFO")
                return False
        
        # Look for common main file names
        main_patterns = [
            'main.py', 'app.py', '__main__.py',
            'run.py', 'start.py', 'launcher.py'
        ]
        
        files = scan_results.get('files', [])
        
        for pattern in main_patterns:
            for file_info in files:
                if Path(file_info['path']).name.lower() == pattern.lower():
                    return self._set_file_path('main', file_info['path'], validate=True)
        
        self.context.log("No main entry point found in scan results", "WARN")
        return False
    
    def _auto_detect_name(self, scan_results: Dict, force: bool = False) -> bool:
        """Auto-detect application name from project directory"""
        # Use the project directory name as default
        project_name = Path.cwd().name
        
        # Clean up the name
        project_name = project_name.replace('_', ' ').replace('-', ' ').title()
        
        return self._set_string('name', project_name)
    
    def _auto_configure_all(self) -> bool:
        """Auto-configure all possible settings from scan results"""
        self.context.log("Auto-configuring from scan results...")
        
        scan_results = self.context.get_memory('last_scan')
        if not scan_results:
            self.context.log("Error: No scan results found. Run 'scan' command first.", "ERROR")
            return False
        
        success_count = 0
        total_count = 0
        
        # Try each auto-detection
        auto_detect_vars = ['name', 'icon', 'splash', 'main']
        
        for var in auto_detect_vars:
            total_count += 1
            if self._auto_detect_and_set(var, force=False):
                success_count += 1
        
        self.context.log(f"\nAuto-configuration complete: {success_count}/{total_count} variables set")
        
        # Show current configuration
        self._list_settings()
        
        return success_count > 0
    
    def _validate_icon(self, path: Path) -> bool:
        """Validate icon file"""
        if not PIL_AVAILABLE:
            # Can't validate without PIL, just check extension
            return path.suffix.lower() in ['.ico', '.png', '.icns']
        
        try:
            with Image.open(path) as img:
                # Check if it's a valid image
                img.verify()
                return True
        except Exception:
            return False
    
    def _validate_image(self, path: Path) -> bool:
        """Validate image file"""
        if not PIL_AVAILABLE:
            return path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.bmp', '.gif']
        
        try:
            with Image.open(path) as img:
                img.verify()
                return True
        except Exception:
            return False
    
    def _save_config(self):
        """Save configuration to file"""
        try:
            with open(self.context.config_path, 'w') as f:
                json.dump(self.context.config, f, indent=2)
            self.context.log_verbose(f"Configuration saved to {self.context.config_path}")
        except Exception as e:
            self.context.log(f"Error saving configuration: {e}", "ERROR")


class GetCommand(Command):
    """
    Get configuration variable values.
    """
    
    @classmethod
    def get_name(cls) -> str:
        return "get"
    
    @classmethod
    def get_aliases(cls) -> List[str]:
        return ["show"]
    
    @classmethod
    def get_description(cls) -> str:
        return "Get configuration variable values"
    
    @classmethod
    def get_flags(cls) -> List[str]:
        return ["--all"]
    
    @classmethod
    def get_help(cls) -> str:
        return """
Get Command
===========

Usage: get <variable> [options]

Description:
  Retrieve configuration variable values.

Examples:
  get icon              # Show icon path
  get name              # Show application name
  get --all             # Show all configuration
"""
    
    def execute(self, *args, **kwargs) -> bool:
        """Execute the get command"""
        try:
            if '--all' in args or kwargs.get('all'):
                # Show all configuration
                for key, value in self.context.config.items():
                    self.context.log(f"{key} = {value}")
                return True
            
            if len(args) < 1:
                self.context.log("Error: Missing variable name", "ERROR")
                return False
            
            variable = args[0].lower()
            value = self.context.get_config(variable)
            
            if value is None:
                self.context.log(f"Variable '{variable}' is not set", "WARN")
                return False
            
            self.context.log(f"{variable} = {value}")
            return True
            
        except Exception as e:
            self.context.log(f"Error executing get command: {e}", "ERROR")
            return False


class UnsetCommand(Command):
    """
    Remove/unset configuration variables.
    """
    
    @classmethod
    def get_name(cls) -> str:
        return "unset"
    
    @classmethod
    def get_aliases(cls) -> List[str]:
        return ["remove", "clear"]
    
    @classmethod
    def get_description(cls) -> str:
        return "Remove configuration variables"
    
    @classmethod
    def get_flags(cls) -> List[str]:
        return ["--all"]
    
    @classmethod
    def get_help(cls) -> str:
        return """
Unset Command
=============

Usage: unset <variable> [options]

Description:
  Remove configuration variables.

Options:
  --all    Clear all configuration

Examples:
  unset icon           # Remove icon setting
  unset --all          # Clear all configuration
"""
    
    def execute(self, *args, **kwargs) -> bool:
        """Execute the unset command"""
        try:
            if '--all' in args or kwargs.get('all'):
                self.context.config = {}
                self._save_config()
                self.context.log("All configuration cleared")
                return True
            
            if len(args) < 1:
                self.context.log("Error: Missing variable name", "ERROR")
                return False
            
            variable = args[0].lower()
            
            if variable in self.context.config:
                del self.context.config[variable]
                self._save_config()
                self.context.log(f"Removed '{variable}' from configuration")
                return True
            else:
                self.context.log(f"Variable '{variable}' is not set", "WARN")
                return False
            
        except Exception as e:
            self.context.log(f"Error executing unset command: {e}", "ERROR")
            return False
    
    def _save_config(self):
        """Save configuration to file"""
        try:
            with open(self.context.config_path, 'w') as f:
                json.dump(self.context.config, f, indent=2)
        except Exception as e:
            self.context.log(f"Error saving configuration: {e}", "ERROR")


# Register commands with the system
COMMANDS = [SetCommand, GetCommand, UnsetCommand]
