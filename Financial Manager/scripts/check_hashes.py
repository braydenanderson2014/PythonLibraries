from src.account import AccountManager
import json, os

am = AccountManager()
print('Loaded accounts:', list(am.accounts.keys()))
for u in ['admin','testuser']:
    ok = am.verify_password(u, u)
    print(f'user {u} login with password "{u}":', ok)

with open(os.path.join('resources','accounts.json')) as f:
    data = json.load(f)
print('admin stored hash:', data['admin']['password_hash'])
import src.hasher as h
print('hash(admin) salted:', h.hash_password('admin'))
print('hash(admin) legacy:', h.legacy_hash('admin'))
print('verify admin salted?', h.verify_hash(data['admin']['password_hash'],'admin'))
