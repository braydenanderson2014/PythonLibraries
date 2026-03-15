"""
Stock Portfolio Widget

Provides UI for managing and viewing stock portfolios with positions and P&L.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
    QFormLayout, QLineEdit, QMessageBox, QGroupBox, QMenu,
    QDoubleSpinBox, QComboBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QBrush, QFont, QAction
from datetime import datetime
from assets.Logger import Logger
import sys
import os

# Add parent directory to path to access src module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.portfolio import PortfolioManager, PortfolioPosition
from src.stock_manager import StockManager, get_refresh_manager
from src.stock_data import StockDataManager
from src.data_sources import create_default_provider
from ui.stock_data_manager import get_stock_data_manager


logger = Logger()


class AddTradeDialog(QDialog):
    """Dialog for adding a trade (buy/sell) to portfolio"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Trade")
        self.setModal(True)
        self.setMinimumWidth(450)
        
        self.symbol_input = None
        self.quantity_input = None
        self.price_input = None
        self.trade_type_combo = None
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Info label
        info = QLabel("Enter trade details to add to your portfolio.")
        layout.addWidget(info)
        
        # Form
        form_layout = QFormLayout()
        
        # Trade type
        self.trade_type_combo = QComboBox()
        self.trade_type_combo.addItems(["Buy", "Sell"])
        form_layout.addRow("Trade Type:", self.trade_type_combo)
        
        # Symbol
        self.symbol_input = QLineEdit()
        self.symbol_input.setPlaceholderText("e.g., AAPL")
        self.symbol_input.textChanged.connect(lambda text: self.symbol_input.setText(text.upper()))
        form_layout.addRow("Symbol:", self.symbol_input)
        
        # Quantity
        self.quantity_input = QDoubleSpinBox()
        self.quantity_input.setRange(0.001, 1_000_000)
        self.quantity_input.setDecimals(3)
        self.quantity_input.setValue(1.0)
        self.quantity_input.setSuffix(" shares")
        form_layout.addRow("Quantity:", self.quantity_input)
        
        # Price
        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0.01, 1_000_000)
        self.price_input.setDecimals(2)
        self.price_input.setValue(100.0)
        self.price_input.setPrefix("$")
        form_layout.addRow("Price per Share:", self.price_input)
        
        layout.addLayout(form_layout)
        
        # Total
        self.total_label = QLabel()
        self.update_total()
        self.quantity_input.valueChanged.connect(self.update_total)
        self.price_input.valueChanged.connect(self.update_total)
        layout.addWidget(self.total_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        add_button = QPushButton("Add Trade")
        add_button.clicked.connect(self.accept)
        add_button.setDefault(True)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(add_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def update_total(self):
        """Update the total trade value"""
        quantity = self.quantity_input.value()
        price = self.price_input.value()
        total = quantity * price
        self.total_label.setText(f"<b>Total Value: ${total:,.2f}</b>")
    
    def get_trade_data(self):
        """Get the trade data from the dialog"""
        is_buy = self.trade_type_combo.currentText() == "Buy"
        quantity = self.quantity_input.value()
        
        return {
            'symbol': self.symbol_input.text().strip().upper(),
            'quantity': quantity if is_buy else -quantity,  # Negative for sells
            'price': self.price_input.value()
        }


class StockPortfolioWidget(QWidget):
    """Main widget for stock portfolio management"""
    
    symbol_selected = pyqtSignal(str)  # Emitted when a symbol is selected
    
    def __init__(self, username=None, parent=None):
        super().__init__(parent)
        self.username = username or "default"
        
        # Managers
        self.data_manager = get_stock_data_manager()  # Use global StockDataManager
        self.portfolio_manager = PortfolioManager(stock_data=self.data_manager)
        self.provider = create_default_provider()
        
        # Listen to stock updates from data manager
        self.data_manager.on_stock_updated(self._on_stock_data_updated)
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._trigger_data_manager_refresh)
        
        self.setup_ui()
        self.load_portfolio()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("<h2>Stock Portfolio</h2>")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Auto-refresh controls
        self.auto_refresh_checkbox = QComboBox()
        self.auto_refresh_checkbox.addItems(["Manual", "30 sec", "1 min", "5 min", "15 min"])
        self.auto_refresh_checkbox.currentTextChanged.connect(self.on_refresh_interval_changed)
        header_layout.addWidget(QLabel("Auto-refresh:"))
        header_layout.addWidget(self.auto_refresh_checkbox)
        
        # Refresh button
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.refresh_portfolio)
        header_layout.addWidget(self.refresh_btn)
        
        # Add trade button
        add_btn = QPushButton("➕ Add Trade")
        add_btn.clicked.connect(self.show_add_trade_dialog)
        header_layout.addWidget(add_btn)
        
        layout.addLayout(header_layout)
        
        # Summary section
        summary_group = QGroupBox("Portfolio Summary")
        summary_layout = QHBoxLayout()
        
        self.total_value_label = QLabel("Total Value: $0.00")
        self.total_value_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        summary_layout.addWidget(self.total_value_label)
        
        summary_layout.addStretch()
        
        self.total_cost_label = QLabel("Total Cost: $0.00")
        summary_layout.addWidget(self.total_cost_label)
        
        self.total_pl_label = QLabel("Total P&L: $0.00 (0.00%)")
        summary_layout.addWidget(self.total_pl_label)
        
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        
        # Positions table
        positions_group = QGroupBox("Positions")
        positions_layout = QVBoxLayout()
        
        self.positions_table = QTableWidget()
        self.positions_table.setColumnCount(13)
        self.positions_table.setHorizontalHeaderLabels([
            "Symbol", "Name", "Quantity", "Avg Cost", "Current Price", "Closing", "After-Hours",
            "Market Value", "Total Cost", "Unrealized P&L", "P&L %",
            "Last Update", "Actions"
        ])
        self.positions_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.positions_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.positions_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.positions_table.customContextMenuRequested.connect(self.show_context_menu)
        self.positions_table.cellDoubleClicked.connect(self.on_symbol_double_clicked)
        
        positions_layout.addWidget(self.positions_table)
        positions_group.setLayout(positions_layout)
        layout.addWidget(positions_group)
        
        # Status bar
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: gray; padding: 5px;")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
    
    def load_portfolio(self):
        """Load and display portfolio positions"""
        positions = self.portfolio_manager.get_positions(self.username)
        
        self.positions_table.setRowCount(len(positions))
        
        for row, position in enumerate(positions):
            # Add stock to data manager's watch list
            stock_data = self.data_manager.get_stock_data(position.symbol)
            if not stock_data:
                self.data_manager.add_stock(position.symbol)
            
            # Symbol
            symbol_item = QTableWidgetItem(position.symbol)
            symbol_item.setFlags(symbol_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.positions_table.setItem(row, 0, symbol_item)
            
            # Populate from cache if available
            self._update_row_from_cache(row, position)
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(4, 2, 4, 2)
            
            buy_btn = QPushButton("Buy")
            buy_btn.clicked.connect(lambda checked, s=position.symbol: self.quick_buy(s))
            actions_layout.addWidget(buy_btn)
            
            sell_btn = QPushButton("Sell")
            sell_btn.clicked.connect(lambda checked, s=position.symbol: self.quick_sell(s))
            actions_layout.addWidget(sell_btn)
            
            remove_btn = QPushButton("Close")
            remove_btn.clicked.connect(lambda checked, s=position.symbol: self.close_position(s))
            actions_layout.addWidget(remove_btn)
            
            actions_widget.setLayout(actions_layout)
            self.positions_table.setCellWidget(row, 12, actions_widget)
        
        self.status_label.setText(f"Loaded {len(positions)} positions")
        self._update_portfolio_summary()
    
    def _update_row_from_cache(self, row: int, position):
        """Update a table row with cached stock data."""
        stock_data = self.data_manager.get_stock_data(position.symbol)
        
        # Name - get from stock data cache
        name = stock_data.company_name if stock_data else "—"
        if not name or name == "—":
            name = "—"
        self.positions_table.setItem(row, 1, QTableWidgetItem(name))
        
        # Quantity
        self.positions_table.setItem(row, 2, QTableWidgetItem(f"{position.quantity:.3f}"))
        
        # Avg Cost
        self.positions_table.setItem(row, 3, QTableWidgetItem(f"${position.avg_cost:.2f}"))
        
        if stock_data and stock_data.price:
            # Current Price
            price_item = QTableWidgetItem(f"${stock_data.price:.2f}")
            self.positions_table.setItem(row, 4, price_item)
            
            # Closing Price
            closing_price = stock_data.closing_price if hasattr(stock_data, 'closing_price') else None
            if closing_price:
                closing_item = QTableWidgetItem(f"${closing_price:.2f}")
                self.positions_table.setItem(row, 5, closing_item)
            else:
                self.positions_table.setItem(row, 5, QTableWidgetItem("—"))
            
            # After-Hours Price
            after_hours = stock_data.after_hours_price if hasattr(stock_data, 'after_hours_price') else None
            if after_hours:
                after_hours_item = QTableWidgetItem(f"${after_hours:.2f}")
                self.positions_table.setItem(row, 6, after_hours_item)
            else:
                self.positions_table.setItem(row, 6, QTableWidgetItem("—"))
            
            # Market Value
            market_value = position.quantity * stock_data.price
            self.positions_table.setItem(row, 7, QTableWidgetItem(f"${market_value:,.2f}"))
            
            # Total Cost
            total_cost = position.quantity * position.avg_cost
            self.positions_table.setItem(row, 8, QTableWidgetItem(f"${total_cost:,.2f}"))
            
            # Unrealized P&L
            pl = market_value - total_cost
            pl_item = QTableWidgetItem(f"${pl:,.2f}")
            if pl < 0:
                pl_item.setForeground(QBrush(QColor("red")))
            else:
                pl_item.setForeground(QBrush(QColor("green")))
            self.positions_table.setItem(row, 9, pl_item)
            
            # P&L %
            if total_cost != 0:
                pl_pct = (pl / total_cost) * 100
                pct_item = QTableWidgetItem(f"{pl_pct:.2f}%")
                if pl_pct < 0:
                    pct_item.setForeground(QBrush(QColor("red")))
                else:
                    pct_item.setForeground(QBrush(QColor("green")))
                self.positions_table.setItem(row, 10, pct_item)
            
            # Last update
            if stock_data.last_updated:
                time_str = stock_data.last_updated.strftime("%H:%M:%S")
                self.positions_table.setItem(row, 11, QTableWidgetItem(time_str))
        else:
            # Placeholder for empty columns
            for col in range(4, 12):
                item = QTableWidgetItem("—")
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.positions_table.setItem(row, col, item)
    
    def _update_portfolio_summary(self):
        """Update the portfolio summary labels."""
        positions = self.portfolio_manager.get_positions(self.username)
        total_cost = 0
        total_value = 0
        
        for position in positions:
            total_cost += position.quantity * position.avg_cost
            stock_data = self.data_manager.get_stock_data(position.symbol)
            if stock_data and stock_data.price:
                total_value += position.quantity * stock_data.price
        
        self.total_cost_label.setText(f"Total Cost: ${total_cost:,.2f}")
        self.total_value_label.setText(f"Total Value: ${total_value:,.2f}")
        
        total_pl = total_value - total_cost
        pl_pct = (total_pl / total_cost * 100) if total_cost != 0 else 0
        
        pl_color = "red" if total_pl < 0 else "green"
        self.total_pl_label.setText(f'<span style="color: {pl_color};">Total P&L: ${total_pl:,.2f} ({pl_pct:.2f}%)</span>')
    
    def show_add_trade_dialog(self):
        """Show dialog to add a new trade"""
        dialog = AddTradeDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            trade_data = dialog.get_trade_data()
            if trade_data['symbol']:
                self.add_trade(trade_data)
    
    def add_trade(self, trade_data):
        """Add a trade to the portfolio"""
        symbol = trade_data['symbol']
        quantity = trade_data['quantity']
        price = trade_data['price']
        
        # Add to data manager (background refresh will fetch its data)
        self.data_manager.add_stock(symbol)
        
        # Add to portfolio manager
        self.portfolio_manager.add_trade(self.username, symbol, quantity, price)
        
        # Reload portfolio
        self.load_portfolio()
        
        trade_type = "Buy" if quantity > 0 else "Sell"
        self.status_label.setText(f"Added {trade_type} trade: {abs(quantity):.3f} shares of {symbol} @ ${price:.2f}")
    
    def quick_buy(self, symbol):
        """Quick buy dialog for existing position"""
        dialog = AddTradeDialog(self)
        dialog.symbol_input.setText(symbol)
        dialog.symbol_input.setEnabled(False)
        dialog.trade_type_combo.setCurrentText("Buy")
        dialog.trade_type_combo.setEnabled(False)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            trade_data = dialog.get_trade_data()
            self.add_trade(trade_data)
    
    def quick_sell(self, symbol):
        """Quick sell dialog for existing position"""
        dialog = AddTradeDialog(self)
        dialog.symbol_input.setText(symbol)
        dialog.symbol_input.setEnabled(False)
        dialog.trade_type_combo.setCurrentText("Sell")
        dialog.trade_type_combo.setEnabled(False)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            trade_data = dialog.get_trade_data()
            self.add_trade(trade_data)
    
    def close_position(self, symbol):
        """Close a position completely"""
        reply = QMessageBox.question(
            self,
            "Confirm Close",
            f"Close position for {symbol}?\n"
            "This will remove it from your portfolio.\n"
            "You can add it back later with new trades.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.portfolio_manager.remove_position(self.username, symbol)
            self.load_portfolio()
            self.status_label.setText(f"Closed position: {symbol}")
    
    def refresh_portfolio(self):
        """Trigger a refresh of portfolio quotes from the provider."""
        positions = self.portfolio_manager.get_positions(self.username)
        symbols = [pos.symbol for pos in positions]
        
        if not symbols:
            self.status_label.setText("No positions in portfolio")
            return
        
        try:
            # Fetch fresh quotes from the provider
            quotes = self.provider.fetch_quotes(symbols)
            
            # Ingest the quotes into the data manager
            for symbol, quote_data in quotes.items():
                self.data_manager.ingest_quote(quote_data)
            
            # Update the UI
            self.load_portfolio()
            self.status_label.setText(f"Refreshed {len(quotes)} positions successfully")
        except Exception as e:
            self.status_label.setText(f"Refresh failed: {str(e)}")
            logger.error(f"Portfolio refresh error: {e}")
    
    def _trigger_data_manager_refresh(self):
        """Called by auto-refresh timer to trigger a refresh cycle."""
        self.refresh_portfolio()
    
    def _on_stock_data_updated(self, ticker: str, stock_data):
        """Called when stock data is updated in the manager."""
        # Find row for this ticker and update it
        positions = self.portfolio_manager.get_positions(self.username)
        for i, pos in enumerate(positions):
            if pos.symbol == ticker:
                self._update_row_from_cache(i, pos)
        
        # Update summary
        self._update_portfolio_summary()
    
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
        """Show context menu for position actions"""
        menu = QMenu(self)
        
        # Get selected row
        row = self.positions_table.rowAt(position.y())
        if row < 0:
            return
        
        symbol_item = self.positions_table.item(row, 0)
        if not symbol_item:
            return
        
        symbol = symbol_item.text()
        
        # Add actions
        view_action = QAction(f"View {symbol} Details", self)
        view_action.triggered.connect(lambda: self.view_symbol_details(symbol))
        menu.addAction(view_action)
        
        menu.addSeparator()
        
        buy_action = QAction(f"Buy More {symbol}", self)
        buy_action.triggered.connect(lambda: self.quick_buy(symbol))
        menu.addAction(buy_action)
        
        sell_action = QAction(f"Sell {symbol}", self)
        sell_action.triggered.connect(lambda: self.quick_sell(symbol))
        menu.addAction(sell_action)
        
        menu.addSeparator()
        
        close_action = QAction(f"Close Position", self)
        close_action.triggered.connect(lambda: self.close_position(symbol))
        menu.addAction(close_action)
        
        menu.exec(self.positions_table.viewport().mapToGlobal(position))
    
    def on_symbol_double_clicked(self, row, col):
        """Handle double-click on symbol"""
        symbol_item = self.positions_table.item(row, 0)
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
        self.load_portfolio()


if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    widget = StockPortfolioWidget(username='test_user')
    widget.setMinimumSize(1200, 600)
    widget.show()
    
    sys.exit(app.exec())
