import hashlib

salt = 'RentTracker2025'
stored_hash = '135bf726232f2e81a4616fe1d463cb5c3d76b6abbe2eb91d4ddbf5891a2217e8'

# Test common passwords
test_passwords = ['test123', 'password', '123456', 'admin', 'test', '', '1234', 'Password123', 'Test123']

print(f"Looking for hash: {stored_hash}")
print()

for pwd in test_passwords:
    hash_result = hashlib.sha256((pwd + salt).encode()).hexdigest()
    print(f'Password: "{pwd}" -> Hash: {hash_result}')
    if hash_result == stored_hash:
        print(f'*** MATCH FOUND: Password is "{pwd}" ***')
        break
else:
    print("No matching password found in test list")
