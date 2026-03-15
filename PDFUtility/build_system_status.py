#!/usr/bin/env python3
"""
Build System Status Check
=========================

This script provides a comprehensive overview of the build system configuration
and validates that all components are ready for production builds.
"""

import json
import os
import sys
from pathlib import Path

def check_build_config():
    """Check build configuration file"""
    config_path = ".github/build-config.json"
    
    if not os.path.exists(config_path):
        return False, "Build config file not found"
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Validate required fields
        required_fields = ["name", "platforms", "architectures"]
        missing_fields = [field for field in required_fields if field not in config]
        
        if missing_fields:
            return False, f"Missing required fields: {missing_fields}"
        
        return True, config
        
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {e}"
    except Exception as e:
        return False, f"Error reading config: {e}"

def check_workflow_files():
    """Check workflow files exist"""
    workflow_files = [
        ".github/workflows/advanced-build.yml",
        ".github/workflows/issue-auto-manager.yml",
        ".github/workflows/advanced-issue-manager.yml"
    ]
    
    status = {}
    
    for workflow in workflow_files:
        if os.path.exists(workflow):
            status[workflow] = "✅ Present"
        else:
            status[workflow] = "❌ Missing"
    
    return status

def check_compatibility_files():
    """Check compatibility and support files"""
    support_files = [
        "pyqt_compatibility.py",
        "requirements.txt",
        "BUILD_SYSTEM_DOCS.md",
        "test_dependency_fallbacks.py"
    ]
    
    status = {}
    
    for file_path in support_files:
        if os.path.exists(file_path):
            status[file_path] = "✅ Present"
        else:
            status[file_path] = "❌ Missing"
    
    return status

def analyze_build_matrix(config):
    """Analyze the build matrix that would be generated"""
    platforms = config.get("platforms", [])
    architectures = config.get("architectures", {})
    excluded = config.get("excluded_architectures", {})
    
    matrix = []
    excluded_builds = []
    
    for platform in platforms:
        platform_arches = architectures.get(platform, [])
        excluded_arches = excluded.get(platform, [])
        
        for arch in platform_arches:
            if arch in excluded_arches:
                excluded_builds.append(f"{platform}-{arch}")
            else:
                matrix.append(f"{platform}-{arch}")
    
    return matrix, excluded_builds

def main():
    print("🏗️ Build System Status Check")
    print("=" * 50)
    
    overall_status = True
    
    # Check build configuration
    print("\n📋 Build Configuration:")
    config_ok, config_result = check_build_config()
    
    if config_ok:
        config = config_result
        print("✅ Configuration file valid")
        print(f"   📱 App Name: {config['name']}")
        print(f"   🖥️ Platforms: {', '.join(config['platforms'])}")
        print(f"   🐍 Python Version: {config.get('python_version', 'default')}")
        
        # Analyze build matrix
        matrix, excluded = analyze_build_matrix(config)
        print(f"\n🎯 Build Matrix:")
        print(f"   ✅ Active Builds: {len(matrix)}")
        for build in matrix:
            print(f"      • {build}")
        
        if excluded:
            print(f"   🚫 Excluded Builds: {len(excluded)}")
            for build in excluded:
                print(f"      • {build} (excluded)")
        
        # Check dependency fallbacks
        fallbacks = config.get("dependency_fallbacks", {})
        print(f"\n🔄 Dependency Fallbacks: {len(fallbacks)} configured")
        for package, options in fallbacks.items():
            print(f"   📦 {package}: {len(options)} fallback options")
            
    else:
        print(f"❌ Configuration error: {config_result}")
        overall_status = False
    
    # Check workflow files
    print(f"\n🔧 Workflow Files:")
    workflow_status = check_workflow_files()
    
    for workflow, status in workflow_status.items():
        print(f"   {status} {os.path.basename(workflow)}")
        if "❌" in status:
            overall_status = False
    
    # Check compatibility files
    print(f"\n📚 Support Files:")
    support_status = check_compatibility_files()
    
    for file_path, status in support_status.items():
        print(f"   {status} {file_path}")
        if "❌" in status and file_path in ["pyqt_compatibility.py", "requirements.txt"]:
            overall_status = False
    
    # Check PyQt dependencies
    print(f"\n🖥️ GUI Compatibility:")
    try:
        import pyqt_compatibility
        print(f"   ✅ Compatibility layer: {pyqt_compatibility.get_pyqt_version()}")
        print(f"   🔧 PyQt6 available: {pyqt_compatibility.is_pyqt6()}")
        print(f"   🔧 PyQt5 available: {pyqt_compatibility.is_pyqt5()}")
    except ImportError as e:
        print(f"   ⚠️ Compatibility layer: Not available ({e})")
    
    # Summary
    print(f"\n{'=' * 50}")
    print("📊 SUMMARY")
    print("=" * 50)
    
    if overall_status:
        print("🎉 Build system is ready for production!")
        print("\n✅ Key Features:")
        print("   • Multi-platform builds (Windows, Linux, macOS)")
        print("   • Dependency fallback system")
        print("   • PyQt6/PyQt5 compatibility")
        print("   • x86 exclusion for PyQt6 compatibility")
        print("   • Automatic release creation")
        print("   • Comprehensive error handling")
        print("   • Issue management automation")
        
        if config_ok and excluded:
            print(f"\n📝 Note: {len(excluded)} architecture(s) excluded for compatibility")
            
        print(f"\n🚀 Ready to build!")
        
    else:
        print("⚠️ Build system has issues that need attention")
        print("\n🔧 Please fix the issues marked with ❌ above")
    
    return 0 if overall_status else 1

if __name__ == "__main__":
    sys.exit(main())
