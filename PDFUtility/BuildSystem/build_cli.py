#!/usr/bin/env python3
"""
PyInstaller Build Tool - CLI Core Module
Complete CLI interface with integrated core functionality (no GUI dependencies)
This module serves as both the CLI interface and the core functionality
"""

import sys
import os
import json
import argparse
import urllib.request
import urllib.parse
import tempfile
import subprocess
import platform
import glob
import shutil
import re
from datetime import datetime
from pathlib import Path

# ============================================================================
# UNICODE SAFE PRINTING
# ============================================================================

def safe_print(*args, **kwargs):
    """
    Unicode-safe print function that handles encoding issues on Windows
    """
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # Fallback for Windows console encoding issues
        fallback_args = []
        for arg in args:
            if isinstance(arg, str):
                # Replace Unicode emojis and special characters with ASCII equivalents
                fallback = (arg
                    .replace('🔄', '[->]')
                    .replace('❌', '[X]')
                    .replace('✅', '[OK]')
                    .replace('📋', '[LIST]')
                    .replace('🔍', '[SCAN]')
                    .replace('📦', '[PKG]')
                    .replace('🔧', '[TOOL]')
                    .replace('🚀', '[GO]')
                    .replace('🎉', '[SUCCESS]')
                    .replace('⚠️', '[WARN]')
                    .replace('💡', '[TIP]')
                    .replace('🖥️', '[OS]')
                    .replace('🏗️', '[BUILD]')
                    .replace('📁', '[DIR]')
                    .replace('📄', '[FILE]')
                    .replace('🔨', '[MAKE]')
                    .replace('⭐', '[*]')
                    .replace('📊', '[CHART]')
                    .replace('🔒', '[LOCK]')
                    .replace('🔓', '[UNLOCK]')
                    .replace('🔍', '[FIND]')
                    .replace('💻', '[PC]')
                    .replace('📱', '[APP]')
                    .replace('🌟', '[STAR]')
                    .replace('🎯', '[TARGET]')
                    .replace('🔗', '[LINK]')
                    .replace('📝', '[NOTE]')
                    .replace('⏰', '[TIME]')
                    .replace('🔔', '[BELL]')
                    .replace('📈', '[UP]')
                    .replace('📉', '[DOWN]')
                    .replace('🔑', '[KEY]')
                    .replace('🎮', '[GAME]')
                    .replace('🌐', '[WEB]')
                    .replace('📷', '[CAM]')
                    .replace('🎵', '[MUSIC]')
                    .replace('🎬', '[VIDEO]')
                    .replace('🔴', '[RED]')
                    .replace('🟢', '[GREEN]')
                    .replace('🟡', '[YELLOW]')
                    .replace('🔵', '[BLUE]')
                    .replace('🟣', '[PURPLE]')
                    .replace('⚫', '[BLACK]')
                    .replace('⚪', '[WHITE]')
                    .replace('🔺', '[UP]')
                    .replace('🔻', '[DOWN]')
                    .replace('🔸', '[DIAMOND]')
                    .replace('🔹', '[DIAMOND]')
                    .replace('💎', '[GEM]')
                    .replace('🏆', '[TROPHY]')
                    .replace('🎊', '[PARTY]')
                    .replace('🎈', '[BALLOON]')
                    .replace('🎁', '[GIFT]')
                    .replace('🍀', '[LUCK]')
                    .replace('⚡', '[BOLT]')
                    .replace('🌈', '[RAINBOW]')
                    .replace('🌙', '[MOON]')
                    .replace('☀️', '[SUN]')
                    .replace('⭐', '[STAR]')
                    .replace('🌟', '[SHINY]')
                )
                fallback_args.append(fallback)
            else:
                fallback_args.append(str(arg))
        
        try:
            print(*fallback_args, **kwargs)
        except:
            # Ultimate fallback - just print without special characters
            simple_args = [str(arg).encode('ascii', 'ignore').decode('ascii') for arg in args]
            print(*simple_args, **kwargs)

# ============================================================================
# SCRIPT LOCATION DETECTION
# ============================================================================

def get_script_location():
    """
    Get the actual location of the script, regardless of how it's called.
    Works across platforms and handles cases where:
    - Script is run directly (python build_cli.py)
    - Script is compiled with PyInstaller 
    - Script is called from PATH after being added as executable
    - Script is run from different working directory
    """
    try:
        # Method 1: PyInstaller detection
        if hasattr(sys, '_MEIPASS'):
            # Running from PyInstaller bundle
            script_dir = os.path.dirname(sys.executable)
            return os.path.abspath(script_dir)
        
        # Method 2: Direct script execution
        if __file__:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            return script_dir
        
        # Method 3: Fallback to current working directory
        return os.getcwd()
        
    except Exception as e:
        print(f"⚠️  Warning: Could not determine script location: {e}")
        return os.getcwd()

def get_working_context():
    """
    Get comprehensive context about where the script is and where it's running.
    Returns dict with script location, working directory, and other useful info.
    """
    try:
        script_location = get_script_location()
        working_directory = os.getcwd()
        
        # Check if we're running from the script's directory
        same_directory = os.path.abspath(script_location) == os.path.abspath(working_directory)
        
        # Get relative path if they're different
        relative_path = None
        if not same_directory:
            try:
                relative_path = os.path.relpath(script_location, working_directory)
            except ValueError:
                # Different drives on Windows
                relative_path = script_location
        
        # Detect execution method
        execution_method = "unknown"
        if hasattr(sys, '_MEIPASS'):
            execution_method = "pyinstaller"
        elif __file__ and __file__.endswith('.py'):
            execution_method = "python_script"
        elif sys.executable.endswith('.exe'):
            execution_method = "executable"
        
        return {
            'script_location': script_location,
            'working_directory': working_directory,
            'same_directory': same_directory,
            'relative_path': relative_path,
            'execution_method': execution_method,
            'platform': platform.system(),
            'python_executable': sys.executable
        }
        
    except Exception as e:
        print(f"⚠️  Warning: Error getting working context: {e}")
        return {
            'script_location': os.getcwd(),
            'working_directory': os.getcwd(), 
            'same_directory': True,
            'relative_path': None,
            'execution_method': "fallback",
            'platform': platform.system(),
            'python_executable': sys.executable
        }

# Initialize global context
SCRIPT_CONTEXT = get_working_context()

# ============================================================================
# CORE FUNCTIONALITY CLASSES
# ============================================================================

class ConsoleMemory:
    """Memory system for console mode to store scan results and configuration"""
    
    def __init__(self, memory_file="build_console_memory.json"):
        # Make memory file relative to script location, not current working directory
        if not os.path.isabs(memory_file):
            script_location = get_script_location()
            self.memory_file = os.path.join(script_location, memory_file)
        else:
            self.memory_file = memory_file
        self.memory = self.load_memory()
    
    def load_memory(self):
        """Load memory from file"""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load console memory: {e}")
        
        return {
            "scan_results": {},
            "build_config": {},
            "last_scan_type": None,
            "last_updated": None
        }
    
    def save_memory(self):
        """Save memory to file"""
        try:
            self.memory["last_updated"] = datetime.now().isoformat()
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(self.memory, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving console memory: {e}")
    
    def store_scan_results(self, scan_type, results, append=False):
        """Store scan results in memory"""
        if append and scan_type in self.memory["scan_results"]:
            existing = self.memory["scan_results"][scan_type]
            combined = list(set(existing + results))  # Remove duplicates
            self.memory["scan_results"][scan_type] = combined
        else:
            self.memory["scan_results"][scan_type] = results
        
        self.memory["last_scan_type"] = scan_type
        self.save_memory()
    
    def get_scan_results(self, scan_type=None):
        """Get scan results from memory"""
        if scan_type:
            return self.memory["scan_results"].get(scan_type, [])
        return self.memory["scan_results"]
    
    def store_config(self, config_data):
        """Store build configuration in memory"""
        self.memory["build_config"].update(config_data)
        self.save_memory()
    
    def get_config(self):
        """Get build configuration from memory"""
        return self.memory["build_config"]
    
    def clear_memory(self, section=None):
        """Clear memory section or all memory"""
        if section:
            if section in self.memory:
                self.memory[section] = {} if section in ["scan_results", "build_config"] else None
        else:
            self.memory = {
                "scan_results": {},
                "build_config": {},
                "last_scan_type": None,
                "last_updated": None
            }
        self.save_memory()
    
    def show_memory_status(self):
        """Display current memory status"""
        print("📋 Console Memory Status:")
        print("=" * 40)
        
        if self.memory["last_updated"]:
            print(f"Last Updated: {self.memory['last_updated']}")
        
        scan_results = self.memory["scan_results"]
        if scan_results:
            print(f"\nStored Scan Results:")
            for scan_type, files in scan_results.items():
                print(f"  📁 {scan_type}: {len(files)} files")
        else:
            print("\nNo scan results stored")
        
        config = self.memory["build_config"]
        if config:
            print(f"\nStored Configuration Keys: {list(config.keys())}")
        else:
            print("\nNo configuration stored")
            
    def show_detailed_memory_status(self):
        """Display detailed memory status with all contents"""
        print("📋 Detailed Console Memory Status:")
        print("=" * 50)
        
        if self.memory["last_updated"]:
            print(f"Last Updated: {self.memory['last_updated']}")
        
        scan_results = self.memory["scan_results"]
        if scan_results:
            print(f"\n📁 Detailed Scan Results:")
            for scan_type, files in scan_results.items():
                print(f"\n  📂 {scan_type.upper()} ({len(files)} files):")
                if files:
                    for file_path in files[:10]:  # Show first 10
                        print(f"    📄 {file_path}")
                    if len(files) > 10:
                        print(f"    ... and {len(files) - 10} more files")
                else:
                    print("    (No files)")
        else:
            print("\nNo scan results stored")
        
        config = self.memory["build_config"]
        if config:
            print(f"\n🏗️  Build Configuration:")
            for key, value in config.items():
                print(f"  {key}: {value}")
        else:
            print("\nNo build configuration stored")
            
        print(f"\n💾 Memory file location: {self.memory_file}")
        
        # Show memory file size
        try:
            if os.path.exists(self.memory_file):
                size = os.path.getsize(self.memory_file)
                print(f"💾 Memory file size: {size} bytes")
            else:
                print("💾 Memory file: Not created yet")
        except Exception as e:
            print(f"💾 Memory file: Error reading size - {e}")
            print("\nNo configuration stored")

class BuildToolCore:
    """Core functionality for CLI (no GUI dependencies)"""
    
    def __init__(self):
        self.config = self.load_environment_config()
        self.memory = ConsoleMemory()
        
    def load_environment_config(self):
        """Load configuration from Build_Script.env file"""
        config = {}
        env_file = "Build_Script.env"
        
        if os.path.exists(env_file):
            try:
                with open(env_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            config[key.strip()] = value.strip()
            except Exception as e:
                print(f"Warning: Could not load {env_file}: {e}")
        
        return config

    def find_python_with_pil(self):
        """Find a Python executable that has PIL/Pillow installed"""
        print("🔍 Searching for Python with PIL...")
        
        # List of Python executables to try in order of preference
        python_candidates = []
        
        if platform.system() == 'Windows':
            # Use py launcher with explicit version to bypass PATH issues
            python_candidates.extend([
                'py -3.13',  # Force Python 3.13 via py launcher
                'py -3.12',  # Try Python 3.12 
                'py -3.11',  # Try Python 3.11
                'py',        # Default py launcher
            ])
            
            # Direct paths to bypass PATH completely
            python_candidates.extend([
                'C:\\Users\\brayd\\AppData\\Local\\Programs\\Python\\Python313\\python.exe',
                'C:\\Python313\\python.exe',
                'C:\\Python312\\python.exe',
                'C:\\Python311\\python.exe',
            ])
        
        # Add fallbacks
        python_candidates.extend([
            'python',   # Current python (might be MSYS2)
            'python3',  # Python 3 specifically
            sys.executable,  # Current interpreter
        ])
        
        for python_cmd in python_candidates:
            try:
                print(f"🔍 Trying: {python_cmd}")
                
                # Handle py launcher with version flags
                if python_cmd.startswith('py '):
                    cmd_parts = python_cmd.split()
                else:
                    cmd_parts = [python_cmd]
                
                # Test if this Python has PIL
                test_cmd = cmd_parts + ['-c', 'from PIL import Image; print("PIL_AVAILABLE"); import sys; print(f"PYTHON_PATH:{sys.executable}")']
                
                result = subprocess.run(
                    test_cmd,
                    capture_output=True,
                    text=True,
                    timeout=10,
                    shell=True if python_cmd.startswith('py ') else False
                )
                
                if result.returncode == 0 and 'PIL_AVAILABLE' in result.stdout:
                    # Extract the actual Python path from output
                    for line in result.stdout.split('\n'):
                        if line.startswith('PYTHON_PATH:'):
                            actual_python = line.replace('PYTHON_PATH:', '')
                            print(f"🐍 Found Python with PIL: {python_cmd} -> {actual_python}")
                            return python_cmd
                    
                    print(f"🐍 Found Python with PIL: {python_cmd}")
                    return python_cmd
                else:
                    print(f"   ❌ No PIL or failed: return code {result.returncode}")
                    if result.stderr:
                        print(f"   Error: {result.stderr.strip()}")
                    
            except (subprocess.SubprocessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
                print(f"   ❌ Exception: {e}")
                continue
        
        print("⚠️  No Python installation with PIL found")
        return None
    
    def resolve_scan_path(self, scan_directory):
        """Resolve relative paths for scanning, supporting ../path and ./path patterns"""
        if scan_directory is None:
            return None
            
        # Handle relative paths
        if scan_directory.startswith('../') or scan_directory.startswith('./'):
            # Get the current working directory (where the command was run from)
            base_path = SCRIPT_CONTEXT['working_directory']
            
            # Resolve the relative path
            resolved_path = os.path.abspath(os.path.join(base_path, scan_directory))
            
            print(f"🔄 Resolving relative path:")
            print(f"   📁 Base directory: {base_path}")
            print(f"   📂 Relative path: {scan_directory}")
            print(f"   ✅ Resolved to: {resolved_path}")
            
            return resolved_path
        else:
            # Absolute path or simple directory name
            return scan_directory
    
    def scan_files(self, scan_type, scan_directory=None, contains_filter=None):
        """Scan for files of a specific type"""
        # First resolve any relative paths
        if scan_directory is not None:
            scan_directory = self.resolve_scan_path(scan_directory)
        
        if scan_directory is None:
            # Check if project root is configured
            memory = ConsoleMemory()
            build_config = memory.get_config()
            project_root = build_config.get('project_root')
            
            if project_root and os.path.exists(project_root):
                print(f"📁 Using configured project root: {project_root}")
                scan_directory = project_root
            elif SCRIPT_CONTEXT['same_directory']:
                # Running from script directory, use current working directory
                scan_directory = os.getcwd()
            else:
                # Running from different directory, offer choice or use working directory
                print(f"🔍 Script location: {SCRIPT_CONTEXT['script_location']}")
                print(f"📁 Working directory: {SCRIPT_CONTEXT['working_directory']}")
                print(f"❓ Scanning in working directory (where you called the command from)")
                print(f"💡 To scan script directory instead, use: --scan-here")
                print(f"💡 To set project root permanently, use: --set-root /path/to/project")
                scan_directory = SCRIPT_CONTEXT['working_directory']
        
        scan_patterns = {
            'icons': ['*.ico', '*.png', '*.jpg', '*.jpeg', '*.svg', '*.bmp', '*.gif'],
            'images': ['*.png', '*.jpg', '*.jpeg', '*.svg', '*.bmp', '*.gif', '*.tiff', '*.webp'],
            'config': ['*.json', '*.yaml', '*.yml', '*.toml', '*.ini', '*.cfg', '*.conf'],
            'data': ['*.csv', '*.xlsx', '*.db', '*.sqlite', '*.xml', '*.txt'],
            'templates': ['*.html', '*.jinja2', '*.j2', '*.template'],
            'python': ['*.py', '*.pyw'],
            'docs': ['*.md', '*.txt', '*.rst', '*.doc', '*.docx', '*.pdf'],
            'help': ['*help*', '*README*', '*guide*', '*tutorial*', '*manual*'],
            'splash': ['*splash*', '*logo*', '*banner*'],
            'json': ['*.json'],
            'tutorials': ['*tutorial*', '*guide*', '*example*', '*demo*'],
            'virtual': [],  # Special handling for virtual environments
            'project': ['*']  # Scan everything for project overview
        }
        
        if scan_type not in scan_patterns:
            print(f"❌ Unknown scan type: {scan_type}")
            print(f"Available types: {', '.join(scan_patterns.keys())}")
            return []
        
        # Special handling for virtual environments
        if scan_type == 'virtual':
            return self.scan_virtual_environments(scan_directory, contains_filter)
        
        patterns = scan_patterns[scan_type]
        found_files = []
        
        print(f"🔍 Scanning for {scan_type} files in: {scan_directory}")
        
        for pattern in patterns:
            search_pattern = os.path.join(scan_directory, '**', pattern)
            matches = glob.glob(search_pattern, recursive=True)
            
            for match in matches:
                if os.path.isfile(match):
                    # Apply contains filter if specified
                    if contains_filter:
                        try:
                            with open(match, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                if contains_filter.lower() in content.lower():
                                    found_files.append(match)
                        except:
                            # If we can't read the file, skip the contains filter
                            if contains_filter.lower() in os.path.basename(match).lower():
                                found_files.append(match)
                    else:
                        found_files.append(match)
        
        # Remove duplicates and sort
        found_files = sorted(list(set(found_files)))
        
        print(f"✅ Found {len(found_files)} {scan_type} files")
        for file in found_files[:10]:  # Show first 10
            print(f"  📄 {file}")
        
        if len(found_files) > 10:
            print(f"  ... and {len(found_files) - 10} more")
        
        return found_files
    
    def scan_virtual_environments(self, scan_directory=None, contains_filter=None):
        """Scan for virtual environments in the specified directory"""
        import platform
        
        if scan_directory is None:
            scan_directory = os.getcwd()
        
        print(f"🔍 Scanning for virtual environments in: {scan_directory}")
        
        virtual_envs = []
        
        # Look for directories that contain virtual environment indicators
        for root, dirs, files in os.walk(scan_directory):
            # Skip nested searches within virtual environments themselves
            if any(venv_indicator in root for venv_indicator in ['Scripts', 'bin', 'lib', 'Lib']):
                continue
                
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                
                # Check if this directory is a virtual environment
                is_venv = False
                venv_info = {}
                
                if platform.system() == "Windows":
                    # Check for Windows virtual environment structure
                    activate_bat = os.path.join(dir_path, 'Scripts', 'activate.bat')
                    activate_ps1 = os.path.join(dir_path, 'Scripts', 'Activate.ps1')
                    python_exe = os.path.join(dir_path, 'Scripts', 'python.exe')
                    pip_exe = os.path.join(dir_path, 'Scripts', 'pip.exe')
                    pyvenv_cfg = os.path.join(dir_path, 'pyvenv.cfg')
                    
                    if os.path.exists(activate_bat) or os.path.exists(activate_ps1):
                        is_venv = True
                        # Get Python version from the virtual environment
                        python_version = self.get_python_version_from_venv(python_exe, pyvenv_cfg)
                        venv_type = self.detect_venv_type(dir_path, pyvenv_cfg)
                        
                        venv_info = {
                            'path': dir_path,
                            'name': dir_name,
                            'type': f'Windows Virtual Environment ({venv_type})',
                            'activate_bat': os.path.exists(activate_bat),
                            'activate_ps1': os.path.exists(activate_ps1),
                            'python_exe': os.path.exists(python_exe),
                            'pip_exe': os.path.exists(pip_exe),
                            'pyvenv_cfg': os.path.exists(pyvenv_cfg),
                            'python_version': python_version,
                            'venv_type': venv_type,
                            'status': 'Healthy' if all([os.path.exists(activate_bat), os.path.exists(python_exe)]) else 'Needs Repair'
                        }
                else:
                    # Check for Unix/Linux virtual environment structure
                    activate_sh = os.path.join(dir_path, 'bin', 'activate')
                    python_bin = os.path.join(dir_path, 'bin', 'python')
                    pip_bin = os.path.join(dir_path, 'bin', 'pip')
                    pyvenv_cfg = os.path.join(dir_path, 'pyvenv.cfg')
                    
                    if os.path.exists(activate_sh):
                        is_venv = True
                        # Get Python version from the virtual environment
                        python_version = self.get_python_version_from_venv(python_bin, pyvenv_cfg)
                        venv_type = self.detect_venv_type(dir_path, pyvenv_cfg)
                        
                        venv_info = {
                            'path': dir_path,
                            'name': dir_name,
                            'type': f'Unix Virtual Environment ({venv_type})',
                            'activate_sh': os.path.exists(activate_sh),
                            'python_bin': os.path.exists(python_bin),
                            'pip_bin': os.path.exists(pip_bin),
                            'pyvenv_cfg': os.path.exists(pyvenv_cfg),
                            'python_version': python_version,
                            'venv_type': venv_type,
                            'status': 'Healthy' if all([os.path.exists(activate_sh), os.path.exists(python_bin)]) else 'Needs Repair'
                        }
                
                # Apply contains filter if specified
                if is_venv:
                    if contains_filter:
                        if contains_filter.lower() in dir_name.lower():
                            virtual_envs.append(venv_info)
                    else:
                        virtual_envs.append(venv_info)
        
        # Display results with detailed information
        print(f"✅ Found {len(virtual_envs)} virtual environments")
        
        for i, venv in enumerate(virtual_envs[:10], 1):  # Show first 10
            status_icon = "✅" if venv['status'] == 'Healthy' else "⚠️"
            python_ver = venv.get('python_version', 'Unknown')
            venv_type = venv.get('venv_type', 'Unknown')
            
            print(f"  {status_icon} [{i}] {venv['name']} ({venv['status']})")
            print(f"      📁 Path: {venv['path']}")
            print(f"      🐍 Python: {python_ver} | Type: {venv_type}")
            print(f"      🔧 Type: {venv['type']}")
            
            # Show specific components
            if platform.system() == "Windows":
                components = []
                if venv.get('activate_bat'): components.append("activate.bat")
                if venv.get('activate_ps1'): components.append("Activate.ps1")
                if venv.get('python_exe'): components.append("python.exe")
                if venv.get('pip_exe'): components.append("pip.exe")
                if venv.get('pyvenv_cfg'): components.append("pyvenv.cfg")
                
                missing = []
                if not venv.get('activate_bat'): missing.append("activate.bat")
                if not venv.get('python_exe'): missing.append("python.exe")
                if not venv.get('pip_exe'): missing.append("pip.exe")
                if not venv.get('pyvenv_cfg'): missing.append("pyvenv.cfg")
                
                print(f"      ✅ Components: {', '.join(components)}")
                if missing:
                    print(f"      ❌ Missing: {', '.join(missing)}")
            else:
                components = []
                if venv.get('activate_sh'): components.append("activate")
                if venv.get('python_bin'): components.append("python")
                if venv.get('pip_bin'): components.append("pip")
                if venv.get('pyvenv_cfg'): components.append("pyvenv.cfg")
                
                missing = []
                if not venv.get('activate_sh'): missing.append("activate")
                if not venv.get('python_bin'): missing.append("python")
                if not venv.get('pip_bin'): missing.append("pip")
                if not venv.get('pyvenv_cfg'): missing.append("pyvenv.cfg")
                
                print(f"      ✅ Components: {', '.join(components)}")
                if missing:
                    print(f"      ❌ Missing: {', '.join(missing)}")
            print()
        
        if len(virtual_envs) > 10:
            print(f"  ... and {len(virtual_envs) - 10} more virtual environments")
        
        # Return paths for memory storage (compatible with existing system)
        return [venv['path'] for venv in virtual_envs]
    
    def get_python_version_from_venv(self, python_exe, pyvenv_cfg):
        """Get Python version from virtual environment"""
        import subprocess
        
        # Try to get version from Python executable first
        if os.path.exists(python_exe):
            try:
                result = subprocess.run([
                    python_exe, "--version"
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    version_line = result.stdout.strip()
                    # Extract version number from "Python X.Y.Z"
                    if "Python" in version_line:
                        return version_line.replace("Python ", "").strip()
                    else:
                        return version_line.strip()
            except:
                pass  # Fall back to pyvenv.cfg
        
        # Try to get version from pyvenv.cfg
        if os.path.exists(pyvenv_cfg):
            try:
                with open(pyvenv_cfg, 'r') as f:
                    content = f.read()
                    for line in content.split('\n'):
                        if line.startswith('version'):
                            version = line.split('=')[1].strip()
                            return version
            except:
                pass
        
        return "Unknown"
    
    def detect_venv_type(self, venv_path, pyvenv_cfg):
        """Detect whether this is a venv or virtualenv created environment"""
        
        # Check pyvenv.cfg for creation command
        if os.path.exists(pyvenv_cfg):
            try:
                with open(pyvenv_cfg, 'r') as f:
                    content = f.read()
                    
                    # Look for command line that created the venv
                    for line in content.split('\n'):
                        if 'command' in line:
                            command = line.lower()
                            if 'virtualenv' in command:
                                return "virtualenv"
                            elif 'venv' in command or '-m venv' in command:
                                return "venv"
            except:
                pass
        
        # Check for virtualenv-specific files/directories
        virtualenv_indicators = [
            'pip-selfcheck.json',  # Old virtualenv versions
            'pyvenv.cfg'  # Both have this, but check content differences
        ]
        
        # Check for presence of certain files that indicate virtualenv
        if platform.system() == "Windows":
            scripts_dir = os.path.join(venv_path, "Scripts")
            # virtualenv creates more executables typically
            if os.path.exists(scripts_dir):
                scripts = os.listdir(scripts_dir)
                # virtualenv typically has wheel, setuptools, etc. executables
                virtualenv_scripts = ['wheel.exe', 'easy_install.exe']
                if any(script in scripts for script in virtualenv_scripts):
                    return "virtualenv"
        else:
            bin_dir = os.path.join(venv_path, "bin")
            if os.path.exists(bin_dir):
                scripts = os.listdir(bin_dir)
                virtualenv_scripts = ['wheel', 'easy_install']
                if any(script in scripts for script in virtualenv_scripts):
                    return "virtualenv"
        
        # Default to venv (Python's built-in module)
        return "venv"
    
    def find_python_executable(self, version):
        """Find a specific Python executable version, prioritizing official Python installs"""
        import subprocess
        import platform
        import os
        
        if platform.system() == "Windows":
            # Priority order: Official Python > Python Launcher > Direct commands
            # Avoid MinGW64 and other non-official installations
            
            # 1. Try official Python installation paths first
            username = os.environ.get('USERNAME', 'User')
            version_no_dots = version.replace('.', '')
            
            official_paths = [
                f"C:\\Users\\{username}\\AppData\\Local\\Programs\\Python\\Python{version_no_dots}\\python.exe",
                f"C:\\Python{version_no_dots}\\python.exe",
                f"C:\\Program Files\\Python {version}\\python.exe",
                f"C:\\Program Files (x86)\\Python {version}\\python.exe"
            ]
            
            # Test official paths first
            for path in official_paths:
                if os.path.exists(path):
                    try:
                        test_result = subprocess.run([
                            path, "--version"
                        ], capture_output=True, text=True, timeout=5)
                        
                        if test_result.returncode == 0:
                            version_output = test_result.stdout.strip()
                            # Ensure it's not MinGW64 Python
                            if (version in version_output and 
                                "msys64" not in path.lower() and 
                                "mingw64" not in path.lower()):
                                print(f"✅ Found official Python {version}: {path}")
                                return path
                    except:
                        continue
            
            # 2. Try Python Launcher with specific version
            launcher_patterns = [
                f"py -{version}",
                f"py -V:{version}",
                f"py -{version.split('.')[0]}.{version.split('.')[1]}" if '.' in version else f"py -{version}"
            ]
            
            for pattern in launcher_patterns:
                try:
                    cmd = pattern.split()
                    # First check what Python it would use
                    which_result = subprocess.run(
                        cmd + ["-c", "import sys; print(sys.executable)"],
                        capture_output=True, text=True, timeout=5
                    )
                    
                    if which_result.returncode == 0:
                        python_path = which_result.stdout.strip()
                        # Skip if it's MinGW64 Python
                        if ("msys64" in python_path.lower() or 
                            "mingw64" in python_path.lower()):
                            print(f"⚠️  Skipping MinGW64 Python: {python_path}")
                            continue
                        
                        # Test version
                        test_result = subprocess.run(
                            cmd + ["--version"], 
                            capture_output=True, text=True, timeout=5
                        )
                        
                        if test_result.returncode == 0:
                            version_output = test_result.stdout.strip()
                            if version in version_output:
                                print(f"✅ Found Python via launcher: {' '.join(cmd)} -> {python_path}")
                                return cmd
                except:
                    continue
            
            # 3. Try direct executable names (with MinGW64 filtering)
            direct_patterns = [
                f"python{version}",
                f"python{version}.exe",
                "python.exe",
                "python3.exe"
            ]
            
            for pattern in direct_patterns:
                try:
                    # Check where this executable points to
                    which_result = subprocess.run([
                        pattern, "-c", "import sys; print(sys.executable)"
                    ], capture_output=True, text=True, timeout=5)
                    
                    if which_result.returncode == 0:
                        python_path = which_result.stdout.strip()
                        # Skip MinGW64 installations
                        if ("msys64" in python_path.lower() or 
                            "mingw64" in python_path.lower()):
                            print(f"⚠️  Skipping MinGW64 Python: {python_path}")
                            continue
                        
                        # Test version
                        test_result = subprocess.run([
                            pattern, "--version"
                        ], capture_output=True, text=True, timeout=5)
                        
                        if test_result.returncode == 0:
                            version_output = test_result.stdout.strip()
                            if (version in version_output or 
                                version.replace(".", "") in version_output.replace(".", "")):
                                print(f"✅ Found Python executable: {pattern} -> {python_path}")
                                return pattern
                except:
                    continue
            
        else:  # Unix-like systems
            patterns = [
                f"python{version}",
                f"python{version.split('.')[0]}.{version.split('.')[1]}" if '.' in version else f"python{version}",
                "python3",
                "python"
            ]
            
            for pattern in patterns:
                try:
                    test_result = subprocess.run([
                        pattern, "--version"
                    ], capture_output=True, text=True, timeout=5)
                    
                    if test_result.returncode == 0:
                        version_output = test_result.stdout.strip()
                        if version in version_output:
                            return pattern
                except:
                    continue
            
            # Try common Unix locations
            common_locations = [
                f"/usr/bin/python{version}",
                f"/usr/local/bin/python{version}",
                f"/opt/python{version}/bin/python"
            ]
            
            for location in common_locations:
                if os.path.exists(location):
                    return location
        
        for location in common_locations:
            if os.path.exists(location):
                return location
        
        return None
    
    def find_latest_python_version(self):
        """Find the latest/newest Python version available on the system"""
        import subprocess
        import platform
        import re
        import shutil
        
        print("🔍 Scanning system for available Python versions...")
        
        available_versions = []
        
        if platform.system() == "Windows":
            # Try Python Launcher first (most reliable on Windows)
            try:
                # Check if py.exe exists
                if shutil.which("py"):
                    result = subprocess.run(["py", "-0"], capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        print("   ✅ Python Launcher found, scanning versions...")
                        # Parse the output to extract version numbers
                        for line in result.stdout.split('\n'):
                            # Look for patterns like " -V:3.13" or " -3.12-64" or " -3.11"
                            match = re.search(r'-(?:V:)?(\d+\.\d+)', line.strip())
                            if match:
                                version = match.group(1)
                                if version not in available_versions:
                                    available_versions.append(version)
                        print(f"   Found via launcher: {available_versions}")
            except:
                print("   ⚠️  Python Launcher not working")
            
            # Also try direct Python executables in common locations
            common_paths = [
                r"C:\Python*\python.exe",
                r"C:\Program Files\Python*\python.exe", 
                r"C:\Program Files (x86)\Python*\python.exe",
                r"C:\Users\*\AppData\Local\Programs\Python\Python*\python.exe"
            ]
            
            # Try direct executable names
            python_patterns = [
                "python3.12", "python3.11", "python3.10", "python3.9", "python3.8",
                "python312", "python311", "python310", "python39", "python38",
                "python3", "python"
            ]
            
            for pattern in python_patterns:
                if shutil.which(pattern):
                    try:
                        # Check where this Python executable is located
                        which_result = subprocess.run([pattern, "-c", "import sys; print(sys.executable)"], 
                                                    capture_output=True, text=True, timeout=5)
                        
                        if which_result.returncode == 0:
                            python_path = which_result.stdout.strip()
                            # Skip MinGW64 Python installations
                            if ("msys64" in python_path.lower() or 
                                "mingw64" in python_path.lower()):
                                print(f"   ⚠️  Skipping MinGW64 Python: {python_path}")
                                continue
                        
                        result = subprocess.run([pattern, "--version"], 
                                              capture_output=True, text=True, timeout=5)
                        if result.returncode == 0:
                            version_output = result.stdout.strip()
                            version_match = re.search(r'Python (\d+\.\d+\.\d+)', version_output)
                            if version_match:
                                full_version = version_match.group(1)
                                major_minor = '.'.join(full_version.split('.')[:2])
                                if major_minor not in available_versions:
                                    available_versions.append(major_minor)
                                    print(f"   ✅ Found official Python {major_minor}: {python_path}")
                    except:
                        continue
        else:
            # Unix/Linux/macOS patterns
            python_patterns = [
                "python3.12", "python3.11", "python3.10", "python3.9", "python3.8", "python3.7",
                "python3", "python"
            ]
            
            for pattern in python_patterns:
                if shutil.which(pattern):
                    try:
                        result = subprocess.run([pattern, "--version"], 
                                              capture_output=True, text=True, timeout=5)
                        if result.returncode == 0:
                            version_output = result.stdout.strip()
                            version_match = re.search(r'Python (\d+\.\d+\.\d+)', version_output)
                            if version_match:
                                full_version = version_match.group(1)
                                major_minor = '.'.join(full_version.split('.')[:2])
                                if major_minor not in available_versions:
                                    available_versions.append(major_minor)
                    except:
                        continue
        
        # Remove duplicates and sort
        available_versions = list(set(available_versions))
        
        if not available_versions:
            print("   ⚠️  No Python versions detected")
            # Fallback: try to get current Python version
            try:
                import sys
                current_version = f"{sys.version_info.major}.{sys.version_info.minor}"
                print(f"   📍 Using current Python version: {current_version}")
                return current_version
            except:
                return None
        
        # Sort versions to find the latest
        def version_sort_key(v):
            try:
                return tuple(map(int, v.split('.')))
            except:
                return (0, 0)
        
        available_versions.sort(key=version_sort_key, reverse=True)
        latest_version = available_versions[0]
        
        print(f"   🐍 Available Python versions: {', '.join(available_versions)}")
        print(f"   ✨ Latest version detected: Python {latest_version}")
        
        return latest_version
    
    def handle_scan_command(self, scan_type, append_mode=False, override_mode=False, scan_directory=None, contains_filter=None):
        """Handle scan command with memory storage"""
        results = self.scan_files(scan_type, scan_directory, contains_filter)
        
        if results:
            # Determine the storage mode
            if override_mode:
                # Override mode: completely replace existing results
                self.memory.store_scan_results(scan_type, results, append=False)
                print(f"🔄 Overrode {scan_type} in memory with {len(results)} files")
            elif append_mode:
                # Append mode: add to existing results
                self.memory.store_scan_results(scan_type, results, append=True)
                print(f"📚 Appended {len(results)} files to {scan_type} in memory")
            else:
                # Default mode: replace existing results
                self.memory.store_scan_results(scan_type, results, append=False)
                print(f"💾 Stored {len(results)} {scan_type} files in memory")
        
        return results
    
    def start_build(self, process_type="build"):
        """Start build process with different types"""
        if process_type.lower() == "build":
            return self.execute_pyinstaller_build()
        elif process_type.lower() == "quick":
            return self.execute_quick_build()
        elif process_type.lower() == "custom":
            return self.execute_custom_build()
        elif process_type.lower() == "package":
            return self.execute_package_build()
        elif process_type.lower() == "msiwrapping":
            return self.execute_package_build()  # Alias for package
        else:
            print(f"❌ Unknown build type: {process_type}")
            print("Available types: build, quick, custom, package, msiwrapping")
            return False

    def execute_pyinstaller_build(self):
        """Execute PyInstaller build using memory configuration"""
        try:
            print("🔨 PyInstaller Build Process")
            print("=" * 40)
            
            # Get build configuration from memory
            build_config = self.memory.get_config()
            
            # Check for required configuration
            main_file = build_config.get('main_file')
            if not main_file:
                # Try to auto-detect main file
                print("🔍 No main file specified, attempting auto-detection...")
                main_file = self.auto_detect_main_file()
                if main_file:
                    print(f"✅ Auto-detected main file: {main_file}")
                    build_config['main_file'] = main_file
                    self.memory.store_config(build_config)
                else:
                    print("❌ No main file found. Please specify using --main <filename>")
                    return False
            
            # Validate main file exists
            if not os.path.exists(main_file):
                print(f"❌ Main file not found: {main_file}")
                return False
            
            # Build PyInstaller command
            command = self.build_pyinstaller_command(build_config)
            
            # Show command preview
            print("\n📋 Build Command Preview:")
            print("-" * 30)
            cmd_str = " \\\n  ".join(command) if len(" ".join(command)) > 80 else " ".join(command)
            print(f"{cmd_str}")
            
            # Show build summary
            self.show_build_summary(build_config)
            
            # Execute build
            return self.execute_build_command(command)
            
        except Exception as e:
            print(f"❌ Build error: {e}")
            return False

    def execute_quick_build(self):
        """Execute quick build with auto-detection"""
        try:
            print("🚀 Quick Build Mode")
            print("=" * 30)
            
            # Auto-detect main file
            main_file = self.auto_detect_main_file()
            if not main_file:
                print("❌ Could not auto-detect main file")
                return False
            
            # Create minimal build configuration
            build_config = {
                'name': self.auto_generate_name(main_file),
                'main_file': main_file,
                'include_date': True,
                'onefile': True,
                'windowed': self.detect_gui_app(main_file),
                'clean': True
            }
            
            # Auto-detect icon
            icon_file = self.auto_detect_icon()
            if icon_file:
                build_config['icon'] = icon_file
                print(f"✅ Auto-detected icon: {icon_file}")
            
            # Store configuration
            self.memory.store_config(build_config)
            
            # Build and execute
            command = self.build_pyinstaller_command(build_config)
            self.show_build_summary(build_config)
            
            return self.execute_build_command(command)
            
        except Exception as e:
            print(f"❌ Quick build error: {e}")
            return False

    def execute_custom_build(self):
        """Execute custom build with user interaction"""
        print("⚙️  Custom Build Mode")
        print("=" * 30)
        print("Custom build mode requires interactive CLI interface.")
        print("Please use: build_cli --console")
        print("Then navigate to: Project Management → Configure build settings")
        return False

    def build_pyinstaller_command(self, config):
        """Build PyInstaller command from configuration"""
        command = ["pyinstaller"]
        
        # Determine OS-specific path separator for --add-data
        import platform
        path_separator = ';' if platform.system() == 'Windows' else ':'
        
        # DEBUG: Confirm we're using the updated version
        safe_print(f"🔧 build_pyinstaller_command() - Using path separator: '{path_separator}' for {platform.system()} [UPDATED VERSION]")
        
        # Generate build name
        build_name = self.generate_build_filename(config)
        command.extend(["--name", build_name])
        
        # Basic options
        if config.get('onefile', True):
            command.append("--onefile")
        else:
            command.append("--onedir")
            
        if config.get('windowed', False):
            command.append("--windowed")
        else:
            command.append("--console")
            
        if config.get('clean', True):
            command.append("--clean")
            
        if config.get('debug', False):
            command.append("--debug=all")
        
        # Icon
        if config.get('icon'):
            icon_path = os.path.abspath(config['icon'])
            command.extend(["--icon", icon_path])
            # Also include icon in data files with proper OS separator
            icon_data_arg = f"--add-data={icon_path}{path_separator}."
            command.append(icon_data_arg)
            safe_print(f"🔧 Adding icon data: {icon_data_arg}")
        
        # Include scan results as data files
        scan_results = self.memory.get_scan_results()
        for scan_type, files in scan_results.items():
            if scan_type in ['config', 'data', 'templates', 'docs']:
                for file_path in files:
                    if os.path.exists(file_path):
                        # Add as data file with proper OS separator
                        data_arg = f"--add-data={file_path}{path_separator}."
                        command.append(data_arg)
                        safe_print(f"🔧 Adding data file: {data_arg}")
        
        # Debug: Show path separator being used
        safe_print(f"🔧 Path separator decision: Platform={platform.system()}, Using='{path_separator}' [FINAL CHECK]")
        
        # OS-specific optimizations
        if platform.system() == 'Windows':
            # Windows-specific PyInstaller options
            command.append("--noupx")  # UPX can cause issues on Windows
        elif platform.system() == 'Linux':
            # Linux-specific optimizations
            command.append("--strip")  # Strip debug symbols on Linux
        elif platform.system() == 'Darwin':  # macOS
            # macOS-specific optimizations
            command.append("--osx-bundle-identifier")
            bundle_id = config.get('bundle_id', f"com.buildtool.{config.get('name', 'app').lower()}")
            command.append(bundle_id)
        
        # Main entry point
        main_file = os.path.abspath(config['main_file'])
        command.append(main_file)
        
        return command

    def find_windows_sdk_tool(self, tool_name):
        """Find Windows SDK tools (makeappx.exe, signtool.exe) and add to PATH if needed"""
        try:
            import platform
            if platform.system() != 'Windows':
                return None
                
            # First, check if it's already in PATH
            try:
                result = subprocess.run([tool_name, '--help'], 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=5)
                print(f"✅ {tool_name} found in system PATH")
                return tool_name  # Found in PATH
            except:
                pass
            
            # Find Windows SDK installation
            sdk_base_paths = [
                r"C:\Program Files (x86)\Windows Kits\10\bin",
                r"C:\Program Files\Windows Kits\10\bin"
            ]
            
            latest_sdk_path = None
            latest_version = None
            
            for base_path in sdk_base_paths:
                if os.path.exists(base_path):
                    # Find latest SDK version
                    try:
                        for item in os.listdir(base_path):
                            item_path = os.path.join(base_path, item)
                            if os.path.isdir(item_path) and re.match(r'^\d+\.\d+\.\d+\.\d+$', item):
                                if latest_version is None or item > latest_version:
                                    latest_version = item
                                    latest_sdk_path = item_path
                    except:
                        continue
            
            if not latest_sdk_path:
                return None
            
            # Determine architecture
            import platform
            arch = "x64" if platform.machine().endswith('64') else "x86"
            
            # Full path to SDK tools
            sdk_tools_path = os.path.join(latest_sdk_path, arch)
            tool_full_path = os.path.join(sdk_tools_path, tool_name)
            
            if os.path.exists(tool_full_path):
                print(f"🔍 Found {tool_name} at: {tool_full_path}")
                print(f"📁 SDK Tools Directory: {sdk_tools_path}")
                
                # Check if this path is already in current session PATH
                current_path = os.environ.get('PATH', '')
                if sdk_tools_path not in current_path:
                    print(f"💡 Adding SDK tools to PATH for this session: {sdk_tools_path}")
                    os.environ['PATH'] = sdk_tools_path + os.pathsep + current_path
                    
                    # Provide instructions for permanent PATH addition
                    print("� To permanently add Windows SDK tools to PATH:")
                    print(f"   Add this directory to your system PATH: {sdk_tools_path}")
                    print("   Or run this PowerShell command as Administrator:")
                    print(f"   [Environment]::SetEnvironmentVariable('PATH', $env:PATH + ';{sdk_tools_path}', 'Machine')")
                
                return tool_name  # Can now use tool name directly
            
            return None
            
        except Exception as e:
            print(f"❌ Error finding {tool_name}: {e}")
            return None

    def setup_windows_sdk_path(self):
        """Helper method to set up Windows SDK PATH - can be called independently"""
        try:
            print("🔧 Windows SDK PATH Setup")
            print("=" * 40)
            
            # Find the latest SDK
            sdk_base_paths = [
                r"C:\Program Files (x86)\Windows Kits\10\bin",
                r"C:\Program Files\Windows Kits\10\bin"
            ]
            
            latest_sdk_path = None
            latest_version = None
            
            for base_path in sdk_base_paths:
                if os.path.exists(base_path):
                    try:
                        for item in os.listdir(base_path):
                            item_path = os.path.join(base_path, item)
                            if os.path.isdir(item_path) and re.match(r'^\d+\.\d+\.\d+\.\d+$', item):
                                if latest_version is None or item > latest_version:
                                    latest_version = item
                                    latest_sdk_path = item_path
                    except:
                        continue
            
            if not latest_sdk_path:
                print("❌ Windows SDK not found")
                print("💡 Install Windows SDK from: https://developer.microsoft.com/windows/downloads/windows-sdk/")
                return False
            
            # Determine architecture
            import platform
            arch = "x64" if platform.machine().endswith('64') else "x86"
            sdk_tools_path = os.path.join(latest_sdk_path, arch)
            
            if not os.path.exists(sdk_tools_path):
                print(f"❌ SDK tools directory not found: {sdk_tools_path}")
                return False
                
            print(f"✅ Found Windows SDK {latest_version}")
            print(f"📁 Tools Directory: {sdk_tools_path}")
            print()
            print("🔧 To add Windows SDK tools to your PATH:")
            print()
            print("Option 1 - PowerShell (Run as Administrator):")
            print(f"[Environment]::SetEnvironmentVariable('PATH', $env:PATH + ';{sdk_tools_path}', 'Machine')")
            print()
            print("Option 2 - Environment Variables GUI:")
            print("1. Press Win+R, type 'sysdm.cpl', press Enter")
            print("2. Click 'Environment Variables'")
            print("3. Select 'PATH' in System Variables, click 'Edit'")
            print("4. Click 'New' and add:")
            print(f"   {sdk_tools_path}")
            print("5. Click OK to save")
            print()
            print("Option 3 - Command Prompt (Run as Administrator):")
            print(f"setx PATH \"%PATH%;{sdk_tools_path}\" /M")
            print()
            print("💡 After adding to PATH, restart your terminal/VS Code for changes to take effect")
            
            return True
            
        except Exception as e:
            print(f"❌ Error in SDK PATH setup: {e}")
            return False

    def collect_packaging_files(self):
        """Collect and organize files for packaging"""
        try:
            print("📦 File Collection for Packaging")
            print("=" * 40)
            
            # Scan for all relevant file types
            print("🔍 Scanning for packaging assets...")
            
            # Scan for icons using contains filter
            print("\n📎 Scanning for icon files...")
            icon_results = self.scan_files_for_packaging('icons', contains='ico')
            
            # Scan for splash screens
            print("🎨 Scanning for splash files...")
            splash_results = self.scan_files_for_packaging('splash')
            
            # Scan for executables
            print("🚀 Scanning for executables...")
            exe_results = self.scan_files_for_packaging('executables', contains='exe')
            
            # Create collection directory
            collection_dir = os.path.join(os.getcwd(), 'packaging_collection')
            os.makedirs(collection_dir, exist_ok=True)
            
            print(f"\n📁 Collection directory: {collection_dir}")
            
            # Organize files
            collected_files = self.organize_collected_files(
                collection_dir, icon_results, splash_results, exe_results
            )
            
            # Store collection results in memory for packaging
            self.store_collection_results(collected_files)
            
            print("\n✅ File collection completed!")
            return True
            
        except Exception as e:
            print(f"❌ Error collecting packaging files: {e}")
            return False

    def scan_files_for_packaging(self, scan_type, contains=None):
        """Scan for specific file types with optional contains filter"""
        try:
            # Get current directory
            current_dir = os.getcwd()
            
            # Define file patterns based on scan type
            patterns = {
                'icons': ['*.ico', '*.png'],
                'splash': ['*splash*', '*Splash*', '*.png', '*.jpg'],
                'executables': ['*.exe']
            }
            
            found_files = []
            
            if scan_type in patterns:
                for pattern in patterns[scan_type]:
                    for file_path in glob.glob(os.path.join(current_dir, pattern)):
                        if os.path.isfile(file_path):
                            # Apply contains filter if specified
                            if contains:
                                if contains.lower() in os.path.basename(file_path).lower():
                                    found_files.append(file_path)
                            else:
                                # For splash files, be more selective
                                if scan_type == 'splash':
                                    filename = os.path.basename(file_path).lower()
                                    if 'splash' in filename or filename.startswith('splash'):
                                        found_files.append(file_path)
                                else:
                                    found_files.append(file_path)
            
            print(f"   Found {len(found_files)} {scan_type} files:")
            for file_path in found_files:
                print(f"   • {os.path.basename(file_path)}")
                
            return found_files
            
        except Exception as e:
            print(f"❌ Error scanning for {scan_type}: {e}")
            return []

    def organize_collected_files(self, collection_dir, icons, splashes, executables):
        """Organize collected files into proper structure"""
        try:
            organized = {
                'icons': [],
                'splashes': [],
                'executables': [],
                'collection_dir': collection_dir
            }
            
            # Create subdirectories
            icons_dir = os.path.join(collection_dir, 'icons')
            splashes_dir = os.path.join(collection_dir, 'splashes')  
            exe_dir = os.path.join(collection_dir, 'executables')
            
            os.makedirs(icons_dir, exist_ok=True)
            os.makedirs(splashes_dir, exist_ok=True)
            os.makedirs(exe_dir, exist_ok=True)
            
            # Copy and organize icons
            for icon_path in icons:
                dest_path = os.path.join(icons_dir, os.path.basename(icon_path))
                shutil.copy2(icon_path, dest_path)
                organized['icons'].append(dest_path)
                print(f"📎 Collected icon: {os.path.basename(icon_path)}")
            
            # Copy and organize splashes
            for splash_path in splashes:
                dest_path = os.path.join(splashes_dir, os.path.basename(splash_path))
                shutil.copy2(splash_path, dest_path)
                organized['splashes'].append(dest_path)
                print(f"🎨 Collected splash: {os.path.basename(splash_path)}")
            
            # Copy and organize executables
            for exe_path in executables:
                dest_path = os.path.join(exe_dir, os.path.basename(exe_path))
                shutil.copy2(exe_path, dest_path)
                organized['executables'].append(dest_path)
                print(f"🚀 Collected executable: {os.path.basename(exe_path)}")
            
            return organized
            
        except Exception as e:
            print(f"❌ Error organizing files: {e}")
            return {}

    def store_collection_results(self, collected_files):
        """Store collection results in memory for use by packaging"""
        try:
            # Store collected files using the proper memory interface
            if collected_files.get('icons'):
                self.memory.store_scan_results('collected_icons', collected_files['icons'])
            
            if collected_files.get('splashes'):
                self.memory.store_scan_results('collected_splashes', collected_files['splashes'])
                
            if collected_files.get('executables'):
                self.memory.store_scan_results('collected_executables', collected_files['executables'])
            
            if collected_files.get('collection_dir'):
                self.memory.store_scan_results('collection_dir', [collected_files['collection_dir']])
            
            print("💾 Stored collection results in memory")
            
        except Exception as e:
            print(f"❌ Error storing collection results: {e}")

    def import_configuration(self, import_file):
        """Import configuration from various file formats"""
        try:
            print("📥 Configuration Import")
            print("=" * 30)
            
            if not os.path.exists(import_file):
                print(f"❌ File not found: {import_file}")
                return False
            
            # Determine file format
            file_ext = os.path.splitext(import_file)[1].lower()
            
            if file_ext == '.json':
                return self.import_json_config(import_file)
            elif file_ext == '.xml':
                return self.import_xml_config(import_file)
            elif file_ext == '.spec':
                return self.import_spec_config(import_file)
            else:
                print(f"❌ Unsupported file format: {file_ext}")
                print("💡 Supported formats: .json, .xml, .spec")
                return False
                
        except Exception as e:
            print(f"❌ Error importing configuration: {e}")
            return False

    def export_configuration(self, export_file):
        """Export current configuration to various file formats"""
        try:
            print("📤 Configuration Export")
            print("=" * 30)
            
            # Determine file format
            file_ext = os.path.splitext(export_file)[1].lower()
            
            if file_ext == '.json':
                return self.export_json_config(export_file)
            elif file_ext == '.xml':
                return self.export_xml_config(export_file)
            elif file_ext == '.spec':
                return self.export_spec_config(export_file)
            else:
                print(f"❌ Unsupported file format: {file_ext}")
                print("💡 Supported formats: .json, .xml, .spec")
                return False
                
        except Exception as e:
            print(f"❌ Error exporting configuration: {e}")
            return False

    def import_json_config(self, json_file):
        """Import configuration from JSON file"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            print(f"📋 Loaded JSON configuration: {json_file}")
            imported_items = 0
            
            # Import tutorials if available
            if 'tutorials' in config_data or 'Tutorials' in config_data:
                tutorials = config_data.get('tutorials', config_data.get('Tutorials', {}))
                if tutorials:
                    tutorial_files = tutorials.get('files', []) if isinstance(tutorials, dict) else tutorials
                    if tutorial_files:
                        self.memory.store_scan_results('tutorials', tutorial_files)
                        print(f"📚 Imported {len(tutorial_files)} tutorial files")
                        imported_items += 1
            
            # Import help documents
            if 'help' in config_data or 'Help' in config_data or 'HELP' in config_data:
                help_data = config_data.get('help', config_data.get('Help', config_data.get('HELP', {})))
                if help_data:
                    help_files = help_data.get('files', []) if isinstance(help_data, dict) else help_data
                    if help_files:
                        self.memory.store_scan_results('help', help_files)
                        print(f"📄 Imported {len(help_files)} help files")
                        imported_items += 1
            
            # Import additional files
            if 'additional' in config_data or 'Additional' in config_data:
                additional = config_data.get('additional', config_data.get('Additional', {}))
                if additional:
                    for category, files in additional.items():
                        if files:
                            self.memory.store_scan_results(category, files)
                            print(f"📎 Imported {len(files)} {category} files")
                            imported_items += 1
            
            # Import build settings
            if 'build' in config_data or 'Build' in config_data:
                build_data = config_data.get('build', config_data.get('Build', {}))
                if build_data:
                    current_config = self.memory.get_config()
                    current_config.update(build_data)
                    self.memory.store_config(current_config)
                    print(f"🔧 Imported build configuration")
                    imported_items += 1
            
            # Import icons
            if 'icons' in config_data or 'Icons' in config_data:
                icons = config_data.get('icons', config_data.get('Icons', []))
                if icons:
                    self.memory.store_scan_results('icons', icons)
                    print(f"🖼️ Imported {len(icons)} icon files")
                    imported_items += 1
            
            # Import splash screens
            if 'splash' in config_data or 'Splash' in config_data:
                splash = config_data.get('splash', config_data.get('Splash', []))
                if splash:
                    self.memory.store_scan_results('splash', splash)
                    print(f"🎨 Imported {len(splash)} splash files")
                    imported_items += 1
            
            print(f"✅ Import completed! Imported {imported_items} categories")
            return True
            
        except Exception as e:
            print(f"❌ Error importing JSON: {e}")
            return False

    def import_xml_config(self, xml_file):
        """Import configuration from XML file"""
        try:
            import xml.etree.ElementTree as ET
            
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            print(f"📋 Loaded XML configuration: {xml_file}")
            imported_items = 0
            
            # Import tutorials
            tutorials_elem = root.find('.//tutorials') or root.find('.//Tutorials')
            if tutorials_elem is not None:
                tutorial_files = [file_elem.text for file_elem in tutorials_elem.findall('file') if file_elem.text]
                if tutorial_files:
                    self.memory.store_scan_results('tutorials', tutorial_files)
                    print(f"📚 Imported {len(tutorial_files)} tutorial files")
                    imported_items += 1
            
            # Import help documents
            help_elem = root.find('.//help') or root.find('.//Help') or root.find('.//HELP')
            if help_elem is not None:
                help_files = [file_elem.text for file_elem in help_elem.findall('file') if file_elem.text]
                if help_files:
                    self.memory.store_scan_results('help', help_files)
                    print(f"📄 Imported {len(help_files)} help files")
                    imported_items += 1
            
            # Import additional categories
            additional_elem = root.find('.//additional') or root.find('.//Additional')
            if additional_elem is not None:
                for category_elem in additional_elem:
                    category_name = category_elem.tag
                    files = [file_elem.text for file_elem in category_elem.findall('file') if file_elem.text]
                    if files:
                        self.memory.store_scan_results(category_name, files)
                        print(f"📎 Imported {len(files)} {category_name} files")
                        imported_items += 1
            
            print(f"✅ XML import completed! Imported {imported_items} categories")
            return True
            
        except Exception as e:
            print(f"❌ Error importing XML: {e}")
            return False

    def import_spec_config(self, spec_file):
        """Import configuration from PyInstaller spec file"""
        try:
            with open(spec_file, 'r', encoding='utf-8') as f:
                spec_content = f.read()
            
            print(f"📋 Loaded spec configuration: {spec_file}")
            imported_items = 0
            
            # Extract main script from spec
            import re
            
            # Look for script files in Analysis
            script_match = re.search(r"Analysis\s*\(\s*\[\s*['\"]([^'\"]+)['\"]", spec_content)
            if script_match:
                main_script = script_match.group(1)
                current_config = self.memory.get_config()
                current_config['main_file'] = main_script
                self.memory.store_config(current_config)
                print(f"📄 Imported main script: {main_script}")
                imported_items += 1
            
            # Extract data files
            datas_matches = re.findall(r"datas\s*=\s*\[(.*?)\]", spec_content, re.DOTALL)
            for datas_match in datas_matches:
                # Extract file paths from datas tuples
                file_matches = re.findall(r"['\"]([^'\"]+)['\"]", datas_match)
                if file_matches:
                    data_files = [f for f in file_matches if os.path.exists(f)]
                    if data_files:
                        self.memory.store_scan_results('data', data_files)
                        print(f"📎 Imported {len(data_files)} data files")
                        imported_items += 1
            
            # Extract icon from spec
            icon_match = re.search(r"icon\s*=\s*['\"]([^'\"]+)['\"]", spec_content)
            if icon_match:
                icon_file = icon_match.group(1)
                if os.path.exists(icon_file):
                    self.memory.store_scan_results('icons', [icon_file])
                    print(f"🖼️ Imported icon: {icon_file}")
                    imported_items += 1
            
            print(f"✅ Spec import completed! Imported {imported_items} categories")
            return True
            
        except Exception as e:
            print(f"❌ Error importing spec: {e}")
            return False

    def export_json_config(self, json_file):
        """Export current configuration to JSON file"""
        try:
            # Gather current configuration
            config_data = {
                "build": self.memory.get_config(),
                "scan_results": {}
            }
            
            # Get all scan results
            scan_results = self.memory.get_scan_results()
            
            # Organize scan results into logical categories
            if scan_results.get('tutorials'):
                config_data["Tutorials"] = {
                    "files": scan_results['tutorials']
                }
            
            if scan_results.get('help'):
                config_data["HELP"] = {
                    "files": scan_results['help']
                }
            
            if scan_results.get('icons'):
                config_data["Icons"] = scan_results['icons']
            
            if scan_results.get('splash'):
                config_data["Splash"] = scan_results['splash']
            
            # Group other categories as additional
            additional_categories = {}
            for key, files in scan_results.items():
                if key not in ['tutorials', 'help', 'icons', 'splash'] and files:
                    additional_categories[key] = files
            
            if additional_categories:
                config_data["Additional"] = additional_categories
            
            # Add metadata
            config_data["_metadata"] = {
                "exported_by": "PDFUtility BuildSystem",
                "export_date": datetime.now().isoformat(),
                "version": "1.0"
            }
            
            # Write to file
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Configuration exported to: {json_file}")
            print(f"📊 Exported {len([k for k in config_data.keys() if not k.startswith('_')])} categories")
            return True
            
        except Exception as e:
            print(f"❌ Error exporting JSON: {e}")
            return False

    def export_xml_config(self, xml_file):
        """Export current configuration to XML file"""
        try:
            import xml.etree.ElementTree as ET
            from xml.dom import minidom
            
            # Create root element
            root = ET.Element("BuildConfiguration")
            
            # Add metadata
            metadata = ET.SubElement(root, "metadata")
            ET.SubElement(metadata, "exported_by").text = "PDFUtility BuildSystem"
            ET.SubElement(metadata, "export_date").text = datetime.now().isoformat()
            ET.SubElement(metadata, "version").text = "1.0"
            
            # Get scan results
            scan_results = self.memory.get_scan_results()
            
            # Add tutorials
            if scan_results.get('tutorials'):
                tutorials_elem = ET.SubElement(root, "Tutorials")
                for tutorial_file in scan_results['tutorials']:
                    ET.SubElement(tutorials_elem, "file").text = tutorial_file
            
            # Add help documents
            if scan_results.get('help'):
                help_elem = ET.SubElement(root, "HELP")
                for help_file in scan_results['help']:
                    ET.SubElement(help_elem, "file").text = help_file
            
            # Add icons
            if scan_results.get('icons'):
                icons_elem = ET.SubElement(root, "Icons")
                for icon_file in scan_results['icons']:
                    ET.SubElement(icons_elem, "file").text = icon_file
            
            # Add splash screens
            if scan_results.get('splash'):
                splash_elem = ET.SubElement(root, "Splash")
                for splash_file in scan_results['splash']:
                    ET.SubElement(splash_elem, "file").text = splash_file
            
            # Add additional categories
            additional_categories = {}
            for key, files in scan_results.items():
                if key not in ['tutorials', 'help', 'icons', 'splash'] and files:
                    additional_categories[key] = files
            
            if additional_categories:
                additional_elem = ET.SubElement(root, "Additional")
                for category, files in additional_categories.items():
                    category_elem = ET.SubElement(additional_elem, category)
                    for file_path in files:
                        ET.SubElement(category_elem, "file").text = file_path
            
            # Add build configuration
            build_config = self.memory.get_config()
            if build_config:
                build_elem = ET.SubElement(root, "Build")
                for key, value in build_config.items():
                    if value is not None:
                        ET.SubElement(build_elem, key).text = str(value)
            
            # Create pretty XML
            xml_str = ET.tostring(root, encoding='unicode')
            pretty_xml = minidom.parseString(xml_str).toprettyxml(indent='  ')
            
            # Write to file
            with open(xml_file, 'w', encoding='utf-8') as f:
                f.write(pretty_xml)
            
            print(f"✅ Configuration exported to XML: {xml_file}")
            return True
            
        except Exception as e:
            print(f"❌ Error exporting XML: {e}")
            return False

    def export_spec_config(self, spec_file):
        """Export current configuration to PyInstaller spec file"""
        try:
            config = self.memory.get_config()
            scan_results = self.memory.get_scan_results()
            
            # Generate spec file content
            spec_content = f"""# -*- mode: python ; coding: utf-8 -*-
# Generated by PDFUtility BuildSystem
# Export Date: {datetime.now().isoformat()}

block_cipher = None

# Data files from scan results
datas = ["""
            
            # Add data files from scan results
            data_files = []
            for category, files in scan_results.items():
                if category not in ['icons'] and files:  # Icons are handled separately
                    for file_path in files:
                        if os.path.exists(file_path):
                            data_files.append(f"    ('{file_path}', '.'),")
            
            if data_files:
                spec_content += "\n" + "\n".join(data_files) + "\n"
            
            spec_content += """]

# Hidden imports (add as needed)
hiddenimports = []

a = Analysis(
    ['""" + config.get('main_file', 'main.py') + """'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='""" + config.get('name', 'app') + """',
    debug=""" + str(config.get('debug', False)).lower() + """,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=""" + str(not config.get('windowed', False)).lower() + ""","""
            
            # Add icon if available
            icon_files = scan_results.get('icons', [])
            if icon_files and os.path.exists(icon_files[0]):
                spec_content += f"\n    icon='{icon_files[0]}',"
            
            spec_content += """
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='""" + config.get('name', 'app') + """',
)
"""
            
            # Write to file
            with open(spec_file, 'w', encoding='utf-8') as f:
                f.write(spec_content)
            
            print(f"✅ Configuration exported to spec: {spec_file}")
            return True
            
        except Exception as e:
            print(f"❌ Error exporting spec: {e}")
            return False

    def execute_package_build(self):
        """Execute packaging build using MakeAppx and SignTool"""
        try:
            print("📦 Package Build Process (MSI/MSIX Creation)")
            print("=" * 50)
            
            # Get build configuration from memory
            build_config = self.memory.get_config()
            
            # First, ensure we have a built executable
            print("🔍 Checking for existing executable...")
            
            # Check for existing build
            if not self.check_existing_executable():
                print("⚠️  No executable found. Building first...")
                if not self.execute_pyinstaller_build():
                    print("❌ Failed to build executable. Cannot proceed with packaging.")
                    return False
            
            # Get packaging configuration
            packaging_config = self.get_packaging_config(build_config)
            
            # Create packaging directory structure
            if not self.prepare_packaging_directory(packaging_config):
                print("❌ Failed to prepare packaging directory.")
                return False
            
            # Generate manifest and packaging files
            if not self.generate_packaging_files(packaging_config):
                print("❌ Failed to generate packaging files.")
                return False
            
            # Execute MakeAppx
            if not self.execute_makeappx(packaging_config):
                print("❌ MakeAppx execution failed.")
                return False
            
            # Execute SignTool (if certificate available)
            if not self.execute_signtool(packaging_config):
                print("⚠️  SignTool execution skipped or failed (certificate may not be available).")
                print("💡 For production releases, ensure you have a valid code signing certificate.")
            
            print("✅ Package build completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Package build failed: {e}")
            return False

    def check_existing_executable(self):
        """Check if a built executable exists"""
        # Look for executable in dist folder
        dist_path = os.path.join(os.getcwd(), "dist")
        if not os.path.exists(dist_path):
            return False
        
        # Look for .exe files
        for file in os.listdir(dist_path):
            if file.endswith('.exe'):
                print(f"✅ Found executable: {file}")
                return True
        
        return False

    def get_packaging_config(self, build_config):
        """Get packaging configuration"""
        app_name = build_config.get('name', 'PDF-Utility')
        version = build_config.get('version', '1.0.0.0')
        
        # Ensure version is in proper format (4 numbers)
        version_parts = version.replace('v', '').split('.')
        while len(version_parts) < 4:
            version_parts.append('0')
        formatted_version = '.'.join(version_parts[:4])
        
        config = {
            'app_name': app_name,
            'version': formatted_version,
            'publisher': 'PDF-Utility Developer',
            'publisher_display_name': 'PDF Utility',
            'package_name': f'{app_name.replace("-", "").replace(" ", "")}Package',
            'executable_name': f'{app_name}.exe',
            'description': 'Professional PDF manipulation and utility application',
            'display_name': app_name,
            'package_dir': os.path.join(os.getcwd(), 'package_build'),
            'assets_dir': os.path.join(os.getcwd(), 'package_build', 'Assets'),
            'output_file': f'{app_name}-{version}.msix'
        }
        
        return config

    def prepare_packaging_directory(self, config):
        """Prepare directory structure for packaging"""
        try:
            package_dir = config['package_dir']
            assets_dir = config['assets_dir']
            
            # Create directories
            os.makedirs(package_dir, exist_ok=True)
            os.makedirs(assets_dir, exist_ok=True)
            
            print(f"📁 Created packaging directory: {package_dir}")
            
            # Copy executable to package directory
            dist_path = os.path.join(os.getcwd(), "dist")
            for file in os.listdir(dist_path):
                if file.endswith('.exe'):
                    src = os.path.join(dist_path, file)
                    dst = os.path.join(package_dir, config['executable_name'])
                    shutil.copy2(src, dst)
                    print(f"📄 Copied executable: {file} → {config['executable_name']}")
                    break
            
            # Copy assets if available
            self.copy_packaging_assets(assets_dir)
            
            return True
            
        except Exception as e:
            print(f"❌ Error preparing packaging directory: {e}")
            return False

    def copy_packaging_assets(self, assets_dir):
        """Copy and convert assets for packaging using scan results and collected files"""
        try:
            # Get scan results from memory
            scan_results = self.memory.get_scan_results()
            
            # Check for collected files first (from --collect command)
            collected_icons = scan_results.get('collected_icons', [])
            collected_splashes = scan_results.get('collected_splashes', [])
            
            # Fallback to regular scan results if no collected files
            if not collected_icons:
                icon_files = scan_results.get('icons', [])
                # If no icon files in scan, try to find them dynamically
                if not icon_files:
                    print("🔍 No icons in memory, scanning for ICO files...")
                    icon_files = self.dynamic_scan_for_icons()
            else:
                icon_files = collected_icons
            
            if not collected_splashes:
                splash_files = scan_results.get('splash', [])
                # If no splash files, try dynamic scan
                if not splash_files:
                    print("🔍 No splashes in memory, scanning for splash files...")
                    splash_files = self.dynamic_scan_for_splashes()
            else:
                splash_files = collected_splashes
            
            print(f"🔍 Found {len(icon_files)} icon files and {len(splash_files)} splash files")
            
            # Process the files
            icon_copied = self.process_icon_files(icon_files, assets_dir)
            splash_copied = self.process_splash_files(splash_files, assets_dir)
            
            # Create default assets if none exist or conversion failed
            if not icon_copied:
                print("⚠️  No suitable icon found, creating default assets")
                self.create_default_package_assets(assets_dir)
            
            if not splash_copied:
                print("💡 No splash screen found, will use icon as fallback")
            
            return True
            
        except Exception as e:
            print(f"⚠️  Warning: Error copying assets: {e}")
            return False

    def dynamic_scan_for_icons(self):
        """Dynamically scan for icon files in current directory"""
        try:
            current_dir = os.getcwd()
            icon_files = []
            
            # Look for common icon file patterns
            patterns = ['*.ico', '*icon*.png', '*logo*.png']
            
            for pattern in patterns:
                for file_path in glob.glob(os.path.join(current_dir, pattern)):
                    if os.path.isfile(file_path):
                        icon_files.append(file_path)
                        print(f"   • Found: {os.path.basename(file_path)}")
            
            return icon_files
            
        except Exception as e:
            print(f"❌ Error in dynamic icon scan: {e}")
            return []

    def dynamic_scan_for_splashes(self):
        """Dynamically scan for splash screen files"""
        try:
            current_dir = os.getcwd()
            splash_files = []
            
            # Look for splash screen patterns
            patterns = ['*splash*', '*Splash*']
            
            for pattern in patterns:
                for file_path in glob.glob(os.path.join(current_dir, pattern)):
                    if os.path.isfile(file_path) and file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                        splash_files.append(file_path)
                        print(f"   • Found: {os.path.basename(file_path)}")
            
            return splash_files
            
        except Exception as e:
            print(f"❌ Error in dynamic splash scan: {e}")
            return []

    def process_icon_files(self, icon_files, assets_dir):
        """Process icon files and convert to PNG if needed"""
        try:
            if not icon_files:
                return False
            
            # Find the best icon file (prefer .ico, then .png)
            best_icon = None
            for icon_path in icon_files:
                if os.path.exists(icon_path):
                    if icon_path.lower().endswith('.ico'):
                        best_icon = icon_path
                        break
                    elif icon_path.lower().endswith('.png') and best_icon is None:
                        best_icon = icon_path
            
            if not best_icon:
                return False
            
            print(f"📎 Using icon: {best_icon}")
            
            if best_icon.lower().endswith('.ico'):
                # Convert ICO to PNG formats required by MSIX
                return self.convert_ico_to_png_logos(best_icon, assets_dir)
            else:
                # Copy PNG file as-is and create required sizes
                return self.process_png_logo(best_icon, assets_dir)
                
        except Exception as e:
            print(f"❌ Error processing icon files: {e}")
            return False

    def process_splash_files(self, splash_files, assets_dir):
        """Process splash screen files"""
        try:
            if not splash_files:
                return False
            
            # Find the best splash file
            best_splash = None
            for splash_path in splash_files:
                if os.path.exists(splash_path):
                    if splash_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                        best_splash = splash_path
                        break
            
            if best_splash:
                splash_dest = os.path.join(assets_dir, 'splash.png')
                shutil.copy2(best_splash, splash_dest)
                print(f"🎨 Copied splash screen: {os.path.basename(best_splash)}")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Error processing splash files: {e}")
            return False

    def convert_ico_to_png_logos(self, ico_path, assets_dir):
        """Convert ICO file to required PNG logo formats"""
        try:
            print(f"🔍 DEBUG: convert_ico_to_png_logos called")
            print(f"🔍 DEBUG: ico_path = {ico_path}")
            print(f"🔍 DEBUG: assets_dir = {assets_dir}")
            print(f"🔍 DEBUG: Current working directory: {os.getcwd()}")
            print(f"🔍 DEBUG: Python executable: {sys.executable}")
            
            # Try to find Python with PIL first
            python_with_pil = self.find_python_with_pil()
            
            if python_with_pil:
                # Use subprocess to run PIL conversion in the correct Python environment
                return self.convert_ico_via_subprocess(ico_path, assets_dir, python_with_pil)
            
            # Try PIL import with comprehensive debugging (fallback)
            try:
                print(f"🔍 DEBUG: Attempting PIL import in current interpreter...")
                print(f"🔍 DEBUG: sys.path first 3 entries: {sys.path[:3]}")
                
                from PIL import Image
                print(f"🔍 DEBUG: PIL imported successfully!")
                print(f"🔍 DEBUG: PIL module location: {Image.__file__}")
                
            except ImportError as e:
                print(f"❌ DEBUG: PIL ImportError caught: {e}")
                print(f"🔍 DEBUG: ImportError type: {type(e)}")
                print(f"🔍 DEBUG: ImportError args: {e.args}")
                
                # Try alternative import approaches
                try:
                    print(f"🔍 DEBUG: Trying 'import PIL' directly...")
                    import PIL
                    print(f"🔍 DEBUG: Direct PIL import worked: {PIL}")
                    from PIL import Image
                    print(f"🔍 DEBUG: Image import after direct PIL worked!")
                except Exception as e2:
                    print(f"❌ DEBUG: Direct PIL import also failed: {e2}")
                
                import traceback
                print(f"🔍 DEBUG: Full import traceback:")
                traceback.print_exc()
                
                print("💡 PIL not available: falling back to placeholders")
                return self.create_placeholder_png_logos(assets_dir)
            
            print("🔄 Converting ICO to PNG formats...")
            print(f"🔍 PIL version: {getattr(Image, '__version__', 'unknown')}")
            
            # Continue with direct PIL conversion...
            return self.convert_ico_directly(ico_path, assets_dir, Image)
                
        except ImportError as e:
            print(f"💡 PIL not available: {e}")
            print("💡 Creating placeholder PNG files instead")
            return self.create_placeholder_png_logos(assets_dir)
        except Exception as e:
            print(f"❌ Error converting ICO to PNG: {e}")
            print(f"🔍 Error type: {type(e).__name__}")
            print("💡 Falling back to placeholder PNG files")
            import traceback
            print(f"🔍 DEBUG: Exception traceback:")
            traceback.print_exc()
            return self.create_placeholder_png_logos(assets_dir)

    def convert_ico_via_subprocess(self, ico_path, assets_dir, python_cmd):
        """Convert ICO using subprocess with the correct Python"""
        try:
            print(f"🔄 Converting ICO via subprocess using: {python_cmd}")
            
            # Create a temporary Python script for the conversion (without Unicode emojis)
            conversion_script = f'''
import os
from PIL import Image

ico_path = r"{ico_path}"
assets_dir = r"{assets_dir}"

print("Converting ICO to PNG formats...")

with Image.open(ico_path) as img:
    print(f"Original image size: {{img.size}}, mode: {{img.mode}}")
    
    # Convert to RGBA if not already
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # Create required logo sizes
    logos_created = 0
    
    # Use compatible resampling method
    try:
        resample_method = Image.Resampling.LANCZOS
    except AttributeError:
        resample_method = Image.LANCZOS
    
    # 44x44 Logo (required)
    logo_44 = img.resize((44, 44), resample_method)
    logo_44_path = os.path.join(assets_dir, 'Square44x44Logo.png')
    logo_44.save(logo_44_path, 'PNG')
    logos_created += 1
    print(f"Created 44x44 logo: {{logo_44_path}}")
    
    # 150x150 Logo (required) 
    logo_150 = img.resize((150, 150), resample_method)
    logo_150_path = os.path.join(assets_dir, 'Square150x150Logo.png')
    logo_150.save(logo_150_path, 'PNG')
    logos_created += 1
    print(f"Created 150x150 logo: {{logo_150_path}}")
    
    # 310x150 Wide Logo (required)
    wide_logo = Image.new('RGBA', (310, 150), (0, 0, 0, 0))
    resized_icon = img.resize((150, 150), resample_method)
    paste_x = (310 - 150) // 2
    wide_logo.paste(resized_icon, (paste_x, 0), resized_icon)
    wide_logo_path = os.path.join(assets_dir, 'Wide310x150Logo.png')
    wide_logo.save(wide_logo_path, 'PNG')
    logos_created += 1
    print(f"Created 310x150 wide logo: {{wide_logo_path}}")
    
    print(f"Created {{logos_created}} PNG logo files from ICO")
    print("CONVERSION_SUCCESS")
'''
            
            # Handle py launcher with version flags vs direct executable
            if python_cmd.startswith('py '):
                # For py launcher, use a more reliable approach
                # Split the command and use shell=False for better output capture
                py_parts = python_cmd.split()
                if len(py_parts) == 2 and py_parts[1].startswith('-'):  # e.g., "py -3.13"
                    # Use py launcher with explicit version
                    cmd_parts = ['py', py_parts[1], '-c', conversion_script]
                    use_shell = False
                else:
                    cmd_parts = [python_cmd, '-c', conversion_script]
                    use_shell = False
            else:
                cmd_parts = [python_cmd, '-c', conversion_script]
                use_shell = False
            
            print(f"🔍 Running command: {' '.join(cmd_parts[:3])} <conversion_script>")
            
            # Run the conversion script with improved output capture
            result = subprocess.run(
                cmd_parts,
                capture_output=True,
                text=True,
                timeout=30,
                shell=use_shell,
                encoding='utf-8',
                errors='replace'  # Handle any encoding issues gracefully
            )
            
            print(f"🔍 Return code: {result.returncode}")
            if result.stdout:
                print(f"🔍 Stdout length: {len(result.stdout)} chars")
                # Show a preview of stdout for debugging
                stdout_preview = result.stdout.replace('\r\n', '\n').strip()
                if stdout_preview:
                    print(f"🔍 Stdout content: {stdout_preview[:500]}{'...' if len(stdout_preview) > 500 else ''}")
                else:
                    print(f"🔍 Stdout appears to be empty or whitespace-only")
            else:
                print(f"🔍 No stdout captured")
            if result.stderr:
                print(f"🔍 Stderr: {result.stderr}")
            
            # Check for success in multiple ways
            success_found = False
            if result.returncode == 0:
                # Check if success marker is in output
                if result.stdout and 'CONVERSION_SUCCESS' in result.stdout:
                    success_found = True
                    print("✅ Success marker found in stdout")
                
                # Always check if files were actually created as primary verification
                required_files = ['Square44x44Logo.png', 'Square150x150Logo.png', 'Wide310x150Logo.png']
                files_exist = all(os.path.exists(os.path.join(assets_dir, f)) for f in required_files)
                
                if files_exist:
                    if not success_found:
                        print("✅ PNG files were created successfully (verified by file existence)")
                    
                    # Show conversion output if available
                    if result.stdout and result.stdout.strip():
                        print("📋 Conversion output:")
                        output_lines = result.stdout.split('\n')
                        for line in output_lines:
                            line = line.strip()
                            if line and not line.startswith('🔍'):
                                print(f"   {line}")
                    
                    return True
                else:
                    print("❌ PNG files not found - conversion failed despite successful return code")
                    if result.stdout:
                        print("📋 Process output (for debugging):")
                        print(result.stdout)
                    return self.create_placeholder_png_logos(assets_dir)
            else:
                print(f"❌ Subprocess conversion failed with return code: {result.returncode}")
                if result.stdout:
                    print(f"Stdout: {result.stdout}")
                if result.stderr:
                    print(f"Stderr: {result.stderr}")
                return self.create_placeholder_png_logos(assets_dir)
                
        except Exception as e:
            print(f"❌ Subprocess conversion error: {e}")
            import traceback
            traceback.print_exc()
            return self.create_placeholder_png_logos(assets_dir)

    def convert_ico_directly(self, ico_path, assets_dir, Image):
        """Direct ICO conversion when PIL is available in current interpreter"""
        # Open the ICO file
        with Image.open(ico_path) as img:
            print(f"📐 Original image size: {img.size}, mode: {img.mode}")
            
            # ICO files can contain multiple sizes, get the best one
            # Convert to RGBA if not already
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Create required logo sizes
            logos_created = 0
            
            # Use compatible resampling method
            try:
                resample_method = Image.Resampling.LANCZOS
            except AttributeError:
                # Fallback for older PIL versions
                resample_method = Image.LANCZOS
            
            # 44x44 Logo (required)
            logo_44 = img.resize((44, 44), resample_method)
            logo_44_path = os.path.join(assets_dir, 'Square44x44Logo.png')
            logo_44.save(logo_44_path, 'PNG')
            logos_created += 1
            print(f"✅ Created 44x44 logo: {logo_44_path}")
            
            # 150x150 Logo (required) 
            logo_150 = img.resize((150, 150), resample_method)
            logo_150_path = os.path.join(assets_dir, 'Square150x150Logo.png')
            logo_150.save(logo_150_path, 'PNG')
            logos_created += 1
            print(f"✅ Created 150x150 logo: {logo_150_path}")
            
            # 310x150 Wide Logo (required)
            # Create a wide logo by centering the icon on a wider canvas
            wide_logo = Image.new('RGBA', (310, 150), (0, 0, 0, 0))  # Transparent background
            resized_icon = img.resize((150, 150), resample_method)
            # Center the icon in the wide canvas
            paste_x = (310 - 150) // 2
            wide_logo.paste(resized_icon, (paste_x, 0), resized_icon)
            wide_logo_path = os.path.join(assets_dir, 'Wide310x150Logo.png')
            wide_logo.save(wide_logo_path, 'PNG')
            logos_created += 1
            print(f"✅ Created 310x150 wide logo: {wide_logo_path}")
            
            print(f"✅ Created {logos_created} PNG logo files from ICO")
            return True

    def process_png_logo(self, png_path, assets_dir):
        """Process existing PNG logo and create required sizes"""
        try:
            from PIL import Image
            
            print(f"🔄 Processing PNG logo: {os.path.basename(png_path)}")
            
            with Image.open(png_path) as img:
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # Use compatible resampling method
                try:
                    resample_method = Image.Resampling.LANCZOS
                except AttributeError:
                    # Fallback for older PIL versions
                    resample_method = Image.LANCZOS
                
                # Create required sizes (same as ICO conversion)
                logo_44 = img.resize((44, 44), resample_method)
                logo_44.save(os.path.join(assets_dir, 'Square44x44Logo.png'), 'PNG')
                
                logo_150 = img.resize((150, 150), resample_method)
                logo_150.save(os.path.join(assets_dir, 'Square150x150Logo.png'), 'PNG')
                
                # Create wide logo
                wide_logo = Image.new('RGBA', (310, 150), (0, 0, 0, 0))
                resized_icon = img.resize((150, 150), resample_method)
                paste_x = (310 - 150) // 2
                wide_logo.paste(resized_icon, (paste_x, 0), resized_icon)
                wide_logo.save(os.path.join(assets_dir, 'Wide310x150Logo.png'), 'PNG')
                
                print("✅ Created PNG logo files from existing PNG")
                return True
                
        except ImportError as e:
            print(f"💡 PIL not available: {e}")
            return self.create_placeholder_png_logos(assets_dir)
        except Exception as e:
            print(f"❌ Error processing PNG logo: {e}")
            print(f"🔍 Error type: {type(e).__name__}")
            return self.create_placeholder_png_logos(assets_dir)

    def create_placeholder_png_logos(self, assets_dir):
        """Create simple placeholder PNG logos when PIL is not available"""
        try:
            # This creates minimal placeholder files - in a real scenario you'd want actual PNG files
            placeholder_files = [
                'Square44x44Logo.png',
                'Square150x150Logo.png', 
                'Wide310x150Logo.png'
            ]
            
            # Create minimal PNG headers (this is a basic approach)
            for filename in placeholder_files:
                placeholder_path = os.path.join(assets_dir, filename)
                # Create a minimal 1x1 transparent PNG (very basic)
                png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x01\x03\x00\x00\x00%\xdbV\xca\x00\x00\x00\x03PLTE\x00\x00\x00\xa7z=\xda\x00\x00\x00\x01tRNS\x00@\xe6\xd8f\x00\x00\x00\nIDAT\x08\x1dc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
                with open(placeholder_path, 'wb') as f:
                    f.write(png_data)
            
            print("📝 Created placeholder PNG files (install PIL for better icon conversion)")
            return True
            
        except Exception as e:
            print(f"❌ Error creating placeholder PNGs: {e}")
            return False

    def create_default_package_assets(self, assets_dir):
        """Create default packaging assets if none exist"""
        # Create a simple logo if none exists
        logo_path = os.path.join(assets_dir, 'Square44x44Logo.png')
        wide_logo_path = os.path.join(assets_dir, 'Wide310x150Logo.png')
        
        # Note: In a real implementation, you'd generate proper PNG files
        # For now, we'll just create placeholder files if the tools support it
        try:
            from PIL import Image
            
            # Create 44x44 logo
            img = Image.new('RGBA', (44, 44), color=(0, 120, 215, 255))  # Blue background
            img.save(logo_path)
            
            # Create wide logo
            img_wide = Image.new('RGBA', (310, 150), color=(0, 120, 215, 255))
            img_wide.save(wide_logo_path)
            
            print("🎨 Created default package assets")
            
        except ImportError:
            print("💡 PIL not available - skipping asset generation")
        except Exception as e:
            print(f"⚠️  Could not create default assets: {e}")

    def generate_packaging_files(self, config):
        """Generate manifest and other packaging files"""
        try:
            # Generate AppxManifest.xml
            manifest_content = self.generate_appx_manifest(config)
            manifest_path = os.path.join(config['package_dir'], 'AppxManifest.xml')
            
            with open(manifest_path, 'w', encoding='utf-8') as f:
                f.write(manifest_content)
            
            print("📋 Generated AppxManifest.xml")
            
            # Generate mapping file for MakeAppx
            mapping_content = self.generate_mapping_file(config)
            mapping_path = os.path.join(config['package_dir'], 'mapping.txt')
            
            with open(mapping_path, 'w', encoding='utf-8') as f:
                f.write(mapping_content)
            
            print("📋 Generated mapping.txt")
            
            return True
            
        except Exception as e:
            print(f"❌ Error generating packaging files: {e}")
            return False

    def generate_appx_manifest(self, config):
        """Generate AppxManifest.xml content using proper PNG assets"""
        # Check which assets are available
        assets_dir = config['assets_dir']
        
        # Use the standard Windows Store logo names (we create these in copy_packaging_assets)
        logo_44 = "Square44x44Logo.png"
        logo_150 = "Square150x150Logo.png" 
        wide_logo = "Wide310x150Logo.png"
        splash_image = "splash.png"
        
        # Verify the files exist (fallback to placeholders if needed)
        if not os.path.exists(os.path.join(assets_dir, logo_44)):
            logo_44 = "Square44x44Logo.png"  # Will be created by asset processing
        
        return f"""<?xml version="1.0" encoding="utf-8"?>
<Package
  xmlns="http://schemas.microsoft.com/appx/manifest/foundation/windows10"
  xmlns:uap="http://schemas.microsoft.com/appx/manifest/uap/windows10"
  xmlns:rescap="http://schemas.microsoft.com/appx/manifest/foundation/windows10/restrictedcapabilities">

  <Identity
    Name="{config['package_name']}"
    Publisher="CN={config['publisher']}"
    Version="{config['version']}" />

  <Properties>
    <DisplayName>{config['display_name']}</DisplayName>
    <PublisherDisplayName>{config['publisher_display_name']}</PublisherDisplayName>
    <Logo>Assets\\{logo_44}</Logo>
    <Description>{config['description']}</Description>
  </Properties>

  <Dependencies>
    <TargetDeviceFamily Name="Windows.Universal" MinVersion="10.0.17763.0" MaxVersionTested="10.0.22000.0" />
  </Dependencies>

  <Resources>
    <Resource Language="x-generate"/>
  </Resources>

  <Applications>
    <Application Id="App"
      Executable="{config['executable_name']}"
      EntryPoint="Windows.FullTrustApplication">
      <uap:VisualElements
        DisplayName="{config['display_name']}"
        Square150x150Logo="Assets\\{logo_150}"
        Square44x44Logo="Assets\\{logo_44}"
        Description="{config['description']}"
        BackgroundColor="transparent">
        <uap:DefaultTile Wide310x150Logo="Assets\\{wide_logo}" />
        <uap:SplashScreen Image="Assets\\{splash_image}" />
      </uap:VisualElements>
    </Application>
  </Applications>

  <Capabilities>
    <rescap:Capability Name="runFullTrust" />
  </Capabilities>

</Package>"""

    def generate_mapping_file(self, config):
        """Generate mapping file for MakeAppx"""
        package_dir = config['package_dir']
        lines = [
            '[Files]',
            f'"{config["executable_name"]}" "{config["executable_name"]}"',
            '"AppxManifest.xml" "AppxManifest.xml"'
        ]
        
        # Add assets
        assets_dir = config['assets_dir']
        if os.path.exists(assets_dir):
            for file in os.listdir(assets_dir):
                if os.path.isfile(os.path.join(assets_dir, file)):
                    lines.append(f'"Assets\\{file}" "Assets\\{file}"')
        
        return '\n'.join(lines)

    def execute_makeappx(self, config):
        """Execute MakeAppx to create MSIX package"""
        try:
            print("🔨 Running MakeAppx...")
            
            # Find MakeAppx executable
            makeappx_path = self.find_windows_sdk_tool('makeappx.exe')
            if not makeappx_path:
                print("❌ MakeAppx not found. Please ensure Windows SDK is installed.")
                print("💡 Install Windows SDK from: https://developer.microsoft.com/windows/downloads/windows-sdk/")
                return False
            
            # Clean up any existing output files to prevent file locking issues
            output_file_path = os.path.join(config['package_dir'], config['output_file'])
            if os.path.exists(output_file_path):
                try:
                    os.remove(output_file_path)
                    print(f"🗑️ Removed existing output file: {config['output_file']}")
                except Exception as cleanup_e:
                    print(f"⚠️ Could not remove existing file: {cleanup_e}")
                    print("💡 This might cause file locking issues")
            
            # Clean up temporary files (Windows creates ~XX files when locked)
            temp_pattern = os.path.join(config['package_dir'], f"~*{config['output_file']}")
            import glob
            for temp_file in glob.glob(temp_pattern):
                try:
                    os.remove(temp_file)
                    print(f"🗑️ Cleaned up temp file: {os.path.basename(temp_file)}")
                except Exception:
                    pass
            
            # MakeAppx command
            makeappx_cmd = [
                makeappx_path,
                'pack',
                '/f', os.path.join(config['package_dir'], 'mapping.txt'),
                '/p', config['output_file'],
                '/o'  # Overwrite existing
            ]
            
            print(f"🔍 Command: {' '.join(makeappx_cmd)}")
            
            # Execute command
            result = subprocess.run(makeappx_cmd, 
                                  cwd=config['package_dir'],
                                  capture_output=True, 
                                  text=True)
            
            if result.returncode == 0:
                print("✅ MakeAppx completed successfully")
                print(f"📦 Package created: {config['output_file']}")
                if result.stdout.strip():
                    print(f"📋 MakeAppx output: {result.stdout.strip()}")
                return True
            else:
                print(f"❌ MakeAppx failed with return code: {result.returncode}")
                if result.stderr.strip():
                    print(f"❌ Error details: {result.stderr.strip()}")
                if result.stdout.strip():
                    print(f"📋 Output: {result.stdout.strip()}")
                    
                # Additional debugging info
                print(f"🔍 Working directory: {config['package_dir']}")
                print(f"🔍 Output file path: {config['output_file']}")
                print(f"🔍 Mapping file exists: {os.path.exists(os.path.join(config['package_dir'], 'mapping.txt'))}")
                
                # Check if the mapping file is readable
                mapping_file = os.path.join(config['package_dir'], 'mapping.txt')
                if os.path.exists(mapping_file):
                    try:
                        with open(mapping_file, 'r') as f:
                            mapping_content = f.read().strip()
                        print(f"📋 Mapping file content (first 200 chars): {mapping_content[:200]}...")
                    except Exception as map_e:
                        print(f"❌ Could not read mapping file: {map_e}")
                
                return False
                
        except FileNotFoundError:
            print("❌ MakeAppx not found. Please ensure Windows SDK is installed.")
            print("💡 Install Windows SDK from: https://developer.microsoft.com/windows/downloads/windows-sdk/")
            return False
        except Exception as e:
            print(f"❌ Error running MakeAppx: {e}")
            return False

    def execute_signtool(self, config):
        """Execute SignTool to sign the package"""
        try:
            print("🔐 Running SignTool...")
            
            # Find SignTool executable
            signtool_path = self.find_windows_sdk_tool('signtool.exe')
            if not signtool_path:
                print("❌ SignTool not found. Please ensure Windows SDK is installed.")
                print("💡 Install Windows SDK from: https://developer.microsoft.com/windows/downloads/windows-sdk/")
                return False
            
            print("✅ signtool.exe found in Windows SDK")
            
            # Check if certificate is available
            cert_info = self.get_certificate_info()
            if not cert_info:
                print("⚠️  No certificate configured - skipping signing")
                print("💡 For production, configure a code signing certificate")
                print("💡 To enable signing:")
                print("   1. Place certificate.pfx in project root, OR")
                print("   2. Set CERT_PATH and CERT_PASSWORD environment variables")
                return True  # Not a failure, just skipped
            
            cert_path, cert_password = cert_info
            print(f"🔍 Using certificate: {cert_path}")
            
            # Convert relative path to absolute path
            if not os.path.isabs(cert_path):
                cert_path = os.path.abspath(cert_path)
            
            if not os.path.exists(cert_path):
                print(f"❌ Certificate file not found: {cert_path}")
                return True  # Not a critical failure
            
            # Build SignTool command
            output_path = os.path.join(config['package_dir'], config['output_file'])
            
            if cert_password:
                # Use certificate with password
                signtool_cmd = [
                    signtool_path,
                    'sign',
                    '/f', cert_path,
                    '/p', cert_password,
                    '/fd', 'SHA256',
                    '/tr', 'http://timestamp.digicert.com',
                    '/td', 'SHA256',
                    '/v',  # Verbose output
                    output_path
                ]
            else:
                # Use certificate without password (or from certificate store)
                signtool_cmd = [
                    signtool_path,
                    'sign',
                    '/f', cert_path,
                    '/fd', 'SHA256',
                    '/tr', 'http://timestamp.digicert.com',
                    '/td', 'SHA256',
                    '/v',  # Verbose output
                    output_path
                ]
            
            print(f"🔍 Command: signtool.exe sign /f {cert_path} [***] /fd SHA256 /tr <timestamp> /td SHA256 /v {os.path.basename(output_path)}")
            
            # Execute command
            result = subprocess.run(signtool_cmd,
                                  cwd=config['package_dir'],
                                  capture_output=True,
                                  text=True,
                                  timeout=60)
            
            if result.returncode == 0:
                print("✅ Package signed successfully")
                print("📋 SignTool output:")
                if result.stdout:
                    # Show relevant output lines
                    for line in result.stdout.split('\n'):
                        line = line.strip()
                        if line and any(keyword in line.lower() for keyword in ['successfully', 'completed', 'signed']):
                            print(f"   {line}")
                return True
            else:
                print(f"❌ Signing failed with return code: {result.returncode}")
                if result.stdout:
                    print(f"📋 SignTool stdout: {result.stdout}")
                if result.stderr:
                    print(f"📋 SignTool stderr: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("⚠️  SignTool timed out. This may indicate network issues with timestamping.")
            return False
        except FileNotFoundError:
            print("⚠️  SignTool not found. Signing skipped.")
            print("💡 Install Windows SDK for SignTool support")
            return True  # Not a critical failure
        except Exception as e:
            print(f"⚠️  Error running SignTool: {e}")
            return True  # Not a critical failure

    def get_certificate_info(self):
        """Get certificate path and password"""
        # Check environment variables first
        env_cert_path = os.environ.get('CERT_PATH')
        env_cert_password = os.environ.get('CERT_PASSWORD')
        
        if env_cert_path and os.path.exists(env_cert_path):
            return (env_cert_path, env_cert_password)
        
        # Check common certificate locations
        cert_locations = [
            ('certificate.pfx', 'PDFUtility2025'),  # Default self-signed cert with password
            ('signing_cert.pfx', None),
            (os.path.expanduser('~/certificate.pfx'), None),
            (os.path.expanduser('~/Documents/certificate.pfx'), None),
            ('cert.pfx', None),
            ('code_signing.pfx', None)
        ]
        
        for cert_path, default_password in cert_locations:
            if os.path.exists(cert_path):
                # If there's a default password, use it, otherwise check for password file
                password = default_password
                if not password:
                    password_file = cert_path.replace('.pfx', '.password')
                    if os.path.exists(password_file):
                        try:
                            with open(password_file, 'r', encoding='utf-8') as f:
                                password = f.read().strip()
                        except Exception:
                            pass
                
                return (cert_path, password)
        
        return None

    def get_certificate_path(self):
        """Legacy method for backwards compatibility"""
        cert_info = self.get_certificate_info()
        if cert_info:
            return cert_info[0]
        return None

    def generate_build_filename(self, config):
        """Generate build filename based on configuration"""
        name = config.get('name', 'BuildToolApp')
        include_date = config.get('include_date', True)
        version = config.get('version', '')
        
        # Check if version appending is disabled
        no_version_local = config.get('no_version_append', False)
        no_version_global = config.get('no_version_append_global', False)
        no_version = no_version_local or no_version_global
        
        # Clean name
        name = re.sub(r'[^\w\-_.]', '_', name)
        
        # Add version if specified and not disabled
        if version and not no_version:
            name = f"{name}_v{version}"
        
        # Add date if requested
        if include_date:
            date_str = datetime.now().strftime("%Y%m%d")
            name = f"{name}_{date_str}"
        
        return name

    def auto_detect_main_file(self):
        """Auto-detect the main Python file"""
        print("🔍 Analyzing Python files to detect main entry point...")
        
        # Look for Python files in current directory
        python_files = []
        for root, dirs, files in os.walk('.'):
            # Skip common directories that shouldn't contain main files
            dirs[:] = [d for d in dirs if d not in {
                '__pycache__', '.git', '.svn', 'venv', 'env', '.venv',
                'node_modules', 'build', 'dist', '.pytest_cache'
            }]
            
            for file in files:
                if file.endswith('.py') and not file.startswith('.'):
                    file_path = os.path.join(root, file)
                    # Prioritize files in root directory
                    if root == '.':
                        python_files.insert(0, file_path)
                    else:
                        python_files.append(file_path)
        
        if not python_files:
            return None
        
        # Score files based on main-like characteristics
        candidates = []
        for file_path in python_files[:20]:  # Limit analysis
            score = 0
            filename = os.path.basename(file_path).lower()
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Filename scoring
                if filename in ['main.py', '__main__.py', 'app.py', 'run.py']:
                    score += 50
                elif 'main' in filename:
                    score += 25
                
                # Content scoring
                if 'if __name__ == "__main__"' in content:
                    score += 40
                if 'def main(' in content:
                    score += 20
                # Note: Removed GUI framework detection to avoid GUI dependencies
                if 'argparse' in content or 'sys.argv' in content:
                    score += 10
                
                # Root directory bonus
                if os.path.dirname(file_path) == '.':
                    score += 20
                
                candidates.append((file_path, score))
                
            except Exception:
                continue
        
        if candidates:
            candidates.sort(key=lambda x: x[1], reverse=True)
            best_file, best_score = candidates[0]
            if best_score >= 20:
                return best_file
        
        return None

    def auto_detect_icon(self):
        """Auto-detect icon file"""
        icon_patterns = ['*.ico', '*.png', '*.jpg', '*.jpeg']
        icon_dirs = ['.', 'assets', 'icons', 'resources', 'static']
        
        for directory in icon_dirs:
            if not os.path.exists(directory):
                continue
                
            for pattern in icon_patterns:
                icons = glob.glob(os.path.join(directory, pattern))
                if icons:
                    # Prefer .ico files
                    ico_files = [f for f in icons if f.endswith('.ico')]
                    if ico_files:
                        return ico_files[0]
                    return icons[0]
        
        return None

    def auto_generate_name(self, main_file):
        """Auto-generate application name from main file"""
        base_name = os.path.splitext(os.path.basename(main_file))[0]
        
        # Clean and capitalize
        name = re.sub(r'[^\w\s]', ' ', base_name)
        name = ' '.join(word.capitalize() for word in name.split())
        name = name.replace(' ', '')
        
        if name.lower() == 'main':
            # Use directory name if main file is generic
            dir_name = os.path.basename(os.getcwd())
            name = ''.join(word.capitalize() for word in re.findall(r'\w+', dir_name))
        
        return name or "Application"

    def detect_gui_app(self, main_file):
        """Detect if the application is a GUI app (for windowed mode)"""
        try:
            with open(main_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read().lower()
            
            # Note: We check for GUI frameworks but don't import them
            gui_keywords = [
                'tkinter', 'pyqt', 'pyside', 'wx', 'kivy', 'flet',
                'streamlit', 'dash', 'flask', 'django', 'fastapi'
            ]
            
            return any(keyword in content for keyword in gui_keywords)
            
        except Exception:
            return False

    def show_build_summary(self, config):
        """Show build configuration summary"""
        print("\n📊 Build Summary:")
        print("-" * 20)
        print(f"Name: {self.generate_build_filename(config)}")
        print(f"Main File: {config.get('main_file', 'Not specified')}")
        print(f"Type: {'Single File' if config.get('onefile') else 'Directory'}")
        print(f"Interface: {'Windowed' if config.get('windowed') else 'Console'}")
        print(f"Icon: {config.get('icon', 'None')}")
        print(f"Clean Build: {config.get('clean', True)}")
        
        # Show included data files
        scan_results = self.memory.get_scan_results()
        data_files = []
        for scan_type, files in scan_results.items():
            if scan_type in ['config', 'data', 'templates', 'docs']:
                data_files.extend(files)
        
        if data_files:
            print(f"Data Files: {len(data_files)} files will be included")

    def execute_build_command(self, command):
        """Execute the PyInstaller build command"""
        try:
            import platform
            import shutil
            
            safe_print(f"\n🔨 Starting build process...")
            safe_print(f"🖥️  Platform: {platform.system()}")
            
            # Verify PyInstaller is available before trying to run
            pyinstaller_cmd = command[0] if command else "pyinstaller"
            if not shutil.which(pyinstaller_cmd):
                # Try alternative ways to find PyInstaller
                alternatives = ["pyinstaller", "python -m PyInstaller", "python3 -m PyInstaller"]
                found = False
                for alt in alternatives:
                    if ' ' in alt:
                        # For module-style calls, test differently
                        test_cmd = alt.split() + ["--version"]
                        try:
                            test_result = subprocess.run(test_cmd, capture_output=True, text=True, timeout=10)
                            if test_result.returncode == 0:
                                safe_print(f"✅ Found PyInstaller via: {alt}")
                                # Replace the first element with the working command
                                if alt.startswith("python"):
                                    command = alt.split() + command[1:]
                                found = True
                                break
                        except:
                            continue
                    else:
                        if shutil.which(alt):
                            safe_print(f"✅ Found PyInstaller at: {shutil.which(alt)}")
                            command[0] = alt
                            found = True
                            break
                
                if not found:
                    safe_print("❌ PyInstaller not found in PATH!")
                    safe_print("💡 Tried alternatives:")
                    for alt in alternatives:
                        safe_print(f"   • {alt}")
                    return False
            else:
                safe_print(f"✅ PyInstaller found at: {shutil.which(pyinstaller_cmd)}")
            
            safe_print(f"📋 Full Command: {' '.join(command)}")
            
            # Show a shortened version for readability
            if len(command) > 10:
                safe_print(f"💡 Shortened: {' '.join(command[:3])} ... [+{len(command)-4} args] ... {command[-1]}")
            
            # Execute the command
            result = subprocess.run(command, capture_output=False, text=True, shell=False)
            
            if result.returncode == 0:
                safe_print("\n" + "=" * 60)
                safe_print("  🎉 BUILD SUCCESSFUL! 🎉")
                safe_print("=" * 60)
                safe_print("✅ Executable created successfully!")
                safe_print("📁 Check the 'dist' folder for your executable.")
                safe_print(f"🚀 Your application is ready to distribute!")
                return True
            else:
                safe_print("\n" + "=" * 60)
                safe_print("  ❌ BUILD FAILED!")
                safe_print("=" * 60)
                safe_print(f"Return code: {result.returncode}")
                safe_print("Check the output above for error details.")
                safe_print("💡 Common issues:")
                safe_print("   • Missing dependencies (install with pip)")
                safe_print("   • Invalid file paths")
                safe_print("   • PyInstaller not installed (pip install pyinstaller)")
                safe_print("   • Wrong path separator in --add-data arguments")
                safe_print("   • Permission issues with output directory")
                return False
                
        except FileNotFoundError as e:
            safe_print("\n❌ Error: PyInstaller not found!")
            safe_print("📦 Install with: pip install pyinstaller")
            safe_print(f"🔍 Error details: {e}")
            return False
        except Exception as e:
            safe_print(f"\n❌ Build execution error: {e}")
            safe_print(f"🔍 Error type: {type(e).__name__}")
            return False

# ============================================================================
# CLI COMMAND DETECTION AND ROUTING
# ============================================================================

# Ultra-minimal fast path detection
def is_fast_command():
    """Check if this is a fast command that doesn't need heavy imports"""
    if len(sys.argv) <= 1:
        return False
    
    fast_commands = {
        '--help', '-h', '--version', '--changelog', 
        '--repo-status', '--update', '--download-cli', '--gui'
    }
    
    return any(arg in fast_commands for arg in sys.argv[1:])

def is_core_command():
    """Check if this command needs core functionality but should be handled by CLI"""
    if len(sys.argv) <= 1:
        return False
        
    # These commands use core functionality but are handled by CLI
    core_commands = {
        '--scan', '--show-memory', '--show-context', '--clear-memory', '--show-optimal',
        '--console', '--install', '--new', '--name', '--date',
        '--downgrade', '--preview-name', '--virtual', '--activate',
        '--scan-dir', '--scan-here', '--type', '--contains', '--install-needed',
        '--location', '--scan-project', '--target', '--from', '--set-root', '--show-root',
        '--append', '--export', '--export-config', '--start',
        '--remove-type', '--delete', '--delete-type', '--create',
        '--show-console', '--auto', '--backup', '--remove', '--add',
        '--detailed', '--main', '--set-version', '--add-to-path',
        '--windowed', '--no-console', '--clean',
        '--replace', '--recreate', '--repair', '--distant-scan',
        '--version', '--latest', '--gui'
    }
    
    return any(arg in core_commands or arg.startswith('--scan') for arg in sys.argv[1:])

def should_delegate_to_core():
    """Check if we should delegate completely to core (only for direct core operations)"""
    if len(sys.argv) <= 1:
        return False
        
    # Only delegate these specific operations to core's main()
    delegate_commands = {
        '--download-core', '--core-help'
    }
    
    return any(arg in delegate_commands for arg in sys.argv[1:])

def has_multiple_commands():
    """Check if multiple commands are present that should be processed together"""
    if len(sys.argv) <= 1:
        return False
    
    # Commands that can be processed together
    processable_commands = {
        '--name', '--date', '--scan', '--append', '--override', '--contains', '--scan-dir',
        '--type', '--target', '--from', '--set-root', '--show-root', '--export', '--start',
        '--show-console', '--virtual', '--activate', '--install-needed',
        '--remove', '--delete', '--add', '--detailed', '--show-memory', '--show-context',
        '--main', '--auto', '--set-version', '--add-to-path', '--replace', '--recreate', '--repair', '--distant-scan',
        '--version', '--latest', '--windowed', '--no-console', '--clean'
    }
    
    # Count how many processable commands we have
    command_count = sum(1 for arg in sys.argv[1:] if arg in processable_commands)
    return command_count > 1

def process_command_queue():
    """Process multiple commands in a queue system"""
    safe_print("🔄 Processing multiple commands...")
    
    try:
        # Parse all commands and their arguments
        command_queue = parse_command_queue()
        
        if not command_queue:
            safe_print("❌ No valid commands found in queue")
            return False
        
        safe_print(f"📋 Found {len(command_queue)} commands to process:")
        for cmd in command_queue:
            safe_print(f"   • {cmd['type']}: {cmd.get('value', 'N/A')}")
        
        # Process each command in the queue
        results = []
        for command in command_queue:
            try:
                result = execute_queued_command(command)
                results.append(result)
                if result:
                    print(f"✅ {command['type']} completed successfully")
                else:
                    print(f"❌ {command['type']} failed")
            except Exception as e:
                print(f"❌ Error processing {command['type']}: {e}")
                results.append(False)
        
        # Show summary
        successful = sum(1 for r in results if r)
        total = len(results)
        print(f"\n📊 Command Queue Summary: {successful}/{total} commands successful")
        
        # If we have build configuration commands, show final config
        config_commands = [cmd for cmd in command_queue if cmd['type'] in ['name', 'date', 'set-version', 'main']]
        if config_commands:
            show_final_build_config()
        
        return all(results)
        
    except Exception as e:
        print(f"❌ Error processing command queue: {e}")
        return False

def parse_command_queue():
    """Parse command line arguments into a queue of commands"""
    queue = []
    args = sys.argv[1:]
    i = 0
    
    while i < len(args):
        arg = args[i]
        
        if arg == '--name' and i + 1 < len(args):
            queue.append({
                'type': 'name',
                'value': args[i + 1]
            })
            i += 2
            
        elif arg == '--date' and i + 1 < len(args):
            queue.append({
                'type': 'date',
                'value': args[i + 1].lower()
            })
            i += 2
            
        elif arg == '--scan' and i + 1 < len(args):
            scan_cmd = {
                'type': 'scan',
                'scan_type': args[i + 1],
                'append': False,
                'override': False,
                'contains': None,
                'scan_dir': None
            }
            queue.append(scan_cmd)
            i += 2
            
        elif arg == '--distant-scan' and i + 1 < len(args):
            distant_scan_cmd = {
                'type': 'distant-scan',
                'scan_directory': args[i + 1],
                'scan_type': 'python',  # Default type, can be overridden by --type
                'append': False,
                'override': False,
                'contains': None
            }
            queue.append(distant_scan_cmd)
            i += 2
            
        elif arg == '--virtual' and i + 1 < len(args):
            virtual_cmd = {
                'type': 'virtual',
                'value': args[i + 1],
                'replace': False,
                'recreate': False,
                'repair': False
            }
            queue.append(virtual_cmd)
            i += 2
            
        elif arg == '--downgrade' and i + 1 < len(args):
            queue.append({
                'type': 'downgrade',
                'version': args[i + 1]
            })
            i += 2
            
        elif arg == '--type' and i + 1 < len(args):
            # Find the most recent command that can use type filter
            for cmd in reversed(queue):
                if cmd['type'] == 'scan':
                    cmd['file_type'] = args[i + 1]
                    break
                elif cmd['type'] == 'distant-scan':
                    cmd['scan_type'] = args[i + 1]
                    break
                elif cmd['type'] == 'remove':
                    cmd['remove_type'] = args[i + 1]
                    break
                elif cmd['type'] == 'delete':
                    cmd['delete_type'] = args[i + 1]
                    break
            i += 2
            
        elif arg == '--target' and i + 1 < len(args):
            # Check if we have a recent remove or delete command, otherwise create target command
            recent_cmd = None
            for cmd in reversed(queue):
                if cmd['type'] in ['remove', 'delete']:
                    recent_cmd = cmd
                    break
            
            if recent_cmd:
                recent_cmd['target'] = args[i + 1]
            else:
                queue.append({
                    'type': 'target',
                    'value': args[i + 1]
                })
            i += 2
            
        elif arg == '--from' and i + 1 < len(args):
            # Find the most recent remove command and specify which category to remove from
            for cmd in reversed(queue):
                if cmd['type'] == 'remove':
                    cmd['from_category'] = args[i + 1]
                    break
            i += 2
            
        elif arg == '--show-console' and i + 1 < len(args):
            queue.append({
                'type': 'show-console',
                'value': args[i + 1].lower()
            })
            i += 2
            
        elif arg == '--append':
            # Find the most recent scan or distant-scan command and mark it for append
            for cmd in reversed(queue):
                if cmd['type'] in ['scan', 'distant-scan']:
                    cmd['append'] = True
                    break
            i += 1
            
        elif arg == '--override':
            # Find the most recent scan or distant-scan command and mark it for override
            for cmd in reversed(queue):
                if cmd['type'] in ['scan', 'distant-scan']:
                    cmd['override'] = True
                    break
            i += 1
            
        elif arg == '--install-needed':
            # Check if next arg is a file path or another command
            project_file = None
            if i + 1 < len(args) and not args[i + 1].startswith('--'):
                project_file = args[i + 1]
                i += 2
            else:
                i += 1
            
            queue.append({
                'type': 'install-needed',
                'project_file': project_file
            })
            
        elif arg == '--contains' and i + 1 < len(args):
            # Find the most recent scan command and add contains filter
            for cmd in reversed(queue):
                if cmd['type'] == 'scan':
                    cmd['contains'] = args[i + 1]
                    break
            i += 2
            
        elif arg == '--scan-dir' and i + 1 < len(args):
            # Find the most recent scan command and add scan directory
            for cmd in reversed(queue):
                if cmd['type'] == 'scan':
                    cmd['scan_dir'] = args[i + 1]
                    break
            i += 2
            
        elif arg == '--scan-here':
            # Find the most recent scan command and set to script location
            for cmd in reversed(queue):
                if cmd['type'] == 'scan':
                    cmd['scan_dir'] = SCRIPT_CONTEXT['script_location']
                    break
            i += 1
            
        elif arg == '--remove':
            # Remove command for memory management
            queue.append({
                'type': 'remove',
                'target': None,
                'remove_type': None,
                'from_category': None
            })
            i += 1
            
        elif arg == '--delete':
            # Delete command for file operations
            queue.append({
                'type': 'delete',
                'target': None,
                'delete_type': None
            })
            i += 1
            
        elif arg == '--add':
            # Add command for file addition - collect all files after --add
            files = []
            i += 1
            
            # Collect all files until we hit another -- command or end of args
            while i < len(args) and not args[i].startswith('--'):
                files.append(args[i])
                i += 1
            
            if files:
                queue.append({
                    'type': 'add',
                    'files': files
                })
            else:
                print("❌ --add requires at least one file argument")
            
        elif arg == '--detailed':
            # Detailed flag - will be processed by --show-memory if present
            i += 1
            
        elif arg == '--show-memory':
            # Show memory command
            queue.append({
                'type': 'show-memory',
                'detailed': '--detailed' in args
            })
            i += 1
            
        elif arg == '--show-context':
            # Show script/working directory context
            queue.append({
                'type': 'show-context'
            })
            i += 1
            
        elif arg == '--main' and i + 1 < len(args):
            # Main file specification
            queue.append({
                'type': 'main',
                'file_path': args[i + 1],
                'auto_analyze': '--auto' in args
            })
            i += 2
            
        elif arg == '--auto':
            # Auto mode flag - can be combined with other commands
            # Find most recent command that can use auto mode
            for cmd in reversed(queue):
                if cmd['type'] == 'main':
                    cmd['auto_analyze'] = True
                    break
                elif cmd['type'] == 'start':
                    cmd['auto_detect'] = True
                    break
            else:
                # Create standalone auto command if no main command exists
                queue.append({
                    'type': 'auto',
                    'analyze_main': True
                })
            i += 1
            
        elif arg == '--set-version' and i + 1 < len(args):
            # Set version command
            queue.append({
                'type': 'set-version',
                'version': args[i + 1]
            })
            i += 2
            
        elif arg == '--add-to-path':
            # Add CLI to system PATH
            queue.append({
                'type': 'add-to-path'
            })
            i += 1
            
        elif arg == '--start' and i + 1 < len(args):
            # Start build process
            queue.append({
                'type': 'start',
                'process': args[i + 1],
                'no_version': False,  # Will be set by --no-version modifier
                'auto_detect': False  # Will be set by --auto modifier
            })
            i += 2
            
        elif arg == '--no-version':
            # No version modifier - find the most recent start command
            for cmd in reversed(queue):
                if cmd['type'] == 'start':
                    cmd['no_version'] = True
                    break
            i += 1
            
        elif arg == '--no-version-append' and i + 1 < len(args):
            # Global setting for version appending
            queue.append({
                'type': 'no-version-append',
                'value': args[i + 1].lower() in ['true', 'yes', '1', 'on']
            })
            i += 2
            
        elif arg == '--windowed':
            # Set windowed mode (no console)
            queue.append({
                'type': 'windowed',
                'value': True
            })
            i += 1
            
        elif arg == '--no-console':
            # Set no-console mode (windowed) - accept true/false parameter
            windowed_value = True  # Default to true if no parameter
            if i + 1 < len(args) and not args[i + 1].startswith('--'):
                windowed_value = args[i + 1].lower() in ['true', 'yes', '1', 'on']
                i += 2
            else:
                i += 1
            queue.append({
                'type': 'windowed',
                'value': windowed_value
            })
            
        elif arg == '--clean':
            # Clean previous builds
            queue.append({
                'type': 'clean'
            })
            i += 1
            
        elif arg == '--replace':
            # Replace modifier - find the most recent virtual command
            for cmd in reversed(queue):
                if cmd['type'] == 'virtual':
                    cmd['replace'] = True
                    break
            i += 1
            
        elif arg == '--recreate':
            # Recreate modifier - find the most recent virtual command
            for cmd in reversed(queue):
                if cmd['type'] == 'virtual':
                    cmd['recreate'] = True
                    break
            i += 1
            
        elif arg == '--repair':
            # Repair modifier - find the most recent virtual command
            for cmd in reversed(queue):
                if cmd['type'] == 'virtual':
                    cmd['repair'] = True
                    break
            i += 1
            
        elif arg == '--version' and i + 1 < len(args):
            # Version modifier - find the most recent virtual command
            for cmd in reversed(queue):
                if cmd['type'] == 'virtual':
                    cmd['python_version'] = args[i + 1]
                    break
            i += 2
            
        elif arg == '--latest':
            # Latest modifier - find the most recent virtual command
            for cmd in reversed(queue):
                if cmd['type'] == 'virtual':
                    cmd['use_latest'] = True
                    break
            i += 1
            
        elif arg == '--activate':
            # Check if this should be treated as a modifier for virtual command
            virtual_cmd_found = False
            for cmd in reversed(queue):
                if cmd['type'] == 'virtual':
                    cmd['activate_after'] = True
                    virtual_cmd_found = True
                    break
            
            # If no virtual command found, treat as standalone activate command
            if not virtual_cmd_found:
                # Check if next arg is an environment name or another command
                env_name = None
                if i + 1 < len(args) and not args[i + 1].startswith('--'):
                    env_name = args[i + 1]
                    i += 2
                else:
                    i += 1
                
                queue.append({
                    'type': 'activate',
                    'env_name': env_name
                })
            else:
                i += 1
            
        else:
            # Skip unknown arguments for now
            i += 1
    
    return queue

def execute_queued_command(command):
    """Execute a single command from the queue"""
    try:
        if command['type'] == 'name':
            return execute_name_command(command['value'])
            
        elif command['type'] == 'date':
            return execute_date_command(command['value'])
            
        elif command['type'] == 'scan':
            return execute_scan_command_queued(command)
            
        elif command['type'] == 'distant-scan':
            return execute_distant_scan_command(command)
            
        elif command['type'] == 'virtual':
            result = execute_virtual_command(
                command['value'], 
                replace=command.get('replace', False),
                recreate=command.get('recreate', False),
                repair=command.get('repair', False),
                python_version=command.get('python_version'),
                use_latest=command.get('use_latest', False)
            )
            
            # If activate_after flag is set, activate the environment
            if result and command.get('activate_after', False):
                print("\n🔄 Activating virtual environment as requested...")
                return execute_activate_command_enhanced(command['value'])
            
            return result
            
        elif command['type'] == 'activate':
            return execute_activate_command_enhanced(command.get('env_name'))
            
        elif command['type'] == 'downgrade':
            return execute_downgrade_command(command['version'])
            
        elif command['type'] == 'target':
            return execute_target_command(command['value'])
            
        elif command['type'] == 'show-console':
            return execute_show_console_command(command['value'])
            
        elif command['type'] == 'install-needed':
            return execute_install_needed_command(command.get('project_file'))
            
        elif command['type'] == 'remove':
            return execute_remove_command(command.get('target'), command.get('remove_type'), command.get('from_category'))
            
        elif command['type'] == 'delete':
            return execute_delete_command(command.get('target'), command.get('delete_type'))
            
        elif command['type'] == 'add':
            return execute_add_command(command.get('files', []))
            
        elif command['type'] == 'show-memory':
            return execute_show_memory_command(command.get('detailed', False))
            
        elif command['type'] == 'show-context':
            return execute_show_context_command()
            
        elif command['type'] == 'main':
            return execute_main_command(command.get('file_path'), command.get('auto_analyze', False))
            
        elif command['type'] == 'auto':
            return execute_auto_command(command.get('analyze_main', False))
            
        elif command['type'] == 'set-version':
            return execute_set_version_command(command.get('version'))
            
        elif command['type'] == 'add-to-path':
            return execute_add_to_path_command()
            
        elif command['type'] == 'start':
            return execute_start_command_queued(command)
            
        elif command['type'] == 'no-version-append':
            return execute_no_version_append_command(command.get('value', False))
            
        elif command['type'] == 'windowed':
            return execute_windowed_command(command.get('value', True))
            
        elif command['type'] == 'clean':
            return execute_clean_command()
            
        else:
            print(f"❌ Unknown command type: {command['type']}")
            return False
            
    except Exception as e:
        print(f"❌ Error executing {command['type']}: {e}")
        return False

def execute_add_command(files):
    """Execute add command from queue to add files to memory"""
    try:
        memory = ConsoleMemory()
        memory = ConsoleMemory()
        
        print("➕ File Add Operation")
        print("=" * 30)
        
        if not files:
            print("❌ No files specified for addition")
            return False
        
        # Parse the files list to handle comma-separated values and quoted strings
        parsed_files = parse_file_list(files)
        
        if not parsed_files:
            print("❌ No valid files found after parsing")
            return False
        
        print(f"📋 Processing {len(parsed_files)} file(s):")
        
        added_files = []
        skipped_files = []
        
        for file_path in parsed_files:
            file_path = file_path.strip()
            if not file_path:
                continue
                
            print(f"   📄 {file_path}")
            
            # Check if file exists
            if os.path.exists(file_path):
                # Determine file type based on extension
                file_type = determine_file_type(file_path)
                
                # Add to memory under scan_results
                if 'scan_results' not in memory.memory:
                    memory.memory['scan_results'] = {}
                
                if file_type not in memory.memory['scan_results']:
                    memory.memory['scan_results'][file_type] = []
                
                # Get absolute path
                abs_path = os.path.abspath(file_path)
                
                # Check if already in memory
                if abs_path not in memory.memory['scan_results'][file_type]:
                    memory.memory['scan_results'][file_type].append(abs_path)
                    added_files.append((file_path, file_type))
                    print(f"   ✅ Added to '{file_type}' memory")
                else:
                    skipped_files.append((file_path, "already in memory"))
                    print(f"   ⚠️  Already in memory")
            else:
                skipped_files.append((file_path, "file not found"))
                print(f"   ❌ File not found")
        
        # Save memory
        if added_files:
            memory.save_memory()
        
        # Show summary
        print(f"\n📊 Summary:")
        print(f"   ✅ Added: {len(added_files)} files")
        print(f"   ⚠️  Skipped: {len(skipped_files)} files")
        
        if added_files:
            print(f"\n📁 Files added by type:")
            type_counts = {}
            for _, file_type in added_files:
                type_counts[file_type] = type_counts.get(file_type, 0) + 1
            
            for file_type, count in type_counts.items():
                print(f"   📂 {file_type}: {count} files")
        
        if skipped_files:
            print(f"\n⚠️  Skipped files:")
            for file_path, reason in skipped_files:
                print(f"   • {file_path} ({reason})")
        
        return len(added_files) > 0
        
    except ImportError:
        print("❌ Core module required for memory operations")
        return False
    except Exception as e:
        print(f"❌ Error in add operation: {e}")
        return False

def parse_file_list(files):
    """Parse a list of files handling comma separation and quoted strings"""
    parsed_files = []
    
    # Join all arguments into a single string for parsing
    full_string = ' '.join(files)
    
    # Handle quoted strings (both single and double quotes)
    import re
    
    # Pattern to match quoted strings or unquoted words
    pattern = r'''(?:[^\s,"]|"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')+'''
    
    # Find all matches
    matches = re.findall(pattern, full_string)
    
    for match in matches:
        # Clean up the match
        cleaned = match.strip()
        
        # Remove quotes if present
        if (cleaned.startswith('"') and cleaned.endswith('"')) or \
           (cleaned.startswith("'") and cleaned.endswith("'")):
            cleaned = cleaned[1:-1]
        
        # Split by comma if no quotes were involved
        if ',' in cleaned and not (match.startswith('"') or match.startswith("'")):
            for part in cleaned.split(','):
                part = part.strip()
                if part:
                    parsed_files.append(part)
        else:
            if cleaned:
                parsed_files.append(cleaned)
    
    # Also handle simple comma separation in the original list
    additional_files = []
    for file_item in files:
        if ',' in file_item and not (file_item.startswith('"') or file_item.startswith("'")):
            for part in file_item.split(','):
                part = part.strip()
                if part and part not in parsed_files:
                    additional_files.append(part)
    
    parsed_files.extend(additional_files)
    
    # Remove duplicates while preserving order
    seen = set()
    final_files = []
    for file_path in parsed_files:
        if file_path not in seen:
            seen.add(file_path)
            final_files.append(file_path)
    
    return final_files

def determine_file_type(file_path):
    """Determine the file type based on extension for memory storage"""
    file_path = file_path.lower()
    
    # Python files
    if file_path.endswith(('.py', '.pyw', '.pyc', '.pyo', '.pyz')):
        return 'python'
    
    # Icon/Image files
    elif file_path.endswith(('.ico', '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.tiff', '.webp')):
        return 'icons'
    
    # Configuration files
    elif file_path.endswith(('.json', '.yaml', '.yml', '.ini', '.cfg', '.conf', '.toml')):
        return 'config'
    
    # Data files
    elif file_path.endswith(('.csv', '.db', '.sqlite', '.xml', '.txt', '.data')):
        return 'data'
    
    # Documentation files
    elif file_path.endswith(('.md', '.rst', '.txt', '.pdf', '.doc', '.docx')):
        return 'docs'
    
    # Template files
    elif file_path.endswith(('.html', '.htm', '.jinja2', '.j2', '.template')):
        return 'templates'
    
    # Help files
    elif file_path.endswith(('.help', '.hlp', '.chm')):
        return 'help'
    
    # Splash screen files
    elif 'splash' in file_path and file_path.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
        return 'splash'
    
    # Tutorial files
    elif any(keyword in file_path for keyword in ['tutorial', 'example', 'demo', 'sample']):
        return 'tutorials'
    
    # Default to 'project' for unknown types
    else:
        return 'project'

def execute_main_command(file_path, auto_analyze=False):
    """Execute main file specification command"""
    try:
        memory = ConsoleMemory()
        
        print("🎯 Main File Configuration")
        print("=" * 40)
        
        # Get project root if configured
        build_config = memory.get_config()
        project_root = build_config.get('project_root')

        if auto_analyze:
            print("🤖 Auto-analysis mode enabled - analyzing Python files...")
            # Use project root for auto-analysis if available
            search_dir = project_root if project_root and os.path.exists(project_root) else None
            main_file = analyze_and_find_main_file(search_dir)
            if main_file:
                print(f"🔍 Auto-detected main file: {main_file}")
                file_path = main_file
            else:
                print("❌ Could not auto-detect main file")
                if not file_path:
                    return False

        if not file_path:
            print("❌ No main file specified")
            return False

        # If file_path is relative and we have project root, make it relative to project root
        if project_root and os.path.exists(project_root) and not os.path.isabs(file_path):
            potential_path = os.path.join(project_root, file_path)
            if os.path.exists(potential_path):
                print(f"📁 Resolving relative path using project root: {project_root}")
                file_path = potential_path

        # Validate the file exists
        if not os.path.exists(file_path):
            print(f"❌ Main file not found: {file_path}")
            if project_root:
                print(f"💡 Searched in project root: {project_root}")
            return False

        # Validate it's a Python file
        if not file_path.lower().endswith(('.py', '.pyw')):
            print(f"❌ Main file must be a Python file: {file_path}")
            return False
        
        # Store in memory
        if 'build_config' not in memory.memory:
            memory.memory['build_config'] = {}
        
        memory.memory['build_config']['main_file'] = os.path.abspath(file_path)
        memory.save_memory()
        
        print(f"✅ Main file set to: {file_path}")
        
        # Analyze the main file
        analyze_main_file_details(file_path)
        
        return True
        
    except ImportError:
        print("❌ Core module required for main file configuration")
        return False
    except Exception as e:
        print(f"❌ Error setting main file: {e}")
        return False

def execute_auto_command(analyze_main=False):
    """Execute auto mode command"""
    try:
        print("🤖 Auto Mode Analysis")
        print("=" * 30)
        
        if analyze_main:
            main_file = analyze_and_find_main_file()
            if main_file:
                # Store the detected main file
                return execute_main_command(main_file, False)
            else:
                print("❌ Could not auto-detect main file")
                return False
        else:
            print("🔍 General auto-analysis (specify --main for main file detection)")
            # Add other auto-analysis features here
            return True
        
    except Exception as e:
        print(f"❌ Error in auto mode: {e}")
        return False

def analyze_and_find_main_file(search_directory=None):
    """Analyze Python files in the specified directory (or current directory) to find the most likely main file"""
    print("🔍 Analyzing Python files to detect main entry point...")
    
    # Use specified directory or current directory
    if search_directory is None:
        search_directory = '.'
    else:
        print(f"📁 Searching in: {search_directory}")
    
    # Find all Python files, prioritizing project files over dependencies
    python_files = []
    project_files = []
    
    for root, dirs, files in os.walk(search_directory):
        # Skip common directories that shouldn't contain main files
        dirs[:] = [d for d in dirs if d not in {
            '__pycache__', '.git', '.svn', 'venv', 'env', '.venv',
            'node_modules', 'build', 'dist', '.pytest_cache',
            'site-packages', 'Lib', 'lib', 'lib64', 'Scripts'
        }]
        
        for file in files:
            if file.endswith(('.py', '.pyw')) and not file.startswith('.'):
                file_path = os.path.join(root, file)
                python_files.append(file_path)
                
                # Prioritize files in the root directory or direct subdirectories
                depth = file_path.count(os.sep)
                if depth <= 2 and not any(exclude in file_path.lower() for exclude in 
                    ['buildscript', 'test_install', 'venv', 'env', '.venv']):
                    project_files.append(file_path)
    
    # Use project files if available, otherwise fall back to all files
    files_to_analyze = project_files if project_files else python_files[:50]  # Limit to 50 for performance
    
    if not files_to_analyze:
        print("❌ No Python files found in current directory")
        return None
    
    print(f"📋 Found {len(files_to_analyze)} Python files to analyze (prioritizing project files)")
    
    # Scoring system for main file detection
    candidates = []
    
    for file_path in files_to_analyze:
        score = 0
        reasons = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Extra bonus for being in root directory
            if os.path.dirname(file_path) in ['.', '']:
                score += 30
                reasons.append("In project root directory")
            
            # Check filename patterns
            filename = os.path.basename(file_path).lower()
            if filename in ['main.py', '__main__.py', 'app.py', 'run.py', 'start.py']:
                score += 50
                reasons.append("Main-like filename")
            elif filename.startswith('main_') or filename.endswith('_main.py'):
                score += 30
                reasons.append("Main-pattern filename")
            elif 'main' in filename:
                score += 20
                reasons.append("Contains 'main' in filename")
            
            # Check for if __name__ == "__main__":
            if 'if __name__ == "__main__"' in content:
                score += 40
                reasons.append("Has __name__ == '__main__' block")
            
            # Check for typical main function patterns
            if 'def main(' in content:
                score += 25
                reasons.append("Has main() function")
            
            # Check for GUI frameworks (likely main files)
            gui_imports = ['tkinter', 'PyQt', 'PySide', 'wx', 'kivy', 'flet', 'streamlit', 'dash']
            for gui_import in gui_imports:
                if f'import {gui_import}' in content or f'from {gui_import}' in content:
                    score += 15
                    reasons.append(f"Imports {gui_import} (GUI framework)")
                    break
            
            # Check for web framework imports (likely main files)
            web_imports = ['flask', 'django', 'fastapi', 'tornado', 'bottle']
            for web_import in web_imports:
                if f'import {web_import}' in content or f'from {web_import}' in content:
                    score += 15
                    reasons.append(f"Imports {web_import} (web framework)")
                    break
            
            # Check for command line argument parsing
            if 'argparse' in content or 'sys.argv' in content or 'click' in content:
                score += 10
                reasons.append("Has command line argument parsing")
            
            # Check for application setup patterns
            if any(pattern in content for pattern in ['app.run(', 'app.exec(', '.mainloop(', 'uvicorn.run(']):
                score += 20
                reasons.append("Has application execution pattern")
            
            # Penalty for test files
            if 'test' in filename.lower() or '/test' in file_path.lower():
                score -= 20
                reasons.append("Test file (penalty)")
            
            # Penalty for utility/helper files
            if any(pattern in filename.lower() for pattern in ['util', 'helper', 'config', 'setting']):
                score -= 10
                reasons.append("Utility/helper file (penalty)")
            
            # Strong penalty for files in virtual environments or build directories
            if any(exclude in file_path.lower() for exclude in 
                ['buildscript', 'site-packages', 'lib/', 'scripts/', 'build/', 'dist/']):
                score -= 50
                reasons.append("In dependency/build directory (major penalty)")
            
            candidates.append({
                'file': file_path,
                'score': score,
                'reasons': reasons
            })
            
        except Exception as e:
            print(f"   ⚠️  Could not analyze {file_path}: {e}")
            continue
    
    if not candidates:
        print("❌ No valid Python files could be analyzed")
        return None
    
    # Sort by score (highest first)
    candidates.sort(key=lambda x: x['score'], reverse=True)
    
    # Show analysis results
    print("\n📊 Main File Analysis Results:")
    print("-" * 60)
    for i, candidate in enumerate(candidates[:5]):  # Show top 5
        print(f"{i+1:2d}. {candidate['file']} (Score: {candidate['score']})")
        for reason in candidate['reasons']:
            print(f"     • {reason}")
        print()
    
    # Return the best candidate if it has a decent score
    best_candidate = candidates[0]
    if best_candidate['score'] >= 20:
        print(f"🎯 Best candidate: {best_candidate['file']} (Score: {best_candidate['score']})")
        return best_candidate['file']
    else:
        print(f"⚠️  Best candidate score too low ({best_candidate['score']}), manual specification recommended")
        print("💡 Consider using: build_cli --main <filename>")
        return None

def analyze_main_file_details(file_path):
    """Analyze details of the specified main file"""
    print(f"\n🔍 Analyzing main file: {file_path}")
    print("-" * 50)
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Basic file info
        lines = content.split('\n')
        print(f"📄 File: {os.path.basename(file_path)}")
        print(f"📍 Path: {os.path.abspath(file_path)}")
        print(f"📏 Size: {len(content)} characters, {len(lines)} lines")
        
        # Check for shebang
        if lines and lines[0].startswith('#!'):
            print(f"🔧 Shebang: {lines[0]}")
        
        # Analyze imports
        imports = []
        for line in lines:
            line = line.strip()
            if line.startswith('import ') or line.startswith('from '):
                imports.append(line)
        
        if imports:
            print(f"\n📦 Imports ({len(imports)}):")
            for imp in imports[:10]:  # Show first 10
                print(f"   • {imp}")
            if len(imports) > 10:
                print(f"   ... and {len(imports) - 10} more")
        
        # Check for main patterns
        patterns_found = []
        if 'if __name__ == "__main__"' in content:
            patterns_found.append("__name__ == '__main__' block")
        if 'def main(' in content:
            patterns_found.append("main() function")
        if any(pattern in content for pattern in ['app.run(', 'app.exec(', '.mainloop(']):
            patterns_found.append("Application execution")
        if 'argparse' in content or 'sys.argv' in content:
            patterns_found.append("Command line parsing")
        
        if patterns_found:
            print(f"\n✅ Detected patterns:")
            for pattern in patterns_found:
                print(f"   • {pattern}")
        
        # Check for potential dependencies
        common_packages = {
            'tkinter': 'GUI (Tkinter)',
            'PyQt': 'GUI (PyQt)',
            'PySide': 'GUI (PySide)', 
            'flask': 'Web (Flask)',
            'django': 'Web (Django)',
            'fastapi': 'Web (FastAPI)',
            'requests': 'HTTP client',
            'numpy': 'Scientific computing',
            'pandas': 'Data analysis',
            'matplotlib': 'Plotting',
            'opencv': 'Computer vision',
            'pygame': 'Game development'
        }
        
        detected_frameworks = []
        for package, description in common_packages.items():
            if package.lower() in content.lower():
                detected_frameworks.append(f"{package} ({description})")
        
        if detected_frameworks:
            print(f"\n🛠️  Detected frameworks/libraries:")
            for framework in detected_frameworks:
                print(f"   • {framework}")
        
        print(f"\n💡 This file appears to be suitable as a main entry point")
        
    except Exception as e:
        print(f"❌ Error analyzing file: {e}")

def execute_show_memory_command(detailed=False):
    """Execute show memory command from queue"""
    try:
        memory = ConsoleMemory()
        
        if detailed:
            show_detailed_memory(memory)
        else:
            memory.show_memory_status()
        return True
    except ImportError:
        print("❌ Core module required for memory operations")
        return False
    except Exception as e:
        print(f"❌ Error showing memory: {e}")
        return False

def execute_show_context_command():
    """Execute show context command - displays script location vs working directory info"""
    try:
        context = SCRIPT_CONTEXT
        
        print("🗂️  Script & Directory Context")
        print("=" * 50)
        
        # Basic info
        print(f"📍 Script Location: {context['script_location']}")
        print(f"📁 Working Directory: {context['working_directory']}")
        print(f"🔄 Same Directory: {'✅ Yes' if context['same_directory'] else '❌ No'}")
        
        # Execution context
        execution_icons = {
            'python_script': '🐍',
            'pyinstaller': '📦', 
            'executable': '⚡',
            'unknown': '❓',
            'fallback': '🔧'
        }
        icon = execution_icons.get(context['execution_method'], '❓')
        print(f"{icon} Execution Method: {context['execution_method'].replace('_', ' ').title()}")
        print(f"🖥️  Platform: {context['platform']}")
        
        # Path relationship
        if not context['same_directory']:
            print(f"📂 Relative Path: {context['relative_path']}")
            print()
            print("⚠️  Potential Issues:")
            print("   • Scanning will target working directory, not script location")
            print("   • Relative paths in config may not resolve correctly")
            print()
            print("💡 Solutions:")
            print(f"   • Use --scan-here to scan script directory")
            print(f"   • Use --scan-dir <path> for custom directories")
            print(f"   • Navigate to script directory first: cd \"{context['script_location']}\"")
        else:
            print()
            print("✅ Optimal Configuration:")
            print("   • Script and working directories match")
            print("   • All relative paths will resolve correctly")
            print("   • Scanning will work as expected")
        
        print()
        print("🛠️  Available Commands:")
        print("   • --show-context        Show this information")
        print("   • --scan-here           Scan script directory")
        print("   • --scan-dir <path>     Scan specific directory")
        
        return True
        
    except Exception as e:
        print(f"❌ Error showing context: {e}")
        return False

def execute_install_needed_command(project_file=None):
    """Execute install needed command from queue"""
    return handle_install_needed(project_file)

def execute_remove_command(target=None, remove_type=None, from_category=None):
    """Execute remove command from queue to remove items from memory"""
    try:
        memory = ConsoleMemory()
        
        print("🗑️  Memory Remove Operation")
        print("=" * 30)
        
        if target and remove_type and from_category:
            print(f"🎯 Removing {remove_type} items matching target: '{target}' from category: '{from_category}'")
            return handle_remove_with_target_type_and_category(memory, target, remove_type, from_category)
        elif target and from_category:
            print(f"🎯 Removing items matching target: '{target}' from category: '{from_category}'")
            return handle_remove_with_target_and_category(memory, target, from_category)
        elif target and remove_type:
            print(f"🎯 Removing {remove_type} items matching target: '{target}'")
            return handle_remove_with_target_and_type(memory, target, remove_type)
        elif target:
            print(f"🎯 Removing all items matching target: '{target}'")
            return handle_remove_with_target(memory, target)
        elif remove_type:
            print(f"📂 Removing all items of type: '{remove_type}'")
            return handle_remove_with_type(memory, remove_type)
        else:
            print("❌ Remove requires either --target or --type specification")
            print("💡 Examples:")
            print("   build_cli --remove --type python")
            print("   build_cli --remove --target myfile.py")
            print("   build_cli --remove --type config --target database")
            print("   build_cli --remove --target Splash.png --from icons")
            return False
        
    except ImportError:
        print("❌ Core module required for memory operations")
        return False
    except Exception as e:
        print(f"❌ Error in remove operation: {e}")
        return False

def execute_delete_command(target=None, delete_type=None):
    """Execute delete command from queue to delete actual files"""
    try:
        print("🗑️  File Delete Operation")
        print("=" * 30)
        
        if target and delete_type:
            print(f"🎯 Deleting {delete_type} files matching target: '{target}'")
            return handle_delete_with_target_and_type(target, delete_type)
        elif target:
            print(f"🎯 Deleting file: '{target}'")
            return handle_delete_with_target(target)
        elif delete_type:
            print(f"📂 Deleting all files of type: '{delete_type}'")
            return handle_delete_with_type(delete_type)
        else:
            print("❌ Delete requires either --target or --type specification")
            print("💡 Examples:")
            print("   build_cli --delete --target myfile.py")
            print("   build_cli --delete --type .pyc")
            print("   build_cli --delete --type temp --target cache")
            return False
        
    except Exception as e:
        print(f"❌ Error in delete operation: {e}")
        return False

def execute_name_command(build_name):
    """Execute name command from queue"""
    try:
        memory = ConsoleMemory()
        memory = ConsoleMemory()
        
        if 'build_config' not in memory.memory:
            memory.memory['build_config'] = {}
        
        memory.memory['build_config']['name'] = build_name
        memory.save_memory()
        
        return True
        
    except ImportError:
        print("❌ Core module required for build configuration")
        return False

def execute_date_command(date_value):
    """Execute date command from queue"""
    try:
        memory = ConsoleMemory()
        memory = ConsoleMemory()
        
        # Parse date value
        if date_value in ['true', 't', 'yes', 'y', '1']:
            include_date = True
        elif date_value in ['false', 'f', 'no', 'n', '0']:
            include_date = False
        else:
            print(f"❌ Invalid date value: '{date_value}'")
            return False
        
        if 'build_config' not in memory.memory:
            memory.memory['build_config'] = {}
        
        memory.memory['build_config']['include_date'] = include_date
        memory.save_memory()
        
        return True
        
    except ImportError:
        print("❌ Core module required for build configuration")
        return False

def execute_set_version_command(version):
    """Execute set-version command from queue"""
    try:
        memory = ConsoleMemory()
        memory = ConsoleMemory()
        
        print("🔢 Version Configuration")
        print("=" * 30)
        
        if not version:
            print("❌ No version specified")
            return False
        
        # Validate version format (basic validation)
        version = version.strip()
        if not version:
            print("❌ Version cannot be empty")
            return False
        
        # Store version in build configuration
        if 'build_config' not in memory.memory:
            memory.memory['build_config'] = {}
        
        memory.memory['build_config']['version'] = version
        memory.save_memory()
        
        print(f"✅ Program version set to: '{version}'")
        
        # Analyze version format and provide feedback
        version_info = analyze_version_format(version)
        if version_info:
            print(f"📋 Version analysis:")
            for info in version_info:
                print(f"   • {info}")
        
        return True
        
    except ImportError:
        print("❌ Core module required for version configuration")
        return False
    except Exception as e:
        print(f"❌ Error setting version: {e}")
        return False

def analyze_version_format(version):
    """Analyze and provide feedback on version format"""
    import re
    
    info = []
    
    # Check for date-based versioning first (more specific)
    if re.match(r'^\d{4}\.\d{1,2}\.\d{1,2}', version):
        info.append("Date-based versioning format")
        parts = version.split('.')
        if len(parts) >= 3:
            year, month, day = parts[0], parts[1], parts[2]
            info.append(f"Year: {year}, Month: {month}, Day: {day}")
    
    # Check for semantic versioning (X.Y.Z)
    elif re.match(r'^(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*))?(?:\+([a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*))?$', version):
        info.append("Follows semantic versioning format (MAJOR.MINOR.PATCH)")
        
        parts = version.split('.')
        major, minor, patch = parts[0], parts[1], parts[2].split('-')[0]
        info.append(f"Major: {major}, Minor: {minor}, Patch: {patch}")
        
        if '-' in version:
            pre_release = version.split('-', 1)[1].split('+')[0]
            info.append(f"Pre-release: {pre_release}")
        
        if '+' in version:
            build_metadata = version.split('+', 1)[1]
            info.append(f"Build metadata: {build_metadata}")
    
    # Check for simple X.Y format
    elif re.match(r'^\d+\.\d+$', version):
        info.append("Simple MAJOR.MINOR format")
    
    # Check for single number
    elif re.match(r'^\d+$', version):
        info.append("Single number version")
    
    # Check for alpha/beta/rc versions
    if any(keyword in version.lower() for keyword in ['alpha', 'beta', 'rc', 'dev', 'pre']):
        info.append("Pre-release version detected")
    
    # Length check
    if len(version) > 20:
        info.append("⚠️  Version string is quite long")
    
    return info

def execute_add_to_path_command():
    """Execute add-to-path command to add CLI to system PATH"""
    import platform
    import subprocess
    
    print("🛣️  System PATH Configuration")
    print("=" * 40)
    
    try:
        # Get current directory (where the CLI executable will be)
        current_dir = os.path.abspath(os.path.dirname(__file__))
        cli_name = "buildtool"  # Our CLI executable name
        
        print(f"📍 CLI Location: {current_dir}")
        print(f"🔧 CLI Name: {cli_name}")
        
        system = platform.system().lower()
        
        if system == "windows":
            return add_to_path_windows(current_dir, cli_name)
        elif system in ["linux", "darwin"]:  # Linux or macOS
            return add_to_path_unix(current_dir, cli_name)
        else:
            print(f"❌ Unsupported operating system: {system}")
            return False
            
    except Exception as e:
        print(f"❌ Error adding to PATH: {e}")
        return False

def add_to_path_windows(cli_dir, cli_name):
    """Add CLI to Windows PATH"""
    import winreg
    
    try:
        print("🪟 Windows PATH Configuration")
        print("-" * 30)
        
        # Check if already in PATH
        current_path = os.environ.get('PATH', '')
        if cli_dir in current_path:
            print(f"✅ Directory already in PATH: {cli_dir}")
        else:
            # Add to User PATH (safer than System PATH)
            try:
                # Open the user environment variables registry key
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Environment",
                    0,
                    winreg.KEY_ALL_ACCESS
                )
                
                # Get current PATH value
                try:
                    current_user_path, _ = winreg.QueryValueEx(key, "PATH")
                except FileNotFoundError:
                    current_user_path = ""
                
                # Add our directory if not already present
                if cli_dir not in current_user_path:
                    new_path = f"{current_user_path};{cli_dir}" if current_user_path else cli_dir
                    winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, new_path)
                    print(f"✅ Added to User PATH: {cli_dir}")
                else:
                    print(f"✅ Already in User PATH: {cli_dir}")
                
                winreg.CloseKey(key)
                
            except Exception as reg_error:
                print(f"❌ Registry error: {reg_error}")
                print("💡 Try running as administrator for system-wide PATH")
                return False
        
        # Create batch file for easy access
        batch_file = os.path.join(cli_dir, f"{cli_name}.bat")
        python_script = os.path.join(cli_dir, "build_cli.py")
        
        batch_content = f'''@echo off
REM BuildTool CLI Launcher
python "{python_script}" %*
'''
        
        try:
            with open(batch_file, 'w') as f:
                f.write(batch_content)
            print(f"✅ Created launcher: {batch_file}")
        except Exception as e:
            print(f"❌ Error creating batch file: {e}")
            return False
        
        print("\n🎉 PATH Configuration Complete!")
        print("💡 Restart your terminal/command prompt to use the new PATH")
        print(f"📋 You can now use: {cli_name} --help")
        print(f"📋 Or directly: {cli_name} --scan python")
        
        return True
        
    except ImportError:
        print("❌ Windows registry module not available")
        print("💡 You may need to manually add to PATH:")
        print(f"   Add this directory: {cli_dir}")
        return False
    except Exception as e:
        print(f"❌ Error configuring Windows PATH: {e}")
        return False

def add_to_path_unix(cli_dir, cli_name):
    """Add CLI to Unix/Linux/macOS PATH"""
    import os
    
    try:
        print("🐧 Unix/Linux/macOS PATH Configuration")
        print("-" * 40)
        
        # Determine shell configuration file
        shell = os.environ.get('SHELL', '/bin/bash')
        home_dir = os.path.expanduser('~')
        
        if 'zsh' in shell:
            shell_rc = os.path.join(home_dir, '.zshrc')
            shell_name = "Zsh"
        elif 'fish' in shell:
            shell_rc = os.path.join(home_dir, '.config/fish/config.fish')
            shell_name = "Fish"
        else:
            shell_rc = os.path.join(home_dir, '.bashrc')
            shell_name = "Bash"
        
        print(f"🐚 Detected shell: {shell_name}")
        print(f"📁 Configuration file: {shell_rc}")
        
        # Create shell script launcher
        script_file = os.path.join(cli_dir, cli_name)
        python_script = os.path.join(cli_dir, "build_cli.py")
        
        script_content = f'''#!/bin/bash
# BuildTool CLI Launcher
python3 "{python_script}" "$@"
'''
        
        try:
            with open(script_file, 'w') as f:
                f.write(script_content)
            os.chmod(script_file, 0o755)  # Make executable
            print(f"✅ Created launcher script: {script_file}")
        except Exception as e:
            print(f"❌ Error creating launcher script: {e}")
            return False
        
        # Add to PATH in shell configuration
        path_line = f'\n# BuildTool CLI\nexport PATH="$PATH:{cli_dir}"\n'
        
        try:
            # Check if already added
            if os.path.exists(shell_rc):
                with open(shell_rc, 'r') as f:
                    content = f.read()
                if cli_dir in content:
                    print(f"✅ Already in {shell_name} PATH configuration")
                else:
                    with open(shell_rc, 'a') as f:
                        f.write(path_line)
                    print(f"✅ Added to {shell_name} PATH configuration")
            else:
                # Create the configuration file
                os.makedirs(os.path.dirname(shell_rc), exist_ok=True)
                with open(shell_rc, 'w') as f:
                    f.write(path_line)
                print(f"✅ Created {shell_name} configuration with PATH")
        except Exception as e:
            print(f"❌ Error updating shell configuration: {e}")
            print("💡 You may need to manually add to PATH:")
            print(f"   export PATH=\"$PATH:{cli_dir}\"")
            return False
        
        print("\n🎉 PATH Configuration Complete!")
        print(f"💡 Restart your terminal or run: source {shell_rc}")
        print(f"📋 You can then use: {cli_name} --help")
        print(f"📋 Or directly: {cli_name} --scan python")
        
        return True
        
    except Exception as e:
        print(f"❌ Error configuring Unix PATH: {e}")
        return False

def execute_scan_command_queued(command):
    """Execute scan command from queue"""
    try:
        core = BuildToolCore()
        
        results = core.handle_scan_command(
            command['scan_type'],
            command.get('append', False),
            command.get('override', False),
            command.get('scan_dir'),
            command.get('contains')
        )
        
        print(f"   Found {len(results)} {command['scan_type']} files")
        return len(results) > 0
        
    except ImportError:
        print("❌ Core module required for scanning")
        return False

def execute_distant_scan_command(command):
    """Execute distant scan command from queue"""
    try:
        core = BuildToolCore()
        
        scan_directory = command['scan_directory']
        scan_type = command['scan_type']
        
        # Resolve relative paths for distant scanning
        resolved_directory = core.resolve_scan_path(scan_directory)
        
        print(f"🌐 Distant Scan Operation")
        print("=" * 40)
        print(f"📁 Original Directory: {scan_directory}")
        if resolved_directory != scan_directory:
            print(f"� Resolved Directory: {resolved_directory}")
        print(f"�🔍 Scan Type: {scan_type}")
        
        # Use the resolved directory
        scan_directory = resolved_directory
        
        # Validate that the target directory exists
        if not os.path.exists(scan_directory):
            print(f"❌ Target directory does not exist: {scan_directory}")
            return False
        
        if not os.path.isdir(scan_directory):
            print(f"❌ Target path is not a directory: {scan_directory}")
            return False
        
        # Execute the scan with the distant directory
        results = core.handle_scan_command(
            scan_type,
            command.get('append', False),
            command.get('override', False),
            scan_directory,  # Use the distant directory instead of current directory
            command.get('contains')
        )
        
        if results:
            print(f"✅ Distant scan completed successfully")
            print(f"📊 Found {len(results)} {scan_type} files in {scan_directory}")
        else:
            print(f"⚠️  No {scan_type} files found in {scan_directory}")
        
        return len(results) > 0
        
    except ImportError:
        print("❌ Core module required for distant scanning")
        return False
    except Exception as e:
        print(f"❌ Error in distant scan: {e}")
        return False

def execute_virtual_command(env_name, replace=False, recreate=False, repair=False, python_version=None, use_latest=False):
    """Execute virtual environment creation/selection command with replace/recreate/repair options"""
    try:
        import subprocess
        import platform
        import shutil
        memory = ConsoleMemory()
        
        # Store virtual environment name in configuration
        if 'build_config' not in memory.memory:
            memory.memory['build_config'] = {}
        
        memory.memory['build_config']['virtual_env'] = env_name
        if python_version:
            memory.memory['build_config']['python_version'] = python_version
        memory.save_memory()
        
        # Handle repair logic first (least destructive)
        if repair:
            print(f"🔧 Virtual Environment Repair: '{env_name}'")
            
            if not os.path.exists(env_name):
                print(f"❌ Environment '{env_name}' doesn't exist. Use --virtual {env_name} to create it first.")
                return False
            
            repair_success = repair_virtual_environment(env_name)
            if repair_success:
                print(f"✅ Environment '{env_name}' repaired successfully!")
                show_activation_instructions(env_name)
                return True
            else:
                print(f"⚠️  Repair failed. Consider using --replace or --recreate for complete restoration.")
                return False
        
        # Handle replace/recreate logic (more destructive)
        elif replace or recreate:
            print(f"🔄 Virtual Environment {'Replace' if replace else 'Recreate'}: '{env_name}'")
            
            if os.path.exists(env_name):
                # First, try to extract existing pip packages
                installed_packages = extract_pip_packages(env_name)
                
                if installed_packages:
                    print(f"� Found {len(installed_packages)} installed packages:")
                    for pkg in installed_packages[:10]:  # Show first 10
                        print(f"   • {pkg}")
                    if len(installed_packages) > 10:
                        print(f"   ... and {len(installed_packages) - 10} more packages")
                else:
                    print("⚠️  No pip packages detected in existing environment")
                
                # Remove the corrupted environment
                print(f"🗑️  Removing corrupted environment '{env_name}'...")
                try:
                    shutil.rmtree(env_name)
                    print(f"✅ Removed corrupted environment successfully")
                except Exception as e:
                    print(f"❌ Warning: Could not fully remove environment: {e}")
                    print("   Continuing anyway...")
            else:
                print(f"⚠️  Environment '{env_name}' doesn't exist, creating new one...")
                installed_packages = []
        else:
            installed_packages = []
        
        print(f"�🔧 Virtual Environment: '{env_name}'")
        
        # Check if environment exists, create if it doesn't
        if not os.path.exists(env_name):
            if not (replace or recreate):
                print(f"📁 Environment '{env_name}' not found. Creating...")
            
            try:
                # Create virtual environment
                print(f"🏗️  Creating virtual environment '{env_name}'...")
                
                # Determine which Python executable to use
                python_cmd = sys.executable  # Default to current Python
                creation_method = "venv"
                
                if use_latest:
                    print("✨ Using latest Python version available...")
                    # Create a temporary core instance to access the method
                    core = BuildToolCore()
                    latest_version = core.find_latest_python_version()
                    if latest_version:
                        python_cmd = core.find_python_executable(latest_version)
                        if python_cmd:
                            print(f"🐍 Using Python version: {latest_version}")
                        else:
                            print(f"⚠️  Could not find executable for Python {latest_version}, falling back to current Python ({sys.version.split()[0]})")
                            python_cmd = sys.executable
                    else:
                        print(f"⚠️  Could not detect latest Python version, falling back to current Python ({sys.version.split()[0]})")
                        python_cmd = sys.executable
                elif python_version:
                    print(f"🐍 Using Python version: {python_version}")
                    # Try to find specific Python version
                    # Create a temporary core instance to access the method
                    core = BuildToolCore()
                    python_cmd = core.find_python_executable(python_version)
                    if not python_cmd:
                        print(f"⚠️  Python {python_version} not found, falling back to current Python ({sys.version.split()[0]})")
                        python_cmd = sys.executable
                
                # Try venv first (Python's built-in)
                if isinstance(python_cmd, list):
                    venv_cmd = python_cmd + ['-m', 'venv', env_name]
                else:
                    venv_cmd = [python_cmd, '-m', 'venv', env_name]
                print(f"   Command: {' '.join(venv_cmd)}")
                
                result = subprocess.run(venv_cmd, capture_output=True, text=True, timeout=120)
                
                if result.returncode == 0:
                    print(f"✅ Virtual environment '{env_name}' created successfully!")
                    
                    # If we have packages to reinstall, do it now
                    if installed_packages and (replace or recreate):
                        success = reinstall_packages(env_name, installed_packages)
                        if not success:
                            print("⚠️  Some packages may not have been reinstalled correctly")
                    
                else:
                    print(f"❌ Failed to create virtual environment:")
                    print(f"   Error: {result.stderr}")
                    return False
                    
            except subprocess.TimeoutExpired:
                print("❌ Timeout creating virtual environment")
                return False
            except Exception as e:
                print(f"❌ Error creating virtual environment: {e}")
                return False
        else:
            if not (replace or recreate):
                print(f"✅ Virtual environment '{env_name}' already exists")
        
        # Show activation instructions
        show_activation_instructions(env_name)
        
        return True
        
    except ImportError:
        print("❌ Core module required for virtual environment configuration")
        return False
    except Exception as e:
        print(f"❌ Error in virtual environment operation: {e}")
        return False


def extract_pip_packages(env_name):
    """Extract list of installed packages from a virtual environment"""
    import subprocess
    import platform
    
    try:
        # Determine pip executable path
        if platform.system() == "Windows":
            pip_exe = os.path.join(env_name, "Scripts", "pip.exe")
        else:
            pip_exe = os.path.join(env_name, "bin", "pip")
        
        # Check if pip exists
        if not os.path.exists(pip_exe):
            print(f"⚠️  Pip not found at: {pip_exe}")
            return []
        
        # Get list of installed packages
        print(f"🔍 Extracting package list from '{env_name}'...")
        result = subprocess.run([
            pip_exe, "list", "--format=freeze"
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            packages = []
            for line in result.stdout.strip().split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and '==' in line:
                    # Extract package name with version
                    packages.append(line)
            return packages
        else:
            print(f"⚠️  Could not extract packages: {result.stderr}")
            return []
            
    except subprocess.TimeoutExpired:
        print("⚠️  Timeout extracting packages")
        return []
    except Exception as e:
        print(f"⚠️  Error extracting packages: {e}")
        return []


def reinstall_packages(env_name, packages):
    """Reinstall packages in the new virtual environment"""
    import subprocess
    import platform
    
    if not packages:
        return True
    
    try:
        # Determine pip executable path
        if platform.system() == "Windows":
            pip_exe = os.path.join(env_name, "Scripts", "pip.exe")
        else:
            pip_exe = os.path.join(env_name, "bin", "pip")
        
        print(f"📦 Reinstalling {len(packages)} packages...")
        
        # Upgrade pip first
        print("� Upgrading pip...")
        subprocess.run([
            pip_exe, "install", "--upgrade", "pip"
        ], capture_output=True, text=True, timeout=120)
        
        # Install packages in batches to avoid command line length limits
        batch_size = 20
        success_count = 0
        failed_packages = []
        
        for i in range(0, len(packages), batch_size):
            batch = packages[i:i + batch_size]
            print(f"📦 Installing batch {i//batch_size + 1}/{(len(packages) + batch_size - 1)//batch_size}...")
            
            try:
                result = subprocess.run([
                    pip_exe, "install"
                ] + batch, capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    success_count += len(batch)
                    print(f"   ✅ Batch installed successfully")
                else:
                    print(f"   ❌ Batch failed: {result.stderr}")
                    failed_packages.extend(batch)
                    
            except subprocess.TimeoutExpired:
                print(f"   ⏰ Batch timed out")
                failed_packages.extend(batch)
            except Exception as e:
                print(f"   ❌ Batch error: {e}")
                failed_packages.extend(batch)
        
        # Summary
        print(f"\n📊 Package Installation Summary:")
        print(f"   ✅ Successfully installed: {success_count} packages")
        if failed_packages:
            print(f"   ❌ Failed to install: {len(failed_packages)} packages")
            print(f"   Failed packages (first 5): {failed_packages[:5]}")
        
        return len(failed_packages) == 0
        
    except Exception as e:
        print(f"❌ Error reinstalling packages: {e}")
        return False


def repair_virtual_environment(env_name):
    """Repair a virtual environment by fixing missing components without full replacement"""
    import subprocess
    import platform
    import shutil
    import tempfile
    
    print("🔍 Diagnosing virtual environment issues...")
    
    # Check what's missing or corrupted
    issues = diagnose_env_issues(env_name)
    
    if not issues:
        print("✅ No issues detected - environment appears healthy!")
        return True
    
    print(f"🔧 Found {len(issues)} issues to repair:")
    for issue in issues:
        print(f"   • {issue}")
    
    # Try to fix issues one by one
    fixed_count = 0
    temp_env = None
    
    try:
        for issue_type, issue_desc in issues:
            print(f"\n🛠️  Fixing: {issue_desc}")
            
            if issue_type == "missing_pip":
                success = fix_missing_pip(env_name)
            elif issue_type == "missing_scripts":
                success = fix_missing_scripts(env_name)
            elif issue_type == "corrupted_pyvenv":
                success = fix_corrupted_pyvenv_cfg(env_name)
            elif issue_type == "missing_libs":
                # For complex lib issues, create a temporary environment to copy from
                if temp_env is None:
                    temp_env = create_temporary_env()
                success = fix_missing_libs(env_name, temp_env)
            else:
                print(f"   ⚠️  Unknown issue type: {issue_type}")
                success = False
            
            if success:
                print(f"   ✅ Fixed: {issue_desc}")
                fixed_count += 1
            else:
                print(f"   ❌ Failed to fix: {issue_desc}")
        
        # Clean up temporary environment
        if temp_env and os.path.exists(temp_env):
            try:
                shutil.rmtree(temp_env)
                print(f"🧹 Cleaned up temporary environment")
            except Exception as e:
                print(f"⚠️  Warning: Could not clean up temp env: {e}")
        
        # Report results
        print(f"\n📊 Repair Summary:")
        print(f"   ✅ Fixed: {fixed_count}/{len(issues)} issues")
        
        if fixed_count == len(issues):
            print("🎉 All issues resolved successfully!")
            return True
        elif fixed_count > 0:
            print("⚠️  Some issues resolved, but problems remain")
            return False
        else:
            print("❌ Unable to resolve any issues automatically")
            return False
            
    except Exception as e:
        print(f"❌ Error during repair process: {e}")
        return False


def diagnose_env_issues(env_name):
    """Diagnose what's wrong with a virtual environment"""
    import platform
    
    issues = []
    
    # Check basic structure
    if platform.system() == "Windows":
        scripts_dir = os.path.join(env_name, "Scripts")
        pip_exe = os.path.join(scripts_dir, "pip.exe")
        python_exe = os.path.join(scripts_dir, "python.exe")
        activate_script = os.path.join(scripts_dir, "activate.bat")
    else:
        bin_dir = os.path.join(env_name, "bin")
        pip_exe = os.path.join(bin_dir, "pip")
        python_exe = os.path.join(bin_dir, "python")
        activate_script = os.path.join(bin_dir, "activate")
    
    lib_dir = os.path.join(env_name, "lib" if platform.system() != "Windows" else "Lib")
    pyvenv_cfg = os.path.join(env_name, "pyvenv.cfg")
    
    # Check for missing pip
    if not os.path.exists(pip_exe):
        issues.append(("missing_pip", f"pip executable missing at {pip_exe}"))
    
    # Check for missing python executable
    if not os.path.exists(python_exe):
        issues.append(("missing_scripts", f"Python executable missing at {python_exe}"))
    
    # Check for missing activation script
    if not os.path.exists(activate_script):
        issues.append(("missing_scripts", f"Activation script missing at {activate_script}"))
    
    # Check pyvenv.cfg
    if not os.path.exists(pyvenv_cfg):
        issues.append(("corrupted_pyvenv", "pyvenv.cfg file missing"))
    else:
        # Check if pyvenv.cfg is readable and has required content
        try:
            with open(pyvenv_cfg, 'r') as f:
                content = f.read()
            if "home" not in content.lower() or "version" not in content.lower():
                issues.append(("corrupted_pyvenv", "pyvenv.cfg appears corrupted or incomplete"))
        except Exception:
            issues.append(("corrupted_pyvenv", "pyvenv.cfg is unreadable"))
    
    # Check lib directory
    if not os.path.exists(lib_dir):
        issues.append(("missing_libs", f"Library directory missing at {lib_dir}"))
    elif not os.listdir(lib_dir):
        issues.append(("missing_libs", "Library directory is empty"))
    
    return issues


def fix_missing_pip(env_name):
    """Fix missing pip by reinstalling it"""
    import subprocess
    import platform
    
    try:
        # Try to use ensurepip to reinstall pip
        if platform.system() == "Windows":
            python_exe = os.path.join(env_name, "Scripts", "python.exe")
        else:
            python_exe = os.path.join(env_name, "bin", "python")
        
        if not os.path.exists(python_exe):
            print("   ❌ Cannot fix pip - Python executable missing")
            return False
        
        print("   🔄 Reinstalling pip using ensurepip...")
        result = subprocess.run([
            python_exe, "-m", "ensurepip", "--upgrade"
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            return True
        else:
            print(f"   ❌ ensurepip failed: {result.stderr}")
            
            # Try alternative method - download get-pip.py
            print("   🔄 Trying alternative pip installation...")
            return install_pip_alternative(env_name)
            
    except Exception as e:
        print(f"   ❌ Error fixing pip: {e}")
        return False


def install_pip_alternative(env_name):
    """Alternative method to install pip using get-pip.py"""
    import subprocess
    import platform
    import urllib.request
    import tempfile
    
    try:
        if platform.system() == "Windows":
            python_exe = os.path.join(env_name, "Scripts", "python.exe")
        else:
            python_exe = os.path.join(env_name, "bin", "python")
        
        # Download get-pip.py to temporary file
        with tempfile.NamedTemporaryFile(mode='w+b', suffix='.py', delete=False) as temp_file:
            print("   📥 Downloading get-pip.py...")
            urllib.request.urlretrieve("https://bootstrap.pypa.io/get-pip.py", temp_file.name)
            
            # Run get-pip.py
            print("   🔄 Installing pip...")
            result = subprocess.run([
                python_exe, temp_file.name
            ], capture_output=True, text=True, timeout=300)
            
            # Clean up
            os.unlink(temp_file.name)
            
            return result.returncode == 0
            
    except Exception as e:
        print(f"   ❌ Alternative pip installation failed: {e}")
        return False


def fix_missing_scripts(env_name):
    """Fix missing scripts by recreating the environment structure"""
    import subprocess
    
    try:
        print("   🔄 Recreating missing scripts...")
        
        # Use venv to recreate just the scripts without removing everything
        result = subprocess.run([
            sys.executable, "-m", "venv", "--clear", env_name
        ], capture_output=True, text=True, timeout=120)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"   ❌ Error recreating scripts: {e}")
        return False


def fix_corrupted_pyvenv_cfg(env_name):
    """Fix corrupted pyvenv.cfg file"""
    try:
        pyvenv_cfg = os.path.join(env_name, "pyvenv.cfg")
        
        # Generate a new pyvenv.cfg file
        python_executable = sys.executable
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        
        cfg_content = f"""home = {os.path.dirname(python_executable)}
include-system-site-packages = false
version = {python_version}
executable = {python_executable}
command = {python_executable} -m venv {env_name}
"""
        
        print("   🔄 Recreating pyvenv.cfg...")
        with open(pyvenv_cfg, 'w') as f:
            f.write(cfg_content)
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error fixing pyvenv.cfg: {e}")
        return False


def fix_missing_libs(env_name, temp_env):
    """Fix missing lib directory by copying from temporary environment"""
    import shutil
    import platform
    
    try:
        # Source and destination paths
        if platform.system() == "Windows":
            temp_lib = os.path.join(temp_env, "Lib")
            target_lib = os.path.join(env_name, "Lib")
        else:
            temp_lib = os.path.join(temp_env, "lib")
            target_lib = os.path.join(env_name, "lib")
        
        if not os.path.exists(temp_lib):
            print("   ❌ Temporary environment also missing lib directory")
            return False
        
        print("   🔄 Copying library files from temporary environment...")
        
        # Remove existing (possibly corrupted) lib directory
        if os.path.exists(target_lib):
            shutil.rmtree(target_lib)
        
        # Copy from temporary environment
        shutil.copytree(temp_lib, target_lib)
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error fixing lib directory: {e}")
        return False


def create_temporary_env():
    """Create a temporary virtual environment for repair purposes"""
    import tempfile
    import subprocess
    
    try:
        temp_dir = tempfile.mkdtemp(prefix="venv_repair_")
        print(f"   📁 Creating temporary environment at {temp_dir}")
        
        result = subprocess.run([
            sys.executable, "-m", "venv", temp_dir
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            return temp_dir
        else:
            print(f"   ❌ Failed to create temporary environment")
            return None
            
    except Exception as e:
        print(f"   ❌ Error creating temporary environment: {e}")
        return None


def show_activation_instructions(env_name):
    """Show activation instructions for the virtual environment"""
    import platform
    
    print(f"\n🚀 Environment '{env_name}' is ready!")
    print("=" * 40)
    
    if platform.system() == "Windows":
        activate_script = f"{env_name}\\Scripts\\activate.bat"
        activate_ps1 = f"{env_name}\\Scripts\\Activate.ps1"
        
        print(f"💡 Activation Commands:")
        print(f"   Command Prompt: {activate_script}")
        print(f"   PowerShell: {activate_ps1}")
        print(f"   Or: .\\{activate_ps1}")
    else:
        activate_script = f"{env_name}/bin/activate"
        print(f"💡 Activation Command:")
        print(f"   source {activate_script}")
    
    print(f"\n💻 Quick Commands:")
    print(f"   Activate & Install: buildtool --virtual {env_name} --activate")
    print(f"   Check packages: pip list")
    print(f"   Deactivate: deactivate")

def execute_activate_command():
    """Execute virtual environment activation command"""
    try:
        import subprocess
        import platform
        import os
        memory = ConsoleMemory()
        
        # Get virtual environment name from configuration
        config = memory.memory.get('build_config', {})
        env_name = config.get('virtual_env')
        
        if not env_name:
            print("❌ No virtual environment specified. Use --virtual <env_name> first")
            return False
        
        print(f"🚀 Activating Virtual Environment: '{env_name}'")
        
        # Check if environment exists
        if not os.path.exists(env_name):
            print(f"❌ Virtual environment '{env_name}' not found")
            print(f"💡 Use --virtual {env_name} to create it first")
            return False
        
        # Actually activate the environment by launching a new shell
        if platform.system() == "Windows":
            activate_script = f"{env_name}\\Scripts\\activate.bat"
            ps_activate = f"{env_name}\\Scripts\\Activate.ps1"
            
            if os.path.exists(activate_script):
                print(f"✅ Launching new shell with '{env_name}' activated...")
                
                # Determine which shell to use
                current_shell = os.environ.get('PSModulePath')  # PowerShell sets this
                
                if current_shell:  # PowerShell
                    print("🐚 Launching PowerShell with activated environment...")
                    activation_cmd = f'& "{os.path.abspath(ps_activate)}"; Write-Host "✅ Virtual environment {env_name} activated!"; Write-Host "💡 Type \\"deactivate\\" to exit the environment"'
                    subprocess.run([
                        "powershell", "-NoExit", "-Command", activation_cmd
                    ])
                else:  # Command Prompt
                    print("🐚 Launching Command Prompt with activated environment...")
                    subprocess.run([
                        "cmd", "/k", f'"{activate_script}" && echo ✅ Virtual environment {env_name} activated! && echo 💡 Type "deactivate" to exit the environment'
                    ])
                
                return True
            else:
                print(f"❌ Activation script not found: {activate_script}")
                return False
        else:  # Unix-like systems
            activate_script = f"{env_name}/bin/activate"
            
            if os.path.exists(activate_script):
                print(f"✅ Launching new shell with '{env_name}' activated...")
                print("🐚 Starting bash with activated environment...")
                
                # For Unix, we need to source the activation script
                subprocess.run([
                    "bash", "--rcfile", 
                    f"<(echo 'source {activate_script}; echo \"✅ Virtual environment {env_name} activated!\"; echo \"💡 Type deactivate to exit the environment\"')"
                ])
                
                return True
            else:
                print(f"❌ Activation script not found: {activate_script}")
                return False
        
    except ImportError:
        print("❌ Required modules not available")
        return False
    except Exception as e:
        print(f"❌ Error activating virtual environment: {e}")
        print("💡 Manual activation commands:")
        if platform.system() == "Windows":
            print(f"   Command Prompt: {env_name}\\Scripts\\activate.bat")
            print(f"   PowerShell: {env_name}\\Scripts\\Activate.ps1")
        else:
            print(f"   Bash/Shell: source {env_name}/bin/activate")
        return False

def execute_activate_command_enhanced(specified_env=None):
    """Execute virtual environment activation command with optional environment name"""
    try:
        import subprocess
        import platform
        import os
        memory = ConsoleMemory()
        
        # Determine which environment to activate
        if specified_env:
            env_name = specified_env
            print(f"🎯 Targeting specified environment: '{env_name}'")
            
            # Update memory with this environment
            if 'build_config' not in memory.memory:
                memory.memory['build_config'] = {}
            memory.memory['build_config']['virtual_env'] = env_name
            memory.save_memory()
        else:
            # Get virtual environment name from configuration
            config = memory.memory.get('build_config', {})
            env_name = config.get('virtual_env')
            
            if not env_name:
                # Try to detect existing virtual environments
                detected_envs = []
                for item in os.listdir('.'):
                    if os.path.isdir(item):
                        # Check if it's a virtual environment
                        if platform.system() == "Windows":
                            if os.path.exists(os.path.join(item, 'Scripts', 'activate.bat')):
                                detected_envs.append(item)
                        else:
                            if os.path.exists(os.path.join(item, 'bin', 'activate')):
                                detected_envs.append(item)
                
                if detected_envs:
                    env_name = detected_envs[0]  # Use the first one found
                    print(f"🔍 Auto-detected virtual environment: '{env_name}'")
                    
                    # Store it for future use
                    if 'build_config' not in memory.memory:
                        memory.memory['build_config'] = {}
                    memory.memory['build_config']['virtual_env'] = env_name
                    memory.save_memory()
                else:
                    print("❌ No virtual environment found!")
                    print("💡 Use --virtual <env_name> to create one first")
                    print("💡 Or use --activate <env_name> to specify one")
                    return False
        
        print(f"🚀 Enhanced Virtual Environment Activation: '{env_name}'")
        
        # Check if environment exists, create if it doesn't
        if not os.path.exists(env_name):
            print(f"❌ Virtual environment '{env_name}' not found")
            print(f"💡 Creating it automatically...")
            
            try:
                # Get the best Python executable for virtual environment creation
                python_exec = find_python_executable()
                if not python_exec:
                    python_exec = sys.executable
                
                result = subprocess.run([
                    python_exec, '-m', 'venv', env_name
                ], capture_output=True, text=True, timeout=120)
                
                if result.returncode == 0:
                    print(f"✅ Virtual environment '{env_name}' created successfully!")
                else:
                    print(f"❌ Failed to create virtual environment:")
                    print(f"   Error: {result.stderr}")
                    return False
                    
            except Exception as e:
                print(f"❌ Error creating virtual environment: {e}")
                return False
        
        # Launch a new shell with the virtual environment activated
        if platform.system() == "Windows":
            activate_script = f"{env_name}\\Scripts\\activate.bat"
            ps_activate = f"{env_name}\\Scripts\\Activate.ps1"
            
            if os.path.exists(activate_script):
                print(f"✅ Virtual environment '{env_name}' found")
                print(f"🚀 Launching enhanced shell with environment activated...")
                
                # Determine shell type and create appropriate activation
                current_shell = os.environ.get('PSModulePath')  # PowerShell indicator
                
                if current_shell:  # PowerShell
                    print("🐚 Starting enhanced PowerShell session...")
                    ps_command = f'''
& "{os.path.abspath(ps_activate)}"
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Enhanced Virtual Environment: {env_name}" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Python:" (python --version) -ForegroundColor Yellow
Write-Host "Location:" (Get-Location) -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "💡 Available commands:" -ForegroundColor Blue
Write-Host "   python --version    | Check Python version"
Write-Host "   pip list            | List installed packages"
Write-Host "   pip freeze          | Show all dependencies"
Write-Host "   deactivate          | Exit virtual environment"
Write-Host ""
Write-Host "🚀 Enhanced environment ready!" -ForegroundColor Green
'''
                    subprocess.run([
                        "powershell", "-NoExit", "-Command", ps_command
                    ])
                else:  # Command Prompt
                    print("🐚 Starting enhanced Command Prompt session...")
                    cmd_script = f'''
call "{activate_script}"
echo ========================================
echo   Enhanced Virtual Environment: {env_name}
echo ========================================
python --version
echo Location: %CD%
echo ========================================
echo.
echo 💡 Available commands:
echo    python --version    ^| Check Python version
echo    pip list            ^| List installed packages
echo    pip freeze          ^| Show all dependencies  
echo    deactivate          ^| Exit virtual environment
echo.
echo 🚀 Enhanced environment ready!
'''
                    # Create temporary batch file for enhanced activation
                    temp_batch = f"temp_activate_{env_name}.bat"
                    with open(temp_batch, 'w', encoding='utf-8') as f:
                        f.write(cmd_script)
                    
                    try:
                        subprocess.run(["cmd", "/k", temp_batch])
                    finally:
                        # Clean up temp file
                        if os.path.exists(temp_batch):
                            os.remove(temp_batch)
                
                return True
            else:
                print(f"❌ Activation script not found: {activate_script}")
                return False
        else:
            activate_script = f"{env_name}/bin/activate"
            if os.path.exists(activate_script):
                print(f"✅ Virtual environment '{env_name}' found")
                print(f"🚀 Launching enhanced shell with environment activated...")
                
                # Enhanced bash activation
                bash_command = f'''
source "{activate_script}"
echo "========================================"
echo "  Enhanced Virtual Environment: {env_name}"
echo "========================================"
echo "Python: $(python --version)"
echo "Location: $(pwd)"
echo "========================================"
echo ""
echo "💡 Available commands:"
echo "   python --version    | Check Python version"
echo "   pip list            | List installed packages"
echo "   pip freeze          | Show all dependencies"
echo "   deactivate          | Exit virtual environment"
echo ""
echo "🚀 Enhanced environment ready!"
'''
                
                subprocess.run([
                    "bash", "--init-file", 
                    f"<(echo '{bash_command}')"
                ])
                
                return True
            else:
                print(f"❌ Activation script not found: {activate_script}")
                return False
        
    except Exception as e:
        print(f"❌ Error during enhanced activation: {e}")
        print("💡 Manual activation commands:")
        if platform.system() == "Windows":
            print(f"   Command Prompt: {env_name}\\Scripts\\activate.bat")
            print(f"   PowerShell: {env_name}\\Scripts\\Activate.ps1")
        else:
            print(f"   Bash/Shell: source {env_name}/bin/activate")
        return False
        
    except ImportError:
        print("❌ Core module required for virtual environment operations")
        return False

def execute_downgrade_command(version):
    """Execute version downgrade command"""
    try:
        memory = ConsoleMemory()
        memory = ConsoleMemory()
        
        # Store downgrade version in configuration
        if 'build_config' not in memory.memory:
            memory.memory['build_config'] = {}
        
        memory.memory['build_config']['downgrade_version'] = version
        memory.save_memory()
        
        print(f"✅ Downgrade version set to: '{version}'")
        print("💡 This will be used for dependency management during build")
        return True
        
    except ImportError:
        print("❌ Core module required for version management")
        return False

def execute_target_command(target):
    """Execute target specification command"""
    try:
        memory = ConsoleMemory()
        memory = ConsoleMemory()
        
        # Store target in configuration
        if 'build_config' not in memory.memory:
            memory.memory['build_config'] = {}
        
        memory.memory['build_config']['target'] = target
        memory.save_memory()
        
        print(f"✅ Build target set to: '{target}'")
        return True
        
    except ImportError:
        print("❌ Core module required for target configuration")
        return False

def execute_show_console_command(show_value):
    """Execute show-console command"""
    try:
        memory = ConsoleMemory()
        memory = ConsoleMemory()
        
        # Parse show console value
        if show_value in ['true', 't', 'yes', 'y', '1']:
            show_console = True
        elif show_value in ['false', 'f', 'no', 'n', '0']:
            show_console = False
        else:
            print(f"❌ Invalid show-console value: '{show_value}'")
            return False
        
        # Store show console setting in configuration
        if 'build_config' not in memory.memory:
            memory.memory['build_config'] = {}
        
        memory.memory['build_config']['show_console'] = show_console
        memory.save_memory()
        
        print(f"✅ Show console set to: {show_console}")
        return True
        
    except ImportError:
        print("❌ Core module required for console configuration")
        return False

def show_final_build_config():
    """Show final build configuration after processing queue"""
    try:
        memory = ConsoleMemory()
        memory = ConsoleMemory()
        
        config = memory.memory.get('build_config', {})
        build_name = config.get('name', 'Auto-generated')
        include_date = config.get('include_date', True)
        version = config.get('version')
        main_file = config.get('main_file')
        
        print("\n🔧 Final Build Configuration:")
        print("─" * 35)
        print(f"📝 Build Name: {build_name}")
        print(f"📅 Include Date: {include_date}")
        
        if version:
            print(f"🔢 Version: {version}")
        
        if main_file:
            print(f"🎯 Main File: {main_file}")
        
        if build_name != 'Auto-generated':
            if include_date:
                from datetime import datetime
                date_str = datetime.now().strftime("%Y%m%d")
                final_name = f"{build_name}_{date_str}"
            else:
                final_name = build_name
            
            print(f"📦 Final Build Name: {final_name}")
            
            if version:
                print(f"💡 Consider adding version to executable name: {final_name}_v{version}")
        
    except ImportError:
        print("❌ Core module not available for configuration display")
    except Exception as e:
        print(f"❌ Error showing final configuration: {e}")

def main():
    """Main entry point for CLI Core Module"""
    
    # Handle ultra-fast commands directly  
    if '--help' in sys.argv or '-h' in sys.argv:
        show_integrated_help()
        return True
    
    elif '--version' in sys.argv:
        print("PyInstaller Build Tool - CLI Core Module")
        print("Version: 2.0.0-core")
        print("Integrated CLI with no GUI dependencies")
        return True
    
    elif '--changelog' in sys.argv:
        print("""
PyInstaller Build Tool - Changelog

Version 2.0.0-core:
  • Integrated CLI core - no separate core module needed
  • Removed GUI dependencies from CLI for clean separation
  • CLI now serves as the core functionality
  • GUI will be separate module that interfaces with CLI core
  • Prevents PyInstaller GUI conflicts when using CLI commands
        """)
        return True
    
    # Handle core functionality commands
    elif '--scan' in sys.argv:
        return handle_scan_command()
    
    elif '--show-memory' in sys.argv:
        return handle_show_memory()
    
    elif '--show-context' in sys.argv:
        return execute_show_context_command()
    
    elif '--clear-memory' in sys.argv:
        return handle_clear_memory()
    
    elif '--remove' in sys.argv:
        return handle_remove_command()
    
    elif '--console' in sys.argv:
        return handle_console_mode()
    
    elif '--start' in sys.argv:
        return handle_start()
    
    elif '--name' in sys.argv:
        return handle_build_name()
    
    elif '--date' in sys.argv:
        return handle_build_date()
    
    elif '--main' in sys.argv:
        return handle_main_file_command()
    
    elif '--add' in sys.argv:
        return handle_add_command()
    
    elif '--set-version' in sys.argv:
        return handle_set_version_command()
    
    elif '--set-root' in sys.argv:
        return handle_set_root()
    
    elif '--show-root' in sys.argv:
        return handle_show_root()
    
    elif '--add-to-path' in sys.argv:
        return handle_add_to_path_command()
        
    elif '--setup-sdk' in sys.argv:
        return handle_setup_sdk_command()
        
    elif '--collect' in sys.argv:
        return handle_collect_command()
        
    elif '--import' in sys.argv:
        return handle_import_command()
        
    elif '--export' in sys.argv:
        return handle_export_command()
        
    elif '--no-version-append' in sys.argv:
        return handle_no_version_append_command()
        
    elif '--gui' in sys.argv:
        return handle_gui_command()
        
    elif '--download-gui' in sys.argv:
        return handle_download_gui()
    
    elif '--repo-status' in sys.argv:
        return handle_repo_status()
    
    elif '--update' in sys.argv:
        return handle_update()
    
    elif '--windowed' in sys.argv:
        return execute_windowed_command(True)
        
    elif '--no-console' in sys.argv:
        # Check if there's a true/false parameter
        windowed_value = True  # Default
        for i, arg in enumerate(sys.argv):
            if arg == '--no-console' and i + 1 < len(sys.argv):
                next_arg = sys.argv[i + 1]
                if not next_arg.startswith('--'):
                    windowed_value = next_arg.lower() in ['true', 'yes', '1', 'on']
                    break
        return execute_windowed_command(windowed_value)
    
    elif '--clean' in sys.argv:
        return execute_clean_command()
    
    # If no arguments provided
    elif len(sys.argv) <= 1:
        print("PyInstaller Build Tool - CLI Core")
        print("=" * 40)
        print("Use --help for available commands")
        print("Use --console for interactive mode")
        return True
    
    # Special case for --auto used alone
    elif '--auto' in sys.argv and len([arg for arg in sys.argv[1:] if not arg.startswith('-') or arg == '--auto']) == 1:
        print("💡 --auto Usage Guide")
        print("=" * 30)
        print("The --auto flag is a modifier that enables automatic detection and configuration.")
        print("It cannot be used by itself and must be combined with other commands.")
        print()
        print("🎯 Common Usage Examples:")
        print("  --main --auto              Auto-detect and set main Python file")
        print("  --add file.py --auto       Add file + auto-detect main file")
        print("  --scan python --auto       Scan for Python files + auto-configure")
        print("  --start build --auto       Start build with auto-detection")
        print()
        print("📚 What --auto does:")
        print("  • Automatically detects your main Python entry point")
        print("  • Analyzes your project structure")
        print("  • Suggests optimal build settings")
        print("  • Configures dependencies and data files")
        print()
        print("💡 Try: python build_cli.py --main --auto")
        return False
    
    else:
        print("❌ Unknown command")
        print("Use --help for available commands")
        return False

def show_integrated_help():
    """Show help for the integrated CLI core"""
    print("""
PyInstaller Build Tool - CLI Core Module

Usage: python build_cli.py [OPTIONS]

Architecture: This CLI now serves as the core functionality with no GUI dependencies.
The GUI is a separate module that interfaces with this core.

Core Commands:
  --help, -h            Show this help message
  --version             Show version information
  --console             Interactive console mode
  --scan TYPE           Scan for files (python, icons, config, etc.)
  --show-memory         Display current memory status
  --clear-memory        Clear all stored data
  --remove              Remove items from memory (with --type, --target, or --from)
  --start PROCESS       Start build process (build, quick, custom, package, msiwrapping)
  --collect             Collect and organize files for packaging
  --import FILE         Import configuration from file (JSON, XML, or spec)
  --export FILE         Export current configuration to file
  --name NAME           Set custom build name
  --date BOOL           Include date in build name (true/false)
  --windowed            Enable windowed mode (no console window)
  --no-console [BOOL]   Same as --windowed, accepts true/false
  --virtual ENV_NAME    Create/manage virtual environment
  --activate [ENV_NAME] Activate virtual environment
  --add-to-path         Add CLI to system PATH
  --setup-sdk           Setup Windows SDK PATH for packaging tools

Information Commands:
  --repo-status         Check GitHub repository status
  --update              Check for updates
  --gui                 Launch GUI interface (if available)
  --download-gui        Information about GUI module
  --changelog           Show recent changes

Scan Types Available:
  python, icons, images, config, data, templates, docs, help, splash, json, tutorials, virtual, project

Scanning Commands:
  --scan TYPE           Scan current directory for specific file type
  --distant-scan DIR    Scan distant directory (use with --type to specify scan type)

Examples:
  python build_cli.py --scan python          Scan for Python files
  python build_cli.py --scan virtual         Scan for virtual environments
  python build_cli.py --distant-scan "C:\\Projects" --type python  Scan distant folder for Python files
  python build_cli.py --distant-scan ./other_project --type config  Scan other project for config files
  python build_cli.py --show-memory          Show current memory status
  python build_cli.py --remove --type python Remove Python files from memory
  python build_cli.py --remove --target "test" Remove files containing "test"
  python build_cli.py --remove --target "Splash.png" --from icons Remove Splash.png from icons only
  python build_cli.py --name "MyApp" --start quick   Set name and start quick build
  python build_cli.py --console              Interactive console mode
  python build_cli.py --start build          Start build with current config

Build Examples:
  python build_cli.py --start build          Full build with current configuration
  python build_cli.py --start quick          Quick auto-build with detection
  python build_cli.py --start package        Create MSIX/MSI package with MakeAppx and SignTool
  python build_cli.py --name "MyApp" --start build   Set name and build
  python build_cli.py --windowed --start build       Build as windowed app (no console)
  python build_cli.py --no-console false --start build   Build with console window

Import/Export Examples:
  python build_cli.py --collect              Collect files for packaging
  python build_cli.py --import config.json   Import configuration from JSON
  python build_cli.py --import build.xml     Import configuration from XML
  python build_cli.py --import app.spec      Import from PyInstaller spec file
  python build_cli.py --export my_config.json    Export current config to JSON
  python build_cli.py --export my_config.xml     Export current config to XML
  python build_cli.py --export my_build.spec     Export as PyInstaller spec

Modifier Flags:
  --auto                Enable automatic detection and configuration
                        (Must be combined with other commands)
  --append              Append to existing results instead of replacing
  --override            Override/replace existing results (explicit replace mode)
  --no-version          Disable version appending for current build
  --no-version-append BOOL  Set global version append setting (true/false)

Auto-Detection Examples:
  python build_cli.py --main --auto          Auto-detect and set main file
  python build_cli.py --scan python --auto   Scan files with auto-configuration
  python build_cli.py --start build --auto   Build with auto-detection

Version Control Examples:
  python build_cli.py --start build --no-version        Build without version
  python build_cli.py --no-version-append false         Disable version globally
  python build_cli.py --set-version 2.1.0 --start build Set version and build

Virtual Environment Examples:
  python build_cli.py --virtual myenv         Create virtual environment 'myenv'
  python build_cli.py --virtual myenv --repair    Repair corrupted environment (non-destructive)
  python build_cli.py --virtual myenv --replace   Replace corrupted environment
  python build_cli.py --virtual myenv --recreate  Recreate environment with packages
  python build_cli.py --virtual myenv --version 3.11  Create with specific Python version
  python build_cli.py --virtual myenv --latest    Create with newest Python version available
  python build_cli.py --virtual py311env --version 3.11 --repair  Repair with version check
  python build_cli.py --activate myenv        Activate environment 'myenv'
  python build_cli.py --virtual myenv --activate  Create and activate in one step

Virtual Environment Modifiers:
  --repair              Repair corrupted environment (tries to fix without replacing)
  --replace             Replace corrupted environment (saves/restores packages)
  --recreate            Recreate environment completely (saves/restores packages)
  --version X.Y         Specify Python version to use (e.g., 3.11, 3.12)
  --latest              Use the newest Python version available on system

Note: This CLI module now contains the core functionality. GUI is separate.
    """)

def handle_console_mode():
    """Handle interactive console mode with menu-based interface"""
    print("🖥️  PyInstaller Build Tool - Interactive Console")
    print("=" * 60)
    
    try:
        core = BuildToolCore()
        memory = core.memory
        
        print("Welcome to the Interactive Console Interface!")
        print("• Type a number to select from the menu")
        print("• Type CLI commands directly (e.g., '--scan python')")
        print("• Type 'help' for command reference, 'exit' to quit")
        print()
        
        while True:
            try:
                # Show main menu
                print("┌─────────────────────────────────────────────┐")
                print("│          MAIN MENU - Select Option         │")
                print("├─────────────────────────────────────────────┤")
                print("│ 1. 🔍 File Scanning & Analysis             │")
                print("│ 2. 💾 Memory Management                    │")
                print("│ 3. 🏗️  Project Configuration               │")
                print("│ 4. 🚀 Build Management                     │")
                print("│ 5. 📊 Repository & Updates                  │")
                print("│ 6. ❓ Help & Documentation                 │")
                print("│ 0. 🚪 Exit Console                         │")
                print("└─────────────────────────────────────────────┘")
                print()
                
                cmd = input("build> ").strip()
                
                # Handle exit commands
                if cmd.lower() in ['exit', 'quit', 'q', '0']:
                    print("👋 Goodbye!")
                    break
                
                # Handle menu selections
                elif cmd == '1':
                    handle_scan_menu(core)
                
                elif cmd == '2':
                    handle_memory_menu(memory)
                
                elif cmd == '3':
                    handle_project_config_menu(core)
                
                elif cmd == '4':
                    handle_build_menu(core)
                
                elif cmd == '5':
                    handle_repo_menu()
                
                elif cmd == '6':
                    handle_help_menu()
                
                # Handle direct CLI commands (advanced users)
                elif cmd.startswith('--'):
                    print(f"🔧 Executing CLI command: {cmd}")
                    success = execute_cli_command(cmd)
                    if success:
                        print("✅ Command completed successfully")
                    else:
                        print("❌ Command failed or not recognized")
                
                # Handle simple console commands
                elif cmd.lower() in ['help', 'h']:
                    show_console_help()
                
                elif cmd.lower() == 'menu':
                    continue  # Show menu again
                
                elif cmd.lower().startswith('scan '):
                    scan_type = cmd[5:].strip()
                    if scan_type:
                        results = core.handle_scan_command(scan_type)
                        print(f"✅ Scan completed - found {len(results)} files")
                    else:
                        print("❌ Please specify scan type (e.g., 'scan python')")
                
                elif cmd.lower() == 'memory':
                    memory.show_memory_status()
                
                elif cmd.lower() == 'clear':
                    memory.clear_memory()
                    print("🧹 Memory cleared successfully")
                
                elif cmd.strip() == '':
                    continue  # Just show menu again
                
                # Try to interpret as CLI command
                else:
                    if cmd:
                        print(f"🤔 Trying to interpret '{cmd}' as CLI command...")
                        success = execute_cli_command(f"--{cmd}" if not cmd.startswith('-') else cmd)
                        if not success:
                            print(f"❌ Unknown command: '{cmd}'")
                            print("💡 Tips:")
                            print("   • Use numbers 1-6 to navigate the menu")
                            print("   • Type '--help' for CLI command reference")
                            print("   • Type 'help' for console commands")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                print("Type 'help' for assistance")
        
        return True
        
    except ImportError:
        print("❌ Core module required for console mode")
        print("You can download it with: build_cli --download-gui")
        return False
    except Exception as e:
        print(f"❌ Error starting console mode: {e}")
        return False

def handle_scan_menu(core):
    """Handle file scanning submenu"""
    while True:
        print("\n┌─────────────────────────────────────────────┐")
        print("│         🔍 FILE SCANNING MENU              │")
        print("├─────────────────────────────────────────────┤")
        print("│ 1. Python files (.py)                      │")
        print("│ 2. Icon files (.ico, .png, etc.)          │")
        print("│ 3. Configuration files (.json, .yaml)      │")
        print("│ 4. Data files (.csv, .db, .xml)           │")
        print("│ 5. Documentation (.md, .txt, .rst)        │")
        print("│ 6. All project files (comprehensive)       │")
        print("│ 7. Custom scan (specify type)              │")
        print("│ 8. Advanced filtering options              │")
        print("│ 0. ← Back to main menu                     │")
        print("└─────────────────────────────────────────────┘")
        
        choice = input("scan> ").strip()
        
        if choice == '0':
            break
        elif choice == '1':
            results = core.handle_scan_command('python')
            print(f"✅ Found {len(results)} Python files")
        elif choice == '2':
            results = core.handle_scan_command('icons')
            print(f"✅ Found {len(results)} icon files")
        elif choice == '3':
            results = core.handle_scan_command('config')
            print(f"✅ Found {len(results)} configuration files")
        elif choice == '4':
            results = core.handle_scan_command('data')
            print(f"✅ Found {len(results)} data files")
        elif choice == '5':
            results = core.handle_scan_command('docs')
            print(f"✅ Found {len(results)} documentation files")
        elif choice == '6':
            results = core.handle_scan_command('project')
            print(f"✅ Found {len(results)} project files")
        elif choice == '7':
            scan_type = input("Enter scan type (icons/config/python/data/etc.): ").strip()
            if scan_type:
                results = core.handle_scan_command(scan_type)
                print(f"✅ Found {len(results)} {scan_type} files")
        elif choice == '8':
            handle_advanced_scan_menu(core)
        else:
            print("❌ Invalid choice. Please select 0-8.")

def handle_advanced_scan_menu(core):
    """Handle advanced scanning options"""
    print("\n🔧 Advanced Scanning Options:")
    scan_type = input("Scan type: ").strip()
    if not scan_type:
        return
    
    contains = input("Filter by content (optional): ").strip()
    scan_dir = input("Custom directory (optional, default=current): ").strip()
    append_mode = input("Append to existing results? (y/n): ").strip().lower() == 'y'
    
    results = core.handle_scan_command(
        scan_type, 
        append_mode=append_mode, 
        scan_directory=scan_dir if scan_dir else None,
        contains_filter=contains if contains else None
    )
    print(f"✅ Advanced scan completed - found {len(results)} files")

def handle_memory_menu(memory):
    """Handle memory management submenu"""
    while True:
        print("\n┌─────────────────────────────────────────────┐")
        print("│         💾 MEMORY MANAGEMENT               │")
        print("├─────────────────────────────────────────────┤")
        print("│ 1. Show current memory status              │")
        print("│ 2. Clear all stored data                   │")
        print("│ 3. Clear specific scan results             │")
        print("│ 4. Remove specific files/items             │")
        print("│ 5. Export memory to file                   │")
        print("│ 6. Import memory from file                 │")
        print("│ 0. ← Back to main menu                     │")
        print("└─────────────────────────────────────────────┘")
        
        choice = input("memory> ").strip()
        
        if choice == '0':
            break
        elif choice == '1':
            memory.show_memory_status()
        elif choice == '2':
            confirm = input("Are you sure you want to clear ALL data? (y/n): ")
            if confirm.lower() == 'y':
                memory.clear_memory()
                print("🧹 All memory cleared successfully")
        elif choice == '3':
            scan_types = list(memory.get_scan_results().keys())
            if scan_types:
                print("Available scan results:", ", ".join(scan_types))
                scan_type = input("Enter type to clear: ").strip()
                if scan_type in scan_types:
                    memory.memory["scan_results"].pop(scan_type, None)
                    memory.save_memory()
                    print(f"🧹 Cleared {scan_type} results")
                else:
                    print("❌ Scan type not found")
            else:
                print("💡 No scan results to clear")
        elif choice == '4':
            handle_interactive_remove(memory)
        elif choice == '5':
            print("💾 Export functionality coming soon!")
        elif choice == '6':
            print("📥 Import functionality coming soon!")
        else:
            print("❌ Invalid choice. Please select 0-6.")

def handle_interactive_remove(memory):
    """Handle interactive remove operations in console"""
    while True:
        print("\n┌─────────────────────────────────────────────┐")
        print("│         🗑️  REMOVE OPERATIONS              │")
        print("├─────────────────────────────────────────────┤")
        print("│ 1. Remove by file type                     │")
        print("│ 2. Remove by filename/pattern              │")
        print("│ 3. Remove by type AND pattern              │")
        print("│ 4. Show what would be removed               │")
        print("│ 0. ← Back to memory menu                   │")
        print("└─────────────────────────────────────────────┘")
        
        choice = input("remove> ").strip()
        
        if choice == '0':
            break
        elif choice == '1':
            # Remove by type
            scan_types = list(memory.get_scan_results().keys())
            if scan_types:
                print(f"\nAvailable types: {', '.join(scan_types)}")
                remove_type = input("Enter type to remove: ").strip()
                if remove_type in scan_types:
                    count = len(memory.get_scan_results()[remove_type])
                    confirm = input(f"Remove {count} {remove_type} files? (y/n): ")
                    if confirm.lower() == 'y':
                        success = handle_remove_with_type(memory, remove_type)
                        if success:
                            print(f"✅ Removed {remove_type} files from memory")
                        else:
                            print("❌ Remove operation failed")
                else:
                    print("❌ Type not found")
            else:
                print("💡 No scan results to remove")
                
        elif choice == '2':
            # Remove by target/pattern
            target = input("Enter filename or pattern to remove: ").strip()
            if target:
                success = handle_remove_with_target(memory, target)
                if success:
                    print(f"✅ Removed files matching '{target}' from memory")
                else:
                    print("❌ Remove operation failed or no matches found")
            else:
                print("❌ Please enter a filename or pattern")
                
        elif choice == '3':
            # Remove by type and target
            scan_types = list(memory.get_scan_results().keys())
            if scan_types:
                print(f"\nAvailable types: {', '.join(scan_types)}")
                remove_type = input("Enter type: ").strip()
                target = input("Enter filename or pattern: ").strip()
                
                if remove_type and target:
                    success = handle_remove_with_target_and_type(memory, target, remove_type)
                    if success:
                        print(f"✅ Removed {remove_type} files matching '{target}' from memory")
                    else:
                        print("❌ Remove operation failed or no matches found")
                else:
                    print("❌ Please enter both type and pattern")
            else:
                print("💡 No scan results to remove")
                
        elif choice == '4':
            # Preview what would be removed
            print("\n📋 Current Memory Contents:")
            scan_results = memory.get_scan_results()
            if scan_results:
                for scan_type, files in scan_results.items():
                    print(f"\n📂 {scan_type} ({len(files)} files):")
                    for i, file_path in enumerate(files[:5]):
                        print(f"   {i+1}. {file_path}")
                    if len(files) > 5:
                        print(f"   ... and {len(files) - 5} more files")
            else:
                print("💡 No files in memory")
        else:
            print("❌ Invalid choice. Please select 0-4.")

def handle_project_menu(core):
    """Handle project management submenu"""
    while True:
        print("\n┌─────────────────────────────────────────────┐")
        print("│         🏗️  PROJECT MANAGEMENT             │")
        print("├─────────────────────────────────────────────┤")
        print("│ 1. Show optimal project structure          │")
        print("│ 2. Configure build settings                │")
        print("│ 3. Analyze current project                 │")
        print("│ 4. Build recommendations                   │")
        print("│ 5. Generate build configuration            │")
        print("│ 6. Create new project (coming soon)        │")
        print("│ 0. ← Back to main menu                     │")
        print("└─────────────────────────────────────────────┘")
        
        choice = input("project> ").strip()
        
        if choice == '0':
            break
        elif choice == '1':
            core.show_optimal_structure()
        elif choice == '2':
            handle_build_config_menu(core)
        elif choice == '3':
            print("🔍 Analyzing current project...")
            results = core.handle_scan_command('project')
            print(f"📊 Project contains {len(results)} files")
        elif choice == '4':
            print("💡 Build recommendations coming soon!")
        elif choice == '5':
            print("⚙️  Configuration generation coming soon!")
        elif choice == '6':
            print("🆕 Project creation functionality coming soon!")
        else:
            print("❌ Invalid choice. Please select 0-6.")

def handle_build_config_menu(core):
    """Handle build configuration submenu"""
    try:
        memory = ConsoleMemory()
        
        while True:
            # Show current configuration
            config = memory.memory.get('build_config', {})
            current_name = config.get('name', 'Auto-generated')
            current_date = config.get('include_date', True)
            
            print("\n┌─────────────────────────────────────────────┐")
            print("│         🔧 BUILD CONFIGURATION             │")
            print("├─────────────────────────────────────────────┤")
            print(f"│ Current Name: {current_name:<25} │")
            print(f"│ Include Date: {str(current_date):<25} │")
            print("├─────────────────────────────────────────────┤")
            print("│ 1. Set build name                          │")
            print("│ 2. Toggle date inclusion                   │")
            print("│ 3. Show preview of final build name        │")
            print("│ 4. Reset to defaults                       │")
            print("│ 5. Show current configuration              │")
            print("│ 0. ← Back to project menu                  │")
            print("└─────────────────────────────────────────────┘")
            
            choice = input("config> ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                name = input("Enter build name: ").strip()
                if name:
                    if 'build_config' not in memory.memory:
                        memory.memory['build_config'] = {}
                    memory.memory['build_config']['name'] = name
                    memory.save_memory()
                    print(f"✅ Build name set to: '{name}'")
                else:
                    print("❌ No name entered")
                    
            elif choice == '2':
                current_setting = memory.memory.get('build_config', {}).get('include_date', True)
                new_setting = not current_setting
                if 'build_config' not in memory.memory:
                    memory.memory['build_config'] = {}
                memory.memory['build_config']['include_date'] = new_setting
                memory.save_memory()
                print(f"✅ Date inclusion toggled to: {new_setting}")
                
            elif choice == '3':
                show_build_preview(memory)
                
            elif choice == '4':
                confirm = input("Reset all build settings to defaults? (y/n): ")
                if confirm.lower() == 'y':
                    memory.memory['build_config'] = {
                        'name': 'Auto-generated',
                        'include_date': True
                    }
                    memory.save_memory()
                    print("✅ Build configuration reset to defaults")
                    
            elif choice == '5':
                show_build_config(memory)
                
            else:
                print("❌ Invalid choice. Please select 0-5.")
                
    except ImportError:
        print("❌ Core module required for build configuration")
    except Exception as e:
        print(f"❌ Error in build configuration: {e}")

def show_build_preview(memory):
    """Show preview of the final build name"""
    config = memory.memory.get('build_config', {})
    build_name = config.get('name', 'Auto-generated')
    include_date = config.get('include_date', True)
    
    print("\n🎯 Build Name Preview:")
    print("─" * 25)
    
    if build_name == 'Auto-generated':
        print("📝 Base Name: [Auto-detected from project]")
        if include_date:
            from datetime import datetime
            date_str = datetime.now().strftime("%Y%m%d")
            print(f"📅 With Date: [ProjectName]_{date_str}")
        else:
            print("📅 Without Date: [ProjectName]")
    else:
        print(f"📝 Base Name: {build_name}")
        if include_date:
            from datetime import datetime
            date_str = datetime.now().strftime("%Y%m%d")
            final_name = f"{build_name}_{date_str}"
            print(f"📅 With Date: {final_name}")
        else:
            print(f"📅 Without Date: {build_name}")
    
    print("\n💡 The final executable will be named accordingly")

def handle_launch_menu(core):
    """Handle application launch submenu"""
    while True:
        print("\n┌─────────────────────────────────────────────┐")
        print("│         🚀 LAUNCH APPLICATIONS             │")
        print("├─────────────────────────────────────────────┤")
        print("│ 1. Launch GUI interface                     │")
        print("│ 2. Start build process (coming soon)       │")
        print("│ 3. Run tests (coming soon)                 │")
        print("│ 4. Open project in explorer/finder         │")
        print("│ 0. ← Back to main menu                     │")
        print("└─────────────────────────────────────────────┘")
        
        choice = input("launch> ").strip()
        
        if choice == '0':
            break
        elif choice == '1':
            print("🚀 Launching GUI interface...")
            return core.launch_gui()
        elif choice == '2':
            print("🔨 Build functionality coming soon!")
        elif choice == '3':
            print("🧪 Test functionality coming soon!")
        elif choice == '4':
            import platform
            import subprocess
            try:
                if platform.system() == "Windows":
                    subprocess.run(["explorer", "."])
                elif platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", "."])
                else:  # Linux
                    subprocess.run(["xdg-open", "."])
                print("📁 Opened current directory")
            except Exception as e:
                print(f"❌ Could not open directory: {e}")
        else:
            print("❌ Invalid choice. Please select 0-4.")

def handle_repo_menu():
    """Handle repository management submenu"""
    while True:
        print("\n┌─────────────────────────────────────────────┐")
        print("│         📊 REPOSITORY & UPDATES            │")
        print("├─────────────────────────────────────────────┤")
        print("│ 1. Check repository status                 │")
        print("│ 2. Check for updates                       │")
        print("│ 3. Download GUI module                     │")
        print("│ 4. Download CLI module                     │")
        print("│ 5. View changelog                          │")
        print("│ 0. ← Back to main menu                     │")
        print("└─────────────────────────────────────────────┘")
        
        choice = input("repo> ").strip()
        
        if choice == '0':
            break
        elif choice == '1':
            handle_repo_status()
        elif choice == '2':
            handle_update()
        elif choice == '3':
            handle_download_gui()
        elif choice == '4':
            handle_download_cli()
        elif choice == '5':
            execute_cli_command('--changelog')
        else:
            print("❌ Invalid choice. Please select 0-5.")

def handle_help_menu():
    """Handle help and documentation submenu"""
    while True:
        print("\n┌─────────────────────────────────────────────┐")
        print("│         ❓ HELP & DOCUMENTATION            │")
        print("├─────────────────────────────────────────────┤")
        print("│ 1. Console commands reference              │")
        print("│ 2. CLI commands reference                  │")
        print("│ 3. Scan types reference                    │")
        print("│ 4. Quick start guide                       │")
        print("│ 5. Advanced usage examples                 │")
        print("│ 0. ← Back to main menu                     │")
        print("└─────────────────────────────────────────────┘")
        
        choice = input("help> ").strip()
        
        if choice == '0':
            break
        elif choice == '1':
            show_console_help()
        elif choice == '2':
            execute_cli_command('--help')
        elif choice == '3':
            show_scan_types_help()
        elif choice == '4':
            show_quick_start()
        elif choice == '5':
            show_advanced_examples()
        else:
            print("❌ Invalid choice. Please select 0-5.")

def show_console_help():
    """Show console-specific help"""
    print("""
📖 Console Interface Help:

Menu Navigation:
  • Use numbers (1-6) to navigate menus
  • Type '0' to go back or exit
  • Type 'menu' to return to main menu

Direct Commands:
  • CLI commands: --scan python, --show-memory, etc.
  • Console commands: scan python, memory, clear, help
  • Smart interpretation: 'python' → '--scan python'

Quick Commands:
  scan <type>     - Quick file scanning
  memory          - Show memory status  
  clear           - Clear all memory
  help            - Show this help
  exit            - Exit console
    """)

def show_scan_types_help():
    """Show available scan types"""
    print("""
🔍 Available Scan Types:

Basic Types:
  python          - Python files (.py, .pyw)
  icons           - Icon files (.ico, .png, .jpg, .svg)
  config          - Configuration (.json, .yaml, .ini, .cfg)
  data            - Data files (.csv, .db, .xml, .txt)
  templates       - Template files (.html, .jinja2, .j2)
  docs            - Documentation (.md, .txt, .rst, .pdf)

Advanced Types:
  images          - All image formats
  json            - JSON files specifically
  help            - Help and guide files
  splash          - Splash screen related files
  tutorials       - Tutorial and example files
  project         - Complete project scan (all files)

Usage Examples:
  scan python               - Find Python files
  scan icons --append      - Add icons to existing results
  scan icons --override    - Replace existing icon results
  scan config --contains db - Config files mentioning "db"
  scan tutorials --scan-dir ../Tutorials - Scan relative directory
    """)

def show_quick_start():
    """Show quick start guide"""
    print("""
🚀 Quick Start Guide:

1. First Time Setup:
   • Use menu option 1 → 6 (comprehensive project scan)
   • Check memory with option 2 → 1
   • View project structure with option 3 → 1

2. Regular Workflow:
   • Scan for specific files (option 1)
   • Check what's stored (option 2)
   • Launch GUI when needed (option 4 → 1)

3. Advanced Users:
   • Type CLI commands directly: --scan python --contains "import"
   • Use console shortcuts: scan python, memory, clear

4. Getting Help:
   • Menu option 6 for all help topics
   • Type 'help' for console commands
   • Type '--help' for CLI reference
    """)

def show_advanced_examples():
    """Show advanced usage examples"""
    print("""
🎯 Advanced Usage Examples:

Direct CLI Commands in Console:
  --scan python --contains "import requests"
  --scan config --scan-dir ../project --append
  --show-memory
  --download-gui

Console Command Shortcuts:
  scan python     (equivalent to --scan python)
  memory         (equivalent to --show-memory)
  clear          (equivalent to --clear-memory)

Filtering and Options:
  Advanced scan menu (option 1 → 8) for:
  • Custom directories
  • Content filtering
  • Append mode
  • Multiple criteria

Pro Tips:
  • Mix menu and commands: use menus for discovery, commands for speed
  • Save frequently used commands as shortcuts
  • Use 'menu' to return to main menu from anywhere
    """)

def execute_cli_command(command):
    """Execute a CLI command and return success status - supports command stacking"""
    try:
        # Parse the command into argv format
        args = command.split()
        if not args:
            return False
            
        # Save original argv
        original_argv = sys.argv.copy()
        
        # Replace with our command
        sys.argv = ['build_cli.py'] + args
        
        # Initialize core and memory
        core = BuildToolCore()
        
        # Track success of all commands
        all_success = True
        processed_commands = []
        
        # Process commands in sequence, allowing stacking
        i = 0
        while i < len(args):
            arg = args[i]
            command_success = False
            
            # Handle the command
            if arg == '--scan' and i + 1 < len(args):
                # Execute scan command
                try:
                    scan_type = args[i + 1]
                    
                    # Check for options after scan type
                    append_mode = False
                    contains_filter = None
                    scan_directory = None
                    
                    # Look ahead for modifiers
                    j = i + 2
                    while j < len(args):
                        if args[j] == '--append':
                            append_mode = True
                            j += 1
                        elif args[j] == '--contains' and j + 1 < len(args):
                            contains_filter = args[j + 1]
                            j += 2
                        elif args[j] == '--scan-dir' and j + 1 < len(args):
                            scan_directory = args[j + 1] 
                            j += 2
                        elif args[j].startswith('--'):
                            # Hit next command, stop processing modifiers
                            break
                        else:
                            j += 1
                    
                    results = core.handle_scan_command(scan_type, append_mode, scan_directory, contains_filter)
                    print(f"✅ Scan completed: Found {len(results)} {scan_type} files")
                    processed_commands.append(f"--scan {scan_type}")
                    command_success = True
                    i += 2  # Skip the scan type argument
                except (ValueError, IndexError) as e:
                    print(f"❌ Scan command failed: {e}")
                    i += 1
                    
            elif arg == '--show-memory':
                # Handle show-memory with optional detailed flag
                detailed = False
                if i + 1 < len(args) and args[i + 1] == '--detailed':
                    detailed = True
                    i += 1  # Skip the --detailed flag
                
                memory = ConsoleMemory()
                if detailed:
                    show_detailed_memory(memory)  # Use the comprehensive function
                else:
                    memory.show_memory_status()
                    
                processed_commands.append("--show-memory" + (" --detailed" if detailed else ""))
                command_success = True
                i += 1
                
            elif arg == '--clear-memory':
                memory = ConsoleMemory()
                memory.clear_memory()
                print("🧹 Memory cleared successfully")
                processed_commands.append("--clear-memory")
                command_success = True
                i += 1
                    
            elif arg == '--show-optimal':
                command_success = handle_show_optimal()
                processed_commands.append("--show-optimal")
                i += 1
                
            elif arg == '--name':
                command_success = handle_build_name()
                processed_commands.append("--name")
                i += 1
                
            elif arg == '--date':
                command_success = handle_build_date()
                processed_commands.append("--date")
                i += 1
                
            elif arg == '--help':
                print("PyInstaller Build Tool Enhanced - CLI Help")
                print("Version: 2.0.0-modular")
                print("Command stacking supported: --show-memory --detailed")
                print("For full help, use the console menu system.")
                processed_commands.append("--help")
                command_success = True
                i += 1
                
            elif arg == '--version':
                print("PyInstaller Build Tool Enhanced - CLI Launcher")
                print("Version: 2.0.0-modular")
                processed_commands.append("--version")
                command_success = True
                i += 1
                
            elif arg == '--changelog':
                command_success = handle_changelog()
                processed_commands.append("--changelog")
                i += 1
                
            elif arg == '--repo-status':
                command_success = handle_repo_status()
                processed_commands.append("--repo-status")
                i += 1
                
            elif arg == '--download-gui':
                command_success = handle_download_gui()
                processed_commands.append("--download-gui")
                i += 1
                
            elif arg == '--download-cli':
                command_success = handle_download_cli()
                processed_commands.append("--download-cli")
                i += 1
                
            elif arg == '--update':
                command_success = handle_update()
                processed_commands.append("--update")
                i += 1
                
            elif arg == '--downgrade':
                command_success = handle_downgrade()
                processed_commands.append("--downgrade")
                i += 1
                
            elif arg == '--preview-name':
                command_success = handle_preview_name()
                processed_commands.append("--preview-name")
                i += 1
                
            elif arg == '--virtual':
                command_success = handle_virtual_env()
                processed_commands.append("--virtual")
                i += 1
                
            elif arg == '--activate':
                command_success = handle_activate_env()
                processed_commands.append("--activate")
                i += 1
                
            elif arg == '--install-needed':
                command_success = handle_install_needed()
                processed_commands.append("--install-needed")
                i += 1
                
            elif arg == '--location':
                command_success = handle_location()
                processed_commands.append("--location")
                i += 1
                
            elif arg == '--scan-project':
                command_success = handle_scan_project()
                processed_commands.append("--scan-project")
                i += 1
                
            elif arg == '--target':
                command_success = handle_target()
                processed_commands.append("--target")
                i += 1
                
            elif arg == '--set-root':
                command_success = handle_set_root()
                processed_commands.append("--set-root")
                i += 1
                
            elif arg == '--show-root':
                command_success = handle_show_root()
                processed_commands.append("--show-root")
                i += 1
                
            elif arg == '--export':
                command_success = handle_export()
                processed_commands.append("--export")
                i += 1
                
            elif arg == '--export-config':
                command_success = handle_export_config()
                processed_commands.append("--export-config")
                i += 1
                
            elif arg == '--start':
                command_success = handle_start()
                processed_commands.append("--start")
                i += 1
                
            elif arg == '--remove-type':
                command_success = handle_remove_type()
                processed_commands.append("--remove-type")
                i += 1
                
            elif arg == '--delete':
                command_success = handle_delete()
                processed_commands.append("--delete")
                i += 1
                
            elif arg == '--delete-type':
                command_success = handle_delete_type()
                processed_commands.append("--delete-type")
                i += 1
                
            elif arg == '--create':
                command_success = handle_create()
                processed_commands.append("--create")
                i += 1
                
            elif arg == '--show-console':
                command_success = handle_show_console()
                processed_commands.append("--show-console")
                i += 1
                
            elif arg == '--auto':
                command_success = handle_auto_mode()
                processed_commands.append("--auto")
                i += 1
                
            elif arg == '--backup':
                command_success = handle_backup()
                processed_commands.append("--backup")
                i += 1
                
            elif arg == '--type':
                # This is likely a modifier for another command, skip
                i += 1
                continue
                
            elif arg == '--remove':
                # Handle remove command with modifiers
                try:
                    target = None
                    remove_type = None
                    
                    # Look ahead for --target and --type
                    j = i + 1
                    while j < len(args):
                        if args[j] == '--target' and j + 1 < len(args):
                            target = args[j + 1]
                            j += 2
                        elif args[j] == '--type' and j + 1 < len(args):
                            remove_type = args[j + 1]
                            j += 2
                        elif args[j].startswith('--'):
                            break
                        else:
                            j += 1
                    
                    # Execute remove command
                    memory = ConsoleMemory()
                    if remove_type and target:
                        success = memory.remove_specific_file(remove_type, target)
                        if success:
                            print(f"✅ Removed {target} from {remove_type}")
                            command_success = True
                        else:
                            print(f"❌ Failed to remove {target} from {remove_type}")
                    else:
                        print("❌ Remove command requires --type and --target")
                    
                    processed_commands.append("--remove")
                    i = j  # Continue from where we left off
                except Exception as e:
                    print(f"❌ Remove command failed: {e}")
                    i += 1
                    
            # Skip modifier arguments that are handled by their parent commands
            elif arg in ['--detailed', '--append', '--override', '--contains', '--scan-dir']:
                i += 1
                continue
                
            else:
                # Unknown command
                print(f"⚠️  Unknown command: {arg}")
                i += 1
                continue
            
            # Track overall success
            if not command_success:
                all_success = False
        
        # Summary
        if processed_commands:
            print(f"\n📋 Executed {len(processed_commands)} commands: {', '.join(processed_commands)}")
            
        return all_success
            
    except Exception as e:
        print(f"❌ Error executing command: {e}")
        return False
    finally:
        # Restore original argv
        sys.argv = original_argv
    
    return False

def handle_show_optimal():
    """Show optimal project structure"""
    print("""
🏗️  Optimal Project Structure for PyInstaller

📁 MyProject/
├── 📁 src/                     # Main source code
│   ├── 📄 main.py             # Entry point
│   ├── 📁 modules/            # Your modules
│   └── 📁 utils/              # Utility functions
├── 📁 assets/                 # Static assets
│   ├── 📁 icons/             # Application icons (.ico, .png)
│   ├── 📁 images/            # Images and graphics
│   ├── 📁 data/              # Data files (.json, .csv, etc.)
│   └── 📁 templates/         # HTML/text templates
├── 📁 config/                # Configuration files
│   ├── 📄 settings.json      # Application settings
│   └── 📄 build_config.json  # Build configuration
├── 📁 docs/                  # Documentation
│   ├── 📄 README.md
│   └── 📄 user_guide.md
├── 📁 tests/                 # Test files
├── 📄 requirements.txt       # Dependencies
├── 📄 build_script.py       # Build automation
└── 📄 .env                  # Environment variables

🎯 Naming Conventions:
• Use descriptive, consistent names
• Avoid spaces in file/folder names
• Use lowercase with underscores for Python files
• Use CamelCase for class names
• Include version in final builds (MyApp_v1.0.0_20250804)

🚀 Build Optimization Tips:
• Keep main.py minimal - import from modules
• Use --onefile for single executable
• Exclude unnecessary modules with --exclude-module
• Include data files with --add-data
• Test on target systems before release
    """)
    return True

def handle_changelog():
    """Show changelog information"""
    print("""
📋 PyInstaller Build Tool - Changelog

🆕 Version 2.0.0-modular (Latest)
• ✅ Command stacking support (--show-memory --detailed)
• ✅ Enhanced console system with interactive menus
• ✅ Version control flags (--no-version, --no-version-append)
• ✅ GitHub GUI download functionality
• ✅ Improved memory management with detailed status
• ✅ Modular architecture with separate CLI/GUI components

🔄 Version 1.5.0
• Enhanced file scanning system
• Memory persistence improvements
• Build optimization features

🔄 Version 1.0.0
• Initial release
• Basic PyInstaller integration
• File scanning capabilities
    """)
    return True

def handle_scan_command():
    """Handle scan command"""
    try:
        # Parse scan type from arguments
        scan_type = None
        for i, arg in enumerate(sys.argv):
            if arg == '--scan' and i + 1 < len(sys.argv):
                scan_type = sys.argv[i + 1]
                break
        
        if not scan_type:
            print("❌ Please specify scan type")
            print("Available types: icons, config, python, data, templates, docs, help, splash, json, tutorials")
            return False
        
        print(f"🔍 Scanning for {scan_type} files...")
        
        # Delegate to core for actual scanning
        core = BuildToolCore()
        core = BuildToolCore()
        
        # Check for additional options
        append_mode = '--append' in sys.argv
        contains_filter = None
        scan_directory = None
        
        for i, arg in enumerate(sys.argv):
            if arg == '--contains' and i + 1 < len(sys.argv):
                contains_filter = sys.argv[i + 1]
            elif arg == '--scan-dir' and i + 1 < len(sys.argv):
                scan_directory = sys.argv[i + 1]
        
        results = core.handle_scan_command(scan_type, append_mode, scan_directory, contains_filter)
        print(f"✅ Scan completed - found {len(results)} files")
        return len(results) > 0
        
    except ImportError:
        print("❌ Core module required for scanning")
        return False
    except Exception as e:
        print(f"❌ Error during scan: {e}")
        return False

def handle_show_memory():
    """Show memory status"""
    try:
        memory = ConsoleMemory()
        memory = ConsoleMemory()
        
        # Check if detailed flag is present
        if '--detailed' in sys.argv:
            show_detailed_memory(memory)
        else:
            memory.show_memory_status()
        return True
    except ImportError:
        print("❌ Core module required for memory operations")
        return False
    except Exception as e:
        print(f"❌ Error showing memory: {e}")
        return False

def handle_detailed():
    """Handle detailed flag - can only be used with other commands"""
    print("❌ --detailed flag must be used with another command")
    print("💡 Usage: build_cli --show-memory --detailed")
    return False

def show_detailed_memory(memory):
    """Show comprehensive detailed memory information"""
    import platform
    from datetime import datetime
    
    print("🔍 DETAILED MEMORY ANALYSIS")
    print("=" * 80)
    
    # 1. Memory Overview
    print("\n📊 MEMORY OVERVIEW")
    print("-" * 40)
    if hasattr(memory, 'memory') and memory.memory:
        total_items = 0
        for key, value in memory.memory.items():
            if isinstance(value, dict):
                for subkey, subvalue in value.items():
                    if isinstance(subvalue, list):
                        total_items += len(subvalue)
            elif isinstance(value, list):
                total_items += len(value)
        
        print(f"📈 Total items in memory: {total_items}")
        print(f"📁 Memory sections: {len(memory.memory)}")
    else:
        print("❌ Memory is empty or not initialized")
        return
    
    # 2. Build Configuration Details
    print("\n🔧 BUILD CONFIGURATION")
    print("-" * 40)
    build_config = memory.memory.get('build_config', {})
    if build_config:
        for key, value in build_config.items():
            print(f"🔸 {key}: {value}")
        
        # Show computed build name
        build_name = build_config.get('name', 'Auto-generated')
        include_date = build_config.get('include_date', True)
        if build_name != 'Auto-generated' and include_date:
            from datetime import datetime
            date_str = datetime.now().strftime("%Y%m%d")
            final_name = f"{build_name}_{date_str}"
            print(f"🎯 Computed final name: {final_name}")
    else:
        print("❌ No build configuration found")
    
    # 3. Scan Results Details
    print("\n📁 SCAN RESULTS DETAILED BREAKDOWN")
    print("-" * 40)
    scan_results = memory.memory.get('scan_results', {})
    if scan_results:
        for file_type, files in scan_results.items():
            print(f"\n📂 {file_type.upper()} FILES ({len(files)} items):")
            if files:
                for i, file_path in enumerate(files, 1):
                    try:
                        # Get file info
                        if os.path.exists(file_path):
                            stat = os.stat(file_path)
                            size = stat.st_size
                            modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                            
                            # Format size
                            if size < 1024:
                                size_str = f"{size}B"
                            elif size < 1024**2:
                                size_str = f"{size/1024:.1f}KB"
                            elif size < 1024**3:
                                size_str = f"{size/(1024**2):.1f}MB"
                            else:
                                size_str = f"{size/(1024**3):.1f}GB"
                            
                            print(f"   {i:3d}. {os.path.basename(file_path)}")
                            print(f"        📍 Path: {file_path}")
                            print(f"        📏 Size: {size_str}")
                            print(f"        📅 Modified: {modified}")
                            
                            # Try to get additional file info
                            try:
                                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    first_lines = [f.readline().strip() for _ in range(3)]
                                    first_lines = [line for line in first_lines if line]
                                    if first_lines:
                                        print(f"        📝 Preview: {first_lines[0][:60]}{'...' if len(first_lines[0]) > 60 else ''}")
                            except:
                                pass
                            
                            print()
                        else:
                            print(f"   {i:3d}. {os.path.basename(file_path)} ❌ FILE NOT FOUND")
                            print(f"        📍 Path: {file_path}")
                            print()
                    except Exception as e:
                        print(f"   {i:3d}. {os.path.basename(file_path)} ❌ ERROR: {e}")
                        print()
            else:
                print("   (No files in this category)")
    else:
        print("❌ No scan results found")
    
    # 4. Project Analysis
    print("\n🏗️  PROJECT ANALYSIS")
    print("-" * 40)
    
    # Analyze current directory
    current_dir = os.getcwd()
    print(f"📍 Current working directory: {current_dir}")
    
    # Count files by type in current directory
    file_counts = {}
    total_size = 0
    try:
        for root, dirs, files in os.walk(current_dir):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    ext = os.path.splitext(file)[1].lower()
                    if not ext:
                        ext = '[no extension]'
                    file_counts[ext] = file_counts.get(ext, 0) + 1
                    total_size += os.path.getsize(file_path)
                except:
                    pass
        
        print(f"📊 Total files in project: {sum(file_counts.values())}")
        print(f"📏 Total project size: {total_size/(1024**2):.1f}MB")
        print(f"📂 File types found: {len(file_counts)}")
        
        # Show top file types
        sorted_types = sorted(file_counts.items(), key=lambda x: x[1], reverse=True)
        print("\n🔝 Top file types:")
        for ext, count in sorted_types[:10]:
            print(f"   {ext}: {count} files")
    except Exception as e:
        print(f"❌ Error analyzing project: {e}")
    
    # 5. Environment Information
    print("\n🌍 ENVIRONMENT INFORMATION")
    print("-" * 40)
    print(f"🐍 Python version: {sys.version.split()[0]}")
    print(f"💻 Platform: {platform.platform()}")
    print(f"🏠 Home directory: {os.path.expanduser('~')}")
    print(f"📂 Current directory: {os.getcwd()}")
    
    # Virtual environment info
    venv_config = build_config.get('virtual_env')
    if venv_config:
        print(f"🔧 Configured virtual env: {venv_config}")
        if os.path.exists(venv_config):
            print(f"✅ Virtual environment exists")
        else:
            print(f"❌ Virtual environment not found")
    
    # 6. Memory Storage Information
    print("\n💾 MEMORY STORAGE DETAILS")
    print("-" * 40)
    memory_file = getattr(memory, 'memory_file', 'build_console_memory.json')
    if os.path.exists(memory_file):
        stat = os.stat(memory_file)
        size = stat.st_size
        modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        print(f"📄 Memory file: {memory_file}")
        print(f"📏 File size: {size} bytes")
        print(f"📅 Last modified: {modified}")
    else:
        print(f"❌ Memory file not found: {memory_file}")
    
    # 7. Available Commands Summary
    print("\n⚡ AVAILABLE OPERATIONS")
    print("-" * 40)
    operations = [
        "🔍 --scan [type] - Scan for files",
        "➕ --add [files] - Add files to memory", 
        "🗑️ --remove - Remove from memory",
        "🗑️ --delete - Delete actual files",
        "🧹 --clear-memory - Clear all memory",
        "📤 --export - Export scan results",
        "🔧 --name [name] - Set build name",
        "📅 --date [true/false] - Include date",
        "🚀 --virtual [env] - Set virtual environment",
        "⚡ --activate - Activate environment"
    ]
    
    for op in operations:
        print(f"   {op}")
    
    print("\n" + "=" * 80)
    print("📋 Detailed analysis complete!")
    print("💡 Use individual commands for specific operations")
    print("=" * 80)

def handle_clear_memory():
    """Clear memory"""
    try:
        memory = ConsoleMemory()
        memory.clear_memory()
        print("🧹 All memory cleared successfully")
        return True
    except Exception as e:
        print(f"❌ Error clearing memory: {e}")
        return False

def handle_remove_command():
    """Handle remove command from CLI arguments"""
    try:
        # Parse command line arguments for remove operation
        args = sys.argv
        target = None
        remove_type = None
        
        # Look for --target argument
        try:
            target_idx = args.index('--target')
            if target_idx + 1 < len(args):
                target = args[target_idx + 1]
        except ValueError:
            pass
        
        # Look for --type argument
        try:
            type_idx = args.index('--type')
            if type_idx + 1 < len(args):
                remove_type = args[type_idx + 1]
        except ValueError:
            pass
        
        # Execute the remove command
        return execute_remove_command(target, remove_type)
        
    except Exception as e:
        print(f"❌ Error in remove command: {e}")
        return False

def handle_install_command():
    """Handle install command"""
    print("📦 Install Command")
    print("=" * 30)
    print("Install functionality coming soon!")
    print("For now, you can:")
    print("• pip install -r requirements.txt")
    print("• pip install pyinstaller pyqt6")
    return True

def handle_new_project():
    """Handle new project creation"""
    print("🆕 New Project Creation")
    print("=" * 30)
    print("Project creation functionality coming soon!")
    print("For now, manually create the optimal structure shown with --show-optimal")
    return True

def handle_build_name():
    """Handle setting build name"""
    try:
        # Parse the name from arguments
        build_name = None
        for i, arg in enumerate(sys.argv):
            if arg == '--name' and i + 1 < len(sys.argv):
                build_name = sys.argv[i + 1]
                break
        
        if not build_name:
            print("❌ Please specify a build name")
            print("Example: build_cli --name 'MyApplication'")
            return False
        
        print(f"🏷️  Build Name Configuration")
        print("=" * 40)
        
        # Store the build name in memory
        memory = ConsoleMemory()
        
        # Initialize build_config if it doesn't exist
        if 'build_config' not in memory.memory:
            memory.memory['build_config'] = {}
        
        memory.memory['build_config']['name'] = build_name
        memory.save_memory()
        
        print(f"✅ Build name set to: '{build_name}'")
        
        # Show current configuration
        show_build_config(memory)
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting build name: {e}")
        return False

def handle_build_date():
    """Handle setting build date configuration"""
    try:
        # Parse the date setting from arguments
        include_date = None
        for i, arg in enumerate(sys.argv):
            if arg == '--date' and i + 1 < len(sys.argv):
                date_value = sys.argv[i + 1].lower()
                if date_value in ['true', 't', 'yes', 'y', '1']:
                    include_date = True
                elif date_value in ['false', 'f', 'no', 'n', '0']:
                    include_date = False
                else:
                    print(f"❌ Invalid date value: '{sys.argv[i + 1]}'")
                    print("Valid values: true, false, yes, no, 1, 0")
                    return False
                break
        
        if include_date is None:
            print("❌ Please specify date setting")
            print("Example: build_cli --date true")
            print("Valid values: true, false, yes, no, 1, 0")
            return False
        
        print(f"📅 Build Date Configuration")
        print("=" * 40)
        
        # Store the date setting in memory
        memory = ConsoleMemory()
        
        # Initialize build_config if it doesn't exist
        if 'build_config' not in memory.memory:
            memory.memory['build_config'] = {}
        
        memory.memory['build_config']['include_date'] = include_date
        memory.save_memory()
        
        print(f"✅ Date inclusion set to: {include_date}")
        
        # Show current configuration
        show_build_config(memory)
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting build date: {e}")
        return False

def show_build_config(memory):
    """Show current build configuration"""
    config = memory.memory.get('build_config', {})
    
    print("\n🔧 Current Build Configuration:")
    print("─" * 35)
    
    # Get build name
    build_name = config.get('name', 'Auto-generated')
    include_date = config.get('include_date', True)
    
    print(f"📝 Build Name: {build_name}")
    print(f"📅 Include Date: {include_date}")
    
    # Generate preview of final build name
    if build_name != 'Auto-generated':
        if include_date:
            from datetime import datetime
            date_str = datetime.now().strftime("%Y%m%d")
            final_name = f"{build_name}_{date_str}"
        else:
            final_name = build_name
        
        print(f"🎯 Final Build Name: {final_name}")
    else:
        print("🎯 Final Build Name: Will be auto-generated based on project")
    
    print()
    print("💡 Tips:")
    print("   • Use --name to set custom build name")
    print("   • Use --date true/false to control date inclusion")
    print("   • Settings are saved and will be used for future builds")

def handle_download_cli():
    """Handle CLI module download"""
    print("📥 Downloading CLI Module...")
    print("=" * 40)
    
    try:
        import urllib.request
        import tempfile
        import shutil
        
        # Download the CLI module from GitHub
        repo_owner = "braydenanderson2014"
        repo_name = "SystemCommands"
        file_url = f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}/main/Build_Script/build_cli.py"
        
        print(f"📡 Downloading from: {file_url}")
        
        with tempfile.NamedTemporaryFile(mode='w+b', delete=False) as temp_file:
            with urllib.request.urlopen(file_url, timeout=30) as response:
                shutil.copyfileobj(response, temp_file)
            temp_path = temp_file.name
        
        # Move to current directory
        target_path = "build_cli_new.py"
        shutil.move(temp_path, target_path)
        
        print(f"✅ CLI module downloaded successfully to {target_path}")
        print("🔄 Replace your current CLI with the new version if desired")
        return True
        
    except Exception as e:
        print(f"❌ Error downloading CLI module: {e}")
        print("💡 Please check your internet connection and try again")
        return False

def handle_repo_status():
    """Handle repository status check without heavy imports"""
    try:
        import urllib.request
        import json
        
        print("📊 GitHub Repository Status Check")
        print("=" * 40)
        
        # Try to get repository info
        repo_owner = "braydenanderson2014"  # Default, should be configurable
        repo_name = "SystemCommands"
        api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
        
        try:
            with urllib.request.urlopen(api_url, timeout=10) as response:
                data = json.loads(response.read().decode())
                
            print(f"📂 Repository: {data['full_name']}")
            print(f"⭐ Stars: {data['stargazers_count']}")
            print(f"🍴 Forks: {data['forks_count']}")
            print(f"📅 Last Updated: {data['updated_at'][:10]}")
            print(f"🌐 URL: {data['html_url']}")
            print("✅ Repository is accessible")
            return True
            
        except Exception as e:
            print(f"❌ Error accessing repository: {e}")
            print("💡 Check your internet connection and repository configuration")
            return False
            
    except ImportError:
        print("❌ Required modules not available")
        return False

def handle_gui_command():
    """Handle GUI launch command - checks for GUI availability and launches it"""
    import subprocess
    import os
    import sys
    import time
    
    print("🎨 GUI Interface Launcher")
    print("=" * 30)
    
    # List of possible GUI module names in order of preference
    gui_candidates = [
        "build_gui_interface.py",
        "build_gui_core.py",
        "BuildTool_GUI.py",
        "build_gui.py",
        "gui_interface.py"
    ]
    
    gui_file = None
    
    # Check for GUI file in current directory
    for candidate in gui_candidates:
        if os.path.exists(candidate):
            gui_file = candidate
            print(f"✅ Found GUI module: {gui_file}")
            break
    
    if not gui_file:
        print("❌ GUI module not found!")
        print("\n💡 Available options:")
        print("   1. Download GUI module:")
        print("      python build_cli.py --download-gui")
        print("   2. Expected GUI filenames:")
        for candidate in gui_candidates:
            print(f"      • {candidate}")
        print("\n🏗️  Architecture:")
        print("   CLI (this file) = Core functionality + Console interface")
        print("   GUI (separate)  = Graphical interface that calls CLI")
        
        # Ask if user wants to download GUI now
        try:
            download = input("\n❓ Download GUI module now? (y/N): ").strip().lower()
            if download == 'y':
                return handle_download_gui()
            else:
                return False
        except (KeyboardInterrupt, EOFError):
            print("\n❌ Operation cancelled")
            return False
    
    # Determine the best Python executable to use
    python_executables = []
    
    # Try different Python executables in order of preference
    if os.name == 'nt':  # Windows
        # Prioritize official Python installations
        username = os.environ.get('USERNAME', 'User')
        candidates = [
            # Official Python installations (highest priority)
            f"C:\\Users\\{username}\\AppData\\Local\\Programs\\Python\\Python313\\python.exe",
            f"C:\\Users\\{username}\\AppData\\Local\\Programs\\Python\\Python312\\python.exe",
            f"C:\\Users\\{username}\\AppData\\Local\\Programs\\Python\\Python311\\python.exe",
            "py",  # Python Launcher (but we'll check what it points to)
            sys.executable,  # Current Python
            "python",
            "python3"
        ]
    else:  # Unix-like
        candidates = [
            sys.executable,  # Current Python
            "python3",
            "python"
        ]
    
    # Test each candidate
    for candidate in candidates:
        try:
            # Check if it's a direct path that exists
            if candidate.startswith('C:') and not os.path.exists(candidate):
                continue
            
            # Test if this Python executable works
            if candidate == "py":
                test_cmd = ["py", "--version"]
                pyqt_test_cmd = ["py", "-c", "import PyQt6; print('PyQt6 available')"]
                path_check_cmd = ["py", "-c", "import sys; print(sys.executable)"]
            else:
                test_cmd = [candidate, "--version"]
                pyqt_test_cmd = [candidate, "-c", "import PyQt6; print('PyQt6 available')"]
                path_check_cmd = [candidate, "-c", "import sys; print(sys.executable)"]
            
            # Test basic functionality
            result = subprocess.run(test_cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                # Check where this Python is actually located
                path_result = subprocess.run(path_check_cmd, capture_output=True, text=True, timeout=5)
                if path_result.returncode == 0:
                    python_path = path_result.stdout.strip()
                    # Skip MinGW64 Python installations
                    if ("msys64" in python_path.lower() or 
                        "mingw64" in python_path.lower()):
                        print(f"⚠️  Skipping MinGW64 Python: {candidate} -> {python_path}")
                        continue
                    
                    # Test PyQt6 availability
                    pyqt_result = subprocess.run(pyqt_test_cmd, capture_output=True, text=True, timeout=5)
                    has_pyqt = pyqt_result.returncode == 0
                
                # For py launcher, also test script execution vs -c execution
                script_executable = None
                if candidate == "py" and has_pyqt:
                    # Check if py launcher uses the same Python for scripts vs -c commands
                    script_py_result = subprocess.run(
                        ["py", "-c", "import sys; print(sys.executable)"], 
                        capture_output=True, text=True, timeout=5
                    )
                    if script_py_result.returncode == 0:
                        script_executable = script_py_result.stdout.strip()
                        print(f"   🔍 py launcher uses: {script_executable}")
                
                python_executables.append({
                    'cmd': candidate,
                    'version': result.stdout.strip(),
                    'working': True,
                    'has_pyqt': has_pyqt,
                    'pyqt_error': pyqt_result.stderr.strip() if not has_pyqt else None,
                    'python_path': python_path,
                    'script_executable': python_path if candidate != "py" else script_executable
                })
                
                status = "✅" if has_pyqt else "⚠️ "
                pyqt_status = "with PyQt6" if has_pyqt else "without PyQt6"
                print(f"{status} Found Python: {candidate} ({result.stdout.strip()}) {pyqt_status}")
            else:
                python_executables.append({
                    'cmd': candidate,
                    'error': result.stderr.strip(),
                    'working': False,
                    'has_pyqt': False
                })
        except Exception as e:
            python_executables.append({
                'cmd': candidate,
                'error': str(e),
                'working': False,
                'has_pyqt': False
            })
    
    # Prioritize Python with PyQt6, then fall back to any working Python
    working_python = None
    working_python_info = None
    
    # First, try to find Python with PyQt6
    for py_info in python_executables:
        if py_info.get('working') and py_info.get('has_pyqt'):
            working_python = py_info['cmd']
            working_python_info = py_info
            print(f"🎯 Selected Python with PyQt6: {working_python}")
            break
    
    # If no Python with PyQt6, use first working Python
    if not working_python:
        for py_info in python_executables:
            if py_info.get('working'):
                working_python = py_info['cmd']
                working_python_info = py_info
                print(f"⚠️  Selected Python without PyQt6: {working_python}")
                break
    
    if not working_python:
        print("❌ No working Python executable found!")
        print("💡 Available Python executables tested:")
        for py_info in python_executables:
            status = "✅" if py_info.get('working') else "❌"
            if py_info.get('working'):
                pyqt_status = " (with PyQt6)" if py_info.get('has_pyqt') else " (no PyQt6)"
                print(f"   {status} {py_info['cmd']}: {py_info.get('version', 'Unknown version')}{pyqt_status}")
            else:
                print(f"   {status} {py_info['cmd']}: {py_info.get('error', 'Unknown error')}")
        return False
    
    # Check if GUI file is a valid Python file
    try:
        with open(gui_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(1000)  # Read first 1KB
            if not any(keyword in content.lower() for keyword in ['import', 'def ', 'class ', 'python']):
                print(f"⚠️  Warning: {gui_file} may not be a Python file")
    except Exception as e:
        print(f"⚠️  Warning: Could not validate {gui_file}: {e}")
    
    # Launch the GUI using subprocess to avoid import issues
    try:
        print(f"🚀 Launching GUI: {gui_file}")
        print(f"🐍 Using Python: {working_python}")
        print("💡 GUI will run independently of this CLI process")
        
        # Prepare command
        if working_python == "py" and working_python_info.get('script_executable'):
            # Use direct Python path if py launcher is inconsistent
            direct_python = working_python_info['script_executable']
            cmd = [direct_python, gui_file]
            print(f"🔧 Using direct Python path due to py launcher inconsistency: {direct_python}")
        elif working_python == "py":
            cmd = ["py", gui_file]
        else:
            cmd = [working_python, gui_file]
        
        print(f"📝 Command: {' '.join(cmd)}")
        
        # Launch with error monitoring
        if os.name == 'nt':  # Windows
            # On Windows, use CREATE_NEW_PROCESS_GROUP to make GUI independent
            process = subprocess.Popen(
                cmd,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
        else:  # Unix-like systems
            process = subprocess.Popen(
                cmd,
                start_new_session=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
        
        print("⏳ Waiting for GUI to initialize...")
        
        # Wait a short time to check if the process starts successfully
        time.sleep(2)
        
        # Check if process is still running (good sign)
        if process.poll() is None:
            print("✅ GUI launched successfully!")
            print("📱 The graphical interface should be starting...")
            print("🔄 You can continue using this CLI independently")
            return True
        else:
            # Process exited quickly, likely an error
            stdout, stderr = process.communicate(timeout=5)
            print("❌ GUI failed to start!")
            print(f"🔍 Exit code: {process.returncode}")
            
            if stderr:
                print("📋 Error output:")
                # Show first few lines of error
                error_lines = stderr.strip().split('\n')[:5]
                for line in error_lines:
                    print(f"   {line}")
                if len(stderr.split('\n')) > 5:
                    print("   ... (more errors in full output)")
                
                # Check for common issues
                if "ModuleNotFoundError" in stderr and "PyQt" in stderr:
                    print("\n💡 Solution: Install PyQt6")
                    print(f"   {working_python} -m pip install PyQt6")
                elif "ModuleNotFoundError" in stderr:
                    print("\n💡 Missing dependencies detected")
                    print("   Check the error above for required modules")
                elif "Permission" in stderr:
                    print("\n💡 Permission issue detected")
                    print("   Try running as administrator")
            
            if stdout:
                print("📄 Standard output:")
                stdout_lines = stdout.strip().split('\n')[:3]
                for line in stdout_lines:
                    print(f"   {line}")
            
            # Offer to install missing dependencies
            if "ModuleNotFoundError" in stderr and "PyQt" in stderr:
                try:
                    if working_python_info and working_python_info.get('has_pyqt'):
                        print("\n🤔 Strange: PyQt6 should be available but GUI still failed")
                        print("💡 This might be a different issue than missing PyQt6")
                        return False
                    
                    install = input("\n❓ Install PyQt6 now? (y/N): ").strip().lower()
                    if install == 'y':
                        print(f"\n📦 Installing PyQt6 using {working_python}...")
                        if working_python == "py":
                            install_cmd = ["py", "-m", "pip", "install", "PyQt6"]
                        else:
                            install_cmd = [working_python, "-m", "pip", "install", "PyQt6"]
                        
                        print(f"📝 Install command: {' '.join(install_cmd)}")
                        install_result = subprocess.run(install_cmd, capture_output=True, text=True, timeout=120)
                        
                        if install_result.returncode == 0:
                            print("✅ PyQt6 installed successfully!")
                            
                            # Try to launch GUI again
                            print("🔄 Attempting to launch GUI again...")
                            retry_process = subprocess.Popen(
                                cmd,
                                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True,
                                start_new_session=False if os.name == 'nt' else True
                            )
                            
                            time.sleep(3)  # Wait longer for retry
                            
                            if retry_process.poll() is None:
                                print("✅ GUI launched successfully after installing PyQt6!")
                                return True
                            else:
                                retry_stdout, retry_stderr = retry_process.communicate(timeout=5)
                                print("❌ GUI still failed to start after installing PyQt6")
                                if retry_stderr:
                                    print("📋 New error:")
                                    for line in retry_stderr.strip().split('\n')[:3]:
                                        print(f"   {line}")
                                return False
                        else:
                            print(f"❌ Installation failed:")
                            if install_result.stderr:
                                for line in install_result.stderr.strip().split('\n')[:3]:
                                    print(f"   {line}")
                            
                            # Check if it's a pip issue and suggest alternatives
                            if "No module named pip" in install_result.stderr:
                                print(f"\n💡 Pip not available in {working_python}")
                                print("🔄 Trying alternative Python with PyQt6...")
                                
                                # Try to find another Python with PyQt6
                                for py_info in python_executables:
                                    if (py_info.get('working') and py_info.get('has_pyqt') and 
                                        py_info['cmd'] != working_python):
                                        alt_python = py_info['cmd']
                                        print(f"🎯 Found alternative: {alt_python}")
                                        
                                        # Try with alternative Python
                                        alt_cmd = [alt_python, gui_file] if alt_python != "py" else ["py", gui_file]
                                        print(f"📝 Trying with: {' '.join(alt_cmd)}")
                                        
                                        alt_process = subprocess.Popen(
                                            alt_cmd,
                                            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0,
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE,
                                            text=True,
                                            start_new_session=False if os.name == 'nt' else True
                                        )
                                        
                                        time.sleep(3)
                                        
                                        if alt_process.poll() is None:
                                            print(f"✅ GUI launched successfully with {alt_python}!")
                                            return True
                                        else:
                                            print(f"❌ {alt_python} also failed")
                                            continue
                                
                                print("\n💡 Manual installation suggestions:")
                                for py_info in python_executables:
                                    if py_info.get('working') and not py_info.get('has_pyqt'):
                                        cmd = py_info['cmd']
                                        if cmd == "py":
                                            print(f"   py -m pip install PyQt6")
                                        else:
                                            print(f"   {cmd} -m pip install PyQt6")
                            else:
                                print(f"\n💡 Try manually:")
                                print(f"   {working_python} -m pip install --upgrade pip")
                                print(f"   {working_python} -m pip install PyQt6")
                            return False
                except (KeyboardInterrupt, EOFError):
                    print("\n❌ Installation cancelled")
            
            return False
        
    except subprocess.TimeoutExpired:
        print("⏳ GUI is taking longer than expected to start...")
        print("💡 Check if the GUI window appeared")
        return True
    except FileNotFoundError:
        print(f"❌ Python executable not found: {working_python}")
        print(f"💡 Try manually: python {gui_file}")
        return False
    except Exception as e:
        print(f"❌ Error launching GUI: {e}")
        print(f"💡 Try manually: {working_python} {gui_file}")
        return False

def handle_download_gui():
    """Handle GUI module download from GitHub repository"""
    print("📥 GUI Module Download")
    print("=" * 40)
    
    try:
        import urllib.request
        import urllib.error
        
        # Configuration
        repo_owner = "braydenanderson2014"
        repo_name = "SystemCommands"
        gui_filename = "build_gui_interface.py"
        branch = "main"
        
        # GitHub raw file URL
        file_url = f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}/{branch}/Build_Script/{gui_filename}"
        
        print(f"🌐 Repository: {repo_owner}/{repo_name}")
        print(f"📂 Branch: {branch}")
        print(f"📄 Target File: {gui_filename}")
        print(f"🔗 URL: {file_url}")
        
        # Check if file already exists
        if os.path.exists(gui_filename):
            print(f"\n⚠️  File '{gui_filename}' already exists!")
            response = input("Do you want to overwrite it? (y/N): ").strip().lower()
            if response != 'y':
                print("❌ Download cancelled")
                return False
        
        print(f"\n📥 Downloading {gui_filename}...")
        
        try:
            # Download the file
            with urllib.request.urlopen(file_url, timeout=30) as response:
                if response.status == 200:
                    content = response.read()
                    
                    # Write to local file
                    with open(gui_filename, 'wb') as f:
                        f.write(content)
                    
                    file_size = len(content)
                    print(f"✅ Successfully downloaded {gui_filename}")
                    print(f"📏 File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
                    
                    # Make executable on Unix-like systems
                    if hasattr(os, 'chmod'):
                        os.chmod(gui_filename, 0o755)
                        print("🔧 Made file executable")
                    
                    print(f"\n🎯 Usage:")
                    print(f"   python {gui_filename}")
                    print(f"   # or")
                    print(f"   python build_cli.py --gui (if supported)")
                    
                    print(f"\n🏗️  Architecture:")
                    print("   CLI (this file) = Core functionality + Console interface")
                    print("   GUI (downloaded)  = Graphical interface that calls CLI core")
                    
                    return True
                else:
                    print(f"❌ HTTP Error {response.status}: Failed to download file")
                    return False
                    
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print("❌ File not found on GitHub")
                print("💡 Check if the file exists in the repository:")
                print(f"   {file_url}")
            else:
                print(f"❌ HTTP Error {e.code}: {e.reason}")
            return False
            
        except urllib.error.URLError as e:
            print(f"❌ Network Error: {e.reason}")
            print("💡 Check your internet connection")
            return False
            
    except ImportError:
        print("❌ Required modules (urllib) not available")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def handle_update():
    """Handle update check and download"""
    print("🔄 Checking for Updates...")
    print("=" * 30)
    
    try:
        import urllib.request
        import json
        
        repo_owner = "braydenanderson2014"
        repo_name = "SystemCommands"
        api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
        
        print(f"📡 Checking: {api_url}")
        
        with urllib.request.urlopen(api_url, timeout=10) as response:
            data = json.loads(response.read().decode())
        
        latest_version = data['tag_name']
        current_version = "2.0.0-modular"
        
        print(f"📦 Current Version: {current_version}")
        print(f"🆕 Latest Version: {latest_version}")
        
        if latest_version == current_version:
            print("✅ You have the latest version!")
        else:
            print("🚀 New version available!")
            print(f"📋 Release Notes: {data.get('body', 'No release notes available')}")
            print(f"🔗 Download: {data['html_url']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking for updates: {e}")
        return False

def handle_main_file_command():
    """Handle --main file specification command"""
    try:
        # Parse the main file from arguments
        main_file = None
        auto_analyze = False
        
        for i, arg in enumerate(sys.argv):
            if arg == '--main' and i + 1 < len(sys.argv):
                main_file = sys.argv[i + 1]
                break
            elif arg == '--main' and '--auto' in sys.argv:
                auto_analyze = True
                break
        
        # Route to command queue system for proper handling
        if auto_analyze:
            return execute_auto_command(analyze_main=True)
        elif main_file:
            return execute_main_command(main_file, False)
        else:
            print("❌ Please specify main file or use --auto")
            print("Examples:")
            print("   build_cli --main main.py")
            print("   build_cli --main --auto")
            return False
            
    except Exception as e:
        print(f"❌ Error in main file command: {e}")
        return False

def handle_auto_command():
    """Handle --auto command"""
    try:
        # Route to command queue system for proper handling
        return execute_auto_command(analyze_main=True)
        
    except Exception as e:
        print(f"❌ Error in auto command: {e}")
        return False

def handle_add_command():
    """Handle --add command"""
    try:
        # Parse files from arguments
        files = []
        start_collecting = False
        
        for arg in sys.argv[1:]:
            if arg == '--add':
                start_collecting = True
                continue
            elif arg.startswith('--'):
                break  # Stop at next flag
            elif start_collecting:
                files.append(arg)
        
        if not files:
            print("❌ Please specify files to add")
            print("Example: build_cli --add file1.py file2.json")
            return False
            
        # Route to command queue system
        return execute_add_command(files)
        
    except Exception as e:
        print(f"❌ Error in add command: {e}")
        return False

def handle_set_version_command():
    """Handle --set-version command"""
    try:
        # Parse version from arguments
        version = None
        for i, arg in enumerate(sys.argv):
            if arg == '--set-version' and i + 1 < len(sys.argv):
                version = sys.argv[i + 1]
                break
        
        if not version:
            print("❌ Please specify version")
            print("Example: build_cli --set-version 1.0.0")
            return False
            
        # Route to command queue system
        return execute_set_version_command(version)
        
    except Exception as e:
        print(f"❌ Error in set-version command: {e}")
        return False

def handle_add_to_path_command():
    """Handle --add-to-path command"""
    try:
        # Route to command queue system
        return execute_add_to_path_command()
        
    except Exception as e:
        print(f"❌ Error in add-to-path command: {e}")
        return False

def handle_setup_sdk_command():
    """Handle --setup-sdk command"""
    try:
        print("🔧 Setting up Windows SDK PATH...")
        core = BuildToolCore()
        return core.setup_windows_sdk_path()
        
    except Exception as e:
        print(f"❌ Error in setup-sdk command: {e}")
        return False

def handle_collect_command():
    """Handle --collect command"""
    try:
        print("📦 Collecting files for packaging...")
        core = BuildToolCore()
        return core.collect_packaging_files()
        
    except Exception as e:
        print(f"❌ Error in collect command: {e}")
        return False

def handle_import_command():
    """Handle --import command"""
    try:
        # Get the import file path from arguments
        import_file = None
        for i, arg in enumerate(sys.argv):
            if arg == '--import' and i + 1 < len(sys.argv):
                import_file = sys.argv[i + 1]
                break
        
        if not import_file:
            print("❌ Please specify a file to import: --import <file>")
            print("💡 Supported formats: .json, .xml, .spec")
            return False
        
        print(f"📥 Importing configuration from: {import_file}")
        core = BuildToolCore()
        return core.import_configuration(import_file)
        
    except Exception as e:
        print(f"❌ Error in import command: {e}")
        return False

def handle_export_command():
    """Handle --export command"""
    try:
        # Get the export file path from arguments
        export_file = None
        for i, arg in enumerate(sys.argv):
            if arg == '--export' and i + 1 < len(sys.argv):
                export_file = sys.argv[i + 1]
                break
        
        if not export_file:
            print("❌ Please specify a file to export: --export <file>")
            print("💡 Supported formats: .json, .xml, .spec")
            return False
        
        print(f"📤 Exporting configuration to: {export_file}")
        core = BuildToolCore()
        return core.export_configuration(export_file)
        
    except Exception as e:
        print(f"❌ Error in export command: {e}")
        return False

def handle_no_version_append_command():
    """Handle --no-version-append command"""
    try:
        # Parse the value from arguments
        value = None
        for i, arg in enumerate(sys.argv):
            if arg == '--no-version-append' and i + 1 < len(sys.argv):
                value = sys.argv[i + 1]
                break
        
        if not value:
            print("❌ Please specify true/false for --no-version-append")
            print("Example: build_cli --no-version-append true")
            return False
        
        # Convert to boolean
        enable_no_version = value.lower() in ['true', 'yes', '1', 'on']
        
        return execute_no_version_append_command(enable_no_version)
        
    except Exception as e:
        print(f"❌ Error in no-version-append command: {e}")
        return False

# New command handlers
def handle_downgrade():
    """Handle version downgrade command"""
    try:
        # Parse the version from arguments
        version = None
        for i, arg in enumerate(sys.argv):
            if arg == '--downgrade' and i + 1 < len(sys.argv):
                version = sys.argv[i + 1]
                break
        
        if not version:
            print("❌ Please specify version to downgrade to")
            print("Example: build_cli --downgrade 3.8")
            return False
        
        print(f"⬇️  Version Downgrade Configuration")
        print("=" * 40)
        
        # Store the downgrade version
        memory = ConsoleMemory()
        memory = ConsoleMemory()
        
        if 'build_config' not in memory.memory:
            memory.memory['build_config'] = {}
        
        memory.memory['build_config']['downgrade_version'] = version
        memory.save_memory()
        
        print(f"✅ Downgrade version set to: '{version}'")
        print("💡 This will be used for dependency management during build")
        
        return True
        
    except ImportError:
        print("❌ Core module required for version management")
        return False
    except Exception as e:
        print(f"❌ Error setting downgrade version: {e}")
        return False

def handle_preview_name():
    """Handle preview name command"""
    try:
        memory = ConsoleMemory()
        memory = ConsoleMemory()
        
        config = memory.memory.get('build_config', {})
        build_name = config.get('name', 'Auto-generated')
        include_date = config.get('include_date', True)
        
        print("🎯 Build Name Preview:")
        print("=" * 25)
        
        if build_name == 'Auto-generated':
            print("📝 Base Name: [Auto-detected from project]")
            if include_date:
                from datetime import datetime
                date_str = datetime.now().strftime("%Y%m%d")
                print(f"📅 With Date: [ProjectName]_{date_str}")
            else:
                print("📅 Without Date: [ProjectName]")
        else:
            print(f"📝 Base Name: {build_name}")
            if include_date:
                from datetime import datetime
                date_str = datetime.now().strftime("%Y%m%d")
                final_name = f"{build_name}_{date_str}"
                print(f"📅 With Date: {final_name}")
            else:
                print(f"📅 Without Date: {build_name}")
        
        print("\n💡 The final executable will be named accordingly")
        return True
        
    except ImportError:
        print("❌ Core module required for name preview")
        return False
    except Exception as e:
        print(f"❌ Error showing name preview: {e}")
        return False

def handle_virtual_env():
    """Handle virtual environment command"""
    try:
        import subprocess
        import platform
        
        # Parse the environment name from arguments
        env_name = None
        for i, arg in enumerate(sys.argv):
            if arg == '--virtual' and i + 1 < len(sys.argv):
                env_name = sys.argv[i + 1]
                break
        
        if not env_name:
            print("❌ Please specify virtual environment name")
            print("Example: build_cli --virtual myenv")
            return False
        
        print(f"🔧 Virtual Environment Configuration")
        print("=" * 40)
        
        # Store the virtual environment name
        memory = ConsoleMemory()
        memory = ConsoleMemory()
        
        if 'build_config' not in memory.memory:
            memory.memory['build_config'] = {}
        
        memory.memory['build_config']['virtual_env'] = env_name
        memory.save_memory()
        
        print(f"🎯 Virtual Environment: '{env_name}'")
        
        # Check if environment exists, create if it doesn't
        if not os.path.exists(env_name):
            print(f"📁 Environment '{env_name}' not found. Creating...")
            try:
                # Create virtual environment
                result = subprocess.run([
                    sys.executable, '-m', 'venv', env_name
                ], capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0:
                    print(f"✅ Virtual environment '{env_name}' created successfully!")
                else:
                    print(f"❌ Failed to create virtual environment:")
                    print(f"   Error: {result.stderr}")
                    return False
                    
            except subprocess.TimeoutExpired:
                print("❌ Timeout creating virtual environment")
                return False
            except Exception as e:
                print(f"❌ Error creating virtual environment: {e}")
                return False
        else:
            print(f"✅ Virtual environment '{env_name}' already exists")
        
        # Show activation instructions
        if platform.system() == "Windows":
            activate_script = f"{env_name}\\Scripts\\activate.bat"
            print(f"💡 To activate: {activate_script}")
            print(f"📋 Or in PowerShell: {env_name}\\Scripts\\Activate.ps1")
        else:
            activate_script = f"{env_name}/bin/activate"
            print(f"💡 To activate: source {activate_script}")
        
        return True
        
    except ImportError:
        print("❌ Core module required for virtual environment configuration")
        return False
    except Exception as e:
        print(f"❌ Error setting virtual environment: {e}")
        return False

def handle_activate_env():
    """Handle virtual environment activation command"""
    try:
        # Parse optional environment name from arguments
        specified_env = None
        for i, arg in enumerate(sys.argv):
            if arg == '--activate' and i + 1 < len(sys.argv):
                # Check if next arg is an environment name (not another command)
                if not sys.argv[i + 1].startswith('--'):
                    specified_env = sys.argv[i + 1]
                break
        
        print(f"🚀 Virtual Environment Activation")
        print("=" * 40)
        
        # Use enhanced activation function
        return execute_activate_command_enhanced(specified_env)
        
    except Exception as e:
        print(f"❌ Error activating virtual environment: {e}")
        return False

def scan_directory_for_dependencies(directory="."):
    """Recursively scan directory for Python files and analyze dependencies."""
    import os
    import re
    
    print(f"🔍 Recursively scanning directory: {directory}")
    
    all_imports = set()
    py_files = []
    
    # Skip these directories completely
    skip_dirs = {
        '__pycache__', 'node_modules', '.git', '.svn', '.hg',
        'venv', 'env', 'virtualenv', '.venv', '.env',
        'build', 'dist', '.pytest_cache', '.coverage',
        'site-packages', 'Lib', 'lib', 'lib64',
        '.tox', '.mypy_cache', 'htmlcov', 'test_install'
    }
    
    # Find all Python files recursively, but limit to project files only
    for root, dirs, files in os.walk(directory):
        # Filter out unwanted directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in skip_dirs and not d.endswith('Script')]
        
        # Skip if we're in a virtual environment or package directory
        if any(skip_dir in root for skip_dir in skip_dirs):
            continue
        
        for file in files:
            if file.endswith('.py') and not file.startswith('.'):
                file_path = os.path.join(root, file)
                # Only include files that are likely part of the actual project
                if not any(skip_dir in file_path for skip_dir in skip_dirs):
                    py_files.append(file_path)
    
    print(f"📂 Found {len(py_files)} Python files to analyze")
    
    if not py_files:
        print("⚠️  No Python files found")
        return []
    
    # Analyze each Python file
    for py_file in py_files:
        try:
            file_imports = analyze_single_file_dependencies(py_file)
            all_imports.update(file_imports)
        except Exception as e:
            print(f"⚠️  Error analyzing {py_file}: {e}")
    
    return list(all_imports)

def analyze_project_dependencies(project_file):
    """Analyze a Python project file to detect required packages."""
    import re
    import os
    
    if not os.path.exists(project_file):
        print(f"⚠️  Project file not found: {project_file}")
        return []
    
    return analyze_single_file_dependencies(project_file)

def analyze_single_file_dependencies(file_path):
    """Analyze a single Python file to detect required packages."""
    import re
    import os
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
    except Exception as e:
        print(f"⚠️  Error reading file {file_path}: {e}")
        return []
    
    # Common import to package mappings
    import_to_package = {
        'cv2': 'opencv-python',
        'PIL': 'Pillow',
        'sklearn': 'scikit-learn',
        'yaml': 'PyYAML',
        'bs4': 'beautifulsoup4',
        'requests': 'requests',
        'numpy': 'numpy',
        'pandas': 'pandas',
        'matplotlib': 'matplotlib',
        'seaborn': 'seaborn',
        'tensorflow': 'tensorflow',
        'torch': 'torch',
        'flask': 'Flask',
        'django': 'Django',
        'fastapi': 'fastapi',
        'streamlit': 'streamlit',
        'plotly': 'plotly',
        'dash': 'dash',
        'scipy': 'scipy',
        'PyQt6': 'PyQt6',
        'PyQt5': 'PyQt5',
        'psutil': 'psutil',
        'selenium': 'selenium',
        'lxml': 'lxml',
        'openpyxl': 'openpyxl',
        'xlsxwriter': 'xlsxwriter',
    }
    
    # Built-in modules that don't need installation
    builtin_modules = {
        'tkinter', 'sqlite3', 'json', 'os', 'sys', 'datetime', 'time', 'math', 're', 
        'subprocess', 'pathlib', 'collections', 'itertools', 'functools', 'operator', 
        'copy', 'pickle', 'base64', 'hashlib', 'hmac', 'secrets', 'uuid', 'random', 
        'statistics', 'decimal', 'fractions', 'numbers', 'cmath', 'string', 'textwrap', 
        'unicodedata', 'stringprep', 'readline', 'rlcompleter', 'threading', 'multiprocessing',
        'queue', 'sched', 'mutex', 'tempfile', 'shutil', 'glob', 'fnmatch', 'linecache',
        'fileinput', 'filecmp', 'tempfile', 'csv', 'configparser', 'netrc', 'xdrlib',
        'plistlib', 'calendar', 'collections', 'heapq', 'bisect', 'array', 'weakref',
        'types', 'contextlib', 'abc', 'atexit', 'traceback', 'gc', 'inspect', 'site',
        'user', 'builtins', 'warnings', 'dataclasses', 'enum', 'graphlib', 'typing',
        'socket', 'ssl', 'select', 'selectors', 'asyncio', 'asyncore', 'asynchat',
        'signal', 'mmap', 'codecs', 'locale', 'gettext', 'logging', 'getpass', 'curses',
        'platform', 'errno', 'ctypes', 'io', 'argparse', 'optparse', 'getopt', 'urllib',
        'http', 'ftplib', 'poplib', 'imaplib', 'smtplib', 'socketserver', 'xmlrpc',
        'email', 'mailcap', 'mailbox', 'mimetypes', 'encodings', 'html', 'xml', 'webbrowser'
    }
    
    # Improved regex patterns for import detection
    import_patterns = [
        # Standard imports: import module_name
        r'^\s*import\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        # From imports: from module_name import something
        r'^\s*from\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+import',
    ]
    
    found_imports = set()
    lines = content.split('\n')
    
    for line in lines:
        # Skip comments and docstrings
        line = line.strip()
        if line.startswith('#') or line.startswith('"""') or line.startswith("'''"):
            continue
            
        for pattern in import_patterns:
            matches = re.findall(pattern, line, re.MULTILINE)
            found_imports.update(matches)
    
    # Map imports to packages, filtering out built-ins and local modules
    required_packages = set()
    for import_name in found_imports:
        # Skip built-in modules
        if import_name in builtin_modules:
            continue
            
        # Skip private/internal modules
        if import_name.startswith('_'):
            continue
            
        # Skip local project modules (assume they start with current project name or build_)
        file_name = os.path.splitext(os.path.basename(file_path))[0]
        if import_name.startswith(file_name) or import_name.startswith('build_'):
            continue
            
        # Map known imports to their package names
        if import_name in import_to_package:
            required_packages.add(import_to_package[import_name])
        else:
            # For unknown imports, only add if they look like real package names
            # (contain common package patterns)
            if (len(import_name) > 2 and 
                not import_name.lower() in ['main', 'test', 'tests', 'src', 'lib', 'utils', 'config', 'settings'] and
                not any(word in import_name.lower() for word in ['test', 'mock', 'fake', 'dummy'])):
                required_packages.add(import_name)
    
    return sorted(list(required_packages))

def install_package_with_retry(package, pip_cmd, max_retries=3, timeout=120):
    """Install a package with retry mechanism for timeout scenarios."""
    import subprocess
    import time
    
    for attempt in range(max_retries):
        try:
            print(f"   Installing {package}... (attempt {attempt + 1}/{max_retries})")
            result = subprocess.run([pip_cmd, "install", package], 
                                  capture_output=True, text=True, timeout=timeout)
            
            if result.returncode == 0:
                print(f"   ✅ {package} installed successfully")
                return True, "success"
            else:
                print(f"   ⚠️  {package} installation failed: {result.stderr.strip()}")
                return False, "failed"
                
        except subprocess.TimeoutExpired:
            print(f"   ⚠ Timeout installing {package} (attempt {attempt + 1}) - checking with pip list...")
            
            # Check if package was actually installed despite timeout
            if verify_package_installed(package, pip_cmd):
                print(f"   ✅ {package} was successfully installed (verified with pip list)")
                return True, "timeout_success"
            
            # If not the last attempt, wait and try again
            if attempt < max_retries - 1:
                print(f"   🔄 Package not found, retrying in 5 seconds...")
                time.sleep(5)
                continue
            else:
                print(f"   ❌ {package} installation failed after {max_retries} attempts")
                return False, "timeout_failed"
                
        except Exception as e:
            print(f"   ❌ Error installing {package}: {e}")
            if attempt < max_retries - 1:
                print(f"   🔄 Retrying in 3 seconds...")
                time.sleep(3)
                continue
            else:
                return False, "error"
    
    return False, "max_retries_exceeded"

def verify_package_installed(package_name, pip_cmd="pip"):
    """Verify if a package is installed using pip list."""
    try:
        import subprocess
        result = subprocess.run([pip_cmd, "list"], capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            installed_packages = result.stdout.lower()
            return package_name.lower() in installed_packages
        return False
    except Exception:
        return False

def handle_install_needed(project_file=None):
    """Handle install needed packages command"""
    try:
        import subprocess
        import platform
        memory = ConsoleMemory()
        
        memory = ConsoleMemory()
        config = memory.memory.get('build_config', {})
        env_name = config.get('virtual_env')
        
        print("📦 Install Needed Packages")
        print("=" * 30)
        
        # Determine pip command
        if env_name and os.path.exists(env_name):
            if platform.system() == "Windows":
                pip_cmd = f"{env_name}\\Scripts\\pip.exe"
            else:
                pip_cmd = f"{env_name}/bin/pip"
            print(f"🔧 Target Environment: {env_name}")
        else:
            pip_cmd = "pip"
            print("🔧 Target Environment: System Python")
        
        # Check if pip exists
        try:
            result = subprocess.run([pip_cmd, "--version"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                print(f"❌ Pip not found at: {pip_cmd}")
                return False
        except Exception as e:
            print(f"❌ Error checking pip: {e}")
            return False
        
        packages_installed = []
        
        # Intelligent package detection if project file is provided
        if project_file:
            print(f"🔍 Analyzing project file: {project_file}")
            required_packages = analyze_project_dependencies(project_file)
        else:
            print("� No project file specified - scanning all Python files recursively...")
            required_packages = scan_directory_for_dependencies()
            
        if required_packages:
            print(f"📋 Found {len(required_packages)} required packages: {', '.join(required_packages)}")
            
            for package in required_packages:
                success, status = install_package_with_retry(package, pip_cmd)
                if success:
                    packages_installed.append(package)
        else:
            print("📋 No additional packages detected from analysis")
        
        # Also check for requirements.txt and install if it exists
        if os.path.exists('requirements.txt'):
            print("📋 Found requirements.txt - installing packages...")
            try:
                result = subprocess.run([
                    pip_cmd, "install", "-r", "requirements.txt"
                ], capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    print("✅ Successfully installed packages from requirements.txt")
                    packages_installed.append("requirements.txt packages")
                else:
                    print("❌ Failed to install from requirements.txt:")
                    print(f"   Error: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                print("❌ Timeout installing packages")
            except Exception as e:
                print(f"❌ Error installing packages: {e}")
        
        # If no packages were found through intelligent detection AND no requirements.txt, install common packages
        if not required_packages and not os.path.exists('requirements.txt'):
            print("📋 No specific packages detected - installing common PyInstaller packages...")
            
            common_packages = [
                "pyinstaller",
                "pyqt6", 
                "requests",
                "pillow"
            ]
            
            for package in common_packages:
                success, status = install_package_with_retry(package, pip_cmd)
                if success:
                    packages_installed.append(package)
        
        # Show summary
        if packages_installed:
            print(f"\n📊 Installation Summary:")
            print(f"   ✅ Successfully installed: {len(packages_installed)} items")
            for item in packages_installed:
                print(f"      • {item}")
        else:
            print("\n⚠️  No packages were installed")
        
        # List installed packages
        print("\n📋 Checking installed packages...")
        try:
            result = subprocess.run([
                pip_cmd, "list", "--format=columns"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 2:  # Header lines
                    print(f"📦 Found {len(lines) - 2} installed packages in environment")
                    
                    # Show relevant packages
                    relevant = ['pyinstaller', 'pyqt6', 'requests', 'pillow', 'numpy', 'pandas']
                    found_relevant = []
                    for line in lines[2:]:  # Skip headers
                        package_name = line.split()[0].lower()
                        if any(rel in package_name for rel in relevant):
                            found_relevant.append(line)
                    
                    if found_relevant:
                        print("🎯 Relevant packages found:")
                        for pkg in found_relevant:
                            print(f"   • {pkg}")
                else:
                    print("📦 No packages found")
                    
        except Exception as e:
            print(f"⚠️  Could not list packages: {e}")
        
        return True
        
    except ImportError:
        print("❌ Core module required for package installation")
        return False
    except Exception as e:
        print(f"❌ Error with install needed: {e}")
        return False

def handle_location():
    """Handle location specification command"""
    try:
        # Parse the location from arguments
        location = None
        for i, arg in enumerate(sys.argv):
            if arg == '--location' and i + 1 < len(sys.argv):
                location = sys.argv[i + 1]
                break
        
        if not location:
            print("❌ Please specify location path")
            print("Example: build_cli --location /path/to/project")
            return False
        
        print(f"📍 Location Configuration")
        print("=" * 30)
        
        # Store the location
        memory = ConsoleMemory()
        memory = ConsoleMemory()
        
        if 'build_config' not in memory.memory:
            memory.memory['build_config'] = {}
        
        memory.memory['build_config']['location'] = location
        memory.save_memory()
        
        print(f"✅ Location set to: '{location}'")
        
        # Check if location exists
        if os.path.exists(location):
            print(f"📁 Location exists and is accessible")
        else:
            print(f"⚠️  Location does not exist: {location}")
            print("💡 It will be created when needed")
        
        return True
        
    except ImportError:
        print("❌ Core module required for location configuration")
        return False
    except Exception as e:
        print(f"❌ Error setting location: {e}")
        return False

def handle_scan_project():
    """Handle scan project command"""
    try:
        print("🔍 Scanning Project Structure")
        print("=" * 35)
        
        core = BuildToolCore()
        core = BuildToolCore()
        
        # Perform comprehensive project scan
        results = core.handle_scan_command('project')
        
        print(f"✅ Project scan completed")
        print(f"📊 Found {len(results)} files total")
        
        # Show breakdown by file types
        extensions = {}
        for file_path in results:
            ext = os.path.splitext(file_path)[1].lower()
            if not ext:
                ext = '[no extension]'
            extensions[ext] = extensions.get(ext, 0) + 1
        
        print("\n📋 File Type Breakdown:")
        for ext, count in sorted(extensions.items(), key=lambda x: x[1], reverse=True):
            print(f"   {ext}: {count} files")
        
        return True
        
    except ImportError:
        print("❌ Core module required for project scanning")
        return False
    except Exception as e:
        print(f"❌ Error scanning project: {e}")
        return False

def handle_target():
    """Handle target specification command"""
    try:
        # Parse the target from arguments
        target = None
        for i, arg in enumerate(sys.argv):
            if arg == '--target' and i + 1 < len(sys.argv):
                target = sys.argv[i + 1]
                break
        
        if not target:
            print("❌ Please specify target")
            print("Example: build_cli --target main.py")
            return False
        
        print(f"🎯 Build Target Configuration")
        print("=" * 35)
        
        # Store the target
        memory = ConsoleMemory()
        memory = ConsoleMemory()
        
        if 'build_config' not in memory.memory:
            memory.memory['build_config'] = {}
        
        memory.memory['build_config']['target'] = target
        memory.save_memory()
        
        print(f"✅ Build target set to: '{target}'")
        
        # Check if target exists
        if os.path.exists(target):
            print(f"📁 Target file exists and is accessible")
        else:
            print(f"⚠️  Target file not found: {target}")
        
        return True
        
    except ImportError:
        print("❌ Core module required for target configuration")
        return False
    except Exception as e:
        print(f"❌ Error setting target: {e}")
        return False

def handle_set_root():
    """Handle set root directory command"""
    try:
        # Parse the root path from arguments
        root_path = None
        for i, arg in enumerate(sys.argv):
            if arg == '--set-root' and i + 1 < len(sys.argv):
                root_path = sys.argv[i + 1]
                break
        
        if not root_path:
            print("❌ Please specify root directory path")
            print("Example: build_cli --set-root /path/to/project/root")
            print("         build_cli --set-root ..")
            print("         build_cli --set-root .")
            return False
        
        # Convert relative paths to absolute paths
        original_path = root_path
        if not os.path.isabs(root_path):
            root_path = os.path.abspath(root_path)
        
        print(f"📁 Project Root Configuration")
        print("=" * 35)
        
        if original_path != root_path:
            print(f"🔄 Converting relative path '{original_path}' to absolute path")
        
        # Store the root path
        memory = ConsoleMemory()
        
        if 'build_config' not in memory.memory:
            memory.memory['build_config'] = {}
        
        memory.memory['build_config']['project_root'] = root_path
        memory.save_memory()
        
        print(f"✅ Project root set to: '{root_path}'")
        
        # Check if root exists
        if os.path.exists(root_path) and os.path.isdir(root_path):
            print(f"📁 Root directory exists and is accessible")
        else:
            print(f"⚠️  Root directory not found: {root_path}")
        
        return True
        
    except ImportError:
        print("❌ Core module required for root configuration")
        return False
    except Exception as e:
        print(f"❌ Error setting project root: {e}")
        return False

def handle_show_root():
    """Handle show project root command"""
    try:
        memory = ConsoleMemory()
        build_config = memory.get_config()
        project_root = build_config.get('project_root')
        
        print(f"📁 Project Root Configuration")
        print("=" * 35)
        
        if project_root:
            print(f"✅ Current project root: {project_root}")
            
            # Check if root exists
            if os.path.exists(project_root) and os.path.isdir(project_root):
                print(f"📁 Directory exists and is accessible")
            else:
                print(f"⚠️  Directory not found: {project_root}")
                
            print()
            print("🔄 Available commands:")
            print("   • --set-root <path>  Set new project root")
            print("   • --show-root        Show current project root")
        else:
            print("❌ No project root configured")
            print("💡 Set a project root with: --set-root /path/to/project")
            
        return True
        
    except Exception as e:
        print(f"❌ Error showing project root: {e}")
        return False

def handle_export():
    """Handle export scan results command"""
    try:
        import json
        from datetime import datetime
        
        print("📤 Export Scan Results")
        print("=" * 25)
        
        memory = ConsoleMemory()
        memory = ConsoleMemory()
        
        scan_results = memory.get_scan_results()
        
        if not scan_results:
            print("❌ No scan results to export")
            print("💡 Run some scans first: --scan python")
            return False
        
        # Export to JSON file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_file = f"scan_results_export_{timestamp}.json"
        
        export_data = {
            'timestamp': timestamp,
            'scan_results': scan_results,
            'build_config': memory.get_config(),
            'export_info': {
                'version': '2.0.0-modular',
                'tool': 'PyInstaller Build Tool'
            }
        }
        
        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Scan results exported to: {export_file}")
        print(f"📊 Exported {len(scan_results)} scan result sets")
        
        return True
        
    except ImportError:
        print("❌ Core module required for export")
        return False
    except Exception as e:
        print(f"❌ Error exporting scan results: {e}")
        return False

def handle_export_config():
    """Handle export configuration command"""
    try:
        import json
        from datetime import datetime
        
        print("📤 Export Configuration")
        print("=" * 25)
        
        memory = ConsoleMemory()
        memory = ConsoleMemory()
        
        config = memory.get_config()
        
        if not config:
            print("❌ No configuration to export")
            print("💡 Set some configuration first: --name MyApp")
            return False
        
        # Export configuration to JSON file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        config_file = f"build_config_export_{timestamp}.json"
        
        export_data = {
            'timestamp': timestamp,
            'build_config': config,
            'export_info': {
                'version': '2.0.0-modular',
                'tool': 'PyInstaller Build Tool'
            }
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Configuration exported to: {config_file}")
        print(f"📊 Exported configuration settings")
        
        return True
        
    except ImportError:
        print("❌ Core module required for export")
        return False
    except Exception as e:
        print(f"❌ Error exporting configuration: {e}")
        return False

def handle_start():
    """Handle start process command"""
    try:
        # Parse the process to start from arguments
        process = None
        for i, arg in enumerate(sys.argv):
            if arg == '--start' and i + 1 < len(sys.argv):
                process = sys.argv[i + 1]
                break
        
        if not process:
            print("❌ Please specify process to start")
            print("Examples: build_cli --start build, --start quick, --start package")
            return False
        
        print(f"🚀 Starting Process: {process}")
        print("=" * 30)
        
        if process.lower() in ['build', 'quick', 'custom']:
            print(f"🔨 Starting {process} build process...")
            core = BuildToolCore()
            return core.start_build(process.lower())
            
        elif process.lower() in ['package', 'msiwrapping']:
            print(f"📦 Starting {process} packaging process...")
            core = BuildToolCore()
            return core.start_build(process.lower())
            
        elif process.lower() == 'server':
            print("🌐 Starting server...")
            print("💡 Server functionality coming soon!")
            return True
            
        else:
            print(f"❌ Unknown process: {process}")
            print("Available processes: build, quick, custom, package, msiwrapping, server")
            print("💡 Note: GUI functionality has been separated - use separate GUI module")
            return False
        
    except Exception as e:
        print(f"❌ Error starting process: {e}")
        return False

def handle_remove_type():
    """Handle remove type command"""
    try:
        # Parse the type to remove from arguments
        file_type = None
        for i, arg in enumerate(sys.argv):
            if arg == '--remove-type' and i + 1 < len(sys.argv):
                file_type = sys.argv[i + 1]
                break
        
        if not file_type:
            print("❌ Please specify file type to remove")
            print("Example: build_cli --remove-type temp")
            return False
        
        print(f"🗑️  Remove File Type: {file_type}")
        print("=" * 30)
        
        memory = ConsoleMemory()
        memory = ConsoleMemory()
        
        # Check for contains filter
        contains_filter = None
        for i, arg in enumerate(sys.argv):
            if arg == '--contains' and i + 1 < len(sys.argv):
                contains_filter = sys.argv[i + 1]
                break
        
        if contains_filter:
            print(f"🔍 With filter: contains '{contains_filter}'")
        
        print("⚠️  This is a destructive operation!")
        print("💡 Use --backup first to create a backup")
        print("🚧 Remove functionality coming soon!")
        
        return True
        
    except ImportError:
        print("❌ Core module required for file operations")
        return False
    except Exception as e:
        print(f"❌ Error with remove type: {e}")
        return False

def handle_delete():
    """Handle delete file command"""
    try:
        # Parse the file to delete from arguments
        file_path = None
        for i, arg in enumerate(sys.argv):
            if arg == '--delete' and i + 1 < len(sys.argv):
                file_path = sys.argv[i + 1]
                break
        
        if not file_path:
            print("❌ Please specify file to delete")
            print("Example: build_cli --delete temp_file.txt")
            return False
        
        print(f"🗑️  Delete File: {file_path}")
        print("=" * 30)
        
        if os.path.exists(file_path):
            print(f"📁 File exists: {file_path}")
            print("⚠️  This is a destructive operation!")
            print("💡 Use --backup first to create a backup")
            print("🚧 Delete functionality coming soon!")
        else:
            print(f"❌ File not found: {file_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error with delete: {e}")
        return False

def handle_delete_type():
    """Handle delete type command"""
    try:
        # Parse the type to delete from arguments
        file_type = None
        for i, arg in enumerate(sys.argv):
            if arg == '--delete-type' and i + 1 < len(sys.argv):
                file_type = sys.argv[i + 1]
                break
        
        if not file_type:
            print("❌ Please specify file type to delete")
            print("Example: build_cli --delete-type cache")
            return False
        
        print(f"🗑️  Delete File Type: {file_type}")
        print("=" * 30)
        
        # Check for contains filter
        contains_filter = None
        for i, arg in enumerate(sys.argv):
            if arg == '--contains' and i + 1 < len(sys.argv):
                contains_filter = sys.argv[i + 1]
                break
        
        if contains_filter:
            print(f"🔍 With filter: contains '{contains_filter}'")
        
        print("⚠️  This is a destructive operation!")
        print("💡 Use --backup first to create a backup")
        print("🚧 Delete type functionality coming soon!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error with delete type: {e}")
        return False

def handle_create():
    """Handle auto-create project command"""
    try:
        print("🏗️  Auto-Create Project")
        print("=" * 25)
        
        # Check if auto mode is also specified
        auto_mode = '--auto' in sys.argv
        
        if auto_mode:
            print("🤖 Auto mode enabled - minimal user input required")
        else:
            print("🔧 Interactive mode - will ask for configuration")
        
        print("🚧 Auto-create functionality coming soon!")
        print("\n💡 This will:")
        print("   • Analyze current directory")
        print("   • Detect project type")
        print("   • Create optimal build configuration")
        print("   • Set up necessary files")
        
        if auto_mode:
            print("   • Automatically find splash screens")
            print("   • Auto-inject splash screen code")
            print("   • Configure build settings")
        
        return True
        
    except Exception as e:
        print(f"❌ Error with create: {e}")
        return False

def handle_show_console():
    """Handle show console command"""
    try:
        # Parse the show console setting from arguments
        show_value = None
        for i, arg in enumerate(sys.argv):
            if arg == '--show-console' and i + 1 < len(sys.argv):
                show_value = sys.argv[i + 1].lower()
                break
        
        if not show_value:
            print("❌ Please specify show console setting")
            print("Example: build_cli --show-console true")
            print("Valid values: true, false, yes, no, 1, 0")
            return False
        
        # Parse show console value
        if show_value in ['true', 't', 'yes', 'y', '1']:
            show_console = True
        elif show_value in ['false', 'f', 'no', 'n', '0']:
            show_console = False
        else:
            print(f"❌ Invalid show-console value: '{show_value}'")
            print("Valid values: true, false, yes, no, 1, 0")
            return False
        
        print(f"🖥️  Console Display Configuration")
        print("=" * 40)
        
        # Store the show console setting
        memory = ConsoleMemory()
        memory = ConsoleMemory()
        
        if 'build_config' not in memory.memory:
            memory.memory['build_config'] = {}
        
        memory.memory['build_config']['show_console'] = show_console
        memory.save_memory()
        
        print(f"✅ Show console set to: {show_console}")
        print("💡 This controls whether the console window is visible during build execution")
        
        return True
        
    except ImportError:
        print("❌ Core module required for console configuration")
        return False
    except Exception as e:
        print(f"❌ Error setting show console: {e}")
        return False

def handle_auto_mode():
    """Handle auto mode command"""
    try:
        print("🤖 Auto Mode Configuration")
        print("=" * 30)
        
        # Store auto mode setting
        memory = ConsoleMemory()
        memory = ConsoleMemory()
        
        if 'build_config' not in memory.memory:
            memory.memory['build_config'] = {}
        
        memory.memory['build_config']['auto_mode'] = True
        memory.save_memory()
        
        print("✅ Auto mode enabled")
        print("\n🚀 Auto mode features:")
        print("   • Automatic project analysis")
        print("   • Smart dependency detection")
        print("   • Auto-find splash screens")
        print("   • Optimal build configuration")
        print("   • Automatic code injection (splash screen disable)")
        print("\n💡 This will try to automate everything with minimal user input")
        
        return True
        
    except ImportError:
        print("❌ Core module required for auto mode configuration")
        return False
    except Exception as e:
        print(f"❌ Error setting auto mode: {e}")
        return False

def handle_backup():
    """Handle backup command"""
    try:
        from datetime import datetime
        
        print("💾 Backup Operation")
        print("=" * 20)
        
        # Create backup of current project
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = f"backup_{timestamp}"
        
        print(f"📁 Creating backup directory: {backup_dir}")
        print("🚧 Backup functionality coming soon!")
        print("\n💡 This will backup:")
        print("   • Source code files")
        print("   • Configuration files")
        print("   • Assets and resources")
        print("   • Build configurations")
        
        return True
        
    except Exception as e:
        print(f"❌ Error with backup: {e}")
        return False

def handle_remove():
    """Handle remove command for memory operations"""
    try:
        memory = ConsoleMemory()
        
        # Parse target and type from arguments
        target = None
        remove_type = None
        
        for i, arg in enumerate(sys.argv):
            if arg == '--target' and i + 1 < len(sys.argv):
                target = sys.argv[i + 1]
            elif arg == '--type' and i + 1 < len(sys.argv):
                remove_type = sys.argv[i + 1]
        
        memory = ConsoleMemory()
        
        print("🗑️  Memory Remove Operation")
        print("=" * 30)
        
        if target and remove_type:
            print(f"🎯 Removing {remove_type} items matching target: '{target}'")
            return handle_remove_with_target_and_type(memory, target, remove_type)
        elif target:
            print(f"🎯 Removing all items matching target: '{target}'")
            return handle_remove_with_target(memory, target)
        elif remove_type:
            print(f"📂 Removing all items of type: '{remove_type}'")
            return handle_remove_with_type(memory, remove_type)
        else:
            print("❌ Remove requires either --target or --type specification")
            print("💡 Examples:")
            print("   build_cli --remove --type python")
            print("   build_cli --remove --target myfile.py")
            print("   build_cli --remove --type config --target database")
            return False
        
    except ImportError:
        print("❌ Core module required for memory operations")
        print("You can download it with: build_cli --download-gui")
        return False

def handle_add():
    """Handle add command for adding files to memory"""
    try:
        # Parse files from arguments after --add
        files = []
        add_found = False
        
        for i, arg in enumerate(sys.argv):
            if arg == '--add':
                add_found = True
                # Collect all arguments after --add until we hit another -- command
                j = i + 1
                while j < len(sys.argv) and not sys.argv[j].startswith('--'):
                    files.append(sys.argv[j])
                    j += 1
                break
        
        if not add_found:
            print("❌ --add command not found")
            return False
        
        if not files:
            print("❌ No files specified after --add")
            print("💡 Examples:")
            print("   build_cli --add helloworld.py")
            print("   build_cli --add file1.py file2.py file3.py")
            print("   build_cli --add file1.py,file2.py,file3.py")
            print("   build_cli --add \"file with spaces.py\"")
            print("   build_cli --add 'another file.py' normal.py")
            return False
        
        return execute_add_command(files)
        
    except Exception as e:
        print(f"❌ Error with add command: {e}")
        return False
    except Exception as e:
        print(f"❌ Error in remove operation: {e}")
        return False

def handle_main():
    """Handle main file specification command"""
    try:
        # Parse main file from arguments
        main_file = None
        auto_mode = '--auto' in sys.argv
        
        for i, arg in enumerate(sys.argv):
            if arg == '--main' and i + 1 < len(sys.argv):
                main_file = sys.argv[i + 1]
                break
        
        if auto_mode and not main_file:
            # Auto-detect main file
            print("🤖 Auto-detecting main file...")
            main_file = analyze_and_find_main_file()
            if not main_file:
                print("❌ Could not auto-detect main file")
                return False
        elif not main_file:
            print("❌ Please specify a main file")
            print("Example: build_cli --main main.py")
            print("Or use: build_cli --main --auto (for auto-detection)")
            return False
        
        return execute_main_command(main_file, auto_mode)
        
    except Exception as e:
        print(f"❌ Error handling main command: {e}")
        return False

def handle_set_version():
    """Handle set-version command"""
    try:
        # Parse version from arguments
        version = None
        for i, arg in enumerate(sys.argv):
            if arg == '--set-version' and i + 1 < len(sys.argv):
                version = sys.argv[i + 1]
                break
        
        if not version:
            print("❌ Please specify a version")
            print("Example: build_cli --set-version 1.0.0")
            print("         build_cli --set-version 2024.1.15")
            print("         build_cli --set-version 1.2.3-beta")
            return False
        
        return execute_set_version_command(version)
        
    except Exception as e:
        print(f"❌ Error handling set-version command: {e}")
        return False

def handle_add_to_path():
    """Handle add-to-path command"""
    try:
        return execute_add_to_path_command()
        
    except Exception as e:
        print(f"❌ Error handling add-to-path command: {e}")
        return False

def handle_type_filter():
    """Handle type filter command"""
    try:
        # Parse the type filter from arguments
        file_type = None
        for i, arg in enumerate(sys.argv):
            if arg == '--type' and i + 1 < len(sys.argv):
                file_type = sys.argv[i + 1]
                break
        
        if not file_type:
            print("❌ Please specify file type to filter")
            print("Example: build_cli --scan python --type .py")
            return False
        
        print(f"🔍 Type Filter: {file_type}")
        print("=" * 25)
        
        print("💡 Type filter should be used with scan commands")
        print("Example: build_cli --scan python --type .py --contains 'import'")
        
        return True
        
    except Exception as e:
        print(f"❌ Error with type filter: {e}")
        return False

# Memory Remove Operations
def handle_remove_with_target_and_type(memory, target, remove_type):
    """Remove items from memory matching both target and type"""
    try:
        scan_results = memory.get_scan_results()
        removed_count = 0
        
        if remove_type not in scan_results:
            print(f"❌ No '{remove_type}' scan results found in memory")
            return False
        
        original_files = scan_results[remove_type].copy()
        remaining_files = []
        
        for file_path in original_files:
            if target.lower() not in file_path.lower():
                remaining_files.append(file_path)
            else:
                removed_count += 1
                print(f"   ✅ Removed: {file_path}")
        
        # Update memory
        memory.memory['scan_results'][remove_type] = remaining_files
        memory.save_memory()
        
        print(f"📊 Summary: Removed {removed_count} items from '{remove_type}' memory")
        return True
        
    except Exception as e:
        print(f"❌ Error removing items: {e}")
        return False

def handle_remove_with_target(memory, target):
    """Remove all items from memory matching target"""
    try:
        scan_results = memory.get_scan_results()
        total_removed = 0
        
        for scan_type in scan_results:
            original_files = scan_results[scan_type].copy()
            remaining_files = []
            removed_count = 0
            
            for file_path in original_files:
                if target.lower() not in file_path.lower():
                    remaining_files.append(file_path)
                else:
                    removed_count += 1
                    print(f"   ✅ Removed from {scan_type}: {file_path}")
            
            if removed_count > 0:
                memory.memory['scan_results'][scan_type] = remaining_files
                total_removed += removed_count
        
        memory.save_memory()
        print(f"📊 Summary: Removed {total_removed} items total from memory")
        return total_removed > 0
        
    except Exception as e:
        print(f"❌ Error removing items: {e}")
        return False

def handle_remove_with_type(memory, remove_type):
    """Remove all items of specified type from memory"""
    try:
        scan_results = memory.get_scan_results()
        
        if remove_type not in scan_results:
            print(f"❌ No '{remove_type}' scan results found in memory")
            return False
        
        removed_count = len(scan_results[remove_type])
        del memory.memory['scan_results'][remove_type]
        memory.save_memory()
        
        print(f"📊 Summary: Removed all {removed_count} '{remove_type}' items from memory")
        return True
        
    except Exception as e:
        print(f"❌ Error removing type: {e}")
        return False

def handle_remove_with_target_and_category(memory, target, from_category):
    """Remove items from memory matching target from a specific category"""
    try:
        scan_results = memory.get_scan_results()
        
        if from_category not in scan_results:
            print(f"❌ No '{from_category}' scan results found in memory")
            return False
        
        original_files = scan_results[from_category].copy()
        remaining_files = []
        removed_count = 0
        
        for file_path in original_files:
            if target.lower() not in file_path.lower():
                remaining_files.append(file_path)
            else:
                removed_count += 1
                print(f"   ✅ Removed from '{from_category}': {file_path}")
        
        # Update memory
        memory.memory['scan_results'][from_category] = remaining_files
        memory.save_memory()
        
        print(f"📊 Summary: Removed {removed_count} items matching '{target}' from '{from_category}' memory")
        return True
        
    except Exception as e:
        print(f"❌ Error removing items from category: {e}")
        return False

def handle_remove_with_target_type_and_category(memory, target, remove_type, from_category):
    """Remove items from memory matching target and type from a specific category"""
    try:
        scan_results = memory.get_scan_results()
        
        if from_category not in scan_results:
            print(f"❌ No '{from_category}' scan results found in memory")
            return False
        
        # For this advanced case, we validate that the remove_type matches the from_category
        if remove_type != from_category:
            print(f"⚠️  Warning: remove_type '{remove_type}' differs from from_category '{from_category}'")
            print(f"📋 Using category '{from_category}' for removal")
        
        original_files = scan_results[from_category].copy()
        remaining_files = []
        removed_count = 0
        
        for file_path in original_files:
            if target.lower() not in file_path.lower():
                remaining_files.append(file_path)
            else:
                removed_count += 1
                print(f"   ✅ Removed from '{from_category}': {file_path}")
        
        # Update memory
        memory.memory['scan_results'][from_category] = remaining_files
        memory.save_memory()
        
        print(f"📊 Summary: Removed {removed_count} '{remove_type}' items matching '{target}' from '{from_category}' memory")
        return True
        
    except Exception as e:
        print(f"❌ Error removing items from specific category: {e}")
        return False

# File Delete Operations
def handle_delete_with_target_and_type(target, delete_type):
    """Delete files matching both target and type"""
    try:
        import os
        import glob
        
        deleted_count = 0
        
        # Create pattern for file searching
        if delete_type.startswith('.'):
            # File extension
            pattern = f"**/*{target}*{delete_type}"
        else:
            # File type or name pattern
            pattern = f"**/*{target}*"
        
        print(f"🔍 Searching for files matching pattern: {pattern}")
        
        matching_files = glob.glob(pattern, recursive=True)
        
        if not matching_files:
            print(f"❌ No files found matching pattern")
            return False
        
        print(f"📋 Found {len(matching_files)} matching files:")
        for file_path in matching_files:
            print(f"   • {file_path}")
        
        confirm = input(f"\n⚠️  Delete {len(matching_files)} files? (y/N): ").strip().lower()
        if confirm == 'y':
            for file_path in matching_files:
                try:
                    os.remove(file_path)
                    print(f"   ✅ Deleted: {file_path}")
                    deleted_count += 1
                except Exception as e:
                    print(f"   ❌ Failed to delete {file_path}: {e}")
            
            print(f"📊 Summary: Successfully deleted {deleted_count}/{len(matching_files)} files")
        else:
            print("❌ Delete operation cancelled")
            return False
        
        return deleted_count > 0
        
    except Exception as e:
        print(f"❌ Error in delete operation: {e}")
        return False

def handle_delete_with_target(target):
    """Delete specific file or files matching target"""
    try:
        import os
        import glob
        
        # Check if target is a specific file
        if os.path.isfile(target):
            print(f"📁 Target file found: {target}")
            confirm = input(f"⚠️  Delete '{target}'? (y/N): ").strip().lower()
            if confirm == 'y':
                os.remove(target)
                print(f"✅ Successfully deleted: {target}")
                return True
            else:
                print("❌ Delete operation cancelled")
                return False
        else:
            # Search for files matching pattern
            pattern = f"**/*{target}*"
            matching_files = glob.glob(pattern, recursive=True)
            
            if not matching_files:
                print(f"❌ No files found matching '{target}'")
                return False
            
            print(f"📋 Found {len(matching_files)} files matching '{target}':")
            for file_path in matching_files:
                print(f"   • {file_path}")
            
            confirm = input(f"\n⚠️  Delete {len(matching_files)} files? (y/N): ").strip().lower()
            if confirm == 'y':
                deleted_count = 0
                for file_path in matching_files:
                    try:
                        os.remove(file_path)
                        print(f"   ✅ Deleted: {file_path}")
                        deleted_count += 1
                    except Exception as e:
                        print(f"   ❌ Failed to delete {file_path}: {e}")
                
                print(f"📊 Summary: Successfully deleted {deleted_count}/{len(matching_files)} files")
                return deleted_count > 0
            else:
                print("❌ Delete operation cancelled")
                return False
        
    except Exception as e:
        print(f"❌ Error in delete operation: {e}")
        return False

def handle_delete_with_type(delete_type):
    """Delete all files of specified type"""
    try:
        import os
        import glob
        
        # Create pattern based on type
        if delete_type.startswith('.'):
            # File extension
            pattern = f"**/*{delete_type}"
        else:
            # Named pattern
            patterns = {
                'pyc': '**/*.pyc',
                'pycache': '**/__pycache__/**',
                'temp': '**/temp/**',
                'cache': '**/cache/**',
                'log': '**/*.log',
                'backup': '**/backup*/**'
            }
            pattern = patterns.get(delete_type, f"**/*{delete_type}*")
        
        print(f"🔍 Searching for files of type '{delete_type}' with pattern: {pattern}")
        
        matching_files = []
        for match in glob.glob(pattern, recursive=True):
            if os.path.isfile(match):
                matching_files.append(match)
        
        if not matching_files:
            print(f"❌ No files found of type '{delete_type}'")
            return False
        
        print(f"📋 Found {len(matching_files)} files of type '{delete_type}':")
        for file_path in matching_files[:10]:  # Show first 10
            print(f"   • {file_path}")
        if len(matching_files) > 10:
            print(f"   ... and {len(matching_files) - 10} more files")
        
        confirm = input(f"\n⚠️  Delete all {len(matching_files)} files of type '{delete_type}'? (y/N): ").strip().lower()
        if confirm == 'y':
            deleted_count = 0
            for file_path in matching_files:
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        deleted_count += 1
                    elif os.path.isdir(file_path):
                        import shutil
                        shutil.rmtree(file_path)
                        deleted_count += 1
                except Exception as e:
                    print(f"   ❌ Failed to delete {file_path}: {e}")
            
            print(f"📊 Summary: Successfully deleted {deleted_count}/{len(matching_files)} items")
            return deleted_count > 0
        else:
            print("❌ Delete operation cancelled")
            return False
        
    except Exception as e:
        print(f"❌ Error in delete operation: {e}")
        return False

def execute_start_command_queued(command):
    """Execute start command from queue with version control support"""
    try:
        process = command.get('process', 'build')
        no_version = command.get('no_version', False)
        auto_detect = command.get('auto_detect', False)
        
        print(f"🚀 Starting Process: {process}")
        print("=" * 30)
        
        if no_version:
            print("🔧 Version appending disabled for this build")
        
        if process.lower() in ['build', 'quick', 'custom']:
            print(f"🔨 Starting {process} build process...")
            core = BuildToolCore()
            
            # Set no-version flag in build config if specified
            if no_version:
                build_config = core.memory.get_config()
                build_config['no_version_append'] = True
                core.memory.store_config(build_config)
            
            return core.start_build(process.lower())
            
        elif process.lower() in ['package', 'msiwrapping']:
            print(f"📦 Starting {process} packaging process...")
            core = BuildToolCore()
            
            # Set no-version flag in build config if specified
            if no_version:
                build_config = core.memory.get_config()
                build_config['no_version_append'] = True
                core.memory.store_config(build_config)
            
            return core.start_build(process.lower())
            
        elif process.lower() == 'server':
            print("🌐 Starting server...")
            print("💡 Server functionality coming soon!")
            return True
            
        else:
            print(f"❌ Unknown process: {process}")
            print("Available processes: build, quick, custom, package, msiwrapping, server")
            return False
        
    except Exception as e:
        print(f"❌ Error starting process: {e}")
        return False

def execute_no_version_append_command(enable_no_version):
    """Execute no-version-append global setting command"""
    try:
        memory = ConsoleMemory()
        
        print("🔧 Version Append Configuration")
        print("=" * 40)
        
        # Store the global setting
        build_config = memory.get_config()
        build_config['no_version_append_global'] = enable_no_version
        memory.store_config(build_config)
        
        if enable_no_version:
            print("✅ Global setting: Version will NOT be appended to build names")
            print("💡 This affects all future builds unless overridden")
        else:
            print("✅ Global setting: Version WILL be appended to build names (default)")
            print("💡 You can still use --no-version for individual builds")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting version append configuration: {e}")
        return False

def execute_windowed_command(windowed_value):
    """Execute windowed/no-console mode configuration command"""
    try:
        memory = ConsoleMemory()
        
        print("🖥️  Console/Windowed Mode Configuration")
        print("=" * 45)
        
        # Store the windowed setting in build configuration
        build_config = memory.get_config()
        build_config['windowed'] = windowed_value
        memory.store_config(build_config)
        
        if windowed_value:
            print("✅ Windowed mode enabled (no console)")
            print("📋 PyInstaller will use: --windowed")
            print("💡 Your application will run without a console window")
            print("⚠️  Note: Console output won't be visible unless redirected")
        else:
            print("✅ Console mode enabled")
            print("📋 PyInstaller will use: --console")
            print("💡 Your application will show a console window")
            print("✨ Console output will be visible during execution")
        
        print()
        print("🔄 Available commands:")
        print("   • --windowed         Enable windowed mode (no console)")
        print("   • --no-console       Same as --windowed")
        print("   • --no-console false Enable console mode")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting windowed/console configuration: {e}")
        return False

def execute_clean_command():
    """Execute clean command to remove previous build artifacts"""
    try:
        import shutil
        import glob
        
        print("🧹 Cleaning Previous Build Artifacts")
        print("=" * 40)
        
        # Get project root if configured, otherwise use script location
        memory = ConsoleMemory()
        build_config = memory.get_config()
        project_root = build_config.get('project_root')
        
        if project_root and os.path.exists(project_root):
            print(f"📁 Using configured project root: {project_root}")
            clean_dir = project_root
        else:
            # Get script location for accurate cleanup
            clean_dir = get_working_context()['script_location']
            print(f"📁 Using script location: {clean_dir}")
            
        cleaned = []
        
        # Clean dist/ directory
        dist_path = os.path.join(clean_dir, 'dist')
        if os.path.exists(dist_path):
            shutil.rmtree(dist_path)
            cleaned.append('dist/')
            
        # Clean build/ directory  
        build_path = os.path.join(clean_dir, 'build')
        if os.path.exists(build_path):
            shutil.rmtree(build_path)
            cleaned.append('build/')
            
        # Clean .spec files
        spec_pattern = os.path.join(clean_dir, '*.spec')
        spec_files = glob.glob(spec_pattern)
        for spec_file in spec_files:
            os.remove(spec_file)
            cleaned.append(os.path.basename(spec_file))
            
        # Clean __pycache__ directories only in the main directory
        # (not in virtual environments)
        main_pycache = os.path.join(clean_dir, '__pycache__')
        if os.path.exists(main_pycache):
            try:
                shutil.rmtree(main_pycache)
                cleaned.append('__pycache__')
            except:
                pass  # Skip if can't remove
                    
        if cleaned:
            print("✅ Successfully cleaned:")
            for item in cleaned:
                print(f"   • {item}")
        else:
            print("💡 No build artifacts found to clean")
            
        print()
        print("🔄 Available commands:")
        print("   • --clean            Clean previous build artifacts")
        print("   • --show-memory      Show current build configuration")
        
        return True
        
    except Exception as e:
        print(f"❌ Error cleaning build artifacts: {e}")
        return False

def handle_project_config_menu(core):
    """Enhanced project configuration menu with more options"""
    while True:
        print("\n┌─────────────────────────────────────────────┐")
        print("│         🏗️  PROJECT CONFIGURATION           │")
        print("├─────────────────────────────────────────────┤")
        print("│ 1. Set Application Name                    │")
        print("│ 2. Set Version                             │")
        print("│ 3. Set Main File                           │")
        print("│ 4. Configure Build Options                 │")
        print("│ 5. Show Current Configuration              │")
        print("│ 6. Optimal Project Structure Guide        │")
        print("│ 7. Auto-detect Project Settings           │")
        print("│ 8. Reset Configuration                     │")
        print("│ 0. ← Back to main menu                     │")
        print("└─────────────────────────────────────────────┘")
        
        choice = input("config> ").strip()
        
        if choice == '0':
            break
        elif choice == '1':
            name = input("Enter application name: ").strip()
            if name:
                build_config = core.memory.get_config()
                build_config['name'] = name
                core.memory.store_config(build_config)
                print(f"✅ Application name set to: {name}")
            else:
                print("❌ Name cannot be empty")
                
        elif choice == '2':
            version = input("Enter version (e.g., 1.0.0): ").strip()
            if version:
                build_config = core.memory.get_config()
                build_config['version'] = version
                core.memory.store_config(build_config)
                print(f"✅ Version set to: {version}")
            else:
                print("❌ Version cannot be empty")
                
        elif choice == '3':
            main_file = input("Enter main file path (or 'auto' for auto-detection): ").strip()
            if main_file:
                if main_file.lower() == 'auto':
                    detected = core.auto_detect_main_file()
                    if detected:
                        build_config = core.memory.get_config()
                        build_config['main_file'] = detected
                        core.memory.store_config(build_config)
                        print(f"✅ Auto-detected main file: {detected}")
                    else:
                        print("❌ Could not auto-detect main file")
                elif os.path.exists(main_file):
                    build_config = core.memory.get_config()
                    build_config['main_file'] = main_file
                    core.memory.store_config(build_config)
                    print(f"✅ Main file set to: {main_file}")
                else:
                    print(f"❌ File not found: {main_file}")
            else:
                print("❌ Main file cannot be empty")
                
        elif choice == '4':
            handle_build_options_menu(core)
            
        elif choice == '5':
            show_current_config(core)
            
        elif choice == '6':
            core.show_optimal_structure()
            
        elif choice == '7':
            print("🤖 Auto-detecting project settings...")
            main_file = core.auto_detect_main_file()
            if main_file:
                name = core.auto_generate_name(main_file)
                build_config = core.memory.get_config()
                build_config.update({
                    'main_file': main_file,
                    'name': name,
                    'windowed': core.detect_gui_app(main_file)
                })
                core.memory.store_config(build_config)
                print(f"✅ Auto-configured:")
                print(f"   Name: {name}")
                print(f"   Main File: {main_file}")
                print(f"   GUI App: {build_config['windowed']}")
            else:
                print("❌ Could not auto-detect project settings")
                
        elif choice == '8':
            confirm = input("⚠️  Reset all configuration? (y/N): ").strip().lower()
            if confirm == 'y':
                core.memory.clear_memory('build_config')
                print("✅ Configuration reset successfully")
            else:
                print("❌ Reset cancelled")
        else:
            print("❌ Invalid choice. Please select 0-8.")

def handle_build_menu(core):
    """Enhanced build management menu"""
    while True:
        print("\n┌─────────────────────────────────────────────┐")
        print("│         🚀 BUILD MANAGEMENT                 │")
        print("├─────────────────────────────────────────────┤")
        print("│ 1. Quick Build (auto-detection)            │")
        print("│ 2. Full Build (with current config)        │")
        print("│ 3. Custom Build (interactive)              │")
        print("│ 4. Preview Build Command                   │")
        print("│ 5. Build with Version Control              │")
        print("│ 6. Clean Build (remove old files)          │")
        print("│ 7. Test Build (debug mode)                 │")
        print("│ 8. Build Settings                          │")
        print("│ 0. ← Back to main menu                     │")
        print("└─────────────────────────────────────────────┘")
        
        choice = input("build> ").strip()
        
        if choice == '0':
            break
        elif choice == '1':
            print("🚀 Starting Quick Build...")
            success = core.start_build("quick")
            if success:
                print("✅ Quick build completed successfully!")
            else:
                print("❌ Quick build failed")
                
        elif choice == '2':
            print("🔨 Starting Full Build...")
            success = core.start_build("build")
            if success:
                print("✅ Full build completed successfully!")
            else:
                print("❌ Full build failed")
                
        elif choice == '3':
            print("⚙️  Interactive custom build coming soon!")
            
        elif choice == '4':
            print("📋 Build Command Preview:")
            print("-" * 40)
            build_config = core.memory.get_config()
            if build_config.get('main_file'):
                command = core.build_pyinstaller_command(build_config)
                cmd_str = " \\\n  ".join(command) if len(" ".join(command)) > 80 else " ".join(command)
                print(f"{cmd_str}")
            else:
                print("❌ No main file configured. Please configure project first.")
                
        elif choice == '5':
            handle_version_build_menu(core)
            
        elif choice == '6':
            print("🧹 Cleaning build files...")
            try:
                import shutil
                for directory in ['build', 'dist', '__pycache__']:
                    if os.path.exists(directory):
                        shutil.rmtree(directory)
                        print(f"✅ Removed {directory}/")
                    else:
                        print(f"ℹ️  {directory}/ not found")
                
                # Remove .spec files
                import glob
                spec_files = glob.glob("*.spec")
                for spec_file in spec_files:
                    os.remove(spec_file)
                    print(f"✅ Removed {spec_file}")
                
                print("✅ Build cleanup completed!")
            except Exception as e:
                print(f"❌ Cleanup error: {e}")
                
        elif choice == '7':
            print("🐛 Starting Debug Build...")
            build_config = core.memory.get_config()
            build_config['debug'] = True
            core.memory.store_config(build_config)
            success = core.start_build("build")
            if success:
                print("✅ Debug build completed!")
            else:
                print("❌ Debug build failed")
                
        elif choice == '8':
            handle_build_options_menu(core)
        else:
            print("❌ Invalid choice. Please select 0-8.")

def handle_build_options_menu(core):
    """Handle build options configuration"""
    while True:
        build_config = core.memory.get_config()
        
        print("\n┌─────────────────────────────────────────────┐")
        print("│         ⚙️  BUILD OPTIONS                   │")
        print("├─────────────────────────────────────────────┤")
        print(f"│ 1. Single File: {build_config.get('onefile', True):<23} │")
        print(f"│ 2. Windowed Mode: {build_config.get('windowed', False):<21} │")
        print(f"│ 3. Include Date: {build_config.get('include_date', True):<22} │")
        print(f"│ 4. Clean Build: {build_config.get('clean', True):<23} │")
        print(f"│ 5. Debug Mode: {build_config.get('debug', False):<24} │")
        print(f"│ 6. Version Append: {not build_config.get('no_version_append_global', False):<19} │")
        print("│ 7. Icon File Selection                     │")
        print("│ 0. ← Back to configuration menu           │")
        print("└─────────────────────────────────────────────┘")
        
        choice = input("options> ").strip()
        
        if choice == '0':
            break
        elif choice == '1':
            current = build_config.get('onefile', True)
            build_config['onefile'] = not current
            core.memory.store_config(build_config)
            print(f"✅ Single file mode: {'Enabled' if not current else 'Disabled'}")
            
        elif choice == '2':
            current = build_config.get('windowed', False)
            build_config['windowed'] = not current
            core.memory.store_config(build_config)
            print(f"✅ Windowed mode: {'Enabled' if not current else 'Disabled'}")
            
        elif choice == '3':
            current = build_config.get('include_date', True)
            build_config['include_date'] = not current
            core.memory.store_config(build_config)
            print(f"✅ Include date: {'Enabled' if not current else 'Disabled'}")
            
        elif choice == '4':
            current = build_config.get('clean', True)
            build_config['clean'] = not current
            core.memory.store_config(build_config)
            print(f"✅ Clean build: {'Enabled' if not current else 'Disabled'}")
            
        elif choice == '5':
            current = build_config.get('debug', False)
            build_config['debug'] = not current
            core.memory.store_config(build_config)
            print(f"✅ Debug mode: {'Enabled' if not current else 'Disabled'}")
            
        elif choice == '6':
            current = build_config.get('no_version_append_global', False)
            build_config['no_version_append_global'] = not current
            core.memory.store_config(build_config)
            print(f"✅ Version append: {'Disabled' if not current else 'Enabled'}")
            
        elif choice == '7':
            icon_file = input("Enter icon file path (or 'auto' for auto-detection): ").strip()
            if icon_file:
                if icon_file.lower() == 'auto':
                    detected = core.auto_detect_icon()
                    if detected:
                        build_config['icon'] = detected
                        core.memory.store_config(build_config)
                        print(f"✅ Auto-detected icon: {detected}")
                    else:
                        print("❌ Could not auto-detect icon file")
                elif os.path.exists(icon_file):
                    build_config['icon'] = icon_file
                    core.memory.store_config(build_config)
                    print(f"✅ Icon file set to: {icon_file}")
                else:
                    print(f"❌ Icon file not found: {icon_file}")
            else:
                # Remove icon
                if 'icon' in build_config:
                    del build_config['icon']
                    core.memory.store_config(build_config)
                    print("✅ Icon file removed")
        else:
            print("❌ Invalid choice. Please select 0-7.")

def handle_version_build_menu(core):
    """Handle version-controlled builds"""
    while True:
        print("\n┌─────────────────────────────────────────────┐")
        print("│         🔢 VERSION BUILD MENU              │")
        print("├─────────────────────────────────────────────┤")
        print("│ 1. Build with Version                      │")
        print("│ 2. Build without Version                   │")
        print("│ 3. Set Global Version Policy               │")
        print("│ 4. Auto-increment Version                  │")
        print("│ 5. Show Version Status                     │")
        print("│ 0. ← Back to build menu                    │")
        print("└─────────────────────────────────────────────┘")
        
        choice = input("version> ").strip()
        
        if choice == '0':
            break
        elif choice == '1':
            version = input("Enter version (e.g., 1.0.0): ").strip()
            if version:
                build_config = core.memory.get_config()
                build_config['version'] = version
                build_config['no_version_append'] = False
                core.memory.store_config(build_config)
                print(f"🚀 Building with version {version}...")
                success = core.start_build("build")
                if success:
                    print("✅ Version build completed!")
            else:
                print("❌ Version cannot be empty")
                
        elif choice == '2':
            build_config = core.memory.get_config()
            build_config['no_version_append'] = True
            core.memory.store_config(build_config)
            print("🚀 Building without version...")
            success = core.start_build("build")
            if success:
                print("✅ No-version build completed!")
                
        elif choice == '3':
            current = core.memory.get_config().get('no_version_append_global', False)
            print(f"Current global policy: {'No version append' if current else 'Version append'}")
            new_policy = input("Disable version append globally? (y/N): ").strip().lower()
            
            build_config = core.memory.get_config()
            build_config['no_version_append_global'] = (new_policy == 'y')
            core.memory.store_config(build_config)
            
            policy_text = "disabled" if new_policy == 'y' else "enabled"
            print(f"✅ Global version append: {policy_text}")
            
        elif choice == '4':
            current_version = core.memory.get_config().get('version', '1.0.0')
            print(f"Current version: {current_version}")
            print("Auto-increment options:")
            print("1. Patch (1.0.0 → 1.0.1)")
            print("2. Minor (1.0.0 → 1.1.0)")
            print("3. Major (1.0.0 → 2.0.0)")
            
            increment_choice = input("Select increment type (1-3): ").strip()
            
            try:
                parts = current_version.split('.')
                if len(parts) >= 3:
                    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
                    
                    if increment_choice == '1':
                        patch += 1
                    elif increment_choice == '2':
                        minor += 1
                        patch = 0
                    elif increment_choice == '3':
                        major += 1
                        minor = 0
                        patch = 0
                    else:
                        print("❌ Invalid choice")
                        continue
                    
                    new_version = f"{major}.{minor}.{patch}"
                    build_config = core.memory.get_config()
                    build_config['version'] = new_version
                    core.memory.store_config(build_config)
                    print(f"✅ Version incremented to: {new_version}")
                else:
                    print("❌ Invalid version format for auto-increment")
            except ValueError:
                print("❌ Could not parse version number")
                
        elif choice == '5':
            build_config = core.memory.get_config()
            version = build_config.get('version', 'Not set')
            global_no_version = build_config.get('no_version_append_global', False)
            local_no_version = build_config.get('no_version_append', False)
            
            print(f"\n📊 Version Status:")
            print(f"   Current Version: {version}")
            print(f"   Global Policy: {'No version append' if global_no_version else 'Version append'}")
            print(f"   Local Override: {'No version append' if local_no_version else 'Default'}")
            print(f"   Effective: {'No version will be appended' if (global_no_version or local_no_version) else 'Version will be appended'}")
        else:
            print("❌ Invalid choice. Please select 0-5.")

def show_current_config(core):
    """Show current project configuration"""
    build_config = core.memory.get_config()
    
    print("\n📊 Current Project Configuration:")
    print("=" * 50)
    print(f"Application Name: {build_config.get('name', 'Not set')}")
    print(f"Version: {build_config.get('version', 'Not set')}")
    print(f"Main File: {build_config.get('main_file', 'Not set')}")
    print(f"Icon File: {build_config.get('icon', 'Not set')}")
    print()
    print("Build Options:")
    print(f"  Single File: {build_config.get('onefile', True)}")
    print(f"  Windowed Mode: {build_config.get('windowed', False)}")
    print(f"  Include Date: {build_config.get('include_date', True)}")
    print(f"  Clean Build: {build_config.get('clean', True)}")
    print(f"  Debug Mode: {build_config.get('debug', False)}")
    print()
    print("Version Control:")
    print(f"  Global No-Version: {build_config.get('no_version_append_global', False)}")
    print(f"  Local No-Version: {build_config.get('no_version_append', False)}")
    
    # Preview build name
    if build_config.get('name'):
        preview_name = core.generate_build_filename(build_config)
        print(f"\nPreview Build Name: {preview_name}")

if __name__ == "__main__":
    try:
        print(f"DEBUG: sys.argv = {sys.argv}")  # Debug line
        
        # Check if we should use command queue system
        if has_multiple_commands():
            print("DEBUG: Using queue system (multiple commands)")  # Debug line
            # Multiple commands detected - use queue system
            success = process_command_queue()
        elif is_core_command():
            print("DEBUG: Detected core command")  # Debug line
            # Single core command that can be handled by queue system
            # Commands like --auto, --add, --set-version, etc. should use queue
            queue_commands = {
                '--add', '--set-version', '--add-to-path',
                '--virtual', '--activate', '--install-needed',
                '--export-config', '--downgrade',
                '--start', '--no-version', '--no-version-append'
            }
            
            if any(cmd in sys.argv for cmd in queue_commands):
                print("DEBUG: Routing to queue system")  # Debug line
                # Route to queue system
                success = process_command_queue()
            else:
                print("DEBUG: Using main() for core command")  # Debug line
                # Use regular main() for basic commands
                success = main()
        else:
            print("DEBUG: Using main() for simple command")  # Debug line
            # Use regular main() for simple commands
            success = main()
            
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        safe_print("\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        safe_print(f"❌ Unexpected error: {e}")
        sys.exit(1)
