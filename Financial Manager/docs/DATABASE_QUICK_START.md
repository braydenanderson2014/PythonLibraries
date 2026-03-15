# Quick Start Guide: Database Performance Improvements

## What Changed?
Your rent system now handles database operations in the background, preventing the UI from freezing.

## For End Users
When you make changes (add payments, modify rent, etc.), you'll now see:
1. **Animated Progress Dialog** - A spinning animation showing work is being done
2. **Progress Messages** - Text showing what's happening (e.g., "Saving tenant data...")
3. **Responsive UI** - The UI won't freeze - you can still interact with windows
4. **Cancel Button** - Option to cancel long-running operations

## For Developers

### How to Use the New Async Save

**Simple Usage:**
```python
# In any UI component that has access to rent_tracker
self.save_tenants_async()
```

**With Callbacks:**
```python
def on_success(result):
    print("Save completed!")
    self.refresh_ui()

def on_error(error):
    print(f"Save failed: {error}")

self.save_tenants_async(
    on_success=on_success,
    on_error=on_error
)
```

### For Other Database Operations

Use `DatabaseOperationManager` for any database operation:

```python
from src.database_worker import DatabaseOperationManager

def my_database_operation():
    # Your database code here
    # This runs in background thread
    tenant = self.rent_tracker.get_tenant_by_name("John Doe")
    tenant.rent_amount = 1500
    return tenant

DatabaseOperationManager.execute_with_progress(
    parent_widget=self,
    operation=my_database_operation,
    on_success=lambda result: print(f"Done! {result}"),
    dialog_title="Updating Tenant",
    dialog_message="Updating tenant information..."
)
```

### With Progress Reporting

For operations that need to report progress:

```python
def bulk_operation(progress_callback=None):
    total = 100
    for i in range(total):
        # Do work
        if progress_callback:
            percentage = int((i / total) * 100)
            progress_callback(percentage, f"Processing item {i+1}/{total}")
    return "Complete"

DatabaseOperationManager.execute_with_progress(
    parent_widget=self,
    operation=bulk_operation,
    dialog_title="Bulk Operation",
    dialog_message="Processing items...",
    show_progress=True  # Enable progress reporting
)
```

## Important Notes

1. **Automatic in rent_management_tab.py**: All save operations in the rent management tab already use the async version - no changes needed!

2. **Thread-Safe**: Operations run in background threads, but PyQt signals handle UI updates safely.

3. **Error Handling**: Errors are automatically displayed in message boxes unless you provide custom error handlers.

4. **Cancellation**: Users can click "Cancel" in the progress dialog to abort operations (where supported).

## Migrating Other Components

If you have other components that do heavy database operations:

1. **Import the manager:**
   ```python
   from src.database_worker import DatabaseOperationManager
   ```

2. **Wrap your operation:**
   ```python
   # Instead of:
   self.some_slow_database_operation()
   
   # Do:
   DatabaseOperationManager.execute_with_progress(
       parent_widget=self,
       operation=self.some_slow_database_operation,
       dialog_title="Working...",
       dialog_message="Processing..."
   )
   ```

## Troubleshooting

### "Module not found" errors
Make sure the paths are correct. The database_worker module is in `src/database_worker.py`.

### Operations not showing progress
Set `show_progress=True` and ensure your operation accepts a `progress_callback` parameter.

### UI still freezing
Check if you're doing heavy work in the UI thread before/after the async operation. Move all heavy work into the operation function.

## Performance Tips

1. **Batch Operations**: Process multiple items in one database transaction
2. **Avoid UI Updates in Loops**: Use callbacks after operation completes
3. **Progress Reporting**: For operations > 1 second, add progress reporting
4. **Cancel Support**: For very long operations, check cancellation flag

## Example: Complete Flow

```python
class MyWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.rent_tracker = rent_tracker
        
    def handle_button_click(self):
        """User clicked a button that needs database work"""
        
        def do_work():
            # This runs in background thread
            tenant = self.rent_tracker.get_tenant_by_name("Jane Doe")
            tenant.rent_amount = 2000
            self.rent_tracker.save_tenants()
            return tenant
        
        def on_complete(tenant):
            # This runs in UI thread after work completes
            QMessageBox.information(
                self, 
                "Success", 
                f"Updated {tenant.name} successfully!"
            )
            self.refresh_display()
        
        def on_error(error):
            # This runs in UI thread if error occurs
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to update: {error}"
            )
        
        # Execute with progress dialog
        DatabaseOperationManager.execute_with_progress(
            parent_widget=self,
            operation=do_work,
            on_success=on_complete,
            on_error=on_error,
            dialog_title="Updating Tenant",
            dialog_message="Saving changes..."
        )
```

## Questions?
Check the full documentation in `DATABASE_PERFORMANCE_IMPROVEMENTS.md` or examine `src/database_worker.py` for implementation details.
