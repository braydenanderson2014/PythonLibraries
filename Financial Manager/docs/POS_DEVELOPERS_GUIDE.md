# POS System - Developer's Guide

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                  UI Layer (PyQt6)                   │
│              pos_tab.py (900+ lines)                │
│  ┌──────────────────────────────────────────────┐  │
│  │  Products | Sales | Inventory | Reports      │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
                        △
                        │
                   Uses (depends on)
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│              Business Logic Layer                   │
│            pos_manager.py (450 lines)               │
│  • Product management with validation               │
│  • Inventory control with constraints               │
│  • Sales processing and refunds                     │
│  • Analytics and reporting                          │
└─────────────────────────────────────────────────────┘
                        △
                        │
                   Uses (depends on)
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│              Database Layer (SQLite3)               │
│            pos_database.py (420 lines)              │
│  • Low-level SQL operations                         │
│  • Schema management                                │
│  • Query execution                                  │
│  • Transaction management                           │
└─────────────────────────────────────────────────────┘
                        △
                        │
                   Uses (depends on)
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│              SQLite Database                        │
│         financial_manager.db                        │
│  • pos_products table                               │
│  • pos_inventory table                              │
│  • pos_transactions table                           │
└─────────────────────────────────────────────────────┘
```

---

## Code Structure

### 1. Database Layer (pos_database.py)

**Responsibility**: Direct SQLite operations

**Key Classes**:
```python
class POSDatabase:
    def __init__(self, db_path: Optional[str] = None)
    def connect(self) -> sqlite3.Connection
    def execute_query(self, query: str, params: Tuple) -> sqlite3.Cursor
    def commit(self)
```

**Product Methods**:
```python
def add_product(name, description, ...) -> str
def get_product(product_id) -> Optional[Dict]
def get_product_by_name(name) -> Optional[Dict]
def get_all_products(active_only=True) -> List[Dict]
def update_product(product_id, **kwargs) -> bool
def delete_product(product_id) -> bool
```

**Inventory Methods**:
```python
def update_inventory(product_id, quantity_change, ...) -> str
def get_inventory_history(product_id) -> List[Dict]
def get_inventory_status() -> List[Dict]
```

**Sales Methods**:
```python
def record_sale(product_id, quantity, unit_price, ...) -> str
def get_transaction(transaction_id) -> Optional[Dict]
def get_all_transactions(limit, offset) -> List[Dict]
def get_product_transactions(product_id) -> List[Dict]
def refund_transaction(transaction_id, notes) -> str
```

**Reporting Methods**:
```python
def get_sales_summary(product_id=None) -> Dict
def get_inventory_status() -> List[Dict]
```

---

### 2. Business Logic Layer (pos_manager.py)

**Responsibility**: Business rules, validation, abstraction

**Key Classes**:
```python
class POSManager:
    def __init__(self, db: POSDatabase = None)
```

**Important Design Patterns**:

1. **Validation First**
   ```python
   def add_product(self, name: str, ...):
       if not name or not name.strip():
           raise ValueError("Product name is required")
       if price < 0:
           raise ValueError("Price cannot be negative")
   ```

2. **Inventory Constraints**
   ```python
   def update_inventory(self, product_id, quantity_change):
       # The database layer ensures it never goes negative
       # This layer validates the operation is allowed
   ```

3. **Smart Pricing**
   ```python
   def process_sale(self, product_id, quantity):
       product = self.db.get_product(product_id)
       # Use sale_price if available, else regular price
       unit_price = product['sale_price'] or product['price']
   ```

**Key Methods Structure**:

```python
def process_sale(self, product_id, quantity, ...):
    # 1. Get and validate product
    product = self.db.get_product(product_id)
    if not product:
        raise ValueError(...)
    
    # 2. Calculate price
    unit_price = product['sale_price'] or product['price']
    
    # 3. Record transaction
    transaction_id = self.db.record_sale(...)
    
    # 4. Return results
    return transaction_id, total_amount
```

---

### 3. UI Layer (pos_tab.py)

**Responsibility**: User interface and user interaction

**Key Classes**:

```python
class POSTab(QWidget):
    """Main POS interface"""
    def __init__(self, parent=None)
    def init_ui(self)
    def create_product_tab(self) -> QWidget
    def create_sales_tab(self) -> QWidget
    def create_inventory_tab(self) -> QWidget
    def create_reports_tab(self) -> QWidget

class AddProductDialog(QDialog):
    """Dialog for adding products"""
    def __init__(self, parent=None)
    def get_data(self) -> Dict[str, Any]

class ProcessSaleDialog(QDialog):
    """Dialog for processing sales"""
    def __init__(self, product: Dict, parent=None)
    def get_data(self) -> Dict[str, Any]
