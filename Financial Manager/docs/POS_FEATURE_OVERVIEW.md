# POS System - Feature Overview

## Three Major Enhancements

---

## 1. ITEM NUMBER ENTRY (Sales Tab)

### Old Way (Single Item)
```
┌─────────────────────────┐
│ Select Product Dropdown │
│ [Pick from list]        │
├─────────────────────────┤
│ Quantity: [1]           │
│ Price: $10.00           │
│ Total: $10.00           │
├─────────────────────────┤
│ [Process Sale]          │
└─────────────────────────┘
```

### New Way (Multiple Items with Cart)
```
┌────────────────────────────────┐
│ Item #: [type here]  Qty: [5]  │
│ [Add Item] [type or press enter]
├────────────────────────────────┤
│         SHOPPING CART           │
│ Product    | Item # | Qty | Total
│ Apple      | APPL-1 | 3   | $9.00
│ Orange     | ORNG-1 | 2   | $4.00
│ [Remove]   [Remove]             │
├────────────────────────────────┤
│ Available Deals: [dropdown]     │
│                  [Apply Deal]   │
├────────────────────────────────┤
│ Payment: [Cash]                 │
│ Customer: [Optional]            │
├────────────────────────────────┤
│ Subtotal: $13.00                │
│ Discount: -$1.30 (Deal)         │
│ TOTAL:    $11.70                │
├────────────────────────────────┤
│ [Process Sale] [Cancel]         │
└────────────────────────────────┘
```

**Key Benefits:**
- Type instead of scroll
- See cart before checkout
- Multiple items at once
- Apply discounts to entire cart
- Easy to add/remove items

---

## 2. DEALS MANAGEMENT (Deals Tab)

### Create a Deal
```
┌──────────────────────────────┐
│  Create New Deal             │
├──────────────────────────────┤
│ Name:        [Summer 20% Off]│
│ Description: [Optional text] │
│ Type:        [tag v]         │
│              - product       │
│              - tag           │
│              - all           │
│ Discount:    [20]            │
│ Type:        [% v]           │
│              - percentage    │
│              - fixed         │
│ Tags:        [summer,sale]   │
│ Start Date:  [2025-06-01 ...] (optional)
│ End Date:    [2025-08-31 ...] (optional)
│                              │
│ [Create Deal] [Cancel]       │
└──────────────────────────────┘
```

### View Deals
```
┌────────────────────────────────────────────┐
│ [Create New Deal]                          │
├─────┬──────┬─────────┬────────┬────┬──────┤
│Name │Type  │Discount │Products│Date│Action│
├─────┼──────┼─────────┼────────┼────┼──────┤
│Sum- │tag   │20%      │summer  │...│Deac..│
│mer  │      │         │sale    │    │      │
│     │      │         │        │    │      │
├─────┼──────┼─────────┼────────┼────┼──────┤
│Holi-│all   │$5 fixed │All     │..  │Deac..│
│day  │      │         │        │    │      │
└─────┴──────┴─────────┴────────┴────┴──────┘
```

**Deal Types:**
- **product** → Specific items
- **tag** → By product tags
- **all** → Entire store

**Discount Types:**
- **percentage** → 0-100%
- **fixed** → Dollar amount

---

## 3. PRODUCT EDITOR (Products Tab)

### Product List
```
┌──────────────────────────────────────────┐
│ [Add New Product]                        │
├────────┬──────┬─────┬──────┬──────┬─────┤
│Product │Item #│Price│Stock │Status│Act. │
├────────┼──────┼─────┼──────┼──────┼─────┤
│Apple   │APPL-1│$1.50│  45  │[OK] │Edit │
│Orange  │ORNG-1│$2.00│  12  │[LOW]│Edit │
│Banana  │BANA-1│$0.99│   2  │[CRIT]Edit │
└────────┴──────┴─────┴──────┴──────┴─────┘
```

### Edit Product Dialog
```
┌────────────────────────────────┐
│ Edit Product - Apple           │
├────────────────────────────────┤
│ Product Name:    [Apple      ] │
│ Description:     [Red apple   ]│
│ Item Number:     [APPL-1    ] │
│ Category:        [Fruit     ] │
│ Tags:            [fresh,red ] │
│ Regular Price:   [$1.50     ] │
│ Sale Price:      [$1.25     ] │
│ Purchase Price:  [$0.75     ] │
│ Fees:            [$0.00     ] │
│ Restrictions:    [None      ] │
│ Current Stock:   [45        ] │
│ Reorder Level:   [20        ] │
├────────────────────────────────┤
│ [Save Changes] [Deactivate]  [Cancel]
└────────────────────────────────┘
```

