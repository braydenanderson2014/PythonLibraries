"""
Test that new user creation uses the database system
"""
from src.account_db import AccountDatabaseManager
from src.account import AccountManager

db_mgr = AccountDatabaseManager()
json_mgr = AccountManager()

print("=" * 60)
print("TESTING NEW USER CREATION (Database System)")
print("=" * 60)

# Check current state
db_users_before = [u['username'] for u in db_mgr.list_users()]
json_mgr.load()
json_users_before = list(json_mgr.accounts.keys())

print(f"\nBEFORE creating new user:")
print(f"  Database accounts: {db_users_before}")
print(f"  JSON accounts: {json_users_before}")

# Create a new test user
test_username = "newuser_test"
test_password = "testpass123"

print(f"\nCreating new user: {test_username}...")

try:
    db_mgr.create_user(test_username, test_password)
    print(f"  SUCCESS: User created in database")
except Exception as e:
    print(f"  FAILED: {e}")

# Check final state
db_users_after = [u['username'] for u in db_mgr.list_users()]
json_mgr.load()
json_users_after = list(json_mgr.accounts.keys())

print(f"\nAFTER creating new user:")
print(f"  Database accounts: {db_users_after}")
print(f"  JSON accounts: {json_users_after}")

# Verify the user was created in database, not JSON
if test_username in db_users_after and test_username not in json_users_after:
    print(f"\n  SUCCESS: {test_username} created in DATABASE (not in JSON)")
elif test_username in db_users_after and test_username in json_users_after:
    print(f"\n  WARNING: {test_username} in BOTH database and JSON (should be database only)")
elif test_username in json_users_after:
    print(f"\n  FAILED: {test_username} created in JSON (should be in DATABASE)")
else:
    print(f"\n  FAILED: {test_username} not found anywhere")

print("\n" + "=" * 60)
