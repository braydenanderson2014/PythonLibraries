#!/usr/bin/env python3
"""
Validation script for the enhanced AboutDialog changes
This script validates the code syntax and structure without running the GUI
"""

import sys
import os
import ast

def validate_about_dialog_code():
    """Validate that the AboutDialog code is syntactically correct"""
    
    # Read the main_application.py file
    main_app_path = os.path.join(os.path.dirname(__file__), 'main_application.py')
    
    try:
        with open(main_app_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # Parse the code to check for syntax errors
        ast.parse(code)
        print("✅ AboutDialog code syntax is valid")
        
        # Check for the AboutDialog class
        if 'class AboutDialog(QDialog):' in code:
            print("✅ AboutDialog class found")
        else:
            print("❌ AboutDialog class not found")
            return False
        
        # Check for the new methods
        if 'def create_application_tab(self):' in code:
            print("✅ create_application_tab method found")
        else:
            print("❌ create_application_tab method not found")
            return False
            
        if 'def create_company_tab(self):' in code:
            print("✅ create_company_tab method found")
        else:
            print("❌ create_company_tab method not found")
            return False
        
        # Check for company-related content
        if 'PDF Solutions Inc.' in code:
            print("✅ Company name found in code")
        else:
            print("❌ Company name not found in code")
            return False
            
        # Check for tab widget usage
        if 'QTabWidget' in code and 'tab_widget.addTab' in code:
            print("✅ Tab widget implementation found")
        else:
            print("❌ Tab widget implementation not found")
            return False
            
        # Check for logo handling
        if 'company_logo.png' in code:
            print("✅ Company logo reference found")
        else:
            print("❌ Company logo reference not found")
            return False
        
        print("✅ All validation checks passed!")
        return True
        
    except FileNotFoundError:
        print("❌ main_application.py file not found")
        return False
    except SyntaxError as e:
        print(f"❌ Syntax error in code: {e}")
        return False
    except Exception as e:
        print(f"❌ Error validating code: {e}")
        return False

def check_logo_files():
    """Check if the logo files exist"""
    
    logo_dir = os.path.join(os.path.dirname(__file__), 'assets', 'images')
    
    files_to_check = [
        'company_logo.png',
        'company_logo.ico',
        'README_LOGO_SETUP.md'
    ]
    
    print("\n📁 Checking logo files:")
    
    for filename in files_to_check:
        filepath = os.path.join(logo_dir, filename)
        if os.path.exists(filepath):
            print(f"✅ {filename} exists")
        else:
            print(f"❌ {filename} not found")
    
    return True

def main():
    """Main validation function"""
    print("🔍 Validating AboutDialog Enhancements")
    print("=" * 50)
    
    # Validate the code
    code_valid = validate_about_dialog_code()
    
    # Check logo files
    check_logo_files()
    
    # Summary
    print("\n" + "=" * 50)
    if code_valid:
        print("🎉 AboutDialog enhancement validation completed successfully!")
        print("\n📋 What's New:")
        print("   • Tabbed interface with Application and Company tabs")
        print("   • Company logo support (PNG/ICO)")
        print("   • Enhanced visual design with proper styling")
        print("   • Comprehensive company information section")
        print("   • Contact details and social media links")
        print("   • Technical information display")
        print("\n⚠️  Note: Replace placeholder logo files with actual images")
    else:
        print("❌ Validation failed - please check the errors above")

if __name__ == "__main__":
    main()
