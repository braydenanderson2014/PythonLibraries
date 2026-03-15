# POS Deals & Item Number - Quick Start Guide

## What's New

### ✓ Item Number Entry (Sales)
Instead of selecting from a dropdown, you can now:
1. Type an **item number** or **product name**
2. Set the quantity
3. Press Enter or click "Add Item"
4. Item appears in cart
5. Repeat for multiple items
6. Process entire cart at once

### ✓ Promotional Deals
Create deals that automatically discount products:
- By **item number** (specific products)
- By **tag** (multiple products with same tag)
- By **percentage** or **fixed amount**
- With **start and end dates**

### ✓ Product Editor
The "Edit" button now actually works! Edit:
- Name, description, prices
- Item number, category, tags
- Fees, restrictions
- Inventory and reorder level
- Deactivate products

---

## How To: Process Sale with Item Numbers

```
1. Click Sales tab
2. Click "Process Sale" button
3. Type: APPLE-001 (or just "Apple")
4. Qty: 3
5. Press Enter
6. Type: BANANA-001
7. Qty: 2
8. Press Enter
9. [Optional] Select a Deal and click "Apply Deal"
10. Enter customer info
11. Click "Process Sale"
```

**Result:** Multi-item sale processed with optional discount!

---

## How To: Create a Deal

```
1. Click Deals tab
2. Click "Create New Deal"
3. Fill in:
   - Name: "Summer 20% Off"
   - Type: tag
   - Discount: 20
   - Type: percentage
   - Tags: summer,sale
   - Start: 2025-06-01 00:00:00
   - End: 2025-08-31 23:59:59
4. Click "Create Deal"
```

**Now:** Products tagged with "summer" or "sale" get 20% off!

---

## How To: Edit a Product

```
1. Click Products tab
2. Find product in list
3. Click "Edit" button
4. Change any field you want
5. Click "Save Changes"
6. Product updates immediately
```

**Can Edit:**
- Name, description, tags
- Prices (regular, sale, purchase)
- Item number, category
- Fees, restrictions
- Stock quantity
- Reorder level

---

## Deal Types Explained

### Type: "product"
- Apply to **specific products**
- Enter product names/numbers in Products field
- Example: "10% off Apples and Oranges"

### Type: "tag"
- Apply to all products with matching **tags**
- Enter tags in Tags field (comma-separated)
- Example: "30% off everything tagged 'clearance'"

### Type: "all"
- Apply to **everything**
- No product or tag selection needed
- Example: "Black Friday - 25% off entire store"

---

## Deal Discount Types

### Percentage
- 0-100%
- Example: 20% off a $50 item = $10 discount
- Best for: Percentage-based promotions

### Fixed
- Dollar amount
- Example: $5 off any purchase
- Best for: Fixed discounts (buy 3 get $5 off)

---

## Tagging Products for Deals

When you create products, add tags separated by commas:
```
Tags: clearance,summer,sale,popular
```

Then create deals by tag:
```
Tag Deal: "40% Off Clearance"
  Type: tag
  Tags: clearance
  Discount: 40%
```

---

## Sale Processing Flow (New)

```
BEFORE: Select product → Enter qty → Confirm

AFTER:  Type item # → Qty → Add
        Type item # → Qty → Add
        Type item # → Qty → Add
        [Optional] Select deal
        Confirm all items at once
```

**Benefits:**
- Faster for multiple items
- See cart before processing
- Can apply bulk discounts
- Easy to add/remove items

---

## Key Fields

### Products
- Item numbers
- Or full product names
- Examples: "APPLE-001", "Gala Apple", "Apple"

### Tags
- Comma-separated
- Examples: "summer,sale,clearance"
- Match these in deals

### Dates
- Start date (optional)
- End date (optional)
- Format: YYYY-MM-DD HH:MM:SS
- If not set, deal is always active

### Discount Value
- For percentage: 0-100
- For fixed: any dollar amount
- Examples: 20 (for 20%) or 5 (for $5)

---

## Examples

### Example 1: Weekend Specials
```
Name: "Weekend 15% Off Everything"
Type: all
Discount: 15%
Dates: 
  Start: Every Friday 5pm
  End: Every Sunday 11:59pm
```

### Example 2: Buy More Save More
```
Name: "Buy 5+ Get $10 Off"
Type: product
Products: APPLE-001, ORANGE-001, BANANA-001
Discount: $10 fixed
(Can note in description: "Min 5 items")
```

### Example 3: Clearance Event
```
Name: "Clearance 50% Off"
Type: tag
Tags: clearance
Discount: 50%
Start: Today
End: End of month
```

### Example 4: Customer Loyalty
```
Name: "Regular Customer - $5 Off"
Type: all
Discount: $5 fixed
(Apply manually by naming deal to customer)
```

---

## Tips & Tricks

**Tip 1: Use descriptive names**
- "Summer Sale 20%" instead of "Deal 1"
- Easier to find and select

**Tip 2: Use tags strategically**
- "sale" for ongoing promotions
- "seasonal" for seasonal items
- "clearance" for items to move
- "bulk-buy" for quantity deals

**Tip 3: Set specific dates**
- Deals auto-enable/disable
- No need to manually deactivate
- Saves time on busy days

**Tip 4: Keep product info updated**
- Add tags when creating products
- Makes deal creation faster
- Customers see correct pricing

**Tip 5: Test deals before using**
- Create a test deal
- Process a test sale
- Verify discount applies
- Then activate for real sales

---

## Troubleshooting

**Q: Deal doesn't appear in Sales dialog**
A: Check if deal is active and within date range

**Q: Product not found when typing item number**
A: Make sure item number matches exactly (case-sensitive)

**Q: Discount doesn't apply**
A: Verify product tags match deal tags, or product ID is in deal

**Q: Edit button shows blank dialog**
A: This shouldn't happen - product must exist in database

**Q: Can't find a deal to deactivate**
A: Look in Deals tab - deals are only shown there

---

## What Gets Logged

Every sale with a deal logs:
1. **Transaction ID** - unique sale identifier
2. **Product IDs** - what was sold
3. **Quantities** - how many of each
4. **Unit Prices** - individual item prices
5. **Deal ID** - which deal was applied
6. **Discount Amount** - actual $ discount given
7. **Final Total** - after discount

All historical data is preserved!

---

## Files That Were Updated

- `src/pos_database.py` - Added deal tables and methods
- `src/pos_manager.py` - Added deal management logic
- `ui/pos_tab.py` - New sales dialog, deals tab, product editor

**New tables in database:**
- `pos_deals` - Stores all deals
- `pos_deal_applications` - Logs applied discounts

---

## Next Steps

1. **Open Financial Manager**
2. **Go to Point of Sale tab**
3. **Click Deals tab**
4. **Create your first deal**
5. **Click Sales tab**
6. **Process a sale with the new system**

Enjoy your enhanced POS system!

