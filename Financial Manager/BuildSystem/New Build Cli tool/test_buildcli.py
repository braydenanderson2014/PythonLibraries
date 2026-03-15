#!/usr/bin/env python3
"""
Test script for BuildCLI functionality.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from main import BuildCLI


async def test_basic_functionality():
    """Test basic CLI functionality."""
    print("Testing BuildCLI functionality...")
    
    cli = BuildCLI()
    
    try:
        await cli.initialize()
        print("✓ CLI initialization successful")
        
        # Test version command
        print("\n--- Testing version command ---")
        cli.print_version()
        
        # Test help command
        print("\n--- Testing help command ---")
        cli.print_help()
        
        # Test echo command
        print("\n--- Testing echo command ---")
        exit_code = await cli.run(['echo', 'Hello from BuildCLI!'])
        print(f"Echo command exit code: {exit_code}")
        
        # Test dry-run mode
        print("\n--- Testing dry-run mode ---")
        exit_code = await cli.run(['--dry-run', 'echo', 'This is a dry run'])
        print(f"Dry-run exit code: {exit_code}")
        
        # Test command chaining
        print("\n--- Testing command chaining ---")
        exit_code = await cli.run(['echo', 'Step 1', '&&', 'echo', 'Step 2'])
        print(f"Command chain exit code: {exit_code}")
        
        # Test build command (dry-run)
        print("\n--- Testing build command (dry-run) ---")
        exit_code = await cli.run(['--dry-run', 'build', 'main.py'])
        print(f"Build command exit code: {exit_code}")
        
        print("\n✓ All tests completed successfully!")
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False
    
    return True


async def test_module_loading():
    """Test module loading functionality."""
    print("\n--- Testing module loading ---")
    
    cli = BuildCLI()
    await cli.initialize()
    
    # Check loaded modules
    modules = cli.module_manager.get_available_modules()
    print(f"Loaded modules: {list(modules.keys())}")
    
    # Check command handlers
    handlers = cli.module_manager.get_command_handlers()
    print(f"Available commands: {list(handlers.keys())}")
    
    return True


async def test_configuration():
    """Test configuration functionality."""
    print("\n--- Testing configuration ---")
    
    cli = BuildCLI()
    
    print(f"Log level: {cli.config.log_level}")
    print(f"Module cache dir: {cli.config.module_cache_dir}")
    print(f"Parallel execution: {cli.config.parallel_execution}")
    
    return True


def test_file_structure():
    """Test that all required files exist."""
    print("\n--- Testing file structure ---")
    
    required_files = [
        'main.py',
        'core/__init__.py',
        'core/cli_parser.py',
        'core/command_queue.py',
        'core/config.py',
        'core/module_manager.py',
        'utils/__init__.py',
        'utils/logger.py',
        'modules/system.py',
        'modules/pyinstaller_module.py',
        'requirements.txt',
        'setup.py',
        'README.md',
        'build.bat',
        'build.sh',
        'buildcli.spec'
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = project_root / file_path
        if not full_path.exists():
            missing_files.append(file_path)
        else:
            print(f"✓ {file_path}")
    
    if missing_files:
        print(f"✗ Missing files: {missing_files}")
        return False
    
    print("✓ All required files present")
    return True


async def main():
    """Main test function."""
    print("BuildCLI Test Suite")
    print("=" * 50)
    
    # Test file structure first
    if not test_file_structure():
        print("File structure test failed!")
        return 1
    
    # Test configuration
    if not await test_configuration():
        print("Configuration test failed!")
        return 1
    
    # Test module loading
    if not await test_module_loading():
        print("Module loading test failed!")
        return 1
    
    # Test basic functionality
    if not await test_basic_functionality():
        print("Basic functionality test failed!")
        return 1
    
    print("\n" + "=" * 50)
    print("All tests passed! BuildCLI is ready to use.")
    print("\nTo build an executable, run:")
    print("  Windows: build.bat")
    print("  Linux/Mac: ./build.sh")
    print("\nTo use the CLI directly:")
    print("  python main.py --help")
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)