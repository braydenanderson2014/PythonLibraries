# Stock System - Implementation Guide

## Overview

The Stock System has been fully integrated into the Financial Manager with a modular, extensible architecture. The system provides:

- **Watchlist Management** - Track multiple stocks with real-time quotes
- **Portfolio Management** - Manage positions with P&L tracking
- **Modular Design** - Easy to extend with new features
- **Auto-refresh** - Configurable automatic quote updates
- **User Isolation** - Per-user watchlists and portfolios

## Architecture

### Component Structure

```
ui/
├── stock_manager_widget.py       # Main container
├── stock_watchlist_widget.py     # Watchlist UI
└── stock_portfolio_widget.py     # Portfolio UI

src/
├── watchlist.py                  # Watchlist data manager
├── portfolio.py                  # Portfolio data manager
├── stock_manager.py              # Quote refresh coordinator
├── stock_data.py                 # Historical data storage
└── stock_api.py                  # API client for quotes
```

### Design Principles

1. **Modularity** - Each widget is independent and reusable
2. **Extensibility** - Easy to add new tabs/features
3. **Separation of Concerns** - UI separate from business logic
4. **User-Centric** - All data is per-user
5. **Signal-Driven** - Widgets communicate via Qt signals

## Features

### 1. Stock Watchlist Widget

**Location**: `ui/stock_watchlist_widget.py`

**Features**:
- Add/remove stocks from watchlist
- View real-time price quotes
- Price change indicators (color-coded)
- Volume and market cap display
- Auto-refresh with configurable intervals
- Context menu for quick actions
- Double-click to view details

**Key Components**:
```python
class StockWatchlistWidget(QWidget):
    symbol_selected = pyqtSignal(str)
    
    def add_symbol(self, symbol)
    def remove_symbol(self, symbol)
    def refresh_quotes(self)
    def set_username(self, username)
```

**Table Columns**:
1. Symbol
2. Company Name
3. Current Price
4. Price Change ($)
5. Price Change (%)
6. Volume
7. Market Cap
8. Previous Close
9. Last Update
10. Actions (Remove button)

### 2. Stock Portfolio Widget

**Location**: `ui/stock_portfolio_widget.py`

**Features**:
- Add buy/sell trades
- Track positions with average cost
- Real-time market values
- Unrealized P&L calculation
- Total portfolio summary
- Quick buy/sell actions
- Close position management
- Context menu for operations

**Key Components**:
```python
class StockPortfolioWidget(QWidget):
    symbol_selected = pyqtSignal(str)
    
    def add_trade(self, trade_data)
    def close_position(self, symbol)
    def refresh_portfolio(self)
    def set_username(self, username)
```

**Table Columns**:
1. Symbol
2. Company Name
3. Quantity (shares)
4. Average Cost
5. Current Price
6. Market Value
7. Total Cost
8. Unrealized P&L ($)
9. P&L (%)
10. Last Update
11. Actions (Buy/Sell/Close)

**Summary Metrics**:
- Total Portfolio Value
- Total Cost Basis
- Total P&L ($ and %)

### 3. Stock Manager Widget

**Location**: `ui/stock_manager_widget.py`

**Features**:
- Tab-based container
- Watchlist tab
- Portfolio tab
- Extensible for new tabs
- Unified symbol selection
- Username propagation
- Bulk refresh

**Key Components**:
```python
class StockManagerWidget(QWidget):
    symbol_selected = pyqtSignal(str)
    
    def set_username(self, username)
    def refresh_all(self)
    
    # Extension methods (placeholders):
    def create_charts_widget(self)
    def create_news_widget(self)
    def create_analysis_widget(self)
```

## Integration with Financial Manager

### Added to Main UI

The stock system is integrated as a new tab in the Financial Manager:

**File**: `ui/financial_tracker.py`

**Changes**:
1. Import added: `from ui.stock_manager_widget import StockManagerWidget`
2. New tab: "📈 Stocks" (between Net Worth and Banking API)
3. Method: `create_stock_manager_tab()`
4. Signal handler: `on_stock_symbol_selected(symbol)`

