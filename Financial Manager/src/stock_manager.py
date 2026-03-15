from __future__ import annotations

"""Coordinator that periodically refreshes stock quotes.

Integrates with either PyQt (QTimer) or a background thread fallback.
"""

from typing import Callable, List, Optional
from datetime import timedelta
import threading
import time
from assets.Logger import Logger
logger = Logger()

try:  # optional PyQt integration
    from PyQt6.QtCore import QTimer, QObject, pyqtSignal
except Exception:  # pragma: no cover - PyQt may not be present in some test contexts
    QTimer = None  # type: ignore
    QObject = object  # type: ignore
    def pyqtSignal(*_a, **_k):  # type: ignore
        return None

try:
    from .stock_data import StockDataManager, StockView, Candle
    from .stock_api import StockAPIClient, MockStockAPIClient
    from .data_sources import create_default_provider, QuoteProvider
    from .stock import Stock
    from .refresh_manager import RefreshManager
    from ui.stock_data_manager import get_stock_data_manager
    from .stock_alerts import get_stock_alert_manager
except Exception:  # pragma: no cover - fallback when run as loose script
    from stock_data import StockDataManager, StockView, Candle  # type: ignore
    from stock_api import StockAPIClient, MockStockAPIClient  # type: ignore
    from data_sources import create_default_provider, QuoteProvider  # type: ignore
    from stock import Stock  # type: ignore
    from refresh_manager import RefreshManager  # type: ignore
    from stock_data_manager import get_stock_data_manager  # type: ignore


# Global refresh manager shared by all widgets
_global_refresh_manager: Optional[RefreshManager] = None

def get_refresh_manager() -> RefreshManager:
    """Get or create the global refresh manager."""
    global _global_refresh_manager
    if _global_refresh_manager is None:
        logger.debug("StockManager", "Creating global RefreshManager instance")
        _global_refresh_manager = RefreshManager()
        logger.info("StockManager", "Global RefreshManager instance created")
    return _global_refresh_manager


