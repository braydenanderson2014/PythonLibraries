from src.stock_manager import StockManager
from src.portfolio import PortfolioManager
from src.watchlist import WatchlistManager
from src.stock_data import StockDataManager

# Setup managers
stock_data = StockDataManager()
stock_manager = StockManager(data_manager=stock_data)
portfolio = PortfolioManager(stock_data=stock_data)
watchlists = WatchlistManager()

# Seed some symbols
for sym in ["AAPL","MSFT","TSLA"]:
    stock_manager.refresh([sym])

# Watchlist operations
user = 'admin'
watchlists.add_symbol(user, 'AAPL')
watchlists.add_symbol(user, 'MSFT')
print('Watchlist:', watchlists.list_symbols(user))

# Portfolio trades
portfolio.add_trade(user, 'AAPL', 10, 150.00)
portfolio.add_trade(user, 'AAPL', 5, 155.00)
portfolio.add_trade(user, 'MSFT', 2, 300.00)

print('Positions:')
for p in portfolio.get_positions(user):
    print(' ', p.symbol, p.quantity, p.avg_cost)

print('Portfolio value:', portfolio.portfolio_value(user))
print('Unrealized P/L:', portfolio.unrealized_pl(user))
