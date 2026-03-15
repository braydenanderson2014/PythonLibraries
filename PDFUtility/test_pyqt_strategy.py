#!/usr/bin/env python3
"""
Test script to verify PyQt installation strategy for different platforms
This simulates the logic used in the advanced build workflow
"""

import sys
import subprocess
import platform

def run_command(cmd):
    """Run a command and return success status"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Timeout"

def test_pyqt_installation_strategy():
    """Test the PyQt installation strategy"""
    print(f"🖥️ Platform: {platform.system()} {platform.machine()}")
    print(f"🐍 Python: {sys.version}")
    print()
    
    # Simulate the logic from the workflow
    is_windows_x86 = platform.system() == "Windows" and platform.machine().endswith("86")
    
    print("🔧 Testing PyQt installation strategy...")
    
    if is_windows_x86:
        print("🔧 Windows x86 detected - would use PyQt5 for compatibility")
        # Test PyQt5 installation check (don't actually install)
        success, stdout, stderr = run_command("python -c \"import PyQt5; print('PyQt5 available')\"")
        if success:
            print("✅ PyQt5 already available")
        else:
            print("⚠️ PyQt5 not available - would install PyQt5>=5.15.0")
    else:
        print("🔧 Standard platform - would try PyQt6 first")
        # Test PyQt6 installation check
        success, stdout, stderr = run_command("python -c \"import PyQt6; print('PyQt6 available')\"")
        if success:
            print("✅ PyQt6 already available")
        else:
            print("⚠️ PyQt6 not available - would install PyQt6>=6.0")
            # Test PyQt5 fallback
            success, stdout, stderr = run_command("python -c \"import PyQt5; print('PyQt5 available')\"")
            if success:
                print("✅ PyQt5 available as fallback")
            else:
                print("⚠️ PyQt5 not available - would install PyQt5>=5.15.0 as fallback")
    
    print()
    print("📋 Testing requirements file parsing...")
    
    # Test requirements file detection
    requirements_files = ["requirements.txt", "test_requirements.txt", "BuildSystem/PDFUtility_requirements.txt"]
    found_file = None
    
    for req_file in requirements_files:
        try:
            with open(req_file, 'r') as f:
                found_file = req_file
                break
        except FileNotFoundError:
            continue
    
    if found_file:
        print(f"📋 Found requirements file: {found_file}")
        
        # Simulate filtering PyQt lines
        try:
            with open(found_file, 'r') as f:
                lines = f.readlines()
            
            filtered_lines = []
            pyqt_lines = []
            
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    if any(pkg in line for pkg in ['PyQt5', 'PyQt6', 'pyinstaller', 'PyInstaller']):
                        pyqt_lines.append(line)
                    else:
                        filtered_lines.append(line)
            
            print(f"📦 PyQt/PyInstaller lines (handled separately): {len(pyqt_lines)}")
            for line in pyqt_lines:
                print(f"   - {line}")
            
            print(f"📦 Additional requirements to install: {len(filtered_lines)}")
            for line in filtered_lines:
                print(f"   - {line}")
                
        except Exception as e:
            print(f"⚠️ Error reading requirements file: {e}")
    else:
        print("📋 No requirements file found - would use minimal dependencies")
    
    print()
    print("✅ PyQt installation strategy test completed!")

if __name__ == "__main__":
    test_pyqt_installation_strategy()
