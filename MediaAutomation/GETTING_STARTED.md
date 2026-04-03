# Getting Started - Media Automation System UI & Scheduling

## Welcome!

Your Media Automation System now has a complete user-friendly interface with real-time status reporting and task scheduling capabilities.

## What You Can Do Now

### 1. **Monitor Everything** 👁️
The real-time status dashboard shows:
- What tasks are currently running
- Progress bars for ongoing operations  
- Which services are online/offline
- System statistics (files scanned, distributed, storage used)
- All updates happen in real-time

### 2. **Schedule Anything** 📅
Set up automated tasks to run:
- **Simple intervals**: Every 2 hours, every 30 minutes, every day
- **Complex patterns**: Specific times (e.g., 2 AM daily), multiple days (Monday-Friday), custom schedules
- Enable/disable schedules without deleting them
- View when each task will next run

### 3. **Track Everything** 📝
View complete history of:
- Every task that ran (start time, duration, result)
- All system events (tasks, services, errors)
- Error messages and details
- Search and filter to find what you need

## Quick Start (5 Minutes)

### Step 1: Install Requirements
```bash
pip install -r requirements_ui_scheduler.txt
```

### Step 2: Start the Application
```bash
python media_automation_app.py
```

You'll see:
- A splash screen showing startup progress
- Then the main window with 3 tabs:
  - **Status Dashboard** - What's happening right now
  - **Task Scheduler** - Create new automated tasks
  - **Logs & History** - Records of past tasks and events

### Step 3: Create Your First Schedule

1. Go to **Task Scheduler** tab
2. Click **Interval Schedule** tab (or **Cron Schedule** for advanced)
3. Select a task from the dropdown
4. Set the interval (e.g., "Every 2 hours")
5. Click **✓ Create Schedule**

That's it! The task will now run automatically.

## Important Features

### Real-Time Dashboard
Shows:
- ✓ Completed tasks (green)
- ⊙ Running tasks (blue) 
- ✗ Failed tasks (red)
- Current progress with file counts
- Service status (online/offline)
- System statistics

Updates automatically every 2 seconds.

### Status Reporting
The system automatically reports:
- When a task starts, progresses, completes, or fails
- When a service comes online or goes offline
- Updated statistics (files scanned, distributed, etc.)
- All events with timestamps

You can see all of this in:
1. **Status Dashboard** tab (live view)
2. **Logs & History** → **System Events** tab (historical view)

### Task Scheduling
Two ways to schedule:

**Method 1: Simple Intervals**
```
Every 30 minutes
Every 2 hours  
Every 1 day
```
Best for regular, repeating tasks.

**Method 2: Cron Expressions**
```
*/5 * * * *        → Every 5 minutes
0 * * * *          → Every hour
0 0 * * *          → Daily at midnight
0 2 * * *          → Daily at 2 AM
0 0 * * MON        → Weekly on Monday
0 2 * * MON-FRI    → 2 AM on weekdays
0 */12 * * *       → Twice daily
```
Best for complex schedules.

## Common Use Cases

### Use Case 1: Monitor Services Regularly
```
Create a "Service Health Check" task
Set to: Every 30 minutes
Result: Services checked automatically, status updated in dashboard
```

### Use Case 2: Scan for New Files Daily
```
Create a "File Scan" task
Set to: Cron expression "0 0 * * *" (daily at midnight)
Result: New files detected and processed automatically
```

### Use Case 3: Run Full Workflow Weekly
```
Create a "Full Workflow" task
Set to: Cron expression "0 2 * * MON" (Monday at 2 AM)
Result: Scan → Distribute → Update media servers automatically
```

## Understanding the Dashboard

### Status Card
Shows overall system status:
- **Ready** - System initialized and ready for tasks
- **Running Tasks** - One or more tasks currently executing
- **Error** - System encountered an error (check logs)

### Active Tasks Section
Shows each running task with:
- Task name and status badge
- Progress bar (if applicable)
- Current item being processed
- Error message (if failed)

### Service Status Table
Shows health of all configured services:
- Service name
- Service type (indexer, download manager, media server)
- Online/Offline status with checkmark or X
- Last check time

### Statistics Section
Shows aggregated system metrics:
- Files scanned
- Files distributed
- Total size distributed
- Tasks completed
- Tasks failed

## Accessing System Status Programmatically

If you want to check status in your own code:

