from __future__ import annotations

from typing import Any, Dict

from ..interfaces import DownloadManagerAdapter
from .servarr_base import ReadarrAPIClient


class ReadarrAdapter(DownloadManagerAdapter):
    """Readarr book management adapter."""

    name = "readarr"

    def __init__(self, base_url: str = "http://localhost:8787", api_key: str = "") -> None:
        """
        Initialize Readarr adapter.

        :param base_url: Readarr base URL
        :param api_key: Readarr API key
        """
        self.client = ReadarrAPIClient(base_url, api_key)

    def add_entry(self, entry: Dict[str, Any]) -> bool:
        """
        Add author to library.

        Expected entry format:
        {
            "foreignAuthorId": "author-id",
            "authorName": "Author Name",
            "qualityProfileId": 1,
            "metadataProfileId": 1,
            "rootFolderPath": "/path/to/books",
            "monitored": True
        }
        """
        try:
            # Search for the author first
            search_results = self.client.search_author(entry.get("authorName", ""))
            if not search_results:
                return False

            # Use first result and merge with entry params
            author_data = search_results[0]
            author_data.update(entry)
            author_data["addOptions"] = {"searchForMissingBooks": True}

            # Add to Readarr
            self.client.add_author(author_data)
            return True
        except Exception:
            return False

    def search_and_download(self, query: str, **kwargs) -> bool:
        """
        Search and add author from query string.

        Additional kwargs:
        - quality_profile_id: Quality profile to use
        - metadata_profile_id: Metadata profile to use
        - root_folder_path: Root folder for downloads
        """
        try:
            results = self.client.search_author(query)
            if not results:
                return False

            author = results[0]
            quality_id = kwargs.get("quality_profile_id", 1)
            metadata_id = kwargs.get("metadata_profile_id", 1)
            root_folder = kwargs.get("root_folder_path", "/books")

            entry = {
                "foreignAuthorId": author.get("foreignAuthorId"),
                "authorName": author.get("authorName", author.get("name")),
                "qualityProfileId": quality_id,
                "metadataProfileId": metadata_id,
                "rootFolderPath": root_folder,
                "monitored": True,
            }

            return self.add_entry(entry)
        except Exception:
            return False

    def get_library_status(self) -> Dict[str, Any]:
        """Get Readarr library status."""
        try:
            authors_list = self.client.get_author()
            return {
                "success": True,
                "author_count": len(authors_list) if isinstance(authors_list, list) else 0,
                "authors": authors_list,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def health_check(self) -> bool:
        """Check if Readarr is reachable."""
        return self.client.test_connection()
