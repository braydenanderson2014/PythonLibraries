"""
Real-time status dashboard widget showing current system state.

Displays:
- Currently running tasks with progress
- System status overview
- Service health status
- System statistics
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QProgressBar, QTableWidget, QTableWidgetItem, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QColor, QIcon
from datetime import datetime
from typing import Dict, Optional

from .styles import get_color


class StatusUpdater(QObject):
    """Emitter for status updates (thread-safe)."""
    status_updated = pyqtSignal()
    

class StatusDashboard(QWidget):
    """
    Real-time status dashboard showing:
    - Active tasks with progress bars
    - System status
    - Service health
    - Statistics
    """
    
    def __init__(self, status_tracker, event_bus):
        """
        Initialize the status dashboard.
        
        Args:
            status_tracker: StatusTracker instance for status data
            event_bus: EventBus instance for subscribing to events
        """
        super().__init__()
        self.status_tracker = status_tracker
        self.event_bus = event_bus
        self.status_updater = StatusUpdater()
        
        # Subscribe to events
        from event_system import EventType
        self.event_bus.subscribe(EventType.TASK_STARTED, self._on_task_event)
        self.event_bus.subscribe(EventType.TASK_PROGRESS, self._on_task_event)
        self.event_bus.subscribe(EventType.TASK_COMPLETED, self._on_task_event)
        self.event_bus.subscribe(EventType.TASK_FAILED, self._on_task_event)
        self.event_bus.subscribe(EventType.SERVICE_ONLINE, self._on_service_event)
        self.event_bus.subscribe(EventType.SERVICE_OFFLINE, self._on_service_event)
        self.event_bus.subscribe(EventType.STATISTICS_UPDATED, self._on_stats_event)
        self.event_bus.subscribe(EventType.SYSTEM_STATUS_CHANGED, self._on_system_event)
        
        # Connect status updates to UI refresh
        self.status_updater.status_updated.connect(self._refresh_ui)
        
        # Setup UI
        self._setup_ui()
        
        # Start auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._refresh_ui)
        self.refresh_timer.start(2000)  # Update every 2 seconds
    
    def _setup_ui(self):
        """Setup the dashboard layout."""
        layout = QVBoxLayout()
        
        # System status card
        layout.addWidget(self._create_system_status_card())
        
        # Active tasks card
        layout.addWidget(self._create_active_tasks_card())
        
        # Services health card
        layout.addWidget(self._create_services_card())
        
        # Statistics card
        layout.addWidget(self._create_statistics_card())
        
        layout.addStretch()
        self.setLayout(layout)
    
    def _create_system_status_card(self) -> QGroupBox:
        """Create the system status card."""
        group = QGroupBox("System Status")
        layout = QHBoxLayout()
        
        self.system_status_label = QLabel("Initializing...")
        self.system_status_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(self.system_status_label)
        
        self.uptime_label = QLabel("Uptime: 0h 0m 0s")
        self.uptime_label.setStyleSheet(f"color: {get_color('text_secondary')};")
        layout.addWidget(self.uptime_label)
        
        layout.addStretch()
        group.setLayout(layout)
        return group
    
    def _create_active_tasks_card(self) -> QGroupBox:
        """Create the active tasks display card."""
        group = QGroupBox("Active Tasks")
        layout = QVBoxLayout()
        
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.tasks_container = QWidget()
        self.tasks_layout = QVBoxLayout()
        self.tasks_container.setLayout(self.tasks_layout)
        scroll.setWidget(self.tasks_container)
        
        layout.addWidget(scroll)
        group.setLayout(layout)
        return group
    
    def _create_services_card(self) -> QGroupBox:
        """Create the services health card."""
        group = QGroupBox("Service Status")
        layout = QVBoxLayout()
        
        self.services_table = QTableWidget(0, 4)
        self.services_table.setHorizontalHeaderLabels(["Service", "Type", "Status", "Last Check"])
        self.services_table.horizontalHeader().setStretchLastSection(False)
        self.services_table.setMaximumHeight(150)
        
        layout.addWidget(self.services_table)
        group.setLayout(layout)
        return group
    
    def _create_statistics_card(self) -> QGroupBox:
        """Create the statistics card."""
        group = QGroupBox("Statistics")
        layout = QGridLayout()
        
        # Statistics labels
        self.stats_labels = {}
        stats = [
            ("total_files_scanned", "Files Scanned", "0"),
            ("total_files_distributed", "Files Distributed", "0"),
            ("total_distribution_size_gb", "Total Distribution Size", "0 GB"),
            ("total_tasks_completed", "Tasks Completed", "0"),
            ("total_tasks_failed", "Tasks Failed", "0"),
        ]
        
        for i, (key, label, default) in enumerate(stats):
            label_widget = QLabel(label)
            label_widget.setStyleSheet(f"color: {get_color('text_secondary')};")
            value_widget = QLabel(default)
            value_widget.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            
            layout.addWidget(label_widget, i // 3, (i % 3) * 2)
            layout.addWidget(value_widget, i // 3, (i % 3) * 2 + 1, Qt.AlignmentFlag.AlignRight)
            
            self.stats_labels[key] = value_widget
        
        group.setLayout(layout)
        return group
    
    def _refresh_ui(self):
        """Refresh all UI elements."""
        self._update_system_status()
        self._update_tasks()
        self._update_services()
        self._update_statistics()
    
    def _update_system_status(self):
        """Update the system status display."""
        status = self.status_tracker.get_system_status()
        status_text = status.value.upper()
        
        # Map status to color
        color_map = {
            "ready": get_color("success"),
            "running_tasks": get_color("accent"),
            "error": get_color("error"),
            "initializing": get_color("warning"),
            "stopped": get_color("border"),
        }
        
        color = color_map.get(status.value, get_color("text"))
        self.system_status_label.setText(f"● {status_text}")
        self.system_status_label.setStyleSheet(f"color: {color};")
    
    def _update_tasks(self):
        """Update the active tasks display."""
        # Clear existing widgets
        while self.tasks_layout.count():
            self.tasks_layout.takeAt(0).widget().deleteLater()
        
        tasks = self.status_tracker.get_all_task_statuses()
        
        if not tasks:
            no_tasks_label = QLabel("No active tasks")
            no_tasks_label.setStyleSheet(f"color: {get_color('text_secondary')};")
            self.tasks_layout.addWidget(no_tasks_label)
        else:
            for task_id, task in tasks.items():
                # Skip idle tasks
                if task.status == "idle":
                    continue
                
                task_widget = self._create_task_widget(task)
                self.tasks_layout.addWidget(task_widget)
        
        self.tasks_layout.addStretch()
    
    def _create_task_widget(self, task) -> QWidget:
        """Create a widget for a single task."""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Task header
        header_layout = QHBoxLayout()
        name_label = QLabel(task.task_name)
        name_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        header_layout.addWidget(name_label)
        
        # Status badge
        status_color_map = {
            "running": get_color("accent"),
            "completed": get_color("success"),
            "error": get_color("error"),
            "idle": get_color("border"),
        }
        status_badge = QLabel(task.status.upper())
        status_badge.setStyleSheet(f"background-color: {status_color_map.get(task.status)}; "
                                  f"color: white; padding: 2px 8px; border-radius: 3px;")
        header_layout.addWidget(status_badge)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Progress bar
        if task.total_items > 0:
            progress_bar = QProgressBar()
            progress_bar.setValue(int((task.processed_items / task.total_items) * 100))
            progress_bar.setMaximumHeight(16)
            layout.addWidget(progress_bar)
            
            # Progress text
            progress_text = QLabel(f"{task.processed_items}/{task.total_items} items")
            progress_text.setStyleSheet(f"color: {get_color('text_secondary')}; font-size: 9px;")
            layout.addWidget(progress_text)
        
        # Current item
        if task.current_item:
            current_label = QLabel(f"Current: {task.current_item[:60]}")
            current_label.setStyleSheet(f"color: {get_color('text_secondary')}; font-size: 9px;")
            layout.addWidget(current_label)
        
        # Error message
        if task.error_message:
            error_label = QLabel(f"Error: {task.error_message}")
            error_label.setStyleSheet(f"color: {get_color('error')}; font-size: 9px;")
            layout.addWidget(error_label)
        
        widget.setLayout(layout)
        return widget
    
    def _update_services(self):
        """Update the services health table."""
        services = self.status_tracker.get_all_service_statuses()
        
        self.services_table.setRowCount(len(services))
        self.services_table.setColumnCount(4)
        self.services_table.setHorizontalHeaderLabels(["Service", "Type", "Status", "Last Check"])
        
        for row, (service_name, service) in enumerate(services.items()):
            # Service name
            item = QTableWidgetItem(service.service_name)
            self.services_table.setItem(row, 0, item)
            
            # Service type
            item = QTableWidgetItem(service.service_type)
            self.services_table.setItem(row, 1, item)
            
            # Status
            status_text = "🟢 Online" if service.is_online else "🔴 Offline"
            item = QTableWidgetItem(status_text)
            if not service.is_online and service.error_message:
                item.setToolTip(service.error_message)
            self.services_table.setItem(row, 2, item)
            
            # Last check
            last_check = datetime.fromisoformat(service.last_check)
            time_ago = self._format_time_ago(last_check)
            item = QTableWidgetItem(time_ago)
            self.services_table.setItem(row, 3, item)
    
    def _update_statistics(self):
        """Update the statistics display."""
        stats = self.status_tracker.get_statistics()
        
        # Format and update
        for key, label_widget in self.stats_labels.items():
            if key == "total_distribution_size_gb":
                value = stats.get(key, 0)
                label_widget.setText(f"{value:.2f} GB")
            else:
                value = stats.get(key, 0)
                label_widget.setText(str(int(value)))
    
    def _on_task_event(self, event):
        """Handle task events."""
        self.status_updater.status_updated.emit()
    
    def _on_service_event(self, event):
        """Handle service events."""
        self.status_updater.status_updated.emit()
    
    def _on_stats_event(self, event):
        """Handle statistics events."""
        self.status_updater.status_updated.emit()
    
    def _on_system_event(self, event):
        """Handle system events."""
        self.status_updater.status_updated.emit()
    
    def _format_time_ago(self, dt: datetime) -> str:
        """Format a datetime as 'X minutes ago'."""
        now = datetime.now()
        diff = (now - dt).total_seconds()
        
        if diff < 60:
            return "just now"
        elif diff < 3600:
            minutes = int(diff / 60)
            return f"{minutes}m ago"
        elif diff < 86400:
            hours = int(diff / 3600)
            return f"{hours}h ago"
        else:
            days = int(diff / 86400)
            return f"{days}d ago"
    
    def closeEvent(self, event):
        """Clean up when widget is closed."""
        self.refresh_timer.stop()
        super().closeEvent(event)
