#!/usr/bin/env python3
"""
PyInstaller Build Tool - Ultra-Fast CLI Launcher
Minimal imports for maximum performance on command-line operations
"""

import sys
import os

# Ultra-minimal fast path detection
def is_fast_command():
    """Check if this is a fast command that doesn't need heavy imports"""
    if len(sys.argv) <= 1:
        return False
    
    fast_commands = {
        '--help', '-h', '--version', '--changelog', 
        '--repo-status', '--update', '--download-gui'
    }
    
    return any(arg in fast_commands for arg in sys.argv[1:])

def main():
    """Ultra-fast main entry point"""
    
    # For GUI or complex operations, delegate to core module
    if not is_fast_command() or '--gui' in sys.argv:
        try:
            # Import core module only when needed
            from build_gui_core import main as core_main
            return core_main()
        except ImportError:
            print("❌ Core module not found. Please ensure build_gui_core.py is available.")
            return False
        except Exception as e:
            print(f"❌ Error loading core module: {e}")
            return False
    
    # Handle ultra-fast commands directly
    if '--help' in sys.argv or '-h' in sys.argv:
        print("""
PyInstaller Build Tool - Fast CLI Launcher

Usage: build_cli [OPTIONS]

Fast Commands (no additional imports):
  --help, -h            Show this help message
  --gui                 Launch GUI interface (auto-downloads if needed)
  --version             Show version information
  --repo-status         Check GitHub repository status
  --download-gui        Download/update GUI module
  --changelog           Show recent changes
  --update              Check for updates

Examples:
  build_cli --gui                 Launch graphical interface
  build_cli --repo-status         Quick repository check
  build_cli --version             Show version info

For advanced operations, use --gui to access the full interface.
        """)
        return True
    
    elif '--version' in sys.argv:
        print("PyInstaller Build Tool Enhanced - CLI Launcher")
        print("Version: 1.0.0-modular")
        print("Ultra-fast command-line interface")
        return True
    
    # For all other commands, delegate to core
    try:
        from build_gui_core import main as core_main
        return core_main()
    except ImportError:
        print("❌ Core module not found. Please ensure build_gui_core.py is available.")
        return False

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
