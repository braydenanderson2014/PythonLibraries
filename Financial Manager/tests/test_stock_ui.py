"""
Stock System Test

Demonstrates the stock management UI functionality.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QMessageBox
from ui.stock_manager_widget import StockManagerWidget
from src.watchlist import WatchlistManager
from src.portfolio import PortfolioManager


def setup_test_data():
    """Setup some test data for demonstration"""
    print("Setting up test data...")
    
    username = "test_user"
    
    # Setup watchlist
    watchlist = WatchlistManager()
    test_symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
    for symbol in test_symbols:
        watchlist.add_symbol(username, symbol)
    print(f"✓ Added {len(test_symbols)} symbols to watchlist")
    
    # Setup portfolio
    portfolio = PortfolioManager()
    test_trades = [
        ("AAPL", 10.0, 150.00),
        ("MSFT", 15.0, 300.00),
        ("GOOGL", 5.0, 2800.00),
    ]
    for symbol, qty, price in test_trades:
        portfolio.add_trade(username, symbol, qty, price)
    print(f"✓ Added {len(test_trades)} positions to portfolio")
    
    print("\nTest data ready!")
    return username


def main():
    """Run the stock system test"""
    print("=" * 60)
    print("Stock System Test")
    print("=" * 60)
    print()
    
    # Setup test data
    username = setup_test_data()
    
    # Create application
    app = QApplication(sys.argv)
    
    # Create and show stock manager widget
    print("\nLaunching Stock Manager UI...")
    widget = StockManagerWidget(username=username)
    widget.setWindowTitle("Stock Manager - Test")
    widget.setMinimumSize(1200, 700)
    widget.show()
    
    # Show welcome message
    QMessageBox.information(
        widget,
        "Stock Manager Test",
        "Welcome to the Stock Manager!\n\n"
        "Features:\n"
        "• Watchlist Tab - Track stock prices and changes\n"
        "• Portfolio Tab - Manage positions and view P&L\n"
        "• Auto-refresh - Set intervals for automatic updates\n"
        "• Add/Remove - Manage your stocks easily\n\n"
        "Test data has been loaded:\n"
        f"• Watchlist: {', '.join(['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA'])}\n"
        f"• Portfolio: AAPL, MSFT, GOOGL positions\n\n"
        "Click 'Refresh' to load current prices!\n"
        "(Note: Prices shown depend on your data provider)"
    )
    
    print("✓ UI launched successfully")
    print("\nInstructions:")
    print("  1. Click the '🔄 Refresh Now' button to load stock prices")
    print("  2. Try adding new symbols to the watchlist")
    print("  3. Add trades to the portfolio")
    print("  4. Enable auto-refresh to see updates")
    print("  5. Double-click a symbol for details")
    print()
    
    # Run application
    sys.exit(app.exec())


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
