# MediaAutomation

A modular media pipeline orchestrator for:

- Disc ripping (MakeMKV)
- Online/local ripper adapters (Tuneboto, Vidicable, DispCam, Flixicam, StreamFab)
- Encoding/transcoding (HandBrakeCLI)
- Subtitle processing (your Subtitle tool)
- PyQt6 desktop UI, with an internal web tools tab when WebEngine is installed
- Extensible adapters for additional tools via plugin modules

## Why this structure

This project is designed like a task orchestrator, not a single-purpose script. Each stage (ripper, subtitle, encoder) is an adapter behind a common interface, so you can add more tools without rewriting the whole workflow.

## Quick start

1. Create a starter config automatically if you do not have one yet:

```powershell
python main.py --new-config
```

2. Or copy `config.example.json` to `config.json` manually.
3. Update executable paths in `config.json`.
4. Edit jobs in `config.json`.
5. Run in dry mode first:

```powershell
python main.py --config config.json --dry-run
```

6. Run for real:

```powershell
python main.py --config config.json --run
```

7. Launch desktop UI:

```powershell
python main.py --config config.json --gui
```

GUI features:

- Pipeline tab: config selection, job picker, dry-run toggle, plugin imports, run logs
- Web tools tab: embedded browser view for internal/external web pages (if `PyQt6-WebEngine` is installed)

## Job model

Each job can define:

- `ripper` such as `makemkv`, `tuneboto`, `vidicable`, `dispcam`, `flixicam`, `streamfab`
- optional `ripper_candidates` list for fallback priority per job
- optional `subtitle_adapter` such as `subtitle_tool`
- `encoder` such as `handbrake`

The pipeline order is always:

1. Rip/acquire source media
2. Optional subtitle stage
3. Encode with final output

## Online ripper adapters

The following adapters are included as command stubs and should be adjusted to your local CLI syntax:

- `media_automation/adapters/tuneboto.py`
- `media_automation/adapters/vidicable.py`
- `media_automation/adapters/dispcam.py`
- `media_automation/adapters/flixicam.py`
- `media_automation/adapters/streamfab.py`

These tools are typically non-CLI desktop apps. The adapters now use a practical workflow:

1. Launch the desktop app (optionally with source URL)
2. On first use, wait for a sign-in checkpoint so you can maximize the app and verify account login
3. Wait for you to perform download actions in the app UI
4. Watch a configured download folder and detect the first completed media file
5. Pass that file into subtitle and encoding stages

For online jobs, the pipeline can try multiple rippers in priority order:

- `job.ripper_candidates` (if provided)
- otherwise `defaults.online_ripper_priority`
- then fallback to `job.ripper`

This lets you prioritize Vidicable/DispCam/Flixicam/StreamFab first and leave TuneBoto last.

Required config for non-CLI tools:

- `defaults.download_watch_dir` (or `job.metadata.download_watch_dir`)
- `defaults.download_timeout_sec`
- `defaults.download_stable_for_sec`
- `defaults.download_extensions`
- `defaults.launch_with_source_url`
- `defaults.online_ripper_priority`
- `defaults.first_use_signin_required`
- `defaults.first_use_signin_wait_sec`

Optional per-job metadata overrides:

- `download_watch_dir`
- `download_timeout_sec`
- `download_stable_for_sec`
- `download_extensions`
- `launch_with_source_url`
- `launch_args` (list of additional args)

Important:

- Some online services have DRM, legal restrictions, and anti-automation terms.
- Keep usage compliant with local law and the service terms.

## PyQt6 dependencies

Install GUI dependencies:

```powershell
pip install -r requirements.txt
```

If you skip `PyQt6-WebEngine`, the GUI still works and shows a fallback message in the web tab.

## Adding another ripper/encoder/subtitle tool

1. Create a new adapter class implementing one interface:
   - `RipperAdapter`
   - `SubtitleAdapter`
   - `EncoderAdapter`
2. Register it in `AdapterRegistry`, or expose it via plugin.

### Plugin loading

You can load external adapter modules at runtime:

```powershell
python main.py --config config.json --plugin my_media_plugins.my_register
```

Your plugin module must provide:

```python
def register(registry):
    registry.rippers["my_ripper"] = MyRipperAdapter()
```

## Notes for integrating your existing Subtitle project

## Servarr Stack Integration

MediaAutomation now integrates with the Servarr application stack for media library management:

- **Prowlarr** - Indexer aggregation and search
- **Sonarr** - TV show management and download automation
- **Radarr** - Movie management and download automation
- **Lidarr** - Music management and download automation
- **Readarr** - Book management and download automation

### Quick Setup

1. Update `config.json` with your Servarr service URLs and API keys:

```json
{
  "servarr": {
    "sonarr": {
      "base_url": "http://localhost:8989",
      "api_key": "your_api_key"
    },
    "radarr": {
      "base_url": "http://localhost:7878",
      "api_key": "your_api_key"
    }
  }
}
```

2. Test your connections:

```powershell
python test_servarr.py
```

3. See examples:

```powershell
python examples_servarr.py
```

### Documentation

- **[SERVARR_INTEGRATION.md](SERVARR_INTEGRATION.md)** - Complete integration guide and API examples
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - Implementation details and architecture
- **[config.servarr.example.json](config.servarr.example.json)** - Configuration template
- **[test_servarr.py](test_servarr.py)** - Connectivity testing script
- **[examples_servarr.py](examples_servarr.py)** - Working code examples

### Features

- Search and add content to Sonarr, Radarr, Lidarr, and Readarr
- Get library status and monitor collections
- Direct REST API access to all services
- Health checks for service connectivity
- Extensible architecture for additional operations

