"""Pluggable stock data source architecture.

This module defines a set of provider classes that can fetch:
  * realtime/last quotes
  * candles (historical OHLCV)
  * fundamentals / metadata

It supplies a Composite provider that tries providers in priority order.

Providers implemented here are intentionally light-weight and will only
perform network calls if their public methods are invoked. API keys are
discovered from environment variables (documented below).

ENVIRONMENT VARIABLES (if present):
  ALPHA_VANTAGE_API_KEY
  POLYGON_API_KEY
  FINNHUB_API_KEY
  TWELVEDATA_API_KEY
  STOCKANALYSIS_API_KEY (placeholder – stockanalysis.com does not publish a
                         public official API; future integration point.)

Design Notes:
  - We keep the existing StockAPIClient interface (fetch_quotes) for
    backward compatibility; the Extended interface adds candles & fundamentals.
  - Each provider returns normalized dict structures so higher layers can
    ingest them directly with StockDataManager.ingest_quote / add_candle / upsert_fundamentals.
  - All timestamps normalized to UTC ISO 8601 strings.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Iterable
import os
import time

from assets.Logger import Logger
logger = Logger()

# Load environment variables from env.env if present
try:
    from .env_loader import _loaded_vars as _env_vars  # type: ignore
except Exception:
    _env_vars = {}

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # type: ignore

try:
    import pandas as pd  # type: ignore
except Exception:  # pragma: no cover
    pd = None  # type: ignore


# ----------------------------------------------------------------------------
# Base Interfaces
# ----------------------------------------------------------------------------

class QuoteProvider(ABC):
    name: str = "base"

    @abstractmethod
    def fetch_quotes(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """Return mapping symbol -> normalized quote dict.

        Required keys (normal form):
          symbol, latest_price, previous_close?, volume?, market_cap?, timestamp
        Additional keys allowed (e.g., open/high/low) for enrichment.
        """
        raise NotImplementedError

    def fetch_candles(self, symbol: str, *, interval: str = '1d', limit: int = 100) -> List[Dict[str, Any]]:  # pragma: no cover - optional
        """Return list of candles (dict) each with: open, high, low, close, volume, start, end."""
        return []

    def fetch_fundamentals(self, symbol: str) -> Optional[Dict[str, Any]]:  # pragma: no cover - optional
        return None

    def fetch_ticker_details(self, symbol: str) -> Optional[Dict[str, Any]]:  # pragma: no cover - optional
        """Fetch ticker/company details (name, exchange, etc).
        
        Returns dict with optional keys: name, exchange, description, etc.
        """
        return None

    # Corporate actions -------------------------------------------------
    def fetch_splits(self, symbol: str) -> List[Dict[str, Any]]:  # pragma: no cover - optional
        return []

    def fetch_dividends(self, symbol: str) -> List[Dict[str, Any]]:  # pragma: no cover - optional
        return []

    # Candle range ------------------------------------------------------
    def fetch_candles_range(self, symbol: str, *, interval: str, start: str, end: str) -> List[Dict[str, Any]]:  # pragma: no cover - optional
        return []


# ----------------------------------------------------------------------------
# Mock Provider (already present conceptually) but with candle/fundamental stubs
# ----------------------------------------------------------------------------

class MockProvider(QuoteProvider):
    name = "mock"

    def __init__(self, seed: int | None = None):
        logger.debug("MockProvider", f"Initializing MockProvider with seed: {seed}")
        import random
        self._rand = random.Random(seed)
        self._state: Dict[str, float] = {}

    def fetch_quotes(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        logger.debug("MockProvider", f"Fetching quotes for {len(symbols)} symbols")
        from datetime import datetime
        out: Dict[str, Dict[str, Any]] = {}
        now = datetime.utcnow().isoformat()
        for s in symbols:
            base = self._state.get(s, self._rand.uniform(10, 300))
            change = self._rand.uniform(-0.015, 0.015) * base
            price = max(0.01, base + change)
            self._state[s] = price
            out[s] = {
                'symbol': s,
                'latest_price': round(price, 2),
                'previous_close': round(base, 2),
                'volume': int(self._rand.uniform(50_000, 2_000_000)),
                'market_cap': round(price * self._rand.uniform(5_000_000, 200_000_000), 2),
                'open': round(base * self._rand.uniform(0.99, 1.01), 2),
                'high': round(price * 1.01, 2),
                'low': round(price * 0.99, 2),
                'timestamp': now,
            }
        return out

    def fetch_candles(self, symbol: str, *, interval: str = '1d', limit: int = 100) -> List[Dict[str, Any]]:
        logger.debug("MockProvider", f"Fetching {limit} candles for {symbol} (interval: {interval})")
        from datetime import datetime, timedelta
        now = datetime.utcnow()
        out: List[Dict[str, Any]] = []
        price = self._state.get(symbol, 100.0)
        for i in range(limit):
            end = now - timedelta(minutes=i if interval.endswith('m') else i*1440)
            start = end - timedelta(minutes=1 if interval.endswith('m') else 1440)
            o = price * (1 + self._rand.uniform(-0.01, 0.01))
            c = o * (1 + self._rand.uniform(-0.01, 0.01))
            h = max(o, c) * (1 + self._rand.uniform(0, 0.005))
            l = min(o, c) * (1 - self._rand.uniform(0, 0.005))
            v = int(self._rand.uniform(10_000, 150_000))
            out.append({
                'symbol': symbol,
                'interval': interval,
                'open': round(o, 2),
                'high': round(h, 2),
                'low': round(l, 2),
                'close': round(c, 2),
                'volume': v,
                'start': start.isoformat(),
                'end': end.isoformat(),
            })
        return list(reversed(out))

    def fetch_fundamentals(self, symbol: str) -> Optional[Dict[str, Any]]:
        logger.debug("MockProvider", f"Fetching fundamentals for {symbol}")
        return {
            'symbol': symbol,
            'sector': 'MockSector',
            'industry': 'MockIndustry',
            'pe_ratio': round(self._rand.uniform(5, 40), 2),
            'eps': round(self._rand.uniform(0.5, 10), 2),
            'dividend_yield': round(self._rand.uniform(0, 5), 2),
            'beta': round(self._rand.uniform(0.5, 1.5), 2),
            'shares_outstanding': int(self._rand.uniform(10_000_000, 2_000_000_000)),
        }

    def fetch_ticker_details(self, symbol: str) -> Optional[Dict[str, Any]]:
        logger.debug("MockProvider", f"Fetching ticker details for {symbol}")
        """Return mock company name and details."""
        company_names = {
            'AAPL': 'Apple Inc.',
            'MSFT': 'Microsoft Corporation',
            'GOOGL': 'Alphabet Inc.',
            'AMZN': 'Amazon.com Inc.',
            'TSLA': 'Tesla Inc.',
            'META': 'Meta Platforms Inc.',
            'NVDA': 'NVIDIA Corporation',
        }
        name = company_names.get(symbol.upper(), f"{symbol} Corporation")
        return {
            'symbol': symbol.upper(),
            'name': name,
            'exchange': 'NASDAQ' if symbol.upper() in ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'META', 'NVDA'] else 'NYSE',
        }



# ----------------------------------------------------------------------------
# External Providers (stubs & partial implementations)
# ----------------------------------------------------------------------------

class _HTTPProviderMixin:
    timeout = 10

    def _get(self, url: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:  # pragma: no cover - network not tested
        if requests is None:
            raise RuntimeError("'requests' not installed; add to requirements.txt")
        r = requests.get(url, params=params, timeout=self.timeout)
        if r.status_code != 200:
            return None
        try:
            return r.json()
        except Exception:
            return None


class AlphaVantageProvider(_HTTPProviderMixin, QuoteProvider):  # pragma: no cover - network
    name = "alpha_vantage"
    BASE = "https://www.alphavantage.co/query"

    def __init__(self, api_key: str):
        logger.debug("AlphaVantageProvider", "Initializing AlphaVantageProvider")
        self.api_key = api_key
        self._last_call = 0.0
        self._min_interval = 12.0  # free tier ~5 calls/minute

    def _throttle(self):
        delta = time.time() - self._last_call
        if delta < self._min_interval:
            time.sleep(self._min_interval - delta)
        self._last_call = time.time()

    def fetch_quotes(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        logger.debug("AlphaVantageProvider", f"Fetching quotes for {len(symbols)} symbols")
        # Alpha Vantage best-effort: GLOBAL_QUOTE one by one (slow on free tier)
        out: Dict[str, Dict[str, Any]] = {}
        for sym in symbols:
            self._throttle()
            data = self._get(self.BASE, {
                'function': 'GLOBAL_QUOTE',
                'symbol': sym,
                'apikey': self.api_key,
            }) or {}
            quote = data.get('Global Quote', {})
            if quote:
                out[sym] = {
                    'symbol': sym,
                    'latest_price': float(quote.get('05. price', '0') or 0),
                    'previous_close': float(quote.get('08. previous close', '0') or 0),
                    'volume': int(float(quote.get('06. volume', '0') or 0)),
                    'timestamp': quote.get('07. latest trading day'),
                }
        return out

    def fetch_candles(self, symbol: str, *, interval: str = '1d', limit: int = 100) -> List[Dict[str, Any]]:
        logger.debug("AlphaVantageProvider", f"Fetching {limit} candles for {symbol}")
        func = 'TIME_SERIES_DAILY_ADJUSTED'
        data = self._get(self.BASE, {
            'function': func,
            'symbol': symbol,
            'apikey': self.api_key,
            'outputsize': 'full' if limit > 100 else 'compact'
        }) or {}
        series = data.get('Time Series (Daily)', {})
        out: List[Dict[str, Any]] = []
        for date_str, row in list(series.items())[:limit]:
            o = float(row.get('1. open', 0))
            h = float(row.get('2. high', 0))
            l = float(row.get('3. low', 0))
            c = float(row.get('4. close', 0))
            v = int(float(row.get('6. volume', 0)))
            out.append({
                'symbol': symbol,
                'interval': '1d',
                'open': o, 'high': h, 'low': l, 'close': c, 'volume': v,
                'start': f"{date_str}T00:00:00Z",
                'end': f"{date_str}T23:59:59Z",
            })
        return out

    def fetch_ticker_details(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch ticker details from Alpha Vantage.
        
        Alpha Vantage doesn't have a dedicated ticker details endpoint,
        so we return None to fall back to other providers.
        """
        return None
        return out


