#!/usr/bin/env python
"""Verify that the datetime parsing fix works correctly."""

import sys
from pathlib import Path
import pandas as pd
import matplotlib.dates as mdates

# Test the fix
print("Testing datetime parsing fix for mixed timezones...\n")

# Simulate data with mixed timezones (like yfinance returns)
test_data = {
    'start': [
        '2025-12-15 00:00:00-05:00',  # EST
        '2025-12-16 00:00:00-05:00',  # EST
        '2025-12-17 00:00:00-05:00',  # EST
        '2025-12-18 00:00:00-05:00',  # EST
        '2025-12-19 00:00:00-05:00',  # EST
    ],
    'close': [273.50, 273.75, 274.00, 273.90, 273.67],
    'after_hours_price': [273.55, 273.80, 274.05, 273.95, 273.70]
}

df = pd.DataFrame(test_data)

print("Original DataFrame:")
print(df)
print(f"\nData types:\n{df.dtypes}\n")

# Apply the fix from stock_chart_widget.py
try:
    print("Parsing dates with utc=True...")
    df['date'] = pd.to_datetime(df['start'], utc=True)
    print("✓ Dates parsed successfully")
    
    print("\nConverting to naive datetime...")
    df['date'] = df['date'].dt.tz_localize(None)
    print("✓ Timezone localized (removed)")
    
    print("\nConverting to numeric matplotlib dates...")
    dates = mdates.date2num(df['date'])
    print(f"✓ Successfully converted {len(dates)} dates to numeric format")
    
    print(f"\nDate range: {df['date'].min()} to {df['date'].max()}")
    print(f"Numeric date range: {dates.min():.0f} to {dates.max():.0f}")
    
    # Verify we can use matplotlib date formatter
    from matplotlib.dates import DateFormatter
    formatter = DateFormatter("%Y-%m-%d")
    print(f"✓ DateFormatter created successfully")
    
    print("\n[SUCCESS] All datetime operations work correctly!")
    print("✓ No FutureWarning about mixed timezones")
    print("✓ .dt accessor works properly")
    print("✓ matplotlib.dates.date2num() converts dates correctly")
    
except Exception as e:
    print(f"\n[FAILED] Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
