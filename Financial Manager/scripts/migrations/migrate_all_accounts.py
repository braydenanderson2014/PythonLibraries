"""
Manual migration tool to migrate all remaining JSON accounts to database
Run this to ensure all accounts are migrated
"""
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, PROJECT_ROOT)

from src.account_migration import AccountMigration
from src.account import AccountManager

print("=" * 70)
print("ACCOUNT MIGRATION UTILITY - Manual Migration Tool")
print("=" * 70)

migration = AccountMigration()
json_mgr = AccountManager()

# Get current status
status = migration.get_migration_status()

print(f"\nCURRENT STATUS:")
print(f"  JSON-only accounts (need migration): {len(status['json_only'])}")
print(f"    {status['json_only']}")
print(f"  Database accounts: {len(status['database_only'])}")
print(f"    {status['database_only']}")

if status['needs_migration'] > 0:
    print(f"\nMIGRATING {status['needs_migration']} accounts...")
    
    for username in status['json_only']:
        print(f"\n  Migrating: {username}")
        success, message = migration.migrate_json_to_database(username)
        
        if success:
            print(f"    SUCCESS: {message}")
        else:
            print(f"    FAILED: {message}")
    
    # Show final status
    print("\n" + "=" * 70)
    status = migration.get_migration_status()
    print(f"FINAL STATUS:")
    print(f"  JSON-only accounts: {len(status['json_only'])}")
    print(f"  Database accounts: {len(status['database_only'])}")
    
    if status['needs_migration'] == 0:
        print(f"\n  SUCCESS: All accounts migrated to database!")
    else:
        print(f"\n  WARNING: {status['needs_migration']} accounts still need migration")
else:
    print(f"\nNO MIGRATION NEEDED - All accounts are already in the database!")

print("\n" + "=" * 70)
