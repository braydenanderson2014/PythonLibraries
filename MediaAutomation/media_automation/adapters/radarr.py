from __future__ import annotations

from typing import Any, Dict

from ..interfaces import DownloadManagerAdapter
from .servarr_base import RadarrAPIClient


class RadarrAdapter(DownloadManagerAdapter):
    """Radarr movie management adapter."""

    name = "radarr"

    def __init__(self, base_url: str = "http://localhost:7878", api_key: str = "") -> None:
        """
        Initialize Radarr adapter.

        :param base_url: Radarr base URL
        :param api_key: Radarr API key
        """
        self.client = RadarrAPIClient(base_url, api_key)

    def add_entry(self, entry: Dict[str, Any]) -> bool:
        """
        Add movie to library.

        Expected entry format:
        {
            "tmdbId": 12345,
            "title": "Movie Title",
            "qualityProfileId": 1,
            "rootFolderPath": "/path/to/movies",
            "monitored": True
        }
        """
        try:
            # Search for the movie first
            search_results = self.client.search_movie(entry.get("title", ""))
            if not search_results:
                return False

            # Use first result and merge with entry params
            movie_data = search_results[0]
            movie_data.update(entry)
            movie_data["addOptions"] = {"searchForMovie": True}

            # Add to Radarr
            self.client.add_movie(movie_data)
            return True
        except Exception:
            return False

    def search_and_download(self, query: str, **kwargs) -> bool:
        """
        Search and add movie from query string.

        Additional kwargs:
        - quality_profile_id: Quality profile to use
        - root_folder_path: Root folder for downloads
        - year: Movie release year (optional filter)
        """
        try:
            results = self.client.search_movie(query)
            if not results:
                return False

            movie = results[0]
            quality_id = kwargs.get("quality_profile_id", 1)
            root_folder = kwargs.get("root_folder_path", "/movies")

            entry = {
                "tmdbId": movie.get("tmdbId"),
                "title": movie.get("title"),
                "qualityProfileId": quality_id,
                "rootFolderPath": root_folder,
                "monitored": True,
            }

            return self.add_entry(entry)
        except Exception:
            return False

    def get_library_status(self) -> Dict[str, Any]:
        """Get Radarr library status."""
        try:
            movie_list = self.client.get_movie()
            return {
                "success": True,
                "movie_count": len(movie_list) if isinstance(movie_list, list) else 0,
                "movies": movie_list,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def health_check(self) -> bool:
        """Check if Radarr is reachable."""
        return self.client.test_connection()
