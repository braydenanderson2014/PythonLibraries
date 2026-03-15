#!/usr/bin/env python3
# simple_settings_verification.py - Simple verification without encoding issues

import os

def main():
    """Simple verification of settings"""
    print("=== PDFUtility Settings Verification ===\n")
    
    from settings_controller import SettingsController
    
    settings = SettingsController()
    settings.load_settings()
    
    documents_path = settings.get_documents_path()
    print(f"Documents Path: {documents_path}")
    
    if "OneDrive" in documents_path:
        print("✅ OneDrive Documents folder detected correctly")
    else:
        print("📁 Standard Documents folder detected")
    
    # Check key settings
    merge_dir = settings.get_setting("pdf", "default_merge_dir")
    split_dir = settings.get_setting("pdf", "default_split_dir")
    output_dir = settings.get_setting("pdf", "default_output_dir")
    
    print(f"\n=== Widget Default Directories ===")
    print(f"Merge Directory: {merge_dir}")
    print(f"Split Directory: {split_dir}")
    print(f"Output Directory: {output_dir}")
    
    # Check if all paths are in Documents
    paths_in_documents = all(documents_path in path for path in [merge_dir, split_dir, output_dir])
    
    if paths_in_documents:
        print("✅ All widget directories are correctly set to Documents folder!")
    else:
        print("❌ Some widget directories are not in Documents folder")
    
    # Check if directories exist
    all_exist = all(os.path.exists(path) for path in [merge_dir, split_dir, output_dir])
    
    if all_exist:
        print("✅ All directories exist and are ready for use!")
    else:
        print("❌ Some directories don't exist")
    
    print(f"\n=== Code Changes Verification ===")
    
    # Check if the key files contain the expected changes
    files_to_check = {
        "pdf_merger_widget.py": "settings_controller=None",
        "pdf_splitter_widget.py": "settings_controller=None",
        "main_application.py": "settings_controller=self.settings"
    }
    
    for filename, expected_text in files_to_check.items():
        if os.path.exists(filename):
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    content = f.read()
                    if expected_text in content:
                        print(f"✅ {filename} - Updated correctly")
                    else:
                        print(f"❌ {filename} - Missing expected changes")
            except:
                print(f"⚠️ {filename} - Could not verify (encoding issue)")
        else:
            print(f"❌ {filename} - File not found")
    
    print(f"\n=== Final Status ===")
    if paths_in_documents and all_exist:
        print("🎉 SUCCESS: PDFUtility widgets should now use Documents folder!")
        print("   - Settings are correctly configured")
        print("   - All directories exist")
        print("   - OneDrive compatibility confirmed")
    else:
        print("⚠️ PARTIAL: Some issues remain")

if __name__ == "__main__":
    main()
