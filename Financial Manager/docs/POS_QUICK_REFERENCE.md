# POS System Quick Reference

## Quick Start

### Access the POS System
1. Open Financial Manager
2. Click "Point of Sale" tab (newly added)
3. You'll see 4 sub-tabs: Products, Sales, Inventory, Reports

## Tab Guide

### 📦 Products Tab
**What to do:**
- Add new products with "Add New Product" button
- Search for existing products
- View product details (price, stock, status)

**Product fields:**
- Name (required)
- Description
- Item Number (SKU)
- Tags
- Regular Price
- Sale Price (optional)
- Purchase Price
- Fees
- Restrictions
- Initial Quantity
- Reorder Level

**Status colors:**
- 🟢 GREEN = Normal stock
- 🟡 YELLOW = Low stock (below reorder level)
- 🔴 RED = Out of stock

---

### 💳 Sales Tab
**Quick sale in 3 clicks:**
1. Select product from dropdown
2. Click "Process Sale"
3. Enter quantity and payment method
4. Done!

**Optional:**
- Customer name
- Customer contact
- Sale notes

**Price logic:**
- Uses sale price if available
- Falls back to regular price
- Adds any product fees automatically

**Can sell at 0 inventory** ✓
(Inventory stays at 0, doesn't go negative)

---

### 📊 Inventory Tab
**Monitor stock levels:**
- View all products with current quantities
- See reorder levels
- Track total inventory value

**Adjust inventory:**
- Click "Adjust Inventory" button
- Select product
- Enter quantity change (+ or -)
- Reason is tracked automatically

---

### 📈 Reports Tab
**Choose report type:**

1. **Sales Summary**
   - Total transactions
   - Total quantity sold
   - Total revenue
   - Average transaction amount

2. **Top Sellers**
   - Best selling products
   - Quantity sold
   - Revenue per product
   - Current stock

3. **Low Stock**
   - Products below reorder level
   - Current vs. reorder level
   - When to reorder

4. **Inventory Value**
   - Product value calculation
   - Total inventory value
   - Cost basis per product

---

## Product Attributes Explained

| Field | Purpose | Example |
|-------|---------|---------|
| **Name** | Product identifier | "Coffee - Medium" |
| **Item Number** | SKU/barcode | "COFF-MED-001" |
| **Price** | Regular selling price | $3.50 |
| **Sale Price** | Discounted price | $2.99 |
| **Purchase Price** | Cost to you | $1.50 |
| **Fees** | Associated costs (tax, handling) | $0.25 |
| **Restrictions** | Special notes | "Limited time", "Must be 18+" |
| **Reorder Level** | When to restock | 20 units |
| **Tags** | Search keywords | "beverage, hot, popular" |

---

## Inventory Management Rules

### Key Rules:
1. ✓ **Can sell at 0 inventory** (useful for pre-orders)
2. ✗ **Cannot go negative** (capped at 0)
3. ✓ **All changes tracked** (audit trail)
4. ✓ **Sales deduct automatically** (no manual step needed)
5. ✓ **Refunds restore inventory** (instantly)

### Example Scenario:
```
Start: 0 units in stock
Sell 5 units → Still 0 units (not -5)
Refund that sale → Still 0 units
Restock 100 → 100 units

This allows:
- Pre-orders
- Dropshipping
- Backordered items
- Special orders
```

---

## Common Tasks

### ✅ Add a New Product
1. Go to **Products** tab
2. Click **"Add New Product"**
3. Fill in product details
4. Set initial quantity
5. Click **"Add Product"**

### ✅ Process a Sale
1. Go to **Sales** tab
2. Select product from dropdown
3. Click **"Process Sale"**
4. Enter quantity
5. Select payment method
6. (Optional) Add customer info
7. Click **"Process Sale"**

### ✅ Restock Item
1. Go to **Inventory** tab
2. Click **"Adjust Inventory"**
3. Select product
4. Enter positive number (e.g., +50)
5. Confirm
6. Stock updates instantly

### ✅ Process Refund
*(Coming in next update - for now, note the transaction ID and contact admin)*

### ✅ Check Low Stock
1. Go to **Reports** tab
2. Select **"Low Stock"**
3. View products below reorder level
4. Restock as needed

---

## Data Entry Tips

### Product Names
- Use clear, descriptive names
- Include size/variant if applicable
- Examples: "Coffee - Large", "Tea - Green", "Pastry - Croissant"

### Item Numbers (SKU)
- Use consistent format
- Include category prefix: "COFF-", "TEA-", "FOOD-"
- Example: "COFF-MED-001"

### Tags
- Separate with commas
- Use consistent terminology
- Example: "beverage, hot, popular, morning"

### Prices
- Regular price = what you normally charge
- Sale price = discounted price (optional)
- Include all fees in regular price if not separate

---

## Keyboard Shortcuts
*(Coming in future update)*

For now, use mouse/trackpad to navigate.

---

## FAQ

**Q: Can I sell items that are out of stock?**
A: Yes! Inventory stays at 0 but doesn't go negative. Perfect for pre-orders.

**Q: What happens when inventory hits reorder level?**
A: The product shows as "LOW STOCK" (yellow). You get alerts in reports.

**Q: Can I edit products after creation?**
A: Coming in next update! For now, contact admin.

**Q: Are refunds supported?**
A: Yes! Admin can process refunds. The system will restore inventory automatically.

**Q: How far back does transaction history go?**
A: All transactions are logged. Reports show recent ones; full history available to admin.

**Q: Can I delete products?**
A: Products are "soft deleted" (marked inactive). You won't see them but data is preserved.

**Q: Is there a daily/weekly summary?**
A: Sales Summary report shows all-time stats. Daily reports coming soon.

---

## Getting Help

1. **Hover over fields** for tooltips (coming soon)
2. **Check logs** in `financial_tracker.log`
3. **Test data** is in SQLite database
4. **Reset database** by deleting `financial_manager.db`

---

## Important Notes

⚠️ **Backup your data!** 
- Database location: `~/.financial_manager/financial_manager.db`
- Regular backups recommended
- Use File > Backup & Restore

⚠️ **Fees are per-transaction** - included in final total

⚠️ **Sale price is optional** - if not set, regular price is used

⚠️ **All changes are logged** - you have a complete audit trail

---

## Performance Tips

- Search by item number for fastest lookup
- Use tags to organize products
- Set appropriate reorder levels
- Review reports weekly
- Archive old transactions (admin feature)

---

**Last Updated:** December 27, 2025  
**Version:** 1.0.0 - Quick Reference  
**Status:** Ready to Use
