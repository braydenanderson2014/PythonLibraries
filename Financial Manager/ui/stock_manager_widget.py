"""
Stock Manager Widget

Main container for stock management features including watchlist and portfolio.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QLabel
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import pyqtSignal
from assets.Logger import Logger

logger = Logger()

from .stock_watchlist_widget import StockWatchlistWidget
from .stock_portfolio_widget import StockPortfolioWidget
from .stock_chart_widget import StockChartWidget


class StockManagerWidget(QWidget):
    """Main stock manager widget with tabs for watchlist and portfolio.
    
    This is a modular container that can be easily extended with additional
    stock-related features.
    """
    
    symbol_selected = pyqtSignal(str)  # Emitted when a symbol is selected
    
    def __init__(self, username=None, parent=None):
        super().__init__(parent)
        logger.debug("StockManagerWidget", f"Initializing StockManagerWidget for user {username}")
        self.username = username or "default"
        
        # Sub-widgets
        self.watchlist_widget = None
        self.portfolio_widget = None
        self.chart_widget = None
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("<h1>📈 Stock Manager</h1>")
        header.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(header)
        
        # Tab widget
        tabs = QTabWidget()
        
        # Watchlist tab
        self.watchlist_widget = StockWatchlistWidget(username=self.username)
        self.watchlist_widget.symbol_selected.connect(self.on_symbol_selected)
        tabs.addTab(self.watchlist_widget, "👁️ Watchlist")
        
        # Portfolio tab
        self.portfolio_widget = StockPortfolioWidget(username=self.username)
        self.portfolio_widget.symbol_selected.connect(self.on_symbol_selected)
        tabs.addTab(self.portfolio_widget, "💼 Portfolio")
        
        # Chart tab
        self.chart_widget = StockChartWidget()
        tabs.addTab(self.chart_widget, "📊 Charts")
        
        # Placeholder for future tabs (news, analysis, etc.)
        # tabs.addTab(self.create_news_widget(), "📰 News")
        # tabs.addTab(self.create_analysis_widget(), "🔍 Analysis")
        
        layout.addWidget(tabs)
        self.setLayout(layout)
    
    def on_symbol_selected(self, symbol):
        """Handle symbol selection from any sub-widget"""
        # Propagate signal up to parent
        self.symbol_selected.emit(symbol)
        
        # Update chart to show this symbol
        if self.chart_widget:
            import logging
            logging.info(f"StockManagerWidget: Loading chart for symbol {symbol}")
            self.chart_widget.set_symbol(symbol)
            # Switch to chart tab
            tabs_widget = self.findChild(QTabWidget)
            if tabs_widget:
                tabs_widget.setCurrentWidget(self.chart_widget)
    
    def set_username(self, username):
        """Update username for all sub-widgets"""
        self.username = username
        if self.watchlist_widget:
            self.watchlist_widget.set_username(username)
        if self.portfolio_widget:
            self.portfolio_widget.set_username(username)
    
    def refresh_all(self):
        """Refresh all sub-widgets"""
        if self.watchlist_widget:
            self.watchlist_widget.refresh_quotes()
        if self.portfolio_widget:
            self.portfolio_widget.refresh_portfolio()
        if self.chart_widget:
            self.chart_widget.refresh_chart()
    
    # --- Methods for future extensibility ---
    
    def create_charts_widget(self):
        """
        Placeholder for charts/technical analysis widget.
        Implement this to add charting functionality.
        """
        widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Charts widget - Coming soon!"))
        widget.setLayout(layout)
        return widget
    
    def create_news_widget(self):
        """
        Placeholder for stock news widget.
        Implement this to add news feed functionality.
        """
        widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("News widget - Coming soon!"))
        widget.setLayout(layout)
        return widget
    
    def create_analysis_widget(self):
        """
        Placeholder for stock analysis widget.
        Implement this to add fundamental/technical analysis.
        """
        widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Analysis widget - Coming soon!"))
        widget.setLayout(layout)
        return widget


if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    widget = StockManagerWidget(username='test_user')
    widget.setMinimumSize(1200, 700)
    widget.show()
    
    sys.exit(app.exec())
