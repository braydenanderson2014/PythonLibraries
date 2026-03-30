#!/usr/bin/env python3
"""
Examples for media servers and file distribution with load balancing.
"""

import time
from pathlib import Path

# =============================================================================
# EXAMPLE 1: Basic File Distribution
# =============================================================================

def example_1_basic_distribution():
    """Example 1: Distribute files to multiple outputs with load balancing"""
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Basic File Distribution with Load Balancing")
    print("=" * 70)
    
    from media_automation.file_distribution import (
        FileDistributor,
        OutputFolder,
        DistributionStrategy,
    )
    
    # Setup output folders
    outputs = [
        OutputFolder(Path("/output1"), max_size_gb=100),
        OutputFolder(Path("/output2"), max_size_gb=100),
        OutputFolder(Path("/output3"), max_size_gb=100),
    ]
    
    # Create distributor with equal size strategy
    distributor = FileDistributor(
        outputs,
        strategy=DistributionStrategy.EQUAL_SIZE,
        copy_mode=True,  # Copy instead of move
    )
    
    print("\n✓ Distributor created with EQUAL_SIZE strategy")
    print("  Outputs:")
    for i, output in enumerate(outputs):
        print(f"    {i+1}. {output.path} (max {output.max_size_gb}GB)")
    
    # Show load status
    status = distributor.get_load_status()
    print("\nInitial load status:")
    for output_name, stats in status.items():
        print(f"  {output_name}:")
        print(f"    - Current: {stats['current_size_gb']:.2f}GB")
        print(f"    - Available: {stats['available_space_gb']:.2f}GB")
        print(f"    - Files: {stats['total_files']}")


# =============================================================================
# EXAMPLE 2: Automatic File Scanning and Distribution
# =============================================================================

def example_2_auto_scanning():
    """Example 2: Scan directory and automatically distribute files"""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Automatic File Scanning and Distribution")
    print("=" * 70)
    
    from media_automation.file_distribution import (
        FileDistributionPipeline,
        OutputFolder,
        DistributionStrategy,
    )
    
    outputs = [
        OutputFolder(Path("/output1"), max_size_gb=500),
        OutputFolder(Path("/output2"), max_size_gb=500),
    ]
    
    # Create pipeline
    pipeline = FileDistributionPipeline(
        input_paths="/input",
        output_folders=outputs,
        extensions=[".mkv", ".mp4"],
        scan_interval=5,
        strategy=DistributionStrategy.EQUAL_SIZE,
        copy_mode=False,  # Move files
    )
    
    print("\n✓ Pipeline created")
    print("  Input: /input")
    print("  Extensions: .mkv, .mp4")
    print("  Scan interval: 5 seconds")
    print("  Strategy: EQUAL_SIZE")
    print("  Mode: MOVE")
    
    # Callback function
    def on_file_distributed(scanned_file, destination):
        if destination:
            size_gb = scanned_file.size_bytes / (1024**3)
            print(f"  ✓ {scanned_file.path.name} ({size_gb:.2f}GB)")
            print(f"    → {destination}")
        else:
            print(f"  ✗ {scanned_file.path.name} (no space available)")
    
    print("\nStarting pipeline...")
    print("(In production, this would monitor continuously)")
    
    # In production, this would be:
    # pipeline.start(callback=on_file_distributed)
    # time.sleep(3600)
    # pipeline.stop()


# =============================================================================
# EXAMPLE 3: Multi-Tier Storage Strategy
# =============================================================================

def example_3_multi_tier():
    """Example 3: Different strategies for different media types"""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Multi-Tier Storage with Type-Based Routing")
    print("=" * 70)
    
    from media_automation.file_distribution import (
        FileScanner,
        FileDistributor,
        OutputFolder,
        DistributionStrategy,
    )
    
    # High-performance storage for video
    video_outputs = [
        OutputFolder(Path("/nvme/videos"), max_size_gb=1000),
        OutputFolder(Path("/ssd/videos"), max_size_gb=2000),
    ]
    
    # Slower storage for archives
    archive_outputs = [
        OutputFolder(Path("/hdd/archives"), max_size_gb=5000),
    ]
    
    video_distributor = FileDistributor(
        video_outputs, strategy=DistributionStrategy.EQUAL_SIZE
    )
    
    archive_distributor = FileDistributor(
        archive_outputs, strategy=DistributionStrategy.ROUND_ROBIN
    )
    
    print("\n✓ Multi-tier storage setup")
    print("  Video Outputs: (EQUAL_SIZE strategy)")
    for out in video_outputs:
        print(f"    - {out.path} ({out.max_size_gb}GB)")
    print("  Archive Outputs: (ROUND_ROBIN strategy)")
    for out in archive_outputs:
        print(f"    - {out.path} ({out.max_size_gb}GB)")
    
    # Show routing logic
    print("\nRouting Rules:")
    print("  .mkv, .mp4, .avi → Video storage (EQUAL_SIZE)")
    print("  .zip, .7z, .rar → Archive storage (ROUND_ROBIN)")
    print("  other → Video storage (default)")


