"""
POS (Point of Sale) Tab
Main UI for the Point of Sale system in Financial Manager
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
                             QTableWidget, QTableWidgetItem, QPushButton, 
                             QDialog, QLabel, QLineEdit, QDoubleSpinBox, 
                             QSpinBox, QComboBox, QTextEdit, QMessageBox,
                             QInputDialog, QHeaderView, QFrame,
                             QGroupBox, QFormLayout, QCheckBox)
from PyQt6.QtCore import Qt, pyqtSignal, QDate, QDateTime
from PyQt6.QtGui import QColor, QFont
from datetime import datetime
from typing import Optional, Dict, Any
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pos_manager import POSManager
from services.store_settings import StoreSettings
from assets.Logger import Logger

logger = Logger()


class AddProductDialog(QDialog):
    """Dialog for adding a new product"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Product")
        self.setGeometry(100, 100, 600, 500)
        self.init_ui()
    
    def init_ui(self):
        layout = QFormLayout()
        
        # Product fields
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Required")
        layout.addRow("Product Name:", self.name_input)
        
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(80)
        layout.addRow("Description:", self.description_input)
        
        self.item_number_input = QLineEdit()
        self.item_number_input.setPlaceholderText("SKU or Item Number")
        layout.addRow("Item Number:", self.item_number_input)
        
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("Comma-separated tags")
        layout.addRow("Tags:", self.tags_input)
        
        # Pricing
        self.price_input = QDoubleSpinBox()
        self.price_input.setMinimum(0)
        self.price_input.setMaximum(999999)
        self.price_input.setDecimals(2)
        layout.addRow("Regular Price:", self.price_input)
        
        self.sale_price_input = QDoubleSpinBox()
        self.sale_price_input.setMinimum(0)
        self.sale_price_input.setMaximum(999999)
        self.sale_price_input.setDecimals(2)
        layout.addRow("Sale Price (optional):", self.sale_price_input)
        
        self.purchase_price_input = QDoubleSpinBox()
        self.purchase_price_input.setMinimum(0)
        self.purchase_price_input.setMaximum(999999)
        self.purchase_price_input.setDecimals(2)
        layout.addRow("Purchase Price:", self.purchase_price_input)
        
        self.fees_input = QDoubleSpinBox()
        self.fees_input.setMinimum(0)
        self.fees_input.setMaximum(999999)
        self.fees_input.setDecimals(2)
        layout.addRow("Fees:", self.fees_input)
        
        # Restrictions
        self.restrictions_input = QLineEdit()
        self.restrictions_input.setPlaceholderText("Any restrictions on this product")
        layout.addRow("Restrictions:", self.restrictions_input)
        
        # Initial inventory
        self.initial_qty_input = QSpinBox()
        self.initial_qty_input.setMinimum(0)
        self.initial_qty_input.setMaximum(999999)
        layout.addRow("Initial Quantity:", self.initial_qty_input)
        
        # Reorder level
        self.reorder_level_input = QSpinBox()
        self.reorder_level_input.setMinimum(0)
        self.reorder_level_input.setMaximum(999999)
        layout.addRow("Reorder Level:", self.reorder_level_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        add_btn = QPushButton("Add Product")
        cancel_btn = QPushButton("Cancel")
        
        add_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(add_btn)
        button_layout.addWidget(cancel_btn)
        layout.addRow(button_layout)
        
        self.setLayout(layout)
    
    def get_data(self) -> Dict[str, Any]:
        """Get the entered data"""
        sale_price = self.sale_price_input.value() if self.sale_price_input.value() > 0 else None
        
        return {
            'name': self.name_input.text(),
            'description': self.description_input.toPlainText(),
            'item_number': self.item_number_input.text(),
            'tags': self.tags_input.text(),
            'price': self.price_input.value(),
            'sale_price': sale_price,
            'purchase_price': self.purchase_price_input.value(),
            'fees': self.fees_input.value(),
            'restrictions': self.restrictions_input.text(),
            'initial_quantity': self.initial_qty_input.value(),
            'reorder_level': self.reorder_level_input.value()
        }


class POSTab(QWidget):
    """Point of Sale system tab - Simplified version"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.debug("POSTab", "Initializing POSTab")
        
        self.pos_manager = POSManager()
        self.cart = []
        self.applied_deal = None
        
        # Load default tax rate from settings
        try:
            self.default_tax_rate = self.pos_manager.get_tax_rate(None)
        except:
            self.default_tax_rate = 0.08
        
        self.init_ui()
        self.load_products()
        self.load_deals()
        
        logger.info("POSTab", "POSTab initialized successfully")
    
    def init_ui(self):
        main_layout = QVBoxLayout()
        
        # Location/Tax section
        location_group = QGroupBox("Tax Information")
        location_layout = QVBoxLayout()
        
        # Location input
        location_row = QHBoxLayout()
        location_row.addWidget(QLabel("Sale Location:"))
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Leave blank for default tax rate")
        # Pre-populate with the current location from store settings
        if self.location:
            self.location_input.setText(self.location if isinstance(self.location, str) else "")
        self.location_input.textChanged.connect(self.on_location_changed)
        location_row.addWidget(self.location_input)
        
        self.tax_rate_label = QLabel()
        self.update_tax_rate_label()
        location_row.addWidget(self.tax_rate_label)
        location_row.addStretch()
        
        location_layout.addLayout(location_row)
        
        # Tax exempt checkbox
        self.tax_exempt_check = QCheckBox("Tax Exempt")
        self.tax_exempt_check.setToolTip("Mark this transaction as tax-exempt")
        self.tax_exempt_check.stateChanged.connect(self.on_tax_exempt_changed)
        location_layout.addWidget(self.tax_exempt_check)
        
        location_group.setLayout(location_layout)
        main_layout.addWidget(location_group)
        
        # Item entry section
        item_group = QGroupBox("Add Items")
        item_layout = QHBoxLayout()
        
        item_layout.addWidget(QLabel("Item #:"))
        self.item_number_input = QLineEdit()
        self.item_number_input.setPlaceholderText("Enter item number or product name")
        self.item_number_input.returnPressed.connect(self.add_item_to_cart)
        item_layout.addWidget(self.item_number_input)
        
        item_layout.addWidget(QLabel("Qty:"))
        self.item_qty_input = QSpinBox()
        self.item_qty_input.setMinimum(1)
        self.item_qty_input.setMaximum(99999)
        self.item_qty_input.setValue(1)
        item_layout.addWidget(self.item_qty_input)
        
        add_btn = QPushButton("Add Item")
        add_btn.clicked.connect(self.add_item_to_cart)
        item_layout.addWidget(add_btn)
        
        item_group.setLayout(item_layout)
        main_layout.addWidget(item_group)
        
        # Cart display
        cart_label = QLabel("Cart Items:")
        cart_font = QFont()
        cart_font.setBold(True)
        cart_label.setFont(cart_font)
        main_layout.addWidget(cart_label)
        
        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(6)
        self.cart_table.setHorizontalHeaderLabels(["Product", "Item #", "Qty", "Price", "Subtotal", "Remove"])
        self.cart_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.cart_table.setMaximumHeight(200)
        main_layout.addWidget(self.cart_table)
        
        # Deals section
        deals_group = QGroupBox("Apply Deals")
        deals_layout = QHBoxLayout()
        
        deals_layout.addWidget(QLabel("Available Deals:"))
        self.deals_combo = QComboBox()
        self.deals_combo.addItem("-- No deal --")
        deals_layout.addWidget(self.deals_combo)
        
        apply_deal_btn = QPushButton("Apply Deal")
        apply_deal_btn.clicked.connect(self.apply_deal)
        deals_layout.addWidget(apply_deal_btn)
        
        deals_layout.addStretch()
        deals_group.setLayout(deals_layout)
        main_layout.addWidget(deals_group)
        
        # Payment section
        payment_group = QGroupBox("Payment Information")
        payment_layout = QFormLayout()
        
        self.payment_method_input = QComboBox()
        self.payment_method_input.addItems(["Cash", "Card", "Check", "Other"])
        payment_layout.addRow("Payment Method:", self.payment_method_input)
        
        self.customer_name_input = QLineEdit()
        self.customer_name_input.setPlaceholderText("Optional")
        payment_layout.addRow("Customer Name:", self.customer_name_input)
        
        self.customer_contact_input = QLineEdit()
        self.customer_contact_input.setPlaceholderText("Optional")
        payment_layout.addRow("Customer Contact:", self.customer_contact_input)
        
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(60)
        payment_layout.addRow("Notes:", self.notes_input)
        
        payment_group.setLayout(payment_layout)
        main_layout.addWidget(payment_group)
        
        # Totals section
        totals_layout = QFormLayout()
        
        self.subtotal_label = QLabel("$0.00")
        subtotal_font = QFont()
        subtotal_font.setPointSize(11)
        self.subtotal_label.setFont(subtotal_font)
        totals_layout.addRow("Subtotal:", self.subtotal_label)
        
        self.discount_label = QLabel("$0.00")
        self.discount_label.setFont(subtotal_font)
        totals_layout.addRow("Discount:", self.discount_label)
        
        self.tax_label = QLabel("$0.00")
        self.tax_label.setFont(subtotal_font)
        totals_layout.addRow("Tax:", self.tax_label)
        
        self.total_label = QLabel("$0.00")
        total_font = QFont()
        total_font.setBold(True)
        total_font.setPointSize(13)
        self.total_label.setFont(total_font)
        totals_layout.addRow("Total:", self.total_label)
        
        main_layout.addLayout(totals_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        process_btn = QPushButton("Process Sale")
        cancel_btn = QPushButton("Cancel")
        
        process_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(process_btn)
        button_layout.addWidget(cancel_btn)
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
        
        # Load available deals
        self.load_deals()
        self.applied_deal = None
    
    def on_location_changed(self):
        """Handle location change"""
        self.location = self.location_input.text().strip() or None
        self.update_tax_rate_label()
        self.update_totals()
    
    def on_tax_exempt_changed(self):
        """Handle tax exempt checkbox change"""
        self.update_totals()
    
    def update_tax_rate_label(self):
        """Update the tax rate display"""
        try:
            tax_rate = self.pos_manager.get_tax_rate(self.location)
            self.tax_rate_label.setText(f"(Tax Rate: {tax_rate*100:.2f}%)")
        except:
            self.tax_rate_label.setText("")
    
    def load_deals(self):
        """Load available deals into the combo box"""
        try:
            deals = self.pos_manager.get_active_deals()
            self.deals_combo.clear()
            self.deals_combo.addItem("-- No deal --")
            for deal in deals:
                # Generate appropriate display text based on deal type
                if deal['deal_mechanism'] == 'discount':
                    symbol = '%' if deal['discount_type'] == 'percentage' else '$'
                    display_text = f"{deal['name']} ({deal['discount_value']}{symbol} off)"
                else:  # bogo
                    display_text = f"{deal['name']} (Buy {deal['bogo_buy_qty']} Get {deal['bogo_get_qty']} Free)"
                
                self.deals_combo.addItem(display_text, deal['deal_id'])
        except Exception as e:
            logger.error("ProcessSaleDialog", f"Error loading deals: {e}")
    
    def add_item_to_cart(self):
        """Add item to cart by item number"""
        item_input = self.item_number_input.text().strip()
        if not item_input:
            QMessageBox.warning(self, "Error", "Please enter an item number or product name")
            return
        
        try:
            # Try to find by item number first
            product = self.pos_manager.get_product_by_item_number(item_input)
            if not product:
                # Try to find by name
                product = self.pos_manager.get_product_by_name(item_input)
            
            if not product:
                QMessageBox.warning(self, "Error", f"Product '{item_input}' not found")
                return
            
            # Check if already in cart
            for i, item in enumerate(self.cart):
                if item['product_id'] == product['product_id']:
                    # Update quantity
                    item['quantity'] += self.item_qty_input.value()
                    self.update_cart_display()
                    self.item_number_input.clear()
                    self.item_qty_input.setValue(1)
                    return
            
            # Add new item
            unit_price = product['sale_price'] if product['sale_price'] else product['price']
            self.cart.append({
                'product_id': product['product_id'],
                'name': product['name'],
                'item_number': product['item_number'] or 'N/A',
                'quantity': self.item_qty_input.value(),
                'unit_price': unit_price,
                'category': product['category'],
                'price': product['price'],  # Store original price for deal matching
                'tags': product['tags'].split(',') if product['tags'] else []
            })
            
            self.update_cart_display()
            self.item_number_input.clear()
            self.item_qty_input.setValue(1)
            self.item_number_input.setFocus()
            
        except Exception as e:
            logger.error("ProcessSaleDialog", f"Error adding item: {e}")
            QMessageBox.warning(self, "Error", f"Error adding item: {e}")
    
    def update_cart_display(self):
        """Update the cart table display"""
        self.cart_table.setRowCount(0)
        
        for i, item in enumerate(self.cart):
            self.cart_table.insertRow(i)
            
            # Product name
            self.cart_table.setItem(i, 0, QTableWidgetItem(item['name']))
            
            # Item number
            self.cart_table.setItem(i, 1, QTableWidgetItem(item['item_number']))
            
            # Quantity
            self.cart_table.setItem(i, 2, QTableWidgetItem(str(item['quantity'])))
            
            # Price
            self.cart_table.setItem(i, 3, QTableWidgetItem(f"${item['unit_price']:.2f}"))
            
            # Subtotal
            subtotal = item['quantity'] * item['unit_price']
            self.cart_table.setItem(i, 4, QTableWidgetItem(f"${subtotal:.2f}"))
            
            # Remove button
            remove_btn = QPushButton("Remove")
            remove_btn.clicked.connect(lambda checked, row=i: self.remove_item(row))
            self.cart_table.setCellWidget(i, 5, remove_btn)
        
        self.update_totals()
    
    def remove_item(self, row):
        """Remove item from cart"""
        if 0 <= row < len(self.cart):
            self.cart.pop(row)
            self.update_cart_display()
    
    def apply_deal(self):
        """Apply selected deal to cart"""
        if not self.cart:
            QMessageBox.warning(self, "Error", "Cart is empty")
            return
        
        deal_id = self.deals_combo.currentData()
        if not deal_id:
            self.applied_deal = None
            self.update_totals()
            return
        
        try:
            deal = self.pos_manager.get_deal(deal_id)
            
            # Validate that deal applies to at least one item in cart
            applicable_items = 0
            for item in self.cart:
                applicable_deals = self.pos_manager.get_applicable_deals(
                    product_id=item['product_id'],
                    tags=item['tags'],
                    item_number=item['item_number'],
                    price=item['price'],
                    category=item['category']
                )
                if any(d['deal_id'] == deal_id for d in applicable_deals):
                    applicable_items += 1
            
            if applicable_items == 0:
                QMessageBox.warning(self, "Error", "This deal does not apply to any items in the cart")
                return
            
            self.applied_deal = deal
            self.update_totals()
            QMessageBox.information(self, "Success", f"Deal '{deal['name']}' applied to {applicable_items} item(s)!")
        except Exception as e:
            logger.error("ProcessSaleDialog", f"Error applying deal: {e}")
            QMessageBox.warning(self, "Error", f"Error applying deal: {e}")
    
    def update_totals(self):
        """Update total price with deal applied and tax calculated"""
        subtotal = sum(item['quantity'] * item['unit_price'] for item in self.cart)
        discount = 0
        
        if self.applied_deal and self.cart:
            # Apply deal to items that qualify
            total_discount = 0
            for item in self.cart:
                # Check if this item qualifies for the deal
                applicable_deals = self.pos_manager.get_applicable_deals(
                    product_id=item['product_id'],
                    tags=item['tags'],
                    item_number=item['item_number'],
                    price=item['price'],
                    category=item['category']
                )
                
                # Check if our applied deal is in the applicable list
                if any(d['deal_id'] == self.applied_deal['deal_id'] for d in applicable_deals):
                    # Calculate discount for this item
                    item_discount = self.pos_manager.calculate_deal_discount(
                        self.applied_deal, item['quantity'], item['unit_price']
                    )
                    total_discount += item_discount
            
            discount = total_discount
        
        # Calculate tax on the discounted subtotal (unless tax exempt)
        discounted_subtotal = subtotal - discount
        
        if self.tax_exempt_check.isChecked():
            tax_amount = 0
        else:
            tax_amount = self.pos_manager.calculate_tax(discounted_subtotal, self.location)
        
        total = discounted_subtotal + tax_amount
        
        self.subtotal_label.setText(f"${subtotal:.2f}")
        self.discount_label.setText(f"-${discount:.2f}")
        self.tax_label.setText(f"${tax_amount:.2f}")
        self.total_label.setText(f"${total:.2f}")
    
    def get_data(self) -> Dict[str, Any]:
        """Get the sale data"""
        if not self.cart:
            raise ValueError("Cart is empty")
        
        return {
            'cart': self.cart,
            'applied_deal': self.applied_deal,
            'location': self.location,
            'tax_exempt': self.tax_exempt_check.isChecked(),
            'payment_method': self.payment_method_input.currentText(),
            'customer_name': self.customer_name_input.text(),
            'customer_contact': self.customer_contact_input.text(),
            'notes': self.notes_input.toPlainText()
        }


class POSTab(QWidget):
    """Point of Sale system tab"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.debug("POSTab", "Initializing POSTab")
        
        self.pos_manager = POSManager()
        self.store_settings = StoreSettings()
        self.current_product = None
        self.cart = []
        self.applied_deal = None
        self.location = self.store_settings.get_location()  # Load from store settings
        
        # Load default tax rate from settings
        try:
            self.default_tax_rate = self.pos_manager.get_tax_rate(None)
        except:
            self.default_tax_rate = 0.08
        
        self.init_ui()
        self.load_products()
        self.load_deals()
        
        logger.info("POSTab", "POSTab initialized successfully")
    
    def init_ui(self):
        """Initialize UI components"""
        main_layout = QVBoxLayout()
        
        # Create tabs
        tabs = QTabWidget()
        
        # Product Management Tab
        tabs.addTab(self.create_product_tab(), "Products")
        
        # Sales Tab
        tabs.addTab(self.create_sales_tab(), "Process Sales")
        
        # Recent Sales Tab
        tabs.addTab(self.create_recent_sales_tab(), "Recent Sales")
        
        # Inventory Tab
        tabs.addTab(self.create_inventory_tab(), "Inventory")
        
        # Deals Tab
        tabs.addTab(self.create_deals_tab(), "Deals")
        
        # Reports Tab
        tabs.addTab(self.create_reports_tab(), "Reports")
        
        main_layout.addWidget(tabs)
        self.setLayout(main_layout)
    
    def create_product_tab(self) -> QWidget:
        """Create the product management tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Add product button
        add_btn = QPushButton("Add New Product")
        add_btn.clicked.connect(self.add_product)
        layout.addWidget(add_btn)
        
        # Search/filter
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.product_search = QLineEdit()
        self.product_search.setPlaceholderText("Search by name, item number, or tags...")
        self.product_search.textChanged.connect(self.filter_products)
        search_layout.addWidget(self.product_search)
        layout.addLayout(search_layout)
        
        # Product table
        self.product_table = QTableWidget()
        self.product_table.setColumnCount(9)
        self.product_table.setHorizontalHeaderLabels(
            ["Name", "Item #", "Price", "Sale Price", "In Stock", "Reorder Level", "Status", "Actions", "ID"]
        )
        self.product_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.product_table.setColumnHidden(8, True)  # Hide ID column
        layout.addWidget(self.product_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_sales_tab(self) -> QWidget:
        """Create the integrated sales processing tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Location/Tax section (IMPORTANT: Must be before items to initialize location properly)
        location_group = QGroupBox("Tax Information")
        location_layout = QVBoxLayout()
        
        # Location input
        location_row = QHBoxLayout()
        location_row.addWidget(QLabel("Sale Location:"))
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Leave blank for default tax rate")
        # Pre-populate with the current location from store settings
        if self.location:
            self.location_input.setText(self.location if isinstance(self.location, str) else "")
        self.location_input.textChanged.connect(self.on_location_changed)
        location_row.addWidget(self.location_input)
        
        self.tax_rate_label = QLabel()
        self.update_tax_rate_label()
        location_row.addWidget(self.tax_rate_label)
        location_row.addStretch()
        
        location_layout.addLayout(location_row)
        
        # Tax exempt checkbox
        self.tax_exempt_check = QCheckBox("Tax Exempt")
        self.tax_exempt_check.setToolTip("Mark this transaction as tax-exempt")
        self.tax_exempt_check.stateChanged.connect(self.on_tax_exempt_changed)
        location_layout.addWidget(self.tax_exempt_check)
        
        location_group.setLayout(location_layout)
        layout.addWidget(location_group)
        
        # Item entry section
        item_group = QGroupBox("Add Items to Cart")
        item_layout = QHBoxLayout()
        
        item_layout.addWidget(QLabel("Item #/Name:"))
        self.item_number_input = QLineEdit()
        self.item_number_input.setPlaceholderText("Enter item number or product name")
        self.item_number_input.returnPressed.connect(self.add_item_to_cart)
        item_layout.addWidget(self.item_number_input)
        
        item_layout.addWidget(QLabel("Qty:"))
        self.item_qty_input = QSpinBox()
        self.item_qty_input.setMinimum(1)
        self.item_qty_input.setMaximum(99999)
        self.item_qty_input.setValue(1)
        item_layout.addWidget(self.item_qty_input)
        
        add_btn = QPushButton("Add Item")
        add_btn.clicked.connect(self.add_item_to_cart)
        add_btn.setMaximumWidth(100)
        item_layout.addWidget(add_btn)
        
        item_group.setLayout(item_layout)
        layout.addWidget(item_group)
        
        # Cart display
        cart_label = QLabel("Shopping Cart:")
        cart_font = QFont()
        cart_font.setBold(True)
        cart_label.setFont(cart_font)
        layout.addWidget(cart_label)
        
        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(6)
        self.cart_table.setHorizontalHeaderLabels(["Product", "Item #", "Qty", "Price", "Subtotal", "Remove"])
        self.cart_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.cart_table.setMaximumHeight(200)
        layout.addWidget(self.cart_table)
        
        # Deals section
        deals_group = QGroupBox("Promotions & Deals")
        deals_layout = QHBoxLayout()
        
        deals_layout.addWidget(QLabel("Available Deals:"))
        self.deals_combo = QComboBox()
        self.deals_combo.addItem("-- No deal --")
        deals_layout.addWidget(self.deals_combo)
        
        apply_deal_btn = QPushButton("Apply Deal")
        apply_deal_btn.clicked.connect(self.apply_deal)
        apply_deal_btn.setMaximumWidth(100)
        deals_layout.addWidget(apply_deal_btn)
        deals_layout.addStretch()
        deals_group.setLayout(deals_layout)
        layout.addWidget(deals_group)
        
        # Payment section
        payment_group = QGroupBox("Payment Information")
        payment_layout = QFormLayout()
        
        self.payment_method_input = QComboBox()
        self.payment_method_input.addItems(["Cash", "Card", "Check", "Other"])
        payment_layout.addRow("Payment Method:", self.payment_method_input)
        
        self.customer_name_input = QLineEdit()
        self.customer_name_input.setPlaceholderText("Optional - customer name")
        payment_layout.addRow("Customer Name:", self.customer_name_input)
        
        self.customer_contact_input = QLineEdit()
        self.customer_contact_input.setPlaceholderText("Optional - phone/email")
        payment_layout.addRow("Customer Contact:", self.customer_contact_input)
        
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(50)
        self.notes_input.setPlaceholderText("Optional notes")
        payment_layout.addRow("Notes:", self.notes_input)
        
        payment_group.setLayout(payment_layout)
        layout.addWidget(payment_group)
        
        # Totals section
        totals_layout = QFormLayout()
        
        self.subtotal_label = QLabel("$0.00")
        subtotal_font = QFont()
        subtotal_font.setPointSize(11)
        self.subtotal_label.setFont(subtotal_font)
        totals_layout.addRow("Subtotal:", self.subtotal_label)
        
        self.discount_label = QLabel("$0.00")
        self.discount_label.setFont(subtotal_font)
        totals_layout.addRow("Discount:", self.discount_label)
        
        self.tax_label = QLabel("$0.00")
        self.tax_label.setFont(subtotal_font)
        # Dynamic tax rate label - will be updated in calculate_totals()
        self.tax_rate_label_totals = QLabel(f"Tax:")
        totals_layout.addRow(self.tax_rate_label_totals, self.tax_label)
        
        self.total_label = QLabel("$0.00")
        total_font = QFont()
        total_font.setBold(True)
        total_font.setPointSize(14)
        self.total_label.setFont(total_font)
        totals_layout.addRow("TOTAL:", self.total_label)
        
        layout.addLayout(totals_layout)
        
        # Process button
        process_btn = QPushButton("Complete Sale")
        process_btn.clicked.connect(self.complete_sale)
        process_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                font-size: 14px;
                padding: 15px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        layout.addWidget(process_btn)
        
        clear_btn = QPushButton("Clear Cart")
        clear_btn.clicked.connect(self.clear_cart)
        layout.addWidget(clear_btn)
        
        widget.setLayout(layout)
        return widget

    
    def create_recent_sales_tab(self) -> QWidget:
        """Create the recent sales tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Stats bar
        stats_layout = QHBoxLayout()
        stats_layout.addWidget(QLabel("Today's Sales:"))
        self.today_sales_label = QLabel("$0.00")
        self.today_sales_label.setStyleSheet("font-weight: bold; color: green;")
        stats_layout.addWidget(self.today_sales_label)
        
        stats_layout.addWidget(QLabel("Transactions:"))
        self.transaction_count_label = QLabel("0")
        self.transaction_count_label.setStyleSheet("font-weight: bold;")
        stats_layout.addWidget(self.transaction_count_label)
        stats_layout.addStretch()
        layout.addLayout(stats_layout)
        
        # Controls
        control_layout = QHBoxLayout()
        
        # Search/filter
        control_layout.addWidget(QLabel("Search:"))
        self.sales_search_input = QLineEdit()
        self.sales_search_input.setPlaceholderText("Search by customer name, product, or transaction ID...")
        self.sales_search_input.textChanged.connect(self.filter_recent_sales)
        control_layout.addWidget(self.sales_search_input)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_recent_sales)
        control_layout.addWidget(refresh_btn)
        
        layout.addLayout(control_layout)
        
        # Recent sales table
        self.recent_sales_table = QTableWidget()
        self.recent_sales_table.setColumnCount(7)
        self.recent_sales_table.setHorizontalHeaderLabels(
            ["Date/Time", "Product", "Qty", "Unit Price", "Subtotal", "Tax", "Total"]
        )
        self.recent_sales_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.recent_sales_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.recent_sales_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_inventory_tab(self) -> QWidget:
        """Create the inventory management tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Inventory controls
        control_layout = QHBoxLayout()
        adjust_btn = QPushButton("Adjust Inventory")
        adjust_btn.clicked.connect(self.adjust_inventory)
        control_layout.addWidget(adjust_btn)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_inventory)
        control_layout.addWidget(refresh_btn)
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # Inventory table
        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(6)
        self.inventory_table.setHorizontalHeaderLabels(
            ["Product", "Item #", "Current Stock", "Reorder Level", "Status", "Total Value"]
        )
        self.inventory_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.inventory_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_deals_tab(self) -> QWidget:
        """Create the deals/promotions management tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Add deal button
        add_btn = QPushButton("Create New Deal")
        add_btn.clicked.connect(self.create_deal)
        layout.addWidget(add_btn)
        
        # Deals table
        self.deals_table = QTableWidget()
        self.deals_table.setColumnCount(6)
        self.deals_table.setHorizontalHeaderLabels(
            ["Name", "Type", "Targeting", "Start Date", "End Date", "Actions"]
        )
        self.deals_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.deals_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.deals_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.deals_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_reports_tab(self) -> QWidget:
        """Create the reports tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Report selection
        report_layout = QHBoxLayout()
        report_layout.addWidget(QLabel("Select Report:"))
        self.report_combo = QComboBox()
        self.report_combo.addItems(["Sales Summary", "Top Sellers", "Low Stock", "Inventory Value"])
        self.report_combo.currentIndexChanged.connect(self.load_report)
        report_layout.addWidget(self.report_combo)
        layout.addLayout(report_layout)
        
        # Report display
        self.report_table = QTableWidget()
        layout.addWidget(self.report_table)
        
        widget.setLayout(layout)
        return widget
    
    def load_products(self):
        """Load all products into the table"""
        logger.debug("POSTab", "Loading products")
        try:
            products = self.pos_manager.get_all_products()
            self.product_table.setRowCount(len(products))
            
            for row, product in enumerate(products):
                self.product_table.setItem(row, 0, QTableWidgetItem(product['name']))
                self.product_table.setItem(row, 1, QTableWidgetItem(product['item_number'] or ''))
                self.product_table.setItem(row, 2, QTableWidgetItem(f"${product['price']:.2f}"))
                
                sale_price = product['sale_price'] if product['sale_price'] else '—'
                if sale_price != '—':
                    sale_price = f"${sale_price:.2f}"
                self.product_table.setItem(row, 3, QTableWidgetItem(str(sale_price)))
                
                self.product_table.setItem(row, 4, QTableWidgetItem(str(product['quantity_in_stock'])))
                self.product_table.setItem(row, 5, QTableWidgetItem(str(product['reorder_level'])))
                
                # Status
                if product['quantity_in_stock'] <= product['reorder_level']:
                    status = "LOW STOCK"
                    item = QTableWidgetItem(status)
                    item.setBackground(QColor(255, 200, 0))
                elif product['quantity_in_stock'] == 0:
                    status = "OUT OF STOCK"
                    item = QTableWidgetItem(status)
                    item.setBackground(QColor(255, 100, 100))
                else:
                    status = "OK"
                    item = QTableWidgetItem(status)
                    item.setBackground(QColor(100, 255, 100))
                self.product_table.setItem(row, 6, item)
                
                # Actions
                edit_btn = QPushButton("Edit")
                edit_btn.clicked.connect(lambda checked, pid=product['product_id']: self.edit_product(pid))
                self.product_table.setCellWidget(row, 7, edit_btn)
                
                # ID (hidden)
                self.product_table.setItem(row, 8, QTableWidgetItem(product['product_id']))
            
            logger.info("POSTab", f"Loaded {len(products)} products")
        except Exception as e:
            logger.error("POSTab", f"Error loading products: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load products: {e}")
    
    def filter_products(self):
        """Filter products based on search"""
        search_text = self.product_search.text().lower()
        
        for row in range(self.product_table.rowCount()):
            show = False
            for col in range(self.product_table.columnCount() - 1):  # Exclude ID column
                item = self.product_table.item(row, col)
                if item and search_text in item.text().lower():
                    show = True
                    break
            self.product_table.setRowHidden(row, not show)
    
    def add_product(self):
        """Add a new product"""
        logger.debug("POSTab", "Opening add product dialog")
        dialog = AddProductDialog(self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                data = dialog.get_data()
                
                if not data['name']:
                    QMessageBox.warning(self, "Validation Error", "Product name is required")
                    return
                
                self.pos_manager.add_product(**data)
                self.load_products()
                QMessageBox.information(self, "Success", f"Product '{data['name']}' added successfully")
                logger.info("POSTab", f"Product added: {data['name']}")
            except Exception as e:
                logger.error("POSTab", f"Error adding product: {e}")
                QMessageBox.critical(self, "Error", f"Failed to add product: {e}")
    
    def edit_product(self, product_id: str):
        """Edit a product"""
        logger.debug("POSTab", f"Editing product: {product_id}")
        
        try:
            product = self.pos_manager.get_product(product_id)
            if not product:
                QMessageBox.critical(self, "Error", "Product not found")
                return
            
            # Create edit dialog
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Edit Product - {product['name']}")
            dialog.setGeometry(100, 100, 600, 600)
            
            layout = QFormLayout()
            
            # Product name
            name_input = QLineEdit()
            name_input.setText(product['name'])
            layout.addRow("Product Name:", name_input)
            
            # Description
            desc_input = QTextEdit()
            desc_input.setText(product['description'] or "")
            desc_input.setMaximumHeight(80)
            layout.addRow("Description:", desc_input)
            
            # Item number
            item_num_input = QLineEdit()
            item_num_input.setText(product['item_number'] or "")
            layout.addRow("Item Number:", item_num_input)
            
            # Category
            category_input = QLineEdit()
            category_input.setText(product['category'] or "")
            layout.addRow("Category:", category_input)
            
            # Tags
            tags_input = QLineEdit()
            tags_input.setText(product['tags'] or "")
            tags_input.setPlaceholderText("Comma-separated tags")
            layout.addRow("Tags:", tags_input)
            
            # Prices
            price_input = QDoubleSpinBox()
            price_input.setMinimum(0)
            price_input.setMaximum(999999)
            price_input.setValue(product['price'] or 0)
            layout.addRow("Regular Price:", price_input)
            
            sale_price_input = QDoubleSpinBox()
            sale_price_input.setMinimum(0)
            sale_price_input.setMaximum(999999)
            sale_price_input.setValue(product['sale_price'] or 0)
            layout.addRow("Sale Price:", sale_price_input)
            
            purchase_price_input = QDoubleSpinBox()
            purchase_price_input.setMinimum(0)
            purchase_price_input.setMaximum(999999)
            purchase_price_input.setValue(product['purchase_price'] or 0)
            layout.addRow("Purchase Price:", purchase_price_input)
            
            # Fees
            fees_input = QDoubleSpinBox()
            fees_input.setMinimum(0)
            fees_input.setMaximum(999999)
            fees_input.setValue(product['fees'] or 0)
            layout.addRow("Fees:", fees_input)
            
            # Restrictions
            restrictions_input = QTextEdit()
            restrictions_input.setText(product['restrictions'] or "")
            restrictions_input.setMaximumHeight(60)
            layout.addRow("Restrictions:", restrictions_input)
            
            # Inventory
            qty_input = QSpinBox()
            qty_input.setMinimum(0)
            qty_input.setMaximum(999999)
            qty_input.setValue(product['quantity_in_stock'])
            layout.addRow("Current Stock:", qty_input)
            
            # Reorder level
            reorder_input = QSpinBox()
            reorder_input.setMinimum(0)
            reorder_input.setMaximum(999999)
            reorder_input.setValue(product['reorder_level'] or 0)
            layout.addRow("Reorder Level:", reorder_input)
            
            layout.addRow(QLabel(""))  # Spacer
            
            # Buttons
            button_layout = QHBoxLayout()
            save_btn = QPushButton("Save Changes")
            delete_btn = QPushButton("Deactivate")
            cancel_btn = QPushButton("Cancel")
            
            button_layout.addWidget(save_btn)
            button_layout.addWidget(delete_btn)
            button_layout.addWidget(cancel_btn)
            layout.addRow(button_layout)
            
            dialog.setLayout(layout)
            
            def save_changes():
                try:
                    # Update product
                    self.pos_manager.update_product(
                        product_id,
                        name=name_input.text(),
                        description=desc_input.toPlainText(),
                        item_number=item_num_input.text(),
                        category=category_input.text(),
                        tags=tags_input.text(),
                        price=price_input.value(),
                        sale_price=sale_price_input.value(),
                        purchase_price=purchase_price_input.value(),
                        fees=fees_input.value(),
                        restrictions=restrictions_input.toPlainText(),
                        reorder_level=reorder_input.value()
                    )
                    
                    # Update inventory if changed
                    if qty_input.value() != product['quantity_in_stock']:
                        diff = qty_input.value() - product['quantity_in_stock']
                        self.pos_manager.adjust_inventory(
                            product_id, diff, 
                            transaction_type="manual",
                            notes="Manual inventory adjustment"
                        )
                    
                    QMessageBox.information(dialog, "Success", "Product updated successfully!")
                    self.load_products()
                    self.load_inventory()
                    dialog.accept()
                except Exception as e:
                    logger.error("POSTab", f"Error saving product: {e}")
                    QMessageBox.critical(dialog, "Error", f"Failed to save product: {e}")
            
            def deactivate_product():
                reply = QMessageBox.question(
                    dialog, "Confirm Deactivation",
                    f"Are you sure you want to deactivate '{product['name']}'?\nThis product will no longer be available for sale.",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    try:
                        self.pos_manager.delete_product(product_id)
                        QMessageBox.information(dialog, "Success", "Product deactivated!")
                        self.load_products()
                        self.load_inventory()
                        dialog.accept()
                    except Exception as e:
                        logger.error("POSTab", f"Error deactivating product: {e}")
                        QMessageBox.critical(dialog, "Error", f"Failed to deactivate: {e}")
            
            save_btn.clicked.connect(save_changes)
            delete_btn.clicked.connect(deactivate_product)
            cancel_btn.clicked.connect(dialog.reject)
            
            dialog.exec()
            
        except Exception as e:
            logger.error("POSTab", f"Error editing product: {e}")
            QMessageBox.critical(self, "Error", f"Error editing product: {e}")
    
    def add_item_to_cart(self):
        """Add item to cart"""
        item_input = self.item_number_input.text().strip()
        if not item_input:
            QMessageBox.warning(self, "Error", "Please enter an item number or name")
            return
        
        try:
            # Try to find by item number first
            product = self.pos_manager.get_product_by_item_number(item_input)
            if not product:
                product = self.pos_manager.get_product_by_name(item_input)
            
            if not product:
                QMessageBox.warning(self, "Error", f"Product '{item_input}' not found")
                return
            
            # Check if already in cart
            for item in self.cart:
                if item['product_id'] == product['product_id']:
                    item['quantity'] += self.item_qty_input.value()
                    self.update_cart_display()
                    self.item_number_input.clear()
                    self.item_qty_input.setValue(1)
                    self.item_number_input.setFocus()
                    return
            
            # Add new item
            unit_price = product['sale_price'] if product['sale_price'] else product['price']
            self.cart.append({
                'product_id': product['product_id'],
                'name': product['name'],
                'item_number': product['item_number'] or 'N/A',
                'quantity': self.item_qty_input.value(),
                'unit_price': unit_price,
                'category': product.get('category', ''),
                'price': product['price'],
                'tags': product.get('tags', '').split(',') if product.get('tags') else []
            })
            
            self.update_cart_display()
            self.item_number_input.clear()
            self.item_qty_input.setValue(1)
            self.item_number_input.setFocus()
            
        except Exception as e:
            logger.error("POSTab", f"Error adding item: {e}")
            QMessageBox.warning(self, "Error", f"Error: {str(e)}")
    
    def update_cart_display(self):
        """Update cart table"""
        self.cart_table.setRowCount(0)
        
        for i, item in enumerate(self.cart):
            self.cart_table.insertRow(i)
            self.cart_table.setItem(i, 0, QTableWidgetItem(item['name']))
            self.cart_table.setItem(i, 1, QTableWidgetItem(item['item_number']))
            self.cart_table.setItem(i, 2, QTableWidgetItem(str(item['quantity'])))
            self.cart_table.setItem(i, 3, QTableWidgetItem(f"${item['unit_price']:.2f}"))
            subtotal = item['quantity'] * item['unit_price']
            self.cart_table.setItem(i, 4, QTableWidgetItem(f"${subtotal:.2f}"))
            
            remove_btn = QPushButton("Remove")
            remove_btn.clicked.connect(lambda checked, row=i: self.remove_item_from_cart(row))
            self.cart_table.setCellWidget(i, 5, remove_btn)
        
        self.calculate_totals()
    
    def remove_item_from_cart(self, row):
        """Remove item from cart"""
        if 0 <= row < len(self.cart):
            self.cart.pop(row)
            self.update_cart_display()
    
    def apply_deal(self):
        """Apply selected deal to cart"""
        if not self.cart:
            QMessageBox.warning(self, "Error", "Cart is empty")
            return
        
        deal_id = self.deals_combo.currentData()
        if not deal_id:
            self.applied_deal = None
            self.calculate_totals()
            return
        
        try:
            deal = self.pos_manager.get_deal(deal_id)
            applicable_items = 0
            
            for item in self.cart:
                applicable_deals = self.pos_manager.get_applicable_deals(
                    product_id=item['product_id'],
                    tags=item.get('tags', []),
                    item_number=item['item_number'],
                    price=item['price'],
                    category=item.get('category')
                )
                if any(d['deal_id'] == deal_id for d in applicable_deals):
                    applicable_items += 1
            
            if applicable_items == 0:
                QMessageBox.warning(self, "Error", "This deal doesn't apply to items in cart")
                return
            
            self.applied_deal = deal
            self.calculate_totals()
            QMessageBox.information(self, "Success", f"Deal '{deal['name']}' applied!")
        except Exception as e:
            logger.error("POSTab", f"Error applying deal: {e}")
            QMessageBox.warning(self, "Error", f"Error: {str(e)}")
    
    def on_location_changed(self):
        """Handle location change"""
        self.location = self.location_input.text().strip() or None
        self.update_tax_rate_label()
        self.calculate_totals()
    
    def on_tax_exempt_changed(self):
        """Handle tax exempt checkbox change"""
        self.calculate_totals()
    
    def update_tax_rate_label(self):
        """Update the tax rate display in the location section"""
        try:
            tax_rate = self.pos_manager.get_tax_rate(self.location)
            self.tax_rate_label.setText(f"(Tax Rate: {tax_rate*100:.2f}%)")
        except:
            self.tax_rate_label.setText("")
    
    def calculate_totals(self):
        """Calculate cart totals"""
        if not self.cart:
            self.subtotal_label.setText("$0.00")
            self.discount_label.setText("$0.00")
            self.tax_label.setText("$0.00")
            self.total_label.setText("$0.00")
            return
        
        # Calculate subtotal
        subtotal = sum(item['quantity'] * item['unit_price'] for item in self.cart)
        discount = 0
        
        # Apply deal if selected
        if self.applied_deal:
            for item in self.cart:
                applicable_deals = self.pos_manager.get_applicable_deals(
                    product_id=item['product_id'],
                    tags=item.get('tags', []),
                    item_number=item['item_number'],
                    price=item['price'],
                    category=item.get('category')
                )
                if any(d['deal_id'] == self.applied_deal['deal_id'] for d in applicable_deals):
                    item_discount = self.pos_manager.calculate_deal_discount(
                        self.applied_deal, item['quantity'], item['unit_price']
                    )
                    discount += item_discount
        
        # Calculate tax on discounted amount (use location-based tax rate or default)
        discounted_subtotal = subtotal - discount
        
        # Use location-based tax or default, respect tax-exempt status
        if hasattr(self, 'tax_exempt_check') and self.tax_exempt_check.isChecked():
            tax_amount = 0
        else:
            # Get store tax preferences
            tax_preferences = self.store_settings.get_tax_preferences()
            tax_amount = self.pos_manager.calculate_tax(
                discounted_subtotal, 
                self.location,
                tax_preferences=tax_preferences
            )
        
        # Calculate total
        total = discounted_subtotal + tax_amount
        
        # Update labels
        self.subtotal_label.setText(f"${subtotal:.2f}")
        self.discount_label.setText(f"-${discount:.2f}" if discount > 0 else "$0.00")
        self.tax_label.setText(f"${tax_amount:.2f}")
        self.total_label.setText(f"${total:.2f}")
        
        # Update tax rate label to show current location-based rate
        try:
            current_rate = self.pos_manager.get_tax_rate(self.location)
            self.tax_rate_label_totals.setText(f"Tax ({current_rate*100:.2f}%):")
        except:
            self.tax_rate_label_totals.setText("Tax:")
    
    def complete_sale(self):
        """Process the completed sale"""
        if not self.cart:
            QMessageBox.warning(self, "Error", "Cart is empty")
            return
        
        try:
            total_amount = sum(item['quantity'] * item['unit_price'] for item in self.cart)
            discount_amount = 0
            
            if self.applied_deal:
                for item in self.cart:
                    applicable_deals = self.pos_manager.get_applicable_deals(
                        product_id=item['product_id'],
                        tags=item.get('tags', []),
                        item_number=item['item_number'],
                        price=item['price'],
                        category=item.get('category')
                    )
                    if any(d['deal_id'] == self.applied_deal['deal_id'] for d in applicable_deals):
                        discount_amount += self.pos_manager.calculate_deal_discount(
                            self.applied_deal, item['quantity'], item['unit_price']
                        )
            
            discounted_total = total_amount - discount_amount
            
            # Calculate tax based on location and exempt status
            if self.tax_exempt_check.isChecked():
                tax_amount = 0.0
            else:
                # Get tax rate for location (uses DEFAULT if no location specified)
                tax_rate = self.pos_manager.get_tax_rate(self.location)
                tax_amount = discounted_total * tax_rate
            
            final_total = discounted_total + tax_amount
            
            # Process each item
            for cart_item in self.cart:
                try:
                    transaction_id, subtotal, tax, amt_total = self.pos_manager.process_sale_with_tax(
                        product_id=cart_item['product_id'],
                        quantity=cart_item['quantity'],
                        payment_method=self.payment_method_input.currentText(),
                        customer_name=self.customer_name_input.text(),
                        customer_contact=self.customer_contact_input.text(),
                        location=self.location,
                        tax_exempt=self.tax_exempt_check.isChecked(),
                        notes=self.notes_input.toPlainText()
                    )
                    
                    if self.applied_deal:
                        self.pos_manager.db.record_deal_application(
                            self.applied_deal['deal_id'], transaction_id, discount_amount
                        )
                except Exception as item_error:
                    logger.error("POSTab", f"Error processing item: {item_error}")
            
            # Show confirmation
            deal_text = f"\nDeal: {self.applied_deal['name']}" if self.applied_deal else ""
            QMessageBox.information(
                self, "Sale Complete",
                f"Sale processed!\n\nItems: {len(self.cart)}\nSubtotal: ${discounted_total:.2f}\nTax: ${tax_amount:.2f}\nTotal: ${final_total:.2f}{deal_text}"
            )
            
            # Clear cart
            self.clear_cart()
            self.load_recent_sales()
            self.load_products()
            
        except Exception as e:
            logger.error("POSTab", f"Error completing sale: {e}")
            QMessageBox.critical(self, "Error", f"Failed to process sale: {str(e)}")
    
    def clear_cart(self):
        """Clear the shopping cart"""
        self.cart = []
        self.applied_deal = None
        self.deals_combo.setCurrentIndex(0)
        self.customer_name_input.clear()
        self.customer_contact_input.clear()
        self.notes_input.clear()
        self.payment_method_input.setCurrentIndex(0)
        self.update_cart_display()
    
    def load_recent_sales(self):
        """Load recent sales"""
        logger.debug("POSTab", "Loading recent sales")
        try:
            transactions = self.pos_manager.get_all_transactions(limit=100)
            self.recent_sales_data = transactions  # Store for filtering
            self.display_recent_sales(transactions)
            
            # Update today's stats
            today_sales = 0
            for t in transactions:
                if not t.get('is_refunded'):
                    today_sales += t.get('total_amount', 0)
            
            self.today_sales_label.setText(f"${today_sales:.2f}")
            self.transaction_count_label.setText(str(len([t for t in transactions if not t.get('is_refunded')])))
            
        except Exception as e:
            logger.error("POSTab", f"Error loading recent sales: {e}")
    
    def display_recent_sales(self, transactions):
        """Display transactions in the table"""
        self.recent_sales_table.setRowCount(len(transactions))
        
        for row, transaction in enumerate(transactions):
            self.recent_sales_table.setItem(row, 0, QTableWidgetItem(transaction['created_at']))
            
            product = self.pos_manager.get_product(transaction['product_id'])
            product_name = product['name'] if product else "Unknown"
            self.recent_sales_table.setItem(row, 1, QTableWidgetItem(product_name))
            
            self.recent_sales_table.setItem(row, 2, QTableWidgetItem(str(transaction['quantity_sold'])))
            self.recent_sales_table.setItem(row, 3, QTableWidgetItem(f"${transaction['unit_price']:.2f}"))
            
            # Subtotal (before tax)
            subtotal = transaction.get('subtotal', (transaction['quantity_sold'] * transaction['unit_price']))
            self.recent_sales_table.setItem(row, 4, QTableWidgetItem(f"${subtotal:.2f}"))
            
            # Tax amount
            tax_amount = transaction.get('tax_amount', 0)
            self.recent_sales_table.setItem(row, 5, QTableWidgetItem(f"${tax_amount:.2f}"))
            
            # Total
            self.recent_sales_table.setItem(row, 6, QTableWidgetItem(f"${transaction['total_amount']:.2f}"))
    
    def filter_recent_sales(self):
        """Filter recent sales based on search input"""
        search_text = self.sales_search_input.text().lower()
        
        if not hasattr(self, 'recent_sales_data'):
            return
        
        # Filter transactions
        filtered = []
        for t in self.recent_sales_data:
            product = self.pos_manager.get_product(t['product_id'])
            product_name = product['name'].lower() if product else ""
            
            if (search_text in product_name or 
                search_text in t.get('customer_name', '').lower() or
                search_text in t.get('transaction_id', '').lower()):
                filtered.append(t)
        
        self.display_recent_sales(filtered)
    
    def load_inventory(self):
        """Load inventory status"""
        logger.debug("POSTab", "Loading inventory")
        try:
            inventory = self.pos_manager.get_inventory_status()
            self.inventory_table.setRowCount(len(inventory))
            
            for row, item in enumerate(inventory):
                self.inventory_table.setItem(row, 0, QTableWidgetItem(item['name']))
                self.inventory_table.setItem(row, 1, QTableWidgetItem(item['item_number'] or ''))
                self.inventory_table.setItem(row, 2, QTableWidgetItem(str(item['quantity_in_stock'])))
                self.inventory_table.setItem(row, 3, QTableWidgetItem(str(item['reorder_level'])))
                
                # Status
                if item['quantity_in_stock'] == 0:
                    status = "OUT"
                    item_widget = QTableWidgetItem(status)
                    item_widget.setBackground(QColor(255, 100, 100))
                elif item['quantity_in_stock'] <= item['reorder_level']:
                    status = "LOW"
                    item_widget = QTableWidgetItem(status)
                    item_widget.setBackground(QColor(255, 200, 0))
                else:
                    status = "OK"
                    item_widget = QTableWidgetItem(status)
                    item_widget.setBackground(QColor(100, 255, 100))
                self.inventory_table.setItem(row, 4, item_widget)
                
                self.inventory_table.setItem(row, 5, QTableWidgetItem(f"${item['total_value']:.2f}"))
        except Exception as e:
            logger.error("POSTab", f"Error loading inventory: {e}")
    
    def adjust_inventory(self):
        """Adjust inventory for a product"""
        products = self.pos_manager.get_all_products()
        if not products:
            QMessageBox.warning(self, "Warning", "No products available")
            return
        
        product_names = [p['name'] for p in products]
        product, ok = QInputDialog.getItem(self, "Select Product", "Product:", product_names)
        
        if ok and product:
            quantity, ok = QInputDialog.getInt(self, "Adjustment", "Quantity change:", 0, -999999, 999999)
            
            if ok:
                try:
                    prod = self.pos_manager.get_product_by_name(product)
                    if prod:
                        self.pos_manager.adjust_inventory(prod['product_id'], quantity, "manual")
                        self.load_inventory()
                        self.load_products()
                        QMessageBox.information(self, "Success", f"Inventory adjusted by {quantity}")
                        logger.info("POSTab", f"Inventory adjusted: {product} by {quantity}")
                except Exception as e:
                    logger.error("POSTab", f"Error adjusting inventory: {e}")
                    QMessageBox.critical(self, "Error", f"Failed to adjust inventory: {e}")
    
    def create_deal(self):
        """Create a new deal with flexible targeting options"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Create Deal")
        dialog.setGeometry(100, 100, 700, 800)
        
        layout = QFormLayout()
        
        # Deal name
        name_input = QLineEdit()
        layout.addRow("Deal Name:", name_input)
        
        # Description
        desc_input = QTextEdit()
        desc_input.setMaximumHeight(60)
        layout.addRow("Description:", desc_input)
        
        # Deal mechanism (discount vs BOGO)
        mechanism_combo = QComboBox()
        mechanism_combo.addItems(["discount", "bogo"])
        layout.addRow("Deal Type:", mechanism_combo)
        
        # === DISCOUNT FIELDS ===
        discount_label = QLabel("Discount Settings:")
        discount_label.setStyleSheet("font-weight: bold")
        layout.addRow(discount_label)
        
        # Discount value
        discount_input = QDoubleSpinBox()
        discount_input.setMinimum(0)
        discount_input.setMaximum(9999)
        discount_input.setValue(0)
        layout.addRow("Discount Value:", discount_input)
        
        # Discount type
        discount_type = QComboBox()
        discount_type.addItems(["percentage", "fixed"])
        layout.addRow("Discount Type (% or $):", discount_type)
        
        # === BOGO FIELDS ===
        bogo_label = QLabel("BOGO Settings (Buy X Get Y Free):")
        bogo_label.setStyleSheet("font-weight: bold")
        layout.addRow(bogo_label)
        
        # Buy quantity
        buy_qty_input = QSpinBox()
        buy_qty_input.setMinimum(1)
        buy_qty_input.setValue(1)
        layout.addRow("Buy Quantity:", buy_qty_input)
        
        # Get quantity
        get_qty_input = QSpinBox()
        get_qty_input.setMinimum(1)
        get_qty_input.setValue(1)
        layout.addRow("Get Free Quantity:", get_qty_input)
        
        # === TARGETING OPTIONS ===
        target_label = QLabel("Targeting Options (select at least one):")
        target_label.setStyleSheet("font-weight: bold")
        layout.addRow(target_label)
        
        # Product/Item selection
        products_input = QLineEdit()
        products_input.setPlaceholderText("Comma-separated product names or IDs")
        layout.addRow("Target Products:", products_input)
        
        # Item numbers
        item_numbers_input = QLineEdit()
        item_numbers_input.setPlaceholderText("Comma-separated item numbers (SKUs)")
        layout.addRow("Target Item Numbers:", item_numbers_input)
        
        # Tags
        tags_input = QLineEdit()
        tags_input.setPlaceholderText("Comma-separated tags")
        layout.addRow("Target Tags:", tags_input)
        
        # Categories
        categories_input = QLineEdit()
        categories_input.setPlaceholderText("Comma-separated categories")
        layout.addRow("Target Categories:", categories_input)
        
        # === PRICE RANGE ===
        price_label = QLabel("Price Range Targeting (optional):")
        price_label.setStyleSheet("font-weight: bold")
        layout.addRow(price_label)
        
        price_min_input = QDoubleSpinBox()
        price_min_input.setMinimum(0)
        price_min_input.setMaximum(99999)
        price_min_input.setValue(0)
        layout.addRow("Minimum Price ($):", price_min_input)
        
        price_max_input = QDoubleSpinBox()
        price_max_input.setMinimum(0)
        price_max_input.setMaximum(99999)
        price_max_input.setValue(99999)
        layout.addRow("Maximum Price ($):", price_max_input)
        
        # === DATES ===
        date_label = QLabel("Date Range (optional):")
        date_label.setStyleSheet("font-weight: bold")
        layout.addRow(date_label)
        
        start_date_input = QLineEdit()
        start_date_input.setPlaceholderText("YYYY-MM-DD HH:MM:SS")
        layout.addRow("Start Date:", start_date_input)
        
        end_date_input = QLineEdit()
        end_date_input.setPlaceholderText("YYYY-MM-DD HH:MM:SS")
        layout.addRow("End Date:", end_date_input)
        
        # Toggle visibility based on mechanism
        def toggle_mechanism_fields():
            is_discount = mechanism_combo.currentText() == "discount"
            discount_input.setEnabled(is_discount)
            discount_type.setEnabled(is_discount)
            buy_qty_input.setEnabled(not is_discount)
            get_qty_input.setEnabled(not is_discount)
        
        mechanism_combo.currentTextChanged.connect(toggle_mechanism_fields)
        toggle_mechanism_fields()
        
        # Buttons
        button_layout = QHBoxLayout()
        create_btn = QPushButton("Create Deal")
        cancel_btn = QPushButton("Cancel")
        
        button_layout.addWidget(create_btn)
        button_layout.addWidget(cancel_btn)
        layout.addRow(button_layout)
        
        dialog.setLayout(layout)
        
        def save_deal():
            try:
                if not name_input.text().strip():
                    QMessageBox.warning(dialog, "Error", "Deal name is required")
                    return
                
                mechanism = mechanism_combo.currentText()
                
                # Validate targeting
                has_targeting = (
                    products_input.text().strip() or
                    item_numbers_input.text().strip() or
                    tags_input.text().strip() or
                    categories_input.text().strip() or
                    (price_min_input.value() > 0 or price_max_input.value() < 99999)
                )
                
                if not has_targeting:
                    QMessageBox.warning(dialog, "Error", "At least one targeting option must be specified")
                    return
                
                # Parse product IDs/names
                product_ids = []
                if products_input.text().strip():
                    for item in products_input.text().split(','):
                        item = item.strip()
                        prod = self.pos_manager.get_product_by_item_number(item)
                        if not prod:
                            prod = self.pos_manager.get_product_by_name(item)
                        if prod:
                            product_ids.append(prod['product_id'])
                
                # Parse item numbers
                item_numbers = [i.strip().upper() for i in item_numbers_input.text().split(',') 
                               if i.strip()] if item_numbers_input.text() else []
                
                # Parse tags
                tags = [t.strip() for t in tags_input.text().split(',') 
                       if t.strip()] if tags_input.text() else []
                
                # Parse categories
                categories = [c.strip() for c in categories_input.text().split(',') 
                             if c.strip()] if categories_input.text() else []
                
                # Price range
                price_min = price_min_input.value() if price_min_input.value() > 0 else None
                price_max = price_max_input.value() if price_max_input.value() < 99999 else None
                
                # Validate mechanism-specific fields
                if mechanism == "discount":
                    if discount_input.value() == 0:
                        QMessageBox.warning(dialog, "Error", "Discount value must be greater than 0")
                        return
                else:  # bogo
                    if buy_qty_input.value() <= 0 or get_qty_input.value() <= 0:
                        QMessageBox.warning(dialog, "Error", "BOGO quantities must be positive")
                        return
                
                # Create deal
                deal_id = self.pos_manager.create_deal(
                    name=name_input.text(),
                    description=desc_input.toPlainText(),
                    deal_mechanism=mechanism,
                    discount_value=discount_input.value() if mechanism == "discount" else None,
                    discount_type=discount_type.currentText() if mechanism == "discount" else None,
                    bogo_buy_qty=buy_qty_input.value() if mechanism == "bogo" else None,
                    bogo_get_qty=get_qty_input.value() if mechanism == "bogo" else None,
                    product_ids=product_ids if product_ids else None,
                    tags=tags if tags else None,
                    categories=categories if categories else None,
                    item_numbers=item_numbers if item_numbers else None,
                    price_min=price_min,
                    price_max=price_max,
                    start_date=start_date_input.text() if start_date_input.text() else None,
                    end_date=end_date_input.text() if end_date_input.text() else None
                )
                
                QMessageBox.information(dialog, "Success", f"Deal created: {deal_id}")
                self.load_deals()
                dialog.accept()
                
            except Exception as e:
                logger.error("POSTab", f"Error creating deal: {e}")
                QMessageBox.critical(dialog, "Error", f"Failed to create deal: {e}")
        
        create_btn.clicked.connect(save_deal)
        cancel_btn.clicked.connect(dialog.reject)
        
        dialog.exec()
    
    def load_deals(self):
        """Load all deals into the table"""
        logger.debug("POSTab", "Loading deals")
        try:
            deals = self.pos_manager.get_all_deals()
            self.deals_table.setRowCount(len(deals))
            
            for row, deal in enumerate(deals):
                # Name
                self.deals_table.setItem(row, 0, QTableWidgetItem(deal['name']))
                
                # Type (mechanism)
                mechanism = deal['deal_mechanism']
                if mechanism == 'discount':
                    deal_type = f"Discount ({deal['discount_value']}{'%' if deal['discount_type'] == 'percentage' else '$'})"
                else:  # bogo
                    deal_type = f"BOGO (Buy {deal['bogo_buy_qty']} Get {deal['bogo_get_qty']})"
                self.deals_table.setItem(row, 1, QTableWidgetItem(deal_type))
                
                # Build targeting description
                targets = []
                if deal['product_ids']:
                    targets.append(f"Products: {len(deal['product_ids'])}")
                if deal['tags']:
                    targets.append(f"Tags: {', '.join(deal['tags'][:2])}")
                if deal['categories']:
                    targets.append(f"Categories: {', '.join(deal['categories'][:2])}")
                if deal['item_numbers']:
                    targets.append(f"Items: {', '.join(deal['item_numbers'][:2])}")
                if deal['price_min'] is not None or deal['price_max'] is not None:
                    price_range = f"Price: ${deal['price_min'] or '0'}-${deal['price_max'] or '∞'}"
                    targets.append(price_range)
                
                targeting_text = " | ".join(targets) if targets else "All Products"
                self.deals_table.setItem(row, 2, QTableWidgetItem(targeting_text))
                
                # Start date
                start = deal['start_date'] or "N/A"
                self.deals_table.setItem(row, 3, QTableWidgetItem(start))
                
                # End date
                end = deal['end_date'] or "N/A"
                self.deals_table.setItem(row, 4, QTableWidgetItem(end))
                
                # Actions
                action_btn = QPushButton("Deactivate" if deal['is_active'] else "View")
                if deal['is_active']:
                    action_btn.clicked.connect(lambda checked, d=deal: self.deactivate_deal(d['deal_id']))
                self.deals_table.setCellWidget(row, 5, action_btn)
            
            logger.info("POSTab", f"Loaded {len(deals)} deals")
        except Exception as e:
            logger.error("POSTab", f"Error loading deals: {e}")
    
    def deactivate_deal(self, deal_id: str):
        """Deactivate a deal"""
        try:
            self.pos_manager.deactivate_deal(deal_id)
            QMessageBox.information(self, "Success", "Deal deactivated")
            self.load_deals()
        except Exception as e:
            logger.error("POSTab", f"Error deactivating deal: {e}")
            QMessageBox.critical(self, "Error", f"Failed to deactivate deal: {e}")
    
    def load_report(self):
        """Load the selected report"""
        report_type = self.report_combo.currentText()
        logger.debug("POSTab", f"Loading report: {report_type}")
        
        try:
            if report_type == "Sales Summary":
                self.load_sales_summary_report()
            elif report_type == "Top Sellers":
                self.load_top_sellers_report()
            elif report_type == "Low Stock":
                self.load_low_stock_report()
            elif report_type == "Inventory Value":
                self.load_inventory_value_report()
        except Exception as e:
            logger.error("POSTab", f"Error loading report: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load report: {e}")
    
    def load_sales_summary_report(self):
        """Load sales summary report"""
        summary = self.pos_manager.get_sales_summary()
        
        self.report_table.setRowCount(1)
        self.report_table.setColumnCount(5)
        self.report_table.setHorizontalHeaderLabels(
            ["Total Transactions", "Total Qty Sold", "Total Revenue", "Avg Transaction", "Last Sale"]
        )
        
        self.report_table.setItem(0, 0, QTableWidgetItem(str(summary.get('total_transactions', 0))))
        self.report_table.setItem(0, 1, QTableWidgetItem(str(summary.get('total_quantity', 0))))
        self.report_table.setItem(0, 2, QTableWidgetItem(f"${summary.get('total_revenue', 0):.2f}"))
        self.report_table.setItem(0, 3, QTableWidgetItem(f"${summary.get('avg_transaction', 0):.2f}"))
        self.report_table.setItem(0, 4, QTableWidgetItem(str(summary.get('last_sale', ''))))
    
    def load_top_sellers_report(self):
        """Load top sellers report"""
        top_sellers = self.pos_manager.get_top_sellers(10)
        
        self.report_table.setRowCount(len(top_sellers))
        self.report_table.setColumnCount(4)
        self.report_table.setHorizontalHeaderLabels(["Product", "Qty Sold", "Revenue", "Current Stock"])
        
        for row, item in enumerate(top_sellers):
            self.report_table.setItem(row, 0, QTableWidgetItem(item['name']))
            self.report_table.setItem(row, 1, QTableWidgetItem(str(item['quantity_sold'])))
            self.report_table.setItem(row, 2, QTableWidgetItem(f"${item['total_revenue']:.2f}"))
            self.report_table.setItem(row, 3, QTableWidgetItem(str(item['current_stock'])))
    
    def load_low_stock_report(self):
        """Load low stock report"""
        low_stock = self.pos_manager.get_low_stock_products()
        
        self.report_table.setRowCount(len(low_stock))
        self.report_table.setColumnCount(4)
        self.report_table.setHorizontalHeaderLabels(["Product", "Item #", "Current", "Reorder Level"])
        
        for row, item in enumerate(low_stock):
            self.report_table.setItem(row, 0, QTableWidgetItem(item['name']))
            self.report_table.setItem(row, 1, QTableWidgetItem(item['item_number'] or ''))
            
            qty_item = QTableWidgetItem(str(item['current_stock']))
            qty_item.setBackground(QColor(255, 200, 0))
            self.report_table.setItem(row, 2, qty_item)
            
            self.report_table.setItem(row, 3, QTableWidgetItem(str(item['reorder_level'])))
    
    def load_inventory_value_report(self):
        """Load inventory value report"""
        inventory = self.pos_manager.get_inventory_status()
        
        self.report_table.setRowCount(len(inventory) + 1)
        self.report_table.setColumnCount(5)
        self.report_table.setHorizontalHeaderLabels(["Product", "Item #", "Qty", "Unit Price", "Total Value"])
        
        total_value = 0
        for row, item in enumerate(inventory):
            self.report_table.setItem(row, 0, QTableWidgetItem(item['name']))
            self.report_table.setItem(row, 1, QTableWidgetItem(item['item_number'] or ''))
            self.report_table.setItem(row, 2, QTableWidgetItem(str(item['quantity_in_stock'])))
            self.report_table.setItem(row, 3, QTableWidgetItem(f"${item['price']:.2f}"))
            self.report_table.setItem(row, 4, QTableWidgetItem(f"${item['total_value']:.2f}"))
            total_value += item['total_value']
        
        # Total row
        total_row = len(inventory)
        self.report_table.setItem(total_row, 3, QTableWidgetItem("TOTAL:"))
        total_item = QTableWidgetItem(f"${total_value:.2f}")
        total_item.setBackground(QColor(200, 200, 200))
        font = QFont()
        font.setBold(True)
        total_item.setFont(font)
        self.report_table.setItem(total_row, 4, total_item)
    
    def showEvent(self, event):
        """Called when tab is shown"""
        super().showEvent(event)
        self.load_products()
        self.load_recent_sales()
        self.load_inventory()
