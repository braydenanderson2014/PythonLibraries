#!/usr/bin/env python3
"""
Test script for the Issue Reporting System
"""

import sys
import os

def test_imports():
    """Test that all required imports work"""
    print("Testing issue reporting system imports...")
    
    try:
        from issue_reporter import IssueReportDialog, get_issue_reporter
        print("✅ Issue reporter import successful")
    except ImportError as e:
        print(f"❌ Issue reporter import failed: {e}")
        return False
    
    try:
        import requests
        print("✅ Requests library available")
    except ImportError as e:
        print(f"❌ Requests library missing: {e}")
        return False
    
    return True

def test_env_configuration():
    """Test that .env file has issue reporting configuration"""
    print("\nTesting issue reporting configuration...")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("⚠️  python-dotenv not available, checking manually")
        # Simple .env parsing
        env_file = os.path.join(os.path.dirname(__file__), '.env')
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                for line in f:
                    if '=' in line and not line.strip().startswith('#'):
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value
    
    required_vars = [
        'GITHUB_OWNER', 'GITHUB_REPO', 'GITHUB_TOKEN', 
        'ISSUES_API_URL'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    else:
        print("✅ All required environment variables present")
    
    return True

def test_github_api_access():
    """Test GitHub API access"""
    print("\nTesting GitHub API access...")
    
    try:
        import requests
        
        github_owner = os.getenv('GITHUB_OWNER', '')
        github_repo = os.getenv('GITHUB_REPO', '')
        github_token = os.getenv('GITHUB_TOKEN', '')
        
        if not all([github_owner, github_repo]):
            print("❌ Missing GitHub repository configuration")
            return False
        
        # Test API access
        url = f"https://api.github.com/repos/{github_owner}/{github_repo}"
        headers = {}
        
        if github_token:
            headers['Authorization'] = f'token {github_token}'
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("✅ GitHub API access successful")
            print(f"   Repository: {github_owner}/{github_repo}")
            return True
        elif response.status_code == 401:
            print("❌ GitHub API authentication failed")
            print("   Check your GITHUB_TOKEN in .env file")
            return False
        elif response.status_code == 404:
            print("❌ Repository not found")
            print(f"   Check GITHUB_OWNER and GITHUB_REPO in .env file")
            return False
        else:
            print(f"❌ GitHub API error: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error accessing GitHub API: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def show_features():
    """Show the features of the issue reporting system"""
    print("\n" + "="*60)
    print("ISSUE REPORTING SYSTEM - FEATURES")
    print("="*60)
    
    print("\n🐛 BUG REPORTING:")
    print("   • Structured bug report forms")
    print("   • Steps to reproduce")
    print("   • Expected vs actual behavior")
    print("   • Automatic system information")
    print("   • Log file uploads (as private Gists)")
    
    print("\n💡 FEATURE REQUESTS:")
    print("   • Feature request forms")
    print("   • Detailed descriptions")
    print("   • Automatic labeling")
    
    print("\n📋 ISSUE MANAGEMENT:")
    print("   • View existing issues and features")
    print("   • Filter by type (bugs/features)")
    print("   • See issue status (open/closed)")
    print("   • Works with private repositories")
    
    print("\n🔧 TECHNICAL FEATURES:")
    print("   • GitHub API integration")
    print("   • Private Gist uploads for logs")
    print("   • Automatic labeling and formatting")
    print("   • Background submission")
    print("   • Progress indication")
    
    print("\n🔒 PRIVACY:")
    print("   • Works with private repositories")
    print("   • Log files uploaded as private Gists")
    print("   • No sensitive data exposed")
    print("   • Users can see known issues without repo access")

def show_usage_guide():
    """Show how to use the issue reporting system"""
    print("\n" + "="*60)
    print("USAGE GUIDE")
    print("="*60)
    
    print("\n📝 FOR USERS:")
    print("   1. Go to Help → Report Issue / Request Feature")
    print("   2. Choose Bug Report or Feature Request")
    print("   3. Fill in the required information")
    print("   4. Optionally attach log files")
    print("   5. Submit and receive issue number")
    print("   6. Check Known Issues tab to see all issues")
    
    print("\n👨‍💻 FOR DEVELOPERS:")
    print("   1. Issues are created in your GitHub repository")
    print("   2. Automatic labeling helps organize")
    print("   3. System information is included")
    print("   4. Log files are uploaded as private Gists")
    print("   5. Users can track status without repo access")

if __name__ == "__main__":
    print("Issue Reporting System - Test & Verification")
    print("=" * 50)
    
    success = True
    success &= test_imports()
    success &= test_env_configuration()
    success &= test_github_api_access()
    
    show_features()
    show_usage_guide()
    
    if success:
        print(f"\n🎉 SUCCESS! Issue reporting system is ready!")
        print("Users can now report issues and request features.")
    else:
        print(f"\n❌ Issues found. Please resolve them before using the system.")
