#!/usr/bin/env python3
# file_list_controller.py - Shared file list controller

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QListWidget

class FileListController(QObject):
    """
    Controller for sharing file lists between different widgets
    """
    # Signal emitted when files are added/removed
    files_updated = pyqtSignal(list)
    items_appended   = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pdf_files = []
        self._list_widget = QListWidget()
        
        # Connect signals
        self.files_updated.connect(self._update_list_widget)
        self.items_appended.connect(self._append_list_items)

    def get_files(self):
        """Get the current list of PDF files"""
        return self._pdf_files.copy()
    
    def set_files(self, files):
        """Set the list of PDF files"""
        if files != self._pdf_files:
            self._pdf_files = files.copy()
            self.files_updated.emit(self._pdf_files)
    
    def add_files(self, files):
        """Add files to the list (avoiding duplicates)"""
        new = []
        for f in files:
            if f not in self._pdf_files:
                self._pdf_files.append(f)
                new.append(f)

        if new:
            # Fast incremental append
            self.items_appended.emit(new)
            
    def _append_list_items(self, items):
        """Append only new items, without clearing everything"""
        self._list_widget.addItems(items)
    
    def add_file(self, file):
        """Add a single file to the list (avoiding duplicates)"""
        if file not in self._pdf_files:
            self._pdf_files.append(file)
            self.files_updated.emit(self._pdf_files)
            return True
        return False
    
    def remove_files(self, files):
        """Remove files from the list"""
        removed = False
        for file in files:
            if file in self._pdf_files:
                self._pdf_files.remove(file)
                removed = True
        
        if removed:
            self.files_updated.emit(self._pdf_files)
    
    def clear_files(self):
        """Clear all files from the list"""
        if self._pdf_files:
            self._pdf_files.clear()
            self.files_updated.emit(self._pdf_files)
            
    def get_list_widget(self):
        """Get the shared list widget"""
        return self._list_widget
        
    def _update_list_widget(self, files):
        """Update the list widget with the current files"""
        self._list_widget.clear()
        self._list_widget.addItems(files)

    def disable_updates(self):
        self._list_widget.setUpdatesEnabled(False)
    def enable_updates(self):
        """Re-enable the file list controller"""
        self._list_widget.setUpdatesEnabled(True)

    def disable_signals(self):
        """Disable signals to prevent unnecessary updates"""
        self.files_updated.disconnect(self._update_list_widget)

    def enable_signals(self):
        """Re-enable signals for updates"""
        self.files_updated.connect(self._update_list_widget)
        self._update_list_widget(self._pdf_files)


    