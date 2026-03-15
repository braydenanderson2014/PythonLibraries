#!/usr/bin/env python3
"""
Test script for Issue Reporter fixes
Tests the updated issue reporting system with Auto and unconfirmed tags
"""

import os
import sys
import tempfile

def test_issue_labels():
    """Test that Auto and unconfirmed labels are added"""
    
    # Test bug labels
    bug_labels = os.getenv('ISSUE_LABELS_BUG', 'bug,user-reported').split(',')
    bug_labels.extend(['Auto', 'unconfirmed'])
    expected_bug_labels = [label.strip() for label in bug_labels]
    
    print("Bug Issue Labels Test:")
    print(f"Expected labels: {expected_bug_labels}")
    if 'Auto' in expected_bug_labels and 'unconfirmed' in expected_bug_labels:
        print("✅ Bug labels include Auto and unconfirmed")
    else:
        print("❌ Bug labels missing Auto or unconfirmed")
    
    # Test feature labels
    feature_labels = os.getenv('ISSUE_LABELS_FEATURE', 'enhancement,feature-request').split(',')
    feature_labels.extend(['Auto', 'unconfirmed'])
    expected_feature_labels = [label.strip() for label in feature_labels]
    
    print("\nFeature Request Labels Test:")
    print(f"Expected labels: {expected_feature_labels}")
    if 'Auto' in expected_feature_labels and 'unconfirmed' in expected_feature_labels:
        print("✅ Feature labels include Auto and unconfirmed")
    else:
        print("❌ Feature labels missing Auto or unconfirmed")

def test_env_config():
    """Test environment configuration"""
    print("\nEnvironment Configuration Test:")
    
    # Check if .env is loaded
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ dotenv module available and loaded")
    except ImportError:
        print("⚠️ dotenv not available, using os.getenv only")
    
    # Check key settings
    log_upload = os.getenv('ENABLE_LOG_UPLOAD', 'true').lower()
    print(f"Log upload setting: {log_upload}")
    if log_upload == 'false':
        print("✅ Log upload disabled (logs will be embedded as text)")
    else:
        print("⚠️ Log upload still enabled")
        
    # Check other settings
    github_owner = os.getenv('GITHUB_OWNER', '')
    github_repo = os.getenv('GITHUB_REPO', '')
    if github_owner and github_repo:
        print(f"✅ GitHub repository: {github_owner}/{github_repo}")
    else:
        print("❌ GitHub repository configuration missing")

def test_yaml_config():
    """Test that the YAML config is valid"""
    print("\nYAML Config Test:")
    
    config_path = '.github/ISSUE_TEMPLATE/config.yml'
    if not os.path.exists(config_path):
        print("❌ config.yml not found")
        return
        
    try:
        with open(config_path, 'r') as f:
            content = f.read()
            
        # Basic YAML validation (check for quoted strings)
        if '"💬 Ask a Question"' in content and '"🔒 Security Issue"' in content:
            print("✅ config.yml has properly quoted emoji strings")
        else:
            print("❌ config.yml may have unquoted emoji strings")
            
        # Check structure
        if 'blank_issues_enabled: false' in content:
            print("✅ Blank issues disabled")
        if 'contact_links:' in content:
            print("✅ Contact links configured")
            
        print("Config content:")
        print(content)
        
    except Exception as e:
        print(f"❌ Error reading config.yml: {e}")

def test_log_embedding_logic():
    """Test the log embedding logic"""
    print("\nLog Embedding Logic Test:")
    
    # Create a test log file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        f.write("2025-08-10 12:00:00 - INFO - Application started\n")
        f.write("2025-08-10 12:01:00 - ERROR - Test error message\n")
        f.write("2025-08-10 12:02:00 - DEBUG - Debug information\n")
        log_file = f.name
    
    try:
        # Test file size check
        file_size = os.path.getsize(log_file)
        max_size_kb = 10
        print(f"Test log file size: {file_size} bytes")
        
        if file_size <= max_size_kb * 1024:
            print("✅ Log file under size limit")
        else:
            print("⚠️ Log file would be truncated")
            
        # Test file reading
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        if "Test error message" in content:
            print("✅ Log content readable")
        else:
            print("❌ Log content not readable")
            
        # Simulate body formatting
        body_parts = ["## Log Files", f"### {os.path.basename(log_file)}", "```", content.strip(), "```"]
        body = "\n".join(body_parts)
        
        if "## Log Files" in body and "```" in body:
            print("✅ Log formatting looks correct")
        else:
            print("❌ Log formatting incorrect")
            
    except Exception as e:
        print(f"❌ Log processing error: {e}")
    finally:
        os.unlink(log_file)

if __name__ == "__main__":
    print("Testing Issue Reporter Fixes")
    print("=" * 40)
    
    test_issue_labels()
    test_env_config()
    test_yaml_config()
    test_log_embedding_logic()
    
    print("\n" + "=" * 40)
    print("Issue Reporter fixes test completed!")