**Tab Order**:
1. Overview
2. Transactions
3. Recurring
4. Loans
5. Budgets
6. Goals
7. Net Worth
8. **📈 Stocks** ← NEW
9. Banking API
10. Bank Dashboards
11. Settings

## Data Model

### Watchlist

**File**: `src/watchlist.py`

**Schema**:
```json
{
  "username": ["AAPL", "MSFT", "GOOGL"]
}
```

**Methods**:
- `add_symbol(username, symbol)` - Add to watchlist
- `remove_symbol(username, symbol)` - Remove from watchlist
- `list_symbols(username)` - Get user's watchlist

### Portfolio

**File**: `src/portfolio.py`

**Schema**:
```json
{
  "username": {
    "AAPL": {
      "symbol": "AAPL",
      "quantity": 10.5,
      "avg_cost": 150.00
    }
  }
}
```

**Classes**:
```python
@dataclass
class PortfolioPosition:
    symbol: str
    quantity: float
    avg_cost: float
    
    def market_value(self, price) -> float
    def unrealized_pl(self, price) -> float
```

**Methods**:
- `add_trade(username, symbol, quantity, price)` - Add buy/sell
- `remove_position(username, symbol)` - Close position
- `get_positions(username)` - Get user's positions
- `portfolio_value(username)` - Total portfolio value

## Auto-Refresh System

Both widgets support auto-refresh at configurable intervals:

**Intervals**:
- Manual (off)
- 30 seconds
- 1 minute
- 5 minutes
- 15 minutes

**Implementation**:
```python
self.refresh_timer = QTimer()
self.refresh_timer.timeout.connect(self.refresh_quotes)
self.refresh_timer.start(interval_ms)
```

## Extension Points

### Adding New Tabs

The `StockManagerWidget` has placeholder methods for adding new functionality:

**1. Charts Widget**
```python
def create_charts_widget(self):
    # Implement technical analysis charts
    # - Candlestick charts
    # - Technical indicators (RSI, MACD, etc.)
    # - Drawing tools
    pass
```

**2. News Widget**
```python
def create_news_widget(self):
    # Implement stock news feed
    # - Company news
    # - Market updates
    # - Sentiment analysis
    pass
```

**3. Analysis Widget**
```python
def create_analysis_widget(self):
    # Implement fundamental analysis
    # - Financial ratios
    # - Earnings data
    # - Analyst ratings
    pass
```

**4. Screener Widget**
```python
def create_screener_widget(self):
    # Implement stock screener
    # - Filter by criteria
    # - Custom filters
    # - Saved screens
    pass
```

**5. Alerts Widget**
```python
def create_alerts_widget(self):
    # Implement price alerts
    # - Price targets
    # - Percentage moves
    # - Volume alerts
    pass
```

### Adding to Existing Widgets

**Watchlist Enhancements**:
- Import from CSV
- Export watchlist
- Multiple watchlists
- Sorting/filtering
- Custom columns
- Charting integration

**Portfolio Enhancements**:
- Transaction history
- Realized P&L tracking
- Dividend tracking
- Cost basis methods (FIFO, LIFO, etc.)
- Performance charts
- Tax reporting

## Usage Guide

### Basic Workflow

**1. Adding to Watchlist**:
```
Stocks Tab → Watchlist → ➕ Add Symbol → Enter "AAPL" → Add
```

**2. Refreshing Quotes**:
```
Stocks Tab → Watchlist → 🔄 Refresh Now
```

**3. Adding a Trade**:
```
Stocks Tab → Portfolio → ➕ Add Trade →
  Buy/Sell → AAPL → 10 shares @ $150 → Add
```

**4. Viewing P&L**:
```
Stocks Tab → Portfolio → 🔄 Refresh
(Portfolio summary shows total P&L)
```

**5. Enabling Auto-Refresh**:
```
Stocks Tab → Auto-refresh dropdown → Select "1 min"
```

