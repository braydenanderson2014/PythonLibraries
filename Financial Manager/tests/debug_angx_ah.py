#!/usr/bin/env python
"""Investigate ANGX after-hours price issue."""

import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))

from src.data_sources import YFinanceProvider

print("Investigating ANGX after-hours price issue...\n")

provider = YFinanceProvider()
symbol = "ANGX"

# Get historical data with split info
print(f"Fetching {symbol} data with max interval...")
candles = provider.fetch_candles(symbol, interval='1d', limit=10000)

if candles:
    print(f"Got {len(candles)} candles\n")
    
    # Show first 20 candles with after-hours
    print("First 20 candles with after-hours prices:")
    print("-" * 80)
    for i, candle in enumerate(candles[:20]):
        start = candle.get('start', 'N/A')
        close = candle.get('close', 0)
        ah_price = candle.get('after_hours_price', None)
        if ah_price:
            print(f"{i+1:2d}. {start:30s} | Close: ${close:7.2f} | AH: ${ah_price:7.2f}")
        else:
            print(f"{i+1:2d}. {start:30s} | Close: ${close:7.2f} | AH: None")
    
    print("\n" + "-" * 80)
    
    # Check for any anomalies
    print("\nChecking for anomalies:")
    ah_prices = [c.get('after_hours_price', 0) for c in candles if c.get('after_hours_price')]
    regular_prices = [c.get('close', 0) for c in candles]
    
    if ah_prices:
        max_ah = max(ah_prices)
        max_close = max(regular_prices)
        print(f"Max after-hours price: ${max_ah:.2f}")
        print(f"Max closing price: ${max_close:.2f}")
        
        if max_ah > max_close * 1.2:
            print(f"\n⚠️  WARNING: After-hours prices are {(max_ah/max_close - 1)*100:.1f}% higher than closing prices!")
            print("This could indicate:")
            print("  1. Unadjusted intraday data (before stock split)")
            print("  2. Incorrect price aggregation from multiple sources")
            print("  3. Data from different exchanges")
    
    # Fetch raw intraday data to inspect
    print("\n" + "-" * 80)
    print("\nFetching raw intraday data for inspection...")
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        
        # Get intraday data with prepost=True
        intraday = ticker.history(period='90d', interval='1h', prepost=True)
        
        if not intraday.empty:
            print(f"Got {len(intraday)} intraday data points")
            
            # Group by date and show price range
            intraday['date'] = pd.to_datetime(intraday.index).date
            daily_ranges = intraday.groupby('date').agg({
                'Close': ['min', 'max', 'first', 'last']
            })
            
            print("\nIntraday price ranges (last 10 trading days):")
            print("-" * 80)
            for date, row in daily_ranges.tail(10).iterrows():
                min_price = row[('Close', 'min')]
                max_price = row[('Close', 'max')]
                first_price = row[('Close', 'first')]
                last_price = row[('Close', 'last')]
                print(f"{date} | Min: ${min_price:7.2f} | Max: ${max_price:7.2f} | First: ${first_price:7.2f} | Last: ${last_price:7.2f}")
            
            # Check for the high prices
            high_prices = intraday[intraday['Close'] > 17.91]
            if not high_prices.empty:
                print(f"\n⚠️  Found {len(high_prices)} data points above $17.91:")
                print("-" * 80)
                for idx, row in high_prices.head(10).iterrows():
                    print(f"{idx} | Close: ${row['Close']:.2f}")
    
    except Exception as e:
        print(f"Error: {e}")

else:
    print(f"No candles fetched for {symbol}")
