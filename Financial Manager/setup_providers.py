#!/usr/bin/env python3
"""Quick setup script to test real data providers."""

import os
import sys

print("=" * 70)
print("Stock Data Provider Configuration Helper")
print("=" * 70)
print()

providers = [
    ("POLYGON_API_KEY", "Polygon.io", "https://polygon.io/dashboard/signup"),
    ("FINNHUB_API_KEY", "Finnhub", "https://finnhub.io/api"),
    ("TWELVEDATA_API_KEY", "Twelve Data", "https://twelvedata.com/register"),
    ("ALPHA_VANTAGE_API_KEY", "Alpha Vantage", "https://www.alphavantage.co/api"),
]

print("Current Environment Variables:")
print("-" * 70)

configured = []
for env_var, name, url in providers:
    value = os.getenv(env_var)
    if value:
        print(f"✓ {name:20} ({env_var:25}) = {value[:20]}...")
        configured.append((name, env_var))
    else:
        print(f"✗ {name:20} ({env_var:25}) = NOT SET")

print()
print("=" * 70)

if not configured:
    print("WARNING: No data providers configured!")
    print()
    print("To enable real stock data, set at least one API key:")
    print()
    for env_var, name, url in providers:
        print(f"  {name}:")
        print(f"    Get key: {url}")
        print(f"    Set: export {env_var}='your_key_here'")
        print()
else:
    print(f"✓ {len(configured)} provider(s) configured:")
    for name, var in configured:
        print(f"  - {name} ({var})")
    print()
    print("The app will use these providers in this order:")
    print("  1. Polygon.io")
    print("  2. Finnhub")
    print("  3. Twelve Data")
    print("  4. Alpha Vantage")
    print()
    print("If one provider fails or is rate-limited, the app will")
    print("automatically try the next one.")

print("=" * 70)
