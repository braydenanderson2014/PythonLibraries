#!/usr/bin/env python3
"""Test real data providers with sample stocks."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data_sources import (
    create_default_provider, PolygonProvider, FinnhubProvider,
    TwelveDataProvider, AlphaVantageProvider
)

print("=" * 70)
print("Real Data Provider Test")
print("=" * 70)
print()

test_symbols = ['AAPL', 'MSFT', 'GOOGL']

# Check what providers are available
print("Available Providers:")
print("-" * 70)

available_providers = []

if os.getenv('POLYGON_API_KEY'):
    available_providers.append(('Polygon.io', PolygonProvider(os.getenv('POLYGON_API_KEY'))))
    print("✓ Polygon.io")

if os.getenv('FINNHUB_API_KEY'):
    available_providers.append(('Finnhub', FinnhubProvider(os.getenv('FINNHUB_API_KEY'))))
    print("✓ Finnhub")

if os.getenv('TWELVEDATA_API_KEY'):
    available_providers.append(('Twelve Data', TwelveDataProvider(os.getenv('TWELVEDATA_API_KEY'))))
    print("✓ Twelve Data")

if os.getenv('ALPHA_VANTAGE_API_KEY'):
    available_providers.append(('Alpha Vantage', AlphaVantageProvider(os.getenv('ALPHA_VANTAGE_API_KEY'))))
    print("✓ Alpha Vantage")

if not available_providers:
    print("✗ No providers configured - set API keys to enable real data")
    print()
    print("See REAL_DATA_SETUP.md for instructions")
    sys.exit(1)

print()
print("Testing Providers:")
print("-" * 70)

for provider_name, provider in available_providers:
    print()
    print(f"{provider_name}:")
    try:
        quotes = provider.fetch_quotes(test_symbols)
        if quotes:
            for symbol, data in quotes.items():
                price = data.get('latest_price', 'N/A')
                print(f"  {symbol}: ${price}")
        else:
            print(f"  No data returned")
    except Exception as e:
        print(f"  Error: {e}")

print()
print("=" * 70)
print("Testing Composite Provider (tries all providers):")
print("-" * 70)

try:
    provider = create_default_provider(include_mock=False)
    print(f"Using: {provider.name}")
    print()
    
    quotes = provider.fetch_quotes(test_symbols)
    if quotes:
        print("Quotes retrieved:")
        for symbol, data in quotes.items():
            price = data.get('latest_price', 'N/A')
            timestamp = data.get('timestamp', 'N/A')
            print(f"  {symbol}: ${price} (as of {timestamp})")
    else:
        print("No quotes returned")
except Exception as e:
    print(f"Error: {e}")

print("=" * 70)
