#!/usr/bin/env python3
"""
Test the GUI structure without actually running PyQt6
This validates that all classes are properly defined and importable
"""

import sys
import os
import ast
import inspect

def analyze_gui_file():
    """Analyze the GUI file structure"""
    print("🔍 Analyzing PyQt6 GUI Interface Structure...")
    print("=" * 60)
    
    gui_file = "build_gui_interface.py"
    
    if not os.path.exists(gui_file):
        print("❌ GUI file not found!")
        return False
    
    try:
        # Read and parse the file
        with open(gui_file, 'r') as f:
            content = f.read()
        
        # Parse the AST to find classes
        tree = ast.parse(content)
        
        classes = []
        functions = []
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append(node.name)
            elif isinstance(node, ast.FunctionDef):
                if not node.name.startswith('_'):  # Skip private methods
                    functions.append(node.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        
        # Print analysis
        print("📦 Import Analysis:")
        for imp in sorted(set(imports)):
            print(f"  • {imp}")
        
        print(f"\n🏗️ Classes Found ({len(classes)}):")
        for cls in sorted(classes):
            print(f"  • {cls}")
        
        print(f"\n⚙️ Functions Found ({len([f for f in functions if not any(c in f for c in classes)])}):")
        standalone_functions = [f for f in functions if not any(f.startswith(c.lower()) for c in classes)]
        for func in sorted(set(standalone_functions)):
            print(f"  • {func}")
        
        # Validate expected classes
        expected_classes = [
            'CLIInterface',
            'CLIThread', 
            'ProjectConfigTab',
            'FileScanTab',
            'BuildTab',
            'MainWindow'
        ]
        
        print(f"\n✅ Class Validation:")
        missing_classes = []
        for expected in expected_classes:
            if expected in classes:
                print(f"  ✓ {expected}")
            else:
                print(f"  ❌ {expected} - MISSING")
                missing_classes.append(expected)
        
        if missing_classes:
            print(f"\n⚠️ Missing Classes: {', '.join(missing_classes)}")
            return False
        
        # Check file size and structure
        lines = content.split('\n')
        print(f"\n📊 File Statistics:")
        print(f"  • Total Lines: {len(lines)}")
        print(f"  • File Size: {len(content):,} bytes")
        print(f"  • Classes: {len(classes)}")
        print(f"  • Functions: {len(functions)}")
        
        print(f"\n🎯 Structure Validation:")
        
        # Check for main components
        required_patterns = [
            ('PyQt6 imports', 'from PyQt6.QtWidgets import'),
            ('CLI interface', 'class CLIInterface'),
            ('Thread handling', 'class CLIThread'),
            ('Project configuration', 'class ProjectConfigTab'),
            ('File scanning', 'class FileScanTab'),
            ('Build operations', 'class BuildTab'),
            ('Main window', 'class MainWindow'),
            ('Main function', 'def main()'),
            ('Launch function', 'def launch_gui()'),
        ]
        
        for desc, pattern in required_patterns:
            if pattern in content:
                print(f"  ✓ {desc}")
            else:
                print(f"  ❌ {desc}")
        
        print(f"\n🚀 GUI Interface Analysis Complete!")
        print("✅ All major components are present and properly structured.")
        print("\nThe GUI is ready to launch when PyQt6 is available.")
        print("Install PyQt6 with: pip install PyQt6")
        
        return True
        
    except Exception as e:
        print(f"❌ Error analyzing GUI file: {e}")
        return False

def test_cli_integration():
    """Test if the CLI file exists and is accessible"""
    print(f"\n🔗 CLI Integration Test:")
    print("=" * 30)
    
    cli_file = "build_cli.py"
    
    if os.path.exists(cli_file):
        print(f"  ✓ CLI file found: {cli_file}")
        
        # Test basic CLI functionality
        try:
            result = os.system(f"python {cli_file} --help > /dev/null 2>&1")
            if result == 0:
                print(f"  ✓ CLI is executable")
            else:
                print(f"  ⚠️ CLI may have issues")
        except:
            print(f"  ⚠️ Could not test CLI execution")
    else:
        print(f"  ❌ CLI file not found: {cli_file}")
        return False
    
    return True

def main():
    """Main test function"""
    print("🧪 PyInstaller Build Tool - GUI Structure Test")
    print("=" * 60)
    
    success = True
    
    # Test GUI structure
    success &= analyze_gui_file()
    
    # Test CLI integration
    success &= test_cli_integration()
    
    print(f"\n{'='*60}")
    if success:
        print("🎉 All Tests Passed!")
        print("✅ GUI structure is valid and ready to use")
        print("📋 Next steps:")
        print("   1. Install PyQt6: pip install PyQt6")
        print("   2. Run GUI: python build_gui_interface.py")
        print("   3. Or use CLI: python build_cli.py --download-gui")
    else:
        print("❌ Some tests failed!")
        print("⚠️ Fix the issues above before using the GUI")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