# =============================================================================
# EXAMPLE 4: Plex Media Server Integration
# =============================================================================

def example_4_plex_integration():
    """Example 4: Use Plex to organize distributed media"""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Plex Media Server Integration")
    print("=" * 70)
    
    from media_automation.adapters.media_servers_base import PlexAPIClient
    
    # Initialize Plex client
    plex = PlexAPIClient(
        base_url="http://localhost:32400",
        token="your_plex_token_here",
    )
    
    print("\n✓ Plex client initialized")
    print("  URL: http://localhost:32400")
    
    # Test connection
    print("\nTesting Plex connection...")
    if plex.test_connection():
        print("  ✓ Connected to Plex!")
        
        # Get libraries
        try:
            libraries = plex.get_libraries()
            print(f"  ✓ Found {len(libraries)} libraries:")
            for i, lib in enumerate(libraries):
                print(f"    {i+1}. {lib.get('title', 'Unknown')} ({lib.get('type')})")
        except Exception as e:
            print(f"  ℹ Could not fetch libraries: {e}")
    else:
        print("  ✗ Could not connect to Plex")


# =============================================================================
# EXAMPLE 5: Jellyfin Media Server Integration
# =============================================================================

def example_5_jellyfin_integration():
    """Example 5: Use Jellyfin as media server alternative"""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Jellyfin Media Server Integration")
    print("=" * 70)
    
    from media_automation.adapters.media_servers_base import JellyfinAPIClient
    
    # Initialize Jellyfin client
    jellyfin = JellyfinAPIClient(
        base_url="http://localhost:8096",
        api_key="your_jellyfin_api_key_here",
    )
    
    print("\n✓ Jellyfin client initialized")
    print("  URL: http://localhost:8096")
    
    # Test connection
    print("\nTesting Jellyfin connection...")
    if jellyfin.test_connection():
        print("  ✓ Connected to Jellyfin!")
        
        # Search for content
        try:
            results = jellyfin.search_items("Breaking Bad")
            print(f"  ✓ Search 'Breaking Bad': {results.get('ItemCount', 'N/A')} results")
        except Exception as e:
            print(f"  ℹ Could not search: {e}")
    else:
        print("  ✗ Could not connect to Jellyfin")


# =============================================================================
# EXAMPLE 6: qBittorrent Integration
# =============================================================================

def example_6_qbittorrent_integration():
    """Example 6: Add torrents and monitor downloads"""
    print("\n" + "=" * 70)
    print("EXAMPLE 6: qBittorrent Torrent Client Integration")
    print("=" * 70)
    
    from media_automation.adapters.media_servers_base import QBittorrentAPIClient
    
    # Initialize qBittorrent client
    qb = QBittorrentAPIClient(
        base_url="http://localhost:8080",
        username="admin",
        password="adminadmin",
    )
    
    print("\n✓ qBittorrent client initialized")
    print("  URL: http://localhost:8080")
    
    # Test connection
    print("\nTesting qBittorrent connection...")
    if qb.test_connection():
        print("  ✓ Connected to qBittorrent!")
        
        # Get torrent status
        try:
            torrents = qb.get_torrents()
            downloading = [t for t in torrents if t.get('state') == 'downloading']
            completed = [t for t in torrents if t.get('state') == 'uploading']
            
            print(f"  ✓ {len(torrents)} total torrents")
            print(f"    - Downloading: {len(downloading)}")
            print(f"    - Completed: {len(completed)}")
        except Exception as e:
            print(f"  ℹ Could not fetch torrents: {e}")
    else:
        print("  ✗ Could not connect to qBittorrent")


# =============================================================================
# EXAMPLE 7: Combined Workflow
# =============================================================================

