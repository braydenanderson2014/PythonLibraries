from __future__ import annotations

from typing import Any, Dict

from ..interfaces import IndexerAdapter
from .servarr_base import ProwlarrAPIClient


class ProwlarrAdapter(IndexerAdapter):
    """Prowlarr indexer aggregator adapter."""

    name = "prowlarr"

    def __init__(self, base_url: str = "http://localhost:9696", api_key: str = "") -> None:
        """
        Initialize Prowlarr adapter.

        :param base_url: Prowlarr base URL
        :param api_key: Prowlarr API key
        """
        self.client = ProwlarrAPIClient(base_url, api_key)

    def search(self, query: str, **kwargs) -> Dict[str, Any]:
        """Search across all configured indexers."""
        try:
            categories = kwargs.get("categories")
            results = self.client.search(query, categories=categories)
            return {
                "success": True,
                "query": query,
                "results": results,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def add_indexer(self, indexer_config: Dict[str, Any]) -> bool:
        """Add or reconfigure an indexer."""
        try:
            self.client.add_indexer(indexer_config)
            return True
        except Exception:
            return False

    def health_check(self) -> bool:
        """Check if Prowlarr is reachable."""
        return self.client.test_connection()
