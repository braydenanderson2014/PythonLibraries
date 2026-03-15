# PyInstaller Data Persistence Fix

## Problem
When running the Financial Manager as a PyInstaller bundled executable, user data (accounts, tenants, payments, etc.) would not persist between application restarts. New data would be saved during runtime but disappear when the app was closed and reopened.

## Root Cause
The application was using relative file paths based on `__file__` to store data:
```python
ACCOUNT_DB = os.path.join(os.path.dirname(__file__), '../resources/accounts.json')
```

When PyInstaller bundles an application, it extracts files to a temporary directory that gets cleaned up after the app closes. This means any data saved to these locations is lost.

## Solution
Created a new `app_paths.py` module that:

1. **Detects Runtime Environment**: Checks if running as a PyInstaller bundle using `sys.frozen`

2. **Uses Platform-Specific Persistent Directories**:
   - **Windows**: `%APPDATA%\FinancialManager`
   - **macOS**: `~/Library/Application Support/FinancialManager`
   - **Linux**: `~/.local/share/FinancialManager` (follows XDG Base Directory spec)

3. **Falls Back to Development Paths**: When running in development mode, uses the original `./resources` directory

## Implementation

### New Module: `src/app_paths.py`

This module provides centralized path management with functions:
- `get_app_data_dir()` - Returns appropriate data directory for current environment
- `get_resource_path(filename)` - Returns full path for any resource file
- Pre-computed path constants for all database files

### Files Modified

Updated all modules to import paths from `app_paths`:

**Core Data Files**:
- `src/account.py` - User accounts
- `src/tenant.py` - Tenant data  
- `src/bank.py` - Bank transactions
- `src/watchlist.py` - Watchlists
- `src/stock_data.py` - Stock data
- `src/portfolio.py` - Portfolios
- `src/budget.py` - Budgets
- `src/bank_accounts.py` - Bank account info
- `src/settings.py` - Application settings
- `src/transaction_rules.py` - Transaction rules
- `src/action_queue.py` - Scheduled actions
- `src/attachment_manager.py` - File attachments
- `src/notification_system.py` - Notification state
- `src/tenant_notification_automation.py` - Automation state

**UI Files**:
- `ui/login.py` - Login authentication
- `ui/create_user.py` - User creation
- `ui/change_pass.py` - Password changes

## Path Locations

### Development Mode
```
/workspaces/SystemCommands/Python Projects/Financial Manager/resources/
├── accounts.json
├── tenants.json
├── bank_data.json
├── ...
```

### PyInstaller Bundle (Windows)
```
C:\Users\<username>\AppData\Roaming\FinancialManager\
├── accounts.json
├── tenants.json
├── bank_data.json
├── ...
```

### PyInstaller Bundle (macOS)
```
/Users/<username>/Library/Application Support/FinancialManager/
├── accounts.json
├── tenants.json
├── bank_data.json
├── ...
```

### PyInstaller Bundle (Linux)
```
/home/<username>/.local/share/FinancialManager/
├── accounts.json
├── tenants.json
├── bank_data.json
├── ...
```

## Testing

To test the fix:

1. **Build the executable**:
   ```bash
   python build_system.py
   ```

2. **Run the executable and create data**:
   - Create a new user
   - Add tenants
   - Make payments

3. **Close the application completely**

4. **Reopen the executable**:
   - Verify user login works
   - Verify tenant data persists
   - Verify all data is intact

## Debug Utility

Run `python -m src.app_paths` to print current path configuration:
```
=== Financial Manager Path Configuration ===
Running as bundle: True
Platform: win32
App data directory: C:\Users\username\AppData\Roaming\FinancialManager
Bundle extraction dir: C:\Users\username\AppData\Local\Temp\_MEI12345

Database locations:
  Accounts: C:\Users\username\AppData\Roaming\FinancialManager\accounts.json
  Tenants: C:\Users\username\AppData\Roaming\FinancialManager\tenants.json
  ...
=============================================
```

## Benefits

✅ Data persists across application restarts  
✅ Works in both development and bundled modes  
✅ Platform-appropriate data locations  
✅ Automatic directory creation  
✅ Centralized path management  
✅ Easy to maintain and update  

## Migration

Existing users with data in the old location should:

1. Locate their old data files (in the app's installation directory)
2. Copy them to the new persistent location shown by the debug utility
3. Or simply start fresh - the app will create new empty databases

## Future Improvements

- Add automatic data migration from old to new locations
- Implement data backup/export functionality
- Add cloud sync support
- Provide user-configurable data directory option
