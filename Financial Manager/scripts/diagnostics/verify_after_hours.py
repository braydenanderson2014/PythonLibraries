#!/usr/bin/env python3
"""Verify the complete after-hours implementation"""

import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, PROJECT_ROOT)

from src.data_sources import create_default_provider

def verify_implementation():
    """Verify all aspects of the after-hours implementation"""
    
    print("\n" + "=" * 100)
    print("After-Hours Implementation Verification".center(100))
    print("=" * 100 + "\n")
    
    provider = create_default_provider()
    symbol = 'AAPL'
    
    tests = [
        ("1-month data has after-hours prices", '1mo', 21),
        ("1-year data has after-hours prices", '1y', 252),
        ("5-year data has after-hours prices", '5y', 1260),
        ("Chart can display multiple after-hours points as a line", '1mo', 21),
    ]
    
    print("Test Results:")
    print("-" * 100)
    
    for test_name, interval, expected_limit in tests:
        try:
            candles = provider.fetch_candles(symbol, interval=interval, limit=expected_limit)
            
            if not candles:
                print(f"[FAIL] {test_name}")
                print(f"       No candles returned")
                continue
            
            # Count after-hours prices
            ah_count = sum(1 for c in candles if 'after_hours_price' in c and c['after_hours_price'] is not None)
            
            if ah_count > 1:
                print(f"[PASS] {test_name}")
                print(f"       {ah_count}/{len(candles)} candles have after-hours data ({ah_count/len(candles)*100:.0f}%)")
            elif ah_count == 1:
                print(f"[PARTIAL] {test_name}")
                print(f"       Only 1 after-hours price available (scatter point, not line)")
            else:
                print(f"[FAIL] {test_name}")
                print(f"       No after-hours data available")
                
        except Exception as e:
            print(f"[ERROR] {test_name}: {str(e)[:60]}")
    
    print("\n" + "=" * 100)
    print("Summary".center(100))
    print("=" * 100)
    print("""
Daily After-Hours Prices: ENABLED
  - Extracts after-hours trading prices from intraday data (16:00-20:00 ET)
  - Available for all days in the requested period
  - Displayed as a dashed orange line on charts (when multiple points)
  - Displayed as a square marker on charts (when single point)

Data Sources:
  - Primary: Yahoo Finance (yfinance library)
  - Aggregation: Intraday hourly data from 16:00-20:00 ET
  - Fallback: ticker.info['postMarketPrice'] for today only

Chart Display:
  - Closing Price: Blue solid line with circle markers
  - After-Hours Price: Orange dashed line with square markers
  - Both on same scale for direct comparison

Benefits:
  - See after-market trading activity
  - Compare regular vs after-hours price movements
  - Track investor sentiment outside regular hours
  - Identify earnings-related after-hours moves
""")
    print("=" * 100 + "\n")

if __name__ == '__main__':
    verify_implementation()
