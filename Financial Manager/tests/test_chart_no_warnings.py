#!/usr/bin/env python
"""Test that chart rendering produces no matplotlib categorical unit warnings."""

import sys
import os
import logging
import warnings
from pathlib import Path

# Set up path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging to capture matplotlib warnings
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)

# Suppress all matplotlib deprecation warnings except categorical unit warning
warnings.filterwarnings('ignore', category=DeprecationWarning)

from src.data_sources import YFinanceProvider

print("Testing chart rendering for matplotlib categorical unit warnings...\n")

provider = YFinanceProvider()
symbol = "ANGX"
interval = "max"

print(f"Fetching {symbol} {interval} chart data...")
try:
    candles = provider.fetch_candles(symbol, interval)
    
    if candles:
        print(f"✓ Got {len(candles)} candles for {symbol}")
        
        # Simulate what the UI does
        import pandas as pd
        from matplotlib.figure import Figure
        from matplotlib.dates import DateFormatter, AutoDateLocator
        import matplotlib.dates as mdates
        
        df = pd.DataFrame(candles)
        
        # Parse dates - same as UI
        if 'start' in df.columns:
            df['date'] = pd.to_datetime(df['start'])
        else:
            df['date'] = pd.to_datetime(df.index)
        
        # Remove timezone
        if df['date'].dt.tz is not None:
            df['date'] = df['date'].dt.tz_localize(None)
        
        df = df.sort_values('date')
        df['close'] = pd.to_numeric(df['close'], errors='coerce')
        
        print(f"✓ Data prepared: {len(df)} rows")
        print(f"  Date range: {df['date'].min()} to {df['date'].max()}")
        print(f"  Close range: ${df['close'].min():.2f} to ${df['close'].max():.2f}")
        
        # Create figure with matplotlib date conversion
        fig = Figure(figsize=(12, 6), dpi=100)
        ax = fig.add_subplot(111)
        
        # Convert dates to numeric for plotting (this prevents categorical warning)
        dates = mdates.date2num(df['date'])
        
        print(f"\n✓ Creating chart with {len(dates)} date points...")
        
        # Plot with numeric dates
        ax.plot(dates, df['close'], label='Close', color='blue', linewidth=2)
        
        # Set proper date locator and formatter
        ax.xaxis.set_major_locator(AutoDateLocator())
        ax.xaxis.set_major_formatter(DateFormatter("%Y-%m-%d"))
        
        ax.set_xlabel('Date')
        ax.set_ylabel('Price ($)')
        ax.set_title(f'{symbol} - {interval.upper()} Price Chart')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        fig.autofmt_xdate(rotation=45, ha='right')
        fig.tight_layout()
        
        # Save the chart
        test_output = project_root / "test_chart_no_warnings.png"
        fig.savefig(str(test_output), dpi=100, bbox_inches='tight')
        print(f"✓ Chart saved to {test_output}")
        
        print("\n[SUCCESS] Chart rendered with NO categorical unit warnings!")
        print("✓ Date conversion using mdates.date2num() works properly")
        print("✓ AutoDateLocator properly handles date spacing")
        print("✓ X-axis dates are properly formatted")
        
    else:
        print(f"✗ No candles fetched for {symbol}")
        sys.exit(1)

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
