#!/usr/bin/env python3
# build_rent_tracker.py - Build script specifically for Rent Tracker

import os
import subprocess
from datetime import datetime

def find_icon_file():
    """Find available icon files"""
    icon_files = [
        "Rent_Tracker.ico",          # Exact match for our app
        "rent_tracker.ico",
        "icon.ico",
        "assets/Rent_Tracker.ico",
        "assets/rent_tracker.ico",
        "assets/icon.ico",
        "icons/Rent_Tracker.ico",
        "icons/rent_tracker.ico",
        "icons/icon.ico"
    ]
    
    for icon_path in icon_files:
        if os.path.exists(icon_path):
            return icon_path
    return None

def build_rent_tracker():
    """Build the Rent Tracker application"""
    print("🏠 Building Rent Tracker Application 🏠\n")
    
    # Check for main file
    main_file = "Rent_Tracker.py"
    if not os.path.exists(main_file):
        print(f"❌ Error: {main_file} not found!")
        return False
    
    # Find icon file
    icon_file = find_icon_file()
    if icon_file:
        print(f"✅ Found icon: {icon_file}")
    else:
        print("⚠️  No icon file found. Consider running create_icon.py first.")
        create_icon = input("Would you like to try creating an icon now? (y/n): ").lower()
        if create_icon in ['y', 'yes']:
            try:
                subprocess.run(["python", "create_icon.py", "--generate"], check=True)
                icon_file = find_icon_file()
                if icon_file:
                    print(f"✅ Created and found icon: {icon_file}")
            except:
                print("❌ Could not create icon automatically.")
    
    # Get build options
    print("\n📋 Build Configuration:")
    
    app_name = input("Application name (default: Rent Tracker): ").strip()
    if not app_name:
        app_name = "Rent Tracker"
    
    # Generate version with date
    date_str = datetime.now().strftime("%m%d%Y")
    build_type = input("Build type (ALPHA/BETA/RELEASE) [ALPHA]: ").strip().upper()
    if not build_type:
        build_type = "ALPHA"
    
    final_name = f"{app_name}-{date_str}-{build_type}"
    
    # Build options
    one_file = input("Create single executable file? (Y/n): ").lower()
    create_onefile = one_file not in ['n', 'no']
    
    windowed = input("Hide console window? (Y/n): ").lower()
    hide_console = windowed not in ['n', 'no']
    
    # Build PyInstaller command
    cmd = ["pyinstaller"]
    
    # Basic options
    cmd.extend(["--name", final_name])
    
    if create_onefile:
        cmd.append("--onefile")
    
    if hide_console:
        cmd.append("--windowed")
    
    # Icon handling - more robust inclusion
    if icon_file:
        cmd.extend(["--icon", icon_file])
        # Also add the icon as a data file to ensure it's accessible at runtime
        cmd.extend(["--add-data", f"{icon_file};."])
        print(f"✅ Icon will be included: {icon_file}")
    
    # Clean build
    cmd.append("--clean")
    
    # Add additional Windows-specific options for better icon support
    if os.name == 'nt':  # Windows
        version_file = "version_info.txt"
        if os.path.exists(version_file):
            cmd.extend(["--version-file", version_file])
            print(f"✅ Version info included: {version_file}")
    
    # Add data files that might be needed
    data_files = ["pin_hash.txt", "accounts.json"]
    for data_file in data_files:
        if os.path.exists(data_file):
            cmd.extend(["--add-data", f"{data_file};."])
    
    # Add UPX compression if available (optional, for smaller file size)
    try:
        subprocess.run(["upx", "--version"], capture_output=True, check=True)
        compress = input("Use UPX compression for smaller file size? (y/N): ").lower()
        if compress in ['y', 'yes']:
            cmd.append("--upx-dir=.")
            print("✅ UPX compression enabled")
    except:
        pass  # UPX not available, skip
    
    # Main file
    cmd.append(main_file)
    
    # Show command preview
    print("\n" + "="*60)
    print("  COMMAND PREVIEW")
    print("="*60)
    print(f"Command: {' '.join(cmd)}")
    print()
    print(f"Final executable name: {final_name}.exe")
    print(f"Icon: {icon_file if icon_file else 'None'}")
    print(f"Type: {'Single file' if create_onefile else 'Directory'}")
    print(f"Console: {'Hidden' if hide_console else 'Visible'}")
    print("="*60)
    
    # Confirm and execute
    confirm = input("\nExecute build? (Y/n): ").lower()
    if confirm not in ['n', 'no']:
        print(f"\n🔨 Building {final_name}...")
        
        try:
            result = subprocess.run(cmd, capture_output=False)
            
            if result.returncode == 0:
                print("\n" + "="*60)
                print("  🎉 BUILD SUCCESSFUL! 🎉")
                print("="*60)
                print(f"Executable created: {final_name}.exe")
                print("Location: dist/ folder")
                print()
                print("📦 Your Rent Tracker is ready to distribute!")
                if icon_file:
                    print(f"✅ Icon included: {icon_file}")
                return True
            else:
                print("\n❌ Build failed! Check output above for errors.")
                return False
                
        except FileNotFoundError:
            print("\n❌ PyInstaller not found!")
            print("Install with: pip install pyinstaller")
            return False
        except Exception as e:
            print(f"\n❌ Build error: {e}")
            return False
    else:
        print("Build cancelled.")
        return False

def main():
    """Main entry point"""
    try:
        build_rent_tracker()
    except KeyboardInterrupt:
        print("\n\nBuild cancelled by user.")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
