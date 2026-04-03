from __future__ import annotations

import importlib
from typing import Dict, Optional

from ..interfaces import (
    DownloadManagerAdapter,
    EncoderAdapter,
    IndexerAdapter,
    MediaServerAdapter,
    RipperAdapter,
    SubtitleAdapter,
)
from .dispcam import DispCamAdapter
from .flixicam import FlixicamAdapter
from .handbrake import HandBrakeAdapter
from .jellyfin import JellyfinAdapter
from .lidarr import LidarrAdapter
from .makemkv import MakeMKVAdapter
from .plex import PlexAdapter
from .prowlarr import ProwlarrAdapter
from .qbittorrent import QBittorrentAdapter
from .radarr import RadarrAdapter
from .readarr import ReadarrAdapter
from .sonarr import SonarrAdapter
from .streamfab import StreamFabAdapter
from .subtitle_tool import SubtitleToolAdapter
from .tuneboto import TuneBotoAdapter
from .vidicable import VidicableAdapter


class AdapterRegistry:
    def __init__(self) -> None:
        self.rippers: Dict[str, RipperAdapter] = {
            MakeMKVAdapter.name: MakeMKVAdapter(),
            TuneBotoAdapter.name: TuneBotoAdapter(),
            VidicableAdapter.name: VidicableAdapter(),
            DispCamAdapter.name: DispCamAdapter(),
            FlixicamAdapter.name: FlixicamAdapter(),
            StreamFabAdapter.name: StreamFabAdapter(),
        }
        self.encoders: Dict[str, EncoderAdapter] = {
            HandBrakeAdapter.name: HandBrakeAdapter(),
        }
        self.subtitles: Dict[str, SubtitleAdapter] = {
            SubtitleToolAdapter.name: SubtitleToolAdapter(),
        }
        self.indexers: Dict[str, IndexerAdapter] = {
            ProwlarrAdapter.name: ProwlarrAdapter(),
        }
        self.download_managers: Dict[str, DownloadManagerAdapter] = {
            SonarrAdapter.name: SonarrAdapter(),
            RadarrAdapter.name: RadarrAdapter(),
            LidarrAdapter.name: LidarrAdapter(),
            ReadarrAdapter.name: ReadarrAdapter(),
            QBittorrentAdapter.name: QBittorrentAdapter(),
        }
        self.media_servers: Dict[str, MediaServerAdapter] = {
            PlexAdapter.name: PlexAdapter(),
            JellyfinAdapter.name: JellyfinAdapter(),
        }

    def register_plugin(self, import_path: str) -> None:
        """
        Import module and call register(registry) if present.
        This allows drop-in external adapters without changing core code.
        """
        module = importlib.import_module(import_path)
        register = getattr(module, "register", None)
        if callable(register):
            register(self)

    def get_ripper(self, name: str) -> RipperAdapter:
        if name not in self.rippers:
            raise KeyError(f"Unknown ripper adapter: {name}")
        return self.rippers[name]

    def get_encoder(self, name: str) -> EncoderAdapter:
        if name not in self.encoders:
            raise KeyError(f"Unknown encoder adapter: {name}")
        return self.encoders[name]

    def get_subtitle(self, name: str) -> SubtitleAdapter:
        if name not in self.subtitles:
            raise KeyError(f"Unknown subtitle adapter: {name}")
        return self.subtitles[name]

    def maybe_get_subtitle(self, name: Optional[str]) -> Optional[SubtitleAdapter]:
        if not name:
            return None
        return self.get_subtitle(name)

    def get_indexer(self, name: str) -> IndexerAdapter:
        if name not in self.indexers:
            raise KeyError(f"Unknown indexer adapter: {name}")
        return self.indexers[name]

    def maybe_get_indexer(self, name: Optional[str]) -> Optional[IndexerAdapter]:
        if not name:
            return None
        return self.get_indexer(name)

    def get_download_manager(self, name: str) -> DownloadManagerAdapter:
        if name not in self.download_managers:
            raise KeyError(f"Unknown download manager adapter: {name}")
        return self.download_managers[name]

    def maybe_get_download_manager(self, name: Optional[str]) -> Optional[DownloadManagerAdapter]:
        if not name:
            return None
        return self.get_download_manager(name)

    def get_media_server(self, name: str) -> MediaServerAdapter:
        if name not in self.media_servers:
            raise KeyError(f"Unknown media server adapter: {name}")
        return self.media_servers[name]

    def maybe_get_media_server(self, name: Optional[str]) -> Optional[MediaServerAdapter]:
        if not name:
            return None
        return self.get_media_server(name)
