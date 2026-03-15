#!/usr/bin/env python3
"""Test chart rendering with after-hours prices"""

import sys
import os
import pandas as pd

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data_sources import create_default_provider

def test_chart_data():
    """Test fetching and displaying chart data with after-hours prices"""
    provider = create_default_provider()
    symbol = 'AAPL'
    
    test_intervals = [
        ('1d', 1, '1 Day (Current)'),
        ('1y', 252, '1 Year (252 trading days)'),
        ('5y', 1260, '5 Years (1260 trading days)'),
        ('max', 10000, 'All Time')
    ]
    
    print("=" * 100)
    print(f"Chart Data Test for {symbol}")
    print("=" * 100)
    
    for interval, limit, label in test_intervals:
        print(f"\n{label}:")
        print("-" * 100)
        
        try:
            candles = provider.fetch_candles(symbol, interval=interval, limit=limit)
            
            if not candles:
                print(f"  ❌ No candles returned")
                continue
            
            df = pd.DataFrame(candles)
            
            # Parse dates
            if 'start' in df.columns:
                df['date'] = pd.to_datetime(df['start'])
            
            df = df.sort_values('date')
            
            print(f"  ✓ Got {len(df)} candles")
            
            # Display info
            first_date = df['date'].min()
            last_date = df['date'].max()
            first_close = df['close'].iloc[0]
            last_close = df['close'].iloc[-1]
            min_price = df['close'].min()
            max_price = df['close'].max()
            
            print(f"  📅 Date range: {first_date.date()} to {last_date.date()} ({len(df)} days)")
            print(f"  💹 Price range: ${min_price:.2f} - ${max_price:.2f}")
            print(f"  📊 Opening: ${first_close:.2f}, Closing: ${last_close:.2f}")
            
            # Check for after-hours prices
            after_hours_count = df['after_hours_price'].notna().sum()
            if after_hours_count > 0:
                print(f"  🌙 After-hours prices: {after_hours_count} available")
                latest_ah = df[df['after_hours_price'].notna()]['after_hours_price'].iloc[-1] if after_hours_count > 0 else None
                latest_close = df[df['after_hours_price'].notna()]['close'].iloc[-1] if after_hours_count > 0 else None
                if latest_ah and latest_close:
                    ah_diff = latest_ah - latest_close
                    ah_pct = (ah_diff / latest_close * 100)
                    sign = "+" if ah_diff >= 0 else ""
                    print(f"    Latest: Close ${latest_close:.2f} → After-Hours ${latest_ah:.2f} ({sign}{ah_diff:.2f} / {sign}{ah_pct:.2f}%)")
            else:
                print(f"  🌙 After-hours prices: Not available for this interval")
            
            # Show a sample row
            print(f"\n  Sample candle (most recent):")
            last_row = df.iloc[-1]
            print(f"    Date: {last_row['date'].date()}")
            print(f"    Open: ${last_row['open']:.2f}, High: ${last_row['high']:.2f}, Low: ${last_row['low']:.2f}, Close: ${last_row['close']:.2f}")
            if pd.notna(last_row.get('after_hours_price')):
                print(f"    After-Hours: ${last_row['after_hours_price']:.2f}")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 100)
    print("Summary:")
    print("✓ 1 day and 1 year should have different data and price ranges")
    print("✓ 5 years should show broader historical trends")
    print("✓ All Time should show maximum available history")
    print("✓ After-hours prices should be available for recent data points")
    print("=" * 100)

if __name__ == '__main__':
    test_chart_data()
