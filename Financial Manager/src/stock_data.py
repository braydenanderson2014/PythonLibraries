from __future__ import annotations

"""Historical stock data manager.

This module introduces a redesigned storage layer that separates relatively
static metadata (name, exchange) from rapidly changing quote snapshots
(price, volume, etc.). It supports maintaining an in‑memory time‑series per
symbol and persisting to a JSON file on disk.

Schema (JSON):
{
  "AAPL": {
    "meta": {"symbol": "AAPL", "name": "Apple Inc.", "exchange": "NASDAQ"},
    "history": [
       {"timestamp": "2025-10-06T12:34:00.123456Z", "price": 174.12, "previous_close": 173.55, "volume": 1200000, "market_cap": 2500000000000.0},
       ... newer last ...
    ]
  },
  ...
}

Backward compatibility: the old implementation stored a flat mapping of
symbol -> last snapshot fields (using keys like latest_price). A migration
routine detects that shape and converts each entry into a one‑element history.
"""

import json
import os
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from threading import RLock
from typing import Dict, Optional, List, Iterable, Any
try:
    from .app_paths import STOCK_DB
except ImportError:
    from app_paths import STOCK_DB

ISO_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
from assets.Logger import Logger
logger = Logger()


# --- Data Models -----------------------------------------------------------

@dataclass
class StockMeta:
    symbol: str
    name: Optional[str] = None
    exchange: Optional[str] = None


@dataclass
class QuoteSnapshot:
    symbol: str
    price: float
    previous_close: Optional[float] = None
    volume: Optional[int] = None
    market_cap: Optional[float] = None
    # Optional intraday OHLC if available from quote endpoint
    day_open: Optional[float] = None
    day_high: Optional[float] = None
    day_low: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    # Closing price (regular market hours)
    closing_price: Optional[float] = None
    # After-hours trading details
    after_hours_price: Optional[float] = None
    after_hours_volume: Optional[int] = None
    post_market_change: Optional[float] = None
    post_market_change_percent: Optional[float] = None

    @classmethod
    def from_raw(cls, symbol: str, raw: Dict[str, Any]) -> 'QuoteSnapshot':
        """Create snapshot from a raw payload (flexible key mapping)."""
        mapping = {
            'price': 'price', 'latest_price': 'price', 'last': 'price',
            'previous_close': 'previous_close', 'prevClose': 'previous_close',
            'volume': 'volume',
            'market_cap': 'market_cap', 'marketCap': 'market_cap',
            'open': 'day_open', 'day_open': 'day_open',
            'high': 'day_high', 'day_high': 'day_high',
            'low': 'day_low', 'day_low': 'day_low',
            'timestamp': 'timestamp',
            'closing_price': 'closing_price', 'regularMarketPrice': 'closing_price',
            'after_hours_price': 'after_hours_price', 'postMarketPrice': 'after_hours_price',
            'after_hours_volume': 'after_hours_volume', 'postMarketVolume': 'after_hours_volume',
            'post_market_change': 'post_market_change', 'postMarketChange': 'post_market_change',
            'post_market_change_percent': 'post_market_change_percent', 'postMarketChangePercent': 'post_market_change_percent',
        }
        norm: Dict[str, Any] = {}
        for k, v in raw.items():
            key = mapping.get(k)
            if key:
                norm[key] = v
        # Ensure price present (fallback 0.0 if missing)
        price = float(norm.get('price', 0.0) or 0.0)
        ts = norm.get('timestamp')
        timestamp: datetime
        if isinstance(ts, str):
            try:
                timestamp = datetime.fromisoformat(ts.replace('Z', '+00:00')).astimezone(tz=None).replace(tzinfo=None)
            except Exception:
                timestamp = datetime.utcnow()
        elif isinstance(ts, (int, float)):
            timestamp = datetime.utcfromtimestamp(float(ts))
        elif isinstance(ts, datetime):
            timestamp = ts
        else:
            timestamp = datetime.utcnow()
        return cls(
            symbol=symbol.upper(),
            price=price,
            previous_close=norm.get('previous_close'),
            volume=norm.get('volume'),
            market_cap=norm.get('market_cap'),
            timestamp=timestamp,
            closing_price=norm.get('closing_price'),
            after_hours_price=norm.get('after_hours_price'),
            after_hours_volume=norm.get('after_hours_volume'),
            post_market_change=norm.get('post_market_change'),
            post_market_change_percent=norm.get('post_market_change_percent'),
        )

    def to_dict(self) -> Dict[str, Any]:  # for persistence
        d = asdict(self)
        d['timestamp'] = self.timestamp.strftime(ISO_FORMAT)
        # attach raw_* dynamic attributes and adjusted flag if present
        for attr in ('raw_price','raw_previous_close','raw_day_open','raw_day_high','raw_day_low','raw_volume','adjusted'):
            if hasattr(self, attr):
                d[attr] = getattr(self, attr)
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QuoteSnapshot':
        ts = data.get('timestamp')
        if isinstance(ts, str):
            try:
                data = dict(data)
                data['timestamp'] = datetime.strptime(ts, ISO_FORMAT)
            except Exception:
                data['timestamp'] = datetime.utcnow()
        # Remove dynamic fields before construction
        dynamic = {}
        for k in list(data.keys()):
            if k.startswith('raw_') or k == 'adjusted':
                dynamic[k] = data.pop(k)
        obj = cls(**{k: v for k, v in data.items() if k in cls.__annotations__})
        for k, v in dynamic.items():
            setattr(obj, k, v)
        return obj