### Advanced Features

**Context Menu Actions**:
- Right-click on any symbol
- View Details
- Refresh single symbol
- Quick buy/sell
- Remove/Close position

**Double-Click**:
- Double-click any symbol
- Triggers `symbol_selected` signal
- Can be used for detail views

**Keyboard Shortcuts** (Future):
- `Ctrl+R` - Refresh
- `Ctrl+A` - Add symbol/trade
- `Delete` - Remove selected
- `F5` - Force refresh all

## Testing

### Run Test Script

```bash
cd "Python Projects/Financial Manager"
python test_stock_ui.py
```

**Test Data Created**:
- Watchlist: AAPL, MSFT, GOOGL, AMZN, TSLA
- Portfolio: AAPL (10 @ $150), MSFT (15 @ $300), GOOGL (5 @ $2800)

### Manual Testing

1. **Launch Financial Manager**:
   ```bash
   python main.py
   ```

2. **Navigate to Stocks Tab**

3. **Test Watchlist**:
   - Add symbols
   - Refresh quotes
   - Remove symbols
   - Enable auto-refresh

4. **Test Portfolio**:
   - Add buy trade
   - Add sell trade
   - View P&L
   - Close position

## Configuration

### Stock Data Provider

The system uses the provider configured in `src/stock_manager.py`:

**Default**: Mock provider (for testing)

**Production**: Configure in `src/data_sources.py`

Options:
- Alpha Vantage
- Yahoo Finance
- IEX Cloud
- Polygon.io
- Finnhub

### Data Storage

**Watchlist**: `resources/watchlists.json`
**Portfolio**: `resources/portfolios.json`
**Stock Data**: `resources/stocks.json`

## Performance Considerations

### Optimization Tips

1. **Batch Refreshes**:
   - Refresh multiple symbols together
   - Reduces API calls

2. **Caching**:
   - Stock data cached in `StockDataManager`
   - Reduces redundant fetches

3. **Async Updates**:
   - Use `QTimer` for non-blocking refreshes
   - UI remains responsive

4. **Selective Updates**:
   - Only refresh visible tabs
   - Pause when tab not active

## Future Enhancements

### Planned Features

- [ ] **Historical Charts** - Price/volume charts with technical indicators
- [ ] **Stock News** - Real-time news feed integration
- [ ] **Fundamental Data** - Financial statements, ratios
- [ ] **Options Trading** - Options chains and analysis
- [ ] **Alerts System** - Price/volume alerts
- [ ] **Stock Screener** - Filter stocks by criteria
- [ ] **Backtesting** - Test trading strategies
- [ ] **Export/Import** - CSV import/export
- [ ] **Mobile Sync** - Sync with mobile app
- [ ] **Social Features** - Share watchlists/portfolios

### API Integrations

- [ ] Real-time quotes (WebSocket)
- [ ] News APIs (NewsAPI, Benzinga)
- [ ] Fundamental data (Financial Modeling Prep)
- [ ] Options data (CBOE, TradierBrokerage)
- [ ] Broker integration (Alpaca, TD Ameritrade)

## Troubleshooting

### Common Issues

**Q: Quotes not refreshing?**
- Check internet connection
- Verify API provider configuration
- Check API rate limits

**Q: Symbols not found?**
- Ensure correct ticker symbol
- Check if symbol exists on exchange
- Verify API provider supports symbol

**Q: Portfolio P&L incorrect?**
- Verify trades entered correctly
- Check current prices are updating
- Ensure no duplicate positions

**Q: Auto-refresh not working?**
- Check interval is not "Manual"
- Verify timer is running
- Check console for errors

## Support

For issues or questions:
1. Check this documentation
2. Review test script output
3. Check application logs
4. File an issue with details

---

**Status**: ✅ Fully Implemented and Integrated

The stock system is now ready to use with watchlist and portfolio management. The modular architecture makes it easy to add new features like charts, news, and analysis tools.
