from __future__ import annotations

from typing import Any, Dict

from ..interfaces import MediaServerAdapter
from .media_servers_base import PlexAPIClient


class PlexAdapter(MediaServerAdapter):
    """Plex Media Server adapter."""

    name = "plex"

    def __init__(self, base_url: str = "http://localhost:32400", token: str = "") -> None:
        """
        Initialize Plex adapter.

        :param base_url: Plex server base URL
        :param token: Plex API token
        """
        self.client = PlexAPIClient(base_url, token)

    def get_libraries(self) -> Dict[str, Any]:
        """Get all media libraries."""
        try:
            libraries = self.client.get_libraries()
            return {
                "success": True,
                "libraries": [
                    {
                        "id": lib.get("key"),
                        "title": lib.get("title"),
                        "type": lib.get("type"),
                    }
                    for lib in libraries
                ],
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def scan_library(self, library_id: str) -> bool:
        """Trigger library scan."""
        try:
            return self.client.scan_library(library_id)
        except Exception:
            return False

    def search_items(self, query: str) -> Dict[str, Any]:
        """Search for items across all libraries."""
        try:
            # Plex doesn't have direct search API in traditional sense
            # This is a placeholder - would need Plex global search integration
            return {
                "success": True,
                "query": query,
                "results": [],
                "note": "Use Plex web UI for full search capabilities",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_library_contents(self, library_id: str) -> Dict[str, Any]:
        """Get contents of a specific library."""
        try:
            contents = self.client.get_library_contents(library_id)
            return {
                "success": True,
                "library_id": library_id,
                "item_count": len(contents),
                "items": contents[:50],  # Return first 50 for preview
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def health_check(self) -> bool:
        """Check if Plex is reachable."""
        return self.client.test_connection()
