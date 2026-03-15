"""
Help System Integration for PDF Utility (PyQt6 Version)
This module provides functionality to access and display help documentation
that was bundled with the application during the PyInstaller build process.
"""

import os
import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QDialog, QVBoxLayout, QHBoxLayout, QWidget, 
    QComboBox, QPushButton, QTextEdit, QLabel, QMessageBox,
    QGroupBox, QSplitter
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QAction

class HelpSystem:
    def __init__(self, parent=None):
        self.parent = parent
        self.help_dir = self._get_help_directory()
        self.help_files = self._discover_help_files()
        
    def _get_help_directory(self):
        """Get the help directory path for the bundled application"""
        if getattr(sys, 'frozen', False):
            # Running as PyInstaller bundle
            base_path = sys._MEIPASS
            print(f"Help system: PyInstaller bundle detected, base path: {base_path}")
            
            # Try multiple possible help directory names
            help_dir_names = ['Help Documents', 'help', 'docs', 'documentation']
            for dir_name in help_dir_names:
                help_path = os.path.join(base_path, dir_name)
                print(f"Help system: Checking for help directory: {help_path}")
                if os.path.exists(help_path):
                    print(f"Help system: Found help directory: {help_path}")
                    return help_path
            
            print("Help system: No help directory found in bundle")
            return None
        else:
            # Running as script
            base_path = os.path.dirname(os.path.abspath(__file__))
            print(f"Help system: Running as script, base path: {base_path}")
            
            # Try multiple possible help directory names
            help_dir_names = ['Help Documents', 'help', 'docs', 'documentation']
            for dir_name in help_dir_names:
                help_path = os.path.join(base_path, dir_name)
                print(f"Help system: Checking for help directory: {help_path}")
                if os.path.exists(help_path):
                    print(f"Help system: Found help directory: {help_path}")
                    return help_path
            
            print("Help system: No help directory found")
            return None
    
    def _discover_help_files(self):
        """Discover available help files"""
        help_files = {}
        
        if not self.help_dir:
            print("Help system: No help directory found")
            return help_files
        
        print(f"Help system: Scanning for help files in {self.help_dir}")
            
        try:
            files_found = []
            for file_name in os.listdir(self.help_dir):
                files_found.append(file_name)
                
                if file_name.startswith('HELP_') and file_name.endswith(('.md', '.txt', '.rst')):
                    # Extract widget name from filename
                    widget_name = file_name[5:]  # Remove 'HELP_' prefix
                    widget_name = widget_name.rsplit('.', 1)[0]  # Remove extension
                    
                    file_path = os.path.join(self.help_dir, file_name)
                    help_files[widget_name] = {
                        'path': file_path,
                        'title': self._format_widget_name(widget_name),
                        'filename': file_name
                    }
                    print(f"Help system: Found help file {file_name} -> {widget_name}")
            
            print(f"Help system: Total files in directory: {len(files_found)}")
            print(f"Help system: Help files found: {len(help_files)}")
            
            if not help_files and files_found:
                print(f"Help system: Files in directory but no help files:")
                for file_name in files_found:
                    print(f"  - {file_name}")
                    
        except OSError as e:
            print(f"Help system: Error reading help directory: {e}")
            
        return help_files
    
    def _format_widget_name(self, widget_name):
        """Format widget name for display"""
        # Convert camelCase or snake_case to Title Case
        if '_' in widget_name:
            parts = widget_name.split('_')
        else:
            # Simple camelCase split
            parts = [widget_name]
            
        formatted_parts = []
        for part in parts:
            if part.lower() == 'pdf':
                formatted_parts.append('PDF')
            elif part.lower() == 'ocr':
                formatted_parts.append('OCR')
            elif part.lower() == 'tts':
                formatted_parts.append('Text-to-Speech')
            else:
                formatted_parts.append(part.capitalize())
                
        return ' '.join(formatted_parts)
    
    def _sort_help_items_with_priority(self):
        """Sort help items with priority files (containing '(1)') first"""
        help_items = []
        priority_items = []
        regular_items = []
        
        for info in self.help_files.values():
            title = info['title']
            filename = info['filename']
            
            # Check if filename contains "(1)" - these get priority
            if '(1)' in filename:
                priority_items.append(title)
            else:
                regular_items.append(title)
        
        # Sort both lists alphabetically
        priority_items.sort()
        regular_items.sort()
        
        # Combine with priority items first
        return priority_items + regular_items
    
    def get_available_topics(self):
        """Get list of available help topics"""
        return list(self.help_files.keys())
    
    def get_help_content(self, topic):
        """Get help content for a specific topic"""
        if topic not in self.help_files:
            return None
            
        try:
            with open(self.help_files[topic]['path'], 'r', encoding='utf-8') as f:
                return f.read()
        except (OSError, UnicodeDecodeError):
            return None
    
    def show_help_window(self, topic=None):
        """Show help window with content"""
        if not self.help_files:
            QMessageBox.information(self.parent, "Help Not Available", 
                                  "Help documentation is not available in this installation.")
            return
            
        help_dialog = HelpDialog(self.parent, self)
        if topic and topic in self.help_files:
            help_dialog.set_topic(topic)
        help_dialog.exec()
    
    def show_context_help(self, widget_name):
        """Show help for a specific widget context"""
        if widget_name in self.help_files:
            self.show_help_window(widget_name)
        else:
            # Try to find similar help topics
            similar_topics = [topic for topic in self.help_files.keys() 
                            if widget_name.lower() in topic.lower()]
            
            if similar_topics:
                self.show_help_window(similar_topics[0])
            else:
                self.show_help_window()
    
    def create_help_menu(self, menubar):
        """Create Help menu for the application"""
        help_menu = menubar.addMenu("Help")
        
        # Add general help
        general_help_action = QAction("Help Documentation", self.parent)
        general_help_action.triggered.connect(lambda: self.show_help_window())
        help_menu.addAction(general_help_action)
        
        help_menu.addSeparator()
        
        # Add specific widget help topics
        for topic_key, topic_info in self.help_files.items():
            action = QAction(f"{topic_info['title']} Help", self.parent)
            action.triggered.connect(lambda checked, t=topic_key: self.show_help_window(t))
            help_menu.addAction(action)
        
        help_menu.addSeparator()
        
        # About action
        about_action = QAction("About PDF Utility", self.parent)
        about_action.triggered.connect(self._show_about_dialog)
        help_menu.addAction(about_action)
        
        return help_menu
    
    def _show_about_dialog(self):
        """Show about dialog"""
        about_text = """PDF Utility
        
A comprehensive PDF processing tool with multiple widgets for:
• PDF Splitting and Merging
• Image to PDF Conversion
• White Space Removal
• Text-to-Speech Conversion
• File Search and Management
• Automated Import Processing

Built with comprehensive help documentation for all features."""
        
        QMessageBox.about(self.parent, "About PDF Utility", about_text)