## Media Servers & File Distribution

NEW: Automatic file scanning and distribution with intelligent load balancing, plus media server integrations:

- **Plex Media Server** - Centralized media management and streaming
- **Jellyfin** - Open-source media server alternative  
- **qBittorrent** - Torrent client with WebUI REST API
- **FileDistributor** - Route files to multiple outputs with load balancing
- **FileScanner** - Automatic input directory monitoring and file detection

### Key Features

- **Load Balancing Strategies**: EQUAL_SIZE, LEAST_USED, ROUND_ROBIN, RANDOM
- **Multi-Output Support**: Distribute files across multiple storage devices
- **Automatic Scanning**: Watch directories and process new files
- **Capacity Management**: Enforce per-output size limits
- **Rebalancing Detection**: Identify when storage is imbalanced
- **Media Server Integration**: Trigger library scans on Plex, Jellyfin after distribution

### Quick Start

```python
from media_automation.file_distribution import FileDistributionPipeline, OutputFolder, DistributionStrategy
from pathlib import Path

# Setup outputs with load balancing
outputs = [
    OutputFolder(Path("/output1"), max_size_gb=500),
    OutputFolder(Path("/output2"), max_size_gb=500),
    OutputFolder(Path("/output3"), max_size_gb=500),
]

# Create auto-scanning pipeline
pipeline = FileDistributionPipeline(
    input_paths="/input",
    output_folders=outputs,
    strategy=DistributionStrategy.EQUAL_SIZE,
    extensions=[".mkv", ".mp4"]
)

# Start automatic monitoring and distribution
pipeline.start()
```

### Documentation

- **[MEDIA_SERVERS_AND_DISTRIBUTION.md](MEDIA_SERVERS_AND_DISTRIBUTION.md)** - Complete guide with all strategies and configurations
- **[examples_distribution.py](examples_distribution.py)** - 8 working examples covering all use cases

### Notes for integrating your existing Subtitle project



Current subtitle stage command is a placeholder call:

```text
python Subtitle/main.py --input <in> --output <out> --profile <profile>
```

Update `media_automation/adapters/subtitle_tool.py` to match your real subtitle CLI arguments and script path.

## Real-Time Status Dashboard & Task Scheduling

NEW: Professional PyQt6 user interface with real-time status monitoring, task scheduling, and execution history tracking.

### Features

- **Real-Time Status Dashboard**: Live task monitoring with progress bars, system health overview, service status
- **Task Scheduling**: Both simple intervals (every X hours) and cron expressions (e.g., "0 */12 * * *")
- **Event System**: Comprehensive event bus with subscriber pattern for task and service events
- **Status Tracking**: Central status tracker reporting on all tasks, services, and system statistics
- **Execution History**: View detailed task execution records with start/end times and duration
- **System Tray**: Minimize to system tray with quick-access menu
- **Professional Dark Theme**: Microsoft-style dark UI with blue accents

### Quick Start

1. Install UI dependencies:

```powershell
pip install -r requirements_ui_scheduler.txt
```

2. Start the application:

```powershell
python media_automation_app.py
```

3. The UI will show:
   - **Status Dashboard** - Real-time task progress and service health
   - **Task Scheduler** - Create interval or cron-based schedules
   - **Logs & History** - View task execution records and system events
   - Quick action buttons for running tasks immediately

### Scheduling Examples

**Simple Intervals:**
- Every 30 minutes
- Every 2 hours
- Every 1 day

**Cron Expressions:**
- `*/5 * * * *` - Every 5 minutes
- `0 * * * *` - Every hour
- `0 0 * * *` - Daily at midnight
- `0 0 * * MON` - Weekly on Monday
- `0 2 * * MON-FRI` - 2 AM on weekdays
- `0 */12 * * *` - Twice daily

### Status Reporting

Access system status programmatically:

```python
from event_system import get_status_tracker, get_event_bus, EventType

status_tracker = get_status_tracker()

# Get current task statuses
tasks = status_tracker.get_all_task_statuses()
for task_id, task in tasks.items():
    print(f"{task.task_name}: {task.status} ({task.progress}%)")

# Get service health
services = status_tracker.get_all_service_statuses()
for service_name, service in services.items():
    print(f"{service.service_name}: {'Online' if service.is_online else 'Offline'}")

# Submit to events
event_bus = get_event_bus()
event_bus.subscribe(EventType.TASK_COMPLETED, my_callback_function)
```

### Documentation

- **[UI_AND_SCHEDULER_GUIDE.md](UI_AND_SCHEDULER_GUIDE.md)** - Complete user interface and scheduler guide
- **[examples_ui_scheduler.py](examples_ui_scheduler.py)** - 5 detailed examples showing all features
- **[requirements_ui_scheduler.txt](requirements_ui_scheduler.txt)** - UI and scheduler dependencies

### Components

- `event_system.py` - Event bus and status tracking
- `scheduler.py` - Task scheduling with intervals and cron
- `task_manager.py` - Central task orchestrator
- `gui/` - PyQt6 user interface components
  - `styles.py` - Professional dark theme
  - `status_dashboard.py` - Real-time status display
  - `task_scheduler_widget.py` - Schedule creation and management
  - `logs_viewer.py` - Execution history and event logs
  - `main_window.py` - Main application window
- `media_automation_app.py` - Application launcher

## Architecture

- `main.py`: entry point
- `media_automation/cli.py`: argument parsing and run flow
- `media_automation/gui.py`: PyQt6 desktop UI
- `media_automation/app_runner.py`: shared execution service used by CLI and GUI
- `media_automation/pipeline.py`: stage orchestration
- `media_automation/adapters/*`: tool-specific adapters
- `config.example.json`: starter config
