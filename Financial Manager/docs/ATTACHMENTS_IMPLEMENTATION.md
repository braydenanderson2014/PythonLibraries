# Transaction Attachments Implementation Guide

**Feature**: Transaction Attachments/Receipts  
**Status**: ✅ Complete  
**Date**: December 4, 2025

---

## Overview

The transaction attachments feature allows users to attach files (receipts, invoices, documents) to any transaction for record-keeping, tax documentation, and expense reporting.

## Features Implemented

### 1. File Attachment Support ✅
- Attach multiple files per transaction
- Supported file types: Images (JPEG, PNG, GIF, BMP, WebP), PDFs, Documents, and all other file types
- Files are copied to `resources/attachments/` with unique names to prevent collisions
- Original filenames are preserved in metadata

### 2. AttachmentManager Utility Class ✅
**Location**: `src/attachment_manager.py`

**Key Methods**:
- `add_attachment(source_path, transaction_id)` - Add a file attachment
- `delete_attachment(attachment_data)` - Remove an attachment file
- `get_attachment_path(attachment_data)` - Get full path to attachment
- `get_file_icon(file_type)` - Get icon/emoji for file type
- `format_file_size(size_bytes)` - Human-readable file size
- `cleanup_orphaned_files(active_attachments)` - Remove unused files

**Attachment Metadata Structure**:
```python
{
    'filename': 'receipt_2024-12-01.jpg',           # Original filename
    'stored_filename': 'abc123def456_20241201_153045.jpg',  # Unique stored name
    'path': '/path/to/resources/attachments/abc123def456_20241201_153045.jpg',  # Full path
    'relative_path': 'resources/attachments/abc123def456_20241201_153045.jpg',  # Relative path
    'type': 'image/jpeg',                           # MIME type
    'size': 125000,                                 # File size in bytes
    'uploaded_date': '2024-12-01T15:30:45',        # ISO timestamp
    'transaction_id': 'tx_abc123'                   # Associated transaction (optional)
}
```

### 3. Transaction Model Updates ✅
**Location**: `src/bank.py`

**Changes to Transaction class**:
- Added `attachments` parameter to `__init__`
- Added `has_attachments()` method
- Added `attachments` field to `to_dict()` serialization
- Updated `Bank.add_transaction()` to accept `attachments` parameter

### 4. UI Integration ✅

#### Add Transaction Dialog
**Location**: `ui/financial_tracker.py` - `AddTransactionDialog`

**Features**:
- File picker button to add attachments
- Attachments list table showing:
  - File type icon (📎, 🖼️, 📕, etc.)
  - Filename
  - File size (human-readable)
  - View and Delete action buttons
- Attachments are included when saving transaction

#### Transactions Table
**Added Features**:
- New column: 📎 (Attachment indicator)
- Shows "📎 X" button when transaction has attachments (X = number of attachments)
- Click button to view attachments
- Empty cell when no attachments

#### Attachment Viewer Dialog
**Location**: `ui/financial_tracker.py` - `AttachmentViewerDialog`

**Features**:
- View multiple attachments with Previous/Next navigation
- Image preview for supported formats (JPEG, PNG, GIF, BMP, WebP)
- PDF placeholder with "Open in System Viewer" option
- File type icons for other document types
- Opens files in system default application
- File info display: filename, size, position (X/N)
- Cross-platform support (Windows, macOS, Linux)

### 5. File Storage ✅
**Directory**: `resources/attachments/`

**File Naming Convention**:
```
{hash}_{timestamp}{extension}
```
- `hash`: First 12 characters of MD5 hash for uniqueness
- `timestamp`: YYYYMMDD_HHMMSS format
- Example: `a1b2c3d4e5f6_20241204_143022.jpg`

**Benefits**:
- Prevents filename collisions
- Preserves file extensions
- Allows tracking of upload time
- Original filenames stored in metadata

---

## Usage Guide

### Adding Attachments to a Transaction

1. Open "Add Transaction" dialog
2. Fill in transaction details (amount, description, etc.)
3. Scroll down to "Attachments" section
4. Click "📎 Add Attachment" button
5. Select file(s) from file picker
6. Files appear in attachments list
7. Click "OK" to save transaction with attachments

### Viewing Attachments

**From Transactions Table**:
1. Locate transaction with 📎 icon in attachments column
2. Click the "📎 X" button
3. Attachment viewer opens

**Features**:
- Use "← Previous" / "Next →" buttons to navigate
- Click "Open in System Viewer" to open in default app (e.g., Photos, Adobe Reader)
- Images display inline
- PDFs and other files show icon with open option

