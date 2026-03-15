# POS System Deals & Item Number Enhancement

## Overview

The Point of Sale system has been significantly enhanced with:
1. **Item Number-Based Sales Entry** - Add items to cart by typing item numbers
2. **Promotional Deals System** - Create and manage deals/promotions with start/end dates
3. **Tag-Based Deals** - Apply discounts automatically to products with matching tags
4. **Complete Product Editor** - Edit all product attributes in an intuitive dialog

---

## New Features

### 1. Enhanced Sales Processing Dialog

**What's New:**
- **Item Entry by Number**: Type item number or product name and press Enter to add to cart
- **Shopping Cart**: See all items you're adding before checkout
- **Quantity Control**: Change quantity for each item independently
- **Deal Application**: Select and apply deals to entire cart
- **Real-Time Totals**: See subtotal, discount, and final total as you add items
- **Remove Items**: Remove individual items from cart before processing

**How It Works:**
```
1. Click "Sales" tab
2. Click "Process Sale" button
3. Type item number or product name in "Item #" field
4. Set quantity if needed
5. Press Enter or click "Add Item"
6. Repeat for each item
7. Optional: Select a deal and click "Apply Deal"
8. Enter payment info and customer details
9. Click "Process Sale" to complete
```

---

### 2. Promotional Deals System

**Database Tables Created:**
- `pos_deals` - Stores deal information with start/end dates
- `pos_deal_applications` - Logs which deals were applied to which transactions

**Deal Types:**
- **Product**: Apply discount to specific products
- **Tag**: Apply discount to products with specific tags (e.g., "sale", "clearance")
- **All**: Apply discount to entire cart

**Discount Types:**
- **Percentage**: Discount as percentage (0-100%)
- **Fixed**: Discount as fixed amount (e.g., $5 off)

**Deal Features:**
- Start and End dates (optional)
- Active/Inactive status
- Applied discount tracking
- Multiple tags support
- Multiple product IDs support

---

### 3. Deal Management Tab

**New "Deals" Tab in POS System**

**Features:**
- **Create Deal Button**: Opens dialog to create new promotions
- **Deals Table**: Shows all deals with:
  - Deal name and description
  - Discount amount and type
  - Applicable products or tags
  - Start and end dates
  - Deactivate button for active deals

**Creating a Deal:**

Dialog has these fields:
- **Deal Name**: Name of the promotion (e.g., "Summer Sale")
- **Description**: Optional description
- **Deal Type**: 
  - `product` - Apply to specific products
  - `tag` - Apply to products with tags
  - `all` - Apply to everything
- **Discount Value**: Amount or percentage
- **Discount Type**: 
  - `percentage` - 0-100%
  - `fixed` - Dollar amount
- **Products** (if type=product): Comma-separated product names/numbers
- **Tags** (if type=tag): Comma-separated tags (e.g., "clearance,holiday")
- **Start Date**: YYYY-MM-DD HH:MM:SS (optional)
- **End Date**: YYYY-MM-DD HH:MM:SS (optional)

---

### 4. Complete Product Editor

**What's Improved:**
The "Edit" button on products now opens a full editor instead of showing "Coming Soon"

**Fields You Can Edit:**
- Product Name
- Description
- Item Number (SKU)
- Category
- Tags (comma-separated for deal targeting)
- Regular Price
- Sale Price
- Purchase Price (cost)
- Fees (transaction fees)
- Restrictions
- Current Stock (Quantity)
- Reorder Level

**Actions Available:**
- **Save Changes**: Update all product information
- **Deactivate**: Remove product from active sales (archive it)
- **Cancel**: Close without changes

**How To Edit:**
1. Click "Products" tab
2. Find product in table
3. Click the "Edit" button in Actions column
4. Make your changes
5. Click "Save Changes"
6. Product updates immediately

---

## Database Schema Additions

### pos_deals Table
```sql
CREATE TABLE pos_deals (
    deal_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    deal_type TEXT NOT NULL,           -- 'product', 'tag', 'all'
    discount_value REAL NOT NULL,      -- Amount or percentage
    discount_type TEXT NOT NULL,       -- 'percentage' or 'fixed'
    product_ids TEXT,                  -- JSON array of product IDs
    tags TEXT,                         -- JSON array of tags
    start_date TIMESTAMP,              -- When deal starts
    end_date TIMESTAMP,                -- When deal ends
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
```

### pos_deal_applications Table
```sql
CREATE TABLE pos_deal_applications (
    application_id TEXT PRIMARY KEY,
    deal_id TEXT NOT NULL,
    transaction_id TEXT NOT NULL,
    discount_amount REAL NOT NULL,     -- Actual discount applied
    created_at TIMESTAMP
)
```

---

## API Methods (POSManager)

### Deal Management Methods

**Create Deal:**
```python
deal_id = pos_manager.create_deal(
    name="Summer 20% Off",
    description="20% off all summer items",
    deal_type="tag",                    # 'product', 'tag', or 'all'
    discount_value=20,
    discount_type="percentage",         # 'percentage' or 'fixed'
    tags=["summer", "sale"],
    start_date="2025-06-01 00:00:00",
    end_date="2025-08-31 23:59:59"
)
```

**Get Deals:**
```python
# Get all active deals for current date/time
active_deals = pos_manager.get_active_deals()

# Get all deals (active and inactive)
all_deals = pos_manager.get_all_deals()

# Get single deal
deal = pos_manager.get_deal(deal_id)
```

**Update Deal:**
```python
pos_manager.update_deal(
    deal_id,
    discount_value=25,
    discount_type="percentage"
)
```

