#!/usr/bin/env python3
"""Investigate stock price data storage"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.stock_data import StockDataManager
import json

dm = StockDataManager()

print("Stock Data Analysis")
print("=" * 70)

# Check what's in the database
if os.path.exists(dm.db_path):
    with open(dm.db_path, 'r') as f:
        data = json.load(f)
        
    for symbol, stock_data in data.items():
        print(f"\n{symbol}:")
        print(f"  Meta: {stock_data.get('meta')}")
        
        history = stock_data.get('history', [])
        if history:
            latest = history[-1]
            print(f"  Latest Price: ${latest.get('price')}")
            print(f"  Market Cap: ${latest.get('market_cap')}")
            print(f"  Volume: {latest.get('volume')}")
            print(f"  Timestamp: {latest.get('timestamp')}")
else:
    print("No stock database found")
