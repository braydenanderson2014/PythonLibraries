#!/usr/bin/env python3
# search_widget.py - Advanced file search widget

import os
import fnmatch
import re
from datetime import datetime, timedelta
from typing import List, Dict, Set

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLineEdit, QComboBox, QSpinBox, QCheckBox, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar,
    QLabel, QFrame, QMessageBox, QMenu, QFileDialog, QTextEdit,
    QDateEdit, QDoubleSpinBox, QTabWidget, QSplitter, QTreeWidget,
    QTreeWidgetItem, QListWidget, QListWidgetItem, QScrollArea
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QDate, QTimer
from PyQt6.QtGui import QFont, QIcon, QPixmap, QAction

from PDFLogger import Logger


class FileSearchThread(QThread):
    """Background thread for searching files"""
    progress_update = pyqtSignal(int, int, str)  # current, total, status
    file_found = pyqtSignal(dict)  # file info dictionary
    search_complete = pyqtSignal(int)  # total files found
    
    def __init__(self, search_params: dict):
        super().__init__()
        self.search_params = search_params
        self._cancel = False
        
    def cancel(self):
        self._cancel = True
        
    def run(self):
        try:
            found_count = 0
            scanned_count = 0
            
            search_path = self.search_params['search_path']
            filename_pattern = self.search_params['filename_pattern']
            file_extensions = self.search_params['file_extensions']
            content_search = self.search_params['content_search']
            case_sensitive = self.search_params['case_sensitive']
            use_regex = self.search_params['use_regex']
            min_size = self.search_params['min_size']
            max_size = self.search_params['max_size']
            date_from = self.search_params['date_from']
            date_to = self.search_params['date_to']
            include_subdirs = self.search_params['include_subdirs']
            
            # Count total files first for progress
            total_files = 0
            if include_subdirs:
                for root, dirs, files in os.walk(search_path):
                    if self._cancel:
                        return
                    total_files += len(files)
            else:
                try:
                    total_files = len([f for f in os.listdir(search_path) 
                                     if os.path.isfile(os.path.join(search_path, f))])
                except OSError:
                    total_files = 0
            
            # Search files
            if include_subdirs:
                for root, dirs, files in os.walk(search_path):
                    if self._cancel:
                        return
                    found_count = self._search_in_directory(root, files, scanned_count, total_files, found_count)
                    scanned_count += len(files)
            else:
                try:
                    files = [f for f in os.listdir(search_path) 
                           if os.path.isfile(os.path.join(search_path, f))]
                    found_count = self._search_in_directory(search_path, files, 0, total_files, 0)
                except OSError:
                    pass
                    
            self.search_complete.emit(found_count)
            
        except Exception as e:
            print(f"Search error: {e}")
            self.search_complete.emit(0)
    
    def _search_in_directory(self, directory: str, files: List[str], scanned_start: int, total_files: int, found_start: int) -> int:
        """Search files in a specific directory"""
        found_count = found_start
        
        for i, filename in enumerate(files):
            if self._cancel:
                return found_count
                
            scanned_count = scanned_start + i + 1
            self.progress_update.emit(scanned_count, total_files, f"Scanning: {filename}")
            
            filepath = os.path.join(directory, filename)
            
            try:
                if self._matches_criteria(filepath, filename):
                    file_info = self._get_file_info(filepath)
                    self.file_found.emit(file_info)
                    found_count += 1
            except Exception as e:
                # Skip files that can't be accessed
                continue
                
        return found_count
    
    def _matches_criteria(self, filepath: str, filename: str) -> bool:
        """Check if file matches search criteria"""
        params = self.search_params
        
        # Filename pattern match
        if params['filename_pattern']:
            pattern = params['filename_pattern']
            filename_contains = params.get('filename_contains', True)
            
            if filename_contains:
                # Simple contains search
                search_filename = filename if params['case_sensitive'] else filename.lower()
                search_pattern = pattern if params['case_sensitive'] else pattern.lower()
                if search_pattern not in search_filename:
                    return False
            elif params['use_regex']:
                # Regex search
                flags = 0 if params['case_sensitive'] else re.IGNORECASE
                if not re.search(pattern, filename, flags):
                    return False
            else:
                # Wildcard pattern search
                if params['case_sensitive']:
                    if not fnmatch.fnmatch(filename, pattern):
                        return False
                else:
                    if not fnmatch.fnmatch(filename.lower(), pattern.lower()):
                        return False
        
        # File extension filter
        if params['file_extensions']:
            ext = os.path.splitext(filename)[1].lower()
            if ext not in [e.lower() for e in params['file_extensions']]:
                return False
        
        # File size filter
        try:
            file_size = os.path.getsize(filepath)
            if params['min_size'] > 0 and file_size < params['min_size']:
                return False
            if params['max_size'] > 0 and file_size > params['max_size']:
                return False
        except OSError:
            return False
        
        # Date filter
        try:
            mod_time = datetime.fromtimestamp(os.path.getmtime(filepath))
            if params['date_from'] and mod_time.date() < params['date_from']:
                return False
            if params['date_to'] and mod_time.date() > params['date_to']:
                return False
        except OSError:
            return False
        
        # Content search (for text files)
        if params['content_search']:
            content_contains = params.get('content_contains', True)
            content_case_sensitive = params.get('content_case_sensitive', False)
            content_regex = params.get('content_regex', False)
            
            if not self._search_file_content(filepath, params['content_search'], 
                                           content_case_sensitive, content_regex, content_contains):
                return False
        
        return True
    
    def _search_file_content(self, filepath: str, search_text: str, case_sensitive: bool, use_regex: bool, use_contains: bool = True) -> bool:
        """Search for text within file content"""
        try:
            # Only search in text-based files
            text_extensions = {'.txt', '.pdf', '.doc', '.docx', '.py', '.js', '.html', '.css', '.xml', '.json', '.csv'}
            ext = os.path.splitext(filepath)[1].lower()
            
            if ext not in text_extensions:
                return False
            
            # For PDF files, we'd need a PDF reader library
            if ext == '.pdf':
                # Placeholder - would need PyPDF2 or similar
                return False
            
            # For text files
            encodings = ['utf-8', 'latin-1', 'cp1252']
            for encoding in encodings:
                try:
                    with open(filepath, 'r', encoding=encoding) as f:
                        content = f.read()
                        
                    if use_regex:
                        flags = 0 if case_sensitive else re.IGNORECASE
                        return bool(re.search(search_text, content, flags))
                    elif use_contains:
                        # Simple contains search (new default)
                        if case_sensitive:
                            return search_text in content
                        else:
                            return search_text.lower() in content.lower()
                    else:
                        # Exact word matching (legacy)
                        if case_sensitive:
                            return search_text in content
                        else:
                            return search_text.lower() in content.lower()
                except UnicodeDecodeError:
                    continue
                    
        except Exception:
            pass
            
        return False
    
    def _get_file_info(self, filepath: str) -> dict:
        """Get comprehensive file information"""
        try:
            stat = os.stat(filepath)
            size = stat.st_size
            mod_time = datetime.fromtimestamp(stat.st_mtime)
            
            return {
                'path': filepath,
                'name': os.path.basename(filepath),
                'directory': os.path.dirname(filepath),
                'size': size,
                'size_formatted': self._format_file_size(size),
                'modified': mod_time,
                'modified_formatted': mod_time.strftime('%Y-%m-%d %H:%M:%S'),
                'extension': os.path.splitext(filepath)[1].lower(),
                'is_pdf': filepath.lower().endswith('.pdf')
            }
        except OSError:
            return {
                'path': filepath,
                'name': os.path.basename(filepath),
                'directory': os.path.dirname(filepath),
                'size': 0,
                'size_formatted': '0 B',
                'modified': datetime.now(),
                'modified_formatted': 'Unknown',
                'extension': os.path.splitext(filepath)[1].lower(),
                'is_pdf': filepath.lower().endswith('.pdf')
            }
    
    def _format_file_size(self, size: int) -> str:
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"


