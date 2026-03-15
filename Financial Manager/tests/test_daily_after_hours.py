#!/usr/bin/env python3
"""Test daily after-hours price extraction"""

import sys
import os
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data_sources import create_default_provider

def test_daily_after_hours():
    """Test if we can extract daily after-hours prices"""
    provider = create_default_provider()
    symbol = 'AAPL'
    
    print("\n" + "=" * 100)
    print(f"Testing Daily After-Hours Prices for {symbol}".center(100))
    print("=" * 100 + "\n")
    
    # Test with a 1-month interval to see multiple days
    print("Fetching 1-month of price data...")
    candles = provider.fetch_candles(symbol, interval='1mo', limit=21)
    
    if not candles:
        print("[X] No candles returned")
        return
    
    df = pd.DataFrame(candles)
    print(f"[OK] Got {len(df)} daily candles\n")
    
    # Check for after-hours prices
    ah_count = df['after_hours_price'].notna().sum() if 'after_hours_price' in df.columns else 0
    
    print(f"After-Hours Price Statistics:")
    print(f"  Total candles: {len(df)}")
    print(f"  Candles with after-hours data: {ah_count}")
    print(f"  Coverage: {(ah_count/len(df)*100):.1f}%\n")
    
    if ah_count > 0:
        print("Sample data with after-hours prices:")
        print("-" * 100)
        
        ah_df = df[df['after_hours_price'].notna()][['start', 'close', 'after_hours_price']].copy()
        for idx, row in ah_df.iterrows():
            date = pd.to_datetime(row['start']).strftime('%Y-%m-%d')
            close = float(row['close'])
            ah = float(row['after_hours_price'])
            diff = ah - close
            pct = (diff / close * 100) if close != 0 else 0
            print(f"  {date}: Close ${close:.2f} -> After-Hours ${ah:.2f} ({diff:+.2f} / {pct:+.2f}%)")
        
        print("\n[SUCCESS] Daily after-hours prices are available!")
        print("   Chart will display as a line graph instead of just scatter points.\n")
    else:
        print("[INFO] No after-hours prices found")
        print("   This is expected if using AlphaVantage provider (which doesn't support after-hours)")
        print("   Make sure yfinance is installed for after-hours data.\n")
    
    print("=" * 100)

if __name__ == '__main__':
    test_daily_after_hours()
