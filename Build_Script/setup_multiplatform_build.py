#!/usr/bin/env python3
"""
Multi-Platform Build Setup Script
Helps set up the GitHub Actions workflow for automated PyInstaller builds
"""

import os
import json
import shutil
import argparse
from pathlib import Path

def create_directory_structure():
    """Create necessary directory structure"""
    directories = [
        '.github/workflows',
        '.github'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def copy_workflow_files():
    """Copy workflow files to the target repository"""
    workflow_files = [
        ('multi-platform-build.yml', '.github/workflows/multi-platform-build.yml'),
        ('test-build.yml', '.github/workflows/test-build.yml')
    ]
    
    for source, target in workflow_files:
        if os.path.exists(source):
            shutil.copy2(source, target)
            print(f"✅ Copied workflow: {target}")
        else:
            print(f"❌ Source file not found: {source}")

def create_build_config(app_name=None, interactive=True):
    """Create build configuration file"""
    config_path = '.github/build-config.json'
    
    if interactive:
        print("\n🔧 Build Configuration Setup")
        print("=" * 40)
        
        app_name = input(f"App name [{app_name or 'MyApp'}]: ").strip() or app_name or 'MyApp'
        windowed = input("Windowed app (no console)? [y/N]: ").lower().startswith('y')
        
        platforms = []
        if input("Build for Windows? [Y/n]: ").lower() not in ['n', 'no']:
            platforms.append('windows')
        if input("Build for Linux? [Y/n]: ").lower() not in ['n', 'no']:
            platforms.append('linux')
        if input("Build for macOS? [Y/n]: ").lower() not in ['n', 'no']:
            platforms.append('macos')
        
        build_type = 'onefile'
        if input("Build as directory instead of single file? [y/N]: ").lower().startswith('y'):
            build_type = 'onedir'
    else:
        windowed = False
        platforms = ['windows', 'linux', 'macos']
        build_type = 'onefile'
    
    config = {
        "name": app_name,
        "version": "auto",
        "append_version": True,
        "append_date": False,
        "windowed": windowed,
        "main_file": "auto",
        "python_version": "3.13.3",
        "build_type": build_type,
        "platforms": platforms,
        "architectures": {
            "windows": ["x64", "x86"],
            "linux": ["x64", "arm64"],
            "macos": ["x64", "arm64"]
        },
        "additional_flags": [
            "--clean"
        ]
    }
    
    # Filter architectures based on selected platforms
    config["architectures"] = {
        platform: config["architectures"][platform] 
        for platform in platforms 
        if platform in config["architectures"]
    }
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Created build config: {config_path}")
    return config

def detect_main_file():
    """Detect potential main files"""
    main_candidates = [
        'main.py', 'app.py', '__main__.py', 'run.py',
        'src/main.py', 'src/app.py'
    ]
    
    found = []
    for candidate in main_candidates:
        if os.path.exists(candidate):
            found.append(candidate)
    
    return found

def analyze_project():
    """Analyze the current project structure"""
    print("\n🔍 Project Analysis")
    print("=" * 30)
    
    # Check for Python files
    python_files = list(Path('.').rglob('*.py'))
    print(f"📄 Found {len(python_files)} Python files")
    
    # Check for main files
    main_files = detect_main_file()
    if main_files:
        print(f"🎯 Potential main files: {', '.join(main_files)}")
    else:
        print("⚠️  No obvious main file found")
    
    # Check for dependencies
    dep_files = []
    for dep_file in ['requirements.txt', 'Pipfile', 'pyproject.toml', 'setup.py']:
        if os.path.exists(dep_file):
            dep_files.append(dep_file)
    
    if dep_files:
        print(f"📦 Dependency files: {', '.join(dep_files)}")
    else:
        print("⚠️  No dependency files found")
    
    # Check for resources
    resource_patterns = {
        'Icons': ['*.ico', '*.png', '*.jpg'],
        'Config': ['*.json', '*.yaml', '*.yml', '*.toml'],
        'Data': ['*.csv', '*.db', '*.sqlite', '*.xml']
    }
    
    for resource_type, patterns in resource_patterns.items():
        files = []
        for pattern in patterns:
            files.extend(list(Path('.').rglob(pattern)))
        if files:
            print(f"📂 {resource_type}: {len(files)} files")

def create_example_app():
    """Create a simple example app for testing"""
    if input("\nCreate example app for testing? [y/N]: ").lower().startswith('y'):
        example_code = '''#!/usr/bin/env python3
"""
Example application for testing multi-platform builds
"""

import sys
import platform

def main():
    print("🚀 Multi-Platform Build Test Application")
    print("=" * 45)
    print(f"Platform: {platform.system()}")
    print(f"Architecture: {platform.machine()}")
    print(f"Python: {sys.version}")
    print()
    print("✅ Build successful!")
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()
'''
        
        with open('main.py', 'w') as f:
            f.write(example_code)
        
        # Create basic requirements.txt
        with open('requirements.txt', 'w') as f:
            f.write("# Add your dependencies here\n")
        
        print("✅ Created example app: main.py")
        print("✅ Created requirements.txt template")

def show_next_steps():
    """Show next steps for the user"""
    print("\n🎉 Setup Complete!")
    print("=" * 30)
    print("Next steps:")
    print("1. Commit and push the workflow files:")
    print("   git add .github/")
    print("   git commit -m 'Add multi-platform build workflow'")
    print("   git push")
    print()
    print("2. Test the workflow:")
    print("   • Go to Actions tab in GitHub")
    print("   • Run 'Test Multi-Platform Build' manually")
    print()
    print("3. Create a release:")
    print("   git tag v1.0.0")
    print("   git push origin v1.0.0")
    print()
    print("4. Customize .github/build-config.json as needed")
    print()
    print("📖 See MULTI_PLATFORM_BUILD.md for detailed documentation")

def main():
    parser = argparse.ArgumentParser(description='Set up multi-platform build workflow')
    parser.add_argument('--app-name', help='Application name')
    parser.add_argument('--no-interactive', action='store_true', help='Skip interactive configuration')
    parser.add_argument('--example', action='store_true', help='Create example app')
    
    args = parser.parse_args()
    
    print("🏗️  Multi-Platform Build Setup")
    print("=" * 40)
    
    # Analyze current project
    analyze_project()
    
    # Create directory structure
    create_directory_structure()
    
    # Copy workflow files (if available)
    copy_workflow_files()
    
    # Create build configuration
    app_name = args.app_name or os.path.basename(os.getcwd())
    config = create_build_config(app_name, not args.no_interactive)
    
    # Create example app if requested
    if args.example or (not args.no_interactive and not detect_main_file()):
        create_example_app()
    
    # Show next steps
    show_next_steps()

if __name__ == '__main__':
    main()
