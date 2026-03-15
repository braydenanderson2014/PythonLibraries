#!/usr/bin/env python3
"""
PDF Viewer Widget
Allows users to select and view PDF files with native rendering
"""

import os
import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QFileDialog, QScrollArea, QMessageBox, QFrame, QSplitter,
    QListWidget, QListWidgetItem, QSpinBox, QComboBox, QProgressBar,
    QLineEdit, QCompleter
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QStringListModel
from PyQt6.QtGui import QPixmap, QPainter, QFont
from pathlib import Path

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

class PDFRenderWorker(QThread):
    """Worker thread for PDF rendering to avoid blocking UI"""
    page_rendered = pyqtSignal(int, QPixmap)
    render_complete = pyqtSignal()
    error_occurred = pyqtSignal(str)
    progress_updated = pyqtSignal(int, int)  # current, total
    
    def __init__(self, pdf_path, page_numbers, zoom_factor=1.0):
        super().__init__()
        self.pdf_path = pdf_path
        self.page_numbers = page_numbers
        self.zoom_factor = zoom_factor
        self._stop_rendering = False
    
    def stop_rendering(self):
        """Stop the rendering process"""
        self._stop_rendering = True
    
    def run(self):
        """Render PDF pages in background thread"""
        try:
            if not PYMUPDF_AVAILABLE:
                self.error_occurred.emit("PyMuPDF not available. Install with: pip install PyMuPDF")
                return
                
            doc = fitz.open(self.pdf_path)
            
            for i, page_num in enumerate(self.page_numbers):
                if self._stop_rendering:
                    break
                    
                if page_num >= len(doc):
                    continue
                    
                page = doc.load_page(page_num)
                
                # Create transformation matrix for zoom
                mat = fitz.Matrix(self.zoom_factor, self.zoom_factor)
                pix = page.get_pixmap(matrix=mat)
                
                # Convert to QPixmap
                img_data = pix.tobytes("ppm")
                qimg = QPixmap()
                qimg.loadFromData(img_data)
                
                self.page_rendered.emit(page_num, qimg)
                self.progress_updated.emit(i + 1, len(self.page_numbers))
            
            doc.close()
            self.render_complete.emit()
            
        except Exception as e:
            self.error_occurred.emit(f"Error rendering PDF: {str(e)}")

