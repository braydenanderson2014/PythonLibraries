"""
POS Manager Module
High-level management of products, inventory, and sales operations
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from .pos_database import POSDatabase
from .pos_tax_manager import POSTaxManager
from .product_tax_manager import ProductTaxManager
from .rental_manager import RentalManager
from assets.Logger import Logger

logger = Logger()


class POSManager:
    """Manages POS operations for the Financial Manager"""
    
    def __init__(self, db=None):
        """Initialize POS Manager"""
        logger.debug("POSManager", "Initializing POSManager")
        self.db = db or POSDatabase()
        self.tax_manager = POSTaxManager(self.db)
        self.product_tax_manager = ProductTaxManager(self.db)
        self.rental_manager = RentalManager(self.db)
        logger.info("POSManager", "POSManager initialized successfully")
    
    # Product Management
    def add_product(self, name: str, description: str = "", item_number: str = "",
                   upc: str = "", tags: str = "", price: float = 0.0, sale_price: Optional[float] = None,
                   purchase_price: float = 0.0, fees: float = 0.0,
                   restrictions: str = "", initial_quantity: int = 0, 
                   reorder_level: int = 0, product_tax_type: str = "standard") -> str:
        """
        Add a new product to the inventory
        
        Args:
            name: Product name
            description: Product description
            item_number: SKU or item number
            tags: Comma-separated tags
            price: Regular price
            sale_price: Optional sale price
            purchase_price: Cost to purchase
            fees: Any additional fees
            restrictions: Any restrictions on the product
            initial_quantity: Starting inventory quantity
            reorder_level: Inventory level at which to reorder
        
        Returns:
            product_id of the newly created product
        """
        logger.debug("POSManager", f"Adding new product: {name}")
        
        # Validate inputs
        if not name or not name.strip():
            logger.error("POSManager", "Product name is required")
            raise ValueError("Product name is required")
        
        if price < 0:
            logger.error("POSManager", "Price cannot be negative")
            raise ValueError("Price cannot be negative")
        
        if sale_price is not None and sale_price < 0:
            logger.error("POSManager", "Sale price cannot be negative")
            raise ValueError("Sale price cannot be negative")
        
        # Create product
        product_id = self.db.add_product(
            name=name.strip(),
            description=description,
            item_number=item_number,
            upc=upc,
            tags=tags,
            price=price,
            sale_price=sale_price,
            purchase_price=purchase_price,
            fees=fees,
            restrictions=restrictions,
            product_tax_type=product_tax_type
        )
        
        # Update reorder level if provided
        if reorder_level > 0:
            self.db.update_product(product_id, reorder_level=reorder_level)
        
        # Add initial inventory
        if initial_quantity > 0:
            self.db.update_inventory(
                product_id, 
                initial_quantity,
                transaction_type="initial_stock",
                notes="Initial stock entry"
            )
        
        logger.info("POSManager", f"Product added: {product_id} - {name}")
        return product_id
    
    def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get product details by ID"""
        logger.debug("POSManager", f"Fetching product: {product_id}")
        return self.db.get_product(product_id)
    
    def get_product_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get product details by name"""
        logger.debug("POSManager", f"Fetching product by name: {name}")
        return self.db.get_product_by_name(name)
    
    def get_product_by_upc(self, upc: str) -> Optional[Dict[str, Any]]:
        """Get product details by UPC (barcode)"""
        logger.debug("POSManager", f"Fetching product by UPC: {upc}")
        return self.db.get_product_by_upc(upc)
    
    def get_product_by_item_number(self, item_number: str) -> Optional[Dict[str, Any]]:
        """Get product details by item number"""
        logger.debug("POSManager", f"Fetching product by item number: {item_number}")
        return self.db.get_product_by_item_number(item_number)
    
    def get_all_products(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all products"""
        logger.debug("POSManager", "Fetching all products")
        return self.db.get_all_products(active_only)
    
    def update_product(self, product_id: str, **kwargs) -> bool:
        """Update product information"""
        logger.debug("POSManager", f"Updating product: {product_id}")
        
        # Validate numeric fields
        if 'price' in kwargs and kwargs['price'] < 0:
            raise ValueError("Price cannot be negative")
        if 'sale_price' in kwargs and kwargs['sale_price'] is not None and kwargs['sale_price'] < 0:
            raise ValueError("Sale price cannot be negative")
        if 'purchase_price' in kwargs and kwargs['purchase_price'] < 0:
            raise ValueError("Purchase price cannot be negative")
        if 'fees' in kwargs and kwargs['fees'] < 0:
            raise ValueError("Fees cannot be negative")
        
        return self.db.update_product(product_id, **kwargs)
    
    def delete_product(self, product_id: str) -> bool:
        """Delete (deactivate) a product"""
        logger.debug("POSManager", f"Deleting product: {product_id}")
        return self.db.delete_product(product_id)
    
    # Inventory Management
    def adjust_inventory(self, product_id: str, quantity: int, 
                        transaction_type: str = "manual", 
                        reference_id: str = "", notes: str = "") -> str:
        """
        Adjust inventory for a product
        
        Args:
            product_id: Product to adjust
            quantity: Quantity to add/remove (negative for removal)
            transaction_type: Type of transaction (manual, damaged, lost, etc.)
            reference_id: Reference to another transaction
            notes: Additional notes
        
        Returns:
            inventory_id of the transaction
        """
        logger.debug("POSManager", f"Adjusting inventory: {product_id}, qty={quantity}")
        
        if not self.db.get_product(product_id):
            logger.error("POSManager", f"Product not found: {product_id}")
            raise ValueError(f"Product {product_id} not found")
        
        return self.db.update_inventory(
            product_id, quantity, transaction_type, reference_id, notes
        )
    
    def get_inventory_history(self, product_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get inventory change history"""
        logger.debug("POSManager", f"Fetching inventory history: {product_id}")
        return self.db.get_inventory_history(product_id, limit)
    
    def get_inventory_status(self) -> List[Dict[str, Any]]:
        """Get current inventory status for all products"""
        logger.debug("POSManager", "Fetching inventory status")
        return self.db.get_inventory_status()
    
    def is_low_stock(self, product_id: str) -> bool:
        """Check if product is below reorder level"""
        product = self.db.get_product(product_id)
        if not product:
            return False
        return product['quantity_in_stock'] <= product['reorder_level']
    
    # Sales Operations
    def process_sale(self, product_id: str, quantity: int, 
                    payment_method: str = "cash",
                    customer_name: str = "", customer_contact: str = "",
                    notes: str = "") -> Tuple[str, float]:
        """
        Process a sale transaction
        
        Args:
            product_id: Product being sold
            quantity: Quantity to sell
            payment_method: Payment method (cash, card, check, etc.)
            customer_name: Name of customer
            customer_contact: Customer contact info
            notes: Additional notes
        
        Returns:
            Tuple of (transaction_id, total_amount)
        """
        logger.debug("POSManager", f"Processing sale: {product_id}, qty={quantity}")
        
        # Get product
        product = self.db.get_product(product_id)
        if not product:
            logger.error("POSManager", f"Product not found: {product_id}")
            raise ValueError(f"Product {product_id} not found")
        
        if not product['is_active']:
            logger.error("POSManager", f"Product is not active: {product_id}")
            raise ValueError(f"Product is not active")
        
        if quantity <= 0:
            logger.error("POSManager", "Quantity must be greater than 0")
            raise ValueError("Quantity must be greater than 0")
        
        # Use sale price if available, otherwise use regular price
        unit_price = product['sale_price'] if product['sale_price'] else product['price']
        fees = product['fees']
        
        # Record transaction
        transaction_id = self.db.record_sale(
            product_id=product_id,
            quantity=quantity,
            unit_price=unit_price,
            fees=fees,
            payment_method=payment_method,
            customer_name=customer_name,
            customer_contact=customer_contact,
            notes=notes
        )
        
        # Calculate total
        total = (quantity * unit_price) + fees
        
        logger.info("POSManager", f"Sale processed: {transaction_id}, total: {total}")
        return transaction_id, total
    
    def get_transaction(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """Get transaction details"""
        logger.debug("POSManager", f"Fetching transaction: {transaction_id}")
        return self.db.get_transaction(transaction_id)
    
    def get_all_transactions(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all transactions"""
        logger.debug("POSManager", f"Fetching transactions: limit={limit}, offset={offset}")
        return self.db.get_all_transactions(limit, offset)
    
    def get_product_sales(self, product_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all sales for a specific product"""
        logger.debug("POSManager", f"Fetching sales for product: {product_id}")
        return self.db.get_product_transactions(product_id, limit)
    
    def refund_sale(self, transaction_id: str, notes: str = "") -> str:
        """
        Process a refund for a sale
        
        Args:
            transaction_id: Original transaction to refund
            notes: Refund reason
        
        Returns:
            refund_transaction_id
        """
        logger.debug("POSManager", f"Processing refund for transaction: {transaction_id}")
        return self.db.refund_transaction(transaction_id, notes)
    
    # Deal/Promotion Management
    def create_deal(self, name: str, description: str = "", deal_mechanism: str = "discount",
                   discount_value: float = 0.0, discount_type: str = "percentage",
                   bogo_buy_qty: Optional[int] = None, bogo_get_qty: Optional[int] = None,
                   product_ids: Optional[List[str]] = None, tags: Optional[List[str]] = None,
                   categories: Optional[List[str]] = None, item_numbers: Optional[List[str]] = None,
                   price_min: Optional[float] = None, price_max: Optional[float] = None,
                   start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
        """
        Create a new deal/promotion
        
        Args:
            name: Deal name
            description: Deal description
            deal_mechanism: 'discount' or 'bogo' (Buy One Get One)
            discount_value: Discount amount or percentage (for discount mechanism)
            discount_type: 'percentage' or 'fixed' (for discount mechanism)
            bogo_buy_qty: How many to buy (for bogo mechanism)
            bogo_get_qty: How many free/discounted (for bogo mechanism)
            product_ids: List of product IDs this deal applies to
            tags: List of product tags this deal applies to
            categories: List of categories this deal applies to
            item_numbers: List of item numbers this deal applies to
            price_min: Minimum price (inclusive) for price range targeting
            price_max: Maximum price (inclusive) for price range targeting
            start_date: When the deal starts (ISO format)
            end_date: When the deal ends (ISO format)
        
        Returns:
            deal_id
        """
        logger.debug("POSManager", f"Creating deal: {name} ({deal_mechanism})")
        
        if deal_mechanism not in ["discount", "bogo"]:
            raise ValueError("Deal mechanism must be 'discount' or 'bogo'")
        
        if deal_mechanism == "discount":
            if discount_value < 0:
                raise ValueError("Discount value cannot be negative")
            if discount_type not in ["percentage", "fixed"]:
                raise ValueError("Discount type must be 'percentage' or 'fixed'")
            if discount_type == "percentage" and discount_value > 100:
                raise ValueError("Percentage discount cannot exceed 100%")
        
        elif deal_mechanism == "bogo":
            if not bogo_buy_qty or not bogo_get_qty:
                raise ValueError("BOGO deals require buy_qty and get_qty")
            if bogo_buy_qty <= 0 or bogo_get_qty <= 0:
                raise ValueError("Quantities must be positive")
        
        if price_min is not None and price_max is not None:
            if price_min > price_max:
                raise ValueError("price_min cannot be greater than price_max")
        
        return self.db.add_deal(
            name, description, deal_mechanism, discount_value, discount_type,
            bogo_buy_qty, bogo_get_qty, product_ids, tags, categories, item_numbers,
            price_min, price_max, start_date, end_date
        )
    
    def get_deal(self, deal_id: str) -> Optional[Dict[str, Any]]:
        """Get deal details"""
        logger.debug("POSManager", f"Fetching deal: {deal_id}")
        return self.db.get_deal(deal_id)
    
    def get_active_deals(self) -> List[Dict[str, Any]]:
        """Get all active deals"""
        logger.debug("POSManager", "Fetching active deals")
        return self.db.get_active_deals()
    
    def get_all_deals(self) -> List[Dict[str, Any]]:
        """Get all deals"""
        logger.debug("POSManager", "Fetching all deals")
        return self.db.get_all_deals()
    
    def update_deal(self, deal_id: str, **kwargs) -> bool:
        """Update a deal"""
        logger.debug("POSManager", f"Updating deal: {deal_id}")
        return self.db.update_deal(deal_id, **kwargs)
    
    def deactivate_deal(self, deal_id: str) -> bool:
        """Deactivate a deal"""
        logger.debug("POSManager", f"Deactivating deal: {deal_id}")
        return self.db.deactivate_deal(deal_id)
    
    # Product Tax Management
    def get_product_tax_categories(self) -> List[str]:
        """Get all available product tax categories"""
        logger.debug("POSManager", "Fetching product tax categories")
        return self.product_tax_manager.get_category_names()
    
    def calculate_tax_with_product_type(self, amount: float, base_tax_rate: float,
                                       product_tax_type: str = "standard") -> float:
        """Calculate tax considering product tax category"""
        logger.debug("POSManager", 
                    f"Calculating tax with product type: amount={amount}, rate={base_tax_rate}, type={product_tax_type}")
        return self.product_tax_manager.calculate_tax_with_category(amount, base_tax_rate, product_tax_type)
    
    def is_product_tax_exempt(self, product_tax_type: str) -> bool:
        """Check if product tax type is exempt"""
        return self.product_tax_manager.is_category_exempt(product_tax_type)
    
    # Rental Management
    def create_rental(self, product_id: str, customer_name: str,
                     start_date: str, end_date: str, daily_rate: float,
                     notes: str = "") -> Optional[str]:
        """Create a rental"""
        logger.debug("POSManager", f"Creating rental for product: {product_id}")
        return self.rental_manager.create_rental(product_id, customer_name, start_date, end_date, daily_rate, notes)
    
    def get_rental(self, rental_id: str) -> Optional[Dict[str, Any]]:
        """Get rental details"""
        logger.debug("POSManager", f"Fetching rental: {rental_id}")
        return self.rental_manager.get_rental(rental_id)
    
    def get_active_rentals(self) -> List[Dict[str, Any]]:
        """Get all active rentals"""
        logger.debug("POSManager", "Fetching active rentals")
        return self.rental_manager.get_active_rentals()
    
    def get_customer_rentals(self, customer_name: str) -> List[Dict[str, Any]]:
        """Get rentals for a customer"""
        logger.debug("POSManager", f"Fetching rentals for customer: {customer_name}")
        return self.rental_manager.get_customer_rentals(customer_name)
    
    def calculate_rental_cost(self, rental_id: str) -> Optional[Dict[str, float]]:
        """Calculate rental cost"""
        logger.debug("POSManager", f"Calculating rental cost: {rental_id}")
        return self.rental_manager.calculate_rental_cost(rental_id)
    
    def return_rental(self, rental_id: str, paid_amount: float = 0.0) -> bool:
        """Return a rental"""
        logger.debug("POSManager", f"Returning rental: {rental_id}")
        return self.rental_manager.return_rental(rental_id, paid_amount)
    
    def get_rental_summary(self, rental_id: str) -> Optional[Dict[str, Any]]:
        """Get rental summary with all details"""
        logger.debug("POSManager", f"Getting rental summary: {rental_id}")
        return self.rental_manager.get_rental_summary(rental_id)
    
    def get_applicable_deals(self, product_id: str, tags: Optional[List[str]] = None,
                           item_number: Optional[str] = None, price: Optional[float] = None,
                           category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get deals applicable to a product with multiple targeting criteria"""
        logger.debug("POSManager", f"Finding applicable deals for product: {product_id}")
        return self.db.get_applicable_deals(product_id, tags, item_number, price, category)
    
    def calculate_deal_discount(self, deal: Dict[str, Any], quantity: int, unit_price: float) -> float:
        """Calculate discount amount from a deal
        
        Args:
            deal: Deal dictionary
            quantity: Number of items
            unit_price: Price per item
        
        Returns:
            Discount amount (positive number representing savings)
        """
        if deal['deal_mechanism'] == 'discount':
            if deal['discount_type'] == 'percentage':
                return (quantity * unit_price) * (deal['discount_value'] / 100)
            else:  # fixed
                return deal['discount_value'] * quantity
        
        elif deal['deal_mechanism'] == 'bogo':
            # Buy X Get Y free logic
            buy_qty = deal['bogo_buy_qty']
            get_qty = deal['bogo_get_qty']
            
            if buy_qty == 0:
                return 0
            
            # Calculate how many complete "buy X get Y" sets we have
            complete_sets = quantity // (buy_qty + get_qty)
            remainder = quantity % (buy_qty + get_qty)
            
            # Free items from complete sets
            free_items = complete_sets * get_qty
            
            # Additional free items from remainder
            if remainder > buy_qty:
                free_items += remainder - buy_qty
            
            return free_items * unit_price
        
        return 0.0
    
    # Reporting
    def get_sales_summary(self, product_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get sales summary
        
        Args:
            product_id: If provided, get summary for specific product; else all
        
        Returns:
            Dictionary with sales statistics
        """
        logger.debug("POSManager", f"Generating sales summary for: {product_id or 'all'}")
        return self.db.get_sales_summary(product_id)
    
    def get_daily_sales(self, days: int = 1) -> Dict[str, Any]:
        """Get daily sales summary"""
        logger.debug("POSManager", f"Generating daily sales summary: {days} days")
        
        summary = self.db.get_sales_summary()
        transactions = self.db.get_all_transactions(limit=10000)
        
        # Filter by date
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_transactions = [
            t for t in transactions 
            if datetime.fromisoformat(t['created_at']) >= cutoff_date
            and not t['is_refunded']
        ]
        
        total_quantity = sum(t['quantity_sold'] for t in recent_transactions)
        total_revenue = sum(t['total_amount'] for t in recent_transactions)
        
        return {
            'days': days,
            'transaction_count': len(recent_transactions),
            'total_quantity': total_quantity,
            'total_revenue': total_revenue,
            'avg_transaction': total_revenue / len(recent_transactions) if recent_transactions else 0
        }
    
    def get_top_sellers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top selling products"""
        logger.debug("POSManager", f"Fetching top {limit} selling products")
        
        products = self.db.get_all_products()
        product_sales = []
        
        for product in products:
            summary = self.db.get_sales_summary(product['product_id'])
            if summary.get('total_quantity', 0) > 0:
                product_sales.append({
                    'product_id': product['product_id'],
                    'name': product['name'],
                    'quantity_sold': summary.get('total_quantity', 0),
                    'total_revenue': summary.get('total_revenue', 0),
                    'current_stock': product['quantity_in_stock']
                })
        
        # Sort by quantity sold
        product_sales.sort(key=lambda x: x['quantity_sold'], reverse=True)
        return product_sales[:limit]
    
    def get_low_stock_products(self) -> List[Dict[str, Any]]:
        """Get products below reorder level"""
        logger.debug("POSManager", "Fetching low stock products")
        
        products = self.db.get_all_products()
        low_stock = [
            {
                'product_id': p['product_id'],
                'name': p['name'],
                'item_number': p['item_number'],
                'current_stock': p['quantity_in_stock'],
                'reorder_level': p['reorder_level']
            }
            for p in products
            if p['quantity_in_stock'] <= p['reorder_level']
        ]
        
        return low_stock    
    # Tax Management
    def calculate_tax(self, amount: float, location: Optional[str] = None, 
                     tax_preferences: Optional[Dict[str, bool]] = None) -> float:
        """
        Calculate tax for a transaction amount
        
        Args:
            amount: Pre-tax amount
            location: Location/state for tax lookup. If None, uses default
            tax_preferences: Dict with 'state', 'local', 'federal' keys for tax types
        
        Returns:
            Tax amount
        """
        logger.debug("POSManager", f"Calculating tax: amount={amount}, location={location}, preferences={tax_preferences}")
        
        # If tax preferences provided, use them; otherwise get tax rate directly
        if tax_preferences:
            # Use TaxService for more detailed tax breakdown
            try:
                from services.tax_service import TaxService
                tax_data = TaxService.get_location_taxes(
                    location or "US",
                    include_state=tax_preferences.get('include_state_tax', True),
                    include_local=tax_preferences.get('include_local_tax', True),
                    include_federal=tax_preferences.get('include_federal_tax', False)
                )
                if tax_data:
                    tax_rate = tax_data['combined_rate']
                else:
                    tax_rate = self.get_tax_rate(location)
            except Exception as e:
                logger.warning("POSManager", f"Error using TaxService: {e}, falling back to default")
                tax_rate = self.get_tax_rate(location)
        else:
            tax_rate = self.get_tax_rate(location)
        
        return self.tax_manager.calculate_tax(amount, tax_rate)
    
    def get_tax_rate(self, location: Optional[str] = None) -> float:
        """
        Get the current tax rate for a location
        
        Args:
            location: Location/state code (e.g., 'CA', 'NY'). If None, uses default
        
        Returns:
            Tax rate as decimal (e.g., 0.08 for 8%)
        """
        logger.debug("POSManager", f"Getting tax rate for location: {location}")
        return self.tax_manager.get_tax_rate(location)
    
    def set_default_tax_rate(self, rate: float) -> bool:
        """
        Set the default tax rate for the business
        
        Args:
            rate: Tax rate as decimal (e.g., 0.08 for 8%)
        
        Returns:
            True if successful
        """
        if rate < 0 or rate > 1:
            logger.error("POSManager", "Tax rate must be between 0 and 1")
            raise ValueError("Tax rate must be between 0 and 1")
        
        logger.debug("POSManager", f"Setting default tax rate to {rate}")
        return self.tax_manager.set_default_tax_rate(rate)
    
    def add_location_tax_rate(self, location: str, rate: float) -> bool:
        """
        Add or update tax rate for a specific location
        
        Args:
            location: Location code (e.g., 'CA', 'NY', 'NYC')
            rate: Tax rate as decimal (e.g., 0.08 for 8%)
        
        Returns:
            True if successful
        """
        if not location or not location.strip():
            logger.error("POSManager", "Location code is required")
            raise ValueError("Location code is required")
        
        if rate < 0 or rate > 1:
            logger.error("POSManager", "Tax rate must be between 0 and 1")
            raise ValueError("Tax rate must be between 0 and 1")
        
        logger.debug("POSManager", f"Adding tax rate for {location}: {rate}")
        return self.tax_manager.add_location_tax_rate(location.strip(), rate)
    
    def reload_tax_rates(self):
        """Reload all tax rates from the database (call after making changes)"""
        logger.info("POSManager", "Reloading tax rates from database")
        self.tax_manager.reload_tax_rates()
    
    def get_all_tax_rates(self) -> Dict[str, float]:
        """
        Get all configured tax rates by location
        
        Returns:
            Dictionary of location -> tax rate
        """
        logger.debug("POSManager", "Fetching all tax rates")
        return self.tax_manager.get_all_tax_rates()
    
    def process_sale_with_tax(self, product_id: str, quantity: int,
                             payment_method: str = "cash",
                             customer_name: str = "", customer_contact: str = "",
                             location: Optional[str] = None,
                             tax_exempt: bool = False,
                             notes: str = "") -> Tuple[str, float, float, float]:
        """
        Process a sale transaction with automatic tax calculation
        
        Args:
            product_id: Product being sold
            quantity: Quantity to sell
            payment_method: Payment method (cash, card, check, etc.)
            customer_name: Name of customer
            customer_contact: Customer contact info
            location: Location for tax lookup (optional)
            tax_exempt: Whether this transaction is tax-exempt
            notes: Additional notes
        
        Returns:
            Tuple of (transaction_id, subtotal, tax_amount, total_amount)
        """
        logger.debug("POSManager", f"Processing sale with tax: {product_id}, qty={quantity}, tax_exempt={tax_exempt}")
        
        # Get product
        product = self.db.get_product(product_id)
        if not product:
            logger.error("POSManager", f"Product not found: {product_id}")
            raise ValueError(f"Product {product_id} not found")
        
        if not product['is_active']:
            logger.error("POSManager", f"Product is not active: {product_id}")
            raise ValueError(f"Product is not active")
        
        if quantity <= 0:
            logger.error("POSManager", "Quantity must be greater than 0")
            raise ValueError("Quantity must be greater than 0")
        
        # Use sale price if available, otherwise use regular price
        unit_price = product['sale_price'] if product['sale_price'] else product['price']
        fees = product['fees']
        
        # Calculate subtotal
        subtotal = (quantity * unit_price) + fees
        
        # Get tax rate for location
        tax_rate = self.get_tax_rate(location) if not tax_exempt else 0.0
        
        # Calculate tax (skip if tax-exempt)
        if tax_exempt:
            tax_amount = 0.0
        else:
            tax_amount = self.calculate_tax(subtotal, location)
        
        # Calculate total
        total_amount = subtotal + tax_amount
        
        # Record transaction
        transaction_id = self.db.record_sale(
            product_id=product_id,
            quantity=quantity,
            unit_price=unit_price,
            fees=fees,
            tax_rate=tax_rate * 100,  # Convert to percentage for storage
            tax_amount=tax_amount,
            tax_exempt=tax_exempt,
            location=location,
            payment_method=payment_method,
            customer_name=customer_name,
            customer_contact=customer_contact,
            notes=notes
        )
        
        logger.info("POSManager", f"Sale with tax processed: {transaction_id}, total: {total_amount}, tax_exempt: {tax_exempt}")
        return transaction_id, subtotal, tax_amount, total_amount