#!/usr/bin/env python3
"""
Core functionality shared between CLI and GUI versions
Contains GitHub integration, console operations, and utility functions
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

class ConsoleMemory:
    """Memory system for console mode to store scan results and configuration"""
    
    def __init__(self, memory_file="build_console_memory.json"):
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

class BuildToolCore:
    """Core functionality shared between CLI and GUI versions"""
    
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
    
    def scan_files(self, scan_type, scan_directory=None, contains_filter=None):
        """Scan for files of a specific type"""
        if scan_directory is None:
            scan_directory = os.getcwd()
        
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
            'project': ['*']  # Scan everything for project overview
        }
        
        if scan_type not in scan_patterns:
            print(f"❌ Unknown scan type: {scan_type}")
            print(f"Available types: {', '.join(scan_patterns.keys())}")
            return []
        
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
    
    def handle_scan_command(self, scan_type, append_mode=False, scan_directory=None, contains_filter=None):
        """Handle scan command with memory storage"""
        results = self.scan_files(scan_type, scan_directory, contains_filter)
        
        if results:
            self.memory.store_scan_results(scan_type, results, append_mode)
            if append_mode:
                print(f"📚 Appended {len(results)} files to {scan_type} in memory")
            else:
                print(f"💾 Stored {len(results)} {scan_type} files in memory")
        
        return results
    
    def show_optimal_structure(self):
        """Display optimal project structure guide"""
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
• Include version in final builds (MyApp_v1.0.0_20250104)

🚀 Build Optimization Tips:
• Keep main.py minimal - import from modules
• Use --onefile for single executable
• Exclude unnecessary modules with --exclude-module
• Include data files with --add-data
• Test on target systems before release
        """)
        return True
    
    def get_github_repository_info(self):
        """Get repository information from GitHub API"""
        repo_owner = self.config.get('GITHUB_REPO_OWNER', 'braydenanderson2014')
        repo_name = self.config.get('GITHUB_REPO_NAME', 'Build_Script')
        token = self.config.get('GITHUB_API_TOKEN', '')
        
        if not token:
            return {"error": "GitHub API token not configured in Build_Script.env"}
        
        try:
            url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'PyInstaller-Build-Tool'
            }
            
            request = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(request, timeout=10) as response:
                data = json.loads(response.read().decode())
                
                return {
                    "name": data.get("name", "Unknown"),
                    "description": data.get("description", "No description"),
                    "stars": data.get("stargazers_count", 0),
                    "forks": data.get("forks_count", 0),
                    "language": data.get("language", "Unknown"),
                    "size": data.get("size", 0),
                    "updated_at": data.get("updated_at", "Unknown"),
                    "default_branch": data.get("default_branch", "main"),
                    "clone_url": data.get("clone_url", ""),
                    "ssh_url": data.get("ssh_url", ""),
                    "homepage": data.get("homepage", ""),
                    "topics": data.get("topics", [])
                }
                
        except Exception as e:
            return {"error": f"Failed to fetch repository info: {str(e)}"}
    
    def check_repository_status(self):
        """Check repository status including recent commits and releases"""
        repo_info = self.get_github_repository_info()
        if "error" in repo_info:
            return repo_info
            
        repo_owner = self.config.get('GITHUB_REPO_OWNER', 'braydenanderson2014')
        repo_name = self.config.get('GITHUB_REPO_NAME', 'Build_Script')
        token = self.config.get('GITHUB_API_TOKEN', '')
        
        try:
            # Get recent commits
            commits_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/commits"
            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'PyInstaller-Build-Tool'
            }
            
            commits_request = urllib.request.Request(f"{commits_url}?per_page=5", headers=headers)
            
            with urllib.request.urlopen(commits_request, timeout=10) as response:
                commits_data = json.loads(response.read().decode())
                
                recent_commits = []
                for commit in commits_data[:5]:
                    recent_commits.append({
                        "sha": commit["sha"][:8],
                        "message": commit["commit"]["message"].split('\n')[0][:60],
                        "author": commit["commit"]["author"]["name"],
                        "date": commit["commit"]["author"]["date"]
                    })
            
            # Get latest release
            releases_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
            releases_request = urllib.request.Request(releases_url, headers=headers)
            
            try:
                with urllib.request.urlopen(releases_request, timeout=10) as response:
                    release_data = json.loads(response.read().decode())
                    latest_release = {
                        "tag_name": release_data.get("tag_name", "None"),
                        "name": release_data.get("name", "No name"),
                        "published_at": release_data.get("published_at", "Unknown"),
                        "download_count": sum(asset.get("download_count", 0) for asset in release_data.get("assets", []))
                    }
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    latest_release = {"tag_name": "None", "name": "No releases found"}
                else:
                    raise
            
            return {
                **repo_info,
                "recent_commits": recent_commits,
                "latest_release": latest_release,
                "status": "active" if recent_commits else "inactive"
            }
            
        except Exception as e:
            return {**repo_info, "error": f"Failed to fetch detailed status: {str(e)}"}

    def download_executable(self, exe_type="gui"):
        """Download executable from GitHub releases"""
        valid_types = ["cli", "gui", "full"]
        if exe_type not in valid_types:
            print(f"❌ Invalid executable type: {exe_type}")
            print(f"Valid types: {', '.join(valid_types)}")
            return False
            
        print(f"🔍 Checking for {exe_type} executable...")
        
        repo_owner = self.config.get('GITHUB_REPO_OWNER', 'braydenanderson2014')
        repo_name = self.config.get('GITHUB_REPO_NAME', 'Build_Script')
        token = self.config.get('GITHUB_API_TOKEN', '')
        
        if not token:
            print("❌ GitHub API token not configured in Build_Script.env")
            return False
        
        try:
            # Get latest release
            url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'PyInstaller-Build-Tool'
            }
            
            request = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(request, timeout=30) as response:
                release_data = json.loads(response.read().decode())
                
                # Look for the specific executable in assets
                exe_name = f"build_{exe_type}.exe"
                download_url = None
                
                for asset in release_data.get("assets", []):
                    if asset["name"] == exe_name:
                        download_url = asset["browser_download_url"]
                        break
                
                if not download_url:
                    print(f"❌ {exe_name} not found in latest release")
                    print("Available assets:")
                    for asset in release_data.get("assets", []):
                        print(f"  - {asset['name']}")
                    return False
                
                # Download the executable
                print(f"📥 Downloading {exe_name}...")
                
                with urllib.request.urlopen(download_url) as download_response:
                    if download_response.status == 200:
                        with open(exe_name, 'wb') as f:
                            f.write(download_response.read())
                        
                        # Make executable (Unix-like systems)
                        if platform.system() != "Windows":
                            os.chmod(exe_name, 0o755)
                        
                        print(f"✅ {exe_name} downloaded successfully")
                        return True
                    else:
                        print(f"❌ Failed to download: HTTP {download_response.status}")
                        return False
                        
        except Exception as e:
            print(f"❌ Failed to download executable: {e}")
            return False

    def download_gui_module(self):
        """Download or update GUI module if not present"""
        gui_file = "build_gui_interface.py"
        
        if os.path.exists(gui_file):
            print(f"GUI module already exists: {gui_file}")
            return True
            
        print("GUI module not found. Downloading...")
        
        repo_owner = self.config.get('GITHUB_REPO_OWNER', 'braydenanderson2014')
        repo_name = self.config.get('GITHUB_REPO_NAME', 'SystemCommands')
        
        try:
            url = f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}/main/Build_Script/build_gui_interface.py"
            
            with urllib.request.urlopen(url, timeout=30) as response:
                if response.status == 200:
                    with open(gui_file, 'wb') as f:
                        f.write(response.read())
                    print(f"✅ GUI module downloaded successfully: {gui_file}")
                    return True
                else:
                    print(f"❌ Failed to download GUI module: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            print(f"❌ Failed to download GUI module: {e}")
            return False

    def download_cli_module(self):
        """Download or update CLI module"""
        cli_file = "build_cli_new.py"  # Don't overwrite current CLI
        
        print("Downloading CLI module...")
        
        repo_owner = self.config.get('GITHUB_REPO_OWNER', 'braydenanderson2014')
        repo_name = self.config.get('GITHUB_REPO_NAME', 'SystemCommands')
        
        try:
            url = f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}/main/Build_Script/build_cli.py"
            
            with urllib.request.urlopen(url, timeout=30) as response:
                if response.status == 200:
                    with open(cli_file, 'wb') as f:
                        f.write(response.read())
                    print(f"✅ CLI module downloaded successfully: {cli_file}")
                    print("🔄 Replace your current CLI with the new version if desired")
                    return True
                else:
                    print(f"❌ Failed to download CLI module: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            print(f"❌ Failed to download CLI module: {e}")
            return False

    def launch_gui(self):
        """Launch GUI interface"""
        gui_file = "build_gui_interface.py"
        
        # Check if GUI module exists
        if not os.path.exists(gui_file):
            print("GUI module not found. Attempting to download...")
            if not self.download_gui_module():
                print("❌ Failed to download GUI module. Please check your internet connection.")
                return False
        
        # First try to import directly (for development environment)
        try:
            sys.path.insert(0, os.path.dirname(os.path.abspath(gui_file)))
            import build_gui_interface
            return build_gui_interface.launch_gui()
            
        except ImportError as e:
            print(f"⚠️  Direct import failed: {e}")
            print("🔄 Attempting to launch GUI using system Python...")
            
            # Try to launch using system Python as subprocess
            return self._launch_gui_subprocess(gui_file)
            
        except Exception as e:
            print(f"❌ Failed to launch GUI: {e}")
            return False
    
    def _launch_gui_subprocess(self, gui_file):
        """Launch GUI using system Python as subprocess"""
        try:
            # Find Python executable
            python_executables = [
                sys.executable,  # Current Python
                "python",        # System Python
                "python3",       # Python 3
                "py",           # Windows Python Launcher
            ]
            
            # Try to find a Python executable that has PyQt6
            working_python = None
            for python_cmd in python_executables:
                try:
                    # Test if this Python has PyQt6
                    result = subprocess.run(
                        [python_cmd, "-c", "import PyQt6; print('PyQt6 available')"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode == 0:
                        working_python = python_cmd
                        print(f"✅ Found Python with PyQt6: {python_cmd}")
                        break
                except (subprocess.SubprocessError, FileNotFoundError):
                    continue
            
            if not working_python:
                print("❌ No Python installation with PyQt6 found.")
                print("Please install PyQt6 in your system Python: pip install PyQt6")
                print("Or run from a virtual environment with PyQt6 installed.")
                return False
            
            # Launch GUI using the working Python
            print(f"🚀 Launching GUI with {working_python}...")
            
            # Use CREATE_NEW_CONSOLE to create a new window
            if platform.system() == "Windows":
                subprocess.Popen(
                    [working_python, gui_file],
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                    cwd=os.path.dirname(os.path.abspath(gui_file))
                )
            else:
                subprocess.Popen(
                    [working_python, gui_file],
                    cwd=os.path.dirname(os.path.abspath(gui_file))
                )
            
            print("✅ GUI launched successfully in separate process")
            return True
            
        except Exception as e:
            print(f"❌ Failed to launch GUI subprocess: {e}")
            return False

    def start_build(self, process_type="build"):
        """Start build process with different types"""
        if process_type.lower() == "build":
            return self.execute_pyinstaller_build()
        elif process_type.lower() == "quick":
            return self.execute_quick_build()
        elif process_type.lower() == "custom":
            return self.execute_custom_build()
        else:
            print(f"❌ Unknown build type: {process_type}")
            print("Available types: build, quick, custom")
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
            # Also include icon in data files
            command.extend(["--add-data", f"{icon_path};."])
        
        # Include scan results as data files
        scan_results = self.memory.get_scan_results()
        for scan_type, files in scan_results.items():
            if scan_type in ['config', 'data', 'templates', 'docs']:
                for file_path in files:
                    if os.path.exists(file_path):
                        # Add as data file
                        command.extend(["--add-data", f"{file_path};."])
        
        # Main entry point
        main_file = os.path.abspath(config['main_file'])
        command.append(main_file)
        
        return command

    def generate_build_filename(self, config):
        """Generate build filename based on configuration"""
        name = config.get('name', 'BuildToolApp')
        include_date = config.get('include_date', True)
        version = config.get('version', '')
        
        # Clean name
        name = re.sub(r'[^\w\-_.]', '_', name)
        
        # Add version if specified
        if version:
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
                if any(gui in content.lower() for gui in ['tkinter', 'pyqt', 'pyside', 'wx']):
                    score += 15
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
        """Detect if the application is a GUI app"""
        try:
            with open(main_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read().lower()
            
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
        print(f"Interface: {'GUI (Windowed)' if config.get('windowed') else 'Console'}")
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
            print(f"\n🔨 Starting build process...")
            print(f"Command: {' '.join(command[:3])} ... {command[-1]}")
            
            # Execute command
            result = subprocess.run(command, capture_output=False, text=True)
            
            if result.returncode == 0:
                print("\n" + "=" * 60)
                print("  🎉 BUILD SUCCESSFUL! 🎉")
                print("=" * 60)
                print("✅ Executable created successfully!")
                print("📁 Check the 'dist' folder for your executable.")
                print(f"🚀 Your application is ready to distribute!")
                return True
            else:
                print("\n" + "=" * 60)
                print("  ❌ BUILD FAILED!")
                print("=" * 60)
                print("Check the output above for error details.")
                print("💡 Common issues:")
                print("   • Missing dependencies (install with pip)")
                print("   • Invalid file paths")
                print("   • PyInstaller not installed (pip install pyinstaller)")
                return False
                
        except FileNotFoundError:
            print("\n❌ Error: PyInstaller not found!")
            print("📦 Install with: pip install pyinstaller")
            return False
        except Exception as e:
            print(f"\n❌ Build execution error: {e}")
            return False

def main():
    """Simplified core entry point - mainly for downloading and core functions"""
    core = BuildToolCore()
    
    parser = argparse.ArgumentParser(
        description="PyInstaller Build Tool - Core Functions (Use build_cli.py for full CLI)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Core Module Usage:
  %(prog)s --download-gui           Download GUI interface module
  %(prog)s --download-cli           Download CLI module
  %(prog)s --download-exe TYPE      Download executable (cli/gui/full)
  %(prog)s --scan TYPE              Scan for files (when called directly)
  %(prog)s --gui                    Launch GUI interface

Note: For full CLI functionality, use build_cli.py instead.
This module is primarily for downloading components and core operations.
        """
    )
    
    parser.add_argument('--download-gui', action='store_true',
                       help='Download or update GUI module')
    parser.add_argument('--download-cli', action='store_true',
                       help='Download or update CLI module')
    parser.add_argument('--download-exe', choices=['cli', 'gui', 'full'],
                       help='Download executable from GitHub releases (cli/gui/full)')
    parser.add_argument('--gui', action='store_true',
                       help='Launch GUI interface')
    parser.add_argument('--scan', type=str,
                       help='Scan for files (when using core directly)')
    parser.add_argument('--append', action='store_true',
                       help='Append scan results instead of replacing')
    parser.add_argument('--contains', type=str,
                       help='Filter scan results containing specific text')
    parser.add_argument('--scan-dir', type=str,
                       help='Directory to scan (default: current directory)')
    
    args = parser.parse_args()
    
    if args.gui:
        return core.launch_gui()
    
    elif args.download_gui:
        return core.download_gui_module()
        
    elif args.download_cli:
        return core.download_cli_module()
        
    elif args.download_exe:
        return core.download_executable(args.download_exe)
    
    elif args.scan:
        scan_dir = args.scan_dir if args.scan_dir else os.getcwd()
        results = core.handle_scan_command(
            args.scan, 
            append_mode=args.append,
            scan_directory=scan_dir,
            contains_filter=args.contains
        )
        print(f"Core scan completed - found {len(results)} files")
        return len(results) > 0
        
    else:
        print("PyInstaller Build Tool - Core Module")
        print("=" * 40)
        print("For full CLI functionality, use: python build_cli.py --help")
        print("This core module is primarily for:")
        print("• Downloading GUI/CLI modules")
        print("• Direct scanning operations")
        print("• Providing core functions to CLI and GUI")
        print()
        parser.print_help()
        return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
