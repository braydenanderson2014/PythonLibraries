# Servarr Stack Integration Guide

This guide covers integrating MediaAutomation with the Servarr application stack (Prowlarr, Sonarr, Radarr, Lidarr, Readarr).

## Overview

The Servarr stack consists of automation applications for managing media libraries:

- **Prowlarr**: Indexer aggregator and manager
- **Sonarr**: TV show manager and download automation
- **Radarr**: Movie manager and download automation
- **Lidarr**: Music manager and download automation
- **Readarr**: Book manager and download automation

All services support REST APIs (HTTP) - no CLI needed for integration.

## Setup

### 1. Install Servarr Applications

Each application can be run via Docker or standalone. For example:

```bash
# Docker Compose example
version: '3.8'
services:
  prowlarr:
    image: lscr.io/linuxserver/prowlarr:latest
    ports:
      - "9696:9696"
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=UTC
    volumes:
      - /path/to/prowlarr:/config

  sonarr:
    image: lscr.io/linuxserver/sonarr:latest
    ports:
      - "8989:8989"
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=UTC
    volumes:
      - /path/to/sonarr:/config
      - /path/to/tv:/tv

  radarr:
    image: lscr.io/linuxserver/radarr:latest
    ports:
      - "7878:7878"
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=UTC
    volumes:
      - /path/to/radarr:/config
      - /path/to/movies:/movies

  lidarr:
    image: lscr.io/linuxserver/lidarr:latest
    ports:
      - "8686:8686"
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=UTC
    volumes:
      - /path/to/lidarr:/config
      - /path/to/music:/music

  readarr:
    image: lscr.io/linuxserver/readarr:latest
    ports:
      - "8787:8787"
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=UTC
    volumes:
      - /path/to/readarr:/config
      - /path/to/books:/books
```

### 2. Generate API Keys

In each application's web UI (Settings → General), generate an API key.

### 3. Update config.json

Add Servarr configurations to your MediaAutomation config:

```json
{
  "paths": {
    "output_root": "./output",
    "temp_root": "./temp"
  },
  "executables": {
    "makemkv": "",
    "handbrake": ""
  },
  "servarr": {
    "prowlarr": {
      "base_url": "http://localhost:9696",
      "api_key": "your_prowlarr_api_key_here"
    },
    "sonarr": {
      "base_url": "http://localhost:8989",
      "api_key": "your_sonarr_api_key_here",
      "quality_profile_id": 1,
      "root_folder_path": "/tv"
    },
    "radarr": {
      "base_url": "http://localhost:7878",
      "api_key": "your_radarr_api_key_here",
      "quality_profile_id": 1,
      "root_folder_path": "/movies"
    },
    "lidarr": {
      "base_url": "http://localhost:8686",
      "api_key": "your_lidarr_api_key_here",
      "quality_profile_id": 1,
      "metadata_profile_id": 1,
      "root_folder_path": "/music"
    },
    "readarr": {
      "base_url": "http://localhost:8787",
      "api_key": "your_readarr_api_key_here",
      "quality_profile_id": 1,
      "metadata_profile_id": 1,
      "root_folder_path": "/books"
    }
  },
  "jobs": []
}
```

## Usage Examples

### Search and Add TV Show

```python
from media_automation.adapters.factory import AdapterRegistry

registry = AdapterRegistry()
sonarr = registry.get_download_manager("sonarr")

# Connect to Sonarr
sonarr.client = SonarrAPIClient("http://localhost:8989", "your_api_key")

# Search for series
if sonarr.search_and_download("Breaking Bad", quality_profile_id=1):
    print("Series added successfully!")
    status = sonarr.get_library_status()
    print(f"Library now has {status['series_count']} series")
```

### Search and Add Movie

```python
from media_automation.adapters.factory import AdapterRegistry

registry = AdapterRegistry()
radarr = registry.get_download_manager("radarr")

# Connect to Radarr
radarr.client = RadarrAPIClient("http://localhost:7878", "your_api_key")

# Search for movie
if radarr.search_and_download("Inception"):
    print("Movie added successfully!")
    status = radarr.get_library_status()
    print(f"Library now has {status['movie_count']} movies")
```

