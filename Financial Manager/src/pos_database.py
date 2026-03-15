"""
POS (Point of Sale) Database Module
Handles SQLite database operations for product inventory and sales transactions
"""

import sqlite3
import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import sys

try:
    from .app_paths import get_app_data_dir
except ImportError:
    from app_paths import get_app_data_dir

from assets.Logger import Logger
logger = Logger()


class POSDatabase:
    """Manages SQLite database operations for POS system"""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize POS database manager"""
        logger.debug("POSDatabase", "Initializing POSDatabase")
        if db_path is None:
            data_dir = get_app_data_dir()
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, 'financial_manager.db')
            logger.debug("POSDatabase", f"Using default database path: {db_path}")
        
        self.db_path = db_path
        self.connection = None
        logger.info("POSDatabase", f"Initializing database at {db_path}")
        self.initialize_database()
    
    def connect(self):
        """Establish database connection"""
        if self.connection is None:
            logger.debug("POSDatabase", f"Establishing database connection to {self.db_path}")
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
            logger.info("POSDatabase", "Database connection established")
        return self.connection
    
    def close(self):
        """Close database connection"""
        if self.connection:
            logger.debug("POSDatabase", "Closing database connection")
            self.connection.close()
            self.connection = None
            logger.info("POSDatabase", "Database connection closed")
    
    def execute_query(self, query: str, params: Tuple = ()) -> sqlite3.Cursor:
        """Execute a database query"""
        logger.debug("POSDatabase", f"Executing query: {query[:100]}..." if len(query) > 100 else f"Executing query: {query}")
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor
    
    def commit(self):
        """Commit changes to database"""
        if self.connection:
            logger.debug("POSDatabase", "Committing database changes")
            self.connection.commit()
            logger.debug("POSDatabase", "Changes committed successfully")
    
    def initialize_database(self):
        """Create POS tables if they don't exist"""
        logger.debug("POSDatabase", "Initializing POS database tables")
        conn = self.connect()
        cursor = conn.cursor()
        
        # Products table
        logger.debug("POSDatabase", "Creating products table")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pos_products (
                product_id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                item_number TEXT UNIQUE,
                upc TEXT UNIQUE,
                category TEXT,
                product_tax_type TEXT DEFAULT 'standard',
                tags TEXT,
                price REAL DEFAULT 0.0,
                sale_price REAL,
                purchase_price REAL,
                fees REAL DEFAULT 0.0,
                restrictions TEXT,
                quantity_in_stock INTEGER DEFAULT 0,
                reorder_level INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Inventory table
        logger.debug("POSDatabase", "Creating inventory table")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pos_inventory (
                inventory_id TEXT PRIMARY KEY,
                product_id TEXT NOT NULL,
                quantity_change INTEGER NOT NULL,
                transaction_type TEXT NOT NULL,
                reference_id TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES pos_products(product_id)
            )
        ''')
        
        # Sales transactions table
        logger.debug("POSDatabase", "Creating sales transactions table")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pos_transactions (
                transaction_id TEXT PRIMARY KEY,
                product_id TEXT NOT NULL,
                quantity_sold INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                fees REAL DEFAULT 0.0,
                subtotal REAL NOT NULL,
                tax_rate REAL DEFAULT 0.0,
                tax_amount REAL DEFAULT 0.0,
                tax_exempt BOOLEAN DEFAULT 0,
                total_amount REAL NOT NULL,
                location TEXT,
                payment_method TEXT,
                customer_name TEXT,
                customer_contact TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_refunded BOOLEAN DEFAULT 0,
                refund_transaction_id TEXT,
                FOREIGN KEY (product_id) REFERENCES pos_products(product_id)
            )
        ''')
        
        # Tax rates by location table
        logger.debug("POSDatabase", "Creating tax rates table")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pos_tax_rates (
                tax_rate_id TEXT PRIMARY KEY,
                location TEXT NOT NULL UNIQUE,
                rate REAL NOT NULL,
                description TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Deals/Promotions table
        logger.debug("POSDatabase", "Creating deals table")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pos_deals (
                deal_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                deal_mechanism TEXT NOT NULL,
                discount_value REAL,
                discount_type TEXT,
                bogo_buy_qty INTEGER,
                bogo_get_qty INTEGER,
                product_ids TEXT,
                tags TEXT,
                categories TEXT,
                item_numbers TEXT,
                price_min REAL,
                price_max REAL,
                start_date TIMESTAMP,
                end_date TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Product Tax Categories table
        logger.debug("POSDatabase", "Creating product tax categories table")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pos_product_tax_categories (
                tax_category_id TEXT PRIMARY KEY,
                category_name TEXT NOT NULL UNIQUE,
                description TEXT,
                tax_rate_modifier REAL DEFAULT 0.0,
                is_exempt BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Rental Items table
        logger.debug("POSDatabase", "Creating rentals table")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pos_rentals (
                rental_id TEXT PRIMARY KEY,
                product_id TEXT NOT NULL,
                customer_name TEXT NOT NULL,
                rental_start_date TIMESTAMP NOT NULL,
                rental_end_date TIMESTAMP NOT NULL,
                daily_rate REAL NOT NULL,
                total_cost REAL DEFAULT 0.0,
                paid_amount REAL DEFAULT 0.0,
                status TEXT DEFAULT 'active',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES pos_products(product_id)
            )
        ''')
        
        # Deal applications log table
        logger.debug("POSDatabase", "Creating deal applications table")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pos_deal_applications (
                application_id TEXT PRIMARY KEY,
                deal_id TEXT NOT NULL,
                transaction_id TEXT NOT NULL,
                discount_amount REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (deal_id) REFERENCES pos_deals(deal_id),
                FOREIGN KEY (transaction_id) REFERENCES pos_transactions(transaction_id)
            )
        ''')
        
        # Create indices for performance
        logger.debug("POSDatabase", "Creating database indices")
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_pos_products_name ON pos_products(name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_pos_products_item_number ON pos_products(item_number)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_pos_inventory_product ON pos_inventory(product_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_pos_transactions_product ON pos_transactions(product_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_pos_transactions_date ON pos_transactions(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_pos_deals_active ON pos_deals(is_active)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_pos_deals_dates ON pos_deals(start_date, end_date)')
        
        conn.commit()
        logger.info("POSDatabase", "POS database tables initialized successfully")
    
    # Product Operations
    def add_product(self, name: str, description: str = "", item_number: str = "", 
                   upc: str = "", tags: str = "", price: float = 0.0, sale_price: Optional[float] = None,
                   purchase_price: float = 0.0, fees: float = 0.0, restrictions: str = "",
                   product_tax_type: str = "standard") -> str:
        """Add a new product to the database"""
        product_id = str(uuid.uuid4())
        logger.debug("POSDatabase", f"Adding product: {name}")
        
        cursor = self.execute_query('''
            INSERT INTO pos_products 
            (product_id, name, description, item_number, upc, tags, price, sale_price, 
             purchase_price, fees, restrictions, product_tax_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (product_id, name, description, item_number, upc, tags, price, sale_price, 
              purchase_price, fees, restrictions, product_tax_type))
        self.commit()
        logger.info("POSDatabase", f"Product added successfully with ID: {product_id}")
        return product_id
    
    def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get a product by ID"""
        logger.debug("POSDatabase", f"Fetching product: {product_id}")
        cursor = self.execute_query('SELECT * FROM pos_products WHERE product_id = ?', (product_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    
    def get_product_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a product by name"""
        logger.debug("POSDatabase", f"Fetching product by name: {name}")
        cursor = self.execute_query('SELECT * FROM pos_products WHERE name = ?', (name,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    
    def get_product_by_item_number(self, item_number: str) -> Optional[Dict[str, Any]]:
        """Get a product by item number"""
        logger.debug("POSDatabase", f"Fetching product by item number: {item_number}")
        cursor = self.execute_query('SELECT * FROM pos_products WHERE item_number = ?', (item_number,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    
    def get_product_by_upc(self, upc: str) -> Optional[Dict[str, Any]]:
        """Get a product by UPC (barcode)"""
        logger.debug("POSDatabase", f"Fetching product by UPC: {upc}")
        cursor = self.execute_query('SELECT * FROM pos_products WHERE upc = ?', (upc,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    
    def get_all_products(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all products"""
        logger.debug("POSDatabase", "Fetching all products")
        if active_only:
            cursor = self.execute_query('SELECT * FROM pos_products WHERE is_active = 1 ORDER BY name')
        else:
            cursor = self.execute_query('SELECT * FROM pos_products ORDER BY name')
        return [dict(row) for row in cursor.fetchall()]
    
    def update_product(self, product_id: str, **kwargs) -> bool:
        """Update product information"""
        logger.debug("POSDatabase", f"Updating product: {product_id}")
        
        allowed_fields = {'name', 'description', 'item_number', 'category', 'tags', 
                         'price', 'sale_price', 'purchase_price', 'fees', 'restrictions',
                         'quantity_in_stock', 'reorder_level', 'is_active'}
        fields_to_update = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not fields_to_update:
            logger.warning("POSDatabase", "No valid fields to update")
            return True  # Return True since there's nothing to update
        
        fields_to_update['updated_at'] = datetime.now().isoformat()
        
        set_clause = ', '.join([f'{k} = ?' for k in fields_to_update.keys()])
        values = list(fields_to_update.values()) + [product_id]
        
        cursor = self.execute_query(f'UPDATE pos_products SET {set_clause} WHERE product_id = ?', values)
        self.commit()
        logger.info("POSDatabase", f"Product {product_id} updated successfully")
        return True
    
    def delete_product(self, product_id: str) -> bool:
        """Soft delete a product (mark as inactive)"""
        logger.debug("POSDatabase", f"Deleting product: {product_id}")
        return self.update_product(product_id, is_active=False)

    # Inventory Operations
    def update_inventory(self, product_id: str, quantity_change: int, 
                        transaction_type: str = "manual", reference_id: str = "", 
                        notes: str = "") -> str:
        """Update inventory for a product"""
        inventory_id = str(uuid.uuid4())
        logger.debug("POSDatabase", f"Updating inventory for product {product_id}: change={quantity_change}")
        
        # Get current inventory
        product = self.get_product(product_id)
        if not product:
            logger.error("POSDatabase", f"Product not found: {product_id}")
            raise ValueError(f"Product {product_id} not found")
        
        current_qty = product['quantity_in_stock']
        new_qty = current_qty + quantity_change
        
        # Prevent negative inventory (but allow 0)
        if new_qty < 0:
            new_qty = 0
            logger.warning("POSDatabase", f"Inventory adjustment capped at 0 for {product_id}")
        
        # Record the transaction
        cursor = self.execute_query('''
            INSERT INTO pos_inventory 
            (inventory_id, product_id, quantity_change, transaction_type, reference_id, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (inventory_id, product_id, quantity_change, transaction_type, reference_id, notes))
        
        # Update the product's inventory
        self.update_product(product_id, quantity_in_stock=new_qty)
        self.commit()
        
        logger.info("POSDatabase", f"Inventory updated: {product_id} -> {new_qty} units")
        return inventory_id
    
    def get_inventory_history(self, product_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get inventory change history for a product"""
        logger.debug("POSDatabase", f"Fetching inventory history for product: {product_id}")
        cursor = self.execute_query(
            'SELECT * FROM pos_inventory WHERE product_id = ? ORDER BY created_at DESC LIMIT ?',
            (product_id, limit)
        )
        return [dict(row) for row in cursor.fetchall()]
    
    # Sales Operations
    def record_sale(self, product_id: str, quantity: int, unit_price: float, 
                   fees: float = 0.0, payment_method: str = "", 
                   customer_name: str = "", customer_contact: str = "", 
                   tax_amount: float = 0.0, tax_rate: float = 0.0, 
                   location: str = "", tax_exempt: bool = False, notes: str = "") -> str:
        """Record a sale transaction"""
        transaction_id = str(uuid.uuid4())
        logger.debug("POSDatabase", f"Recording sale: product={product_id}, qty={quantity}, tax_exempt={tax_exempt}")
        
        # Get the product
        product = self.get_product(product_id)
        if not product:
            logger.error("POSDatabase", f"Product not found: {product_id}")
            raise ValueError(f"Product {product_id} not found")
        
        # Calculate subtotal and total
        subtotal = (quantity * unit_price) + fees
        total_amount = subtotal + tax_amount
        
        # Record the transaction
        cursor = self.execute_query('''
            INSERT INTO pos_transactions 
            (transaction_id, product_id, quantity_sold, unit_price, fees, subtotal, tax_rate, tax_amount, 
             tax_exempt, total_amount, location, payment_method, customer_name, customer_contact, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (transaction_id, product_id, quantity, unit_price, fees, subtotal, tax_rate, tax_amount,
              tax_exempt, total_amount, location, payment_method, customer_name, customer_contact, notes))
        
        # Update inventory (deduct sold quantity, but don't go negative)
        self.update_inventory(product_id, -quantity, transaction_type="sale", 
                            reference_id=transaction_id, notes=f"Sale transaction")
        
        self.commit()
        logger.info("POSDatabase", f"Sale recorded: {transaction_id}, total: {total_amount}")
        return transaction_id
    
    def get_transaction(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """Get a transaction by ID"""
        logger.debug("POSDatabase", f"Fetching transaction: {transaction_id}")
        cursor = self.execute_query('SELECT * FROM pos_transactions WHERE transaction_id = ?', (transaction_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    
    def get_all_transactions(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all transactions with pagination"""
        logger.debug("POSDatabase", f"Fetching transactions: limit={limit}, offset={offset}")
        cursor = self.execute_query(
            'SELECT * FROM pos_transactions ORDER BY created_at DESC LIMIT ? OFFSET ?',
            (limit, offset)
        )
        return [dict(row) for row in cursor.fetchall()]
    
    def get_product_transactions(self, product_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all transactions for a specific product"""
        logger.debug("POSDatabase", f"Fetching transactions for product: {product_id}")
        cursor = self.execute_query(
            'SELECT * FROM pos_transactions WHERE product_id = ? ORDER BY created_at DESC LIMIT ?',
            (product_id, limit)
        )
        return [dict(row) for row in cursor.fetchall()]
    
    def refund_transaction(self, transaction_id: str, notes: str = "") -> str:
        """Record a refund for a transaction"""
        transaction = self.get_transaction(transaction_id)
        if not transaction:
            logger.error("POSDatabase", f"Transaction not found: {transaction_id}")
            raise ValueError(f"Transaction {transaction_id} not found")
        
        if transaction['is_refunded']:
            logger.warning("POSDatabase", f"Transaction already refunded: {transaction_id}")
            raise ValueError("Transaction already refunded")
        
        # Create refund transaction
        refund_id = str(uuid.uuid4())
        logger.debug("POSDatabase", f"Creating refund for transaction: {transaction_id}")
        
        cursor = self.execute_query('''
            INSERT INTO pos_transactions 
            (transaction_id, product_id, quantity_sold, unit_price, fees, total_amount,
             payment_method, customer_name, customer_contact, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (refund_id, transaction['product_id'], -transaction['quantity_sold'], 
              transaction['unit_price'], -transaction['fees'], -transaction['total_amount'],
              transaction['payment_method'], transaction['customer_name'], 
              transaction['customer_contact'], f"Refund: {notes}"))
        
        # Mark original as refunded
        self.execute_query(
            'UPDATE pos_transactions SET is_refunded = 1, refund_transaction_id = ? WHERE transaction_id = ?',
            (refund_id, transaction_id)
        )
        
        # Restore inventory
        self.update_inventory(transaction['product_id'], transaction['quantity_sold'],
                            transaction_type="refund", reference_id=transaction_id,
                            notes=f"Refund for transaction {transaction_id}")
        
        self.commit()
        logger.info("POSDatabase", f"Refund recorded: {refund_id} for transaction {transaction_id}")
        return refund_id
    
    # Reporting Operations
    def get_sales_summary(self, product_id: Optional[str] = None) -> Dict[str, Any]:
        """Get sales summary"""
        logger.debug("POSDatabase", f"Generating sales summary for product: {product_id or 'all'}")
        
        if product_id:
            cursor = self.execute_query('''
                SELECT COUNT(*) as total_transactions,
                       SUM(quantity_sold) as total_quantity,
                       SUM(total_amount) as total_revenue,
                       AVG(total_amount) as avg_transaction,
                       MIN(created_at) as first_sale,
                       MAX(created_at) as last_sale
                FROM pos_transactions 
                WHERE product_id = ? AND is_refunded = 0
            ''', (product_id,))
        else:
            cursor = self.execute_query('''
                SELECT COUNT(*) as total_transactions,
                       SUM(quantity_sold) as total_quantity,
                       SUM(total_amount) as total_revenue,
                       AVG(total_amount) as avg_transaction,
                       MIN(created_at) as first_sale,
                       MAX(created_at) as last_sale
                FROM pos_transactions 
                WHERE is_refunded = 0
            ''')
        
        row = cursor.fetchone()
        return dict(row) if row else {}
    
    def get_inventory_status(self) -> List[Dict[str, Any]]:
        """Get inventory status for all products"""
        logger.debug("POSDatabase", "Generating inventory status report")
        cursor = self.execute_query('''
            SELECT product_id, name, item_number, quantity_in_stock, reorder_level, 
                   price, sale_price, quantity_in_stock * price as total_value
            FROM pos_products 
            WHERE is_active = 1 
            ORDER BY quantity_in_stock ASC
        ''')
        return [dict(row) for row in cursor.fetchall()]    
    # Deal/Promotion Operations
    def add_deal(self, name: str, description: str = "", deal_mechanism: str = "discount",
                discount_value: float = 0.0, discount_type: str = "percentage",
                bogo_buy_qty: Optional[int] = None, bogo_get_qty: Optional[int] = None,
                product_ids: Optional[List[str]] = None, tags: Optional[List[str]] = None,
                categories: Optional[List[str]] = None, item_numbers: Optional[List[str]] = None,
                price_min: Optional[float] = None, price_max: Optional[float] = None,
                start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
        """Add a new deal/promotion
        
        Args:
            deal_mechanism: 'discount' or 'bogo'
            discount_value/type: For 'discount' mechanism (e.g., 10%, $5 off)
            bogo_buy_qty/get_qty: For 'bogo' mechanism (e.g., buy 1 get 1 free)
            product_ids: List of product IDs to target
            tags: List of tags to target
            categories: List of product categories
            item_numbers: List of item numbers
            price_min/price_max: Price range to target
        """
        deal_id = str(uuid.uuid4())
        logger.debug("POSDatabase", f"Adding deal: {name} ({deal_mechanism})")
        
        product_ids_str = json.dumps(product_ids) if product_ids else None
        tags_str = json.dumps(tags) if tags else None
        categories_str = json.dumps(categories) if categories else None
        item_numbers_str = json.dumps(item_numbers) if item_numbers else None
        
        self.execute_query('''
            INSERT INTO pos_deals 
            (deal_id, name, description, deal_mechanism, discount_value, discount_type,
             bogo_buy_qty, bogo_get_qty, product_ids, tags, categories, item_numbers,
             price_min, price_max, start_date, end_date, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ''', (deal_id, name, description, deal_mechanism, discount_value, discount_type,
              bogo_buy_qty, bogo_get_qty, product_ids_str, tags_str, categories_str, item_numbers_str,
              price_min, price_max, start_date, end_date))
        
        self.commit()
        logger.info("POSDatabase", f"Deal added: {deal_id} - {name}")
        return deal_id
    
    def get_deal(self, deal_id: str) -> Optional[Dict[str, Any]]:
        """Get a deal by ID"""
        logger.debug("POSDatabase", f"Fetching deal: {deal_id}")
        cursor = self.execute_query('SELECT * FROM pos_deals WHERE deal_id = ?', (deal_id,))
        row = cursor.fetchone()
        if row:
            deal = dict(row)
            deal['product_ids'] = json.loads(deal['product_ids']) if deal['product_ids'] else []
            deal['tags'] = json.loads(deal['tags']) if deal['tags'] else []
            return deal
        return None
    
    def get_active_deals(self) -> List[Dict[str, Any]]:
        """Get all active deals for current date/time"""
        logger.debug("POSDatabase", "Fetching active deals")
        cursor = self.execute_query('''
            SELECT * FROM pos_deals 
            WHERE is_active = 1 
            AND (start_date IS NULL OR start_date <= CURRENT_TIMESTAMP)
            AND (end_date IS NULL OR end_date >= CURRENT_TIMESTAMP)
            ORDER BY created_at DESC
        ''')
        deals = []
        for row in cursor.fetchall():
            deal = dict(row)
            deal['product_ids'] = json.loads(deal['product_ids']) if deal['product_ids'] else []
            deal['tags'] = json.loads(deal['tags']) if deal['tags'] else []
            deals.append(deal)
        return deals
    
    def get_all_deals(self) -> List[Dict[str, Any]]:
        """Get all deals (active and inactive)"""
        logger.debug("POSDatabase", "Fetching all deals")
        cursor = self.execute_query('SELECT * FROM pos_deals ORDER BY created_at DESC')
        deals = []
        for row in cursor.fetchall():
            deal = dict(row)
            deal['product_ids'] = json.loads(deal['product_ids']) if deal['product_ids'] else []
            deal['tags'] = json.loads(deal['tags']) if deal['tags'] else []
            deals.append(deal)
        return deals
    
    def update_deal(self, deal_id: str, **kwargs) -> bool:
        """Update a deal"""
        logger.debug("POSDatabase", f"Updating deal: {deal_id}")
        
        # Convert lists to JSON
        if 'product_ids' in kwargs:
            kwargs['product_ids'] = json.dumps(kwargs['product_ids'])
        if 'tags' in kwargs:
            kwargs['tags'] = json.dumps(kwargs['tags'])
        
        # Build update query
        updates = []
        values = []
        for key, value in kwargs.items():
            updates.append(f"{key} = ?")
            values.append(value)
        
        updates.append("updated_at = ?")
        values.append(datetime.now().isoformat())
        values.append(deal_id)
        
        query = f"UPDATE pos_deals SET {', '.join(updates)} WHERE deal_id = ?"
        self.execute_query(query, tuple(values))
        self.commit()
        logger.info("POSDatabase", f"Deal updated: {deal_id}")
        return True
    
    def deactivate_deal(self, deal_id: str) -> bool:
        """Deactivate a deal"""
        logger.debug("POSDatabase", f"Deactivating deal: {deal_id}")
        self.execute_query(
            'UPDATE pos_deals SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE deal_id = ?',
            (deal_id,)
        )
        self.commit()
        logger.info("POSDatabase", f"Deal deactivated: {deal_id}")
        return True
    
    def get_applicable_deals(self, product_id: str, tags: Optional[List[str]] = None, 
                           item_number: Optional[str] = None, price: Optional[float] = None,
                           category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get deals applicable to a product with multiple targeting criteria
        
        Args:
            product_id: Product ID to check
            tags: Product tags
            item_number: Product item number
            price: Product price to check against price ranges
            category: Product category
        """
        logger.debug("POSDatabase", f"Finding applicable deals for product: {product_id}")
        
        # Get all active deals
        deals = self.get_active_deals()
        applicable = []
        
        for deal in deals:
            matches = False
            
            # Check product_ids targeting
            if deal['product_ids'] and product_id in deal['product_ids']:
                matches = True
            
            # Check tags targeting
            if not matches and tags and deal['tags']:
                if any(tag in deal['tags'] for tag in tags):
                    matches = True
            
            # Check item numbers targeting
            if not matches and item_number and deal['item_numbers']:
                if item_number in deal['item_numbers']:
                    matches = True
            
            # Check category targeting
            if not matches and category and deal['categories']:
                if category in deal['categories']:
                    matches = True
            
            # Check price range targeting
            if not matches and price is not None and (deal['price_min'] is not None or deal['price_max'] is not None):
                price_matches = True
                if deal['price_min'] is not None and price < deal['price_min']:
                    price_matches = False
                if deal['price_max'] is not None and price > deal['price_max']:
                    price_matches = False
                if price_matches:
                    matches = True
            
            if matches:
                applicable.append(deal)
        
        logger.debug("POSDatabase", f"Found {len(applicable)} applicable deals")
        return applicable
    
    def record_deal_application(self, deal_id: str, transaction_id: str, discount_amount: float) -> str:
        """Record that a deal was applied to a transaction"""
        application_id = str(uuid.uuid4())
        logger.debug("POSDatabase", f"Recording deal application: {deal_id} -> {transaction_id}")
        
        self.execute_query('''
            INSERT INTO pos_deal_applications 
            (application_id, deal_id, transaction_id, discount_amount, created_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (application_id, deal_id, transaction_id, discount_amount))
        
        self.commit()
        logger.info("POSDatabase", f"Deal application recorded: {application_id}")
        return application_id
    
    # Product Tax Categories
    def add_product_tax_category(self, category_name: str, description: str = "", 
                                tax_rate_modifier: float = 0.0, is_exempt: bool = False) -> str:
        """Add a product tax category"""
        category_id = str(uuid.uuid4())
        logger.debug("POSDatabase", f"Adding tax category: {category_name}")
        
        self.execute_query('''
            INSERT INTO pos_product_tax_categories 
            (tax_category_id, category_name, description, tax_rate_modifier, is_exempt)
            VALUES (?, ?, ?, ?, ?)
        ''', (category_id, category_name, description, tax_rate_modifier, is_exempt))
        
        self.commit()
        logger.info("POSDatabase", f"Tax category added: {category_id}")
        return category_id
    
    def get_product_tax_category(self, category_name: str) -> Optional[Dict[str, Any]]:
        """Get a product tax category by name"""
        logger.debug("POSDatabase", f"Fetching tax category: {category_name}")
        cursor = self.execute_query(
            'SELECT * FROM pos_product_tax_categories WHERE category_name = ? AND is_active = 1',
            (category_name,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_all_product_tax_categories(self) -> List[Dict[str, Any]]:
        """Get all active product tax categories"""
        logger.debug("POSDatabase", "Fetching all tax categories")
        cursor = self.execute_query(
            'SELECT * FROM pos_product_tax_categories WHERE is_active = 1 ORDER BY category_name'
        )
        return [dict(row) for row in cursor.fetchall()]
    
    # Rental Operations
    def add_rental(self, product_id: str, customer_name: str, rental_start_date: str,
                   rental_end_date: str, daily_rate: float, notes: str = "") -> str:
        """Create a new rental"""
        rental_id = str(uuid.uuid4())
        logger.debug("POSDatabase", f"Adding rental for product: {product_id}")
        
        self.execute_query('''
            INSERT INTO pos_rentals
            (rental_id, product_id, customer_name, rental_start_date, rental_end_date, daily_rate, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (rental_id, product_id, customer_name, rental_start_date, rental_end_date, daily_rate, notes))
        
        self.commit()
        logger.info("POSDatabase", f"Rental created: {rental_id}")
        return rental_id
    
    def get_rental(self, rental_id: str) -> Optional[Dict[str, Any]]:
        """Get a rental by ID"""
        logger.debug("POSDatabase", f"Fetching rental: {rental_id}")
        cursor = self.execute_query('SELECT * FROM pos_rentals WHERE rental_id = ?', (rental_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_active_rentals(self) -> List[Dict[str, Any]]:
        """Get all active rentals"""
        logger.debug("POSDatabase", "Fetching active rentals")
        cursor = self.execute_query(
            "SELECT * FROM pos_rentals WHERE status = 'active' ORDER BY rental_end_date"
        )
        return [dict(row) for row in cursor.fetchall()]
    
    def update_rental_status(self, rental_id: str, status: str, paid_amount: float = 0.0) -> bool:
        """Update rental status (active, returned, extended)"""
        logger.debug("POSDatabase", f"Updating rental {rental_id} to status: {status}")
        
        self.execute_query('''
            UPDATE pos_rentals SET status = ?, paid_amount = ?, updated_at = CURRENT_TIMESTAMP
            WHERE rental_id = ?
        ''', (status, paid_amount, rental_id))
        
        self.commit()
        logger.info("POSDatabase", f"Rental {rental_id} updated to {status}")
        return True
    
    def get_rentals_by_customer(self, customer_name: str) -> List[Dict[str, Any]]:
        """Get all rentals for a customer"""
        logger.debug("POSDatabase", f"Fetching rentals for customer: {customer_name}")
        cursor = self.execute_query(
            'SELECT * FROM pos_rentals WHERE customer_name = ? ORDER BY rental_start_date DESC',
            (customer_name,)
        )
        return [dict(row) for row in cursor.fetchall()]