#!/usr/bin/env python3
"""
PyQt Import Converter (Optional)
================================

This script can optionally convert PyQt6 imports to use the compatibility layer.
This is only needed if you want maximum compatibility, but the current approach
of excluding x86 builds is probably simpler.

Usage:
    python convert_pyqt_imports.py --help
    python convert_pyqt_imports.py --dry-run  # Preview changes
    python convert_pyqt_imports.py --apply    # Apply changes
"""

import os
import re
import argparse
from pathlib import Path

def find_python_files(directory):
    """Find all Python files in the directory"""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Skip virtual environments and build directories
        dirs[:] = [d for d in dirs if d not in {'.venv', 'venv', 'build', 'dist', '__pycache__', '.git'}]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    return python_files

def analyze_pyqt_imports(file_path):
    """Analyze PyQt imports in a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"⚠️ Could not read {file_path}: {e}")
        return None, None, []
    
    # Patterns to find PyQt6 imports
    patterns = [
        (r'from PyQt6\.(\w+) import (.+)', 'from_import'),
        (r'import PyQt6\.(\w+)(?:\s+as\s+(\w+))?', 'direct_import'),
        (r'PyQt6\.(\w+)\.(\w+)', 'usage')
    ]
    
    imports_found = []
    
    for pattern, import_type in patterns:
        matches = re.finditer(pattern, content)
        for match in matches:
            imports_found.append({
                'type': import_type,
                'match': match,
                'line': content[:match.start()].count('\n') + 1,
                'text': match.group(0)
            })
    
    return content, file_path, imports_found

def convert_imports(content, imports_found):
    """Convert PyQt6 imports to compatibility layer"""
    new_content = content
    
    # Track what we need to import from compatibility layer
    compat_imports = set()
    
    # Process imports in reverse order to maintain positions
    for import_info in sorted(imports_found, key=lambda x: x['match'].start(), reverse=True):
        match = import_info['match']
        import_type = import_info['type']
        
        if import_type == 'from_import':
            # from PyQt6.QtWidgets import QWidget, QLabel
            module = match.group(1)  # QtWidgets
            imports = match.group(2)  # QWidget, QLabel
            
            # Add to compatibility imports
            compat_imports.add(f"from pyqt_compatibility import {imports}")
            
            # Remove the original import
            new_content = new_content[:match.start()] + new_content[match.end():]
            
        elif import_type == 'direct_import':
            # import PyQt6.QtWidgets as QtWidgets
            module = match.group(1)  # QtWidgets
            alias = match.group(2) if match.group(2) else module  # QtWidgets or custom alias
            
            # Add to compatibility imports
            compat_imports.add(f"from pyqt_compatibility import {module} as {alias}")
            
            # Remove the original import
            new_content = new_content[:match.start()] + new_content[match.end():]
    
    # Add compatibility imports at the beginning
    if compat_imports:
        import_lines = '\n'.join(sorted(compat_imports)) + '\n'
        
        # Find the best place to insert imports (after initial comments/docstrings)
        lines = new_content.split('\n')
        insert_line = 0
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped and not stripped.startswith('#') and not stripped.startswith('"""') and not stripped.startswith("'''"):
                insert_line = i
                break
        
        lines.insert(insert_line, import_lines)
        new_content = '\n'.join(lines)
    
    return new_content

def main():
    parser = argparse.ArgumentParser(description='Convert PyQt6 imports to compatibility layer')
    parser.add_argument('--directory', '-d', default='.', help='Directory to process (default: current)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be changed without applying')
    parser.add_argument('--apply', action='store_true', help='Apply the changes')
    parser.add_argument('--exclude', nargs='*', default=['test_*.py', '*_test.py'], help='File patterns to exclude')
    
    args = parser.parse_args()
    
    if not args.dry_run and not args.apply:
        print("⚠️ Please specify --dry-run or --apply")
        return
    
    print(f"🔍 Scanning for PyQt6 imports in: {args.directory}")
    print(f"🎯 Mode: {'DRY RUN' if args.dry_run else 'APPLY CHANGES'}")
    print()
    
    python_files = find_python_files(args.directory)
    print(f"📁 Found {len(python_files)} Python files")
    
    files_with_imports = []
    total_imports = 0
    
    for file_path in python_files:
        # Skip excluded files
        file_name = os.path.basename(file_path)
        if any(re.match(pattern.replace('*', '.*'), file_name) for pattern in args.exclude):
            continue
        
        content, _, imports_found = analyze_pyqt_imports(file_path)
        
        if imports_found:
            files_with_imports.append((file_path, content, imports_found))
            total_imports += len(imports_found)
            
            print(f"📄 {file_path}: {len(imports_found)} PyQt6 imports")
            for import_info in imports_found[:3]:  # Show first 3
                print(f"   Line {import_info['line']}: {import_info['text']}")
            if len(imports_found) > 3:
                print(f"   ... and {len(imports_found) - 3} more")
    
    print(f"\n📊 Summary: {len(files_with_imports)} files with {total_imports} PyQt6 imports")
    
    if not files_with_imports:
        print("✅ No PyQt6 imports found to convert")
        return
    
    if args.dry_run:
        print("\n🔍 DRY RUN - Showing what would be changed:")
        for file_path, content, imports_found in files_with_imports:
            print(f"\n📄 {file_path}:")
            new_content = convert_imports(content, imports_found)
            
            # Show diff-like output
            original_lines = content.split('\n')
            new_lines = new_content.split('\n')
            
            # Simple diff display
            for i, (old, new) in enumerate(zip(original_lines[:20], new_lines[:20])):
                if old != new:
                    print(f"  - {i+1}: {old}")
                    print(f"  + {i+1}: {new}")
    
    elif args.apply:
        print(f"\n🔧 Applying changes to {len(files_with_imports)} files...")
        
        for file_path, content, imports_found in files_with_imports:
            try:
                new_content = convert_imports(content, imports_found)
                
                # Backup original file
                backup_path = file_path + '.backup'
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # Write new content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                print(f"✅ {file_path} (backup: {backup_path})")
                
            except Exception as e:
                print(f"❌ Failed to convert {file_path}: {e}")
        
        print(f"\n🎉 Conversion complete!")
        print("📝 Original files backed up with .backup extension")
        print("🧪 Don't forget to test your application after conversion!")

if __name__ == "__main__":
    main()
