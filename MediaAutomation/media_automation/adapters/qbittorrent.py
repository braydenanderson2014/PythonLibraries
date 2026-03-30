from __future__ import annotations

from typing import Any, Dict

from ..interfaces import DownloadManagerAdapter
from .media_servers_base import QBittorrentAPIClient


class QBittorrentAdapter(DownloadManagerAdapter):
    """qBittorrent torrent download manager adapter."""

    name = "qbittorrent"

    def __init__(
        self,
        base_url: str = "http://localhost:8080",
        username: str = "admin",
        password: str = "adminadmin",
    ) -> None:
        """
        Initialize qBittorrent adapter.

        :param base_url: qBittorrent WebUI URL
        :param username: WebUI username
        :param password: WebUI password
        """
        self.client = QBittorrentAPIClient(base_url, username, password)

    def add_entry(self, entry: Dict[str, Any]) -> bool:
        """
        Add torrent to download queue.

        Expected entry format:
        {
            "url": "magnet:...",  # or .torrent file path
            "save_path": "/downloads/movies",
            "paused": False
        }
        """
        try:
            url_or_path = entry.get("url", entry.get("magnet", entry.get("path")))
            save_path = entry.get("save_path", "")

            if url_or_path.startswith(("http://", "https://", "magnet:")):
                return self.client.add_torrent(url_or_path, save_path)
            else:
                return self.client.add_torrent_file(url_or_path, save_path)
        except Exception:
            return False

    def search_and_download(self, query: str, **kwargs) -> bool:
        """
        Search for torrent and download (requires external search service).

        This adapter needs integration with search service like Prowlarr.
        For now, this would be called after Prowlarr returns a magnet link.
        """
        try:
            magnet = kwargs.get("magnet_link")
            save_path = kwargs.get("save_path", "/downloads")
            if magnet:
                return self.client.add_torrent(magnet, save_path)
            return False
        except Exception:
            return False

    def get_library_status(self) -> Dict[str, Any]:
        """Get qBittorrent library status (active torrents)."""
        try:
            torrents = self.client.get_torrents()
            completed = [t for t in torrents if t.get("state") == "uploading"]
            downloading = [t for t in torrents if t.get("state") == "downloading"]

            return {
                "success": True,
                "total_count": len(torrents),
                "downloading": len(downloading),
                "completed": len(completed),
                "torrents": torrents,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def health_check(self) -> bool:
        """Check if qBittorrent is reachable."""
        return self.client.test_connection()
