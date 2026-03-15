"""
Stock Watchlist Widget

Provides UI for managing and viewing stock watchlists.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
    QFormLayout, QLineEdit, QMessageBox, QGroupBox, QMenu,
    QComboBox, QSpinBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QBrush, QIcon, QAction
from datetime import datetime
import logging
import sys
import os

# Add parent directory to path to access src module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.watchlist import WatchlistManager
from src.stock_manager import StockManager, get_refresh_manager
from src.stock_data import StockDataManager
from src.data_sources import create_default_provider
from ui.stock_data_manager import get_stock_data_manager
from assets.Logger import Logger

logger = Logger()

class AddSymbolDialog(QDialog):
    """Dialog for adding a stock symbol to watchlist"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Stock to Watchlist")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        self.symbol_input = None
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Info label
        info = QLabel("Enter a stock symbol to add to your watchlist.")
        layout.addWidget(info)
        
        # Form
        form_layout = QFormLayout()
        
        self.symbol_input = QLineEdit()
        self.symbol_input.setPlaceholderText("e.g., AAPL, MSFT, GOOGL")
        self.symbol_input.textChanged.connect(lambda text: self.symbol_input.setText(text.upper()))
        form_layout.addRow("Symbol:", self.symbol_input)
        
        layout.addLayout(form_layout)
        
        # Examples
        examples = QLabel("Popular symbols: AAPL, MSFT, GOOGL, AMZN, TSLA, META, NVDA")
        examples.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(examples)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        add_button = QPushButton("Add to Watchlist")
        add_button.clicked.connect(self.accept)
        add_button.setDefault(True)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(add_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def get_symbol(self):
        """Get the entered symbol"""
        return self.symbol_input.text().strip().upper()


class StockWatchlistWidget(QWidget):
    """Main widget for stock watchlist management"""
    
    symbol_selected = pyqtSignal(str)  # Emitted when a symbol is selected
    
    def __init__(self, username=None, parent=None):
        super().__init__(parent)
        self.username = username or "default"
        
        # Managers
        self.watchlist_manager = WatchlistManager()
        self.data_manager = get_stock_data_manager()  # Use global StockDataManager
        self.provider = create_default_provider()
        
        # Listen to stock updates from data manager
        self.data_manager.on_stock_updated(self._on_stock_data_updated)
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._trigger_data_manager_refresh)
        
        self.setup_ui()
        self.load_watchlist()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("<h2>Stock Watchlist</h2>")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Auto-refresh controls
        self.auto_refresh_checkbox = QComboBox()
        self.auto_refresh_checkbox.addItems(["Manual", "30 sec", "1 min", "5 min", "15 min"])
        self.auto_refresh_checkbox.currentTextChanged.connect(self.on_refresh_interval_changed)
        header_layout.addWidget(QLabel("Auto-refresh:"))
        header_layout.addWidget(self.auto_refresh_checkbox)
        
        # Refresh button
        self.refresh_btn = QPushButton("🔄 Refresh Now")
        self.refresh_btn.clicked.connect(self.refresh_quotes)
        header_layout.addWidget(self.refresh_btn)
        
        # Add symbol button
        add_btn = QPushButton("➕ Add Symbol")
        add_btn.clicked.connect(self.show_add_dialog)
        header_layout.addWidget(add_btn)
        
        layout.addLayout(header_layout)
        
        # Watchlist table
        watchlist_group = QGroupBox("Your Watchlist")
        watchlist_layout = QVBoxLayout()
        
        self.watchlist_table = QTableWidget()
        self.watchlist_table.setColumnCount(12)
        self.watchlist_table.setHorizontalHeaderLabels([
            "Symbol", "Name", "Price", "Closing", "After-Hours", "Change", "Change %", 
            "Volume", "Market Cap", "Prev Close", "Last Update", "Actions"
        ])
        self.watchlist_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.watchlist_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.watchlist_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.watchlist_table.customContextMenuRequested.connect(self.show_context_menu)
        self.watchlist_table.cellDoubleClicked.connect(self.on_symbol_double_clicked)
        
        watchlist_layout.addWidget(self.watchlist_table)
        watchlist_group.setLayout(watchlist_layout)
        layout.addWidget(watchlist_group)
        
        # Status bar
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: gray; padding: 5px;")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
    
    def load_watchlist(self):
        """Load and display watchlist symbols"""
        symbols = self.watchlist_manager.list_symbols(self.username)
        
        self.watchlist_table.setRowCount(len(symbols))
        
        for row, symbol in enumerate(symbols):
            # Add stock to data manager's watch list
            stock_data = self.data_manager.get_stock_data(symbol)
            if not stock_data:
                self.data_manager.add_stock(symbol)
            
            # Symbol
            symbol_item = QTableWidgetItem(symbol)
            symbol_item.setFlags(symbol_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.watchlist_table.setItem(row, 0, symbol_item)
            
            # Populate from cache if available
            self._update_row_from_cache(row, symbol)
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(4, 2, 4, 2)
            
            alerts_btn = QPushButton("🔔 Alerts")
            alerts_btn.setMaximumWidth(80)
            alerts_btn.clicked.connect(lambda checked, s=symbol: self.show_alerts_dialog(s))
            actions_layout.addWidget(alerts_btn)
            
            remove_btn = QPushButton("Remove")
            remove_btn.setMaximumWidth(80)
            remove_btn.clicked.connect(lambda checked, s=symbol: self.remove_symbol(s))
            actions_layout.addWidget(remove_btn)
            
            actions_widget.setLayout(actions_layout)
            self.watchlist_table.setCellWidget(row, 11, actions_widget)
        
        self.status_label.setText(f"Loaded {len(symbols)} symbols")
    
    def _update_row_from_cache(self, row: int, symbol: str):
        """Update a table row with cached stock data."""
        stock_data = self.data_manager.get_stock_data(symbol)
        if not stock_data:
            return
        
        # Name
        name = stock_data.company_name or "—"
        self.watchlist_table.setItem(row, 1, QTableWidgetItem(name))
        
        if stock_data.price:
            # Price
            price_item = QTableWidgetItem(f"${stock_data.price:.2f}")
            self.watchlist_table.setItem(row, 2, price_item)
            
            # Closing Price
            closing_price = stock_data.closing_price if hasattr(stock_data, 'closing_price') else None
            if closing_price:
                closing_item = QTableWidgetItem(f"${closing_price:.2f}")
                self.watchlist_table.setItem(row, 3, closing_item)
            else:
                self.watchlist_table.setItem(row, 3, QTableWidgetItem("—"))
            
            # After-Hours Price
            after_hours = stock_data.after_hours_price if hasattr(stock_data, 'after_hours_price') else None
            if after_hours:
                after_hours_item = QTableWidgetItem(f"${after_hours:.2f}")
                self.watchlist_table.setItem(row, 4, after_hours_item)
            else:
                self.watchlist_table.setItem(row, 4, QTableWidgetItem("—"))
            
            # Change
            if stock_data.change is not None:
                change_item = QTableWidgetItem(f"${stock_data.change:.2f}")
                self.watchlist_table.setItem(row, 5, change_item)
            
            # Change %
            if stock_data.change_percent is not None:
                change_pct = stock_data.change_percent
                pct_item = QTableWidgetItem(f"{change_pct:.2f}%")
                # Color red or green based on positive/negative
                if change_pct < 0:
                    pct_item.setForeground(QBrush(QColor("red")))
                else:
                    pct_item.setForeground(QBrush(QColor("green")))
                self.watchlist_table.setItem(row, 6, pct_item)
            
            # Last update
            if stock_data.last_updated:
                time_str = stock_data.last_updated.strftime("%H:%M:%S")
                self.watchlist_table.setItem(row, 10, QTableWidgetItem(time_str))
        else:
            # Placeholder for empty columns
            for col in range(1, 11):
                item = QTableWidgetItem("—")
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.watchlist_table.setItem(row, col, item)
    
    def show_add_dialog(self):
        """Show dialog to add a new symbol"""
        dialog = AddSymbolDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            symbol = dialog.get_symbol()
            if symbol:
                self.add_symbol(symbol)
    
    def add_symbol(self, symbol):
        """Add a symbol to the watchlist"""
        symbol = symbol.upper()
        
        # Check if already exists
        existing = self.watchlist_manager.list_symbols(self.username)
        if symbol in existing:
            QMessageBox.information(self, "Already Added", f"{symbol} is already in your watchlist.")
            return
        
        # Add to data manager (background refresh will fetch its data)
        self.data_manager.add_stock(symbol)
        
        # Add to watchlist
        self.watchlist_manager.add_symbol(self.username, symbol)
        
        # Reload table
        self.load_watchlist()
        
        self.status_label.setText(f"Added {symbol} to watchlist")
    
    def remove_symbol(self, symbol):
        """Remove a symbol from the watchlist"""
        reply = QMessageBox.question(
            self,
            "Confirm Removal",
            f"Remove {symbol} from watchlist?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.watchlist_manager.remove_symbol(self.username, symbol)
            self.load_watchlist()
            self.status_label.setText(f"Removed {symbol} from watchlist")
    
    def show_alerts_dialog(self, symbol: str):
        """Show the price alerts dialog for a stock"""
        try:
            from .stock_alert_dialog import StockAlertDialog
            
            dialog = StockAlertDialog(ticker=symbol, parent=self)
            dialog.alerts_changed.connect(self.on_alerts_changed)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open alerts dialog: {e}")
    
    def on_alerts_changed(self):
        """Handle alerts being changed - could update UI to show alert status"""
        pass  # Alerts are checked automatically in the background
    
    def refresh_quotes(self):
        """Trigger a refresh of stock quotes from the provider."""
        symbols = self.watchlist_manager.list_symbols(self.username)
        if not symbols:
            self.status_label.setText("No symbols in watchlist")
            return
        
        try:
            # Fetch fresh quotes from the provider
            quotes = self.provider.fetch_quotes(symbols)
            
            # Ingest the quotes into the data manager
            for symbol, quote_data in quotes.items():
                self.data_manager.ingest_quote(quote_data)
            
            # Update the UI
            self.load_watchlist()
            self.status_label.setText(f"Refreshed {len(quotes)} quotes successfully")
        except Exception as e:
            self.status_label.setText(f"Refresh failed: {str(e)}")
            import logging
            logging.error(f"Stock refresh error: {e}")
    
    def _trigger_data_manager_refresh(self):
        """Called by auto-refresh timer to trigger a refresh cycle."""
        self.refresh_quotes()
    
    def _on_stock_data_updated(self, ticker: str, stock_data):
        """Called when stock data is updated in the manager."""
        # Find row for this ticker and update it
        symbols = self.watchlist_manager.list_symbols(self.username)
        if ticker in symbols:
            row = symbols.index(ticker)
            self._update_row_from_cache(row, ticker)

    
    def on_refresh_interval_changed(self, interval_text):
        """Handle auto-refresh interval change"""
        self.refresh_timer.stop()
        
        if interval_text == "Manual":
            self.status_label.setText("Auto-refresh disabled")
            return
        
        # Parse interval
        interval_map = {
            "30 sec": 30_000,
            "1 min": 60_000,
            "5 min": 300_000,
            "15 min": 900_000
        }
        
        interval_ms = interval_map.get(interval_text, 60_000)
        self.refresh_timer.start(interval_ms)
        self.status_label.setText(f"Auto-refresh enabled: {interval_text}")
    
    def show_context_menu(self, position):
        """Show context menu for watchlist actions"""
        menu = QMenu(self)
        
        # Get selected row
        row = self.watchlist_table.rowAt(position.y())
        if row < 0:
            return
        
        symbol_item = self.watchlist_table.item(row, 0)
        if not symbol_item:
            return
        
        symbol = symbol_item.text()
        
        # Add actions
        view_action = QAction(f"View {symbol} Details", self)
        view_action.triggered.connect(lambda: self.view_symbol_details(symbol))
        menu.addAction(view_action)
        
        refresh_action = QAction(f"Refresh {symbol}", self)
        refresh_action.triggered.connect(lambda: self.stock_manager.refresh([symbol]))
        menu.addAction(refresh_action)
        
        menu.addSeparator()
        
        remove_action = QAction(f"Remove {symbol}", self)
        remove_action.triggered.connect(lambda: self.remove_symbol(symbol))
        menu.addAction(remove_action)
        
        menu.exec(self.watchlist_table.viewport().mapToGlobal(position))
    
    def on_symbol_double_clicked(self, row, col):
        """Handle double-click on symbol"""
        symbol_item = self.watchlist_table.item(row, 0)
        if symbol_item:
            symbol = symbol_item.text()
            self.symbol_selected.emit(symbol)
    
    def view_symbol_details(self, symbol):
        """View detailed information for a symbol"""
        # Emit signal for parent to handle
        self.symbol_selected.emit(symbol)
    
    def set_username(self, username):
        """Change the current username"""
        self.username = username
        self.load_watchlist()


if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    widget = StockWatchlistWidget(username='test_user')
    widget.setMinimumSize(1000, 600)
    widget.show()
    
    sys.exit(app.exec())
