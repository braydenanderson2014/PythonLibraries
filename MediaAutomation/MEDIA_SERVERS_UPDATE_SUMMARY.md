# MediaAutomation Updates: Media Servers, qBittorrent, and File Distribution

## Overview

This update adds comprehensive media server support and a powerful modular file scanning/distribution system with load balancing to MediaAutomation.

## New Components

### 1. Media Servers (3 new adapters)

#### Plex Media Server (`adapters/plex.py`)
- Central media library management and streaming
- MediaServerAdapter implementation
- Features: Get libraries, trigger scans, search content, get library contents
- Configuration: Base URL + API token

#### Jellyfin (`adapters/jellyfin.py`)
- Open-source alternative to Plex
- MediaServerAdapter implementation  
- Features: Get libraries, refresh/scan, search items, content browsing
- Configuration: Base URL + API key

#### qBittorrent (`adapters/qbittorrent.py`)
- Lightweight torrent client with WebUI
- DownloadManagerAdapter implementation
- Features: Add torrents, get status, pause/resume, preferences management
- Configuration: WebUI URL + credentials

### 2. Media Server Base Clients (`adapters/media_servers_base.py`)

Contains low-level HTTP API clients for each service:
- `PlexAPIClient` - HTTP client for Plex REST API
- `JellyfinAPIClient` - HTTP client for Jellyfin API
- `QBittorrentAPIClient` - HTTP client for qBittorrent WebUI API

### 3. File Distribution System (`file_distribution.py`)

#### FileScanner
Monitors input directories for new files:
- Configurable file extensions to watch
- Automatic polling at configurable intervals
- Tracks scanned files and processing status
- Background threading support
- File metadata tracking (size, extension, timestamp)

#### FileDistributor
Distributes files to multiple output folders:
- Four load balancing strategies:
  - **EQUAL_SIZE**: Distribute by total folder size
  - **LEAST_USED**: Use output with fewest files
  - **ROUND_ROBIN**: Cycle through outputs
  - **RANDOM**: Random selection
- Per-output capacity limits (GB)
- Copy or move modes
- Load status reporting
- Rebalancing detection
- Rename conflict handling

#### FileDistributionPipeline
Combined auto-scanning and distribution:
- End-to-end orchestration
- Automatic file detection and routing
- Configurable callback system
- Statistics tracking
- Easy start/stop interface

### 4. Interfaces (`interfaces.py`)

Added two new adapter base classes:
- `MediaServerAdapter` - Format for media servers (Plex, Jellyfin)
- Extended `DownloadManagerAdapter` - Now includes torrent clients

### 5. Factory Updates (`adapters/factory.py`)

Registry now includes:
- `media_servers` dict for Plex and Jellyfin
- `download_managers` dict now includes qBittorrent
- Accessor methods: `get_media_server()`, `maybe_get_media_server()`
- Updated imports for all new adapters

## Files Created

### Core Implementation (8 files)
```
media_automation/
├── adapters/
│   ├── media_servers_base.py      # HTTP clients for Plex, Jellyfin, qBittorrent
│   ├── plex.py                     # Plex adapter
│   ├── jellyfin.py                 # Jellyfin adapter
│   └── qbittorrent.py              # qBittorrent adapter
├── file_distribution.py            # Scanner, Distributor, Pipeline classes
└── interfaces.py                   # UPDATED: New adapter base classes
```

### Documentation (4 files)
```
├── MEDIA_SERVERS_AND_DISTRIBUTION.md  # Complete guide (900+ lines)
├── config.full.example.json           # Full config template with all features
├── examples_distribution.py           # 8 working examples
└── README.md                          # UPDATED: Added media servers section
```

### Testing (2 files)
Documentation files (see above)

## Load Balancing Strategies Explained

### EQUAL_SIZE
Balances **total folder size** across outputs.
- Best for: Mixed workload where size matters
- Example: 3 × 500GB outputs, files go to smallest

### LEAST_USED  
Uses output with **fewest files**.
- Best for: Uniform file sizes
- Example: Output 1 has 25 files, Output 2 has 18 → Use Output 2

