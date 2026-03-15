from __future__ import annotations

"""Stock API abstraction layer.

Currently provides a MockStockAPIClient that fabricates data. A real
implementation can subclass StockAPIClient and override fetch_quotes.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any
from datetime import datetime
import random
from assets.Logger import Logger
logger = Logger()


class StockAPIClient(ABC):
    """Abstract base for quote providers."""

    @abstractmethod
    def fetch_quotes(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """Return mapping symbol -> raw data dict.

        Expected keys (flexible): price/latest_price, previous_close, volume, market_cap.
        Implementations may add additional keys.
        """
        raise NotImplementedError


class MockStockAPIClient(StockAPIClient):
    """Simple mock provider producing pseudo-random prices.

    Useful for development without hitting a real API.
    """

    def __init__(self, seed: int | None = None):
        logger.debug("MockStockAPIClient", f"Initializing MockStockAPIClient with seed={seed}")
        self.random = random.Random(seed)
        self._state: Dict[str, float] = {}
        logger.info("MockStockAPIClient", "MockStockAPIClient initialized successfully")

    def fetch_quotes(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        logger.debug("MockStockAPIClient", f"Fetching quotes for {len(symbols)} symbols: {symbols}")
        now = datetime.utcnow().isoformat()
        out: Dict[str, Dict[str, Any]] = {}
        for sym in symbols:
            base = self._state.get(sym, self.random.uniform(10, 300))
            # random walk small movement
            change = self.random.uniform(-0.02, 0.02) * base
            price = max(0.01, base + change)
            self._state[sym] = price
            out[sym] = {
                'symbol': sym,
                'latest_price': round(price, 2),
                'previous_close': round(base, 2),
                'volume': int(self.random.uniform(50_000, 5_000_000)),
                'market_cap': round(price * self.random.uniform(10_000_000, 500_000_000), 2),
                'timestamp': now,
            }
            logger.debug("MockStockAPIClient", f"Generated quote for {sym}: ${price:.2f}")
        logger.info("MockStockAPIClient", f"Successfully fetched {len(out)} quotes")
        return out


__all__ = ["StockAPIClient", "MockStockAPIClient"]
