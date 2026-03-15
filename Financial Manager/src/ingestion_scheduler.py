"""Ingestion scheduler for periodic backfilling & fundamentals refresh.

Provides a light-weight, thread-based scheduler (no external deps) that can:
  * Periodically refresh quotes using StockManager.refresh
  * Backfill missing candles for tracked symbols (recent lookback)
  * Update fundamentals at a slower cadence (e.g., daily)
  * Record splits/dividends from provider corporate action feeds (future)

This is intentionally simple; if needs grow, replace with APScheduler or
an asyncio variant later.
"""
from __future__ import annotations

import threading, time
from datetime import datetime, timedelta
from typing import Callable, List, Optional

try:
    from .stock_manager import StockManager
except Exception:  # pragma: no cover
    from stock_manager import StockManager  # type: ignore

from assets.Logger import Logger
logger = Logger()

class IngestionScheduler:
    def __init__(self, manager: StockManager, symbol_provider: Callable[[], List[str]], *,
                 quote_interval: timedelta = timedelta(minutes=5),
                 candle_interval: timedelta = timedelta(hours=1),
                 fundamentals_interval: timedelta = timedelta(hours=24),
                 candle_backfill_limit: int = 120):
        self.manager = manager
        self.symbol_provider = symbol_provider
        self.quote_interval = quote_interval
        self.candle_interval = candle_interval
        self.fundamentals_interval = fundamentals_interval
        self.candle_backfill_limit = candle_backfill_limit
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._last_candle_run: Optional[datetime] = None
        self._last_fund_run: Optional[datetime] = None
        logger.debug("IngestionScheduler", f"Initialized with quote_interval={quote_interval}, candle_interval={candle_interval}, fundamentals_interval={fundamentals_interval}, backfill_limit={candle_backfill_limit}")

    def start(self, run_immediate: bool = True):
        if self._thread and self._thread.is_alive():
            logger.debug("IngestionScheduler", "Scheduler thread already running, skipping start")
            return
        self._stop.clear()
        logger.debug("IngestionScheduler", f"Starting scheduler with run_immediate={run_immediate}")
        def loop():
            next_quote = time.time() if run_immediate else time.time() + self.quote_interval.total_seconds()
            while not self._stop.is_set():
                now_ts = time.time()
                if now_ts >= next_quote:
                    self._run_quotes()
                    next_quote = now_ts + self.quote_interval.total_seconds()
                self._maybe_candles()
                self._maybe_fundamentals()
                self._stop.wait(1.0)
        self._thread = threading.Thread(target=loop, name="IngestionScheduler", daemon=True)
        self._thread.start()
        logger.info("IngestionScheduler", "Scheduler thread started successfully")

    def stop(self):
        logger.debug("IngestionScheduler", "Stopping scheduler")
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
        logger.info("IngestionScheduler", "Scheduler stopped successfully")

    # --- Internal tasks -------------------------------------------------
    def _run_quotes(self):
        try:
            symbols = self.symbol_provider()
            if symbols:
                logger.debug("IngestionScheduler", f"Refreshing quotes for {len(symbols)} symbols")
                self.manager.refresh(symbols)
                logger.info("IngestionScheduler", f"Successfully refreshed quotes for {len(symbols)} symbols")
            else:
                logger.warning("IngestionScheduler", "No symbols provided for quote refresh")
        except Exception as e:  # pragma: no cover
            logger.error("IngestionScheduler", f"Quote refresh error: {str(e)}")

    def _maybe_candles(self):
        now = datetime.utcnow()
        if self._last_candle_run and (now - self._last_candle_run) < self.candle_interval:
            return
        self._last_candle_run = now
        try:
            symbols = self.symbol_provider()
            if symbols:
                logger.debug("IngestionScheduler", f"Backfilling candles for {len(symbols)} symbols with limit={self.candle_backfill_limit}")
                for sym in symbols:
                    self.manager.backfill_candles(sym, interval='1d', limit=self.candle_backfill_limit)
                logger.info("IngestionScheduler", f"Successfully backfilled candles for {len(symbols)} symbols")
            else:
                logger.warning("IngestionScheduler", "No symbols provided for candle backfill")
        except Exception as e:  # pragma: no cover
            logger.error("IngestionScheduler", f"Candle backfill error: {str(e)}")

    def _maybe_fundamentals(self):
        now = datetime.utcnow()
        if self._last_fund_run and (now - self._last_fund_run) < self.fundamentals_interval:
            return
        self._last_fund_run = now
        try:
            symbols = self.symbol_provider()
            if symbols:
                logger.debug("IngestionScheduler", f"Updating fundamentals for {len(symbols)} symbols")
                for sym in symbols:
                    self.manager.update_fundamentals(sym)
                logger.info("IngestionScheduler", f"Successfully updated fundamentals for {len(symbols)} symbols")
            else:
                logger.warning("IngestionScheduler", "No symbols provided for fundamentals update")
        except Exception as e:  # pragma: no cover
            logger.error("IngestionScheduler", f"Fundamentals update error: {str(e)}")

__all__ = ["IngestionScheduler"]