class PolygonProvider(_HTTPProviderMixin, QuoteProvider):  # pragma: no cover - network
    name = "polygon"
    BASE = "https://api.polygon.io"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def fetch_quotes(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        logger.debug("PolygonProvider", f"Fetching quotes for {len(symbols)} symbols")
        # Polygon has batch endpoint for snapshots; for simplicity fetch individually
        out: Dict[str, Dict[str, Any]] = {}
        for sym in symbols:
            data = self._get(f"{self.BASE}/v2/aggs/ticker/{sym}/prev", {'apiKey': self.api_key}) or {}
            results = data.get('results') or []
            if results:
                r = results[0]
                out[sym] = {
                    'symbol': sym,
                    'latest_price': r.get('c'),
                    'previous_close': r.get('o'),
                    'volume': r.get('v'),
                    'timestamp': r.get('t'),
                }
        return out

    def fetch_candles(self, symbol: str, *, interval: str = '1d', limit: int = 100) -> List[Dict[str, Any]]:
        # Use aggregate bars endpoint with range derived from limit (daily only in simplified form)
        # If interval not '1d' we could map but for now handle '1d'
        from datetime import datetime, timedelta
        end_dt = datetime.utcnow()
        start_dt = end_dt - timedelta(days=limit + 5)
        return self.fetch_candles_range(symbol, interval=interval, start=start_dt.strftime('%Y-%m-%d'), end=end_dt.strftime('%Y-%m-%d'))

    def fetch_candles_range(self, symbol: str, *, interval: str, start: str, end: str) -> List[Dict[str, Any]]:
        # Polygon range endpoint: /v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from}/{to}
        # Map interval to multiplier/timespan
        mapping = {
            '1d': (1, 'day'),
            '1h': (1, 'hour'),
            '15m': (15, 'minute'),
            '5m': (5, 'minute'),
            '1m': (1, 'minute'),
        }
        mult, span = mapping.get(interval, (1, 'day'))
        url = f"{self.BASE}/v2/aggs/ticker/{symbol}/range/{mult}/{span}/{start}/{end}"
        data = self._get(url, {'apiKey': self.api_key}) or {}
        results = data.get('results') or []
        out: List[Dict[str, Any]] = []
        for r in results:
            out.append({
                'symbol': symbol,
                'interval': interval,
                'open': r.get('o'), 'high': r.get('h'), 'low': r.get('l'), 'close': r.get('c'),
                'volume': r.get('v'),
                'start': r.get('t'), 'end': r.get('t'),  # polygon gives epoch ms
            })
        return out

    def fetch_splits(self, symbol: str) -> List[Dict[str, Any]]:
        data = self._get(f"{self.BASE}/v3/reference/splits", {'ticker': symbol, 'apiKey': self.api_key, 'limit': 1000}) or {}
        results = data.get('results') or []
        out = []
        for r in results:
            try:
                ratio = (r.get('split_to') or 1) / (r.get('split_from') or 1)
                out.append({'date': r.get('execution_date'), 'ratio': ratio})
            except Exception:
                continue
        return out

    def fetch_dividends(self, symbol: str) -> List[Dict[str, Any]]:
        data = self._get(f"{self.BASE}/v3/reference/dividends", {'ticker': symbol, 'apiKey': self.api_key, 'limit': 1000}) or {}
        results = data.get('results') or []
        out = []
        for r in results:
            amt = r.get('cash_amount')
            exec_date = r.get('ex_dividend_date') or r.get('record_date')
            if amt is not None and exec_date:
                out.append({'date': exec_date, 'amount': amt})
        return out

    def fetch_ticker_details(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch ticker details from Polygon API."""
        data = self._get(f"{self.BASE}/v3/reference/tickers/{symbol}", {'apiKey': self.api_key}) or {}
        results = data.get('results')
        if results:
            return {
                'symbol': results.get('ticker', symbol).upper(),
                'name': results.get('name'),
                'exchange': results.get('primary_exchange'),
            }
        return None


class YFinanceProvider(QuoteProvider):  # pragma: no cover - network
    """Free provider using yfinance library (no API key required).
    
    Great for current prices and historical data.
    Requires: pip install yfinance
    """
    name = "yfinance"
    
    def __init__(self):
        try:
            import yfinance  # type: ignore
            self.yf = yfinance
        except ImportError:
            raise RuntimeError(
                "yfinance not installed. Install with: pip install yfinance"
            )
    
    def fetch_quotes(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """Fetch quotes from Yahoo Finance via yfinance."""
        from datetime import datetime
        out: Dict[str, Dict[str, Any]] = {}
        now = datetime.utcnow().isoformat()
        
        for sym in symbols:
            try:
                ticker = self.yf.Ticker(sym)
                # Get current data
                data = ticker.history(period='1d')
                if data.empty:
                    continue
                
                latest = data.iloc[-1]
                info = ticker.info or {}
                
                # Get the actual closing price and current price (may be after-hours)
                closing_price = float(latest['Close']) if 'Close' in latest and not pd.isna(latest['Close']) else None
                current_price = float(info.get('currentPrice', closing_price)) if info.get('currentPrice') else closing_price
                previous_close = float(info.get('previousClose')) if info.get('previousClose') else closing_price
                
                # After-hours information
                post_market_price = float(info.get('postMarketPrice')) if info.get('postMarketPrice') else None
                post_market_change = float(info.get('postMarketChange')) if info.get('postMarketChange') else None
                post_market_change_percent = float(info.get('postMarketChangePercent')) if info.get('postMarketChangePercent') else None
                
                out[sym] = {
                    'symbol': sym.upper(),
                    'latest_price': current_price or closing_price,
                    'regularMarketPrice': closing_price,  # Regular market closing price
                    'closing_price': closing_price,
                    'postMarketPrice': post_market_price,
                    'after_hours_price': post_market_price,
                    'postMarketChange': post_market_change,
                    'post_market_change': post_market_change,
                    'postMarketChangePercent': post_market_change_percent,
                    'post_market_change_percent': post_market_change_percent,
                    'previous_close': previous_close,
                    'volume': int(latest['Volume']) if 'Volume' in latest and not pd.isna(latest['Volume']) else None,
                    'market_cap': float(info.get('marketCap', 0)) if info.get('marketCap') else None,
                    'timestamp': now,
                }
            except Exception as e:
                logger.error("YFinanceProvider", f"Error fetching {sym}: {str(e)}")
                continue
        
        return out
    
    def fetch_candles(self, symbol: str, *, interval: str = '1d', limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch historical candles from Yahoo Finance."""
        logger.debug("YFinanceProvider", f"Fetching {limit} candles for {symbol} (interval: {interval})")
        
        try:
            logger.debug("YFinanceProvider", f"Attempting to fetch {symbol} with interval={interval}")
            ticker = self.yf.Ticker(symbol)
            
            # Map chart intervals to yfinance intervals
            # Chart passes: 1d, 5d, 1mo, 3mo, 6mo, 1y, 5y, max
            # We convert to daily data for all these ranges
            period_map = {
                '1m': '60m',     # 1 minute (5d max history)
                '5m': '5m',      # 5 minutes
                '15m': '15m',    # 15 minutes
                '1h': '1h',      # 1 hour
                '1d': '1d',      # 1 day (daily bars)
                '5d': '1d',      # 5 days (use daily bars)
                '1mo': '1d',     # 1 month (use daily bars)
                '3mo': '1d',     # 3 months (use daily bars)
                '6mo': '1d',     # 6 months (use daily bars)
                '1y': '1d',      # 1 year (use daily bars)
                '5y': '1d',      # 5 years (use daily bars)
                'max': '1d',     # All time (use daily bars)
            }
            period = period_map.get(interval, '1d')
            
            # Map chart periods to yfinance history periods
            history_map = {
                '1m': '5d',
                '5m': '60d',
                '15m': '60d',
                '1h': '730d',
                '1d': 'max',
                '5d': '5d',
                '1mo': '1mo',
                '3mo': '3mo',
                '6mo': '6mo',
                '1y': '1y',
                '5y': '5y',
                'max': 'max',
            }
            history = history_map.get(interval, 'max')
            
            logger.debug("YFinanceProvider", f"Fetching {symbol} with history={history}, period={period}")
            
            data = ticker.history(period=history, interval=period)
            logger.debug("YFinanceProvider", f"Got {len(data) if not data.empty else 0} rows from ticker.history()")
            
            if data.empty:
                logger.warning("YFinanceProvider", f"Empty data for {symbol} with history={history}, period={period}")
                return []
            
            out = []
            for i, (date, row) in enumerate(data.iterrows()):
                if pd.isna(row['Close']):
                    continue
                
                out.append({
                    'symbol': symbol,
                    'interval': interval,
                    'open': float(row['Open']) if not pd.isna(row['Open']) else None,
                    'high': float(row['High']) if not pd.isna(row['High']) else None,
                    'low': float(row['Low']) if not pd.isna(row['Low']) else None,
                    'close': float(row['Close']),
                    'volume': int(row['Volume']) if not pd.isna(row['Volume']) else None,
                    'start': date.isoformat(),
                    'end': date.isoformat(),
                })
            
            # Try to fetch after-hours price data
            try:
                if out:
                    # Get intraday data with extended hours to capture after-hours trading
                    # This helps us estimate after-hours prices for multiple days
                    intraday_limit = min(60, len(out))  # Get intraday for last N days
                    period_map_intraday = {
                        '1d': '5d',
                        '5d': '60d',
                        '1mo': '60d',
                        '3mo': '60d',
                        '6mo': '90d',
                        '1y': '90d',
                        '5y': '90d',
                        'max': '90d',
                    }
                    intraday_period = period_map_intraday.get(interval, '60d')
                    
                    try:
                        intraday_data = ticker.history(period=intraday_period, interval='1h', prepost=True)
                        
                        if not intraday_data.empty:
                            # Group by date and extract after-hours close (16:00-20:00 ET)
                            intraday_data_copy = intraday_data.copy()
                            intraday_data_copy['date'] = pd.to_datetime(intraday_data_copy.index).date
                            intraday_data_copy['hour'] = pd.to_datetime(intraday_data_copy.index).hour
                            
                            # After-hours trading typically 16:00 (4 PM) to 20:00 (8 PM) ET
                            after_hours_data = intraday_data_copy[(intraday_data_copy['hour'] >= 16) & (intraday_data_copy['hour'] <= 19)]
                            
                            # Get the last after-hours close for each day
                            ah_by_date = after_hours_data.groupby('date')['Close'].last()
                            
                            # Get today's date to limit how far back we use intraday data
                            # Intraday data may be unadjusted, so only use recent data to be safe
                            from datetime import datetime, timedelta
                            today = datetime.now().date()
                            cutoff_date = today - timedelta(days=30)  # Only use intraday for last 30 days
                            
                            # Match after-hours prices to our daily candles
                            for i, candle in enumerate(out):
                                candle_date = pd.to_datetime(candle['start']).date()
                                # Only apply after-hours price if it's recent enough to trust the data
                                if candle_date in ah_by_date.index and candle_date >= cutoff_date:
                                    ah_price = float(ah_by_date[candle_date])
                                    # Validate the price is reasonable (not more than 50% above daily close)
                                    daily_close = candle.get('close', 0)
                                    if not pd.isna(ah_price) and ah_price > 0 and daily_close > 0:
                                        # After-hours should be within reasonable range of daily close
                                        if ah_price <= daily_close * 1.10:  # Allow up to 10% above close
                                            out[i]['after_hours_price'] = ah_price
                                            logger.debug("YFinanceProvider", f"Added after-hours price ${ah_price:.2f} for {candle_date}")
                                        else:
                                            logger.debug("YFinanceProvider", f"Rejected unrealistic after-hours price ${ah_price:.2f} (close: ${daily_close:.2f}) for {candle_date}")
                    except Exception as intraday_e:
                        logger.debug("YFinanceProvider", f"Could not fetch intraday data for after-hours: {intraday_e}")
                        
                        # Fallback: at least get today's after-hours price
                        try:
                            quote = ticker.info or {}
                            if 'postMarketPrice' in quote and out:
                                out[-1]['after_hours_price'] = float(quote['postMarketPrice'])
                                logger.debug("YFinanceProvider", f"Added today's after-hours price from ticker info")
                        except:
                            pass
            except Exception as ah_e:
                logger.debug("YFinanceProvider", f"Error processing after-hours data: {ah_e}")
            
            logger.info("YFinanceProvider", f"Successfully fetched {len(out)} candles for {symbol} (interval={interval})")
            # Return last `limit` candles
            return out[-limit:] if limit else out
        except Exception as e:
            logger.error("YFinanceProvider", f"Error fetching candles for {symbol}: {type(e).__name__}: {str(e)}")
            return []
    
    def fetch_ticker_details(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch company details from Yahoo Finance."""
        logger.debug("YFinanceProvider", f"Fetching ticker details for {symbol}")
        try:
            ticker = self.yf.Ticker(symbol)
            info = ticker.info or {}
            
            return {
                'symbol': symbol.upper(),
                'name': info.get('longName') or info.get('shortName'),
                'exchange': info.get('exchange'),
            }
        except Exception:
            return None
    
    def fetch_fundamentals(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch fundamentals from Yahoo Finance."""
        logger.debug("YFinanceProvider", f"Fetching fundamentals for {symbol}")
        try:
            ticker = self.yf.Ticker(symbol)
            info = ticker.info or {}
            
            return {
                'symbol': symbol.upper(),
                'sector': info.get('sector'),
                'industry': info.get('industry'),
                'pe_ratio': float(info.get('trailingPE', 0)) if info.get('trailingPE') else None,
                'eps': float(info.get('trailingEps', 0)) if info.get('trailingEps') else None,
                'dividend_yield': float(info.get('dividendYield', 0)) if info.get('dividendYield') else None,
                'beta': float(info.get('beta', 0)) if info.get('beta') else None,
                'market_cap': float(info.get('marketCap', 0)) if info.get('marketCap') else None,
                'fifty_two_week_high': float(info.get('fiftyTwoWeekHigh', 0)) if info.get('fiftyTwoWeekHigh') else None,
                'fifty_two_week_low': float(info.get('fiftyTwoWeekLow', 0)) if info.get('fiftyTwoWeekLow') else None,
            }
        except Exception:
            return None


class FinnhubProvider(_HTTPProviderMixin, QuoteProvider):  # pragma: no cover - network
    name = "finnhub"
    BASE = "https://finnhub.io/api/v1"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def fetch_quotes(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """Fetch quotes from Finnhub."""
        logger.debug("FinnhubProvider", f"Fetching quotes for {len(symbols)} symbols")
        out: Dict[str, Dict[str, Any]] = {}
        from datetime import datetime
        now = datetime.utcnow().isoformat()
        
        for sym in symbols:
            data = self._get(f"{self.BASE}/quote", {'symbol': sym, 'token': self.api_key}) or {}
            if data and data.get('c'):  # c = current price
                out[sym] = {
                    'symbol': sym,
                    'latest_price': data.get('c'),  # current price
                    'previous_close': data.get('pc'),  # previous close
                    'volume': data.get('v'),  # volume (intraday)
                    'timestamp': now,
                }
        return out

    def fetch_ticker_details(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch company details from Finnhub."""
        logger.debug("FinnhubProvider", f"Fetching ticker details for {symbol}")
        data = self._get(f"{self.BASE}/stock/profile2", {'symbol': symbol, 'token': self.api_key}) or {}
        if data:
            return {
                'symbol': data.get('ticker', symbol).upper(),
                'name': data.get('name'),
                'exchange': data.get('exchange'),
            }
        return None


class TwelveDataProvider(_HTTPProviderMixin, QuoteProvider):  # pragma: no cover - network
    name = "twelvedata"
    BASE = "https://api.twelvedata.com"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def fetch_quotes(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """Fetch quotes from Twelve Data."""
        logger.debug("TwelveDataProvider", f"Fetching quotes for {len(symbols)} symbols")
        out: Dict[str, Dict[str, Any]] = {}
        
        # Twelve Data supports batch requests
        sym_list = ','.join(symbols)
        data = self._get(f"{self.BASE}/quote", {'symbols': sym_list, 'apikey': self.api_key}) or {}
        
        for result in data.get('data', []):
            sym = result.get('symbol', '').upper()
            if sym and result.get('last'):
                out[sym] = {
                    'symbol': sym,
                    'latest_price': float(result.get('last', 0)),
                    'previous_close': float(result.get('previous_close', 0)) if result.get('previous_close') else None,
                    'volume': int(float(result.get('volume', 0))) if result.get('volume') else None,
                    'timestamp': result.get('timestamp'),
                }
        return out

    def fetch_ticker_details(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch company details from Twelve Data."""
        logger.debug("TwelveDataProvider", f"Fetching ticker details for {symbol}")
        data = self._get(f"{self.BASE}/symbol_search", {'symbol': symbol, 'apikey': self.api_key}) or {}
        
        results = data.get('data', [])
        if results:
            first = results[0]
            return {
                'symbol': first.get('symbol', symbol).upper(),
                'name': first.get('instrument_name'),
                'exchange': first.get('exchange'),
            }
        return None


# Placeholder provider for stockanalysis.com (no public API documented)
class StockAnalysisProvider(QuoteProvider):  # pragma: no cover - placeholder
    name = "stockanalysis"
    def __init__(self, api_key: Optional[str] = None):
        logger.debug("StockAnalysisProvider", "Initializing StockAnalysisProvider")
        self.api_key = api_key
    def fetch_quotes(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        logger.debug("StockAnalysisProvider", f"Fetching quotes for {len(symbols)} symbols")
        # Placeholder: real implementation would be added if official API emerges.
        return {}



# ----------------------------------------------------------------------------
# Composite / Factory
# ----------------------------------------------------------------------------

class CompositeQuoteProvider(QuoteProvider):
    name = "composite"

    def __init__(self, providers: Iterable[QuoteProvider]):
        self._providers = list(providers)

    def fetch_quotes(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        logger.debug("CompositeQuoteProvider", f"Fetching quotes for {len(symbols)} symbols from {len(self._providers)} providers")
        remaining = set(s.upper() for s in symbols)
        aggregate: Dict[str, Dict[str, Any]] = {}
        for provider in self._providers:
            if not remaining:
                break
            try:
                result = provider.fetch_quotes(list(remaining))
            except Exception:
                continue
            for sym, data in result.items():
                if sym.upper() in remaining:
                    aggregate[sym.upper()] = data
                    remaining.remove(sym.upper())
        return aggregate

    def fetch_candles(self, symbol: str, *, interval: str = '1d', limit: int = 100) -> List[Dict[str, Any]]:
        logger.info("CompositeQuoteProvider", f"Trying {len(self._providers)} providers for {symbol} candles")
        for i, provider in enumerate(self._providers):
            try:
                logger.debug("CompositeQuoteProvider", f"Trying provider {i+1}/{len(self._providers)}: {provider.name}")
                candles = provider.fetch_candles(symbol, interval=interval, limit=limit)
                if candles:
                    logger.info("CompositeQuoteProvider", f"Provider {provider.name} returned {len(candles)} candles")
                    return candles
                else:
                    logger.debug("CompositeQuoteProvider", f"Provider {provider.name} returned empty list")
            except Exception as e:
                logger.debug("CompositeQuoteProvider", f"Provider {provider.name} failed: {str(e)}")
                continue
        logger.warning("CompositeQuoteProvider", f"All providers failed to get candles for {symbol}")
        return []

    def fetch_fundamentals(self, symbol: str) -> Optional[Dict[str, Any]]:
        logger.debug("CompositeQuoteProvider", f"Fetching fundamentals for {symbol}")
        for provider in self._providers:
            try:
                f = provider.fetch_fundamentals(symbol)
                if f:
                    return f
            except Exception:
                continue
        return None

    def fetch_ticker_details(self, symbol: str) -> Optional[Dict[str, Any]]:
        logger.debug("CompositeQuoteProvider", f"Fetching ticker details for {symbol}")
        for provider in self._providers:
            try:
                details = provider.fetch_ticker_details(symbol)
                if details:
                    return details
            except Exception:
                continue
        return None



def create_default_provider(include_mock: bool = False) -> QuoteProvider:
    logger.debug("create_default_provider", f"Creating default provider (include_mock={include_mock})")
    providers: List[QuoteProvider] = []
    
    # Priority order (high fidelity first)
    # 1. Free provider with excellent coverage (no API key needed)
    try:
        providers.append(YFinanceProvider())
    except Exception:
        pass  # yfinance not installed, skip
    
    # 2. API key-based providers (in preference order)
    if (k := os.getenv('ALPHA_VANTAGE_API_KEY')):
        providers.append(AlphaVantageProvider(k))
    if (k := os.getenv('POLYGON_API_KEY')):
        providers.append(PolygonProvider(k))
    if (k := os.getenv('FINNHUB_API_KEY')):
        providers.append(FinnhubProvider(k))
    if (k := os.getenv('TWELVEDATA_API_KEY')):
        providers.append(TwelveDataProvider(k))
    
    # 3. Placeholder (only if API key set by user in future)
    if (k := os.getenv('STOCKANALYSIS_API_KEY')):
        providers.append(StockAnalysisProvider(k))
    
    # Fall back to mock if nothing configured
    if not providers:
        if include_mock:
            providers.append(MockProvider())
        else:
            raise RuntimeError(
                "No data provider configured!\n"
                "Option 1 (Recommended): Install yfinance (pip install yfinance) - Free, no API key needed\n"
                "Option 2: Set environment variables for:\n"
                "  - ALPHA_VANTAGE_API_KEY (https://www.alphavantage.co) - Free tier available\n"
                "  - POLYGON_API_KEY (https://polygon.io)\n"
                "  - FINNHUB_API_KEY (https://finnhub.io)\n"
                "  - TWELVEDATA_API_KEY (https://twelvedata.com)"
            )
    
    # Always return CompositeQuoteProvider for consistent fallback behavior
    return CompositeQuoteProvider(providers)


__all__ = [
    'QuoteProvider', 'MockProvider', 'YFinanceProvider', 'AlphaVantageProvider', 
    'PolygonProvider', 'FinnhubProvider', 'TwelveDataProvider', 'StockAnalysisProvider', 
    'CompositeQuoteProvider', 'create_default_provider'
]
