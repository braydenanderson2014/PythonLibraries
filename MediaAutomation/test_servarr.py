#!/usr/bin/env python3
"""
Test script for MediaAutomation Servarr integrations.
Run this to verify all your Servarr services are correctly configured.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    from media_automation.adapters.factory import AdapterRegistry
    from media_automation.adapters.servarr_base import (
        LidarrAPIClient,
        ProwlarrAPIClient,
        RadarrAPIClient,
        ReadarrAPIClient,
        SonarrAPIClient,
    )
except ImportError:
    print("ERROR: MediaAutomation not properly installed. Run: pip install -r requirements.txt")
    sys.exit(1)


def load_config(config_path: Path = Path("config.json")) -> dict:
    """Load configuration from JSON file."""
    if not config_path.exists():
        print(f"ERROR: Config file not found at {config_path}")
        return {}
    
    with open(config_path) as f:
        return json.load(f)


def test_prowlarr(config: dict) -> bool:
    """Test Prowlarr connection."""
    print("\n[TESTING] Prowlarr...")
    try:
        servarr_config = config.get("servarr", {})
        prowlarr_config = servarr_config.get("prowlarr", {})
        
        if not prowlarr_config.get("enabled", True):
            print("  ⊘ Prowlarr disabled in config")
            return False
        
        base_url = prowlarr_config.get("base_url", "http://localhost:9696")
        api_key = prowlarr_config.get("api_key", "")
        
        if not api_key:
            print("  ✗ API key not configured")
            return False
        
        client = ProwlarrAPIClient(base_url, api_key)
        if client.test_connection():
            indexers = client.get_indexers()
            print(f"  ✓ Connected! Found {len(indexers)} indexers")
            return True
        else:
            print("  ✗ Connection failed")
            return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def test_sonarr(config: dict) -> bool:
    """Test Sonarr connection."""
    print("\n[TESTING] Sonarr...")
    try:
        servarr_config = config.get("servarr", {})
        sonarr_config = servarr_config.get("sonarr", {})
        
        if not sonarr_config.get("enabled", True):
            print("  ⊘ Sonarr disabled in config")
            return False
        
        base_url = sonarr_config.get("base_url", "http://localhost:8989")
        api_key = sonarr_config.get("api_key", "")
        
        if not api_key:
            print("  ✗ API key not configured")
            return False
        
        client = SonarrAPIClient(base_url, api_key)
        if client.test_connection():
            series = client.get_series()
            count = len(series) if isinstance(series, list) else 0
            print(f"  ✓ Connected! Library has {count} series")
            return True
        else:
            print("  ✗ Connection failed")
            return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def test_radarr(config: dict) -> bool:
    """Test Radarr connection."""
    print("\n[TESTING] Radarr...")
    try:
        servarr_config = config.get("servarr", {})
        radarr_config = servarr_config.get("radarr", {})
        
        if not radarr_config.get("enabled", True):
            print("  ⊘ Radarr disabled in config")
            return False
        
        base_url = radarr_config.get("base_url", "http://localhost:7878")
        api_key = radarr_config.get("api_key", "")
        
        if not api_key:
            print("  ✗ API key not configured")
            return False
        
        client = RadarrAPIClient(base_url, api_key)
        if client.test_connection():
            movies = client.get_movie()
            count = len(movies) if isinstance(movies, list) else 0
            print(f"  ✓ Connected! Library has {count} movies")
            return True
        else:
            print("  ✗ Connection failed")
            return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def test_lidarr(config: dict) -> bool:
    """Test Lidarr connection."""
    print("\n[TESTING] Lidarr...")
    try:
        servarr_config = config.get("servarr", {})
        lidarr_config = servarr_config.get("lidarr", {})
        
        if not lidarr_config.get("enabled", True):
            print("  ⊘ Lidarr disabled in config")
            return False
        
        base_url = lidarr_config.get("base_url", "http://localhost:8686")
        api_key = lidarr_config.get("api_key", "")
        
        if not api_key:
            print("  ✗ API key not configured")
            return False
        
        client = LidarrAPIClient(base_url, api_key)
        if client.test_connection():
            artists = client.get_artist()
            count = len(artists) if isinstance(artists, list) else 0
            print(f"  ✓ Connected! Library has {count} artists")
            return True
        else:
            print("  ✗ Connection failed")
            return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def test_readarr(config: dict) -> bool:
    """Test Readarr connection."""
    print("\n[TESTING] Readarr...")
    try:
        servarr_config = config.get("servarr", {})
        readarr_config = servarr_config.get("readarr", {})
        
        if not readarr_config.get("enabled", True):
            print("  ⊘ Readarr disabled in config")
            return False
        
        base_url = readarr_config.get("base_url", "http://localhost:8787")
        api_key = readarr_config.get("api_key", "")
        
        if not api_key:
            print("  ✗ API key not configured")
            return False
        
        client = ReadarrAPIClient(base_url, api_key)
        if client.test_connection():
            authors = client.get_author()
            count = len(authors) if isinstance(authors, list) else 0
            print(f"  ✓ Connected! Library has {count} authors")
            return True
        else:
            print("  ✗ Connection failed")
            return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("MediaAutomation Servarr Integration Tester")
    print("=" * 60)
    
    config = load_config()
    
    if not config:
        print("\nERROR: Could not load configuration")
        return False
    
    results = {
        "Prowlarr": test_prowlarr(config),
        "Sonarr": test_sonarr(config),
        "Radarr": test_radarr(config),
        "Lidarr": test_lidarr(config),
        "Readarr": test_readarr(config),
    }
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for service, success in results.items():
        status = "✓ OK" if success else "✗ FAILED"
        print(f"  {service:12} {status}")
    
    print("=" * 60)
    
    if any(results.values()):
        print("\n✓ At least one service is working!")
        return True
    else:
        print("\n✗ No services are reachable. Check:")
        print("  - Services are running (Docker/systemd)")
        print("  - Base URLs are correct in config.json")
        print("  - API keys are valid")
        print("  - Firewall allows access to service ports")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
