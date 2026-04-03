# Media Automation System - Quick Reference

## Starting the System

### GUI Application
```bash
python media_automation_app.py
```

### Programmatically
```python
from event_system import initialize_event_system
from task_manager import TaskManager

event_bus, status_tracker = initialize_event_system()
task_manager = TaskManager(event_bus, status_tracker)
task_manager.start()
```

## Adding a Scheduled Task

### Simple Interval (Every X time)
```python
from event_system import get_event_bus, get_status_tracker
from scheduler import TaskScheduler

scheduler = TaskScheduler()

task_id = scheduler.add_interval_task(
    task_name="My Task",
    task_function=my_function,
    interval_value=2,
    interval_unit="hours"  # "minutes", "hours", or "days"
)

scheduler.start()
```

### Cron Expression (Complex Patterns)
```python
scheduler = TaskScheduler()

task_id = scheduler.add_cron_task(
    task_name="Daily Task",
    task_function=my_function,
    cron_expression="0 2 * * *"  # 2 AM daily
)

scheduler.start()
```

### Common Cron Patterns
```
*/5 * * * *       → Every 5 minutes
0 * * * *         → Every hour
0 0 * * *         → Daily at midnight
0 0 * * MON       → Weekly on Monday
0 2 * * MON-FRI   → 2 AM on weekdays
0 */12 * * *      → Twice daily (every 12 hours)
0 0 1 * *         → First day of month
```

## Reporting Task Status

### Update Status
```python
from event_system import get_status_tracker

tracker = get_status_tracker()

# Task running
tracker.update_task_status(
    task_id="task-1",
    task_name="File Scan",
    status="running",
    progress=50.0,
    processed_items=50,
    total_items=100
)

# Task completed
tracker.update_task_status(
    task_id="task-1",
    task_name="File Scan",
    status="completed"
)

# Task failed
tracker.update_task_status(
    task_id="task-1",
    task_name="File Scan",
    status="error",
    error_message="Connection timeout"
)
```

### Get Status
```python
tracker = get_status_tracker()

# Get single task
task = tracker.get_task_status("task-1")
print(f"{task.task_name}: {task.status} ({task.progress}%)")

# Get all tasks
tasks = tracker.get_all_task_statuses()
for task_id, task in tasks.items():
    print(f"{task.task_name}: {task.status}")

# Get system status
system_status = tracker.get_system_status()
print(f"System: {system_status.value}")
```

## Tracking Service Health

### Update Service Status
```python
tracker = get_status_tracker()

# Service online
tracker.update_service_status(
    service_name="Prowlarr",
    service_type="indexer",
    is_online=True,
    response_time_ms=125
)

# Service offline
tracker.update_service_status(
    service_name="Radarr",
    service_type="download_manager",
    is_online=False,
    response_time_ms=0,
    error_message="Connection refused"
)
```

### Get Service Status
```python
tracker = get_status_tracker()

# Get single service
service = tracker.get_service_status("Prowlarr")
if service.is_online:
    print(f"✓ Online ({service.response_time_ms}ms)")
else:
    print(f"✗ Offline: {service.error_message}")

# Get all services
services = tracker.get_all_service_statuses()
for service_name, service in services.items():
    print(f"{service.service_name}: {service.service_type}")
```

## Subscribing to Events

### Subscribe to Events
```python
from event_system import get_event_bus, EventType

event_bus = get_event_bus()

# Task completed
def on_complete(event):
    print(f"✓ {event.data['task_name']} done!")

event_bus.subscribe(EventType.TASK_COMPLETED, on_complete)

# Task failed
def on_error(event):
    print(f"✗ {event.data['task_name']}: {event.data['error_message']}")

event_bus.subscribe(EventType.TASK_FAILED, on_error)

# Service status changed
def on_service_change(event):
    status = "Online" if event.data['is_online'] else "Offline"
    print(f"{event.data['service_name']}: {status}")

event_bus.subscribe(EventType.SERVICE_ONLINE, on_service_change)
event_bus.subscribe(EventType.SERVICE_OFFLINE, on_service_change)

# Statistics updated
def on_stats(event):
    files = event.data.get('total_files_scanned', 0)
    print(f"Now tracking {files} files")

event_bus.subscribe(EventType.STATISTICS_UPDATED, on_stats)
```

### Available Event Types
```python
EventType.TASK_STARTED              # Task execution began
EventType.TASK_PROGRESS             # Task progress update
EventType.TASK_COMPLETED            # Task finished successfully
EventType.TASK_FAILED               # Task encountered error
EventType.SERVICE_ONLINE            # Service became available
EventType.SERVICE_OFFLINE           # Service became unavailable
EventType.FILE_SCANNED              # File was scanned
EventType.FILE_DISTRIBUTED          # File was distributed
EventType.STATISTICS_UPDATED        # System stats updated
EventType.SYSTEM_STATUS_CHANGED     # Overall system status changed
EventType.ERROR_OCCURRED            # System error
```

## Tracking System Statistics

