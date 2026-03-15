"""Feature engineering utilities for stock time-series.

Minimal initial set (pure Python / no pandas dependency yet):
  - simple moving average (SMA)
  - exponential moving average (EMA)
  - rolling standard deviation (volatility proxy)
  - log returns & cumulative returns

If performance or complexity increases, migrate to pandas / numpy.
"""
from __future__ import annotations

from math import log
from typing import List, Dict, Any, Iterable, Optional
from statistics import mean, pstdev

from assets.Logger import Logger
logger = Logger()

try:
    from .stock_data import StockDataManager
except Exception:  # pragma: no cover
    from stock_data import StockDataManager  # type: ignore


def _get_closes(store: StockDataManager, symbol: str, limit: int) -> List[float]:
    logger.debug("features", f"Fetching closes for {symbol}, limit={limit}")
    snaps = store.history(symbol, limit=limit)
    closes = [s.price for s in snaps if s.price is not None]
    logger.info("features", f"Retrieved {len(closes)} close prices for {symbol}")
    return closes


def sma(values: List[float], window: int) -> List[Optional[float]]:
    logger.debug("features", f"Computing SMA with window={window} for {len(values)} values")
    out: List[Optional[float]] = []
    for i in range(len(values)):
        if i + 1 < window:
            out.append(None)
        else:
            seg = values[i+1-window:i+1]
            out.append(sum(seg)/window)
    logger.debug("features", f"SMA computation complete: {len(out)} values")
    return out


def ema(values: List[float], window: int) -> List[Optional[float]]:
    logger.debug("features", f"Computing EMA with window={window} for {len(values)} values")
    if not values:
        logger.warning("features", "Empty values list provided to EMA")
        return []
    k = 2 / (window + 1)
    out: List[Optional[float]] = []
    ema_prev = None
    for v in values:
        if ema_prev is None:
            ema_prev = v
        else:
            ema_prev = v * k + ema_prev * (1 - k)
        out.append(ema_prev)
    # replace the first window-1 entries with None for consistency
    for i in range(min(window-1, len(out))):
        out[i] = None
    logger.debug("features", f"EMA computation complete: {len(out)} values")
    return out


def log_returns(values: List[float]) -> List[Optional[float]]:
    logger.debug("features", f"Computing log returns for {len(values)} values")
    out: List[Optional[float]] = [None]
    valid_count = 0
    for prev, cur in zip(values, values[1:]):
        if prev and cur and prev > 0:
            out.append(log(cur/prev))
            valid_count += 1
        else:
            out.append(None)
    logger.debug("features", f"Log returns complete: {valid_count}/{len(values)-1} valid returns")
    return out


def rolling_volatility(values: List[float], window: int) -> List[Optional[float]]:
    logger.debug("features", f"Computing rolling volatility with window={window} for {len(values)} values")
    out: List[Optional[float]] = []
    valid_count = 0
    for i in range(len(values)):
        if i + 1 < window:
            out.append(None)
        else:
            seg = values[i+1-window:i+1]
            if len(seg) > 1:
                try:
                    out.append(pstdev(seg))
                    valid_count += 1
                except Exception as e:
                    logger.debug("features", f"Volatility calculation failed at index {i}: {str(e)}")
                    out.append(None)
            else:
                out.append(None)
    logger.debug("features", f"Volatility computation complete: {valid_count} valid values")
    return out


def basic_feature_frame(store: StockDataManager, symbol: str, lookback: int = 200) -> List[Dict[str, Any]]:
    """Return list of dict rows containing basic features aligned with closes.

    Each row keys: index, close, sma_20, ema_20, vol_20, log_ret.
    Rows with insufficient history will have None values for those features.
    """
    logger.debug("features", f"Building basic feature frame for {symbol}, lookback={lookback}")
    closes = _get_closes(store, symbol, limit=lookback)
    logger.debug("features", f"Computing SMA20, EMA20, VOL20, log returns for {len(closes)} closes")
    sma20 = sma(closes, 20)
    ema20 = ema(closes, 20)
    vol20 = rolling_volatility(closes, 20)
    lret = log_returns(closes)
    rows: List[Dict[str, Any]] = []
    for i, close in enumerate(closes):
        rows.append({
            'index': i,
            'close': close,
            'sma_20': sma20[i],
            'ema_20': ema20[i],
            'vol_20': vol20[i],
            'log_ret': lret[i],
        })
    logger.info("features", f"Feature frame complete for {symbol}: {len(rows)} rows with features (SMA20, EMA20, VOL20, log_ret)")
    return rows

__all__ = [
    'sma','ema','log_returns','rolling_volatility','basic_feature_frame'
]
