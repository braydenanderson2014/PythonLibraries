from __future__ import annotations

import json, os
from typing import Dict, List
try:
    from .app_paths import WATCHLIST_DB
except ImportError:
    from app_paths import WATCHLIST_DB
from assets.Logger import Logger
logger = Logger()


class WatchlistManager:
    """Maintains per-user watchlists of symbols."""

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or WATCHLIST_DB
        logger.debug("WatchlistManager", f"Initializing WatchlistManager with database: {self.db_path}")
        self._data: Dict[str, List[str]] = {}
        self.load()
        logger.info("WatchlistManager", f"WatchlistManager initialized with {len(self._data)} user(s)")

    def load(self):
        logger.debug("WatchlistManager", f"Loading watchlist data from {self.db_path}")
        if os.path.exists(self.db_path):
            try:
                self._data = json.load(open(self.db_path, 'r', encoding='utf-8'))
                logger.info("WatchlistManager", f"Loaded watchlists for {len(self._data)} user(s)")
            except Exception as e:
                logger.error("WatchlistManager", f"Failed to load watchlist data: {e}")
                self._data = {}
        else:
            logger.debug("WatchlistManager", f"Watchlist database not found at {self.db_path}")
            self._data = {}

    def save(self):
        try:
            logger.debug("WatchlistManager", f"Saving watchlist data for {len(self._data)} user(s)")
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            json.dump(self._data, open(self.db_path, 'w', encoding='utf-8'), indent=2)
            logger.info("WatchlistManager", "Watchlist data saved")
        except Exception as e:
            logger.error("WatchlistManager", f"Failed to save watchlist data: {e}")

    def add_symbol(self, username: str, symbol: str):
        logger.debug("WatchlistManager", f"Adding symbol {symbol} to watchlist for {username}")
        symbol = symbol.upper()
        lst = self._data.setdefault(username, [])
        if symbol not in lst:
            lst.append(symbol)
            self.save()
            logger.info("WatchlistManager", f"Added symbol {symbol} to {username}'s watchlist")
        else:
            logger.warning("WatchlistManager", f"Symbol {symbol} already in {username}'s watchlist")

    def remove_symbol(self, username: str, symbol: str) -> bool:
        logger.debug("WatchlistManager", f"Removing symbol {symbol} from {username}'s watchlist")
        symbol = symbol.upper()
        lst = self._data.get(username)
        if not lst or symbol not in lst:
            logger.warning("WatchlistManager", f"Symbol {symbol} not found in {username}'s watchlist")
            return False
        lst.remove(symbol)
        self.save()
        logger.info("WatchlistManager", f"Removed symbol {symbol} from {username}'s watchlist")
        return True

    def list_symbols(self, username: str) -> List[str]:
        symbols = list(self._data.get(username, []))
        logger.debug("WatchlistManager", f"Listed {len(symbols)} symbols for {username}")
        return symbols

__all__ = ["WatchlistManager"]
