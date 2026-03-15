#!/usr/bin/env python3
# main_application.py - Main PDF Utility Application

import os
import sys
import glob
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QVBoxLayout, QWidget,
    QMessageBox, QMenuBar, QMenu, QToolBar, QStatusBar, QDialog,
    QDialogButtonBox, QVBoxLayout, QLabel, QTextEdit, QPushButton,
    QFileDialog, QHBoxLayout, QGroupBox, QFrame
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QAction, QIcon, QPixmap

from pdf_splitter_widget import PDFSplitterWidget
from pdf_merger_widget import PDFMergerWidget
from image_converter_widget import ImageConverterWidget
from white_space_widget import WhiteSpaceWidget
from tts_widget import TTSWidget
from search_widget import SearchWidget
from pdf_viewer_widget import PDFViewerWidget
from ocr_widget import OCRWidget
from settings_controller import SettingsController
from file_list_controller import FileListController
from directory_monitor import DirectoryMonitor
from PDFLogger import Logger
from help_system_qt import get_help_system
from tutorial_system import get_tutorial_manager, auto_start_main_tutorial
from update_system import get_update_manager
from issue_reporter import get_issue_reporter

class AboutDialog(QDialog):
    """About dialog for the application"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About PDF Utility")
        self.setMinimumSize(500, 650)
        
        main_layout = QVBoxLayout(self)
        
        # Create tab widget for different sections
        tab_widget = QTabWidget()
        
        # Application Tab
        app_tab = self.create_application_tab()
        tab_widget.addTab(app_tab, "Application")
        
        # Company Tab
        company_tab = self.create_company_tab()
        tab_widget.addTab(company_tab, "Company")
        
        main_layout.addWidget(tab_widget)
        
        # OK button
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(self.accept)
        main_layout.addWidget(button_box)
    
    def create_application_tab(self):
        """Create the application information tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # App logo/icon (using existing icon if available)
        try:
            icon_label = QLabel()
            icon_path = os.path.join(os.path.dirname(__file__), "PDF_Utility.ico")
            if os.path.exists(icon_path):
                pixmap = QPixmap(icon_path)
                scaled_pixmap = pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, 
                                           Qt.TransformationMode.SmoothTransformation)
                icon_label.setPixmap(scaled_pixmap)
            else:
                icon_label.setText("📄")
                icon_label.setStyleSheet("font-size: 48px;")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(icon_label)
        except Exception:
            # Fallback to emoji if icon loading fails
            icon_label = QLabel("📄")
            icon_label.setStyleSheet("font-size: 48px;")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(icon_label)
        
        # App info
        app_info = QLabel("<h2>PDF Utility</h2>")
        app_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(app_info)
        
        # Version info
        version_info = QLabel("Version 1.0.0")
        version_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_info.setStyleSheet("color: #666; font-size: 12px; margin-bottom: 20px;")
        layout.addWidget(version_info)
        
        # Description
        description = QTextEdit()
        description.setReadOnly(True)
        description.setMaximumHeight(200)
        description.setHtml("""
        <div style="font-family: Segoe UI, Arial, sans-serif; font-size: 11pt; line-height: 1.4;">
        <p><b>PDF Utility</b> is a comprehensive tool for manipulating PDF files:</p>
        <ul style="margin: 10px 0;">
            <li>Split PDFs by page, range, or custom selection</li>
            <li>Merge multiple PDFs into a single document</li>
            <li>Optimize PDFs by removing unnecessary white space</li>
            <li>Convert images to PDF format</li>
            <li>Text-to-speech conversion from PDF content</li>
            <li>Advanced search and file management</li>
            <li>Batch process multiple files at once</li>
        </ul>
        <p style="margin-top: 15px; font-style: italic; color: #555;">
        Built with PyQt6 and PyPDF2 for reliable, efficient PDF processing.
        </p>
        </div>
        """)
        layout.addWidget(description)
        
        # Technical details
        tech_group = QGroupBox("Technical Information")
        tech_layout = QVBoxLayout(tech_group)
        
        tech_info = QLabel(f"""
        <div style="font-family: monospace; font-size: 10pt;">
        <b>Platform:</b> {sys.platform}<br>
        <b>Python:</b> {sys.version.split()[0]}<br>
        <b>PyQt6:</b> Available<br>
        <b>Working Directory:</b> {os.getcwd()}
        </div>
        """)
        tech_info.setWordWrap(True)
        tech_layout.addWidget(tech_info)
        layout.addWidget(tech_group)
        
        layout.addStretch()
        return tab
    
    def create_company_tab(self):
        """Create the company information tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Company logo
        try:
            logo_label = QLabel()
            logo_path = os.path.join(os.path.dirname(__file__), "assets", "images", "company_logo.png")
            if os.path.exists(logo_path):
                pixmap = QPixmap(logo_path)
                scaled_pixmap = pixmap.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, 
                                           Qt.TransformationMode.SmoothTransformation)
                logo_label.setPixmap(scaled_pixmap)
            else:
                logo_label.setText("🏢")
                logo_label.setStyleSheet("font-size: 56px;")
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(logo_label)
        except Exception:
            # Fallback to emoji if logo loading fails
            logo_label = QLabel("🏢")
            logo_label.setStyleSheet("font-size: 56px;")
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(logo_label)
        
        # Company name
        company_name = QLabel("<h2>PDF Solutions Inc.</h2>")
        company_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        company_name.setStyleSheet("color: #2c3e50; margin: 10px 0;")
        layout.addWidget(company_name)
        
        # Company tagline
        tagline = QLabel("<i>Innovative Document Processing Solutions</i>")
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tagline.setStyleSheet("color: #7f8c8d; font-size: 12px; margin-bottom: 20px;")
        layout.addWidget(tagline)
        
        # Company description
        company_desc = QTextEdit()
        company_desc.setReadOnly(True)
        company_desc.setMaximumHeight(180)
        company_desc.setHtml("""
        <div style="font-family: Segoe UI, Arial, sans-serif; font-size: 11pt; line-height: 1.5;">
        <p><b>PDF Solutions Inc.</b> specializes in developing professional document processing 
        tools that streamline workflow and enhance productivity for businesses and individuals.</p>
        
        <p>Our mission is to provide intuitive, powerful, and reliable software solutions 
        that make PDF manipulation accessible to everyone, from casual users to enterprise clients.</p>
        
        <p>Founded with a vision to simplify document management, we continue to innovate 
        and expand our offerings to meet the evolving needs of our users.</p>
        </div>
        """)
        layout.addWidget(company_desc)
        
        # Contact Information
        contact_group = QGroupBox("Contact Information")
        contact_layout = QVBoxLayout(contact_group)
        
        contact_info = QLabel("""
        <div style="font-size: 10pt; line-height: 1.6;">
        <b>🌐 Website:</b> www.pdfsolutions.com<br>
        <b>📧 Support:</b> support@pdfsolutions.com<br>
        <b>📧 Sales:</b> sales@pdfsolutions.com<br>
        <b>📞 Phone:</b> +1 (555) 123-4567<br>
        <b>📍 Address:</b> 123 Tech Street, Software City, SC 12345
        </div>
        """)
        contact_info.setWordWrap(True)
        contact_layout.addWidget(contact_info)
        layout.addWidget(contact_group)
        
        # Social Media / Links (Optional)
        social_group = QGroupBox("Follow Us")
        social_layout = QVBoxLayout(social_group)
        
        social_info = QLabel("""
        <div style="font-size: 10pt;">
        <b>LinkedIn:</b> linkedin.com/company/pdfsolutions<br>
        <b>Twitter:</b> @PDFSolutionsInc<br>
        <b>GitHub:</b> github.com/pdfsolutions
        </div>
        """)
        social_layout.addWidget(social_info)
        layout.addWidget(social_group)
        
        layout.addStretch()
        return tab

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.logger = Logger()
        self.settings = SettingsController()
        
        # Settings dialog instance tracking
        self._settings_dialog_instance = None
        
        # Initialize help system
        self.help_system = get_help_system(self)
        
        # Initialize tutorial manager with settings
        self.tutorial_manager = get_tutorial_manager(self, self.settings)
        
        # Initialize update manager
        self.update_manager = get_update_manager(self)
        
        # Set application icon
        self.set_application_icon()
        
        # Initialize directory monitor
        self.directory_monitor = DirectoryMonitor(self)
        
        self.initUI()
        
        # Start the directory monitor if enabled
        if self.settings.get_setting("auto_import", "enabled", False):
            self.start_directory_monitor()
            watch_dir = self.settings.get_setting("auto_import", "watch_directory", "")
            self.logger.info("MainApplication", f"Auto-import enabled. Monitoring directory: {watch_dir}")
        
        # Auto-start tutorials after UI is fully loaded
        QTimer.singleShot(1500, self.check_for_tutorials)
    
    def set_application_icon(self):
        """Set the application icon for both window and taskbar"""
        try:
            # Get the directory where the script/executable is located
            if getattr(sys, 'frozen', False):
                # Running as compiled executable (PyInstaller)
                if hasattr(sys, '_MEIPASS'):
                    # Temporary directory created by PyInstaller
                    script_dir = sys._MEIPASS
                else:
                    # Directory of the executable
                    script_dir = os.path.dirname(sys.executable)
                self.logger.info("MainApplication", f"Running as compiled executable. Base directory: {script_dir}")
            else:
                # Running as script
                script_dir = os.path.dirname(os.path.abspath(__file__))
                self.logger.info("MainApplication", f"Running as script. Base directory: {script_dir}")
            
            # Common icon file patterns and locations
            icon_patterns = [
                "*.ico", "*.icns", "*.png"
            ]
            
            search_directories = [
                script_dir,  # Main directory
                os.path.join(script_dir, "assets"),
                os.path.join(script_dir, "icons"), 
                os.path.join(script_dir, "resources"),
                os.path.join(script_dir, "images"),
                os.path.join(script_dir, "static")
            ]
            
            # Find icon files
            found_icons = []
            for directory in search_directories:
                if os.path.exists(directory):
                    for pattern in icon_patterns:
                        search_path = os.path.join(directory, pattern)
                        for file_path in glob.glob(search_path):
                            if os.path.isfile(file_path):
                                found_icons.append(file_path)
            
            if found_icons:
                # Use the first icon found (preferring .ico files)
                icon_file = None
                for icon in found_icons:
                    if icon.lower().endswith('.ico'):
                        icon_file = icon
                        break
                
                if not icon_file:
                    icon_file = found_icons[0]
                
                # Set the icon
                icon = QIcon(icon_file)
                self.setWindowIcon(icon)
                
                # Also set it for the QApplication (affects taskbar on some systems)
                QApplication.instance().setWindowIcon(icon)
                
                self.logger.info("MainApplication", f"✅ Application icon set: {icon_file}")
                
                # Platform-specific taskbar icon handling
                if os.name == 'nt':  # Windows
                    self.set_windows_taskbar_icon(icon_file)
                    
            else:
                self.logger.warning("MainApplication", "⚠️ No icon files found. Using default icon.")
                
        except Exception as e:
            self.logger.error("MainApplication", f"Failed to set application icon: {e}")
            # Continue without icon - not a critical error
    
    def set_windows_taskbar_icon(self, icon_path):
        """Set the taskbar icon on Windows"""
        try:
            import ctypes
            from ctypes import wintypes
            
            # Get window handle
            hwnd = int(self.winId())
            
            # Load icon
            try:
                # Load the icon from file
                hicon = ctypes.windll.user32.LoadImageW(
                    None,
                    icon_path,
                    1,  # IMAGE_ICON
                    0, 0,  # Use default size
                    0x00000010 | 0x00008000  # LR_LOADFROMFILE | LR_SHARED
                )
                
                if hicon:
                    # Set both small and large icons
                    ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 0, hicon)  # WM_SETICON, ICON_SMALL
                    ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 1, hicon)  # WM_SETICON, ICON_BIG
                    self.logger.info("MainApplication", "✅ Windows taskbar icon set successfully")
                else:
                    self.logger.warning("MainApplication", "⚠️ Failed to load icon for taskbar")
                    
            except Exception as e:
                self.logger.warning("MainApplication", f"⚠️ Failed to set taskbar icon: {e}")
                
        except ImportError:
            self.logger.warning("MainApplication", "⚠️ ctypes not available for taskbar icon")
        except Exception as e:
            self.logger.warning("MainApplication", f"⚠️ Taskbar icon setting failed: {e}")
            # Not critical, continue without taskbar icon
        
    def initUI(self):
        """Initialize the UI"""
        # Set window properties
        self.setWindowTitle("PDF Utility")
        self.setMinimumSize(800, 600)
        
        # Create central widget with tab layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        layout = QVBoxLayout(self.central_widget)
        
        # Create shared file list controller
        self.file_list_controller = FileListController(self)
        
        # Connect directory monitor to file list controller
        self.directory_monitor.new_pdfs_signal.connect(self.handle_new_pdfs)
        
        # Create tab widget
        self.tabs = QTabWidget()
        
        # Connect tab change signal for contextual tutorials
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        # Create and add PDF splitter widget
        self.splitter_widget = PDFSplitterWidget(
            file_list_controller=self.file_list_controller, 
            settings_controller=self.settings
        )
        self.tabs.addTab(self.splitter_widget, "Split PDF")
        
        # Create and add PDF merger widget
        self.merger_widget = PDFMergerWidget(
            file_list_controller=self.file_list_controller, 
            settings_controller=self.settings
        )
        self.tabs.addTab(self.merger_widget, "Merge PDFs")
        
        # Create and add Image Converter widget (with shared controller for PDFs only)
        self.image_converter_widget = ImageConverterWidget(file_list_controller=self.file_list_controller)
        self.tabs.addTab(self.image_converter_widget, "Image Converter")
        
        # Create and add White Space Remover widget
        self.white_space_widget = WhiteSpaceWidget(file_list_controller=self.file_list_controller)
        self.tabs.addTab(self.white_space_widget, "Remove White Space")
        
        # Create and add Text to Speech widget
        self.tts_widget = TTSWidget(file_list_controller=self.file_list_controller)
        self.tabs.addTab(self.tts_widget, "Text to Speech")
        
        # Create and add OCR widget
        self.ocr_widget = OCRWidget(file_list_controller=self.file_list_controller)
        self.tabs.addTab(self.ocr_widget, "OCR")

        # Create and add Search widget (standalone - not connected to file_list_controller)
        self.search_widget = SearchWidget(
            file_list_controller=self.file_list_controller,
            merger_widget=self.merger_widget,
            splitter_widget=self.splitter_widget
        )
        self.tabs.addTab(self.search_widget, "File Search")
        
        # Create status bar before PDF viewer (needed for status updates)
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # PDF Viewer tab
        self.pdf_viewer_widget = PDFViewerWidget(self, file_list_controller=self.file_list_controller, status_bar=self.status_bar)
        self.tabs.addTab(self.pdf_viewer_widget, "PDF Viewer")
        
        # PDF Editor tab removed for commercial version
        # self.editor_widget = self.create_placeholder_widget(
        #     "PDF Editor", 
        #     "Edit PDF files, add annotations, and more."
        # )
        # self.tabs.addTab(self.editor_widget, "PDF Editor")
        
        layout.addWidget(self.tabs)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Load settings
        self.load_settings()
        
    def create_menu_bar(self):
        """Create the menu bar"""
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("&File")
        
        # Settings action
        settings_action = QAction("&Settings...", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.setStatusTip("Open application settings")
        settings_action.triggered.connect(self.show_settings_dialog)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menu_bar.addMenu("&Tools")
        
        split_action = QAction("&Split PDF", self)
        split_action.setStatusTip("Split PDF files")
        split_action.triggered.connect(lambda: self.tabs.setCurrentIndex(0))
        tools_menu.addAction(split_action)
        
        merge_action = QAction("&Merge PDFs", self)
        merge_action.setStatusTip("Merge PDF files")
        merge_action.triggered.connect(lambda: self.tabs.setCurrentIndex(1))
        tools_menu.addAction(merge_action)
        
        whitespace_action = QAction("&Remove White Space", self)
        whitespace_action.setStatusTip("Remove blank pages from PDF files")
        whitespace_action.triggered.connect(lambda: self.tabs.setCurrentIndex(3))
        tools_menu.addAction(whitespace_action)
        
        tts_action = QAction("&Text to Speech", self)
        tts_action.setStatusTip("Convert PDF text to speech")
        tts_action.triggered.connect(lambda: self.tabs.setCurrentIndex(4))
        tools_menu.addAction(tts_action)
        
        # Add a separator
        tools_menu.addSeparator()
        
        # File operations submenu
        file_ops_menu = tools_menu.addMenu("File &Operations")
        
        copy_action = QAction("&Copy Files", self)
        copy_action.setStatusTip("Copy selected files to a new location")
        copy_action.triggered.connect(self.copy_selected_files)
        file_ops_menu.addAction(copy_action)
        
        duplicate_action = QAction("&Duplicate Files", self)
        duplicate_action.setStatusTip("Create a duplicate of selected files")
        duplicate_action.triggered.connect(self.duplicate_selected_files)
        file_ops_menu.addAction(duplicate_action)
        
        delete_action = QAction("&Delete Files", self)
        delete_action.setStatusTip("Delete selected files from disk")
        delete_action.triggered.connect(self.delete_selected_files)
        file_ops_menu.addAction(delete_action)
        
        # Add a separator
        tools_menu.addSeparator()
        
        # Directory monitoring actions
        monitor_menu = tools_menu.addMenu("Directory &Monitoring")
        
        start_monitor_action = QAction("&Start Monitoring", self)
        start_monitor_action.setStatusTip("Start monitoring directory for new PDFs")
        start_monitor_action.triggered.connect(self.start_directory_monitor)
        monitor_menu.addAction(start_monitor_action)
        
        stop_monitor_action = QAction("S&top Monitoring", self)
        stop_monitor_action.setStatusTip("Stop monitoring directory")
        stop_monitor_action.triggered.connect(self.stop_directory_monitor)
        monitor_menu.addAction(stop_monitor_action)
        
        # Add a separator
        tools_menu.addSeparator()
        
        # Settings action removed for commercial version
        # settings_action = QAction("&Settings", self)
        # settings_action.setStatusTip("Configure application settings")
        # settings_action.triggered.connect(self.show_settings_dialog)
        # tools_menu.addAction(settings_action)
        
        # Tutorial actions
        tools_menu.addSeparator()
        tutorial_menu = tools_menu.addMenu("&Tutorials")
        
        show_tutorial_action = QAction("Show Tutorial for Current Tab", self)
        show_tutorial_action.setStatusTip("Show tutorial for the currently active widget")
        show_tutorial_action.triggered.connect(self.show_current_widget_tutorial)
        tutorial_menu.addAction(show_tutorial_action)
        
        restart_welcome_action = QAction("Restart Welcome Tutorial", self)
        restart_welcome_action.setStatusTip("Restart the main application tutorial")
        restart_welcome_action.triggered.connect(lambda: self.tutorial_manager.start_tutorial("main_application", force=True) if hasattr(self, 'tutorial_manager') else None)
        tutorial_menu.addAction(restart_welcome_action)
        
        # Help menu - integrated with help system
        help_menu = self.help_system.create_help_menu(menu_bar)
        
        # Add issue reporting to help menu
        help_menu.addSeparator()
        issue_action = QAction("Report Issue / Request Feature...", self)
        issue_action.setStatusTip("Report bugs or request new features")
        issue_action.triggered.connect(self.show_issue_reporter)
        help_menu.addAction(issue_action)
        
        # Add update check to help menu
        update_action = QAction("Check for Updates...", self)
        update_action.setStatusTip("Check for application updates")
        update_action.triggered.connect(self.check_for_updates)
        help_menu.addAction(update_action)
    
    def check_for_tutorials(self):
        """Check if tutorials should be auto-started"""
        # Use the auto-start method that respects all tutorial settings
        if auto_start_main_tutorial(self, self.settings):
            self.logger.info("MainApplication", "Started welcome tutorial for new user")
    
    def on_tab_changed(self, index):
        """Handle tab change and show contextual tutorials if enabled"""
        if not hasattr(self, 'tutorial_manager') or not self.tutorial_manager:
            return
            
        # Map tab indices to tutorial names
        tab_tutorial_map = {
            0: "split_widget",       # Split PDF
            1: "merge_widget",       # Merge PDFs  
            2: "image_converter",    # Image Converter
            3: "white_space_widget", # Remove White Space
            4: "tts_widget",         # Text to Speech
            5: "search_widget",      # File Search
            # 6: PDF Editor (placeholder, no tutorial yet)
        }
        
        # Show tutorial for the current tab if it's the first time
        if index in tab_tutorial_map:
            tutorial_name = tab_tutorial_map[index]
            if self.tutorial_manager.show_widget_tutorial_if_first_time(tutorial_name):
                self.logger.info("MainApplication", f"Started tutorial for {tutorial_name}")
    
    def show_current_widget_tutorial(self):
        """Manually show tutorial for the currently active widget"""
        current_index = self.tabs.currentIndex()
        if hasattr(self, 'tutorial_manager') and self.tutorial_manager:
            tab_tutorial_map = {
                0: "split_widget",
                1: "merge_widget", 
                2: "image_converter",
                3: "white_space_widget",
                4: "tts_widget",
                5: "search_widget",
            }
            
            if current_index in tab_tutorial_map:
                tutorial_name = tab_tutorial_map[current_index]
                success = self.tutorial_manager.start_tutorial(tutorial_name, force=True)
                if success:
                    self.status_bar.showMessage(f"Started tutorial for current widget", 3000)
                    self.logger.info("MainApplication", f"Manually started tutorial for {tutorial_name}")
                else:
                    self.status_bar.showMessage("Tutorial not available for this widget", 3000)
            else:
                self.status_bar.showMessage("No tutorial available for this tab", 3000)
    
    def show_settings_dialog(self):
        """Show the rebuilt modular settings dialog and restart directory monitoring if needed"""
        # Check if a settings dialog is already open
        if self._settings_dialog_instance is not None and self._settings_dialog_instance.isVisible():
            # Bring existing dialog to front and focus it
            self._settings_dialog_instance.raise_()
            self._settings_dialog_instance.activateWindow()
            return
        
        from rebuilt_settings_dialog import SettingsDialog
        
        # Store the current auto-import enabled state
        was_enabled = self.settings.get_setting("auto_import", "enabled", False)
        
        # Create new settings dialog instance
        self._settings_dialog_instance = SettingsDialog(self)
        
        # Connect to cleanup when dialog is closed
        self._settings_dialog_instance.finished.connect(self._on_settings_dialog_closed)
        
        # Show the rebuilt settings dialog
        result = self._settings_dialog_instance.exec()
        
        if result == QDialog.DialogCode.Accepted:
            # Update UI based on new settings
            self.status_bar.showMessage("Settings updated", 3000)
            
            # Reload settings since they might have changed
            self.settings.load_settings()
            
            # Check if auto-import was enabled or disabled
            is_now_enabled = self.settings.get_setting("auto_import", "enabled", False)
            
            # Update directory monitoring based on new settings
            if not was_enabled and is_now_enabled:
                # Auto-import was turned on - start monitoring
                self.start_directory_monitor()
            elif was_enabled and not is_now_enabled:
                # Auto-import was turned off - stop monitoring
                self.stop_directory_monitor()
            elif was_enabled and is_now_enabled:
                # Auto-import remained on but settings might have changed - restart
                self.stop_directory_monitor()
                self.start_directory_monitor()
        
    def _on_settings_dialog_closed(self):
        """Cleanup when settings dialog is closed"""
        self._settings_dialog_instance = None
        
    def check_for_updates(self):
        """Check for application updates"""
        if hasattr(self, 'update_manager'):
            self.update_manager.check_for_updates_manual()
        else:
            QMessageBox.information(
                self,
                "Update Check",
                "Update system is not available."
            )
    
    def show_issue_reporter(self):
        """Show the issue reporting dialog"""
        try:
            dialog = get_issue_reporter(self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Could not open issue reporter:\n{str(e)}"
            )
    
    def show_about_dialog(self):
        """Show the about dialog"""
        dialog = AboutDialog(self)
        dialog.exec()
        
    def load_settings(self):
        """Load application settings"""
        # Load window state if available
        if self.settings.has_setting("interface", "window_size"):
            size = self.settings.get_setting("interface", "window_size")
            self.resize(size[0], size[1])
            
        if self.settings.has_setting("interface", "window_position"):
            pos = self.settings.get_setting("interface", "window_position")
            self.move(pos[0], pos[1])
            
        if self.settings.has_setting("interface", "active_tab"):
            tab_index = self.settings.get_setting("interface", "active_tab")
            self.tabs.setCurrentIndex(tab_index)
            
        # Create directories for auto-import if they don't exist
        watch_dir = self.settings.get_setting("auto_import", "watch_directory")
        if watch_dir:
            os.makedirs(watch_dir, exist_ok=True)
            
        processed_dir = self.settings.get_setting("auto_import", "processed_directory")
        if processed_dir:
            os.makedirs(processed_dir, exist_ok=True)
            
    def save_settings(self):
        """Save application settings"""
        # Save window state
        self.settings.set_setting("interface", "window_size", [self.width(), self.height()])
        self.settings.set_setting("interface", "window_position", [self.x(), self.y()])
        self.settings.set_setting("interface", "active_tab", self.tabs.currentIndex())
        
        # Save settings to file
        self.settings.save_settings()
        
    def closeEvent(self, event):
        """Handle window close event"""
        self.save_settings()
        
        # Stop directory monitor
        if self.directory_monitor:
            self.directory_monitor.stop_monitoring()
            
        event.accept()
        
    def start_directory_monitor(self):
        """Start the directory monitor"""
        # Reload settings to ensure we have the latest
        self.settings.load_settings()
        
        # Check if auto-import is enabled
        if not self.settings.get_setting("auto_import", "enabled", False):
            self.status_bar.showMessage("Cannot start monitoring: Auto-import is disabled in settings", 5000)
            self.logger.warning("MainApplication", "Cannot start monitoring: Auto-import is disabled in settings")
            return False

        # Check watch directory
        watch_dir = self.settings.get_setting("auto_import", "watch_directory", "")
        if not watch_dir:
            self.status_bar.showMessage("Cannot start monitoring: No watch directory specified", 5000)
            self.logger.warning("MainApplication", "Cannot start monitoring: No watch directory specified")
            return False
            
        # Start monitoring
        self.logger.info("MainApplication", "Attempting to start directory monitoring...")
        if self.directory_monitor.start_monitoring():
            self.status_bar.showMessage(f"Directory monitoring started: {watch_dir}", 5000)
            self.logger.info("MainApplication", f"Directory monitoring started: {watch_dir}")
            return True
        else:
            self.status_bar.showMessage("Failed to start directory monitoring", 5000)
            self.logger.error("MainApplication", "Failed to start directory monitoring")
            return False
        
    def stop_directory_monitor(self):
        """Stop the directory monitor"""
        self.directory_monitor.stop_monitoring()
        self.status_bar.showMessage("Directory monitoring stopped", 3000)
        
    def handle_new_pdfs(self, pdf_paths):
        """Handle newly detected PDF files"""
        if not pdf_paths:
            return
            
        # Add the PDFs to the shared file list
        self.file_list_controller.add_files(pdf_paths)
        
        # Show notification
        pdf_count = len(pdf_paths)
        self.status_bar.showMessage(f"Added {pdf_count} new PDF file(s) from monitored directory", 5000)
        
        # Auto-process if enabled
        if self.settings.get_setting("auto_import", "auto_process", False):
            # Determine which tab to use based on current tab
            current_tab = self.tabs.currentWidget()
            if isinstance(current_tab, PDFSplitterWidget):
                # Auto-split
                self.logger.info("MainApplication", "Auto-processing PDFs with splitter")
                # We can't directly call this as it would need UI interaction
                # Instead, we add the files to the list for manual processing
            elif isinstance(current_tab, PDFMergerWidget):
                # Auto-merge
                self.logger.info("MainApplication", "Auto-processing PDFs with merger")
                # We can't directly call this as it would need UI interaction
                # Instead, we add the files to the list for manual processing
            else:
                self.logger.info("MainApplication", "Added new PDFs to file list")
        
    def copy_selected_files(self):
        """Copy selected files to a new location"""
        self.logger.info("MainApplication", "Copying selected files")
        
        # Get the current list widget from the active tab
        current_tab = self.tabs.currentWidget()
        if not hasattr(current_tab, 'listbox'):
            QMessageBox.information(self, "No File List", "The current tab doesn't have a file list.")
            return
            
        listbox = current_tab.listbox
        
        # Get selected items
        selected_items = listbox.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Files Selected", "Please select at least one file to copy.")
            return
            
        # Get selected file paths
        selected_paths = [item.text() for item in selected_items]
        
        # Check files exist
        valid_paths = []
        for path in selected_paths:
            if os.path.exists(path):
                valid_paths.append(path)
            else:
                self.logger.warning("MainApplication", f"File not found: {path}")
        
        if not valid_paths:
            QMessageBox.warning(self, "Warning", "None of the selected files could be found.")
            return
            
        # Get destination directory
        dest_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Destination Directory",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        
        if not dest_dir:
            return
            
        # Copy files
        success_count = 0
        for path in valid_paths:
            try:
                # Create destination path
                filename = os.path.basename(path)
                dest_path = os.path.join(dest_dir, filename)
                
                # Handle duplicate filenames
                counter = 1
                base_name, ext = os.path.splitext(filename)
                while os.path.exists(dest_path):
                    dest_path = os.path.join(dest_dir, f"{base_name}_copy{counter}{ext}")
                    counter += 1
                
                # Copy the file
                import shutil
                shutil.copy2(path, dest_path)
                
                # Add the new file to the list
                self.file_list_controller.add_file(dest_path)
                
                success_count += 1
            except Exception as e:
                self.logger.error("MainApplication", f"Error copying file {path}: {str(e)}")
        
        # Show results
        if success_count > 0:
            QMessageBox.information(
                self, 
                "Copy Complete", 
                f"Successfully copied {success_count} file(s) to {dest_dir}"
            )
        else:
            QMessageBox.warning(self, "Copy Failed", "Failed to copy any files.")
    
    def duplicate_selected_files(self):
        """Create a duplicate of selected files in the same directory"""
        self.logger.info("MainApplication", "Duplicating selected files")
        
        # Get the current list widget from the active tab
        current_tab = self.tabs.currentWidget()
        if not hasattr(current_tab, 'listbox'):
            QMessageBox.information(self, "No File List", "The current tab doesn't have a file list.")
            return
            
        listbox = current_tab.listbox
        
        # Get selected items
        selected_items = listbox.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Files Selected", "Please select at least one file to duplicate.")
            return
            
        # Get selected file paths
        selected_paths = [item.text() for item in selected_items]
        
        # Check files exist
        valid_paths = []
        for path in selected_paths:
            if os.path.exists(path):
                valid_paths.append(path)
            else:
                self.logger.warning("MainApplication", f"File not found: {path}")
        
        if not valid_paths:
            QMessageBox.warning(self, "Warning", "None of the selected files could be found.")
            return
            
        # Duplicate files
        success_count = 0
        new_files = []
        for path in valid_paths:
            try:
                # Create destination path in the same directory
                dir_name = os.path.dirname(path)
                filename = os.path.basename(path)
                base_name, ext = os.path.splitext(filename)
                
                # Handle duplicate filenames
                counter = 1
                dest_path = os.path.join(dir_name, f"{base_name}_copy{counter}{ext}")
                while os.path.exists(dest_path):
                    counter += 1
                    dest_path = os.path.join(dir_name, f"{base_name}_copy{counter}{ext}")
                
                # Copy the file
                import shutil
                shutil.copy2(path, dest_path)
                
                # Add the new file to the list
                new_files.append(dest_path)
                
                success_count += 1
            except Exception as e:
                self.logger.error("MainApplication", f"Error duplicating file {path}: {str(e)}")
        
        # Add all new files to the list at once
        if new_files:
            self.file_list_controller.add_files(new_files)
        
        # Show results
        if success_count > 0:
            QMessageBox.information(
                self, 
                "Duplicate Complete", 
                f"Successfully duplicated {success_count} file(s)"
            )
        else:
            QMessageBox.warning(self, "Duplicate Failed", "Failed to duplicate any files.")
    
    def delete_selected_files(self):
        """Delete selected files from disk"""
        self.logger.info("MainApplication", "Deleting selected files")
        
        # Get the current list widget from the active tab
        current_tab = self.tabs.currentWidget()
        if not hasattr(current_tab, 'listbox'):
            QMessageBox.information(self, "No File List", "The current tab doesn't have a file list.")
            return
            
        listbox = current_tab.listbox
        
        # Get selected items
        selected_items = listbox.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Files Selected", "Please select at least one file to delete.")
            return
            
        # Get selected file paths
        selected_paths = [item.text() for item in selected_items]
        
        # Check files exist
        valid_paths = []
        for path in selected_paths:
            if os.path.exists(path):
                valid_paths.append(path)
            else:
                self.logger.warning("MainApplication", f"File not found: {path}")
        
        if not valid_paths:
            QMessageBox.warning(self, "Warning", "None of the selected files could be found.")
            return
            
        # Confirm deletion
        result = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to permanently delete {len(valid_paths)} file(s) from disk?\n\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if result != QMessageBox.StandardButton.Yes:
            return
            
        # Delete files
        success_count = 0
        for path in valid_paths:
            try:
                os.remove(path)
                success_count += 1
            except Exception as e:
                self.logger.error("MainApplication", f"Error deleting file {path}: {str(e)}")
        
        # Remove deleted files from the list
        if success_count > 0:
            self.file_list_controller.remove_files(valid_paths)
        
        # Show results
        if success_count > 0:
            QMessageBox.information(
                self, 
                "Delete Complete", 
                f"Successfully deleted {success_count} file(s)"
            )
        else:
            QMessageBox.warning(self, "Delete Failed", "Failed to delete any files.")
    
    def create_placeholder_widget(self, title, description):
        """Create a placeholder widget for future functionality"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Add title
        title_label = QLabel(f"<h2>{title}</h2>")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Add description
        desc_label = QLabel(description)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc_label)
        
        # Add coming soon message
        coming_soon = QLabel("<h3>Coming Soon!</h3>")
        coming_soon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(coming_soon)
        
        layout.addStretch()
        
        return widget

# Close PyInstaller splash screen (if present)
try:
    import pyi_splash
    pyi_splash.close()
except ImportError:
    # Not running as PyInstaller executable, or splash not enabled
    pass
def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle("Fusion")
    
    # Create and show the main window
    main_window = MainWindow()
    main_window.show()
    
    # Start the event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
