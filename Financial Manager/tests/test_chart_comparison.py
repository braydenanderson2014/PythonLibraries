#!/usr/bin/env python3
"""Comparison of chart data for different timeframes"""

import sys
import os
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data_sources import create_default_provider

def test_comparison():
    """Show clear differences between chart timeframes"""
    provider = create_default_provider()
    symbol = 'AAPL'
    
    print("\n" + "=" * 120)
    print(f"CHART COMPARISON: How {symbol} data differs by timeframe".center(120))
    print("=" * 120 + "\n")
    
    test_cases = [
        ('1d', 1),
        ('1y', 252),
        ('5y', 1260),
    ]
    
    results = []
    for interval, limit in test_cases:
        try:
            candles = provider.fetch_candles(symbol, interval=interval, limit=limit)
            if candles:
                df = pd.DataFrame(candles)
                df['date'] = pd.to_datetime(df['start'])
                df = df.sort_values('date')
                
                first_price = df['close'].iloc[0]
                last_price = df['close'].iloc[-1]
                change = last_price - first_price
                change_pct = (change / first_price * 100) if first_price != 0 else 0
                
                results.append({
                    'Interval': interval.upper(),
                    'Candles': len(df),
                    'Date Range': f"{df['date'].min().date()} to {df['date'].max().date()}",
                    'Span': f"{(df['date'].max() - df['date'].min()).days} days",
                    'Start Price': f"${first_price:.2f}",
                    'End Price': f"${last_price:.2f}",
                    'Change': f"${change:+.2f}",
                    'Change %': f"{change_pct:+.2f}%",
                    'High': f"${df['close'].max():.2f}",
                    'Low': f"${df['close'].min():.2f}",
                })
        except Exception as e:
            print(f"Error for {interval}: {e}")
    
    # Print comparison table
    if results:
        print(f"{'Interval':<12} {'Candles':<10} {'Date Span':<10} {'Start Price':<12} {'End Price':<12} {'Change':<15} {'High':<12} {'Low':<12}")
        print("-" * 120)
        
        for r in results:
            print(f"{r['Interval']:<12} {str(r['Candles']):<10} {r['Span']:<10} {r['Start Price']:<12} {r['End Price']:<12} {r['Change %']:<15} {r['High']:<12} {r['Low']:<12}")
    
    print("\n" + "=" * 120)
    print("KEY OBSERVATIONS:")
    print("=" * 120)
    print("""
✓ 1D Chart:
  - Shows TODAY ONLY (1 candle)
  - Price range is TIGHT (high/low for single day)
  - Useful for: Intraday trading, current session analysis
  
✓ 1Y Chart:
  - Shows LAST 252 TRADING DAYS (yearly trend)
  - Price range shows ANNUAL movement
  - Useful for: Yearly performance, trend analysis
  
✓ 5Y Chart:
  - Shows LAST ~1,256 TRADING DAYS (5-year trend)
  - Price range shows LONG-TERM movement
  - Useful for: Long-term investment decisions, growth analysis

⭐ After-Hours Price:
  - Available for TODAY's data (most recent point)
  - Shows as orange marker on chart
  - Indicates trading activity after market close (4:00 PM - 8:00 PM ET)
""")
    print("=" * 120 + "\n")

if __name__ == '__main__':
    test_comparison()