### ROUND_ROBIN
Cycles through outputs in order.
- Best for: Simple rotation
- Example: File 1 → Out1, File 2 → Out 2, File 3 → Out 3, File 4 → Out 1...

### RANDOM
Random output selection.
- Best for: Unpredictable patterns
- Example: Randomly chosen output for each file

## Configuration

### Media Servers

```json
{
  "media_servers": {
    "plex": {
      "enabled": true,
      "base_url": "http://localhost:32400",
      "api_key": "your_token"
    },
    "jellyfin": {
      "enabled": true,
      "base_url": "http://localhost:8096",
      "api_key": "your_key"
    }
  },
  "download_managers": {
    "qbittorrent": {
      "enabled": true,
      "base_url": "http://localhost:8080",
      "username": "admin",
      "password": "password"
    }
  }
}
```

### File Distribution

```json
{
  "file_distribution": {
    "enabled": true,
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
      }
    },
    "scan_interval": 5,
    "strategy": "equal_size",
    "copy_mode": false,
    "extensions": [".mkv", ".mp4"],
    "trigger_media_server_scans": {
      "plex": true,
      "jellyfin": true
    }
  }
}
```

## Usage Examples

### Basic File Distribution
```python
from media_automation.file_distribution import FileDistributor, OutputFolder, DistributionStrategy
from pathlib import Path

outputs = [
    OutputFolder(Path("/out1"), max_size_gb=500),
    OutputFolder(Path("/out2"), max_size_gb=500),
]

dis = FileDistributor(outputs, strategy=DistributionStrategy.EQUAL_SIZE)
dest = dis.distribute_file(Path("/input/movie.mkv"))
```

### Auto-Scanning Pipeline
```python
from media_automation.file_distribution import FileDistributionPipeline

pipeline = FileDistributionPipeline(
    input_paths="/input",
    output_folders=outputs,
    strategy=DistributionStrategy.EQUAL_SIZE,
)

pipeline.start()
# ... runs continuously ...
pipeline.stop()
```

### Media Server Integration
```python
from media_automation.adapters.media_servers_base import PlexAPIClient

plex = PlexAPIClient("http://localhost:32400", "token")
if plex.test_connection():
    libraries = plex.get_libraries()
    plex.scan_library("1")  # Trigger scan
```

### Combined Workflow
```python
# Scan input → Distribute → Trigger Plex/Jellyfin scans
# See examples_distribution.py Example 7 for full implementation
```

## API Reference

### FileScanner
```python
scanner = FileScanner(input_paths, extensions, poll_interval)
scanner.scan_once()                    # Single scan
scanner.get_unprocessed_files()        # Unprocessed files
scanner.mark_processed(file_path)      # Mark as done
scanner.start_monitoring(callback)     # Background monitor
scanner.stop_monitoring()              # Stop monitoring
```

### FileDistributor
```python
distributor = FileDistributor(outputs, strategy, copy_mode)
distributor.distribute_file(path, name)          # Single file
distributor.distribute_batch(files, callback)    # Multiple files
distributor.get_load_status()                    # Status report
distributor.rebalance_if_needed()                # Check imbalance
```

### FileDistributionPipeline
```python
pipeline = FileDistributionPipeline(...)
pipeline.start(callback)    # Start auto-distribution
pipeline.stop()             # Stop pipeline
pipeline.get_stats()        # Statistics
```

### Media Server Adapters
All implement `MediaServerAdapter`:
```python
adapter.get_libraries()             # Get all libraries
adapter.scan_library(id)            # Trigger scan
adapter.search_items(query)         # Search content
adapter.get_library_contents(id)    # Get library items
adapter.health_check()              # Test connection
```

## Performance Considerations

1. **Large Files**: EQUAL_SIZE strategy better than LEAST_USED
2. **Scan Interval**: Higher values = lower CPU, lower responsiveness
3. **Copy vs Move**: Move is ~10x faster for large files
4. **Output Count**: 2-4 is typical sweet spot
5. **Capacity Limits**: Set realistic limits to trigger balancing

