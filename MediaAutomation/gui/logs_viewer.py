"""
Logs and execution history viewer widget.

Displays:
- Task execution history
- Event log
- Filtering and search capabilities
- Real-time updates
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLineEdit, QPushButton, QComboBox, QLabel, QTabWidget, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QDate
from PyQt6.QtGui import QFont, QColor
from datetime import datetime, timedelta
from typing import Optional

from .styles import get_color


class LogsUpdater(QObject):
    """Emitter for log updates (thread-safe)."""
    logs_updated = pyqtSignal()


class LogsViewer(QWidget):
    """
    Widget for viewing task execution history and event logs.
    
    Features:
    - View execution history for each task
    - View system events
    - Filter by date range, task, status
    - Search logs
    - Clear history
    """
    
    def __init__(self, task_scheduler, event_bus):
        """
        Initialize the logs viewer.
        
        Args:
            task_scheduler: TaskScheduler instance for execution history
            event_bus: EventBus instance for events
        """
        super().__init__()
        self.task_scheduler = task_scheduler
        self.event_bus = event_bus
        self.logs_updater = LogsUpdater()
        
        # Subscribe to events
        from event_system import EventType
        self.event_bus.subscribe(EventType.TASK_COMPLETED, lambda e: self.logs_updater.logs_updated.emit())
        self.event_bus.subscribe(EventType.TASK_FAILED, lambda e: self.logs_updater.logs_updated.emit())
        self.event_bus.subscribe(EventType.ERROR_OCCURRED, lambda e: self.logs_updater.logs_updated.emit())
        
        # Connect updates
        self.logs_updater.logs_updated.connect(self._refresh_logs)
        
        # Setup UI
        self._setup_ui()
        
        # Start auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._refresh_logs)
        self.refresh_timer.start(5000)  # Update every 5 seconds
    
    def _setup_ui(self):
        """Setup the logs viewer UI."""
        layout = QVBoxLayout()
        
        # Create tabs
        tabs = QTabWidget()
        tabs.addTab(self._create_execution_history_tab(), "Execution History")
        tabs.addTab(self._create_event_log_tab(), "System Events")
        
        layout.addWidget(tabs)
        self.setLayout(layout)
    
    def _create_execution_history_tab(self) -> QWidget:
        """Create the execution history tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Filters
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("Filter by status:"))
        self.exec_status_filter = QComboBox()
        self.exec_status_filter.addItems(["All", "Completed", "Failed", "Running"])
        self.exec_status_filter.currentTextChanged.connect(self._refresh_logs)
        filter_layout.addWidget(self.exec_status_filter)
        
        filter_layout.addWidget(QLabel("Search:"))
        self.exec_search = QLineEdit()
        self.exec_search.setPlaceholderText("Search task name...")
        self.exec_search.textChanged.connect(self._refresh_logs)
        filter_layout.addWidget(self.exec_search)
        
        filter_layout.addStretch()
        
        clear_btn = QPushButton("Clear History")
        clear_btn.setMaximumWidth(100)
        clear_btn.setStyleSheet("background-color: #DC3545;")
        clear_btn.clicked.connect(self._clear_execution_history)
        filter_layout.addWidget(clear_btn)
        
        layout.addLayout(filter_layout)
        
        # Execution history table
        self.exec_history_table = QTableWidget(0, 6)
        self.exec_history_table.setHorizontalHeaderLabels(
            ["Task Name", "Start Time", "End Time", "Duration", "Status", "Error Message"]
        )
        self.exec_history_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.exec_history_table)
        
        widget.setLayout(layout)
        return widget
    
    def _create_event_log_tab(self) -> QWidget:
        """Create the system events log tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Filters
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("Filter by type:"))
        self.event_type_filter = QComboBox()
        self.event_type_filter.addItems(["All", "Task", "Service", "System", "File", "Error"])
        self.event_type_filter.currentTextChanged.connect(self._refresh_logs)
        filter_layout.addWidget(self.event_type_filter)
        
        filter_layout.addWidget(QLabel("Search:"))
        self.event_search = QLineEdit()
        self.event_search.setPlaceholderText("Search events...")
        self.event_search.textChanged.connect(self._refresh_logs)
        filter_layout.addWidget(self.event_search)
        
        filter_layout.addStretch()
        
        clear_btn = QPushButton("Clear Events")
        clear_btn.setMaximumWidth(100)
        clear_btn.setStyleSheet("background-color: #DC3545;")
        clear_btn.clicked.connect(self._clear_events)
        filter_layout.addWidget(clear_btn)
        
        layout.addLayout(filter_layout)
        
        # Events table
        self.events_table = QTableWidget(0, 4)
        self.events_table.setHorizontalHeaderLabels(
            ["Timestamp", "Type", "Source", "Message"]
        )
        self.events_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.events_table)
        
        widget.setLayout(layout)
        return widget
    
    def _refresh_logs(self):
        """Refresh the logs displays."""
        self._update_execution_history()
        self._update_events()
    
    def _update_execution_history(self):
        """Update the execution history table."""
        # Get filter values
        status_filter = self.exec_status_filter.currentText().lower()
        search_text = self.exec_search.text().lower()
        
        # Get execution history
        history = self.task_scheduler.get_execution_history(limit=100)
        
        # Filter
        filtered_history = []
        for execution in history:
            # Status filter
            if status_filter not in ["all"] and status_filter != execution.status:
                continue
            
            # Search filter
            if search_text and search_text not in execution.task_name.lower():
                continue
            
            filtered_history.append(execution)
        
        # Update table
        self.exec_history_table.setRowCount(len(filtered_history))
        
        for row, execution in enumerate(filtered_history):
            # Task name
            item = QTableWidgetItem(execution.task_name)
            self.exec_history_table.setItem(row, 0, item)
            
            # Start time
            start_time = datetime.fromisoformat(execution.start_time)
            item = QTableWidgetItem(start_time.strftime("%Y-%m-%d %H:%M:%S"))
            self.exec_history_table.setItem(row, 1, item)
            
            # End time
            if execution.end_time:
                end_time = datetime.fromisoformat(execution.end_time)
                item = QTableWidgetItem(end_time.strftime("%Y-%m-%d %H:%M:%S"))
            else:
                item = QTableWidgetItem("-")
            self.exec_history_table.setItem(row, 2, item)
            
            # Duration
            item = QTableWidgetItem(f"{execution.execution_time_seconds:.1f}s")
            self.exec_history_table.setItem(row, 3, item)
            
            # Status
            status_color_map = {
                "completed": get_color("success"),
                "failed": get_color("error"),
                "running": get_color("accent"),
            }
            status_text = execution.status.upper()
            item = QTableWidgetItem(status_text)
            item.setForeground(QColor(status_color_map.get(execution.status, get_color("text"))))
            self.exec_history_table.setItem(row, 4, item)
            
            # Error message
            error_msg = execution.error_message or "-"
            item = QTableWidgetItem(error_msg)
            if execution.error_message:
                item.setToolTip(execution.error_message)
            self.exec_history_table.setItem(row, 5, item)
    
    def _update_events(self):
        """Update the system events table."""
        # Get filter values
        event_type_filter = self.event_type_filter.currentText().lower()
        search_text = self.event_search.text().lower()
        
        # Get events from event bus
        from event_system import EventType
        events = self.event_bus.get_history(limit=100)
        
        # Filter events
        filtered_events = []
        for event in events:
            # Type filter
            event_category = self._get_event_category(event.event_type)
            if event_type_filter not in ["all"] and event_type_filter != event_category:
                continue
            
            # Search filter
            search_fields = [
                event.event_type.value,
                event.source,
                str(event.data)
            ]
            if search_text and not any(search_text in field.lower() for field in search_fields):
                continue
            
            filtered_events.append(event)
        
        # Update table
        self.events_table.setRowCount(len(filtered_events))
        
        for row, event in enumerate(filtered_events):
            # Timestamp
            timestamp = datetime.fromisoformat(event.timestamp)
            item = QTableWidgetItem(timestamp.strftime("%Y-%m-%d %H:%M:%S"))
            self.events_table.setItem(row, 0, item)
            
            # Type
            item = QTableWidgetItem(event.event_type.value)
            self.events_table.setItem(row, 1, item)
            
            # Source
            item = QTableWidgetItem(event.source)
            self.events_table.setItem(row, 2, item)
            
            # Message
            message = self._format_event_message(event)
            item = QTableWidgetItem(message)
            item.setToolTip(str(event.data))
            self.events_table.setItem(row, 3, item)
    
    def _get_event_category(self, event_type) -> str:
        """Get the category of an event."""
        name = event_type.value
        if "task" in name:
            return "task"
        elif "service" in name:
            return "service"
        elif "file" in name or "distribution" in name:
            return "file"
        elif "error" in name:
            return "error"
        else:
            return "system"
    
    def _format_event_message(self, event) -> str:
        """Format an event as a human-readable message."""
        event_type = event.event_type.value
        
        if "task" in event_type:
            return f"{event.data.get('task_name', 'Unknown')} - {event.data.get('status', 'unknown')}"
        elif "service" in event_type:
            is_online = event.data.get("is_online", False)
            status = "online" if is_online else "offline"
            return f"{event.data.get('service_name', 'Unknown')} - {status}"
        elif "statistics" in event_type:
            files = event.data.get("total_files_scanned", 0)
            return f"Stats updated: {files} files scanned"
        else:
            return event_type
    
    def _clear_execution_history(self):
        """Clear execution history."""
        reply = QMessageBox.question(
            self, "Confirm Clear",
            "Are you sure you want to clear all execution history?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Note: TaskScheduler doesn't have a clear method yet, but this is where it would go
            self._refresh_logs()
    
    def _clear_events(self):
        """Clear event log."""
        reply = QMessageBox.question(
            self, "Confirm Clear",
            "Are you sure you want to clear all events?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.event_bus.clear_history()
            self._refresh_logs()
    
    def closeEvent(self, event):
        """Clean up when widget is closed."""
        self.refresh_timer.stop()
        super().closeEvent(event)
