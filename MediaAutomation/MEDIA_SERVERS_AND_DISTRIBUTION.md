# Media Servers and File Distribution Guide

This guide covers the new media server integrations (Plex, Jellyfin, qBittorrent) and modular file scanning/distribution system with load balancing.

## Media Server Adapters

### Plex Media Server

Plex is a centralized media server for organizing and streaming your media collection.

#### Setup

1. Install Plex Media Server from https://www.plex.tv/
2. Access web interface at `http://localhost:32400`
3. Generate API token in Settings → Account → Auth token

#### Configuration

```json
{
  "media_servers": {
    "plex": {
      "base_url": "http://localhost:32400",
      "api_key": "your_plex_token"
    }
  }
}
```

#### Usage

```python
from media_automation.adapters.factory import AdapterRegistry

registry = AdapterRegistry()
plex = registry.get_media_server("plex")
plex.client = PlexAPIClient("http://localhost:32400", "your_token")

# Get libraries
libraries = plex.get_libraries()
print(f"Found {len(libraries['libraries'])} libraries")

# Trigger library scan
if plex.scan_library("1"):  # Library ID
    print("Scan triggered")

# Get library contents
contents = plex.get_library_contents("1")
```

### Jellyfin Media Server

Jellyfin is an open-source media server alternative to Plex.

#### Setup

1. Install Jellyfin: https://jellyfin.org/
2. Access web interface at `http://localhost:8096`
3. Generate API key in Settings → API Keys

#### Configuration

```json
{
  "media_servers": {
    "jellyfin": {
      "base_url": "http://localhost:8096",
      "api_key": "your_jellyfin_api_key"
    }
  }
}
```

#### Usage

```python
from media_automation.adapters.jellyfin import JellyfinAdapter

jellyfin = JellyfinAdapter("http://localhost:8096", "your_api_key")

# Search for content
results = jellyfin.search_items("Breaking Bad")
print(f"Found {results['result_count']} results")

# Get library contents
contents = jellyfin.get_library_contents("library_id")
```

### qBittorrent Torrent Client

qBittorrent is a lightweight torrent client with a WebUI API.

#### Setup

1. Install qBittorrent: https://www.qbittorrent.org/
2. Enable WebUI: Preferences → Web UI (typically port 8080)
3. Default credentials: admin / adminadmin

#### Configuration

```json
{
  "download_managers": {
    "qbittorrent": {
      "base_url": "http://localhost:8080",
      "username": "admin",
      "password": "your_password"
    }
  }
}
```

#### Usage

```python
from media_automation.adapters.qbittorrent import QBittorrentAdapter

qb = QBittorrentAdapter("http://localhost:8080", "admin", "password")

# Add torrent from magnet link
entry = {"url": "magnet:?xt=urn:btih:...", "save_path": "/downloads/movies"}
if qb.add_entry(entry):
    print("Torrent added")

# Get status
status = qb.get_library_status()
print(f"Active: {status['downloading']}, Completed: {status['completed']}")
```

## File Distribution System

MediaAutomation now includes a modular file scanning and distribution system with intelligent load balancing.

### Components

#### FileScanner
Watches input directories and detects new media files.

#### FileDistributor
Distributes files to multiple output folders with configurable load balancing strategies.

#### FileDistributionPipeline
Combined auto-scanning and distribution pipeline.

### Load Balancing Strategies

1. **ROUND_ROBIN**: Cycle through outputs in order
2. **LEAST_USED**: Always use the output with fewest files
3. **EQUAL_SIZE**: Balance by total folder size
4. **RANDOM**: Random output selection

### Basic Usage

#### Simple File Distribution

```python
from pathlib import Path
from media_automation.file_distribution import (
    FileDistributor,
    OutputFolder,
    DistributionStrategy,
)

# Define output folders
outputs = [
    OutputFolder(Path("/output1"), max_size_gb=500),
    OutputFolder(Path("/output2"), max_size_gb=500),
    OutputFolder(Path("/output3"), max_size_gb=500),
]

# Create distributor with load balancing
distributor = FileDistributor(
    outputs,
    strategy=DistributionStrategy.EQUAL_SIZE,
    copy_mode=True,  # True=copy, False=move
)

# Distribute a file
dest = distributor.distribute_file(Path("/input/movie.mkv"))
if dest:
    print(f"File copied to {dest}")

# Check load status
status = distributor.get_load_status()
for output_info, stats in status.items():
    print(f"{stats['path']}: {stats['current_size_gb']:.2f}GB")
```

#### Automatic Scanning and Distribution

