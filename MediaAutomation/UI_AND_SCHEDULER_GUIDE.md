# Media Automation System - User Interface & Scheduler Guide

## Overview

The Media Automation System provides a comprehensive PyQt6-based user interface with real-time status monitoring, task scheduling, and execution history tracking. The system is built around a professional dark theme and includes extensive status reporting capabilities.

## Features

### 1. **Real-Time Status Dashboard**
- Live task monitoring with progress indicators
- System status overview with color-coded indicators
- Service health status for all configured services
- System statistics (files scanned, distributed, uptime)
- Auto-refresh every 2 seconds

**Status Indicators:**
- 🟢 **Online** - Service is accessible
- 🔴 **Offline** - Service is unavailable
- 🟡 **Running** - Task is in progress
- 🟢 **Completed** - Task finished successfully
- 🔴 **Error** - Task or service has error

### 2. **Task Scheduler**

Two types of scheduling supported:

#### a. **Simple Interval Schedules**
Run tasks at regular intervals (e.g., every 2 hours, 30 minutes)

**Example:**
- "Every 2 hours" - Runs repeatedly every 2 hours
- "Every 30 minutes" - Runs repeatedly every 30 minutes
- "Every 1 day" - Runs once per day

#### b. **Cron Schedules**
Powerful cron-based scheduling for complex patterns

**Cron Expression Format:**
```
┌───────────── minute (0 - 59)
│ ┌───────────── hour (0 - 23)
│ │ ┌───────────── day of month (1 - 31)
│ │ │ ┌───────────── month (1 - 12)
│ │ │ │ ┌───────────── day of week (0 - 6) (0 = Sunday)
│ │ │ │ │
│ │ │ │ │
* * * * *
```

**Common Patterns:**

| Pattern | Meaning |
|---------|---------|
| `*/5 * * * *` | Every 5 minutes |
| `0 * * * *` | Every hour (at minute 0) |
| `0 0 * * *` | Daily at midnight |
| `0 12 * * *` | Daily at 12:00 PM |
| `0 0 * * MON` | Weekly on Monday at midnight |
| `0 2 * * MON-FRI` | 2:00 AM on weekdays |
| `0 */12 * * *` | Twice daily (every 12 hours) |
| `0 0 1 * *` | First day of each month |
| `0 0,6,12,18 * * *` | Four times daily (every 6 hours) |

**Day of Week:**
- 0 = Sunday
- 1 = Monday
- 2 = Tuesday
- 3 = Wednesday
- 4 = Thursday
- 5 = Friday
- 6 = Saturday

### 3. **Execution History & Logs**

View detailed execution records:

**Execution History Tab:**
- Task name and execution status
- Start and end times
- Execution duration
- Error messages (if any)
- Filter by status (all, completed, failed, running)
- Search by task name
- Clear history

**System Events Log:**
- All system events (task, service, file distribution, errors)
- Event timestamps and source
- Event type categorization
- Filter by type (task, service, file, error, system)
- Search events
- Clear event log

### 4. **Quick Actions**
- 🔍 **Service Health Check** - Check all services immediately
- ▶️ **Run Full Workflow** - Trigger scan → distribute → refresh media servers
- 📦 **Minimize to Tray** - Hide window to system tray

## Status Reporting System

The event system provides comprehensive status tracking:

### Event Types

| Event Type | Description | Example |
|-----------|-------------|---------|
| `TASK_STARTED` | Task execution began | File scan started |
| `TASK_PROGRESS` | Task progress update | 45/100 files distributed |
| `TASK_COMPLETED` | Task finished successfully | Distribution completed |
| `TASK_FAILED` | Task encountered error | Service health check failed |
| `SERVICE_ONLINE` | Service became available | Prowlarr online |
| `SERVICE_OFFLINE` | Service became unavailable | Radarr offline |
| `STATISTICS_UPDATED` | System stats updated | 1000 files scanned |
| `SYSTEM_STATUS_CHANGED` | Overall system status changed | Ready → Running Tasks |