class StockManager(QObject):  # type: ignore[misc]
    """High-level manager that owns StockDataManager and schedules updates."""

    updated = pyqtSignal(list)  # emits list[Stock] after refresh (if PyQt available)

    def __init__(self, data_manager: Optional[StockDataManager] = None, api_client: Optional[StockAPIClient] = None, provider: Optional[QuoteProvider] = None, *, auto_adjust: bool = True):
        logger.debug("StockManager", f"Initializing StockManager with auto_adjust={auto_adjust}")
        super().__init__()  # type: ignore
        self.data_manager = data_manager or StockDataManager()
        # Keep backward compatibility: if old api_client provided, wrap its fetch into provider-like interface.
        if provider is None:
            if api_client is not None:
                class _Adapter(QuoteProvider):  # type: ignore
                    def fetch_quotes(self_inner, symbols):
                        return api_client.fetch_quotes(symbols)
                provider = _Adapter()
            else:
                provider = create_default_provider()
        self._provider = provider
        # Internal scheduling state (simple assignments to avoid runtime parsing issues if type stubs missing)
        self._update_timer = None  # QTimer | None
        self._thread = None  # threading.Thread | None
        self._thread_stop = threading.Event()
        self._symbols_provider = None  # callable returning list[str]
        self._auto_adjust = auto_adjust
        logger.info("StockManager", "StockManager initialized successfully")

    # --- Core update logic -------------------------------------------------
    def refresh(self, symbols: List[str]) -> List[StockView]:
        logger.debug("StockManager", f"Refreshing {len(symbols)} symbols: {symbols}")
        if not symbols:
            logger.debug("StockManager", "No symbols provided for refresh")
            return []
        # Fetch raw quotes
        raw = self._provider.fetch_quotes([s.upper() for s in symbols])
        updated: List[StockView] = []
        for sym, payload in raw.items():
            payload['symbol'] = sym  # ensure canonical
            view = self.data_manager.ingest_quote(payload)
            if view:
                updated.append(view)
        if hasattr(self, 'updated') and self.updated:  # emit if signal is real
            try:
                self.updated.emit(updated)  # type: ignore
            except Exception:
                pass
        logger.info("StockManager", f"Refresh complete: {len(updated)} stocks updated")
        return updated

    # --- Scheduling (PyQt) -------------------------------------------------
    def start_hourly_updates_qt(self, symbols_provider: Callable[[], List[str]], interval: timedelta = timedelta(hours=1)):
        if QTimer is None:
            raise RuntimeError("PyQt not available; use start_hourly_updates_thread instead")
        self.stop_updates()
        self._symbols_provider = symbols_provider
        timer = QTimer()
        timer.setInterval(int(interval.total_seconds() * 1000))
        timer.timeout.connect(self._on_timer)  # type: ignore
        timer.start()
        self._update_timer = timer
        # Kick an immediate refresh
        self._on_timer()

    def _on_timer(self):
        if not self._symbols_provider:
            logger.debug("StockManager", "No symbols provider set, skipping refresh")
            return
        try:
            symbols = self._symbols_provider()
            logger.debug("StockManager", f"Timer triggered refresh for {len(symbols)} symbols")
            self.refresh(symbols)
        except Exception as e:
            logger.error("StockManager", f"Update error in timer callback: {e}")

    # --- Scheduling (thread fallback) -------------------------------------
    def start_hourly_updates_thread(self, symbols_provider: Callable[[], List[str]], interval: timedelta = timedelta(hours=1)):
        logger.debug("StockManager", f"Starting hourly updates thread with interval {interval}")
        self.stop_updates()
        self._symbols_provider = symbols_provider
        self._thread_stop.clear()

        def loop():
            # Immediate refresh
            self._on_timer()
            while not self._thread_stop.wait(interval.total_seconds()):
                self._on_timer()

        t = threading.Thread(target=loop, name="StockUpdateThread", daemon=True)
        t.start()
        self._thread = t
        logger.info("StockManager", "Stock update thread started")

    def stop_updates(self):
        logger.debug("StockManager", "Stopping stock updates")
        if self._update_timer is not None:
            try:
                self._update_timer.stop()
                logger.debug("StockManager", "Qt timer stopped")
            except Exception:
                pass
            self._update_timer = None
        if self._thread is not None:
            self._thread_stop.set()
            self._thread = None
            logger.debug("StockManager", "Update thread stopped")
        logger.info("StockManager", "Stock updates stopped")

    # --- Convenience -------------------------------------------------------
    def tracked_symbols(self) -> List[str]:
        return [s.symbol for s in self.data_manager.all()]

    # --- Extended utilities ----------------------------------------------
    def backfill_candles(self, symbol: str, interval: str = '1d', limit: int = 100) -> int:
        """Fetch historical candles via provider (if supported) and store them.

        Returns number of candles added.
        """
        logger.debug("StockManager", f"Backfilling candles for {symbol}: interval={interval}, limit={limit}")
        try:
            candles = self._provider.fetch_candles(symbol, interval=interval, limit=limit)  # type: ignore[attr-defined]
        except Exception as e:
            logger.warning("StockManager", f"Failed to fetch candles for {symbol}: {e}")
            candles = []
        added = 0
        for c in candles:
            try:
                from datetime import datetime
                start = c.get('start')
                end = c.get('end')
                if isinstance(start, str):
                    from datetime import datetime
                    start_dt = datetime.fromisoformat(start.replace('Z', '+00:00')).replace(tzinfo=None)
                else:
                    start_dt = start
                if isinstance(end, str):
                    end_dt = datetime.fromisoformat(end.replace('Z', '+00:00')).replace(tzinfo=None)
                else:
                    end_dt = end
                candle = Candle(
                    symbol=symbol.upper(), interval=c.get('interval', interval),
                    open=c.get('open'), high=c.get('high'), low=c.get('low'), close=c.get('close'),
                    volume=c.get('volume'), start=start_dt, end=end_dt
                )
                self.data_manager.add_candle(candle)
                added += 1
            except Exception:
                continue
        logger.info("StockManager", f"Backfilled {added} candles for {symbol}")
        return added

    def backfill_candles_range(self, symbol: str, interval: str, start: str, end: str) -> int:
        try:
            candles = self._provider.fetch_candles_range(symbol, interval=interval, start=start, end=end)  # type: ignore[attr-defined]
        except Exception:
            candles = []
        added = 0
        for c in candles:
            try:
                from datetime import datetime
                def to_dt(val):
                    if isinstance(val, (int, float)):
                        # polygon epoch ms
                        import datetime as _dt
                        return _dt.datetime.utcfromtimestamp(val/1000.0)
                    if isinstance(val, str):
                        from datetime import datetime as _d
                        try:
                            return _d.fromisoformat(val.replace('Z','+00:00')).replace(tzinfo=None)
                        except Exception:
                            return _d.utcnow()
                    return val
                start_dt = to_dt(c.get('start'))
                end_dt = to_dt(c.get('end'))
                candle = Candle(symbol=symbol.upper(), interval=interval,
                                 open=c.get('open'), high=c.get('high'), low=c.get('low'), close=c.get('close'),
                                 volume=c.get('volume'), start=start_dt, end=end_dt)
                self.data_manager.add_candle(candle)
                added += 1
            except Exception:
                continue
        return added

    def sync_corporate_actions(self, symbol: str) -> dict:
        """Fetch splits/dividends from provider and record them.

        Returns dict with counts: {'splits': x, 'dividends': y}
        """
        logger.debug("StockManager", f"Syncing corporate actions for {symbol}")
        splits_added = 0
        dividends_added = 0
        try:
            splits = self._provider.fetch_splits(symbol)  # type: ignore[attr-defined]
        except Exception as e:
            logger.warning("StockManager", f"Failed to fetch splits for {symbol}: {e}")
            splits = []
        from datetime import datetime as _d
        for s in splits:
            try:
                date_str = s.get('date')
                if not date_str:
                    continue
                dt = _d.fromisoformat(date_str.replace('Z','+00:00')) if 'T' in date_str else _d.fromisoformat(date_str + 'T00:00:00+00:00')
                ratio = float(s.get('ratio') or 1)
                # Avoid duplicate: compare existing list dates
                if not any(existing['date'].startswith(date_str) for existing in self.data_manager.list_splits(symbol)):
                    self.data_manager.record_split(symbol, dt.replace(tzinfo=None), ratio)
                    splits_added += 1
            except Exception:
                continue
        try:
            dividends = self._provider.fetch_dividends(symbol)  # type: ignore[attr-defined]
        except Exception as e:
            logger.warning("StockManager", f"Failed to fetch dividends for {symbol}: {e}")
            dividends = []
        for d in dividends:
            try:
                date_str = d.get('date')
                amt = d.get('amount')
                if date_str and amt is not None:
                    if not any(existing['date'].startswith(date_str) for existing in self.data_manager.list_dividends(symbol)):
                        dt = _d.fromisoformat(date_str.replace('Z','+00:00')) if 'T' in date_str else _d.fromisoformat(date_str + 'T00:00:00+00:00')
                        self.data_manager.record_dividend(symbol, dt.replace(tzinfo=None), float(amt))
                        dividends_added += 1
            except Exception:
                continue
        logger.info("StockManager", f"Synced corporate actions for {symbol}: {splits_added} splits, {dividends_added} dividends")
        return {'splits': splits_added, 'dividends': dividends_added}

    def update_fundamentals(self, symbol: str) -> bool:
        logger.debug("StockManager", f"Updating fundamentals for {symbol}")
        try:
            f = self._provider.fetch_fundamentals(symbol)  # type: ignore[attr-defined]
        except Exception as e:
            logger.warning("StockManager", f"Failed to fetch fundamentals for {symbol}: {e}")
            f = None
        if not f:
            logger.warning("StockManager", f"No fundamentals data returned for {symbol}")
            return False
        # Remove keys not in Fundamentals dataclass implicitly handled by upsert_fundamentals
        allowed = {'sector','industry','pe_ratio','eps','dividend_yield','beta','shares_outstanding'}
        filtered = {k: v for k, v in f.items() if k in allowed}
        self.data_manager.upsert_fundamentals(symbol, **filtered)
        logger.info("StockManager", f"Fundamentals updated for {symbol}")
        return True

__all__ = ["StockManager"]