### Deleting Attachments

**During Transaction Creation**:
1. In Add Transaction dialog
2. Find attachment in list
3. Click "Delete" button next to attachment
4. File is removed from storage

**Note**: Currently, attachments cannot be edited after transaction creation. To modify attachments, delete and recreate the transaction.

---

## Technical Implementation

### Data Flow

1. **User Selects File** → File picker dialog
2. **File Upload** → `AttachmentManager.add_attachment()`
   - Copies file to `resources/attachments/`
   - Generates unique filename
   - Creates metadata dict
3. **Store Metadata** → Added to `Transaction.attachments` list
4. **Save Transaction** → `Bank.add_transaction(attachments=...)`
5. **Persist to JSON** → `bank_data.json` includes attachment metadata
6. **Display** → Transactions table shows 📎 indicator
7. **View** → `AttachmentViewerDialog` loads file from stored path

### File Operations

#### Adding File
```python
from src.attachment_manager import AttachmentManager

manager = AttachmentManager()
attachment_data = manager.add_attachment('/path/to/receipt.jpg')
# Returns metadata dict with stored path, size, type, etc.
```

#### Viewing File
```python
file_path = manager.get_attachment_path(attachment_data)
# Opens in system viewer using os.startfile (Windows), open (macOS), or xdg-open (Linux)
```

#### Deleting File
```python
manager.delete_attachment(attachment_data)
# Removes file from resources/attachments/
```

### Security & Storage

**File Isolation**:
- All attachments stored in dedicated `resources/attachments/` folder
- Files renamed with hash-based unique names
- Original filenames preserved in metadata for display

**File Cleanup**:
- Use `AttachmentManager.cleanup_orphaned_files()` to remove files no longer referenced by any transaction
- Recommended to run periodically (e.g., on app startup or manual cleanup)

**Storage Considerations**:
- No file size limits enforced (system limits apply)
- Consider implementing size limits for production use
- Monitor `resources/attachments/` folder size

---

## Code Examples

### Creating Transaction with Attachment

```python
from src.bank import Bank
from src.attachment_manager import AttachmentManager

# Initialize
bank = Bank()
attachment_manager = AttachmentManager()

# Add attachment
attachment = attachment_manager.add_attachment('/path/to/receipt.pdf')

# Create transaction with attachment
bank.add_transaction(
    amount=45.99,
    desc='Office Supplies',
    account='Business Checking',
    type_='out',
    category='Business Expense',
    user_id='user123',
    attachments=[attachment]
)
```

### Viewing Transaction Attachments

```python
# Get transaction
transactions = bank.list_transactions(user_id='user123')
tx = transactions[0]

# Check for attachments
if tx.get('attachments'):
    print(f"Transaction has {len(tx['attachments'])} attachment(s)")
    
    # View first attachment
    attachment = tx['attachments'][0]
    file_path = attachment_manager.get_attachment_path(attachment)
    print(f"Attachment path: {file_path}")
```

### Cleanup Orphaned Files

```python
# Collect all attachments from all transactions
all_attachments = []
for tx in bank.list_transactions():
    all_attachments.extend(tx.get('attachments', []))

# Remove files not referenced
deleted_count = attachment_manager.cleanup_orphaned_files(all_attachments)
print(f"Removed {deleted_count} orphaned attachment files")
```

---

## File Type Icons

The system displays appropriate icons for different file types:

| Icon | File Type |
|------|-----------|
| 🖼️ | Images (JPEG, PNG, GIF, BMP, WebP) |
| 📕 | PDF Documents |
| 📝 | Text Files |
| 🎥 | Videos |
| 🎵 | Audio Files |
| 📊 | Spreadsheets (Excel, CSV) |
| 📄 | Word Documents |
| 📦 | Archives (ZIP, TAR, etc.) |
| 📎 | Other File Types |

---

## Testing

### Manual Testing Checklist

- [ ] Add single attachment to transaction
- [ ] Add multiple attachments to transaction
- [ ] View image attachment (displays inline)
- [ ] View PDF attachment (shows placeholder)
- [ ] Open attachment in system viewer
- [ ] Navigate between multiple attachments (Previous/Next)
- [ ] Delete attachment from transaction
- [ ] Verify attachment persists after saving
- [ ] Verify attachment indicator shows in table
- [ ] Test with various file types (images, PDFs, docs, etc.)
- [ ] Verify file copied to resources/attachments/
- [ ] Verify unique filenames prevent collisions

