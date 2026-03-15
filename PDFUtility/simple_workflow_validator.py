#!/usr/bin/env python3
"""
Simple GitHub Actions workflow validation
"""

import os
import re

def check_workflow_issues(file_path):
    """Check for common workflow issues"""
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for duplicate context declaration
        if 'const context = github.context' in content:
            issues.append("❌ Found 'const context = github.context' - this is already available in github-script")
        
        # Check for basic YAML structure
        if not content.strip().startswith('name:'):
            issues.append("⚠️  File doesn't start with 'name:' field")
        
        # Check for required sections
        required_sections = ['name:', 'on:', 'jobs:']
        for section in required_sections:
            if section not in content:
                issues.append(f"⚠️  Missing required section: {section}")
        
        # Check for proper indentation (basic check)
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if line.strip() and line.startswith('\t'):
                issues.append(f"⚠️  Line {i}: Using tabs instead of spaces for indentation")
                break  # Only report first occurrence
        
        return issues
        
    except Exception as e:
        return [f"❌ Error reading file: {e}"]

def main():
    """Main validation function"""
    print("🔍 GitHub Actions Workflow Validation")
    print("=" * 45)
    
    workflows_dir = os.path.join('.github', 'workflows')
    
    if not os.path.exists(workflows_dir):
        print(f"❌ Workflows directory not found: {workflows_dir}")
        return
    
    workflow_files = []
    for filename in os.listdir(workflows_dir):
        if filename.endswith(('.yml', '.yaml')):
            filepath = os.path.join(workflows_dir, filename)
            workflow_files.append((filename, filepath))
    
    if not workflow_files:
        print("❌ No workflow files found")
        return
    
    print(f"Found {len(workflow_files)} workflow files:\n")
    
    all_clean = True
    
    for filename, filepath in workflow_files:
        print(f"📄 {filename}")
        print("-" * 30)
        
        issues = check_workflow_issues(filepath)
        
        if issues:
            all_clean = False
            for issue in issues:
                print(f"   {issue}")
        else:
            print("   ✅ No issues found")
        
        print()
    
    print("=" * 45)
    
    if all_clean:
        print("🎉 All workflow files look good!")
    else:
        print("⚠️  Some issues found - see details above")
        print("\n💡 Common fixes:")
        print("   • Remove 'const context = github.context' from github-script actions")
        print("   • Use spaces instead of tabs for indentation")
        print("   • Ensure all required sections are present")

if __name__ == "__main__":
    main()
