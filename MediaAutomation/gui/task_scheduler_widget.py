"""
Task scheduler widget for creating and managing scheduled tasks.

Features:
- Create interval-based schedules
- Create cron-based schedules
- Manage existing schedules (enable/disable/delete)
- View next execution time
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton,
    QComboBox, QSpinBox, QLineEdit, QTableWidget, QTableWidgetItem,
    QDialog, QMessageBox, QCheckBox, QTabWidget
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
from datetime import datetime
from typing import Optional

from .styles import get_color
from scheduler import ScheduleType


class TaskSchedulerWidget(QWidget):
    """
    Widget for managing scheduled tasks.
    
    Allows users to:
    - Create new interval schedules
    - Create new cron schedules
    - Manage existing schedules
    - View execution history
    """
    
    def __init__(self, task_manager, task_scheduler):
        """
        Initialize the scheduler widget.
        
        Args:
            task_manager: TaskManager instance
            task_scheduler: TaskScheduler instance
        """
        super().__init__()
        self.task_manager = task_manager
        self.task_scheduler = task_scheduler
        
        # Available tasks that can be scheduled
        self.available_tasks = {
            "File Scan": self._task_file_scan,
            "Service Health Check": self._task_health_check,
            "Full Workflow": self._task_full_workflow,
        }
        
        # Setup UI
        self._setup_ui()
        
        # Start auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._refresh_schedules)
        self.refresh_timer.start(5000)  # Update every 5 seconds
    
    def _setup_ui(self):
        """Setup the UI layout."""
        layout = QVBoxLayout()
        
        # Create tabs for different schedule types
        tabs = QTabWidget()
        tabs.addTab(self._create_interval_tab(), "Interval Schedule")
        tabs.addTab(self._create_cron_tab(), "Cron Schedule")
        
        layout.addWidget(tabs)
        
        # Manage schedules section
        layout.addWidget(self._create_management_card())
        
        self.setLayout(layout)
    
    def _create_interval_tab(self) -> QWidget:
        """Create the interval schedule tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Task selection
        task_layout = QHBoxLayout()
        task_layout.addWidget(QLabel("Task:"))
        self.interval_task_combo = QComboBox()
        self.interval_task_combo.addItems(self.available_tasks.keys())
        task_layout.addWidget(self.interval_task_combo)
        task_layout.addStretch()
        layout.addLayout(task_layout)
        
        # Interval configuration
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Run every:"))
        
        self.interval_value = QSpinBox()
        self.interval_value.setMinimum(1)
        self.interval_value.setMaximum(999)
        self.interval_value.setValue(1)
        interval_layout.addWidget(self.interval_value)
        
        self.interval_unit = QComboBox()
        self.interval_unit.addItems(["minutes", "hours", "days"])
        self.interval_unit.setCurrentText("hours")
        interval_layout.addWidget(self.interval_unit)
        interval_layout.addStretch()
        layout.addLayout(interval_layout)
        
        # Description
        desc_layout = QHBoxLayout()
        desc_layout.addWidget(QLabel("Description (optional):"))
        self.interval_description = QLineEdit()
        self.interval_description.setPlaceholderText("Enter task description...")
        desc_layout.addWidget(self.interval_description)
        layout.addLayout(desc_layout)
        
        # Create button
        create_btn = QPushButton("✓ Create Schedule")
        create_btn.setStyleSheet("background-color: #28A745;")
        create_btn.clicked.connect(self._create_interval_schedule)
        layout.addWidget(create_btn)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def _create_cron_tab(self) -> QWidget:
        """Create the cron schedule tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Task selection
        task_layout = QHBoxLayout()
        task_layout.addWidget(QLabel("Task:"))
        self.cron_task_combo = QComboBox()
        self.cron_task_combo.addItems(self.available_tasks.keys())
        task_layout.addWidget(self.cron_task_combo)
        task_layout.addStretch()
        layout.addLayout(task_layout)
        
        # Cron expression
        cron_layout = QHBoxLayout()
        cron_layout.addWidget(QLabel("Cron Expression:"))
        self.cron_expression = QLineEdit()
        self.cron_expression.setPlaceholderText("e.g., '0 */12 * * *' for twice daily")
        cron_layout.addWidget(self.cron_expression)
        layout.addLayout(cron_layout)
        
        # Cron examples help
        help_text = QLabel(
            "Common patterns:\n"
            "  */5 * * * * — Every 5 minutes\n"
            "  0 * * * * — Every hour\n"
            "  0 0 * * * — Daily at midnight\n"
            "  0 0 * * MON — Weekly on Monday"
        )
        help_text.setStyleSheet(f"color: {get_color('text_secondary')}; font-size: 9px; white-space: pre-wrap;")
        layout.addWidget(help_text)
        
        # Description
        desc_layout = QHBoxLayout()
        desc_layout.addWidget(QLabel("Description (optional):"))
        self.cron_description = QLineEdit()
        self.cron_description.setPlaceholderText("Enter task description...")
        desc_layout.addWidget(self.cron_description)
        layout.addLayout(desc_layout)
        
        # Create button
        create_btn = QPushButton("✓ Create Schedule")
        create_btn.setStyleSheet("background-color: #28A745;")
        create_btn.clicked.connect(self._create_cron_schedule)
        layout.addWidget(create_btn)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def _create_management_card(self) -> QGroupBox:
        """Create the schedule management card."""
        group = QGroupBox("Manage Schedules")
        layout = QVBoxLayout()
        
        # Schedules table
        self.schedules_table = QTableWidget(0, 6)
        self.schedules_table.setHorizontalHeaderLabels(
            ["Task Name", "Type", "Schedule", "Enabled", "Next Run", "Actions"]
        )
        self.schedules_table.horizontalHeader().setStretchLastSection(False)
        self.schedules_table.setColumnWidth(5, 100)
        
        layout.addWidget(self.schedules_table)
        group.setLayout(layout)
        return group
    
    def _refresh_schedules(self):
        """Refresh the schedules table."""
        schedules = self.task_scheduler.get_all_tasks()
        
        self.schedules_table.setRowCount(len(schedules))
        
        for row, (task_id, config) in enumerate(schedules.items()):
            # Task name
            item = QTableWidgetItem(config.task_name)
            self.schedules_table.setItem(row, 0, item)
            
            # Schedule type
            item = QTableWidgetItem(config.schedule_type.value.upper())
            self.schedules_table.setItem(row, 1, item)
            
            # Schedule details
            if config.schedule_type == ScheduleType.INTERVAL:
                schedule_str = f"Every {config.interval_value} {config.interval_unit}"
            elif config.schedule_type == ScheduleType.CRON:
                schedule_str = config.cron_expression
            else:
                schedule_str = config.scheduled_time
            
            item = QTableWidgetItem(schedule_str)
            self.schedules_table.setItem(row, 2, item)
            
            # Enabled checkbox
            check_widget = QWidget()
            check_layout = QHBoxLayout()
            check_box = QCheckBox()
            check_box.setChecked(config.enabled)
            check_box.stateChanged.connect(lambda state, tid=task_id: self._toggle_schedule(tid, state))
            check_layout.addWidget(check_box)
            check_layout.setContentsMargins(5, 0, 5, 0)
            check_widget.setLayout(check_layout)
            self.schedules_table.setCellWidget(row, 3, check_widget)
            
            # Next execution
            next_exec = self.task_scheduler.get_next_execution_time(task_id)
            if next_exec:
                next_exec_str = self._format_next_execution(next_exec)
            else:
                next_exec_str = "N/A"
            
            item = QTableWidgetItem(next_exec_str)
            self.schedules_table.setItem(row, 4, item)
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout()
            
            delete_btn = QPushButton("Delete")
            delete_btn.setStyleSheet("background-color: #DC3545; padding: 4px 8px; font-size: 9px;")
            delete_btn.setMaximumWidth(60)
            delete_btn.clicked.connect(lambda checked, tid=task_id: self._delete_schedule(tid))
            actions_layout.addWidget(delete_btn)
            
            actions_layout.addStretch()
            actions_widget.setLayout(actions_layout)
            self.schedules_table.setCellWidget(row, 5, actions_widget)
    
    def _create_interval_schedule(self):
        """Create a new interval schedule."""
        task_name = self.interval_task_combo.currentText()
        interval_value = self.interval_value.value()
        interval_unit = self.interval_unit.currentText()
        description = self.interval_description.text()
        
        try:
            task_id = self.task_scheduler.add_interval_task(
                task_name=f"{task_name} - Interval",
                task_function=self.available_tasks[task_name],
                interval_value=interval_value,
                interval_unit=interval_unit,
                description=description
            )
            
            QMessageBox.information(self, "Success", f"Schedule created successfully!\nTask ID: {task_id}")
            self._refresh_schedules()
            
            # Clear inputs
            self.interval_description.clear()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create schedule: {e}")
    
    def _create_cron_schedule(self):
        """Create a new cron schedule."""
        task_name = self.cron_task_combo.currentText()
        cron_expr = self.cron_expression.text().strip()
        description = self.cron_description.text()
        
        if not cron_expr:
            QMessageBox.warning(self, "Validation Error", "Please enter a cron expression")
            return
        
        try:
            task_id = self.task_scheduler.add_cron_task(
                task_name=f"{task_name} - Cron",
                task_function=self.available_tasks[task_name],
                cron_expression=cron_expr,
                description=description
            )
            
            QMessageBox.information(self, "Success", f"Schedule created successfully!\nTask ID: {task_id}")
            self._refresh_schedules()
            
            # Clear inputs
            self.cron_expression.clear()
            self.cron_description.clear()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create schedule: {e}")
    
    def _toggle_schedule(self, task_id: str, state):
        """Enable or disable a schedule."""
        if state:
            self.task_scheduler.enable_task(task_id)
        else:
            self.task_scheduler.disable_task(task_id)
    
    def _delete_schedule(self, task_id: str):
        """Delete a schedule."""
        reply = QMessageBox.question(
            self, "Confirm Delete",
            "Are you sure you want to delete this schedule?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.task_scheduler.remove_task(task_id)
            self._refresh_schedules()
    
    def _format_next_execution(self, dt) -> str:
        """Format next execution time."""
        now = datetime.now()
        diff = (dt - now).total_seconds()
        
        if diff < 60:
            return "in < 1 minute"
        elif diff < 3600:
            minutes = int(diff / 60)
            return f"in {minutes} minutes"
        elif diff < 86400:
            hours = int(diff / 3600)
            return f"in {hours} hours"
        else:
            days = int(diff / 86400)
            return f"in {days} days"
    
    # Task implementations
    def _task_file_scan(self):
        """File scan task."""
        # This would be provided by the application
        pass
    
    def _task_health_check(self):
        """Health check task."""
        self.task_manager.check_all_services_health()
    
    def _task_full_workflow(self):
        """Full workflow task."""
        # This would be provided by the application
        pass
    
    def closeEvent(self, event):
        """Clean up when widget is closed."""
        self.refresh_timer.stop()
        super().closeEvent(event)
