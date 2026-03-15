# Point of Sale (POS) System Documentation

## Overview

The Financial Manager now includes a full-featured Point of Sale system that manages product inventory, processes sales transactions, and provides comprehensive reporting and analytics.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    UI Layer (pos_tab.py)                 │
│  ┌──────────────┬──────────────┬──────────────┐          │
│  │  Products    │   Sales      │  Inventory   │ Reports  │
│  │  Management  │  Processing  │  Tracking    │          │
│  └──────────────┴──────────────┴──────────────┘          │
└─────────────────────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│        Business Logic Layer (pos_manager.py)            │
│  • Product CRUD operations                              │
│  • Inventory management                                 │
│  • Sales processing                                     │
│  • Reporting and analytics                              │
└─────────────────────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│         Database Layer (pos_database.py)                │
│  • SQLite database operations                           │
│  • Product table management                             │
│  • Inventory tracking                                   │
│  • Sales transactions                                   │
└─────────────────────────────────────────────────────────┘
```

## Database Schema

### pos_products Table
Stores all product information:

```sql
product_id          TEXT PRIMARY KEY      -- Unique UUID
name                TEXT NOT NULL UNIQUE  -- Product name
description         TEXT                  -- Product description
item_number         TEXT UNIQUE           -- SKU or item number
category            TEXT                  -- Product category
tags                TEXT                  -- Comma-separated tags
price               REAL                  -- Regular selling price
sale_price          REAL                  -- Optional sale price
purchase_price      REAL                  -- Cost to purchase
fees                REAL                  -- Associated fees
restrictions        TEXT                  -- Any restrictions
quantity_in_stock   INTEGER               -- Current inventory level
reorder_level       INTEGER               -- Minimum inventory threshold
is_active           BOOLEAN               -- Soft delete flag
created_at          TIMESTAMP             -- Creation timestamp
updated_at          TIMESTAMP             -- Last modification timestamp
```

### pos_inventory Table
Tracks all inventory changes:

```sql
inventory_id        TEXT PRIMARY KEY      -- Unique UUID
product_id          TEXT NOT NULL         -- Foreign key to products
quantity_change     INTEGER               -- Amount changed (+/-)
transaction_type    TEXT                  -- Type (sale, restock, manual, etc.)
reference_id        TEXT                  -- Link to related transaction
notes               TEXT                  -- Additional notes
created_at          TIMESTAMP             -- Timestamp of change
```

### pos_transactions Table
Records all sales:

```sql
transaction_id      TEXT PRIMARY KEY      -- Unique UUID
product_id          TEXT NOT NULL         -- Foreign key to products
quantity_sold       INTEGER               -- Number of units sold
unit_price          REAL                  -- Price per unit at time of sale
fees                REAL                  -- Transaction fees
total_amount        REAL                  -- Total sale amount
payment_method      TEXT                  -- Payment type (cash, card, etc.)
customer_name       TEXT                  -- Customer name (optional)
customer_contact    TEXT                  -- Customer contact (optional)
notes               TEXT                  -- Additional notes
is_refunded         BOOLEAN               -- Whether transaction is refunded
refund_transaction_id TEXT                -- Link to refund transaction
created_at          TIMESTAMP             -- Transaction timestamp
```

## Core Classes

### POSDatabase (`src/pos_database.py`)

Low-level database operations for the POS system.

**Key Methods:**

#### Product Operations
- `add_product(...)` - Create a new product
- `get_product(product_id)` - Retrieve product by ID
- `get_product_by_name(name)` - Find product by name
- `get_product_by_item_number(item_number)` - Find by SKU
- `get_all_products(active_only=True)` - List all products
- `update_product(product_id, **kwargs)` - Update product fields
- `delete_product(product_id)` - Soft delete (mark inactive)

#### Inventory Operations
- `update_inventory(product_id, quantity_change, ...)` - Adjust stock levels
  - **Important**: Inventory cannot go negative (capped at 0)
  - Tracks all changes in the `pos_inventory` table
  - Supports sales even at 0 inventory (stays at 0)
- `get_inventory_history(product_id)` - View change history
- `get_inventory_status()` - Get all product inventory levels

#### Sales Operations
- `record_sale(product_id, quantity, unit_price, ...)` - Process a sale
  - Automatically deducts from inventory
  - Calculates total with fees
- `get_transaction(transaction_id)` - Retrieve sale details
- `get_all_transactions(limit, offset)` - List recent sales
- `get_product_transactions(product_id)` - Sales by product
- `refund_transaction(transaction_id, ...)` - Create refund
  - Marks original as refunded
  - Restores inventory
  - Creates negative transaction record

#### Reporting
- `get_sales_summary(product_id=None)` - Sales statistics
- `get_inventory_status()` - Current inventory report

### POSManager (`src/pos_manager.py`)

High-level business logic and validation.

**Key Methods:**

#### Product Management
```python
# Add a new product with validation
product_id = pos_manager.add_product(
    name="Coffee",
    description="Fresh brewed coffee",
    item_number="COFFEE-001",
    price=3.50,
    sale_price=3.00,
    purchase_price=1.50,
    fees=0.25,
    restrictions="",
    initial_quantity=100,
    reorder_level=20
)
```

#### Sales Processing
```python
# Process a sale
transaction_id, total = pos_manager.process_sale(
    product_id=product_id,
    quantity=2,
    payment_method="cash",
    customer_name="John Doe",
    customer_contact="555-1234",
    notes="Regular customer"
)
```

#### Inventory Management
```python
# Adjust inventory manually
pos_manager.adjust_inventory(
    product_id=product_id,
    quantity=50,
    transaction_type="restock"
)

