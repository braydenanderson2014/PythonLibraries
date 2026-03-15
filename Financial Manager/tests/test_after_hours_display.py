#!/usr/bin/env python3
"""Test that after-hours prices display with dates in the chart info"""

import sys
import os
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data_sources import create_default_provider

def test_after_hours_display():
    """Test the after-hours price display logic"""
    
    print("\n" + "=" * 100)
    print("Testing After-Hours Price Info Display".center(100))
    print("=" * 100 + "\n")
    
    provider = create_default_provider()
    symbol = 'AAPL'
    
    # Fetch different intervals
    test_cases = [
        ('1d', 1, 'Today only'),
        ('1mo', 21, 'Past month'),
        ('1y', 252, 'Past year'),
    ]
    
    for interval, limit, description in test_cases:
        print(f"\nTest Case: {interval.upper()} - {description}")
        print("-" * 100)
        
        candles = provider.fetch_candles(symbol, interval=interval, limit=limit)
        
        if not candles:
            print(f"  [ERROR] No data returned")
            continue
        
        # Find most recent after-hours price (simulating update_price_info logic)
        after_hours = None
        after_hours_date = None
        
        for candle in reversed(candles):
            if 'after_hours_price' in candle and candle['after_hours_price'] is not None:
                after_hours = candle['after_hours_price']
                after_hours_date = candle.get('start', '')
                break
        
        if after_hours:
            if after_hours_date:
                try:
                    date_obj = pd.to_datetime(after_hours_date)
                    date_str = date_obj.strftime('%m/%d/%Y')
                    day_name = date_obj.strftime('%A')
                    
                    # Check if it's a weekend
                    is_weekend = date_obj.weekday() >= 5
                    weekend_note = " (Last trading day - market closed on weekend)" if is_weekend else ""
                    
                    print(f"  After-Hours Price: ${after_hours:.2f}")
                    print(f"  Date: {date_str} ({day_name}){weekend_note}")
                    print(f"  Display: <b>After-Hours Price:</b> ${after_hours:.2f} (as of {date_str})")
                except:
                    print(f"  After-Hours Price: ${after_hours:.2f}")
            else:
                print(f"  After-Hours Price: ${after_hours:.2f}")
        else:
            print(f"  After-Hours Price: — (Not available)")
    
    print("\n" + "=" * 100)
    print("Summary".center(100))
    print("=" * 100)
    print("""
Price Info Display Logic:
1. Attempts to get after-hours price from stock data (real-time)
2. If not available, gets most recent from chart data
3. Displays with date if from historical data (handles weekends)
4. Shows last known trading day's after-hours price

Weekend Handling:
- Markets are closed on weekends
- If fetching on Monday, shows Friday's after-hours price
- If fetching on weekend, shows Friday's price (last trading day)
- Date shown indicates when the after-hours trading occurred

Display Format Examples:
- Today: "After-Hours Price: $273.10"
- Historical: "After-Hours Price: $273.10 (as of 12/19/2025)"
- Last Trading Day: "After-Hours Price: $271.53 (as of 12/19/2025)"
""")
    print("=" * 100 + "\n")

if __name__ == '__main__':
    test_after_hours_display()
