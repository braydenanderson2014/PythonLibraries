# Real Stock Data Provider Setup Guide

This Financial Manager now supports multiple real-time stock data providers. You need to set at least ONE API key to enable real data fetching.

## Supported Providers

### 1. Polygon.io (Recommended)
- **Website**: https://polygon.io
- **Free Tier**: Yes - 5 API calls per minute, limited but free
- **Paid Tier**: Starting at $10/month
- **Features**: Best for tick data, company details, comprehensive
- **Setup**:
  ```bash
  # Windows (PowerShell)
  $env:POLYGON_API_KEY = "your_api_key_here"
  
  # Windows (Command Prompt)
  set POLYGON_API_KEY=your_api_key_here
  
  # Linux/Mac
  export POLYGON_API_KEY="your_api_key_here"
  ```

### 2. Finnhub
- **Website**: https://finnhub.io
- **Free Tier**: Yes - 60 API calls per minute
- **Paid Tier**: Starting at $10/month
- **Features**: Real-time quotes, company profiles, news
- **Setup**:
  ```bash
  # Windows (PowerShell)
  $env:FINNHUB_API_KEY = "your_api_key_here"
  
  # Windows (Command Prompt)
  set FINNHUB_API_KEY=your_api_key_here
  
  # Linux/Mac
  export FINNHUB_API_KEY="your_api_key_here"
  ```

### 3. Twelve Data
- **Website**: https://twelvedata.com
- **Free Tier**: Yes - 800 API calls per day, 5 RPS
- **Paid Tier**: Starting at $9/month
- **Features**: Stock, ETF, crypto quotes and fundamentals
- **Setup**:
  ```bash
  # Windows (PowerShell)
  $env:TWELVEDATA_API_KEY = "your_api_key_here"
  
  # Windows (Command Prompt)
  set TWELVEDATA_API_KEY=your_api_key_here
  
  # Linux/Mac
  export TWELVEDATA_API_KEY="your_api_key_here"
  ```

### 4. Alpha Vantage
- **Website**: https://www.alphavantage.co
- **Free Tier**: Yes - 5 API calls per minute
- **Paid Tier**: Starting at $20/month
- **Features**: Time series data, technical indicators
- **Setup**:
  ```bash
  # Windows (PowerShell)
  $env:ALPHA_VANTAGE_API_KEY = "your_api_key_here"
  
  # Windows (Command Prompt)
  set ALPHA_VANTAGE_API_KEY=your_api_key_here
  
  # Linux/Mac
  export ALPHA_VANTAGE_API_KEY="your_api_key_here"
  ```

## Setting Environment Variables Permanently

### Windows (PowerShell - Persistent)
1. Open PowerShell as Administrator
2. Run:
   ```powershell
   [Environment]::SetEnvironmentVariable("POLYGON_API_KEY", "your_key_here", "User")
   [Environment]::SetEnvironmentVariable("FINNHUB_API_KEY", "your_key_here", "User")
   ```
3. Restart the application

### Windows (Command Prompt - Persistent)
1. Right-click "This PC" → Properties
2. Click "Advanced system settings"
3. Click "Environment Variables"
4. Click "New" under "User variables"
5. Add variable names and values
6. Restart the application

### Linux/Mac (Add to ~/.bashrc or ~/.zshrc)
```bash
export POLYGON_API_KEY="your_key_here"
export FINNHUB_API_KEY="your_key_here"
export TWELVEDATA_API_KEY="your_key_here"
export ALPHA_VANTAGE_API_KEY="your_key_here"
```

Then run: `source ~/.bashrc` or `source ~/.zshrc`

## How It Works

The application uses a **Composite Provider** that:
1. Tries providers in priority order: Polygon → Finnhub → Twelve Data → Alpha Vantage
2. Fills gaps - if one provider doesn't have data, tries the next
3. Falls back gracefully if a provider is rate-limited or unavailable
4. Caches data to minimize API calls

## Getting Free API Keys

1. **Polygon.io**: Sign up at https://polygon.io/dashboard/signup - includes free tier
2. **Finnhub**: Sign up at https://finnhub.io - free tier available
3. **Twelve Data**: Sign up at https://twelvedata.com/register - free tier available
4. **Alpha Vantage**: Sign up at https://www.alphavantage.co/api - free tier available

## Verifying Setup

Run the application and try to add a stock. If you see real stock prices instead of mock data, your API key is working!

## Troubleshooting

**Error: "No data provider configured!"**
- You haven't set any API keys
- Set at least one environment variable
- Restart the application after setting the variable

**Prices look wrong or are blank**
- API rate limit might be exceeded
- Check if you have a valid API key
- Try a different provider
- Wait a few minutes and refresh

**Some stocks work, others don't**
- Different providers have different symbols support
- The composite provider will automatically try other sources
- Some stock symbols might not be available on all providers