# Check low stock products
low_stock = pos_manager.get_low_stock_products()
```

#### Reporting
```python
# Get sales summary
summary = pos_manager.get_sales_summary()

# Get top selling products
top_sellers = pos_manager.get_top_sellers(limit=10)

# Get daily sales
daily = pos_manager.get_daily_sales(days=1)
```

### POSTab (`ui/pos_tab.py`)

User interface for the POS system with 4 main tabs:

#### 1. **Products Tab**
- View all active products in a searchable table
- Add new products via dialog
- Edit existing products
- Shows current price, sale price, and stock levels
- Color-coded status indicators:
  - GREEN: Normal stock
  - YELLOW: Low stock (below reorder level)
  - RED: Out of stock

#### 2. **Sales Tab**
- Quick product selection via dropdown
- One-click sale processing
- Customer information capture (optional)
- Recent sales history display
- Shows quantity, unit price, and total amount

#### 3. **Inventory Tab**
- Real-time inventory status for all products
- Manual inventory adjustments
- Stock level monitoring
- Total inventory value calculation
- Status indicators for reordering

#### 4. **Reports Tab**
- Sales Summary: Total transactions, revenue, average sale
- Top Sellers: Best-selling products by quantity
- Low Stock: Products below reorder level
- Inventory Value: Total value of inventory by product

## Features

### ✅ Product Management
- Create products with comprehensive attributes
- Support for regular and sale prices
- Track purchase price and fees
- Add product restrictions and tags
- Categorization support

### ✅ Inventory Control
- Real-time stock level tracking
- Automatic inventory updates on sales
- **Zero-inventory sales support**: Can sell items even if quantity is 0, but inventory stays at 0 (never goes negative)
- Inventory change history with audit trail
- Reorder level alerts
- Manual inventory adjustments
- Stock transaction types: sale, restock, damaged, lost, manual

### ✅ Sales Processing
- Quick sale entry for any product
- Multiple payment methods (cash, card, check, other)
- Per-transaction fees included in totals
- Optional customer information capture
- Uses sale price if available, otherwise regular price

### ✅ Refunds
- Full transaction refunds supported
- Automatic inventory restoration
- Refund tracking and audit trail
- Links original and refund transactions

### ✅ Reporting
- Comprehensive sales summaries
- Top performing products
- Low stock alerts
- Inventory value assessment
- Daily/weekly/monthly sales trends

## Important Inventory Behavior

### Zero-Inventory Sales Rule

The POS system allows selling products even when inventory is at 0:

```python
# These operations are allowed:
pos_manager.process_sale(product_id, quantity=5)  # Even if qty_in_stock = 0