@dataclass
class Candle:
    """Represents an OHLCV bar for a symbol and interval.

    interval examples: '1m','5m','15m','1h','1d'. Start inclusive, end exclusive.
    """
    symbol: str
    interval: str
    open: float
    high: float
    low: float
    close: float
    volume: Optional[int]
    start: datetime
    end: datetime

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['start'] = self.start.strftime(ISO_FORMAT)
        d['end'] = self.end.strftime(ISO_FORMAT)
        for attr in ('raw_open','raw_high','raw_low','raw_close','raw_volume','adjusted'):
            if hasattr(self, attr):
                d[attr] = getattr(self, attr)
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Candle':
        dd = dict(data)
        for k in ('start','end'):
            v = dd.get(k)
            if isinstance(v, str):
                try:
                    dd[k] = datetime.strptime(v, ISO_FORMAT)
                except Exception:
                    dd[k] = datetime.utcnow()
        dynamic = {}
        for k in list(dd.keys()):
            if k.startswith('raw_') or k == 'adjusted':
                dynamic[k] = dd.pop(k)
        obj = cls(**{k: v for k, v in dd.items() if k in cls.__annotations__})
        for k, v in dynamic.items():
            setattr(obj, k, v)
        return obj


@dataclass
class Fundamentals:
    """Holds latest point-in-time fundamentals plus TTM & quarterly sequences.

    ttm: dict of trailing twelve month aggregate ratios/metrics.
    quarterly: list of {period_end, metrics...} newest last (limited length).
    """
    symbol: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    pe_ratio: Optional[float] = None
    eps: Optional[float] = None
    dividend_yield: Optional[float] = None
    beta: Optional[float] = None
    shares_outstanding: Optional[int] = None
    updated_at: datetime = field(default_factory=datetime.utcnow)
    ttm: Dict[str, float] = field(default_factory=dict)
    quarterly: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['updated_at'] = self.updated_at.strftime(ISO_FORMAT)
        # ensure period_end in quarterly entries is ISO
        qnorm = []
        for q in self.quarterly:
            qd = dict(q)
            pe = qd.get('period_end')
            if isinstance(pe, datetime):
                qd['period_end'] = pe.strftime(ISO_FORMAT)
            qnorm.append(qd)
        d['quarterly'] = qnorm
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Fundamentals':
        d = dict(data)
        ua = d.get('updated_at')
        if isinstance(ua, str):
            try:
                d['updated_at'] = datetime.strptime(ua, ISO_FORMAT)
            except Exception:
                d['updated_at'] = datetime.utcnow()
        qlist = []
        for q in d.get('quarterly', []) or []:
            qd = dict(q)
            pe = qd.get('period_end')
            if isinstance(pe, str):
                try:
                    qd['period_end'] = datetime.strptime(pe, ISO_FORMAT)
                except Exception:
                    pass
            qlist.append(qd)
        d['quarterly'] = qlist
        return cls(**d)

    def add_quarterly(self, period_end: datetime, **metrics: Any,):
        entry = {'period_end': period_end, **metrics}
        self.quarterly.append(entry)
        # retain only last 12 quarters by default
        if len(self.quarterly) > 12:
            del self.quarterly[:-12]
        self.updated_at = datetime.utcnow()

    def set_ttm(self, **metrics: float):
        self.ttm.update({k: float(v) for k, v in metrics.items()})
        self.updated_at = datetime.utcnow()


