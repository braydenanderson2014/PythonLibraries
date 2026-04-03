from __future__ import annotations

from typing import Any, Dict

from ..interfaces import DownloadManagerAdapter
from .servarr_base import LidarrAPIClient


class LidarrAdapter(DownloadManagerAdapter):
    """Lidarr music management adapter."""

    name = "lidarr"

    def __init__(self, base_url: str = "http://localhost:8686", api_key: str = "") -> None:
        """
        Initialize Lidarr adapter.

        :param base_url: Lidarr base URL
        :param api_key: Lidarr API key
        """
        self.client = LidarrAPIClient(base_url, api_key)

    def add_entry(self, entry: Dict[str, Any]) -> bool:
        """
        Add artist to library.

        Expected entry format:
        {
            "foreignArtistId": "artist-id",
            "artistName": "Artist Name",
            "qualityProfileId": 1,
            "metadataProfileId": 1,
            "rootFolderPath": "/path/to/music",
            "monitored": True
        }
        """
        try:
            # Search for the artist first
            search_results = self.client.search_artist(entry.get("artistName", ""))
            if not search_results:
                return False

            # Use first result and merge with entry params
            artist_data = search_results[0]
            artist_data.update(entry)
            artist_data["addOptions"] = {"searchForMissingAlbums": True}

            # Add to Lidarr
            self.client.add_artist(artist_data)
            return True
        except Exception:
            return False

    def search_and_download(self, query: str, **kwargs) -> bool:
        """
        Search and add artist from query string.

        Additional kwargs:
        - quality_profile_id: Quality profile to use
        - metadata_profile_id: Metadata profile to use
        - root_folder_path: Root folder for downloads
        """
        try:
            results = self.client.search_artist(query)
            if not results:
                return False

            artist = results[0]
            quality_id = kwargs.get("quality_profile_id", 1)
            metadata_id = kwargs.get("metadata_profile_id", 1)
            root_folder = kwargs.get("root_folder_path", "/music")

            entry = {
                "foreignArtistId": artist.get("foreignArtistId"),
                "artistName": artist.get("artistName", artist.get("name")),
                "qualityProfileId": quality_id,
                "metadataProfileId": metadata_id,
                "rootFolderPath": root_folder,
                "monitored": True,
            }

            return self.add_entry(entry)
        except Exception:
            return False

    def get_library_status(self) -> Dict[str, Any]:
        """Get Lidarr library status."""
        try:
            artists_list = self.client.get_artist()
            return {
                "success": True,
                "artist_count": len(artists_list) if isinstance(artists_list, list) else 0,
                "artists": artists_list,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def health_check(self) -> bool:
        """Check if Lidarr is reachable."""
        return self.client.test_connection()
