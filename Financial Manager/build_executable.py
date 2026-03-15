#!/usr/bin/env python3
"""
PyInstaller Builder for Financial Manager
Creates a standalone executable with all dependencies and assets
"""

import subprocess
import sys
import os
from pathlib import Path
import shlex

def main():
    # Get project root
    project_root = Path(__file__).parent.absolute()
    
    print("=" * 50)
    print("Financial Manager - PyInstaller Builder")
    print("=" * 50)
    print(f"\nProject Root: {project_root}\n")
    
    # Check PyInstaller installation
    try:
        subprocess.run([sys.executable, "-m", "pip", "show", "pyinstaller"], 
                      capture_output=True, check=True)
    except subprocess.CalledProcessError:
        print("PyInstaller not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller", "-q"], 
                      check=True)
    
    # Define paths
    resources_icons = project_root / "resources" / "icons"
    # SPLASH SCREEN DISABLED TEMPORARILY TO DEBUG ERRORS
    # resources_splash = project_root / "resources" / "Splash.png"
    icon_file = project_root / "resources" / "icons" / "Rent_Tracker.ico"
    main_script = project_root / "main_window.py"
    dist_path = project_root / "dist"
    build_path = project_root / "build"
    spec_path = project_root
    
    # Verify key files exist
    if not main_script.exists():
        print(f"ERROR: main_window.py not found at {main_script}")
        return 1
    
    if not icon_file.exists():
        print(f"WARNING: Icon file not found at {icon_file}, continuing without icon...")
        icon_file = None
    
    # Build PyInstaller command - use shell to handle spaces in paths properly
    dist_str = str(dist_path)
    build_str = str(build_path)
    spec_str = str(spec_path)
    resources_str = str(project_root / 'resources')
    icons_str = str(resources_icons)
    ui_str = str(project_root / 'ui')
    src_str = str(project_root / 'src')
    main_script_str = str(main_script)
    
    cmd_parts = [
        sys.executable, "-m", "PyInstaller",
        "--name=FinancialManager",
        "--onefile",
        # SHOW CONSOLE TEMPORARILY TO DEBUG ERRORS
        # "--windowed",
        "--console",
        f"--distpath={shlex.quote(dist_str)}",
        f"--buildpath={shlex.quote(build_str)}",
        f"--specpath={shlex.quote(spec_str)}",
        "--noconfirm",
        "--clean",  # Clean old build files
        "--hidden-import=pyi_splash",  # Support pyi_splash if available
        "--collect-all=matplotlib",
        # Hidden imports
        "--hidden-import=PyQt6",
        "--hidden-import=PyQt6.QtCore",
        "--hidden-import=PyQt6.QtGui",
        "--hidden-import=PyQt6.QtWidgets",
        "--hidden-import=matplotlib",
        "--hidden-import=matplotlib.backends.backend_qt5agg",
        "--hidden-import=openpyxl",
        "--hidden-import=requests",
        "--hidden-import=pandas",
        "--hidden-import=numpy",
        "--hidden-import=sqlite3",
        "--hidden-import=json",
        "--hidden-import=datetime",
        "--hidden-import=pathlib",
        # Data files (convert Path objects to strings)
        f"--add-data={shlex.quote(resources_str + ';resources')}",
        f"--add-data={shlex.quote(icons_str + ';resources/icons')}",
        f"--add-data={shlex.quote(ui_str + ';ui')}",
        f"--add-data={shlex.quote(src_str + ';src')}",
    ]
    
    # Add icon if available
    if icon_file:
        cmd_parts.append(f"--icon={shlex.quote(str(icon_file))}")
    
    # Add splash if available
    #if resources_splash:
        #cmd_parts.append(f'--splash="{str(resources_splash)}"')
    
    # Add main script (must be last)
    cmd_parts.append(shlex.quote(main_script_str))
    
    # Convert to command string for display
    cmd_str = ' '.join(cmd_parts)
    
    print("Building executable with PyInstaller...")
    print("\n" + "=" * 70)
    print("COMMAND TO EXECUTE (as list):")
    print("=" * 70)
    for i, part in enumerate(cmd_parts):
        print(f"  [{i}]: {repr(part)}")
    print("\n" + "=" * 70)
    print("COMMAND TO EXECUTE (as string):")
    print("=" * 70)
    print(cmd_str)
    print("=" * 70 + "\n")
    
    try:
        # Run with shell=False and pass cmd list directly for better path handling
        result = subprocess.run(cmd_parts, check=True, text=True)
        
        print("\n" + "=" * 50)
        print("Build completed successfully!")
        print("=" * 50)
        print(f"\nExecutable location:")
        print(f"  {dist_path / 'FinancialManager.exe'}\n")
        
        return 0
        
    except subprocess.CalledProcessError as e:
        print("\n" + "=" * 50)
        print(f"Build failed with error code {e.returncode}")
        print("=" * 50)
        return 1
    except Exception as e:
        print(f"\nERROR: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
