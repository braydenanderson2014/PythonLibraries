"""
Help System Integration for PDF Utility
This module provides functionality to access and display help documentation
that was bundled with the application during the PyInstaller build process.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import webbrowser
from pathlib import Path

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
            help_path = os.path.join(base_path, 'help')
        else:
            # Running as script
            base_path = os.path.dirname(os.path.abspath(__file__))
            help_path = os.path.join(base_path, 'Help Documents')
            
        return help_path if os.path.exists(help_path) else None
    
    def _discover_help_files(self):
        """Discover available help files"""
        help_files = {}
        
        if not self.help_dir:
            return help_files
            
        try:
            for file_name in os.listdir(self.help_dir):
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
        except OSError:
            pass
            
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
            else:
                formatted_parts.append(part.capitalize())
                
        return ' '.join(formatted_parts)
    
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
            messagebox.showinfo("Help Not Available", 
                              "Help documentation is not available in this installation.")
            return
            
        help_window = tk.Toplevel(self.parent) if self.parent else tk.Tk()
        help_window.title("PDF Utility - Help Documentation")
        help_window.geometry("900x700")
        help_window.configure(bg='white')
        
        # Create main frame
        main_frame = ttk.Frame(help_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create topic selection frame
        topic_frame = ttk.LabelFrame(main_frame, text="Help Topics")
        topic_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Topic selection combobox
        topic_label = ttk.Label(topic_frame, text="Select Topic:")
        topic_label.pack(side=tk.LEFT, padx=(10, 5), pady=10)
        
        self.topic_var = tk.StringVar()
        topic_combo = ttk.Combobox(topic_frame, textvariable=self.topic_var, 
                                 values=list(self.help_files.keys()), 
                                 state="readonly", width=30)
        topic_combo.pack(side=tk.LEFT, padx=(0, 10), pady=10)
        
        # Show help button
        show_button = ttk.Button(topic_frame, text="Show Help", 
                               command=lambda: self._display_help_content(content_text))
        show_button.pack(side=tk.LEFT, padx=(0, 10), pady=10)
        
        # Content display area
        content_frame = ttk.LabelFrame(main_frame, text="Help Content")
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Text widget with scrollbar
        content_text = scrolledtext.ScrolledText(content_frame, wrap=tk.WORD, 
                                               font=('Segoe UI', 10),
                                               bg='white', fg='black')
        content_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Bind topic selection
        topic_combo.bind('<<ComboboxSelected>>', 
                        lambda e: self._display_help_content(content_text))
        
        # Show initial topic if provided
        if topic and topic in self.help_files:
            self.topic_var.set(topic)
            self._display_help_content(content_text)
        elif self.help_files:
            # Show first available topic
            first_topic = list(self.help_files.keys())[0]
            self.topic_var.set(first_topic)
            self._display_help_content(content_text)
    
    def _display_help_content(self, text_widget):
        """Display help content in text widget"""
        topic = self.topic_var.get()
        if not topic:
            return
            
        content = self.get_help_content(topic)
        if content:
            text_widget.delete(1.0, tk.END)
            
            # Basic markdown rendering for better readability
            formatted_content = self._format_markdown_content(content)
            text_widget.insert(1.0, formatted_content)
            
            # Configure text tags for better formatting
            self._configure_text_formatting(text_widget)
        else:
            text_widget.delete(1.0, tk.END)
            text_widget.insert(1.0, f"Unable to load help content for {topic}")
    
    def _format_markdown_content(self, content):
        """Basic markdown formatting for display"""
        lines = content.split('\n')
        formatted_lines = []
        
        for line in lines:
            # Convert markdown headers to readable format
            if line.startswith('# '):
                formatted_lines.append(f"\n{line[2:].upper()}\n{'=' * len(line[2:])}")
            elif line.startswith('## '):
                formatted_lines.append(f"\n{line[3:]}\n{'-' * len(line[3:])}")
            elif line.startswith('### '):
                formatted_lines.append(f"\n{line[4:]}")
            # Convert markdown bold to uppercase
            elif '**' in line:
                line = line.replace('**', '')
                formatted_lines.append(line.upper() if line.strip() else line)
            # Convert markdown code blocks
            elif line.startswith('```'):
                formatted_lines.append('--- CODE ---' if line == '```' else '--- END CODE ---')
            else:
                formatted_lines.append(line)
                
        return '\n'.join(formatted_lines)
    
    def _configure_text_formatting(self, text_widget):
        """Configure text widget formatting"""
        text_widget.configure(font=('Consolas', 10))
        
        # Create tags for different formatting
        text_widget.tag_configure("header1", font=('Segoe UI', 14, 'bold'))
        text_widget.tag_configure("header2", font=('Segoe UI', 12, 'bold'))
        text_widget.tag_configure("code", font=('Consolas', 9), background='#f0f0f0')
    
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
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        # Add general help
        help_menu.add_command(label="Help Documentation", 
                            command=lambda: self.show_help_window())
        help_menu.add_separator()
        
        # Add specific widget help topics
        for topic_key, topic_info in self.help_files.items():
            help_menu.add_command(
                label=f"{topic_info['title']} Help",
                command=lambda t=topic_key: self.show_help_window(t)
            )
        
        help_menu.add_separator()
        help_menu.add_command(label="About PDF Utility", 
                            command=self._show_about_dialog)
    
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

Built with comprehensive help documentation for all features.
        """
        
        messagebox.showinfo("About PDF Utility", about_text)
    
    def add_help_button(self, parent_frame, widget_name, row=None, column=None):
        """Add a help button for a specific widget"""
        help_button = ttk.Button(parent_frame, text="?", width=3,
                               command=lambda: self.show_context_help(widget_name))
        
        if row is not None and column is not None:
            help_button.grid(row=row, column=column, padx=2, pady=2, sticky='ne')
        else:
            help_button.pack(side=tk.RIGHT, padx=2, pady=2)
        
        return help_button

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
