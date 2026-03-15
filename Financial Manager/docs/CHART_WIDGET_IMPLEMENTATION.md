# Stock Chart Widget Implementation

## Overview
Added a comprehensive stock chart widget to the Financial Manager application with support for displaying closing prices, after-hours prices, and historical data with full scrolling capabilities.

## New Files Created

### [ui/stock_chart_widget.py](ui/stock_chart_widget.py)
A complete PyQt6 widget for visualizing stock price data with the following features:

**Features:**
- **Price Chart Visualization**: Displays historical price data using matplotlib
  - Closing price line chart with markers
  - After-hours price scatter plot overlay
  - Multiple time period options (1 day, 5 days, 1 month, 3 months, 6 months, 1 year)

- **Scrolling Capabilities**:
  - Vertical scrolling using QScrollArea for chart content
  - Horizontal scrolling for extended date ranges
  - Full mouse wheel and scroll bar support

- **Price Information Display**:
  - Current price
  - Closing price
  - After-hours price
  - Price change ($ and %)
  - Last updated timestamp
  - Color-coded gains (green) and losses (red)

- **Interactive Controls**:
  - Period selector dropdown (1d, 5d, 1mo, 3mo, 6mo, 1y)
  - Refresh button to update chart data
  - Status labels for price information

**Key Methods:**
- `load_chart(symbol)`: Load and display chart for a specific stock symbol
- `refresh_chart()`: Refresh chart with latest data from provider
- `on_interval_changed()`: Handle time period changes
- `update_price_info()`: Update price information labels
- `set_symbol(symbol)`: Set the symbol for the chart

## Files Modified

### [ui/stock_manager_widget.py](ui/stock_manager_widget.py)
**Changes:**
1. Added import for `StockChartWidget`
2. Added `self.chart_widget` to initialization
3. Created chart tab with `StockChartWidget()`
4. Enhanced `on_symbol_selected()` to:
   - Automatically load selected symbol in chart widget
   - Switch to chart tab when symbol is selected
5. Updated `refresh_all()` to refresh chart widget

**Result:** Stock symbols can now be selected from watchlist/portfolio and automatically display in the chart tab with full price history.

## Technical Details

### Data Sources
- Uses `QuoteProvider.fetch_candles()` for historical OHLC data
- Integrates with `StockDataManager` for real-time price information
- Displays closing price and after-hours price when available

### Visualization
- Matplotlib backend: Qt5Agg or QTAgg (auto-detected)
- Responsive figure sizing (12x6 inches, 100 DPI)
- Automatic date formatting and axis rotation
- Grid overlay for readability
- Legend showing price types

### UI Layout
```
┌─────────────────────────────────────┐
│ Stock Price Chart | Period: [1 Day] │
├─────────────────────────────────────┤
│                                     │
│  ┌─────────────────────────────┐   │
│  │                             │   │
│  │    Matplotlib Chart         │ ↔ │  Horizontal Scroll
│  │   (Closing + After-Hours)   │   │
│  │                             │   │
│  └─────────────────────────────┘   │
│           ↕ Vertical Scroll        │
├─────────────────────────────────────┤
│ Current Price: $100.00              │
│ Closing Price: $99.50  After-Hours: │
│ Change: +$0.50 (+0.50%)             │
│ Last Updated: 2025-12-20 16:30:00   │
└─────────────────────────────────────┘
```

## Usage

### From Watchlist/Portfolio
1. Click on any stock symbol in the watchlist or portfolio
2. Application automatically switches to the "📊 Charts" tab
3. Chart displays historical data with closing and after-hours prices
4. Use period selector to change time range (1d to 1y)
5. Click "Refresh" to update with latest data
6. Scroll horizontally to see more dates
7. Scroll vertically to see full chart

### Standalone
```python
from ui.stock_chart_widget import StockChartWidget

widget = StockChartWidget(symbol='AAPL')
widget.show()
```

## Integration Points

1. **Symbol Selection Flow**:
   - User clicks symbol in watchlist → `symbol_selected` signal
   - `StockManagerWidget.on_symbol_selected()` → calls `chart_widget.set_symbol()`
   - Chart automatically loads and displays

2. **Data Flow**:
   - `fetch_candles()` from provider → DataFrame
   - Real-time prices from `StockDataManager`
   - Combined display of historical + current data

3. **Refresh Mechanism**:
   - Manual refresh button in chart
   - Auto-refresh via `StockManagerWidget.refresh_all()`
   - Updates both price data and chart visualization

## Future Enhancements

- Volume chart (second subplot)
- Technical indicators (SMA, EMA, RSI, MACD)
- Range selection zoom
- Export chart as image
- Price annotations for significant events
- Multiple symbol comparison
- Candlestick chart option