```python
from media_automation.file_distribution import FileDistributionPipeline

# Create pipeline that auto-scans and distributes
pipeline = FileDistributionPipeline(
    input_paths="/input",
    output_folders=outputs,
    extensions=[".mkv", ".mp4"],
    scan_interval=5,  # Scan every 5 seconds
    strategy=DistributionStrategy.EQUAL_SIZE,
    copy_mode=False,  # Move files instead of copying
)

# Define callback for each distributed file
def on_file_distributed(scanned_file, destination):
    if destination:
        print(f"✓ {scanned_file.path.name} → {destination}")
    else:
        print(f"✗ {scanned_file.path.name} (failed)")

# Start pipeline
pipeline.start(callback=on_file_distributed)

# ... let it run ...

# Get statistics
stats = pipeline.get_stats()
print(f"Processed: {stats['processed_files']}/{stats['scanned_files']}")
print(f"Rebalance needed: {stats['rebalance_needed']}")

# Stop pipeline
pipeline.stop()
```

#### Configuration in config.json

```json
{
  "file_distribution": {
    "input_paths": ["/input", "/downloads"],
    "output_folders": {
      "primary": {
        "path": "/output1",
        "max_size_gb": 500,
        "enabled": true
      },
      "secondary": {
        "path": "/output2",
        "max_size_gb": 500,
        "enabled": true
      },
      "overflow": {
        "path": "/output3",
        "max_size_gb": 1000,
        "enabled": true
      }
    },
    "scan_interval": 5,
    "strategy": "equal_size",
    "copy_mode": false,
    "extensions": [".mkv", ".mp4", ".avi", ".mov"]
  }
}
```

### Advanced Usage

#### Multi-Tier Distribution

```python
# Separate storage for different media types
video_outputs = [
    OutputFolder(Path("/nvme/videos"), max_size_gb=1000),  # Fast storage
    OutputFolder(Path("/ssd/videos"), max_size_gb=2000),   # Slower backup
]

video_dist = FileDistributor(video_outputs, strategy=DistributionStrategy.EQUAL_SIZE)

# Music on separate system
music_outputs = [
    OutputFolder(Path("/nas/music"), max_size_gb=500),
]

music_dist = FileDistributor(music_outputs)

# Route files based on extension
def smart_distribute(file_path):
    if file_path.suffix.lower() in [".mkv", ".mp4"]:
        return video_dist.distribute_file(file_path)
    elif file_path.suffix.lower() in [".flac", ".mp3"]:
        return music_dist.distribute_file(file_path)
    else:
        return video_dist.distribute_file(file_path)  # Default
```

#### Rebalancing Strategy

```python
distributor = FileDistributor(outputs, strategy=DistributionStrategy.EQUAL_SIZE)

# Periodically check if rebalancing is needed
import time

while True:
    if distributor.rebalance_if_needed():
        status = distributor.get_load_status()
        max_load = max(s['current_size_gb'] for s in status.values())
        min_load = min(s['current_size_gb'] for s in status.values())
        print(f"Imbalance detected: {max_load:.2f}GB vs {min_load:.2f}GB")
        print("Consider redistributing files or adding outputs")
    
    time.sleep(3600)  # Check hourly
```

#### Monitor and React to Capacity

```python
def on_file_distributed(scanned_file, destination):
    if destination is None:
        print(f"⚠ No output could fit {scanned_file.size_bytes / 1e9:.2f}GB file")
        # Could trigger alerts, stop processing, or request user action
    else:
        print(f"✓ Distributed to {destination}")

pipeline = FileDistributionPipeline(
    input_paths="/input",
    output_folders=outputs,
    strategy=DistributionStrategy.LEAST_USED,
)

pipeline.start(callback=on_file_distributed)
```

## Combined Workflow Example

Integrate scanning, distribution, and media servers:

