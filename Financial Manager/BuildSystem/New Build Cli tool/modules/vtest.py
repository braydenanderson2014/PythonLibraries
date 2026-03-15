"""
Virtual Test Environment module for BuildCLI.
Provides integration with Windows Sandbox, VirtualBox, and other virtualization platforms.
"""

import os
import sys
import json
import asyncio
import subprocess
import tempfile
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Callable, Optional, Tuple
import uuid
import time


MODULE_INFO = {
    'name': 'vtest',
    'version': '1.0.0',
    'description': 'Virtual test environments for BuildCLI using Windows Sandbox, VirtualBox, etc.',
    'author': 'BuildCLI',
    'commands': [
        'vtest-create', 'vtest-list', 'vtest-start', 'vtest-stop', 'vtest-delete',
        'vtest-run', 'vtest-copy', 'vtest-status', 'vtest-templates', 'vtest-export',
        'sandbox-create', 'sandbox-run', 'vbox-create', 'vbox-run', 'vtest-config'
    ]
}


class VirtualTestManager:
    """Manages virtual test environments across different platforms."""
    
    def __init__(self, config_manager):
        self.config = config_manager
        self.vtest_dir = Path.home() / ".buildcli" / "vtest"
        self.templates_dir = self.vtest_dir / "templates"
        self.instances_dir = self.vtest_dir / "instances"
        
        # Ensure directories exist
        self.vtest_dir.mkdir(parents=True, exist_ok=True)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.instances_dir.mkdir(parents=True, exist_ok=True)
        
        # Platform capabilities
        self.platforms = {
            'windows_sandbox': WindowsSandboxManager(self),
            'virtualbox': VirtualBoxManager(self),
            'hyper_v': HyperVManager(self),
            'docker': DockerManager(self)
        }
    
    async def detect_available_platforms(self) -> Dict[str, bool]:
        """Detect which virtualization platforms are available."""
        availability = {}
        
        for platform_name, manager in self.platforms.items():
            try:
                availability[platform_name] = await manager.is_available()
            except Exception as e:
                print(f"Error checking {platform_name}: {e}")
                availability[platform_name] = False
        
        return availability
    
    async def create_environment(self, name: str, platform: str, template: Optional[str] = None, **kwargs) -> bool:
        """Create a new virtual test environment."""
        if platform not in self.platforms:
            print(f"Unsupported platform: {platform}")
            print(f"Available platforms: {', '.join(self.platforms.keys())}")
            return False
        
        manager = self.platforms[platform]
        
        if not await manager.is_available():
            print(f"Platform {platform} is not available on this system")
            return False
        
        print(f"Creating virtual test environment '{name}' using {platform}...")
        
        try:
            success = await manager.create_environment(name, template, **kwargs)
            
            if success:
                # Store environment metadata
                env_info = {
                    'name': name,
                    'platform': platform,
                    'template': template,
                    'created_date': self._get_current_timestamp(),
                    'status': 'created',
                    'config': kwargs
                }
                
                self._save_environment_info(name, env_info)
                print(f"✓ Virtual test environment '{name}' created successfully")
            
            return success
        
        except Exception as e:
            print(f"Error creating environment: {e}")
            return False
    
    async def list_environments(self) -> List[Dict[str, Any]]:
        """List all virtual test environments."""
        environments = []
        
        if not self.instances_dir.exists():
            return environments
        
        for env_dir in self.instances_dir.iterdir():
            if env_dir.is_dir():
                info = self._load_environment_info(env_dir.name)
                if info:
                    # Update status from platform
                    platform = info.get('platform')
                    if platform in self.platforms:
                        try:
                            status = await self.platforms[platform].get_status(env_dir.name)
                            info['status'] = status
                        except Exception:
                            info['status'] = 'unknown'
                    
                    environments.append(info)
        
        return environments
    
    async def start_environment(self, name: str) -> bool:
        """Start a virtual test environment."""
        env_info = self._load_environment_info(name)
        if not env_info:
            print(f"Environment '{name}' not found")
            return False
        
        platform = env_info.get('platform')
        if platform not in self.platforms:
            print(f"Platform {platform} not supported")
            return False
        
        manager = self.platforms[platform]
        print(f"Starting environment '{name}' on {platform}...")
        
        try:
            success = await manager.start_environment(name)
            if success:
                print(f"✓ Environment '{name}' started successfully")
            return success
        except Exception as e:
            print(f"Error starting environment: {e}")
            return False
    
    async def stop_environment(self, name: str) -> bool:
        """Stop a virtual test environment."""
        env_info = self._load_environment_info(name)
        if not env_info:
            print(f"Environment '{name}' not found")
            return False
        
        platform = env_info.get('platform')
        if platform not in self.platforms:
            print(f"Platform {platform} not supported")
            return False
        
        manager = self.platforms[platform]
        print(f"Stopping environment '{name}' on {platform}...")
        
        try:
            success = await manager.stop_environment(name)
            if success:
                print(f"✓ Environment '{name}' stopped successfully")
            return success
        except Exception as e:
            print(f"Error stopping environment: {e}")
            return False
    
    async def delete_environment(self, name: str, force: bool = False) -> bool:
        """Delete a virtual test environment."""
        env_info = self._load_environment_info(name)
        if not env_info:
            print(f"Environment '{name}' not found")
            return False
        
        if not force:
            print(f"This will permanently delete environment '{name}'")
            print("Use --force to confirm deletion")
            return False
        
        platform = env_info.get('platform')
        if platform in self.platforms:
            manager = self.platforms[platform]
            try:
                await manager.delete_environment(name)
            except Exception as e:
                print(f"Warning: Error cleaning up platform resources: {e}")
        
        # Remove local metadata
        env_dir = self.instances_dir / name
        if env_dir.exists():
            shutil.rmtree(env_dir)
        
        print(f"✓ Environment '{name}' deleted successfully")
        return True
    
    async def run_command_in_environment(self, name: str, command: str, **kwargs) -> bool:
        """Run a command inside a virtual test environment."""
        env_info = self._load_environment_info(name)
        if not env_info:
            print(f"Environment '{name}' not found")
            return False
        
        platform = env_info.get('platform')
        if platform not in self.platforms:
            print(f"Platform {platform} not supported")
            return False
        
        manager = self.platforms[platform]
        print(f"Running command in '{name}': {command}")
        
        try:
            return await manager.run_command(name, command, **kwargs)
        except Exception as e:
            print(f"Error running command: {e}")
            return False
    
    async def copy_files_to_environment(self, name: str, source: str, destination: str) -> bool:
        """Copy files to a virtual test environment."""
        env_info = self._load_environment_info(name)
        if not env_info:
            print(f"Environment '{name}' not found")
            return False
        
        platform = env_info.get('platform')
        if platform not in self.platforms:
            print(f"Platform {platform} not supported")
            return False
        
        manager = self.platforms[platform]
        print(f"Copying {source} to {name}:{destination}")
        
        try:
            return await manager.copy_files(name, source, destination)
        except Exception as e:
            print(f"Error copying files: {e}")
            return False
    
    def _save_environment_info(self, name: str, info: Dict[str, Any]) -> None:
        """Save environment information."""
        env_dir = self.instances_dir / name
        env_dir.mkdir(exist_ok=True)
        
        info_file = env_dir / "environment.json"
        with open(info_file, 'w') as f:
            json.dump(info, f, indent=2)
    
    def _load_environment_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Load environment information."""
        info_file = self.instances_dir / name / "environment.json"
        if info_file.exists():
            try:
                with open(info_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return None
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp string."""
        from datetime import datetime
        return datetime.now().isoformat()


