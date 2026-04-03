from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional

from .models import JobArtifacts, JobConfig, PipelineContext


class RipperAdapter(ABC):
    name: str

    @abstractmethod
    def rip(self, ctx: PipelineContext, job: JobConfig, artifacts: JobArtifacts) -> Path:
        """Rip or acquire source media and return output file path."""


class SubtitleAdapter(ABC):
    name: str

    @abstractmethod
    def process(self, ctx: PipelineContext, job: JobConfig, artifacts: JobArtifacts) -> Path:
        """Generate/process subtitles and return resulting media file path."""


class EncoderAdapter(ABC):
    name: str

    @abstractmethod
    def encode(self, ctx: PipelineContext, job: JobConfig, artifacts: JobArtifacts) -> Path:
        """Encode input media and return output file path."""


class IndexerAdapter(ABC):
    """Adapter for indexer services (Prowlarr, etc.)"""
    name: str

    @abstractmethod
    def search(self, query: str, **kwargs) -> Dict[str, Any]:
        """Search for content and return results."""

    @abstractmethod
    def add_indexer(self, indexer_config: Dict[str, Any]) -> bool:
        """Add or configure an indexer."""

    @abstractmethod
    def health_check(self) -> bool:
        """Health check/ping to service."""


class DownloadManagerAdapter(ABC):
    """Adapter for download managers (Sonarr, Radarr, Lidarr, etc.)"""
    name: str

    @abstractmethod
    def add_entry(self, entry: Dict[str, Any]) -> bool:
        """Add show/movie/music to library and trigger search."""

    @abstractmethod
    def search_and_download(self, query: str, **kwargs) -> bool:
        """Search for and download content."""

    @abstractmethod
    def get_library_status(self) -> Dict[str, Any]:
        """Get current library status."""

    @abstractmethod
    def health_check(self) -> bool:
        """Health check/ping to service."""


class MediaServerAdapter(ABC):
    """Adapter for media servers (Plex, Jellyfin, etc.)"""
    name: str

    @abstractmethod
    def get_libraries(self) -> Dict[str, Any]:
        """Get available libraries/collections."""

    @abstractmethod
    def scan_library(self, library_id: str) -> bool:
        """Trigger library scan/refresh."""

    @abstractmethod
    def search_items(self, query: str) -> Dict[str, Any]:
        """Search for items in library."""

    @abstractmethod
    def get_library_contents(self, library_id: str) -> Dict[str, Any]:
        """Get contents of a specific library."""

    @abstractmethod
    def health_check(self) -> bool:
        """Health check/ping to service."""
