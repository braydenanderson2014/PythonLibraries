"""
Test if the migration module can be imported successfully
"""
import sys
import traceback

print("=" * 60)
print("TESTING MIGRATION MODULE IMPORTS")
print("=" * 60)

try:
    print("\n[1] Importing src.account_migration...")
    from src.account_migration import auto_migrate_on_login
    print("    SUCCESS: auto_migrate_on_login imported")
except Exception as e:
    print(f"    FAILED: {e}")
    traceback.print_exc()

print("\nDone")