class WindowsSandboxManager:
    """Manager for Windows Sandbox environments."""
    
    def __init__(self, parent_manager):
        self.parent = parent_manager
    
    async def is_available(self) -> bool:
        """Check if Windows Sandbox is available."""
        if sys.platform != "win32":
            return False
        
        try:
            # Check if Windows Sandbox is enabled
            result = await asyncio.create_subprocess_exec(
                'powershell', '-Command', 
                'Get-WindowsOptionalFeature -Online -FeatureName "Containers-DisposableClientVM"',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                output = stdout.decode()
                return "State : Enabled" in output
            
        except Exception:
            pass
        
        return False
    
    async def create_environment(self, name: str, template: Optional[str] = None, **kwargs) -> bool:
        """Create a Windows Sandbox configuration."""
        config_dir = self.parent.instances_dir / name
        config_dir.mkdir(exist_ok=True)
        
        # Create sandbox configuration
        config = self._create_sandbox_config(name, **kwargs)
        
        config_file = config_dir / f"{name}.wsb"
        with open(config_file, 'w') as f:
            f.write(config)
        
        print(f"Windows Sandbox configuration created: {config_file}")
        return True
    
    def _create_sandbox_config(self, name: str, **kwargs) -> str:
        """Create Windows Sandbox XML configuration."""
        # Default configuration
        config = {
            'VGpu': kwargs.get('vgpu', 'Default'),
            'Networking': kwargs.get('networking', 'Default'),
            'MappedFolders': kwargs.get('mapped_folders', []),
            'LogonCommand': kwargs.get('logon_command', None),
            'AudioInput': kwargs.get('audio_input', 'Default'),
            'VideoInput': kwargs.get('video_input', 'Default'),
            'ProtectedClient': kwargs.get('protected_client', 'Default'),
            'PrinterRedirection': kwargs.get('printer_redirection', 'Default'),
            'ClipboardRedirection': kwargs.get('clipboard_redirection', 'Default'),
        }
        
        # Build XML configuration
        root = ET.Element('Configuration')
        
        for key, value in config.items():
            if key == 'MappedFolders' and value:
                mapped_folders = ET.SubElement(root, 'MappedFolders')
                for folder in value:
                    mapped_folder = ET.SubElement(mapped_folders, 'MappedFolder')
                    host_folder = ET.SubElement(mapped_folder, 'HostFolder')
                    host_folder.text = folder.get('host')
                    sandbox_folder = ET.SubElement(mapped_folder, 'SandboxFolder')
                    sandbox_folder.text = folder.get('sandbox', 'C:\\Shared')
                    read_only = ET.SubElement(mapped_folder, 'ReadOnly')
                    read_only.text = str(folder.get('readonly', False)).lower()
            elif key == 'LogonCommand' and value:
                logon_command = ET.SubElement(root, 'LogonCommand')
                command = ET.SubElement(logon_command, 'Command')
                command.text = value.get('command', 'cmd.exe')
            elif value != 'Default' and value is not None:
                element = ET.SubElement(root, key)
                element.text = str(value)
        
        # Convert to string
        return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding='unicode')
    
    async def start_environment(self, name: str) -> bool:
        """Start Windows Sandbox with configuration."""
        config_file = self.parent.instances_dir / name / f"{name}.wsb"
        
        if not config_file.exists():
            print(f"Sandbox configuration not found: {config_file}")
            return False
        
        try:
            # Start Windows Sandbox
            process = await asyncio.create_subprocess_exec(
                'WindowsSandbox.exe', str(config_file),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            print(f"Windows Sandbox started with PID: {process.pid}")
            return True
        
        except Exception as e:
            print(f"Failed to start Windows Sandbox: {e}")
            return False
    
    async def stop_environment(self, name: str) -> bool:
        """Stop Windows Sandbox (close all sandbox processes)."""
        try:
            # Kill all WindowsSandbox processes
            await asyncio.create_subprocess_exec(
                'taskkill', '/F', '/IM', 'WindowsSandbox.exe',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            return True
        except Exception:
            return False
    
    async def delete_environment(self, name: str) -> bool:
        """Delete Windows Sandbox configuration."""
        config_file = self.parent.instances_dir / name / f"{name}.wsb"
        if config_file.exists():
            config_file.unlink()
        return True
    
    async def get_status(self, name: str) -> str:
        """Get Windows Sandbox status."""
        try:
            result = await asyncio.create_subprocess_exec(
                'tasklist', '/FI', 'IMAGENAME eq WindowsSandbox.exe',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                output = stdout.decode()
                if "WindowsSandbox.exe" in output:
                    return "running"
            
            return "stopped"
        
        except Exception:
            return "unknown"
    
    async def run_command(self, name: str, command: str, **kwargs) -> bool:
        """Run command in Windows Sandbox (limited capability)."""
        print("Note: Direct command execution in Windows Sandbox requires additional setup")
        print("Consider using mapped folders to share scripts and results")
        return True
    
    async def copy_files(self, name: str, source: str, destination: str) -> bool:
        """Copy files to Windows Sandbox (via mapped folders)."""
        print("Note: File copying to Windows Sandbox should be configured via mapped folders")
        print("Update the sandbox configuration to include the required folder mappings")
        return True


class VirtualBoxManager:
    """Manager for VirtualBox environments."""
    
    def __init__(self, parent_manager):
        self.parent = parent_manager
    
    async def is_available(self) -> bool:
        """Check if VirtualBox is available."""
        try:
            result = await asyncio.create_subprocess_exec(
                'vboxmanage', '--version',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            return result.returncode == 0
        
        except Exception:
            return False
    
    async def create_environment(self, name: str, template: Optional[str] = None, **kwargs) -> bool:
        """Create a VirtualBox VM."""
        try:
            # Create VM
            await asyncio.create_subprocess_exec(
                'vboxmanage', 'createvm', '--name', name, '--register',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Configure VM
            memory = kwargs.get('memory', '2048')
            cpus = kwargs.get('cpus', '2')
            
            await asyncio.create_subprocess_exec(
                'vboxmanage', 'modifyvm', name, 
                '--memory', memory, '--cpus', cpus,
                '--boot1', 'dvd', '--boot2', 'disk', '--boot3', 'none', '--boot4', 'none',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Create hard disk if specified
            disk_size = kwargs.get('disk_size', '20480')  # 20GB default
            if disk_size:
                disk_path = self.parent.instances_dir / name / f"{name}.vdi"
                disk_path.parent.mkdir(exist_ok=True)
                
                await asyncio.create_subprocess_exec(
                    'vboxmanage', 'createhd', '--filename', str(disk_path), 
                    '--size', disk_size, '--format', 'VDI',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                # Attach disk
                await asyncio.create_subprocess_exec(
                    'vboxmanage', 'storagectl', name, '--name', 'SATA', 
                    '--add', 'sata', '--controller', 'IntelAhci',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                await asyncio.create_subprocess_exec(
                    'vboxmanage', 'storageattach', name, '--storagectl', 'SATA',
                    '--port', '0', '--device', '0', '--type', 'hdd', '--medium', str(disk_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
            
            return True
        
        except Exception as e:
            print(f"Failed to create VirtualBox VM: {e}")
            return False
    
    async def start_environment(self, name: str) -> bool:
        """Start VirtualBox VM."""
        try:
            await asyncio.create_subprocess_exec(
                'vboxmanage', 'startvm', name, '--type', 'gui',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            return True
        except Exception as e:
            print(f"Failed to start VirtualBox VM: {e}")
            return False
    
    async def stop_environment(self, name: str) -> bool:
        """Stop VirtualBox VM."""
        try:
            await asyncio.create_subprocess_exec(
                'vboxmanage', 'controlvm', name, 'acpipowerbutton',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            return True
        except Exception as e:
            print(f"Failed to stop VirtualBox VM: {e}")
            return False
    
    async def delete_environment(self, name: str) -> bool:
        """Delete VirtualBox VM."""
        try:
            # Stop VM first
            await self.stop_environment(name)
            
            # Wait a bit for shutdown
            await asyncio.sleep(5)
            
            # Force power off if still running
            await asyncio.create_subprocess_exec(
                'vboxmanage', 'controlvm', name, 'poweroff',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Unregister and delete
            await asyncio.create_subprocess_exec(
                'vboxmanage', 'unregistervm', name, '--delete',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            return True
        except Exception as e:
            print(f"Failed to delete VirtualBox VM: {e}")
            return False
    
    async def get_status(self, name: str) -> str:
        """Get VirtualBox VM status."""
        try:
            result = await asyncio.create_subprocess_exec(
                'vboxmanage', 'showvminfo', name, '--machinereadable',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                output = stdout.decode()
                for line in output.split('\n'):
                    if line.startswith('VMState='):
                        state = line.split('=')[1].strip('"')
                        return state.lower()
            
            return "unknown"
        
        except Exception:
            return "unknown"
    
    async def run_command(self, name: str, command: str, **kwargs) -> bool:
        """Run command in VirtualBox VM."""
        username = kwargs.get('username', 'user')
        password = kwargs.get('password', '')
        
        try:
            result = await asyncio.create_subprocess_exec(
                'vboxmanage', 'guestcontrol', name, 'run',
                '--username', username, '--password', password,
                '--', command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if stdout:
                print(stdout.decode())
            if stderr:
                print(stderr.decode())
            
            return result.returncode == 0
        
        except Exception as e:
            print(f"Failed to run command in VM: {e}")
            return False
    
    async def copy_files(self, name: str, source: str, destination: str) -> bool:
        """Copy files to VirtualBox VM."""
        try:
            await asyncio.create_subprocess_exec(
                'vboxmanage', 'guestcontrol', name, 'copyto',
                source, destination,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            return True
        except Exception as e:
            print(f"Failed to copy files to VM: {e}")
            return False


class HyperVManager:
    """Manager for Hyper-V environments."""
    
    def __init__(self, parent_manager):
        self.parent = parent_manager
    
    async def is_available(self) -> bool:
        """Check if Hyper-V is available."""
        if sys.platform != "win32":
            return False
        
        try:
            result = await asyncio.create_subprocess_exec(
                'powershell', '-Command', 'Get-WindowsOptionalFeature -Online -FeatureName "Microsoft-Hyper-V-All"',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                output = stdout.decode()
                return "State : Enabled" in output
            
        except Exception:
            pass
        
        return False
    
    async def create_environment(self, name: str, template: Optional[str] = None, **kwargs) -> bool:
        """Create Hyper-V VM."""
        print("Hyper-V VM creation not yet implemented")
        return False
    
    async def start_environment(self, name: str) -> bool:
        """Start Hyper-V VM."""
        print("Hyper-V VM start not yet implemented")
        return False
    
    async def stop_environment(self, name: str) -> bool:
        """Stop Hyper-V VM."""
        print("Hyper-V VM stop not yet implemented")
        return False
    
    async def delete_environment(self, name: str) -> bool:
        """Delete Hyper-V VM."""
        print("Hyper-V VM deletion not yet implemented")
        return False
    
    async def get_status(self, name: str) -> str:
        """Get Hyper-V VM status."""
        return "unknown"
    
    async def run_command(self, name: str, command: str, **kwargs) -> bool:
        """Run command in Hyper-V VM."""
        print("Hyper-V command execution not yet implemented")
        return False
    
    async def copy_files(self, name: str, source: str, destination: str) -> bool:
        """Copy files to Hyper-V VM."""
        print("Hyper-V file copying not yet implemented")
        return False


class DockerManager:
    """Manager for Docker container environments."""
    
    def __init__(self, parent_manager):
        self.parent = parent_manager
    
    async def is_available(self) -> bool:
        """Check if Docker is available."""
        try:
            result = await asyncio.create_subprocess_exec(
                'docker', '--version',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            return result.returncode == 0
        
        except Exception:
            return False
    
    async def create_environment(self, name: str, template: Optional[str] = None, **kwargs) -> bool:
        """Create Docker container."""
        image = template or kwargs.get('image', 'ubuntu:latest')
        
        try:
            # Pull image if needed
            await asyncio.create_subprocess_exec(
                'docker', 'pull', image,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Create container
            cmd = ['docker', 'create', '--name', name]
            
            # Add additional options
            if kwargs.get('interactive', True):
                cmd.extend(['-i', '-t'])
            
            if kwargs.get('ports'):
                for port_mapping in kwargs['ports']:
                    cmd.extend(['-p', port_mapping])
            
            if kwargs.get('volumes'):
                for volume_mapping in kwargs['volumes']:
                    cmd.extend(['-v', volume_mapping])
            
            cmd.append(image)
            
            if kwargs.get('command'):
                cmd.extend(kwargs['command'].split())
            
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            return result.returncode == 0
        
        except Exception as e:
            print(f"Failed to create Docker container: {e}")
            return False
    
    async def start_environment(self, name: str) -> bool:
        """Start Docker container."""
        try:
            await asyncio.create_subprocess_exec(
                'docker', 'start', name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            return True
        except Exception as e:
            print(f"Failed to start Docker container: {e}")
            return False
    
    async def stop_environment(self, name: str) -> bool:
        """Stop Docker container."""
        try:
            await asyncio.create_subprocess_exec(
                'docker', 'stop', name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            return True
        except Exception as e:
            print(f"Failed to stop Docker container: {e}")
            return False
    
    async def delete_environment(self, name: str) -> bool:
        """Delete Docker container."""
        try:
            # Stop container first
            await self.stop_environment(name)
            
            # Remove container
            await asyncio.create_subprocess_exec(
                'docker', 'rm', name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            return True
        except Exception as e:
            print(f"Failed to delete Docker container: {e}")
            return False
    
    async def get_status(self, name: str) -> str:
        """Get Docker container status."""
        try:
            result = await asyncio.create_subprocess_exec(
                'docker', 'inspect', name, '--format', '{{.State.Status}}',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                return stdout.decode().strip()
            
            return "not found"
        
        except Exception:
            return "unknown"
    
    async def run_command(self, name: str, command: str, **kwargs) -> bool:
        """Run command in Docker container."""
        try:
            cmd = ['docker', 'exec']
            
            if kwargs.get('interactive', True):
                cmd.extend(['-i', '-t'])
            
            cmd.extend([name, 'sh', '-c', command])
            
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if stdout:
                print(stdout.decode())
            if stderr:
                print(stderr.decode())
            
            return result.returncode == 0
        
        except Exception as e:
            print(f"Failed to run command in container: {e}")
            return False
    
    async def copy_files(self, name: str, source: str, destination: str) -> bool:
        """Copy files to Docker container."""
        try:
            await asyncio.create_subprocess_exec(
                'docker', 'cp', source, f"{name}:{destination}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            return True
        except Exception as e:
            print(f"Failed to copy files to container: {e}")
            return False


# Global manager instance
_vtest_manager = None


def get_vtest_manager():
    """Get global virtual test environment manager."""
    global _vtest_manager
    if _vtest_manager is None:
        from core.config import Config
        config = Config()
        _vtest_manager = VirtualTestManager(config)
    return _vtest_manager


# Command implementations
async def vtest_create_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Create virtual test environment command."""
    if len(args) < 2:
        print("Usage: vtest-create <name> <platform> [--template <template>] [options]")
        print("Platforms: windows_sandbox, virtualbox, hyper_v, docker")
        return False
    
    name = args[0]
    platform = args[1]
    template = modifiers.get('template')
    
    if modifiers.get('dry_run', False):
        print(f"[DRY RUN] Would create virtual test environment '{name}' using {platform}")
        return True
    
    # Pass all modifiers as kwargs
    kwargs = {k: v for k, v in modifiers.items() if k not in ['dry_run', 'template']}
    
    manager = get_vtest_manager()
    return await manager.create_environment(name, platform, template, **kwargs)


async def vtest_list_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """List virtual test environments command."""
    manager = get_vtest_manager()
    environments = await manager.list_environments()
    
    if not environments:
        print("No virtual test environments found")
        return True
    
    print(f"Found {len(environments)} virtual test environment(s):")
    print()
    
    for env in environments:
        print(f"  {env['name']} ({env['platform']})")
        print(f"    Status: {env.get('status', 'unknown')}")
        print(f"    Template: {env.get('template', 'default')}")
        print(f"    Created: {env.get('created_date', 'unknown')}")
        print()
    
    return True


async def vtest_start_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Start virtual test environment command."""
    if not args:
        print("Usage: vtest-start <name>")
        return False
    
    name = args[0]
    
    if modifiers.get('dry_run', False):
        print(f"[DRY RUN] Would start virtual test environment '{name}'")
        return True
    
    manager = get_vtest_manager()
    return await manager.start_environment(name)


async def vtest_stop_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Stop virtual test environment command."""
    if not args:
        print("Usage: vtest-stop <name>")
        return False
    
    name = args[0]
    
    if modifiers.get('dry_run', False):
        print(f"[DRY RUN] Would stop virtual test environment '{name}'")
        return True
    
    manager = get_vtest_manager()
    return await manager.stop_environment(name)


async def vtest_delete_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Delete virtual test environment command."""
    if not args:
        print("Usage: vtest-delete <name> [--force]")
        return False
    
    name = args[0]
    force = modifiers.get('force', False)
    
    if modifiers.get('dry_run', False):
        print(f"[DRY RUN] Would delete virtual test environment '{name}'")
        return True
    
    manager = get_vtest_manager()
    return await manager.delete_environment(name, force)


async def vtest_run_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Run command in virtual test environment."""
    if len(args) < 2:
        print("Usage: vtest-run <name> <command>")
        return False
    
    name = args[0]
    command = ' '.join(args[1:])
    
    if modifiers.get('dry_run', False):
        print(f"[DRY RUN] Would run '{command}' in environment '{name}'")
        return True
    
    # Pass modifiers as kwargs for platform-specific options
    kwargs = {k: v for k, v in modifiers.items() if k != 'dry_run'}
    
    manager = get_vtest_manager()
    return await manager.run_command_in_environment(name, command, **kwargs)


async def vtest_copy_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Copy files to virtual test environment."""
    if len(args) < 3:
        print("Usage: vtest-copy <name> <source> <destination>")
        return False
    
    name = args[0]
    source = args[1]
    destination = args[2]
    
    if modifiers.get('dry_run', False):
        print(f"[DRY RUN] Would copy '{source}' to '{name}:{destination}'")
        return True
    
    manager = get_vtest_manager()
    return await manager.copy_files_to_environment(name, source, destination)


async def vtest_status_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Show virtual test environment status."""
    if not args:
        # Show status of all environments
        return await vtest_list_command(args, modifiers)
    
    name = args[0]
    manager = get_vtest_manager()
    
    env_info = manager._load_environment_info(name)
    if not env_info:
        print(f"Environment '{name}' not found")
        return False
    
    platform = env_info.get('platform')
    if platform in manager.platforms:
        try:
            status = await manager.platforms[platform].get_status(name)
            print(f"Environment '{name}' status: {status}")
        except Exception as e:
            print(f"Error getting status: {e}")
            return False
    
    return True


async def vtest_templates_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """List available virtual test environment templates."""
    manager = get_vtest_manager()
    
    print("Available platforms and their capabilities:")
    print()
    
    availability = await manager.detect_available_platforms()
    
    for platform, available in availability.items():
        status = "✓" if available else "✗"
        print(f"  {status} {platform}")
    
    print()
    print("Templates:")
    print("  - Default configurations for each platform")
    print("  - Custom templates can be created in ~/.buildcli/vtest/templates/")
    
    return True


async def vtest_export_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Export virtual test environment configuration."""
    if not args:
        print("Usage: vtest-export <name> [output_file]")
        return False
    
    name = args[0]
    output_file = args[1] if len(args) > 1 else f"{name}_config.json"
    
    manager = get_vtest_manager()
    env_info = manager._load_environment_info(name)
    
    if not env_info:
        print(f"Environment '{name}' not found")
        return False
    
    try:
        with open(output_file, 'w') as f:
            json.dump(env_info, f, indent=2)
        
        print(f"Environment configuration exported to: {output_file}")
        return True
    
    except Exception as e:
        print(f"Error exporting configuration: {e}")
        return False


async def sandbox_create_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Create Windows Sandbox environment (shortcut command)."""
    if not args:
        print("Usage: sandbox-create <name> [options]")
        return False
    
    name = args[0]
    
    # Add platform to args
    new_args = [name, 'windows_sandbox']
    
    return await vtest_create_command(new_args, modifiers)


async def sandbox_run_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Run Windows Sandbox environment (shortcut command)."""
    if not args:
        print("Usage: sandbox-run <name>")
        return False
    
    name = args[0]
    return await vtest_start_command([name], modifiers)


async def vbox_create_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Create VirtualBox environment (shortcut command)."""
    if not args:
        print("Usage: vbox-create <name> [options]")
        return False
    
    name = args[0]
    
    # Add platform to args
    new_args = [name, 'virtualbox']
    
    return await vtest_create_command(new_args, modifiers)


async def vbox_run_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Run VirtualBox environment (shortcut command)."""
    if not args:
        print("Usage: vbox-run <name>")
        return False
    
    name = args[0]
    return await vtest_start_command([name], modifiers)


async def vtest_config_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Show virtual test environment configuration."""
    manager = get_vtest_manager()
    
    print("Virtual Test Environment System Configuration:")
    print()
    print(f"Base directory: {manager.vtest_dir}")
    print(f"Templates directory: {manager.templates_dir}")
    print(f"Instances directory: {manager.instances_dir}")
    print()
    
    availability = await manager.detect_available_platforms()
    
    print("Platform availability:")
    for platform, available in availability.items():
        status = "Available" if available else "Not available"
        print(f"  {platform}: {status}")
    
    return True


# Command registration function
async def register_commands() -> Dict[str, Callable]:
    """Register all commands provided by this module."""
    return {
        'vtest-create': vtest_create_command,
        'vtest-list': vtest_list_command,
        'vtest-start': vtest_start_command,
        'vtest-stop': vtest_stop_command,
        'vtest-delete': vtest_delete_command,
        'vtest-run': vtest_run_command,
        'vtest-copy': vtest_copy_command,
        'vtest-status': vtest_status_command,
        'vtest-templates': vtest_templates_command,
        'vtest-export': vtest_export_command,
        'sandbox-create': sandbox_create_command,
        'sandbox-run': sandbox_run_command,
        'vbox-create': vbox_create_command,
        'vbox-run': vbox_run_command,
        'vtest-config': vtest_config_command,
    }


# Alternative function name for compatibility
def get_commands() -> List[str]:
    """Get list of command names provided by this module."""
    return MODULE_INFO['commands']