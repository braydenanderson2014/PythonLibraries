#!/usr/bin/env python3
"""
Test script for the commercial PDF Utility changes
"""

import sys
import os

def test_imports():
    """Test that all required imports work"""
    print("Testing imports...")
    
    try:
        from main_application import MainWindow
        print("✅ Main application import successful")
    except ImportError as e:
        print(f"❌ Main application import failed: {e}")
        return False
    
    try:
        from update_system import UpdateManager, get_update_manager
        print("✅ Update system import successful")
    except ImportError as e:
        print(f"❌ Update system import failed: {e}")
        return False
    
    try:
        import packaging.version
        import requests
        try:
            from dotenv import load_dotenv
        except ImportError:
            print("⚠️  python-dotenv not available, but optional")
        print("✅ All dependencies available")
    except ImportError as e:
        print(f"❌ Dependency missing: {e}")
        return False
    
    return True

def test_env_file():
    """Test that .env file exists and has required variables"""
    print("\nTesting .env file...")
    
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    if not os.path.exists(env_file):
        print("❌ .env file not found")
        return False
    
    print("✅ .env file exists")
    
    # Load and check variables
    try:
        from dotenv import load_dotenv
        load_dotenv(env_file)
    except ImportError:
        print("⚠️  python-dotenv not available, reading .env manually")
        # Simple .env parsing
        with open(env_file, 'r') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    
    required_vars = [
        'GITHUB_OWNER', 'GITHUB_REPO', 'CURRENT_VERSION', 
        'APP_NAME', 'UPDATE_CHECK_URL'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")
        print("   Update .env file with your repository details")
    else:
        print("✅ All required environment variables present")
    
    return True

def show_summary():
    """Show summary of changes made"""
    print("\n" + "="*60)
    print("COMMERCIAL PDF UTILITY - CHANGES SUMMARY")
    print("="*60)
    
    print("\n🚫 REMOVED FEATURES:")
    print("   • PDF Editor tab (commented out)")
    print("   • Settings menu item (commented out)")
    
    print("\n✅ ADDED FEATURES:")
    print("   • Update system with GitHub integration")
    print("   • Check for Updates menu item in Help menu")
    print("   • Automatic background update checking")
    print("   • .env file for configuration")
    
    print("\n📁 NEW FILES CREATED:")
    print("   • update_system.py - Main update functionality")
    print("   • .env - Configuration file for GitHub details")
    
    print("\n📝 CONFIGURATION REQUIRED:")
    print("   • Edit .env file with your GitHub repository details")
    print("   • Replace 'your-username' with your GitHub username")
    print("   • Replace 'pdf-utility' with your repository name")
    print("   • Add GitHub personal access token (optional)")
    
    print("\n🚀 READY FOR COMMERCIAL DISTRIBUTION:")
    print("   • Simplified interface (no editor/settings)")
    print("   • Professional update system")
    print("   • Easy configuration via .env file")

if __name__ == "__main__":
    print("Commercial PDF Utility - Testing Configuration")
    print("=" * 50)
    
    success = True
    success &= test_imports()
    success &= test_env_file()
    
    show_summary()
    
    if success:
        print(f"\n🎉 READY! Your PDF Utility is configured for commercial distribution.")
        print("Remember to update the .env file with your repository details.")
    else:
        print(f"\n❌ Issues found. Please resolve them before distribution.")
