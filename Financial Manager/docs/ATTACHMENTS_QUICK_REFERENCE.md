# Transaction Attachments - Quick Reference Guide

**Feature**: Attach receipts, invoices, and documents to transactions  
**Version**: 1.0  
**Date**: December 4, 2025

---

## Quick Start

### Adding Attachments

1. Click **"Add Transaction"**
2. Fill in transaction details
3. Scroll to **"Attachments"** section
4. Click **"📎 Add Attachment"**
5. Select file(s)
6. Click **"OK"** to save

### Viewing Attachments

1. Find transaction with **📎 X** icon
2. Click the paperclip button
3. Use **Previous/Next** to navigate
4. Click **"Open in System Viewer"** for full access

---

## Supported File Types

### ✅ Fully Supported (with preview)
- **Images**: JPEG, PNG, GIF, BMP, WebP
  - Display inline in viewer
  - Perfect for receipt photos

### ✅ Supported (open externally)
- **PDFs**: All PDF documents
- **Documents**: Word, Excel, text files
- **Any other file type**

---

## Common Use Cases

### 📷 Receipt Photos
- Take photo of receipt with phone
- Transfer to computer
- Attach to transaction
- Never lose a receipt again!

### 📄 Invoices & Bills
- Attach PDF invoices
- Link to payment transactions
- Easy reference for taxes

### 💼 Business Expenses
- Attach all supporting documents
- Complete audit trail
- Export for reimbursement

### 📊 Tax Documentation
- Attach receipts for deductible expenses
- Filter transactions by category
- Have all documentation in one place

---

## Tips & Tricks

### Best Practices

**Naming Files**:
- Use descriptive names before uploading
- Original filename is preserved
- Example: `walmart_groceries_2024-12-04.jpg`

**File Organization**:
- Attach immediately after purchase
- One receipt per transaction
- Multiple pages? Use multi-page PDF or multiple images

**Image Quality**:
- Use good lighting for photos
- Ensure text is readable
- Landscape orientation often works best

### Keyboard Shortcuts (in Viewer)

While viewing attachments:
- **Open in System Viewer**: Opens full-resolution image/PDF
- System apps often have more features (zoom, print, etc.)

---

## File Icons Guide

| Icon | Meaning |
|------|---------|
| 📎 X | Transaction has X attachment(s) |
| 🖼️ | Image file |
| 📕 | PDF document |
| 📝 | Text file |
| 📄 | Word/document |
| 📊 | Spreadsheet |
| 📦 | Archive/zip |

---

## Storage Location

All attachments are stored in:
```
Financial Manager/
  └── resources/
      └── attachments/
```

**Important**: Don't manually delete files from this folder. Use the app's delete function to ensure proper cleanup.

---

## FAQ

**Q: How many attachments can I add?**  
A: Unlimited! Add as many as needed per transaction.

**Q: What's the file size limit?**  
A: No enforced limit, but keep it reasonable. Large files may slow down the app.

**Q: Can I edit attachments later?**  
A: Currently, no. Delete and recreate the transaction if needed.

**Q: Are attachments backed up?**  
A: Yes, if you backup the entire Financial Manager folder (including resources/attachments/).

**Q: Can I export attachments?**  
A: Currently manual - open the transaction, view attachment, save from system viewer.

**Q: Do attachments sync?**  
A: Not automatically. Copy the entire app folder to sync across devices.

---

## Troubleshooting

### Problem: Can't view attachment

**Solutions**:
1. Check if file exists in `resources/attachments/` folder
2. Try "Open in System Viewer"
3. File may be corrupted - re-upload if available

### Problem: Attachment button missing

**Solutions**:
1. Ensure using latest version
2. Feature only available in "Add Transaction" (not recurring)
3. Check if transaction was created before feature was added

### Problem: Large app folder

**Solutions**:
1. Attachments take up space
2. Delete transactions with attachments you no longer need
3. Consider compressing images before uploading

---

## Examples

### Example 1: Grocery Receipt
```
Transaction:
  Amount: $156.84
  Description: Grocery Shopping - Walmart
  Category: Groceries
  Attachments: receipt_walmart_dec4.jpg
```

### Example 2: Business Lunch
```
Transaction:
  Amount: $48.50
  Description: Client Lunch - Olive Garden
  Category: Business Meals
  Attachments: 
    - receipt.jpg
    - business_purpose_note.pdf
```

### Example 3: Tax-Deductible Donation
```
Transaction:
  Amount: $500.00
  Description: Charity Donation - Red Cross
  Category: Charity
  Attachments: 
    - donation_receipt.pdf
    - tax_letter.pdf
```

---

## Security & Privacy

**File Security**:
- Files stored locally on your computer
- No cloud upload (unless you manually sync)
- Password-protect your computer for security

**Sensitive Documents**:
- Use caution with sensitive information
- Consider encrypting backup drives
- Don't share screen during demos

---

## Getting Help

**Feature Issues**:
- Check docs/ATTACHMENTS_IMPLEMENTATION.md for technical details
- Report bugs on GitHub
- Contact support

**Feature Requests**:
- Want OCR to auto-read receipts?
- Need cloud sync?
- Suggest improvements!

---

## Summary

✅ **Attach any file type** to transactions  
✅ **View images inline** in the app  
✅ **Open PDFs** in your PDF reader  
✅ **Multiple attachments** per transaction  
✅ **Never lose receipts** again  

**Start using attachments today to better document your financial transactions!**
