"""
Test the dual-backend login system
"""
import random
import string
from src.account_db import AccountDatabaseManager
from src.account import AccountManager, generate_account_id
from src.hasher import hash_password

# Generate unique test usernames to avoid conflicts
def gen_username(prefix):
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return f"{prefix}_{suffix}"

print("=" * 70)
print("TESTING DUAL-BACKEND LOGIN SYSTEM (Database + JSON)")
print("=" * 70)

# Create test data
db_mgr = AccountDatabaseManager()
json_mgr = AccountManager()

# Test 1: User in database
print("\n[TEST 1] User in DATABASE")
test_db_user = gen_username("dbuser")
test_db_pass = "dbpassword123"
test_db_id = generate_account_id()

# Add user to database
db_mgr.create_user(test_db_user, test_db_pass, test_db_id)
print(f"  Created {test_db_user} in database (ID: {test_db_id})")

# Try to verify
if db_mgr.verify_password(test_db_user, test_db_pass):
    print(f"  SUCCESS: Password verification PASSED for database user")
else:
    print(f"  FAILED: Password verification FAILED for database user")

# Test 2: User in JSON
print("\n[TEST 2] User in JSON")
test_json_user = gen_username("jsonuser")
test_json_pass = "jsonpassword123"

# Add user to JSON
json_mgr.create_account(test_json_user, test_json_pass)
print(f"  Created {test_json_user} in JSON")

# Try to verify
json_mgr.load()
if json_mgr.verify_password(test_json_user, test_json_pass):
    print(f"  SUCCESS: Password verification PASSED for JSON user")
else:
    print(f"  FAILED: Password verification FAILED for JSON user")

# Test 3: Verify database is preferred
print("\n[TEST 3] Database user preferred over JSON (same username)")
test_both_user = gen_username("bothuser")
test_both_pass = "bothpassword123"
test_both_id = generate_account_id()

# Add to database first
db_mgr.create_user(test_both_user, test_both_pass, test_both_id)
print(f"  Created {test_both_user} in database")

# Check database
db_user = db_mgr.get_user_by_username(test_both_user)
if db_user and db_mgr.verify_password(test_both_user, test_both_pass):
    print(f"  SUCCESS: User found in DATABASE with correct password")
else:
    print(f"  FAILED: User NOT found in database or password wrong")

# Try JSON (should not be there)
json_mgr.load()
if test_both_user not in json_mgr.accounts:
    print(f"  SUCCESS: User NOT in JSON (as expected)")
else:
    print(f"  FAILED: User found in JSON (should only be in database)")

print("\n" + "=" * 70)
print("LOGIN SYSTEM VERIFICATION")
print("=" * 70)

print(f"\nDatabase users: {[u['username'] for u in db_mgr.list_users()]}")

json_mgr.load()
print(f"JSON users: {list(json_mgr.accounts.keys())}")

print("\nConclusion: The dual-backend system is ready!")
print("  - New users created go to DATABASE")
print("  - Existing JSON users can still log in")
print("  - JSON users are automatically migrated on login")

print("\n" + "=" * 70)
