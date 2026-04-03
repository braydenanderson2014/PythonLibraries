#!/usr/bin/env python3
"""
Examples of using MediaAutomation Servarr adapters.
These are real, working examples you can run.
"""

from pathlib import Path
from media_automation.adapters.factory import AdapterRegistry
from media_automation.adapters.servarr_base import (
    SonarrAPIClient,
    RadarrAPIClient,
    LidarrAPIClient,
    ProwlarrAPIClient,
)


def example_1_sonarr_search_and_add():
    """Example 1: Search for a TV show and add it to Sonarr"""
    print("\n" + "=" * 60)
    print("EXAMPLE 1: Search and Add TV Show to Sonarr")
    print("=" * 60)
    
    # Initialize Sonarr adapter
    registry = AdapterRegistry()
    sonarr = registry.get_download_manager("sonarr")
    
    # Configure connection (would normally come from config.json)
    sonarr.client = SonarrAPIClient(
        base_url="http://localhost:8989",
        api_key="your_sonarr_api_key_here"
    )
    
    # Search and add a show
    try:
        if sonarr.search_and_download("Breaking Bad", quality_profile_id=1):
            print("✓ TV show 'Breaking Bad' added successfully!")
            
            # Get library status
            status = sonarr.get_library_status()
            if status["success"]:
                print(f"  Library now has {status['series_count']} series")
        else:
            print("✗ Failed to add show")
    except Exception as e:
        print(f"✗ Error: {e}")


def example_2_radarr_search_and_add():
    """Example 2: Search for a movie and add it to Radarr"""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Search and Add Movie to Radarr")
    print("=" * 60)
    
    registry = AdapterRegistry()
    radarr = registry.get_download_manager("radarr")
    
    radarr.client = RadarrAPIClient(
        base_url="http://localhost:7878",
        api_key="your_radarr_api_key_here"
    )
    
    try:
        if radarr.search_and_download("Inception"):
            print("✓ Movie 'Inception' added successfully!")
            
            status = radarr.get_library_status()
            if status["success"]:
                print(f"  Library now has {status['movie_count']} movies")
        else:
            print("✗ Failed to add movie")
    except Exception as e:
        print(f"✗ Error: {e}")


def example_3_lidarr_search_and_add():
    """Example 3: Search for an artist and add to Lidarr"""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Search and Add Artist to Lidarr")
    print("=" * 60)
    
    registry = AdapterRegistry()
    lidarr = registry.get_download_manager("lidarr")
    
    lidarr.client = LidarrAPIClient(
        base_url="http://localhost:8686",
        api_key="your_lidarr_api_key_here"
    )
    
    try:
        if lidarr.search_and_download(
            "The Beatles",
            quality_profile_id=1,
            metadata_profile_id=1
        ):
            print("✓ Artist 'The Beatles' added successfully!")
            
            status = lidarr.get_library_status()
            if status["success"]:
                print(f"  Library now has {status['artist_count']} artists")
        else:
            print("✗ Failed to add artist")
    except Exception as e:
        print(f"✗ Error: {e}")


def example_4_prowlarr_search():
    """Example 4: Search across all Prowlarr indexers"""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Search via Prowlarr")
    print("=" * 60)
    
    registry = AdapterRegistry()
    prowlarr = registry.get_indexer("prowlarr")
    
    prowlarr.client = ProwlarrAPIClient(
        base_url="http://localhost:9696",
        api_key="your_prowlarr_api_key_here"
    )
    
    try:
        results = prowlarr.search("Doctor Who Season 1")
        if results["success"]:
            print(f"✓ Found {len(results['results'])} results for '{results['query']}'")
            
            # Show first few results
            for i, result in enumerate(results['results'][:3]):
                print(f"  {i+1}. {result.get('title', 'N/A')}")
        else:
            print(f"✗ Search failed: {results.get('error')}")
    except Exception as e:
        print(f"✗ Error: {e}")


