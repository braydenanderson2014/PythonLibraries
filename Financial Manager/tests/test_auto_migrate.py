"""
Test if auto_migrate_on_login actually removes accounts from JSON
"""
import sys

print("=" * 60)
print("TESTING AUTO-MIGRATION ON LOGIN")
print("=" * 60)

from src.account_migration import auto_migrate_on_login
from src.account import AccountManager

# Check initial state
print("\nBEFORE migration:")
mgr = AccountManager()
mgr.load()
print(f"  JSON accounts: {list(mgr.accounts.keys())}")

# Pick a user to migrate
if mgr.accounts:
    test_user = list(mgr.accounts.keys())[0]
    print(f"\nAttempting migration for: {test_user}")
    
    result = auto_migrate_on_login(test_user)
    print(f"  Migration result: {result}")
    
    # Check final state
    print("\nAFTER migration:")
    mgr.load()
    print(f"  JSON accounts: {list(mgr.accounts.keys())}")
    
    if test_user not in mgr.accounts:
        print(f"\n  SUCCESS: {test_user} was removed from JSON")
    else:
        print(f"\n  FAILED: {test_user} is still in JSON!")