class MemorySearchThread(QThread):
    """Background thread for searching loaded PDFs in memory"""
    progress_update = pyqtSignal(int, int, str)  # current, total, status
    file_found = pyqtSignal(dict)  # file info dictionary with search results
    search_complete = pyqtSignal(int)  # total files found
    
    def __init__(self, search_params: dict, pdf_files: List[str]):
        super().__init__()
        self.search_params = search_params
        self.pdf_files = pdf_files
        self._cancel = False
        
    def cancel(self):
        self._cancel = True
        
    def run(self):
        try:
            found_count = 0
            total_files = len(self.pdf_files)
            
            content_search = self.search_params['content_search']
            content_contains = self.search_params.get('content_contains', True)
            content_regex = self.search_params.get('content_regex', False)
            content_case_sensitive = self.search_params.get('content_case_sensitive', False)
            filename_pattern = self.search_params['filename_pattern']
            filename_contains = self.search_params.get('filename_contains', True)
            case_sensitive = self.search_params['case_sensitive']
            use_regex = self.search_params['use_regex']
            
            for i, pdf_path in enumerate(self.pdf_files):
                if self._cancel:
                    break
                
                try:
                    # Update progress
                    self.progress_update.emit(i + 1, total_files, f"Searching {os.path.basename(pdf_path)}")
                    
                    # Check if file exists
                    if not os.path.exists(pdf_path):
                        continue
                    
                    # Apply filename filter if enabled
                    if filename_pattern:
                        filename = os.path.basename(pdf_path)
                        if filename_contains:
                            # Simple contains search
                            search_filename = filename if case_sensitive else filename.lower()
                            search_pattern = filename_pattern if case_sensitive else filename_pattern.lower()
                            if search_pattern not in search_filename:
                                continue
                        elif use_regex:
                            # Regex search
                            if not re.search(filename_pattern, filename, 0 if case_sensitive else re.IGNORECASE):
                                continue
                        else:
                            # Wildcard pattern search
                            if not fnmatch.fnmatch(filename.lower() if not case_sensitive else filename, 
                                                 filename_pattern.lower() if not case_sensitive else filename_pattern):
                                continue
                    
                    # Get basic file info
                    file_info = self._get_file_info(pdf_path)
                    
                    # Search content if enabled
                    if content_search:
                        search_results = self._search_pdf_content(pdf_path, content_search, content_case_sensitive, content_regex, content_contains)
                        if search_results:
                            file_info['content_matches'] = search_results
                            file_info['match_count'] = len(search_results)
                        else:
                            continue  # No matches found, skip this file
                    else:
                        # If no content search, just include file if it matches filename criteria
                        file_info['content_matches'] = []
                        file_info['match_count'] = 0
                    
                    self.file_found.emit(file_info)
                    found_count += 1
                    
                except Exception as e:
                    # Log error but continue
                    print(f"Error searching {pdf_path}: {e}")
                    continue
            
            self.search_complete.emit(found_count)
            
        except Exception as e:
            print(f"Memory search thread error: {e}")
            self.search_complete.emit(0)
    
    def _search_pdf_content(self, pdf_path: str, search_term: str, case_sensitive: bool, use_regex: bool, use_contains: bool = True) -> List[Dict]:
        """Search for content within a PDF file"""
        matches = []
        
        try:
            import fitz  # PyMuPDF
            
            with fitz.open(pdf_path) as doc:
                for page_num, page in enumerate(doc, 1):
                    if self._cancel:
                        break
                        
                    try:
                        text = page.get_text()
                        if not text.strip():
                            continue
                        
                        if use_regex:
                            flags = 0 if case_sensitive else re.IGNORECASE
                            pattern_matches = list(re.finditer(search_term, text, flags))
                            for match in pattern_matches:
                                context_start = max(0, match.start() - 50)
                                context_end = min(len(text), match.end() + 50)
                                context = text[context_start:context_end].strip()
                                
                                matches.append({
                                    'page': page_num,
                                    'match': match.group(),
                                    'context': context,
                                    'position': match.start()
                                })
                        elif use_contains:
                            # Simple contains search (new default behavior)
                            search_text = search_term if case_sensitive else search_term.lower()
                            page_text = text if case_sensitive else text.lower()
                            
                            start = 0
                            while True:
                                pos = page_text.find(search_text, start)
                                if pos == -1:
                                    break
                                
                                context_start = max(0, pos - 50)
                                context_end = min(len(text), pos + len(search_term) + 50)
                                context = text[context_start:context_end].strip()
                                
                                matches.append({
                                    'page': page_num,
                                    'match': text[pos:pos + len(search_term)],
                                    'context': context,
                                    'position': pos
                                })
                                
                                start = pos + 1
                        else:
                            # Exact word matching (legacy behavior)
                            search_text = search_term if case_sensitive else search_term.lower()
                            page_text = text if case_sensitive else text.lower()
                            
                            start = 0
                            while True:
                                pos = page_text.find(search_text, start)
                                if pos == -1:
                                    break
                                
                                context_start = max(0, pos - 50)
                                context_end = min(len(text), pos + len(search_term) + 50)
                                context = text[context_start:context_end].strip()
                                
                                matches.append({
                                    'page': page_num,
                                    'match': text[pos:pos + len(search_term)],
                                    'context': context,
                                    'position': pos
                                })
                                
                                start = pos + 1
                                
                    except Exception as e:
                        print(f"Error searching page {page_num} in {pdf_path}: {e}")
                        continue
                        
        except Exception as e:
            print(f"Error opening PDF {pdf_path}: {e}")
            
        return matches
    
    def _get_file_info(self, filepath: str) -> dict:
        """Get comprehensive file information"""
        try:
            stat = os.stat(filepath)
            size = stat.st_size
            mod_time = datetime.fromtimestamp(stat.st_mtime)
            
            return {
                'path': filepath,
                'name': os.path.basename(filepath),
                'directory': os.path.dirname(filepath),
                'size': size,
                'size_formatted': self._format_file_size(size),
                'modified': mod_time,
                'modified_formatted': mod_time.strftime('%Y-%m-%d %H:%M:%S'),
                'extension': os.path.splitext(filepath)[1].lower(),
                'is_pdf': filepath.lower().endswith('.pdf'),
                'source': 'memory'
            }
        except OSError:
            return {
                'path': filepath,
                'name': os.path.basename(filepath),
                'directory': os.path.dirname(filepath),
                'size': 0,
                'size_formatted': '0 B',
                'modified': datetime.now(),
                'modified_formatted': 'Unknown',
                'extension': os.path.splitext(filepath)[1].lower(),
                'is_pdf': filepath.lower().endswith('.pdf'),
                'source': 'memory'
            }
    
    def _format_file_size(self, size: int) -> str:
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"