**Editable Fields:**
- ✓ Name
- ✓ Description
- ✓ Item Number
- ✓ Category
- ✓ Tags (for deals)
- ✓ Regular Price
- ✓ Sale Price
- ✓ Purchase Price
- ✓ Fees
- ✓ Restrictions
- ✓ Current Stock
- ✓ Reorder Level

---

## COMPLETE WORKFLOW

### Sales with Deal

```
STEP 1: Start Sale
  ┌─ Click Sales Tab
  └─ Click "Process Sale"

STEP 2: Add Items
  ┌─ Type: "APPLE"
  ├─ Qty: 5
  ├─ Press Enter
  ├─ Type: "ORANGE"
  ├─ Qty: 3
  └─ Press Enter

STEP 3: Apply Discount
  ┌─ Select Deal: "Fresh Fruit 15% Off"
  └─ Click "Apply Deal"

STEP 4: Review Cart
  ┌─ Apples:   5 × $1.50 = $7.50
  ├─ Oranges:  3 × $2.00 = $6.00
  ├─ Subtotal:              $13.50
  ├─ Discount: -$2.03 (15%)
  └─ TOTAL:                 $11.47

STEP 5: Checkout
  ┌─ Payment Method: Cash
  ├─ Customer Name: (optional)
  ├─ Notes: (optional)
  └─ Click "Process Sale"

RESULT: ✓ Sale recorded with discount
        ✓ Inventory updated
        ✓ Deal logged
        ✓ Transaction complete
```

---

## TAB LAYOUT

```
┌─────────────────────────────────────────┐
│   Point of Sale System - 5 Tabs         │
├──────┬──────┬────────┬──────┬──────────┤
│Prod. │Sales │Invntry │Deals │Reports   │
├──────┴──────┴────────┴──────┴──────────┤
│                                         │
│  ← Tab Content Shows Here →             │
│                                         │
└─────────────────────────────────────────┘
```

### Products Tab
- Add new products
- Search/filter
- View all products
- **Edit** button → Full editor

### Sales Tab
- **Process Sale** → New dialog with:
  - Item number input
  - Shopping cart
  - Deal selector
  - Payment info
  - Real-time totals

### Inventory Tab
- View stock levels
- Adjust inventory
- Reorder alerts

### **NEW:** Deals Tab
- **Create Deal** → Dialog with:
  - Name, description
  - Deal type (product/tag/all)
  - Discount amount & type
  - Product/tag selection
  - Start/end dates
- View all deals in table
- Deactivate deals

### Reports Tab
- Sales summary
- Top sellers
- Low stock
- Inventory value

---

## KEY FEATURES

### ✓ Fast Item Entry
- Type item number or name
- Quantity input
- Multiple items at once
- No dropdown scrolling

### ✓ Smart Deals
- By specific products
- By product tags
- By discount type (% or $)
- Automatic start/end dates
- Full audit trail

### ✓ Full Product Control
- Edit all fields
- Tag products for deals
- Adjust inventory
- Soft delete (archive)
- Change prices anytime

### ✓ Professional Workflow
- Multi-item checkout
- Visible discount application
- Customer information
- Payment method tracking
- Complete transaction logging

---

## QUICK REFERENCE

### To Sell Multiple Items
1. Sales Tab → Process Sale
2. Type item name or number
3. Set quantity
4. Press Enter to add
5. Repeat steps 2-4
6. Optional: Apply deal
7. Click Process Sale

### To Create a Deal
1. Deals Tab → Create New Deal
2. Name it (e.g., "Summer Sale")
3. Choose type (product/tag/all)
4. Set discount (% or $)
5. Optional: Add dates
6. Click Create

### To Edit a Product
1. Products Tab → Find product
2. Click Edit button
3. Change fields
4. Click Save Changes

### To Stop Using a Deal
1. Deals Tab → Find deal
2. Click Deactivate button
3. Deal is inactive (can reactivate)

---

## DATA FLOW

```
Sale with Deal:

Customer Item → Item Number Lookup
                      ↓
                 Find Product
                      ↓
                Add to Cart
                      ↓
                Apply Deal
                (if selected)
                      ↓
            Calculate Totals
                      ↓
            Process Transaction
                      ↓
         Record in Database:
        - pos_transactions
        - pos_inventory
        - pos_deal_applications
                      ↓
              Display Receipt
```

---

## STATUS INDICATORS

### In Product List
```
[OK]   → Stock > Reorder Level
[LOW]  → Stock = Reorder Level
[CRIT] → Stock < Reorder Level
```

### Deal Availability
```
Active   → Within date range (or no dates set)
Inactive → Outside date range or deactivated
```

---

## NOTES

- **All changes are saved immediately**
- **Inventory updates in real-time**
- **Deals can be scheduled with dates**
- **All transactions are logged**
- **Products can be deactivated (not deleted)**
- **Tags link products to deals**

