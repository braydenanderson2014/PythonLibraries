#!/usr/bin/env python3
"""Test chart intervals to verify different data ranges"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data_sources import create_default_provider

def test_intervals():
    """Test fetching candles for different intervals"""
    provider = create_default_provider()
    symbol = 'AAPL'
    
    intervals = ['1d', '5d', '1mo', '3mo', '6mo', '1y', '5y', 'max']
    
    print(f"Testing {symbol} with different intervals:\n")
    print("-" * 80)
    
    for interval in intervals:
        # Determine limit based on interval
        limit_map = {
            '1d': 1,           # 1 day = 1 candle
            '5d': 5,           # 5 days = 5 candles
            '1mo': 21,         # 1 month ≈ 21 trading days
            '3mo': 63,         # 3 months ≈ 63 trading days
            '6mo': 126,        # 6 months ≈ 126 trading days
            '1y': 252,         # 1 year ≈ 252 trading days
            '5y': 1260,        # 5 years ≈ 1260 trading days
            'max': 10000,      # All time = get all available
        }
        limit = limit_map.get(interval, 100)
        
        print(f"\nInterval: {interval:5s} (limit={limit:5d})")
        
        try:
            candles = provider.fetch_candles(symbol, interval=interval, limit=limit)
            
            if not candles:
                print(f"  ❌ No data returned")
            else:
                print(f"  ✓ Got {len(candles)} candles")
                
                # Show first and last dates
                if 'start' in candles[0]:
                    first_date = candles[0]['start']
                    last_date = candles[-1]['start']
                    print(f"  📅 Date range: {first_date} to {last_date}")
                    
                    # Show first and last prices
                    first_price = candles[0]['close']
                    last_price = candles[-1]['close']
                    change = last_price - first_price
                    change_pct = (change / first_price * 100) if first_price != 0 else 0
                    print(f"  💹 Price range: ${first_price:.2f} → ${last_price:.2f} (Change: {change:+.2f} / {change_pct:+.2f}%)")
                    
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    print("\n" + "-" * 80)
    print("\nTest Summary:")
    print("✓ All intervals should return different date ranges")
    print("✓ 1d should have 1 candle (today's close)")
    print("✓ 5d should have ~5 candles (last 5 trading days)")
    print("✓ 1y should have ~252 candles (last year's trading days)")
    print("✓ max should have the most candles (entire history)")
    print("✓ Price changes should be different for each interval")

if __name__ == '__main__':
    test_intervals()