def example_7_combined_workflow():
    """Example 7: End-to-end workflow combining all components"""
    print("\n" + "=" * 70)
    print("EXAMPLE 7: Combined Workflow - Production Setup")
    print("=" * 70)
    
    from media_automation.file_distribution import (
        FileDistributionPipeline,
        OutputFolder,
        DistributionStrategy,
    )
    from media_automation.adapters.media_servers_base import (
        PlexAPIClient,
        JellyfinAPIClient,
    )
    
    print("\n✓ Setting up production workflow:")
    print("  1. Scan input directories")
    print("  2. Distribute files to multiple outputs")
    print("  3. Trigger media server scans")
    print("  4. Monitor load and rebalance")
    
    # Setup outputs
    outputs = [
        OutputFolder(Path("/media/movies1"), max_size_gb=1000),
        OutputFolder(Path("/media/movies2"), max_size_gb=1000),
        OutputFolder(Path("/media/movies3"), max_size_gb=1000),
    ]
    
    # Create pipeline
    pipeline = FileDistributionPipeline(
        input_paths=["/ripped_media", "/downloads"],
        output_folders=outputs,
        extensions=[".mkv", ".mp4"],
        strategy=DistributionStrategy.EQUAL_SIZE,
    )
    
    # Initialize media servers
    plex = PlexAPIClient("http://localhost:32400", "token")
    jellyfin = JellyfinAPIClient("http://localhost:8096", "api_key")
    
    # Callback to trigger media server scans
    def on_file_distributed(scanned_file, destination):
        if destination:
            print(f"✓ {scanned_file.path.name}")
            print(f"  Destination: {destination}")
            
            # Trigger Plex scan
            try:
                if plex.test_connection():
                    plex.scan_library("1")
                    print("  → Plex scan triggered")
            except:
                pass
            
            # Trigger Jellyfin scan
            try:
                if jellyfin.test_connection():
                    jellyfin.refresh_library("movies")
                    print("  → Jellyfin scan triggered")
            except:
                pass
    
    print("\nWorkflow configured and ready to start")
    print("(In production, call pipeline.start(callback=on_file_distributed))")


# =============================================================================
# EXAMPLE 8: Rebalancing Monitor
# =============================================================================

def example_8_rebalancing_monitor():
    """Example 8: Monitor storage and trigger rebalancing alerts"""
    print("\n" + "=" * 70)
    print("EXAMPLE 8: Storage Rebalancing Monitor")
    print("=" * 70)
    
    from media_automation.file_distribution import (
        FileDistributor,
        OutputFolder,
        DistributionStrategy,
    )
    
    outputs = [
        OutputFolder(Path("/storage1"), max_size_gb=500),
        OutputFolder(Path("/storage2"), max_size_gb=500),
        OutputFolder(Path("/storage3"), max_size_gb=500),
    ]
    
    distributor = FileDistributor(outputs, strategy=DistributionStrategy.EQUAL_SIZE)
    
    print("\n✓ Rebalancing monitor configured")
    print("  Strategy: EQUAL_SIZE")
    print("  Outputs: 3 x 500GB")
    
    # Simulate storage states
    outputs[0].current_size_bytes = 400 * 1024**3
    outputs[1].current_size_bytes = 300 * 1024**3
    outputs[2].current_size_bytes = 200 * 1024**3
    
    print("\nCurrent storage usage:")
    status = distributor.get_load_status()
    for name, stats in status.items():
        pct = (stats['current_size_gb'] / stats['max_size_gb']) * 100
        print(f"  {name}: {stats['current_size_gb']:.0f}/{stats['max_size_gb']:.0f}GB ({pct:.1f}%)")
    
    if distributor.rebalance_if_needed():
        print("\n⚠ REBALANCING RECOMMENDED!")
        max_load = max(s['current_size_gb'] for s in status.values())
        min_load = min(s['current_size_gb'] for s in status.values())
        print(f"  Imbalance: {max_load:.0f}GB vs {min_load:.0f}GB ({max_load/min_load:.1f}x)")
    else:
        print("\n✓ Storage is well balanced")


# =============================================================================
# Main
# =============================================================================

def main():
    """Run all examples"""
    print("\n╔════════════════════════════════════════════════════════════════════╗")
    print("║  MediaAutomation: Media Servers & File Distribution Examples       ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    
    examples = [
        ("Basic Distribution", example_1_basic_distribution),
        ("Auto Scanning", example_2_auto_scanning),
        ("Multi-Tier Storage", example_3_multi_tier),
        ("Plex Integration", example_4_plex_integration),
        ("Jellyfin Integration", example_5_jellyfin_integration),
        ("qBittorrent Integration", example_6_qbittorrent_integration),
        ("Combined Workflow", example_7_combined_workflow),
        ("Rebalancing Monitor", example_8_rebalancing_monitor),
    ]
    
    for name, func in examples:
        try:
            func()
        except Exception as e:
            print(f"\n✗ Example '{name}' error: {e}")
    
    print("\n" + "=" * 70)
    print("Examples complete!")
    print("=" * 70)
    print("\nFor more information, see:")
    print("  - MEDIA_SERVERS_AND_DISTRIBUTION.md")
    print("  - File distribution class: media_automation/file_distribution.py")
    print("  - Media server classes: media_automation/adapters/media_servers_base.py")


if __name__ == "__main__":
    main()