# Result:
# - Sale is recorded
# - Inventory STAYS at 0 (doesn't go negative to -5)
# - Transaction is logged normally
```

This is useful for:
- Pre-orders
- Special orders
- Dropshipping
- Backordered items

### Inventory Tracking Rules

1. **Can never go negative**: Automatically capped at 0
2. **All changes logged**: Every transaction recorded
3. **Audit trail**: Transaction type and reference tracking
4. **Refunds restore stock**: Properly reverses sales

## Usage Examples

### Example 1: Complete Workflow
```python
from src.pos_manager import POSManager

pos = POSManager()

# Add products
coffee_id = pos.add_product(
    name="Coffee",
    price=3.50,
    initial_quantity=100
)

tea_id = pos.add_product(
    name="Tea",
    price=2.50,
    initial_quantity=75
)

# Process sales
txn1, total1 = pos.process_sale(coffee_id, 2, payment_method="cash")
txn2, total2 = pos.process_sale(tea_id, 1, payment_method="card")

# Check inventory
coffee = pos.get_product(coffee_id)
print(f"Coffee in stock: {coffee['quantity_in_stock']}")  # 98

# Get reports
summary = pos.get_sales_summary()
top_sellers = pos.get_top_sellers()
```

### Example 2: Low Stock Management
```python
# Check for low stock
low_stock = pos.get_low_stock_products()
for item in low_stock:
    print(f"REORDER: {item['name']} - Current: {item['current_stock']}, Level: {item['reorder_level']}")

# Restock items
pos.adjust_inventory(coffee_id, 100, transaction_type="restock")
```

### Example 3: Refunds
```python
# Process refund
refund_id = pos.refund_sale(
    transaction_id="txn-123",
    notes="Customer requested return"
)

# Check that inventory was restored
coffee = pos.get_product(coffee_id)
print(f"Inventory after refund: {coffee['quantity_in_stock']}")
```

## Testing

Comprehensive test suite included: `test_pos_system.py`

Run tests:
```bash
python test_pos_system.py
```

**18 tests covering:**
- Product CRUD operations
- Inventory updates and constraints
- Zero-inventory sales
- Refund processing
- Sales summary reporting
- Top sellers reporting
- Low stock identification
- Complete workflow integration

All tests pass successfully ✓

## Integration with Financial Manager

The POS system is fully integrated as a new tab in the main Financial Manager application:

1. Access via "Point of Sale" tab in main window
2. Seamlessly integrates with existing database
3. Uses same logging system as other modules
4. Follows same UI patterns and conventions

## File Structure

```
src/
  pos_database.py      -- Low-level database operations (420 lines)
  pos_manager.py       -- Business logic and validation (450 lines)
  
ui/
  pos_tab.py           -- User interface implementation (900+ lines)
  
test_pos_system.py     -- Comprehensive test suite (450+ lines)

README_POS.md          -- This documentation
```

## Performance Considerations

- SQLite database with proper indexing
- Efficient queries with pagination support
- Transaction batching for bulk operations
- Lazy loading of product lists
- Cached inventory calculations

## Future Enhancements

Potential features for expansion:
- Barcode scanning integration
- Multi-location inventory sync
- Customer loyalty program
- Receipt printing
- Tax calculation
- Bulk product import/export
- Discount/promotion system
- Staff commission tracking
- Advanced analytics dashboard

## Support

For issues or questions about the POS system:
1. Check the test suite for usage examples
2. Review the docstrings in the code
3. Check the application logs (financial_tracker.log)
4. Examine the database schema in pos_database.py

---

**Version:** 1.0.0  
**Last Updated:** December 27, 2025  
**Status:** Production Ready
