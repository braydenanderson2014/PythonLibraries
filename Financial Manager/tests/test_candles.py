#!/usr/bin/env python3
"""Test script to debug candle fetching"""

import sys
import os
import logging

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(name)s - %(levelname)s - %(message)s'
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data_sources import create_default_provider

# Test fetching candles
provider = create_default_provider()
print(f"Provider type: {type(provider).__name__}")
print(f"Provider: {provider}")

if hasattr(provider, '_providers'):
    print(f"Number of sub-providers: {len(provider._providers)}")
    for i, p in enumerate(provider._providers):
        print(f"  {i+1}. {p.name}")

print("\n--- Testing fetch_candles for KO ---")
candles = provider.fetch_candles('KO', interval='1d', limit=5)
print(f"Result: {len(candles)} candles")
if candles:
    for c in candles:
        print(f"  {c['start']}: Close=${c['close']:.2f}")
else:
    print("  No candles returned!")