class SearchWidget(QWidget):
    """Advanced file search widget with rich filtering options"""
    
    def __init__(self, parent=None, file_list_controller=None, merger_widget=None, splitter_widget=None):
        super().__init__(parent)
        self.file_list_controller = file_list_controller
        self.merger_widget = merger_widget
        self.splitter_widget = splitter_widget
        self.logger = Logger()
        
        # Search state
        self.search_thread = None
        self.search_results = []
        self.is_searching = False
        
        self.setup_ui()
        
        # Set default path to system Documents folder
        self.set_default_search_path()
    
    def get_documents_folder(self) -> str:
        """Get the system's Documents folder path, handling OneDrive redirection"""
        import platform
        
        system = platform.system().lower()
        if system == "windows":
            # Windows Documents folder - handle OneDrive redirection
            try:
                # Try to get the actual Documents folder from Windows registry or shell folders
                import winreg
                import ctypes
                from ctypes import wintypes
                
                # Try to get the real Documents folder path from Windows
                try:
                    # Use SHGetFolderPath to get the actual Documents folder
                    CSIDL_MYDOCUMENTS = 5
                    buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
                    ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_MYDOCUMENTS, None, 0, buf)
                    default_path = buf.value
                    if default_path and os.path.exists(default_path):
                        return default_path
                except:
                    pass
                
                # Fallback: Try common OneDrive locations
                onedrive_paths = [
                    os.path.join(os.path.expanduser("~"), "OneDrive", "Documents"),
                    os.path.join(os.path.expanduser("~"), "OneDrive - Personal", "Documents"),
                    os.path.join(os.environ.get("OneDrive", ""), "Documents") if os.environ.get("OneDrive") else None,
                    os.path.join(os.environ.get("OneDriveConsumer", ""), "Documents") if os.environ.get("OneDriveConsumer") else None,
                ]
                
                # Check OneDrive paths first
                for path in onedrive_paths:
                    if path and os.path.exists(path):
                        return path
                
                # Standard Windows Documents folder
                default_path = os.path.join(os.path.expanduser("~"), "Documents")
                
            except ImportError:
                # If winreg is not available, fall back to standard path
                default_path = os.path.join(os.path.expanduser("~"), "Documents")
                
        elif system == "darwin":  # macOS
            default_path = os.path.join(os.path.expanduser("~"), "Documents")
        else:  # Linux and other Unix-like systems
            # Try common locations for Documents folder
            documents_paths = [
                os.path.join(os.path.expanduser("~"), "Documents"),
                os.path.join(os.path.expanduser("~"), "documents"),
                os.path.expanduser("~")  # Fallback to home directory
            ]
            default_path = next((path for path in documents_paths if os.path.exists(path)), os.path.expanduser("~"))
        
        # Ensure the default path exists, fallback to home directory
        if not os.path.exists(default_path):
            default_path = os.path.expanduser("~")
        
        return default_path
    
    def set_default_search_path(self):
        """Set the default search path to the Documents folder"""
        documents_path = self.get_documents_folder()
        self.path_edit.setText(documents_path)
        
    def setup_ui(self):
        """Set up the user interface"""
        layout = QVBoxLayout(self)
        
        # Create splitter for search criteria and results
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Left panel - Search criteria with scroll area
        criteria_widget = self.create_search_criteria_widget()
        
        # Wrap criteria widget in a scroll area
        criteria_scroll = QScrollArea()
        criteria_scroll.setWidget(criteria_widget)
        criteria_scroll.setWidgetResizable(True)
        criteria_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        criteria_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        criteria_scroll.setMinimumWidth(300)  # Ensure minimum usable width
        criteria_scroll.setMaximumWidth(450)  # Prevent it from getting too wide
        
        splitter.addWidget(criteria_scroll)
        
        # Right panel - Results
        results_widget = self.create_results_widget()
        splitter.addWidget(results_widget)
        
        # Set splitter proportions (criteria panel smaller, results panel larger)
        splitter.setSizes([350, 650])
        
        # Status bar
        self.status_label = QLabel("Ready to search")
        layout.addWidget(self.status_label)
        
    def create_search_criteria_widget(self) -> QWidget:
        """Create the search criteria panel"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Path selection
        path_group = QGroupBox("Search Location")
        path_layout = QVBoxLayout(path_group)
        
        path_input_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Select folder to search...")
        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_folder)
        
        path_input_layout.addWidget(self.path_edit)
        path_input_layout.addWidget(self.browse_button)
        path_layout.addLayout(path_input_layout)
        
        self.include_subdirs_cb = QCheckBox("Include subdirectories")
        self.include_subdirs_cb.setChecked(True)
        path_layout.addWidget(self.include_subdirs_cb)
        
        # In-memory search toggle
        self.search_memory_cb = QCheckBox("Search loaded PDFs in memory")
        self.search_memory_cb.setToolTip("Search through PDFs currently loaded in the Merger and Splitter widgets")
        self.search_memory_cb.stateChanged.connect(self.toggle_memory_search)
        path_layout.addWidget(self.search_memory_cb)
        
        layout.addWidget(path_group)
        
        # Filename criteria
        filename_group = QGroupBox("Filename Criteria")
        filename_layout = QGridLayout(filename_group)
        
        self.use_filename_filter_cb = QCheckBox("Enable filename pattern filter")
        self.use_filename_filter_cb.stateChanged.connect(self.toggle_filename_filter)
        filename_layout.addWidget(self.use_filename_filter_cb, 0, 0, 1, 2)
        
        self.pattern_label = QLabel("Pattern:")
        filename_layout.addWidget(self.pattern_label, 1, 0)
        self.filename_pattern_edit = QLineEdit()
        self.filename_pattern_edit.setPlaceholderText("*.pdf or regex pattern or simple text")
        self.filename_pattern_edit.setEnabled(False)
        filename_layout.addWidget(self.filename_pattern_edit, 1, 1)
        
        # Search mode options
        self.filename_contains_cb = QCheckBox("Simple contains search")
        self.filename_contains_cb.setChecked(True)  # Default to simple contains
        self.filename_contains_cb.setToolTip("Search for text anywhere in filename (e.g., 'test' matches 'test_file.pdf')")
        self.filename_contains_cb.setEnabled(False)
        filename_layout.addWidget(self.filename_contains_cb, 2, 0, 1, 2)
        
        self.use_regex_cb = QCheckBox("Use regular expressions")
        self.use_regex_cb.setToolTip("Advanced pattern matching with regex")
        self.use_regex_cb.setEnabled(False)
        filename_layout.addWidget(self.use_regex_cb, 3, 0, 1, 2)
        
        self.case_sensitive_cb = QCheckBox("Case sensitive")
        self.case_sensitive_cb.setEnabled(False)
        filename_layout.addWidget(self.case_sensitive_cb, 4, 0, 1, 2)
        
        layout.addWidget(filename_group)
        
        # File type filter
        filetype_group = QGroupBox("File Type Filter")
        filetype_layout = QVBoxLayout(filetype_group)
        
        # Common file types
        type_layout = QGridLayout()
        self.pdf_cb = QCheckBox("PDF (.pdf)")
        self.pdf_cb.setChecked(True)
        self.doc_cb = QCheckBox("Documents (.doc, .docx)")
        self.txt_cb = QCheckBox("Text (.txt)")
        self.image_cb = QCheckBox("Images (.jpg, .png, .gif)")
        self.all_files_cb = QCheckBox("All files")
        
        type_layout.addWidget(self.pdf_cb, 0, 0)
        type_layout.addWidget(self.doc_cb, 0, 1)
        type_layout.addWidget(self.txt_cb, 1, 0)
        type_layout.addWidget(self.image_cb, 1, 1)
        type_layout.addWidget(self.all_files_cb, 2, 0, 1, 2)
        
        filetype_layout.addLayout(type_layout)
        
        # Custom extensions
        custom_layout = QHBoxLayout()
        custom_layout.addWidget(QLabel("Custom:"))
        self.custom_extensions_edit = QLineEdit()
        self.custom_extensions_edit.setPlaceholderText(".xyz, .abc (comma separated)")
        custom_layout.addWidget(self.custom_extensions_edit)
        filetype_layout.addLayout(custom_layout)
        
        layout.addWidget(filetype_group)
        
        # File size filter
        size_group = QGroupBox("File Size Filter")
        size_layout = QGridLayout(size_group)
        
        # Enable checkbox for size filter
        self.use_size_filter_cb = QCheckBox("Enable file size filter")
        self.use_size_filter_cb.stateChanged.connect(self.toggle_size_filter)
        size_layout.addWidget(self.use_size_filter_cb, 0, 0, 1, 2)
        
        self.min_size_label = QLabel("Min size:")
        size_layout.addWidget(self.min_size_label, 1, 0)
        self.min_size_spin = QDoubleSpinBox()
        self.min_size_spin.setRange(0, 999999)
        self.min_size_spin.setSuffix(" MB")
        self.min_size_spin.setEnabled(False)
        size_layout.addWidget(self.min_size_spin, 1, 1)
        
        self.max_size_label = QLabel("Max size:")
        size_layout.addWidget(self.max_size_label, 2, 0)
        self.max_size_spin = QDoubleSpinBox()
        self.max_size_spin.setRange(0, 999999)
        self.max_size_spin.setSuffix(" MB")
        self.max_size_spin.setEnabled(False)
        size_layout.addWidget(self.max_size_spin, 2, 1)
        
        layout.addWidget(size_group)
        
        # Date filter
        date_group = QGroupBox("Date Filter")
        date_layout = QGridLayout(date_group)
        
        self.use_date_filter_cb = QCheckBox("Enable date filter")
        self.use_date_filter_cb.stateChanged.connect(self.toggle_date_filter)
        date_layout.addWidget(self.use_date_filter_cb, 0, 0, 1, 2)
        
        self.date_from_label = QLabel("Modified from:")
        date_layout.addWidget(self.date_from_label, 1, 0)
        self.date_from_edit = QDateEdit()
        self.date_from_edit.setCalendarPopup(True)
        self.date_from_edit.setDate(QDate.currentDate().addYears(-1))
        self.date_from_edit.setEnabled(False)
        date_layout.addWidget(self.date_from_edit, 1, 1)
        
        self.date_to_label = QLabel("Modified to:")
        date_layout.addWidget(self.date_to_label, 2, 0)
        self.date_to_edit = QDateEdit()
        self.date_to_edit.setCalendarPopup(True)
        self.date_to_edit.setDate(QDate.currentDate())
        self.date_to_edit.setEnabled(False)
        date_layout.addWidget(self.date_to_edit, 2, 1)
        
        layout.addWidget(date_group)
        
        # Content search
        content_group = QGroupBox("Content Search")
        content_layout = QVBoxLayout(content_group)
        
        self.use_content_filter_cb = QCheckBox("Enable content search")
        self.use_content_filter_cb.stateChanged.connect(self.toggle_content_filter)
        content_layout.addWidget(self.use_content_filter_cb)
        
        self.content_search_edit = QLineEdit()
        self.content_search_edit.setPlaceholderText("Search text within files...")
        self.content_search_edit.setEnabled(False)
        content_layout.addWidget(self.content_search_edit)
        
        # Content search mode options
        content_options_layout = QVBoxLayout()
        
        self.content_contains_cb = QCheckBox("Simple contains search")
        self.content_contains_cb.setChecked(True)  # Default to simple contains
        self.content_contains_cb.setToolTip("Search for text anywhere in content (e.g., 'test' matches any occurrence)")
        self.content_contains_cb.setEnabled(False)
        content_options_layout.addWidget(self.content_contains_cb)
        
        self.content_regex_cb = QCheckBox("Use regular expressions for content")
        self.content_regex_cb.setToolTip("Advanced pattern matching within PDF content")
        self.content_regex_cb.setEnabled(False)
        content_options_layout.addWidget(self.content_regex_cb)
        
        self.content_case_sensitive_cb = QCheckBox("Case sensitive content search")
        self.content_case_sensitive_cb.setEnabled(False)
        content_options_layout.addWidget(self.content_case_sensitive_cb)
        
        content_layout.addLayout(content_options_layout)
        
        layout.addWidget(content_group)
        
        # Search buttons
        button_layout = QHBoxLayout()
        self.search_button = QPushButton("Start Search")
        self.search_button.clicked.connect(self.start_search)
        self.stop_button = QPushButton("Stop Search")
        self.stop_button.clicked.connect(self.stop_search)
        self.stop_button.setEnabled(False)
        self.clear_button = QPushButton("Clear Results")
        self.clear_button.clicked.connect(self.clear_results)
        
        button_layout.addWidget(self.search_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.clear_button)
        layout.addLayout(button_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        layout.addStretch()
        
        return widget
    
    def toggle_size_filter(self, state):
        """Toggle size filter controls"""
        enabled = state == Qt.CheckState.Checked.value
        self.min_size_label.setEnabled(enabled)
        self.min_size_spin.setEnabled(enabled)
        self.max_size_label.setEnabled(enabled)
        self.max_size_spin.setEnabled(enabled)
    
    def toggle_date_filter(self, state):
        """Toggle date filter controls"""
        enabled = state == Qt.CheckState.Checked.value
        self.date_from_label.setEnabled(enabled)
        self.date_from_edit.setEnabled(enabled)
        self.date_to_label.setEnabled(enabled)
        self.date_to_edit.setEnabled(enabled)
    
    def toggle_content_filter(self, state):
        """Toggle content search controls"""
        enabled = state == Qt.CheckState.Checked.value
        self.content_search_edit.setEnabled(enabled)
        self.content_contains_cb.setEnabled(enabled)
        self.content_regex_cb.setEnabled(enabled)
        self.content_case_sensitive_cb.setEnabled(enabled)
    
    def toggle_filename_filter(self, state):
        """Toggle filename pattern filter controls"""
        enabled = state == Qt.CheckState.Checked.value
        self.pattern_label.setEnabled(enabled)
        self.filename_pattern_edit.setEnabled(enabled)
        self.filename_contains_cb.setEnabled(enabled)
        self.use_regex_cb.setEnabled(enabled)
        self.case_sensitive_cb.setEnabled(enabled)
    
    def toggle_memory_search(self, state):
        """Toggle in-memory search mode"""
        enabled = state == Qt.CheckState.Checked.value
        
        # When memory search is enabled, disable file system search controls
        self.path_edit.setEnabled(not enabled)
        self.browse_button.setEnabled(not enabled)
        self.include_subdirs_cb.setEnabled(not enabled)
        
        if enabled:
            # Update status to show memory search mode
            loaded_pdfs = self.get_loaded_pdfs_from_memory()
            count = len(loaded_pdfs)
            self.status_label.setText(f"Memory search mode: {count} PDFs loaded in widgets")
        else:
            self.status_label.setText("File system search mode")
    
    def get_loaded_pdfs_from_memory(self) -> List[str]:
        """Get list of PDF files currently loaded in memory across all widgets"""
        loaded_pdfs = []
        
        # Get PDFs from merger widget
        if self.merger_widget and hasattr(self.merger_widget, 'pdf_list'):
            for i in range(self.merger_widget.pdf_list.count()):
                item = self.merger_widget.pdf_list.item(i)
                if item:
                    pdf_path = item.text()
                    if pdf_path not in loaded_pdfs:
                        loaded_pdfs.append(pdf_path)
        
        # Get PDFs from splitter widget
        if self.splitter_widget and hasattr(self.splitter_widget, 'pdf_list'):
            for i in range(self.splitter_widget.pdf_list.count()):
                item = self.splitter_widget.pdf_list.item(i)
                if item:
                    pdf_path = item.text()
                    if pdf_path not in loaded_pdfs:
                        loaded_pdfs.append(pdf_path)
        
        # Get PDFs from file list controller if available
        if self.file_list_controller and hasattr(self.file_list_controller, 'get_all_files'):
            try:
                controller_files = self.file_list_controller.get_all_files()
                for file_path in controller_files:
                    if file_path.lower().endswith('.pdf') and file_path not in loaded_pdfs:
                        loaded_pdfs.append(file_path)
            except Exception as e:
                self.logger.warning("SearchWidget", f"Could not get files from controller: {e}")
        
        return loaded_pdfs
    
    def create_results_widget(self) -> QWidget:
        """Create the results panel"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Results header
        header_layout = QHBoxLayout()
        self.results_label = QLabel("Search Results (0 files)")
        header_layout.addWidget(self.results_label)
        header_layout.addStretch()
        
        # Export button
        self.export_button = QPushButton("Export Results")
        self.export_button.clicked.connect(self.export_results)
        self.export_button.setEnabled(False)
        header_layout.addWidget(self.export_button)
        
        layout.addLayout(header_layout)
        
        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels([
            "Name", "Path", "Size", "Modified", "Type", "Directory"
        ])
        
        # Set column properties
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Name
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)          # Path
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Size
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Modified
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Type
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)          # Directory
        
        # Context menu
        self.results_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.results_table.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addWidget(self.results_table)
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        self.open_file_button = QPushButton("Open File")
        self.open_file_button.clicked.connect(self.open_selected_file)
        self.open_file_button.setEnabled(False)
        
        self.open_folder_button = QPushButton("Open Folder")
        self.open_folder_button.clicked.connect(self.open_selected_folder)
        self.open_folder_button.setEnabled(False)
        
        self.add_to_list_button = QPushButton("Add PDFs to List")
        self.add_to_list_button.clicked.connect(self.add_pdfs_to_list)
        self.add_to_list_button.setEnabled(False)
        
        action_layout.addWidget(self.open_file_button)
        action_layout.addWidget(self.open_folder_button)
        action_layout.addWidget(self.add_to_list_button)
        action_layout.addStretch()
        
        layout.addLayout(action_layout)
        
        # Connect selection change
        self.results_table.itemSelectionChanged.connect(self.on_selection_changed)
        
        return widget
    
    def browse_folder(self):
        """Browse for search folder"""
        # Use the Documents folder as the default starting location
        default_path = self.get_documents_folder()
        
        folder = QFileDialog.getExistingDirectory(self, "Select Search Folder", default_path)
        if folder:
            self.path_edit.setText(folder)
    
    def start_search(self):
        """Start the file search"""
        # Check if we're in memory search mode
        if self.search_memory_cb.isChecked():
            return self.start_memory_search()
        
        # Regular file system search validation
        if not self.path_edit.text():
            QMessageBox.warning(self, "Warning", "Please select a folder to search.")
            return
        
        if not os.path.exists(self.path_edit.text()):
            QMessageBox.warning(self, "Warning", "Selected folder does not exist.")
            return
        
        # Prepare search parameters
        search_params = self.get_search_parameters()
        
        # Clear previous results
        self.clear_results()
        
        # Start search thread
        self.search_thread = FileSearchThread(search_params)
        self.search_thread.progress_update.connect(self.on_search_progress)
        self.search_thread.file_found.connect(self.on_file_found)
        self.search_thread.search_complete.connect(self.on_search_complete)
        
        self.search_thread.start()
        
        # Update UI
        self.is_searching = True
        self.search_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.status_label.setText("Starting search...")
        
        self.logger.info("SearchWidget", f"Started search in: {search_params['search_path']}")
    
    def start_memory_search(self):
        """Start searching through loaded PDFs in memory"""
        # Get loaded PDFs
        loaded_pdfs = self.get_loaded_pdfs_from_memory()
        
        if not loaded_pdfs:
            QMessageBox.information(
                self, "Info", 
                "No PDFs are currently loaded in the Merger or Splitter widgets.\n"
                "Please add some PDFs to those widgets first, or disable memory search mode."
            )
            return
        
        # Prepare search parameters (modified for memory search)
        search_params = self.get_search_parameters()
        
        # Clear previous results
        self.clear_results()
        
        # Start memory search thread
        self.search_thread = MemorySearchThread(search_params, loaded_pdfs)
        self.search_thread.progress_update.connect(self.on_search_progress)
        self.search_thread.file_found.connect(self.on_file_found)
        self.search_thread.search_complete.connect(self.on_search_complete)
        
        self.search_thread.start()
        
        # Update UI
        self.is_searching = True
        self.search_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.status_label.setText(f"Starting memory search of {len(loaded_pdfs)} PDFs...")
        
        self.logger.info("SearchWidget", f"Started memory search of {len(loaded_pdfs)} PDFs")
    
    def stop_search(self):
        """Stop the current search"""
        if self.search_thread and self.is_searching:
            self.search_thread.cancel()
            self.search_thread.wait(3000)
            
        self.on_search_complete(len(self.search_results))
    
    def clear_results(self):
        """Clear search results"""
        self.search_results.clear()
        self.results_table.setRowCount(0)
        self.results_label.setText("Search Results (0 files)")
        self.export_button.setEnabled(False)
        self.update_action_buttons()
    
    def get_search_parameters(self) -> dict:
        """Get search parameters from UI"""
        # File extensions
        extensions = []
        if self.pdf_cb.isChecked():
            extensions.append('.pdf')
        if self.doc_cb.isChecked():
            extensions.extend(['.doc', '.docx'])
        if self.txt_cb.isChecked():
            extensions.append('.txt')
        if self.image_cb.isChecked():
            extensions.extend(['.jpg', '.jpeg', '.png', '.gif', '.bmp'])
        if self.all_files_cb.isChecked():
            extensions = []  # Empty list means all files
        
        # Custom extensions
        custom_ext = self.custom_extensions_edit.text().strip()
        if custom_ext:
            custom_list = [ext.strip() for ext in custom_ext.split(',')]
            extensions.extend(custom_list)
        
        return {
            'search_path': self.path_edit.text(),
            'filename_pattern': self.filename_pattern_edit.text().strip() if self.use_filename_filter_cb.isChecked() else '',
            'filename_contains': self.filename_contains_cb.isChecked() if self.use_filename_filter_cb.isChecked() else True,
            'file_extensions': extensions,
            'content_search': self.content_search_edit.text().strip() if self.use_content_filter_cb.isChecked() else '',
            'content_contains': self.content_contains_cb.isChecked() if self.use_content_filter_cb.isChecked() else True,
            'content_regex': self.content_regex_cb.isChecked() if self.use_content_filter_cb.isChecked() else False,
            'content_case_sensitive': self.content_case_sensitive_cb.isChecked() if self.use_content_filter_cb.isChecked() else False,
            'case_sensitive': self.case_sensitive_cb.isChecked() if self.use_filename_filter_cb.isChecked() else False,
            'use_regex': self.use_regex_cb.isChecked() if self.use_filename_filter_cb.isChecked() else False,
            'min_size': int(self.min_size_spin.value() * 1024 * 1024) if self.use_size_filter_cb.isChecked() and self.min_size_spin.value() > 0 else 0,
            'max_size': int(self.max_size_spin.value() * 1024 * 1024) if self.use_size_filter_cb.isChecked() and self.max_size_spin.value() > 0 else 0,
            'date_from': self.date_from_edit.date().toPython() if self.use_date_filter_cb.isChecked() else None,
            'date_to': self.date_to_edit.date().toPython() if self.use_date_filter_cb.isChecked() else None,
            'include_subdirs': self.include_subdirs_cb.isChecked()
        }
    
    def on_search_progress(self, current: int, total: int, status: str):
        """Handle search progress updates"""
        if total > 0:
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(current)
        self.status_label.setText(f"{status} ({current}/{total})")
    
    def on_file_found(self, file_info: dict):
        """Handle when a file is found"""
        self.search_results.append(file_info)
        
        # Add to table
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)
        
        # Basic file information
        name_item = QTableWidgetItem(file_info['name'])
        
        # Add tooltip with content matches if available (for memory searches)
        if 'content_matches' in file_info and file_info['content_matches']:
            matches = file_info['content_matches']
            match_count = len(matches)
            
            # Create tooltip showing first few matches
            tooltip_lines = [f"Found {match_count} content match(es):"]
            for i, match in enumerate(matches[:3]):  # Show first 3 matches
                context = match['context'][:100] + "..." if len(match['context']) > 100 else match['context']
                tooltip_lines.append(f"Page {match['page']}: {context}")
            
            if len(matches) > 3:
                tooltip_lines.append(f"... and {len(matches) - 3} more matches")
            
            name_item.setToolTip("\n".join(tooltip_lines))
            
            # Add match count to name for memory searches
            if file_info.get('source') == 'memory':
                name_item.setText(f"{file_info['name']} ({match_count} matches)")
        
        self.results_table.setItem(row, 0, name_item)
        self.results_table.setItem(row, 1, QTableWidgetItem(file_info['path']))
        self.results_table.setItem(row, 2, QTableWidgetItem(file_info['size_formatted']))
        self.results_table.setItem(row, 3, QTableWidgetItem(file_info['modified_formatted']))
        self.results_table.setItem(row, 4, QTableWidgetItem(file_info['extension']))
        self.results_table.setItem(row, 5, QTableWidgetItem(file_info['directory']))
        
        # Update results count
        count = len(self.search_results)
        total_matches = sum(len(r.get('content_matches', [])) for r in self.search_results)
        
        if self.search_memory_cb.isChecked() and total_matches > 0:
            self.results_label.setText(f"Search Results ({count} files, {total_matches} content matches)")
        else:
            self.results_label.setText(f"Search Results ({count} files)")
    
    def on_search_complete(self, total_found: int):
        """Handle search completion"""
        self.is_searching = False
        self.search_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        
        # Use the actual results count instead of the parameter (which might be incorrect)
        actual_count = len(self.search_results)
        self.export_button.setEnabled(actual_count > 0)
        
        # Get the file types that were actually searched
        search_params = self.get_search_parameters()
        extensions = search_params['file_extensions']
        
        # Create a summary of what was searched
        if not extensions:  # All files
            file_type_summary = "all file types"
        else:
            # Count files by type
            type_counts = {}
            for result in self.search_results:
                ext = result['extension'].lower()
                type_counts[ext] = type_counts.get(ext, 0) + 1
            
            # Create summary string
            if type_counts:
                type_parts = [f"{count} {ext}" for ext, count in sorted(type_counts.items())]
                file_type_summary = ", ".join(type_parts)
            else:
                # Fallback to what was searched for
                file_type_summary = ", ".join(extensions)
        
        self.status_label.setText(
            f"Search complete: {actual_count} files found ({file_type_summary})"
        )
        
        self.logger.info("SearchWidget", f"Search completed: {actual_count} files found")
    
    def on_selection_changed(self):
        """Handle selection change in results table"""
        self.update_action_buttons()
    
    def update_action_buttons(self):
        """Update action button states based on selection"""
        has_selection = len(self.results_table.selectedItems()) > 0
        self.open_file_button.setEnabled(has_selection)
        self.open_folder_button.setEnabled(has_selection)
        
        # Check if any selected files are PDFs
        has_pdfs = False
        if has_selection:
            selected_rows = set(item.row() for item in self.results_table.selectedItems())
            has_pdfs = any(self.search_results[row]['is_pdf'] for row in selected_rows 
                          if row < len(self.search_results))
        
        self.add_to_list_button.setEnabled(has_pdfs and self.file_list_controller is not None)
    
    def show_context_menu(self, position):
        """Show context menu for results table"""
        if not self.results_table.itemAt(position):
            return
        
        menu = QMenu(self)
        
        open_action = menu.addAction("Open File")
        open_action.triggered.connect(self.open_selected_file)
        
        folder_action = menu.addAction("Open Containing Folder")
        folder_action.triggered.connect(self.open_selected_folder)
        
        menu.addSeparator()
        
        copy_path_action = menu.addAction("Copy File Path")
        copy_path_action.triggered.connect(self.copy_selected_path)
        
        if self.file_list_controller:
            menu.addSeparator()
            add_pdf_action = menu.addAction("Add PDFs to List")
            add_pdf_action.triggered.connect(self.add_pdfs_to_list)
        
        menu.exec(self.results_table.mapToGlobal(position))
    
    def open_selected_file(self):
        """Open the selected file"""
        selected_rows = set(item.row() for item in self.results_table.selectedItems())
        if selected_rows and self.search_results:
            row = min(selected_rows)
            if row < len(self.search_results):
                filepath = self.search_results[row]['path']
                os.startfile(filepath) if os.name == 'nt' else os.system(f'open "{filepath}"')
    
    def open_selected_folder(self):
        """Open the folder containing the selected file"""
        selected_rows = set(item.row() for item in self.results_table.selectedItems())
        if selected_rows and self.search_results:
            row = min(selected_rows)
            if row < len(self.search_results):
                directory = self.search_results[row]['directory']
                os.startfile(directory) if os.name == 'nt' else os.system(f'open "{directory}"')
    
    def copy_selected_path(self):
        """Copy selected file path to clipboard"""
        selected_rows = set(item.row() for item in self.results_table.selectedItems())
        if selected_rows and self.search_results:
            paths = []
            for row in selected_rows:
                if row < len(self.search_results):
                    paths.append(self.search_results[row]['path'])
            
            if paths:
                from PyQt6.QtWidgets import QApplication
                clipboard = QApplication.clipboard()
                clipboard.setText('\n'.join(paths))
    
    def add_pdfs_to_list(self):
        """Add selected PDF files to the main file list"""
        if not self.file_list_controller:
            QMessageBox.information(self, "Info", "No file list controller available.")
            return
        
        selected_rows = set(item.row() for item in self.results_table.selectedItems())
        if not selected_rows:
            QMessageBox.information(self, "Info", "Please select files to add.")
            return
        
        pdf_files = []
        for row in selected_rows:
            if row < len(self.search_results):
                file_info = self.search_results[row]
                if file_info['is_pdf']:
                    pdf_files.append(file_info['path'])
        
        if pdf_files:
            self.file_list_controller.add_files(pdf_files)
            QMessageBox.information(
                self, "Success", 
                f"Added {len(pdf_files)} PDF file(s) to the main list."
            )
            self.logger.info("SearchWidget", f"Added {len(pdf_files)} PDFs to main list")
        else:
            QMessageBox.information(self, "Info", "No PDF files selected.")
    
    def export_results(self):
        """Export search results to CSV"""
        if not self.search_results:
            QMessageBox.information(self, "Info", "No results to export.")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Search Results", 
            f"search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv)"
        )
        
        if filename:
            try:
                import csv
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # Write header
                    writer.writerow(['Name', 'Full Path', 'Directory', 'Size (bytes)', 
                                   'Size (formatted)', 'Modified', 'Extension'])
                    
                    # Write data
                    for file_info in self.search_results:
                        writer.writerow([
                            file_info['name'],
                            file_info['path'],
                            file_info['directory'],
                            file_info['size'],
                            file_info['size_formatted'],
                            file_info['modified_formatted'],
                            file_info['extension']
                        ])
                
                QMessageBox.information(self, "Success", f"Results exported to: {filename}")
                self.logger.info("SearchWidget", f"Exported {len(self.search_results)} results to {filename}")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export results: {str(e)}")
                self.logger.error("SearchWidget", f"Export failed: {str(e)}")
