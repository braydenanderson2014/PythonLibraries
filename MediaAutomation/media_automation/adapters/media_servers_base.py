from __future__ import annotations

from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

try:
    import requests
except ImportError:
    requests = None


class QBittorrentAPIClient:
    """qBittorrent WebUI API client for torrent management."""

    def __init__(self, base_url: str, username: str = "admin", password: str = "adminadmin", timeout: int = 30) -> None:
        """
        Initialize qBittorrent API client.

        :param base_url: Base URL (e.g., 'http://localhost:8080')
        :param username: WebUI username
        :param password: WebUI password
        :param timeout: Request timeout in seconds
        """
        if not requests:
            raise ImportError("requests library is required. Install with: pip install requests")

        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.timeout = timeout
        self.session = requests.Session()

    def _login(self) -> bool:
        """Authenticate with qBittorrent."""
        try:
            url = urljoin(self.base_url, "/api/v2/auth/login")
            response = self.session.post(
                url,
                data={"username": self.username, "password": self.password},
                timeout=self.timeout,
            )
            return response.status_code == 200
        except Exception:
            return False

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any] | List[Dict[str, Any]]:
        """Make API request."""
        url = urljoin(self.base_url, endpoint)
        try:
            response = self.session.request(
                method,
                url,
                data=data,
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.RequestException as e:
            raise ConnectionError(f"Failed to connect to {url}: {e}")

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any] | List:
        """GET request."""
        return self._request("GET", endpoint, params=params)

    def post(
        self, endpoint: str, data: Optional[Dict[str, Any]] = None, **kwargs
    ) -> Dict[str, Any] | List:
        """POST request."""
        return self._request("POST", endpoint, data=data, **kwargs)

    def test_connection(self) -> bool:
        """Test API connection and authentication."""
        try:
            if not self._login():
                return False
            self.get("/api/v2/app/webapiVersion")
            return True
        except Exception:
            return False

    def add_torrent(self, torrent_url: str, save_path: str = "") -> bool:
        """Add torrent from URL."""
        try:
            data = {"urls": torrent_url}
            if save_path:
                data["savepath"] = save_path
            self.post("/api/v2/torrents/add", data=data)
            return True
        except Exception:
            return False

    def add_torrent_file(self, torrent_file_path: str, save_path: str = "") -> bool:
        """Add torrent from file."""
        try:
            with open(torrent_file_path, "rb") as f:
                files = {"torrents": f}
                data = {}
                if save_path:
                    data["savepath"] = save_path
                self.session.post(
                    urljoin(self.base_url, "/api/v2/torrents/add"),
                    files=files,
                    data=data,
                    timeout=self.timeout,
                )
            return True
        except Exception:
            return False

    def get_torrents(self, status_filter: str = "all") -> List[Dict[str, Any]]:
        """Get torrent list."""
        return self.get("/api/v2/torrents/info", params={"filter": status_filter})

    def pause_torrent(self, torrent_hash: str) -> bool:
        """Pause a torrent."""
        try:
            self.post("/api/v2/torrents/pause", data={"hashes": torrent_hash})
            return True
        except Exception:
            return False

    def resume_torrent(self, torrent_hash: str) -> bool:
        """Resume a torrent."""
        try:
            self.post("/api/v2/torrents/resume", data={"hashes": torrent_hash})
            return True
        except Exception:
            return False

    def get_app_preferences(self) -> Dict[str, Any]:
        """Get application preferences."""
        return self.get("/api/v2/app/preferences")

    def set_app_preferences(self, prefs: Dict[str, Any]) -> bool:
        """Set application preferences."""
        try:
            self.post("/api/v2/app/setPreferences", data=prefs)
            return True
        except Exception:
            return False


class PlexAPIClient:
    """Plex Media Server API client."""

    def __init__(self, base_url: str, token: str, timeout: int = 30) -> None:
        """
        Initialize Plex API client.

        :param base_url: Base URL (e.g., 'http://localhost:32400')
        :param token: Plex API token
        :param timeout: Request timeout in seconds
        """
        if not requests:
            raise ImportError("requests library is required. Install with: pip install requests")

        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"X-Plex-Token": token})

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make API request."""
        url = urljoin(self.base_url, endpoint)
        try:
            response = self.session.request(
                method,
                url,
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()
            # Plex returns XML, but also supports JSON with Accept header
            try:
                return response.json()
            except ValueError:
                return {"raw": response.text}
        except requests.RequestException as e:
            raise ConnectionError(f"Failed to connect to {url}: {e}")

    def test_connection(self) -> bool:
        """Test API connection."""
        try:
            self._request("GET", "/identity")
            return True
        except Exception:
            return False

    def get_libraries(self) -> List[Dict[str, Any]]:
        """Get all media libraries."""
        try:
            result = self._request("GET", "/library/sections")
            return result.get("MediaContainer", {}).get("Directory", [])
        except Exception:
            return []

    def scan_library(self, library_key: str) -> bool:
        """Trigger library scan."""
        try:
            self._request("GET", f"/library/sections/{library_key}/refresh")
            return True
        except Exception:
            return False

    def get_library_contents(self, library_key: str) -> List[Dict[str, Any]]:
        """Get contents of a library."""
        try:
            result = self._request("GET", f"/library/sections/{library_key}/all")
            return result.get("MediaContainer", {}).get("Metadata", [])
        except Exception:
            return []


class JellyfinAPIClient:
    """Jellyfin Media Server API client."""

    def __init__(self, base_url: str, api_key: str, timeout: int = 30) -> None:
        """
        Initialize Jellyfin API client.

        :param base_url: Base URL (e.g., 'http://localhost:8096')
        :param api_key: Jellyfin API key
        :param timeout: Request timeout in seconds
        """
        if not requests:
            raise ImportError("requests library is required. Install with: pip install requests")

        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"X-MediaBrowser-Token": api_key})

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make API request."""
        url = urljoin(self.base_url, endpoint)
        try:
            response = self.session.request(
                method,
                url,
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.RequestException as e:
            raise ConnectionError(f"Failed to connect to {url}: {e}")

    def test_connection(self) -> bool:
        """Test API connection."""
        try:
            self._request("GET", "/System/Info")
            return True
        except Exception:
            return False

    def get_libraries(self) -> List[Dict[str, Any]]:
        """Get all media libraries."""
        try:
            result = self._request("GET", "/Library/VirtualFolders")
            return result
        except Exception:
            return []

    def refresh_library(self, library_id: str) -> bool:
        """Trigger library refresh/scan."""
        try:
            self._request("POST", f"/Library/Refresh?collectionId={library_id}")
            return True
        except Exception:
            return False

    def get_items(self, library_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get items from a library."""
        try:
            result = self._request(
                "GET",
                f"/Users/me/Items",
                params={"parentId": library_id, "limit": limit},
            )
            return result.get("Items", [])
        except Exception:
            return []

    def search_items(self, query: str) -> List[Dict[str, Any]]:
        """Search for items."""
        try:
            result = self._request(
                "GET",
                "/Search/Hints",
                params={"searchTerm": query},
            )
            return result.get("SearchHints", [])
        except Exception:
            return []
