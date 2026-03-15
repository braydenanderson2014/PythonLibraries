# Account Migration: JSON to Database

## Overview

The Financial Manager now includes automatic account migration from JSON file storage to SQLite database storage. This feature seamlessly handles the transition, maintaining security and user experience.

## How It Works

### Automatic Detection

When a user logs in successfully, the system automatically:

1. **Detects the login source**: Determines if credentials came from JSON or database
2. **Checks database status**: Verifies if the account already exists in the database
3. **Migrates if needed**: If account is in JSON but not in database, it migrates
4. **Cleans up**: Removes the user entry from JSON file after successful migration

### Step-by-Step Process

#### 1. User Logs In
```
User enters username/password → System verifies credentials
```

#### 2. Source Detection
The system checks where the credentials are stored:
- **JSON Storage**: User found in `accounts.json`
- **Database Storage**: User found in SQLite database
- **Both**: Should not happen normally (duplicate)

#### 3. Migration Check
If credentials are in JSON:
- Check if the account hash already exists in the database
- If yes: Just remove from JSON (account was previously migrated)
- If no: Perform full migration

#### 4. Migration Process
```
Copy account from JSON to database:
├── Preserve account ID (unchanged)
├── Copy password hash (no re-hashing)
├── Copy all account details
└── Remove from JSON file
```

#### 5. Cleanup
The JSON entry for that user is deleted, leaving it ready for other users.

## Technical Details

### Key Components

#### `AccountMigration` Class (`src/account_migration.py`)

Main migration handler with methods:

- **`detect_login_source(username)`**: Determines where credentials come from
  - Returns: `'json'`, `'database'`, or `None`

- **`is_hash_in_database(username)`**: Checks if account exists in database
  - Returns: `True` if in database, `False` otherwise

- **`migrate_json_to_database(username)`**: Performs the migration
  - Migrates account from JSON to database
  - Removes JSON entry
  - Returns: `(success: bool, message: str)`

- **`get_migration_status()`**: Provides overall migration statistics
  - Returns: Dict with counts and lists of users in each location

- **`migrate_all_json_users()`**: Bulk migrate all JSON users
  - Migrates all users from JSON to database
  - Returns: Dict with results for each user

#### `auto_migrate_on_login(username)` Function

Convenience function called automatically during login:

```python
def auto_migrate_on_login(username: str) -> bool:
    """Automatically migrate user on successful login"""
    # 1. Detect source
    # 2. If JSON: Migrate to database
    # 3. Return success status
```

### Login Integration

The login dialog in `ui/login.py` calls the migration function after successful authentication:

```python
if account_manager.verify_password(username, password):
    # ... existing login code ...
    
    # Attempt automatic migration from JSON to database
    try:
        from src.account_migration import auto_migrate_on_login
        auto_migrate_on_login(username)
    except Exception as e:
        # Don't fail login due to migration issues
        logger.warning("LoginDialog", f"Auto-migration failed (non-blocking): {e}")
    
    # Continue with normal login
```

### Database Changes

Added new method to `AccountDatabaseManager` (`src/account_db.py`):

- **`create_user_with_hash(username, password_hash, account_id, **details)`**
  - Creates user account using existing password hash
  - Used specifically for migration from JSON
  - Preserves hash integrity during migration

## Migration States

```
Before Migration:
├── accounts.json
│   └── user_data (with password_hash)
└── database (empty or partial)

After Migration:
├── accounts.json
│   └── (user entry removed)
└── database
    └── user_data (with original password_hash)
```

## Testing

### Using the Test Script

Run `test_migration.py` to test migration functionality:

```bash
python test_migration.py
```

**Available Tests:**

1. **Check migration status**
   - Shows current state of JSON vs database users
   - Identifies users needing migration

2. **Test single user migration**
   - Migrates a specific user
   - Shows before/after source

3. **Test auto-migration on login**
   - Tests the convenience function
   - Simulates login-time migration

4. **Migrate all JSON users**
   - Bulk migrates all users
   - Shows results for each user

### Test Output Example

```
Migration Status:
  JSON Users: 3
  Database Users: 2
  Users in both: 0
  JSON-only users: ['user1', 'user2', 'user3']
  Database-only users: ['user4', 'user5']
  Needs migration: 3
```

## Security Considerations

✓ **Password Hash Preservation**: Original password hashes are preserved (no re-hashing)
✓ **Account ID Preservation**: Original account IDs remain unchanged
✓ **Duplicate Prevention**: Database uniqueness constraints prevent duplicates
✓ **Atomic Operations**: Each migration is atomic (succeeds or rolls back completely)
✓ **Non-Blocking**: Migration failures don't prevent user login
✓ **Logging**: All migration operations are logged for auditing

## Common Scenarios

### Scenario 1: New User, Never Logged In
```
User creates account via JSON → First login
Auto-migration triggers → Moves to database
JSON entry removed
Result: User fully migrated ✓
```

### Scenario 2: User Already in Database
```
User already exists in database
User logs in with JSON credentials still present
Auto-migration detects duplicate
Just removes JSON entry (no migration needed)
Result: Cleanup completed ✓
```

### Scenario 3: Migration Failure
```
User logs in
Auto-migration attempted
Error occurs (disk full, permissions, etc.)
Migration fails gracefully (non-blocking)
User still logs in successfully
Error logged for investigation
Result: User unaffected ✓
```

## Configuration

### Switching Storage Backends

To explicitly switch backends:

```python
from src.account_unified import UnifiedAccountManager

manager = UnifiedAccountManager()
manager.set_backend('database', save_config=True)
```

### Auto-Detection

The system automatically detects the backend:

1. Checks `account_config.json` for configured backend
2. Checks if database exists and has users
3. Defaults to JSON if neither condition is met

## Troubleshooting

### Issue: Migration seems slow
**Solution**: Migration is I/O bound. Check disk speed and available resources.

### Issue: Some users not migrated
**Solution**: Check logs for specific error messages. May indicate corrupted JSON data.

### Issue: Duplicate accounts appearing
**Solution**: This shouldn't happen due to database constraints. If it occurs, run migration test to diagnose.

### Issue: JSON file still has entries after migration
**Solution**: Check that migration completed successfully. Manual cleanup can remove entries if needed.

## Manual Cleanup (if needed)

If JSON file needs manual cleanup:

```python
from src.account import AccountManager

manager = AccountManager()
manager.load()
del manager.accounts['username_to_remove']
manager.save()
```

## Future Enhancements

Potential improvements to the migration system:

- Batch migration with progress tracking
- Scheduled/background migrations
- Migration history/audit log
- Admin tool for forced re-migration
- Conflict resolution for edge cases

## Monitoring

Check migration status anytime:

```python
from src.account_migration import AccountMigration

migration = AccountMigration()
status = migration.get_migration_status()
print(status)
```

This provides:
- Total users in each storage
- List of users needing migration
- Users in both locations (anomalies)

## Support

For migration issues:

1. Check the application logs in `financial_tracker.log`
2. Run the test script to diagnose
3. Use migration status reports to identify problem areas
4. Contact support with migration status output
