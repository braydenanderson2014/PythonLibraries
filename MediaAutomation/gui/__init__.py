"""
GUI module for media automation system.

Components:
- styles: Professional dark theme
- status_dashboard: Real-time status display
- task_scheduler_widget: Schedule creation and management
- logs_viewer: Execution history and event logs
- main_window: Main application window
"""

from .styles import DARK_STYLESHEET, get_color
from .status_dashboard import StatusDashboard
from .task_scheduler_widget import TaskSchedulerWidget
from .logs_viewer import LogsViewer
from .downloads_widget import DownloadsWidget
from .jobs_widget import JobsWidget
from .main_window import MediaAutomationUI

__all__ = [
    "DARK_STYLESHEET",
    "get_color",
    "StatusDashboard",
    "TaskSchedulerWidget",
    "LogsViewer",
    "DownloadsWidget",
    "JobsWidget",
    "MediaAutomationUI",
]
