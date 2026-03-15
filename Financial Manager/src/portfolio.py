from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Callable
import json, os
from assets.Logger import Logger
logger = Logger()
try:
    from .stock_data import StockDataManager
    from .app_paths import PORTFOLIO_DB
except ImportError:
    from stock_data import StockDataManager
    from app_paths import PORTFOLIO_DB


@dataclass
class PortfolioPosition:
    symbol: str
    quantity: float
    avg_cost: float  # average cost per share

    def market_value(self, price: float | None) -> float:
        if price is None:
            return 0.0
        return self.quantity * price

    def unrealized_pl(self, price: float | None) -> float:
        if price is None:
            return 0.0
        return (price - self.avg_cost) * self.quantity


class PortfolioManager:
    """Manages per-user portfolios (username keyed)."""

    def __init__(self, db_path: str | None = None, stock_data: StockDataManager | None = None):
        self.db_path = db_path or PORTFOLIO_DB
        self.stock_data = stock_data or StockDataManager()
        self._data: Dict[str, Dict[str, PortfolioPosition]] = {}
        logger.debug("PortfolioManager", f"Initialized with db_path={self.db_path}")
        self.load()

    # --- Persistence -------------------------------------------------------
    def load(self):
        if os.path.exists(self.db_path):
            try:
                raw = json.load(open(self.db_path, 'r', encoding='utf-8'))
                self._data = {
                    user: {sym: PortfolioPosition(**pos) for sym, pos in positions.items()}
                    for user, positions in raw.items()
                }
                total_positions = sum(len(positions) for positions in self._data.values())
                logger.info("PortfolioManager", f"Loaded {len(self._data)} users with {total_positions} total positions from {self.db_path}")
            except Exception as e:
                logger.error("PortfolioManager", f"Error loading portfolio database: {str(e)}")
                self._data = {}
        else:
            logger.debug("PortfolioManager", f"Portfolio database not found at {self.db_path}, starting with empty data")
            self._data = {}

    def save(self):
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            payload = {
                user: {sym: asdict(pos) for sym, pos in positions.items()}
                for user, positions in self._data.items()
            }
            json.dump(payload, open(self.db_path, 'w', encoding='utf-8'), indent=2)
            total_positions = sum(len(positions) for positions in self._data.values())
            logger.debug("PortfolioManager", f"Saved {len(self._data)} users with {total_positions} total positions to {self.db_path}")
        except Exception as e:
            logger.error("PortfolioManager", f"Error saving portfolio database: {str(e)}")

    # --- CRUD --------------------------------------------------------------
    def add_trade(self, username: str, symbol: str, quantity: float, price: float):
        symbol = symbol.upper()
        logger.debug("PortfolioManager", f"Adding trade for {username}: {quantity} shares of {symbol} at ${price:.2f}")
        user_positions = self._data.setdefault(username, {})
        pos = user_positions.get(symbol)
        if pos is None:
            user_positions[symbol] = PortfolioPosition(symbol=symbol, quantity=quantity, avg_cost=price)
            logger.info("PortfolioManager", f"Created new position for {username}: {symbol} ({quantity} shares, avg_cost=${price:.2f})")
        else:
            # Recalculate average cost (weighted)
            total_shares = pos.quantity + quantity
            if total_shares <= 0:
                # Treat as position closed if zero or negative
                if total_shares == 0:
                    del user_positions[symbol]
                    logger.info("PortfolioManager", f"Closed position for {username}: {symbol}")
                else:
                    pos.quantity = total_shares  # allow negative (short) with same avg cost for now
                    logger.info("PortfolioManager", f"Updated position for {username}: {symbol} (short {abs(total_shares)} shares)")
            else:
                old_avg = pos.avg_cost
                pos.avg_cost = (pos.avg_cost * pos.quantity + price * quantity) / total_shares
                pos.quantity = total_shares
                logger.info("PortfolioManager", f"Updated position for {username}: {symbol} ({total_shares} shares, avg_cost=${old_avg:.2f} -> ${pos.avg_cost:.2f})")
        self.save()

    def remove_position(self, username: str, symbol: str) -> bool:
        symbol = symbol.upper()
        logger.debug("PortfolioManager", f"Removing position for {username}: {symbol}")
        user_positions = self._data.get(username)
        if not user_positions or symbol not in user_positions:
            logger.warning("PortfolioManager", f"Position not found for {username}: {symbol}")
            return False
        del user_positions[symbol]
        self.save()
        logger.info("PortfolioManager", f"Removed position for {username}: {symbol}")
        return True

    def get_positions(self, username: str) -> List[PortfolioPosition]:
        positions = list(self._data.get(username, {}).values())
        logger.debug("PortfolioManager", f"Retrieved {len(positions)} positions for {username}")
        return positions

    # --- Analytics ---------------------------------------------------------
    def portfolio_value(self, username: str) -> float:
        try:
            total = 0.0
            for pos in self.get_positions(username):
                stock = self.stock_data.get(pos.symbol)
                price = stock.latest_price if stock else None
                total += pos.market_value(price)
            total = round(total, 2)
            logger.debug("PortfolioManager", f"Calculated portfolio value for {username}: ${total:.2f}")
            return total
        except Exception as e:
            logger.error("PortfolioManager", f"Error calculating portfolio value for {username}: {str(e)}")
            return 0.0

    def unrealized_pl(self, username: str) -> float:
        try:
            pl = 0.0
            for pos in self.get_positions(username):
                stock = self.stock_data.get(pos.symbol)
                price = stock.latest_price if stock else None
                pl += pos.unrealized_pl(price)
            pl = round(pl, 2)
            logger.debug("PortfolioManager", f"Calculated unrealized P&L for {username}: ${pl:.2f}")
            return pl
        except Exception as e:
            logger.error("PortfolioManager", f"Error calculating unrealized P&L for {username}: {str(e)}")
            return 0.0

__all__ = ["PortfolioManager", "PortfolioPosition"]
