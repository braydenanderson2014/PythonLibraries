#!/usr/bin/env python3
# PDFListWidget.py - Custom QListWidget with drag-and-drop support for PDF files

from PyQt6.QtWidgets import QListWidget, QAbstractItemView
from PyQt6.QtCore import Qt, QMimeData, QUrl
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QDrag
import os

class PDFListWidget(QListWidget):
    """A custom QListWidget that supports drag-and-drop for PDF files"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.parent = parent
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter events - accept only PDF files"""
        if event.mimeData().hasUrls():
            has_pdf = False
            for url in event.mimeData().urls():
                if url.isLocalFile() and url.toLocalFile().lower().endswith('.pdf'):
                    has_pdf = True
                    break
                    
            if has_pdf:
                event.acceptProposedAction()
                return
        super().dragEnterEvent(event)
    
    def dragMoveEvent(self, event):
        """Handle drag move events - accept only PDF files"""
        if event.mimeData().hasUrls():
            has_pdf = False
            for url in event.mimeData().urls():
                if url.isLocalFile() and url.toLocalFile().lower().endswith('.pdf'):
                    has_pdf = True
                    break
                    
            if has_pdf:
                event.acceptProposedAction()
                return
        super().dragMoveEvent(event)
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop events - add PDF files to the list"""
        if event.mimeData().hasUrls():
            pdf_files = []
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    if file_path.lower().endswith('.pdf'):
                        pdf_files.append(file_path)
            
            if pdf_files and self.parent and hasattr(self.parent, 'process_dropped_files'):
                # Use the parent's method to add files to ensure proper handling
                self.parent.process_dropped_files(pdf_files)
                event.acceptProposedAction()
                return
            elif pdf_files:
                # Fallback if parent doesn't have the proper method
                for pdf_file in pdf_files:
                    self.addItem(pdf_file)
                event.acceptProposedAction()
                return
                
        super().dropEvent(event)
    
    def startDrag(self, supportedActions):
        """Start drag operation for selected items"""
        selected_items = self.selectedItems()
        if not selected_items:
            return
            
        mime_data = QMimeData()
        urls = []
        
        for item in selected_items:
            file_path = item.text()
            if os.path.exists(file_path):
                urls.append(QUrl.fromLocalFile(file_path))
        
        if urls:
            mime_data.setUrls(urls)
            drag = QDrag(self)
            drag.setMimeData(mime_data)
            drag.exec(supportedActions)
