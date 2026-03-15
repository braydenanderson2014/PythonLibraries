# editor/renderers/run_renderer.py
"""
Helper script to run renderers with the correct Python version.
This ensures PyQt6 WebEngine is available when needed.
"""

import os
import sys
import subprocess
import importlib.util

def get_python_paths():
    """Get a list of available Python executables."""
    python_paths = []
    
    # Check if py launcher is available
    try:
        # Try to get Python 3.13+ first, as it's known to work with PyQt6
        result = subprocess.run(["py", "-3.13", "-c", "import sys; print(sys.executable)"], 
                               capture_output=True, text=True)
        if result.returncode == 0:
            python_paths.append(("py -3.13", result.stdout.strip()))
    except FileNotFoundError:
        pass
    
    # Add current Python executable
    python_paths.append((sys.executable, sys.executable))
    
    return python_paths

def check_pyqt_availability(python_cmd):
    """Check if PyQt6 WebEngine is available with the given Python command."""
    try:
        # Create a temporary test script
        temp_script = os.path.join(os.path.dirname(__file__), "_temp_pyqt_check.py")
        with open(temp_script, "w") as f:
            f.write("""
import sys
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    print("PyQt6_AVAILABLE=True")
except ImportError:
    print("PyQt6_AVAILABLE=False")
""")
        
        # Run the test script with the specified Python command
        if python_cmd.startswith("py "):
            # For py launcher
            cmd_parts = python_cmd.split() + [temp_script]
            result = subprocess.run(cmd_parts, capture_output=True, text=True)
        else:
            # For direct executable path
            result = subprocess.run([python_cmd, temp_script], capture_output=True, text=True)
            
        # Clean up
        try:
            os.unlink(temp_script)
        except:
            pass
            
        # Check if PyQt6 is available
        if "PyQt6_AVAILABLE=True" in result.stdout:
            return True
    except Exception as e:
        print(f"Error checking PyQt availability: {e}")
    
    return False

def get_best_python_command():
    """Get the best Python command that supports PyQt6."""
    python_paths = get_python_paths()
    
    for cmd, path in python_paths:
        if check_pyqt_availability(cmd):
            print(f"Found PyQt6-compatible Python: {cmd} ({path})")
            return cmd
    
    # If no compatible Python found, use the current one
    print("Warning: No PyQt6-compatible Python found. Using current Python.")
    return sys.executable

def run_script(script_path, args=None):
    """Run a script using the best Python command."""
    python_cmd = get_best_python_command()
    
    if args is None:
        args = []
    
    if python_cmd.startswith("py "):
        # For py launcher
        cmd_parts = python_cmd.split() + [script_path] + args
        subprocess.run(cmd_parts)
    else:
        # For direct executable path
        subprocess.run([python_cmd, script_path] + args)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_renderer.py <script_path> [args...]")
        sys.exit(1)
        
    script_path = sys.argv[1]
    args = sys.argv[2:]
    run_script(script_path, args)
