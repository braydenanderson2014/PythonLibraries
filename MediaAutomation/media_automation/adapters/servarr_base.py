from __future__ import annotations

import json
from typing import Any, Dict, Optional
from urllib.parse import urljoin

try:
    import requests
except ImportError:
    requests = None


class ServarrAPIClient:
    """Base class for Servarr stack API clients (Sonarr, Radarr, Lidarr, etc.)"""

    def __init__(self, base_url: str, api_key: str, timeout: int = 30) -> None:
        """
        Initialize Servarr API client.

        :param base_url: Base URL (e.g., 'http://localhost:8989')
        :param api_key: API key from service settings
        :param timeout: Request timeout in seconds
        """
        if not requests:
            raise ImportError("requests library is required. Install with: pip install requests")

        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"X-Api-Key": api_key, "Content-Type": "application/json"})

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make API request.

        :param method: HTTP method (GET, POST, PUT, DELETE)
        :param endpoint: API endpoint (relative to base URL)
        :param data: Request body data
        :param params: Query parameters
        :return: Response JSON as dict
        """
        url = urljoin(self.base_url, endpoint)
        try:
            response = self.session.request(
                method,
                url,
                json=data,
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.RequestException as e:
            raise ConnectionError(f"Failed to connect to {url}: {e}")

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """GET request."""
        return self._request("GET", endpoint, params=params)

    def post(
        self, endpoint: str, data: Optional[Dict[str, Any]] = None, **kwargs
    ) -> Dict[str, Any]:
        """POST request."""
        return self._request("POST", endpoint, data=data, **kwargs)

    def put(
        self, endpoint: str, data: Optional[Dict[str, Any]] = None, **kwargs
    ) -> Dict[str, Any]:
        """PUT request."""
        return self._request("PUT", endpoint, data=data, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """DELETE request."""
        return self._request("DELETE", endpoint, **kwargs)

    def test_connection(self) -> bool:
        """Test API connection."""
        try:
            self.get("/api/v3/system/status")
            return True
        except (ConnectionError, Exception):
            return False


class ProwlarrAPIClient(ServarrAPIClient):
    """Prowlarr API client for indexer management."""

    def get_indexers(self) -> list[Dict[str, Any]]:
        """Get all indexers."""
        return self.get("/api/v1/indexer")

    def add_indexer(self, indexer_config: Dict[str, Any]) -> Dict[str, Any]:
        """Add new indexer."""
        return self.post("/api/v1/indexer", data=indexer_config)

    def search(self, query: str, categories: Optional[list[int]] = None) -> Dict[str, Any]:
        """Search via all indexers."""
        params = {"query": query}
        if categories:
            params["categories"] = ",".join(map(str, categories))
        return self.get("/api/v1/search", params=params)


class SonarrAPIClient(ServarrAPIClient):
    """Sonarr API client for TV show management."""

    def add_series(self, series_params: Dict[str, Any]) -> Dict[str, Any]:
        """Add series to library."""
        return self.post("/api/v3/series", data=series_params)

    def search_series(self, term: str) -> list[Dict[str, Any]]:
        """Search for series."""
        return self.get("/api/v3/series/lookup", params={"term": term})

    def get_series(self, series_id: Optional[int] = None) -> Dict[str, Any] | list[Dict[str, Any]]:
        """Get series by ID or all series."""
        endpoint = f"/api/v3/series/{series_id}" if series_id else "/api/v3/series"
        return self.get(endpoint)

    def trigger_search(self, series_id: int, season: int = 0) -> Dict[str, Any]:
        """Trigger search for series/season."""
        return self.post(
            "/api/v3/command",
            data={"name": "SeriesSearch", "seriesId": series_id, "seasonNumber": season},
        )


class RadarrAPIClient(ServarrAPIClient):
    """Radarr API client for movie management."""

    def add_movie(self, movie_params: Dict[str, Any]) -> Dict[str, Any]:
        """Add movie to library."""
        return self.post("/api/v3/movie", data=movie_params)

    def search_movie(self, term: str) -> list[Dict[str, Any]]:
        """Search for movie."""
        return self.get("/api/v3/movie/lookup", params={"term": term})

    def get_movie(self, movie_id: Optional[int] = None) -> Dict[str, Any] | list[Dict[str, Any]]:
        """Get movie by ID or all movies."""
        endpoint = f"/api/v3/movie/{movie_id}" if movie_id else "/api/v3/movie"
        return self.get(endpoint)

    def trigger_search(self, movie_id: int) -> Dict[str, Any]:
        """Trigger search for movie."""
        return self.post(
            "/api/v3/command",
            data={"name": "MoviesSearch", "movieIds": [movie_id]},
        )


class LidarrAPIClient(ServarrAPIClient):
    """Lidarr API client for music management."""

    def add_artist(self, artist_params: Dict[str, Any]) -> Dict[str, Any]:
        """Add artist to library."""
        return self.post("/api/v1/artist", data=artist_params)

    def search_artist(self, term: str) -> list[Dict[str, Any]]:
        """Search for artist."""
        return self.get("/api/v1/artist/lookup", params={"term": term})

    def get_artist(self, artist_id: Optional[int] = None) -> Dict[str, Any] | list[Dict[str, Any]]:
        """Get artist by ID or all artists."""
        endpoint = f"/api/v1/artist/{artist_id}" if artist_id else "/api/v1/artist"
        return self.get(endpoint)

    def trigger_search(self, artist_id: int) -> Dict[str, Any]:
        """Trigger search for artist."""
        return self.post(
            "/api/v1/command",
            data={"name": "ArtistSearch", "artistId": artist_id},
        )


class ReadarrAPIClient(ServarrAPIClient):
    """Readarr API client for book management."""

    def add_author(self, author_params: Dict[str, Any]) -> Dict[str, Any]:
        """Add author to library."""
        return self.post("/api/v1/author", data=author_params)

    def search_author(self, term: str) -> list[Dict[str, Any]]:
        """Search for author."""
        return self.get("/api/v1/author/lookup", params={"term": term})

    def get_author(self, author_id: Optional[int] = None) -> Dict[str, Any] | list[Dict[str, Any]]:
        """Get author by ID or all authors."""
        endpoint = f"/api/v1/author/{author_id}" if author_id else "/api/v1/author"
        return self.get(endpoint)

    def trigger_search(self, author_id: int) -> Dict[str, Any]:
        """Trigger search for author."""
        return self.post(
            "/api/v1/command",
            data={"name": "AuthorSearch", "authorId": author_id},
        )
