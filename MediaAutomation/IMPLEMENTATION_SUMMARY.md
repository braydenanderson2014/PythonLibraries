# MediaAutomation Servarr Implementation Summary

## What's Been Implemented

You now have full REST API support integrated into MediaAutomation for:

### Implemented Services ✓

1. **Prowlarr** - Indexer aggregator/manager
   - Adapter: `ProwlarrAdapter`
   - Features: Search across indexers, add/manage indexers

2. **Sonarr** - TV show management and download automation
   - Adapter: `SonarrAdapter`
   - Features: Add shows, search, trigger searches, library status

3. **Radarr** - Movie management and download automation
   - Adapter: `RadarrAdapter`
   - Features: Add movies, search, trigger searches, library status

4. **Lidarr** - Music management and download automation
   - Adapter: `LidarrAdapter`
   - Features: Add artists, search, trigger searches, library status

5. **Readarr** - Book management and download automation
   - Adapter: `ReadarrAdapter`
   - Features: Add authors, search, trigger searches, library status

## Architecture

### Core Components
- **`servarr_base.py`** - Base HTTP client classes for all Servarr services
- **`interfaces.py`** - Extended with `IndexerAdapter` and `DownloadManagerAdapter`
- **`factory.py`** - Updated registry with new adapter types
- **Individual adapters** - Prowlarr, Sonarr, Radarr, Lidarr, Readarr

### API Support
All services use HTTP REST APIs (no CLI required):
- Prowlarr: `/api/v1/`
- Sonarr: `/api/v3/`
- Radarr: `/api/v3/`
- Lidarr: `/api/v1/`
- Readarr: `/api/v1/`

## Files Created

- `media_automation/adapters/servarr_base.py` - Base API clients
- `media_automation/adapters/prowlarr.py` - Prowlarr adapter
- `media_automation/adapters/sonarr.py` - Sonarr adapter
- `media_automation/adapters/radarr.py` - Radarr adapter
- `media_automation/adapters/lidarr.py` - Lidarr adapter
- `media_automation/adapters/readarr.py` - Readarr adapter
- `SERVARR_INTEGRATION.md` - Comprehensive integration guide
- `config.servarr.example.json` - Example config with Servarr settings
- `test_servarr.py` - Testing script for all services

## Files Modified

- `media_automation/interfaces.py` - Added new adapter base classes
- `media_automation/adapters/factory.py` - Registered all adapters
- `requirements.txt` - Added `requests` dependency

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Update config.json** with your Servarr URLs and API keys:
   ```json
   {
     "servarr": {
       "sonarr": {
         "base_url": "http://localhost:8989",
         "api_key": "your_key_here"
       }
     }
   }
   ```

3. **Test connectivity:**
   ```bash
   python test_servarr.py
   ```

## Other Services to Consider Adding

### Media Management
- **Overseerr** - Media request management for Sonarr/Radarr
  - REST API support via `/api/v1/`
  - Could add RequestManagerAdapter
  - Use case: Manage user requests in multi-user setup

- **Jellyseerr** - Request management for Jellyfish/Emby
  - Similar to Overseerr but for Jellyfin environments
  - REST API available

### Subtitle Management
- **Bazarr** - Subtitle management (syncs with Sonarr/Radarr)
  - REST API via `/api/`
  - Could add SubtitleManagerAdapter
  - More powerful than basic subtitle_tool

### Download Managers
- **SABnzbd** - Usenet downloader with API
  - REST API available
  - Could add NzbDownloadAdapter
  - Good for NZB-based downloading

- **Transmission** / **rTorrent** - Torrent clients with APIs
  - REST/socket APIs available
  - Could add TorrentDownloadAdapter
  - Common in Servarr stacks

- **qBittorrent** - Advanced torrent client
  - WebUI API available via `/api/v2/`
  - Popular alternative to Transmission

### Search & Indexing
- **Jackett** - Alternative indexer aggregator to Prowlarr
  - REST API via `/api/v2.0/indexers/`
  - Could add as alternative IndexerAdapter
  - Pre-Prowlarr systems may use this

### Content Delivery
- **Plex** / **Jellyfin** - Media servers
  - Both have REST APIs
  - Could add MediaServerAdapter for library management
  - Useful for organizing output from rippers

### Notification Services
- **Notifiarr** - Notification hub for Servarr stack
  - Sends alerts when media is added/downloaded
  - Could add NotificationAdapter
  - REST API available

## Implementation Patterns

When adding new services, follow this pattern:

1. Create base client class in a shared file (like `servarr_base.py`)
2. Create adapter class inheriting from appropriate interface
3. Register in `AdapterRegistry` (factory.py)
4. Add configuration template to `config.json`
5. Update documentation

Example:

```python
# 1. Base client (in shared file)
class ServiceAPIClient:
    def __init__(self, base_url, api_key):
        self.session = requests.Session()
        
    def test_connection(self):
        return self.get("/api/v1/system/status")

# 2. Adapter
class ServiceAdapter(SomeAdapter):
    name = "service_name"
    
    def __init__(self, base_url=..., api_key=...):
        self.client = ServiceAPIClient(base_url, api_key)
    
    # Implement interface methods

# 3. Register in factory
self.adapters[ServiceAdapter.name] = ServiceAdapter()
```

## Next Steps (Optional)

1. Add Overseerr for multi-user request management
2. Add Bazarr for advanced subtitle handling
3. Add Jackett as Prowlarr alternative
4. Add torrent client support (qBittorrent, Transmission)
5. Create web UI for managing Servarr connections
6. Add scheduler for periodic Servarr searches
7. Create hooks for automatic downloads after ripping

## CLI/HTML Support Status

| Service | CLI | REST API | HTML UI |
|---------|-----|----------|---------|
| Prowlarr | ✗ | ✓ | ✓ |
| Sonarr | ✗ | ✓ | ✓ |
| Radarr | ✗ | ✓ | ✓ |
| Lidarr | ✗ | ✓ | ✓ |
| Readarr | ✗ | ✓ | ✓ |
| Jackett | ✗ | ✓ | ✓ |
| Overseerr | ✗ | ✓ | ✓ |
| Bazarr | ✗ | ✓ | ✓ |
| SABnzbd | ✓ (limited) | ✓ | ✓ |
| qBittorrent | ✗ | ✓ | ✓ |

**Note:** Most modern services use REST APIs, making them easier to integrate than CLI-only tools.

## Testing

Run the test script to verify your setup:

```bash
python test_servarr.py
```

This will check:
- Service connectivity
- API key validity
- Library status (count of items)
- Report any configuration issues
