"""
PyInstaller integration module for BuildCLI.
"""

import asyncio
import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Any, Callable


MODULE_INFO = {
    'name': 'pyinstaller',
    'version': '1.0.0',
    'description': 'PyInstaller integration for building executables',
    'author': 'BuildCLI',
    'commands': ['build', 'build-exe', 'clean-build', 'analyze']
}


async def build_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Build command - creates an executable using PyInstaller."""
    # Default to building the main.py file
    script_file = args[0] if args else 'main.py'
    
    if not os.path.exists(script_file):
        raise ValueError(f"Script file not found: {script_file}")
    
    # Build PyInstaller command
    pyinstaller_args = [
        sys.executable, '-m', 'PyInstaller'
    ]
    
    # Add common options
    if modifiers.get('one_file', True):
        pyinstaller_args.append('--onefile')
    
    if modifiers.get('console', True):
        pyinstaller_args.append('--console')
    else:
        pyinstaller_args.append('--windowed')
    
    if modifiers.get('debug', False):
        pyinstaller_args.append('--debug=all')
    
    # Icon file
    icon_file = modifiers.get('icon')
    if icon_file and os.path.exists(icon_file):
        pyinstaller_args.extend(['--icon', icon_file])
    
    # Additional data files
    add_data = modifiers.get('add_data', [])
    if isinstance(add_data, str):
        add_data = [add_data]
    
    for data_spec in add_data:
        pyinstaller_args.extend(['--add-data', data_spec])
    
    # Hidden imports
    hidden_imports = modifiers.get('hidden_imports', [])
    if isinstance(hidden_imports, str):
        hidden_imports = [hidden_imports]
    
    for import_name in hidden_imports:
        pyinstaller_args.extend(['--hidden-import', import_name])
    
    # Output directory
    dist_dir = modifiers.get('dist_dir', 'dist')
    pyinstaller_args.extend(['--distpath', dist_dir])
    
    # Build directory
    build_dir = modifiers.get('build_dir', 'build')
    pyinstaller_args.extend(['--workpath', build_dir])
    
    # Spec file directory
    spec_dir = modifiers.get('spec_dir', '.')
    pyinstaller_args.extend(['--specpath', spec_dir])
    
    # Clean build
    if modifiers.get('clean', False):
        pyinstaller_args.append('--clean')
    
    # No confirm
    pyinstaller_args.append('--noconfirm')
    
    # Add the script file
    pyinstaller_args.append(script_file)
    
    # Handle dry-run mode
    if modifiers.get('dry_run', False):
        print(f"[DRY RUN] Would execute: {' '.join(pyinstaller_args)}")
        return True
    
    print(f"Building executable from {script_file}...")
    print(f"Command: {' '.join(pyinstaller_args)}")
    
    try:
        # Execute PyInstaller
        process = await asyncio.create_subprocess_exec(
            *pyinstaller_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )
        
        # Stream output in real-time
        if process.stdout:
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                print(line.decode('utf-8', errors='replace').rstrip())
        
        await process.wait()
        
        if process.returncode == 0:
            print(f"\n✓ Build completed successfully!")
            
            # Find the output executable
            if modifiers.get('one_file', True):
                exe_name = Path(script_file).stem
                if sys.platform == 'win32':
                    exe_name += '.exe'
                exe_path = Path(dist_dir) / exe_name
                
                if exe_path.exists():
                    print(f"Executable created: {exe_path}")
                    print(f"Size: {exe_path.stat().st_size / 1024 / 1024:.1f} MB")
            
            return True
        else:
            print(f"\n✗ Build failed with exit code {process.returncode}")
            return False
    
    except FileNotFoundError:
        print("PyInstaller not found. Install it with: pip install pyinstaller")
        return False
    except Exception as e:
        print(f"Build failed: {e}")
        return False


async def build_exe_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Build-exe command - alias for build with exe-specific defaults."""
    # Set exe-specific defaults
    modifiers.setdefault('one_file', True)
    modifiers.setdefault('console', True)
    
    return await build_command(args, modifiers)


async def clean_build_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Clean build command - removes build artifacts."""
    import shutil
    
    dirs_to_clean = ['build', 'dist', '__pycache__']
    files_to_clean = ['*.spec']
    
    cleaned = []
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            if modifiers.get('dry_run', False):
                print(f"[DRY RUN] Would remove directory: {dir_name}")
            else:
                shutil.rmtree(dir_name)
                cleaned.append(dir_name)
                print(f"Removed directory: {dir_name}")
    
    # Clean spec files
    import glob
    for pattern in files_to_clean:
        for file_path in glob.glob(pattern):
            if modifiers.get('dry_run', False):
                print(f"[DRY RUN] Would remove file: {file_path}")
            else:
                os.remove(file_path)
                cleaned.append(file_path)
                print(f"Removed file: {file_path}")
    
    if cleaned:
        print(f"Cleaned {len(cleaned)} items")
    else:
        print("Nothing to clean")
    
    return True


async def analyze_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Analyze command - analyzes dependencies and imports."""
    script_file = args[0] if args else 'main.py'
    
    if not os.path.exists(script_file):
        raise ValueError(f"Script file not found: {script_file}")
    
    print(f"Analyzing {script_file}...")
    
    # Use PyInstaller's analysis capabilities
    try:
        # Try to run PyInstaller analysis
        analysis_args = [
            sys.executable, '-m', 'PyInstaller',
            '--analyze', script_file
        ]
        
        if modifiers.get('dry_run', False):
            print(f"[DRY RUN] Would analyze: {script_file}")
            return True
        
        process = await asyncio.create_subprocess_exec(
            *analysis_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            if stdout:
                print(stdout.decode('utf-8', errors='replace'))
            return True
        else:
            print(f"Analysis failed: {stderr.decode('utf-8', errors='replace')}")
            return False
    
    except Exception as e:
        print(f"Analysis failed: {e}")
        return False


# Command registration function
async def register_commands() -> Dict[str, Callable]:
    """Register all commands provided by this module."""
    return {
        'build': build_command,
        'build-exe': build_exe_command,
        'clean-build': clean_build_command,
        'analyze': analyze_command,
    }


# Alternative function name for compatibility
def get_commands() -> List[str]:
    """Get list of command names provided by this module."""
    return MODULE_INFO['commands']