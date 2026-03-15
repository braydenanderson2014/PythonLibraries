#!/usr/bin/env python3
"""
PyInstaller Build Tool - CLI Core Module
Complete CLI interface with integrated core functionality (no GUI dependencies)
This module serves as both the CLI interface and the core functionality
"""

import sys
import os
import json
import hashlib
import platform
import subprocess
import time
import tempfile
from datetime import datetime
from pathlib import Path
import argparse
import urllib.request
import urllib.parse
import tempfile
import subprocess
import platform
import glob
import shutil
import re
import hashlib
from datetime import datetime
from pathlib import Path
import threading
import time

# ============================================================================
# PROGRESS TRACKING AND GUI COMMUNICATION SYSTEM
# ============================================================================

class ProgressTracker:
    """Thread-safe progress tracking system for GUI-CLI communication"""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._progress_file = os.path.join(tempfile.gettempdir(), 'build_cli_progress.json')
        self._history_file = os.path.join(tempfile.gettempdir(), 'build_cli_history.json')
        self.reset()
    
    def reset(self):
        """Reset progress to initial state"""
        with self._lock:
            self._progress = {
                'status': 'idle',
                'operation': '',
                'current_step': 0,
                'total_steps': 0,
                'progress_percent': 0,
                'current_task': '',
                'subtask': '',
                'start_time': None,
                'elapsed_time': 0,
                'estimated_remaining': 0,
                'error': None,
                'warnings': [],
                'completed': False,
                'last_update': datetime.now().isoformat()
            }
            self._save_progress()
    
    def start_operation(self, operation, total_steps=100):
        """Start a new operation"""
        with self._lock:
            self._progress.update({
                'status': 'running',
                'operation': operation,
                'current_step': 0,
                'total_steps': total_steps,
                'progress_percent': 0,
                'current_task': operation,
                'subtask': '',
                'start_time': datetime.now().isoformat(),
                'elapsed_time': 0,
                'error': None,
                'warnings': [],
                'completed': False,
                'last_update': datetime.now().isoformat()
            })
            self._save_progress()
    
    def update_progress(self, current_step=None, task=None, subtask=None, error=None, warning=None):
        """Update current progress"""
        with self._lock:
            if current_step is not None:
                self._progress['current_step'] = current_step
                if self._progress['total_steps'] > 0:
                    self._progress['progress_percent'] = min(100, (current_step / self._progress['total_steps']) * 100)
            
            if task is not None:
                self._progress['current_task'] = task
            
            if subtask is not None:
                self._progress['subtask'] = subtask
            
            if error is not None:
                self._progress['error'] = error
                self._progress['status'] = 'error'
            
            if warning is not None:
                self._progress['warnings'].append({
                    'message': warning,
                    'timestamp': datetime.now().isoformat()
                })
            
            # Calculate elapsed time
            if self._progress['start_time']:
                start = datetime.fromisoformat(self._progress['start_time'])
                elapsed = datetime.now() - start
                self._progress['elapsed_time'] = elapsed.total_seconds()
                
                # Estimate remaining time
                if self._progress['progress_percent'] > 0:
                    total_estimated = (elapsed.total_seconds() / self._progress['progress_percent']) * 100
                    self._progress['estimated_remaining'] = max(0, total_estimated - elapsed.total_seconds())
            
            self._progress['last_update'] = datetime.now().isoformat()
            self._save_progress()
    
    def complete_operation(self, success=True, final_message=None):
        """Mark operation as complete"""
        with self._lock:
            self._progress.update({
                'status': 'completed' if success else 'failed',
                'current_step': self._progress['total_steps'],
                'progress_percent': 100 if success else self._progress['progress_percent'],
                'completed': True,
                'last_update': datetime.now().isoformat()
            })
            
            if final_message:
                self._progress['current_task'] = final_message
            
            self._save_progress()
            
            # Save to history
            self._save_to_history()
    
    def get_progress(self):
        """Get current progress (for GUI polling)"""
        with self._lock:
            return self._progress.copy()
    
    def _save_progress(self):
        """Save progress to file for GUI access"""
        try:
            with open(self._progress_file, 'w', encoding='utf-8') as f:
                json.dump(self._progress, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save progress: {e}")
    
    def _save_to_history(self):
        """Save completed operation to history"""
        try:
            history = []
            if os.path.exists(self._history_file):
                with open(self._history_file, 'r') as f:
                    history = json.load(f)
            
            # Add current operation to history
            history_entry = {
                'operation': self._progress['operation'],
                'status': self._progress['status'],
                'duration': self._progress['elapsed_time'],
                'timestamp': self._progress['last_update'],
                'error': self._progress.get('error'),
                'warnings_count': len(self._progress.get('warnings', []))
            }
            
            history.insert(0, history_entry)  # Most recent first
            
            # Keep only last 50 entries
            history = history[:50]
            
            with open(self._history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2)
                
        except Exception as e:
            print(f"Warning: Could not save to history: {e}")

class CommandHistory:
    """Command history management for last-run recall"""
    
    def __init__(self):
        self._history_file = os.path.join(tempfile.gettempdir(), 'build_cli_commands.json')
        self._max_history = 100
    
    def add_command(self, command, args=None, success=None, duration=None):
        """Add command to history"""
        try:
            history = self.get_history()
            
            entry = {
                'command': command,
                'args': args or [],
                'timestamp': datetime.now().isoformat(),
                'success': success,
                'duration': duration
            }
            
            # Remove duplicates (same command with same args)
            history = [h for h in history if not (h['command'] == command and h.get('args') == args)]
            
            # Add to front
            history.insert(0, entry)
            
            # Limit size
            history = history[:self._max_history]
            
            with open(self._history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2)
                
        except Exception as e:
            print(f"Warning: Could not save command history: {e}")
    
    def get_history(self, limit=20):
        """Get command history"""
        try:
            if os.path.exists(self._history_file):
                with open(self._history_file, 'r') as f:
                    return json.load(f)[:limit]
        except Exception as e:
            print(f"Warning: Could not load command history: {e}")
        return []
    
    def get_last_command(self):
        """Get the last successful command"""
        history = self.get_history(10)
        for entry in history:
            if entry.get('success', False):
                return entry
        return None

# Global instances
progress_tracker = ProgressTracker()
command_history = CommandHistory()

class TUIEnhancements:
    """TUI enhancement utilities for better user experience"""
    
    @staticmethod
    def show_progress_bar(current, total, width=50, task=""):
        """Display a progress bar"""
        if total == 0:
            percent = 100
        else:
            percent = min(100, (current / total) * 100)
        
        filled = int(width * percent / 100)
        bar = '█' * filled + '░' * (width - filled)
        
        print(f"\r{task} [{bar}] {percent:.1f}% ({current}/{total})", end='', flush=True)
        
        if current >= total:
            print()  # New line when complete
    
    @staticmethod
    def searchable_list(items, title="Select items", multi_select=False, search_prompt="Search"):
        """Interactive searchable list with optional multi-select"""
        if not items:
            print("No items available")
            return [] if multi_select else None
        
        print(f"\n{title}")
        print("=" * len(title))
        print(f"💡 Type '{search_prompt.lower()}' to filter, 'q' to quit")
        if multi_select:
            print("💡 Use space to toggle selection, Enter to confirm")
        
        filtered_items = items[:]
        selected = set() if multi_select else None
        search_term = ""
        
        while True:
            # Clear screen section and show current state
            print(f"\nSearch: {search_term}")
            print("-" * 40)
            
            # Show filtered items
            for i, item in enumerate(filtered_items[:10]):  # Show max 10
                marker = ""
                if multi_select and item in selected:
                    marker = "✓ "
                print(f"{i+1:2}. {marker}{item}")
            
            if len(filtered_items) > 10:
                print(f"    ... and {len(filtered_items) - 10} more (refine search)")
            
            if multi_select and selected:
                print(f"\nSelected: {len(selected)} items")
            
            try:
                choice = input(f"\nEnter choice (1-{min(10, len(filtered_items))}), search term, or command: ").strip()
                
                if choice.lower() == 'q':
                    return [] if multi_select else None
                
                if choice.lower() == 'all' and multi_select:
                    selected.update(filtered_items)
                    continue
                
                if choice.lower() == 'none' and multi_select:
                    selected.clear()
                    continue
                
                if choice == "" and multi_select:
                    return list(selected)
                
                # Try to parse as number
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < min(10, len(filtered_items)):
                        item = filtered_items[idx]
                        if multi_select:
                            if item in selected:
                                selected.remove(item)
                            else:
                                selected.add(item)
                        else:
                            return item
                    else:
                        print("Invalid selection")
                except ValueError:
                    # Use as search term
                    search_term = choice.lower()
                    filtered_items = [item for item in items if search_term in item.lower()]
                    
            except KeyboardInterrupt:
                return [] if multi_select else None
    
    @staticmethod
    def bulk_file_operations(scan_results, operation_type="add"):
        """Bulk file operations with pattern matching"""
        print(f"\n🔄 Bulk {operation_type.title()} Operations")
        print("=" * 40)
        
        patterns = {
            'images': ['*.png', '*.jpg', '*.jpeg', '*.gif', '*.bmp', '*.tiff'],
            'icons': ['*.ico'],
            'configs': ['*.json', '*.yaml', '*.yml', '*.ini'],
            'docs': ['*.md', '*.txt', '*.pdf', '*.doc'],
            'assets': ['assets/*', 'static/*', 'resources/*'],
            'all': ['*']
        }
        
        print("Available bulk operations:")
        for i, (name, pattern_list) in enumerate(patterns.items(), 1):
            example_pattern = pattern_list[0] if len(pattern_list) == 1 else f"{pattern_list[0]} + {len(pattern_list)-1} more"
            print(f"{i}. {name.title()}: {example_pattern}")
        
        choice = input("\nSelect operation (1-6) or enter custom pattern: ").strip()
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(patterns):
                selected_patterns = list(patterns.values())[idx]
                operation_name = list(patterns.keys())[idx]
            else:
                return []
        except ValueError:
            # Custom pattern
            selected_patterns = [choice]
            operation_name = "custom"
        
        # Find matching files
        matching_files = []
        for scan_type, files in scan_results.items():
            for file_path in files:
                for pattern in selected_patterns:
                    if pattern == '*' or glob.fnmatch.fnmatch(file_path.lower(), pattern.lower()):
                        matching_files.append(file_path)
                        break
        
        matching_files = list(set(matching_files))  # Remove duplicates
        
        if not matching_files:
            print(f"No files found matching {operation_name} patterns")
            return []
        
        print(f"\nFound {len(matching_files)} matching files:")
        for i, f in enumerate(matching_files[:5]):
            print(f"  {i+1}. {os.path.basename(f)}")
        
        if len(matching_files) > 5:
            print(f"  ... and {len(matching_files) - 5} more")
        
        confirm = input(f"\nProceed with {operation_type} for all {len(matching_files)} files? (y/n): ").lower()
        
        if confirm == 'y':
            return matching_files
        
        return []

# ============================================================================
# ============================================================================
# MULTI-SANDBOX TESTING SYSTEM
# ============================================================================

class BaseSandboxManager:
    """Base class for all sandbox testing environments"""

    def __init__(self, sandbox_type):
        self.sandbox_type = sandbox_type
        self.sandbox_dir = os.path.join(os.getcwd(), f'{sandbox_type.lower()}_test')
        self.host_folder = os.path.join(self.sandbox_dir, 'host_share')

    def is_available(self):
        """Check if this sandbox type is available on the current system"""
        raise NotImplementedError("Subclasses must implement is_available()")

    def create_environment(self, config):
        """Create the sandbox environment files"""
        raise NotImplementedError("Subclasses must implement create_environment()")

    def launch_sandbox(self, config):
        """Launch the sandbox environment"""
        raise NotImplementedError("Subclasses must implement launch_sandbox()")

    def get_requirements(self):
        """Get system requirements for this sandbox type"""
        raise NotImplementedError("Subclasses must implement get_requirements()")

class WindowsSandboxManager(BaseSandboxManager):
    """Windows Sandbox testing system for clean machine testing"""

    def __init__(self):
        super().__init__('windows_sandbox')
        self.wsb_file = os.path.join(self.sandbox_dir, 'test_environment.wsb')

    def is_available(self):
        """Validate that we're running on Windows with Sandbox support"""
        try:
            if platform.system() != 'Windows':
                return False, "Windows Sandbox is only available on Windows systems"

            print("[SCAN] Detailed Windows Sandbox compatibility check...")

            # Check Windows version (Sandbox requires Windows 10 Pro/Enterprise/Education)
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
                build_number = int(winreg.QueryValueEx(key, "CurrentBuildNumber")[0])
                winreg.CloseKey(key)

                if build_number < 18305:
                    return False, f"Windows Sandbox requires Windows 10 build 18305 or later. Current build: {build_number}"

                # Check if Windows edition supports Sandbox
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
                    edition = winreg.QueryValueEx(key, "EditionID")[0]
                    winreg.CloseKey(key)

                    if edition == "Core":  # Windows 10 Home
                        print("   [X] Windows 10 Home does NOT support Windows Sandbox")
                        print("   [TIP] Windows Sandbox requires Pro, Enterprise, or Education edition")
                        return False, "Windows 10 Home does not support Windows Sandbox"

                    print(f"   ✅ Windows {edition} edition supports Windows Sandbox")

                except Exception as e:
                    print(f"   ⚠️  Warning: Could not verify Windows edition details: {e}")
                    print(f"   ⚠️  Warning: Windows Sandbox typically requires Pro/Enterprise/Education edition")

            except ImportError:
                return False, "Windows registry access not available"
            except Exception as e:
                print(f"   ⚠️  Warning: Could not verify Windows version details: {e}")
                return False, f"Could not verify Windows version: {e}"

            # Check if Windows Sandbox feature is available
            print("   [SCAN] Checking Windows Sandbox feature availability...")
            try:
                result = subprocess.run(['powershell', '-Command',
                    'Get-WindowsOptionalFeature -Online -FeatureName Containers-DisposableClientVM'],
                    capture_output=True, text=True, timeout=10)

                if result.returncode == 0 and 'Enabled' in result.stdout:
                    print("   [OK] Windows Sandbox feature is ENABLED")
                    return self.verify_sandbox_executable()
                else:
                    print("   [X] Windows Sandbox feature is DISABLED")
                    return False, "Windows Sandbox feature is not enabled"

            except subprocess.TimeoutExpired:
                return False, "Windows Sandbox feature check timed out"
            except Exception as e:
                print(f"   [WARN] Could not check Windows Sandbox feature: {e}")
                return False, f"Could not verify Windows Sandbox feature: {e}"

        except Exception as e:
            return False, f"Windows Sandbox compatibility check failed: {e}"

    def verify_sandbox_executable(self):
        """Verify that WindowsSandbox.exe exists and is accessible"""
        try:
            sandbox_path = r"C:\Windows\System32\WindowsSandbox.exe"
            if os.path.exists(sandbox_path):
                print("   [OK] WindowsSandbox.exe found")
                return True, "Windows Sandbox is ready"
            else:
                print("   [X] WindowsSandbox.exe not found")
                return False, "WindowsSandbox.exe not found in expected location"
        except Exception as e:
            return False, f"Could not verify WindowsSandbox.exe: {e}"

    def get_requirements(self):
        """Get system requirements for Windows Sandbox"""
        return {
            'os': 'Windows 10 Pro/Enterprise/Education or Windows 11 Pro/Enterprise',
            'build': '18305 or later',
            'features': ['Virtualization enabled in BIOS/UEFI', 'Windows Sandbox feature enabled'],
            'ram': 'Minimum 4GB available RAM',
            'storage': 'Minimum 1GB free space'
        }

    def create_environment(self, config):
        """Create Windows Sandbox environment (.wsb file)"""
        try:
            os.makedirs(self.sandbox_dir, exist_ok=True)
            os.makedirs(self.host_folder, exist_ok=True)

            # Create the .wsb configuration file
            wsb_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<Configuration>
    <VGpu>{config.get('vgpu', 'Default')}</VGpu>
    <Networking>{config.get('networking', 'Default')}</Networking>
    <MappedFolders>
        <MappedFolder>
            <HostFolder>{self.host_folder}</HostFolder>
            <SandboxFolder>C:\\Users\\WDAGUtilityAccount\\Desktop\\HostFiles</SandboxFolder>
            <ReadOnly>true</ReadOnly>
        </MappedFolder>
    </MappedFolders>
    <LogonCommand>
        <Command>powershell.exe -ExecutionPolicy Bypass -File C:\\Users\\WDAGUtilityAccount\\Desktop\\HostFiles\\setup.ps1</Command>
    </LogonCommand>
</Configuration>'''

            with open(self.wsb_file, 'w', encoding='utf-8') as f:
                f.write(wsb_content)

            # Create setup script for the sandbox
            setup_script = os.path.join(self.host_folder, 'setup.ps1')
            with open(setup_script, 'w', encoding='utf-8') as f:
                f.write(self._generate_setup_script(config))

            # Copy requirements and test files
            self._copy_test_files(config)

            return True, f"Windows Sandbox environment created at {self.wsb_file}"

        except Exception as e:
            return False, f"Failed to create Windows Sandbox environment: {e}"

    def _generate_setup_script(self, config):
        """Generate PowerShell setup script for Windows Sandbox"""
        venv_name = config.get('venv_name', 'test_env')

        script = f'''# Windows Sandbox Setup Script
Write-Host "🚀 Setting up test environment in Windows Sandbox..." -ForegroundColor Green

# Create desktop shortcuts
$desktopPath = "C:\\Users\\WDAGUtilityAccount\\Desktop"

# Copy test files to desktop
if (Test-Path "C:\\Users\\WDAGUtilityAccount\\Desktop\\HostFiles\\*") {{
    Copy-Item "C:\\Users\\WDAGUtilityAccount\\Desktop\\HostFiles\\*" $desktopPath -Recurse -Force
}}

# Install Python if needed
$pythonInstalled = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonInstalled) {{
    Write-Host "⚠️ Python not found in sandbox - this is expected for minimal testing" -ForegroundColor Yellow
}}

Write-Host "✅ Sandbox environment setup complete!" -ForegroundColor Green
Write-Host "📁 Test files are available on the desktop" -ForegroundColor Cyan

# Keep the window open
Read-Host "Press Enter to exit"
'''

        return script

    def _copy_test_files(self, config):
        """Copy test files to the sandbox host folder"""
        try:
            # Copy requirements.txt if it exists
            req_file = config.get('requirements_file', 'requirements.txt')
            if os.path.exists(req_file):
                shutil.copy2(req_file, self.host_folder)

            # Create test files if requested
            if config.get('additional_files'):
                for test_file in config.get('additional_files', []):
                    test_path = os.path.join(self.host_folder, test_file)
                    with open(test_path, 'w') as f:
                        f.write(f"# Test file: {test_file}\n# Generated for Windows Sandbox testing\n")

            # Create a README for the sandbox
            readme_path = os.path.join(self.host_folder, 'SANDBOX_README.txt')
            with open(readme_path, 'w') as f:
                f.write(self._generate_readme(config))

        except Exception as e:
            print(f"[WARN] Could not copy test files: {e}")

    def _generate_readme(self, config):
        """Generate README for Windows Sandbox testing"""
        return f'''WINDOWS SANDBOX TEST ENVIRONMENT
=====================================

This is a clean Windows environment for testing your application.

TEST ENVIRONMENT DETAILS:
- Virtual Environment Name: {config.get('venv_name', 'test_env')}
- Memory: {config.get('memory_mb', 4096)}MB
- GPU: {config.get('vgpu', 'Default')}
- Networking: {config.get('networking', 'Default')}

FILES AVAILABLE:
- Host files are mapped to: C:\\Users\\WDAGUtilityAccount\\Desktop\\HostFiles
- All files from the host folder are available on the desktop

TESTING INSTRUCTIONS:
1. Double-click any .exe files to test installation
2. Run .msi files to test installer packages
3. Check .txt and .json files for configuration details
4. Test networking if enabled

NOTES:
- This is a temporary environment - all changes will be lost when closed
- No persistent data is saved
- Test thoroughly before distributing to end users

Generated by PyInstaller Build Tool
'''

    def launch_sandbox(self, config):
        """Launch Windows Sandbox with the created environment"""
        try:
            if not os.path.exists(self.wsb_file):
                return False, "Sandbox environment file not found. Run creation first."

            print(f"[LAUNCH] Starting Windows Sandbox...")
            print(f"[FILE] {self.wsb_file}")

            # Launch the .wsb file (this will open it with Windows Sandbox)
            result = subprocess.run(['cmd', '/c', 'start', '', self.wsb_file],
                                  capture_output=True, text=True)

            if result.returncode == 0:
                return True, "Windows Sandbox launched successfully"
            else:
                return False, f"Failed to launch Windows Sandbox: {result.stderr}"

        except Exception as e:
            return False, f"Error launching Windows Sandbox: {e}"

    def install_windows_sandbox(self):
        """Install/Enable Windows Sandbox feature"""
        safe_print("\n🔧 Installing Windows Sandbox feature...")
        
        try:
            # Use the existing admin privilege system
            if not is_admin():
                safe_print("🔒 Administrative privileges required for Windows Sandbox installation")
                
                # Ask for confirmation before requesting privileges
                try:
                    choice = input("Request admin privileges now? (y/n): ").lower().strip()
                    if choice not in ['y', 'yes']:
                        safe_print("⚠️  Installation cancelled")
                        return False
                except KeyboardInterrupt:
                    safe_print("\n⚠️  Installation cancelled")
                    return False
                
                # Request admin privileges with output capture
                safe_print("🔒 Requesting administrator privileges with output capture...")
                success, output = request_admin_privileges_with_output()
                
                if not success:
                    safe_print("❌ Failed to obtain administrator privileges")
                    safe_print("💡 Manual installation:")
                    safe_print("   1. Open Command Prompt as Administrator")
                    safe_print("   2. Run: python build_cli.py --sandbox --install")
                    if output:
                        safe_print("ℹ️  Elevation output:")
                        safe_print(output)
                    return False
                
                # Display captured output from elevated process
                if output:
                    safe_print("ℹ️  Output from elevated installation:")
                    safe_print("="*50)
                    safe_print(output)
                    safe_print("="*50)
                
                return success
            
            # We have admin privileges, proceed with installation
            safe_print("✅ Running with administrator privileges")
            
            # Enable Windows Sandbox feature using DISM
            safe_print("   📦 Enabling Windows Sandbox feature...")
            result = subprocess.run([
                'dism', '/online', '/Enable-Feature', 
                '/FeatureName:Containers-DisposableClientVM', '/All', '/NoRestart'
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                safe_print("   ✅ Windows Sandbox feature enabled successfully!")
                safe_print("")
                safe_print("⚠️  RESTART REQUIRED:")
                safe_print("   Your computer must be restarted for changes to take effect")
                safe_print("   After restart, run: python build_cli.py --sandbox")
                
                # Offer automatic restart
                try:
                    restart_choice = input("\nRestart now? (y/n): ").lower().strip()
                    if restart_choice in ['y', 'yes']:
                        safe_print("ℹ️  Restarting system in 10 seconds...")
                        safe_print("   Press Ctrl+C to cancel")
                        try:
                            time.sleep(10)
                            subprocess.run(['shutdown', '/r', '/t', '0'])
                        except KeyboardInterrupt:
                            safe_print("   Restart cancelled - please restart manually")
                except KeyboardInterrupt:
                    safe_print("\n   Restart cancelled - please restart manually")
                
                return True
                
            else:
                safe_print(f"   ❌ Failed to enable Windows Sandbox (exit code: {result.returncode})")
                if result.stderr.strip():
                    safe_print(f"   ❌ Error: {result.stderr.strip()}")
                if result.stdout.strip():
                    safe_print(f"   ℹ️  Output: {result.stdout.strip()}")
                    
                # Check if it's already enabled
                if "already enabled" in result.stdout.lower() or "already enabled" in result.stderr.lower():
                    safe_print("   💡 Windows Sandbox may already be enabled - restart required")
                    return True
                
                safe_print("")
                safe_print("💡 Manual installation alternatives:")
                safe_print("   1. Open PowerShell as Administrator")
                safe_print("   2. Run: Enable-WindowsOptionalFeature -Online -FeatureName Containers-DisposableClientVM -All")
                safe_print("   3. Or use: dism /online /Enable-Feature /FeatureName:\"Containers-DisposableClientVM\" /All")
                safe_print("   4. Restart your computer")
                return False
                
        except subprocess.TimeoutExpired:
            safe_print("   ⏰ Installation timed out (Windows features can take time)")
            safe_print("   💡 The installation may still be in progress")
            return False
        except Exception as e:
            safe_print(f"   ❌ Installation error: {e}")
            return False

class VirtualBoxSandboxManager(BaseSandboxManager):
    """VirtualBox sandbox testing system"""

    def __init__(self):
        super().__init__('virtualbox')
        self.vm_name = 'PyInstaller_Test_VM'

    def is_available(self):
        """Check if VirtualBox is installed and available"""
        try:
            # Check if VBoxManage command is available
            result = subprocess.run(['VBoxManage', '--version'],
                                  capture_output=True, text=True, timeout=5)

            if result.returncode == 0:
                version = result.stdout.strip()
                print(f"   ✅ VirtualBox {version} found")
                return True, f"VirtualBox {version} is available"
            else:
                return False, "VBoxManage command not found"

        except FileNotFoundError:
            return False, "VirtualBox is not installed"
        except subprocess.TimeoutExpired:
            return False, "VirtualBox version check timed out"
        except Exception as e:
            return False, f"VirtualBox check failed: {e}"

    def get_requirements(self):
        """Get system requirements for VirtualBox"""
        return {
            'software': 'Oracle VirtualBox',
            'os': 'Windows, macOS, Linux',
            'ram': 'Minimum 4GB available RAM',
            'storage': 'Minimum 10GB free space for VM',
            'cpu': 'VT-x/AMD-V virtualization support'
        }

    def create_environment(self, config):
        """Create VirtualBox VM environment"""
        try:
            print("[VBOX] Creating VirtualBox test environment...")

            # Create VM directory
            vm_dir = os.path.join(self.sandbox_dir, 'vm')
            os.makedirs(vm_dir, exist_ok=True)

            # Generate VM creation script
            script_path = os.path.join(self.sandbox_dir, 'create_vm.bat' if platform.system() == 'Windows' else 'create_vm.sh')

            script_content = self._generate_vbox_script(config)
            with open(script_path, 'w') as f:
                f.write(script_content)

            # Make script executable on Unix systems
            if platform.system() != 'Windows':
                os.chmod(script_path, 0o755)

            # Copy test files
            self._copy_vbox_test_files(config)

            return True, f"VirtualBox environment created. Run {script_path} to create VM"

        except Exception as e:
            return False, f"Failed to create VirtualBox environment: {e}"

    def _generate_vbox_script(self, config):
        """Generate VirtualBox VM creation script"""
        memory_mb = config.get('memory_mb', 2048)
        vm_name = config.get('vm_name', self.vm_name)

        if platform.system() == 'Windows':
            script = f'''@echo off
echo 🚀 Creating VirtualBox Test VM...
echo ===============================

REM Create VM
VBoxManage createvm --name "{vm_name}" --ostype "Windows10_64" --register

REM Configure VM
VBoxManage modifyvm "{vm_name}" --memory {memory_mb}
VBoxManage modifyvm "{vm_name}" --vram 128
VBoxManage modifyvm "{vm_name}" --cpus 2
VBoxManage modifyvm "{vm_name}" --nic1 nat
VBoxManage modifyvm "{vm_name}" --usb off
VBoxManage modifyvm "{vm_name}" --usbehci off

REM Create virtual disk
VBoxManage createhd --filename "%~dp0vm\\{vm_name}.vdi" --size 20480

REM Add storage controllers
VBoxManage storagectl "{vm_name}" --name "SATA Controller" --add sata --controller IntelAhci
VBoxManage storageattach "{vm_name}" --storagectl "SATA Controller" --port 0 --device 0 --type hdd --medium "%~dp0vm\\{vm_name}.vdi"

REM Add IDE controller for CD/DVD
VBoxManage storagectl "{vm_name}" --name "IDE Controller" --add ide

echo ✅ VirtualBox VM created successfully!
echo 📝 VM Name: {vm_name}
echo 💾 Memory: {memory_mb}MB
echo 📁 VM files: %~dp0vm\\
echo.
echo 🚀 To start the VM, run:
echo VBoxManage startvm "{vm_name}"
echo.
pause
'''
        else:
            script = f'''#!/bin/bash
echo "🚀 Creating VirtualBox Test VM..."
echo "==============================="

# Create VM
VBoxManage createvm --name "{vm_name}" --ostype "Windows10_64" --register

# Configure VM
VBoxManage modifyvm "{vm_name}" --memory {memory_mb}
VBoxManage modifyvm "{vm_name}" --vram 128
VBoxManage modifyvm "{vm_name}" --cpus 2
VBoxManage modifyvm "{vm_name}" --nic1 nat
VBoxManage modifyvm "{vm_name}" --usb off
VBoxManage modifyvm "{vm_name}" --usbehci off

# Create virtual disk
VBoxManage createhd --filename "$(dirname "$0")/vm/{vm_name}.vdi" --size 20480

# Add storage controllers
VBoxManage storagectl "{vm_name}" --name "SATA Controller" --add sata --controller IntelAhci
VBoxManage storageattach "{vm_name}" --storagectl "SATA Controller" --port 0 --device 0 --type hdd --medium "$(dirname "$0")/vm/{vm_name}.vdi"

# Add IDE controller for CD/DVD
VBoxManage storagectl "{vm_name}" --name "IDE Controller" --add ide

echo "✅ VirtualBox VM created successfully!"
echo "📝 VM Name: {vm_name}"
echo "💾 Memory: {memory_mb}MB"
echo "📁 VM files: $(dirname "$0")/vm/"
echo ""
echo "🚀 To start the VM, run:"
echo "VBoxManage startvm \\"{vm_name}\\""
'''

        return script

    def _copy_vbox_test_files(self, config):
        """Copy test files for VirtualBox environment"""
        try:
            # Create a README for VirtualBox testing
            readme_path = os.path.join(self.sandbox_dir, 'VIRTUALBOX_README.txt')
            with open(readme_path, 'w') as f:
                f.write(self._generate_vbox_readme(config))

            # Copy test files if specified
            if config.get('additional_files'):
                test_dir = os.path.join(self.sandbox_dir, 'test_files')
                os.makedirs(test_dir, exist_ok=True)

                for test_file in config.get('additional_files', []):
                    test_path = os.path.join(test_dir, test_file)
                    with open(test_path, 'w') as f:
                        f.write(f"# Test file: {test_file}\n# Generated for VirtualBox testing\n")

        except Exception as e:
            print(f"[WARN] Could not copy VirtualBox test files: {e}")

    def _generate_vbox_readme(self, config):
        """Generate README for VirtualBox testing"""
        return f'''VIRTUALBOX TEST ENVIRONMENT
===============================

This directory contains a VirtualBox test environment for your application.

VM CONFIGURATION:
- VM Name: {config.get('vm_name', self.vm_name)}
- Memory: {config.get('memory_mb', 2048)}MB
- CPUs: 2
- Disk: 20GB
- Network: NAT

FILES IN THIS DIRECTORY:
- create_vm.bat/sh: Script to create the VirtualBox VM
- vm/: Directory where VM files will be created
- test_files/: Test files for the VM (if --test-files was used)

CREATION INSTRUCTIONS:
1. Run the create_vm script to set up the VM
2. Start the VM using VirtualBox GUI or command line
3. Install your application in the VM for testing
4. Test thoroughly before distributing

TESTING BEST PRACTICES:
- Test on different OS versions if possible
- Verify installation and uninstallation
- Test with different hardware configurations
- Check compatibility with antivirus software
- Test network connectivity if your app requires it

NOTES:
- VM files can be large (20GB+)
- Clean up VMs after testing to save disk space
- Consider using snapshots for quick test iterations

Generated by PyInstaller Build Tool
'''

    def launch_sandbox(self, config):
        """Launch VirtualBox VM"""
        try:
            vm_name = config.get('vm_name', self.vm_name)

            print(f"[VBOX] Starting VirtualBox VM: {vm_name}")

            # Check if VM exists
            result = subprocess.run(['VBoxManage', 'list', 'vms'],
                                  capture_output=True, text=True)

            if vm_name not in result.stdout:
                return False, f"VM '{vm_name}' does not exist. Run creation script first."

            # Start the VM
            result = subprocess.run(['VBoxManage', 'startvm', vm_name],
                                  capture_output=True, text=True)

            if result.returncode == 0:
                return True, f"VirtualBox VM '{vm_name}' started successfully"
            else:
                return False, f"Failed to start VirtualBox VM: {result.stderr}"

        except Exception as e:
            return False, f"Error launching VirtualBox VM: {e}"

class DockerSandboxManager(BaseSandboxManager):
    """Docker container sandbox testing system"""

    def __init__(self):
        super().__init__('docker')
        self.container_name = 'pyinstaller_test'

    def is_available(self):
        """Check if Docker is installed and available"""
        try:
            # Check if docker command is available
            result = subprocess.run(['docker', '--version'],
                                  capture_output=True, text=True, timeout=5)

            if result.returncode == 0:
                version = result.stdout.strip()
                print(f"   ✅ Docker {version} found")

                # Check if Docker daemon is running
                result = subprocess.run(['docker', 'info'],
                                      capture_output=True, text=True, timeout=10)

                if result.returncode == 0:
                    return True, f"Docker is running and available"
                else:
                    return False, "Docker daemon is not running"
            else:
                return False, "Docker command not found"

        except FileNotFoundError:
            return False, "Docker is not installed"
        except subprocess.TimeoutExpired:
            return False, "Docker check timed out"
        except Exception as e:
            return False, f"Docker check failed: {e}"

    def get_requirements(self):
        """Get system requirements for Docker"""
        return {
            'software': 'Docker Desktop or Docker Engine',
            'os': 'Windows, macOS, Linux',
            'ram': 'Minimum 2GB available RAM',
            'storage': 'Minimum 5GB free space',
            'features': ['Docker daemon running', 'Docker images available']
        }

    def create_environment(self, config):
        """Create Docker container environment"""
        try:
            print("[DOCKER] Creating Docker test environment...")

            # Create Dockerfile
            dockerfile_path = os.path.join(self.sandbox_dir, 'Dockerfile')
            with open(dockerfile_path, 'w') as f:
                f.write(self._generate_dockerfile(config))

            # Create docker-compose.yml if needed
            compose_path = os.path.join(self.sandbox_dir, 'docker-compose.yml')
            with open(compose_path, 'w') as f:
                f.write(self._generate_docker_compose(config))

            # Create test script
            script_path = os.path.join(self.sandbox_dir, 'run_tests.sh')
            with open(script_path, 'w') as f:
                f.write(self._generate_docker_script(config))

            # Make script executable
            os.chmod(script_path, 0o755)

            # Copy test files
            self._copy_docker_test_files(config)

            return True, f"Docker environment created in {self.sandbox_dir}"

        except Exception as e:
            return False, f"Failed to create Docker environment: {e}"

    def _generate_dockerfile(self, config):
        """Generate Dockerfile for testing"""
        return f'''FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    wget \\
    curl \\
    vim \\
    htop \\
    && rm -rf /var/lib/apt/lists/*

# Create test user
RUN useradd -m -s /bin/bash testuser
USER testuser
WORKDIR /home/testuser

# Copy test files
COPY --chown=testuser:testuser . /home/testuser/test_files/

# Set up Python environment
RUN python -m pip install --user --upgrade pip

# Copy requirements if available
COPY --chown=testuser:testuser requirements.txt* /home/testuser/
RUN if [ -f requirements.txt ]; then pip install --user -r requirements.txt; fi

# Default command
CMD ["/bin/bash"]
'''

    def _generate_docker_compose(self, config):
        """Generate docker-compose.yml"""
        memory_mb = config.get('memory_mb', 1024)

        return f'''version: '3.8'

services:
  pyinstaller-test:
    build: .
    container_name: {self.container_name}
    volumes:
      - ./test_files:/home/testuser/test_results
    environment:
      - PYTHONPATH=/home/testuser/.local/lib/python3.9/site-packages
    mem_limit: {memory_mb}m
    mem_reservation: 512m
    restart: unless-stopped
    command: /bin/bash -c "echo '🐳 Docker test environment ready!' && tail -f /dev/null"
'''

    def _generate_docker_script(self, config):
        """Generate test script for Docker"""
        return f'''#!/bin/bash
echo "🐳 Docker Test Environment"
echo "=========================="

CONTAINER_NAME="{self.container_name}"

echo "📦 Building Docker image..."
docker-compose build

echo "🚀 Starting Docker container..."
docker-compose up -d

echo "⏳ Waiting for container to be ready..."
sleep 5

echo "🔍 Checking container status..."
docker ps | grep $CONTAINER_NAME

echo ""
echo "✅ Docker test environment is ready!"
echo ""
echo "🔧 Useful commands:"
echo "  docker exec -it $CONTAINER_NAME /bin/bash    # Enter container"
echo "  docker-compose logs -f                       # View logs"
echo "  docker-compose down                          # Stop container"
echo "  docker-compose down -v                       # Stop and remove volumes"
echo ""
echo "📁 Test files are available in ./test_files/"
echo "📁 Container files are mapped to /home/testuser/test_results/"
'''

    def _copy_docker_test_files(self, config):
        """Copy test files for Docker environment"""
        try:
            # Create test files directory
            test_dir = os.path.join(self.sandbox_dir, 'test_files')
            os.makedirs(test_dir, exist_ok=True)

            # Create a README for Docker testing
            readme_path = os.path.join(self.sandbox_dir, 'DOCKER_README.txt')
            with open(readme_path, 'w') as f:
                f.write(self._generate_docker_readme(config))

            # Copy test files if specified
            if config.get('additional_files'):
                for test_file in config.get('additional_files', []):
                    test_path = os.path.join(test_dir, test_file)
                    with open(test_path, 'w') as f:
                        f.write(f"# Test file: {test_file}\n# Generated for Docker testing\n")

        except Exception as e:
            print(f"[WARN] Could not copy Docker test files: {e}")

    def _generate_docker_readme(self, config):
        """Generate README for Docker testing"""
        return f'''DOCKER TEST ENVIRONMENT
=========================

This directory contains a Docker test environment for your application.

CONTAINER CONFIGURATION:
- Base Image: python:3.9-slim
- Memory Limit: {config.get('memory_mb', 1024)}MB
- Container Name: {self.container_name}
- User: testuser

FILES IN THIS DIRECTORY:
- Dockerfile: Container definition
- docker-compose.yml: Multi-container setup
- run_tests.sh: Script to start the environment
- test_files/: Directory for test files and results

QUICK START:
1. Run: ./run_tests.sh
2. Wait for the container to start
3. Enter the container: docker exec -it {self.container_name} /bin/bash
4. Test your application in the isolated environment

TESTING INSTRUCTIONS:
- Your application files should be copied to test_files/
- Test installation and execution in the container
- Verify all dependencies work correctly
- Test with different base images if needed

DOCKER COMMANDS:
- docker-compose build          # Build the container
- docker-compose up -d          # Start in background
- docker-compose logs -f        # View logs
- docker exec -it {self.container_name} /bin/bash  # Enter container
- docker-compose down           # Stop container

NOTES:
- Container is isolated from host system
- Changes in container are preserved until removed
- Use volumes for persistent test data
- Test multiple Python versions by changing base image

Generated by PyInstaller Build Tool
'''

    def launch_sandbox(self, config):
        """Launch Docker container"""
        try:
            print(f"[DOCKER] Starting Docker container: {self.container_name}")

            # Check if container exists and is running
            result = subprocess.run(['docker', 'ps', '-a', '--format', 'table {{.Names}}\\t{{.Status}}'],
                                  capture_output=True, text=True)

            if self.container_name in result.stdout:
                print(f"[DOCKER] Container {self.container_name} exists")

                # Check if it's running
                result = subprocess.run(['docker', 'ps', '--format', '{{.Names}}'],
                                      capture_output=True, text=True)

                if self.container_name in result.stdout:
                    return True, f"Docker container '{self.container_name}' is already running"
                else:
                    # Start existing container
                    result = subprocess.run(['docker', 'start', self.container_name],
                                          capture_output=True, text=True)

                    if result.returncode == 0:
                        return True, f"Docker container '{self.container_name}' started"
                    else:
                        return False, f"Failed to start Docker container: {result.stderr}"
            else:
                # Container doesn't exist, use docker-compose
                compose_file = os.path.join(self.sandbox_dir, 'docker-compose.yml')
                if os.path.exists(compose_file):
                    result = subprocess.run(['docker-compose', 'up', '-d'],
                                          cwd=self.sandbox_dir,
                                          capture_output=True, text=True)

                    if result.returncode == 0:
                        return True, f"Docker container '{self.container_name}' created and started"
                    else:
                        return False, f"Failed to create/start Docker container: {result.stderr}"
                else:
                    return False, "Docker compose file not found"

        except Exception as e:
            return False, f"Error launching Docker container: {e}"

class SandboxManagerFactory:
    """Factory for creating sandbox managers"""

    @staticmethod
    def get_available_sandboxes():
        """Get list of available sandbox types on this system"""
        sandboxes = []

        # Check Windows Sandbox
        windows_manager = WindowsSandboxManager()
        available, message = windows_manager.is_available()
        sandboxes.append({
            'type': 'windows',
            'name': 'Windows Sandbox',
            'available': available,
            'message': message,
            'manager': windows_manager
        })

        # Check VirtualBox
        vbox_manager = VirtualBoxSandboxManager()
        available, message = vbox_manager.is_available()
        sandboxes.append({
            'type': 'virtualbox',
            'name': 'VirtualBox',
            'available': available,
            'message': message,
            'manager': vbox_manager
        })

        # Check Docker
        docker_manager = DockerSandboxManager()
        available, message = docker_manager.is_available()
        sandboxes.append({
            'type': 'docker',
            'name': 'Docker',
            'available': available,
            'message': message,
            'manager': docker_manager
        })

        return sandboxes

    @staticmethod
    def create_sandbox_manager(sandbox_type):
        """Create a sandbox manager of the specified type"""
        if sandbox_type.lower() in ['windows', 'windows_sandbox']:
            return WindowsSandboxManager()
        elif sandbox_type.lower() in ['virtualbox', 'vbox']:
            return VirtualBoxSandboxManager()
        elif sandbox_type.lower() in ['docker', 'container']:
            return DockerSandboxManager()
        else:
            raise ValueError(f"Unsupported sandbox type: {sandbox_type}")

    def handle_enhanced_sandbox_testing():
        """Enhanced sandbox testing with multiple sandbox type support"""
        try:
            print("🚀 Multi-Sandbox Testing System")
            print("=" * 50)

            # Parse command line arguments
            config = {
                'venv_name': 'pdf_utility_env',
                'memory_mb': 4096,
                'vgpu': 'Default',
                'networking': 'Default',
                'create_venv': True,
                'test_type': 'smoke',
                'additional_files': [],
                'requirements_file': 'requirements.txt',
                'sandbox_type': 'auto',  # Auto-detect best available
                'vm_name': 'PyInstaller_Test_VM',
                'container_name': 'pyinstaller_test'
            }

            # Process command line arguments
            args = sys.argv
            install_only = False
            skip_validation = False
            dry_run = False

            i = 0
            while i < len(args):
                arg = args[i]

                # Sandbox type selection
                if arg == '--type' and i + 1 < len(args):
                    config['sandbox_type'] = args[i + 1]
                    i += 1
                elif arg == '--sandbox-type' and i + 1 < len(args):
                    config['sandbox_type'] = args[i + 1]
                    i += 1

                # Existing arguments
                elif arg == '--venv' and i + 1 < len(args):
                    config['venv_name'] = args[i + 1]
                    i += 1
                elif arg == '--memory' and i + 1 < len(args):
                    try:
                        config['memory_mb'] = int(args[i + 1])
                    except ValueError:
                        print(f"[WARN] Invalid memory value: {args[i + 1]}, using default 4096MB")
                    i += 1
                elif arg == '--no-vgpu':
                    config['vgpu'] = 'Disable'
                elif arg == '--offline':
                    config['networking'] = 'Disable'
                elif arg == '--install':
                    install_only = True
                elif arg == '--skip-validation':
                    skip_validation = True
                    print("[WARN] Skipping sandbox validation (development mode)")
                elif arg == '--dry-run':
                    dry_run = True
                    print("[TEST] Dry run mode - will create files but not launch sandbox")
                elif arg == '--test-files':
                    # Create some dummy test files for demonstration
                    test_files = [
                        'test_executable.exe',
                        'test_installer.msi',
                        'test_config.json',
                        'test_readme.txt'
                    ]
                    config['additional_files'] = test_files
                    print("[TEST] Test files mode - will create dummy files for testing")
                elif arg == '--portable':
                    # Create portable test package for systems without sandbox support
                    config['sandbox_type'] = 'portable'
                    print("[PORTABLE] Creating portable test package (compatible with all systems)")

                i += 1

            # Get available sandboxes
            available_sandboxes = SandboxManagerFactory.get_available_sandboxes()

            print("\n📋 Available Sandbox Types:")
            print("-" * 30)
            for sandbox in available_sandboxes:
                status = "✅ Available" if sandbox['available'] else "❌ Not Available"
                print(f"  {sandbox['name']} ({sandbox['type']}): {status}")
                if not sandbox['available']:
                    print(f"    └─ {sandbox['message']}")

            # Determine which sandbox to use
            sandbox_type = config['sandbox_type']

            if sandbox_type == 'auto':
                # Auto-select the best available sandbox
                for sandbox in available_sandboxes:
                    if sandbox['available']:
                        sandbox_type = sandbox['type']
                        print(f"\n🎯 Auto-selected: {sandbox['name']}")
                        break
                else:
                    print("\n❌ No sandboxes available on this system")
                    print("💡 Consider installing VirtualBox or Docker for testing")
                    return False

            # Find the selected sandbox
            selected_sandbox = None
            for sandbox in available_sandboxes:
                if sandbox['type'] == sandbox_type or sandbox_type in sandbox['type']:
                    selected_sandbox = sandbox
                    break

            if not selected_sandbox:
                print(f"\n❌ Sandbox type '{sandbox_type}' not found")
                print("📋 Available types:", [s['type'] for s in available_sandboxes])
                return False

            if not selected_sandbox['available']:
                print(f"\n❌ {selected_sandbox['name']} is not available: {selected_sandbox['message']}")

                # Show requirements
                requirements = selected_sandbox['manager'].get_requirements()
                print(f"\n📋 Requirements for {selected_sandbox['name']}:")
                for key, value in requirements.items():
                    print(f"  • {key}: {value}")

                return False

            print(f"\n🎯 Using: {selected_sandbox['name']}")
            manager = selected_sandbox['manager']

            # Handle installation if requested
            if install_only:
                print(f"\n🔧 Installing {selected_sandbox['name']}...")
                # Installation logic would go here
                print("💡 Please install the required software manually")
                return True

            # Create the sandbox environment
            print(f"\n🏗️ Creating {selected_sandbox['name']} environment...")
            success, message = manager.create_environment(config)

            if not success:
                print(f"❌ Failed to create environment: {message}")
                return False

            print(f"✅ {message}")

            # Launch if not dry run
            if not dry_run:
                print(f"\n🚀 Launching {selected_sandbox['name']}...")
                success, message = manager.launch_sandbox(config)

                if success:
                    print(f"✅ {message}")
                    print("\n🎉 Sandbox testing environment is ready!")
                    print(f"📁 Environment files: {manager.sandbox_dir}")
                else:
                    print(f"❌ Failed to launch: {message}")
                    return False
            else:
                print(f"\n📁 Environment created (dry run): {manager.sandbox_dir}")
                print("💡 Run without --dry-run to actually launch the sandbox")

            return True

        except Exception as e:
            print(f"❌ Error in enhanced sandbox testing: {e}")
            import traceback
            traceback.print_exc()
            return False
            self.scripts_folder = os.path.join(self.host_folder, 'scripts')
            self.builds_folder = os.path.join(self.host_folder, 'builds')
            self.dev_folder = os.path.join(self.host_folder, 'development')
        
    def validate_windows_environment(self):
        """Validate that we're running on Windows with Sandbox support"""
        if platform.system() != "Windows":
            raise EnvironmentError("Windows Sandbox is only available on Windows systems")
        
        safe_print("🔍 Detailed Windows Sandbox compatibility check...")
        
        # Check Windows version (Sandbox requires Windows 10 Pro/Enterprise/Education)
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
            build_number = winreg.QueryValueEx(key, "CurrentBuildNumber")[0]
            product_name = winreg.QueryValueEx(key, "ProductName")[0]
            edition_id = winreg.QueryValueEx(key, "EditionID")[0]
            winreg.CloseKey(key)
            
            safe_print(f"   🖥️  Windows: {product_name}")
            safe_print(f"   📊 Edition: {edition_id}")
            safe_print(f"   🔢 Build: {build_number}")
            
            if int(build_number) < 18305:
                raise EnvironmentError(f"Windows Sandbox requires Windows 10 build 18305 or later. Current build: {build_number}")
            
            # Check if Windows edition supports Sandbox
            supported_editions = ['Professional', 'Enterprise', 'Education']
            if not any(edition in edition_id for edition in supported_editions):
                safe_print(f"   ⚠️  Warning: Windows Sandbox typically requires Pro/Enterprise/Education edition")
                safe_print(f"   📝 Your edition: {edition_id}")
                
        except Exception as e:
            safe_print(f"   ⚠️  Warning: Could not verify Windows version details: {e}")
        
        # CRITICAL: Check for Windows Home edition limitation
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
            edition_id = winreg.QueryValueEx(key, "EditionID")[0]
            winreg.CloseKey(key)
            
            if 'Core' in edition_id:  # Windows Home = Core edition
                safe_print("\n⚠️  COMPATIBILITY ISSUE DETECTED:")
                safe_print("   ❌ Windows 10 Home does NOT support Windows Sandbox")
                safe_print("   💡 Windows Sandbox requires Pro, Enterprise, or Education edition")
                safe_print("\nℹ️  Alternative Solutions:")
                safe_print("   1. Upgrade to Windows 10 Pro ($99+)")
                safe_print("   2. Use VirtualBox/VMware instead") 
                safe_print("   3. Use Docker Desktop (if available)")
                safe_print("   4. Use cloud-based testing (Azure, AWS)")
                
                choice = input("\nWould you like to set up a VirtualBox alternative? (y/n): ").lower().strip()
                if choice in ['y', 'yes']:
                    safe_print("\n💡 VirtualBox alternative not yet implemented")
                    safe_print("   Coming in future update!")
                    return False
                else:
                    safe_print("\n💡 Manual alternatives:")
                    safe_print("   - Use a physical test machine with Windows Pro")
                    safe_print("   - Test in a VM with VirtualBox/VMware")
                    safe_print("   - Use cloud testing services")
                    return False
        except:
            pass
        
        # Check if Windows Sandbox feature is available
        safe_print("   🔍 Checking Windows Sandbox feature availability...")
        try:
            result = subprocess.run([
                'powershell', '-Command', 
                'Get-WindowsOptionalFeature -Online -FeatureName "Containers-DisposableClientVM"'
            ], capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                output = result.stdout.lower()
                if 'state' in output:
                    if 'enabled' in output:
                        safe_print("   ✅ Windows Sandbox feature is ENABLED")
                        return self.verify_sandbox_executable()
                    elif 'disabled' in output:
                        safe_print("   ❌ Windows Sandbox feature is DISABLED")
                    elif 'available' in output or 'installable' in output:
                        safe_print("   📦 Windows Sandbox feature is available but not enabled")
                    else:
                        safe_print("   ❓ Windows Sandbox feature status unclear")
                        safe_print(f"   📄 Raw output: {result.stdout[:200]}...")
                else:
                    safe_print("   ❓ Could not determine Windows Sandbox feature status")
            else:
                safe_print(f"   ❌ Error checking feature status (code: {result.returncode})")
                if result.stderr:
                    safe_print(f"   📝 Error: {result.stderr[:200]}...")
                
        except subprocess.TimeoutExpired:
            safe_print("   ⏰ Feature check timed out")
        except Exception as e:
            safe_print(f"   ❌ Feature check failed: {e}")
        
        # Final check - look for WindowsSandbox.exe
        sandbox_exe_found = self.verify_sandbox_executable()
        if sandbox_exe_found:
            safe_print("   ✅ WindowsSandbox.exe found - feature appears to be working")
            return True
        
        # Offer installation
        safe_print("\n❌ Windows Sandbox feature is NOT properly enabled")
        safe_print("💡 This feature is required for sandbox testing")

            # Ask user if they want to install it
        safe_print("\n🔧 Would you like to enable Windows Sandbox now?")
        safe_print("   This will:")
        safe_print("   - Enable the Windows Sandbox feature")
        safe_print("   - Request administrator privileges automatically") 
        safe_print("   - Require a system restart")
        
        try:
            choice = input("\nEnable Windows Sandbox? (y/n): ").lower().strip()
            if choice in ['y', 'yes']:
                return self.install_windows_sandbox()
            else:
                safe_print("⚠️  Continuing without enabling Windows Sandbox")
                safe_print("💡 Manual enable: python build_cli.py --sandbox --install")
                return False
        except KeyboardInterrupt:
            safe_print("\n⚠️  Installation cancelled")
            return False
    
    def verify_sandbox_executable(self):
        """Verify that WindowsSandbox.exe exists and is accessible"""
        safe_print("   🔍 Verifying WindowsSandbox.exe availability...")
        
        # Common locations for WindowsSandbox.exe
        possible_paths = [
            os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'system32', 'WindowsSandbox.exe'),
            'C:\\Windows\\system32\\WindowsSandbox.exe',
            os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files'), 'WindowsSandbox', 'WindowsSandbox.exe')
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                safe_print(f"   ✅ Found: {path}")
                return True
        
        safe_print("   ❌ WindowsSandbox.exe not found in expected locations")
        
        # Try to find it using where command
        try:
            result = subprocess.run(['where', 'WindowsSandbox.exe'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                path = result.stdout.strip()
                safe_print(f"   ✅ Found via 'where': {path}")
                return True
            else:
                safe_print("   ❌ 'where WindowsSandbox.exe' found nothing")
        except:
            safe_print("   ❌ Could not run 'where' command")
        
        return False
    
    def create_portable_test_package(self, config):
        """Create a portable test package for Windows Home users who can't use Sandbox"""
        print("[PKG] Creating Portable Test Package for Windows Home")
        print("="*60)
        
        # Create portable directory structure
        portable_dir = os.path.join(os.getcwd(), 'portable_test_package')
        test_files_dir = os.path.join(portable_dir, 'test_files')
        scripts_dir = os.path.join(portable_dir, 'scripts')
        
        os.makedirs(test_files_dir, exist_ok=True)
        os.makedirs(scripts_dir, exist_ok=True)
        
        print(f"📁 Package directory: {portable_dir}")
        
        # Copy build outputs and additional files
        copied_files = []
        
        # Copy from dist directory
        dist_dir = os.path.join(os.getcwd(), 'dist')
        if os.path.exists(dist_dir):
            for file in os.listdir(dist_dir):
                src_path = os.path.join(dist_dir, file)
                if os.path.isfile(src_path):
                    dest_path = os.path.join(test_files_dir, file)
                    shutil.copy2(src_path, dest_path)
                    copied_files.append(file)
                    print(f"   ✅ Copied: {file}")
        
        # Copy additional files or create test files
        if config.get('additional_files'):
            for file_path in config['additional_files']:
                if os.path.exists(file_path):
                    filename = os.path.basename(file_path)
                    dest_path = os.path.join(test_files_dir, filename)
                    shutil.copy2(file_path, dest_path)
                    copied_files.append(filename)
                    print(f"   ✅ Copied: {filename}")
                else:
                    # Create test file
                    filename = os.path.basename(file_path) if os.path.sep in file_path else file_path
                    if filename.startswith('test_'):
                        dest_path = os.path.join(test_files_dir, filename)
                        self.create_test_file(dest_path, filename)
                        copied_files.append(filename)
                        print(f"   🧪 Created test file: {filename}")
        
        # Create test execution script
        self.create_portable_test_script(scripts_dir, config)
        
        # Create README for the portable package
        self.create_portable_readme(portable_dir, copied_files, config)
        
        print(f"\n✅ Portable test package created!")
        print(f"📦 Location: {portable_dir}")
        print(f"🔧 Files included: {len(copied_files)}")
        
        print("\n💡 Usage Instructions:")
        print("   1. Copy the entire 'portable_test_package' folder to any Windows machine")
        print("   2. Run 'scripts\\run_portable_tests.bat' as Administrator")
        print("   3. Test results will be saved in the package folder")
        print("   4. No Windows Sandbox required - works on Home edition!")
        
        # Open the directory
        try:
            subprocess.run(['explorer', portable_dir])
            print("   📂 Package folder opened in Explorer")
        except:
            pass
            
        return True

    def create_portable_test_package(self, config):
        """Create a portable test package for Windows Home users who can't use Sandbox"""
        print("[PKG] Creating Portable Test Package for Windows Home")
        print("="*60)
        
        # Create portable directory structure
        portable_dir = os.path.join(os.getcwd(), 'portable_test_package')
        test_files_dir = os.path.join(portable_dir, 'test_files')
        scripts_dir = os.path.join(portable_dir, 'scripts')
        
        os.makedirs(test_files_dir, exist_ok=True)
        os.makedirs(scripts_dir, exist_ok=True)
        
        print(f"📁 Package directory: {portable_dir}")
        
        # Copy build outputs and additional files
        copied_files = []
        
        # Copy from dist directory
        dist_dir = os.path.join(os.getcwd(), 'dist')
        if os.path.exists(dist_dir):
            for file in os.listdir(dist_dir):
                src_path = os.path.join(dist_dir, file)
                if os.path.isfile(src_path):
                    dest_path = os.path.join(test_files_dir, file)
                    shutil.copy2(src_path, dest_path)
                    copied_files.append(file)
                    print(f"   ✅ Copied: {file}")
        
        # Copy additional files or create test files
        if config.get('additional_files'):
            for file_path in config['additional_files']:
                if os.path.exists(file_path):
                    filename = os.path.basename(file_path)
                    dest_path = os.path.join(test_files_dir, filename)
                    shutil.copy2(file_path, dest_path)
                    copied_files.append(filename)
                    print(f"   ✅ Copied: {filename}")
                else:
                    # Create test file
                    filename = os.path.basename(file_path) if os.path.sep in file_path else file_path
                    if filename.startswith('test_'):
                        dest_path = os.path.join(test_files_dir, filename)
                        self.create_test_file(dest_path, filename)
                        copied_files.append(filename)
                        print(f"   🧪 Created test file: {filename}")
        
        # Create test execution script
        self.create_portable_test_script(scripts_dir, config)
        
        # Create README for the portable package
        self.create_portable_readme(portable_dir, copied_files, config)
        
        print(f"\n✅ Portable test package created!")
        print(f"📦 Location: {portable_dir}")
        print(f"🔧 Files included: {len(copied_files)}")
        
        print("\n💡 Usage Instructions:")
        print("   1. Copy the entire 'portable_test_package' folder to any Windows machine")
        print("   2. Run 'scripts\\run_portable_tests.bat' as Administrator")
        print("   3. Test results will be saved in the package folder")
        print("   4. No Windows Sandbox required - works on Home edition!")
        
        # Open the directory
        try:
            subprocess.run(['explorer', portable_dir])
            print("   📂 Package folder opened in Explorer")
        except:
            pass
            
        return True
    
    def create_portable_test_script(self, scripts_dir, config):
        """Create the portable test execution script"""
        script_path = os.path.join(scripts_dir, 'run_portable_tests.bat')
        
        venv_name = config.get('venv_name', 'portable_test_env')
        
        script_content = f'''@echo off
title Portable Test Environment - PDF Utility
color 0A

echo ====================================================
echo    PDF Utility - Portable Test Environment
echo    (Windows Home Compatible)
echo ====================================================
echo.

echo [INFO] This package works on ANY Windows edition!
echo [INFO] No Windows Sandbox required
echo.

cd /d "%~dp0.."

echo [1/4] Setting up test environment...
echo    📂 Test files location: %CD%\\test_files
echo    📝 Results will be saved to: %CD%\\test_results

if not exist test_results mkdir test_results

echo.
echo [2/4] Python Environment Setup...
python --version >nul 2>&1
if errorlevel 1 (
    echo    ❌ Python not found! Please install Python 3.7+ first
    echo    💡 Download from: https://python.org/downloads
    pause
    exit /b 1
) else (
    echo    ✅ Python found
)

echo    🐍 Creating virtual environment: {venv_name}
python -m venv {venv_name}

if exist {venv_name}\\Scripts\\activate.bat (
    echo    ✅ Virtual environment created
    call {venv_name}\\Scripts\\activate.bat
    
    echo    📦 Installing common packages...
    pip install --quiet --upgrade pip
    pip install --quiet requests pillow
    
    echo    ✅ Environment ready
) else (
    echo    ⚠️  Virtual environment creation failed, continuing anyway
)

echo.
echo [3/4] Running Tests...
echo ====================================================

for %%f in (test_files\\*) do (
    echo.
    echo 🧪 Testing: %%~nxf
    echo    📁 Path: %%f
    echo    📊 Size: 
    dir "%%f" 2>nul | find "%%~nxf"
    
    REM Test based on file type
    if /i "%%~xf"==".exe" (
        echo    🔧 Testing executable...
        "%%f" --version 2>nul || echo    💡 No version info available
        "%%f" --help 2>nul || echo    💡 No help info available
    )
    
    if /i "%%~xf"==".json" (
        echo    📋 Validating JSON...
        python -m json.tool "%%f" >nul 2>&1 && echo    ✅ Valid JSON || echo    ❌ Invalid JSON
    )
    
    echo    ✅ Basic test completed
)

echo.
echo [4/4] Generating Test Report...
echo Test Report - %date% %time% > test_results\\portable_test_report.txt
echo ====================================================== >> test_results\\portable_test_report.txt
echo. >> test_results\\portable_test_report.txt

echo System Information: >> test_results\\portable_test_report.txt
systeminfo | findstr "OS Name OS Version" >> test_results\\portable_test_report.txt
echo. >> test_results\\portable_test_report.txt

echo Files Tested: >> test_results\\portable_test_report.txt
dir test_files\\*.* /b >> test_results\\portable_test_report.txt 2>nul

echo.
echo ====================================================
echo    ✅ Portable Testing Complete!
echo ====================================================
echo    📄 Report saved: test_results\\portable_test_report.txt
echo    📂 Test files: test_files\\
echo    🔧 Environment: {venv_name}\\
echo.
echo 💡 This package can be copied to other Windows machines
echo 💡 No Windows Sandbox or Pro edition required!
echo.
pause
'''
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        print(f"   ✅ Created: {script_path}")
    
    def create_portable_readme(self, portable_dir, copied_files, config):
        """Create README file for the portable package"""
        readme_path = os.path.join(portable_dir, 'README.txt')
        
        readme_content = f'''PDF Utility - Portable Test Package
====================================================

Created: {datetime.now()}
Compatible with: ALL Windows editions (including Home)

WHAT IS THIS?
This portable test package was created because Windows Sandbox
is only available on Windows Pro/Enterprise/Education editions.

This package provides clean machine testing capabilities for 
Windows Home users and other environments where Sandbox isn't available.

CONTENTS:
- test_files/     : Your build outputs and test files ({len(copied_files)} files)
- scripts/        : Automated test execution scripts  
- test_results/   : Test results and reports (created when run)

FILES INCLUDED:
{chr(10).join(f"  • {file}" for file in copied_files)}

USAGE INSTRUCTIONS:

1. COPY THIS ENTIRE FOLDER to your test machine
   (Can be Windows Home, Pro, any edition)

2. RUN AS ADMINISTRATOR:
   Right-click scripts\\run_portable_tests.bat → "Run as administrator"

3. FOLLOW THE ON-SCREEN PROMPTS
   The script will:
   • Check Python installation
   • Create virtual environment  
   • Run automated tests
   • Generate test report

4. CHECK RESULTS:
   Open test_results\\portable_test_report.txt

REQUIREMENTS:
• Windows 7/8/10/11 (any edition)
• Python 3.7+ (download from python.org if not installed)
• Administrator privileges (for complete testing)

ADVANTAGES OVER WINDOWS SANDBOX:
✅ Works on Windows Home edition
✅ No virtualization overhead
✅ Can test on older Windows versions
✅ Results persist after testing
✅ Can modify and customize easily
✅ Works in corporate environments with restrictions

SUPPORT:
This package was automatically generated by the PDF Utility build system.
For issues or questions, refer to the main project documentation.

Generated with configuration:
- Virtual environment: {config.get('venv_name', 'portable_test_env')}
- Memory limit: Not applicable (uses host resources)
- Network: Host network (not isolated)
- Files: {len(copied_files)} test files included

Happy testing! 🎯
'''
        
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
            
        print(f"   ✅ Created: {readme_path}")
    
    def create_sandbox_structure(self, config):
        """Create sandbox directory structure"""
        print("📁 Creating sandbox directory structure...")
        
        # Create directories
        os.makedirs(self.scripts_folder, exist_ok=True)
        os.makedirs(self.builds_folder, exist_ok=True)
        os.makedirs(self.dev_folder, exist_ok=True)
        
        print(f"   📂 Sandbox directory: {self.sandbox_dir}")
        print(f"   📂 Host share: {self.host_folder}")
        print(f"   📂 Scripts: {self.scripts_folder}")
        print(f"   📂 Builds: {self.builds_folder}")
        print(f"   📂 Development: {self.dev_folder}")
        
        return True
    
    def copy_build_outputs(self, config):
        """Copy build outputs to sandbox"""
        print("📦 Copying build outputs to sandbox...")
        
        dist_dir = os.path.join(os.getcwd(), 'dist')
        copied_files = []
        
        if os.path.exists(dist_dir):
            for file in os.listdir(dist_dir):
                src_path = os.path.join(dist_dir, file)
                if os.path.isfile(src_path):
                    dest_path = os.path.join(self.builds_folder, file)
                    shutil.copy2(src_path, dest_path)
                    copied_files.append(file)
                    print(f"   ✅ Copied: {file}")
        
        # Copy specific files from config
        if config.get('additional_files'):
            for file_path in config['additional_files']:
                if os.path.exists(file_path):
                    filename = os.path.basename(file_path)
                    dest_path = os.path.join(self.builds_folder, filename)
                    shutil.copy2(file_path, dest_path)
                    copied_files.append(filename)
                    print(f"   ✅ Copied additional: {filename}")
                else:
                    # Check if this is a test file - create dummy content
                    filename = os.path.basename(file_path) if os.path.sep in file_path else file_path
                    if any(filename.startswith('test_') for f in ['test_executable.exe', 'test_installer.msi', 'test_config.json', 'test_readme.txt']):
                        dest_path = os.path.join(self.builds_folder, filename)
                        self.create_test_file(dest_path, filename)
                        copied_files.append(filename)
                        print(f"   🧪 Created test file: {filename}")
                    else:
                        print(f"   ⚠️  File not found: {file_path}")
        
        return copied_files
    
    def create_test_file(self, dest_path, filename):
        """Create a test file with appropriate dummy content"""
        try:
            if filename.endswith('.exe'):
                # Create a dummy executable (just a text file with .exe extension)
                content = "This is a test executable file for Windows Sandbox testing.\n"
                content += f"Filename: {filename}\n"
                content += f"Created: {datetime.now()}\n"
                content += "This would normally be a compiled executable.\n"
                
            elif filename.endswith('.msi'):
                # Create a dummy MSI installer
                content = "This is a test MSI installer file for Windows Sandbox testing.\n"
                content += f"Filename: {filename}\n" 
                content += f"Created: {datetime.now()}\n"
                content += "This would normally be a Windows Installer package.\n"
                
            elif filename.endswith('.json'):
                # Create a JSON config file
                import json
                config_data = {
                    "test_file": True,
                    "filename": filename,
                    "created": datetime.now().isoformat(),
                    "purpose": "Windows Sandbox testing",
                    "settings": {
                        "debug": True,
                        "test_mode": True
                    }
                }
                content = json.dumps(config_data, indent=2)
                
            elif filename.endswith('.txt'):
                # Create a text readme
                content = f"Test File: {filename}\n"
                content += "=" * 50 + "\n\n"
                content += "This is a test file created for Windows Sandbox testing.\n\n"
                content += f"Created: {datetime.now()}\n"
                content += "Purpose: Demonstrate file copying and sandbox setup\n\n"
                content += "Instructions:\n"
                content += "1. This file should appear on the Windows Sandbox desktop\n"
                content += "2. Test scripts should be able to access this file\n" 
                content += "3. Use this to verify the sandbox environment is working\n"
                
            else:
                # Generic test file
                content = f"Test file: {filename}\nCreated for Windows Sandbox testing.\n"
            
            with open(dest_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
        except Exception as e:
            print(f"   ❌ Error creating test file {filename}: {e}")
    
    def create_setup_scripts(self, config):
        """Create setup scripts for the sandbox environment"""
        print("📝 Creating sandbox setup scripts...")
        
        # Main setup script
        setup_script = self.generate_setup_script(config)
        setup_path = os.path.join(self.scripts_folder, 'setup_environment.bat')
        
        with open(setup_path, 'w', encoding='utf-8') as f:
            f.write(setup_script)
        
        # Python virtual environment setup
        if config.get('create_venv', True):
            venv_script = self.generate_venv_script(config)
            venv_path = os.path.join(self.scripts_folder, 'setup_python_env.bat')
            
            with open(venv_path, 'w', encoding='utf-8') as f:
                f.write(venv_script)
        
        # Test execution script
        test_script = self.generate_test_script(config)
        test_path = os.path.join(self.scripts_folder, 'run_tests.bat')
        
        with open(test_path, 'w', encoding='utf-8') as f:
            f.write(test_script)
        
        print(f"   ✅ Setup script: {setup_path}")
        print(f"   ✅ Test script: {test_path}")
        
        return [setup_path, test_path]
    
    def generate_setup_script(self, config):
        """Generate the main setup script"""
        script = f'''@echo off
title Windows Sandbox - Build Testing Environment
color 0A

echo ====================================================
echo    PDF Utility - Windows Sandbox Test Environment
echo ====================================================
echo.

echo [1/4] Setting up environment...
cd /d C:\\Users\\WDAGUtilityAccount\\Desktop\\host_share

echo [2/4] Copying files to Desktop...
if exist builds\\ (
    xcopy builds\\*.* C:\\Users\\WDAGUtilityAccount\\Desktop\\ /Y /Q
    echo    ✅ Build files copied to Desktop
)

if exist development\\ (
    xcopy development\\*.* C:\\Users\\WDAGUtilityAccount\\Desktop\\dev\\ /E /I /Y /Q 2>nul
    echo    ✅ Development files copied to Desktop\\dev
)

echo [3/4] Setting up Python environment...
if exist scripts\\setup_python_env.bat (
    call scripts\\setup_python_env.bat
) else (
    echo    ⚠️  No Python environment setup found
)

echo [4/4] Running tests...
if exist scripts\\run_tests.bat (
    call scripts\\run_tests.bat
) else (
    echo    ⚠️  No test script found
)

echo.
echo ====================================================
echo    Setup Complete! Files are on Desktop
echo ====================================================
echo.
echo Available files:
dir C:\\Users\\WDAGUtilityAccount\\Desktop\\*.exe 2>nul
echo.
echo Press any key to continue...
pause >nul
'''
        return script
    
    def generate_venv_script(self, config):
        """Generate virtual environment setup script"""
        venv_name = config.get('venv_name', 'sandbox_env')
        requirements = config.get('requirements_file', 'requirements.txt')
        
        script = f'''@echo off
echo Setting up Python virtual environment: {venv_name}

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo    ❌ Python not found! Installing Python...
    REM In a real sandbox, you might want to include Python installer
    echo    💡 Please install Python manually for full testing
    goto :end
)

echo    🐍 Python found, creating virtual environment...
python -m venv {venv_name}

if exist {venv_name}\\Scripts\\activate.bat (
    echo    ✅ Virtual environment created: {venv_name}
    call {venv_name}\\Scripts\\activate.bat
    
    REM Upgrade pip
    echo    📦 Upgrading pip...
    python -m pip install --upgrade pip
    
    REM Install requirements if available
    if exist host_share\\{requirements} (
        echo    📋 Installing requirements from {requirements}...
        pip install -r host_share\\{requirements}
    ) else (
        echo    💡 No requirements file found, installing common packages...
        pip install requests pillow
    )
    
    echo    ✅ Python environment setup complete
) else (
    echo    ❌ Failed to create virtual environment
)

:end
'''
        return script
    
    def generate_test_script(self, config):
        """Generate test execution script"""
        test_type = config.get('test_type', 'smoke')
        
        script = f'''@echo off
echo Running {test_type} tests...

REM Look for executables to test
for %%f in (C:\\Users\\WDAGUtilityAccount\\Desktop\\*.exe) do (
    echo.
    echo Testing: %%~nxf
    echo    File size: 
    dir "%%f" | find "%%~nxf"
    
    echo    Attempting to run with --help flag...
    "%%f" --help 2>nul
    if errorlevel 1 (
        echo    ⚠️  Help flag not supported or execution failed
    ) else (
        echo    ✅ Executable responded to --help
    )
    
    REM Basic execution test (with timeout)
    echo    Testing basic execution...
    timeout /t 3 /nobreak > nul 2>&1 & "%%f" --version 2>nul
    if errorlevel 1 (
        echo    ⚠️  Version flag not supported
    ) else (
        echo    ✅ Executable responded to --version
    )
)

echo.
echo ====================================================
echo    Test Summary Complete
echo ====================================================

REM Create test report
echo Test Report - %date% %time% > C:\\Users\\WDAGUtilityAccount\\Desktop\\test_report.txt
echo. >> C:\\Users\\WDAGUtilityAccount\\Desktop\\test_report.txt
echo Files tested: >> C:\\Users\\WDAGUtilityAccount\\Desktop\\test_report.txt
dir C:\\Users\\WDAGUtilityAccount\\Desktop\\*.exe /b >> C:\\Users\\WDAGUtilityAccount\\Desktop\\test_report.txt

echo    📄 Test report saved to Desktop\\test_report.txt
'''
        return script
    
    def create_wsb_file(self, config):
        """Create Windows Sandbox .wsb configuration file"""
        print("📋 Creating Windows Sandbox configuration...")
        
        vgpu = config.get('vgpu', 'Default')  # Default, Enable, Disable
        networking = config.get('networking', 'Default')  # Default, Enable, Disable  
        memory = config.get('memory_mb', 4096)  # Memory in MB
        
        wsb_content = f'''<Configuration>
  <VGpu>{vgpu}</VGpu>
  <Networking>{networking}</Networking>
  <MappedFolders>
    <MappedFolder>
      <HostFolder>{os.path.abspath(self.host_folder)}</HostFolder>
      <SandboxFolder>C:\\Users\\WDAGUtilityAccount\\Desktop\\host_share</SandboxFolder>
      <ReadOnly>true</ReadOnly>
    </MappedFolder>
  </MappedFolders>
  <LogonCommand>
    <Command>C:\\Users\\WDAGUtilityAccount\\Desktop\\host_share\\scripts\\setup_environment.bat</Command>
  </LogonCommand>
  <MemoryInMB>{memory}</MemoryInMB>
</Configuration>'''
        
        with open(self.wsb_file, 'w', encoding='utf-8') as f:
            f.write(wsb_content)
        
        print(f"   ✅ Sandbox config: {self.wsb_file}")
        return self.wsb_file
    
    def launch_sandbox(self, config):
        """Launch Windows Sandbox with the configuration"""
        print("🚀 Launching Windows Sandbox...")
        
        try:
            # Try multiple methods to launch Windows Sandbox
            # Ensure proper path normalization
            wsb_path = os.path.abspath(self.wsb_file).replace('/', '\\')
            
            launch_methods = [
                # Method 1: Direct .wsb file execution via cmd (fixed path handling)
                ['cmd', '/c', 'start', '/wait', wsb_path],
                
                # Method 2: PowerShell with proper escaping
                ['powershell', '-Command', f'& {{Start-Process -FilePath "{wsb_path}" -Wait}}'],
                
                # Method 3: Full path to WindowsSandbox.exe 
                [os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'system32', 'WindowsSandbox.exe'), wsb_path],
                
                # Method 4: Explorer association (simple)
                ['explorer', wsb_path],
                
                # Method 5: Direct Windows association via rundll32
                ['rundll32', 'shell32.dll,ShellExec_RunDLL', wsb_path]
            ]
            
            for i, method in enumerate(launch_methods):
                try:
                    print(f"   🔄 Trying launch method {i + 1}...")
                    print(f"   🔧 Command: {' '.join(method[:3])}{'...' if len(method) > 3 else ''}")
                    print(f"   📁 Target file: {wsb_path}")
                    
                    # Check if the .wsb file exists before trying to launch
                    if not os.path.exists(wsb_path):
                        print(f"   ❌ .wsb file does not exist: {wsb_path}")
                        continue
                    
                    # Method 1: cmd start (most compatible)
                    if method[0] == 'cmd' and 'start' in method:
                        # Use a simpler approach for cmd start - avoid extra quotes/escaping
                        # The issue was with the /wait and quoting - let's use a cleaner approach
                        result = subprocess.run(['cmd', '/c', 'start', '', wsb_path], 
                                              capture_output=True, text=True, timeout=10)
                        
                        if result.returncode != 0:
                            print(f"   📝 CMD Error (code {result.returncode}): {result.stderr.strip()}")
                            continue
                            
                    # Method 2: PowerShell methods  
                    elif method[0] == 'powershell':
                        result = subprocess.run(method, capture_output=True, text=True, timeout=10)
                        
                        if result.returncode != 0:
                            print(f"   📝 PS Error (code {result.returncode}): {result.stderr.strip()}")
                            continue
                            
                    # Method 3-5: Direct execution methods
                    else:
                        # For direct execution, just start the process
                        process = subprocess.Popen(method, stdout=subprocess.PIPE, 
                                                 stderr=subprocess.PIPE)
                        
                        # Give it a moment to start
                        try:
                            stdout, stderr = process.communicate(timeout=5)
                            if process.returncode and process.returncode != 0:
                                print(f"   📝 Exec Error (code {process.returncode}): {stderr.decode().strip()}")
                                continue
                        except subprocess.TimeoutExpired:
                            # This is actually good - it means the process started and is running
                            pass
                    
                    print("   ✅ Windows Sandbox launched successfully!")
                    print(f"   💡 Configuration file: {wsb_path}")
                    print("   💡 The sandbox will auto-setup and run tests")
                    print(f"   📋 Used launch method {i + 1}: {method[0]}")
                    
                    return True
                    
                except subprocess.TimeoutExpired:
                    print(f"   ⚠️  Method {i + 1} timed out (may have started successfully)")
                    # Timeout might actually mean success for some methods
                    if i == 0:  # If it's the first method, consider it successful
                        print("   ✅ Assuming successful launch (timeout often means success)")
                        return True
                    continue
                except (subprocess.CalledProcessError, subprocess.SubprocessError) as e:
                    print(f"   ⚠️  Method {i + 1} failed: {type(e).__name__}")
                    if hasattr(e, 'stderr') and e.stderr:
                        print(f"   📝 Error details: {e.stderr.strip()}")
                    continue
                except (FileNotFoundError, OSError) as e:
                    print(f"   ⚠️  Method {i + 1} failed: {type(e).__name__} - {str(e)}")
                    continue
            
            # If all methods failed
            print("   ❌ All launch methods failed. Windows Sandbox may not be enabled.")
            print("\n💡 Manual steps:")
            print("   1. Enable Windows Sandbox feature:")
            print("      dism /online /Enable-Feature /FeatureName:\"Containers-DisposableClientVM\" /All")
            print("   2. Restart your computer")
            print(f"   3. Double-click: {self.wsb_file}")
            print("\n🔧 Alternative: Open PowerShell as Administrator and run:")
            print(f"      Start-Process '{self.wsb_file}'")
            
            return False
            
        except Exception as e:
            print(f"   ❌ Unexpected error launching sandbox: {e}")
            print(f"   📁 You can manually open: {self.wsb_file}")
            return False

def create_sandbox_test_environment(config=None):
    """Main function to create and launch sandbox testing environment"""
    
    if config is None:
        config = {}
    
    sandbox = WindowsSandboxManager()
    
    try:
        # Validate Windows environment (unless skipped)
        if config.get('skip_validation', False):
            print("⚠️  Skipping Windows Sandbox validation (development mode)")
            validation_result = True
        else:
            print("🔍 Validating Windows Sandbox environment...")
            validation_result = sandbox.validate_windows_environment()
            
            if validation_result is False:
                print("❌ Windows Sandbox is not available or installation failed")
                print("💡 Please enable Windows Sandbox manually and try again")
                print("💡 Or use --skip-validation for development/testing")
                return False
        
        # Create directory structure  
        sandbox.create_sandbox_structure(config)
        
        # Copy build outputs
        copied_files = sandbox.copy_build_outputs(config)
        
        if not copied_files:
            print("⚠️  No build files found to copy. Run a build first or specify additional_files in config.")
        
        # Create setup scripts
        sandbox.create_setup_scripts(config)
        
        # Create .wsb file
        wsb_file = sandbox.create_wsb_file(config)
        
        # Launch sandbox (unless dry-run mode)
        if config.get('dry_run', False):
            print("🧪 Dry run mode - skipping sandbox launch")
            print(f"💡 To manually launch: double-click {wsb_file}")
            success = True
        else:
            success = sandbox.launch_sandbox(config)
        
        print("\n" + "="*60)
        print("🎯 Windows Sandbox Test Environment Summary")
        print("="*60)
        print(f"Sandbox Directory: {sandbox.sandbox_dir}")
        print(f"Configuration File: {wsb_file}")
        print(f"Files Copied: {len(copied_files)}")
        
        if config.get('dry_run', False):
            print("Mode: Dry run (files created, launch skipped)")
        elif config.get('skip_validation', False):
            print("Mode: Validation skipped (development mode)")
        
        if copied_files:
            for f in copied_files:
                print(f"  • {f}")
        
        print("\n💡 Next Steps:")
        print("1. Windows Sandbox will launch automatically")
        print("2. Setup scripts will run on startup")  
        print("3. Test results will be on the Desktop")
        print("4. Close sandbox when testing is complete")
        
        return success
        
    except EnvironmentError as e:
        print(f"❌ Environment Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error creating sandbox environment: {e}")
        return False

# ============================================================================
# ADMINISTRATIVE PRIVILEGES MANAGEMENT
# ============================================================================

def is_admin():
    """Check if the script is running with administrative privileges"""
    try:
        if platform.system() == "Windows":
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin()
        elif platform.system() in ["Linux", "Darwin"]:  # Darwin is macOS
            return os.geteuid() == 0
        else:
            # For other systems, assume we need to check
            return False
    except:
        return False

def request_admin_privileges():
    """Request administrative privileges if not already running as admin"""
    if is_admin():
        return True  # Already running as admin
    
    current_system = platform.system()
    script_path = os.path.abspath(sys.argv[0])
    args = sys.argv[1:]
    
    print("🔐 Administrative privileges required for this operation.")
    print(f"🖥️  Detected OS: {current_system}")
    
    try:
        if current_system == "Windows":
            print("💡 Requesting elevation via Windows UAC...")
            
            # Use ctypes to trigger UAC elevation
            try:
                import ctypes
                ctypes.windll.shell32.ShellExecuteW(
                    None, 
                    "runas", 
                    sys.executable, 
                    f'"{script_path}" {" ".join(args)}', 
                    None, 
                    1
                )
                sys.exit(0)  # Exit this non-admin instance
            except Exception as e:
                print(f"⚠️  Primary elevation method failed: {e}")
                
                # Fallback to PowerShell method
                try:
                    args_str = ','.join([f"'{arg}'" for arg in args])
                    powershell_cmd = [
                        "powershell", "-Command",
                        f"Start-Process -FilePath 'python' -ArgumentList '\"{script_path}\"',{args_str} -Verb RunAs -Wait"
                    ]
                    result = subprocess.run(powershell_cmd, capture_output=True, text=True)
                    if result.returncode == 0:
                        print("✅ Command completed with elevated privileges")
                        sys.exit(0)
                    else:
                        print(f"⚠️  Elevation failed: {result.stderr}")
                        return False
                except Exception as e2:
                    print(f"⚠️  PowerShell elevation failed: {e2}")
                    return False
                    
        elif current_system in ["Linux", "Darwin"]:
            print("💡 Requesting elevation via sudo...")
            
            # Check if sudo is available
            try:
                subprocess.run(["which", "sudo"], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                print("❌ sudo not found. Please run as root or install sudo.")
                return False
            
            # Use sudo to re-run the script
            sudo_cmd = ["sudo", sys.executable, script_path] + args
            
            try:
                result = subprocess.run(sudo_cmd)
                sys.exit(result.returncode)  # Exit with the same code as the elevated process
            except KeyboardInterrupt:
                print("\n⚠️  Elevation cancelled by user")
                sys.exit(1)
            except Exception as e:
                print(f"⚠️  sudo elevation failed: {e}")
                return False
        else:
            print(f"⚠️  Administrative privilege elevation not supported on {current_system}")
            print("💡 Please run this script as an administrator/root manually")
            return False
            
    except Exception as e:
        print(f"❌ Error requesting administrative privileges: {e}")
        return False

def request_admin_privileges_with_output():
    """Request admin privileges and capture output from elevated process"""
    if is_admin():
        return True, ""  # Already running as admin
    
    current_system = platform.system()
    script_path = os.path.abspath(sys.argv[0])
    args = sys.argv[1:]
    
    print("🔐 Administrative privileges required - capturing output...")
    print(f"🖥️  Detected OS: {current_system}")
    
    # Create temporary files for output capture
    temp_dir = tempfile.gettempdir()
    output_file = os.path.join(temp_dir, f"admin_output_{int(time.time())}.txt")
    error_file = os.path.join(temp_dir, f"admin_error_{int(time.time())}.txt")
    
    try:
        if current_system == "Windows":
            print("💡 Requesting elevation with output capture...")
            
            # Create a wrapper script that captures output
            wrapper_script = os.path.join(temp_dir, f"admin_wrapper_{int(time.time())}.py")
            wrapper_content = f'''import subprocess
import sys
import os

# Unicode-safe print function for elevated processes
def safe_print(*args, **kwargs):
    """Safe print function that handles Unicode encoding issues without freezing"""
    try:
        # Try to print normally first
        print(*args, **kwargs)
        return
    except UnicodeEncodeError:
        # Fallback for Windows console encoding issues
        fallback_args = []
        for arg in args:
            if isinstance(arg, str):
                # Replace Unicode emojis and special characters with ASCII equivalents
                # Use a more efficient approach to avoid long chained replacements
                fallback = arg
                emoji_map = {
                    '🔄': '[->]', '❌': '[X]', '✅': '[OK]',
                    '📋': '[LIST]', '🔍': '[SCAN]', '📦': '[PKG]',
                    '🔧': '[TOOL]', '🚀': '[GO]', '🎉': '[SUCCESS]',
                    '⚠️': '[WARN]', '💡': '[TIP]', '🖥️': '[OS]',
                    '🏗️': '[BUILD]', '📁': '[DIR]', '📄': '[FILE]',
                    '🔨': '[MAKE]', '⭐': '[*]', '📊': '[CHART]',
                    '🔒': '[LOCK]', '🔓': '[UNLOCK]', '💻': '[PC]',
                    '📱': '[APP]', '🌟': '[STAR]', '🎯': '[TARGET]',
                    '🔗': '[LINK]', '📝': '[NOTE]', '⏰': '[TIME]',
                    '🔔': '[BELL]', '📈': '[UP]', '📉': '[DOWN]',
                    '🔑': '[KEY]', '🎮': '[GAME]', '🌐': '[WEB]',
                    '📷': '[CAM]', '🎵': '[MUSIC]', '🎬': '[VIDEO]',
                    '🔴': '[RED]', '🟢': '[GREEN]', '🟡': '[YELLOW]',
                    '🔵': '[BLUE]', '🟣': '[PURPLE]', '⚫': '[BLACK]',
                    '⚪': '[WHITE]', '🔺': '[UP]', '🔻': '[DOWN]',
                    '🔸': '[DIAMOND]', '🔹': '[DIAMOND]', '💎': '[GEM]',
                    '🏆': '[TROPHY]', '🎊': '[PARTY]', '🎈': '[BALLOON]',
                    '🎁': '[GIFT]', '🍀': '[LUCK]', '⚡': '[BOLT]',
                    '🌈': '[RAINBOW]', '🌙': '[MOON]', '☀️': '[SUN]'
                }
                
                # Replace emojis one by one to avoid long chains
                for emoji, replacement in emoji_map.items():
                    if emoji in fallback:
                        fallback = fallback.replace(emoji, replacement)
                
                fallback_args.append(fallback)
            else:
                fallback_args.append(str(arg))
        
        try:
            print(*fallback_args, **kwargs)
        except Exception:
            # Final fallback - strip all non-ASCII characters
            simple_args = []
            for arg in args:
                if isinstance(arg, str):
                    # Remove all non-ASCII characters
                    simple_arg = ''.join(char for char in arg if ord(char) < 128)
                    simple_args.append(simple_arg)
                else:
                    simple_args.append(str(arg))
            print(*simple_args, **kwargs)

# Redirect print to safe_print for the subprocess
original_print = print

def ultra_safe_print(*args, **kwargs):
    """Ultra-safe print that strips all Unicode characters"""
    try:
        print(*args, **kwargs)
    except:
        # Convert everything to ASCII
        safe_args = []
        for arg in args:
            if isinstance(arg, str):
                # Use dictionary-based replacement to avoid long chained operations
                emoji_map = {
                    '🔄': '[->]', '❌': '[X]', '✅': '[OK]',
                    '📋': '[LIST]', '🔍': '[SCAN]', '📦': '[PKG]',
                    '🔧': '[TOOL]', '🚀': '[GO]', '🎉': '[SUCCESS]',
                    '⚠️': '[WARN]', '💡': '[TIP]', '🖥️': '[OS]',
                    '🏗️': '[BUILD]', '📁': '[DIR]', '📄': '[FILE]',
                    '🔨': '[MAKE]', '⭐': '[*]', '📊': '[CHART]',
                    '🔒': '[LOCK]', '🔓': '[UNLOCK]', '💻': '[PC]',
                    '📱': '[APP]', '🌟': '[STAR]', '🎯': '[TARGET]',
                    '🔗': '[LINK]', '📝': '[NOTE]', '⏰': '[TIME]',
                    '🔔': '[BELL]', '📈': '[UP]', '📉': '[DOWN]',
                    '🔑': '[KEY]', '🎮': '[GAME]', '🌐': '[WEB]',
                    '📷': '[CAM]', '🎵': '[MUSIC]', '🎬': '[VIDEO]',
                    '🔴': '[RED]', '🟢': '[GREEN]', '🟡': '[YELLOW]',
                    '🔵': '[BLUE]', '🟣': '[PURPLE]', '⚫': '[BLACK]',
                    '⚪': '[WHITE]', '🔺': '[UP]', '🔻': '[DOWN]',
                    '🔸': '[DIAMOND]', '🔹': '[DIAMOND]', '💎': '[GEM]',
                    '🏆': '[TROPHY]', '🎊': '[PARTY]', '🎈': '[BALLOON]',
                    '🎁': '[GIFT]', '🍀': '[LUCK]', '⚡': '[BOLT]',
                    '🌈': '[RAINBOW]', '🌙': '[MOON]', '☀️': '[SUN]'
                }
                
                safe_arg = str(arg)
                # Replace emojis one by one to avoid long chains
                for emoji, replacement in emoji_map.items():
                    if emoji in safe_arg:
                        safe_arg = safe_arg.replace(emoji, replacement)
                
                # Strip any remaining non-ASCII characters
                safe_arg = safe_arg.encode('ascii', 'ignore').decode('ascii')
                safe_args.append(safe_arg)
            else:
                safe_args.append(str(arg).encode('ascii', 'ignore').decode('ascii'))
        
        try:
            print(*safe_args, **kwargs)
        except:
            # Last resort - just print without any special handling
            print("ERROR: Could not display message due to encoding issues")

print = ultra_safe_print

try:
    # Run the original command and capture output
    result = subprocess.run([
        sys.executable, r"{script_path}"
    ] + {args}, 
    capture_output=True, text=True, cwd=r"{os.getcwd()}", encoding='utf-8', errors='replace')
    
    # Write output to temp files
    with open(r"{output_file}", "w", encoding="utf-8", errors='replace') as f:
        f.write(result.stdout)
    
    with open(r"{error_file}", "w", encoding="utf-8", errors='replace') as f:
        f.write(result.stderr)
        f.write(f"\\nReturn Code: {{result.returncode}}")
    
    # Exit with same code
    sys.exit(result.returncode)
    
except Exception as e:
    with open(r"{error_file}", "w", encoding="utf-8", errors='replace') as f:
        f.write(f"Wrapper error: {{e}}")
    sys.exit(1)
'''
            
            # Write wrapper script
            with open(wrapper_script, 'w', encoding='utf-8', errors='replace') as f:
                f.write(wrapper_content)
            
            try:
                # Use ctypes to trigger UAC elevation for wrapper
                import ctypes
                result = ctypes.windll.shell32.ShellExecuteW(
                    None, 
                    "runas", 
                    sys.executable, 
                    f'"{wrapper_script}"', 
                    None, 
                    1  # SW_SHOWNORMAL
                )
                
                if result > 32:  # Success
                    print("⏳ Waiting for elevated process to complete...")
                    
                    # Wait for output files to be created (max 30 seconds)
                    for i in range(300):  # 30 seconds with 0.1s intervals
                        if os.path.exists(output_file) or os.path.exists(error_file):
                            time.sleep(0.5)  # Give it a bit more time to write
                            break
                        time.sleep(0.1)
                    
                    # Read the captured output
                    stdout_content = ""
                    stderr_content = ""
                    
                    if os.path.exists(output_file):
                        try:
                            with open(output_file, 'r', encoding='utf-8', errors='replace') as f:
                                stdout_content = f.read()
                            os.unlink(output_file)  # Clean up
                        except Exception as e:
                            print(f"⚠️  Error reading output: {e}")
                    
                    if os.path.exists(error_file):
                        try:
                            with open(error_file, 'r', encoding='utf-8', errors='replace') as f:
                                stderr_content = f.read()
                            os.unlink(error_file)  # Clean up
                        except Exception as e:
                            print(f"⚠️  Error reading errors: {e}")
                    
                    # Clean up wrapper script
                    try:
                        os.unlink(wrapper_script)
                    except:
                        pass
                    
                    # Print captured output
                    if stdout_content.strip():
                        print("📤 Output from elevated process:")
                        print("="*50)
                        print(stdout_content)
                        print("="*50)
                    
                    if stderr_content.strip():
                        print("⚠️  Errors from elevated process:")
                        print("-"*50)
                        print(stderr_content)
                        print("-"*50)
                    
                    # Determine success based on content
                    success = "Return Code: 0" in stderr_content or (stdout_content.strip() and "❌" not in stdout_content)
                    
                    return success, stdout_content + "\n" + stderr_content
                    
                else:
                    print(f"❌ UAC elevation failed with code: {result}")
                    return False, f"UAC elevation failed with code: {result}"
                    
            except Exception as e:
                print(f"⚠️  UAC elevation method failed: {e}")
                # Clean up files
                for file_path in [wrapper_script, output_file, error_file]:
                    try:
                        if os.path.exists(file_path):
                            os.unlink(file_path)
                    except:
                        pass
                return False, f"UAC elevation failed: {e}"
                    
        elif current_system in ["Linux", "Darwin"]:
            print("💡 Requesting elevation via sudo with output capture...")
            
            # Check if sudo is available
            try:
                subprocess.run(["which", "sudo"], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                print("❌ sudo not found. Please run as root or install sudo.")
                return False, "sudo not found"
            
            # Use sudo to re-run the script and capture output
            sudo_cmd = ["sudo", sys.executable, script_path] + args
            
            try:
                result = subprocess.run(sudo_cmd, capture_output=True, text=True, timeout=300)
                
                # Print captured output
                if result.stdout.strip():
                    print("📤 Output from elevated process:")
                    print("="*50)
                    print(result.stdout)
                    print("="*50)
                
                if result.stderr.strip():
                    print("⚠️  Errors from elevated process:")
                    print("-"*50)
                    print(result.stderr)
                    print("-"*50)
                
                success = result.returncode == 0
                return success, result.stdout + "\n" + result.stderr
                
            except subprocess.TimeoutExpired:
                print("⚠️  Elevated process timed out after 5 minutes")
                return False, "Process timed out"
            except KeyboardInterrupt:
                print("\n⚠️  Elevation cancelled by user")
                return False, "Cancelled by user"
            except Exception as e:
                print(f"⚠️  sudo elevation failed: {e}")
                return False, f"sudo elevation failed: {e}"
        else:
            print(f"⚠️  Administrative privilege elevation not supported on {current_system}")
            print("💡 Please run this script as an administrator/root manually")
            return False, f"Elevation not supported on {current_system}"
            
    except Exception as e:
        print(f"❌ Error requesting administrative privileges: {e}")
        return False, f"Error requesting privileges: {e}"

def run_elevated_command(command, args=None, capture_output=True):
    """Run a specific command with elevated privileges and capture output"""
    if args is None:
        args = []
    
    if is_admin():
        # Already running as admin, just run the command
        try:
            if capture_output:
                result = subprocess.run([command] + args, capture_output=True, text=True, timeout=300)
                return result.returncode == 0, result.stdout, result.stderr
            else:
                result = subprocess.run([command] + args, timeout=300)
                return result.returncode == 0, "", ""
        except Exception as e:
            return False, "", str(e)
    
    current_system = platform.system()
    temp_dir = tempfile.gettempdir()
    
    if current_system == "Windows":
        # Create temporary script to run the command
        script_content = f'''import subprocess
import sys
import json

try:
    result = subprocess.run({[command] + args}, capture_output=True, text=True)
    
    output_data = {{
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "success": result.returncode == 0
    }}
    
    with open(r"{temp_dir}\\elevated_result.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
        
except Exception as e:
    error_data = {{
        "returncode": 1,
        "stdout": "",
        "stderr": f"Command execution error: {{e}}",
        "success": False
    }}
    
    with open(r"{temp_dir}\\elevated_result.json", "w", encoding="utf-8") as f:
        json.dump(error_data, f, ensure_ascii=False, indent=2)
'''
        
        script_path = os.path.join(temp_dir, f"elevated_cmd_{int(time.time())}.py")
        result_path = os.path.join(temp_dir, "elevated_result.json")
        
        # Clean up any existing result file
        try:
            if os.path.exists(result_path):
                os.unlink(result_path)
        except:
            pass
        
        try:
            # Write the script
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            # Execute with elevation
            import ctypes
            result = ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, f'"{script_path}"', None, 1
            )
            
            if result > 32:  # Success
                # Wait for result file
                for i in range(300):  # 30 seconds
                    if os.path.exists(result_path):
                        time.sleep(0.5)  # Give it time to write
                        break
                    time.sleep(0.1)
                
                # Read result
                if os.path.exists(result_path):
                    try:
                        with open(result_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        # Clean up
                        os.unlink(result_path)
                        os.unlink(script_path)
                        
                        return data["success"], data["stdout"], data["stderr"]
                    except Exception as e:
                        return False, "", f"Error reading result: {e}"
                else:
                    return False, "", "No result file created"
            else:
                return False, "", f"UAC elevation failed with code: {result}"
                
        except Exception as e:
            # Clean up
            for path in [script_path, result_path]:
                try:
                    if os.path.exists(path):
                        os.unlink(path)
                except:
                    pass
            return False, "", f"Elevation failed: {e}"
    
    elif current_system in ["Linux", "Darwin"]:
        # Use sudo directly
        try:
            result = subprocess.run(
                ["sudo"] + [command] + args, 
                capture_output=True, text=True, timeout=300
            )
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", f"sudo failed: {e}"
    
    else:
        return False, "", f"Elevated commands not supported on {current_system}"

def demonstrate_elevated_output_capture():
    """Demonstrate the UAC output capture system"""
    print("🧪 UAC Output Capture Demonstration")
    print("="*50)
    
    # Test 1: Simple command
    print("\n📋 Test 1: Running 'whoami' with elevation")
    success, stdout, stderr = run_elevated_command("whoami")
    
    print(f"✅ Success: {success}")
    if stdout:
        print(f"📤 Output: {stdout.strip()}")
    if stderr:
        print(f"⚠️  Errors: {stderr.strip()}")
    
    # Test 2: System information
    print("\n📋 Test 2: Getting system information")
    success, stdout, stderr = run_elevated_command("systeminfo", ["/fo", "list"])
    
    print(f"✅ Success: {success}")
    if stdout:
        # Show just first few lines
        lines = stdout.split('\n')[:10]
        print("📤 Output (first 10 lines):")
        for line in lines:
            if line.strip():
                print(f"   {line}")
    if stderr:
        print(f"⚠️  Errors: {stderr.strip()}")
    
    # Test 3: PowerShell command
    print("\n📋 Test 3: PowerShell command with elevation")
    success, stdout, stderr = run_elevated_command("powershell", [
        "-Command", "Get-WindowsOptionalFeature -Online -FeatureName Containers-DisposableClientVM | Select-Object State"
    ])
    
    print(f"✅ Success: {success}")
    if stdout:
        print(f"📤 Output: {stdout.strip()}")
    if stderr:
        print(f"⚠️  Errors: {stderr.strip()}")
    
    print("\n🎯 UAC Output Capture Test Complete!")
    print("💡 This system captures all output from elevated processes")
    print("💡 Output is displayed in the main window for full audit trail")
    
    return True

def needs_admin_privileges(operation):
    """Check if a specific operation requires administrative privileges"""
    admin_operations = [
        'setup_sign',  # Certificate installation
        'install_cert',  # Certificate installation
        'msix_sign',   # MSIX signing (sometimes)
    ]
    
    return operation in admin_operations

def ensure_admin_for_operation(operation_name, operation_description="this operation"):
    """Ensure administrative privileges for a specific operation"""
    if needs_admin_privileges(operation_name):
        if not is_admin():
            print(f"⚠️  {operation_description} requires administrative privileges")
            print("🔄 Requesting elevation...")
            
            if not request_admin_privileges():
                print(f"❌ Cannot proceed with {operation_description} without administrative privileges")
                print("💡 Please run the script as administrator/root and try again")
                return False
            else:
                return True  # Should not reach here as request_admin_privileges exits
        else:
            print(f"✅ Running with administrative privileges for {operation_description}")
            return True
    else:
        return True  # Operation doesn't need admin privileges

# ============================================================================
# UNICODE SAFE PRINTING
# ============================================================================

def safe_print(*args, **kwargs):
    """
    Unicode-safe print function with intelligent emoji handling
    Detects terminal capabilities and provides appropriate fallbacks
    """
    # Check if we should use emojis based on terminal capabilities
    use_emojis = _should_use_emojis()

    if use_emojis:
        # Try to print with emojis directly
        try:
            print(*args, **kwargs)
            return
        except UnicodeEncodeError:
            # Fall back to ASCII if direct printing fails
            pass

    # Process arguments for emoji replacement
    processed_args = []
    for arg in args:
        if isinstance(arg, str):
            processed_arg = _process_emojis_for_display(arg, use_emojis)
            processed_args.append(processed_arg)
        else:
            processed_args.append(arg)

    try:
        print(*processed_args, **kwargs)
    except UnicodeEncodeError:
        # Final fallback - strip all Unicode characters
        ascii_args = []
        for arg in args:
            if isinstance(arg, str):
                # Remove all non-ASCII characters
                ascii_arg = ''.join(char for char in arg if ord(char) < 128)
                ascii_args.append(ascii_arg)
            else:
                ascii_args.append(str(arg))
        print(*ascii_args, **kwargs)
    except Exception as e:
        # Last resort - simple string conversion
        simple_args = [str(arg) for arg in args]
        print(*simple_args, **kwargs)

def _should_use_emojis():
    """
    Detect if the terminal supports Unicode emojis
    """
    # Check environment variables
    if os.environ.get('TERM') == 'dumb':
        return False

    # Check for CI/CD environments that might not support emojis
    if os.environ.get('CI') or os.environ.get('CONTINUOUS_INTEGRATION'):
        return False

    # Check for Windows Terminal or modern terminals
    term_program = os.environ.get('TERM_PROGRAM', '').lower()
    if any(term in term_program for term in ['vscode', 'hyper', 'tabby', 'alacritty', 'kitty']):
        return True

    # Check Windows Terminal
    if os.environ.get('WT_SESSION'):
        return True

    # Check for Windows with modern console
    if platform.system() == 'Windows':
        try:
            import ctypes
            # Check if we're in Windows Terminal or similar
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
            if handle:
                # Try to get console mode
                mode = ctypes.c_uint32()
                if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                    return True
        except:
            pass
        return False

    # For other systems, assume Unicode support
    return True

def _process_emojis_for_display(text, use_emojis=True):
    """
    Process text to handle emoji display appropriately
    """
    if use_emojis:
        return text

    # Emoji to ASCII mapping for better readability
    emoji_map = {
        # Status emojis
        '✅': '[OK]',
        '❌': '[ERROR]',
        '⚠️': '[WARNING]',
        'ℹ️': '[INFO]',
        '🔄': '[LOADING]',
        '⏳': '[WAITING]',
        '🎉': '[SUCCESS]',
        '💡': '[TIP]',
        '🔧': '[TOOL]',
        '🚀': '[START]',
        '🏁': '[FINISH]',
        '🔍': '[SEARCH]',
        '📦': '[PACKAGE]',
        '📁': '[FOLDER]',
        '📄': '[FILE]',
        '🔨': '[BUILD]',
        '⭐': '[STAR]',
        '🌟': '[FEATURE]',
        '🎯': '[TARGET]',
        '🔗': '[LINK]',
        '📋': '[LIST]',
        '📝': '[NOTE]',
        '⏰': '[TIME]',
        '🔔': '[NOTIFICATION]',
        '📈': '[UP]',
        '📉': '[DOWN]',
        '🔑': '[KEY]',
        '🔒': '[LOCKED]',
        '🔓': '[UNLOCKED]',
        '💻': '[COMPUTER]',
        '🖥️': '[DESKTOP]',
        '📱': '[MOBILE]',
        '🌐': '[WEB]',
        '🎮': '[GAME]',
        '📷': '[CAMERA]',
        '🎵': '[MUSIC]',
        '🎬': '[VIDEO]',
        '🏆': '[WIN]',
        '🎊': '[CELEBRATE]',
        '🎈': '[FUN]',
        '🎁': '[GIFT]',
        '🍀': '[LUCK]',
        '⚡': '[FAST]',
        '🌈': '[COLORFUL]',
        '🌙': '[NIGHT]',
        '☀️': '[DAY]',
        '🔴': '[RED]',
        '🟢': '[GREEN]',
        '🟡': '[YELLOW]',
        '🔵': '[BLUE]',
        '🟣': '[PURPLE]',
        '⚫': '[BLACK]',
        '⚪': '[WHITE]',
        '🔺': '[TRIANGLE]',
        '🔻': '[TRIANGLE_DOWN]',
        '🔸': '[DIAMOND]',
        '🔹': '[DIAMOND_SMALL]',
        '💎': '[DIAMOND]',
        '🏗️': '[CONSTRUCTION]',
        '📊': '[CHART]',
        '🔥': '[HOT]',
        '❄️': '[COLD]',
        '💧': '[WATER]',
        '🌪️': '[WIND]',
        '🌊': '[WAVE]',
        '🌱': '[GROW]',
        '🌿': '[PLANT]',
        '🌳': '[TREE]',
        '🌸': '[FLOWER]',
        '🌺': '[BLOOM]',
        '🍎': '[APPLE]',
        '🍊': '[ORANGE]',
        '🍋': '[LEMON]',
        '🍌': '[BANANA]',
        '🍉': '[WATERMELON]',
        '🍇': '[GRAPES]',
        '🍓': '[STRAWBERRY]',
        '🍑': '[PEACH]',
        '🍒': '[CHERRY]',
        '🍍': '[PINEAPPLE]',
        '🥝': '[KIWI]',
        '🍅': '[TOMATO]',
        '🥕': '[CARROT]',
        '🌽': '[CORN]',
        '🥔': '[POTATO]',
        '🍠': '[SWEET_POTATO]',
        '🥒': '[CUCUMBER]',
        '🥬': '[LETTUCE]',
        '🌶️': '[PEPPER]',
        '🫑': '[BELL_PEPPER]',
        '🍄': '[MUSHROOM]',
        '🥑': '[AVOCADO]',
        '🍆': '[EGGPLANT]',
        '🌰': '[CHESTNUT]',
        '🥜': '[PEANUT]',
        '🌰': '[NUT]',
        '🍞': '[BREAD]',
        '🥐': '[CROISSANT]',
        '🥖': '[BAGUETTE]',
        '🫓': '[FLATBREAD]',
        '🥨': '[PRETZEL]',
        '🥯': '[BAGEL]',
        '🥞': '[PANCAKE]',
        '🧇': '[WAFFLE]',
        '🧀': '[CHEESE]',
        '🍖': '[MEAT]',
        '🍗': '[CHICKEN]',
        '🥩': '[STEAK]',
        '🥓': '[BACON]',
        '🍔': '[BURGER]',
        '🍟': '[FRIES]',
        '🍕': '[PIZZA]',
        '🌭': '[HOT_DOG]',
        '🥪': '[SANDWICH]',
        '🌮': '[TACO]',
        '🌯': '[BURRITO]',
        '🫔': '[TAMALE]',
        '🥙': '[STUFFED_FLATBREAD]',
        '🧆': '[FALAFEL]',
        '🥚': '[EGG]',
        '🍳': '[COOKING]',
        '🥘': '[PAELLA]',
        '🍲': '[SOUP]',
        '🫕': '[FONDUE]',
        '🥣': '[BOWL]',
        '🥗': '[SALAD]',
        '🍿': '[POPCORN]',
        '🧈': '[BUTTER]',
        '🧂': '[SALT]',
        '🥫': '[CANNED]',
        '🍱': '[BENTO]',
        '🍘': '[RICE_CRACKER]',
        '🍙': '[RICE_BALL]',
        '🍚': '[RICE]',
        '🍛': '[CURRY]',
        '🍜': '[NOODLES]',
        '🍝': '[PASTA]',
        '🍠': '[ROASTED_SWEET_POTATO]',
        '🍢': '[ODEN]',
        '🍣': '[SUSHI]',
        '🍤': '[FRIED_SHRIMP]',
        '🍥': '[FISH_CAKE]',
        '🥮': '[MOON_CAKE]',
        '🍡': '[DANGO]',
        '🥟': '[DUMPLING]',
        '🥠': '[FORTUNE_COOKIE]',
        '🥡': '[TAKEOUT]',
        '🦪': '[OYSTER]',
        '🍦': '[ICE_CREAM]',
        '🍧': '[SHAVED_ICE]',
        '🍨': '[ICE_CREAM]',
        '🍩': '[DONUT]',
        '🍪': '[COOKIE]',
        '🎂': '[CAKE]',
        '🍰': '[SHORTCAKE]',
        '🧁': '[CUPCAKE]',
        '🥧': '[PIE]',
        '🍫': '[CHOCOLATE]',
        '🍬': '[CANDY]',
        '🍭': '[LOLLIPOP]',
        '🍮': '[CUSTARD]',
        '🍯': '[HONEY]',
        '🍼': '[BABY_BOTTLE]',
        '🥛': '[MILK]',
        '☕': '[COFFEE]',
        '🫖': '[TEA]',
        '🍵': '[TEA]',
        '🍶': '[SAKE]',
        '🍾': '[CHAMPAGNE]',
        '🍷': '[WINE]',
        '🍸': '[COCKTAIL]',
        '🍹': '[TROPICAL_DRINK]',
        '🍺': '[BEER]',
        '🍻': '[BEERS]',
        '🥂': '[CHEERS]',
        '🥃': '[WHISKEY]',
        '🫗': '[POUR]',
        '🥤': '[CUP]',
        '🧋': '[BUBBLE_TEA]',
        '🧃': '[JUICE_BOX]',
        '🧉': '[MATE]',
        '🧊': '[ICE]',
        '🥢': '[CHOPSTICKS]',
        '🍽️': '[PLATE]',
        '🍴': '[FORK_KNIFE]',
        '🥄': '[SPOON]',
        '🔪': '[KNIFE]',
        '🫙': '[JAR]',
        '🏺': '[AMPHORA]',
    }

    # Replace emojis with ASCII equivalents
    result = text
    for emoji, replacement in emoji_map.items():
        result = result.replace(emoji, replacement)

    return result

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
            
            # Show hidden imports summary
            hidden_imports = config.get('hidden_imports', [])
            if hidden_imports:
                print(f"  🕵️ Hidden Imports: {len(hidden_imports)} modules detected")
            
            # Show hooks summary
            hooks_dir = config.get('hooks_directory')
            runtime_hooks = config.get('runtime_hooks', [])
            if hooks_dir or runtime_hooks:
                print(f"  🔧 PyInstaller Hooks: {len(runtime_hooks)} runtime hooks configured")
        else:
            print("\nNo configuration stored")
            
    def _is_likely_stdlib(self, module_name):
        """Check if a module is likely from the standard library"""
        stdlib_modules = {
            'os', 'sys', 'json', 're', 'datetime', 'pathlib', 'subprocess', 'platform',
            'collections', 'itertools', 'functools', 'operator', 'math', 'random',
            'string', 'io', 'contextlib', 'copy', 'pickle', 'sqlite3', 'urllib',
            'http', 'email', 'xml', 'html', 'csv', 'configparser', 'logging',
            'argparse', 'shutil', 'tempfile', 'glob', 'fnmatch', 'linecache',
            'textwrap', 'unicodedata', 'encodings', 'codecs', 'time', 'calendar',
            'hashlib', 'hmac', 'secrets', 'ssl', 'socket', 'threading', 'multiprocessing',
            'concurrent', 'asyncio', 'queue', 'sched', 'weakref', 'types', 'abc',
            'numbers', 'enum', 'decimal', 'fractions', 'statistics', 'array',
            'bisect', 'heapq', 'zlib', 'gzip', 'bz2', 'lzma', 'zipfile', 'tarfile',
            'ast', 'ctypes', 'pkgutil', 'traceback', 'importlib'
        }
        
        # Check base module name
        base_module = module_name.split('.')[0]
        return base_module in stdlib_modules
            
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
                if key == 'hidden_imports':
                    print(f"  🕵️ {key}: {len(value)} modules")
                    # Show detailed list of hidden imports
                    if value:
                        # Group by type (try to categorize)
                        standard_lib = []
                        third_party = []
                        for module in value:
                            if self._is_likely_stdlib(module):
                                standard_lib.append(module)
                            else:
                                third_party.append(module)
                        
                        if standard_lib:
                            print(f"    📚 Standard Library ({len(standard_lib)}):")
                            for module in sorted(standard_lib)[:15]:  # Show first 15
                                print(f"      • {module}")
                            if len(standard_lib) > 15:
                                print(f"      ... and {len(standard_lib) - 15} more")
                        
                        if third_party:
                            print(f"    📦 Third Party ({len(third_party)}):")
                            for module in sorted(third_party)[:15]:  # Show first 15
                                print(f"      • {module}")
                            if len(third_party) > 15:
                                print(f"      ... and {len(third_party) - 15} more")
                elif key == 'hooks_directory':
                    print(f"  🔧 {key}: {value}")
                elif key == 'runtime_hooks':
                    print(f"  🎣 {key}: {len(value)} hooks")
                    for hook in value:
                        print(f"    • {hook}")
                else:
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

class ArtifactManager:
    """
    Manages build artifacts and generates a manifest.json file.
    """
    def __init__(self, build_name, dist_path):
        self.build_name = build_name
        self.dist_path = Path(dist_path)
        self.artifacts = []

    def add_artifact(self, file_path, artifact_type):
        """
        Add an artifact to the manifest.
        :param file_path: Path to the artifact file.
        :param artifact_type: Type of the artifact (e.g., executable, log, etc.).
        """
        file_path = Path(file_path)
        if file_path.exists():
            artifact_info = {
                "name": file_path.name,
                "path": str(file_path.resolve()),
                "type": artifact_type,
                "size": file_path.stat().st_size,
                "sha256": self.calculate_sha256(file_path),
                "signed": self.check_signing_state(file_path)
            }
            self.artifacts.append(artifact_info)
        else:
            print(f"⚠️ Warning: Artifact not found: {file_path}")

    def calculate_sha256(self, file_path):
        """
        Calculate the SHA-256 hash of a file.
        :param file_path: Path to the file.
        :return: SHA-256 hash as a hexadecimal string.
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def check_signing_state(self, file_path):
        """
        Check if the file is signed (placeholder implementation).
        :param file_path: Path to the file.
        :return: Signing state as a boolean.
        """
        # Placeholder: Implement actual signing check logic if needed
        if platform.system() == 'Windows' and file_path.suffix.lower() == '.exe':
            try:
                # Use signtool to check signing status
                result = subprocess.run(
                    ['signtool', 'verify', '/pa', str(file_path)],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                return result.returncode == 0
            except:
                pass
        return False

    def generate_sbom(self, project_root):
        """
        Generate a Software Bill of Materials (SBOM).
        :param project_root: Root directory of the project.
        """
        sbom_path = self.dist_path / "sbom.json"
        sbom_data = {
            "project": self.build_name,
            "generated_at": datetime.now().isoformat(),
            "platform": platform.system(),
            "architecture": platform.machine(),
            "dependencies": self._collect_dependencies(project_root)
        }
        
        # Ensure dist directory exists
        self.dist_path.mkdir(parents=True, exist_ok=True)
        
        with open(sbom_path, "w") as f:
            json.dump(sbom_data, f, indent=4)
        self.add_artifact(sbom_path, "sbom")

    def _collect_dependencies(self, project_root):
        """
        Collect project dependencies (placeholder implementation).
        """
        dependencies = []
        
        # Try to read requirements.txt
        req_file = Path(project_root) / "requirements.txt"
        if req_file.exists():
            try:
                with open(req_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            dependencies.append({
                                "name": line.split('==')[0].split('>=')[0].split('<=')[0].split('>')[0].split('<')[0],
                                "version": "unknown",
                                "source": "requirements.txt"
                            })
            except:
                pass
        
        return dependencies

    def write_manifest(self):
        """
        Write the manifest.json file to the dist directory.
        """
        # Ensure dist directory exists
        self.dist_path.mkdir(parents=True, exist_ok=True)
        
        manifest_path = self.dist_path / "manifest.json"
        manifest_data = {
            "build_name": self.build_name,
            "generated_at": datetime.now().isoformat(),
            "platform": platform.system(),
            "architecture": platform.machine(),
            "total_artifacts": len(self.artifacts),
            "artifacts": self.artifacts
        }
        
        with open(manifest_path, "w") as f:
            json.dump(manifest_data, f, indent=4)
        print(f"✅ Manifest written to: {manifest_path}")
        print(f"📦 Total artifacts registered: {len(self.artifacts)}")

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
        
        # Debug: Show current Python being used by script
        current_python = sys.executable
        print(f"🔍 DEBUG: Current script Python: {current_python}")
        
        # Check if current Python in script has PIL issues (like PlatformIO, MSYS2, etc.)
        problematic_paths = ['platformio', 'msys', 'mingw', 'conda', 'anaconda']
        current_is_problematic = any(path.lower() in current_python.lower() for path in problematic_paths)
        if current_is_problematic:
            print(f"⚠️  Current Python appears to be from a development environment")
            print(f"   Path contains: {[p for p in problematic_paths if p.lower() in current_python.lower()]}")
            print(f"   Will prioritize system Python installations")
        
        # List of Python executables to try in order of preference
        python_candidates = []
        
        if platform.system() == 'Windows':
            # HIGHEST PRIORITY: py launcher - this bypasses PATH issues completely
            print("🔍 Priority 1: Python Launcher (bypasses PATH issues)")
            python_candidates.extend([
                'py -3.13',  # Force Python 3.13 via py launcher
                'py -3.12',  # Try Python 3.12 
                'py -3.11',  # Try Python 3.11
                'py',        # Default py launcher
            ])
            
            # Direct system Python paths to bypass PATH issues from VS Code/PlatformIO
            print("🔍 Priority 2: Direct system Python paths")
            username = os.environ.get('USERNAME', 'User')
            python_candidates.extend([
                f'C:\\Users\\{username}\\AppData\\Local\\Programs\\Python\\Python313\\python.exe',
                f'C:\\Users\\{username}\\AppData\\Local\\Programs\\Python\\Python312\\python.exe',
                f'C:\\Users\\{username}\\AppData\\Local\\Programs\\Python\\Python311\\python.exe',
                'C:\\Python313\\python.exe',
                'C:\\Python312\\python.exe',
                'C:\\Python311\\python.exe',
            ])
        
        # Last resort: PATH-based commands (may pick up problematic environments)
        print("🔍 Priority 3: PATH-based commands (last resort)")
        python_candidates.extend([
            'python3',  # Python 3 specifically
            'python',   # Current python (might be PlatformIO/MSYS2)
        ])
        
        # Test each candidate
        for python_cmd in python_candidates:
            try:
                print(f"🔍 Trying: {python_cmd}")
                
                # Handle py launcher with version flags
                if python_cmd.startswith('py '):
                    cmd_parts = python_cmd.split()
                else:
                    cmd_parts = [python_cmd]
                
                # First, check what Python executable this resolves to
                path_cmd = cmd_parts + ['-c', 'import sys; print(f"PYTHON_PATH:{sys.executable}")']
                path_result = subprocess.run(
                    path_cmd,
                    capture_output=True,
                    text=True,
                    timeout=5,
                    shell=True if python_cmd.startswith('py ') else False
                )
                
                python_path = ""
                if path_result.returncode == 0:
                    for line in path_result.stdout.split('\n'):
                        if line.startswith('PYTHON_PATH:'):
                            python_path = line.replace('PYTHON_PATH:', '').strip()
                            break
                
                # Skip problematic Python installations when we have better options
                if python_path and any(prob.lower() in python_path.lower() for prob in problematic_paths):
                    print(f"   ⚠️  Skipping problematic Python: {python_path}")
                    print(f"   Contains: {[p for p in problematic_paths if p.lower() in python_path.lower()]}")
                    continue
                
                # Test if this Python has PIL
                test_cmd = cmd_parts + ['-c', 'from PIL import Image; print("PIL_AVAILABLE")']
                
                result = subprocess.run(
                    test_cmd,
                    capture_output=True,
                    text=True,
                    timeout=10,
                    shell=True if python_cmd.startswith('py ') else False
                )
                
                if result.returncode == 0 and 'PIL_AVAILABLE' in result.stdout:
                    print(f"🐍 Found Python with PIL: {python_cmd}")
                    if python_path:
                        print(f"   → {python_path}")
                    return python_cmd
                else:
                    print(f"   ❌ No PIL or failed: return code {result.returncode}")
                    if result.stderr:
                        error_msg = result.stderr.strip()[:100]
                        print(f"   Error: {error_msg}...")
                    
            except (subprocess.SubprocessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
                print(f"   ❌ Exception: {e}")
                continue
        
        print("⚠️  No Python installation with PIL found")
        print("💡 Suggestions:")
        print("   1. Install PIL in system Python: pip install Pillow")
        print("   2. Use py launcher: py -m pip install Pillow")
        print("   3. Check if VS Code/PlatformIO is interfering with PATH")
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
            # Start progress tracking
            progress_tracker.start_operation("PyInstaller Build", total_steps=10)
            progress_tracker.update_progress(1, "Initializing build process")
            
            print("🔨 PyInstaller Build Process")
            print("=" * 40)
            
            # Get build configuration from memory
            build_config = self.memory.get_config()
            scan_results = self.memory.get_scan_results()
            progress_tracker.update_progress(2, "Loading configuration")

            # Initialize ArtifactManager
            build_name = build_config.get('name', 'PDFUtility_Build')
            dist_path = Path(os.getcwd()) / "dist"
            artifact_manager = ArtifactManager(build_name, dist_path)
            
            # Check for force clean flag
            force_clean = '--force-clean' in sys.argv
            
            # Initialize incremental build manager
            incremental_manager = IncrementalBuildManager()
            incremental_manager.setup_pyinstaller_cache()
            progress_tracker.update_progress(3, "Setting up build environment")
            
            # Analyze changes for incremental build
            changes = incremental_manager.analyze_changes(scan_results, build_config)
            
            # Check if build can be skipped
            if incremental_manager.should_skip_build(changes, force_clean):
                print("🎯 Build output is up to date!")
                print("💡 Use --force-clean to force a rebuild")
                progress_tracker.complete_operation(True, "Build skipped - output is up to date")
                return True
            
            # Check for required configuration
            main_file = build_config.get('main_file')
            if not main_file:
                # Try to auto-detect main file
                print("🔍 No main file specified, attempting auto-detection...")
                progress_tracker.update_progress(4, "Auto-detecting main file")
                main_file = self.auto_detect_main_file()
                if main_file:
                    print(f"✅ Auto-detected main file: {main_file}")
                    build_config['main_file'] = main_file
                    self.memory.store_config(build_config)
                else:
                    print("❌ No main file found. Please specify using --main <filename>")
                    progress_tracker.complete_operation(False, "No main file found")
                    return False
            
            # Validate main file exists
            if not os.path.exists(main_file):
                print(f"❌ Main file not found: {main_file}")
                progress_tracker.complete_operation(False, f"Main file not found: {main_file}")
                return False
            
            # Build PyInstaller command
            progress_tracker.update_progress(5, "Building PyInstaller command")
            command = self.build_pyinstaller_command(build_config)
            
            # Show command preview
            print("\n📋 Build Command Preview:")
            print("-" * 30)
            print(command)
            print("-" * 30)
            
            # Confirm before executing
            if '--no-confirm' not in sys.argv:
                if input("Proceed with build? (y/n): ").lower() != 'y':
                    print("Build cancelled.")
                    progress_tracker.complete_operation(False, "Build cancelled by user")
                    return False
            
            # Execute build
            print("\n🔨 Starting build process...")
            progress_tracker.update_progress(6, "Executing PyInstaller build", "Running compilation...")
            result = self.execute_build_command(command)
            
            if result:
                print("\n📦 Registering build artifacts...")
                progress_tracker.update_progress(8, "Processing artifacts", "Registering build outputs")
                
                # The output path is typically in dist/
                output_exe_path = dist_path / f"{build_config.get('name', 'app')}.exe"
                if output_exe_path.exists():
                    artifact_manager.add_artifact(output_exe_path, "executable")
                
                # Add other potential artifacts like logs, symbols, etc.
                build_log_path = Path(os.getcwd()) / "build.log" # Assuming a log is created
                if build_log_path.exists():
                    artifact_manager.add_artifact(build_log_path, "log")

                # Generate SBOM
                progress_tracker.update_progress(9, "Generating SBOM and manifest")
                artifact_manager.generate_sbom(os.getcwd())

                # Finalize and write manifest
                artifact_manager.write_manifest()

                # Update build cache if successful
                try:
                    build_metadata = {
                        'last_build': datetime.now().isoformat(),
                        'build_config': build_config,
                        'main_file': main_file,
                        'command': command
                    }
                    incremental_manager.save_build_cache(build_metadata)
                    print("💾 Build cache updated for next incremental build")
                except Exception as e:
                    print(f"⚠️  Warning: Could not update build cache: {e}")
                    progress_tracker.update_progress(warning=f"Could not update build cache: {e}")
                
                progress_tracker.complete_operation(True, "Build completed successfully")
            else:
                progress_tracker.complete_operation(False, "Build failed during compilation")
            
            return result
            
        except Exception as e:
            print(f"❌ Build error: {e}")
            progress_tracker.complete_operation(False, f"Build error: {e}")
            import traceback
            traceback.print_exc()
            return False
            cmd_str = " \\\n  ".join(command) if len(" ".join(command)) > 80 else " ".join(command)
            print(f"{cmd_str}")
            
            # Show build summary
            self.show_build_summary(build_config)
            
            # Execute build
            result = self.execute_build_command(command)
            
            # Update build cache if successful
            if result:
                try:
                    build_metadata = {
                        'last_build': datetime.now().isoformat(),
                        'build_config': build_config,
                        'main_file': main_file,
                        'command': command
                    }
                    incremental_manager.save_build_cache(build_metadata)
                    print("💾 Build cache updated for next incremental build")
                except Exception as e:
                    print(f"⚠️  Warning: Could not update build cache: {e}")
            
            return result
            
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
        
        # Check if profile is active and apply profile-specific arguments
        profile_name = config.get('profile')
        if profile_name:
            safe_print(f"🎯 Building with profile: {profile_name}")
            profile_manager = BuildProfileManager()
            try:
                profile_args = profile_manager.generate_pyinstaller_args(config)
                command.extend(profile_args)
                safe_print(f"🔧 Applied profile args: {' '.join(profile_args)}")
            except Exception as e:
                safe_print(f"⚠️ Warning: Could not apply profile args: {e}")
        
        # Check if template is active and apply template-specific arguments
        template_name = config.get('template')
        if template_name:
            safe_print(f"📋 Building with template: {template_name}")
            template_manager = ProjectTemplateManager()
            try:
                template_args = template_manager.generate_pyinstaller_args_from_template(config)
                command.extend(template_args)
                safe_print(f"🔧 Applied template args: {len(template_args)} additional arguments")
            except Exception as e:
                safe_print(f"⚠️ Warning: Could not apply template args: {e}")
        
        # DEBUG: Confirm we're using the updated version
        safe_print(f"🔧 build_pyinstaller_command() - Using path separator: '{path_separator}' for {platform.system()} [PROFILE+TEMPLATE-ENHANCED VERSION]")
        
        # Generate build name
        build_name = self.generate_build_filename(config)
        command.extend(["--name", build_name])
        
        # Basic options (may be overridden by profile settings above)
        bundle_type = config.get('bundle_type', 'onedir')
        if bundle_type == 'onefile' or config.get('onefile', False):
            if '--onedir' not in command:  # Don't override profile setting
                command.append("--onefile")
        else:
            if '--onefile' not in command:  # Don't override profile setting
                command.append("--onedir")
            
        # Windowed/console mode (respect profile settings)
        if '--windowed' not in command and '--console' not in command:
            if config.get('windowed', False):
                command.append("--windowed")
            else:
                command.append("--console")
            
        if config.get('clean', True):
            command.append("--clean")
            
        # Debug mode (enhanced by profile)
        debug_mode = config.get('debug', False) or config.get('debug_logs', False)
        if debug_mode and '--debug' not in ' '.join(command):
            command.append("--debug=all")
        
        # Hidden imports from configuration and tracing
        hidden_imports = config.get('hidden_imports', [])
        if hidden_imports:
            safe_print(f"🔧 Adding {len(hidden_imports)} hidden imports")
            for hidden_import in hidden_imports:
                command.extend(["--hidden-import", hidden_import])
                safe_print(f"   • {hidden_import}")
        
        # Hook directories from generation
        if config.get('hooks_directory'):
            hooks_dir = config['hooks_directory']
            if os.path.exists(hooks_dir):
                command.extend(["--additional-hooks-dir", hooks_dir])
                safe_print(f"🔧 Adding hooks directory: {hooks_dir}")
        
        # Runtime hooks
        if config.get('runtime_hooks'):
            for runtime_hook in config['runtime_hooks']:
                if os.path.exists(runtime_hook):
                    command.extend(["--runtime-hook", runtime_hook])
                    safe_print(f"🔧 Adding runtime hook: {runtime_hook}")
        
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
            
            # Check for admin privileges for optimal MSIX signing
            if not is_admin():
                print("💡 Running without administrative privileges")
                print("   • Executable signing will work")
                print("   • MSIX signing may fail (requires certificate in trusted stores)")
                print("   • For full MSIX signing: py build_cli.py --setup sign (as Administrator)")
                print()
            else:
                print("✅ Running with administrative privileges for optimal signing")
                print()
            
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
            
            # First, try to sign the executable inside the package (more likely to succeed)
            exe_path = os.path.join(packaging_config['package_dir'], 'PDF-Utility.exe')
            if os.path.exists(exe_path) and self.get_certificate_info():
                print("🔐 Pre-signing executable...")
                self.sign_executable(exe_path, packaging_config)
            
            # Execute SignTool on the MSIX package (if certificate available)
            if not self.execute_signtool(packaging_config):
                print("⚠️  MSIX package signing failed.")
                print("💡 Note: MSIX signing often requires certificate installation to trusted stores.")
                print("💡 Run: py build_cli.py --setup sign (as Administrator)")
                print("💡 The executable inside the package may still be signed.")
            
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

    def sign_executable(self, exe_path, config):
        """Enhanced executable signing with AV/SmartScreen friendly options"""
        try:
            print("🔐 Advanced Code Signing (AV/SmartScreen Friendly)")
            print("=" * 55)
            
            # Find SignTool executable
            signtool_path = self.find_windows_sdk_tool('signtool.exe')
            if not signtool_path:
                print("❌ SignTool not found for executable signing.")
                self._show_unsigned_warnings()
                return False
            
            # Get certificate info
            cert_info = self.get_certificate_info()
            if not cert_info:
                print("❌ No certificate available for signing.")
                self._show_unsigned_warnings()
                return False
            
            print(f"📁 Executable: {os.path.basename(exe_path)}")
            print(f"🔑 Certificate type: {cert_info[0]}")
            
            # Check if dual-signing is requested (default: True for better compatibility)
            enable_dual_sign = config.get('dual_sign', True)
            
            # Step 1: Primary SHA-256 signature with timestamping
            primary_success = self._sign_with_sha256_and_timestamp(
                signtool_path, exe_path, cert_info
            )
            
            if not primary_success:
                print("❌ Primary SHA-256 signing failed")
                self._show_unsigned_warnings()
                return False
            
            # Step 2: Optional dual-sign with SHA-1 for legacy compatibility
            if enable_dual_sign:
                dual_success = self._dual_sign_with_sha1(
                    signtool_path, exe_path, cert_info
                )
                
                if dual_success:
                    print("✅ Dual-signature (SHA-256 + SHA-1) completed successfully")
                else:
                    print("⚠️  Dual-signing failed, but primary SHA-256 signature is intact")
            
            # Step 3: Verify signature and timestamps
            self._verify_executable_signature(signtool_path, exe_path)
            
            # Step 4: SmartScreen advice
            self._show_smartscreen_advice(exe_path)
            
            return True
            
        except Exception as e:
            print(f"❌ Error in advanced signing: {e}")
            self._show_unsigned_warnings()
            return False

    def _sign_with_sha256_and_timestamp(self, signtool_path, exe_path, cert_config):
        """Enhanced SHA-256 signature with configurable timestamping and retry logic"""
        print("🔒 Step 1: SHA-256 signature with enterprise timestamping")
        
        # Extract certificate configuration
        cert_type, cert_path, cert_password = cert_config
        
        # RFC 3161 timestamping servers (in order of preference)
        timestamp_servers = [
            "http://timestamp.digicert.com",
            "http://timestamp.comodoca.com",
            "http://timestamp.sectigo.com", 
            "http://timestamp.globalsign.com/?signature=sha2",
            "http://tsa.starfieldtech.com",
            "http://timestamp.entrust.net/TSS/RFC3161sha2TS"
        ]
        
        # Build base command based on certificate type
        if cert_type == 'file':
            base_cmd = [
                signtool_path,
                'sign',
                '/f', cert_path,
                '/fd', 'SHA256',  # File digest algorithm
                '/td', 'SHA256',  # Timestamp digest algorithm
                '/d', 'PDF Utility Application',  # Description
                '/du', 'https://github.com/braydenanderson2014/PDF-Utility'  # URL
            ]
            
            if cert_password:
                base_cmd.extend(['/p', cert_password])
                
        elif cert_type == 'store':
            base_cmd = [
                signtool_path,
                'sign',
                '/sha1', cert_path,  # Use thumbprint or subject
                '/fd', 'SHA256',
                '/td', 'SHA256',
                '/d', 'PDF Utility Application',
                '/du', 'https://github.com/braydenanderson2014/PDF-Utility'
            ]
        else:
            print(f"❌ Unsupported certificate type: {cert_type}")
            return False
        
        # Try timestamping with multiple servers
        for i, ts_server in enumerate(timestamp_servers, 1):
            print(f"   🕒 Attempting timestamp server {i}/{len(timestamp_servers)}: {ts_server}")
            
            sign_cmd = base_cmd.copy()
            sign_cmd.extend(['/tr', ts_server])  # RFC 3161 timestamp server
            sign_cmd.append(exe_path)
            
            try:
                result = subprocess.run(
                    sign_cmd,
                    capture_output=True,
                    text=True,
                    timeout=45  # Longer timeout for network operations
                )
                
                if result.returncode == 0:
                    print(f"   ✅ SHA-256 signature with timestamp successful")
                    return True
                else:
                    error_msg = self._extract_signing_error(result.stderr)
                    print(f"   ⚠️  Server {i} failed: {error_msg}")
                    
            except subprocess.TimeoutExpired:
                print(f"   ⏰ Server {i} timeout (network issue)")
                continue
            except Exception as e:
                print(f"   ❌ Server {i} error: {e}")
                continue
        
        # Try signing without timestamp as fallback
        print("   🔄 Attempting signature without timestamp (fallback)")
        
        fallback_cmd = [
            signtool_path,
            'sign',
            '/f', cert_path,
            '/fd', 'SHA256',
            '/d', 'PDF Utility Application'
        ]
        
        if cert_password:
            fallback_cmd.extend(['/p', cert_password])
        
        fallback_cmd.append(exe_path)
        
        try:
            result = subprocess.run(fallback_cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("   ⚠️  SHA-256 signature successful BUT without timestamp")
                print("   � Timestamp is recommended for better SmartScreen reputation")
                return True
            else:
                print(f"   ❌ Fallback signing failed: {self._extract_signing_error(result.stderr)}")
                return False
                
        except Exception as e:
            print(f"   ❌ Fallback signing error: {e}")
            return False

    def _dual_sign_with_sha1(self, signtool_path, exe_path, cert_config):
        """Enhanced SHA-1 dual signature with configurable Authenticode timestamping"""
        print("🔒 Step 2: Adding SHA-1 signature for legacy compatibility")
        
        # Extract certificate configuration
        cert_type, cert_path, cert_password = cert_config
        
        # SHA-1 timestamping servers (Authenticode style)
        sha1_timestamp_servers = [
            "http://timestamp.digicert.com",
            "http://timestamp.comodoca.com/authenticode",
            "http://timestamp.sectigo.com/authenticode",
            "http://timestamp.globalsign.com/scripts/timstamp.dll"
        ]
        
        # Build base command based on certificate type
        if cert_type == 'file':
            base_cmd = [
                signtool_path,
                'sign',
                '/f', cert_path,
                '/fd', 'SHA1',  # File digest for SHA-1
                '/as',  # Append signature (dual-sign)
                '/d', 'PDF Utility Application'
            ]
            
            if cert_password:
                base_cmd.extend(['/p', cert_password])
                
        elif cert_type == 'store':
            base_cmd = [
                signtool_path,
                'sign',
                '/sha1', cert_path,  # Use thumbprint or subject
                '/fd', 'SHA1',
                '/as',  # Append signature (dual-sign)
                '/d', 'PDF Utility Application'
            ]
        else:
            print(f"❌ Unsupported certificate type for dual signing: {cert_type}")
            return False
        
        # Try SHA-1 timestamping
        for i, ts_server in enumerate(sha1_timestamp_servers, 1):
            print(f"   🕒 Attempting SHA-1 timestamp server {i}/{len(sha1_timestamp_servers)}")
            
            sign_cmd = base_cmd.copy()
            sign_cmd.extend(['/t', ts_server])  # Authenticode timestamp server
            sign_cmd.append(exe_path)
            
            try:
                result = subprocess.run(
                    sign_cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    print(f"   ✅ SHA-1 dual signature with timestamp successful")
                    return True
                else:
                    print(f"   ⚠️  SHA-1 server {i} failed")
                    
            except Exception as e:
                print(f"   ❌ SHA-1 server {i} error: {e}")
                continue
        
        # Try SHA-1 without timestamp
        print("   🔄 Attempting SHA-1 signature without timestamp")
        
        fallback_cmd = [
            signtool_path,
            'sign',
            '/f', cert_path,
            '/fd', 'SHA1',
            '/as',
            '/d', 'PDF Utility Application'
        ]
        
        if cert_password:
            fallback_cmd.extend(['/p', cert_password])
        
        fallback_cmd.append(exe_path)
        
        try:
            result = subprocess.run(fallback_cmd, capture_output=True, text=True, timeout=30)
            return result.returncode == 0
        except Exception:
            return False

    def _verify_executable_signature(self, signtool_path, exe_path):
        """Verify the executable signature and show details"""
        print("🔍 Step 3: Verifying signature")
        
        try:
            verify_cmd = [signtool_path, 'verify', '/pa', '/v', exe_path]
            result = subprocess.run(verify_cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("   ✅ Signature verification successful")
                
                # Extract useful info from verification output
                output_lines = result.stdout.split('\n')
                for line in output_lines:
                    if 'Timestamp:' in line or 'Hash of file' in line or 'Issued to:' in line:
                        print(f"   📋 {line.strip()}")
                        
            else:
                print("   ⚠️  Signature verification failed")
                print(f"   📋 {result.stderr.strip()[:200]}...")
                
        except Exception as e:
            print(f"   ❌ Verification error: {e}")

    def _show_smartscreen_advice(self, exe_path):
        """Show SmartScreen and AV advice"""
        print("💡 SmartScreen & Antivirus Advice:")
        print("   🛡️  Your executable is now signed and timestamped")
        print("   📈 This greatly improves SmartScreen reputation")
        print("   🕒 Timestamps ensure signature validity even after certificate expiry")
        print("   🔄 Dual signatures support both modern and legacy Windows systems")
        print("")
        print("   ⭐ For best results:")
        print("   • Use an Extended Validation (EV) certificate for instant reputation")
        print("   • Submit to Microsoft SmartScreen for reputation building")
        print("   • Consider VirusTotal submission for multi-AV scanning")

    def _show_unsigned_warnings(self):
        """Show warnings when executable is not signed"""
        print("⚠️  UNSIGNED EXECUTABLE WARNINGS:")
        print("=" * 45)
        print("❌ Your executable is NOT SIGNED - this may cause:")
        print("   🛡️  SmartScreen warnings for users")
        print("   🚫 Antivirus false positives")
        print("   ⚠️  'Unknown Publisher' security warnings")
        print("   📱 Mobile Device Management (MDM) blocks")
        print("")
        print("💡 To fix this:")
        print("   1. Obtain a code signing certificate:")
        print("      • Self-signed: py build_cli.py --setup sign")
        print("      • Commercial: DigiCert, Sectigo, GlobalSign, etc.")
        print("   2. Set environment variables:")
        print("      • set CERT_PATH=path\\to\\certificate.pfx")
        print("      • set CERT_PASSWORD=your_password")
        print("   3. Rebuild with signing enabled")
        print("")

    def _extract_signing_error(self, stderr_text):
        """Extract useful error information from SignTool output"""
        if not stderr_text:
            return "Unknown error"
        
        # Common error patterns
        error_patterns = [
            "timestamp server",
            "certificate",
            "password",
            "network",
            "timeout",
            "access denied"
        ]
        
        stderr_lower = stderr_text.lower()
        for pattern in error_patterns:
            if pattern in stderr_lower:
                # Find the line containing the pattern
                for line in stderr_text.split('\n'):
                    if pattern in line.lower():
                        return line.strip()[:100]
        
        # Return first meaningful line
        lines = [line.strip() for line in stderr_text.split('\n') if line.strip()]
        return lines[0][:100] if lines else "Unknown error"

    def execute_signtool(self, config):
        """Execute SignTool to sign the MSIX package"""
        try:
            print("🔐 Running SignTool on MSIX package...")
            
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
                print("⚠️  No certificate configured - skipping MSIX signing")
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
            
            # Build SignTool command with enhanced error handling
            output_path = os.path.join(config['package_dir'], config['output_file'])
            
            # For MSIX signing, we'll try fewer approaches since it's more restricted
            signing_attempts = []
            
            if cert_password:
                # Simple approach for MSIX - avoid complex options that might not work
                signing_attempts.append({
                    'name': 'MSIX with SHA256',
                    'cmd': [
                        signtool_path,
                        'sign',
                        '/f', cert_path,
                        '/p', cert_password,
                        '/fd', 'SHA256',
                        output_path
                    ]
                })
                
                # Fallback with SHA1
                signing_attempts.append({
                    'name': 'MSIX with SHA1',
                    'cmd': [
                        signtool_path,
                        'sign',
                        '/f', cert_path,
                        '/p', cert_password,
                        '/fd', 'SHA1',
                        output_path
                    ]
                })
            else:
                # Certificate without password
                signing_attempts.append({
                    'name': 'MSIX certificate only',
                    'cmd': [
                        signtool_path,
                        'sign',
                        '/f', cert_path,
                        '/fd', 'SHA256',
                        output_path
                    ]
                })
            
            # Try each signing approach
            for i, attempt in enumerate(signing_attempts, 1):
                print(f"🔍 MSIX signing attempt {i}/{len(signing_attempts)}: {attempt['name']}")
                print(f"🔍 Command: signtool.exe sign /f {os.path.basename(cert_path)} [***] ... {os.path.basename(output_path)}")
                
                try:
                    # Execute command with timeout
                    result = subprocess.run(
                        attempt['cmd'],
                        cwd=config['package_dir'],
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    
                    if result.returncode == 0:
                        print("✅ MSIX package signed successfully")
                        print("📋 SignTool output:")
                        if result.stdout:
                            # Show relevant output lines
                            for line in result.stdout.split('\n'):
                                line = line.strip()
                                if line and any(keyword in line.lower() for keyword in ['successfully', 'completed', 'signed', 'done']):
                                    print(f"   {line}")
                        return True
                    else:
                        print(f"⚠️  MSIX attempt {i} failed with return code: {result.returncode}")
                        
                        # For MSIX, we expect failures with self-signed certs, so don't continue
                        if i == 1:  # First attempt failed
                            print("📋 MSIX Package Signing Information:")
                            print("   • MSIX packages require certificates to be installed in trusted stores")
                            print("   • Self-signed certificates often cannot sign MSIX packages directly")
                            print("   • The executable inside the package may already be signed")
                            print("")
                            print("📋 To enable MSIX signing:")
                            print("   1. Run as Administrator: py build_cli.py --setup sign")
                            print("   2. Or use a commercial code signing certificate")
                            print("")
                            
                            # Show brief error for diagnosis
                            if result.stderr:
                                error_preview = result.stderr[:200].replace('\n', ' ').replace('\r', '')
                                print(f"📋 Error preview: {error_preview}...")
                            
                            # Don't try other approaches for MSIX - it's likely a trust issue
                            return False
                            
                except subprocess.TimeoutExpired:
                    print(f"⚠️  MSIX attempt {i} timed out")
                    return False
                except Exception as e:
                    print(f"⚠️  MSIX attempt {i} exception: {e}")
                    return False
            
            print("❌ All MSIX signing attempts failed")
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

    def show_signing_error_details(self, result, cert_path, cert_password, error_text):
        """Show detailed signing error information"""
        print("📋 Detailed Error Information:")
        
        # Check for specific SignTool requirement messages
        if "No file digest algorithm specified" in error_text:
            print("🔍 SignTool Digest Algorithm Issue:")
            print("   • Modern SignTool versions require explicit digest algorithm")
            print("   • Attempting fallbacks with SHA1 and SHA256 algorithms")
            print("   • This is not an OS compatibility issue")
        elif "A required function is not present" in error_text:
            print("🔍 OS Compatibility Issue:")
            print("   • Windows version does not support specified SignTool options")
            print("   • This typically occurs with older Windows versions or SignTool versions")
            print("   • Solution: Will try fallback signing methods with legacy options")
            print("   • Consider updating Windows SDK for better compatibility")
        elif "SignerSign() failed" in error_text:
            print("🔍 SignerSign() Error Analysis:")
            
            if "0x8007000b" in error_text or "internal error" in error_text:
                print("   • Certificate trust issue detected")
                print("   • Solution: Install certificate to trusted stores")
                print("   • Run: py build_cli.py --setup sign (as Administrator)")
            elif "0x80070005" in error_text:
                print("   • Access denied error")
                print("   • Solution: Run as Administrator")
            elif "0x80092004" in error_text:
                print("   • Certificate validation failed")
                print("   • Solution: Check certificate validity and trust chain")
            else:
                print("   • Generic SignerSign() failure")
                print("   • This often indicates certificate or trust issues")
        
        if "timestamp" in error_text.lower():
            print("🔍 Timestamp server issues:")
            print("   • Network connectivity problems")
            print("   • Timestamp server temporarily unavailable")
            print("   • Try signing without timestamp server")
        
        # Check Windows version for specific guidance
        try:
            import platform
            win_version = platform.version()
            win_release = platform.release()
            print(f"🔍 System Info: Windows {win_release} (Version {win_version})")
            
            # Provide specific guidance based on Windows version
            if win_release in ['7', '8', '8.1']:
                print("   • Older Windows version detected")
                print("   • Modern SignTool options may not be supported")
                print("   • Using legacy signing fallbacks recommended")
            elif win_release == '10':
                print("   • Windows 10 detected - should support modern SignTool")
                print("   • Digest algorithm requirements may vary by build")
        except Exception:
            pass
        
        print("\n📋 Troubleshooting Steps:")
        print("1. Verify certificate is valid:")
        print(f"   py certificate_setup.py")
        print("2. Install certificate to trusted stores:")
        print(f"   py build_cli.py --setup sign (as Administrator)")  
        print("3. Try creating a new certificate:")
        print(f"   py build_cli.py --new cert (as Administrator)")
        print("4. For digest algorithm issues:")
        print("   • Modern SignTool requires explicit /fd parameter")
        print("   • Automatic fallbacks include SHA1 and SHA256 options")
        print("5. For older Windows versions:")
        print("   • Update Windows SDK to latest version")
        print("   • Use legacy signing options (automatically attempted)")
        
        if result.stdout:
            print(f"\n📋 SignTool stdout: {result.stdout}")
        if result.stderr:
            print(f"📋 SignTool stderr: {result.stderr}")

    def get_certificate_info(self):
        """Enhanced certificate discovery with multiple provider support"""
        
        # Priority order: Environment -> Windows Store -> HSM/Key Vault -> File-based
        
        # 1. Check environment variables for explicit certificate configuration
        cert_config = self._get_env_certificate_config()
        if cert_config:
            return cert_config
            
        # 2. Try Windows Certificate Store (if on Windows)
        if os.name == 'nt':
            store_cert = self._get_certificate_from_store()
            if store_cert:
                return store_cert
                
        # 3. Check for HSM/Key Vault configuration
        hsm_config = self._get_hsm_certificate_config()
        if hsm_config:
            return hsm_config
        
        # 4. File-based certificate discovery with secure prompting
        file_cert = self._get_file_certificate_with_prompt()
        if file_cert:
            return file_cert
            
        return None

    def _get_env_certificate_config(self):
        """Get certificate configuration from environment variables"""
        # Standard file-based certificate
        env_cert_path = os.environ.get('CERT_PATH')
        env_cert_password = os.environ.get('CERT_PASSWORD')
        
        if env_cert_path and os.path.exists(env_cert_path):
            return ('file', env_cert_path, env_cert_password)
        
        # Windows Certificate Store configuration
        cert_subject = os.environ.get('CERT_SUBJECT')  # e.g., "CN=MyCompany"
        cert_thumbprint = os.environ.get('CERT_THUMBPRINT')  # SHA-1 thumbprint
        cert_store = os.environ.get('CERT_STORE', 'My')  # Default to Personal store
        
        if cert_subject or cert_thumbprint:
            return ('store', cert_subject or cert_thumbprint, cert_store)
        
        # HSM/Key Vault configuration
        hsm_container = os.environ.get('HSM_CONTAINER')
        hsm_provider = os.environ.get('HSM_PROVIDER')
        key_vault_url = os.environ.get('KEY_VAULT_URL')
        key_vault_cert = os.environ.get('KEY_VAULT_CERT_NAME')
        
        if hsm_container and hsm_provider:
            return ('hsm', hsm_container, hsm_provider)
        elif key_vault_url and key_vault_cert:
            return ('keyvault', key_vault_url, key_vault_cert)
            
        return None

    def _get_certificate_from_store(self):
        """Get certificate from Windows Certificate Store"""
        try:
            import subprocess
            
            # Try to find code signing certificates in the store
            print("🔍 Searching Windows Certificate Store for code signing certificates...")
            
            # Use PowerShell to enumerate certificates
            ps_script = '''
            Get-ChildItem -Path "Cert:\\CurrentUser\\My" | 
            Where-Object { $_.EnhancedKeyUsageList -match "Code Signing" } |
            Select-Object Subject, Thumbprint, NotAfter |
            Format-Table -AutoSize
            '''
            
            result = subprocess.run(
                ['powershell', '-Command', ps_script],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout.strip():
                print("📋 Available code signing certificates:")
                print(result.stdout)
                
                # For now, return the first certificate found (could be enhanced with user selection)
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if 'CN=' in line:  # Found a certificate line
                        parts = line.split()
                        if len(parts) >= 2:
                            thumbprint = parts[1] if len(parts[1]) == 40 else None
                            if thumbprint:
                                print(f"✅ Using certificate: {parts[0]}")
                                return ('store', thumbprint, 'My')
                                
        except Exception as e:
            print(f"⚠️  Could not access Windows Certificate Store: {e}")
            
        return None

    def _get_hsm_certificate_config(self):
        """Get HSM/Key Vault certificate configuration"""
        # Check for Azure Key Vault configuration
        if os.environ.get('AZURE_KEY_VAULT_URL'):
            vault_url = os.environ.get('AZURE_KEY_VAULT_URL')
            cert_name = os.environ.get('AZURE_KEY_VAULT_CERT_NAME')
            if vault_url and cert_name:
                return ('azure_keyvault', vault_url, cert_name)
        
        # Check for generic HSM configuration
        hsm_container = os.environ.get('HSM_CONTAINER_NAME')
        hsm_provider = os.environ.get('HSM_PROVIDER_NAME', 'Microsoft Enhanced RSA and AES Cryptographic Provider')
        
        if hsm_container:
            return ('hsm', hsm_container, hsm_provider)
            
        return None

    def _get_file_certificate_with_prompt(self):
        """Get file-based certificate with secure password prompting"""
        import getpass
        
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
                print(f"📋 Found certificate: {os.path.basename(cert_path)}")
                
                # Try default password first
                password = default_password
                
                # Check for password file
                if not password:
                    password_file = cert_path.replace('.pfx', '.password')
                    if os.path.exists(password_file):
                        try:
                            with open(password_file, 'r', encoding='utf-8') as f:
                                password = f.read().strip()
                                print("🔑 Using password from .password file")
                        except Exception:
                            pass
                
                # If no password found, prompt securely
                if not password:
                    try:
                        password = getpass.getpass(f"🔐 Enter password for {os.path.basename(cert_path)}: ")
                    except KeyboardInterrupt:
                        print("\n❌ Certificate password entry cancelled")
                        continue
                    except Exception as e:
                        print(f"⚠️  Error reading password: {e}")
                        continue
                
                return ('file', cert_path, password)
                
                return ('file', cert_path, password)
                
        return None

    def _get_timestamp_servers_config(self):
        """Get configurable timestamp server list with failover support"""
        
        # Check for custom TSA configuration
        custom_tsa_list = os.environ.get('CUSTOM_TSA_SERVERS')
        if custom_tsa_list:
            servers = [server.strip() for server in custom_tsa_list.split(',')]
            return {
                'rfc3161_servers': [s for s in servers if 'rfc3161' in s.lower() or not s.startswith('http://timestamp')],
                'authenticode_servers': [s for s in servers if s.startswith('http://timestamp')]
            }
        
        # Default enterprise-grade timestamp servers with geographic distribution
        return {
            'rfc3161_servers': [
                "http://timestamp.digicert.com",           # Primary - DigiCert (US)
                "http://timestamp.sectigo.com",            # Sectigo (UK) 
                "http://timestamp.globalsign.com/?signature=sha2",  # GlobalSign (EU)
                "http://tsa.starfieldtech.com",           # Starfield (US)
                "http://timestamp.entrust.net/TSS/RFC3161sha2TS",  # Entrust (CA)
                "http://timestamp.comodoca.com",           # Sectigo alternative
                "http://rfc3161timestamp.globalsign.com/advanced",  # GlobalSign advanced
                "http://timestamp.apple.com/ts01"          # Apple (for additional redundancy)
            ],
            'authenticode_servers': [
                "http://timestamp.digicert.com",           # DigiCert Authenticode
                "http://timestamp.sectigo.com/authenticode",  # Sectigo Authenticode  
                "http://timestamp.comodoca.com/authenticode",  # Legacy Comodo
                "http://timestamp.globalsign.com/scripts/timstamp.dll",  # GlobalSign legacy
                "http://timestamp.verisign.com/scripts/timstamp.dll",    # Legacy Verisign
                "http://timestamp.entrust.net/TSS/AuthenticodeTS"        # Entrust Authenticode
            ]
        }

    def _build_signing_command(self, cert_config, exe_path, digest='SHA256', append_signature=False):
        """Build SignTool command based on certificate provider type"""
        
        cert_type, cert_data, cert_extra = cert_config
        
        base_cmd = ['signtool', 'sign']
        
        # Configure certificate source
        if cert_type == 'file':
            cert_path, password = cert_data, cert_extra
            base_cmd.extend(['/f', cert_path])
            if password:
                base_cmd.extend(['/p', password])
                
        elif cert_type == 'store':
            # Windows Certificate Store signing
            thumbprint_or_subject, store_name = cert_data, cert_extra
            base_cmd.extend(['/s', store_name])
            
            if len(thumbprint_or_subject) == 40:  # Thumbprint
                base_cmd.extend(['/sha1', thumbprint_or_subject])
            else:  # Subject name
                base_cmd.extend(['/n', thumbprint_or_subject])
                
        elif cert_type == 'hsm':
            # Hardware Security Module
            container_name, provider_name = cert_data, cert_extra
            base_cmd.extend(['/csp', provider_name])
            base_cmd.extend(['/kc', container_name])
            
        elif cert_type == 'azure_keyvault':
            # Azure Key Vault (requires Azure CLI and special setup)
            vault_url, cert_name = cert_data, cert_extra
            # Note: This requires AzureSignTool or special SignTool configuration
            print("⚠️  Azure Key Vault signing requires AzureSignTool")
            print(f"   Install: dotnet tool install --global AzureSignTool")
            print(f"   Command: azuresigntool sign -kvu {vault_url} -kvc {cert_name}")
            return None
        
        # Add digest algorithm
        base_cmd.extend(['/fd', digest])
        
        # Add signature description and URL
        base_cmd.extend(['/d', 'PDF Utility Application'])
        base_cmd.extend(['/du', 'https://github.com/braydenanderson2014/PDF-Utility'])
        
        # Append signature for dual-signing
        if append_signature:
            base_cmd.append('/as')
        
        base_cmd.append(exe_path)
        return base_cmd

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
                
                # Auto-run smoke test if requested
                if '--auto-smoke-test' in sys.argv or '--smoke-test-after-build' in sys.argv:
                    safe_print("\n🧪 Running automatic post-build smoke test...")
                    
                    # Find the built executable
                    dist_dir = 'dist'
                    if os.path.exists(dist_dir):
                        exe_files = [f for f in os.listdir(dist_dir) if f.endswith('.exe')]
                        if exe_files:
                            latest_exe = max(exe_files, key=lambda f: os.path.getmtime(os.path.join(dist_dir, f)))
                            exe_path = os.path.join(dist_dir, latest_exe)
                            
                            try:
                                smoke_tester = SmokeTestManager(test_timeout=15)  # Shorter timeout for auto-test
                                enable_gui = '--gui-test' in sys.argv
                                smoke_result = smoke_tester.run_smoke_test(exe_path, enable_gui_test=enable_gui)
                                
                                if smoke_result:
                                    safe_print("🎉 Smoke test passed - executable ready for distribution!")
                                else:
                                    safe_print("⚠️  Smoke test failed - review test results before distribution")
                            except Exception as e:
                                safe_print(f"⚠️  Smoke test error: {e}")
                        else:
                            safe_print("⚠️  No executable found for smoke testing")
                    else:
                        safe_print("⚠️  No dist directory found for smoke testing")
                
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
        '--console', '--install', '--new', '--new-project', '--name', '--date',
        '--downgrade', '--preview-name', '--virtual', '--activate',
        '--scan-dir', '--scan-here', '--type', '--contains', '--install-needed',
        '--location', '--scan-project', '--target', '--from', '--set-root', '--show-root',
        '--append', '--export', '--export-config', '--start',
        '--remove-type', '--delete', '--delete-type', '--create',
        '--show-console', '--auto', '--backup', '--remove', '--add',
        '--detailed', '--main', '--set-version', '--add-to-path',
        '--windowed', '--no-console', '--clean',
        '--replace', '--recreate', '--repair', '--distant-scan',
        '--version', '--latest', '--gui',
        '--no-dual-sign', '--enable-dual-sign', '--no-timestamp', '--verify-signature'
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
        '--version', '--latest', '--windowed', '--no-console', '--clean',
        '--no-dual-sign', '--enable-dual-sign', '--no-timestamp', '--verify-signature'
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
            
        elif arg == '--no-dual-sign':
            # Disable dual signing (SHA-256 only)
            queue.append({
                'type': 'config',
                'key': 'dual_sign',
                'value': False
            })
            i += 1
            
        elif arg == '--enable-dual-sign':
            # Enable dual signing (SHA-256 + SHA-1) - default behavior
            queue.append({
                'type': 'config',
                'key': 'dual_sign',
                'value': True
            })
            i += 1
            
        elif arg == '--no-timestamp':
            # Disable timestamping (not recommended)
            queue.append({
                'type': 'config',
                'key': 'enable_timestamp',
                'value': False
            })
            i += 1
            
        elif arg == '--verify-signature':
            # Force signature verification after signing
            queue.append({
                'type': 'verify-signature'
            })
            i += 1
            
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
            
        elif command['type'] == 'config':
            return execute_config_command(command.get('key'), command.get('value'))
            
        elif command['type'] == 'verify-signature':
            return execute_verify_signature_command()
            
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
                # Create a BuildToolCore instance to access the methods
                build_core = BuildToolCore()
                latest_version = build_core.find_latest_python_version()
                if latest_version:
                    python_exec = build_core.find_python_executable(latest_version)
                else:
                    python_exec = None
                    
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
    
    # Handle ultra-fast commands directly WITHOUT safe print override
    if '--help' in sys.argv or '-h' in sys.argv:
        show_integrated_help()
        return True
    
    # Handle version command with original print (no safe print override needed)
    if '--version' in sys.argv:
        # Use original print for version info
        original_print = __builtins__['print'] if isinstance(__builtins__, dict) else __builtins__.print
        original_print("PyInstaller Build Tool - CLI Core Module")
        original_print("Version: 2.0.0-core")
        original_print("Integrated CLI with no GUI dependencies")
        return True
    
    # Handle UAC-sensitive commands without safe print override to prevent hangs
    if '--sandbox' in sys.argv and '--install' in sys.argv:
        return handle_sandbox_testing()
    
    if '--setup' in sys.argv and 'sign' in sys.argv:
        return handle_setup_command()

    # Enable safe Unicode printing for elevated processes (only for non-sensitive commands)
    def safe_unicode_print(*args, **kwargs):
        """Safe print that handles Unicode encoding issues"""
        # Use the original built-in print to avoid recursion
        original_print = __builtins__['print'] if isinstance(__builtins__, dict) else __builtins__.print
        
        try:
            original_print(*args, **kwargs)
        except UnicodeEncodeError:
            # Replace Unicode emojis with ASCII equivalents
            safe_args = []
            for arg in args:
                if isinstance(arg, str):
                    safe_arg = (str(arg)
                        .replace('❌', '[X]').replace('✅', '[OK]').replace('⚠️', '[WARN]')
                        .replace('🔧', '[TOOL]').replace('🔍', '[SCAN]').replace('📦', '[PKG]')
                        .replace('💡', '[TIP]').replace('🖥️', '[OS]').replace('🔐', '[LOCK]')
                        .replace('📋', '[LIST]').replace('📁', '[DIR]').replace('📄', '[FILE]')
                    )
                    # Strip any remaining non-ASCII characters
                    safe_arg = safe_arg.encode('ascii', 'ignore').decode('ascii')
                    safe_args.append(safe_arg)
                else:
                    safe_args.append(str(arg).encode('ascii', 'ignore').decode('ascii'))
            original_print(*safe_args, **kwargs)
        except:
            # Last resort - use basic print without any Unicode
            try:
                ascii_args = [str(arg).encode('ascii', 'ignore').decode('ascii') for arg in args]
                original_print(*ascii_args, **kwargs)
            except:
                # Absolute last resort
                original_print("ERROR: Could not display message due to encoding issues")
    
    # Override print for this session (only for non-help commands)
    import builtins
    builtins.print = safe_unicode_print

    # GitHub Actions Helper: build_cli.py ci --github
    if 'ci' in sys.argv and '--github' in sys.argv:
        return handle_ci_github_command()
        
    elif '--ci' in sys.argv and '--github' in sys.argv:
        return handle_ci_github_command()
    
    elif '--progress' in sys.argv:
        return handle_progress_status()
    
    elif '--history' in sys.argv:
        return handle_command_history()
    
    elif '--select-files' in sys.argv:
        return handle_interactive_file_selection()
    
    elif '--bulk-add' in sys.argv:
        return handle_bulk_operations()

    elif '--sandbox' in sys.argv:
        return handle_sandbox_testing()

    elif '--sandbox-status' in sys.argv:
        return handle_sandbox_status_check()
    
    elif '--uac-test' in sys.argv:
        return demonstrate_elevated_output_capture()

    elif '--changelog' in sys.argv:
        print("""
PyInstaller Build Tool - Changelog

Version 2.0.0-core:
  • Integrated CLI core - no separate core module needed
  • Removed GUI dependencies from CLI for clean separation
  • CLI now serves as the core functionality
  • GUI will be separate module that interfaces with CLI core
  • Prevents PyInstaller GUI conflicts when using CLI commands
  • Added TUI enhancements: progress tracking, searchable lists, bulk operations
  • Added GUI-CLI bridge for progress communication
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
        
    elif '--no-dual-sign' in sys.argv:
        return execute_config_command('dual_sign', False)
        
    elif '--enable-dual-sign' in sys.argv:
        return execute_config_command('dual_sign', True)
        
    elif '--no-timestamp' in sys.argv:
        return execute_config_command('enable_timestamp', False)
        
    elif '--verify-signature' in sys.argv:
        return execute_verify_signature_command()
        
    elif '--cert-file' in sys.argv:
        # Set certificate file path
        try:
            idx = sys.argv.index('--cert-file')
            if idx + 1 < len(sys.argv):
                cert_path = sys.argv[idx + 1]
                os.environ['CERT_PATH'] = cert_path
                print(f"✅ Certificate file set: {cert_path}")
                return True
            else:
                print("❌ --cert-file requires a path argument")
                return False
        except Exception as e:
            print(f"❌ Error setting certificate file: {e}")
            return False
    
    elif '--cert-store' in sys.argv:
        # Set Windows Certificate Store subject/thumbprint
        try:
            idx = sys.argv.index('--cert-store')
            if idx + 1 < len(sys.argv):
                cert_subject = sys.argv[idx + 1]
                os.environ['CERT_SUBJECT'] = cert_subject
                print(f"✅ Certificate store subject set: {cert_subject}")
                return True
            else:
                print("❌ --cert-store requires a subject or thumbprint argument")
                return False
        except Exception as e:
            print(f"❌ Error setting certificate store: {e}")
            return False
            
    elif '--cert-hsm' in sys.argv:
        # Set HSM container
        try:
            idx = sys.argv.index('--cert-hsm')
            if idx + 1 < len(sys.argv):
                container = sys.argv[idx + 1]
                os.environ['HSM_CONTAINER'] = container
                print(f"✅ HSM container set: {container}")
                return True
            else:
                print("❌ --cert-hsm requires a container name argument")
                return False
        except Exception as e:
            print(f"❌ Error setting HSM container: {e}")
            return False
            
    elif '--cert-keyvault' in sys.argv:
        # Set Azure Key Vault URL
        try:
            idx = sys.argv.index('--cert-keyvault')
            if idx + 1 < len(sys.argv):
                vault_url = sys.argv[idx + 1]
                os.environ['AZURE_KEY_VAULT_URL'] = vault_url
                print(f"✅ Azure Key Vault URL set: {vault_url}")
                return True
            else:
                print("❌ --cert-keyvault requires a vault URL argument")
                return False
        except Exception as e:
            print(f"❌ Error setting Key Vault URL: {e}")
            return False
            
    elif '--tsa-servers' in sys.argv:
        # Set custom timestamp servers
        try:
            idx = sys.argv.index('--tsa-servers')
            if idx + 1 < len(sys.argv):
                servers = sys.argv[idx + 1]
                os.environ['CUSTOM_TSA_SERVERS'] = servers
                print(f"✅ Custom timestamp servers set: {servers}")
                return True
            else:
                print("❌ --tsa-servers requires a comma-separated list")
                return False
        except Exception as e:
            print(f"❌ Error setting TSA servers: {e}")
            return False
            
    elif '--tsa-retries' in sys.argv:
        # Set TSA retry count
        try:
            idx = sys.argv.index('--tsa-retries')
            if idx + 1 < len(sys.argv):
                retries = sys.argv[idx + 1]
                os.environ['TSA_MAX_RETRIES'] = retries
                print(f"✅ TSA max retries set: {retries}")
                return True
            else:
                print("❌ --tsa-retries requires a number argument")
                return False
        except Exception as e:
            print(f"❌ Error setting TSA retries: {e}")
            return False
            
    elif '--tsa-delay' in sys.argv:
        # Set TSA retry delay
        try:
            idx = sys.argv.index('--tsa-delay')
            if idx + 1 < len(sys.argv):
                delay = sys.argv[idx + 1]
                os.environ['TSA_RETRY_DELAY'] = delay
                print(f"✅ TSA retry delay set: {delay}s")
                return True
            else:
                print("❌ --tsa-delay requires a number argument")
                return False
        except Exception as e:
            print(f"❌ Error setting TSA delay: {e}")
            return False
            
    elif '--tsa-timeout' in sys.argv:
        # Set TSA timeout
        try:
            idx = sys.argv.index('--tsa-timeout')
            if idx + 1 < len(sys.argv):
                timeout = sys.argv[idx + 1]
                os.environ['TSA_TIMEOUT'] = timeout
                print(f"✅ TSA timeout set: {timeout}s")
                return True
            else:
                print("❌ --tsa-timeout requires a number argument")
                return False
        except Exception as e:
            print(f"❌ Error setting TSA timeout: {e}")
            return False
        
    elif '--setup-sdk' in sys.argv:
        return handle_setup_sdk_command()
        
    elif '--setup' in sys.argv:
        return handle_setup_command()
        
    elif '--doctor' in sys.argv:
        return handle_doctor_command()
        
    elif '--new' in sys.argv:
        return handle_new_command()
    
    elif '--new-project' in sys.argv:
        return handle_new_project_command()
    
    elif '--collect' in sys.argv:
        return handle_collect_command()
        
    elif '--import' in sys.argv:
        return handle_import_command()
        
    elif '--export' in sys.argv:
        return handle_export_command()
        
    elif '--export-manifest' in sys.argv:
        return handle_export_manifest_command()
        
    elif '--no-version-append' in sys.argv:
        return handle_no_version_append_command()
        
    elif '--gui' in sys.argv:
        return handle_gui_command()
        
    elif '--generate-hooks' in sys.argv:
        return handle_generate_hooks_command()
        
    elif '--trace-imports' in sys.argv:
        return handle_trace_imports_command()
        
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
    
    elif '--description' in sys.argv:
        return handle_description_command()
        
    elif '--force-clean' in sys.argv:
        return handle_force_clean_command()
        
    elif '--cache-info' in sys.argv:
        return handle_cache_info_command()
        
    elif '--smoke-test' in sys.argv:
        return handle_smoke_test_command()
        
    elif '--generate-appinstaller' in sys.argv:
        return handle_msix_appinstaller_command()
        
    elif '--github-connect' in sys.argv:
        return handle_github_connect_command()
        
    elif '--generate-winget' in sys.argv:
        return handle_winget_manifest_command()
    
    elif '--setup-wheelhouse' in sys.argv:
        return handle_setup_wheelhouse_command()
        
    elif '--wheelhouse-info' in sys.argv:
        return handle_wheelhouse_info_command()
    
    elif '--profile' in sys.argv:
        return handle_profile_command()
    
    elif '--template' in sys.argv:
        return handle_template_command()
    
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
  --export-manifest FILE Export reproducible build manifest with checksums
  --name NAME           Set custom build name
  --date BOOL           Include date in build name (true/false)
  --windowed            Enable windowed mode (no console window)
  --no-console [BOOL]   Same as --windowed, accepts true/false
  --virtual ENV_NAME    Create/manage virtual environment
  --activate [ENV_NAME] Activate virtual environment
  --add-to-path         Add CLI to system PATH
  --setup-sdk           Setup Windows SDK PATH for packaging tools
  --setup TYPE          Setup system components (sign, sdk, env)
  --doctor              Verify toolchain and dependencies
  --new TYPE            Create new items (cert, keysign)
  --description [TEXT]  Set or view build description
  --description --import-from FILE  Import description from file
  --force-clean         Force clean rebuild (bypass incremental cache)
  --cache-info          Show build cache information
  --smoke-test          Run post-build smoke test on latest executable
  --generate-appinstaller  Generate MSIX App Installer for auto-updates
  --github-connect      Connect to GitHub repository for testing
  --generate-winget     Generate Windows Package Manager (Winget) manifest

TUI Enhancement Commands:
  --progress [--json]   Show build progress status (JSON output for GUI)
  --history             Show command history with success indicators
  --history --repeat N  Repeat command number N from history
  --select-files [--multi]  Interactive searchable file selection
  --bulk-add            Bulk add files with pattern matching (images, configs, etc.)
  --bulk-add --remove   Bulk remove files from configuration

Windows Sandbox Testing:
  --sandbox             Create Windows Sandbox test environment (.wsb file)
  --sandbox-status      Diagnose Windows Sandbox installation and compatibility
  --sandbox --install   Install/enable Windows Sandbox feature (requires admin)
  --sandbox --portable  Create portable test package (Windows Home compatible)
  --sandbox --venv NAME Use custom virtual environment name
  --sandbox --memory MB Set sandbox memory (default: 4096MB)
  --sandbox --no-vgpu   Disable GPU acceleration in sandbox
  --sandbox --offline   Disable networking in sandbox
  --sandbox --dev       Include development files (not just builds)
  --sandbox --test-files Create dummy test files for demonstration
  --sandbox --skip-validation  Skip Windows Sandbox feature validation (dev mode)
  --sandbox --dry-run   Create files but don't launch sandbox (testing mode)

UAC & Elevation Testing:
  --uac-test            Test UAC elevation with output capture system

GUI-CLI Bridge:
  The progress tracking system creates temporary files that GUI can poll:
  - Progress: %TEMP%/build_cli_progress.json
  - History: %TEMP%/build_cli_history.json
  - Commands: %TEMP%/build_cli_commands.json

CI/CD and Performance Commands:
  ci --github           Show GitHub Actions workflow steps and env vars
  --setup-wheelhouse    Setup local wheel cache for fast repeated builds
  --wheelhouse-info     Show wheelhouse cache status and information
  --profile PROFILE     Set build profile (dev|prod|debug|release|test)
  --template TEMPLATE   Set project template (tkinter|pyqt5|pyqt6|pyside2|pyside6|pymupdf|fastapi|flask|matplotlib|default)
  --new-project NAME    Create new project with template, virtual environment, and dependencies

Advanced PyInstaller Features:
  --generate-hooks [FILE]      Generate PyInstaller hooks for better import detection
  --trace-imports [FILE]       Trace and analyze hidden imports in Python files

Code Signing Commands:
  --setup sign          Configure code signing certificates
  --new cert            Create self-signed code signing certificate
  --new keysign         Create code signing certificate (alias)

Advanced Signing Features (AV/SmartScreen Friendly):
  • Automatic SHA-256 + SHA-1 dual signatures for maximum compatibility
  • Multiple timestamping servers with automatic fallback
  • RFC 3161 and Authenticode timestamp support
  • Enhanced signature verification and reporting
  • SmartScreen reputation optimization
  • Comprehensive unsigned executable warnings

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
  python build_cli.py --export-manifest build_manifest.json  Export reproducible build manifest

Modifier Flags:
  --auto                Enable automatic detection and configuration
                        (Must be combined with other commands)
  --append              Append to existing results instead of replacing
  --override            Override/replace existing results (explicit replace mode)
  --no-version          Disable version appending for current build
  --no-version-append BOOL  Set global version append setting (true/false)
  --auto-smoke-test     Run smoke test automatically after successful build
  --gui-test            Include GUI testing in smoke tests
  --msix-update-uri URI Set MSIX update server URI
  --msix-min-version VER Set minimum MSIX version for updates
  --release-channel CHAN Set release channel (stable/beta)
  --github-repo REPO    GitHub repository (owner/repo format)
  --github-token TOKEN  GitHub API token for private repos
  --github-branch BRANCH GitHub branch (default: main)
  --bundle TYPE         Bundle type for packaging (onefile|onedir|portable)
  --default TYPE        Set default bundle type for current session
  --winget-output FILE  Output path for Winget manifest file
  --winget-publisher PUB Publisher name for Winget manifest
  --winget-homepage URL Homepage URL for Winget manifest
  --winget-license LIC  License type for Winget manifest
  --winget-download-url URL Download URL template for releases

Code Signing Options (AV/SmartScreen Friendly):
  --no-dual-sign        Disable dual signatures (SHA-256 only)
  --enable-dual-sign    Enable dual signatures (SHA-256 + SHA-1) - default
  --no-timestamp        Disable timestamping (not recommended for production)
  --verify-signature    Verify signature of most recently built executable

Certificate Provider Options:
  --cert-file PATH      Use certificate from file (.pfx)
  --cert-store SUBJECT  Use certificate from Windows Store by subject/thumbprint
  --cert-hsm CONTAINER  Use HSM certificate container
  --cert-keyvault URL   Use Azure Key Vault certificate

Timestamp Configuration:
  --tsa-servers LIST    Comma-separated list of timestamp servers
  --tsa-retries N       Number of retry attempts per server (default: 3)
  --tsa-delay SECONDS   Delay between retries (default: 2.0)
  --tsa-timeout SECONDS Timeout per attempt (default: 45)

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

Code Signing Examples:
  python build_cli.py --new cert             Create self-signed certificate
  python build_cli.py --setup sign           Configure code signing
  python build_cli.py --start package        Build signed MSIX package

System Verification Examples:
  python build_cli.py --doctor               Verify entire toolchain and dependencies
  python build_cli.py --setup env            Diagnose Python environment issues

Description Management Examples:
  python build_cli.py --description "PDF utility app"  Set description directly
  python build_cli.py --description --import-from desc.txt  Import from text file
  python build_cli.py --description --import-from info.json  Import from JSON file
  python build_cli.py --description          Show current description

Incremental Build Examples:
  python build_cli.py --start build          Use incremental build (skip if unchanged)
  python build_cli.py --force-clean --start build  Force clean rebuild
  python build_cli.py --cache-info           Show build cache status
  python build_cli.py --force-clean          Clear all build caches

Post-Build Testing Examples:
  python build_cli.py --smoke-test           Run smoke test on latest executable
  python build_cli.py --smoke-test --gui-test  Include GUI testing in smoke test
  python build_cli.py --start build --auto-smoke-test  Build with automatic smoke test
  python build_cli.py --start package --auto-smoke-test --gui-test  Package with full testing

MSIX App Installer Examples:
  python build_cli.py --generate-appinstaller  Generate basic App Installer
  python build_cli.py --generate-appinstaller --msix-update-uri "https://mysite.com/updates/"  
  python build_cli.py --generate-appinstaller --release-channel beta --msix-min-version 1.2.0
  python build_cli.py --start package --generate-appinstaller --msix-update-uri "https://releases.myapp.com/"

GitHub Integration Examples:
  python build_cli.py --github-connect --github-repo "owner/repo"  Connect to public repo
  python build_cli.py --github-connect --github-repo "owner/repo" --github-token "ghp_xxx"  Private repo
  python build_cli.py --github-connect --github-repo "myuser/myapp" --github-branch "develop"  Specific branch

Winget Manifest Examples:
  python build_cli.py --generate-winget      Generate basic Winget manifest (onefile)
  python build_cli.py --generate-winget --bundle onedir  Generate manifest for directory bundle
  python build_cli.py --generate-winget --bundle portable  Generate manifest for portable app
  python build_cli.py --generate-winget --default onefile  Set onefile as default bundle type
  python build_cli.py --generate-winget --winget-publisher "My Company" --winget-license "MIT"
  python build_cli.py --generate-winget --winget-homepage "https://myapp.com" --winget-output "MyApp.yaml"

Advanced PyInstaller Examples:
  python build_cli.py --generate-hooks       Auto-generate hooks using main file from memory
  python build_cli.py --generate-hooks main.py  Generate hooks for specific file
  python build_cli.py --trace-imports        Trace hidden imports using main file from memory
  python build_cli.py --trace-imports app.py    Trace hidden imports for specific file
  python build_cli.py --main app.py --generate-hooks  Set main file then generate hooks
  python build_cli.py --trace-imports --start build  Trace imports and build with results

CI/CD and Performance Examples:
  python build_cli.py ci --github            Show GitHub Actions workflow template
  python build_cli.py --setup-wheelhouse     Setup local wheel cache for faster builds
  python build_cli.py --wheelhouse-info      Check wheelhouse cache status
  python build_cli.py --force-clean          Clear all caches (build + wheelhouse)

Build Profile Examples:
  python build_cli.py --profile dev          Set development profile (console, no UPX, debug logs)
  python build_cli.py --profile prod         Set production profile (windowed, UPX, optimized)
  python build_cli.py --profile debug        Set debug profile (max debugging info)
  python build_cli.py --profile release      Set release profile (max optimization, signed)
  python build_cli.py --profile test         Set testing profile (includes test frameworks)
  python build_cli.py --profile current      Show current active profile
  python build_cli.py --profile list         List all available profiles

Project Template Examples:
  python build_cli.py --template tkinter     Set Tkinter GUI template (tkinter + themed widgets)
  python build_cli.py --template pyqt6       Set PyQt6 GUI template (Qt6 widgets, windowed)
  python build_cli.py --template pyqt5       Set PyQt5 GUI template (Qt5 widgets, windowed)
  python build_cli.py --template pyside6     Set PySide6 GUI template (Qt6 widgets, windowed)
  python build_cli.py --template pymupdf     Set PyMuPDF template (PDF processing, document handling)
  python build_cli.py --template fastapi     Set FastAPI template (web API, uvicorn server)
  python build_cli.py --template flask       Set Flask template (web app, werkzeug server)
  python build_cli.py --template matplotlib  Set Matplotlib template (data visualization, plotting)
  python build_cli.py --template auto        Auto-detect template based on project files
  python build_cli.py --template current     Show current active template
  python build_cli.py --template list        List all available templates

Project Creation Examples:
  python build_cli.py --new-project MyApp             Create default Python project
  python build_cli.py --new-project MyGUI --template tkinter    Create Tkinter GUI project
  python build_cli.py --new-project MyAPI --template fastapi    Create FastAPI web project
  python build_cli.py --new-project MyQt --template pyqt6       Create PyQt6 desktop app
  python build_cli.py --new-project MyApp --target C:\Projects  Create project in specific directory
  python build_cli.py --new-project MyApp --location ./my-projects  Create project in subdirectory
  python build_cli.py --new-project MyApp --dir D:\Work\Apps     Create project in custom location

Combined Usage Examples:
  python build_cli.py --template pyqt6 --profile prod  # PyQt6 app with production optimizations
  python build_cli.py --template fastapi --profile dev # FastAPI dev server with debugging
  python build_cli.py --template auto --profile release # Auto-detect + release optimizations

Note: Hook generation and import tracing will:
  • Generate PyInstaller hooks for better module detection
  • Create analysis files for hidden imports
  • Update build configuration automatically
  • Save results to hooks/ directory and analysis files

Location Flags for Project Creation:
  --target PATH    Create project in specified directory (absolute or relative path)
  --location PATH  Same as --target (alternative name for clarity)
  --dir PATH       Same as --target (legacy support, same functionality)

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

# ============================================================================
# INCREMENTAL/DELTA BUILD SYSTEM
# ============================================================================

class IncrementalBuildManager:
    """Manages incremental builds with content hashing and cache management"""
    
    def __init__(self, cache_dir=None):
        self.cache_dir = cache_dir or os.path.join(os.getcwd(), '.build_cache')
        self.hash_cache_file = os.path.join(self.cache_dir, 'content_hashes.json')
        self.build_cache_file = os.path.join(self.cache_dir, 'build_cache.json')
        self.pyinstaller_cache_dir = os.path.join(self.cache_dir, 'pyinstaller_cache')
        self.ensure_cache_directory()
        
    def ensure_cache_directory(self):
        """Ensure cache directory exists"""
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(self.pyinstaller_cache_dir, exist_ok=True)
    
    def calculate_file_hash(self, file_path):
        """Calculate SHA256 hash of a file"""
        try:
            hasher = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            print(f"⚠️  Warning: Could not hash file {file_path}: {e}")
            return None
    
    def calculate_directory_hash(self, directory):
        """Calculate hash of all files in a directory tree"""
        file_hashes = []
        
        if not os.path.exists(directory):
            return None
            
        for root, dirs, files in os.walk(directory):
            # Sort for consistent hashing
            dirs.sort()
            files.sort()
            
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    file_hash = self.calculate_file_hash(file_path)
                    if file_hash:
                        relative_path = os.path.relpath(file_path, directory)
                        file_hashes.append(f"{relative_path}:{file_hash}")
                except Exception as e:
                    print(f"⚠️  Warning: Error processing {file_path}: {e}")
                    continue
        
        # Calculate combined hash
        combined = "|".join(sorted(file_hashes))
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def load_hash_cache(self):
        """Load previous content hashes"""
        if os.path.exists(self.hash_cache_file):
            try:
                with open(self.hash_cache_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def save_hash_cache(self, hashes):
        """Save content hashes to cache"""
        try:
            with open(self.hash_cache_file, 'w') as f:
                json.dump(hashes, f, indent=2)
        except Exception as e:
            print(f"⚠️  Warning: Could not save hash cache: {e}")
    
    def load_build_cache(self):
        """Load previous build metadata"""
        if os.path.exists(self.build_cache_file):
            try:
                with open(self.build_cache_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def save_build_cache(self, build_data):
        """Save build metadata to cache"""
        try:
            with open(self.build_cache_file, 'w') as f:
                json.dump(build_data, f, indent=2)
        except Exception as e:
            print(f"⚠️  Warning: Could not save build cache: {e}")
    
    def analyze_changes(self, scan_results, config):
        """Analyze what has changed since last build"""
        print("🔍 Analyzing changes for incremental build...")
        
        previous_hashes = self.load_hash_cache()
        current_hashes = {}
        changes = {
            'files_changed': [],
            'files_added': [],
            'files_removed': [],
            'dependencies_changed': False,
            'config_changed': False,
            'needs_full_rebuild': False
        }
        
        # 1. Check main files
        all_files = []
        for category, files in scan_results.items():
            if isinstance(files, list):
                all_files.extend(files)
            elif isinstance(files, dict):
                for subcategory, subfiles in files.items():
                    if isinstance(subfiles, list):
                        all_files.extend(subfiles)
        
        # Add main file if specified
        main_file = config.get('main_file')
        if main_file and os.path.exists(main_file):
            all_files.append(main_file)
        
        # Remove duplicates
        all_files = list(set(all_files))
        
        # Calculate current hashes
        for file_path in all_files:
            if os.path.exists(file_path):
                current_hash = self.calculate_file_hash(file_path)
                current_hashes[file_path] = current_hash
                
                if file_path in previous_hashes:
                    if previous_hashes[file_path] != current_hash:
                        changes['files_changed'].append(file_path)
                        print(f"   📝 Changed: {os.path.basename(file_path)}")
                else:
                    changes['files_added'].append(file_path)
                    print(f"   ➕ Added: {os.path.basename(file_path)}")
        
        # Check for removed files
        for file_path in previous_hashes:
            if file_path not in current_hashes:
                changes['files_removed'].append(file_path)
                print(f"   ➖ Removed: {os.path.basename(file_path)}")
        
        # 2. Check dependencies (rough approximation)
        try:
            import subprocess
            pip_freeze = subprocess.run([sys.executable, '-m', 'pip', 'freeze'], 
                                      capture_output=True, text=True, timeout=10)
            current_deps = pip_freeze.stdout if pip_freeze.returncode == 0 else ""
            current_deps_hash = hashlib.sha256(current_deps.encode()).hexdigest()
            
            previous_deps_hash = previous_hashes.get('_dependencies_hash')
            if previous_deps_hash != current_deps_hash:
                changes['dependencies_changed'] = True
                print("   📦 Dependencies changed")
                current_hashes['_dependencies_hash'] = current_deps_hash
        except Exception:
            # If we can't check dependencies, assume they changed
            changes['dependencies_changed'] = True
            print("   📦 Dependencies check failed - assuming changed")
        
        # 3. Check build configuration
        config_str = json.dumps(config, sort_keys=True)
        current_config_hash = hashlib.sha256(config_str.encode()).hexdigest()
        previous_config_hash = previous_hashes.get('_config_hash')
        
        if previous_config_hash != current_config_hash:
            changes['config_changed'] = True
            print("   ⚙️  Build configuration changed")
            current_hashes['_config_hash'] = current_config_hash
        
        # Determine if full rebuild is needed
        changes['needs_full_rebuild'] = (
            changes['dependencies_changed'] or 
            changes['config_changed'] or
            len(changes['files_added']) > 0 or
            len(changes['files_removed']) > 0 or
            len(changes['files_changed']) > len(all_files) * 0.3  # If >30% of files changed
        )
        
        # Save updated hashes
        self.save_hash_cache(current_hashes)
        
        return changes
    
    def should_skip_build(self, changes, force_clean=False):
        """Determine if build can be skipped"""
        if force_clean:
            print("🧹 Force clean build requested - rebuilding everything")
            return False
            
        if changes['needs_full_rebuild']:
            print("🔄 Full rebuild required due to significant changes")
            return False
        
        if not changes['files_changed']:
            print("✅ No file changes detected - build can be skipped!")
            return True
        
        print(f"🔄 Incremental build needed - {len(changes['files_changed'])} files changed")
        return False
    
    def setup_pyinstaller_cache(self):
        """Set up PyInstaller cache directory for reuse"""
        try:
            # Set PyInstaller cache environment variable
            os.environ['PYINSTALLER_CACHE_DIR'] = self.pyinstaller_cache_dir
            print(f"📁 Using PyInstaller cache: {self.pyinstaller_cache_dir}")
            return True
        except Exception as e:
            print(f"⚠️  Warning: Could not set PyInstaller cache: {e}")
            return False
    
    def clear_cache(self):
        """Clear all build caches"""
        try:
            if os.path.exists(self.cache_dir):
                shutil.rmtree(self.cache_dir)
                print("🧹 Build cache cleared")
            self.ensure_cache_directory()
            return True
        except Exception as e:
            print(f"❌ Error clearing cache: {e}")
            return False
    
    def get_cache_info(self):
        """Get information about current cache"""
        info = {
            'cache_dir': self.cache_dir,
            'exists': os.path.exists(self.cache_dir),
            'hash_cache_exists': os.path.exists(self.hash_cache_file),
            'build_cache_exists': os.path.exists(self.build_cache_file),
            'pyinstaller_cache_exists': os.path.exists(self.pyinstaller_cache_dir)
        }
        
        if info['exists']:
            try:
                cache_size = sum(
                    os.path.getsize(os.path.join(dirpath, filename))
                    for dirpath, dirnames, filenames in os.walk(self.cache_dir)
                    for filename in filenames
                )
                info['cache_size_mb'] = round(cache_size / (1024 * 1024), 2)
            except Exception:
                info['cache_size_mb'] = 0
        
        return info

# ============================================================================
# POST-BUILD SMOKE TESTING SYSTEM
# ============================================================================

class SmokeTestManager:
    """Manages post-build smoke testing of executables"""
    
    def __init__(self, test_timeout=30):
        self.test_timeout = test_timeout
        self.test_results = {}
    
    def run_smoke_test(self, exe_path, enable_gui_test=False):
        """Run comprehensive smoke test on built executable"""
        try:
            print("🧪 Running Post-Build Smoke Tests")
            print("=" * 40)
            
            if not os.path.exists(exe_path):
                print(f"❌ Executable not found: {exe_path}")
                return False
            
            print(f"🎯 Testing executable: {os.path.basename(exe_path)}")
            
            # Test 1: Basic launch test
            if not self._test_basic_launch(exe_path):
                return False
            
            # Test 2: Self-test mode (if supported)
            if not self._test_self_test_mode(exe_path):
                return False
            
            # Test 3: Import validation
            if not self._test_import_validation(exe_path):
                return False
            
            # Test 4: Resource loading test
            if not self._test_resource_loading(exe_path):
                return False
            
            # Test 5: GUI smoke test (if enabled)
            if enable_gui_test:
                if not self._test_gui_launch(exe_path):
                    return False
            
            print("✅ All smoke tests passed!")
            self._generate_test_report()
            return True
            
        except Exception as e:
            print(f"❌ Smoke test error: {e}")
            return False
    
    def _test_basic_launch(self, exe_path):
        """Test basic executable launch"""
        try:
            print("   🔍 Test 1: Basic launch test...")
            
            # Try to launch with --help to test basic functionality
            process = subprocess.run(
                [exe_path, "--help"], 
                capture_output=True, 
                text=True, 
                timeout=self.test_timeout
            )
            
            if process.returncode == 0:
                print("   ✅ Basic launch: PASSED")
                self.test_results['basic_launch'] = 'PASSED'
                return True
            else:
                print(f"   ❌ Basic launch: FAILED (exit code: {process.returncode})")
                print(f"   📝 Error: {process.stderr[:200]}...")
                self.test_results['basic_launch'] = f'FAILED ({process.returncode})'
                return False
                
        except subprocess.TimeoutExpired:
            print(f"   ⏰ Basic launch: TIMEOUT (>{self.test_timeout}s)")
            self.test_results['basic_launch'] = 'TIMEOUT'
            return False
        except Exception as e:
            print(f"   ❌ Basic launch: ERROR ({e})")
            self.test_results['basic_launch'] = f'ERROR ({e})'
            return False
    
    def _test_self_test_mode(self, exe_path):
        """Test self-test mode if supported"""
        try:
            print("   🔍 Test 2: Self-test mode...")
            
            # Try --self-test flag
            process = subprocess.run(
                [exe_path, "--self-test"], 
                capture_output=True, 
                text=True, 
                timeout=self.test_timeout
            )
            
            # Self-test might not be implemented, so we accept both success and "unknown command"
            if process.returncode == 0:
                print("   ✅ Self-test mode: PASSED")
                self.test_results['self_test'] = 'PASSED'
            elif "unknown command" in process.stderr.lower() or "unrecognized" in process.stderr.lower():
                print("   ⚠️  Self-test mode: NOT IMPLEMENTED (acceptable)")
                self.test_results['self_test'] = 'NOT_IMPLEMENTED'
            else:
                print(f"   ❌ Self-test mode: FAILED (exit code: {process.returncode})")
                self.test_results['self_test'] = f'FAILED ({process.returncode})'
                return False
            
            return True
            
        except subprocess.TimeoutExpired:
            print(f"   ⏰ Self-test mode: TIMEOUT (>{self.test_timeout}s)")
            self.test_results['self_test'] = 'TIMEOUT'
            return False
        except Exception as e:
            print(f"   ❌ Self-test mode: ERROR ({e})")
            self.test_results['self_test'] = f'ERROR ({e})'
            return False
    
    def _test_import_validation(self, exe_path):
        """Test import validation by checking for common import errors"""
        try:
            print("   🔍 Test 3: Import validation...")
            
            # Try to run with a simple command that would trigger imports
            process = subprocess.run(
                [exe_path, "--version"], 
                capture_output=True, 
                text=True, 
                timeout=self.test_timeout
            )
            
            # Look for import errors in stderr
            import_errors = [
                'ModuleNotFoundError', 'ImportError', 'DLL load failed',
                'No module named', 'cannot import', 'failed to import'
            ]
            
            stderr_lower = process.stderr.lower()
            for error in import_errors:
                if error.lower() in stderr_lower:
                    print(f"   ❌ Import validation: FAILED - {error} detected")
                    self.test_results['import_validation'] = f'FAILED ({error})'
                    return False
            
            print("   ✅ Import validation: PASSED")
            self.test_results['import_validation'] = 'PASSED'
            return True
            
        except subprocess.TimeoutExpired:
            print(f"   ⏰ Import validation: TIMEOUT (>{self.test_timeout}s)")
            self.test_results['import_validation'] = 'TIMEOUT'
            return False
        except Exception as e:
            print(f"   ❌ Import validation: ERROR ({e})")
            self.test_results['import_validation'] = f'ERROR ({e})'
            return False
    
    def _test_resource_loading(self, exe_path):
        """Test resource loading capabilities"""
        try:
            print("   🔍 Test 4: Resource loading test...")
            
            # Launch and immediately terminate to test resource loading
            process = subprocess.Popen(
                [exe_path], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Give it a moment to initialize
            import time
            time.sleep(2)
            
            # Terminate gracefully
            process.terminate()
            stdout, stderr = process.communicate(timeout=5)
            
            # Check for resource loading errors
            resource_errors = [
                'FileNotFoundError', 'resource not found', 'failed to load',
                'missing resource', 'icon not found', 'image not found'
            ]
            
            stderr_lower = stderr.lower()
            for error in resource_errors:
                if error.lower() in stderr_lower:
                    print(f"   ❌ Resource loading: FAILED - {error} detected")
                    self.test_results['resource_loading'] = f'FAILED ({error})'
                    return False
            
            print("   ✅ Resource loading: PASSED")
            self.test_results['resource_loading'] = 'PASSED'
            return True
            
        except Exception as e:
            print(f"   ❌ Resource loading: ERROR ({e})")
            self.test_results['resource_loading'] = f'ERROR ({e})'
            return False
    
    def _test_gui_launch(self, exe_path):
        """Test GUI application launch (optional)"""
        try:
            print("   🔍 Test 5: GUI launch test...")
            
            # Launch GUI app and immediately close
            process = subprocess.Popen(
                [exe_path], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Give GUI time to initialize
            import time
            time.sleep(5)
            
            # Check if still running (good sign for GUI)
            if process.poll() is None:
                print("   ✅ GUI launch: PASSED (GUI initialized successfully)")
                process.terminate()
                process.wait(timeout=5)
                self.test_results['gui_launch'] = 'PASSED'
                return True
            else:
                stdout, stderr = process.communicate()
                print(f"   ❌ GUI launch: FAILED (premature exit: {process.returncode})")
                if stderr:
                    print(f"   📝 Error: {stderr[:200]}...")
                self.test_results['gui_launch'] = f'FAILED ({process.returncode})'
                return False
            
        except Exception as e:
            print(f"   ❌ GUI launch: ERROR ({e})")
            self.test_results['gui_launch'] = f'ERROR ({e})'
            return False
    
    def _generate_test_report(self):
        """Generate smoke test report"""
        try:
            print("\n📊 Smoke Test Report:")
            print("-" * 25)
            
            for test_name, result in self.test_results.items():
                status_icon = "✅" if result == "PASSED" else "⚠️" if "NOT_IMPLEMENTED" in result else "❌"
                test_display = test_name.replace('_', ' ').title()
                print(f"   {status_icon} {test_display}: {result}")
            
            # Calculate pass rate
            passed_tests = sum(1 for result in self.test_results.values() if result == "PASSED")
            total_tests = len(self.test_results)
            pass_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            print(f"\n📈 Pass Rate: {passed_tests}/{total_tests} ({pass_rate:.1f}%)")
            
            if pass_rate >= 80:
                print("🎉 Executable ready for distribution!")
            else:
                print("⚠️  Consider investigating failed tests before distribution")
                
        except Exception as e:
            print(f"⚠️  Warning: Could not generate test report: {e}")

# ============================================================================
# MSIX APP INSTALLER INTEGRATION
# ============================================================================

class MSIXAppInstallerManager:
    """Manages MSIX App Installer (.appinstaller) generation and deployment"""
    
    def __init__(self):
        self.default_config = {
            'update_uri': None,
            'min_version': '1.0.0.0',
            'release_channel': 'stable',
            'auto_update': True,
            'update_check_hours': 24
        }
    
    def generate_app_installer(self, msix_path, config=None):
        """Generate .appinstaller file for MSIX auto-updates"""
        try:
            if not config:
                config = self.default_config.copy()
            
            print("📦 Generating MSIX App Installer")
            print("=" * 35)
            
            # Validate MSIX file exists
            if not os.path.exists(msix_path):
                print(f"❌ MSIX file not found: {msix_path}")
                return False
            
            # Extract app info from MSIX
            app_info = self._extract_msix_info(msix_path)
            if not app_info:
                return False
            
            # Generate .appinstaller content
            appinstaller_content = self._generate_appinstaller_xml(msix_path, app_info, config)
            
            # Write .appinstaller file
            appinstaller_path = msix_path.replace('.msix', '.appinstaller')
            with open(appinstaller_path, 'w', encoding='utf-8') as f:
                f.write(appinstaller_content)
            
            print(f"✅ App Installer created: {os.path.basename(appinstaller_path)}")
            print(f"📁 Location: {appinstaller_path}")
            
            # Show deployment instructions
            self._show_deployment_instructions(appinstaller_path, config)
            
            return True
            
        except Exception as e:
            print(f"❌ Error generating App Installer: {e}")
            return False
    
    def _extract_msix_info(self, msix_path):
        """Extract app information from MSIX package"""
        try:
            print(f"🔍 Extracting info from: {os.path.basename(msix_path)}")
            
            # For now, use basic info - could be enhanced to read AppxManifest.xml
            file_size = os.path.getsize(msix_path)
            file_hash = self._calculate_file_hash(msix_path)
            
            # Extract basic info from filename (could be enhanced)
            base_name = os.path.splitext(os.path.basename(msix_path))[0]
            
            app_info = {
                'name': base_name,
                'version': '1.0.0.0',  # Default - could extract from manifest
                'size': file_size,
                'hash': file_hash,
                'filename': os.path.basename(msix_path)
            }
            
            print(f"   📱 App: {app_info['name']}")
            print(f"   🔢 Version: {app_info['version']}")
            print(f"   📦 Size: {file_size / (1024*1024):.1f} MB")
            
            return app_info
            
        except Exception as e:
            print(f"❌ Error extracting MSIX info: {e}")
            return None
    
    def _calculate_file_hash(self, file_path):
        """Calculate SHA256 hash of file"""
        try:
            hasher = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception:
            return "unknown"
    
    def _generate_appinstaller_xml(self, msix_path, app_info, config):
        """Generate .appinstaller XML content"""
        update_uri = config.get('update_uri', 'https://example.com/updates/')
        min_version = config.get('min_version', '1.0.0.0')
        channel = config.get('release_channel', 'stable')
        auto_update = config.get('auto_update', True)
        check_hours = config.get('update_check_hours', 24)
        
        # Ensure update_uri ends with /
        if update_uri and not update_uri.endswith('/'):
            update_uri += '/'
        
        xml_content = f'''<?xml version="1.0" encoding="utf-8"?>
<AppInstaller 
    xmlns="http://schemas.microsoft.com/appx/appinstaller/2018"
    Version="{app_info['version']}"
    Uri="{update_uri}{app_info['filename'].replace('.msix', '.appinstaller')}">

    <MainPackage 
        Name="{app_info['name']}"
        Publisher="CN=Developer"
        Version="{app_info['version']}"
        ProcessorArchitecture="x64"
        Uri="{update_uri}{app_info['filename']}" />

    <UpdateSettings>
        <OnLaunch 
            HoursBetweenUpdateChecks="{check_hours}"
            ShowPrompt="false"
            UpdateBlocksActivation="false" />
        <AutomaticBackgroundTask />
    </UpdateSettings>

    <!-- Release Channel: {channel} -->
    <!-- Minimum Version: {min_version} -->
    <!-- Auto Update: {auto_update} -->
    <!-- File Hash: {app_info['hash'][:16]}... -->
    
</AppInstaller>'''
        
        return xml_content
    
    def _show_deployment_instructions(self, appinstaller_path, config):
        """Show deployment instructions"""
        print("\n🚀 Deployment Instructions:")
        print("-" * 30)
        
        update_uri = config.get('update_uri')
        if update_uri:
            print(f"1. Upload both files to your web server:")
            print(f"   • {os.path.basename(appinstaller_path)}")
            print(f"   • {os.path.basename(appinstaller_path.replace('.appinstaller', '.msix'))}")
            print(f"   📍 Location: {update_uri}")
            print()
            print(f"2. Share this installation link:")
            print(f"   🔗 {update_uri}{os.path.basename(appinstaller_path)}")
            print()
            print("3. Users can install by:")
            print("   • Clicking the link in their browser")
            print("   • Windows will automatically handle updates")
        else:
            print("⚠️  Update URI not configured - set with --msix-update-uri")
        
        print()
        print("💡 Benefits:")
        print("   • Automatic background updates")
        print("   • No user intervention required")
        print("   • Centralized update management")

# ============================================================================
# GITHUB CONNECTION SYSTEM
# ============================================================================

class GitHubConnectionManager:
    """Manages GitHub integration for testing and deployment"""
    
    def __init__(self):
        self.github_config = {}
        self.api_base = "https://api.github.com"
    
    def setup_github_connection(self, repo_url, token=None, branch='main'):
        """Set up GitHub connection for testing purposes"""
        try:
            print("🐙 Setting up GitHub Connection")
            print("=" * 35)
            
            # Parse repository URL
            repo_info = self._parse_repo_url(repo_url)
            if not repo_info:
                return False
            
            self.github_config = {
                'repo_url': repo_url,
                'owner': repo_info['owner'],
                'repo': repo_info['repo'],
                'branch': branch,
                'token': token,
                'connected': True
            }
            
            # Test connection
            if not self._test_github_connection():
                return False
            
            print(f"✅ GitHub connection established!")
            print(f"   📂 Repository: {repo_info['owner']}/{repo_info['repo']}")
            print(f"   🌿 Branch: {branch}")
            print(f"   🔑 Token: {'Configured' if token else 'Not configured'}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error setting up GitHub connection: {e}")
            return False
    
    def _parse_repo_url(self, repo_url):
        """Parse GitHub repository URL"""
        try:
            import re
            
            # Handle various GitHub URL formats
            patterns = [
                r'https://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$',
                r'git@github\.com:([^/]+)/([^/]+?)(?:\.git)?$',
                r'([^/]+)/([^/]+)$'  # Simple owner/repo format
            ]
            
            for pattern in patterns:
                match = re.match(pattern, repo_url.strip())
                if match:
                    owner, repo = match.groups()
                    return {
                        'owner': owner,
                        'repo': repo.replace('.git', '')
                    }
            
            print(f"❌ Invalid GitHub repository URL: {repo_url}")
            return None
            
        except Exception as e:
            print(f"❌ Error parsing repository URL: {e}")
            return None
    
    def _test_github_connection(self):
        """Test GitHub API connection"""
        try:
            print("   🔍 Testing GitHub API connection...")
            
            import urllib.request
            import json
            
            # Test with repository info endpoint
            url = f"{self.api_base}/repos/{self.github_config['owner']}/{self.github_config['repo']}"
            
            # Create request with token if provided
            req = urllib.request.Request(url)
            if self.github_config.get('token'):
                req.add_header('Authorization', f"token {self.github_config['token']}")
            req.add_header('User-Agent', 'PDFUtility-BuildSystem')
            
            # Make request
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    print(f"   ✅ Repository found: {data.get('full_name', 'Unknown')}")
                    return True
                else:
                    print(f"   ❌ GitHub API error: HTTP {response.status}")
                    return False
                    
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(f"   ❌ Repository not found (private repos need token)")
            elif e.code == 403:
                print(f"   ❌ Access denied (check token permissions)")
            else:
                print(f"   ❌ GitHub API error: HTTP {e.code}")
            return False
        except Exception as e:
            print(f"   ❌ Connection test failed: {e}")
            return False
    
    def create_test_release(self, exe_path, version_tag=None):
        """Create a test release on GitHub for testing purposes"""
        try:
            if not self.github_config.get('connected'):
                print("❌ GitHub connection not established")
                return False
            
            print("🚀 Creating GitHub Test Release")
            print("=" * 35)
            
            if not version_tag:
                from datetime import datetime
                version_tag = f"test-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
            # This is a placeholder - would need GitHub API integration
            print(f"📦 Test release: {version_tag}")
            print(f"📁 Executable: {os.path.basename(exe_path)}")
            print(f"🔗 Repository: {self.github_config['owner']}/{self.github_config['repo']}")
            
            print("⚠️  Note: Full GitHub release creation requires API token")
            print("💡 This feature can be extended with GitHub Actions integration")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating test release: {e}")
            return False
    
    def get_github_info(self):
        """Get current GitHub connection information"""
        if self.github_config.get('connected'):
            return self.github_config.copy()
        return None

# ============================================================================
# WINGET MANIFEST GENERATOR
# ============================================================================

class WingetManifestManager:
    """Generate Windows Package Manager (Winget) manifest files from build configuration"""
    
    def __init__(self):
        self.manifest_config = {
            'version': '1.0.0',
            'bundle_type': 'onefile',  # Default bundle type
            'publisher': None,
            'package_identifier': None,
            'package_name': None,
            'license': 'Unknown',
            'description': None,
            'homepage': None,
            'download_url': None,
            'architecture': 'x64',
            'installer_type': 'exe',
            'scope': 'user'
        }
    
    def set_bundle_type(self, bundle_type):
        """Set the bundle type for the manifest"""
        valid_types = ['onefile', 'onedir', 'portable']
        if bundle_type.lower() in valid_types:
            self.manifest_config['bundle_type'] = bundle_type.lower()
            print(f"📦 Bundle type set to: {bundle_type.lower()}")
        else:
            print(f"⚠️  Invalid bundle type: {bundle_type}")
            print(f"💡 Valid options: {', '.join(valid_types)}")
    
    def detect_config_from_build(self):
        """Auto-detect configuration from current build setup"""
        try:
            core = BuildToolCore()
            
            # Get stored configuration
            config = core.memory.get_config()
            
            # Get basic info from build configuration
            build_name = config.get('name') or getattr(core, 'build_name', None)
            if build_name and build_name != 'Unknown':
                self.manifest_config['package_name'] = build_name
                # Create package identifier from name
                clean_name = re.sub(r'[^a-zA-Z0-9]', '', build_name)
                self.manifest_config['package_identifier'] = f"Unknown.{clean_name}"
            
            # Get description if available
            description = config.get('description') or getattr(core, 'build_description', None)
            if description:
                self.manifest_config['description'] = description
            
            # Detect architecture
            arch = platform.machine().lower()
            if 'arm' in arch:
                self.manifest_config['architecture'] = 'arm64'
            elif '64' in arch:
                self.manifest_config['architecture'] = 'x64'
            else:
                self.manifest_config['architecture'] = 'x86'
            
            print("🔍 Auto-detected build configuration:")
            print(f"   📦 Package: {self.manifest_config['package_name']}")
            print(f"   🏗️  Architecture: {self.manifest_config['architecture']}")
            if self.manifest_config['description']:
                desc = self.manifest_config['description']
                print(f"   📝 Description: {desc[:50]}{'...' if len(desc) > 50 else ''}")
                
        except Exception as e:
            print(f"⚠️  Auto-detection failed: {e}")
            import traceback
            traceback.print_exc()
    
    def generate_manifest(self, output_path=None):
        """Generate Winget manifest YAML files"""
        try:
            print("📄 Generating Winget Manifest")
            print("=" * 35)
            
            # Auto-detect if no configuration provided
            if not self.manifest_config.get('package_name'):
                self.detect_config_from_build()
            
            # Set default output path
            if not output_path:
                output_path = f"{self.manifest_config['package_name'] or 'Package'}.yaml"
            
            # Generate manifest content based on bundle type
            manifest_content = self._generate_manifest_content()
            
            # Write manifest file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(manifest_content)
            
            print(f"✅ Manifest generated: {output_path}")
            print(f"📦 Bundle type: {self.manifest_config['bundle_type']}")
            
            # Generate instructions
            self._generate_deployment_instructions(output_path)
            
            return True
            
        except Exception as e:
            print(f"❌ Error generating manifest: {e}")
            return False
    
    def _generate_manifest_content(self):
        """Generate the actual YAML content for the manifest"""
        
        # Package identifier and version
        package_id = self.manifest_config.get('package_identifier', 'Unknown.Package')
        package_name = self.manifest_config.get('package_name', 'Unknown Package')
        version = self.manifest_config.get('version', '1.0.0')
        
        # Base manifest structure
        manifest = f"""# Winget Manifest - Generated by BuildSystem
# Package: {self.manifest_config.get('package_name', 'Unknown')}
# Bundle Type: {self.manifest_config['bundle_type']}
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

PackageIdentifier: {package_id}
PackageVersion: {version}
PackageName: {package_name}
Publisher: {self.manifest_config.get('publisher', 'Unknown Publisher')}
License: {self.manifest_config.get('license', 'Unknown')}
ShortDescription: {self.manifest_config.get('description', 'Application built with BuildSystem')}
PackageUrl: {self.manifest_config.get('homepage', 'https://github.com/user/repo')}
"""
        
        # Add installer section based on bundle type
        if self.manifest_config['bundle_type'] == 'portable':
            app_name = self.manifest_config.get('package_name') or 'app'
            manifest += f"""
Installers:
- Architecture: {self.manifest_config['architecture']}
  InstallerType: portable
  InstallerUrl: {self.manifest_config.get('download_url', 'https://github.com/user/repo/releases/download/v{version}/app.exe')}
  InstallerSha256: # TODO: Add SHA256 hash of the installer
  PortableCommandAlias: {app_name.lower().replace(' ', '') if app_name else 'app'}
"""
        elif self.manifest_config['bundle_type'] == 'onedir':
            manifest += f"""
Installers:
- Architecture: {self.manifest_config['architecture']}
  InstallerType: zip
  InstallerUrl: {self.manifest_config.get('download_url', 'https://github.com/user/repo/releases/download/v{version}/app-onedir.zip')}
  InstallerSha256: # TODO: Add SHA256 hash of the installer
  Scope: {self.manifest_config['scope']}
  InstallModes:
  - interactive
  - silent
"""
        else:  # onefile (default)
            manifest += f"""
Installers:
- Architecture: {self.manifest_config['architecture']}
  InstallerType: {self.manifest_config['installer_type']}
  InstallerUrl: {self.manifest_config.get('download_url', 'https://github.com/user/repo/releases/download/v{version}/app.exe')}
  InstallerSha256: # TODO: Add SHA256 hash of the installer
  Scope: {self.manifest_config['scope']}
  InstallModes:
  - interactive
  - silent
  InstallerSwitches:
    Silent: /S
    SilentWithProgress: /S
"""
        
        manifest += f"""
ManifestType: singleton
ManifestVersion: 1.6.0
"""
        
        return manifest
    
    def _generate_deployment_instructions(self, manifest_path):
        """Generate instructions for submitting to Winget"""
        # Get package info safely
        package_id = self.manifest_config.get('package_identifier', 'Unknown.Package')
        package_name = self.manifest_config.get('package_name') or 'Package'
        version = self.manifest_config.get('version', '1.0.0')
        
        # Extract publisher from package ID safely
        publisher = package_id.split('.')[0] if package_id and '.' in package_id else 'Unknown'
        # Clean package name for folder structure
        clean_package_name = package_name.replace(' ', '') if package_name else 'Package'
        
        instructions = f"""
🚀 Winget Deployment Instructions
=================================

Your manifest has been generated: {manifest_path}

Next Steps for Winget Submission:

1. 📋 Review and Complete Manifest:
   • Add actual download URLs for your releases
   • Calculate and add SHA256 hashes for installers
   • Verify publisher and license information
   • Test the manifest locally

2. 🧪 Test Locally:
   winget install --manifest {manifest_path}

3. 🔧 Fork Microsoft's winget-pkgs repository:
   https://github.com/microsoft/winget-pkgs

4. 📁 Create folder structure:
   manifests/{publisher}/{clean_package_name}/{version}/

5. 📤 Submit Pull Request:
   • Add your manifest to the appropriate folder
   • Follow naming conventions
   • Include clear PR description

💡 Bundle Type Considerations:
   • onefile: Single executable, easiest distribution
   • onedir: Folder-based distribution with dependencies
   • portable: No installation required, runs directly

🔗 Useful Links:
   • Winget Manifest Schema: https://aka.ms/winget-manifest
   • Submission Guide: https://docs.microsoft.com/en-us/windows/package-manager/package/
   • Manifest Validator: winget validate --manifest {manifest_path}
"""
        
        print(instructions)
    
    def set_config(self, key, value):
        """Set a configuration value for the manifest"""
        if key in self.manifest_config:
            self.manifest_config[key] = value
            print(f"✅ Set {key}: {value}")
        else:
            print(f"⚠️  Unknown configuration key: {key}")
    
    def show_config(self):
        """Display current manifest configuration"""
        print("📋 Current Winget Manifest Configuration")
        print("=" * 45)
        
        for key, value in self.manifest_config.items():
            print(f"   {key}: {value}")
        
        print(f"\n💡 Bundle type affects installer configuration")
        print(f"   Current: {self.manifest_config['bundle_type']}")

# ============================================================================
# DESCRIPTION MANAGEMENT SYSTEM
# ============================================================================

def handle_description_command():
    """Handle description command with create/import functionality"""
    try:
        core = BuildToolCore()
        
        # Parse description arguments
        description_text = None
        import_file = None
        
        # Look for --description arguments
        for i, arg in enumerate(sys.argv):
            if arg == '--description':
                # Check if next argument is --import-from
                if i + 1 < len(sys.argv) and sys.argv[i + 1] == '--import-from':
                    if i + 2 < len(sys.argv):
                        import_file = sys.argv[i + 2]
                # Check if next argument is a description string
                elif i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith('--'):
                    description_text = sys.argv[i + 1]
                break
        
        if import_file:
            return import_description_from_file(core, import_file)
        elif description_text:
            return set_description_text(core, description_text)
        else:
            return show_current_description(core)
            
    except Exception as e:
        print(f"❌ Error handling description command: {e}")
        return False

def import_description_from_file(core, file_path):
    """Import description from various file formats"""
    try:
        if not os.path.exists(file_path):
            print(f"❌ Description file not found: {file_path}")
            return False
        
        print(f"📖 Importing description from: {file_path}")
        
        file_ext = os.path.splitext(file_path)[1].lower()
        description_text = ""
        
        if file_ext == '.json':
            # JSON format - look for description field
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    description_text = data.get('description', data.get('desc', ''))
                elif isinstance(data, str):
                    description_text = data
                else:
                    print("❌ JSON file must contain description field or be a string")
                    return False
                    
        elif file_ext in ['.txt', '.md', '.rst']:
            # Plain text formats
            with open(file_path, 'r', encoding='utf-8') as f:
                description_text = f.read().strip()
                
        elif file_ext == '.xml':
            # XML format - look for description element
            try:
                import xml.etree.ElementTree as ET
                tree = ET.parse(file_path)
                root = tree.getroot()
                
                # Look for description element
                desc_element = root.find('.//description')
                if desc_element is not None:
                    description_text = desc_element.text or ""
                else:
                    # Try common variations
                    for tag in ['desc', 'summary', 'comment']:
                        element = root.find(f'.//{tag}')
                        if element is not None:
                            description_text = element.text or ""
                            break
                            
                if not description_text:
                    print("❌ No description element found in XML file")
                    return False
                    
            except Exception as e:
                print(f"❌ Error parsing XML file: {e}")
                return False
                
        else:
            print(f"❌ Unsupported file format: {file_ext}")
            print("   Supported formats: .json, .txt, .md, .rst, .xml")
            return False
        
        if not description_text.strip():
            print("❌ Empty description found in file")
            return False
        
        # Store description in config
        config = core.memory.get_config()
        config['description'] = description_text.strip()
        core.memory.store_config(config)
        
        print("✅ Description imported successfully!")
        print(f"📝 Description ({len(description_text)} chars):")
        print(f"   {description_text[:100]}{'...' if len(description_text) > 100 else ''}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error importing description: {e}")
        return False

def set_description_text(core, description_text):
    """Set description text directly"""
    try:
        if not description_text.strip():
            print("❌ Empty description text provided")
            return False
        
        config = core.memory.get_config()
        config['description'] = description_text.strip()
        core.memory.store_config(config)
        
        print("✅ Description set successfully!")
        print(f"📝 Description ({len(description_text)} chars):")
        print(f"   {description_text}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting description: {e}")
        return False

def show_current_description(core):
    """Show current description"""
    try:
        config = core.memory.get_config()
        description = config.get('description', '')
        
        if description:
            print("📝 Current Description:")
            print(f"   {description}")
            print(f"📊 Length: {len(description)} characters")
        else:
            print("📝 No description set")
            print("💡 Usage:")
            print("   py build_cli.py --description \"Your description here\"")
            print("   py build_cli.py --description --import-from description.txt")
        
        return True
        
    except Exception as e:
        print(f"❌ Error showing description: {e}")
        return False

def handle_force_clean_command():
    """Handle force clean build command"""
    try:
        print("🧹 Force clean build requested")
        print("=" * 35)
        
        # Clear incremental build cache
        incremental_manager = IncrementalBuildManager()
        incremental_manager.clear_cache()
        
        # Clear wheelhouse cache
        try:
            wheelhouse_cache = WheelhouseCache()
            if os.path.exists(wheelhouse_cache.cache_dir):
                shutil.rmtree(wheelhouse_cache.cache_dir)
                print(f"🧹 Cleared wheelhouse cache: {wheelhouse_cache.cache_dir}")
        except Exception as e:
            print(f"⚠️  Warning: Could not clear wheelhouse cache: {e}")
        
        # Clear PyInstaller build artifacts
        build_dir = os.path.join(os.getcwd(), 'build')
        dist_dir = os.path.join(os.getcwd(), 'dist')
        
        for directory in [build_dir, dist_dir]:
            if os.path.exists(directory):
                try:
                    shutil.rmtree(directory)
                    print(f"🧹 Cleared: {directory}")
                except Exception as e:
                    print(f"⚠️  Warning: Could not clear {directory}: {e}")
        
        print("✅ Clean completed - next build will be full rebuild")
        print("💡 Run --setup-wheelhouse to recreate wheel cache")
        return True
        
    except Exception as e:
        print(f"❌ Error performing clean: {e}")
        return False

def handle_cache_info_command():
    """Handle cache info command"""
    try:
        incremental_manager = IncrementalBuildManager()
        cache_info = incremental_manager.get_cache_info()
        
        print("📊 Build Cache Information")
        print("=" * 30)
        print(f"Cache Directory: {cache_info['cache_dir']}")
        print(f"Cache Exists: {'✅ Yes' if cache_info['exists'] else '❌ No'}")
        print(f"Hash Cache: {'✅ Yes' if cache_info['hash_cache_exists'] else '❌ No'}")
        print(f"Build Cache: {'✅ Yes' if cache_info['build_cache_exists'] else '❌ No'}")
        print(f"PyInstaller Cache: {'✅ Yes' if cache_info['pyinstaller_cache_exists'] else '❌ No'}")
        
        if cache_info.get('cache_size_mb', 0) > 0:
            print(f"Total Cache Size: {cache_info['cache_size_mb']} MB")
        
        print()
        print("💡 Cache Management Commands:")
        print("   py build_cli.py --force-clean    Clear all caches")
        print("   py build_cli.py --start build    Use incremental build")
        
        return True
        
    except Exception as e:
        print(f"❌ Error getting cache info: {e}")
        return False

def handle_smoke_test_command():
    """Handle smoke test command"""
    try:
        # Find the most recent executable
        dist_dir = os.path.join(os.getcwd(), 'dist')
        if not os.path.exists(dist_dir):
            print("❌ No dist directory found - build an executable first")
            return False
        
        # Find .exe files
        exe_files = [f for f in os.listdir(dist_dir) if f.endswith('.exe')]
        if not exe_files:
            print("❌ No executable files found in dist directory")
            return False
        
        # Use the most recent exe file
        exe_file = max(exe_files, key=lambda f: os.path.getmtime(os.path.join(dist_dir, f)))
        exe_path = os.path.join(dist_dir, exe_file)
        
        # Check for GUI test flag
        enable_gui = '--gui-test' in sys.argv
        
        # Run smoke test
        smoke_tester = SmokeTestManager()
        return smoke_tester.run_smoke_test(exe_path, enable_gui_test=enable_gui)
        
    except Exception as e:
        print(f"❌ Error running smoke test: {e}")
        return False

def handle_msix_appinstaller_command():
    """Handle MSIX App Installer generation"""
    try:
        # Parse arguments
        update_uri = None
        min_version = '1.0.0.0'
        release_channel = 'stable'
        
        for i, arg in enumerate(sys.argv):
            if arg == '--msix-update-uri' and i + 1 < len(sys.argv):
                update_uri = sys.argv[i + 1]
            elif arg == '--msix-min-version' and i + 1 < len(sys.argv):
                min_version = sys.argv[i + 1]
            elif arg == '--release-channel' and i + 1 < len(sys.argv):
                release_channel = sys.argv[i + 1]
        
        # Find MSIX file
        msix_files = glob.glob('*.msix')
        if not msix_files:
            print("❌ No MSIX files found in current directory")
            print("💡 Run --start package first to create MSIX package")
            return False
        
        # Use the most recent MSIX file
        msix_file = max(msix_files, key=os.path.getmtime)
        
        # Configure App Installer
        config = {
            'update_uri': update_uri,
            'min_version': min_version,
            'release_channel': release_channel,
            'auto_update': True,
            'update_check_hours': 24
        }
        
        # Generate App Installer
        installer_manager = MSIXAppInstallerManager()
        return installer_manager.generate_app_installer(msix_file, config)
        
    except Exception as e:
        print(f"❌ Error generating App Installer: {e}")
        return False

def handle_github_connect_command():
    """Handle GitHub connection setup"""
    try:
        # Parse arguments
        repo_url = None
        token = None
        branch = 'main'
        
        for i, arg in enumerate(sys.argv):
            if arg == '--github-repo' and i + 1 < len(sys.argv):
                repo_url = sys.argv[i + 1]
            elif arg == '--github-token' and i + 1 < len(sys.argv):
                token = sys.argv[i + 1]
            elif arg == '--github-branch' and i + 1 < len(sys.argv):
                branch = sys.argv[i + 1]
        
        if not repo_url:
            print("❌ GitHub repository URL required")
            print("💡 Usage: --github-connect --github-repo owner/repo")
            return False
        
        # Set up GitHub connection
        github_manager = GitHubConnectionManager()
        return github_manager.setup_github_connection(repo_url, token, branch)
        
    except Exception as e:
        print(f"❌ Error connecting to GitHub: {e}")
        return False

def handle_winget_manifest_command():
    """Handle Winget manifest generation"""
    try:
        # Parse arguments
        bundle_type = 'onefile'  # Default bundle type
        output_path = None
        publisher = None
        homepage = None
        license = None
        download_url = None
        
        # Check for --default flag to set default bundle type
        if '--default' in sys.argv:
            try:
                default_idx = sys.argv.index('--default')
                if default_idx + 1 < len(sys.argv):
                    next_arg = sys.argv[default_idx + 1]
                    if next_arg in ['onefile', 'onedir', 'portable']:
                        bundle_type = next_arg
                        print(f"🔧 Setting default bundle type to: {bundle_type}")
            except (ValueError, IndexError):
                pass
        
        # Parse specific arguments
        for i, arg in enumerate(sys.argv):
            if arg == '--bundle' and i + 1 < len(sys.argv):
                potential_type = sys.argv[i + 1]
                if potential_type in ['onefile', 'onedir', 'portable']:
                    bundle_type = potential_type
                else:
                    print(f"⚠️  Invalid bundle type: {potential_type}")
                    print("💡 Valid options: onefile, onedir, portable")
                    
            elif arg == '--winget-output' and i + 1 < len(sys.argv):
                output_path = sys.argv[i + 1]
            elif arg == '--winget-publisher' and i + 1 < len(sys.argv):
                publisher = sys.argv[i + 1]
            elif arg == '--winget-homepage' and i + 1 < len(sys.argv):
                homepage = sys.argv[i + 1]
            elif arg == '--winget-license' and i + 1 < len(sys.argv):
                license = sys.argv[i + 1]
            elif arg == '--winget-download-url' and i + 1 < len(sys.argv):
                download_url = sys.argv[i + 1]
        
        # Create and configure Winget manager
        winget_manager = WingetManifestManager()
        winget_manager.set_bundle_type(bundle_type)
        
        # Set additional configuration if provided
        if publisher:
            winget_manager.set_config('publisher', publisher)
        if homepage:
            winget_manager.set_config('homepage', homepage)
        if license:
            winget_manager.set_config('license', license)
        if download_url:
            winget_manager.set_config('download_url', download_url)
        
        # Generate manifest
        return winget_manager.generate_manifest(output_path)
        
    except Exception as e:
        print(f"❌ Error generating Winget manifest: {e}")
        return False

def handle_scan_command():
    """Handle scan command"""
    start_time = time.time()
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
            command_history.add_command('scan', None, False, time.time() - start_time)
            return False
        
        print(f"🔍 Scanning for {scan_type} files...")
        
        # Delegate to core for actual scanning
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
        
        results = core.handle_scan_command(scan_type, append_mode, False, scan_directory, contains_filter)
        success = len(results) > 0
        duration = time.time() - start_time
        
        # Add to command history
        command_history.add_command(
            'scan',
            [scan_type] + (['--append'] if append_mode else []) + 
            (['--contains', contains_filter] if contains_filter else []) +
            (['--scan-dir', scan_directory] if scan_directory else []),
            success,
            duration
        )
        
        print(f"✅ Scan completed - found {len(results)} files")
        return success
        
    except ImportError:
        print("❌ Core module required for scanning")
        command_history.add_command('scan', None, False, time.time() - start_time)
        return False
    except Exception as e:
        print(f"❌ Error during scan: {e}")
        command_history.add_command('scan', None, False, time.time() - start_time)
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
            if key == 'hidden_imports':
                print(f"🕵️ {key}: {len(value)} modules detected")
                # Show categorized hidden imports
                if value:
                    standard_lib = []
                    third_party = []
                    
                    # Categorize modules
                    stdlib_modules = {
                        'os', 'sys', 'json', 're', 'datetime', 'pathlib', 'subprocess', 'platform',
                        'collections', 'itertools', 'functools', 'operator', 'math', 'random',
                        'string', 'io', 'contextlib', 'copy', 'pickle', 'sqlite3', 'urllib',
                        'http', 'email', 'xml', 'html', 'csv', 'configparser', 'logging',
                        'argparse', 'shutil', 'tempfile', 'glob', 'fnmatch', 'linecache',
                        'textwrap', 'unicodedata', 'encodings', 'codecs', 'time', 'calendar',
                        'hashlib', 'hmac', 'secrets', 'ssl', 'socket', 'threading', 'multiprocessing',
                        'concurrent', 'asyncio', 'queue', 'sched', 'weakref', 'types', 'abc',
                        'numbers', 'enum', 'decimal', 'fractions', 'statistics', 'array',
                        'bisect', 'heapq', 'zlib', 'gzip', 'bz2', 'lzma', 'zipfile', 'tarfile',
                        'ast', 'ctypes', 'pkgutil', 'traceback', 'importlib'
                    }
                    
                    for module in value:
                        base_module = module.split('.')[0]
                        if base_module in stdlib_modules:
                            standard_lib.append(module)
                        else:
                            third_party.append(module)
                    
                    if standard_lib:
                        print(f"   📚 Standard Library ({len(standard_lib)}):")
                        for module in sorted(standard_lib)[:15]:  # Show first 15
                            print(f"     • {module}")
                        if len(standard_lib) > 15:
                            print(f"     ... and {len(standard_lib) - 15} more")
                    
                    if third_party:
                        print(f"   📦 Third Party ({len(third_party)}):")
                        for module in sorted(third_party)[:15]:  # Show first 15
                            print(f"     • {module}")
                        if len(third_party) > 15:
                            print(f"     ... and {len(third_party) - 15} more")
            elif key == 'hooks_directory':
                print(f"🔧 {key}: {value}")
            elif key == 'runtime_hooks':
                print(f"🎣 {key}: {len(value)} runtime hooks configured")
                for hook in value:
                    print(f"   • {hook}")
            else:
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

def handle_setup_command():
    """Handle --setup command with subcommands"""
    try:
        # Get the setup type from arguments
        setup_type = None
        for i, arg in enumerate(sys.argv):
            if arg == '--setup' and i + 1 < len(sys.argv):
                setup_type = sys.argv[i + 1].lower()
                break
        
        if not setup_type:
            print("🔧 Build System Setup")
            print("=" * 30)
            print("Available setup options:")
            print("  --setup sign         Configure code signing")
            print("  --setup sdk          Setup Windows SDK PATH")
            print("  --setup env          Diagnose Python environment issues")
            print()
            print("Examples:")
            print("  py build_cli.py --setup sign")
            print("  py build_cli.py --setup sdk")
            print("  py build_cli.py --setup env")
            return False
        
        if setup_type == 'sign' or setup_type == 'signing':
            return handle_setup_signing()
        elif setup_type == 'sdk':
            return handle_setup_sdk_command()
        elif setup_type == 'env' or setup_type == 'environment':
            return handle_setup_environment()
        else:
            print(f"❌ Unknown setup type: {setup_type}")
            print("💡 Available: sign, sdk, env")
            return False
        
    except Exception as e:
        print(f"❌ Error in setup command: {e}")
        return False

def handle_doctor_command():
    """Handle --doctor command for comprehensive toolchain verification"""
    try:
        print("🏥 Build Toolchain Doctor")
        print("=" * 50)
        print("Verifying all build tools and dependencies...")
        print()
        
        # Track overall health
        issues_found = []
        warnings_found = []
        
        # 1. Python Environment Check
        print("🐍 Python Environment")
        print("-" * 30)
        
        python_ok = verify_python_environment(issues_found, warnings_found)
        print()
        
        # 2. PIL/Pillow Check
        print("🖼️  PIL/Pillow (Image Processing)")
        print("-" * 35)
        
        pil_ok = verify_pil_availability(issues_found, warnings_found)
        print()
        
        # 3. Windows SDK Tools Check
        print("🛠️  Windows SDK Tools")
        print("-" * 25)
        
        sdk_ok = verify_windows_sdk_tools(issues_found, warnings_found)
        print()
        
        # 4. Code Signing Check
        print("🔐 Code Signing")
        print("-" * 20)
        
        signing_ok = verify_code_signing(issues_found, warnings_found)
        print()
        
        # 5. PyInstaller Check
        print("📦 PyInstaller")
        print("-" * 18)
        
        pyinstaller_ok = verify_pyinstaller(issues_found, warnings_found)
        print()
        
        # 6. VC++ Runtime Check
        print("🔧 Visual C++ Runtime")
        print("-" * 25)
        
        vcruntime_ok = verify_vcruntime(issues_found, warnings_found)
        print()
        
        # 7. Optional Tools Check
        print("🎁 Optional Tools")
        print("-" * 20)
        
        verify_optional_tools(issues_found, warnings_found)
        print()
        
        # Summary
        print("📋 DIAGNOSIS SUMMARY")
        print("=" * 50)
        
        total_checks = 6  # Core components that must work
        working_checks = sum([python_ok, pil_ok, sdk_ok, signing_ok, pyinstaller_ok, vcruntime_ok])
        
        if not issues_found:
            print("✅ ALL SYSTEMS OPERATIONAL")
            print("   Your build toolchain is fully functional!")
            if warnings_found:
                print(f"   {len(warnings_found)} minor warnings (see above)")
        else:
            print(f"⚠️  {len(issues_found)} ISSUES FOUND:")
            for i, issue in enumerate(issues_found, 1):
                print(f"   {i}. {issue}")
                
            print(f"\n📊 System Health: {working_checks}/{total_checks} core components working")
            
            if working_checks >= 4:
                print("💡 Most features should work, but some issues need attention")
            elif working_checks >= 2:
                print("⚠️  Limited functionality - several issues need fixing")
            else:
                print("❌ System needs significant fixes before building")
        
        if warnings_found:
            print(f"\n⚠️  {len(warnings_found)} WARNINGS:")
            for i, warning in enumerate(warnings_found, 1):
                print(f"   {i}. {warning}")
        
        print("\n💡 Next steps:")
        if not issues_found:
            print("   • Ready to build: py build_cli.py --start package")
            print("   • Ready to sign: py build_cli.py --setup sign")
        else:
            print("   • Fix critical issues listed above")
            print("   • Run 'py build_cli.py --doctor' again to verify fixes")
            print("   • Use 'py build_cli.py --setup' commands for automatic fixes")
        
        return len(issues_found) == 0
        
    except Exception as e:
        print(f"❌ Error running doctor command: {e}")
        return False

def verify_python_environment(issues_found, warnings_found):
    """Verify Python environment is working correctly"""
    try:
        # Check current Python version
        version = sys.version_info
        print(f"✅ Current Python: {version.major}.{version.minor}.{version.micro}")
        print(f"   Path: {sys.executable}")
        
        # Check if it's a problematic installation
        if any(prob in sys.executable.lower() for prob in ['platformio', 'msys', 'mingw', 'anaconda']):
            warnings_found.append(f"Python from development environment detected: {sys.executable}")
            print(f"   ⚠️  Development environment Python detected")
        
        # Test py launcher
        try:
            result = subprocess.run(['py', '--version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"✅ Python Launcher: {result.stdout.strip()}")
            else:
                warnings_found.append("Python launcher (py) not working properly")
                print("⚠️  Python launcher not working")
        except:
            warnings_found.append("Python launcher (py) not available")
            print("⚠️  Python launcher not found")
        
        # Check minimum version
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            issues_found.append(f"Python version too old: {version.major}.{version.minor} (need 3.8+)")
            print("❌ Python version too old (need 3.8+)")
            return False
        
        return True
        
    except Exception as e:
        issues_found.append(f"Python environment check failed: {e}")
        print(f"❌ Python check failed: {e}")
        return False

def verify_pil_availability(issues_found, warnings_found):
    """Verify PIL/Pillow is available for image processing"""
    try:
        # Try importing PIL directly
        try:
            from PIL import Image
            print("✅ PIL/Pillow available in current Python")
            return True
        except ImportError:
            print("⚠️  PIL not available in current Python")
        
        # Try finding Python with PIL using our detection
        try:
            core = BuildToolCore()
            pil_python = core.find_python_with_pil()
            
            if pil_python:
                print(f"✅ PIL found with: {pil_python}")
                return True
            else:
                issues_found.append("PIL/Pillow not found in any Python installation")
                print("❌ PIL/Pillow not found")
                print("   💡 Fix: py -m pip install Pillow")
                return False
                
        except Exception as e:
            issues_found.append(f"PIL detection failed: {e}")
            print(f"❌ PIL detection error: {e}")
            return False
    
    except Exception as e:
        issues_found.append(f"PIL verification failed: {e}")
        print(f"❌ PIL check failed: {e}")
        return False

def verify_windows_sdk_tools(issues_found, warnings_found):
    """Verify Windows SDK tools (MakeAppx, SignTool) are available"""
    try:
        core = BuildToolCore()
        sdk_ok = True
        
        # Check MakeAppx
        makeappx_path = core.find_windows_sdk_tool('makeappx.exe')
        if makeappx_path:
            print(f"✅ MakeAppx found: {makeappx_path}")
        else:
            issues_found.append("MakeAppx (Windows SDK) not found - cannot create MSIX packages")
            print("❌ MakeAppx not found")
            sdk_ok = False
        
        # Check SignTool
        signtool_path = core.find_windows_sdk_tool('signtool.exe')
        if signtool_path:
            print(f"✅ SignTool found: {signtool_path}")
        else:
            issues_found.append("SignTool (Windows SDK) not found - cannot sign packages")
            print("❌ SignTool not found")
            sdk_ok = False
        
        if not sdk_ok:
            print("   💡 Fix: Install Windows SDK from")
            print("          https://developer.microsoft.com/windows/downloads/windows-sdk/")
        
        return sdk_ok
        
    except Exception as e:
        issues_found.append(f"Windows SDK check failed: {e}")
        print(f"❌ SDK check failed: {e}")
        return False

def verify_code_signing(issues_found, warnings_found):
    """Verify code signing setup"""
    try:
        core = BuildToolCore()
        cert_info = core.get_certificate_info()
        
        if cert_info:
            cert_path, cert_password = cert_info
            print(f"✅ Certificate found: {cert_path}")
            print(f"   Password: {'Yes' if cert_password else 'No'}")
            
            # Check if certificate file exists
            if not os.path.exists(cert_path):
                issues_found.append(f"Certificate file not found: {cert_path}")
                print("❌ Certificate file missing")
                return False
            
            # Check certificate installation (if possible)
            try:
                if check_certificate_installed(cert_path, cert_password):
                    print("✅ Certificate installed in trusted stores")
                else:
                    warnings_found.append("Certificate not installed in trusted stores - MSIX signing may fail")
                    print("⚠️  Certificate not in trusted stores")
                    print("   💡 Fix: py build_cli.py --setup sign (as Administrator)")
            except:
                warnings_found.append("Could not verify certificate installation status")
                print("⚠️  Certificate installation status unknown")
            
            return True
        else:
            warnings_found.append("No code signing certificate configured")
            print("⚠️  No code signing certificate")
            print("   💡 Optional: py build_cli.py --new cert")
            return True  # Not critical for basic functionality
            
    except Exception as e:
        warnings_found.append(f"Code signing check failed: {e}")
        print(f"⚠️  Code signing check failed: {e}")
        return True  # Not critical

def verify_pyinstaller(issues_found, warnings_found):
    """Verify PyInstaller is available and working"""
    try:
        # Try importing PyInstaller
        try:
            import PyInstaller
            print(f"✅ PyInstaller available: {PyInstaller.__version__}")
        except ImportError:
            issues_found.append("PyInstaller not installed")
            print("❌ PyInstaller not found")
            print("   💡 Fix: py -m pip install pyinstaller")
            return False
        
        # Try running PyInstaller command
        try:
            result = subprocess.run(['pyinstaller', '--version'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"✅ PyInstaller command: {result.stdout.strip()}")
            else:
                warnings_found.append("PyInstaller command not working properly")
                print("⚠️  PyInstaller command issues")
        except:
            warnings_found.append("PyInstaller command not available in PATH")
            print("⚠️  PyInstaller command not in PATH")
        
        return True
        
    except Exception as e:
        issues_found.append(f"PyInstaller check failed: {e}")
        print(f"❌ PyInstaller check failed: {e}")
        return False

def verify_vcruntime(issues_found, warnings_found):
    """Verify Visual C++ Runtime is available"""
    try:
        if platform.system() != "Windows":
            print("✅ VC++ Runtime check skipped (not Windows)")
            return True
        
        # Check for common VC++ runtime files
        system32 = os.path.join(os.environ.get('SYSTEMROOT', 'C:\\Windows'), 'System32')
        runtime_files = [
            'msvcp140.dll',
            'vcruntime140.dll',
            'vcruntime140_1.dll'
        ]
        
        found_files = 0
        for runtime_file in runtime_files:
            full_path = os.path.join(system32, runtime_file)
            if os.path.exists(full_path):
                found_files += 1
        
        if found_files >= 2:  # Need at least 2 of the main runtime files
            print(f"✅ VC++ Runtime files found ({found_files}/{len(runtime_files)})")
            return True
        else:
            warnings_found.append("Visual C++ Runtime may be missing - some built applications might not work")
            print("⚠️  VC++ Runtime may be incomplete")
            print("   💡 Fix: Install Visual C++ Redistributable from Microsoft")
            return True  # Not critical for building, but for running
            
    except Exception as e:
        warnings_found.append(f"VC++ Runtime check failed: {e}")
        print(f"⚠️  VC++ Runtime check failed: {e}")
        return True

def verify_optional_tools(issues_found, warnings_found):
    """Verify optional tools that enhance functionality"""
    try:
        # Check for WiX Toolset
        wix_paths = [
            r'C:\Program Files (x86)\WiX Toolset v3.11\bin\candle.exe',
            r'C:\Program Files\WiX Toolset v3.11\bin\candle.exe',
        ]
        
        wix_found = False
        for wix_path in wix_paths:
            if os.path.exists(wix_path):
                print(f"✅ WiX Toolset found: {os.path.dirname(wix_path)}")
                wix_found = True
                break
        
        if not wix_found:
            print("⚠️  WiX Toolset not found (optional - for MSI creation)")
        
        # Check for Advanced Installer
        ai_paths = [
            r'C:\Program Files (x86)\Caphyon\Advanced Installer\bin\AdvancedInstaller.com',
            r'C:\Program Files\Caphyon\Advanced Installer\bin\AdvancedInstaller.com',
        ]
        
        ai_found = False
        for ai_path in ai_paths:
            if os.path.exists(ai_path):
                print(f"✅ Advanced Installer found: {os.path.dirname(ai_path)}")
                ai_found = True
                break
        
        if not ai_found:
            print("⚠️  Advanced Installer not found (optional - for professional MSI)")
        
        # Check for Git
        try:
            result = subprocess.run(['git', '--version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"✅ Git available: {result.stdout.strip()}")
            else:
                print("⚠️  Git not working properly (optional)")
        except:
            print("⚠️  Git not found (optional - for version control)")
        
        return True
        
    except Exception as e:
        print(f"⚠️  Optional tools check failed: {e}")
        return True

def handle_setup_environment():
    """Diagnose Python environment issues"""
    try:
        print("🔍 Python Environment Diagnostic")
        print("=" * 40)
        
        # Show current script Python
        print(f"📍 Current script Python: {sys.executable}")
        print(f"   Version: {sys.version}")
        
        # Show PATH information
        print("\n🛤️  Python PATH Analysis:")
        path_dirs = os.environ.get('PATH', '').split(os.pathsep)
        python_in_path = []
        
        for i, path_dir in enumerate(path_dirs[:10]):  # Show first 10 PATH entries
            if any(python_indicator in path_dir.lower() for python_indicator in ['python', 'anaconda', 'conda', 'platformio', 'msys', 'mingw']):
                python_in_path.append(f"   [{i+1}] {path_dir}")
        
        if python_in_path:
            print("  Python-related directories in PATH:")
            for entry in python_in_path:
                print(entry)
        else:
            print("  No obvious Python directories in PATH")
        
        # Test various Python commands
        print("\n🧪 Python Command Tests:")
        commands_to_test = [
            ('py', 'Python Launcher'),
            ('py -3.13', 'Python 3.13 via Launcher'),
            ('python', 'python command'),
            ('python3', 'python3 command'),
        ]
        
        for cmd, description in commands_to_test:
            try:
                if cmd.startswith('py '):
                    cmd_parts = cmd.split()
                else:
                    cmd_parts = [cmd]
                    
                result = subprocess.run(
                    cmd_parts + ['-c', 'import sys; print(f"Path: {sys.executable}"); print(f"Version: {sys.version_info[:2]}")'],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    shell=True if cmd.startswith('py ') else False
                )
                
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    path_line = lines[0] if lines else "Unknown path"
                    version_line = lines[1] if len(lines) > 1 else "Unknown version"
                    print(f"  ✅ {description}: {path_line}, {version_line}")
                    
                    # Check for problematic installations
                    if any(prob in path_line.lower() for prob in ['platformio', 'msys', 'mingw', 'anaconda']):
                        print(f"     ⚠️  This appears to be from a development environment")
                else:
                    print(f"  ❌ {description}: Failed (return code {result.returncode})")
                    
            except Exception as e:
                print(f"  ❌ {description}: Exception - {e}")
        
        # Test PIL availability
        print("\n📦 PIL/Pillow Availability Test:")
        core = BuildToolCore()
        pil_python = core.find_python_with_pil()
        
        if pil_python:
            print(f"  ✅ PIL found with: {pil_python}")
        else:
            print("  ❌ No Python with PIL found")
            
        # Environment recommendations
        print("\n💡 Recommendations:")
        
        current_python = sys.executable.lower()
        if 'platformio' in current_python:
            print("  🔧 PlatformIO Python detected:")
            print("     • This is from VS Code PlatformIO extension")
            print("     • It may not have PIL/Pillow installed")
            print("     • Solution: Use py launcher for system Python")
            print("     • Command: py -m pip install Pillow")
        elif 'msys' in current_python or 'mingw' in current_python:
            print("  🔧 MSYS2/MinGW Python detected:")
            print("     • This is from development tools")
            print("     • Solution: Use system Python via py launcher")
            print("     • Command: py -m pip install Pillow")
        elif 'anaconda' in current_python or 'conda' in current_python:
            print("  🔧 Conda Python detected:")
            print("     • Install PIL in conda environment: conda install pillow")
            print("     • Or use system Python: py -m pip install Pillow")
        else:
            print("  ✅ Python environment looks normal")
            if not pil_python:
                print("     • Install PIL: pip install Pillow")
                print("     • Or: py -m pip install Pillow")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in environment diagnostic: {e}")
        return False

def handle_new_command():
    """Handle --new command for creating certificates and keys"""
    try:
        # Get the new item type from arguments
        new_type = None
        for i, arg in enumerate(sys.argv):
            if arg == '--new' and i + 1 < len(sys.argv):
                new_type = sys.argv[i + 1].lower()
                break
        
        if not new_type:
            print("🔨 Create New Items")
            print("=" * 25)
            print("Available creation options:")
            print("  --new cert           Create code signing certificate")
            print("  --new keysign        Create code signing certificate (alias)")
            print("  --new certificate    Create code signing certificate (full name)")
            print()
            print("Examples:")
            print("  py build_cli.py --new cert")
            print("  py build_cli.py --new keysign")
            return False
        
        if new_type in ['cert', 'certificate', 'keysign', 'signing-cert']:
            return handle_create_certificate()
        else:
            print(f"❌ Unknown creation type: {new_type}")
            print("💡 Available: cert, certificate, keysign, signing-cert")
            return False
        
    except Exception as e:
        print(f"❌ Error in new command: {e}")
        return False

def handle_setup_signing():
    """Handle signing setup configuration"""
    try:
        print("🔐 Code Signing Setup")
        print("=" * 30)
        
        # Check for administrative privileges for certificate installation
        if not ensure_admin_for_operation('setup_sign', 'Certificate installation and setup'):
            return False
        
        core = BuildToolCore()
        cert_info = core.get_certificate_info()
        cert_path = os.path.join(os.getcwd(), "certificate.pfx")
        
        if cert_info:
            cert_file, cert_pass = cert_info
            print(f"✅ Certificate found: {cert_file}")
            print(f"🔑 Password configured: {'Yes' if cert_pass else 'No'}")
            
            # Check if certificate is installed in trusted stores
            print("\n🔍 Checking certificate installation...")
            if check_certificate_installed(cert_file, cert_pass):
                print("✅ Certificate is installed in trusted stores")
                print("🧪 Test signing with: py build_cli.py --start package")
            else:
                print("⚠️  Certificate needs to be installed to trusted stores")
                print("\n🔄 Installing certificate to trusted stores...")
                
                # Attempt automatic installation since we have admin privileges
                if install_certificate_to_stores(cert_file, cert_pass):
                    print("✅ Certificate installed successfully")
                    print("🧪 Test signing with: py build_cli.py --start package")
                else:
                    print("⚠️  Automatic installation failed")
                    show_certificate_install_instructions(cert_file, cert_pass)
        else:
            print("❌ No certificate found")
            print(f"📍 Expected location: {cert_path}")
            print("\n💡 To create a certificate:")
            print("  py build_cli.py --new cert")
            print("\n💡 Or place your existing certificate.pfx in the project root")
            
        return True
        
    except Exception as e:
        print(f"❌ Error in setup signing: {e}")
        return False

def handle_create_certificate():
    """Handle certificate creation"""
    try:
        print("🔨 Creating Code Signing Certificate")
        print("=" * 40)
        
        # Request administrative privileges for certificate creation and installation
        if not ensure_admin_for_operation('install_cert', 'Certificate creation and installation'):
            print("⚠️  Note: Certificate will be created but may not be automatically installed")
            print("💡 Run as Administrator for automatic certificate installation")
        
        cert_path = os.path.join(os.getcwd(), "certificate.pfx")
        password = "PDFUtility2025"
        
        if os.path.exists(cert_path):
            print(f"⚠️  Certificate already exists: {cert_path}")
            response = input("Replace existing certificate? [y/N]: ").lower().strip()
            if response not in ['y', 'yes']:
                print("❌ Certificate creation cancelled")
                return False
            
            # Backup existing certificate
            backup_path = cert_path + ".backup"
            import shutil
            shutil.copy2(cert_path, backup_path)
            print(f"📁 Backed up existing certificate to: {backup_path}")
        
        # Create the certificate
        success = create_code_signing_certificate(cert_path, password)
        
        if success:
            print("✅ Certificate created successfully!")
            print(f"📁 Location: {cert_path}")
            print(f"🔑 Password: {password}")
            
            # Set environment variables
            os.environ['CERT_PATH'] = cert_path
            os.environ['CERT_PASSWORD'] = password
            
            # Try to set permanently
            set_env_result = set_environment_variables(cert_path, password)
            if set_env_result:
                print("✅ Environment variables configured")
            
            # Try to automatically install certificate if we have admin privileges
            if is_admin():
                print("\n� Attempting automatic certificate installation...")
                if install_certificate_to_stores(cert_path, password):
                    print("✅ Certificate automatically installed to trusted stores")
                    print("🧪 Ready to test: py build_cli.py --start package")
                else:
                    print("⚠️  Automatic installation failed")
                    print("\n📋 Next steps:")
                    print("1. Install certificate to trusted stores:")
                    print("   py build_cli.py --setup sign")
                    print("2. Test signing:")
                    print("   py build_cli.py --start package")
            else:
                print("\n�📋 Next steps:")
                print("1. Install certificate to trusted stores:")
                print("   py build_cli.py --setup sign")
                print("2. Test signing:")
                print("   py build_cli.py --start package")
            
            return True
        else:
            print("❌ Failed to create certificate")
            return False
            
    except Exception as e:
        print(f"❌ Error creating certificate: {e}")
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

def handle_export_manifest_command():
    """Handle --export-manifest command for reproducible builds"""
    try:
        # Get the manifest file path from arguments
        manifest_file = None
        for i, arg in enumerate(sys.argv):
            if arg == '--export-manifest' and i + 1 < len(sys.argv):
                manifest_file = sys.argv[i + 1]
                break
        
        if not manifest_file:
            # Generate default manifest filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            manifest_file = f"build_manifest_{timestamp}.json"
        
        print(f"📋 Generating reproducible build manifest: {manifest_file}")
        return generate_reproducible_manifest(manifest_file)
        
    except Exception as e:
        print(f"❌ Error generating build manifest: {e}")
        return False

def generate_reproducible_manifest(manifest_file):
    """Generate a comprehensive reproducible build manifest"""
    try:
        import hashlib
        import platform
        
        print("🔍 Collecting build environment information...")
        
        manifest = {
            "_manifest_info": {
                "format_version": "1.0",
                "manifest_type": "reproducible_build",
                "generated_by": "PDFUtility BuildSystem",
                "generated_at": datetime.now().isoformat(),
                "purpose": "Enable exact reproduction of this build"
            }
        }
        
        # 1. System Environment
        print("   📊 Recording system environment...")
        manifest["system_environment"] = {
            "platform": {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "architecture": platform.architecture(),
                "python_implementation": platform.python_implementation()
            },
            "python": {
                "version": platform.python_version(),
                "version_info": list(sys.version_info),
                "executable": sys.executable,
                "prefix": sys.prefix,
                "base_prefix": getattr(sys, 'base_prefix', sys.prefix),
                "real_prefix": getattr(sys, 'real_prefix', None),
                "is_venv": hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
            }
        }
        
        # 2. Tool Versions
        print("   🛠️ Recording tool versions...")
        tools = {}
        
        # PyInstaller version
        try:
            import PyInstaller
            tools["pyinstaller"] = {
                "version": PyInstaller.__version__,
                "location": PyInstaller.__file__
            }
        except ImportError:
            tools["pyinstaller"] = None
        
        # PIL version
        try:
            from PIL import Image
            tools["pillow"] = {
                "version": getattr(Image, 'PILLOW_VERSION', 'unknown'),
                "location": Image.__file__
            }
        except ImportError:
            tools["pillow"] = None
        
        # Get tool executable paths
        core = BuildToolCore()
        tools["makeappx"] = core.find_windows_sdk_tool('makeappx.exe')
        tools["signtool"] = core.find_windows_sdk_tool('signtool.exe')
        
        manifest["tool_versions"] = tools
        
        # 3. Python Package Environment
        print("   📦 Recording Python packages...")
        try:
            import subprocess
            pip_freeze = subprocess.run([sys.executable, '-m', 'pip', 'freeze'], 
                                      capture_output=True, text=True, timeout=30)
            if pip_freeze.returncode == 0:
                packages = {}
                for line in pip_freeze.stdout.strip().split('\n'):
                    if line and '==' in line:
                        name, version = line.split('==', 1)
                        packages[name] = {
                            "version": version,
                            "requirement": line
                        }
                manifest["python_packages"] = {
                    "pip_freeze_output": pip_freeze.stdout.strip(),
                    "packages": packages,
                    "total_packages": len(packages)
                }
            else:
                manifest["python_packages"] = {"error": "Could not run pip freeze"}
        except Exception as e:
            manifest["python_packages"] = {"error": str(e)}
        
        # 4. Build Configuration
        print("   ⚙️ Recording build configuration...")
        core = BuildToolCore()
        build_config = core.memory.get_config()
        scan_results = core.memory.get_scan_results()
        
        manifest["build_configuration"] = {
            "config": build_config,
            "scan_results": scan_results
        }
        
        # 5. Input Files with Checksums
        print("   🔍 Computing file checksums...")
        input_files = {}
        
        # Get all files from scan results
        all_files = []
        for category, files in scan_results.items():
            if isinstance(files, list):
                all_files.extend(files)
            elif isinstance(files, dict):
                for subcategory, subfiles in files.items():
                    if isinstance(subfiles, list):
                        all_files.extend(subfiles)
        
        # Add main file if specified
        main_file = build_config.get('main_file')
        if main_file and os.path.exists(main_file):
            all_files.append(main_file)
        
        # Remove duplicates
        all_files = list(set(all_files))
        
        for file_path in all_files:
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    
                    input_files[file_path] = {
                        "size": len(content),
                        "sha256": hashlib.sha256(content).hexdigest(),
                        "md5": hashlib.md5(content).hexdigest(),
                        "modified_time": os.path.getmtime(file_path)
                    }
                except Exception as e:
                    input_files[file_path] = {"error": str(e)}
        
        manifest["input_files"] = {
            "files": input_files,
            "total_files": len(input_files)
        }
        
        # 6. Environment Variables (filtered for security)
        print("   🌍 Recording relevant environment variables...")
        relevant_env_vars = [
            'PATH', 'PYTHONPATH', 'VIRTUAL_ENV', 'CONDA_DEFAULT_ENV',
            'HOME', 'USERPROFILE', 'TEMP', 'TMP',
            'PROCESSOR_ARCHITECTURE', 'PROCESSOR_IDENTIFIER',
            'CERT_PATH', 'CERT_PASSWORD'  # Build-specific vars
        ]
        
        env_vars = {}
        for var in relevant_env_vars:
            value = os.environ.get(var)
            if value:
                # Mask sensitive information
                if 'PASSWORD' in var or 'SECRET' in var or 'KEY' in var:
                    env_vars[var] = "***MASKED***"
                else:
                    env_vars[var] = value
        
        manifest["environment_variables"] = env_vars
        
        # 7. Reproduction Instructions
        manifest["reproduction_instructions"] = {
            "overview": "This manifest contains all information needed to reproduce the build",
            "steps": [
                f"1. Install Python {platform.python_version()} on {platform.system()} {platform.release()}",
                "2. Create virtual environment (if used)",
                "3. Install packages from pip_freeze_output",
                "4. Restore input files with matching checksums",
                "5. Set environment variables (excluding masked ones)",
                "6. Run build with recorded configuration",
                "7. Verify output checksums match"
            ],
            "commands": [
                f"python -m venv build_env",
                f"build_env\\Scripts\\activate  # Windows",
                f"pip install -r requirements.txt  # From pip_freeze_output",
                f"py build_cli.py --import build_config.json",
                f"py build_cli.py --start build"
            ]
        }
        
        # Write manifest
        print(f"💾 Writing manifest to {manifest_file}...")
        with open(manifest_file, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False, default=str)
        
        # Summary
        print(f"✅ Reproducible build manifest created: {manifest_file}")
        print(f"📊 Manifest includes:")
        print(f"   • System: {platform.system()} {platform.release()}")
        print(f"   • Python: {platform.python_version()} ({sys.executable})")
        print(f"   • Packages: {len(manifest.get('python_packages', {}).get('packages', {}))}")
        print(f"   • Input files: {len(input_files)} (with SHA256 checksums)")
        print(f"   • Tools: {len([k for k, v in tools.items() if v])}")
        print(f"   • Environment: {len(env_vars)} variables")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating manifest: {e}")
        import traceback
        traceback.print_exc()
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

def execute_config_command(key, value):
    """Execute configuration command to set build options"""
    try:
        memory = ConsoleMemory()
        build_config = memory.get_config()
        build_config[key] = value
        memory.store_config(build_config)
        
        print(f"✅ Configuration updated: {key} = {value}")
        
        # Show relevant advice based on the setting
        if key == 'dual_sign':
            if value:
                print("💡 Dual signing enabled: SHA-256 + SHA-1 for maximum compatibility")
            else:
                print("💡 Dual signing disabled: SHA-256 only (modern systems)")
        elif key == 'enable_timestamp':
            if value:
                print("💡 Timestamping enabled: Better SmartScreen reputation")
            else:
                print("⚠️  Timestamping disabled: Not recommended for production")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating configuration: {e}")
        return False

def execute_verify_signature_command():
    """Execute signature verification for the last built executable"""
    try:
        import glob
        
        memory = ConsoleMemory()
        build_config = memory.get_config()
        
        # Try to find the most recently built executable
        exe_paths = []
        
        # Check dist directory
        for pattern in ['*.exe', 'dist/*.exe', 'dist/*/*.exe']:
            exe_paths.extend(glob.glob(pattern))
        
        if not exe_paths:
            print("❌ No executable found to verify")
            print("💡 Build an executable first with: python build_cli.py --start build")
            return False
        
        # Use the most recently modified executable
        latest_exe = max(exe_paths, key=os.path.getmtime)
        
        print(f"🔍 Verifying signature for: {os.path.basename(latest_exe)}")
        
        # Create a BuildToolCore instance to access signing methods
        core = BuildToolCore()
        signtool_path = core.find_windows_sdk_tool('signtool.exe')
        
        if not signtool_path:
            print("❌ SignTool not found - cannot verify signature")
            return False
        
        # Use the existing verification method
        core._verify_executable_signature(signtool_path, latest_exe)
        
        return True
        
    except Exception as e:
        print(f"❌ Error verifying signature: {e}")
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

# ============================================================================
# CERTIFICATE MANAGEMENT HELPER FUNCTIONS
# ============================================================================

def check_admin_rights():
    """Check if running with administrator rights"""
    try:
        result = subprocess.run(
            ['powershell', '-Command', "([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] 'Administrator')"],
            capture_output=True,
            text=True,
            shell=True
        )
        return result.returncode == 0 and "True" in result.stdout
    except Exception:
        return False

def run_powershell_command(command):
    """Run a PowerShell command and return success, stdout, stderr"""
    try:
        result = subprocess.run(
            ['powershell', '-Command', command],
            capture_output=True,
            text=True,
            shell=True
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def create_code_signing_certificate(cert_path, password):
    """Create a new self-signed code signing certificate"""
    print("🔨 Creating self-signed code signing certificate...")
    
    create_cmd = f'''
$cert = New-SelfSignedCertificate -Type CodeSigning -Subject "CN=PDF Utility Developer" -KeyUsage DigitalSignature -KeyAlgorithm RSA -KeyLength 2048 -Provider "Microsoft Enhanced RSA and AES Cryptographic Provider" -CertStoreLocation "Cert:\\CurrentUser\\My" -NotAfter (Get-Date).AddYears(3)
$password = ConvertTo-SecureString -String "{password}" -Force -AsPlainText
Export-PfxCertificate -Cert $cert -FilePath "{cert_path}" -Password $password
Write-Host "Certificate created successfully"
'''
    
    success, stdout, stderr = run_powershell_command(create_cmd)
    
    if success:
        print("✅ Certificate created successfully")
        
        # Try to install to trusted stores if admin
        if check_admin_rights():
            install_success = install_certificate_to_stores(cert_path, password)
            if install_success:
                print("✅ Certificate installed to trusted stores")
            else:
                print("⚠️  Certificate created but not installed to trusted stores")
                print("💡 Run 'py build_cli.py --setup sign' as Administrator to install")
        else:
            print("💡 Run as Administrator to automatically install to trusted stores")
        
        return True
    else:
        print(f"❌ Failed to create certificate: {stderr}")
        return False

def install_certificate_to_stores(cert_path, password):
    """Install certificate to trusted root and publisher stores"""
    if not check_admin_rights():
        return False
    
    install_cmd = f'''
$password = ConvertTo-SecureString -String "{password}" -Force -AsPlainText
Import-PfxCertificate -FilePath "{cert_path}" -CertStoreLocation "Cert:\\LocalMachine\\Root" -Password $password
Import-PfxCertificate -FilePath "{cert_path}" -CertStoreLocation "Cert:\\LocalMachine\\TrustedPublisher" -Password $password
Write-Host "Certificate installed to trusted stores"
'''
    
    success, stdout, stderr = run_powershell_command(install_cmd)
    return success

def check_certificate_installed(cert_path, password):
    """Check if certificate is installed in trusted stores"""
    # This is a simplified check - could be enhanced to actually verify the specific certificate
    check_cmd = '''
$rootCerts = Get-ChildItem -Path "Cert:\\LocalMachine\\Root" | Where-Object {$_.Subject -like "*PDF Utility Developer*"}
$pubCerts = Get-ChildItem -Path "Cert:\\LocalMachine\\TrustedPublisher" | Where-Object {$_.Subject -like "*PDF Utility Developer*"}
if ($rootCerts -and $pubCerts) { Write-Host "INSTALLED" } else { Write-Host "NOT_INSTALLED" }
'''
    
    success, stdout, stderr = run_powershell_command(check_cmd)
    return success and "INSTALLED" in stdout

def show_certificate_install_instructions(cert_path, password):
    """Show instructions for installing certificate"""
    print("\n📋 To install certificate to trusted stores:")
    print("1. Open PowerShell as Administrator")
    print("2. Run these commands:")
    print()
    print(f'   $password = ConvertTo-SecureString -String "{password}" -Force -AsPlainText')
    print(f'   Import-PfxCertificate -FilePath "{cert_path}" -CertStoreLocation "Cert:\\LocalMachine\\Root" -Password $password')
    print(f'   Import-PfxCertificate -FilePath "{cert_path}" -CertStoreLocation "Cert:\\LocalMachine\\TrustedPublisher" -Password $password')
    print()
    print("Or simply run:")
    print("   py build_cli.py --setup sign     (as Administrator)")

def set_environment_variables(cert_path, password):
    """Set certificate environment variables"""
    try:
        # Set for current session
        os.environ['CERT_PATH'] = cert_path
        os.environ['CERT_PASSWORD'] = password
        
        # Try to set permanently for user
        cmd1 = f"[Environment]::SetEnvironmentVariable('CERT_PATH', '{cert_path}', 'User')"
        cmd2 = f"[Environment]::SetEnvironmentVariable('CERT_PASSWORD', '{password}', 'User')"
        
        success1, _, _ = run_powershell_command(cmd1)
        success2, _, _ = run_powershell_command(cmd2)
        
        return success1 and success2
    except Exception:
        return False

def handle_generate_hooks_command():
    """Handle --generate-hooks command"""
    try:
        safe_print("🔧 PyInstaller Hook Generation")
        safe_print("=" * 40)
        
        # Parse target file argument
        target_file = None
        for i, arg in enumerate(sys.argv):
            if arg == '--generate-hooks' and i + 1 < len(sys.argv):
                # Check if next argument is a file (not another flag)
                next_arg = sys.argv[i + 1]
                if not next_arg.startswith('--'):
                    target_file = next_arg
                break
        
        # If no target file specified, try to get main entry from memory or auto-detect
        if not target_file:
            core = BuildToolCore()
            build_config = core.memory.get_config()
            
            # Try to get from memory configuration first
            target_file = build_config.get('main_file')
            
            # If still no main file, try auto-detection
            if not target_file:
                safe_print("🔍 No target file specified, attempting auto-detection...")
                target_file = core.auto_detect_main_file()
                
                if not target_file:
                    safe_print("❌ Could not determine main entry point")
                    safe_print("💡 Usage: --generate-hooks [main_file.py]")
                    safe_print("💡 Or set main file first: --main main_file.py")
                    return False
                else:
                    safe_print(f"✅ Auto-detected main file: {target_file}")
        
        # Validate target file exists
        if not os.path.exists(target_file):
            safe_print(f"❌ Target file not found: {target_file}")
            return False
            
        # Generate hooks
        return generate_pyinstaller_hooks(target_file)
        
    except Exception as e:
        safe_print(f"❌ Error in hook generation: {e}")
        return False

def handle_trace_imports_command():
    """Handle --trace-imports command"""
    try:
        safe_print("🕵️ Hidden Import Tracing")
        safe_print("=" * 40)
        
        # Parse target file argument
        target_file = None
        for i, arg in enumerate(sys.argv):
            if arg == '--trace-imports' and i + 1 < len(sys.argv):
                # Check if next argument is a file (not another flag)
                next_arg = sys.argv[i + 1]
                if not next_arg.startswith('--'):
                    target_file = next_arg
                break
        
        # If no target file specified, try to get main entry from memory or auto-detect
        if not target_file:
            core = BuildToolCore()
            build_config = core.memory.get_config()
            
            # Try to get from memory configuration first
            target_file = build_config.get('main_file')
            
            # If still no main file, try auto-detection
            if not target_file:
                safe_print("🔍 No target file specified, attempting auto-detection...")
                target_file = core.auto_detect_main_file()
                
                if not target_file:
                    safe_print("❌ Could not determine main entry point")
                    safe_print("💡 Usage: --trace-imports [main_file.py]")
                    safe_print("💡 Or set main file first: --main main_file.py")
                    return False
                else:
                    safe_print(f"✅ Auto-detected main file: {target_file}")
        
        # Validate target file exists
        if not os.path.exists(target_file):
            safe_print(f"❌ Target file not found: {target_file}")
            return False
            
        # Trace imports
        return trace_hidden_imports(target_file)
        
    except Exception as e:
        safe_print(f"❌ Error in import tracing: {e}")
        return False

def generate_pyinstaller_hooks(target_file):
    """Generate PyInstaller hooks for better import detection"""
    try:
        safe_print(f"🔧 Generating PyInstaller hooks for: {target_file}")
        
        # Create hooks directory
        hooks_dir = os.path.join(os.path.dirname(target_file), 'hooks')
        os.makedirs(hooks_dir, exist_ok=True)
        
        safe_print(f"📁 Hooks directory: {hooks_dir}")
        
        # Analyze the target file for imports
        imports_data = analyze_imports_for_hooks(target_file)
        
        if not imports_data:
            safe_print("⚠️ No hookable imports detected")
            return True
        
        generated_hooks = 0
        
        # Generate hooks for each detected module
        for module_name, import_info in imports_data.items():
            hook_content = generate_hook_content(module_name, import_info)
            
            if hook_content:
                hook_filename = f"hook-{module_name}.py"
                hook_filepath = os.path.join(hooks_dir, hook_filename)
                
                with open(hook_filepath, 'w', encoding='utf-8') as f:
                    f.write(hook_content)
                
                safe_print(f"📝 Generated hook: {hook_filename}")
                generated_hooks += 1
        
        # Generate a runtime hook for initialization
        runtime_hook_content = generate_runtime_hook()
        runtime_hook_path = os.path.join(hooks_dir, 'runtime_hook.py')
        
        with open(runtime_hook_path, 'w', encoding='utf-8') as f:
            f.write(runtime_hook_content)
        
        safe_print(f"📝 Generated runtime hook: runtime_hook.py")
        
        # Update build configuration with hooks
        try:
            core = BuildToolCore()
            build_config = core.memory.get_config()
            build_config['hooks_directory'] = hooks_dir
            build_config['runtime_hooks'] = [runtime_hook_path]
            core.memory.store_config(build_config)
            safe_print("💾 Updated build configuration with hook paths")
        except:
            pass  # Non-critical
        
        safe_print(f"✅ Hook generation completed! Generated {generated_hooks} hooks")
        safe_print(f"💡 Use in PyInstaller: --additional-hooks-dir={hooks_dir}")
        safe_print(f"💡 Use runtime hook: --runtime-hook={runtime_hook_path}")
        
        return True
        
    except Exception as e:
        safe_print(f"❌ Error generating hooks: {e}")
        return False

def trace_hidden_imports(target_file):
    """Trace and analyze hidden imports in Python files"""
    try:
        safe_print(f"🕵️ Tracing hidden imports in: {target_file}")
        
        # Analyze the target file and its dependencies
        hidden_imports = analyze_hidden_imports(target_file)
        
        if not hidden_imports:
            safe_print("✅ No hidden imports detected")
            return True
        
        # Display results
        safe_print(f"\n📊 Hidden Import Analysis Results:")
        safe_print("=" * 50)
        
        for category, imports in hidden_imports.items():
            if imports:
                safe_print(f"\n📂 {category.upper()} ({len(imports)} modules):")
                for imp in sorted(imports):
                    safe_print(f"   • {imp}")
        
        # Generate a summary file
        summary_file = os.path.join(os.path.dirname(target_file), 'hidden_imports_analysis.txt')
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"Hidden Import Analysis for: {target_file}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")
            
            total_imports = sum(len(imports) for imports in hidden_imports.values())
            f.write(f"Total hidden imports detected: {total_imports}\n\n")
            
            for category, imports in hidden_imports.items():
                if imports:
                    f.write(f"{category.upper()} ({len(imports)} modules):\n")
                    for imp in sorted(imports):
                        f.write(f"  - {imp}\n")
                    f.write("\n")
            
            # Generate PyInstaller command fragment
            f.write("PyInstaller Command Fragment:\n")
            f.write("-" * 30 + "\n")
            all_imports = []
            for imports in hidden_imports.values():
                all_imports.extend(imports)
            
            for imp in sorted(set(all_imports)):
                f.write(f"--hidden-import={imp} \\\n")
            
            f.write("\n\nFull command example:\n")
            f.write("pyinstaller --onefile \\\n")
            for imp in sorted(set(all_imports))[:10]:  # Show first 10 to avoid too long line
                f.write(f"  --hidden-import={imp} \\\n")
            if len(all_imports) > 10:
                f.write(f"  # ... and {len(all_imports) - 10} more hidden imports\n")
            f.write(f"  {target_file}\n")
        
        safe_print(f"\n📄 Analysis saved to: {summary_file}")
        
        # Update build configuration with detected imports
        try:
            core = BuildToolCore()
            build_config = core.memory.get_config()
            
            all_imports = []
            for imports in hidden_imports.values():
                all_imports.extend(imports)
            
            # Merge with existing hidden imports
            existing_imports = build_config.get('hidden_imports', [])
            combined_imports = list(set(existing_imports + all_imports))
            
            build_config['hidden_imports'] = combined_imports
            core.memory.store_config(build_config)
            
            safe_print(f"💾 Added {len(all_imports)} hidden imports to build configuration")
        except Exception as e:
            safe_print(f"⚠️ Could not update build config: {e}")
        
        safe_print("✅ Import tracing completed!")
        return True
        
    except Exception as e:
        safe_print(f"❌ Error tracing imports: {e}")
        return False

def analyze_imports_for_hooks(target_file):
    """Analyze Python file for modules that would benefit from PyInstaller hooks"""
    try:
        import ast
        import importlib.util
        
        hookable_modules = {}
        
        # Read and parse the target file
        with open(target_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        try:
            tree = ast.parse(content, filename=target_file)
        except SyntaxError as e:
            safe_print(f"⚠️ Syntax error in {target_file}: {e}")
            return {}
        
        # Collect imports using AST
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name
                    if is_hookable_module(module_name):
                        hookable_modules[module_name] = {
                            'type': 'import',
                            'full_name': module_name,
                            'alias': alias.asname
                        }
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module_name = node.module
                    if is_hookable_module(module_name):
                        imported_items = [alias.name for alias in node.names]
                        hookable_modules[module_name] = {
                            'type': 'from_import',
                            'full_name': module_name,
                            'items': imported_items
                        }
        
        return hookable_modules
        
    except Exception as e:
        safe_print(f"⚠️ Error analyzing imports for hooks: {e}")
        return {}

def is_hookable_module(module_name):
    """Determine if a module would benefit from a PyInstaller hook"""
    # List of modules that commonly need hooks
    hookable_patterns = [
        'PyQt5', 'PyQt6', 'PySide2', 'PySide6',  # Qt frameworks
        'tkinter',  # Tkinter
        'PIL', 'Pillow',  # Image processing
        'numpy', 'scipy', 'matplotlib',  # Scientific computing
        'pandas', 'sklearn',  # Data analysis
        'requests', 'urllib3',  # HTTP libraries
        'sqlalchemy', 'sqlite3',  # Database
        'cryptography', 'ssl',  # Cryptography
        'multiprocessing', 'concurrent',  # Parallel processing
        'xml', 'json', 'yaml',  # Data formats
        'win32api', 'win32gui',  # Windows API
        'psutil', 'os', 'sys',  # System utilities
    ]
    
    return any(pattern in module_name.lower() for pattern in hookable_patterns)

def generate_hook_content(module_name, import_info):
    """Generate PyInstaller hook content for a specific module"""
    try:
        hook_template = f'''# PyInstaller hook for {module_name}
# Generated by PDFUtility BuildSystem

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect all data files for {module_name}
datas = collect_data_files('{module_name}')

# Collect all submodules
hiddenimports = collect_submodules('{module_name}')

'''
        
        # Add specific handling based on module type
        if 'qt' in module_name.lower():
            hook_template += f'''
# Qt-specific handling
try:
    from PyInstaller.utils.hooks import collect_system_data_files
    datas += collect_system_data_files('{module_name}')
except ImportError:
    pass

# Common Qt hidden imports
hiddenimports += [
    '{module_name}.QtCore',
    '{module_name}.QtGui',
    '{module_name}.QtWidgets',
]
'''
        
        elif module_name in ['PIL', 'Pillow']:
            hook_template += '''
# PIL/Pillow specific handling
hiddenimports += [
    'PIL._tkinter_finder',
    'PIL.ImageTk',
    'PIL.Image',
    'PIL.ImageDraw',
    'PIL.ImageFont',
]
'''
        
        elif 'numpy' in module_name.lower():
            hook_template += '''
# NumPy specific handling
hiddenimports += [
    'numpy.core._methods',
    'numpy.lib.format',
    'numpy.random.common',
    'numpy.random.bounded_integers',
    'numpy.random.entropy',
]
'''
        
        elif 'requests' in module_name.lower():
            hook_template += '''
# Requests specific handling
hiddenimports += [
    'requests.packages.urllib3',
    'requests.packages.urllib3.util',
    'requests.packages.urllib3.util.retry',
]
'''
        
        return hook_template
        
    except Exception as e:
        safe_print(f"⚠️ Error generating hook content for {module_name}: {e}")
        return None

def generate_runtime_hook():
    """Generate a runtime hook for application initialization"""
    return '''# PyInstaller runtime hook
# Generated by PDFUtility BuildSystem

import sys
import os

def setup_runtime_environment():
    """Setup runtime environment for the frozen application"""
    
    # Add current directory to Python path
    if hasattr(sys, '_MEIPASS'):
        # Running from PyInstaller bundle
        sys.path.insert(0, sys._MEIPASS)
        os.chdir(sys._MEIPASS)
    
    # Set up encoding for Windows console
    if sys.platform == 'win32':
        try:
            import codecs
            if sys.stdout.encoding != 'utf-8':
                sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
            if sys.stderr.encoding != 'utf-8':
                sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
        except:
            pass

# Run setup
setup_runtime_environment()
'''

def analyze_hidden_imports(target_file):
    """Analyze Python file for hidden imports using multiple methods"""
    try:
        import ast
        import importlib
        import pkgutil
        
        hidden_imports = {
            'standard_library': [],
            'third_party': [],
            'dynamic_imports': [],
            'conditional_imports': [],
            'plugin_imports': []
        }
        
        # Read and parse the target file
        with open(target_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        try:
            tree = ast.parse(content, filename=target_file)
        except SyntaxError as e:
            safe_print(f"⚠️ Syntax error in {target_file}: {e}")
            return hidden_imports
        
        # Analyze AST for different types of imports
        for node in ast.walk(tree):
            # Standard imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name
                    category = categorize_import(module_name)
                    if category and module_name not in hidden_imports[category]:
                        hidden_imports[category].append(module_name)
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module_name = node.module
                    category = categorize_import(module_name)
                    if category and module_name not in hidden_imports[category]:
                        hidden_imports[category].append(module_name)
            
            # Dynamic imports (importlib, __import__)
            elif isinstance(node, ast.Call):
                if (isinstance(node.func, ast.Attribute) and 
                    isinstance(node.func.value, ast.Name) and 
                    node.func.value.id == 'importlib' and 
                    node.func.attr == 'import_module'):
                    
                    if node.args and isinstance(node.args[0], ast.Constant):
                        module_name = node.args[0].value
                        if isinstance(module_name, str) and module_name not in hidden_imports['dynamic_imports']:
                            hidden_imports['dynamic_imports'].append(module_name)
                    elif node.args and isinstance(node.args[0], ast.Str):  # Python < 3.8 compatibility
                        module_name = node.args[0].s
                        if module_name not in hidden_imports['dynamic_imports']:
                            hidden_imports['dynamic_imports'].append(module_name)
                
                elif (isinstance(node.func, ast.Name) and 
                      node.func.id == '__import__'):
                    
                    if node.args and isinstance(node.args[0], ast.Constant):
                        module_name = node.args[0].value
                        if isinstance(module_name, str) and module_name not in hidden_imports['dynamic_imports']:
                            hidden_imports['dynamic_imports'].append(module_name)
                    elif node.args and isinstance(node.args[0], ast.Str):  # Python < 3.8 compatibility
                        module_name = node.args[0].s
                        if module_name not in hidden_imports['dynamic_imports']:
                            hidden_imports['dynamic_imports'].append(module_name)
        
        # Analyze string content for potential dynamic imports
        dynamic_patterns = [
            r"importlib\.import_module\(['\"]([^'\"]+)['\"]",
            r"__import__\(['\"]([^'\"]+)['\"]",
            r"exec\(['\"]import\s+([^'\"]+)['\"]",
            r"eval\(['\"]import\s+([^'\"]+)['\"]"
        ]
        
        import re
        for pattern in dynamic_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if match not in hidden_imports['dynamic_imports']:
                    hidden_imports['dynamic_imports'].append(match)
        
        # Look for plugin-style imports (common patterns)
        plugin_patterns = [
            r"plugins?['\"]?\s*\+\s*['\"]([^'\"]+)",
            r"load_plugin\(['\"]([^'\"]+)['\"]",
            r"get_plugin\(['\"]([^'\"]+)['\"]"
        ]
        
        for pattern in plugin_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if match not in hidden_imports['plugin_imports']:
                    hidden_imports['plugin_imports'].append(match)
        
        # Note: Removed recursive analysis to prevent infinite recursion
        # This now only analyzes the target file directly
        
        return hidden_imports
        
    except Exception as e:
        safe_print(f"⚠️ Error analyzing hidden imports: {e}")
        return {
            'standard_library': [],
            'third_party': [],
            'dynamic_imports': [],
            'conditional_imports': [],
            'plugin_imports': []
        }

def categorize_import(module_name):
    """Categorize an import as standard library, third party, etc."""
    try:
        import sys
        import importlib.util
        
        # Common standard library modules (hardcoded list for reliability)
        stdlib_modules = {
            'os', 'sys', 'json', 're', 'datetime', 'pathlib', 'subprocess', 'platform',
            'collections', 'itertools', 'functools', 'operator', 'math', 'random',
            'string', 'io', 'contextlib', 'copy', 'pickle', 'sqlite3', 'urllib',
            'http', 'email', 'xml', 'html', 'csv', 'configparser', 'logging',
            'argparse', 'shutil', 'tempfile', 'glob', 'fnmatch', 'linecache',
            'textwrap', 'unicodedata', 'encodings', 'codecs', 'time', 'calendar',
            'hashlib', 'hmac', 'secrets', 'ssl', 'socket', 'threading', 'multiprocessing',
            'concurrent', 'asyncio', 'queue', 'sched', 'weakref', 'types', 'abc',
            'numbers', 'enum', 'decimal', 'fractions', 'statistics', 'array',
            'bisect', 'heapq', 'zlib', 'gzip', 'bz2', 'lzma', 'zipfile', 'tarfile'
        }
        
        # Check if it's a built-in module
        if module_name in sys.builtin_module_names:
            return 'standard_library'
            
        # Check our hardcoded list
        base_module = module_name.split('.')[0]  # Get base module name
        if base_module in stdlib_modules:
            return 'standard_library'
        
        # Try to find the module
        try:
            spec = importlib.util.find_spec(module_name)
            if not spec:
                return None  # Module not found
            
            # Check if it's in the standard library by looking at the path
            if spec.origin:
                stdlib_paths = [
                    os.path.dirname(os.__file__),  # Standard library path
                    sys.prefix,  # Python installation prefix
                ]
                
                for stdlib_path in stdlib_paths:
                    if spec.origin.startswith(stdlib_path):
                        # Further check: exclude site-packages
                        if 'site-packages' not in spec.origin:
                            return 'standard_library'
                
                # If it contains site-packages or is in other locations, it's third party
                if 'site-packages' in spec.origin:
                    return 'third_party'
        except (ImportError, ValueError, AttributeError):
            pass
        
        # Default to third party if we can't determine otherwise
        return 'third_party'
        
    except Exception:
        return None

# ============================================================================
# PROJECT TEMPLATE SYSTEM
# ============================================================================

class ProjectTemplateManager:
    """Manages project templates for common Python stacks with optimized PyInstaller configurations"""
    
    def __init__(self):
        self.templates = {
            'default': {
                'name': 'Default Python Application',
                'description': 'Generic Python application with basic PyInstaller settings',
                'stack': ['python'],
                'hidden_imports': [
                    'pkg_resources.extern',
                    'pkg_resources._vendor',
                ],
                'collect_data': [],
                'collect_binaries': [],
                'collect_submodules': [],
                'excludes': [
                    'tkinter',
                    'matplotlib',
                    'PyQt5',
                    'PyQt6',
                    'PySide2',
                    'PySide6',
                ],
                'runtime_hooks': [],
                'upx_exclude': [],
                'binary_excludes': [],
                'datas': [],
                'additional_args': [],
                'icon_extensions': ['.ico', '.png'],
                'data_extensions': ['.txt', '.json', '.yaml', '.yml', '.xml'],
                'requirements': ['pyinstaller'],
            },
            
            'tkinter': {
                'name': 'Tkinter GUI Application',
                'description': 'Tkinter-based desktop applications with themed widgets',
                'stack': ['python', 'tkinter'],
                'hidden_imports': [
                    'tkinter',
                    'tkinter.ttk',
                    'tkinter.filedialog',
                    'tkinter.messagebox',
                    'tkinter.colorchooser',
                    'tkinter.font',
                    'tkinter.scrolledtext',
                    'tkinter.tix',
                    '_tkinter',
                    'PIL._tkinter_finder',  # For Pillow integration
                ],
                'collect_data': [
                    ('tkinter', '.'),
                ],
                'collect_binaries': [],
                'collect_submodules': ['tkinter'],
                'excludes': [
                    'PyQt5',
                    'PyQt6', 
                    'PySide2',
                    'PySide6',
                    'matplotlib.backends.qt_compat',
                ],
                'runtime_hooks': [],
                'upx_exclude': ['_tkinter.pyd', 'tk*.dll', 'tcl*.dll'],
                'binary_excludes': [],
                'datas': [],
                'additional_args': ['--windowed'],
                'icon_extensions': ['.ico', '.png', '.gif', '.xbm'],
                'data_extensions': ['.txt', '.json', '.yaml', '.yml', '.xml', '.ttf', '.otf'],
                'requirements': ['pyinstaller', 'pillow'],
            },
            
            'pyqt5': {
                'name': 'PyQt5 GUI Application', 
                'description': 'PyQt5-based desktop applications with Qt widgets',
                'stack': ['python', 'pyqt5', 'qt'],
                'hidden_imports': [
                    'PyQt5',
                    'PyQt5.QtCore',
                    'PyQt5.QtGui', 
                    'PyQt5.QtWidgets',
                    'PyQt5.QtNetwork',
                    'PyQt5.QtMultimedia',
                    'PyQt5.QtWebEngineWidgets',
                    'PyQt5.QtSvg',
                    'PyQt5.QtPrintSupport',
                    'PyQt5.sip',
                    'sip',
                ],
                'collect_data': [
                    ('PyQt5', '.'),
                ],
                'collect_binaries': [],
                'collect_submodules': ['PyQt5'],
                'excludes': [
                    'tkinter',
                    'PyQt6',
                    'PySide2', 
                    'PySide6',
                ],
                'runtime_hooks': [],
                'upx_exclude': ['Qt5*.dll', 'PyQt5*.pyd'],
                'binary_excludes': [],
                'datas': [],
                'additional_args': ['--windowed'],
                'icon_extensions': ['.ico', '.png', '.svg'],
                'data_extensions': ['.txt', '.json', '.yaml', '.yml', '.xml', '.qss', '.ui', '.qrc'],
                'requirements': ['pyinstaller', 'PyQt5'],
            },
            
            'pyqt6': {
                'name': 'PyQt6 GUI Application',
                'description': 'PyQt6-based desktop applications with modern Qt6 widgets',
                'stack': ['python', 'pyqt6', 'qt6'],
                'hidden_imports': [
                    'PyQt6',
                    'PyQt6.QtCore',
                    'PyQt6.QtGui',
                    'PyQt6.QtWidgets', 
                    'PyQt6.QtNetwork',
                    'PyQt6.QtMultimedia',
                    'PyQt6.QtWebEngineWidgets',
                    'PyQt6.QtSvg',
                    'PyQt6.QtPrintSupport',
                    'PyQt6.sip',
                    'PyQt6.sip',
                ],
                'collect_data': [
                    ('PyQt6', '.'),
                ],
                'collect_binaries': [],
                'collect_submodules': ['PyQt6'],
                'excludes': [
                    'tkinter',
                    'PyQt5',
                    'PySide2',
                    'PySide6',
                ],
                'runtime_hooks': [],
                'upx_exclude': ['Qt6*.dll', 'PyQt6*.pyd'],
                'binary_excludes': [],
                'datas': [],
                'additional_args': ['--windowed'],
                'icon_extensions': ['.ico', '.png', '.svg'],
                'data_extensions': ['.txt', '.json', '.yaml', '.yml', '.xml', '.qss', '.ui', '.qrc'],
                'requirements': ['pyinstaller', 'PyQt6'],
            },
            
            'pyside2': {
                'name': 'PySide2 GUI Application',
                'description': 'PySide2-based desktop applications with Qt5 widgets',
                'stack': ['python', 'pyside2', 'qt'],
                'hidden_imports': [
                    'PySide2',
                    'PySide2.QtCore',
                    'PySide2.QtGui',
                    'PySide2.QtWidgets',
                    'PySide2.QtNetwork',
                    'PySide2.QtMultimedia', 
                    'PySide2.QtWebEngineWidgets',
                    'PySide2.QtSvg',
                    'PySide2.QtPrintSupport',
                    'shiboken2',
                ],
                'collect_data': [
                    ('PySide2', '.'),
                ],
                'collect_binaries': [],
                'collect_submodules': ['PySide2'],
                'excludes': [
                    'tkinter',
                    'PyQt5',
                    'PyQt6',
                    'PySide6',
                ],
                'runtime_hooks': [],
                'upx_exclude': ['Qt5*.dll', 'PySide2*.pyd', 'shiboken2*.pyd'],
                'binary_excludes': [],
                'datas': [],
                'additional_args': ['--windowed'],
                'icon_extensions': ['.ico', '.png', '.svg'],
                'data_extensions': ['.txt', '.json', '.yaml', '.yml', '.xml', '.qss', '.ui', '.qrc'],
                'requirements': ['pyinstaller', 'PySide2'],
            },
            
            'pyside6': {
                'name': 'PySide6 GUI Application',
                'description': 'PySide6-based desktop applications with modern Qt6 widgets',
                'stack': ['python', 'pyside6', 'qt6'],
                'hidden_imports': [
                    'PySide6',
                    'PySide6.QtCore',
                    'PySide6.QtGui', 
                    'PySide6.QtWidgets',
                    'PySide6.QtNetwork',
                    'PySide6.QtMultimedia',
                    'PySide6.QtWebEngineWidgets',
                    'PySide6.QtSvg',
                    'PySide6.QtPrintSupport',
                    'shiboken6',
                ],
                'collect_data': [
                    ('PySide6', '.'),
                ],
                'collect_binaries': [],
                'collect_submodules': ['PySide6'],
                'excludes': [
                    'tkinter',
                    'PyQt5',
                    'PyQt6', 
                    'PySide2',
                ],
                'runtime_hooks': [],
                'upx_exclude': ['Qt6*.dll', 'PySide6*.pyd', 'shiboken6*.pyd'],
                'binary_excludes': [],
                'datas': [],
                'additional_args': ['--windowed'],
                'icon_extensions': ['.ico', '.png', '.svg'],
                'data_extensions': ['.txt', '.json', '.yaml', '.yml', '.xml', '.qss', '.ui', '.qrc'],
                'requirements': ['pyinstaller', 'PySide6'],
            },
            
            'pymupdf': {
                'name': 'PyMuPDF Document Application',
                'description': 'PyMuPDF-based applications for PDF processing and manipulation',
                'stack': ['python', 'pymupdf', 'documents'],
                'hidden_imports': [
                    'fitz',
                    'pymupdf',
                    'frontend',
                    'PIL',
                    'PIL.Image',
                    'PIL.ImageDraw',
                    'PIL.ImageFont',
                ],
                'collect_data': [
                    ('fitz', '.'),
                    ('pymupdf', '.'),
                ],
                'collect_binaries': [
                    ('fitz', '.'),
                ],
                'collect_submodules': ['fitz'],
                'excludes': [
                    'tkinter',
                    'PyQt5',
                    'PyQt6',
                    'PySide2', 
                    'PySide6',
                    'matplotlib',
                ],
                'runtime_hooks': [],
                'upx_exclude': ['mupdf*.dll', 'fitz*.pyd'],
                'binary_excludes': [],
                'datas': [],
                'additional_args': [],
                'icon_extensions': ['.ico', '.png'],
                'data_extensions': ['.pdf', '.txt', '.json', '.yaml', '.yml', '.xml'],
                'requirements': ['pyinstaller', 'PyMuPDF', 'pillow'],
            },
            
            'fastapi': {
                'name': 'FastAPI Web Application',
                'description': 'FastAPI-based web applications with uvicorn server',
                'stack': ['python', 'fastapi', 'web', 'async'],
                'hidden_imports': [
                    'fastapi',
                    'uvicorn',
                    'uvicorn.lifespan',
                    'uvicorn.lifespan.on',
                    'uvicorn.loops',
                    'uvicorn.loops.auto',
                    'uvicorn.protocols',
                    'uvicorn.protocols.http',
                    'uvicorn.protocols.websockets',
                    'starlette',
                    'starlette.applications',
                    'starlette.routing',
                    'starlette.responses',
                    'starlette.middleware',
                    'pydantic',
                    'pydantic.fields',
                    'pydantic.validators',
                    'email_validator',
                    'jinja2',
                    'aiofiles',
                    'multipart',
                ],
                'collect_data': [
                    ('fastapi', '.'),
                    ('uvicorn', '.'),
                    ('starlette', '.'),
                ],
                'collect_binaries': [],
                'collect_submodules': ['fastapi', 'uvicorn', 'starlette'],
                'excludes': [
                    'tkinter',
                    'PyQt5',
                    'PyQt6',
                    'PySide2',
                    'PySide6',
                    'matplotlib',
                ],
                'runtime_hooks': [],
                'upx_exclude': [],
                'binary_excludes': [],
                'datas': [
                    ('templates', 'templates'),
                    ('static', 'static'),
                ],
                'additional_args': ['--console'],
                'icon_extensions': ['.ico', '.png'],
                'data_extensions': ['.html', '.css', '.js', '.json', '.yaml', '.yml', '.xml', '.txt'],
                'requirements': ['pyinstaller', 'fastapi[all]', 'uvicorn[standard]'],
            },
            
            'flask': {
                'name': 'Flask Web Application',
                'description': 'Flask-based web applications with Werkzeug server',
                'stack': ['python', 'flask', 'web'],
                'hidden_imports': [
                    'flask',
                    'werkzeug',
                    'werkzeug.serving',
                    'werkzeug.security',
                    'jinja2',
                    'jinja2.ext',
                    'click',
                    'itsdangerous',
                    'blinker',
                ],
                'collect_data': [
                    ('flask', '.'),
                    ('jinja2', '.'),
                ],
                'collect_binaries': [],
                'collect_submodules': ['flask', 'jinja2'],
                'excludes': [
                    'tkinter',
                    'PyQt5',
                    'PyQt6',
                    'PySide2',
                    'PySide6',
                    'matplotlib',
                ],
                'runtime_hooks': [],
                'upx_exclude': [],
                'binary_excludes': [],
                'datas': [
                    ('templates', 'templates'),
                    ('static', 'static'),
                ],
                'additional_args': ['--console'],
                'icon_extensions': ['.ico', '.png'],
                'data_extensions': ['.html', '.css', '.js', '.json', '.yaml', '.yml', '.xml', '.txt'],
                'requirements': ['pyinstaller', 'flask', 'werkzeug', 'jinja2'],
            },
            
            'matplotlib': {
                'name': 'Matplotlib Data Visualization',
                'description': 'Matplotlib-based applications for data visualization and plotting',
                'stack': ['python', 'matplotlib', 'numpy', 'visualization'],
                'hidden_imports': [
                    'matplotlib',
                    'matplotlib.pyplot',
                    'matplotlib.backends',
                    'matplotlib.backends.backend_tkagg',
                    'matplotlib.backends.backend_qt5agg',
                    'matplotlib.figure',
                    'numpy',
                    'numpy.core',
                    'numpy.core._methods',
                    'numpy.lib',
                    'numpy.lib.format',
                    'pandas',
                    'scipy',
                ],
                'collect_data': [
                    ('matplotlib', '.'),
                ],
                'collect_binaries': [],
                'collect_submodules': ['matplotlib', 'numpy'],
                'excludes': [],
                'runtime_hooks': [],
                'upx_exclude': ['numpy*.pyd', 'matplotlib*.pyd'],
                'binary_excludes': [],
                'datas': [],
                'additional_args': [],
                'icon_extensions': ['.ico', '.png'],
                'data_extensions': ['.csv', '.json', '.yaml', '.yml', '.xml', '.txt', '.dat'],
                'requirements': ['pyinstaller', 'matplotlib', 'numpy', 'pandas'],
            },
        }
        
        self.current_template = 'default'
    
    def list_templates(self):
        """List all available templates"""
        print("📋 Available Project Templates:")
        print("=" * 45)
        
        for template_name, config in self.templates.items():
            stack_info = ' + '.join(config['stack'])
            print(f"\n🎯 {template_name.upper()} - {config['name']}")
            print(f"   {config['description']}")
            print(f"   Stack: {stack_info}")
            print(f"   Hidden imports: {len(config['hidden_imports'])} modules")
            print(f"   Requirements: {', '.join(config['requirements'])}")
    
    def get_template(self, template_name):
        """Get template configuration"""
        template_name = template_name.lower()
        if template_name in self.templates:
            return self.templates[template_name]
        else:
            available = ', '.join(self.templates.keys())
            raise ValueError(f"Unknown template '{template_name}'. Available: {available}")
    
    def apply_template(self, template_name, memory=None):
        """Apply template configuration to build memory"""
        try:
            template = self.get_template(template_name)
            self.current_template = template_name
            
            if memory is None:
                memory = ConsoleMemory()
            
            # Apply template settings to build config
            config = memory.get_config()
            
            # Core template settings
            config['template'] = template_name
            config['template_name'] = template['name']
            config['template_stack'] = template['stack']
            
            # PyInstaller settings
            config['hidden_imports'] = list(set(config.get('hidden_imports', []) + template['hidden_imports']))
            config['collect_data'] = template['collect_data']
            config['collect_binaries'] = template['collect_binaries']
            config['collect_submodules'] = template['collect_submodules']
            config['excludes'] = template['excludes']
            config['upx_exclude'] = template['upx_exclude']
            config['binary_excludes'] = template['binary_excludes']
            
            # Data handling
            config['template_datas'] = template['datas']
            config['template_icon_extensions'] = template['icon_extensions']
            config['template_data_extensions'] = template['data_extensions']
            
            # Additional PyInstaller arguments from template
            existing_args = config.get('additional_pyinstaller_args', [])
            template_args = template['additional_args']
            config['additional_pyinstaller_args'] = list(set(existing_args + template_args))
            
            # Requirements
            config['template_requirements'] = template['requirements']
            
            # Store updated config
            memory.store_config(config)
            
            print(f"✅ Applied template: {template['name']} ({template_name})")
            print(f"   {template['description']}")
            print(f"   Stack: {' + '.join(template['stack'])}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error applying template: {e}")
            return False
    
    def show_current_template(self, memory=None):
        """Show currently active template settings"""
        if memory is None:
            memory = ConsoleMemory()
            
        config = memory.get_config()
        current_template = config.get('template')
        
        if current_template:
            template = self.get_template(current_template)
            print(f"🎯 Current Template: {template['name']} ({current_template})")
            print(f"   {template['description']}")
            print(f"   Stack: {' + '.join(template['stack'])}")
            print()
            print("📋 Template Configuration:")
            print(f"   Hidden Imports: {len(template['hidden_imports'])} modules")
            print(f"   Data Collections: {len(template['collect_data'])} items")
            print(f"   Excluded Modules: {len(template['excludes'])} modules")
            print(f"   UPX Exclusions: {len(template['upx_exclude'])} files")
            print(f"   Additional Args: {' '.join(template['additional_args']) if template['additional_args'] else 'None'}")
            print(f"   Requirements: {', '.join(template['requirements'])}")
        else:
            print("⚠️ No template currently active")
            print("💡 Use --template <name> to set a template")
    
    def auto_detect_template(self, project_path='.'):
        """Auto-detect template based on project files and imports"""
        try:
            import os
            import glob
            
            print(f"🔍 Auto-detecting template for project: {project_path}")
            
            # Check for requirements.txt or pyproject.toml
            requirements = []
            
            req_file = os.path.join(project_path, 'requirements.txt')
            if os.path.exists(req_file):
                try:
                    with open(req_file, 'r') as f:
                        requirements = [line.strip().lower().split('==')[0].split('>=')[0].split('<=')[0] 
                                     for line in f if line.strip() and not line.startswith('#')]
                except Exception:
                    pass
            
            # Check Python files for imports
            imports = set()
            python_files = glob.glob(os.path.join(project_path, '**/*.py'), recursive=True)
            
            for py_file in python_files[:10]:  # Check first 10 Python files
                try:
                    with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        # Simple regex to find imports
                        import re
                        import_matches = re.findall(r'(?:^|\n)(?:import|from)\s+([a-zA-Z_][a-zA-Z0-9_]*)', content)
                        imports.update(import_matches)
                except Exception:
                    continue
            
            # Template detection logic
            all_indicators = set(requirements + list(imports))
            
            # Check for specific frameworks (order matters - most specific first)
            if any(x in all_indicators for x in ['fastapi', 'uvicorn']):
                return 'fastapi'
            elif any(x in all_indicators for x in ['flask', 'werkzeug']):
                return 'flask'
            elif any(x in all_indicators for x in ['pyqt6', 'PyQt6']):
                return 'pyqt6'
            elif any(x in all_indicators for x in ['pyqt5', 'PyQt5']):
                return 'pyqt5'
            elif any(x in all_indicators for x in ['pyside6', 'PySide6']):
                return 'pyside6'
            elif any(x in all_indicators for x in ['pyside2', 'PySide2']):
                return 'pyside2'
            elif any(x in all_indicators for x in ['fitz', 'pymupdf', 'PyMuPDF']):
                return 'pymupdf'
            elif any(x in all_indicators for x in ['matplotlib', 'pyplot']):
                return 'matplotlib'
            elif any(x in all_indicators for x in ['tkinter', 'Tkinter']):
                return 'tkinter'
            else:
                return 'default'
                
        except Exception as e:
            print(f"⚠️ Auto-detection failed: {e}")
            return 'default'
    
    def generate_pyinstaller_args_from_template(self, config):
        """Generate PyInstaller arguments based on template configuration"""
        args = []
        
        # Hidden imports
        hidden_imports = config.get('hidden_imports', [])
        for imp in hidden_imports:
            args.extend(['--hidden-import', imp])
        
        # Collect data
        collect_data = config.get('collect_data', [])
        for data_spec in collect_data:
            if isinstance(data_spec, tuple) and len(data_spec) == 2:
                args.extend(['--collect-data', data_spec[0]])
        
        # Collect binaries
        collect_binaries = config.get('collect_binaries', [])
        for binary_spec in collect_binaries:
            if isinstance(binary_spec, tuple) and len(binary_spec) == 2:
                args.extend(['--collect-binaries', binary_spec[0]])
        
        # Collect submodules
        collect_submodules = config.get('collect_submodules', [])
        for submodule in collect_submodules:
            args.extend(['--collect-submodules', submodule])
        
        # Excludes
        excludes = config.get('excludes', [])
        for exclude in excludes:
            args.extend(['--exclude-module', exclude])
        
        # UPX excludes
        upx_excludes = config.get('upx_exclude', [])
        for upx_exclude in upx_excludes:
            args.extend(['--upx-exclude', upx_exclude])
        
        # Template data files
        template_datas = config.get('template_datas', [])
        for data_spec in template_datas:
            if isinstance(data_spec, tuple) and len(data_spec) == 2:
                src, dst = data_spec
                if os.path.exists(src):
                    args.extend(['--add-data', f'{src}{os.pathsep}{dst}'])
        
        # Additional arguments from template
        additional_args = config.get('additional_pyinstaller_args', [])
        args.extend(additional_args)
        
        return args

class ProjectCreator:
    """Creates new projects with templates, virtual environments, and auto-installed dependencies"""
    
    def __init__(self):
        self.template_manager = ProjectTemplateManager()
    
    def create_project(self, project_name, template_name='default', project_dir=None, python_version=None):
        """Create a complete new project with template, venv, and dependencies"""
        try:
            print(f"🚀 Creating New Project: {project_name}")
            print("=" * 50)
            
            # Determine project directory
            if project_dir is None:
                project_dir = os.path.join(os.getcwd(), project_name)
            else:
                project_dir = os.path.abspath(project_dir)
            
            # Check if directory already exists
            if os.path.exists(project_dir):
                response = input(f"⚠️ Directory '{project_dir}' already exists. Continue? (y/N): ").strip().lower()
                if response != 'y':
                    print("❌ Project creation cancelled")
                    return False
            
            # Create project directory
            os.makedirs(project_dir, exist_ok=True)
            print(f"📁 Project directory: {project_dir}")
            
            # Get template configuration
            try:
                template = self.template_manager.get_template(template_name)
                print(f"📋 Using template: {template['name']} ({template_name})")
                print(f"   {template['description']}")
            except Exception as e:
                print(f"❌ Error loading template: {e}")
                return False
            
            # Step 1: Create virtual environment
            venv_name = f"{project_name}_env"
            venv_path = os.path.join(project_dir, venv_name)
            
            if not self._create_virtual_environment(venv_path, python_version):
                return False
            
            # Step 2: Install template dependencies
            if not self._install_template_dependencies(venv_path, template):
                return False
            
            # Step 3: Create project structure
            if not self._create_project_structure(project_dir, project_name, template):
                return False
            
            # Step 4: Generate starter files
            if not self._generate_starter_files(project_dir, project_name, template):
                return False
            
            # Step 5: Create requirements.txt
            if not self._create_requirements_file(project_dir, template):
                return False
            
            # Step 6: Set up build configuration
            if not self._setup_build_configuration(project_dir, project_name, template_name):
                return False
            
            # Step 7: Create development scripts
            if not self._create_dev_scripts(project_dir, project_name, venv_name, template):
                return False
            
            print()
            print("✅ Project created successfully!")
            print("🎯 Next Steps:")
            print(f"   cd {project_name}")
            
            # Platform-specific activation instructions
            if platform.system() == 'Windows':
                print(f"   {venv_name}\\Scripts\\activate")
            else:
                print(f"   source {venv_name}/bin/activate")
            
            print(f"   python main.py  # Run the starter application")
            print(f"   python ../build_cli.py --start build  # Build executable")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating project: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _create_virtual_environment(self, venv_path, python_version=None):
        """Create virtual environment for the project"""
        try:
            print("\n🐍 Creating virtual environment...")
            
            # Determine Python executable
            if python_version:
                # Try to find specific Python version
                python_candidates = [
                    f"python{python_version}",
                    f"python{python_version.replace('.', '')}",
                    f"py -{python_version}",  # Windows py launcher
                ]
                
                python_exe = None
                for candidate in python_candidates:
                    try:
                        result = subprocess.run([candidate, '--version'], 
                                              capture_output=True, text=True, timeout=5)
                        if result.returncode == 0:
                            python_exe = candidate
                            print(f"   Found Python {python_version}: {candidate}")
                            break
                    except (subprocess.TimeoutExpired, FileNotFoundError):
                        continue
                
                if not python_exe:
                    print(f"⚠️ Python {python_version} not found, using default Python")
                    python_exe = sys.executable
            else:
                python_exe = sys.executable
            
            # Create virtual environment
            cmd = [python_exe, '-m', 'venv', venv_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            
            if result.returncode != 0:
                print(f"❌ Failed to create virtual environment: {result.stderr}")
                return False
            
            print(f"✅ Virtual environment created: {os.path.basename(venv_path)}")
            return True
            
        except Exception as e:
            print(f"❌ Error creating virtual environment: {e}")
            return False
    
    def _get_venv_pip(self, venv_path):
        """Get the pip executable path for the virtual environment"""
        if platform.system() == 'Windows':
            return os.path.join(venv_path, 'Scripts', 'pip.exe')
        else:
            return os.path.join(venv_path, 'bin', 'pip')
    
    def _get_venv_python(self, venv_path):
        """Get the Python executable path for the virtual environment"""
        if platform.system() == 'Windows':
            return os.path.join(venv_path, 'Scripts', 'python.exe')
        else:
            return os.path.join(venv_path, 'bin', 'python')
    
    def _install_template_dependencies(self, venv_path, template):
        """Install template-specific dependencies in the virtual environment"""
        try:
            print("\n📦 Installing template dependencies...")
            
            pip_exe = self._get_venv_pip(venv_path)
            requirements = template.get('requirements', [])
            
            if not requirements:
                print("   No dependencies specified in template")
                return True
            
            # Upgrade pip first
            print("   Upgrading pip...")
            upgrade_cmd = [pip_exe, 'install', '--upgrade', 'pip']
            result = subprocess.run(upgrade_cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                print(f"⚠️ Warning: Could not upgrade pip: {result.stderr}")
            
            # Install each requirement
            for requirement in requirements:
                print(f"   Installing {requirement}...")
                install_cmd = [pip_exe, 'install', requirement]
                result = subprocess.run(install_cmd, capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    print(f"   ✅ {requirement}")
                else:
                    print(f"   ❌ Failed to install {requirement}: {result.stderr[:200]}")
                    # Don't fail completely, continue with other packages
            
            print("✅ Dependencies installation completed")
            return True
            
        except Exception as e:
            print(f"❌ Error installing dependencies: {e}")
            return False
    
    def _create_project_structure(self, project_dir, project_name, template):
        """Create project directory structure based on template"""
        try:
            print("\n📁 Creating project structure...")
            
            # Common directories for all projects
            directories = ['src', 'assets', 'docs']
            
            # Template-specific directories
            stack = template.get('stack', [])
            
            if 'web' in stack or 'fastapi' in stack or 'flask' in stack:
                directories.extend(['templates', 'static', 'static/css', 'static/js', 'static/images'])
            
            if any(gui in stack for gui in ['tkinter', 'pyqt5', 'pyqt6', 'pyside2', 'pyside6']):
                directories.extend(['ui', 'resources', 'icons'])
            
            if 'documents' in stack or 'pymupdf' in stack:
                directories.extend(['documents', 'output'])
            
            if 'visualization' in stack or 'matplotlib' in stack:
                directories.extend(['data', 'plots', 'notebooks'])
            
            # Create directories
            for directory in directories:
                dir_path = os.path.join(project_dir, directory)
                os.makedirs(dir_path, exist_ok=True)
                
                # Create __init__.py for Python packages
                if directory in ['src']:
                    init_file = os.path.join(dir_path, '__init__.py')
                    with open(init_file, 'w') as f:
                        f.write(f'"""Package: {project_name}"""\n')
            
            print(f"✅ Created {len(directories)} directories")
            return True
            
        except Exception as e:
            print(f"❌ Error creating project structure: {e}")
            return False
    
    def _generate_starter_files(self, project_dir, project_name, template):
        """Generate starter application files based on template"""
        try:
            print("\n📄 Generating starter files...")
            
            template_name = template.get('template', 'default')
            stack = template.get('stack', [])
            
            # Generate main.py based on template
            main_content = self._generate_main_file(project_name, template)
            with open(os.path.join(project_dir, 'main.py'), 'w', encoding='utf-8') as f:
                f.write(main_content)
            
            # Generate README.md
            readme_content = self._generate_readme(project_name, template)
            with open(os.path.join(project_dir, 'README.md'), 'w', encoding='utf-8') as f:
                f.write(readme_content)
            
            # Generate .gitignore
            gitignore_content = self._generate_gitignore(template)
            with open(os.path.join(project_dir, '.gitignore'), 'w', encoding='utf-8') as f:
                f.write(gitignore_content)
            
            # Template-specific files
            if 'web' in stack:
                self._generate_web_files(project_dir, project_name, template)
            
            if any(gui in stack for gui in ['tkinter', 'pyqt5', 'pyqt6', 'pyside2', 'pyside6']):
                self._generate_gui_files(project_dir, project_name, template)
            
            print("✅ Starter files generated")
            return True
            
        except Exception as e:
            print(f"❌ Error generating starter files: {e}")
            return False
    
    def _generate_main_file(self, project_name, template):
        """Generate main.py content based on template"""
        stack = template.get('stack', [])
        template_name = template.get('name', 'Application')
        
        if 'tkinter' in stack:
            return f'''#!/usr/bin/env python3
"""
{project_name} - {template_name}
Generated by PyInstaller Build Tool
"""

import tkinter as tk
from tkinter import ttk, messagebox

class {project_name.replace('-', '_').replace(' ', '_').title()}App:
    def __init__(self, root):
        self.root = root
        self.root.title("{project_name}")
        self.root.geometry("800x600")
        
        self.create_widgets()
    
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Welcome label
        ttk.Label(main_frame, text="Welcome to {project_name}!", 
                 font=("Arial", 16, "bold")).grid(row=0, column=0, pady=20)
        
        # Sample button
        ttk.Button(main_frame, text="Click Me!", 
                  command=self.on_button_click).grid(row=1, column=0, pady=10)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
    
    def on_button_click(self):
        messagebox.showinfo("Hello", "Hello from {project_name}!")

def main():
    root = tk.Tk()
    app = {project_name.replace('-', '_').replace(' ', '_').title()}App(root)
    root.mainloop()

if __name__ == "__main__":
    main()
'''
        
        elif any(qt in stack for qt in ['pyqt5', 'pyqt6', 'pyside2', 'pyside6']):
            if 'pyqt6' in stack:
                imports = "from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox"
            elif 'pyqt5' in stack:
                imports = "from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox"
            elif 'pyside6' in stack:
                imports = "from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox"
            else:  # pyside2
                imports = "from PySide2.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox"
                
            return f'''#!/usr/bin/env python3
"""
{project_name} - {template_name}
Generated by PyInstaller Build Tool
"""

import sys
{imports}

class {project_name.replace('-', '_').replace(' ', '_').title()}Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("{project_name}")
        self.setGeometry(100, 100, 800, 600)
        
        self.setup_ui()
    
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Welcome label
        welcome_label = QLabel("Welcome to {project_name}!")
        welcome_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 20px;")
        layout.addWidget(welcome_label)
        
        # Sample button
        button = QPushButton("Click Me!")
        button.clicked.connect(self.on_button_click)
        layout.addWidget(button)
    
    def on_button_click(self):
        QMessageBox.information(self, "Hello", "Hello from {project_name}!")

def main():
    app = QApplication(sys.argv)
    window = {project_name.replace('-', '_').replace(' ', '_').title()}Window()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
'''
        
        elif 'fastapi' in stack:
            return f'''#!/usr/bin/env python3
"""
{project_name} - {template_name}
Generated by PyInstaller Build Tool
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import os

app = FastAPI(
    title="{project_name}",
    description="{template['description']}",
    version="1.0.0"
)

# Mount static files
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return """
    <html>
        <head>
            <title>{project_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                h1 {{ color: #333; }}
                .container {{ max-width: 800px; margin: 0 auto; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Welcome to {project_name}!</h1>
                <p>Your FastAPI application is running successfully.</p>
                <p><a href="/docs">View API Documentation</a></p>
            </div>
        </body>
    </html>
    """

@app.get("/api/hello")
async def hello():
    return {{"message": "Hello from {project_name}!"}}

@app.get("/health")
async def health_check():
    return {{"status": "healthy", "service": "{project_name}"}}

def main():
    print("Starting {project_name}...")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

if __name__ == "__main__":
    main()
'''
        
        else:  # Default template
            return f'''#!/usr/bin/env python3
"""
{project_name} - {template_name}
Generated by PyInstaller Build Tool
"""

def main():
    print("Welcome to {project_name}!")
    print("This is a basic Python application.")
    
    # Your application code here
    name = input("Enter your name: ")
    print(f"Hello, {{name}}! Welcome to {project_name}.")

if __name__ == "__main__":
    main()
'''
    
    def _generate_readme(self, project_name, template):
        """Generate README.md content"""
        stack_str = " + ".join(template.get('stack', ['python']))
        requirements_str = ", ".join(template.get('requirements', ['pyinstaller']))
        
        return f'''# {project_name}

{template['description']}

## Stack
- {stack_str}

## Installation

1. Activate the virtual environment:
   ```bash
   # Windows
   {project_name}_env\\Scripts\\activate
   
   # Linux/Mac
   source {project_name}_env/bin/activate
   ```

2. Install dependencies (already done during project creation):
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the application:
```bash
python main.py
```

## Building Executable

Build with PyInstaller using the build tool:
```bash
# Development build
python ../build_cli.py --profile dev --start build

# Production build  
python ../build_cli.py --profile prod --start build
```

## Project Structure

```
{project_name}/
├── main.py                 # Main application entry point
├── src/                    # Source code modules
├── assets/                 # Application assets
├── requirements.txt        # Python dependencies
├── {project_name}_env/     # Virtual environment
└── README.md              # This file
```

## Dependencies

{requirements_str}

## Generated by

PyInstaller Build Tool - Template: {template.get('name', 'Default')}
'''
    
    def _generate_gitignore(self, template):
        """Generate .gitignore content"""
        base_ignore = '''# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# Virtual environment
*_env/
venv/
.venv/

# PyInstaller
build/
dist/
*.spec

# IDE files
.vscode/
.idea/
*.swp
*.swo

# OS files
.DS_Store
Thumbs.db

# Logs
*.log
'''
        
        stack = template.get('stack', [])
        
        if any(qt in stack for qt in ['pyqt5', 'pyqt6', 'pyside2', 'pyside6']):
            base_ignore += '''
# Qt files
*.qrc
*.ui~
'''
        
        if 'web' in stack:
            base_ignore += '''
# Web files
node_modules/
*.min.js
*.min.css
'''
        
        return base_ignore
    
    def _generate_web_files(self, project_dir, project_name, template):
        """Generate web-specific template files"""
        # Create basic HTML template
        html_content = f'''<!DOCTYPE html>
<html>
<head>
    <title>{project_name}</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <div class="container">
        <h1>Welcome to {project_name}!</h1>
        <p>Your web application is running successfully.</p>
    </div>
    <script src="/static/js/app.js"></script>
</body>
</html>
'''
        
        templates_dir = os.path.join(project_dir, 'templates')
        with open(os.path.join(templates_dir, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Create basic CSS
        css_content = '''body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 0;
    background-color: #f5f5f5;
}

.container {
    max-width: 800px;
    margin: 50px auto;
    padding: 20px;
    background-color: white;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    text-align: center;
}

h1 {
    color: #333;
    margin-bottom: 20px;
}
'''
        
        css_dir = os.path.join(project_dir, 'static', 'css')
        with open(os.path.join(css_dir, 'style.css'), 'w', encoding='utf-8') as f:
            f.write(css_content)
        
        # Create basic JavaScript
        js_content = '''console.log('Application loaded successfully');

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM content loaded');
});
'''
        
        js_dir = os.path.join(project_dir, 'static', 'js')
        with open(os.path.join(js_dir, 'app.js'), 'w', encoding='utf-8') as f:
            f.write(js_content)
    
    def _generate_gui_files(self, project_dir, project_name, template):
        """Generate GUI-specific files"""
        # Create a simple icon placeholder
        icon_text = f'''# Icon placeholder for {project_name}
# Replace this with your actual icon file (.ico, .png)
# Recommended sizes: 16x16, 32x32, 48x48, 256x256
'''
        
        icons_dir = os.path.join(project_dir, 'icons')
        with open(os.path.join(icons_dir, 'icon_placeholder.txt'), 'w', encoding='utf-8') as f:
            f.write(icon_text)
    
    def _create_requirements_file(self, project_dir, template):
        """Create requirements.txt file"""
        try:
            print("\n📄 Creating requirements.txt...")
            
            requirements = template.get('requirements', ['pyinstaller'])
            
            requirements_content = '# Project dependencies\n'
            requirements_content += '# Generated by PyInstaller Build Tool\n\n'
            
            for req in requirements:
                requirements_content += f'{req}\n'
            
            with open(os.path.join(project_dir, 'requirements.txt'), 'w', encoding='utf-8') as f:
                f.write(requirements_content)
            
            print("✅ requirements.txt created")
            return True
            
        except Exception as e:
            print(f"❌ Error creating requirements.txt: {e}")
            return False
    
    def _setup_build_configuration(self, project_dir, project_name, template_name):
        """Set up build configuration for the project"""
        try:
            print("\n🔧 Setting up build configuration...")
            
            # Create a local build configuration file
            build_config = {
                'project_name': project_name,
                'template': template_name,
                'main_file': 'main.py',
                'created': datetime.now().isoformat(),
                'build_tool_version': '2.0.0-enhanced'
            }
            
            with open(os.path.join(project_dir, 'build_config.json'), 'w', encoding='utf-8') as f:
                json.dump(build_config, f, indent=2)
            
            print("✅ Build configuration created")
            return True
            
        except Exception as e:
            print(f"❌ Error setting up build configuration: {e}")
            return False
    
    def _create_dev_scripts(self, project_dir, project_name, venv_name, template):
        """Create development helper scripts"""
        try:
            print("\n📜 Creating development scripts...")
            
            # Create run script
            if platform.system() == 'Windows':
                run_script = f'''@echo off
echo Starting {project_name}...
{venv_name}\\Scripts\\python.exe main.py
pause
'''
                with open(os.path.join(project_dir, 'run.bat'), 'w', encoding='utf-8') as f:
                    f.write(run_script)
                
                build_script = f'''@echo off
echo Building {project_name}...
{venv_name}\\Scripts\\python.exe ..\\build_cli.py --template {template.get('name', 'default').lower().replace(' ', '')} --profile prod --start build
pause
'''
                with open(os.path.join(project_dir, 'build.bat'), 'w', encoding='utf-8') as f:
                    f.write(build_script)
            
            else:  # Linux/Mac
                run_script = f'''#!/bin/bash
echo "Starting {project_name}..."
source {venv_name}/bin/activate
python main.py
'''
                with open(os.path.join(project_dir, 'run.sh'), 'w', encoding='utf-8') as f:
                    f.write(run_script)
                os.chmod(os.path.join(project_dir, 'run.sh'), 0o755)
                
                build_script = f'''#!/bin/bash
echo "Building {project_name}..."
source {venv_name}/bin/activate
python ../build_cli.py --template {template.get('name', 'default').lower().replace(' ', '')} --profile prod --start build
'''
                with open(os.path.join(project_dir, 'build.sh'), 'w', encoding='utf-8') as f:
                    f.write(build_script)
                os.chmod(os.path.join(project_dir, 'build.sh'), 0o755)
            
            print("✅ Development scripts created")
            return True
            
        except Exception as e:
            print(f"❌ Error creating development scripts: {e}")
            return False

def handle_new_project_command():
    """Handle new project creation with template and virtual environment"""
    try:
        print("🚀 New Project Creator")
        print("=" * 30)
        
        # Parse command line arguments
        project_name = None
        template_name = 'default'
        project_dir = None
        python_version = None
        
        i = 0
        while i < len(sys.argv):
            arg = sys.argv[i]
            
            if arg == '--new-project' and i + 1 < len(sys.argv):
                project_name = sys.argv[i + 1]
                i += 1
            elif arg == '--template' and i + 1 < len(sys.argv):
                template_name = sys.argv[i + 1]
                i += 1
            elif arg in ['--dir', '--target', '--location'] and i + 1 < len(sys.argv):
                project_dir = sys.argv[i + 1]
                i += 1
            elif arg == '--python-version' and i + 1 < len(sys.argv):
                python_version = sys.argv[i + 1]
                i += 1
            
            i += 1
        
        # Interactive mode if no project name provided
        if not project_name:
            project_name = input("Enter project name: ").strip()
            if not project_name:
                print("❌ Project name is required")
                return False
        
        # Show template selection if default
        if template_name == 'default':
            print("\n📋 Available templates:")
            template_manager = ProjectTemplateManager()
            template_manager.list_templates()
            
            template_choice = input("\nEnter template name (or press Enter for 'default'): ").strip()
            if template_choice:
                template_name = template_choice
        
        # Create the project
        creator = ProjectCreator()
        return creator.create_project(project_name, template_name, project_dir, python_version)
        
    except Exception as e:
        print(f"❌ Error in new project creation: {e}")
        return False

def handle_template_command():
    """Handle template command"""
    try:
        template_manager = ProjectTemplateManager()
        memory = ConsoleMemory()
        
        # Parse template name from arguments
        template_name = None
        for i, arg in enumerate(sys.argv):
            if arg == '--template' and i + 1 < len(sys.argv):
                template_name = sys.argv[i + 1]
                break
        
        # If no template specified, show current or list available
        if not template_name:
            print("📋 Project Template Manager")
            print("=" * 35)
            
            # Show current template if any
            template_manager.show_current_template(memory)
            print()
            
            # List available templates
            template_manager.list_templates()
            
            print("\n💡 Usage:")
            print("   python build_cli.py --template tkinter")
            print("   python build_cli.py --template pyqt6")
            print("   python build_cli.py --template fastapi")
            print("   python build_cli.py --template auto      # Auto-detect")
            
            return True
        
        # Special case: show current template
        if template_name.lower() in ['current', 'show', 'status']:
            template_manager.show_current_template(memory)
            return True
        
        # Special case: list templates
        if template_name.lower() in ['list', 'ls', 'all']:
            template_manager.list_templates()
            return True
        
        # Special case: auto-detect template
        if template_name.lower() in ['auto', 'detect', 'auto-detect']:
            detected = template_manager.auto_detect_template()
            print(f"🔍 Auto-detected template: {detected}")
            if template_manager.apply_template(detected, memory):
                print("✅ Auto-detected template applied successfully!")
                return True
            else:
                return False
        
        # Apply the specified template
        if template_manager.apply_template(template_name, memory):
            print()
            print("💡 Template applied! Use with build commands:")
            print(f"   python build_cli.py --start build    # Build with {template_name} template")
            print(f"   python build_cli.py --template current # Show current settings")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"❌ Error handling template command: {e}")
        return False

# ============================================================================
# BUILD PROFILE SYSTEM
# ============================================================================

class BuildProfileManager:
    """Manages build profiles (dev, prod, debug) with different default configurations"""
    
    def __init__(self):
        self.profiles = {
            'dev': {
                'name': 'Development',
                'description': 'Fast development builds with debugging enabled',
                'console': True,              # Keep console window
                'upx': False,                 # No UPX compression (faster builds)
                'debug_logs': True,           # Embed debug logging
                'assert_hooks': True,         # Include assertion hooks
                'strip_symbols': False,       # Keep symbols for debugging
                'optimize': 0,                # No optimization (O0)
                'bundle_type': 'onedir',      # Directory bundle (faster)
                'include_tests': True,        # Include test files
                'verbose': True,              # Verbose PyInstaller output
                'manifest_template': 'dev',   # Development manifest
                'sign_code': False,           # No code signing for dev
                'collect_data': True,         # Collect all data files
                'hidden_imports_mode': 'aggressive',  # Include all possible imports
                'runtime_tmpdir': None,       # Use system temp
                'prefer_binary': True,        # Use binary wheels when available
            },
            'prod': {
                'name': 'Production',
                'description': 'Optimized production builds for distribution',
                'console': False,             # No console window (windowed)
                'upx': True,                  # UPX compression for smaller size
                'debug_logs': False,          # No debug logging
                'assert_hooks': False,        # Remove assertions
                'strip_symbols': True,        # Strip debug symbols
                'optimize': 2,                # Full optimization (O2)
                'bundle_type': 'onefile',     # Single executable
                'include_tests': False,       # Exclude test files
                'verbose': False,             # Quiet build
                'manifest_template': 'prod',  # Production manifest
                'sign_code': True,            # Enable code signing
                'collect_data': False,        # Only essential data files
                'hidden_imports_mode': 'conservative',  # Only required imports
                'runtime_tmpdir': None,       # Use system temp
                'prefer_binary': True,        # Use binary wheels
            },
            'debug': {
                'name': 'Debug',
                'description': 'Maximum debugging information for troubleshooting',
                'console': True,              # Keep console for debug output
                'upx': False,                 # No compression (preserve debug info)
                'debug_logs': True,           # Maximum debug logging
                'assert_hooks': True,         # Keep all assertions
                'strip_symbols': False,       # Keep all debug symbols
                'optimize': 0,                # No optimization
                'bundle_type': 'onedir',      # Directory for easier debugging
                'include_tests': True,        # Include test files
                'verbose': True,              # Maximum verbosity
                'manifest_template': 'debug', # Debug manifest with extra info
                'sign_code': False,           # No signing (can interfere with debugging)
                'collect_data': True,         # Collect all possible data
                'hidden_imports_mode': 'aggressive',  # Include everything
                'runtime_tmpdir': './debug_temp',  # Local debug temp directory
                'prefer_binary': False,       # Use source when possible for debugging
            },
            'release': {
                'name': 'Release',
                'description': 'Final release builds with maximum optimization',
                'console': False,             # No console window
                'upx': True,                  # Maximum compression
                'debug_logs': False,          # No debug logs
                'assert_hooks': False,        # Remove assertions
                'strip_symbols': True,        # Strip all symbols
                'optimize': 2,                # Maximum optimization
                'bundle_type': 'onefile',     # Single file distribution
                'include_tests': False,       # No test files
                'verbose': False,             # Quiet build
                'manifest_template': 'release',  # Release manifest
                'sign_code': True,            # Code signing required
                'collect_data': False,        # Minimal data collection
                'hidden_imports_mode': 'minimal',  # Only essential imports
                'runtime_tmpdir': None,       # System temp
                'prefer_binary': True,        # Binary wheels only
            },
            'test': {
                'name': 'Testing',
                'description': 'Testing builds with test frameworks included',
                'console': True,              # Console for test output
                'upx': False,                 # No compression for faster testing
                'debug_logs': True,           # Debug logs for test debugging
                'assert_hooks': True,         # Keep assertions for testing
                'strip_symbols': False,       # Keep symbols for test debugging
                'optimize': 0,                # No optimization
                'bundle_type': 'onedir',      # Directory for test file access
                'include_tests': True,        # Include all test files
                'verbose': True,              # Verbose for test debugging
                'manifest_template': 'test',  # Test manifest
                'sign_code': False,           # No signing for tests
                'collect_data': True,         # Collect test data
                'hidden_imports_mode': 'testing',  # Include test frameworks
                'runtime_tmpdir': './test_temp',  # Test temp directory
                'prefer_binary': True,        # Binary wheels for consistency
            }
        }
        
        self.current_profile = None
    
    def list_profiles(self):
        """List all available profiles"""
        print("🎯 Available Build Profiles:")
        print("=" * 40)
        
        for profile_name, config in self.profiles.items():
            print(f"\n📋 {profile_name.upper()} - {config['name']}")
            print(f"   {config['description']}")
            print(f"   Console: {'✅' if config['console'] else '❌'} | "
                  f"UPX: {'✅' if config['upx'] else '❌'} | "
                  f"Debug: {'✅' if config['debug_logs'] else '❌'} | "
                  f"Bundle: {config['bundle_type']}")
    
    def get_profile(self, profile_name):
        """Get profile configuration"""
        profile_name = profile_name.lower()
        if profile_name in self.profiles:
            return self.profiles[profile_name]
        else:
            available = ', '.join(self.profiles.keys())
            raise ValueError(f"Unknown profile '{profile_name}'. Available: {available}")
    
    def apply_profile(self, profile_name, memory=None):
        """Apply profile configuration to build memory"""
        try:
            profile = self.get_profile(profile_name)
            self.current_profile = profile_name
            
            if memory is None:
                memory = ConsoleMemory()
            
            # Apply profile settings to build config
            config = memory.get_config()
            
            # Core build settings
            config['profile'] = profile_name
            config['windowed'] = not profile['console']  # Invert console setting
            config['bundle_type'] = profile['bundle_type']
            config['optimize_level'] = profile['optimize']
            config['verbose_build'] = profile['verbose']
            
            # Compression and optimization
            config['use_upx'] = profile['upx']
            config['strip_symbols'] = profile['strip_symbols']
            
            # Debug and development settings
            config['debug_logs'] = profile['debug_logs']
            config['include_assertions'] = profile['assert_hooks']
            config['include_tests'] = profile['include_tests']
            
            # Data collection settings
            config['collect_data_aggressive'] = profile['collect_data']
            config['hidden_imports_mode'] = profile['hidden_imports_mode']
            
            # Code signing
            config['enable_code_signing'] = profile['sign_code']
            
            # Runtime settings
            config['runtime_tmpdir'] = profile['runtime_tmpdir']
            config['prefer_binary_wheels'] = profile['prefer_binary']
            
            # Manifest template
            config['manifest_template'] = profile['manifest_template']
            
            # Store updated config
            memory.store_config(config)
            
            print(f"✅ Applied profile: {profile['name']} ({profile_name})")
            print(f"   {profile['description']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error applying profile: {e}")
            return False
    
    def show_current_profile(self, memory=None):
        """Show currently active profile settings"""
        if memory is None:
            memory = ConsoleMemory()
            
        config = memory.get_config()
        current_profile = config.get('profile')
        
        if current_profile:
            profile = self.get_profile(current_profile)
            print(f"🎯 Current Profile: {profile['name']} ({current_profile})")
            print(f"   {profile['description']}")
            print()
            print("📋 Active Settings:")
            print(f"   Console Window: {'✅ Enabled' if not config.get('windowed', False) else '❌ Disabled'}")
            print(f"   UPX Compression: {'✅ Enabled' if config.get('use_upx', False) else '❌ Disabled'}")
            print(f"   Debug Logs: {'✅ Enabled' if config.get('debug_logs', False) else '❌ Disabled'}")
            print(f"   Assertions: {'✅ Included' if config.get('include_assertions', True) else '❌ Stripped'}")
            print(f"   Bundle Type: {config.get('bundle_type', 'onedir')}")
            print(f"   Optimization: Level {config.get('optimize_level', 0)}")
            print(f"   Code Signing: {'✅ Enabled' if config.get('enable_code_signing', False) else '❌ Disabled'}")
        else:
            print("⚠️ No profile currently active")
            print("💡 Use --profile <name> to set a profile")
    
    def generate_pyinstaller_args(self, config):
        """Generate PyInstaller arguments based on profile settings"""
        args = []
        
        # Console/windowed mode
        if config.get('windowed', False):
            args.append('--windowed')
        else:
            args.append('--console')
        
        # Bundle type
        bundle_type = config.get('bundle_type', 'onedir')
        if bundle_type == 'onefile':
            args.append('--onefile')
        else:
            args.append('--onedir')
        
        # UPX compression
        if config.get('use_upx', False):
            args.append('--upx-dir')  # Will be set to UPX path if available
        else:
            args.append('--noupx')
        
        # Debug settings
        if config.get('debug_logs', False):
            args.extend(['--debug', 'all'])
        
        # Optimization level
        optimize = config.get('optimize_level', 0)
        if optimize > 0:
            args.extend(['-O', str(optimize)])
        
        # Strip symbols
        if config.get('strip_symbols', False):
            args.append('--strip')
        
        # Verbose mode
        if config.get('verbose_build', False):
            args.append('--verbose')
        
        # Runtime temp directory
        runtime_tmpdir = config.get('runtime_tmpdir')
        if runtime_tmpdir:
            args.extend(['--runtime-tmpdir', runtime_tmpdir])
        
        return args

def handle_profile_command():
    """Handle profile command"""
    try:
        profile_manager = BuildProfileManager()
        memory = ConsoleMemory()
        
        # Parse profile name from arguments
        profile_name = None
        for i, arg in enumerate(sys.argv):
            if arg == '--profile' and i + 1 < len(sys.argv):
                profile_name = sys.argv[i + 1]
                break
        
        # If no profile specified, show current or list available
        if not profile_name:
            print("🎯 Build Profile Manager")
            print("=" * 30)
            
            # Show current profile if any
            profile_manager.show_current_profile(memory)
            print()
            
            # List available profiles
            profile_manager.list_profiles()
            
            print("\n💡 Usage:")
            print("   python build_cli.py --profile dev")
            print("   python build_cli.py --profile prod")
            print("   python build_cli.py --profile debug")
            print("   python build_cli.py --profile release")
            print("   python build_cli.py --profile test")
            
            return True
        
        # Special case: show current profile
        if profile_name.lower() in ['current', 'show', 'status']:
            profile_manager.show_current_profile(memory)
            return True
        
        # Special case: list profiles
        if profile_name.lower() in ['list', 'ls', 'all']:
            profile_manager.list_profiles()
            return True
        
        # Apply the specified profile
        if profile_manager.apply_profile(profile_name, memory):
            print()
            print("💡 Profile applied! Use with build commands:")
            print(f"   python build_cli.py --start build    # Build with {profile_name} profile")
            print(f"   python build_cli.py --profile current # Show current settings")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"❌ Error handling profile command: {e}")
        return False

# ============================================================================
# GITHUB ACTIONS CI HELPER AND WHEELHOUSE CACHE
# ============================================================================

class WheelhouseCache:
    """Manages local wheel cache per-Python-ABI for fast repeated CI builds"""
    
    def __init__(self, cache_dir=None):
        if cache_dir is None:
            # Default to .wheelhouse in current directory
            self.cache_dir = os.path.abspath('.wheelhouse')
        else:
            self.cache_dir = os.path.abspath(cache_dir)
        
        # Get Python ABI for cache isolation
        self.python_abi = self._get_python_abi()
        self.abi_cache_dir = os.path.join(self.cache_dir, self.python_abi)
        
        # Ensure cache directory exists
        os.makedirs(self.abi_cache_dir, exist_ok=True)
    
    def _get_python_abi(self):
        """Get Python ABI string for cache isolation"""
        try:
            import sysconfig
            # Get detailed ABI info: platform-python_version-abi_flags
            platform_tag = sysconfig.get_platform().replace('-', '_').replace('.', '_')
            python_version = f"py{sys.version_info.major}{sys.version_info.minor}"
            
            # Get ABI flags if available
            try:
                abiflags = sysconfig.get_config_var('ABIFLAGS') or ''
            except:
                abiflags = ''
            
            return f"{platform_tag}-{python_version}{abiflags}"
        except Exception:
            # Fallback to basic info
            return f"{platform.system().lower()}-py{sys.version_info.major}{sys.version_info.minor}"
    
    def get_pip_cache_args(self):
        """Get pip arguments to use the wheelhouse cache"""
        return [
            '--cache-dir', self.abi_cache_dir,
            '--find-links', self.abi_cache_dir,
            '--prefer-binary'
        ]
    
    def setup_environment(self):
        """Setup environment variables for wheelhouse cache"""
        os.environ['WHEELHOUSE'] = self.cache_dir
        os.environ['PIP_CACHE_DIR'] = self.abi_cache_dir
        os.environ['PIP_FIND_LINKS'] = self.abi_cache_dir
        os.environ['PIP_PREFER_BINARY'] = '1'
        
        print(f"🎯 Wheelhouse cache configured:")
        print(f"   Cache dir: {self.cache_dir}")
        print(f"   Python ABI: {self.python_abi}")
        print(f"   ABI cache: {self.abi_cache_dir}")
    
    def download_wheels(self, requirements_file=None, packages=None):
        """Pre-download wheels to cache"""
        try:
            cmd = [sys.executable, '-m', 'pip', 'wheel', '--wheel-dir', self.abi_cache_dir]
            cmd.extend(self.get_pip_cache_args())
            
            if requirements_file and os.path.exists(requirements_file):
                cmd.extend(['-r', requirements_file])
                print(f"📦 Pre-downloading wheels from {requirements_file}")
            elif packages:
                cmd.extend(packages)
                print(f"📦 Pre-downloading wheels for: {', '.join(packages)}")
            else:
                print("⚠️ No requirements file or packages specified")
                return False
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Wheels downloaded successfully")
                return True
            else:
                print(f"❌ Error downloading wheels: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error setting up wheelhouse cache: {e}")
            return False
    
    def get_cache_info(self):
        """Get information about the wheelhouse cache"""
        info = {
            'cache_dir': self.cache_dir,
            'abi_cache_dir': self.abi_cache_dir,
            'python_abi': self.python_abi,
            'exists': os.path.exists(self.abi_cache_dir),
            'wheel_count': 0,
            'cache_size_mb': 0
        }
        
        if info['exists']:
            try:
                wheel_files = [f for f in os.listdir(self.abi_cache_dir) if f.endswith('.whl')]
                info['wheel_count'] = len(wheel_files)
                
                total_size = 0
                for f in os.listdir(self.abi_cache_dir):
                    file_path = os.path.join(self.abi_cache_dir, f)
                    if os.path.isfile(file_path):
                        total_size += os.path.getsize(file_path)
                
                info['cache_size_mb'] = round(total_size / (1024 * 1024), 2)
            except Exception:
                pass
        
        return info

def handle_ci_github_command():
    """Handle GitHub Actions CI helper command"""
    try:
        print("🚀 GitHub Actions CI Helper")
        print("=" * 40)
        print()
        print("📋 Minimal workflow.yml steps to copy-paste:")
        print()
        print("```yaml")
        print("name: Build with PyInstaller")
        print()
        print("on:")
        print("  push:")
        print("    branches: [ main, develop ]")
        print("  pull_request:")
        print("    branches: [ main ]")
        print()
        print("jobs:")
        print("  build:")
        print("    runs-on: ${{ matrix.os }}")
        print("    strategy:")
        print("      matrix:")
        print("        os: [ubuntu-latest, windows-latest, macos-latest]")
        print("        python-version: ['3.9', '3.10', '3.11', '3.12']")
        print()
        print("    steps:")
        print("    - uses: actions/checkout@v4")
        print("    ")
        print("    - name: Set up Python ${{ matrix.python-version }}")
        print("      uses: actions/setup-python@v4")
        print("      with:")
        print("        python-version: ${{ matrix.python-version }}")
        print("    ")
        print("    # Optional: Cache wheelhouse for fast repeated builds")
        print("    - name: Cache wheelhouse (per Python ABI)")
        print("      uses: actions/cache@v4")
        print("      with:")
        print("        path: .wheelhouse")
        print("        key: wheelhouse-${{ runner.os }}-${{ matrix.python-version }}-${{ hashFiles('**/requirements*.txt', '**/setup.py', '**/pyproject.toml') }}")
        print("        restore-keys: |")
        print("          wheelhouse-${{ runner.os }}-${{ matrix.python-version }}-")
        print("          wheelhouse-${{ runner.os }}-")
        print("    ")
        print("    - name: Install dependencies")
        print("      run: |")
        print("        python -m pip install --upgrade pip")
        print("        pip install pyinstaller")
        print("        if [ -f requirements.txt ]; then pip install -r requirements.txt; fi")
        print("      shell: bash")
        print("    ")
        print("    - name: Setup wheelhouse cache")
        print("      run: python BuildSystem/build_cli.py --setup-wheelhouse")
        print("      shell: bash")
        print("    ")
        print("    - name: Build executable")
        print("      run: python BuildSystem/build_cli.py --start build")
        print("      shell: bash")
        print("      env:")
        print("        PYTHONUTF8: 1")
        print("        WHEELHOUSE: .wheelhouse")
        print("    ")
        print("    - name: Upload artifacts")
        print("      uses: actions/upload-artifact@v4")
        print("      with:")
        print("        name: executable-${{ matrix.os }}-py${{ matrix.python-version }}")
        print("        path: dist/")
        print("```")
        print()
        print("🔧 Environment variables you can set:")
        print("   PYTHONUTF8=1              # Fix encoding issues on Windows")
        print("   WHEELHOUSE=.wheelhouse    # Wheelhouse cache directory")
        print("   PIP_CACHE_DIR=.wheelhouse # Pip cache location")
        print("   PIP_PREFER_BINARY=1       # Prefer binary wheels")
        print("   BUILD_NAME=MyApp          # Custom build name")
        print()
        print("⚡ Wheelhouse cache benefits:")
        print("   • Faster repeated builds (reuse downloaded wheels)")
        print("   • Per-Python-ABI isolation (3.9 vs 3.10, Windows vs Linux)")
        print("   • Reduced network usage and build times")
        print("   • Automatic fallback if cache miss")
        print()
        print("🛠️ Additional CLI commands for CI:")
        print("   python BuildSystem/build_cli.py --setup-wheelhouse     # Setup cache")
        print("   python BuildSystem/build_cli.py --wheelhouse-info      # Cache info")
        print("   python BuildSystem/build_cli.py --force-clean          # Clear caches")
        print("   python BuildSystem/build_cli.py --start build --auto   # Auto-detect build")
        print()
        print("📖 For more info: https://github.com/actions/cache")
        
        return True
        
    except Exception as e:
        print(f"❌ Error showing CI helper: {e}")
        return False

def handle_setup_wheelhouse_command():
    """Handle wheelhouse cache setup"""
    try:
        print("🎯 Setting up Wheelhouse Cache")
        print("=" * 35)
        
        # Initialize wheelhouse cache
        cache = WheelhouseCache()
        cache.setup_environment()
        
        # Try to pre-download common PyInstaller dependencies
        common_packages = [
            'pyinstaller',
            'setuptools',
            'wheel',
            'pip'
        ]
        
        # Check for requirements.txt
        requirements_files = ['requirements.txt', 'requirements-dev.txt', 'pyproject.toml']
        found_requirements = None
        
        for req_file in requirements_files:
            if os.path.exists(req_file):
                found_requirements = req_file
                break
        
        if found_requirements:
            print(f"📄 Found requirements file: {found_requirements}")
            if found_requirements.endswith('.txt'):
                cache.download_wheels(requirements_file=found_requirements)
            else:
                print("⚠️ pyproject.toml detected - install dependencies manually if needed")
        else:
            print("📦 Pre-downloading common packages...")
            cache.download_wheels(packages=common_packages)
        
        # Show cache info
        info = cache.get_cache_info()
        print(f"\n📊 Cache Status:")
        print(f"   Wheel files: {info['wheel_count']}")
        print(f"   Cache size: {info['cache_size_mb']} MB")
        print(f"   Python ABI: {info['python_abi']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up wheelhouse: {e}")
        return False

def handle_wheelhouse_info_command():
    """Handle wheelhouse cache info command"""
    try:
        print("📊 Wheelhouse Cache Information")
        print("=" * 35)
        
        cache = WheelhouseCache()
        info = cache.get_cache_info()
        
        print(f"Cache Directory: {info['cache_dir']}")
        print(f"ABI Cache Directory: {info['abi_cache_dir']}")
        print(f"Python ABI: {info['python_abi']}")
        print(f"Cache Exists: {'✅ Yes' if info['exists'] else '❌ No'}")
        print(f"Wheel Files: {info['wheel_count']}")
        print(f"Cache Size: {info['cache_size_mb']} MB")
        
        # Show environment variables
        print(f"\n🔧 Environment Variables:")
        wheelhouse_env = os.environ.get('WHEELHOUSE', 'Not set')
        pip_cache_env = os.environ.get('PIP_CACHE_DIR', 'Not set')
        
        print(f"   WHEELHOUSE: {wheelhouse_env}")
        print(f"   PIP_CACHE_DIR: {pip_cache_env}")
        
        if info['exists'] and info['wheel_count'] > 0:
            print(f"\n📦 Recent wheel files:")
            try:
                wheel_files = [f for f in os.listdir(info['abi_cache_dir']) if f.endswith('.whl')]
                for whl in sorted(wheel_files)[-5:]:  # Show last 5
                    print(f"   • {whl}")
                if len(wheel_files) > 5:
                    print(f"   ... and {len(wheel_files) - 5} more")
            except Exception:
                pass
        
        print(f"\n💡 Commands:")
        print(f"   python build_cli.py --setup-wheelhouse    # Setup cache")
        print(f"   python build_cli.py --force-clean         # Clear all caches")
        
        return True
        
    except Exception as e:
        print(f"❌ Error getting wheelhouse info: {e}")
        return False

# ============================================================================
# TUI ENHANCEMENT HANDLERS (Pre-execution)
# ============================================================================

def handle_sandbox_status_check():
    """Handle --sandbox-status command to diagnose Windows Sandbox availability"""
    try:
        print("🔍 Windows Sandbox Status Diagnostic")
        print("="*50)
        
        sandbox = WindowsSandboxManager()
        
        # Run detailed validation
        try:
            result = sandbox.validate_windows_environment()
            
            if result:
                print("\n✅ Windows Sandbox appears to be properly configured!")
            else:
                print("\n❌ Windows Sandbox is not properly configured")
                
        except Exception as e:
            print(f"\n❌ Validation failed: {e}")
        
        # Additional checks
        print("\n🔧 Additional Diagnostics:")
        
        # Check file associations
        try:
            result = subprocess.run(['assoc', '.wsb'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"   📋 .wsb file association: {result.stdout.strip()}")
            else:
                print("   ❌ No .wsb file association found")
        except:
            print("   ❌ Could not check .wsb file association")
        
        # Check if Hyper-V is enabled (can conflict with Sandbox)
        try:
            result = subprocess.run([
                'powershell', '-Command',
                'Get-WindowsOptionalFeature -Online -FeatureName "Microsoft-Hyper-V" | Select-Object State'
            ], capture_output=True, text=True, timeout=10)
            
            if 'Enabled' in result.stdout:
                print("   ⚠️  Hyper-V is enabled (may conflict with Windows Sandbox)")
            else:
                print("   ✅ Hyper-V not enabled (good for Sandbox compatibility)")
        except:
            print("   ❓ Could not check Hyper-V status")
        
        # Check Windows version details
        try:
            result = subprocess.run(['systeminfo'], capture_output=True, text=True, timeout=15)
            lines = result.stdout.split('\n')
            for line in lines:
                if 'OS Name' in line or 'OS Version' in line:
                    print(f"   🖥️  {line.strip()}")
        except:
            print("   ❓ Could not get detailed system info")
        
        print("\n💡 Manual Test:")
        print(f"   Try double-clicking: {sandbox.wsb_file}")
        print("   Or run: start WindowsSandbox.exe")
        
        return True
        
    except Exception as e:
        print(f"❌ Status check error: {e}")
        return False

def handle_sandbox_testing():
    """Handle --sandbox command for Windows Sandbox testing environment"""
    try:
        safe_print("🧪 Windows Sandbox Testing System")
        safe_print("="*50)
        
        # Parse sandbox-specific arguments
        config = {
            'venv_name': 'pdf_utility_env',
            'memory_mb': 4096,
            'vgpu': 'Default',
            'networking': 'Default',
            'create_venv': True,
            'test_type': 'smoke',
            'additional_files': [],
            'requirements_file': 'requirements.txt'
        }
        
        # Process command line arguments
        args = sys.argv
        install_only = False
        skip_validation = False
        dry_run = False
        
        for i, arg in enumerate(args):
            if arg == '--venv' and i + 1 < len(args):
                config['venv_name'] = args[i + 1]
            elif arg == '--memory' and i + 1 < len(args):
                try:
                    config['memory_mb'] = int(args[i + 1])
                except ValueError:
                    print(f"[WARN] Invalid memory value: {args[i + 1]}, using default 4096MB")
            elif arg == '--no-vgpu':
                config['vgpu'] = 'Disable'
            elif arg == '--offline':
                config['networking'] = 'Disable'
            elif arg == '--install':
                install_only = True
            elif arg == '--skip-validation':
                skip_validation = True
                print("[WARN] Skipping Windows Sandbox validation (development mode)")
            elif arg == '--dry-run':
                dry_run = True
                print("[TEST] Dry run mode - will create files but not launch sandbox")
            elif arg == '--test-files':
                # Create some dummy test files for demonstration
                test_files = [
                    'test_executable.exe',
                    'test_installer.msi', 
                    'test_config.json',
                    'test_readme.txt'
                ]
                config['additional_files'] = test_files
                print("[TEST] Test files mode - will create dummy files for testing")
            elif arg == '--portable':
                # Create portable test package for Windows Home users
                config['portable_mode'] = True
                print("[PKG] Portable mode - creating standalone test package")
            elif arg == '--dev':
                # Include development files
                dev_files = []
                for ext in ['*.py', '*.json', '*.md', '*.txt']:
                    dev_files.extend(glob.glob(ext))
                config['additional_files'] = dev_files[:20]  # Limit to 20 files
                print(f"[DIR] Including {len(config['additional_files'])} development files")
        
        # Add flags to config for later use
        config['skip_validation'] = skip_validation
        config['dry_run'] = dry_run
        
        # Handle portable mode for Windows Home users
        if config.get('portable_mode', False):
            safe_print("📦 Creating portable test package...")
            sandbox = WindowsSandboxManager()
            return sandbox.create_portable_test_package(config)
        
        # Handle installation-only mode
        if install_only:
            safe_print("🔧 Windows Sandbox Installation Mode")
            safe_print("="*50)
            
            sandbox = WindowsSandboxManager()
            
            # Force installation attempt
            safe_print("🔍 Checking Windows Sandbox status...")
            try:
                result = sandbox.install_windows_sandbox()
                return result
            except Exception as e:
                safe_print(f"❌ Installation failed: {e}")
                return False
        
        # Create and launch sandbox
        success = create_sandbox_test_environment(config)
        
        if success:
            print("\n🎉 Sandbox testing environment created successfully!")
            print("\n💡 Tips:")
            print("• The sandbox will auto-setup Python environment")
            print("• Build files will be copied to Desktop")
            print("• Test scripts will run automatically") 
            print("• Results will be saved as test_report.txt on Desktop")
            print("• Close the sandbox window when testing is complete")
            
            return True
        else:
            print("\n[X] Failed to create sandbox environment")
            return False
            
    except Exception as e:
        print(f"[X] Error in sandbox testing: {e}")
        import traceback
        traceback.print_exc()
        return False

# ============================================================================
# EXECUTION BLOCK
# ============================================================================

if __name__ == "__main__":
    try:
        safe_print(f"DEBUG: sys.argv = {sys.argv}")  # Debug line
        
        # Check if we should use command queue system
        if has_multiple_commands():
            safe_print("DEBUG: Using queue system (multiple commands)")  # Debug line
            # Multiple commands detected - use queue system
            success = process_command_queue()
        elif is_core_command():
            safe_print("DEBUG: Detected core command")  # Debug line
            # Single core command that can be handled by queue system
            
            # Special handling for --new-project command
            if '--new-project' in sys.argv:
                safe_print("DEBUG: Routing to new project handler")  # Debug line
                success = handle_new_project_command()
            # Special handling for --new command  
            elif '--new' in sys.argv:
                safe_print("DEBUG: Routing to new item handler")  # Debug line
                success = handle_new_command()
            else:
                # Commands like --auto, --add, --set-version, etc. should use queue
                queue_commands = {
                    '--add', '--set-version', '--add-to-path',
                    '--virtual', '--activate', '--install-needed',
                    '--export-config', '--downgrade',
                    '--start', '--no-version', '--no-version-append'
                }
                
                if any(cmd in sys.argv for cmd in queue_commands):
                    safe_print("DEBUG: Routing to queue system")  # Debug line
                    # Route to queue system
                    success = process_command_queue()
                else:
                    safe_print("DEBUG: Using main() for core command")  # Debug line
                    # Use regular main() for basic commands
                    success = main()
        else:
            safe_print("DEBUG: Using main() for simple command")  # Debug line
            # Use regular main() for simple commands
            success = main()
            
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        safe_print("\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        # Use ASCII-only output for elevated processes to avoid encoding issues
        error_msg = str(e).encode('ascii', 'ignore').decode('ascii')
        try:
            print(f"[X] Unexpected error: {error_msg}")
        except:
            print("ERROR: Unexpected error occurred (encoding issue prevented display)")
        sys.exit(1)

# ============================================================================
# TUI ENHANCEMENT HANDLERS
# ============================================================================

def handle_progress_status():
    """Handle --progress command for GUI and CLI progress querying"""
    try:
        progress = progress_tracker.get_progress()
        
        if '--json' in sys.argv:
            # JSON output for GUI consumption
            print(json.dumps(progress, indent=2))
        else:
            # Human-readable output for CLI
            print("🔄 Build Progress Status")
            print("=" * 40)
            print(f"Status: {progress['status']}")
            print(f"Operation: {progress['operation']}")
            
            if progress['status'] == 'running':
                print(f"Progress: {progress['progress_percent']:.1f}%")
                TUIEnhancements.show_progress_bar(
                    progress['current_step'], 
                    progress['total_steps'],
                    task=progress['current_task']
                )
                
                if progress['subtask']:
                    print(f"Subtask: {progress['subtask']}")
                
                if progress['estimated_remaining'] > 0:
                    remaining_mins = progress['estimated_remaining'] / 60
                    print(f"Estimated remaining: {remaining_mins:.1f} minutes")
            
            elif progress['status'] == 'completed':
                print("✅ Last operation completed successfully")
                
            elif progress['status'] == 'error':
                print(f"❌ Last operation failed: {progress.get('error', 'Unknown error')}")
            
            if progress.get('warnings'):
                print(f"⚠️  Warnings: {len(progress['warnings'])}")
                
        return True
        
    except Exception as e:
        print(f"❌ Error getting progress: {e}")
        return False

def handle_command_history():
    """Handle --history command for last-run command recall"""
    try:
        print("📋 Command History")
        print("=" * 40)
        
        history = command_history.get_history(15)
        
        if not history:
            print("No command history available")
            return True
        
        for i, entry in enumerate(history, 1):
            status_icon = "✅" if entry.get('success') else "❌" if entry.get('success') is False else "❓"
            duration = entry.get('duration', 0)
            duration_str = f" ({duration:.1f}s)" if duration else ""
            timestamp = datetime.fromisoformat(entry['timestamp']).strftime("%m/%d %H:%M")
            
            print(f"{i:2}. {status_icon} {entry['command']}{duration_str} - {timestamp}")
            
            if entry.get('args'):
                args_str = ' '.join(str(arg) for arg in entry['args'][:3])
                if len(entry['args']) > 3:
                    args_str += f" ... +{len(entry['args'])-3} more"
                print(f"     Args: {args_str}")
        
        print("\n💡 Use --repeat <number> to repeat a command")
        
        # Handle --repeat flag
        if '--repeat' in sys.argv:
            try:
                repeat_idx = sys.argv.index('--repeat') + 1
                if repeat_idx < len(sys.argv):
                    repeat_num = int(sys.argv[repeat_idx]) - 1
                    if 0 <= repeat_num < len(history):
                        entry = history[repeat_num]
                        print(f"\n🔄 Repeating: {entry['command']}")
                        
                        # Execute the command (simplified - would need full implementation)
                        print("💡 Command repeat functionality would be implemented here")
                        return True
            except (ValueError, IndexError):
                print("❌ Invalid repeat number")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error accessing command history: {e}")
        return False

def handle_interactive_file_selection():
    """Handle --select-files command with searchable interface"""
    try:
        memory = ConsoleMemory()
        scan_results = memory.get_scan_results()
        
        if not scan_results:
            print("❌ No scanned files available. Run --scan first.")
            return False
        
        print("📁 Interactive File Selection")
        print("=" * 40)
        
        # Choose category
        categories = list(scan_results.keys())
        if not categories:
            print("No file categories found")
            return False
        
        print("Available categories:")
        for i, cat in enumerate(categories, 1):
            count = len(scan_results[cat])
            print(f"{i}. {cat} ({count} files)")
        
        try:
            cat_choice = input("\nSelect category (1-{}) or 'all' for all files: ".format(len(categories))).strip()
            
            if cat_choice.lower() == 'all':
                all_files = []
                for files in scan_results.values():
                    all_files.extend(files)
                files_to_search = all_files
                selected_category = "all"
            else:
                cat_idx = int(cat_choice) - 1
                if 0 <= cat_idx < len(categories):
                    selected_category = categories[cat_idx]
                    files_to_search = scan_results[selected_category]
                else:
                    print("Invalid selection")
                    return False
        except ValueError:
            print("Invalid input")
            return False
        
        # Interactive selection
        multi_select = '--multi' in sys.argv
        selected_files = TUIEnhancements.searchable_list(
            files_to_search,
            title=f"Select files from {selected_category}",
            multi_select=multi_select,
            search_prompt="Filter files"
        )
        
        if selected_files:
            if isinstance(selected_files, list):
                print(f"\n✅ Selected {len(selected_files)} files:")
                for f in selected_files[:5]:
                    print(f"  • {os.path.basename(f)}")
                if len(selected_files) > 5:
                    print(f"  ... and {len(selected_files) - 5} more")
            else:
                print(f"\n✅ Selected: {os.path.basename(selected_files)}")
            
            # Option to add to build configuration
            if input("\nAdd to build configuration? (y/n): ").lower() == 'y':
                config = memory.get_config()
                if 'selected_files' not in config:
                    config['selected_files'] = []
                
                if isinstance(selected_files, list):
                    config['selected_files'].extend(selected_files)
                else:
                    config['selected_files'].append(selected_files)
                
                memory.store_config(config)
                print("✅ Added to build configuration")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in file selection: {e}")
        return False

def handle_bulk_operations():
    """Handle --bulk-add command for bulk file operations"""
    try:
        memory = ConsoleMemory()
        scan_results = memory.get_scan_results()
        
        if not scan_results:
            print("❌ No scanned files available. Run --scan first.")
            return False
        
        operation_type = "add"
        if '--remove' in sys.argv:
            operation_type = "remove"
        
        # Get bulk operation selection
        selected_files = TUIEnhancements.bulk_file_operations(scan_results, operation_type)
        
        if not selected_files:
            print("No files selected")
            return True
        
        # Apply the operation
        config = memory.get_config()
        
        if operation_type == "add":
            if 'bulk_added_files' not in config:
                config['bulk_added_files'] = []
            
            config['bulk_added_files'].extend(selected_files)
            print(f"✅ Bulk added {len(selected_files)} files to configuration")
            
        elif operation_type == "remove":
            # Remove from various config lists
            removed_count = 0
            for key in ['bulk_added_files', 'selected_files', 'data_files']:
                if key in config and isinstance(config[key], list):
                    original_len = len(config[key])
                    config[key] = [f for f in config[key] if f not in selected_files]
                    removed_count += original_len - len(config[key])
            
            print(f"✅ Bulk removed {removed_count} file references from configuration")
        
        memory.store_config(config)
        
        return True
        
    except Exception as e:
        print(f"❌ Error in bulk operations: {e}")
        return False
