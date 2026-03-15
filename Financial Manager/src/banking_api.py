"""
Banking API Integration Module

This module provides integration with banking APIs (Plaid, Yodlee, Open Banking, etc.)
to allow users to link their real bank accounts and automatically import transactions.
"""

import json
import os
import requests
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple
from assets.Logger import Logger

try:
    from .app_paths import BANKING_API_CONFIG_FILE, LINKED_ACCOUNTS_FILE
    from .bank import Transaction, generate_identifier
except ImportError:
    from app_paths import BANKING_API_CONFIG_FILE, LINKED_ACCOUNTS_FILE
    from bank import Transaction, generate_identifier

# Configure logging
logger = Logger()


class BankingAPIProvider:
    """Base class for banking API providers"""
    
    def __init__(self, credentials: Dict[str, str]):
        logger.debug("BankingAPIProvider", f"Initializing provider with credentials")
        self.credentials = credentials
        self.access_token = None
    
    def authenticate(self) -> bool:
        """Authenticate with the banking API"""
        raise NotImplementedError("Subclasses must implement authenticate()")
    
    def get_accounts(self) -> List[Dict[str, Any]]:
        """Get list of linked bank accounts"""
        raise NotImplementedError("Subclasses must implement get_accounts()")
    
    def get_transactions(self, account_id: str, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Get transactions for a specific account"""
        raise NotImplementedError("Subclasses must implement get_transactions()")
    
    def get_balance(self, account_id: str) -> Dict[str, float]:
        """Get current balance for an account"""
        raise NotImplementedError("Subclasses must implement get_balance()")


class PlaidProvider(BankingAPIProvider):
    """Plaid API integration (https://plaid.com/)"""
    
    BASE_URL = "https://sandbox.plaid.com"  # Use sandbox for development
    
    def __init__(self, credentials: Dict[str, str]):
        logger.debug("PlaidProvider", "Initializing Plaid provider")
        super().__init__(credentials)
        self.client_id = credentials.get('client_id')
        self.secret = credentials.get('secret')
        self.environment = credentials.get('environment', 'sandbox')
        
        # Update base URL based on environment
        if self.environment == 'production':
            self.BASE_URL = "https://production.plaid.com"
        elif self.environment == 'development':
            self.BASE_URL = "https://development.plaid.com"
        
        logger.debug("PlaidProvider", f"Plaid environment: {self.environment}")
    
    def authenticate(self) -> bool:
        """Plaid uses access tokens per account, not global auth"""
        # Validation check
        if not self.client_id or not self.secret:
            logger.error("PlaidProvider", "Plaid credentials missing")
            return False
        logger.info("PlaidProvider", "Plaid authentication validation passed")
        return True
    
    def exchange_public_token(self, public_token: str) -> str:
        """Exchange public token for access token (Plaid Link flow)"""
        logger.info("PlaidProvider", "Exchanging public token for access token")
        try:
            response = requests.post(
                f"{self.BASE_URL}/item/public_token/exchange",
                json={
                    "client_id": self.client_id,
                    "secret": self.secret,
                    "public_token": public_token
                }
            )
            response.raise_for_status()
            data = response.json()
            logger.debug("PlaidProvider", "Public token exchanged successfully")
            return data['access_token']
        except Exception as e:
            logger.error("PlaidProvider", f"Failed to exchange public token: {e}")
            return None
    
    def get_accounts(self, access_token: str) -> List[Dict[str, Any]]:
        """Get accounts associated with an access token"""
        logger.debug("PlaidProvider", "Retrieving accounts from Plaid")
        try:
            response = requests.post(
                f"{self.BASE_URL}/accounts/get",
                json={
                    "client_id": self.client_id,
                    "secret": self.secret,
                    "access_token": access_token
                }
            )
            response.raise_for_status()
            data = response.json()
            
            accounts = []
            for account in data.get('accounts', []):
                accounts.append({
                    'account_id': account['account_id'],
                    'name': account['name'],
                    'official_name': account.get('official_name'),
                    'type': account['type'],
                    'subtype': account['subtype'],
                    'mask': account.get('mask'),  # Last 4 digits
                    'balance_current': account['balances'].get('current'),
                    'balance_available': account['balances'].get('available'),
                    'currency': account['balances'].get('iso_currency_code', 'USD')
                })
            
            logger.info("PlaidProvider", f"Retrieved {len(accounts)} accounts from Plaid")
            return accounts
        except Exception as e:
            logger.error("PlaidProvider", f"Failed to get accounts: {e}")
            return []
    
    def get_transactions(self, access_token: str, start_date: date, end_date: date, account_ids: List[str] = None) -> List[Dict[str, Any]]:
        """Get transactions from Plaid"""
        logger.debug("PlaidProvider", f"Retrieving transactions from {start_date} to {end_date}")
        try:
            request_data = {
                "client_id": self.client_id,
                "secret": self.secret,
                "access_token": access_token,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
            
            if account_ids:
                request_data['account_ids'] = account_ids
                logger.debug("PlaidProvider", f"Filtering for {len(account_ids)} specific account(s)")
            
            response = requests.post(
                f"{self.BASE_URL}/transactions/get",
                json=request_data
            )
            response.raise_for_status()
            data = response.json()
            
            transactions = []
            for tx in data.get('transactions', []):
                transactions.append({
                    'transaction_id': tx['transaction_id'],
                    'account_id': tx['account_id'],
                    'amount': abs(tx['amount']),  # Plaid uses negative for expenses
                    'type': 'out' if tx['amount'] > 0 else 'in',  # Plaid positive = expense
                    'date': tx['date'],
                    'name': tx['name'],
                    'merchant_name': tx.get('merchant_name'),
                    'category': tx.get('category', []),  # List of categories
                    'pending': tx['pending'],
                    'payment_channel': tx.get('payment_channel'),
                    'location': tx.get('location', {}),
                    'original_description': tx.get('original_description')
                })
            
            logger.info("PlaidProvider", f"Retrieved {len(transactions)} transactions from Plaid")
            return transactions
        except Exception as e:
            logger.error("PlaidProvider", f"Failed to get transactions: {e}")
            return []
    
    def get_balance(self, access_token: str, account_id: str) -> Dict[str, float]:
        """Get balance for specific account"""
        logger.debug("PlaidProvider", f"Retrieving balance for account: {account_id}")
        accounts = self.get_accounts(access_token)
        for account in accounts:
            if account['account_id'] == account_id:
                logger.debug("PlaidProvider", f"Balance found: ${account['balance_current']}")
                return {
                    'current': account['balance_current'],
                    'available': account['balance_available']
                }
        logger.warning("PlaidProvider", f"Account {account_id} not found")
        return {}


class MockBankingProvider(BankingAPIProvider):
    """Mock provider for testing without real API credentials"""
    
    def __init__(self, credentials: Dict[str, str]):
        logger.debug("MockBankingProvider", "Initializing Mock provider")
        super().__init__(credentials)
    
    def authenticate(self) -> bool:
        """Mock authentication"""
        logger.info("MockBankingProvider", "Mock provider: Authentication successful")
        return True
    
    def get_accounts(self) -> List[Dict[str, Any]]:
        """Return mock accounts"""
        logger.debug("MockBankingProvider", "Returning mock accounts")
        return [
            {
                'account_id': 'mock_checking_001',
                'name': 'Mock Checking Account',
                'official_name': 'Mock Bank Checking',
                'type': 'depository',
                'subtype': 'checking',
                'mask': '1234',
                'balance_current': 5000.00,
                'balance_available': 4800.00,
                'currency': 'USD'
            },
            {
                'account_id': 'mock_savings_001',
                'name': 'Mock Savings Account',
                'official_name': 'Mock Bank Savings',
                'type': 'depository',
                'subtype': 'savings',
                'mask': '5678',
                'balance_current': 15000.00,
                'balance_available': 15000.00,
                'currency': 'USD'
            }
        ]
    
    def get_transactions(self, account_id: str, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Return mock transactions"""
        logger.debug("MockBankingProvider", f"Generating mock transactions for {account_id}")
        transactions = []
        current_date = start_date
        
        # Generate some sample transactions
        sample_transactions = [
            {'name': 'Grocery Store', 'amount': 75.50, 'type': 'out', 'category': ['Food', 'Groceries']},
            {'name': 'Electric Company', 'amount': 120.00, 'type': 'out', 'category': ['Utilities', 'Electric']},
            {'name': 'Salary Deposit', 'amount': 3000.00, 'type': 'in', 'category': ['Income', 'Salary']},
            {'name': 'Gas Station', 'amount': 45.00, 'type': 'out', 'category': ['Transportation', 'Gas']},
            {'name': 'Restaurant', 'amount': 55.25, 'type': 'out', 'category': ['Food', 'Dining']},
            {'name': 'Online Shopping', 'amount': 89.99, 'type': 'out', 'category': ['Shopping', 'Online']},
        ]
        
        day_counter = 0
        while current_date <= end_date:
            # Add 1-2 transactions per week
            if day_counter % 3 == 0:
                tx = sample_transactions[day_counter % len(sample_transactions)]
                transactions.append({
                    'transaction_id': f'mock_tx_{current_date.isoformat()}_{day_counter}',
                    'account_id': account_id,
                    'amount': tx['amount'],
                    'type': tx['type'],
                    'date': current_date.isoformat(),
                    'name': tx['name'],
                    'merchant_name': tx['name'],
                    'category': tx['category'],
                    'pending': False,
                    'payment_channel': 'in person' if 'out' == tx['type'] else 'online'
                })
            
            current_date += timedelta(days=1)
            day_counter += 1
        
        logger.debug("MockBankingProvider", f"Generated {len(transactions)} mock transactions")
        return transactions
    
    def get_balance(self, account_id: str) -> Dict[str, float]:
        """Return mock balance"""
        logger.debug("MockBankingProvider", f"Returning mock balance for {account_id}")
        accounts = self.get_accounts()
        for account in accounts:
            if account['account_id'] == account_id:
                return {
                    'current': account['balance_current'],
                    'available': account['balance_available']
                }
        return {'current': 0.0, 'available': 0.0}


class FinicityProvider(BankingAPIProvider):
    """Finicity provider for financial data aggregation"""
    
    def __init__(self, credentials: Dict[str, str]):
        logger.debug("FinicityProvider", "Initializing Finicity provider")
        super().__init__(credentials)
        self.base_url = "https://api.finicity.com/v1"
        self.partner_id = credentials.get('partner_id', '')
        self.partner_secret = credentials.get('partner_secret', '')
        self.app_key = credentials.get('app_key', '')
    
    def authenticate(self) -> bool:
        """Authenticate with Finicity API"""
        logger.info("FinicityProvider", "Attempting Finicity authentication")
        if not all([self.partner_id, self.partner_secret, self.app_key]):
            logger.error("FinicityProvider", "Missing Finicity credentials")
            return False
        
        try:
            import requests
            auth = (self.partner_id, self.partner_secret)
            headers = {'Finicity-App-Key': self.app_key}
            
            response = requests.post(
                f"{self.base_url}/auth/token",
                auth=auth,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("FinicityProvider", "Finicity authentication successful")
                return True
            else:
                logger.error("FinicityProvider", f"Finicity authentication failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error("FinicityProvider", f"Finicity authentication error: {e}")
            return False
    
    def get_accounts(self, customer_id: str = None) -> List[Dict[str, Any]]:
        """Get accounts from Finicity"""
        logger.debug("FinicityProvider", f"Retrieving accounts for customer: {customer_id}")
        if not customer_id:
            logger.error("FinicityProvider", "Finicity requires customer_id")
            return []
        
        try:
            import requests
            headers = {
                'Finicity-App-Key': self.app_key,
                'Content-Type': 'application/json'
            }
            auth = (self.partner_id, self.partner_secret)
            
            response = requests.get(
                f"{self.base_url}/customers/{customer_id}/accounts",
                auth=auth,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                accounts_data = response.json()
                accounts = []
                
                for account in accounts_data.get('accounts', []):
                    accounts.append({
                        'account_id': str(account.get('id')),
                        'name': account.get('accountName', 'Unknown'),
                        'official_name': account.get('accountName'),
                        'type': account.get('accountType', 'unknown'),
                        'subtype': account.get('accountSubType', 'unknown'),
                        'mask': str(account.get('accountNumber', ''))[-4:],
                        'balance_current': float(account.get('balance', 0)),
                        'balance_available': float(account.get('balance', 0)),
                        'currency': 'USD'
                    })
                
                logger.info("FinicityProvider", f"Retrieved {len(accounts)} accounts from Finicity")
                return accounts
            else:
                logger.error("FinicityProvider", f"Failed to get Finicity accounts: {response.status_code}")
                return []
        except Exception as e:
            logger.error("FinicityProvider", f"Error getting Finicity accounts: {e}")
            return []
    
    def get_transactions(self, customer_id: str, account_id: str, start_date: date, 
                        end_date: date) -> List[Dict[str, Any]]:
        """Get transactions from Finicity"""
        logger.debug("FinicityProvider", f"Retrieving transactions for account {account_id} from {start_date} to {end_date}")
        try:
            import requests
            headers = {
                'Finicity-App-Key': self.app_key,
                'Content-Type': 'application/json'
            }
            auth = (self.partner_id, self.partner_secret)
            
            # Convert dates to Unix timestamps
            start_timestamp = int(datetime.combine(start_date, datetime.min.time()).timestamp())
            end_timestamp = int(datetime.combine(end_date, datetime.max.time()).timestamp())
            
            response = requests.get(
                f"{self.base_url}/customers/{customer_id}/accounts/{account_id}/transactions",
                auth=auth,
                headers=headers,
                params={
                    'fromDate': start_timestamp,
                    'toDate': end_timestamp,
                    'limit': 1000
                },
                timeout=10
            )
            
            if response.status_code == 200:
                transactions_data = response.json()
                transactions = []
                
                for tx in transactions_data.get('transactions', []):
                    amount = float(tx.get('amount', 0))
                    tx_type = 'in' if amount > 0 else 'out'
                    
                    transactions.append({
                        'transaction_id': str(tx.get('id')),
                        'account_id': account_id,
                        'amount': abs(amount),
                        'type': tx_type,
                        'date': datetime.fromtimestamp(tx.get('postedDate')).date().isoformat(),
                        'name': tx.get('description', 'Unknown'),
                        'merchant_name': tx.get('merchant', {}).get('name', tx.get('description')),
                        'category': [tx.get('category', 'Uncategorized')],
                        'pending': tx.get('status') == 'PENDING',
                        'payment_channel': 'online'
                    })
                
                logger.info("FinicityProvider", f"Retrieved {len(transactions)} transactions from Finicity")
                return transactions
            else:
                logger.error("FinicityProvider", f"Failed to get Finicity transactions: {response.status_code}")
                return []
        except Exception as e:
            logger.error("FinicityProvider", f"Error getting Finicity transactions: {e}")
            return []
    
    def get_balance(self, customer_id: str, account_id: str) -> Dict[str, float]:
        """Get account balance from Finicity"""
        logger.debug("FinicityProvider", f"Retrieving balance for account {account_id}")
        try:
            accounts = self.get_accounts(customer_id)
            for account in accounts:
                if account['account_id'] == account_id:
                    logger.debug("FinicityProvider", f"Balance found: ${account['balance_current']}")
                    return {
                        'current': account['balance_current'],
                        'available': account['balance_available']
                    }
            logger.warning("FinicityProvider", f"Account {account_id} not found")
            return {'current': 0.0, 'available': 0.0}
        except Exception as e:
            logger.error("FinicityProvider", f"Error getting Finicity balance: {e}")
            return {'current': 0.0, 'available': 0.0}


class StripeProvider(BankingAPIProvider):
    """Stripe provider for connected bank accounts and payouts"""
    
    def __init__(self, credentials: Dict[str, str]):
        logger.debug("StripeProvider", "Initializing Stripe provider")
        super().__init__(credentials)
        self.api_key = credentials.get('api_key', '')
        self.base_url = "https://api.stripe.com/v1"
    
    def authenticate(self) -> bool:
        """Authenticate with Stripe API"""
        logger.info("StripeProvider", "Attempting Stripe authentication")
        if not self.api_key:
            logger.error("StripeProvider", "Missing Stripe API key")
            return False
        
        try:
            import requests
            headers = {'Authorization': f'Bearer {self.api_key}'}
            
            response = requests.get(
                f"{self.base_url}/account",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("StripeProvider", "Stripe authentication successful")
                return True
            else:
                logger.error("StripeProvider", f"Stripe authentication failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error("StripeProvider", f"Stripe authentication error: {e}")
            return False
    
    def get_accounts(self, **kwargs) -> List[Dict[str, Any]]:
        """Get connected bank accounts from Stripe"""
        logger.debug("StripeProvider", "Retrieving connected bank accounts from Stripe")
        try:
            import requests
            headers = {'Authorization': f'Bearer {self.api_key}'}
            
            response = requests.get(
                f"{self.base_url}/external_accounts",
                headers=headers,
                params={'limit': 100, 'object': 'bank_account'},
                timeout=10
            )
            
            if response.status_code == 200:
                accounts_data = response.json()
                accounts = []
                
                for account in accounts_data.get('data', []):
                    if account.get('object') == 'bank_account':
                        accounts.append({
                            'account_id': account.get('id'),
                            'name': f"{account.get('bank_name', 'Bank')} ...{account.get('last4')}",
                            'official_name': account.get('bank_name'),
                            'type': 'depository',
                            'subtype': account.get('account_type', 'checking'),
                            'mask': account.get('last4'),
                            'balance_current': 0.0,  # Stripe doesn't provide balance
                            'balance_available': 0.0,
                            'currency': account.get('currency', 'usd').upper()
                        })
                
                logger.info("StripeProvider", f"Retrieved {len(accounts)} Stripe accounts")
                return accounts
            else:
                logger.error("StripeProvider", f"Failed to get Stripe accounts: {response.status_code}")
                return []
        except Exception as e:
            logger.error("StripeProvider", f"Error getting Stripe accounts: {e}")
            return []
    
    def get_transactions(self, account_id: str, start_date: date, 
                        end_date: date, **kwargs) -> List[Dict[str, Any]]:
        """Get transactions from Stripe (payouts and transfers)"""
        logger.debug("StripeProvider", f"Retrieving transactions from {start_date} to {end_date}")
        try:
            import requests
            headers = {'Authorization': f'Bearer {self.api_key}'}
            
            start_timestamp = int(datetime.combine(start_date, datetime.min.time()).timestamp())
            end_timestamp = int(datetime.combine(end_date, datetime.max.time()).timestamp())
            
            transactions = []
            
            # Get payouts
            payout_response = requests.get(
                f"{self.base_url}/payouts",
                headers=headers,
                params={
                    'limit': 100,
                    'created[gte]': start_timestamp,
                    'created[lte]': end_timestamp
                },
                timeout=10
            )
            
            if payout_response.status_code == 200:
                payouts = payout_response.json().get('data', [])
                logger.debug("StripeProvider", f"Found {len(payouts)} payouts")
                
                for payout in payouts:
                    if payout.get('destination') == account_id:
                        amount = float(payout.get('amount', 0)) / 100  # Stripe amounts in cents
                        
                        transactions.append({
                            'transaction_id': payout.get('id'),
                            'account_id': account_id,
                            'amount': amount,
                            'type': 'in',
                            'date': datetime.fromtimestamp(payout.get('created')).date().isoformat(),
                            'name': 'Stripe Payout',
                            'merchant_name': 'Stripe',
                            'category': ['Transfer', 'Payout'],
                            'pending': payout.get('status') == 'pending',
                            'payment_channel': 'online'
                        })
            
            logger.info("StripeProvider", f"Retrieved {len(transactions)} transactions from Stripe")
            return transactions
        except Exception as e:
            logger.error("StripeProvider", f"Error getting Stripe transactions: {e}")
            return []
    
    def get_balance(self, account_id: str) -> Dict[str, float]:
        """Stripe doesn't provide real-time balance, return 0"""
        logger.debug("StripeProvider", "Stripe does not provide real-time balance")
        return {'current': 0.0, 'available': 0.0}


class OpenBankingProvider(BankingAPIProvider):
    """Generic Open Banking provider (supports APIs like TrueLayer, Yapstone, etc.)"""
    
    def __init__(self, credentials: Dict[str, str]):
        logger.debug("OpenBankingProvider", "Initializing Open Banking provider")
        super().__init__(credentials)
        self.provider_type = credentials.get('provider_type', 'truelayer')
        self.client_id = credentials.get('client_id', '')
        self.client_secret = credentials.get('client_secret', '')
        self.base_url = credentials.get('base_url', '')
        self.access_token = credentials.get('access_token', '')
        logger.debug("OpenBankingProvider", f"Provider type: {self.provider_type}")
    
    def authenticate(self) -> bool:
        """Authenticate with Open Banking provider"""
        logger.debug("OpenBankingProvider", f"Authenticating with Open Banking provider: {self.provider_type}")
        if not all([self.client_id, self.client_secret, self.base_url]):
            logger.error("OpenBankingProvider", "Missing Open Banking credentials")
            return False
        
        try:
            import requests
            
            response = requests.post(
                f"{self.base_url}/auth/oauth/access_token",
                data={
                    'grant_type': 'client_credentials',
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'scope': 'accounts transactions'
                },
                timeout=10
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get('access_token')
                logger.info("OpenBankingProvider", f"Open Banking ({self.provider_type}) authentication successful")
                return True
            else:
                logger.error("OpenBankingProvider", f"Open Banking authentication failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error("OpenBankingProvider", f"Open Banking authentication error: {str(e)}")
            return False
    
    def get_accounts(self, user_id: str = None, **kwargs) -> List[Dict[str, Any]]:
        """Get accounts from Open Banking provider"""
        logger.debug("OpenBankingProvider", f"Retrieving accounts for user: {user_id}")
        if not self.access_token or not user_id:
            logger.error("OpenBankingProvider", "Missing access token or user_id")
            return []
        
        try:
            import requests
            headers = {'Authorization': f'Bearer {self.access_token}'}
            
            response = requests.get(
                f"{self.base_url}/accounts",
                headers=headers,
                params={'user_id': user_id},
                timeout=10
            )
            
            if response.status_code == 200:
                accounts_data = response.json()
                accounts = []
                
                for account in accounts_data.get('results', []):
                    accounts.append({
                        'account_id': account.get('id'),
                        'name': account.get('name', 'Unknown Account'),
                        'official_name': account.get('institution_name'),
                        'type': account.get('account_type', 'depository'),
                        'subtype': account.get('account_subtype', 'checking'),
                        'mask': account.get('iban', '')[-4:] if account.get('iban') else '',
                        'balance_current': float(account.get('balance', {}).get('current', 0)),
                        'balance_available': float(account.get('balance', {}).get('available', 0)),
                        'currency': account.get('currency', 'GBP')
                    })
                
                logger.info("OpenBankingProvider", f"Retrieved {len(accounts)} accounts for user {user_id}")
                return accounts
            else:
                logger.error("OpenBankingProvider", f"Failed to get Open Banking accounts: {response.status_code}")
                return []
        except Exception as e:
            logger.error("OpenBankingProvider", f"Error getting Open Banking accounts: {str(e)}")
            return []
    
    def get_transactions(self, account_id: str, start_date: date, 
                        end_date: date, **kwargs) -> List[Dict[str, Any]]:
        """Get transactions from Open Banking provider"""
        logger.debug("OpenBankingProvider", f"Retrieving transactions for account: {account_id}, start: {start_date}, end: {end_date}")
        if not self.access_token:
            return []
        
        try:
            import requests
            headers = {'Authorization': f'Bearer {self.access_token}'}
            
            response = requests.get(
                f"{self.base_url}/accounts/{account_id}/transactions",
                headers=headers,
                params={
                    'from': start_date.isoformat(),
                    'to': end_date.isoformat()
                },
                timeout=10
            )
            
            if response.status_code == 200:
                transactions_data = response.json()
                transactions = []
                
                for tx in transactions_data.get('results', []):
                    amount = float(tx.get('amount', 0))
                    tx_type = 'in' if amount > 0 else 'out'
                    
                    transactions.append({
                        'transaction_id': tx.get('id'),
                        'account_id': account_id,
                        'amount': abs(amount),
                        'type': tx_type,
                        'date': tx.get('booking_date', tx.get('date')).split('T')[0],
                        'name': tx.get('description', 'Unknown'),
                        'merchant_name': tx.get('merchant', {}).get('name', tx.get('description')),
                        'category': [tx.get('transaction_type', 'Uncategorized')],
                        'pending': tx.get('status') == 'PENDING',
                        'payment_channel': tx.get('payment_method', 'online')
                    })
                
                logger.info("OpenBankingProvider", f"Retrieved {len(transactions)} transactions for account {account_id}")
                return transactions
            else:
                logger.error("OpenBankingProvider", f"Failed to get Open Banking transactions: {response.status_code}")
                return []
        except Exception as e:
            logger.error("OpenBankingProvider", f"Error getting Open Banking transactions: {str(e)}")
            return []
    
    def get_balance(self, account_id: str) -> Dict[str, float]:
        """Get account balance from Open Banking provider"""
        logger.debug("OpenBankingProvider", f"Retrieving balance for account: {account_id}")
        if not self.access_token:
            return {'current': 0.0, 'available': 0.0}
        
        try:
            import requests
            headers = {'Authorization': f'Bearer {self.access_token}'}
            
            response = requests.get(
                f"{self.base_url}/accounts/{account_id}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                account_data = response.json()
                balance = account_data.get('balance', {})
                result = {
                    'current': float(balance.get('current', 0)),
                    'available': float(balance.get('available', 0))
                }
                logger.info("OpenBankingProvider", f"Retrieved balance for account {account_id}: {result['current']}")
                return result
            logger.warning("OpenBankingProvider", f"Failed to retrieve balance for account {account_id}")
            return {'current': 0.0, 'available': 0.0}
        except Exception as e:
            logger.error("OpenBankingProvider", f"Error getting Open Banking balance: {str(e)}")
            return {'current': 0.0, 'available': 0.0}


class BankingAPIManager:
    """
    Manages banking API connections and linked accounts.
    Provides interface between banking APIs and the Financial Manager.
    """
    
    def __init__(self, user_id: str = None):
        logger.debug("BankingAPIManager", f"Initializing BankingAPIManager for user: {user_id}")
        self.user_id = user_id
        self.providers = {}
        self.linked_accounts = {}
        self.config = {}
        
        self.load_config()
        self.load_linked_accounts()
        self._initialize_providers()
        logger.info("BankingAPIManager", "BankingAPIManager initialization complete")
    
    def load_config(self):
        """Load banking API configuration"""
        logger.debug("BankingAPIManager", "Loading banking API configuration")
        if os.path.exists(BANKING_API_CONFIG_FILE):
            try:
                with open(BANKING_API_CONFIG_FILE, 'r') as f:
                    self.config = json.load(f)
                logger.info("BankingAPIManager", f"Loaded banking API config from {BANKING_API_CONFIG_FILE}")
            except Exception as e:
                logger.error("BankingAPIManager", f"Failed to load banking API config: {str(e)}")
                self.config = {}
        else:
            logger.debug("BankingAPIManager", "No config file found, creating default config")
            # Create default config
            self.config = {
                'providers': {
                    'plaid': {
                        'enabled': False,
                        'client_id': '',
                        'secret': '',
                        'environment': 'sandbox'
                    },
                    'finicity': {
                        'enabled': False,
                        'partner_id': '',
                        'partner_secret': '',
                        'app_key': ''
                    },
                    'stripe': {
                        'enabled': False,
                        'api_key': ''
                    },
                    'open_banking': {
                        'enabled': False,
                        'provider_type': 'truelayer',
                        'client_id': '',
                        'client_secret': '',
                        'base_url': ''
                    },
                    'mock': {
                        'enabled': True  # Enable mock by default for testing
                    }
                }
            }
            self.save_config()
    
    def save_config(self):
        """Save banking API configuration"""
        logger.debug("BankingAPIManager", "Saving banking API configuration")
        try:
            os.makedirs(os.path.dirname(BANKING_API_CONFIG_FILE), exist_ok=True)
            with open(BANKING_API_CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info("BankingAPIManager", f"Saved banking API config to {BANKING_API_CONFIG_FILE}")
        except Exception as e:
            logger.error("BankingAPIManager", f"Failed to save banking API config: {str(e)}")
    
    def load_linked_accounts(self):
        """Load linked bank accounts"""
        logger.debug("BankingAPIManager", f"Loading linked accounts for user: {self.user_id}")
        if os.path.exists(LINKED_ACCOUNTS_FILE):
            try:
                with open(LINKED_ACCOUNTS_FILE, 'r') as f:
                    all_accounts = json.load(f)
                    # Filter by user if user_id is set
                    if self.user_id:
                        self.linked_accounts = {
                            k: v for k, v in all_accounts.items() 
                            if v.get('user_id') == self.user_id
                        }
                    else:
                        self.linked_accounts = all_accounts
                logger.info("BankingAPIManager", f"Loaded {len(self.linked_accounts)} linked accounts")
            except Exception as e:
                logger.error("BankingAPIManager", f"Failed to load linked accounts: {str(e)}")
                self.linked_accounts = {}
        else:
            logger.debug("BankingAPIManager", "No linked accounts file found")
            self.linked_accounts = {}
    
    def save_linked_accounts(self):
        """Save linked bank accounts"""
        logger.debug("BankingAPIManager", f"Saving linked accounts for user: {self.user_id}")
        try:
            os.makedirs(os.path.dirname(LINKED_ACCOUNTS_FILE), exist_ok=True)
            
            # Load existing accounts to preserve other users' data
            all_accounts = {}
            if os.path.exists(LINKED_ACCOUNTS_FILE):
                with open(LINKED_ACCOUNTS_FILE, 'r') as f:
                    all_accounts = json.load(f)
            
            # Remove accounts for current user first (if user_id is set)
            if self.user_id:
                all_accounts = {
                    k: v for k, v in all_accounts.items()
                    if v.get('user_id') != self.user_id
                }
            else:
                # If no user_id, clear all accounts (single user mode)
                all_accounts = {}
            
            # Add current user's accounts
            all_accounts.update(self.linked_accounts)
            
            with open(LINKED_ACCOUNTS_FILE, 'w') as f:
                json.dump(all_accounts, f, indent=2)
            logger.info("BankingAPIManager", f"Saved {len(self.linked_accounts)} linked accounts")
        except Exception as e:
            logger.error("BankingAPIManager", f"Failed to save linked accounts: {str(e)}")
    
    def _initialize_providers(self):
        """Initialize banking API providers based on config"""
        logger.debug("BankingAPIManager", "Initializing banking API providers")
        provider_config = self.config.get('providers', {})
        providers_initialized = []
        
        # Initialize Plaid if enabled
        if provider_config.get('plaid', {}).get('enabled'):
            logger.debug("BankingAPIManager", "Initializing Plaid provider")
            plaid_creds = provider_config['plaid']
            self.providers['plaid'] = PlaidProvider(plaid_creds)
            providers_initialized.append('plaid')
        
        # Initialize Finicity if enabled
        if provider_config.get('finicity', {}).get('enabled'):
            logger.debug("BankingAPIManager", "Initializing Finicity provider")
            finicity_creds = provider_config['finicity']
            self.providers['finicity'] = FinicityProvider(finicity_creds)
            providers_initialized.append('finicity')
        
        # Initialize Stripe if enabled
        if provider_config.get('stripe', {}).get('enabled'):
            logger.debug("BankingAPIManager", "Initializing Stripe provider")
            stripe_creds = provider_config['stripe']
            self.providers['stripe'] = StripeProvider(stripe_creds)
            providers_initialized.append('stripe')
        
        # Initialize Open Banking if enabled
        if provider_config.get('open_banking', {}).get('enabled'):
            logger.debug("BankingAPIManager", "Initializing Open Banking provider")
            open_banking_creds = provider_config['open_banking']
            self.providers['open_banking'] = OpenBankingProvider(open_banking_creds)
            providers_initialized.append('open_banking')
        
        # Initialize Mock provider if enabled
        if provider_config.get('mock', {}).get('enabled'):
            logger.debug("BankingAPIManager", "Initializing Mock provider")
            self.providers['mock'] = MockBankingProvider({})
            providers_initialized.append('mock')
        
        logger.info("BankingAPIManager", f"Initialized {len(providers_initialized)} providers: {', '.join(providers_initialized)}")
    
    def link_account(self, provider_name: str, app_account_id: str, app_account_name: str, 
                     **provider_params) -> bool:
        """
        Link a bank account from a provider to an account in the Financial Manager.
        
        Args:
            provider_name: Name of the banking provider ('plaid', 'finicity', 'stripe', 'open_banking', 'mock')
            app_account_id: Internal account ID in Financial Manager
            app_account_name: Account name in Financial Manager
            **provider_params: Provider-specific parameters:
                - plaid: access_token
                - finicity: customer_id
                - stripe: (uses API key from config)
                - open_banking: user_id
                - mock: (no additional params needed)
        
        Returns:
            bool: True if successful
        """
        logger.debug("BankingAPIManager", f"Linking {provider_name} account to {app_account_name}")
        if provider_name not in self.providers:
            logger.error("BankingAPIManager", f"Provider '{provider_name}' not available")
            return False
        
        provider = self.providers[provider_name]
        
        # Get accounts from provider with provider-specific parameters
        try:
            if provider_name == 'plaid':
                access_token = provider_params.get('access_token')
                if not access_token:
                    logger.error("BankingAPIManager", "Plaid requires 'access_token' parameter")
                    return False
                logger.debug("BankingAPIManager", f"Fetching accounts from Plaid with access token")
                bank_accounts = provider.get_accounts(access_token)
                
            elif provider_name == 'finicity':
                customer_id = provider_params.get('customer_id')
                if not customer_id:
                    logger.error("BankingAPIManager", "Finicity requires 'customer_id' parameter")
                    return False
                logger.debug("BankingAPIManager", f"Fetching accounts from Finicity for customer {customer_id}")
                bank_accounts = provider.get_accounts(customer_id)
                
            elif provider_name == 'stripe':
                logger.debug("BankingAPIManager", "Fetching accounts from Stripe")
                bank_accounts = provider.get_accounts()
                
            elif provider_name == 'open_banking':
                user_id = provider_params.get('user_id')
                if not user_id:
                    logger.error("BankingAPIManager", "Open Banking requires 'user_id' parameter")
                    return False
                logger.debug("BankingAPIManager", f"Fetching accounts from Open Banking for user {user_id}")
                bank_accounts = provider.get_accounts(user_id=user_id)
                
            else:  # mock and others
                logger.debug("BankingAPIManager", f"Fetching accounts from {provider_name}")
                bank_accounts = provider.get_accounts()
            
        except Exception as e:
            logger.error("BankingAPIManager", f"Failed to get accounts from {provider_name}: {str(e)}")
            return False
        
        if not bank_accounts:
            logger.error("BankingAPIManager", "No accounts found from provider")
            return False
        
        # Store linked account info
        for bank_account in bank_accounts:
            link_id = generate_identifier()
            link_data = {
                'link_id': link_id,
                'user_id': self.user_id,
                'provider': provider_name,
                'bank_account_id': bank_account['account_id'],
                'bank_account_name': bank_account['name'],
                'bank_account_mask': bank_account.get('mask'),
                'bank_account_type': bank_account.get('type'),
                'app_account_id': app_account_id,
                'app_account_name': app_account_name,
                'linked_date': datetime.now().isoformat(),
                'last_sync': None,
                'auto_sync': True,
                'auto_categorize': True
            }
            
            # Store provider-specific parameters
            if provider_name == 'plaid':
                link_data['access_token'] = provider_params.get('access_token')
            elif provider_name == 'finicity':
                link_data['customer_id'] = provider_params.get('customer_id')
            elif provider_name == 'open_banking':
                link_data['user_id'] = provider_params.get('user_id')
            
            self.linked_accounts[link_id] = link_data
        
        self.save_linked_accounts()
        logger.info("BankingAPIManager", f"Linked {len(bank_accounts)} account(s) from {provider_name} to {app_account_name}")
        return True
    
    def unlink_account(self, link_id: str) -> bool:
        """Unlink a bank account"""
        logger.debug("BankingAPIManager", f"Unlinking account {link_id}")
        if link_id in self.linked_accounts:
            bank_name = self.linked_accounts[link_id].get('bank_account_name', link_id)
            del self.linked_accounts[link_id]
            self.save_linked_accounts()
            logger.info("BankingAPIManager", f"Unlinked account {bank_name} ({link_id})")
            return True
        logger.warning("BankingAPIManager", f"Account {link_id} not found")
        return False
    
    def get_linked_accounts(self) -> List[Dict[str, Any]]:
        """Get all linked accounts for current user"""
        logger.debug("BankingAPIManager", f"Retrieving {len(self.linked_accounts)} linked accounts")
        return list(self.linked_accounts.values())
    
    def sync_transactions(self, link_id: str, days_back: int = 30, bank_instance=None) -> Tuple[int, List[str]]:
        """
        Sync transactions from a linked bank account into Financial Manager.
        
        Args:
            link_id: ID of the linked account
            days_back: Number of days to sync (default 30)
            bank_instance: Instance of Bank class to add transactions to
        
        Returns:
            Tuple of (number of new transactions, list of errors)
        """
        logger.debug("BankingAPIManager", f"Starting transaction sync for link {link_id}, days_back={days_back}")
        if link_id not in self.linked_accounts:
            logger.error("BankingAPIManager", f"Linked account {link_id} not found")
            return 0, ["Account not found"]
        
        if not bank_instance:
            logger.error("BankingAPIManager", "Bank instance required for sync_transactions")
            return 0, ["Bank instance required"]
        
        link = self.linked_accounts[link_id]
        provider_name = link['provider']
        
        if provider_name not in self.providers:
            logger.error("BankingAPIManager", f"Provider '{provider_name}' not available")
            return 0, [f"Provider '{provider_name}' not available"]
        
        provider = self.providers[provider_name]
        
        # Calculate date range
        end_date = date.today()
        start_date = end_date - timedelta(days=days_back)
        logger.debug("BankingAPIManager", f"Fetching transactions from {start_date} to {end_date} for {provider_name}")
        
        # Get transactions from provider with provider-specific parameters
        try:
            if provider_name == 'plaid':
                logger.debug("BankingAPIManager", f"Fetching from Plaid with token for account {link['bank_account_id']}")
                bank_transactions = provider.get_transactions(
                    access_token=link['access_token'],
                    start_date=start_date,
                    end_date=end_date,
                    account_ids=[link['bank_account_id']]
                )
            elif provider_name == 'finicity':
                logger.debug("BankingAPIManager", f"Fetching from Finicity for customer {link.get('customer_id')}")
                bank_transactions = provider.get_transactions(
                    customer_id=link.get('customer_id'),
                    account_id=link['bank_account_id'],
                    start_date=start_date,
                    end_date=end_date
                )
            elif provider_name == 'stripe':
                logger.debug("BankingAPIManager", f"Fetching from Stripe for account {link['bank_account_id']}")
                bank_transactions = provider.get_transactions(
                    account_id=link['bank_account_id'],
                    start_date=start_date,
                    end_date=end_date
                )
            elif provider_name == 'open_banking':
                logger.debug("BankingAPIManager", f"Fetching from Open Banking for user {link.get('user_id')}")
                bank_transactions = provider.get_transactions(
                    account_id=link['bank_account_id'],
                    start_date=start_date,
                    end_date=end_date,
                    user_id=link.get('user_id')
                )
            else:  # mock and others
                logger.debug("BankingAPIManager", f"Fetching from {provider_name}")
                bank_transactions = provider.get_transactions(
                    account_id=link['bank_account_id'],
                    start_date=start_date,
                    end_date=end_date
                )
        except Exception as e:
            logger.error("BankingAPIManager", f"Failed to fetch transactions from {provider_name}: {str(e)}")
            return 0, [str(e)]
        
        logger.debug("BankingAPIManager", f"Retrieved {len(bank_transactions)} transactions from {provider_name}")
        
        # Import transactions into Financial Manager
        new_count = 0
        errors = []
        duplicates_skipped = 0
        
        for bank_tx in bank_transactions:
            try:
                # Check if transaction already exists (by external ID)
                external_id = f"{provider_name}_{bank_tx['transaction_id']}"
                exists = any(
                    tx.get('external_id') == external_id 
                    for tx in bank_instance.transactions
                )
                
                if exists:
                    logger.debug("BankingAPIManager", f"Skipping duplicate transaction {external_id}")
                    duplicates_skipped += 1
                    continue  # Skip duplicates
                
                # Determine category
                category = None
                if link['auto_categorize'] and bank_tx.get('category'):
                    # Use first category from provider
                    if isinstance(bank_tx['category'], list) and bank_tx['category']:
                        category = bank_tx['category'][0]
                    else:
                        category = str(bank_tx['category'])
                
                # Create transaction in Financial Manager
                logger.debug("BankingAPIManager", f"Adding transaction: {bank_tx.get('name')} - ${bank_tx['amount']}")
                tx_data = bank_instance.add_transaction(
                    amount=bank_tx['amount'],
                    desc=bank_tx.get('name') or bank_tx.get('merchant_name', 'Unknown'),
                    account=link['app_account_name'],
                    account_id=link['app_account_id'],
                    type_=bank_tx['type'],
                    category=category,
                    date=bank_tx['date'],
                    user_id=self.user_id
                )
                
                # Store external ID for deduplication
                for tx in bank_instance.transactions:
                    if tx['identifier'] == tx_data['identifier']:
                        tx['external_id'] = external_id
                        tx['imported_from'] = provider_name
                        tx['bank_account_id'] = link['bank_account_id']
                        break
                
                bank_instance.save()
                new_count += 1
                
            except Exception as e:
                error_msg = f"Failed to import transaction {bank_tx.get('transaction_id')}: {str(e)}"
                logger.error("BankingAPIManager", error_msg)
                errors.append(error_msg)
        
        # Update last sync time
        link['last_sync'] = datetime.now().isoformat()
        self.save_linked_accounts()
        
        logger.info("BankingAPIManager", f"Synced {new_count} new transactions from {link['bank_account_name']} ({duplicates_skipped} duplicates skipped)")
        return new_count, errors
    
    def sync_all_accounts(self, days_back: int = 30, bank_instance=None) -> Dict[str, Tuple[int, List[str]]]:
        """
        Sync all linked accounts.
        
        Returns:
            Dict mapping link_id to (count, errors) tuple
        """
        logger.info("BankingAPIManager", f"Starting batch sync for {len(self.linked_accounts)} linked accounts")
        results = {}
        total_transactions = 0
        total_errors = 0
        
        for link_id in self.linked_accounts.keys():
            logger.debug("BankingAPIManager", f"Syncing account {link_id}")
            count, errors = self.sync_transactions(link_id, days_back, bank_instance)
            results[link_id] = (count, errors)
            total_transactions += count
            total_errors += len(errors)
        
        logger.info("BankingAPIManager", f"Batch sync complete: {total_transactions} transactions, {total_errors} errors")
        return results
    
    def get_account_balance(self, link_id: str) -> Optional[Dict[str, float]]:
        """Get current balance for a linked account"""
        logger.debug("BankingAPIManager", f"Retrieving balance for linked account {link_id}")
        if link_id not in self.linked_accounts:
            logger.error("BankingAPIManager", f"Linked account {link_id} not found")
            return None
        
        link = self.linked_accounts[link_id]
        provider_name = link['provider']
        
        if provider_name not in self.providers:
            logger.error("BankingAPIManager", f"Provider '{provider_name}' not available")
            return None
        
        provider = self.providers[provider_name]
        
        try:
            logger.debug("BankingAPIManager", f"Fetching balance from {provider_name} for account {link['bank_account_id']}")
            if provider_name == 'plaid':
                balance = provider.get_balance(link['access_token'], link['bank_account_id'])
            else:
                balance = provider.get_balance(link['bank_account_id'])
            logger.info("BankingAPIManager", f"Retrieved balance for account {link['bank_account_name']}: {balance}")
            return balance
        except Exception as e:
            logger.error("BankingAPIManager", f"Failed to get balance: {str(e)}")
            return None
    
    def configure_provider(self, provider_name: str, **credentials) -> bool:
        """Configure a banking provider with credentials"""
        logger.debug("BankingAPIManager", f"Configuring provider: {provider_name} with {len(credentials)} credential(s)")
        if 'providers' not in self.config:
            self.config['providers'] = {}
        
        if provider_name not in self.config['providers']:
            self.config['providers'][provider_name] = {}
        
        self.config['providers'][provider_name].update(credentials)
        self.config['providers'][provider_name]['enabled'] = True
        
        self.save_config()
        self._initialize_providers()
        
        logger.info("BankingAPIManager", f"Successfully configured provider: {provider_name}")
        return True
