"""
Main PyQt6 application window for media automation system.

Features:
- Tabbed interface for different sections
- Real-time status dashboard
- Task scheduling interface
- Logs and history viewer
- Configuration management
- System tray integration
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QLabel, QSystemTrayIcon, QMenu, QMessageBox,
    QStatusBar
)
from PyQt6.QtCore import Qt, QTimer, QUrl, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QAction, QFont
from datetime import datetime
import logging
import sys

from .styles import DARK_STYLESHEET, get_color
from .status_dashboard import StatusDashboard
from .task_scheduler_widget import TaskSchedulerWidget
from .logs_viewer import LogsViewer
from .downloads_widget import DownloadsWidget
from .jobs_widget import JobsWidget


logger = logging.getLogger(__name__)


class MediaAutomationUI(QMainWindow):
    """
    Main application window for media automation system.
    
    Provides:
    - Real-time status dashboard
    - Task scheduling interface
    - Task execution history and logs
    - System configuration (basic)
    - System tray integration
    """
    
    def __init__(self, task_manager, task_scheduler, status_tracker, event_bus):
        """
        Initialize the UI.
        
        Args:
            task_manager: TaskManager instance
            task_scheduler: TaskScheduler instance
            status_tracker: StatusTracker instance
            event_bus: EventBus instance
        """
        super().__init__()
        
        self.task_manager = task_manager
        self.task_scheduler = task_scheduler
        self.status_tracker = status_tracker
        self.event_bus = event_bus
        
        # Setup window
        self.setWindowTitle("Media Automation System")
        self.setWindowIcon(self._create_icon())
        self.setGeometry(100, 100, 1200, 800)
        
        # Apply dark theme
        self.setStyleSheet(DARK_STYLESHEET)
        
        # Create UI
        self._setup_ui()
        
        # Setup system tray
        self._setup_tray()
        
        # Setup status bar
        self._setup_status_bar()
        
        # Start the scheduler
        if not self.task_manager.is_running():
            self.task_manager.start()
            logger.info("Task manager started")
        
        logger.info("UI initialized and ready")
    
    def _setup_ui(self):
        """Setup the main UI."""
        central_widget = QWidget()
        layout = QVBoxLayout()
        
        # Create tabbed interface
        self.tabs = QTabWidget()
        
        # Status Dashboard tab
        self.status_dashboard = StatusDashboard(self.status_tracker, self.event_bus)
        self.tabs.addTab(self.status_dashboard, "📊 Status Dashboard")
        
        # Task Scheduler tab
        self.task_scheduler_widget = TaskSchedulerWidget(self.task_manager, self.task_scheduler)
        self.tabs.addTab(self.task_scheduler_widget, "📅 Task Scheduler")

        # Downloads + Job tracking tab
        self.downloads_widget = DownloadsWidget(self.task_manager)
        self.tabs.addTab(self.downloads_widget, "⬇ Downloads & Jobs")

        # Job board + post-processing scheduling tab
        self.jobs_widget = JobsWidget(self.task_manager)
        self.tabs.addTab(self.jobs_widget, "🧩 Jobs")
        
        # Logs Viewer tab
        self.logs_viewer = LogsViewer(self.task_scheduler, self.event_bus)
        self.tabs.addTab(self.logs_viewer, "📝 Logs & History")
        
        # Quick actions bar
        actions_layout = self._create_quick_actions()
        layout.addLayout(actions_layout)
        
        # Main content
        layout.addWidget(self.tabs)
        
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
    
    def _create_quick_actions(self) -> QHBoxLayout:
        """Create quick action buttons."""
        layout = QHBoxLayout()
        
        layout.addWidget(QLabel("Quick Actions:"))
        
        # Run health check
        health_btn = QPushButton("🔍 Service Health Check")
        health_btn.setMaximumWidth(200)
        health_btn.clicked.connect(self._run_health_check)
        layout.addWidget(health_btn)
        
        # Run full workflow
        workflow_btn = QPushButton("▶ Run Full Workflow")
        workflow_btn.setMaximumWidth(200)
        workflow_btn.setStyleSheet("background-color: #28A745;")
        workflow_btn.clicked.connect(self._run_workflow)
        layout.addWidget(workflow_btn)
        
        layout.addStretch()
        
        # Minimize button
        minimize_btn = QPushButton("📦 Minimize to Tray")
        minimize_btn.setMaximumWidth(150)
        minimize_btn.clicked.connect(self.hide)
        layout.addWidget(minimize_btn)
        
        return layout
    
    def _setup_status_bar(self):
        """Setup the status bar."""
        self.status_bar = self.statusBar()
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)
        
        # Task count label
        self.task_count_label = QLabel("Tasks: 0")
        self.status_bar.addPermanentWidget(self.task_count_label)
        
        # Update timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status_bar)
        self.status_timer.start(2000)
    
    def _update_status_bar(self):
        """Update the status bar."""
        # Update system status
        system_status = self.status_tracker.get_system_status()
        self.status_label.setText(f"System: {system_status.value}")
        
        # Update task count
        tasks = self.status_tracker.get_all_task_statuses()
        running_tasks = sum(1 for t in tasks.values() if t.status == "running")
        self.task_count_label.setText(f"Tasks: {running_tasks}")
    
    def _setup_tray(self):
        """Setup system tray icon and menu."""
        # Create tray icon
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self._create_icon())
        
        # Create tray menu
        tray_menu = QMenu()
        
        # Show action
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.showNormal)
        tray_menu.addAction(show_action)
        
        # Hide action
        hide_action = QAction("Hide", self)
        hide_action.triggered.connect(self.hide)
        tray_menu.addAction(hide_action)
        
        tray_menu.addSeparator()
        
        # Health check action
        health_action = QAction("Run Health Check", self)
        health_action.triggered.connect(self._run_health_check)
        tray_menu.addAction(health_action)
        
        tray_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self._exit_app)
        tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
        # Connect tray icon activation
        self.tray_icon.activated.connect(self._on_tray_activated)
    
    def _on_tray_activated(self, reason):
        """Handle tray icon activation."""
        from PyQt6.QtWidgets import QSystemTrayIcon
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.showNormal()
    
    def _run_health_check(self):
        """Run a service health check."""
        self.task_manager.check_all_services_health()
        QMessageBox.information(self, "Health Check", "Service health check started. Check the Status Dashboard for results.")
    
    def _run_workflow(self):
        """Run the full workflow."""
        QMessageBox.information(
            self, 
            "Full Workflow",
            "Note: Full workflow requires file scanner and distributor instances from your application.\n\n"
            "This is a demonstration button. Configure it in your main application file."
        )
    
    def _create_icon(self) -> QIcon:
        """Create the application icon."""
        # For now, create a simple colored icon
        # In production, you'd use an actual image file
        from PyQt6.QtGui import QPixmap, QPalette
        
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        # You could use a QPixmap from a file here
        # pixmap = QPixmap("path/to/icon.png")
        
        return QIcon(pixmap)
    
    def _exit_app(self):
        """Exit the application."""
        reply = QMessageBox.question(
            self,
            "Confirm Exit",
            "Are you sure you want to exit? Scheduled tasks will be stopped.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self._cleanup()
            sys.exit(0)
    
    def _cleanup(self):
        """Clean up resources."""
        logger.info("Cleaning up resources...")
        self.task_manager.stop()
        self.tray_icon.hide()
        logger.info("Cleanup complete")
    
    def closeEvent(self, event):
        """Handle window close event."""
        # Minimize to tray instead of closing
        event.ignore()
        self.hide()
    
    def changeEvent(self, event):
        """Handle window state change."""
        from PyQt6.QtCore import QEvent
        if event.type() == QEvent.Type.WindowStateChange:
            if self.windowState() & Qt.WindowState.WindowMinimized:
                self.hide()
    
    @staticmethod
    def launch():
        """Launch the UI application."""
        from event_system import initialize_event_system
        from task_manager import TaskManager
        
        # Initialize event system
        event_bus, status_tracker = initialize_event_system()
        
        # Create task manager
        task_manager = TaskManager(event_bus=event_bus, status_tracker=status_tracker)
        task_scheduler = task_manager.get_scheduler()
        
        # Create and show UI
        app = QApplication.instance() or QApplication(sys.argv)
        window = MediaAutomationUI(task_manager, task_scheduler, status_tracker, event_bus)
        window.show()
        
        # Start event loop
        sys.exit(app.exec())


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    MediaAutomationUI.launch()