class PDFViewerWidget(QWidget):
    """PDF Viewer Widget for the main application"""
    
    def __init__(self, parent=None, file_list_controller=None):
        super().__init__(parent)
        self.current_pdf_path = None
        self.current_doc = None
        self.total_pages = 0
        self.current_page = 0
        self.zoom_factor = 1.0
        self.render_worker = None
        self.page_pixmaps = {}  # Cache for rendered pages
        self.file_list_controller = file_list_controller  # For importing PDFs from other tabs
        self.pdf_history = []  # Store previously loaded PDFs
        
        self.setup_ui()
        self.check_pymupdf_availability()
        
        # Load PDF history from settings if available
        self.load_pdf_history()
        
    def setup_ui(self):
        """Setup the PDF viewer UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Title
        title_label = QLabel("PDF Viewer")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # File selection area
        file_group = QFrame()
        file_group.setFrameStyle(QFrame.Shape.Box)
        file_group.setStyleSheet("""
            QFrame {
                border: 2px solid palette(mid);
                border-radius: 5px;
                padding: 10px;
                background-color: palette(base);
            }
        """)
        file_layout = QVBoxLayout(file_group)
        
        # First row: File selection and import
        first_row = QHBoxLayout()
        
        self.file_label = QLabel("No PDF file selected")
        self.file_label.setStyleSheet("color: gray; font-style: italic;")
        first_row.addWidget(self.file_label)
        
        first_row.addStretch()
        
        self.select_file_btn = QPushButton("Select PDF File")
        self.select_file_btn.clicked.connect(self.select_pdf_file)
        first_row.addWidget(self.select_file_btn)
        
        self.import_pdfs_btn = QPushButton("Import PDFs from Other Tabs")
        self.import_pdfs_btn.clicked.connect(self.import_pdfs_from_tabs)
        self.import_pdfs_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; font-weight: bold; }")
        self.import_pdfs_btn.setToolTip("Import PDF files from other tabs (Splitter, Merger, etc.)")
        first_row.addWidget(self.import_pdfs_btn)
        
        self.close_file_btn = QPushButton("Close File")
        self.close_file_btn.clicked.connect(self.close_pdf_file)
        self.close_file_btn.setEnabled(False)
        first_row.addWidget(self.close_file_btn)
        
        file_layout.addLayout(first_row)
        
        # Second row: PDF history dropdown with search
        second_row = QHBoxLayout()
        second_row.addWidget(QLabel("Previously loaded PDFs:"))
        
        self.pdf_history_combo = QComboBox()
        self.pdf_history_combo.setEditable(True)
        self.pdf_history_combo.setMinimumWidth(400)
        self.pdf_history_combo.setPlaceholderText("Type to search or select a previously loaded PDF...")
        # Use activated signal instead of currentTextChanged to prevent auto-loading
        self.pdf_history_combo.activated.connect(self.on_history_item_activated)
        
        # Make it searchable
        self.pdf_history_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        
        second_row.addWidget(self.pdf_history_combo)
        second_row.addStretch()
        
        file_layout.addLayout(second_row)
        
        layout.addWidget(file_group)
        
        # Control panel
        controls_group = QFrame()
        controls_group.setFrameStyle(QFrame.Shape.Box)
        controls_group.setStyleSheet("""
            QFrame {
                border: 1px solid palette(mid);
                border-radius: 3px;
                padding: 5px;
                background-color: palette(window);
            }
        """)
        controls_layout = QHBoxLayout(controls_group)
        
        # Page navigation
        controls_layout.addWidget(QLabel("Page:"))
        
        self.prev_page_btn = QPushButton("◀ Previous")
        self.prev_page_btn.clicked.connect(self.previous_page)
        self.prev_page_btn.setEnabled(False)
        controls_layout.addWidget(self.prev_page_btn)
        
        self.page_spin = QSpinBox()
        self.page_spin.setMinimum(1)
        self.page_spin.setMaximum(1)
        self.page_spin.valueChanged.connect(self.go_to_page)
        self.page_spin.setEnabled(False)
        controls_layout.addWidget(self.page_spin)
        
        self.page_total_label = QLabel("of 0")
        controls_layout.addWidget(self.page_total_label)
        
        self.next_page_btn = QPushButton("Next ▶")
        self.next_page_btn.clicked.connect(self.next_page)
        self.next_page_btn.setEnabled(False)
        controls_layout.addWidget(self.next_page_btn)
        
        controls_layout.addStretch()
        
        # Zoom controls
        controls_layout.addWidget(QLabel("Zoom:"))
        
        self.zoom_combo = QComboBox()
        self.zoom_combo.addItems(["50%", "75%", "100%", "125%", "150%", "200%", "300%", "Fit Width"])
        self.zoom_combo.setCurrentText("100%")
        self.zoom_combo.currentTextChanged.connect(self.on_zoom_changed)
        self.zoom_combo.setEnabled(False)
        controls_layout.addWidget(self.zoom_combo)
        
        layout.addWidget(controls_group)
        
        # Progress bar (initially hidden)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Main content area with scrollable PDF view
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid palette(mid);
                background-color: palette(dark);
            }
        """)
        
        # PDF display widget
        self.pdf_display = QLabel()
        self.pdf_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pdf_display.setStyleSheet("""
            QLabel {
                background-color: white;
                border: 1px solid palette(mid);
                margin: 10px;
            }
        """)
        self.pdf_display.setText("Select a PDF file to view")
        self.pdf_display.setMinimumSize(400, 500)
        
        self.scroll_area.setWidget(self.pdf_display)
        layout.addWidget(self.scroll_area, 1)  # Give it most of the space
        
    def check_pymupdf_availability(self):
        """Check if PyMuPDF is available"""
        if not PYMUPDF_AVAILABLE:
            self.pdf_display.setText(
                "PyMuPDF not available.\n\n"
                "To enable PDF viewing, install PyMuPDF:\n"
                "pip install PyMuPDF\n\n"
                "Then restart the application."
            )
            self.pdf_display.setStyleSheet("""
                QLabel {
                    background-color: #ffe6e6;
                    color: #d00;
                    padding: 20px;
                    border: 2px solid #d00;
                    border-radius: 5px;
                    font-size: 12px;
                }
            """)
            self.select_file_btn.setEnabled(False)
    
    def select_pdf_file(self):
        """Open file dialog to select PDF file"""
        if not PYMUPDF_AVAILABLE:
            QMessageBox.warning(
                self, 
                "PyMuPDF Required", 
                "PyMuPDF is required for PDF viewing.\n\nInstall with: pip install PyMuPDF"
            )
            return
            
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select PDF File",
            "",
            "PDF Files (*.pdf);;All Files (*)"
        )
        
        if file_path and os.path.exists(file_path):
            self.load_pdf_file(file_path)
    
    def load_pdf_file(self, file_path):
        """Load and display PDF file"""
        try:
            # Debug: Track when this method is called
            import traceback
            print(f"🔍 DEBUG: load_pdf_file called with: {file_path}")
            print("🔍 DEBUG: Call stack:")
            for line in traceback.format_stack()[-3:-1]:  # Show last 2 stack frames
                print(f"  {line.strip()}")
            
            # Close any existing PDF first
            self.close_pdf_file()
            
            # Open new PDF
            self.current_doc = fitz.open(file_path)
            self.current_pdf_path = file_path
            self.total_pages = len(self.current_doc)
            self.current_page = 0
            
            # Add to history
            self.add_to_history(file_path)
            
            # Update UI
            self.file_label.setText(f"File: {os.path.basename(file_path)} ({self.total_pages} pages)")
            self.file_label.setStyleSheet("color: black; font-weight: bold;")
            
            # Enable controls
            self.close_file_btn.setEnabled(True)
            self.page_spin.setEnabled(True)
            self.page_spin.setMaximum(self.total_pages)
            self.page_spin.setValue(1)
            self.page_total_label.setText(f"of {self.total_pages}")
            self.zoom_combo.setEnabled(True)
            
            # Render first page
            self.render_current_page()
            self.update_navigation_buttons()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Loading PDF",
                f"Failed to load PDF file:\n{str(e)}"
            )
    
    def close_pdf_file(self):
        """Close current PDF file"""
        # Stop any ongoing rendering
        if self.render_worker and self.render_worker.isRunning():
            self.render_worker.stop_rendering()
            self.render_worker.wait()
        
        # Close document
        if self.current_doc:
            self.current_doc.close()
            self.current_doc = None
        
        # Reset state
        self.current_pdf_path = None
        self.total_pages = 0
        self.current_page = 0
        self.page_pixmaps.clear()
        
        # Update UI
        self.file_label.setText("No PDF file selected")
        self.file_label.setStyleSheet("color: gray; font-style: italic;")
        
        self.pdf_display.setText("Select a PDF file to view")
        self.pdf_display.setStyleSheet("""
            QLabel {
                background-color: white;
                border: 1px solid palette(mid);
                margin: 10px;
            }
        """)
        
        # Disable controls
        self.close_file_btn.setEnabled(False)
        self.page_spin.setEnabled(False)
        self.page_spin.setValue(1)
        self.page_spin.setMaximum(1)
        self.page_total_label.setText("of 0")
        self.zoom_combo.setEnabled(False)
        self.prev_page_btn.setEnabled(False)
        self.next_page_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
    
    def render_current_page(self):
        """Render the current page"""
        if not self.current_doc or self.current_page >= self.total_pages:
            return
            
        # Check cache first
        cache_key = (self.current_page, self.zoom_factor)
        if cache_key in self.page_pixmaps:
            self.pdf_display.setPixmap(self.page_pixmaps[cache_key])
            return
        
        # Show progress bar
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)
        
        # Start background rendering
        self.render_worker = PDFRenderWorker(
            self.current_pdf_path, 
            [self.current_page], 
            self.zoom_factor
        )
        self.render_worker.page_rendered.connect(self.on_page_rendered)
        self.render_worker.render_complete.connect(self.on_render_complete)
        self.render_worker.error_occurred.connect(self.on_render_error)
        self.render_worker.progress_updated.connect(self.on_progress_updated)
        self.render_worker.start()
    
    def on_page_rendered(self, page_num, pixmap):
        """Handle rendered page"""
        # Cache the rendered page
        cache_key = (page_num, self.zoom_factor)
        self.page_pixmaps[cache_key] = pixmap
        
        # Display if it's the current page
        if page_num == self.current_page:
            self.pdf_display.setPixmap(pixmap)
            self.pdf_display.adjustSize()
    
    def on_render_complete(self):
        """Handle render completion"""
        self.progress_bar.setVisible(False)
    
    def on_render_error(self, error_message):
        """Handle render error"""
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Render Error", error_message)
    
    def on_progress_updated(self, current, total):
        """Handle progress update"""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
    
    def previous_page(self):
        """Go to previous page"""
        if self.current_page > 0:
            self.current_page -= 1
            self.page_spin.setValue(self.current_page + 1)
            self.render_current_page()
            self.update_navigation_buttons()
    
    def next_page(self):
        """Go to next page"""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.page_spin.setValue(self.current_page + 1)
            self.render_current_page()
            self.update_navigation_buttons()
    
    def go_to_page(self, page_number):
        """Go to specific page"""
        new_page = page_number - 1  # Convert to 0-based index
        if 0 <= new_page < self.total_pages:
            self.current_page = new_page
            self.render_current_page()
            self.update_navigation_buttons()
    
    def update_navigation_buttons(self):
        """Update navigation button states"""
        self.prev_page_btn.setEnabled(self.current_page > 0)
        self.next_page_btn.setEnabled(self.current_page < self.total_pages - 1)
    
    def on_zoom_changed(self, zoom_text):
        """Handle zoom level change"""
        if zoom_text == "Fit Width":
            # Calculate zoom to fit width (simplified)
            self.zoom_factor = 1.0  # For now, just use 100%
        else:
            # Parse percentage
            try:
                zoom_percent = int(zoom_text.replace('%', ''))
                self.zoom_factor = zoom_percent / 100.0
            except ValueError:
                self.zoom_factor = 1.0
        
        # Clear cache for this zoom level and re-render
        self.page_pixmaps.clear()
        if self.current_doc:
            self.render_current_page()
    
    def load_pdf_history(self):
        """Load PDF history from settings or create empty list"""
        # TODO: Load from settings when available
        self.pdf_history = []
        self.update_history_combo()
    
    def save_pdf_history(self):
        """Save PDF history to settings"""
        # TODO: Save to settings when available
        pass
    
    def add_to_history(self, file_path):
        """Add a PDF file to the history"""
        if file_path and os.path.exists(file_path):
            # Remove if already exists to avoid duplicates
            if file_path in self.pdf_history:
                self.pdf_history.remove(file_path)
            
            # Add to the beginning of the list
            self.pdf_history.insert(0, file_path)
            
            # Keep only the last 20 files
            self.pdf_history = self.pdf_history[:20]
            
            # Update the combo box
            self.update_history_combo()
            self.save_pdf_history()
    
    def update_history_combo(self):
        """Update the history combo box with current history"""
        # Block signals to prevent automatic loading during update
        self.pdf_history_combo.blockSignals(True)
        
        self.pdf_history_combo.clear()
        
        if not self.pdf_history:
            self.pdf_history_combo.addItem("No PDFs in history")
            self.pdf_history_combo.setEnabled(False)
            self.pdf_history_combo.blockSignals(False)
            return
        
        self.pdf_history_combo.setEnabled(True)
        
        # Add history items with just the filename for display
        for file_path in self.pdf_history:
            if os.path.exists(file_path):
                display_name = os.path.basename(file_path)
                self.pdf_history_combo.addItem(display_name, file_path)  # Store full path as data
            else:
                # File no longer exists, show in gray
                display_name = f"{os.path.basename(file_path)} (missing)"
                self.pdf_history_combo.addItem(display_name, file_path)
        
        # Don't auto-select any item - let user choose
        self.pdf_history_combo.setCurrentIndex(-1)
        self.pdf_history_combo.setCurrentText("")  # Clear the display text
        
        # Set up completer for searchability
        file_names = [os.path.basename(path) for path in self.pdf_history if os.path.exists(path)]
        completer = QCompleter(file_names)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.pdf_history_combo.setCompleter(completer)
        
        # Re-enable signals
        self.pdf_history_combo.blockSignals(False)
    
    def on_history_item_activated(self, index):
        """Handle user selection from history dropdown (only fires on user interaction)"""
        if index < 0:
            return
            
        file_path = self.pdf_history_combo.itemData(index)
        if file_path and os.path.exists(file_path) and file_path != self.current_pdf_path:
            self.load_pdf_file(file_path)
        elif file_path and not os.path.exists(file_path):
            QMessageBox.warning(
                self, 
                "File Not Found", 
                f"The selected PDF file no longer exists:\n{file_path}"
            )
    
    def import_pdfs_from_tabs(self):
        """Import PDF files from other tabs using the file list controller"""
        if not self.file_list_controller:
            QMessageBox.information(
                self, 
                "No Controller", 
                "File list controller not available. Cannot import from other tabs."
            )
            return
        
        # Get files from the shared controller
        shared_files = self.file_list_controller.get_files()
        pdf_files = [f for f in shared_files if f.lower().endswith('.pdf') and os.path.exists(f)]
        
        if not pdf_files:
            QMessageBox.information(
                self, 
                "No PDFs Found", 
                "No PDF files found in other tabs. Use the 'Copy PDFs to Other Widgets' button in other tabs first."
            )
            return
        
        # Add all found PDFs to history
        added_count = 0
        for pdf_file in pdf_files:
            if pdf_file not in self.pdf_history:
                self.add_to_history(pdf_file)
                added_count += 1
        
        if added_count > 0:
            QMessageBox.information(
                self,
                "PDFs Imported",
                f"Imported {added_count} PDF file(s) to the history.\nSelect from the dropdown to view a PDF."
            )
        else:
            QMessageBox.information(
                self,
                "Already in History", 
                "All PDF files from other tabs are already in the history."
            )

if __name__ == "__main__":
    # Test the widget standalone
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    viewer = PDFViewerWidget()
    viewer.show()
    sys.exit(app.exec())