class HelpDialog(QDialog):
    """Help dialog window"""
    
    def __init__(self, parent, help_system):
        super().__init__(parent)
        self.help_system = help_system
        self.setWindowTitle("PDF Utility - Help Documentation")
        self.resize(900, 700)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        
        # Topic selection group
        topic_group = QGroupBox("Help Topics")
        topic_layout = QHBoxLayout(topic_group)
        
        topic_label = QLabel("Select Topic:")
        topic_layout.addWidget(topic_label)
        
        self.topic_combo = QComboBox()
        # Sort help files with "(1)" files first, then alphabetically
        sorted_help_items = self.help_system._sort_help_items_with_priority()
        self.topic_combo.addItems(sorted_help_items)
        self.topic_combo.currentTextChanged.connect(self.on_topic_changed)
        topic_layout.addWidget(self.topic_combo)
        
        topic_layout.addStretch()
        
        show_button = QPushButton("Refresh")
        show_button.clicked.connect(self.refresh_content)
        topic_layout.addWidget(show_button)
        
        layout.addWidget(topic_group)
        
        # Content display area
        content_group = QGroupBox("Help Content")
        content_layout = QVBoxLayout(content_group)
        
        self.content_text = QTextEdit()
        self.content_text.setReadOnly(True)
        self.content_text.setFont(QFont("Segoe UI", 11))
        # Enable rich text and better formatting
        self.content_text.setAcceptRichText(True)
        self.content_text.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        content_layout.addWidget(self.content_text)
        
        layout.addWidget(content_group)
        
        # Show first topic from sorted list if available
        if self.help_system.help_files:
            # Get the first topic from our sorted priority list
            sorted_help_items = self.help_system._sort_help_items_with_priority()
            if sorted_help_items:
                first_topic_title = sorted_help_items[0]
                # Find the corresponding topic key
                first_topic_key = None
                for key, info in self.help_system.help_files.items():
                    if info['title'] == first_topic_title:
                        first_topic_key = key
                        break
                
                if first_topic_key:
                    self.set_topic(first_topic_key)
    
    def set_topic(self, topic_key):
        """Set the current topic"""
        if topic_key in self.help_system.help_files:
            topic_title = self.help_system.help_files[topic_key]['title']
            index = self.topic_combo.findText(topic_title)
            if index >= 0:
                self.topic_combo.setCurrentIndex(index)
                self.display_content(topic_key)
    
    def on_topic_changed(self, topic_title):
        """Handle topic selection change"""
        # Find topic key by title
        topic_key = None
        for key, info in self.help_system.help_files.items():
            if info['title'] == topic_title:
                topic_key = key
                break
        
        if topic_key:
            self.display_content(topic_key)
    
    def display_content(self, topic_key):
        """Display help content for the topic"""
        content = self.help_system.get_help_content(topic_key)
        if content:
            # Enhanced markdown-to-HTML conversion for better display
            html_content = self._convert_markdown_to_html(content)
            self.content_text.setHtml(html_content)
        else:
            # Create a nicely formatted error message
            error_html = f"""
            <html><head><style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 20px; }}
            .error {{ background-color: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; 
                     padding: 15px; border-radius: 5px; }}
            .error h3 {{ margin-top: 0; color: #721c24; }}
            </style></head><body>
            <div class="error">
                <h3>⚠️ Help Content Not Available</h3>
                <p>Unable to load help content for <strong>{topic_key}</strong>.</p>
                <p>This could be because:</p>
                <ul>
                    <li>The help file is missing or corrupted</li>
                    <li>There was an encoding issue reading the file</li>
                    <li>The help system is not properly configured</li>
                </ul>
                <p>Please check that the help documentation is properly installed.</p>
            </div>
            </body></html>
            """
            self.content_text.setHtml(error_html)
    
    def refresh_content(self):
        """Refresh the current content"""
        current_topic = self.topic_combo.currentText()
        self.on_topic_changed(current_topic)
    
    def _convert_markdown_to_html(self, markdown_content):
        """Convert basic markdown to HTML for better display"""
        lines = markdown_content.split('\n')
        html_lines = ['<html><head><style>']
        
        # Add comprehensive CSS styling
        html_lines.extend([
            'body { font-family: "Segoe UI", Arial, sans-serif; margin: 20px; line-height: 1.4; background-color: white; color: black; }',
            'h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 8px; margin-top: 20px; margin-bottom: 12px; }',
            'h2 { color: #34495e; border-bottom: 2px solid #95a5a6; padding-bottom: 6px; margin-top: 16px; margin-bottom: 10px; }',
            'h3 { color: #5d6d7e; margin-top: 14px; margin-bottom: 8px; }',
            'h4 { color: #626567; margin-top: 12px; margin-bottom: 6px; }',
            'h5 { color: #717d84; margin-top: 10px; margin-bottom: 4px; }',
            'h6 { color: #7f8c8d; margin-top: 8px; margin-bottom: 4px; }',
            'p { margin: 6px 0; }',
            'ul, ol { margin: 8px 0; padding-left: 25px; }',
            'li { margin: 3px 0; }',
            'blockquote { background: #f8f9fa; border-left: 4px solid #3498db; margin: 12px 0; padding: 8px 12px; font-style: italic; }',
            'code { background-color: #ecf0f1; padding: 2px 6px; border-radius: 3px; font-family: "Consolas", "Monaco", "Courier New", monospace; font-size: 90%; }',
            'pre { background-color: #2c3e50; color: #ecf0f1; padding: 12px; border-radius: 6px; overflow-x: auto; margin: 12px 0; }',
            'pre code { background: none; padding: 0; color: #ecf0f1; }',
            'table { border-collapse: collapse; width: 100%; margin: 12px 0; }',
            'th, td { border: 1px solid #bdc3c7; padding: 8px 12px; text-align: left; }',
            'th { background-color: #34495e; color: white; font-weight: bold; }',
            'tr:nth-child(even) { background-color: #f8f9fa; }',
            'a { color: #3498db; text-decoration: none; }',
            'a:hover { text-decoration: underline; }',
            'strong, b { color: black; font-weight: bold; }',
            'em, i { color: black; font-style: italic; }',
            'hr { border: none; border-top: 2px solid #bdc3c7; margin: 16px 0; }',
            '.alert { padding: 8px 12px; margin: 8px 0; border-radius: 4px; }',
            '.alert-info { background-color: #d1ecf1; border-left: 4px solid #17a2b8; color: #0c5460; }',
            '.alert-warning { background-color: #fff3cd; border-left: 4px solid #ffc107; color: #856404; }',
            '.alert-success { background-color: #d4edda; border-left: 4px solid #28a745; color: #155724; }',
            '.alert-danger { background-color: #f8d7da; border-left: 4px solid #dc3545; color: #721c24; }'
        ])
        
        html_lines.extend(['</style></head><body>'])
        
        in_code_block = False
        in_list = False
        list_type = None  # 'ul' or 'ol'
        in_table = False
        table_headers = []
        
        i = 0
        while i < len(lines):
            line = lines[i].rstrip()
            
            # Handle code blocks
            if line.startswith('```'):
                if in_code_block:
                    html_lines.append('</code></pre>')
                    in_code_block = False
                else:
                    language = line[3:].strip() if len(line) > 3 else ''
                    html_lines.append(f'<pre><code class="language-{language}">')
                    in_code_block = True
                i += 1
                continue
            
            if in_code_block:
                # Escape HTML in code blocks
                escaped_line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                html_lines.append(escaped_line)
                i += 1
                continue
            
            # Handle headers
            if line.startswith('#'):
                # Close any open lists
                if in_list:
                    html_lines.append(f'</{list_type}>')
                    in_list = False
                
                level = 0
                while level < len(line) and line[level] == '#':
                    level += 1
                
                if level <= 6 and level < len(line) and line[level] == ' ':
                    header_text = line[level + 1:].strip()
                    # Process inline markdown in headers
                    header_text = self._process_inline_markdown(header_text)
                    html_lines.append(f'<h{level}>{header_text}</h{level}>')
                    i += 1
                    continue
            
            # Handle horizontal rules
            if line.strip() in ['---', '***', '___']:
                if in_list:
                    html_lines.append(f'</{list_type}>')
                    in_list = False
                html_lines.append('<hr>')
                i += 1
                continue
            
            # Handle blockquotes
            if line.startswith('>'):
                if in_list:
                    html_lines.append(f'</{list_type}>')
                    in_list = False
                quote_text = line[1:].strip()
                quote_text = self._process_inline_markdown(quote_text)
                html_lines.append(f'<blockquote>{quote_text}</blockquote>')
                i += 1
                continue
            
            # Handle tables
            if '|' in line and line.strip().startswith('|') and line.strip().endswith('|'):
                if not in_table:
                    html_lines.append('<table>')
                    in_table = True
                    # Parse header row
                    cells = [cell.strip() for cell in line.strip()[1:-1].split('|')]
                    table_headers = cells
                    html_lines.append('<thead><tr>')
                    for cell in cells:
                        html_lines.append(f'<th>{self._process_inline_markdown(cell)}</th>')
                    html_lines.append('</tr></thead><tbody>')
                else:
                    # Check if it's a separator row
                    if all(c in '-|: ' for c in line):
                        i += 1
                        continue
                    # Parse data row
                    cells = [cell.strip() for cell in line.strip()[1:-1].split('|')]
                    html_lines.append('<tr>')
                    for cell in cells:
                        html_lines.append(f'<td>{self._process_inline_markdown(cell)}</td>')
                    html_lines.append('</tr>')
                i += 1
                continue
            elif in_table:
                # End table
                html_lines.append('</tbody></table>')
                in_table = False
            
            # Handle lists
            list_match = None
            if line.strip().startswith(('- ', '* ', '+ ')):
                list_match = ('ul', line[line.find(line.strip()[0]) + 2:])
            elif len(line.strip()) > 2 and line.strip()[0].isdigit() and line.strip()[1:3] in ['. ', ') ']:
                list_match = ('ol', line[line.find(line.strip()[0]) + 3:])
            
            if list_match:
                new_list_type, content = list_match
                if not in_list or list_type != new_list_type:
                    if in_list:
                        html_lines.append(f'</{list_type}>')
                    html_lines.append(f'<{new_list_type}>')
                    in_list = True
                    list_type = new_list_type
                
                content = self._process_inline_markdown(content.strip())
                html_lines.append(f'<li>{content}</li>')
                i += 1
                continue
            elif in_list:
                # End list if we're not in a list item
                html_lines.append(f'</{list_type}>')
                in_list = False
            
            # Handle empty lines - let paragraph margins handle spacing
            if not line.strip():
                # Skip empty lines, let CSS margins handle paragraph spacing
                i += 1
                continue
            
            # Handle alerts (custom extension)
            if line.strip().startswith('> **'):
                alert_type = 'info'
                if 'warning' in line.lower() or 'caution' in line.lower():
                    alert_type = 'warning'
                elif 'error' in line.lower() or 'danger' in line.lower():
                    alert_type = 'danger'
                elif 'success' in line.lower() or 'tip' in line.lower():
                    alert_type = 'success'
                
                alert_text = line.strip()[2:].strip()  # Remove "> "
                alert_text = self._process_inline_markdown(alert_text)
                html_lines.append(f'<div class="alert alert-{alert_type}">{alert_text}</div>')
                i += 1
                continue
            
            # Regular paragraphs
            paragraph_text = self._process_inline_markdown(line)
            html_lines.append(f'<p>{paragraph_text}</p>')
            
            i += 1
        
        # Close any open elements
        if in_code_block:
            html_lines.append('</code></pre>')
        if in_list:
            html_lines.append(f'</{list_type}>')
        if in_table:
            html_lines.append('</tbody></table>')
        
        html_lines.append('</body></html>')
        return '\n'.join(html_lines)
    
    def _process_inline_markdown(self, text):
        """Process inline markdown elements like bold, italic, code, links"""
        import re
        
        # Bold text (**text** or __text__)
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'__(.*?)__', r'<strong>\1</strong>', text)
        
        # Italic text (*text* or _text_)
        text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
        text = re.sub(r'\b_(.*?)_\b', r'<em>\1</em>', text)
        
        # Inline code (`code`)
        text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
        
        # Links [text](url)
        text = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2">\1</a>', text)
        
        # Auto-links <http://example.com>
        text = re.sub(r'<(https?://[^>]+)>', r'<a href="\1">\1</a>', text)
        
        # Strikethrough ~~text~~
        text = re.sub(r'~~(.*?)~~', r'<del>\1</del>', text)
        
        return text

# Global help system instance
_help_system = None

def get_help_system(parent=None):
    """Get or create global help system instance"""
    global _help_system
    if _help_system is None:
        _help_system = HelpSystem(parent)
    return _help_system

def show_help(topic=None, parent=None):
    """Convenience function to show help"""
    help_system = get_help_system(parent)
    help_system.show_help_window(topic)

def show_context_help(widget_name, parent=None):
    """Convenience function to show context-specific help"""
    help_system = get_help_system(parent)
    help_system.show_context_help(widget_name)

def create_help_button(parent, widget_name, help_system=None):
    """Create a help button for a widget"""
    if help_system is None:
        help_system = get_help_system(parent)
    
    help_button = QPushButton("?")
    help_button.setFixedSize(25, 25)
    help_button.setToolTip(f"Help for {widget_name}")
    help_button.clicked.connect(lambda: help_system.show_context_help(widget_name))
    
    return help_button
