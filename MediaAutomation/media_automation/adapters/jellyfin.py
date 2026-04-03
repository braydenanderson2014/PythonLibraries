from __future__ import annotations

from typing import Any, Dict

from ..interfaces import MediaServerAdapter
from .media_servers_base import JellyfinAPIClient


class JellyfinAdapter(MediaServerAdapter):
    """Jellyfin Media Server adapter."""

    name = "jellyfin"

    def __init__(self, base_url: str = "http://localhost:8096", api_key: str = "") -> None:
        """
        Initialize Jellyfin adapter.

        :param base_url: Jellyfin server base URL
        :param api_key: Jellyfin API key
        """
        self.client = JellyfinAPIClient(base_url, api_key)

    def get_libraries(self) -> Dict[str, Any]:
        """Get all media libraries."""
        try:
            libraries = self.client.get_libraries()
            return {
                "success": True,
                "libraries": [
                    {
                        "id": lib.get("ItemId"),
                        "name": lib.get("Name"),
                        "type": lib.get("CollectionType"),
                    }
                    for lib in libraries
                ],
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def scan_library(self, library_id: str) -> bool:
        """Trigger library scan/refresh."""
        try:
            return self.client.refresh_library(library_id)
        except Exception:
            return False

    def search_items(self, query: str) -> Dict[str, Any]:
        """Search for items in libraries."""
        try:
            results = self.client.search_items(query)
            return {
                "success": True,
                "query": query,
                "result_count": len(results),
                "results": results[:20],  # Return first 20 results
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_library_contents(self, library_id: str) -> Dict[str, Any]:
        """Get contents of a specific library."""
        try:
            items = self.client.get_items(library_id)
            return {
                "success": True,
                "library_id": library_id,
                "item_count": len(items),
                "items": items,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def health_check(self) -> bool:
        """Check if Jellyfin is reachable."""
        return self.client.test_connection()