### Search via Prowlarr

```python
from media_automation.adapters.prowlarr import ProwlarrAdapter

prowlarr = ProwlarrAdapter("http://localhost:9696", "your_api_key")

# Search across all indexers
results = prowlarr.search("Doctor Who")
if results['success']:
    print(f"Found {len(results['results'])} results")
```

### Add Artist to Lidarr

```python
from media_automation.adapters.factory import AdapterRegistry

registry = AdapterRegistry()
lidarr = registry.get_download_manager("lidarr")

# Connect to Lidarr
lidarr.client = LidarrAPIClient("http://localhost:8686", "your_api_key")

# Add artist
entry = {
    "artistName": "The Beatles",
    "qualityProfileId": 1,
    "metadataProfileId": 1,
    "rootFolderPath": "/music",
    "monitored": True
}

if lidarr.add_entry(entry):
    print("Artist added successfully!")
```

## Health Checks

All adapters support health checks to verify connectivity:

```python
from media_automation.adapters.factory import AdapterRegistry

registry = AdapterRegistry()

# Check all services
for service_name in ["sonarr", "radarr", "lidarr", "readarr", "prowlarr"]:
    try:
        if service_name == "prowlarr":
            adapter = registry.get_indexer(service_name)
        else:
            adapter = registry.get_download_manager(service_name)
        
        if adapter.health_check():
            print(f"✓ {service_name} is online")
        else:
            print(f"✗ {service_name} is offline")
    except Exception as e:
        print(f"✗ {service_name} error: {e}")
```

## CLI and HTML Request Support

### REST API Support

All Servarr services support comprehensive REST APIs:

- **Prowlarr**: `/api/v1/` endpoints
- **Sonarr**: `/api/v3/` endpoints  
- **Radarr**: `/api/v3/` endpoints
- **Lidarr**: `/api/v1/` endpoints
- **Readarr**: `/api/v1/` endpoints

Direct HTTP requests can also be made using Python's `requests` library:

```python
import requests

# Get Sonarr library
response = requests.get(
    "http://localhost:8989/api/v3/series",
    headers={"X-Api-Key": "your_api_key"}
)
series = response.json()
```

### CLI Support

Servarr applications offer limited CLI support. However, you can:

1. **Start/Stop Services**: Use Docker or system commands
2. **Query via curl**: Use HTTP endpoints from shell scripts
3. **Trigger Actions**: Call API endpoints from Python subprocesses

Example curl command:

```bash
# Search for series
curl -X GET "http://localhost:8989/api/v3/series/lookup?term=Breaking%20Bad" \
  -H "X-Api-Key: your_api_key"

# Trigger search
curl -X POST "http://localhost:8989/api/v3/command" \
  -H "X-Api-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{"name":"SeriesSearch","seriesId":1}'
```

## Other Services to Consider

While implementing Servarr, you may also like:

- **Overseerr** / **Jellyseerr**: Request management and UI
- **Bazarr**: Subtitle management (complements Sonarr/Radarr)
- **Jackett**: Indexer aggregator (alternative to Prowlarr)
- **SABnzbd** / **rTorrent**: Download managers (often used with *arr apps)

## Troubleshooting

### Connection Errors

```python
# Verify API key and URL
adapter.client = SonarrAPIClient("http://localhost:8989", "api_key")
if not adapter.health_check():
    print("Unable to connect - check URL and API key")
```

### Missing API Key

Generate in web UI: Settings → General → API Key

### Port Access

Ensure firewall allows access to service ports (8989, 7878, 8686, 8787, 9696)

### Request Timeout

Adjust timeout (default 30s):

```python
from media_automation.adapters.servarr_base import SonarrAPIClient
client = SonarrAPIClient("http://localhost:8989", "api_key", timeout=60)
```