class StockView:
    """Read‑only convenience view combining meta + latest snapshot.

    Mimics old interface attributes: latest_price, previous_close, volume,
    market_cap, timestamp, name, exchange.
    """

    def __init__(self, meta: StockMeta, snapshot: QuoteSnapshot | None):
        self.symbol = meta.symbol
        self.name = meta.name
        self.exchange = meta.exchange
        # Alias for backward compatibility
        self.company_name = meta.name
        
        if snapshot:
            # Determine which price to use based on closing price availability
            # If closing_price is available, use it; otherwise use price
            self.closing_price = snapshot.closing_price or snapshot.price
            
            # For current display price, prefer closing price if available (during market hours)
            # or after-hours price (after hours)
            if snapshot.after_hours_price and snapshot.after_hours_price != 0:
                self.latest_price = snapshot.after_hours_price
                self.price = snapshot.after_hours_price
                self.is_after_hours = True
            else:
                self.latest_price = self.closing_price
                self.price = self.closing_price
                self.is_after_hours = False
            
            self.previous_close = snapshot.previous_close
            self.volume = snapshot.volume
            self.market_cap = snapshot.market_cap
            self.timestamp = snapshot.timestamp
            self.last_updated = snapshot.timestamp
            
            # After-hours trading information
            self.after_hours_price = snapshot.after_hours_price
            self.after_hours_volume = snapshot.after_hours_volume
            self.post_market_change = snapshot.post_market_change
            self.post_market_change_percent = snapshot.post_market_change_percent
            
            # Calculate change and change_percent if we have previous_close
            if self.previous_close and self.previous_close > 0:
                self.change = self.closing_price - self.previous_close
                self.change_percent = (self.change / self.previous_close) * 100
            else:
                self.change = None
                self.change_percent = None
        else:
            self.latest_price = None
            self.price = None
            self.previous_close = None
            self.volume = None
            self.market_cap = None
            self.timestamp = None
            self.last_updated = None
            self.change = None
            self.change_percent = None
            self.closing_price = None
            self.after_hours_price = None
            self.after_hours_volume = None
            self.post_market_change = None
            self.post_market_change_percent = None
            self.is_after_hours = False

    def __repr__(self):  # pragma: no cover - simple
        return f"<StockView {self.symbol} {self.latest_price}@{self.timestamp}>"


# --- Manager ---------------------------------------------------------------

