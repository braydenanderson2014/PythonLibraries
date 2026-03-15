import os
import json
import random
import string
import sys, os
from assets.Logger import Logger
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'assets')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# Import from our local hasher module to avoid clashing with third-party 'hasher'
try:
    from .hasher import hash_password, verify_hash
    from .app_paths import ACCOUNT_DB
except ImportError:
    from hasher import hash_password, verify_hash
    from app_paths import ACCOUNT_DB

logger = Logger()

def generate_account_id(length=10):
    chars = string.ascii_letters + string.digits
    accountID = ''.join(random.SystemRandom().choice(chars) for _ in range(length))
    logger.debug("Account", f"Generated account ID: {accountID}")
    return accountID

class AccountManager:
    def __init__(self):
        self.accounts = {}
        self.load()

    def create_account(self, username, password, **details):
        if username in self.accounts:
            raise ValueError('Username already exists')
        account_id = generate_account_id()
        self.accounts[username] = {
            'account_id': account_id,
            'username': username,
            'password_hash': hash_password(password),
            'details': details
        }
        self.save()
        logger.info("Account", f"Created account for user: {username}")
        return self.accounts[username]

    def get_account(self, username):
        logger.info("Account", f"Retrieved account for user: {username}")
        return self.accounts.get(username)

    def get_account_by_id(self, account_id):
        logger.info("Account", f"Retrieved account for account ID: {account_id}")
        for acc in self.accounts.values():
            if acc['account_id'] == account_id:
                return acc
        logger.warning("Account", f"Account ID not found: {account_id}")
        return None

    def update_account(self, username, **details):
        if username not in self.accounts:
            raise ValueError('Account not found')
        self.accounts[username]['details'].update(details)
        logger.info("Account", f"Updated account for user: {username}")
        self.save()

    def verify_password(self, username, password):
        acc = self.get_account(username)
        if not acc:
            logger.warning("Account", f"Account not found: {username}")
            return False
        # Accept either the current salted hash or legacy unsalted hash
        stored = acc.get('password_hash', '')
        if verify_hash(stored, password):
            # If the stored hash matches the legacy (unsalted) form, upgrade
            # the record to the salted hash to improve future compatibility.
            from .hasher import legacy_hash, hash_password
            if stored == legacy_hash(password):
                acc['password_hash'] = hash_password(password)
                self.save()
            logger.info("Account", f"Password verified for user: {username}")
            return True
        logger.warning("Account", f"Password verification failed for user: {username}")
        return False
    
    def change_password(self, username, new_password):
        """Change password for an account"""
        if username not in self.accounts:
            raise ValueError('Account not found')
        self.accounts[username]['password_hash'] = hash_password(new_password)
        self.save()
        logger.info("Account", f"Password changed for user: {username}")
        return True

    def save(self):
        # Directory creation is handled by app_paths module
        with open(ACCOUNT_DB, 'w') as f:
            logger.info("Account", "Saving accounts to JSON file")
            logger.debug("Account", f"Accounts data: {self.accounts}")
            json.dump(self.accounts, f, indent=2)

    def load(self):
        if os.path.exists(ACCOUNT_DB):
            with open(ACCOUNT_DB, 'r') as f:
                self.accounts = json.load(f)
            logger.info("Account", "Loaded accounts from JSON file")
            logger.debug("Account", f"Accounts data: {self.accounts}")
        else:
            self.accounts = {}
            logger.info("Account", "No existing account file found; starting fresh")