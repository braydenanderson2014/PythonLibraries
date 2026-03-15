from src.stock_data import StockDataManager
from src.stock import Stock

mgr = StockDataManager()
print('Loaded stocks:', mgr.all())

s = Stock(symbol='AAPL', name='Apple Inc.', latest_price=174.12, volume=1200000)
mgr.add_or_update(s)
print('After add:', mgr.get('AAPL'))

mgr2 = StockDataManager()
print('Reloaded stocks:', mgr2.get('AAPL'))
