#!/usr/bin/env python3
# build_script.py - Interactive PyInstaller Build Tool

import os
import sys
import subprocess
import glob
import json
import re
from datetime import datetime
from pathlib import Path

class PyInstallerBuilder:
    def __init__(self):
        self.program_name = ""
        self.build_status = ""
        self.main_entry = ""
        self.additional_files = []
        self.build_options = {}
        self.changelog_file = ""
        self.known_issues = []
        self.build_notes = ""
        
    def get_date_string(self):
        """Get current date in MDDYYYY format"""
        return datetime.now().strftime("%m%d%Y")
    
    def find_changelog_files(self):
        """Find potential changelog files in the project"""
        changelog_patterns = [
            "changelog.md", "CHANGELOG.md", "changelog.txt", "CHANGELOG.txt",
            "changelog.rst", "CHANGELOG.rst", "changes.md", "CHANGES.md",
            "history.md", "HISTORY.md", "release-notes.md", "RELEASE-NOTES.md"
        ]
        
        search_directories = [
            ".",  # Current directory
            "docs",
            "documentation", 
            "release",
            "releases"
        ]
        
        found_changelogs = []
        
        for directory in search_directories:
            if os.path.exists(directory):
                for pattern in changelog_patterns:
                    search_path = os.path.join(directory, pattern)
                    if os.path.isfile(search_path):
                        found_changelogs.append(search_path)
        
        # Remove duplicates and sort
        return sorted(list(set(found_changelogs)))
    
    def select_changelog_file(self):
        """Allow user to select or specify changelog file"""
        found_changelogs = self.find_changelog_files()
        
        print("\n📄 Changelog Management:")
        print("  1. Add to existing changelog")
        print("  2. Create new changelog")
        print("  3. Skip changelog processing")
        
        while True:
            try:
                choice = input("\nSelect option (1-3): ").strip()
                
                if choice == "1":
                    # Add to existing changelog
                    if not found_changelogs:
                        print("\n📄 No changelog files found in common locations.")
                        manual_changelog = input("Enter changelog file path manually: ").strip()
                        if manual_changelog and os.path.exists(manual_changelog):
                            print(f"✅ Using manually specified changelog: {manual_changelog}")
                            self.changelog_file = manual_changelog
                            return True
                        else:
                            print("❌ File not found! Try creating a new changelog instead.")
                            continue
                    else:
                        print(f"\n📄 Found {len(found_changelogs)} potential changelog file(s):")
                        for i, changelog in enumerate(found_changelogs, 1):
                            file_size = os.path.getsize(changelog)
                            size_kb = file_size / 1024
                            print(f"  {i}. {changelog} ({size_kb:.1f} KB)")
                        
                        print(f"  {len(found_changelogs) + 1}. Enter custom path")
                        
                        while True:
                            try:
                                file_choice = input(f"\nSelect changelog file (1-{len(found_changelogs) + 1}): ").strip()
                                
                                if file_choice.isdigit():
                                    idx = int(file_choice) - 1
                                    
                                    if 0 <= idx < len(found_changelogs):
                                        selected_changelog = found_changelogs[idx]
                                        confirm = input(f"Use '{selected_changelog}' as the changelog? (Y/n): ").lower()
                                        if confirm not in ['n', 'no']:
                                            print(f"✅ Selected existing changelog: {selected_changelog}")
                                            self.changelog_file = selected_changelog
                                            return True
                                    
                                    elif idx == len(found_changelogs):
                                        # Custom path
                                        custom_changelog = input("Enter custom changelog file path: ").strip()
                                        if custom_changelog and os.path.exists(custom_changelog):
                                            print(f"✅ Using custom changelog: {custom_changelog}")
                                            self.changelog_file = custom_changelog
                                            return True
                                        else:
                                            print("❌ File not found!")
                                            continue
                                    
                                    else:
                                        print("❌ Invalid selection!")
                                        continue
                                
                                else:
                                    print("❌ Please enter a number!")
                                    
                            except ValueError:
                                print("❌ Please enter a valid number!")
                                
                elif choice == "2":
                    # Create new changelog
                    new_changelog = input("Enter new changelog filename (e.g., 'changelog.md'): ").strip()
                    if new_changelog:
                        # Don't auto-append extension or modify filename - use exactly what user specified
                        if os.path.exists(new_changelog):
                            overwrite = input(f"File '{new_changelog}' already exists. Overwrite? (y/N): ").lower()
                            if overwrite not in ['y', 'yes']:
                                continue
                        
                        print(f"✅ Will create new changelog: {new_changelog}")
                        self.changelog_file = new_changelog
                        return True
                    else:
                        print("❌ Filename cannot be empty!")
                        continue
                
                elif choice == "3":
                    # Skip changelog
                    print("❌ Skipping changelog processing.")
                    return False
                    
                else:
                    print("❌ Invalid selection!")
                    continue
                    
            except ValueError:
                print("❌ Please enter a valid number!")
            except KeyboardInterrupt:
                print("\n❌ Build cancelled by user.")
                sys.exit(0)
    
    def get_version_info(self):
        """Get version information for the changelog entry"""
        print(f"\n🔢 Version Information:")
        
        # Try to extract version from existing changelog
        existing_version = self.extract_latest_version()
        if existing_version:
            print(f"Latest version found in changelog: {existing_version}")
            suggested_version = self.suggest_next_version(existing_version)
            print(f"Suggested next version: {suggested_version}")
        
        while True:
            if existing_version:
                version = input(f"Enter version number [{suggested_version}]: ").strip()
                if not version:
                    version = suggested_version
            else:
                version = input("Enter version number (e.g., '1.0.0', '2.1', '3'): ").strip()
            
            if version:
                confirm = input(f"Use version '{version}'? (Y/n): ").lower()
                if confirm not in ['n', 'no']:
                    return version
            else:
                print("❌ Version cannot be empty!")
    
    def extract_latest_version(self):
        """Extract the latest version number from existing changelog"""
        if not self.changelog_file or not os.path.exists(self.changelog_file):
            return None
        
        try:
            with open(self.changelog_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for version patterns like "# Version X.Y.Z", "# Version X", etc.
            version_patterns = [
                r'^#\s*Version\s+(\d+(?:\.\d+)*)',  # # Version 1.2.3
                r'^Version\s+(\d+(?:\.\d+)*)',      # Version 1.2.3
                r'^#?\s*v(\d+(?:\.\d+)*)',          # v1.2.3
                r'^#?\s*(\d+(?:\.\d+)*)',           # 1.2.3
            ]
            
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                for pattern in version_patterns:
                    match = re.match(pattern, line, re.IGNORECASE)
                    if match:
                        return match.group(1)
            
            return None
            
        except Exception as e:
            print(f"⚠️  Error reading changelog for version extraction: {e}")
            return None
    
    def suggest_next_version(self, current_version):
        """Suggest the next version number based on current version"""
        try:
            # Split version into parts
            parts = current_version.split('.')
            
            # If it's a single number (e.g., "3"), increment it
            if len(parts) == 1:
                return str(int(parts[0]) + 1)
            
            # If it's X.Y or X.Y.Z, increment the last part
            parts[-1] = str(int(parts[-1]) + 1)
            return '.'.join(parts)
            
        except (ValueError, IndexError):
            # If we can't parse it, just suggest incrementing by 1
            return f"{current_version}.1"
    
    def get_changelog_content(self):
        """Get changelog content using interactive menu system"""
        changelog_data = {
            'known_issues': [],
            'resolved_issues': [],
            'new_features': [],
            'improvements': [],
            'build_notes': [],
            'other': []
        }
        
        while True:
            self.clear_screen()
            print("=" * 60)
            print("  📝 CHANGELOG BUILDER")
            print("=" * 60)
            
            # Show current content summary
            total_items = sum(len(items) for items in changelog_data.values())
            print(f"Current changelog items: {total_items}")
            
            for category, items in changelog_data.items():
                if items:
                    category_name = category.replace('_', ' ').title()
                    print(f"  • {category_name}: {len(items)} items")
            
            print("\n" + "=" * 60)
            print("  MENU OPTIONS")
            print("=" * 60)
            print("  1. Add Known Issue")
            print("  2. Add Resolved Issue") 
            print("  3. Add New Feature")
            print("  4. Add Improvement")
            print("  5. Add Build Note")
            print("  6. Add Other Item")
            print("  7. Review All Items")
            print("  8. Remove Item")
            print("  9. Finish & Continue")
            print("  10. Back to Main Menu")
            print("=" * 60)
            
            choice = input("\nSelect option (1-10): ").strip()
            
            if choice == "1":
                self.add_changelog_item(changelog_data, 'known_issues', 'Known Issue')
            elif choice == "2":
                self.add_changelog_item(changelog_data, 'resolved_issues', 'Resolved Issue')
            elif choice == "3":
                self.add_changelog_item(changelog_data, 'new_features', 'New Feature')
            elif choice == "4":
                self.add_changelog_item(changelog_data, 'improvements', 'Improvement')
            elif choice == "5":
                self.add_changelog_item(changelog_data, 'build_notes', 'Build Note')
            elif choice == "6":
                self.add_changelog_item(changelog_data, 'other', 'Other')
            elif choice == "7":
                self.review_changelog_items(changelog_data)
            elif choice == "8":
                self.remove_changelog_item(changelog_data)
            elif choice == "9":
                if total_items == 0:
                    print("\n⚠️  No changelog items added!")
                    input("Press Enter to continue...")
                    continue
                return self.format_changelog_data(changelog_data)
            elif choice == "10":
                return None  # Back to main menu
            else:
                print("❌ Invalid option!")
                input("Press Enter to continue...")
    
    def add_changelog_item(self, changelog_data, category, category_display):
        """Add an item to a specific changelog category"""
        print(f"\n📝 Add {category_display}:")
        print("Enter the item description (or press Enter to cancel):")
        
        item = input(f"{category_display}: ").strip()
        if item:
            changelog_data[category].append(item)
            print(f"✅ Added {category_display}: {item}")
        else:
            print("❌ Cancelled - no item added")
        
        input("Press Enter to continue...")
    
    def review_changelog_items(self, changelog_data):
        """Review all changelog items"""
        self.clear_screen()
        print("=" * 60)
        print("  📋 CHANGELOG REVIEW")
        print("=" * 60)
        
        total_items = 0
        for category, items in changelog_data.items():
            if items:
                category_name = category.replace('_', ' ').title()
                print(f"\n{category_name}:")
                for i, item in enumerate(items, 1):
                    print(f"  {i}. {item}")
                    total_items += 1
        
        if total_items == 0:
            print("No changelog items added yet.")
        
        print("=" * 60)
        input("Press Enter to continue...")
    
    def remove_changelog_item(self, changelog_data):
        """Remove an item from changelog"""
        # First, show all items with global numbering
        all_items = []
        for category, items in changelog_data.items():
            for item in items:
                all_items.append((category, item))
        
        if not all_items:
            print("\n⚠️  No items to remove!")
            input("Press Enter to continue...")
            return
        
        self.clear_screen()
        print("=" * 60)
        print("  🗑️  REMOVE CHANGELOG ITEM")
        print("=" * 60)
        
        for i, (category, item) in enumerate(all_items, 1):
            category_name = category.replace('_', ' ').title()
            print(f"  {i}. [{category_name}] {item}")
        
        print("=" * 60)
        
        try:
            choice = input(f"Enter item number to remove (1-{len(all_items)}) or press Enter to cancel: ").strip()
            if not choice:
                return
            
            idx = int(choice) - 1
            if 0 <= idx < len(all_items):
                category, item = all_items[idx]
                changelog_data[category].remove(item)
                print(f"✅ Removed: {item}")
            else:
                print("❌ Invalid item number!")
        except ValueError:
            print("❌ Please enter a valid number!")
        
        input("Press Enter to continue...")
    
    def format_changelog_data(self, changelog_data):
        """Format changelog data into a list of items for the version entry"""
        formatted_items = []
        
        # Add program information at the top
        formatted_items.append(f"**Program:** {self.program_name}")
        formatted_items.append(f"**Build Type:** {self.build_status}")
        formatted_items.append("")  # Empty line for spacing
        
        # Add items in a specific order with category labels
        if changelog_data['new_features']:
            formatted_items.append("## NEW FEATURES:")
            for item in changelog_data['new_features']:
                formatted_items.append(f"* {item}")
            formatted_items.append("")  # Empty line after section
        
        if changelog_data['improvements']:
            formatted_items.append("## IMPROVEMENTS:")
            for item in changelog_data['improvements']:
                formatted_items.append(f"* {item}")
            formatted_items.append("")
        
        if changelog_data['resolved_issues']:
            formatted_items.append("## RESOLVED ISSUES:")
            for item in changelog_data['resolved_issues']:
                formatted_items.append(f"* {item}")
            formatted_items.append("")
        
        if changelog_data['known_issues']:
            formatted_items.append("## KNOWN ISSUES:")
            for item in changelog_data['known_issues']:
                formatted_items.append(f"* {item}")
            formatted_items.append("")
        
        if changelog_data['build_notes']:
            formatted_items.append("## BUILD NOTES:")
            for item in changelog_data['build_notes']:
                formatted_items.append(f"* {item}")
            formatted_items.append("")
        
        if changelog_data['other']:
            formatted_items.append("## OTHER:")
            for item in changelog_data['other']:
                formatted_items.append(f"* {item}")
            formatted_items.append("")
        
        # Remove trailing empty line if present
        if formatted_items and formatted_items[-1] == "":
            formatted_items.pop()
        
        return formatted_items
    
    def update_main_changelog(self, version, changelog_items):
        """Update the main changelog file with new version entry at the top"""
        if not self.changelog_file:
            return False
        
        # Create new entry with proper markdown formatting
        new_entry = []
        new_entry.append(f"# Version {version}")
        new_entry.append("")  # Empty line after version header
        
        # Add changelog items (already formatted with categories)
        for item in changelog_items:
            if item.strip():  # Only add non-empty lines
                new_entry.append(item)
        
        new_entry.append("")  # Empty line after version section
        new_entry.append("---")  # Horizontal rule to separate versions
        new_entry.append("")  # Empty line after separator
        
        # Read existing content (if file exists)
        existing_content = ""
        if os.path.exists(self.changelog_file):
            try:
                with open(self.changelog_file, 'r', encoding='utf-8') as f:
                    existing_content = f.read().strip()
                print(f"📖 Read existing changelog ({len(existing_content)} characters)")
            except Exception as e:
                print(f"⚠️  Error reading existing changelog: {e}")
                existing_content = ""
        else:
            print("📄 Creating new changelog file")
        
        # Combine new entry with existing content
        final_content = '\n'.join(new_entry)
        if existing_content:
            final_content += '\n' + existing_content
        
        # Write updated content
        try:
            # Ensure directory exists
            changelog_dir = os.path.dirname(self.changelog_file)
            if changelog_dir and not os.path.exists(changelog_dir):
                os.makedirs(changelog_dir)
            
            with open(self.changelog_file, 'w', encoding='utf-8') as f:
                f.write(final_content)
            
            print(f"✅ Successfully updated changelog: {self.changelog_file}")
            print(f"   📌 Added Version {version} at the top")
            print(f"   📌 Added {len([item for item in changelog_items if item.strip()])} changelog items")
            if existing_content:
                print(f"   📌 Preserved existing content below new entry")
            else:
                print(f"   📌 Created new changelog file")
            
            return True
            
        except Exception as e:
            print(f"❌ Error updating changelog: {e}")
            return False
    
    def preview_changelog_update(self, version, changelog_items):
        """Preview what the changelog update will look like"""
        print("\n" + "=" * 60)
        print("📋 CHANGELOG PREVIEW")
        print("=" * 60)
        print(f"# Version {version}")
        print("")  # Empty line after header
        for item in changelog_items:
            if item.strip():  # Only show non-empty lines
                print(item)
        print("")
        print("---")  # Horizontal rule
        
        if os.path.exists(self.changelog_file):
            print("")
            print("--- Existing content will appear below ---")
            try:
                with open(self.changelog_file, 'r', encoding='utf-8') as f:
                    existing = f.read().strip()
                    # Show first few lines of existing content
                    lines = existing.split('\n')
                    for i, line in enumerate(lines[:5]):
                        print(line)
                    if len(lines) > 5:
                        print(f"... and {len(lines) - 5} more lines")
            except Exception as e:
                print(f"(Could not preview existing content: {e})")
        
        print("=" * 60)
    
    def parse_current_changelog(self):
        """Parse the current changelog to extract latest version information"""
        if not self.changelog_file or not os.path.exists(self.changelog_file):
            return None
        
        try:
            with open(self.changelog_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for the latest version section
            lines = content.split('\n')
            latest_version = {}
            
            # Find the first version header (e.g., "# Version 1.0.0")
            version_pattern = re.compile(r'^#\s*Version\s+(.+)', re.IGNORECASE)
            
            current_section = None
            for i, line in enumerate(lines):
                line_stripped = line.strip()
                
                # Check for version header
                match = version_pattern.match(line_stripped)
                if match and not latest_version:  # Only get the first (latest) version
                    latest_version['version'] = match.group(1).strip()
                    latest_version['program'] = None
                    latest_version['build_type'] = None
                    latest_version['new_features'] = []
                    latest_version['improvements'] = []
                    latest_version['resolved_issues'] = []
                    latest_version['known_issues'] = []
                    latest_version['build_notes'] = []
                    latest_version['other'] = []
                    continue
                
                if not latest_version:
                    continue
                
                # Extract program and build type info
                if line_stripped.startswith('**Program:**'):
                    latest_version['program'] = line_stripped.replace('**Program:**', '').strip()
                elif line_stripped.startswith('**Build Type:**'):
                    latest_version['build_type'] = line_stripped.replace('**Build Type:**', '').strip()
                
                # Check for section headers
                elif line_stripped.startswith('## NEW FEATURES:'):
                    current_section = 'new_features'
                elif line_stripped.startswith('## IMPROVEMENTS:'):
                    current_section = 'improvements'
                elif line_stripped.startswith('## RESOLVED ISSUES:'):
                    current_section = 'resolved_issues'
                elif line_stripped.startswith('## KNOWN ISSUES:'):
                    current_section = 'known_issues'
                elif line_stripped.startswith('## BUILD NOTES:'):
                    current_section = 'build_notes'
                elif line_stripped.startswith('## OTHER:'):
                    current_section = 'other'
                elif line_stripped.startswith('# Version') and i > 0:
                    # Hit the next version, stop parsing
                    break
                elif line_stripped == '---':
                    # Hit separator, stop parsing this version
                    break
                elif current_section and line_stripped.startswith('* '):
                    # Add bullet point to current section
                    latest_version[current_section].append(line_stripped[2:].strip())
            
            return latest_version
            
        except Exception as e:
            print(f"⚠️  Error parsing changelog: {e}")
            return None
    
    def get_known_issues(self):
        """Get known issues from user input"""
        print(f"\n🐛 Known Issues for this build:")
        print("Enter known issues/bugs that exist in this build.")
        print("Enter one per line, press Enter on empty line to finish:")
        
        issues = []
        issue_number = 1
        
        while True:
            issue = input(f"Issue #{issue_number}: ").strip()
            if not issue:
                break
            
            issues.append(issue)
            print(f"  ✓ Added: {issue}")
            issue_number += 1
        
        self.known_issues = issues
        if issues:
            print(f"\n📝 Added {len(issues)} known issue(s)")
        else:
            print("\n✅ No known issues reported for this build")
    
    def get_build_notes(self):
        """Get additional build notes from user"""
        print(f"\n📝 Build Notes (optional):")
        print("Enter any additional notes about this build:")
        notes = input("Notes: ").strip()
        self.build_notes = notes
        if notes:
            print(f"✓ Added build notes: {notes}")
    
    def generate_build_changelog(self):
        """Generate a changelog entry for this specific build"""
        if not self.changelog_file:
            return None
        
        current_data = self.parse_current_changelog()
        if not current_data:
            print("⚠️  Could not parse existing changelog data")
            return None
        
        date_str = datetime.now().strftime("%m/%d/%Y")
        
        changelog_entry = []
        changelog_entry.append(f"# Build: {date_str} - {self.generate_filename()} #")
        changelog_entry.append(f"* Program: [{self.program_name}]")
        changelog_entry.append(f"* Status: [{self.build_status}]")
        changelog_entry.append(f"* Build Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        changelog_entry.append("")
        
        # Issues Resolved
        changelog_entry.append("## Issues Resolved: ##")
        if current_data.get('issues_resolved'):
            for issue in current_data['issues_resolved']:
                changelog_entry.append(f"* {issue}")
        else:
            changelog_entry.append("* No issues resolved in this build")
        changelog_entry.append("")
        
        # Features Added
        changelog_entry.append("## Features Added: ##")
        if current_data.get('features_added'):
            for feature in current_data['features_added']:
                changelog_entry.append(f"* {feature}")
        else:
            changelog_entry.append("* No new features in this build")
        changelog_entry.append("")
        
        # Improvements Made
        changelog_entry.append("## Improvements Made: ##")
        if current_data.get('improvements_made'):
            for improvement in current_data['improvements_made']:
                changelog_entry.append(f"* {improvement}")
        else:
            changelog_entry.append("* No improvements in this build")
        changelog_entry.append("")
        
        # Known Issues
        changelog_entry.append("## Known Issues: ##")
        if self.known_issues:
            for issue in self.known_issues:
                changelog_entry.append(f"* {issue}")
        else:
            changelog_entry.append("* No known issues")
        changelog_entry.append("")
        
        # Build Notes
        if self.build_notes:
            changelog_entry.append("## Build Notes: ##")
            changelog_entry.append(f"* {self.build_notes}")
            changelog_entry.append("")
        
        # Technical Details
        changelog_entry.append("## Technical Details: ##")
        changelog_entry.append(f"* Entry Point: {self.main_entry}")
        changelog_entry.append(f"* Build Type: {'Single File' if self.build_options.get('onefile', True) else 'Directory'}")
        changelog_entry.append(f"* Windowed: {'Yes' if self.build_options.get('windowed', True) else 'No'}")
        if 'icon' in self.build_options:
            changelog_entry.append(f"* Icon: {self.build_options['icon']}")
        if self.additional_files:
            changelog_entry.append(f"* Additional Files: {len(self.additional_files)} file(s)")
        changelog_entry.append("")
        
        return '\n'.join(changelog_entry)
    
    def save_build_changelog(self, changelog_content):
        """Save the build-specific changelog"""
        if not changelog_content:
            return
        
        # Generate filename
        date_str = self.get_date_string()
        filename = f"build-changelog-{self.program_name.lower().replace(' ', '-')}-{date_str}-{self.build_status.lower()}.md"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(changelog_content)
            
            print(f"\n📄 Build changelog saved to: {filename}")
            return filename
            
        except Exception as e:
            print(f"⚠️  Could not save build changelog: {e}")
            return None
    
    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self):
        """Print the script header"""
        print("=" * 60)
        print("  PyInstaller Interactive Build Tool")
        print("  Enhanced with Changelog Integration")
        print("=" * 60)
        print("Features:")
        print("  • Automated PyInstaller build configuration")
        print("  • Intelligent icon and file detection")
        print("  • Changelog parsing and build documentation")
        print("  • Known issues tracking")
        print("  • Build configuration persistence")
        print("=" * 60)
        print()
    
    def get_program_name(self):
        """Get the program name from user"""
        while True:
            name = input("Enter program name (e.g., 'PDF Utility'): ").strip()
            if name:
                self.program_name = name
                break
            print("Program name cannot be empty!")
    
    def get_build_status(self):
        """Get build status from user"""
        statuses = ["ALPHA", "BETA", "RC", "RELEASE", "DEV", "CUSTOM"]
        
        print("\nAvailable build statuses:")
        for i, status in enumerate(statuses, 1):
            print(f"  {i}. {status}")
        
        while True:
            try:
                choice = input(f"\nSelect build status (1-{len(statuses)}): ").strip()
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(statuses):
                        if statuses[idx] == "CUSTOM":
                            custom = input("Enter custom build status: ").strip().upper()
                            if custom:
                                self.build_status = custom
                                break
                        else:
                            self.build_status = statuses[idx]
                            break
                
                print("Invalid selection!")
            except ValueError:
                print("Please enter a number!")
    
    def get_main_entry(self):
        """Get main program entry point"""
        # Look for common entry points
        common_entries = []
        for file in ["main.py", "main_application.py", "app.py", "__main__.py"]:
            if os.path.exists(file):
                common_entries.append(file)
        
        print(f"\nFound potential entry points: {common_entries}" if common_entries else "\nNo common entry points found.")
        
        while True:
            if common_entries:
                print("\nSelect entry point:")
                for i, entry in enumerate(common_entries, 1):
                    print(f"  {i}. {entry}")
                print(f"  {len(common_entries) + 1}. Enter custom path")
                
                choice = input(f"\nChoice (1-{len(common_entries) + 1}): ").strip()
                
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(common_entries):
                        self.main_entry = common_entries[idx]
                        break
                    elif idx == len(common_entries):
                        # Custom path
                        pass
                    else:
                        print("Invalid selection!")
                        continue
            
            # Custom entry point
            custom_entry = input("Enter main entry point file: ").strip()
            if custom_entry and os.path.exists(custom_entry):
                self.main_entry = custom_entry
                break
            elif custom_entry:
                print(f"File '{custom_entry}' not found!")
            else:
                print("Entry point cannot be empty!")

    def find_and_select_icon(self):
        """Search for icon files and ask user to select one"""
        # Common icon file patterns and locations
        icon_patterns = [
            "*.ico", "*.icns", "*.png"
        ]
        
        search_directories = [
            ".",  # Current directory
            "assets",
            "icons", 
            "resources",
            "images",
            "static"
        ]
        
        # Find all potential icon files
        found_icons = []
        
        for directory in search_directories:
            if os.path.exists(directory):
                for pattern in icon_patterns:
                    search_path = os.path.join(directory, pattern)
                    for file_path in glob.glob(search_path):
                        if os.path.isfile(file_path):
                            found_icons.append(file_path)
        
        # Remove duplicates and sort
        found_icons = sorted(list(set(found_icons)))
        
        if not found_icons:
            print("\n🔍 No icon files found in common locations.")
            # Ask for manual input
            manual_icon = input("Enter icon file path manually (optional, .ico/.icns/.png): ").strip()
            if manual_icon and os.path.exists(manual_icon):
                print(f"✅ Using manually specified icon: {manual_icon}")
                return manual_icon
            else:
                print("❌ No icon will be used for this build.")
                return None
        
        print(f"\n🎨 Found {len(found_icons)} potential icon file(s):")
        for i, icon in enumerate(found_icons, 1):
            file_size = os.path.getsize(icon)
            size_kb = file_size / 1024
            print(f"  {i}. {icon} ({size_kb:.1f} KB)")
        
        print(f"  {len(found_icons) + 1}. Enter custom path")
        print(f"  {len(found_icons) + 2}. Skip icon (no icon)")
        
        while True:
            try:
                choice = input(f"\nSelect icon to use (1-{len(found_icons) + 2}): ").strip()
                
                if choice.isdigit():
                    idx = int(choice) - 1
                    
                    if 0 <= idx < len(found_icons):
                        selected_icon = found_icons[idx]
                        # Confirm selection
                        confirm = input(f"Use '{selected_icon}' as the application icon? (Y/n): ").lower()
                        if confirm not in ['n', 'no']:
                            print(f"✅ Selected icon: {selected_icon}")
                            return selected_icon
                        else:
                            continue
                    
                    elif idx == len(found_icons):
                        # Custom path
                        custom_icon = input("Enter custom icon file path: ").strip()
                        if custom_icon and os.path.exists(custom_icon):
                            if custom_icon.lower().endswith(('.ico', '.icns', '.png')):
                                print(f"✅ Using custom icon: {custom_icon}")
                                return custom_icon
                            else:
                                print("⚠️  Warning: Icon file should be .ico, .icns, or .png format")
                                confirm = input("Use this file anyway? (y/N): ").lower()
                                if confirm in ['y', 'yes']:
                                    return custom_icon
                                else:
                                    continue
                        else:
                            print("❌ File not found or empty path!")
                            continue
                    
                    elif idx == len(found_icons) + 1:
                        # Skip icon
                        print("❌ No icon will be used for this build.")
                        return None
                    
                    else:
                        print("❌ Invalid selection!")
                        continue
                
                else:
                    print("❌ Please enter a number!")
                    
            except ValueError:
                print("❌ Please enter a valid number!")
            except KeyboardInterrupt:
                print("\n❌ Build cancelled by user.")
                sys.exit(0)
            entry = input("Enter main program file (e.g., main_application.py): ").strip()
            if entry:
                if os.path.exists(entry):
                    self.main_entry = entry
                    break
                else:
                    create = input(f"File '{entry}' not found. Continue anyway? (y/n): ").lower()
                    if create in ['y', 'yes']:
                        self.main_entry = entry
                        break
            else:
                print("Entry point cannot be empty!")
    
    def find_and_select_splash(self):
        """Search for splash screen files and ask user to select one"""
        # Common splash screen file patterns and locations
        splash_patterns = [
            "*splash*", "*loading*", "*startup*", "*boot*"
        ]
        
        # Common image extensions for splash screens
        image_extensions = [
            "*.png", "*.jpg", "*.jpeg", "*.bmp", "*.gif", "*.tiff", "*.webp"
        ]
        
        search_directories = [
            ".",  # Current directory
            "assets",
            "images",
            "resources", 
            "splash",
            "static",
            "media"
        ]
        
        # Find all potential splash screen files
        found_splashes = []
        
        for directory in search_directories:
            if os.path.exists(directory):
                # Look for files with splash-related names
                for pattern in splash_patterns:
                    for ext in image_extensions:
                        search_pattern = pattern + "." + ext.split(".")[-1]
                        search_path = os.path.join(directory, search_pattern)
                        for file_path in glob.glob(search_path):
                            if os.path.isfile(file_path):
                                found_splashes.append(file_path)
                
                # Also look for any image files in splash-specific directories
                if "splash" in directory.lower() or "loading" in directory.lower():
                    for ext in image_extensions:
                        search_path = os.path.join(directory, ext)
                        for file_path in glob.glob(search_path):
                            if os.path.isfile(file_path):
                                found_splashes.append(file_path)
        
        # Remove duplicates and sort
        found_splashes = sorted(list(set(found_splashes)))
        
        if not found_splashes:
            print("\n🖼️  No splash screen files found in common locations.")
            print("Searched for: splash, loading, startup, boot images")
            # Ask for manual input
            manual_splash = input("Enter splash screen file path manually (optional, .png/.jpg/etc.): ").strip()
            if manual_splash and os.path.exists(manual_splash):
                if self.is_valid_image_file(manual_splash):
                    print(f"✅ Using manually specified splash screen: {manual_splash}")
                    return manual_splash
                else:
                    print("⚠️  Warning: File may not be a valid image format")
                    confirm = input("Use this file anyway? (y/N): ").lower()
                    if confirm in ['y', 'yes']:
                        return manual_splash
            print("❌ No splash screen will be used for this build.")
            return None
        
        print(f"\n🖼️  Found {len(found_splashes)} potential splash screen file(s):")
        for i, splash in enumerate(found_splashes, 1):
            file_size = os.path.getsize(splash)
            size_kb = file_size / 1024
            # Try to get image dimensions if possible
            dimensions = self.get_image_dimensions(splash)
            dim_str = f" - {dimensions}" if dimensions else ""
            print(f"  {i}. {splash} ({size_kb:.1f} KB{dim_str})")
        
        print(f"  {len(found_splashes) + 1}. Enter custom path")
        print(f"  {len(found_splashes) + 2}. Skip splash screen")
        
        while True:
            try:
                choice = input(f"\nSelect splash screen to use (1-{len(found_splashes) + 2}): ").strip()
                
                if choice.isdigit():
                    idx = int(choice) - 1
                    
                    if 0 <= idx < len(found_splashes):
                        selected_splash = found_splashes[idx]
                        # Confirm selection
                        confirm = input(f"Use '{selected_splash}' as the splash screen? (Y/n): ").lower()
                        if confirm not in ['n', 'no']:
                            print(f"✅ Selected splash screen: {selected_splash}")
                            return selected_splash
                        else:
                            continue
                    
                    elif idx == len(found_splashes):
                        # Custom path
                        custom_splash = input("Enter custom splash screen file path: ").strip()
                        if custom_splash and os.path.exists(custom_splash):
                            if self.is_valid_image_file(custom_splash):
                                print(f"✅ Using custom splash screen: {custom_splash}")
                                return custom_splash
                            else:
                                print("⚠️  Warning: File may not be a valid image format")
                                confirm = input("Use this file anyway? (y/N): ").lower()
                                if confirm in ['y', 'yes']:
                                    return custom_splash
                                else:
                                    continue
                        else:
                            print("❌ File not found or empty path!")
                            continue
                    
                    elif idx == len(found_splashes) + 1:
                        # Skip splash screen
                        print("❌ No splash screen will be used for this build.")
                        return None
                    
                    else:
                        print("❌ Invalid selection!")
                        continue
                
                else:
                    print("❌ Please enter a number!")
                    
            except ValueError:
                print("❌ Please enter a valid number!")
            except KeyboardInterrupt:
                print("\n❌ Build cancelled by user.")
                sys.exit(0)
    
    def is_valid_image_file(self, file_path):
        """Check if file has a valid image extension"""
        valid_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp']
        return any(file_path.lower().endswith(ext) for ext in valid_extensions)
    
    def offer_splash_code_integration(self):
        """Offer to automatically add splash screen close code to main entry point"""
        print(f"\n🔧 Splash Screen Integration:")
        print(f"The splash screen needs to be closed manually from your Python code.")
        print(f"Would you like to automatically add the close code to '{self.main_entry}'?")
        
        add_code = input("Add splash close code automatically? (Y/n): ").lower()
        if add_code not in ['n', 'no']:
            self.add_splash_close_code()
        else:
            print("⚠️  Remember to manually add splash close code to your application!")
            print("   Instructions will be generated after the build.")
    
    def add_splash_close_code(self):
        """Automatically add splash screen close code to the main entry point"""
        if not os.path.exists(self.main_entry):
            print(f"❌ Cannot add code - file '{self.main_entry}' not found!")
            return False
        
        try:
            # Read the current file
            with open(self.main_entry, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if splash close code already exists
            if 'pyi_splash.close()' in content:
                print(f"✅ Splash close code already exists in '{self.main_entry}'")
                return True
            
            # Define the splash close code to add
            splash_code = '''
# Close PyInstaller splash screen (if present)
try:
    import pyi_splash
    pyi_splash.close()
except ImportError:
    # Not running as PyInstaller executable, or splash not enabled
    pass
'''
            
            # Try to find a good insertion point
            lines = content.split('\n')
            insert_line = -1
            
            # Look for common patterns where we should insert the code
            patterns_to_find = [
                'if __name__ == "__main__":',
                'root.mainloop()',
                'app.run()',
                'app.exec()',
                'app.exec_()',
                'window.show()',
                'root.deiconify()',
                'root.update()',
                'main()',
                'run()',
            ]
            
            for i, line in enumerate(lines):
                line_stripped = line.strip()
                
                # Check for main execution patterns
                for pattern in patterns_to_find:
                    if pattern in line_stripped:
                        if pattern == 'if __name__ == "__main__":':
                            # Insert after the if statement, but before the main code
                            insert_line = i + 1
                            break
                        elif 'mainloop' in pattern or 'exec' in pattern or 'show' in pattern:
                            # Insert before GUI loop/show commands
                            insert_line = i
                            break
                        elif 'update' in pattern or 'deiconify' in pattern:
                            # Insert after update/show commands
                            insert_line = i + 1
                            break
                        else:
                            # Insert before main/run functions
                            insert_line = i
                            break
                
                if insert_line != -1:
                    break
            
            # If no good insertion point found, add at the end
            if insert_line == -1:
                print("⚠️  Could not find ideal insertion point. Adding code at the end of file.")
                insert_line = len(lines)
            
            # Insert the splash close code
            splash_lines = splash_code.strip().split('\n')
            for i, splash_line in enumerate(splash_lines):
                lines.insert(insert_line + i, splash_line)
            
            # Write the modified content back
            modified_content = '\n'.join(lines)
            
            # Create backup
            backup_file = f"{self.main_entry}.backup"
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Write modified file
            with open(self.main_entry, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            
            print(f"✅ Successfully added splash close code to '{self.main_entry}'")
            print(f"📄 Original file backed up as '{backup_file}'")
            print(f"🔧 Code inserted at line {insert_line + 1}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error adding splash close code: {e}")
            print("⚠️  You'll need to manually add the code. Instructions will be provided.")
            return False
    
    def create_splash_instructions(self):
        """Create detailed instructions for implementing splash screen close functionality"""
        instructions_file = "splash_screen_instructions.md"
        
        instructions_content = f"""# Splash Screen Integration Instructions

## Overview
Your PyInstaller build includes a splash screen that displays during application startup.
**IMPORTANT:** The splash screen must be manually closed from your Python code.

## Required Code Addition

Add this code to your main application file (`{self.main_entry}`) after your application has finished initializing:

```python
# Close PyInstaller splash screen (if present)
try:
    import pyi_splash
    pyi_splash.close()
except ImportError:
    # Not running as PyInstaller executable, or splash not enabled
    pass
```

## Recommended Placement

### For GUI Applications (Tkinter, PyQt, etc.)
Place the code after your main window is created and displayed:

```python
import tkinter as tk

# Create your main window
root = tk.Tk()
root.title("Your Application")

# Configure your GUI
# ... your GUI setup code ...

# Show the main window
root.deiconify()  # If you hid it initially
root.update()     # Force window to display

# Close splash screen after GUI is ready
try:
    import pyi_splash
    pyi_splash.close()
except ImportError:
    pass

# Start main loop
root.mainloop()
```

### For Console Applications
Place the code after your application has finished loading:

```python
# Your imports and initialization
import sys
import os

# Application setup
print("Loading application...")
# ... your setup code ...

# Close splash screen after loading is complete
try:
    import pyi_splash
    pyi_splash.close()
except ImportError:
    pass

print("Application ready!")
# ... rest of your application ...
```

### Advanced: Update Splash Screen Text
You can also update the splash screen text before closing it:

```python
try:
    import pyi_splash
    
    # Update splash text (optional)
    pyi_splash.update_text("Loading complete...")
    
    # Close the splash screen
    pyi_splash.close()
except ImportError:
    pass
```

## Common Issues

1. **Splash screen doesn't close:** Make sure the close code is reachable and executed
2. **Error messages:** The ImportError handling ensures no errors if running without PyInstaller
3. **Timing:** Place the close code after your application is fully ready, not during early initialization

## Testing

- **Development:** The splash code will be ignored when running directly with Python
- **Built executable:** The splash screen will display and close as configured

Generated for build: {self.generate_filename()}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        try:
            with open(instructions_file, 'w', encoding='utf-8') as f:
                f.write(instructions_content)
            print(f"📄 Splash screen instructions saved to: {instructions_file}")
        except Exception as e:
            print(f"⚠️  Could not save instructions file: {e}")
    
    def get_image_dimensions(self, file_path):
        """Try to get image dimensions (requires PIL/Pillow, but gracefully handles if not available)"""
        try:
            from PIL import Image
            with Image.open(file_path) as img:
                return f"{img.width}x{img.height}"
        except ImportError:
            # PIL not available, skip dimensions
            return None
        except Exception:
            # Any other error (corrupt file, etc.)
            return None
    
    def get_additional_files(self):
        """Get additional files to include"""
        print("\nAdditional files/folders to include (optional):")
        print("Examples: README.md, .env, config/, data/")
        print("Enter one per line, press Enter on empty line to finish:")
        
        files = []
        while True:
            file_path = input("File/folder: ").strip()
            if not file_path:
                break
            
            if os.path.exists(file_path):
                files.append(file_path)
                print(f"  ✓ Added: {file_path}")
            else:
                add_anyway = input(f"'{file_path}' not found. Add anyway? (y/n): ").lower()
                if add_anyway in ['y', 'yes']:
                    files.append(file_path)
                    print(f"  ✓ Added: {file_path}")
        
        self.additional_files = files
    
    def get_build_options(self):
        """Get additional build options"""
        print("\nBuild Options:")
        
        # One file vs one folder
        one_file = input("Create single executable file? (Y/n): ").lower()
        self.build_options['onefile'] = one_file not in ['n', 'no']
        
        # Windowed (no console)
        windowed = input("Hide console window (for GUI apps)? (Y/n): ").lower()
        self.build_options['windowed'] = windowed not in ['n', 'no']
        
        # Icon file - search automatically first
        icon_file = self.find_and_select_icon()
        if icon_file:
            self.build_options['icon'] = icon_file
        
        # Splash screen - search automatically first
        splash_file = self.find_and_select_splash()
        if splash_file:
            self.build_options['splash'] = splash_file
            # Offer to automatically add splash close code
            self.offer_splash_code_integration()
        
        # Clean build
        clean = input("Clean previous build? (Y/n): ").lower()
        self.build_options['clean'] = clean not in ['n', 'no']
        
        # Debug/verbose
        debug = input("Enable debug/verbose output? (y/N): ").lower()
        self.build_options['debug'] = debug in ['y', 'yes']
    
    def generate_filename(self):
        """Generate the final executable name"""
        date_str = self.get_date_string()
        return f"{self.program_name}-{date_str}-{self.build_status}"
    
    def build_command(self):
        """Build the PyInstaller command"""
        filename = self.generate_filename()
        
        cmd = ["pyinstaller"]
        
        # Basic options
        cmd.extend(["--name", filename])
        
        if self.build_options.get('onefile', True):
            cmd.append("--onefile")
        
        if self.build_options.get('windowed', True):
            cmd.append("--windowed")
        
        if self.build_options.get('clean', True):
            cmd.append("--clean")
        
        if self.build_options.get('debug', False):
            cmd.append("--debug=all")
        
        # Icon
        if 'icon' in self.build_options:
            cmd.extend(["--icon", self.build_options['icon']])
            
            # Also include the icon file and its directory for runtime access
            icon_path = self.build_options['icon']
            icon_dir = os.path.dirname(icon_path)
            
            # Add the icon file itself
            cmd.extend(["--add-data", f"{icon_path};."])
            
            # If icon is in a subdirectory (like assets, icons, etc.), include the whole directory
            if icon_dir and icon_dir != ".":
                directory_name = os.path.basename(icon_dir)
                if directory_name in ['assets', 'icons', 'resources', 'images', 'static']:
                    if os.path.isdir(icon_dir):
                        cmd.extend(["--add-data", f"{icon_dir};{directory_name}"])
                        print(f"📁 Including icon directory: {icon_dir} -> {directory_name}")
            
            # Search for and include other icon formats of the same name
            icon_base = os.path.splitext(icon_path)[0]
            for ext in ['.ico', '.icns', '.png', '.svg']:
                alt_icon = icon_base + ext
                if os.path.exists(alt_icon) and alt_icon != icon_path:
                    cmd.extend(["--add-data", f"{alt_icon};."])
                    print(f"🎨 Including alternative icon format: {alt_icon}")
        
        # Splash screen
        if 'splash' in self.build_options:
            cmd.extend(["--splash", self.build_options['splash']])
            print(f"🖼️ Including splash screen: {self.build_options['splash']}")
            print("⚠️  IMPORTANT: Add splash screen close code to your main application!")
            print("   Add this to your main entry point after initialization:")
            print("   try:")
            print("       import pyi_splash")
            print("       pyi_splash.close()")
            print("   except ImportError:")
            print("       pass")
            self.create_splash_instructions()
        
        # Additional files
        for file_path in self.additional_files:
            if os.path.isfile(file_path):
                cmd.extend(["--add-data", f"{file_path};."])
            elif os.path.isdir(file_path):
                cmd.extend(["--add-data", f"{file_path};{file_path}"])
        
        # Main entry point
        cmd.append(self.main_entry)
        
        return cmd
    
    def preview_command(self):
        """Show the command that will be executed"""
        cmd = self.build_command()
        
        print("\n" + "=" * 60)
        print("  COMMAND PREVIEW")
        print("=" * 60)
        
        # Format command nicely
        cmd_str = " \\\n  ".join(cmd) if len(" ".join(cmd)) > 80 else " ".join(cmd)
        print(f"\n{cmd_str}\n")
        
        print("=" * 60)
        print("  BUILD SUMMARY")
        print("=" * 60)
        print(f"Program Name: {self.program_name}")
        print(f"Build Status: {self.build_status}")
        print(f"Date: {self.get_date_string()}")
        print(f"Final Name: {self.generate_filename()}")
        print(f"Entry Point: {self.main_entry}")
        print(f"One File: {self.build_options.get('onefile', True)}")
        print(f"Windowed: {self.build_options.get('windowed', True)}")
        print(f"Additional Files: {len(self.additional_files)}")
        if self.additional_files:
            for file in self.additional_files:
                print(f"  - {file}")
        
        # Changelog information
        if self.changelog_file:
            print(f"Changelog File: {self.changelog_file}")
            print(f"Known Issues: {len(self.known_issues)}")
            if self.known_issues:
                for issue in self.known_issues:
                    print(f"  - {issue}")
            if self.build_notes:
                print(f"Build Notes: {self.build_notes}")
        
        print("=" * 60)
    
    def execute_build(self):
        """Execute the PyInstaller command"""
        cmd = self.build_command()
        
        print(f"\nStarting build process...")
        print(f"Command: {' '.join(cmd[:3])} ... {cmd[-1]}")
        
        try:
            # Change to script directory
            original_dir = os.getcwd()
            script_dir = os.path.dirname(os.path.abspath(__file__))
            if script_dir:
                os.chdir(script_dir)
            
            # Execute command
            result = subprocess.run(cmd, capture_output=False, text=True)
            
            # Restore directory
            os.chdir(original_dir)
            
            if result.returncode == 0:
                print("\n" + "=" * 60)
                print("  BUILD SUCCESSFUL! 🎉")
                print("=" * 60)
                print(f"Executable created: {self.generate_filename()}")
                print("Check the 'dist' folder for your executable.")
                
                # Generate and save build changelog if configured
                if self.changelog_file:
                    print("\n📄 Generating build changelog...")
                    changelog_content = self.generate_build_changelog()
                    if changelog_content:
                        changelog_file = self.save_build_changelog(changelog_content)
                        if changelog_file:
                            print(f"📄 Build documentation saved to: {changelog_file}")
                
            else:
                print("\n" + "=" * 60)
                print("  BUILD FAILED! ❌")
                print("=" * 60)
                print("Check the output above for error details.")
                
        except FileNotFoundError:
            print("\n❌ Error: PyInstaller not found!")
            print("Install with: pip install pyinstaller")
        except Exception as e:
            print(f"\n❌ Build error: {e}")
    
    def save_build_config(self):
        """Save complete build configuration for future use"""
        # Get current timestamp
        from datetime import datetime
        
        config = {
            # Metadata
            'config_version': '2.0',
            'saved_date': datetime.now().isoformat(),
            'saved_by': 'PyInstaller Build Script Enhanced',
            
            # Core build settings
            'program_name': self.program_name,
            'build_status': self.build_status,
            'main_entry': self.main_entry,
            
            # File collections
            'additional_files': self.additional_files,
            
            # Build options (includes icon and splash paths)
            'build_options': self.build_options,
            
            # Changelog configuration
            'changelog_file': self.changelog_file,
            'known_issues': self.known_issues,
            'build_notes': self.build_notes,
            
            # File paths for verification
            'file_paths': {
                'icon': self.build_options.get('icon', ''),
                'splash': self.build_options.get('splash', ''),
                'main_entry': self.main_entry,
                'changelog': self.changelog_file,
                'additional_files': self.additional_files
            },
            
            # Build history tracking
            'last_build_date': self.get_date_string(),
            'last_filename': self.generate_filename() if self.program_name and self.build_status else '',
            
            # Settings validation
            'settings_summary': {
                'has_icon': 'icon' in self.build_options,
                'has_splash': 'splash' in self.build_options,
                'has_changelog': bool(self.changelog_file),
                'onefile': self.build_options.get('onefile', True),
                'windowed': self.build_options.get('windowed', True),
                'clean': self.build_options.get('clean', True),
                'debug': self.build_options.get('debug', False),
                'additional_files_count': len(self.additional_files),
                'known_issues_count': len(self.known_issues)
            }
        }
        
        config_file = "build_config.json"
        try:
            import json
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Complete build configuration saved to {config_file}")
            print(f"📊 Configuration Summary:")
            print(f"   • Program: {self.program_name}")
            print(f"   • Status: {self.build_status}")
            print(f"   • Icon: {'✅' if config['settings_summary']['has_icon'] else '❌'}")
            print(f"   • Splash: {'✅' if config['settings_summary']['has_splash'] else '❌'}")
            print(f"   • Changelog: {'✅' if config['settings_summary']['has_changelog'] else '❌'}")
            print(f"   • Additional Files: {config['settings_summary']['additional_files_count']}")
            print(f"   • Build Options: {len(self.build_options)} settings")
            
        except Exception as e:
            print(f"\n⚠️  Could not save config: {e}")
    
    
    def load_build_config(self):
        """Load and validate previous build configuration"""
        config_file = "build_config.json"
        if not os.path.exists(config_file):
            print("🔍 No previous configuration found.")
            return False
        
        try:
            import json
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Display configuration details
            print(f"\n📄 Found previous configuration:")
            print(f"   Config Version: {config.get('config_version', '1.0')}")
            if 'saved_date' in config:
                print(f"   Saved: {config['saved_date']}")
            
            print(f"\n📋 Build Settings:")
            print(f"   • Program: {config.get('program_name', 'N/A')}")
            print(f"   • Status: {config.get('build_status', 'N/A')}")
            print(f"   • Entry: {config.get('main_entry', 'N/A')}")
            
            # Show file validation status
            if 'file_paths' in config:
                print(f"\n🔍 File Validation:")
                file_paths = config['file_paths']
                
                # Check main entry
                main_entry = file_paths.get('main_entry', '')
                if main_entry:
                    status = "✅" if os.path.exists(main_entry) else "❌ MISSING"
                    print(f"   • Main Entry: {main_entry} {status}")
                
                # Check icon
                icon_path = file_paths.get('icon', '')
                if icon_path:
                    status = "✅" if os.path.exists(icon_path) else "❌ MISSING"
                    print(f"   • Icon: {icon_path} {status}")
                
                # Check splash
                splash_path = file_paths.get('splash', '')
                if splash_path:
                    status = "✅" if os.path.exists(splash_path) else "❌ MISSING"
                    print(f"   • Splash: {splash_path} {status}")
                
                # Check changelog
                changelog_path = file_paths.get('changelog', '')
                if changelog_path:
                    status = "✅" if os.path.exists(changelog_path) else "❌ MISSING"
                    print(f"   • Changelog: {changelog_path} {status}")
                
                # Check additional files
                additional_files = file_paths.get('additional_files', [])
                if additional_files:
                    print(f"   • Additional Files: {len(additional_files)} file(s)")
                    missing_files = []
                    for file_path in additional_files:
                        if not os.path.exists(file_path):
                            missing_files.append(file_path)
                    
                    if missing_files:
                        print(f"     ⚠️  {len(missing_files)} file(s) missing:")
                        for missing in missing_files[:3]:  # Show first 3
                            print(f"       - {missing}")
                        if len(missing_files) > 3:
                            print(f"       ... and {len(missing_files) - 3} more")
                    else:
                        print(f"     ✅ All additional files found")
            
            # Show settings summary
            if 'settings_summary' in config:
                summary = config['settings_summary']
                print(f"\n⚙️  Build Configuration:")
                print(f"   • Icon: {'✅' if summary.get('has_icon') else '❌'}")
                print(f"   • Splash Screen: {'✅' if summary.get('has_splash') else '❌'}")
                print(f"   • Changelog: {'✅' if summary.get('has_changelog') else '❌'}")
                print(f"   • Single File: {'✅' if summary.get('onefile') else '❌'}")
                print(f"   • Windowed: {'✅' if summary.get('windowed') else '❌'}")
                print(f"   • Clean Build: {'✅' if summary.get('clean') else '❌'}")
                print(f"   • Debug Mode: {'✅' if summary.get('debug') else '❌'}")
                print(f"   • Additional Files: {summary.get('additional_files_count', 0)}")
                print(f"   • Known Issues: {summary.get('known_issues_count', 0)}")
            
            # Check for missing files before asking to use config
            missing_critical_files = []
            if 'file_paths' in config:
                paths = config['file_paths']
                main_entry = paths.get('main_entry', '')
                if main_entry and not os.path.exists(main_entry):
                    missing_critical_files.append(f"Main entry: {main_entry}")
                
                icon_path = paths.get('icon', '')
                if icon_path and not os.path.exists(icon_path):
                    missing_critical_files.append(f"Icon: {icon_path}")
                
                splash_path = paths.get('splash', '')
                if splash_path and not os.path.exists(splash_path):
                    missing_critical_files.append(f"Splash: {splash_path}")
            
            if missing_critical_files:
                print(f"\n⚠️  WARNING: Some configured files are missing:")
                for missing in missing_critical_files:
                    print(f"   • {missing}")
                print(f"\nYou can still use this configuration, but you'll need to specify new files.")
            
            use_config = input("\n🔄 Use this configuration as starting point? (Y/n): ").lower()
            if use_config not in ['n', 'no']:
                # Load all configuration data
                self.program_name = config.get('program_name', '')
                self.build_status = config.get('build_status', '')
                self.main_entry = config.get('main_entry', '')
                self.additional_files = config.get('additional_files', [])
                self.build_options = config.get('build_options', {})
                self.changelog_file = config.get('changelog_file', '')
                self.known_issues = config.get('known_issues', [])
                self.build_notes = config.get('build_notes', '')
                
                # Validate and clean up missing files from build_options
                if 'icon' in self.build_options:
                    if not os.path.exists(self.build_options['icon']):
                        print(f"⚠️  Removing missing icon from configuration: {self.build_options['icon']}")
                        del self.build_options['icon']
                
                if 'splash' in self.build_options:
                    if not os.path.exists(self.build_options['splash']):
                        print(f"⚠️  Removing missing splash from configuration: {self.build_options['splash']}")
                        del self.build_options['splash']
                
                # Clean up missing additional files
                existing_additional_files = []
                for file_path in self.additional_files:
                    if os.path.exists(file_path):
                        existing_additional_files.append(file_path)
                    else:
                        print(f"⚠️  Removing missing additional file: {file_path}")
                
                self.additional_files = existing_additional_files
                
                print(f"\n✅ Configuration loaded successfully!")
                print(f"📋 Loaded settings for: {self.program_name} ({self.build_status})")
                return True
                
        except Exception as e:
            print(f"❌ Could not load config: {e}")
        
        return False
    
    def show_config_management_menu(self):
        """Show configuration management options"""
        while True:
            self.clear_screen()
            print("=" * 60)
            print("  🔧 CONFIGURATION MANAGEMENT")
            print("=" * 60)
            
            # Show current config status
            if hasattr(self, 'program_name') and self.program_name:
                print(f"Current Configuration:")
                print(f"  • Program: {self.program_name}")
                print(f"  • Status: {self.build_status}")
                print(f"  • Entry: {self.main_entry}")
                print(f"  • Icon: {'✅' if self.build_options.get('icon') else '❌'}")
                print(f"  • Splash: {'✅' if self.build_options.get('splash') else '❌'}")
                print(f"  • Changelog: {'✅' if self.changelog_file else '❌'}")
                print(f"  • Additional Files: {len(self.additional_files)}")
            else:
                print("No configuration loaded.")
            
            print("\n" + "=" * 60)
            print("  MENU OPTIONS")
            print("=" * 60)
            print("  1. Load Configuration")
            print("  2. Save Current Configuration")
            print("  3. Create New Configuration")
            print("  4. View Configuration Details")
            print("  5. Export Configuration")
            print("  6. Import Configuration from File")
            print("  7. Back to Main Menu")
            print("=" * 60)
            
            choice = input("\nSelect option (1-7): ").strip()
            
            if choice == "1":
                self.load_build_config()
                input("Press Enter to continue...")
            elif choice == "2":
                if hasattr(self, 'program_name') and self.program_name:
                    self.save_build_config()
                else:
                    print("❌ No configuration to save!")
                input("Press Enter to continue...")
            elif choice == "3":
                self.reset_configuration()
                print("✅ Configuration reset. You can now create a new one.")
                input("Press Enter to continue...")
            elif choice == "4":
                self.show_detailed_config()
                input("Press Enter to continue...")
            elif choice == "5":
                self.export_configuration()
                input("Press Enter to continue...")
            elif choice == "6":
                self.import_configuration()
                input("Press Enter to continue...")
            elif choice == "7":
                break
            else:
                print("❌ Invalid option!")
                input("Press Enter to continue...")
    
    def reset_configuration(self):
        """Reset all configuration to defaults"""
        self.program_name = ""
        self.build_status = ""
        self.main_entry = ""
        self.additional_files = []
        self.build_options = {}
        self.changelog_file = ""
        self.known_issues = []
        self.build_notes = ""
    
    def show_detailed_config(self):
        """Show detailed configuration information"""
        self.clear_screen()
        print("=" * 60)
        print("  📋 DETAILED CONFIGURATION")
        print("=" * 60)
        
        if not hasattr(self, 'program_name') or not self.program_name:
            print("No configuration loaded.")
            return
        
        print(f"Program Information:")
        print(f"  • Name: {self.program_name}")
        print(f"  • Build Status: {self.build_status}")
        print(f"  • Main Entry: {self.main_entry}")
        print(f"  • Generated Filename: {self.generate_filename()}")
        
        print(f"\nFile Resources:")
        if self.build_options.get('icon'):
            icon_path = self.build_options['icon']
            exists = "✅" if os.path.exists(icon_path) else "❌ MISSING"
            print(f"  • Icon: {icon_path} {exists}")
        else:
            print(f"  • Icon: Not configured")
        
        if self.build_options.get('splash'):
            splash_path = self.build_options['splash']
            exists = "✅" if os.path.exists(splash_path) else "❌ MISSING"
            print(f"  • Splash: {splash_path} {exists}")
        else:
            print(f"  • Splash: Not configured")
        
        if self.changelog_file:
            exists = "✅" if os.path.exists(self.changelog_file) else "❌ MISSING"
            print(f"  • Changelog: {self.changelog_file} {exists}")
        else:
            print(f"  • Changelog: Not configured")
        
        print(f"\nBuild Options:")
        print(f"  • Single File: {'✅' if self.build_options.get('onefile', True) else '❌'}")
        print(f"  • Windowed: {'✅' if self.build_options.get('windowed', True) else '❌'}")
        print(f"  • Clean Build: {'✅' if self.build_options.get('clean', True) else '❌'}")
        print(f"  • Debug Mode: {'✅' if self.build_options.get('debug', False) else '❌'}")
        
        if self.additional_files:
            print(f"\nAdditional Files ({len(self.additional_files)}):")
            for i, file_path in enumerate(self.additional_files, 1):
                exists = "✅" if os.path.exists(file_path) else "❌ MISSING"
                print(f"  {i}. {file_path} {exists}")
        else:
            print(f"\nAdditional Files: None")
        
        if self.known_issues:
            print(f"\nKnown Issues ({len(self.known_issues)}):")
            for i, issue in enumerate(self.known_issues, 1):
                print(f"  {i}. {issue}")
        else:
            print(f"\nKnown Issues: None")
        
        if self.build_notes:
            print(f"\nBuild Notes:")
            print(f"  {self.build_notes}")
        else:
            print(f"\nBuild Notes: None")
    
    def export_configuration(self):
        """Export configuration to a custom named file"""
        if not hasattr(self, 'program_name') or not self.program_name:
            print("❌ No configuration to export!")
            return
        
        # Suggest filename
        date_str = self.get_date_string()
        suggested_name = f"build_config_{self.program_name.lower().replace(' ', '_')}_{date_str}.json"
        
        filename = input(f"Export filename [{suggested_name}]: ").strip()
        if not filename:
            filename = suggested_name
        
        # Add .json extension if not present
        if not filename.endswith('.json'):
            filename += '.json'
        
        try:
            # Create the config data (same as save_build_config but with export metadata)
            from datetime import datetime
            config = {
                'config_version': '2.0',
                'exported_date': datetime.now().isoformat(),
                'exported_by': 'PyInstaller Build Script Enhanced',
                'original_config_file': 'build_config.json',
                
                'program_name': self.program_name,
                'build_status': self.build_status,
                'main_entry': self.main_entry,
                'additional_files': self.additional_files,
                'build_options': self.build_options,
                'changelog_file': self.changelog_file,
                'known_issues': self.known_issues,
                'build_notes': self.build_notes,
                
                'file_paths': {
                    'icon': self.build_options.get('icon', ''),
                    'splash': self.build_options.get('splash', ''),
                    'main_entry': self.main_entry,
                    'changelog': self.changelog_file,
                    'additional_files': self.additional_files
                },
                
                'settings_summary': {
                    'has_icon': 'icon' in self.build_options,
                    'has_splash': 'splash' in self.build_options,
                    'has_changelog': bool(self.changelog_file),
                    'onefile': self.build_options.get('onefile', True),
                    'windowed': self.build_options.get('windowed', True),
                    'clean': self.build_options.get('clean', True),
                    'debug': self.build_options.get('debug', False),
                    'additional_files_count': len(self.additional_files),
                    'known_issues_count': len(self.known_issues)
                }
            }
            
            import json
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Configuration exported to: {filename}")
            
        except Exception as e:
            print(f"❌ Export failed: {e}")
    
    def import_configuration(self):
        """Import configuration from a custom file"""
        filename = input("Enter configuration filename to import: ").strip()
        
        if not filename:
            print("❌ No filename provided!")
            return
        
        if not filename.endswith('.json'):
            filename += '.json'
        
        if not os.path.exists(filename):
            print(f"❌ File not found: {filename}")
            return
        
        try:
            import json
            with open(filename, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            print(f"📄 Configuration found in {filename}:")
            print(f"   • Program: {config.get('program_name', 'N/A')}")
            print(f"   • Status: {config.get('build_status', 'N/A')}")
            print(f"   • Version: {config.get('config_version', '1.0')}")
            
            if 'exported_date' in config:
                print(f"   • Exported: {config['exported_date']}")
            
            confirm = input("\nImport this configuration? (Y/n): ").lower()
            if confirm not in ['n', 'no']:
                # Load the configuration
                self.program_name = config.get('program_name', '')
                self.build_status = config.get('build_status', '')
                self.main_entry = config.get('main_entry', '')
                self.additional_files = config.get('additional_files', [])
                self.build_options = config.get('build_options', {})
                self.changelog_file = config.get('changelog_file', '')
                self.known_issues = config.get('known_issues', [])
                self.build_notes = config.get('build_notes', '')
                
                print(f"✅ Configuration imported successfully!")
                
                # Ask if they want to save as default config too
                save_default = input("Save as default configuration too? (Y/n): ").lower()
                if save_default not in ['n', 'no']:
                    self.save_build_config()
            else:
                print("❌ Import cancelled.")
                
        except Exception as e:
            print(f"❌ Import failed: {e}")

    def run(self):
        """Main application flow with enhanced configuration management"""
        while True:
            self.clear_screen()
            self.print_header()
            
            # Show main menu
            print("\n" + "=" * 60)
            print("  MAIN MENU")
            print("=" * 60)
            print("  1. Quick Build (Auto-detect settings)")
            print("  2. Custom Build (Manual configuration)")
            print("  3. Configuration Management")
            print("  4. Load Previous Configuration")
            print("  5. Exit")
            print("=" * 60)
            
            choice = input("\nSelect option (1-5): ").strip()
            
            if choice == "1":
                self.quick_build_flow()
                break
            elif choice == "2":
                self.custom_build_flow()
                break
            elif choice == "3":
                self.show_config_management_menu()
            elif choice == "4":
                if self.load_build_config():
                    print("\n✅ Configuration loaded! Proceeding to build...")
                    input("Press Enter to continue...")
                    self.proceed_with_loaded_config()
                    break
                else:
                    input("Press Enter to continue...")
            elif choice == "5":
                print("👋 Goodbye!")
                return
            else:
                print("❌ Invalid option!")
                input("Press Enter to continue...")
    
    def quick_build_flow(self):
        """Quick build with automatic detection and minimal user input"""
        print("\n🚀 Quick Build Mode - Auto-detecting settings...")
        
        # Try to load previous config as starting point
        using_previous = self.load_build_config()
        
        if not using_previous:
            # Minimal configuration needed
            self.get_program_name()
            self.get_build_status()
            self.get_main_entry()
            
            # Auto-detect files
            print("\n🔍 Auto-detecting resources...")
            
            # Auto-detect icon
            icon_file = self.find_and_select_icon()
            if icon_file:
                self.build_options['icon'] = icon_file
            
            # Auto-detect splash
            splash_file = self.find_and_select_splash()
            if splash_file:
                self.build_options['splash'] = splash_file
                self.offer_splash_code_integration()
            
            # Set default build options
            self.build_options['onefile'] = True
            self.build_options['windowed'] = True
            self.build_options['clean'] = True
            self.build_options['debug'] = False
            
            print("✅ Quick configuration complete!")
        
        self.execute_build_process()
    
    def custom_build_flow(self):
        """Full custom build with all configuration options"""
        print("\n⚙️  Custom Build Mode - Full configuration...")
        
        # Try to load previous config
        using_previous = self.load_build_config()
        
        if not using_previous:
            # Get all configuration
            self.get_program_name()
            self.get_build_status()
            self.get_main_entry()
            self.get_additional_files()
            self.get_build_options()
        else:
            # Allow modification of loaded config
            self.modify_loaded_config()
        
        self.execute_build_process()
    
    def proceed_with_loaded_config(self):
        """Proceed with build using loaded configuration"""
        print(f"\n📋 Using loaded configuration for: {self.program_name} ({self.build_status})")
        
        # Show configuration summary
        self.show_detailed_config()
        
        # Ask if user wants to modify anything
        modify = input("\nModify any settings before building? (y/N): ").lower()
        if modify in ['y', 'yes']:
            self.modify_loaded_config()
        
        self.execute_build_process()
    
    def modify_loaded_config(self):
        """Allow modification of loaded configuration"""
        print(f"\n🔧 Modifying loaded configuration...")
        print(f"Current settings loaded. Press Enter to keep current values:")
        
        # Program name
        new_name = input(f"Program name [{self.program_name}]: ").strip()
        if new_name:
            self.program_name = new_name
        
        # Build status
        print(f"Current build status: {self.build_status}")
        change_status = input("Change build status? (y/N): ").lower()
        if change_status in ['y', 'yes']:
            self.get_build_status()
        
        # Main entry
        current_entry = self.main_entry
        if not os.path.exists(current_entry):
            print(f"⚠️  Current main entry file not found: {current_entry}")
            self.get_main_entry()
        else:
            change_entry = input(f"Change main entry? Current: {current_entry} (y/N): ").lower()
            if change_entry in ['y', 'yes']:
                self.get_main_entry()
        
        # Icon
        if 'icon' in self.build_options:
            icon_path = self.build_options['icon']
            if os.path.exists(icon_path):
                change_icon = input(f"Change icon? Current: {icon_path} (y/N): ").lower()
            else:
                print(f"⚠️  Current icon file not found: {icon_path}")
                change_icon = input("Select new icon? (Y/n): ").lower()
            
            if change_icon not in ['n', 'no']:
                new_icon = self.find_and_select_icon()
                if new_icon:
                    self.build_options['icon'] = new_icon
                else:
                    if 'icon' in self.build_options:
                        del self.build_options['icon']
        else:
            add_icon = input("Add icon? (Y/n): ").lower()
            if add_icon not in ['n', 'no']:
                icon_file = self.find_and_select_icon()
                if icon_file:
                    self.build_options['icon'] = icon_file
        
        # Splash screen
        if 'splash' in self.build_options:
            splash_path = self.build_options['splash']
            if os.path.exists(splash_path):
                change_splash = input(f"Change splash screen? Current: {splash_path} (y/N): ").lower()
            else:
                print(f"⚠️  Current splash screen file not found: {splash_path}")
                change_splash = input("Select new splash screen? (Y/n): ").lower()
            
            if change_splash not in ['n', 'no']:
                new_splash = self.find_and_select_splash()
                if new_splash:
                    self.build_options['splash'] = new_splash
                    self.offer_splash_code_integration()
                else:
                    if 'splash' in self.build_options:
                        del self.build_options['splash']
        else:
            add_splash = input("Add splash screen? (y/N): ").lower()
            if add_splash in ['y', 'yes']:
                splash_file = self.find_and_select_splash()
                if splash_file:
                    self.build_options['splash'] = splash_file
                    self.offer_splash_code_integration()
        
        # Additional files
        if self.additional_files:
            modify_files = input(f"Modify additional files? Current: {len(self.additional_files)} files (y/N): ").lower()
            if modify_files in ['y', 'yes']:
                self.get_additional_files()
        else:
            add_files = input("Add additional files? (y/N): ").lower()
            if add_files in ['y', 'yes']:
                self.get_additional_files()
        
        # Build options
        modify_options = input("Modify build options (onefile, windowed, etc.)? (y/N): ").lower()
        if modify_options in ['y', 'yes']:
            # Show current options and allow changes
            print(f"\nCurrent build options:")
            print(f"  • Single File: {'✅' if self.build_options.get('onefile', True) else '❌'}")
            print(f"  • Windowed: {'✅' if self.build_options.get('windowed', True) else '❌'}")
            print(f"  • Clean Build: {'✅' if self.build_options.get('clean', True) else '❌'}")
            print(f"  • Debug Mode: {'✅' if self.build_options.get('debug', False) else '❌'}")
            
            # Individual option changes
            for option, description, default in [
                ('onefile', 'Single File', True),
                ('windowed', 'Windowed (Hide Console)', True),
                ('clean', 'Clean Build', True),
                ('debug', 'Debug Mode', False)
            ]:
                current = self.build_options.get(option, default)
                current_text = "Yes" if current else "No"
                new_value = input(f"{description}? Current: {current_text} (y/N): ").lower()
                if new_value in ['y', 'yes']:
                    self.build_options[option] = True
                elif new_value in ['n', 'no']:
                    self.build_options[option] = False
        
        print("✅ Configuration updated!")
    
    def execute_build_process(self):
        """Execute the complete build process including changelog management"""
        # Handle changelog management
        changelog_configured = self.select_changelog_file()
        version = None
        changelog_items = []
        
        if changelog_configured:
            version = self.get_version_info()
            changelog_items = self.get_changelog_content()
            
            # Check if user went back from changelog menu
            if changelog_items is None:
                print("❌ Changelog cancelled - returning to main menu.")
                return
            elif version and changelog_items and len(changelog_items) > 0:
                # Preview the changelog update
                self.preview_changelog_update(version, changelog_items)
                
                confirm_changelog = input("\nProceed with changelog update? (Y/n): ").lower()
                if confirm_changelog in ['n', 'no']:
                    print("❌ Changelog update cancelled.")
                    changelog_configured = False
            else:
                print("❌ No changelog items created.")
                changelog_configured = False
        
        # Show build preview
        self.preview_command()
        
        # Confirm and execute build
        confirm = input("\nExecute build? (Y/n): ").lower()
        if confirm not in ['n', 'no']:
            # Update changelog BEFORE building (so it's included in the build if needed)
            if changelog_configured and version and changelog_items:
                print("\n📄 Updating changelog...")
                changelog_success = self.update_main_changelog(version, changelog_items)
                if changelog_success:
                    print("✅ Changelog updated successfully!")
                else:
                    print("⚠️  Changelog update failed, but continuing with build...")
            
            # Execute the build
            self.execute_build()
            
            # Save config
            save_config = input("\nSave this configuration for next time? (Y/n): ").lower()
            if save_config not in ['n', 'no']:
                self.save_build_config()
        else:
            print("Build cancelled.")
            
            # If build was cancelled, ask if user still wants to update changelog
            if changelog_configured and version and changelog_items:
                update_anyway = input("\nBuild cancelled. Update changelog anyway? (y/N): ").lower()
                if update_anyway in ['y', 'yes']:
                    print("\n📄 Updating changelog...")
                    changelog_success = self.update_main_changelog(version, changelog_items)
                    if changelog_success:
                        print("✅ Changelog updated successfully!")
                    else:
                        print("❌ Changelog update failed.")

def main():
    """Main entry point"""
    try:
        builder = PyInstallerBuilder()
        builder.run()
    except KeyboardInterrupt:
        print("\n\nBuild cancelled by user.")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()