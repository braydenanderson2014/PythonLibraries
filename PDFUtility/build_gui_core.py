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
from datetime import datetime
from pathlib import Path

class BuildToolCore:
    """Core functionality shared between CLI and GUI versions"""
    
    def __init__(self):
        self.config = self.load_environment_config()
        self.memory_file = "build_console_memory.json"
        
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
        repo_name = self.config.get('GITHUB_REPO_NAME', 'Build_Script')
        
        try:
            url = f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}/main/build_gui_interface.py"
            
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

def main():
    """Main CLI entry point"""
    core = BuildToolCore()
    
    parser = argparse.ArgumentParser(
        description="PyInstaller Build Tool - Fast CLI Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --help                   Show this help message
  %(prog)s --gui                    Launch GUI interface (downloads if needed)
  %(prog)s --repo-status            Check GitHub repository status
  %(prog)s --version                Show version information
  %(prog)s --download-gui           Download/update GUI module
  %(prog)s --download-exe gui       Download GUI executable from GitHub
  %(prog)s --download-exe cli       Download CLI executable from GitHub
  %(prog)s --download-exe full      Download full package executable
        """
    )
    
    parser.add_argument('--gui', action='store_true',
                       help='Launch GUI interface (downloads GUI module if needed)')
    parser.add_argument('--repo-status', action='store_true',
                       help='Check GitHub repository status')
    parser.add_argument('--version', action='store_true',
                       help='Show version information')
    parser.add_argument('--update', action='store_true',
                       help='Check for available updates')
    parser.add_argument('--download-gui', action='store_true',
                       help='Download or update GUI module')
    parser.add_argument('--download-exe', choices=['cli', 'gui', 'full'],
                       help='Download executable from GitHub releases (cli/gui/full)')
    parser.add_argument('--changelog', action='store_true',
                       help='Show recent changes and updates')
    
    args = parser.parse_args()
    
    if args.gui:
        return core.launch_gui()
    
    elif args.repo_status:
        print("Checking repository status...")
        status = core.check_repository_status()
        
        if "error" in status:
            print(f"❌ Error: {status['error']}")
            return False
            
        print(f"\n📊 Repository Status for {status['name']}")
        print(f"Description: {status['description']}")
        print(f"⭐ Stars: {status['stars']} | 🍴 Forks: {status['forks']}")
        print(f"Language: {status['language']} | Size: {status['size']} KB")
        print(f"Last Updated: {status['updated_at']}")
        
        if 'recent_commits' in status:
            print(f"\n📝 Recent Commits:")
            for commit in status['recent_commits']:
                print(f"  {commit['sha']} - {commit['message']} ({commit['author']})")
                
        if 'latest_release' in status:
            release = status['latest_release']
            print(f"\n🚀 Latest Release: {release['tag_name']}")
            if release['tag_name'] != "None":
                print(f"  Name: {release['name']}")
                print(f"  Published: {release['published_at']}")
                if 'download_count' in release:
                    print(f"  Downloads: {release['download_count']}")
        
        return True
        
    elif args.version:
        current_version = core.config.get('CURRENT_VERSION', '1.0.0')
        tool_name = core.config.get('BUILD_TOOL_NAME', 'PyInstaller Build Tool Enhanced')
        author = core.config.get('BUILD_TOOL_AUTHOR', 'Enhanced Build System')
        
        print(f"{tool_name}")
        print(f"Version: {current_version}")
        print(f"Author: {author}")
        print(f"Platform: {platform.system()} {platform.release()}")
        print(f"Python: {sys.version.split()[0]}")
        return True
        
    elif args.download_gui:
        return core.download_gui_module()
        
    elif args.download_exe:
        return core.download_executable(args.download_exe)
        
    elif args.changelog:
        print("📋 Recent Changes and Updates:")
        print("• Modular architecture with separate CLI and GUI components")
        print("• Fast CLI launcher with minimal dependencies")
        print("• On-demand GUI module downloading")
        print("• GitHub integration for repository status and updates")
        print("• Environment-based configuration system")
        return True
        
    elif args.update:
        print("🔍 Checking for updates...")
        print("Update system coming soon!")
        return True
        
    else:
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
