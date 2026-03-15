#!/usr/bin/env python3
"""Test script to verify company name fetching from data providers."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data_sources import create_default_provider, MockProvider
from src.stock_data import StockDataManager

def test_ticker_details():
    """Test fetching ticker details"""
    provider = MockProvider()
    
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'META']
    
    print("Testing ticker details fetching:")
    print("-" * 60)
    
    for symbol in symbols:
        details = provider.fetch_ticker_details(symbol)
        if details:
            print(f"{symbol:8} -> {details.get('name'):30} ({details.get('exchange', 'N/A')})")
        else:
            print(f"{symbol:8} -> No details found")
    
    print()
    print("Testing with composite provider (includes mock as fallback):")
    print("-" * 60)
    
    composite = create_default_provider(include_mock=True)
    
    for symbol in symbols:
        details = composite.fetch_ticker_details(symbol)
        if details:
            print(f"{symbol:8} -> {details.get('name'):30} ({details.get('exchange', 'N/A')})")
        else:
            print(f"{symbol:8} -> No details found")
    
    print()
    print("Testing StockDataManager metadata storage:")
    print("-" * 60)
    
    dm = StockDataManager()
    
    for symbol in symbols:
        details = composite.fetch_ticker_details(symbol)
        if details:
            dm.upsert_meta(symbol, name=details['name'], exchange=details.get('exchange'))
        
        # Retrieve and check
        meta = dm._meta.get(symbol)
        if meta:
            print(f"{symbol:8} -> name={meta.name}, exchange={meta.exchange}")
        else:
            print(f"{symbol:8} -> No metadata stored")

if __name__ == '__main__':
    test_ticker_details()
