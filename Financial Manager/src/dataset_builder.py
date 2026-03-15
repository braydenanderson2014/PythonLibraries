"""Dataset builder for supervised learning on stock time-series.

Produces feature/label rows for a single symbol with configurable future
return horizons while avoiding lookahead leakage.
"""
from __future__ import annotations

from typing import List, Dict, Any, Sequence, Optional
from math import log
from assets.Logger import Logger

try:
    from .stock_data import StockDataManager
    from .features import basic_feature_frame
    from ...benchmark_data import enrich_with_benchmarks, enrich_with_macro  # type: ignore
except Exception:  # pragma: no cover
    from stock_data import StockDataManager  # type: ignore
    from features import basic_feature_frame  # type: ignore
    from benchmark_data import enrich_with_benchmarks, enrich_with_macro  # type: ignore


def build_symbol_dataset(
    store: StockDataManager,
    symbol: str,
    *,
    lookback: int = 400,
    horizons: Sequence[int] = (1,5,20),
    include_benchmarks: bool = False,
    benchmarks: Optional[Sequence[str]] = None,
    include_macro: bool = False,
    macro_series: Optional[Sequence[str]] = None,
    include_sentiment: bool = False,
    include_short_interest: bool = False,
) -> List[Dict[str, Any]]:
    logger = Logger()
    logger.debug("build_symbol_dataset", f"Starting dataset build for {symbol}, lookback={lookback}, horizons={horizons}")
    rows = basic_feature_frame(store, symbol, lookback=lookback)
    logger.info("build_symbol_dataset", f"Generated {len(rows)} feature rows for {symbol}")
    if include_benchmarks and benchmarks:
        logger.debug("build_symbol_dataset", f"Enriching with {len(benchmarks)} benchmarks: {benchmarks}")
        enrich_with_benchmarks(rows, list(benchmarks))
        logger.info("build_symbol_dataset", f"Enriched {len(rows)} rows with benchmark data")
    if include_macro and macro_series:
        logger.debug("build_symbol_dataset", f"Enriching with {len(macro_series)} macro series: {macro_series}")
        enrich_with_macro(rows, list(macro_series))
        logger.info("build_symbol_dataset", f"Enriched {len(rows)} rows with macro data")
    if include_sentiment:
        logger.debug("build_symbol_dataset", f"Enriching {symbol} with sentiment data")
        try:
            from ...alt_data import enrich_with_sentiment  # type: ignore
        except Exception:
            from alt_data import enrich_with_sentiment  # type: ignore
        enrich_with_sentiment(rows, symbol)
        logger.info("build_symbol_dataset", f"Enriched {len(rows)} rows with sentiment data")
    if include_short_interest:
        logger.debug("build_symbol_dataset", f"Enriching {symbol} with short interest data")
        try:
            from ...alt_data import enrich_with_short_interest  # type: ignore
        except Exception:
            from alt_data import enrich_with_short_interest  # type: ignore
        enrich_with_short_interest(rows, symbol)
        logger.info("build_symbol_dataset", f"Enriched {len(rows)} rows with short interest data")
    closes = [r['close'] for r in rows]
    logger.debug("build_symbol_dataset", f"Computing future returns for {len(horizons)} horizons")
    # compute future returns for each horizon (log)
    for i, r in enumerate(rows):
        for h in horizons:
            if i + h < len(closes) and closes[i] and closes[i+h]:
                r[f'fut_ret_{h}'] = log(closes[i+h]/closes[i])
            else:
                r[f'fut_ret_{h}'] = None
    logger.debug("build_symbol_dataset", f"Computed future returns for {len(rows)} rows")
    # drop rows where any future label is None (preserve enriched features already attached)
    usable = [r for r in rows if all(r.get(f'fut_ret_{h}') is not None for h in horizons)]
    logger.info("build_symbol_dataset", f"Dataset build complete for {symbol}: {len(usable)}/{len(rows)} rows usable ({100*len(usable)//len(rows) if rows else 0}%)")
    return usable

__all__ = ["build_symbol_dataset"]
