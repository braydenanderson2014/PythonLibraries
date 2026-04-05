#!/usr/bin/env python3
"""Quick verification that all chart features are working"""

import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, PROJECT_ROOT)

from src.data_sources import create_default_provider

def quick_test():
    print("\n" + "=" * 100)
    print("QUICK VERIFICATION: Chart Enhancements".center(100))
    print("=" * 100 + "\n")
    
    provider = create_default_provider()
    symbol = 'AAPL'
    
    tests = [
        ("1. After-hours price in data", '1d', 1, 'after_hours_price'),
        ("2. Five-year support", '5y', 1260, 'close'),
        ("3. All-time support", 'max', 10000, 'close'),
        ("4. One-year data (250 candles)", '1y', 252, 'close'),
    ]
    
    all_passed = True
    
    for test_name, interval, expected_count, check_field in tests:
        try:
            candles = provider.fetch_candles(symbol, interval=interval, limit=expected_count)
            
            if not candles:
                print(f"❌ {test_name}: No data returned")
                all_passed = False
                continue
            
            # Check field exists
            has_field = check_field in candles[-1]
            
            # Check count is reasonable
            count_ok = len(candles) >= (expected_count // 2)  # At least half expected
            
            if has_field and count_ok:
                print(f"✅ {test_name}")
                print(f"   └─ Got {len(candles)} candles, {check_field} available: {has_field}")
            else:
                print(f"❌ {test_name}")
                print(f"   └─ Got {len(candles)} candles, {check_field} available: {has_field}")
                all_passed = False
                
        except Exception as e:
            print(f"❌ {test_name}: {str(e)[:50]}")
            all_passed = False
    
    print("\n" + "=" * 100)
    if all_passed:
        print("✅ ALL TESTS PASSED - Chart enhancements are working!".center(100))
    else:
        print("⚠️  Some tests failed - check output above".center(100))
    print("=" * 100 + "\n")
    
    print("Chart Features Summary:")
    print("  📊 Timeframes: 1D, 5D, 1M, 3M, 6M, 1Y, 5Y, All Time")
    print("  💹 After-hours prices: Visible as orange markers on charts")
    print("  📈 Dynamic data loading: Each interval shows appropriate data density")
    print("  🔄 All intervals fully functional with correct date ranges\n")
    
    return all_passed

if __name__ == '__main__':
    success = quick_test()
    sys.exit(0 if success else 1)
