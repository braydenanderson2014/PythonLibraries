from __future__ import annotations

from typing import Any, Dict, Optional

from ..interfaces import DownloadManagerAdapter
from .servarr_base import SonarrAPIClient


class SonarrAdapter(DownloadManagerAdapter):
    """Sonarr TV show management adapter."""

    name = "sonarr"

    def __init__(self, base_url: str = "http://localhost:8989", api_key: str = "") -> None:
        """
        Initialize Sonarr adapter.

        :param base_url: Sonarr base URL
        :param api_key: Sonarr API key
        """
        self.client = SonarrAPIClient(base_url, api_key)

    def add_entry(self, entry: Dict[str, Any]) -> bool:
        """
        Add TV series to library.

        Expected entry format:
        {
            "tvdbId": 12345,
            "title": "Series Name",
            "qualityProfileId": 1,
            "rootFolderPath": "/path/to/tv",
            "monitored": True,
            "seasonFolder": True
        }
        """
        try:
            # Search for the series first
            search_results = self.client.search_series(entry.get("title", ""))
            if not search_results:
                return False

            # Use first result and merge with entry params
            series_data = search_results[0]
            series_data.update(entry)
            series_data["addOptions"] = {"searchForMissingEpisodes": True}

            # Add to Sonarr
            self.client.add_series(series_data)
            return True
        except Exception:
            return False

    def search_and_download(self, query: str, **kwargs) -> bool:
        """
        Search and add series from query string.

        Additional kwargs:
        - quality_profile_id: Quality profile to use
        - root_folder_path: Root folder for downloads
        - seasons: Specific seasons to monitor
        """
        try:
            results = self.client.search_series(query)
            if not results:
                return False

            series = results[0]
            quality_id = kwargs.get("quality_profile_id", 1)
            root_folder = kwargs.get("root_folder_path", "/tv")

            entry = {
                "tvdbId": series.get("tvdbId"),
                "title": series.get("title"),
                "qualityProfileId": quality_id,
                "rootFolderPath": root_folder,
                "monitored": True,
                "seasonFolder": True,
            }

            return self.add_entry(entry)
        except Exception:
            return False

    def get_library_status(self) -> Dict[str, Any]:
        """Get Sonarr library status."""
        try:
            series_list = self.client.get_series()
            return {
                "success": True,
                "series_count": len(series_list) if isinstance(series_list, list) else 0,
                "series": series_list,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def health_check(self) -> bool:
        """Check if Sonarr is reachable."""
        return self.client.test_connection()