def example_5_health_checks():
    """Example 5: Check health of all services"""
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Service Health Checks")
    print("=" * 60)
    
    registry = AdapterRegistry()
    services = {
        "sonarr": registry.maybe_get_download_manager("sonarr"),
        "radarr": registry.maybe_get_download_manager("radarr"),
        "lidarr": registry.maybe_get_download_manager("lidarr"),
        "prowlarr": registry.maybe_get_indexer("prowlarr"),
    }
    
    # Configure all clients
    services["sonarr"].client = SonarrAPIClient("http://localhost:8989", "api_key")
    services["radarr"].client = RadarrAPIClient("http://localhost:7878", "api_key")
    services["lidarr"].client = LidarrAPIClient("http://localhost:8686", "api_key")
    services["prowlarr"].client = ProwlarrAPIClient("http://localhost:9696", "api_key")
    
    print("\nChecking service health...")
    for name, adapter in services.items():
        try:
            if adapter and adapter.health_check():
                print(f"  ✓ {name:10} OK")
            else:
                print(f"  ✗ {name:10} OFFLINE")
        except Exception as e:
            print(f"  ✗ {name:10} ERROR: {str(e)[:40]}")


def example_6_direct_api_calls():
    """Example 6: Direct API calls using the base clients"""
    print("\n" + "=" * 60)
    print("EXAMPLE 6: Direct API Calls")
    print("=" * 60)
    
    # Initialize Sonarr client directly
    sonarr = SonarrAPIClient(
        base_url="http://localhost:8989",
        api_key="your_sonarr_api_key_here"
    )
    
    try:
        # Search for a series
        results = sonarr.search_series("Breaking Bad")
        if results:
            series = results[0]
            print(f"✓ Found: {series.get('title')} (TVDB ID: {series.get('tvdbId')})")
            
            # Prepare data for adding to library
            print("\nEntry data that would be added to Sonarr:")
            print(f"  - Title: {series.get('title')}")
            print(f"  - Year: {series.get('year')}")
            print(f"  - TVDB ID: {series.get('tvdbId')}")
            print(f"  - Seasons: {len(series.get('seasons', []))}")
        else:
            print("✗ No results found")
    except Exception as e:
        print(f"✗ Error: {e}")


def example_7_advanced_sonarr_search():
    """Example 7: Advanced Sonarr usage - trigger search for existing series"""
    print("\n" + "=" * 60)
    print("EXAMPLE 7: Advanced - Trigger Search")
    print("=" * 60)
    
    sonarr = SonarrAPIClient(
        base_url="http://localhost:8989",
        api_key="your_sonarr_api_key_here"
    )
    
    try:
        # Get all series
        all_series = sonarr.get_series()
        if all_series and len(all_series) > 0:
            first_series = all_series[0]
            series_id = first_series.get("id")
            series_title = first_series.get("title")
            
            print(f"✓ Found series: {series_title} (ID: {series_id})")
            print(f"  Would trigger search for this series")
            print(f"  (Requires: series_id = {series_id})")
            
            # In production, you would do this:
            # result = sonarr.trigger_search(series_id, season=0)
            # print(f"  Search triggered: {result}")
        else:
            print("✗ No series found in library")
    except Exception as e:
        print(f"✗ Error: {e}")


def main():
    """Run all examples"""
    print("\n╔════════════════════════════════════════════════════════════╗")
    print("║    MediaAutomation Servarr Adapter Examples               ║")
    print("╚════════════════════════════════════════════════════════════╝")
    
    print("\nNote: Examples require services running at default ports with valid API keys.")
    print("Update the base_url and api_key values in each example to match your setup.\n")
    
    examples = [
        ("Sonarr Search & Add", example_1_sonarr_search_and_add),
        ("Radarr Search & Add", example_2_radarr_search_and_add),
        ("Lidarr Search & Add", example_3_lidarr_search_and_add),
        ("Prowlarr Search", example_4_prowlarr_search),
        ("Health Checks", example_5_health_checks),
        ("Direct API Calls", example_6_direct_api_calls),
        ("Advanced Search", example_7_advanced_sonarr_search),
    ]
    
    for name, func in examples:
        try:
            func()
        except Exception as e:
            print(f"\n✗ Example '{name}' failed: {e}")
    
    print("\n" + "=" * 60)
    print("Examples complete!")
    print("=" * 60)
    print("\nFor more information, see:")
    print("  - SERVARR_INTEGRATION.md (detailed integration guide)")
    print("  - test_servarr.py (connection testing)")
    print("  - config.servarr.example.json (configuration example)")


if __name__ == "__main__":
    main()