class StockDataManager:
    """Manages stock metadata and time‑series quote snapshots.

    Parameters
    -----------
    db_path : str | None
        Location of JSON persistence file.
    max_history_per_symbol : int | None
        Optional cap on number of snapshots retained in memory (oldest pruned).
    auto_save : bool
        When True, save() after each mutation.
    """

    def __init__(self, db_path: Optional[str] = None, *, max_history_per_symbol: int | None = 500, auto_save: bool = True):
        logger.debug("StockDataManager", f"Initializing StockDataManager with db_path={db_path}, max_history={max_history_per_symbol}, auto_save={auto_save}")
        self.db_path = db_path or STOCK_DB
        self.max_history_per_symbol = max_history_per_symbol
        self.auto_save = auto_save
        self._meta: Dict[str, StockMeta] = {}
        self._history: Dict[str, List[QuoteSnapshot]] = {}
        self._lock = RLock()
        # symbol -> interval -> list[Candle]
        self._candles: Dict[str, Dict[str, List[Candle]]] = {}
        # symbol -> fundamentals
        self._fundamentals: Dict[str, Fundamentals] = {}
        # corporate actions
        self._splits: Dict[str, List[Dict[str, Any]]] = {}
        self._dividends: Dict[str, List[Dict[str, Any]]] = {}
        # Callbacks for stock updates
        self._update_callbacks: List[Any] = []
        self.load()
        logger.info("StockDataManager", "StockDataManager initialized successfully")

    # --- Metadata --------------------------------------------------------
    def upsert_meta(self, symbol: str, name: Optional[str] = None, exchange: Optional[str] = None) -> StockMeta:
        logger.debug("StockDataManager", f"Upserting metadata for {symbol}: name={name}, exchange={exchange}")
        symbol = symbol.upper()
        with self._lock:
            meta = self._meta.get(symbol)
            if meta is None:
                meta = StockMeta(symbol=symbol, name=name, exchange=exchange)
                self._meta[symbol] = meta
                logger.debug("StockDataManager", f"Created new metadata for {symbol}")
            else:
                if name is not None:
                    meta.name = name
                if exchange is not None:
                    meta.exchange = exchange
                logger.debug("StockDataManager", f"Updated metadata for {symbol}")
            if self.auto_save:
                self.save()
            return meta

    # --- Callbacks -------------------------------------------------------
    def on_stock_updated(self, callback: Any) -> None:
        """Register a callback to be called when stock data is updated.
        
        The callback will be called with the symbol string and stock view when stock data changes.
        """
        logger.debug("StockDataManager", f"Registering stock update callback")
        with self._lock:
            if callback not in self._update_callbacks:
                self._update_callbacks.append(callback)
                logger.info("StockDataManager", f"Stock update callback registered, total callbacks: {len(self._update_callbacks)}")
    
    def off_stock_updated(self, callback: Any) -> None:
        """Unregister a callback.
        
        Args:
            callback: The callback function to remove
        """
        logger.debug("StockDataManager", "Unregistering stock update callback")
        with self._lock:
            if callback in self._update_callbacks:
                self._update_callbacks.remove(callback)
                logger.info("StockDataManager", f"Stock update callback removed, remaining callbacks: {len(self._update_callbacks)}")
    
    def _notify_updated(self, symbol: str, stock_view: Any = None) -> None:
        """Internal method to notify all callbacks of an update.
        
        Args:
            symbol: The symbol that was updated
            stock_view: The StockView object containing the updated data
        """
        with self._lock:
            callbacks = list(self._update_callbacks)
        
        logger.debug("StockDataManager", f"Notifying {len(callbacks)} callbacks for {symbol}")
        for callback in callbacks:
            try:
                callback(symbol, stock_view)
            except Exception as e:
                # Log but don't raise - callback errors shouldn't break data manager
                logger.error("StockDataManager", f"Error in stock update callback for {symbol}: {e}")

    # --- Snapshots -------------------------------------------------------
    def add_snapshot(self, snapshot: QuoteSnapshot) -> None:
        logger.debug("StockDataManager", f"Adding snapshot for {snapshot.symbol} at ${snapshot.price}")
        symbol = snapshot.symbol.upper()
        with self._lock:
            if symbol not in self._meta:
                # create placeholder meta if missing
                self._meta[symbol] = StockMeta(symbol=symbol)
            lst = self._history.setdefault(symbol, [])
            lst.append(snapshot)
            # pruning
            if self.max_history_per_symbol and len(lst) > self.max_history_per_symbol:
                del lst[: len(lst) - self.max_history_per_symbol]
                logger.debug("StockDataManager", f"Pruned history for {symbol} to {self.max_history_per_symbol} snapshots")
            if self.auto_save:
                self.save()
        
        # Notify callbacks after snapshot is added
        stock_view = self.get(symbol)
        self._notify_updated(symbol, stock_view)
        logger.info("StockDataManager", f"Snapshot added for {symbol}")

    def ingest_quote(self, raw: Dict[str, Any]) -> StockView:
        """Ingest a raw API quote payload (mutates internal state, returns view)."""
        logger.debug("StockDataManager", f"Ingesting quote payload for symbol")
        symbol = raw.get('symbol') or raw.get('Symbol')
        if not symbol:
            logger.error("StockDataManager", "Quote payload missing 'symbol'")
            raise ValueError("Quote payload missing 'symbol'")
        meta_name = raw.get('name') or raw.get('Name')
        meta_exch = raw.get('exchange') or raw.get('Exchange')
        self.upsert_meta(symbol, name=meta_name, exchange=meta_exch)
        snapshot = QuoteSnapshot.from_raw(symbol, raw)
        self.add_snapshot(snapshot)
        logger.info("StockDataManager", f"Quote ingested for {symbol}")
        return self.get(symbol)  # type: ignore

    # --- Queries ---------------------------------------------------------
    def latest_snapshot(self, symbol: str) -> Optional[QuoteSnapshot]:
        symbol = symbol.upper()
        with self._lock:
            lst = self._history.get(symbol)
            return lst[-1] if lst else None

    def history(self, symbol: str, *, limit: Optional[int] = None, since: Optional[datetime] = None) -> List[QuoteSnapshot]:
        symbol = symbol.upper()
        with self._lock:
            lst = list(self._history.get(symbol, []))
        if since is not None:
            lst = [s for s in lst if s.timestamp >= since]
        if limit is not None:
            lst = lst[-limit:]
        return lst

    def get(self, symbol: str) -> Optional[StockView]:
        symbol = symbol.upper()
        with self._lock:
            meta = self._meta.get(symbol)
            if not meta:
                return None
            snap = self._history.get(symbol, [])[-1] if self._history.get(symbol) else None
            return StockView(meta, snap)

    def symbols(self) -> List[str]:
        with self._lock:
            return list(self._meta.keys())

    def all(self) -> List[StockView]:
        return [self.get(sym) for sym in self.symbols() if self.get(sym) is not None]

    # --- Convenience methods -----------------------------------------------
    def get_stock_data(self, symbol: str) -> Optional[StockView]:
        """Get stock data (convenience alias for get).
        
        Args:
            symbol: Stock symbol
            
        Returns:
            StockView if data exists, None otherwise
        """
        return self.get(symbol)
    
    def add_stock(self, symbol: str, name: Optional[str] = None, exchange: Optional[str] = None) -> StockMeta:
        """Add a stock to tracking (convenience method).
        
        Args:
            symbol: Stock symbol
            name: Optional company name
            exchange: Optional exchange name
            
        Returns:
            The StockMeta object for this symbol
        """
        return self.upsert_meta(symbol, name=name, exchange=exchange)
    
    def force_refresh(self) -> None:
        """Force a refresh (no-op for StockDataManager as it's primarily a storage layer).
        
        In a real implementation, this would fetch new data from providers.
        UI components typically use this as a signal to trigger actual data fetches
        from the StockManager or provider.
        """
        pass

    # --- Candles ---------------------------------------------------------
    def add_candle(self, candle: Candle) -> None:
        symbol = candle.symbol.upper()
        with self._lock:
            if symbol not in self._meta:
                self._meta[symbol] = StockMeta(symbol=symbol)
            per_symbol = self._candles.setdefault(symbol, {})
            lst = per_symbol.setdefault(candle.interval, [])
            lst.append(candle)
            # Optional pruning based on max_history_per_symbol per interval
            if self.max_history_per_symbol and len(lst) > self.max_history_per_symbol:
                del lst[: len(lst) - self.max_history_per_symbol]
            if self.auto_save:
                self.save()

    def candles(self, symbol: str, interval: str, *, limit: Optional[int] = None, since: Optional[datetime] = None) -> List[Candle]:
        symbol = symbol.upper()
        with self._lock:
            lst = list(self._candles.get(symbol, {}).get(interval, []))
        if since:
            lst = [c for c in lst if c.start >= since]
        if limit:
            lst = lst[-limit:]
        return lst

    # --- Fundamentals ----------------------------------------------------
    def upsert_fundamentals(self, symbol: str, **fields: Any) -> Fundamentals:
        symbol = symbol.upper()
        with self._lock:
            f = self._fundamentals.get(symbol)
            if f is None:
                f = Fundamentals(symbol=symbol)
                self._fundamentals[symbol] = f
            for k, v in fields.items():
                if hasattr(f, k) and k != 'symbol':
                    setattr(f, k, v)
            f.updated_at = datetime.utcnow()
            if self.auto_save:
                self.save()
            return f

    def add_quarterly_fundamentals(self, symbol: str, period_end: datetime, **metrics: Any) -> None:
        symbol = symbol.upper()
        with self._lock:
            f = self._fundamentals.get(symbol)
            if f is None:
                f = Fundamentals(symbol=symbol)
                self._fundamentals[symbol] = f
            f.add_quarterly(period_end, **metrics)
            if self.auto_save:
                self.save()

    def set_ttm_fundamentals(self, symbol: str, **metrics: float) -> None:
        symbol = symbol.upper()
        with self._lock:
            f = self._fundamentals.get(symbol)
            if f is None:
                f = Fundamentals(symbol=symbol)
                self._fundamentals[symbol] = f
            f.set_ttm(**metrics)
            if self.auto_save:
                self.save()

    def fundamentals(self, symbol: str) -> Optional[Fundamentals]:
        return self._fundamentals.get(symbol.upper())

    def fundamentals_point_in_time(self, symbol: str, ts: datetime) -> Optional[Dict[str, Any]]:
        """Return a snapshot of fundamentals as they would have been known at timestamp ts.

        This prevents future leakage by excluding quarterly entries or TTM metrics updated after ts.
        For simplicity, we filter quarterly entries whose period_end <= ts and if updated_at > ts we treat object as None.
        """
        f = self._fundamentals.get(symbol.upper())
        if f is None:
            return None
        if f.updated_at > ts:
            # Possibly the entire fundamentals set was updated after ts; still we can include past quarters
            pass
        quarters = [q for q in f.quarterly if isinstance(q.get('period_end'), datetime) and q['period_end'] <= ts]
        # TTM only if fundamentals updated <= ts
        ttm = f.ttm if f.updated_at <= ts else {}
        return {
            'symbol': f.symbol,
            'sector': f.sector,
            'industry': f.industry,
            'pe_ratio': f.pe_ratio if f.updated_at <= ts else None,
            'eps': f.eps if f.updated_at <= ts else None,
            'dividend_yield': f.dividend_yield if f.updated_at <= ts else None,
            'beta': f.beta if f.updated_at <= ts else None,
            'shares_outstanding': f.shares_outstanding if f.updated_at <= ts else None,
            'quarterly': quarters,
            'ttm': ttm,
        }

    # --- Corporate Actions ----------------------------------------------
    def record_split(self, symbol: str, date: datetime, ratio: float) -> int:
        """Record a stock split and retroactively adjust historical prices & volumes.

        ratio: new_shares / old_share (e.g., 2.0 for 2-for-1)
        Returns number of records adjusted.
        """
        symbol = symbol.upper()
        adjusted = 0
        if ratio <= 0:
            return 0
        with self._lock:
            entry = {'date': date.strftime(ISO_FORMAT), 'ratio': ratio}
            self._splits.setdefault(symbol, []).append(entry)
            # Adjust snapshots
            for snap in self._history.get(symbol, []):
                if snap.timestamp < date:
                    # adjust price-like fields
                    # preserve raw values first time we touch them
                    if not hasattr(snap, 'raw_price'):
                        setattr(snap, 'raw_price', snap.price)
                        if snap.previous_close is not None:
                            setattr(snap, 'raw_previous_close', snap.previous_close)
                        if snap.day_open is not None:
                            setattr(snap, 'raw_day_open', snap.day_open)
                        if snap.day_high is not None:
                            setattr(snap, 'raw_day_high', snap.day_high)
                        if snap.day_low is not None:
                            setattr(snap, 'raw_day_low', snap.day_low)
                        if snap.volume is not None:
                            setattr(snap, 'raw_volume', snap.volume)
                    snap.price /= ratio
                    if snap.previous_close is not None:
                        snap.previous_close /= ratio
                    if snap.day_open is not None:
                        snap.day_open /= ratio
                    if snap.day_high is not None:
                        snap.day_high /= ratio
                    if snap.day_low is not None:
                        snap.day_low /= ratio
                    if snap.volume is not None:
                        snap.volume = int(snap.volume * ratio)
                    adjusted += 1
            # Adjust candles
            for interval, clist in self._candles.get(symbol, {}).items():
                for c in clist:
                    if c.start < date:
                        if not hasattr(c, 'raw_open'):
                            setattr(c, 'raw_open', c.open)
                            setattr(c, 'raw_high', c.high)
                            setattr(c, 'raw_low', c.low)
                            setattr(c, 'raw_close', c.close)
                            if c.volume is not None:
                                setattr(c, 'raw_volume', c.volume)
                        c.open /= ratio
                        c.high /= ratio
                        c.low /= ratio
                        c.close /= ratio
                        if c.volume:
                            c.volume = int(c.volume * ratio)
                        adjusted += 1
                        setattr(c, 'adjusted', True)
                setattr(c, 'adjusted', True)
            for snap in self._history.get(symbol, []):
                if snap.timestamp < date:
                    setattr(snap, 'adjusted', True)
            if self.auto_save:
                self.save()
        return adjusted

    def record_dividend(self, symbol: str, date: datetime, amount: float) -> None:
        symbol = symbol.upper()
        with self._lock:
            self._dividends.setdefault(symbol, []).append({'date': date.strftime(ISO_FORMAT), 'amount': float(amount)})
            if self.auto_save:
                self.save()

    def list_splits(self, symbol: str) -> List[Dict[str, Any]]:
        return list(self._splits.get(symbol.upper(), []))

    def list_dividends(self, symbol: str) -> List[Dict[str, Any]]:
        return list(self._dividends.get(symbol.upper(), []))

    # --- Removal ---------------------------------------------------------
    def remove(self, symbol: str) -> bool:
        symbol = symbol.upper()
        with self._lock:
            existed = symbol in self._meta
            self._meta.pop(symbol, None)
            self._history.pop(symbol, None)
            if existed and self.auto_save:
                self.save()
            return existed

    # --- Persistence -----------------------------------------------------
    def save(self) -> None:
        data: Dict[str, Any] = {}
        for sym, meta in self._meta.items():
            hist = self._history.get(sym, [])
            cblocks = self._candles.get(sym, {})
            fundamentals = self._fundamentals.get(sym)
            splits = self._splits.get(sym, [])
            dividends = self._dividends.get(sym, [])
            data[sym] = {
                'meta': asdict(meta),
                'history': [s.to_dict() for s in hist],
                'candles': {ival: [c.to_dict() for c in clist] for ival, clist in cblocks.items()},
                'fundamentals': fundamentals.to_dict() if fundamentals else None,
                'splits': splits,
                'dividends': dividends,
            }
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        tmp_path = self.db_path + '.tmp'
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_path, self.db_path)

    def load(self) -> None:
        if not os.path.exists(self.db_path):
            return
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                raw = json.load(f)
        except Exception:
            return
        if not isinstance(raw, dict):
            return
        # New schema branch
        if raw and all(isinstance(v, dict) and 'meta' in v and 'history' in v for v in raw.values()):
            for sym, block in raw.items():
                try:
                    meta_block = block.get('meta', {})
                    meta = StockMeta(**{k: v for k, v in meta_block.items() if k in {'symbol','name','exchange'}})
                    u = sym.upper()
                    self._meta[u] = meta
                    hist_list: List[QuoteSnapshot] = []
                    for sdict in block.get('history', []):
                        snap = QuoteSnapshot.from_dict(sdict)
                        hist_list.append(snap)
                    self._history[u] = hist_list
                    cblk = block.get('candles', {}) or {}
                    per_interval: Dict[str, List[Candle]] = {}
                    for interval, arr in cblk.items():
                        per_interval[interval] = [Candle.from_dict(cd) for cd in arr]
                    if per_interval:
                        self._candles[u] = per_interval
                    fblk = block.get('fundamentals')
                    if isinstance(fblk, dict):
                        self._fundamentals[u] = Fundamentals.from_dict(fblk)
                    sblk = block.get('splits') or []
                    if isinstance(sblk, list):
                        self._splits[u] = list(sblk)
                    dblk = block.get('dividends') or []
                    if isinstance(dblk, list):
                        self._dividends[u] = list(dblk)
                except Exception:
                    continue
        else:
            # Legacy schema branch
            for sym, snapshot_dict in raw.items():
                if not isinstance(snapshot_dict, dict):
                    continue
                upper = sym.upper()
                meta = StockMeta(symbol=upper, name=snapshot_dict.get('name'), exchange=snapshot_dict.get('exchange'))
                self._meta[upper] = meta
                snap = QuoteSnapshot.from_raw(upper, snapshot_dict)
                self._history[upper] = [snap]
                # legacy had no splits/dividends
        # No pruning on load; will prune on next add if needed

    # --- Convenience / Backfill Helpers ---------------------------------
    def ensure_candles(self, symbol: str, interval: str, lookback_days: int, fetch_range_cb) -> int:
        """Ensure at least lookback_days candles exist; uses callback(start,end) to fetch if missing.

        Returns number of candles added (approx)."""
        symbol = symbol.upper()
        with self._lock:
            existing = self._candles.get(symbol, {}).get(interval, [])
            if existing:
                oldest = existing[0].start
            else:
                oldest = None
        from datetime import datetime as _d, timedelta as _td
        target_start = _d.utcnow() - _td(days=lookback_days)
        if oldest and oldest <= target_start:
            return 0
        # Need backfill
        start = (target_start.strftime('%Y-%m-%d'))
        end = _d.utcnow().strftime('%Y-%m-%d')
        try:
            candles = fetch_range_cb(symbol, interval, start, end)
        except Exception:
            return 0
        added = 0
        for c in candles:
            try:
                start_dt = c.get('start')
                end_dt = c.get('end')
                if isinstance(start_dt, (int, float)):
                    import datetime as _dt
                    start_dt = _dt.datetime.utcfromtimestamp(start_dt/1000)
                if isinstance(end_dt, (int, float)):
                    import datetime as _dt
                    end_dt = _dt.datetime.utcfromtimestamp(end_dt/1000)
                if isinstance(start_dt, str):
                    from datetime import datetime as _d2
                    start_dt = _d2.fromisoformat(start_dt.replace('Z','+00:00')).replace(tzinfo=None)
                if isinstance(end_dt, str):
                    from datetime import datetime as _d2
                    end_dt = _d2.fromisoformat(end_dt.replace('Z','+00:00')).replace(tzinfo=None)
                candle = Candle(symbol=symbol, interval=interval, open=c.get('open'), high=c.get('high'), low=c.get('low'), close=c.get('close'), volume=c.get('volume'), start=start_dt, end=end_dt)
                self.add_candle(candle)
                added += 1
            except Exception:
                continue
        return added

__all__ = [
    'StockDataManager', 'StockMeta', 'QuoteSnapshot', 'StockView', 'Candle', 'Fundamentals'
]