## Troubleshooting

### Files Not Distributing
- Check input path exists and contains files
- Verify output paths are writable
- Check file extensions match configuration
- Ensure enough space in outputs

### Connection Issues
- Verify media servers are running
- Check base URLs and API keys
- Verify firewall allows access
- Check default ports: Plex=32400, Jellyfin=8096, qBittorrent=8080

### Imbalanced Storage
- Switch to EQUAL_SIZE strategy
- Add more output folders
- Increase max_size_gb limits
- Check rebalance_needed flag

## Integration with Existing Features

The new components work seamlessly with existing functionality:

1. **File Distribution** → Output to **Plex/Jellyfin** libraries
2. **qBittorrent** → Download torrents to output folders
3. **Servarr Stack** → Add content, qBittorrent downloads, distribute, serve via Plex
4. **Encoding Pipeline** → Process → Distribute → Serve

Example workflow:
```
MakeMKV (rip) → Subtitle → HandBrake (encode) → FileDistributor 
→ Plex scan → Display in Plex UI
```

## Dependencies

New dependencies added to requirements.txt:
- `requests>=2.28.0` (already added in Servarr update)

No additional dependencies needed for core functionality.

## Next Steps (Optional Enhancements)

1. **Overseerr Integration** - Request management UI
2. **Bazarr Integration** - Subtitle management
3. **Torrent Search Integration** - Prowlarr → qBittorrent pipeline
4. **Auto-Rebalancing** - Move files between outputs automatically
5. **GUI Components** - Add distribution monitor to PyQt6 UI
6. **Cloud Storage** - Support S3, rclone for remote outputs
7. **Caching** - Cache file lists for faster scanning

## Statistics and Monitoring

Pipeline provides real-time statistics:
```python
stats = pipeline.get_stats()
# {
#   "scanned_files": 150,
#   "processed_files": 142,
#   "distribution_load": {...},
#   "rebalance_needed": False
# }
```

Distribution status:
```python
status = distributor.get_load_status()
# {
#   "output_0": {
#     "path": "/out1",
#     "current_size_gb": 450.2,
#     "available_space_gb": 49.8,
#     "total_files": 125
#   },
#   ...
# }
```

## Testing

Run examples to test all features:
```bash
python examples_distribution.py
```

Run connectivity tests:
```bash
python test_servarr.py  # Tests Servarr + media servers
```

## Files Modified

- `media_automation/interfaces.py` - Added MediaServerAdapter
- `media_automation/adapters/factory.py` - Added new adapters and accessors
- `requirements.txt` - Already has requests (from Servarr update)
- `README.md` - Updated with media servers section

## Documentation Files

- **MEDIA_SERVERS_AND_DISTRIBUTION.md** (900+ lines) - Complete guide with:
  - Media server setup and configuration
  - File distribution strategies
  - Load balancing algorithms
  - Advanced usage patterns
  - Troubleshooting guide
  - Full API reference
  - Performance tips

- **examples_distribution.py** - 8 working examples:
  1. Basic distribution
  2. Auto-scanning
  3. Multi-tier storage
  4. Plex integration
  5. Jellyfin integration
  6. qBittorrent integration
  7. Combined workflow
  8. Rebalancing monitor

- **config.full.example.json** - Complete configuration template

## Summary

MediaAutomation now has:
- ✅ Full media server support (Plex + Jellyfin)
- ✅ qBittorrent torrent client integration
- ✅ Automatic file scanning and importing
- ✅ Intelligent multi-output file distribution
- ✅ 4 load balancing strategies
- ✅ Capacity management and limits
- ✅ Rebalancing detection
- ✅ Media server scan triggering
- ✅ Comprehensive documentation
- ✅ Working examples and tests

This enables complex workflows:
1. Rip media (existing)
2. Encode media (existing)
3. Automatically distribute to multiple storage locations with load balancing (NEW)
4. Trigger Plex/Jellyfin scans  (NEW)
5. Integrate with torrent downloads (NEW)
6. Integrate with Servarr stack (existing)
7. All coordinated through unified configuration and API
