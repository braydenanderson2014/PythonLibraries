"""Stock Data Manager wrapper for UI access.

This module provides UI-friendly access to the stock data management
system and coordinates between the UI and the data layer.
"""

import sys
import os
import logging
from typing import Optional, List

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from src.stock_data import StockDataManager as CoreStockDataManager
    from src.stock_data import StockView, Candle, StockMeta
except ImportError:
    from stock_data import StockDataManager as CoreStockDataManager
    from stock_data import StockView, Candle, StockMeta

logger = logging.getLogger(__name__)

# Global instance of stock data manager
_global_stock_data_manager: Optional[CoreStockDataManager] = None


def get_stock_data_manager() -> CoreStockDataManager:
    """Get or create the global stock data manager.
    
    This provides a singleton pattern for accessing the shared stock data
    manager across the UI components.
    
    Returns:
        The global StockDataManager instance
    """
    global _global_stock_data_manager
    if _global_stock_data_manager is None:
        try:
            _global_stock_data_manager = CoreStockDataManager()
            logger.info("Initialized global stock data manager")
        except Exception as e:
            logger.error(f"Failed to initialize stock data manager: {e}")
            raise
    return _global_stock_data_manager


def reset_stock_data_manager():
    """Reset the global stock data manager.
    
    Useful for testing or when you need a fresh instance.
    """
    global _global_stock_data_manager
    _global_stock_data_manager = None


__all__ = [
    "get_stock_data_manager",
    "reset_stock_data_manager",
    "StockView",
    "Candle",
    "StockMeta",
]