### Accessing Status in Code

```python
from event_system import get_status_tracker, get_event_bus, EventType

# Get status tracker
status_tracker = get_status_tracker()

# Get current system status
system_status = status_tracker.get_system_status()
print(f"System: {system_status.value}")  # "ready", "running_tasks", "error", etc.

# Get all task statuses
tasks = status_tracker.get_all_task_statuses()
for task_id, task in tasks.items():
    print(f"{task.task_name}: {task.status} ({task.progress}%)")

# Get service statuses
services = status_tracker.get_all_service_statuses()
for service_name, service in services.items():
    status = "Online" if service.is_online else "Offline"
    print(f"{service.service_name}: {status}")

# Get statistics
stats = status_tracker.get_statistics()
print(f"Files scanned: {stats['total_files_scanned']}")
print(f"Total distributed size: {stats['total_distribution_size_gb']:.2f} GB")

# Subscribe to events
event_bus = get_event_bus()

def on_task_completed(event):
    print(f"Task {event.data['task_name']} completed!")

event_bus.subscribe(EventType.TASK_COMPLETED, on_task_completed)
```

## Configuration Examples

### config.json Setup

```json
{
  "scheduler": {
    "enable_health_check": true,
    "health_check_interval_minutes": 30,
    "enable_file_scanning": true,
    "file_scan_interval_minutes": 60,
    "enable_full_workflow": false
  },
  "file_distribution": {
    "input_directories": [
      "/mnt/media/incoming"
    ],
    "outputs": [
      {
        "path": "/mnt/storage1",
        "max_size_gb": 1000,
        "enabled": true
      },
      {
        "path": "/mnt/storage2",
        "max_size_gb": 1000,
        "enabled": true
      }
    ],
    "strategy": "EQUAL_SIZE"
  }
}
```

## Starting the Application

### Method 1: Direct Python Execution

```bash
# Navigate to MediaAutomation directory
cd d:\PythonLibraries\MediaAutomation

# Run the application
python media_automation_app.py
```

### Method 2: Create Shortcut (Windows)

Create `start_media_automation.bat`:
```batch
@echo off
cd /d d:\PythonLibraries\MediaAutomation
python media_automation_app.py
pause
```

### Method 3: Create Desktop Shortcut

1. Right-click desktop → New → Shortcut
2. Location: `C:\Python\python.exe`
3. Target: `C:\Python\python.exe d:\PythonLibraries\MediaAutomation\media_automation_app.py`
4. Name: "Media Automation System"

## Task Manager API

### Creating Tasks Programmatically

```python
from task_manager import TaskManager
from event_system import initialize_event_system

# Initialize system
event_bus, status_tracker = initialize_event_system()
task_manager = TaskManager(event_bus=event_bus, status_tracker=status_tracker)
task_scheduler = task_manager.get_scheduler()

# Create interval-based task
task_id = task_scheduler.add_interval_task(
    task_name="Backup Files",
    task_function=lambda: print("Backing up..."),
    interval_value=2,
    interval_unit="hours",
    description="Backup files every 2 hours"
)

# Create cron-based task
task_id = task_scheduler.add_cron_task(
    task_name="Midnight Cleanup",
    task_function=lambda: print("Cleaning..."),
    cron_expression="0 0 * * *",  # Daily at midnight
    description="Run cleanup at midnight"
)

# Start scheduler
task_scheduler.start()

# Schedule recurring workflows
task_manager.schedule_recurring_scan(scanner, interval_value=1, interval_unit="hours")
task_manager.schedule_service_health_check(interval_value=30, interval_unit="minutes")

# View scheduled tasks
tasks = task_scheduler.get_all_tasks()
for task_id, config in tasks.items():
    next_run = task_scheduler.get_next_execution_time(task_id)
    print(f"{config.task_name}: next run at {next_run}")

# Stop when done
task_scheduler.stop()
```