```

**UI Architecture**:

```
POSTab (Main Widget)
├── Tab 1: Products
│   ├── Add Product Button
│   ├── Search Field
│   └── Product Table
│
├── Tab 2: Sales
│   ├── Product Combo
│   ├── Price/Stock Display
│   ├── Process Sale Button
│   └── Recent Sales Table
│
├── Tab 3: Inventory
│   ├── Adjust Button
│   ├── Refresh Button
│   └── Inventory Table
│
└── Tab 4: Reports
    ├── Report Type Combo
    └── Report Display Table
```

---

## Data Flow Examples

### Example 1: Add Product

```
User clicks "Add Product"
    ↓
AddProductDialog shows
    ↓
User enters data and clicks "Add"
    ↓
Dialog.get_data() returns dict
    ↓
POSTab.add_product() calls pos_manager.add_product()
    ↓
POSManager validates inputs
    ↓
POSManager calls db.add_product()
    ↓
POSDatabase executes INSERT query
    ↓
Database commit
    ↓
POSTab.load_products() refreshes UI
    ↓
Success message shown
```

### Example 2: Process Sale

```
User selects product and clicks "Process Sale"
    ↓
ProcessSaleDialog shows with product info
    ↓
User enters quantity, payment method, customer info
    ↓
Dialog.get_data() returns dict
    ↓
POSTab.process_sale() calls pos_manager.process_sale()
    ↓
POSManager validates product exists and is active
    ↓
POSManager calculates price (uses sale_price if available)
    ↓
POSManager calls db.record_sale()
    ↓
POSDatabase records transaction
    ↓
POSDatabase calls update_inventory() to deduct
    ↓
Inventory capped at 0 (never goes negative)
    ↓
POSTab refreshes products and recent sales
    ↓
Success message with transaction ID shown
```

### Example 3: Refund

```
User initiates refund (feature coming)
    ↓
POSTab.refund_sale() called with transaction_id
    ↓
POSManager.refund_sale() validates transaction
    ↓
POSManager calls db.refund_transaction()
    ↓
POSDatabase creates negative transaction
    ↓
POSDatabase marks original as refunded
    ↓
POSDatabase calls update_inventory() with positive qty
    ↓
Inventory restored (0 stays 0, otherwise increases)
    ↓
POSTab refreshes UI
    ↓
Success message shown
```

---

## Error Handling Strategy

### Three-Level Error Handling

**Level 1: Input Validation (Manager)**
```python
def process_sale(self, product_id, quantity):
    if not self.db.get_product(product_id):
        raise ValueError("Product not found")
    if quantity <= 0:
        raise ValueError("Quantity must be > 0")
```

**Level 2: Database Constraints**
```python
# SQLite constraints prevent invalid data
CREATE TABLE pos_products (
    product_id TEXT PRIMARY KEY,  # Unique constraint
    name TEXT NOT NULL UNIQUE,     # Not null + unique
    price REAL DEFAULT 0.0         # Default value
)
```

**Level 3: UI Error Handling**
```python
def process_sale(self):
    try:
        transaction_id, total = self.pos_manager.process_sale(...)
        QMessageBox.information(self, "Success", ...)
    except Exception as e:
        logger.error("POSTab", f"Error: {e}")
        QMessageBox.critical(self, "Error", f"Failed: {e}")
```

---

## Testing Strategy

### Unit Tests (Database)
```python
class TestPOSDatabase(unittest.TestCase):
    def setUp(self):
        # Create temp database for testing
        self.db = POSDatabase(temp_path)
    
    def test_add_product(self):
        product_id = self.db.add_product(...)
        product = self.db.get_product(product_id)
        self.assertEqual(product['name'], "Test Product")
```

### Unit Tests (Manager)
```python
class TestPOSManager(unittest.TestCase):
    def test_process_sale(self):
        product_id = self.manager.add_product(...)
        txn_id, total = self.manager.process_sale(product_id, 2)
        self.assertIsNotNone(txn_id)
```

### Integration Tests
```python
class TestPOSIntegration(unittest.TestCase):
    def test_complete_pos_workflow(self):
        # Full workflow: add products, process sales, get reports
        # Verifies all components work together
```

### Running Tests
```bash
python test_pos_system.py           # Run all tests
python test_pos_system.py -v        # Verbose output
```

---

## Extending the System

### Add a New Report Type

1. **Add query to POSDatabase**:
```python
def get_daily_sales(self, date) -> Dict:
    cursor = self.execute_query('''
        SELECT ... FROM pos_transactions 
        WHERE DATE(created_at) = ?
    ''', (date,))
    return dict(cursor.fetchone())
```

2. **Add method to POSManager**:
```python
def get_daily_sales(self, date) -> Dict:
    logger.debug("POSManager", f"Getting daily sales for {date}")
    return self.db.get_daily_sales(date)