### Update Statistics
```python
tracker = get_status_tracker()

tracker.update_statistics(
    total_files_scanned=100,
    total_files_distributed=95,
    total_distribution_size_gb=50.2
)

# Or increment
tracker.increment_statistic("total_files_scanned", 5)
tracker.increment_statistic("total_files_distributed", 1)
tracker.increment_statistic("total_distribution_size_gb", 2.5)
```

### Get Statistics
```python
tracker = get_status_tracker()

stats = tracker.get_statistics()
print(f"Files scanned: {stats['total_files_scanned']}")
print(f"Distribution size: {stats['total_distribution_size_gb']:.2f} GB")
```

## Task Manager Workflows

### Schedule Recurring Scan
```python
task_manager = TaskManager()
task_id = task_manager.schedule_recurring_scan(
    scanner,
    interval_value=1,
    interval_unit="hours"
)
```

### Schedule Health Checks
```python
task_id = task_manager.schedule_service_health_check(
    interval_value=30,
    interval_unit="minutes"
)
```

### Check Services Now
```python
task_manager.check_all_services_health()
```

### Execute Full Workflow
```python
task_manager.execute_full_workflow(
    scanner=scanner,
    distributor=distributor,
    trigger_media_scan=True
)
```

## Configuration Examples

### config.json Scheduler Settings
```json
{
  "scheduler": {
    "enable_health_check": true,
    "health_check_interval_minutes": 30,
    "enable_file_scanning": true,
    "file_scan_interval_minutes": 60,
    "enable_full_workflow": false
  }
}
```

## File Locations

| Component | File | Purpose |
|-----------|------|---------|
| Event System | `event_system.py` | Event bus and status tracking |
| Scheduler | `scheduler.py` | Task scheduling (intervals + cron) |
| Task Manager | `task_manager.py` | Central task orchestrator |
| App Launcher | `media_automation_app.py` | Start the full UI |
| Styles | `gui/styles.py` | UI theme and colors |
| Dashboard | `gui/status_dashboard.py` | Real-time status display |
| Task Scheduler Widget | `gui/task_scheduler_widget.py` | Schedule management UI |
| Logs Viewer | `gui/logs_viewer.py` | Execution history viewer |
| Main Window | `gui/main_window.py` | Main application window |

## Status Values

### Task Status
- `"idle"` - Not running
- `"running"` - Currently executing
- `"completed"` - Finished successfully
- `"error"` - Encountered an error
- `"cancelled"` - Was cancelled
- `"paused"` - Paused (reserved)

### System Status
- `"initializing"` - Starting up
- `"ready"` - Ready for tasks
- `"running_tasks"` - One or more tasks executing
- `"error"` - System error occurred
- `"stopped"` - System stopped

## Common Patterns

### Pattern 1: Simple Recurring Task
```python
scheduler = TaskScheduler()
task_id = scheduler.add_interval_task(
    "Backup",
    backup_function,
    interval_value=1,
    interval_unit="days"
)
scheduler.start()
```

### Pattern 2: Complex Cron Pattern
```python
scheduler = TaskScheduler()
# Run Monday-Friday at 9 AM
task_id = scheduler.add_cron_task(
    "Work Hours Task",
    work_function,
    cron_expression="0 9 * * MON-FRI"
)
scheduler.start()
```

### Pattern 3: Status Reporting with Events
```python
tracker = get_status_tracker()

# Do some work
tracker.update_task_status("my-task", "My Task", "running", progress=0)
# ... work ...
tracker.update_task_status("my-task", "My Task", "running", progress=50)
# ... more work ...
tracker.update_task_status("my-task", "My Task", "completed", progress=100)

# Automatically publishes events; subscribers are notified
```

### Pattern 4: Health Check Loop
```python
def check_health():
    tracker = get_status_tracker()
    for service_name, adapter in services.items():
        try:
            adapter.health_check()
            tracker.update_service_status(
                service_name, "...", True, 100
            )
        except Exception as e:
            tracker.update_service_status(
                service_name, "...", False, 0, str(e)
            )

task_manager.scheduler.add_interval_task(
    "Health Check",
    check_health,
    interval_value=30,
    interval_unit="minutes"
)
```

## Troubleshooting

### Task Not Running?
1. Check if scheduler is running: `scheduler.is_running()`
2. Verify next execution time: `scheduler.get_next_execution_time(task_id)`
3. Check task is enabled: `task.enabled`
4. Validate cron expression: `croniter("0 * * * *")`

### Status Not Updating?
1. Verify tracker initialized: `get_status_tracker()`
2. Check event subscriptions: `event_bus._subscribers`
3. Manually trigger: `tracker.update_task_status(...)`

### UI Not Starting?
1. Check PyQt6 installed: `pip list | grep PyQt6`
2. Check for import errors: `python -c "from PyQt6.QtWidgets import QApplication"`
3. Review log file: `media_automation.log`

## Documentation Files

- **UI_AND_SCHEDULER_GUIDE.md** - Complete user guide
- **UI_SCHEDULER_IMPLEMENTATION_SUMMARY.md** - Architecture and design
- **examples_ui_scheduler.py** - 5 detailed examples
- **requirements_ui_scheduler.txt** - Dependencies
- **README.md** - Project overview (updated)
