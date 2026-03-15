#!/usr/bin/env python3
"""Test the chart rendering with after-hours line"""

import sys
import os
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data_sources import create_default_provider

def test_chart_rendering():
    """Test that the chart would render with after-hours as a line"""
    provider = create_default_provider()
    symbol = 'AAPL'
    
    print("\nFetching chart data...")
    candles = provider.fetch_candles(symbol, interval='1mo', limit=21)
    
    df = pd.DataFrame(candles)
    df['date'] = pd.to_datetime(df['start'])
    df = df.sort_values('date')
    
    # Simulate what the chart widget does
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Plot closing prices (blue line)
    ax.plot(df['date'], df['close'], 
           label='Closing Price', color='blue', linewidth=2, marker='o', markersize=4)
    
    # Plot after-hours prices as a line (orange dashed line)
    if 'after_hours_price' in df.columns and df['after_hours_price'].notna().any():
        after_hours_df = df[df['after_hours_price'].notna()].copy()
        
        if len(after_hours_df) > 1:
            ax.plot(after_hours_df['date'], after_hours_df['after_hours_price'],
                   label='After-Hours Price', color='orange', linewidth=2, 
                   marker='s', markersize=5, linestyle='--', alpha=0.7)
            print(f"[OK] Rendered {len(after_hours_df)} after-hours prices as a dashed line")
        else:
            ax.scatter(after_hours_df['date'], after_hours_df['after_hours_price'],
                      label='After-Hours Price', color='orange', s=150, marker='s', zorder=5)
            print(f"[OK] Rendered {len(after_hours_df)} after-hours price as a scatter point")
    
    ax.set_xlabel('Date', fontsize=11)
    ax.set_ylabel('Price ($)', fontsize=11)
    ax.set_title(f'{symbol} Price History - 1 Month (with Daily After-Hours)', fontsize=12, fontweight='bold')
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, alpha=0.3)
    
    fig.autofmt_xdate(rotation=45, ha='right')
    fig.tight_layout()
    
    # Save the test chart
    chart_path = 'test_chart_with_after_hours.png'
    plt.savefig(chart_path, dpi=100, bbox_inches='tight')
    print(f"[OK] Chart saved to {chart_path}")
    
    print("\nChart Features:")
    print("  - Blue line: Daily closing prices (solid line with circle markers)")
    print("  - Orange line: Daily after-hours prices (dashed line with square markers)")
    print("  - Grid: Light grid for reference")
    print("  - Both prices are displayed on the same scale for easy comparison")
    
    print("\n[SUCCESS] Chart rendering test completed!")

if __name__ == '__main__':
    test_chart_rendering()
