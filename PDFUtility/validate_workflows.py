#!/usr/bin/env python3
"""
Validate GitHub Actions workflow files for syntax errors
"""

import yaml
import os

def validate_workflow_file(file_path):
    """Validate a single workflow YAML file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse YAML
        parsed = yaml.safe_load(content)
        
        print(f"✅ {os.path.basename(file_path)} - Valid YAML syntax")
        
        # Check for required workflow keys
        required_keys = ['name', 'on', 'jobs']
        missing_keys = [key for key in required_keys if key not in parsed]
        
        if missing_keys:
            print(f"⚠️  Missing required keys: {', '.join(missing_keys)}")
        else:
            print(f"✅ {os.path.basename(file_path)} - All required keys present")
        
        # Check for common issues in the script section
        script_content = str(content)
        if 'const context = github.context' in script_content:
            print(f"❌ {os.path.basename(file_path)} - Found 'const context = github.context' declaration")
            print("   This causes errors in github-script action. Use 'context' directly.")
            return False
        
        return True
        
    except yaml.YAMLError as e:
        print(f"❌ {os.path.basename(file_path)} - YAML syntax error: {e}")
        return False
    except FileNotFoundError:
        print(f"❌ {os.path.basename(file_path)} - File not found")
        return False
    except Exception as e:
        print(f"❌ {os.path.basename(file_path)} - Error: {e}")
        return False

def main():
    """Main validation function"""
    print("🔍 Validating GitHub Actions Workflow Files")
    print("=" * 50)
    
    # Find workflow files
    workflows_dir = os.path.join(os.path.dirname(__file__), '.github', 'workflows')
    
    if not os.path.exists(workflows_dir):
        print(f"❌ Workflows directory not found: {workflows_dir}")
        return
    
    workflow_files = []
    for filename in os.listdir(workflows_dir):
        if filename.endswith('.yml') or filename.endswith('.yaml'):
            workflow_files.append(os.path.join(workflows_dir, filename))
    
    if not workflow_files:
        print("❌ No workflow files found")
        return
    
    print(f"Found {len(workflow_files)} workflow files:")
    for file in workflow_files:
        print(f"  - {os.path.basename(file)}")
    
    print("\n" + "=" * 50)
    
    # Validate each file
    all_valid = True
    for file_path in workflow_files:
        is_valid = validate_workflow_file(file_path)
        all_valid = all_valid and is_valid
        print()
    
    # Summary
    print("=" * 50)
    if all_valid:
        print("🎉 All workflow files are valid!")
    else:
        print("❌ Some workflow files have issues that need to be fixed")
        print("\n💡 Tips:")
        print("   - Check YAML indentation (use spaces, not tabs)")
        print("   - Remove 'const context = github.context' in github-script actions")
        print("   - Ensure all required workflow keys are present")

if __name__ == "__main__":
    main()
