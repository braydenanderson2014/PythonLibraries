"""Stock alerts system for price monitoring and notifications.

This module provides functionality for setting up price alerts on stock
symbols and notifying users when price conditions are met.
"""

from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from assets.Logger import Logger
logger = Logger()


class AlertCondition(Enum):
    """Types of price alert conditions."""
    ABOVE = "above"
    BELOW = "below"
    CHANGE_PERCENT = "change_percent"


@dataclass
class StockAlert:
    """Represents a price alert on a stock."""
    symbol: str
    condition: AlertCondition
    price_or_percent: float
    enabled: bool = True
    triggered: bool = False
    message: Optional[str] = None


class StockAlertManager:
    """Manages stock price alerts and notifications.
    
    This manager allows setting up alerts on stock prices and provides
    callbacks when alert conditions are met.
    """
    
    def __init__(self):
        """Initialize the alert manager."""
        logger.debug("StockAlertManager", "Initializing StockAlertManager")
        self._alerts: Dict[str, List[StockAlert]] = {}
        self._callbacks: List[Callable[[StockAlert], None]] = []
        logger.info("StockAlertManager", "StockAlertManager initialized successfully")
    
    def add_alert(self, symbol: str, condition: AlertCondition, value: float) -> StockAlert:
        """Add a new price alert.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            condition: AlertCondition for when to trigger
            value: Price or percentage threshold
            
        Returns:
            The created StockAlert object
        """
        logger.debug("StockAlertManager", f"Adding alert for {symbol}: {condition.value} {value}")
        alert = StockAlert(
            symbol=symbol.upper(),
            condition=condition,
            price_or_percent=value
        )
        
        if symbol.upper() not in self._alerts:
            self._alerts[symbol.upper()] = []
        
        self._alerts[symbol.upper()].append(alert)
        logger.info("StockAlertManager", f"Alert added for {symbol}: {condition.value} {value}")
        
        return alert
    
    def remove_alert(self, symbol: str, alert: StockAlert) -> bool:
        """Remove a specific alert.
        
        Args:
            symbol: Stock symbol
            alert: StockAlert object to remove
            
        Returns:
            True if alert was removed, False if not found
        """
        logger.debug("StockAlertManager", f"Removing alert for {symbol}: {alert.condition.value} {alert.price_or_percent}")
        symbol = symbol.upper()
        if symbol in self._alerts:
            try:
                self._alerts[symbol].remove(alert)
                logger.info("StockAlertManager", f"Alert removed for {symbol}")
                return True
            except ValueError:
                logger.warning("StockAlertManager", f"Alert not found in list for {symbol}")
                pass
        logger.debug("StockAlertManager", f"No alerts found for {symbol}")
        return False
    
    def get_alerts(self, symbol: str) -> List[StockAlert]:
        """Get all alerts for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            List of StockAlert objects for this symbol
        """
        alerts = self._alerts.get(symbol.upper(), [])
        logger.debug("StockAlertManager", f"Retrieved {len(alerts)} alerts for {symbol}")
        return alerts
    
    def register_callback(self, callback: Callable[[StockAlert], None]):
        """Register a callback to be called when an alert triggers.
        
        Args:
            callback: Function that takes a StockAlert and performs notification
        """
        self._callbacks.append(callback)
        logger.debug("StockAlertManager", f"Callback registered, total callbacks: {len(self._callbacks)}")
    
    def check_alerts(self, symbol: str, current_price: float) -> List[StockAlert]:
        """Check if any alerts should trigger for a symbol.
        
        Args:
            symbol: Stock symbol
            current_price: Current price of the stock
            
        Returns:
            List of alerts that were triggered
        """
        logger.debug("StockAlertManager", f"Checking alerts for {symbol} at price ${current_price}")
        triggered = []
        symbol = symbol.upper()
        
        for alert in self.get_alerts(symbol):
            if not alert.enabled or alert.triggered:
                logger.debug("StockAlertManager", f"Skipping disabled/triggered alert for {symbol}")
                continue
            
            should_trigger = False
            
            if alert.condition == AlertCondition.ABOVE:
                should_trigger = current_price > alert.price_or_percent
            elif alert.condition == AlertCondition.BELOW:
                should_trigger = current_price < alert.price_or_percent
            elif alert.condition == AlertCondition.CHANGE_PERCENT:
                # This would need the previous price to calculate percent change
                # For now, we'll skip this type
                pass
            
            if should_trigger:
                alert.triggered = True
                triggered.append(alert)
                logger.info("StockAlertManager", f"Alert triggered for {symbol}: {alert.condition.value} {alert.price_or_percent}")
                
                # Call all registered callbacks
                for callback in self._callbacks:
                    try:
                        callback(alert)
                    except Exception as e:
                        logger.error("StockAlertManager", f"Error in alert callback: {e}")
        
        logger.debug("StockAlertManager", f"Check complete: {len(triggered)} alerts triggered")
        return triggered
    
    def reset_alert(self, alert: StockAlert) -> bool:
        """Reset an alert's triggered status.
        
        Args:
            alert: StockAlert object to reset
            
        Returns:
            True if reset was successful
        """
        alert.triggered = False
        logger.debug("StockAlertManager", f"Alert reset for {alert.symbol}")
        return True
    
    def clear_alerts(self, symbol: Optional[str] = None):
        """Clear alerts for a symbol or all alerts.
        
        Args:
            symbol: Symbol to clear alerts for, or None to clear all
        """
        if symbol is None:
            alert_count = sum(len(alerts) for alerts in self._alerts.values())
            self._alerts.clear()
            logger.info("StockAlertManager", f"Cleared all {alert_count} alerts")
        else:
            symbol = symbol.upper()
            if symbol in self._alerts:
                alert_count = len(self._alerts[symbol])
                del self._alerts[symbol]
                logger.info("StockAlertManager", f"Cleared {alert_count} alerts for {symbol}")


# Global alert manager singleton
_global_alert_manager: Optional[StockAlertManager] = None


def get_stock_alert_manager() -> StockAlertManager:
    """Get or create the global stock alert manager.
    
    Returns:
        The global StockAlertManager instance
    """
    global _global_alert_manager
    if _global_alert_manager is None:
        logger.debug("StockAlerts", "Creating global StockAlertManager instance")
        _global_alert_manager = StockAlertManager()
        logger.info("StockAlerts", "Global StockAlertManager instance created")
    return _global_alert_manager


__all__ = ["StockAlertManager", "StockAlert", "AlertCondition", "get_stock_alert_manager"]
