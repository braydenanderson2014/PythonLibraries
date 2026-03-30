"""
Media Automation System - Application Launcher

Starts the UI and initializes all system components.

Usage:
    python media_automation_app.py

Requirements:
    - PyQt6
    - croniter
    - requests
"""

import sys
import os
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import QApplication, QSplashScreen
from PyQt6.QtGui import QPixmap, QPalette, QFont, QColor
from PyQt6.QtCore import Qt, QTimer
import json

from event_system import initialize_event_system
from task_manager import TaskManager
from scheduler import TaskScheduler
from gui.main_window import MediaAutomationUI
from media_automation.adapters.factory import AdapterRegistry
from media_automation.adapters.prowlarr import ProwlarrAdapter
from media_automation.adapters.sonarr import SonarrAdapter
from media_automation.adapters.radarr import RadarrAdapter
from media_automation.adapters.lidarr import LidarrAdapter
from media_automation.adapters.readarr import ReadarrAdapter
from media_automation.adapters.qbittorrent import QBittorrentAdapter
from media_automation.adapters.plex import PlexAdapter
from media_automation.adapters.jellyfin import JellyfinAdapter


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('media_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_config(config_path: str = "config.json") -> dict:
    """Load configuration from JSON file."""
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        else:
            logger.warning(f"Configuration file not found at {config_path}")
            return {}
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return {}


def _is_enabled(cfg: dict, key: str = "api_key") -> bool:
    """Treat service config as enabled if explicit flag is true or key value is provided."""
    return bool(cfg.get("enabled", False) or cfg.get(key))


def build_adapter_registry(config: dict) -> AdapterRegistry:
    """Create adapter registry using enabled services from config."""
    registry = AdapterRegistry()

    # Keep non-service adapters as created by default, but rebuild service groups from config.
    registry.indexers = {}
    registry.download_managers = {}
    registry.media_servers = {}

    servarr = config.get("servarr", {}) if isinstance(config, dict) else {}
    dm_cfg = config.get("download_managers", {}) if isinstance(config, dict) else {}
    media_cfg = config.get("media_servers", {}) if isinstance(config, dict) else {}

    prowlarr_cfg = servarr.get("prowlarr", {})
    if _is_enabled(prowlarr_cfg):
        registry.indexers["prowlarr"] = ProwlarrAdapter(
            base_url=prowlarr_cfg.get("base_url", "http://localhost:9696"),
            api_key=prowlarr_cfg.get("api_key", ""),
        )

    sonarr_cfg = servarr.get("sonarr", {})
    if _is_enabled(sonarr_cfg):
        registry.download_managers["sonarr"] = SonarrAdapter(
            base_url=sonarr_cfg.get("base_url", "http://localhost:8989"),
            api_key=sonarr_cfg.get("api_key", ""),
        )

    radarr_cfg = servarr.get("radarr", {})
    if _is_enabled(radarr_cfg):
        registry.download_managers["radarr"] = RadarrAdapter(
            base_url=radarr_cfg.get("base_url", "http://localhost:7878"),
            api_key=radarr_cfg.get("api_key", ""),
        )

    lidarr_cfg = servarr.get("lidarr", {})
    if _is_enabled(lidarr_cfg):
        registry.download_managers["lidarr"] = LidarrAdapter(
            base_url=lidarr_cfg.get("base_url", "http://localhost:8686"),
            api_key=lidarr_cfg.get("api_key", ""),
        )

    readarr_cfg = servarr.get("readarr", {})
    if _is_enabled(readarr_cfg):
        registry.download_managers["readarr"] = ReadarrAdapter(
            base_url=readarr_cfg.get("base_url", "http://localhost:8787"),
            api_key=readarr_cfg.get("api_key", ""),
        )

    qb_cfg = dm_cfg.get("qbittorrent", {})
    if bool(qb_cfg.get("enabled", False) or qb_cfg.get("base_url")):
        registry.download_managers["qbittorrent"] = QBittorrentAdapter(
            base_url=qb_cfg.get("base_url", "http://localhost:8080"),
            username=qb_cfg.get("username", "admin"),
            password=qb_cfg.get("password", "adminadmin"),
        )

    plex_cfg = media_cfg.get("plex", {})
    if _is_enabled(plex_cfg):
        registry.media_servers["plex"] = PlexAdapter(
            base_url=plex_cfg.get("base_url", "http://localhost:32400"),
            token=plex_cfg.get("api_key", ""),
        )

    jelly_cfg = media_cfg.get("jellyfin", {})
    if _is_enabled(jelly_cfg):
        registry.media_servers["jellyfin"] = JellyfinAdapter(
            base_url=jelly_cfg.get("base_url", "http://localhost:8096"),
            api_key=jelly_cfg.get("api_key", ""),
        )

    logger.info(
        "Configured adapters: %d indexers, %d download managers, %d media servers",
        len(registry.indexers),
        len(registry.download_managers),
        len(registry.media_servers),
    )
    return registry


def setup_splash_screen(app: QApplication):
    """Create and show a splash screen."""
    splash = QSplashScreen()
    splash.setWindowTitle("Media Automation System - Starting...")
    
    # Create a gradient background
    pixmap = QPixmap(600, 400)
    pixmap.fill(QColor("#1E1E1E"))
    
    splash.setPixmap(pixmap)
    
    # Add text to splash
    splash.showMessage(
        "Media Automation System\n\nInitializing components...",
        Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter,
        QColor("#0078D4")
    )
    
    splash.show()
    app.processEvents()
    
    return splash


def main():
    """Main entry point for the application."""
    logger.info("="*60)
    logger.info("Media Automation System Starting")
    logger.info("="*60)
    
    try:
        # Create Qt application
        app = QApplication.instance() or QApplication(sys.argv)
        
        # Show splash screen
        splash = setup_splash_screen(app)
        
        # Initialize event system
        splash.showMessage(
            "Initializing event system...",
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter,
            QColor("#0078D4")
        )
        app.processEvents()
        
        event_bus, status_tracker = initialize_event_system()
        logger.info("Event system initialized")

        # Load configuration early so adapters can be wired before task manager startup.
        splash.showMessage(
            "Loading configuration...",
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter,
            QColor("#0078D4")
        )
        app.processEvents()

        config = load_config()
        registry = build_adapter_registry(config)
        logger.info("Configuration and adapters loaded")
        
        # Create task manager
        splash.showMessage(
            "Initializing task manager...",
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter,
            QColor("#0078D4")
        )
        app.processEvents()
        
        task_manager = TaskManager(
            event_bus=event_bus,
            status_tracker=status_tracker,
            adapters_factory=registry,
            config=config,
            config_path="config.json",
        )
        task_scheduler = task_manager.get_scheduler()
        logger.info("Task manager initialized")
        
        # Setup default tasks from configuration
        if "scheduler" in config:
            scheduler_config = config["scheduler"]
            
            # Setup health check task if enabled
            if scheduler_config.get("enable_health_check", True):
                health_check_interval = scheduler_config.get("health_check_interval_minutes", 30)
                task_id = task_manager.schedule_service_health_check(
                    interval_value=health_check_interval,
                    interval_unit="minutes"
                )
                logger.info(f"Scheduled service health check every {health_check_interval} minutes")
        
        # Create and show main UI
        splash.showMessage(
            "Loading user interface...",
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter,
            QColor("#0078D4")
        )
        app.processEvents()
        
        window = MediaAutomationUI(task_manager, task_scheduler, status_tracker, event_bus)
        window.show()
        
        # Hide splash screen
        QTimer.singleShot(500, splash.close)
        
        logger.info("Application started successfully")
        logger.info("="*60)
        
        # Start event loop
        sys.exit(app.exec())
        
    except Exception as e:
        logger.critical(f"Error starting application: {e}", exc_info=True)
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