```

3. **Add UI to POSTab**:
```python
def load_daily_sales_report(self):
    report = self.pos_manager.get_daily_sales(today)
    self.report_table.setRowCount(1)
    # Populate table with data
```

### Add a New Product Field

1. **Update database schema** (or create migration):
```python
def initialize_database(self):
    cursor.execute('''
        ALTER TABLE pos_products ADD COLUMN new_field TEXT DEFAULT '';
    ''')
```

2. **Update POSDatabase methods**:
```python
def add_product(self, ..., new_field=""):
    cursor.execute('''
        INSERT INTO pos_products (product_id, ..., new_field)
        VALUES (?, ..., ?)
    ''', (..., new_field))
```

3. **Update POSManager methods**:
```python
def add_product(self, ..., new_field=""):
    product_id = self.db.add_product(..., new_field=new_field)
    return product_id
```

4. **Update UI dialog**:
```python
class AddProductDialog:
    def init_ui(self):
        self.new_field_input = QLineEdit()
        layout.addRow("New Field:", self.new_field_input)
```

---

## Performance Optimization Tips

### Queries
- Always use indexed columns in WHERE clauses
- Use LIMIT and OFFSET for pagination
- Batch operations when possible

### UI
- Load data on demand (lazy loading)
- Cache frequently accessed products
- Use threading for long operations

### Database
- Proper indexing (already done)
- Use transactions for multi-step operations
- Regular VACUUM to optimize file size

---

## Logging

All modules use the project's Logger:

```python
from assets.Logger import Logger
logger = Logger()

# Debug
logger.debug("POSManager", "Debug message")

# Info
logger.info("POSManager", "Operation completed")

# Warning
logger.warning("POSManager", "Unusual condition")

# Error
logger.error("POSManager", "Something went wrong")
```

Logs are written to `financial_tracker.log`

---

## Database Maintenance

### Backup Database
```python
import shutil
shutil.copy('financial_manager.db', 'backup.db')
```

### Check Database Integrity
```python
cursor.execute("PRAGMA integrity_check")
```

### Optimize Database
```python
cursor.execute("VACUUM")
```

### Get Database Info
```python
cursor.execute("SELECT COUNT(*) FROM pos_products")
cursor.execute("SELECT SUM(quantity_in_stock) FROM pos_products")
```

---

## Security Considerations

1. **SQL Injection Prevention**
   - All queries use parameterized statements
   - Never concatenate user input into SQL

2. **Validation**
   - All inputs validated at manager level
   - Type hints used throughout

3. **Audit Trail**
   - All transactions logged
   - Soft deletes preserve data
   - Timestamps on all records

4. **Error Messages**
   - User-friendly messages shown to UI
   - Detailed logs for debugging

---

## Common Issues and Solutions

### Issue: Inventory goes negative
**Solution**: Checked - database prevents this with capped at 0

### Issue: Product not found
**Solution**: Verify product_id exists before operation

### Issue: Slow database queries
**Solution**: Ensure indices are present on WHERE columns

### Issue: Database locked
**Solution**: Close all connections, PRAGMA busy_timeout

---

## Dependencies

### Required
- PyQt6 (for UI) - already in project
- SQLite3 (for database) - built into Python
- assets.Logger (project logger) - already in project

### Optional (Future)
- python-barcode (barcode generation)
- reportlab (receipt printing)
- python-qrcode (QR code generation)

---

## File Organization Best Practices

```
src/
  pos_database.py      -- Database operations only
  pos_manager.py       -- Business logic only
  
ui/
  pos_tab.py           -- UI presentation only
  
test_pos_system.py     -- All tests
  
README_POS.md          -- User documentation
POS_QUICK_REFERENCE.md -- Quick guide
```

Keep layers separated - don't import UI from database, etc.

---

## Version Control

When committing POS changes:

```bash
git add src/pos_*.py
git add ui/pos_tab.py
git add test_pos_system.py
git add README_POS.md
git commit -m "Add/Update Point of Sale system features"
```

---

## Future Development

### Phase 2 Features
- Product image support
- Barcode scanning
- Receipt printing
- Customer database
- Discount codes

### Phase 3 Features
- Multi-location sync
- Mobile app
- Advanced analytics
- Loyalty program
- Staff management

### Phase 4 Features
- Cloud sync
- Advanced reporting
- Integration with accounting
- Tax calculation
- Automation rules

---

## Resources

- **Code**: See inline docstrings and type hints
- **Tests**: test_pos_system.py shows all usage patterns
- **Documentation**: README_POS.md comprehensive reference
- **Quick Start**: POS_QUICK_REFERENCE.md for users

---

**Last Updated**: December 27, 2025  
**Version**: 1.0.0  
**Status**: Production Ready