### Automated Testing

Create test file: `tests/test_attachment_feature.py`

```python
import os
import tempfile
from src.bank import Bank
from src.attachment_manager import AttachmentManager

def test_add_attachment():
    """Test adding an attachment"""
    manager = AttachmentManager()
    
    # Create a temporary test file
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
        temp_file.write(b'Test content')
        temp_path = temp_file.name
    
    try:
        # Add attachment
        attachment = manager.add_attachment(temp_path)
        
        # Verify metadata
        assert 'filename' in attachment
        assert 'stored_filename' in attachment
        assert 'size' in attachment
        assert 'type' in attachment
        
        # Verify file was copied
        stored_path = attachment['path']
        assert os.path.exists(stored_path)
        
        # Cleanup
        manager.delete_attachment(attachment)
        assert not os.path.exists(stored_path)
        
        print("✓ Attachment add/delete test passed")
    finally:
        # Remove temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)

def test_transaction_with_attachment():
    """Test creating transaction with attachment"""
    bank = Bank()
    manager = AttachmentManager()
    
    # Create test file
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
        temp_file.write(b'\xff\xd8\xff\xe0')  # JPEG header
        temp_path = temp_file.name
    
    try:
        # Add attachment
        attachment = manager.add_attachment(temp_path)
        
        # Create transaction
        bank.add_transaction(
            amount=100.00,
            desc='Test Transaction',
            account='Checking',
            type_='out',
            category='Test',
            user_id='test_user',
            attachments=[attachment]
        )
        
        # Verify transaction has attachment
        transactions = bank.list_transactions(user_id='test_user')
        assert len(transactions) > 0
        
        tx = transactions[0]
        assert 'attachments' in tx
        assert len(tx['attachments']) == 1
        assert tx['attachments'][0]['filename'] == os.path.basename(temp_path)
        
        print("✓ Transaction with attachment test passed")
        
        # Cleanup
        manager.delete_attachment(attachment)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

if __name__ == '__main__':
    test_add_attachment()
    test_transaction_with_attachment()
    print("\n✓ All attachment tests passed!")
```

---

## Future Enhancements

### Potential Improvements

1. **Drag-and-Drop Support**
   - Drag files directly into Add Transaction dialog
   - Drop files onto transactions table to attach

2. **Thumbnail Previews**
   - Show small image thumbnails in attachments list
   - Grid view for multiple attachments

3. **Attachment Editing**
   - Edit attachments for existing transactions
   - Add/remove attachments without recreating transaction

4. **Cloud Storage Integration**
   - Option to store attachments in cloud (Google Drive, Dropbox, etc.)
   - Sync attachments across devices

5. **OCR (Optical Character Recognition)**
   - Extract text from receipt images
   - Auto-populate transaction amount/merchant from receipt

6. **File Size Limits**
   - Configurable max file size
   - Warning when uploading large files

7. **Compression**
   - Auto-compress large images
   - Optimize PDFs

8. **Bulk Operations**
   - Export all attachments for date range
   - Zip attachments for backup
   - Import transactions with attachments from zip

9. **Advanced Viewer**
   - Built-in PDF viewer (using PyMuPDF or similar)
   - Image editing (crop, rotate, adjust)
   - Annotation support

10. **Search & Filters**
    - Search transactions by attachment properties
    - Filter by file type
    - Find transactions with/without attachments

---

## Troubleshooting

### Common Issues

**Q: Attachments not showing in table**  
A: Ensure transaction has `attachments` field populated and not empty list

**Q: "File not found" error when viewing**  
A: File may have been moved/deleted from `resources/attachments/` folder. Check file exists at stored path.

**Q: Images not displaying in viewer**  
A: Verify file is a supported image format and not corrupted. Check file permissions.

**Q: "Open in System Viewer" not working**  
A: Ensure system has default application for file type. Try opening file manually from folder.

**Q: Large number of orphaned files**  
A: Run `AttachmentManager.cleanup_orphaned_files()` to remove unused files

---

## Summary

The transaction attachments feature is now fully implemented with:

✅ File upload and storage  
✅ Multiple attachments per transaction  
✅ Visual indicators in UI  
✅ Attachment viewer with navigation  
✅ Cross-platform file opening  
✅ Comprehensive metadata tracking  
✅ File cleanup utilities  

This feature enhances the Financial Manager by enabling proper documentation of transactions, supporting tax preparation, expense reporting, and record-keeping needs.
