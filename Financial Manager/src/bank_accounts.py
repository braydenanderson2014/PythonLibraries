"""
Bank Account Management System
Supports multiple real bank accounts for each user
"""

import json
import os
from datetime import datetime
try:
    from .app_paths import BANK_ACCOUNTS_FILE
except ImportError:
    from app_paths import BANK_ACCOUNTS_FILE

from assets.Logger import Logger
logger = Logger()
class BankAccount:
    def __init__(self, account_id=None, bank_name="", account_type="", account_name="", 
                 account_number="", user_id="", initial_balance=0.0, active=True):
        self.account_id = account_id or self.generate_account_id()
        self.bank_name = bank_name  # e.g., "Tab Bank", "Granite Credit Union", "Mountain America"
        self.account_type = account_type  # e.g., "Checking", "Savings", "Credit Card", "Investment"
        self.account_name = account_name  # User-friendly name like "Main Checking", "Emergency Savings"
        self.account_number = account_number  # Last 4 digits or masked number
        self.user_id = user_id
        self.initial_balance = initial_balance  # Starting balance when account was added
        self.active = active  # Whether account is still active
        self.created_date = datetime.now().isoformat()
        logger.info("BankAccount", f"Initialized bank account: {self.get_display_name()}")
    
    def generate_account_id(self):
        """Generate a unique account ID"""
        return f"acct_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(datetime.now()) % 10000:04d}"
    
    def get_display_name(self):
        """Get a user-friendly display name for the account"""
        parts = []
        if self.bank_name:
            parts.append(self.bank_name)
        if self.account_name:
            parts.append(self.account_name)
        elif self.account_type:
            parts.append(self.account_type)
        
        if self.account_number:
            parts.append(f"...{self.account_number[-4:]}")
            
        return " - ".join(parts) if parts else "Unnamed Account"
    
    def to_dict(self):
        return {
            'account_id': self.account_id,
            'bank_name': self.bank_name,
            'account_type': self.account_type,
            'account_name': self.account_name,
            'account_number': self.account_number,
            'user_id': self.user_id,
            'initial_balance': self.initial_balance,
            'active': self.active,
            'created_date': self.created_date
        }
    
    @classmethod
    def from_dict(cls, data):
        account = cls()
        for key, value in data.items():
            if hasattr(account, key):
                setattr(account, key, value)
        return account

class BankAccountManager:
    def __init__(self):
        self.accounts = []
        self.load_accounts()
    
    def load_accounts(self):
        """Load bank accounts from file"""
        if os.path.exists(BANK_ACCOUNTS_FILE):
            try:
                with open(BANK_ACCOUNTS_FILE, 'r') as f:
                    content = f.read().strip()
                    if content:
                        data = json.loads(content)
                        self.accounts = [BankAccount.from_dict(acc) for acc in data]
                    else:
                        self.accounts = []
            except Exception as e:
                logger.error("BankAccountManager", f"Error loading bank accounts: {e}")
                self.accounts = []
        else:
            self.accounts = []
            self.create_default_accounts()
    
    def create_default_accounts(self):
        """Create some default accounts for users"""
        # Note: These would typically be created by users through the UI
        logger.info("BankAccountManager", "No bank accounts file found. Users can add accounts through the interface.")
    
    def save_accounts(self):
        """Save bank accounts to file"""
        try:
            os.makedirs(os.path.dirname(BANK_ACCOUNTS_FILE), exist_ok=True)
            with open(BANK_ACCOUNTS_FILE, 'w') as f:
                json.dump([acc.to_dict() for acc in self.accounts], f, indent=2)
        except Exception as e:
            logger.error("BankAccountManager", f"Error saving bank accounts: {e}")
    
    def add_account(self, bank_account):
        """Add a new bank account"""
        self.accounts.append(bank_account)
        self.save_accounts()
        logger.info("BankAccountManager", f"Added new bank account: {bank_account.get_display_name()}")
        return bank_account
    
    def remove_account(self, account_id):
        """Remove a bank account (mark as inactive)"""
        for account in self.accounts:
            if account.account_id == account_id:
                account.active = False
                self.save_accounts()
                logger.info("BankAccountManager", f"Removed bank account: {account.get_display_name()}")
                return True
        return False
    
    def get_user_accounts(self, user_id):
        """Get all active accounts for a specific user"""
        return [acc for acc in self.accounts if acc.user_id == user_id and acc.active]
    
    def get_account(self, account_id):
        """Get a specific account by ID"""
        for account in self.accounts:
            if account.account_id == account_id:
                return account
        return None
    
    def list_accounts(self):
        """Get all accounts (for net worth calculations)"""
        return self.accounts
    
    def get_account_choices(self, user_id):
        """Get list of account choices for dropdowns"""
        user_accounts = self.get_user_accounts(user_id)
        return [(acc.account_id, acc.get_display_name()) for acc in user_accounts]
    
    def update_account(self, account_id, **kwargs):
        """Update an existing account"""
        account = self.get_account(account_id)
        if account:
            for key, value in kwargs.items():
                if hasattr(account, key):
                    setattr(account, key, value)
            self.save_accounts()
            logger.info("BankAccountManager", f"Updated bank account: {account.get_display_name()}")
            return account
        return None
    
    def get_accounts_by_bank(self, user_id, bank_name):
        """Get all accounts for a user at a specific bank"""
        user_accounts = self.get_user_accounts(user_id)
        logger.info("BankAccountManager", f"Retrieved accounts for user {user_id} at bank {bank_name}")
        return [acc for acc in user_accounts if acc.bank_name.lower() == bank_name.lower()]
    
    def get_accounts_by_type(self, user_id, account_type):
        """Get all accounts for a user of a specific type"""
        user_accounts = self.get_user_accounts(user_id)
        logger.info("BankAccountManager", f"Retrieved accounts for user {user_id} of type {account_type}")
    
    def calculate_account_balance(self, account_id, bank_instance=None):
        """Calculate current balance for an account based on transactions"""
        account = self.get_account(account_id)
        if not account:
            logger.warning("BankAccountManager", f"Account ID not found: {account_id}")
            return 0.0
        
        balance = account.initial_balance
        
        if bank_instance:
            # Get all transactions for this account
            transactions = bank_instance.list_transactions()
            account_transactions = [t for t in transactions if t.get('account_id') == account_id]
            
            for transaction in account_transactions:
                if transaction['type'] == 'in':
                    balance += transaction['amount']
                else:
                    balance -= transaction['amount']
        
        logger.info("BankAccountManager", f"Calculated balance for account {account_id}: {balance}")
        return balance
