#!/usr/bin/env python3
"""Test market value calculation"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.portfolio import PortfolioPosition

# Test case: 10 shares at $50 average cost, now trading at $75
position = PortfolioPosition(symbol='TEST', quantity=10.0, avg_cost=50.0)

print("Market Value Calculation Test")
print("=" * 50)
print(f"Symbol: {position.symbol}")
print(f"Quantity: {position.quantity}")
print(f"Average Cost: ${position.avg_cost:.2f}")
print()

current_price = 75.0
print(f"Current Price: ${current_price:.2f}")
print()

market_value = position.market_value(current_price)
print(f"Expected Market Value: {position.quantity} × ${current_price:.2f} = ${position.quantity * current_price:.2f}")
print(f"Actual Market Value from method: ${market_value:.2f}")
print()

if market_value == position.quantity * current_price:
    print("✓ Market value calculation is CORRECT")
else:
    print("✗ Market value calculation is WRONG")
    print(f"  Expected: {position.quantity * current_price}")
    print(f"  Got: {market_value}")

# Test unrealized P&L
unrealized_pl = position.unrealized_pl(current_price)
print()
print(f"Unrealized P&L: (${current_price:.2f} - ${position.avg_cost:.2f}) × {position.quantity} = ${unrealized_pl:.2f}")