**Deactivate Deal:**
```python
pos_manager.deactivate_deal(deal_id)
```

**Get Applicable Deals for Product:**
```python
applicable = pos_manager.get_applicable_deals(
    product_id,
    tags=['summer', 'sale']  # Product's tags
)
```

**Calculate Discount:**
```python
discount = pos_manager.calculate_deal_discount(
    deal,
    quantity=5,
    unit_price=19.99
)
```

---

## Usage Examples

### Example 1: Simple Percentage Deal

```
1. Go to Deals tab
2. Click "Create New Deal"
3. Name: "Holiday Sale 15% Off"
4. Deal Type: "all"
5. Discount Value: 15
6. Discount Type: "percentage"
7. Start: 2025-12-01 00:00:00
8. End: 2025-12-31 23:59:59
9. Click "Create Deal"

Now when processing sales, customers automatically see 15% discount applied!
```

### Example 2: Buy 2 Get $5 Off

```
1. Go to Deals tab
2. Click "Create New Deal"
3. Name: "Buy 2 Items - $5 Off"
4. Deal Type: "tag"
5. Tags: "bulk-buy"
6. Discount Value: 5
7. Discount Type: "fixed"
8. Click "Create Deal"

Then add "bulk-buy" tag to products eligible for this deal.
When purchasing 2+ of those items, $5 discount applies!
```

### Example 3: Category-Specific Deal

```
1. Go to Deals tab
2. Click "Create New Deal"
3. Name: "Clearance 40% Off"
4. Deal Type: "tag"
5. Tags: "clearance"
6. Discount Value: 40
7. Discount Type: "percentage"
8. Click "Create Deal"

Then tag clearance items with "clearance" tag.
When they're purchased, 40% discount applies!
```

### Example 4: Processing a Sale with Deal

```
1. Click "Sales" tab
2. Click "Process Sale"
3. Type "APPLE-001" (item number)
4. Set Qty: 3
5. Press Enter
6. Type "ORANGE-001"
7. Set Qty: 2
8. Press Enter
9. Select "Summer 20% Off" from Available Deals
10. Click "Apply Deal"
11. See discount apply to total
12. Enter payment info
13. Click "Process Sale"

Result: Transaction logged with applied deal!
```

---

## Important Notes

### Deal Timing
- Deals respect **start_date** and **end_date**
- If no dates specified, deal is always active
- Only active deals with valid date range are shown/applied
- Dates use ISO format: YYYY-MM-DD HH:MM:SS

### Deal Application
- Deals are applied at **transaction level** (entire cart)
- One deal per transaction
- Discount amount is calculated and logged separately
- Original transaction amount is preserved for records

### Product Tags
- Tags are comma-separated in product editor
- Used to match tag-based deals
- Example tags: "sale", "clearance", "summer", "bulk-buy"
- Same product can have multiple tags

### Inventory
- **Deals do NOT affect inventory**
- Inventory changes when sale is processed
- Manual inventory adjustments logged separately
- Zero-inventory sales still allowed

---

## UI Components

### Sales Dialog (New)
- Item number/name input field
- Quantity spinner
- "Add Item" button
- Shopping cart table
- Deal selector dropdown
- "Apply Deal" button
- Payment info section
- Total calculation display

### Deals Tab (New)
- "Create New Deal" button
- Deals management table
- Deactivate buttons for active deals
- Table shows: Name, Type, Discount, Products/Tags, Dates, Actions

### Product Editor (Enhanced)
- All product fields editable
- Real-time validation
- Save/Deactivate/Cancel buttons
- Automatic inventory adjustment when qty changed

---

## Technical Details

### Sale Processing with Deals

When a sale is processed:
1. Each item in cart is recorded as a transaction
2. If deal selected, discount is calculated
3. Deal application is logged with transaction ID
4. Inventory is updated (or kept at 0 if already 0)
5. Total is displayed with and without discount

### Deal Matching Logic

For each product in cart:
1. Check if product ID matches deal's product_ids list
2. Check if any product tags match deal's tags list
3. If match found, deal is applicable
4. Discount calculated based on discount_type and discount_value
5. Discount amount logged in deal_applications table

---

## Files Modified

1. **src/pos_database.py**
   - Added 2 new tables: pos_deals, pos_deal_applications
   - 10+ new methods for deal management
   - Deal date filtering logic

2. **src/pos_manager.py**
   - 8 new methods for deal operations
   - Discount calculation method
   - Deal validation

3. **ui/pos_tab.py**
   - Completely redesigned ProcessSaleDialog (item number input, shopping cart)
   - New create_deals_tab() method
   - New create_deal() method with dialog
   - New load_deals() method
   - New deactivate_deal() method
   - Full edit_product() implementation (was placeholder)
   - Updated process_sale() to handle multi-item cart with deals

---

## Testing Recommendations

1. **Create a deal** with future dates - verify it doesn't appear in sales
2. **Create a deal** with past end date - verify it's inactive
3. **Apply deal** to sale - verify discount appears in total
4. **Edit product** - change all fields and verify they update
5. **Add multiple items** by item number - verify cart works
6. **Deactivate product** - verify it no longer appears in sales
7. **Check deal tracking** - look at deal_applications table for logged discounts

---

## Future Enhancements

Possible additions:
- Bulk create deals from CSV
- Deal performance reports
- Customer-specific deals
- Percentage-based tiered discounts
- Deal analytics dashboard
- Scheduled deal automation
- Deal conflict resolution (if multiple deals match)

