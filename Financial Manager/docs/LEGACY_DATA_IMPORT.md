# Legacy Data Import Feature

## Overview
This feature allows importing tenant rent payment data from legacy JSON format into the Financial Manager application.

## Location
The import feature is accessible from the main menu:
**Rent → Import Legacy Data...**

## Usage

### Step 1: Prepare Your Legacy Data
Create a JSON file with the following structure:

```json
{
  "Tenant Name": {
    "rent": 1350.0,
    "payments": [
      {
        "date": "MM/DD/YYYY",
        "amount": 800.0,
        "month": "MonthName",
        "method": "PaymentMethod"
      }
    ],
    "na_months": {
      "YYYY": ["January", "February"]
    }
  }
}
```

### Step 2: Import Process

1. Click **Rent → Import Legacy Data...** from the main menu
2. Click **Browse...** to select your legacy data JSON file
3. Review the file preview showing:
   - Number of tenants
   - Payment counts
   - Rent amounts
   - N/A months

4. Configure import options:
   - ✓ **Skip payments that already exist** - Avoids duplicates
   - ☐ **Dry run** - Preview without saving

5. Click **Import Data**

### Step 3: Complete Missing Information

For each new tenant not found in the system, a dialog will appear requesting:

**Required Information:**
- Tenant Name (pre-filled, editable)
- Monthly Rent Amount (from legacy data)
- Deposit Amount
- Lease Start Date (inferred from earliest payment)
- Lease End Date
- Rent Due Day (1-31)

**Optional Information:**
- Contact Info (Phone, Email, Address)
- Notes
- Account Status (Active, Inactive, etc.)

### Step 4: Review Results

After import, a summary shows:
- Tenants created
- Tenants updated
- Payments added
- Payments skipped
- Any errors encountered

## Features

### Smart Tenant Detection
- Matches existing tenants by name (case-insensitive)
- Creates new tenants when no match found
- Updates existing tenant payment history

### Payment Handling
- Parses MM/DD/YYYY date format
- Supports various payment methods (Cash, Zelle, Check, etc.)
- Handles negative amounts (refunds/corrections)
- Detects and skips duplicate payments

### N/A Month Import
- Imports months marked as N/A (tenant not responsible for rent)
- Automatically sets monthly status flags

### Data Validation
- Validates date formats
- Ensures rent/deposit amounts are numeric
- Checks due day is between 1-31
- Verifies lease end date is after start date

### Automatic Processing
- Recalculates delinquency after import
- Updates monthly status for all affected months
- Saves all changes to database

## Example Legacy Data

See `example_legacy_data.json` for a complete example with two tenants.

## Technical Details

### Files Modified
- `ui/main_window.py` - Added menu action and handler
- `ui/legacy_data_import_dialog.py` - Import dialog implementation
- `src/account.py` - Enhanced with directory creation and change_password
- `src/tenant.py` - Enhanced with directory creation in save()

### Database Updates
The import process:
1. Loads legacy JSON file
2. For each tenant:
   - Searches for existing tenant by name
   - Creates new tenant if not found (with user input)
   - Adds payments to payment_history
   - Sets N/A month statuses
3. Recalculates delinquency and monthly balances
4. Saves to tenants.json

## Account Data Saving Improvements

### Enhanced AccountManager
- ✓ Automatic directory creation for resources folder
- ✓ Added `change_password()` method with automatic save
- ✓ Salted password hashing with legacy support
- ✓ Save called on create, update, and password change

### Enhanced TenantManager  
- ✓ Automatic directory creation for resources folder
- ✓ Consistent save behavior across all operations

## Troubleshooting

**Import fails with "Account not found":**
- Ensure you're logged in with appropriate permissions
- Admin users can import for all tenants

**Duplicate payments being added:**
- Enable "Skip payments that already exist" option
- The system checks date, amount, and tenant

**Tenant information dialog shows wrong start date:**
- The system infers from earliest payment
- You can manually adjust the lease start date

**N/A months not importing:**
- Ensure month names are spelled correctly (case-insensitive)
- Supported: January, February, March, April, May, June, July, August, September, October, November, December

## Notes

- The Rent menu is always accessible
- Import Legacy Data doesn't require a tenant to be selected
- Other rent menu items (Add Payment, Edit Rent, etc.) still require tenant selection
- Dry run mode allows previewing changes without saving
