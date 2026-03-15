"""
Stock Chart Widget

Displays stock price charts with closing price and after-hours data.
Includes horizontal and vertical scrolling capabilities.
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QScrollArea, QGridLayout, QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
except ImportError:
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, AutoDateLocator
import pandas as pd

from src.data_sources import create_default_provider
from ui.stock_data_manager import get_stock_data_manager
from assets.Logger import Logger

logger = Logger()


class StockChartWidget(QWidget):
    """Widget for displaying stock price charts with historical data"""
    
    def __init__(self, symbol=None, parent=None):
        super().__init__(parent)
        self.symbol = symbol
        self.data_manager = get_stock_data_manager()
        self.provider = create_default_provider()
        
        # Chart data
        self.chart_data = None
        self.current_interval = "1d"  # 1d, 5d, 1mo, 3mo, 6mo, 1y, 5y, max
        
        self.setup_ui()
        
        if symbol:
            self.load_chart(symbol)
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        
        self.title_label = QLabel("<h2>Stock Price Chart</h2>")
        self.title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # Interval selector
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Period:"))
        
        self.interval_combo = QComboBox()
        self.interval_combo.addItems(["1 Day", "5 Days", "1 Month", "3 Months", "6 Months", "1 Year", "5 Years", "All Time"])
        self.interval_combo.currentTextChanged.connect(self.on_interval_changed)
        interval_layout.addWidget(self.interval_combo)
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_chart)
        interval_layout.addWidget(refresh_btn)
        
        header_layout.addLayout(interval_layout)
        
        layout.addLayout(header_layout)
        
        # Create scroll area for the chart
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #cccccc;
                background-color: white;
            }
        """)
        
        # Create container for chart
        self.chart_container = QWidget()
        self.chart_layout = QVBoxLayout()
        self.chart_layout.setContentsMargins(10, 10, 10, 10)
        self.chart_container.setLayout(self.chart_layout)
        
        self.scroll_area.setWidget(self.chart_container)
        layout.addWidget(self.scroll_area)
        
        # Data info section
        info_group = QGroupBox("Price Information")
        info_layout = QGridLayout()
        
        self.current_price_label = QLabel("Current Price: —")
        self.closing_price_label = QLabel("Closing Price: —")
        self.after_hours_label = QLabel("After-Hours Price: —")
        self.change_label = QLabel("Change: —")
        self.last_updated_label = QLabel("Last Updated: —")
        
        info_layout.addWidget(self.current_price_label, 0, 0)
        info_layout.addWidget(self.closing_price_label, 0, 1)
        info_layout.addWidget(self.after_hours_label, 1, 0)
        info_layout.addWidget(self.change_label, 1, 1)
        info_layout.addWidget(self.last_updated_label, 2, 0)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        self.setLayout(layout)
    
    def load_chart(self, symbol):
        """Load chart for the given symbol"""
        self.symbol = symbol
        self.title_label.setText(f"<h2>{symbol} Price Chart</h2>")
        self.refresh_chart()
    
    def on_interval_changed(self, interval_text):
        """Handle interval selection change"""
        interval_map = {
            "1 Day": "1d",
            "5 Days": "5d",
            "1 Month": "1mo",
            "3 Months": "3mo",
            "6 Months": "6mo",
            "1 Year": "1y",
            "5 Years": "5y",
            "All Time": "max"
        }
        self.current_interval = interval_map.get(interval_text, "1d")
        self.refresh_chart()
    
    def get_interval_label(self):
        """Get human-readable label for the current interval"""
        labels = {
            '1d': '1 Day',
            '5d': '5 Days',
            '1mo': '1 Month',
            '3mo': '3 Months',
            '6mo': '6 Months',
            '1y': '1 Year',
            '5y': '5 Years',
            'max': 'All Time'
        }
        return labels.get(self.current_interval, self.current_interval.upper())
    
    def refresh_chart(self):
        """Refresh the chart with the latest data"""
        if not self.symbol:
            self.title_label.setText("<h2>No symbol selected</h2>")
            return
        
        try:
            # Determine limit based on interval to show appropriate data
            limit_map = {
                '1d': 1,           # 1 day = 1 candle
                '5d': 5,           # 5 days = 5 candles
                '1mo': 21,         # 1 month ≈ 21 trading days
                '3mo': 63,         # 3 months ≈ 63 trading days
                '6mo': 126,        # 6 months ≈ 126 trading days
                '1y': 252,         # 1 year ≈ 252 trading days
                '5y': 1260,        # 5 years ≈ 1260 trading days
                'max': 10000,      # All time = get all available
            }
            limit = limit_map.get(self.current_interval, 100)
            
            logger.info("StockChart", f"Fetching candles for {self.symbol} with interval {self.current_interval}, limit={limit}")
            # Fetch candle data from provider
            candles = self.provider.fetch_candles(
                self.symbol,
                interval=self.current_interval,
                limit=limit
            )
            
            logger.info("StockChart", f"Received {len(candles) if candles else 0} candles for {self.symbol}")
            
            if not candles:
                self.title_label.setText(f"<h2>{self.symbol} - No data available for {self.current_interval}</h2>")
                return
            
            # Store the chart data for use in price info display
            self.chart_data = candles
            
            # Create DataFrame
            df = pd.DataFrame(candles)
            
            # Parse dates - try 'start' first, then 'date', then 'timestamp'
            date_col = None
            if 'start' in df.columns:
                date_col = 'start'
            elif 'date' in df.columns:
                date_col = 'date'
            elif 'timestamp' in df.columns:
                date_col = 'timestamp'
            
            if date_col:
                # Parse with utc=True to handle mixed timezones, then convert to naive UTC
                df['date'] = pd.to_datetime(df[date_col], utc=True)
            else:
                # If no date column, use index
                df['date'] = pd.to_datetime(df.index, utc=True)
            
            # Convert to naive datetime (remove timezone info)
            df['date'] = df['date'].dt.tz_localize(None)
            
            # Sort by date
            df = df.sort_values('date')
            
            # Ensure close and other price columns are numeric
            df['close'] = pd.to_numeric(df['close'], errors='coerce')
            if 'after_hours_price' in df.columns:
                df['after_hours_price'] = pd.to_numeric(df['after_hours_price'], errors='coerce')
            
            # Check if we have data
            if df.empty or 'close' not in df.columns:
                self.title_label.setText(f"<h2>{self.symbol} - No price data available</h2>")
                logger.warning("StockChart", f"No price data for {self.symbol}. DataFrame columns: {df.columns.tolist()}")
                return
            
            # Clear previous chart
            while self.chart_layout.count():
                widget = self.chart_layout.takeAt(0)
                if widget.widget():
                    widget.widget().deleteLater()
            
            # Create figure
            fig = Figure(figsize=(12, 6), dpi=100)
            ax = fig.add_subplot(111)
            
            # Convert dates to matplotlib date format for proper plotting
            import matplotlib.dates as mdates
            dates = mdates.date2num(df['date'])
            
            # Plot closing prices using numeric dates
            ax.plot(dates, df['close'], 
                   label='Closing Price', color='blue', linewidth=2, marker='o', markersize=4)
            
            # Plot after-hours prices as a line if available
            if 'after_hours_price' in df.columns and df['after_hours_price'].notna().any():
                after_hours_df = df[df['after_hours_price'].notna()].copy()
                ah_dates = mdates.date2num(after_hours_df['date'])
                
                # If we have multiple after-hours prices, draw as a line
                if len(after_hours_df) > 1:
                    ax.plot(ah_dates, after_hours_df['after_hours_price'],
                           label='After-Hours Price', color='orange', linewidth=2, 
                           marker='s', markersize=5, linestyle='--', alpha=0.7)
                else:
                    # If only one point, show as scatter
                    ax.scatter(ah_dates, after_hours_df['after_hours_price'],
                              label='After-Hours Price', color='orange', s=150, marker='s', zorder=5)
            
            # Formatting
            ax.set_xlabel('Date', fontsize=11)
            ax.set_ylabel('Price ($)', fontsize=11)
            ax.set_title(f'{self.symbol} Price History - {self.get_interval_label()}', fontsize=12, fontweight='bold')
            ax.legend(loc='best', fontsize=10)
            ax.grid(True, alpha=0.3)
            
            # Format x-axis with proper date locator and formatter
            ax.xaxis.set_major_locator(AutoDateLocator())
            ax.xaxis.set_major_formatter(DateFormatter("%Y-%m-%d"))
            fig.autofmt_xdate(rotation=45, ha='right')
            
            fig.tight_layout()
            
            # Add canvas to scroll area
            canvas = FigureCanvas(fig)
            canvas.setMinimumHeight(400)
            self.chart_layout.addWidget(canvas)
            
            # Update info labels
            self.update_price_info()
            
        except Exception as e:
            logger.error("StockChart", f"Error refreshing chart for {self.symbol}: {e}")
            self.title_label.setText(f"<h2>{self.symbol} - Error loading data</h2>")
            QMessageBox.warning(self, "Chart Error", f"Failed to load chart: {str(e)}")
    
    def update_price_info(self):
        """Update the price information labels"""
        if not self.symbol:
            return
        
        try:
            stock_data = self.data_manager.get_stock_data(self.symbol)
            
            if not stock_data:
                return
            
            # Current price
            current = stock_data.price or 0
            self.current_price_label.setText(f"<b>Current Price:</b> ${current:.2f}")
            
            # Closing price
            closing = stock_data.closing_price or current
            self.closing_price_label.setText(f"<b>Closing Price:</b> ${closing:.2f}")
            
            # After-hours price - try to get from stock data first (most current)
            after_hours = stock_data.after_hours_price
            after_hours_date = None
            
            # If not available, try to get from the chart data that was just loaded
            if not after_hours and hasattr(self, 'chart_data') and self.chart_data:
                # Find the most recent after-hours price from chart data
                # This handles weekends by showing the last known AH price
                for candle in reversed(self.chart_data):
                    if 'after_hours_price' in candle and candle['after_hours_price'] is not None:
                        after_hours = candle['after_hours_price']
                        after_hours_date = candle.get('start', '')
                        break
            
            # Display after-hours price with date if it's from historical data
            if after_hours:
                if after_hours_date:
                    # Format date nicely
                    try:
                        date_obj = pd.to_datetime(after_hours_date)
                        date_str = date_obj.strftime('%m/%d/%Y')
                        self.after_hours_label.setText(f"<b>After-Hours Price:</b> ${after_hours:.2f} (as of {date_str})")
                    except:
                        self.after_hours_label.setText(f"<b>After-Hours Price:</b> ${after_hours:.2f}")
                else:
                    self.after_hours_label.setText(f"<b>After-Hours Price:</b> ${after_hours:.2f}")
            else:
                self.after_hours_label.setText("<b>After-Hours Price:</b> —")
            
            # Change
            prev_close = stock_data.previous_close or closing
            change = current - prev_close
            change_pct = (change / prev_close * 100) if prev_close != 0 else 0
            
            color = "green" if change >= 0 else "red"
            sign = "+" if change >= 0 else ""
            self.change_label.setText(
                f"<b><span style='color: {color};'>Change: {sign}${change:.2f} ({sign}{change_pct:.2f}%)</span></b>"
            )
            
            # Last updated
            if stock_data.last_updated:
                time_str = stock_data.last_updated.strftime("%Y-%m-%d %H:%M:%S")
                self.last_updated_label.setText(f"<b>Last Updated:</b> {time_str}")
            
        except Exception as e:
            logger.error("StockChart", f"Error updating price info: {e}")
    
    def set_symbol(self, symbol):
        """Set the symbol and load its chart"""
        logger.info("StockChart", f"StockChartWidget.set_symbol({symbol})")
        self.load_chart(symbol)


if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    widget = StockChartWidget(symbol='AAPL')
    widget.setMinimumSize(1000, 700)
    widget.show()
    
    sys.exit(app.exec())