```python
from event_system import get_status_tracker, get_event_bus, EventType

# Get the tracker
tracker = get_status_tracker()

# Check what's running
tasks = tracker.get_all_task_statuses()
for task_id, task in tasks.items():
    if task.status == "running":
        print(f"Running: {task.task_name} ({task.progress}%)")

# Check services
services = tracker.get_all_service_statuses()
for name, service in services.items():
    status = "✓ Online" if service.is_online else "✗ Offline"
    print(f"{name}: {status}")

# Get stats
stats = tracker.get_statistics()
print(f"Total: {stats['total_files_scanned']} files scanned")

# Subscribe to updates
event_bus = get_event_bus()

def on_task_done(event):
    print(f"✓ {event.data['task_name']} completed!")

event_bus.subscribe(EventType.TASK_COMPLETED, on_task_done)
```

## UI Customization

### Minimize to System Tray
Click "📦 Minimize to Tray" button to hide the window.

**From Tray:**
- Double-click icon to show/hide
- Right-click for menu (Show, Hide, Run Health Check, Exit)

### Tabs

**Status Dashboard:**
- What's happening right now
- Real-time updates every 2 seconds
- Refresh manually with F5

**Task Scheduler:**
- Create new schedules (interval or cron)
- View all scheduled tasks
- Enable/disable existing schedules
- Delete schedules
- See next execution time

**Logs & History:**
- Execution History - Task records with duration
- System Events - All system events
- Filter and search in both
- Clear history if needed

## Troubleshooting

### Tasks Not Executing?
1. Check if scheduler is running (see status bar)
2. Look at **Logs & History** for errors
3. Make sure task is **enabled** in **Task Scheduler**
4. Check cron expression syntax if using cron

### Status Not Updating?
1. Dashboard refreshes every 2 seconds, give it a moment
2. Click **Logs & History** tab to see full event log
3. Check if tasks are actually running (should see in Active Tasks section)

### Application Won't Start?
1. Make sure PyQt6 is installed: `pip install PyQt6`
2. Check Python version (3.9+): `python --version`
3. Review `media_automation.log` file for error details

### Service Shows Offline?
1. Check service is actually running
2. Verify configuration in `config.json`
3. Check network connectivity
4. Look at error message in service status
5. Check **Logs & History** → **System Events** for details

## System Tray Integration

The system tray icon (in bottom-right corner) provides quick access:

**Right-Click Menu:**
- **Show** - Bring window to foreground
- **Hide** - Minimize to tray
- **Run Health Check** - Immediately check all services
- **Exit** - Close application (stops scheduled tasks)

**Double-Click:**
- Toggle window visibility

## Keyboard Shortcuts

While application is running:
- **F5** - Refresh status dashboard
- **Alt+Tab** - Switch applications
- **Alt+F4** - Close window (minimizes to tray)

## Configuration

The system loads `config.json` for default settings:

```json
{
  "scheduler": {
    "enable_health_check": true,
    "health_check_interval_minutes": 30,
    "enable_file_scanning": true,
    "file_scan_interval_minutes": 60
  }
}
```

Change these to auto-enable certain schedules when the app starts.

## Documentation

Read these for more details:

| Document | Purpose |
|----------|---------|
| **UI_AND_SCHEDULER_GUIDE.md** | Complete guide with all features |
| **QUICK_REFERENCE.md** | Developer cheat sheet |
| **UI_SCHEDULER_IMPLEMENTATION_SUMMARY.md** | Technical architecture |
| **examples_ui_scheduler.py** | Working code examples |

## Next Steps

1. ✅ **Right now** - Start the app and explore the UI
2. 📅 **Create a schedule** - Try creating your first automated task
3. 📝 **Check the logs** - See completed tasks in history
4. 📖 **Read the guides** - Learn about cron expressions and advanced usage
5. 🔌 **Integrate** - Use the API to add custom tasks

## Support

### Common Questions

**Q: How do I know if my schedule is working?**
A: Check **Task Scheduler** for next execution time, or go to **Logs & History** to see completion records.

**Q: Can I edit a schedule I just created?**
A: Currently, delete and recreate it. Or disable it and create a new one.

**Q: What happens when I close the app?**
A: Scheduled tasks stop running. Open the app again to resume.

**Q: Can I run tasks without the UI?**
A: Yes! Use `examples_ui_scheduler.py` for programmatic API usage.

**Q: How often does the dashboard update?**
A: Every 2 seconds automatically (configurable in code).

## Summary

You now have:
- ✅ Real-time status monitoring
- ✅ Simple and advanced task scheduling
- ✅ Complete execution history
- ✅ System tray integration
- ✅ Professional dark UI
- ✅ Comprehensive event reporting

**Enjoy automated media management!** 🎉

---

For questions or issues, see:
- **QUICK_REFERENCE.md** - Quick answers
- **UI_AND_SCHEDULER_GUIDE.md** - Detailed guide
- **examples_ui_scheduler.py** - Working examples
