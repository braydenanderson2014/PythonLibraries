"""
Quick test to verify JSON account removal works
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.account import AccountManager
from src.account_db import AccountDatabaseManager
from src.hasher import verify_hash
from assets.Logger import Logger

logger = Logger()

# Test the removal directly
json_mgr = AccountManager()
db_mgr = AccountDatabaseManager()

print("=" * 60)
print("BEFORE MIGRATION")
print("=" * 60)

# Check what's in JSON
json_mgr.load()
print(f"\nJSON accounts: {list(json_mgr.accounts.keys())}")

# Check what's in database
db_users = db_mgr.list_users()
db_usernames = [u['username'] for u in db_users]
print(f"Database accounts: {db_usernames}")

# Pick the first JSON user to test
if json_mgr.accounts:
    test_user = list(json_mgr.accounts.keys())[0]
    print(f"\nTesting migration with user: {test_user}")
    
    # Get the password hash from JSON
    json_account = json_mgr.accounts[test_user]
    password_hash = json_account['password_hash']
    account_id = json_account['account_id']
    details = json_account.get('details', {})
    
    print(f"  Account ID: {account_id}")
    print(f"  Password Hash: {password_hash[:20]}...")
    
    # Step 1: Add to database with the existing hash
    print(f"\n[STEP 1] Adding {test_user} to database...")
    db_mgr.create_user_with_hash(test_user, password_hash, account_id, **details)
    
    # Verify it's in database
    db_user = db_mgr.get_user_by_username(test_user)
    if db_user:
        print(f"  ✓ Successfully added to database")
    else:
        print(f"  ✗ FAILED to add to database")
    
    # Step 2: Remove from JSON
    print(f"\n[STEP 2] Removing {test_user} from JSON...")
    
    # First, reload to ensure we have latest
    json_mgr.load()
    print(f"  Before removal: {test_user} in JSON? {test_user in json_mgr.accounts}")
    
    if test_user in json_mgr.accounts:
        del json_mgr.accounts[test_user]
        print(f"  Deleted from memory")
    
    # Save to file
    json_mgr.save()
    print(f"  Saved to file")
    
    # Reload from file to verify
    json_mgr.load()
    print(f"  After removal: {test_user} in JSON? {test_user in json_mgr.accounts}")
    
    if test_user not in json_mgr.accounts:
        print(f"  ✓ Successfully removed from JSON")
    else:
        print(f"  ✗ FAILED to remove from JSON")
    
    # Step 3: Verify database still has it
    print(f"\n[STEP 3] Verifying database...")
    db_user = db_mgr.get_user_by_username(test_user)
    if db_user:
        print(f"  ✓ Account still in database")
        db_hash = db_user.get('password_hash')
        if db_hash == password_hash:
            print(f"  ✓ Hash matches original")
        else:
            print(f"  ✗ Hash DOES NOT match!")
    else:
        print(f"  ✗ Account NOT in database")

print("\n" + "=" * 60)
print("AFTER MIGRATION")
print("=" * 60)

json_mgr.load()
print(f"\nJSON accounts: {list(json_mgr.accounts.keys())}")

db_users = db_mgr.list_users()
db_usernames = [u['username'] for u in db_users]
print(f"Database accounts: {db_usernames}")