```python
from pathlib import Path
from media_automation.file_distribution import (
    FileDistributionPipeline,
    OutputFolder,
    DistributionStrategy,
)
from media_automation.adapters.factory import AdapterRegistry

# Setup file distribution
outputs = [
    OutputFolder(Path("/movies1"), max_size_gb=1000),
    OutputFolder(Path("/movies2"), max_size_gb=1000),
]

pipeline = FileDistributionPipeline(
    input_paths=["/ripped_media", "/downloads"],
    output_folders=outputs,
    extensions=[".mkv", ".mp4"],
    strategy=DistributionStrategy.EQUAL_SIZE,
    copy_mode=False,
)

# Setup media servers
registry = AdapterRegistry()
plex = registry.get_media_server("plex")
jellyfin = registry.get_media_server("jellyfin")

# Configure clients
from media_automation.adapters.media_servers_base import PlexAPIClient, JellyfinAPIClient
plex.client = PlexAPIClient("http://localhost:32400", "plex_token")
jellyfin.client = JellyfinAPIClient("http://localhost:8096", "jellyfin_key")

# Callback: Distribute file and trigger library scans
def on_file_processed(scanned_file, destination):
    if destination:
        print(f"✓ {scanned_file.path.name} distributed")
        
        # Trigger both media servers to rescan
        if plex.scan_library("1"):  # Movies library
            print("  → Plex scan triggered")
        if jellyfin.scan_library("movie_library_id"):
            print("  → Jellyfin scan triggered")
    else:
        print(f"✗ {scanned_file.path.name} distribution failed")

# Start pipeline
pipeline.start(callback=on_file_processed)

# Monitor
try:
    while True:
        stats = pipeline.get_stats()
        print(f"\nStatus: {stats['processed_files']} processed")
        
        if stats['rebalance_needed']:
            print("⚠ Rebalancing recommended")
        
        import time
        time.sleep(60)
except KeyboardInterrupt:
    pipeline.stop()
    print("\nShutdown complete")
```

## Health Checks and Testing

```python
from media_automation.adapters.factory import AdapterRegistry
from media_automation.adapters.media_servers_base import (
    PlexAPIClient,
    JellyfinAPIClient,
    QBittorrentAPIClient,
)

def check_all_services():
    registry = AdapterRegistry()
    
    services = {
        "plex": (PlexAPIClient("http://localhost:32400", "token"), "Plex"),
        "jellyfin": (JellyfinAPIClient("http://localhost:8096", "key"), "Jellyfin"),
        "qbittorrent": (QBittorrentAPIClient("http://localhost:8080", "admin", "pass"), "qBittorrent"),
    }
    
    for name, (client, label) in services.items():
        try:
            if client.test_connection():
                print(f"✓ {label} online")
            else:
                print(f"✗ {label} offline")
        except Exception as e:
            print(f"✗ {label} error: {e}")

check_all_services()
```

## Troubleshooting

### File Distribution Issues

**Problem**: Files not being distributed
- Check that output folders exist and are writable
- Verify input paths are correct
- Check file extensions match configuration

**Problem**: Imbalanced distribution
- Switch to `EQUAL_SIZE` strategy
- Increase capacity of underutilized outputs
- Check for `max_size_gb` limits being reached

**Problem**: No space left
- Add more output folders
- Increase `max_size_gb` limits
- Enable `rebalance_needed` monitoring

### Media Server Connection Issues

**Problem**: Cannot connect to Plex
- Verify Plex is running (`http://localhost:32400`)
- Check API token is valid
- Verify firewall allows local access

**Problem**: Cannot connect to Jellyfin
- Verify Jellyfin is running (`http://localhost:8096`)
- Generate new API key if expired
- Check API key has proper permissions

**Problem**: Cannot connect to qBittorrent
- Verify qBittorrent is running with WebUI enabled
- Check credentials in configuration
- Verify WebUI port (default 8080)

## API Reference

### FileScanner

```python
scanner = FileScanner("/input", extensions=[".mkv", ".mp4"], poll_interval=5)

# Single scan
new_files = scanner.scan_once()

# Get unprocessed files
files = scanner.get_unprocessed_files()

# Mark as processed
scanner.mark_processed(file_path)

# Background monitoring
thread = scanner.start_monitoring(callback=lambda files: print(f"Found {len(files)} files"))
scanner.stop_monitoring()
```

### FileDistributor

```python
distributor = FileDistributor(outputs, strategy, copy_mode)

# Distribute single file
dest = distributor.distribute_file(file_path, new_name="custom_name.mkv")

# Distribute batch
results = distributor.distribute_batch(files, callback)

# Get status
status = distributor.get_load_status()

# Check if rebalancing needed
needs_rebalance = distributor.rebalance_if_needed()
```

### Media Server Adapters

All media servers support:

```python
adapter.get_libraries()          # Get all libraries
adapter.scan_library(lib_id)     # Trigger scan
adapter.search_items(query)      # Search for content
adapter.get_library_contents(id) # Get library items
adapter.health_check()           # Test connection
```

## Performance Tips

1. **Use SSD for fast outputs** when using `ROUND_ROBIN` or `RANDOM`
2. **Set appropriate `scan_interval`** - lower = more responsive, higher = lower CPU
3. **Use `EQUAL_SIZE` strategy** for best load balancing
4. **Enable `rebalance_needed` monitoring** for large deployments
5. **Use `copy_mode=False`** (move) instead of copy for faster distribution
6. **Batch process files** instead of one-by-one when possible
