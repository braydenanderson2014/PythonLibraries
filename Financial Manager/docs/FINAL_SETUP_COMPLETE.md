# Stock Data Provider Configuration - Final Setup

## Current Configuration

You have created `resources/env.env` with your Alpha Vantage API key. The system now supports:

### Configured Providers:
1. **YFinance** (Free, no API key needed) - PRIMARY
2. **Alpha Vantage** (Your API key loaded from env.env)
3. **Polygon.io** (Optional - set POLYGON_API_KEY if needed)
4. **Finnhub** (Optional - set FINNHUB_API_KEY if needed)
5. **Twelve Data** (Optional - set TWELVEDATA_API_KEY if needed)

## Setup Complete ✓

### How It Works Now:

1. **env_loader.py** automatically loads `resources/env.env` on startup
2. **YFinance provider** is tried first (free, no API key)
3. **Alpha Vantage** falls back if yfinance fails or rate-limits
4. **Composite provider** tries all sources and picks the best data
5. Stock prices are now **REAL** instead of mock data

## Installation

If you don't have yfinance installed yet:

```bash
pip install yfinance
```

Or add it to requirements.txt:
```
yfinance>=0.2.32
pandas>=1.5.0
```

## Files Modified/Created

### New Files:
- `src/env_loader.py` - Loads environment variables from env.env
- `resources/env.env` - Your API keys (already created)

### Modified Files:
- `src/data_sources.py`:
  - Added `YFinanceProvider` class (free provider)
  - Updated `create_default_provider()` to load env.env and prioritize yfinance
  - Added pandas import for yfinance support
  - Updated error messages to recommend yfinance

## Using the System

### Option 1: YFinance Only (Recommended for most users)
Just run the app. YFinance will provide real stock data for free:
```bash
python main_window.py
```

### Option 2: YFinance + Alpha Vantage
Your setup - uses Alpha Vantage as backup:
```bash
python main_window.py
```
The system will:
- Try yfinance first (real-time prices)
- Use Alpha Vantage for historical data if yfinance is slow

### Option 3: Add More Providers
Set additional environment variables in `resources/env.env`:

```
ALPHA_VANTAGE_API_KEY=GBGQVHTP8GZCPAZS
POLYGON_API_KEY=your_polygon_key
FINNHUB_API_KEY=your_finnhub_key
```

## Provider Details

### YFinance
- **Cost**: Free (funded by community)
- **Rate Limit**: Generous, no official limit
- **Data**: Real-time prices, historical data
- **Company Details**: Yes, via ticker.info
- **Candles**: Yes, 1m/5m/15m/1h/1d intervals
- **No Auth**: Just works!
- **Install**: `pip install yfinance`

### Alpha Vantage (Your configured provider)
- **Cost**: Free tier available
- **Rate Limit**: 5 calls/minute (free tier)
- **Data**: Daily, intraday, technical indicators
- **Company Details**: Via SYMBOL_SEARCH function
- **Auth**: API key in env.env ✓

### Other Providers (Optional)
- **Polygon.io**: Best for professional use
- **Finnhub**: Good free tier (60 calls/min)
- **Twelve Data**: Good for batch requests

## Testing

### Check Configuration
```bash
python setup_providers.py
```

### Test Real Data
```bash
python test_real_providers.py
```

### Test YFinance Specifically
```python
from src.data_sources import YFinanceProvider

provider = YFinanceProvider()
quotes = provider.fetch_quotes(['AAPL', 'MSFT', 'GOOGL'])
for sym, data in quotes.items():
    print(f"{sym}: ${data['latest_price']}")
```

## Environment Variable Priority

The system looks for env.env in this order:
1. `resources/env.env` (your file)
2. Current working directory: `env.env`
3. `.env` file in current directory

## Modular Design

The system is completely modular:
- Each provider is a separate class
- Inherit from `QuoteProvider` to add new ones
- `CompositeQuoteProvider` combines them intelligently
- Easy to enable/disable providers via environment variables

### Adding a New Provider

```python
class MyProvider(QuoteProvider):
    name = "myprovider"
    
    def fetch_quotes(self, symbols):
        # Your implementation
        return {}
    
    def fetch_ticker_details(self, symbol):
        # Optional
        return None
```

Then add to `create_default_provider()`:
```python
try:
    providers.append(MyProvider())
except:
    pass
```

## Troubleshooting

**Problem: "No data provider configured"**
- Make sure yfinance is installed: `pip install yfinance`
- Or set ALPHA_VANTAGE_API_KEY environment variable

**Problem: Still seeing mock prices**
- Restart the application
- Verify env.env is in `resources/` folder
- Run `python setup_providers.py` to check

**Problem: Some stocks have no price**
- Try with different provider (if configured)
- Some symbols might not be available on all providers
- System will try next provider automatically

**Problem: Getting rate limited**
- YFinance: Usually stable, no official limits
- Alpha Vantage: 5 calls/min free, wait between requests
- Add Finnhub (60 calls/min) as backup

## Performance Tips

1. **Use YFinance first** - It's fast and free
2. **Add Alpha Vantage second** - Great backup, good historical data
3. **Set multiple providers** - System automatically load-balances
4. **Auto-refresh interval** - Use 5-15 minutes, not seconds (respects rate limits)

## Next Steps

1. ✅ env.env created with Alpha Vantage key
2. Install yfinance if not already: `pip install yfinance`
3. Run the app: `python main_window.py`
4. Add stocks to portfolio - you'll see REAL prices!
5. (Optional) Add more API keys to env.env for redundancy

## That's It!

Your system now has:
- ✅ Real stock prices from YFinance (free, no setup needed)
- ✅ Backup from Alpha Vantage (your API key loaded automatically)
- ✅ Modular system to add more providers later
- ✅ Automatic fallback when one provider fails
- ✅ Environment variables auto-loaded from env.env

**Run the app and enjoy real stock data!**