## Event Subscriptions

```python
from event_system import get_event_bus, EventType

event_bus = get_event_bus()

# Subscribe to task completion
def on_task_done(event):
    print(f"✓ {event.data['task_name']} completed in {event.data.get('duration')}s")

event_bus.subscribe(EventType.TASK_COMPLETED, on_task_done)

# Subscribe to service status changes
def on_service_status_change(event):
    service = event.data['service_name']
    status = "Online" if event.data['is_online'] else "Offline"
    print(f"Service {service} is now {status}")

event_bus.subscribe(EventType.SERVICE_ONLINE, on_service_status_change)
event_bus.subscribe(EventType.SERVICE_OFFLINE, on_service_status_change)

# Subscribe to statistics updates
def on_stats_updated(event):
    print(f"Stats updated: {event.data}")

event_bus.subscribe(EventType.STATISTICS_UPDATED, on_stats_updated)
```

## System Tray Integration

The application minimizes to system tray with right-click menu:

**Menu Options:**
- Show - Bring window to foreground
- Hide - Minimize to tray
- Run Health Check - Immediately check all services
- Exit - Close application

**Keyboard Shortcuts:**
- Double-click tray icon - Toggle window visibility
- Close window - Minimizes to tray instead of exiting

## UI Customization

### Changing Colors

Edit `gui/styles.py`:

```python
def get_color(color_name: str) -> str:
    """Get a color by name."""
    colors = {
        "background": "#1E1E1E",  # Dark background
        "accent": "#0078D4",      # Primary color (Microsoft blue)
        "success": "#28A745",     # Success (green)
        "error": "#DC3545",       # Error (red)
        "warning": "#FFC107",     # Warning (amber)
        # Add more colors as needed
    }
    return colors.get(color_name, "#E0E0E0")
```

### Light Theme (Optional)

Create `gui/light_theme.py` with light colors and apply with:
```python
self.setStyleSheet(LIGHT_STYLESHEET)
```

## Troubleshooting

### UI Doesn't Start
```bash
# Check Python version (require 3.9+)
python --version

# Check PyQt6 installation
pip list | grep PyQt6

# Install if missing
pip install PyQt6

# Run with verbose logging
set PYTHONVERBOSE=2
python media_automation_app.py
```

### Tasks Not Executing
1. Check that scheduler is running: `task_scheduler.is_running()`
2. Verify task function doesn't have errors
3. Check cron expression validity: `croniter("0 * * * *")`
4. Review logs in `media_automation.log`

### Status Not Updating
1. Check event subscriptions are active
2. Verify status tracker is initialized: `get_status_tracker()`
3. Manually trigger update: `status_tracker.update_task_status(...)`

### Performance Issues
1. Reduce widget refresh interval (in milliseconds)
2. Limit execution history size (default 500)
3. Clear old events periodically
4. Monitor memory usage: `import tracemalloc`

## Performance Metrics

**System Requirements:**
- CPU: 2+ cores (minimal usage, < 5% idle)
- RAM: 256 MB minimum (typically 100-200 MB)
- Disk: Log file ~1 MB per day

**Dashboard Refresh:**
- Status updates: Every 2 seconds
- Schedule table: Every 5 seconds
- Event processing: Real-time (< 1ms latency)

## API Reference

See individual module documentation:
- `event_system.py` - EventBus, StatusTracker
- `scheduler.py` - TaskScheduler, ScheduleConfig
- `task_manager.py` - TaskManager
- `gui/main_window.py` - MediaAutomationUI

## Future Enhancements

- [ ] Notifications/Alerts system
- [ ] Email reports of task execution
- [ ] Web dashboard for remote monitoring
- [ ] Task dependency chains
- [ ] Resource usage graphs
- [ ] Backup and restore schedules
- [ ] Advanced filtering in logs
- [ ] Custom dashboard widgets
- [ ] Multi-language support
