# Real Stock Data Providers - Complete Setup

## Summary of Changes

The Financial Manager now supports **4 real-time stock data providers** instead of just mock data:

1. **Polygon.io** - Recommended, comprehensive
2. **Finnhub** - Fast, reliable 
3. **Twelve Data** - Good free tier
4. **Alpha Vantage** - Alternative option

The system uses a **Composite Provider** that automatically:
- Tries providers in priority order
- Falls back to next provider if one fails/rate-limits
- Combines data from multiple sources for best coverage
- Caches results to minimize API calls

## Quick Start

### Step 1: Get a Free API Key

Pick one of these (all offer free tiers):

- **Polygon.io** (Recommended): https://polygon.io/dashboard/signup
  - Free tier: 5 API calls/minute
  - Great documentation and company details

- **Finnhub**: https://finnhub.io/api
  - Free tier: 60 API calls/minute  
  - Best free tier rate limit

- **Twelve Data**: https://twelvedata.com/register
  - Free tier: 800 API calls/day
  - Good coverage of stocks

- **Alpha Vantage**: https://www.alphavantage.co/api
  - Free tier: 5 API calls/minute
  - Time series data

### Step 2: Set Environment Variable

**Windows (PowerShell):**
```powershell
$env:POLYGON_API_KEY = "your_api_key_here"
```

**Windows (Command Prompt):**
```cmd
set POLYGON_API_KEY=your_api_key_here
```

**Windows (Permanent - PowerShell as Admin):**
```powershell
[Environment]::SetEnvironmentVariable("POLYGON_API_KEY", "your_key_here", "User")
```

**Linux/Mac:**
```bash
export POLYGON_API_KEY="your_api_key_here"
```

### Step 3: Restart and Test

1. Restart the Financial Manager app
2. Add a stock (e.g., AAPL, MSFT)
3. You should see real stock prices!

## Helper Scripts

### Check Configuration
```bash
python setup_providers.py
```
Shows which providers are configured.

### Test Providers
```bash
python test_real_providers.py
```
Tests each configured provider with sample stocks.

## Using Multiple Providers (Recommended)

Set multiple API keys for better coverage:

```powershell
$env:POLYGON_API_KEY = "poly_key_here"
$env:FINNHUB_API_KEY = "finnhub_key_here"
$env:TWELVEDATA_API_KEY = "twelve_key_here"
```

The app will:
1. Try Polygon first
2. Use Finnhub for symbols Polygon doesn't have
3. Use Twelve Data as backup
4. Use Alpha Vantage as fallback

## File Changes

### New Files
- `REAL_DATA_SETUP.md` - Detailed setup guide
- `setup_providers.py` - Check current configuration
- `test_real_providers.py` - Test provider connectivity

### Modified Files
- `src/data_sources.py`:
  - Added `FinnhubProvider` class
  - Added `TwelveDataProvider` class
  - Updated `create_default_provider()` to NOT use mock by default
  - Changed default to fail if no providers configured
  - Updated `__all__` to include new providers

- `ui/stock_watchlist_widget.py`:
  - Already imports `create_default_provider` for name fetching

- `ui/stock_portfolio_widget.py`:
  - Already imports `create_default_provider` for name fetching

## What You Get

✓ Real stock prices instead of random mock data
✓ Automatic fallback if one provider fails
✓ Company names fetched on add and refresh
✓ Multiple providers for redundancy
✓ Accurate portfolio calculations based on real prices

## Troubleshooting

**Problem: "No data provider configured"**
- Set at least one API key environment variable
- Restart the app
- Run: `python setup_providers.py` to verify

**Problem: Prices are still mock data**
- Environment variable wasn't set before app started
- Restart the app after setting the variable
- Run: `python test_real_providers.py` to test

**Problem: Some stocks don't show price**
- Symbol might not be available on that provider
- With multiple providers set, it will try others
- Check the provider's supported symbols list

**Problem: Rate limited**
- Hit provider's API limit
- Wait a few minutes
- Set multiple providers for better limits
- Some providers offer paid tiers for higher limits

## API Rate Limits

| Provider | Free Tier | Limit |
|----------|-----------|-------|
| Polygon | Yes | 5 calls/minute |
| Finnhub | Yes | 60 calls/minute |
| Twelve Data | Yes | 800 calls/day (unlimited RPS) |
| Alpha Vantage | Yes | 5 calls/minute |

**Tip**: Use Finnhub or Twelve Data for better free tier limits!

## Next Steps

1. Choose a provider from the list above
2. Sign up for a free API key
3. Set the environment variable
4. Restart the app
5. Add stocks and verify real prices are showing
6. Consider adding a second provider as backup
