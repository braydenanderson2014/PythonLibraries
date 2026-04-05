import json
import csv
import os
import random
import string
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from assets.Logger import Logger
logger = Logger()
try:
    from .app_paths import BANK_DATA_FILE, RECURRING_DATA_FILE, USER_FINANCE_SETTINGS_FILE, LOANS_DATA_FILE
except ImportError:
    from app_paths import BANK_DATA_FILE, RECURRING_DATA_FILE, USER_FINANCE_SETTINGS_FILE, LOANS_DATA_FILE

def generate_identifier(length=12):
    chars = string.ascii_letters + string.digits
    return ''.join(random.SystemRandom().choice(chars) for _ in range(length))

class Transaction:
    def __init__(self, amount, desc, account, identifier=None, type_='in', category=None, timestamp=None, user_id=None, date=None, account_id=None, splits=None, attachments=None, tags=None):
        self.amount = amount
        self.desc = desc
        self.account = account  # Keep for backward compatibility
        self.account_id = account_id  # New field for specific bank account
        self.identifier = identifier or generate_identifier()
        self.type = type_  # 'in' or 'out'
        self.category = category
        self.timestamp = timestamp or datetime.now().isoformat()
        self.date = date or datetime.now().strftime('%Y-%m-%d')  # Date for the transaction
        self.user_id = user_id  # Associate transaction with user
        self.splits = splits or []  # List of split categories/amounts: [{'category': 'Food', 'amount': 50.00}, ...]
        self.attachments = attachments or []  # List of file attachments: [{'filename': 'receipt.jpg', 'path': 'path/to/file', ...}, ...]
        self.tags = tags or []  # List of tag names: ['tax-deductible', 'work-related', ...]

    def is_split(self):
        """Check if this transaction is split across multiple categories"""
        return len(self.splits) > 0

    def validate_splits(self):
        """Validate that splits sum to total transaction amount"""
        if not self.is_split():
            return True
        split_sum = sum(split['amount'] for split in self.splits)
        return abs(split_sum - self.amount) < 0.01  # Allow for floating point rounding

    def get_categories(self):
        """Get all categories for this transaction (including splits)"""
        if self.is_split():
            return [split['category'] for split in self.splits]
        return [self.category] if self.category else []

    def has_attachments(self):
        """Check if this transaction has any attachments"""
        return len(self.attachments) > 0

    def has_tags(self):
        """Check if this transaction has any tags"""
        return len(self.tags) > 0

    def add_tag(self, tag_name):
        """Add a tag to this transaction"""
        tag_name = tag_name.strip().lower()
        if tag_name and tag_name not in self.tags:
            self.tags.append(tag_name)

    def remove_tag(self, tag_name):
        """Remove a tag from this transaction"""
        tag_name = tag_name.strip().lower()
        if tag_name in self.tags:
            self.tags.remove(tag_name)

    def to_dict(self):
        return {
            'amount': self.amount,
            'desc': self.desc,
            'account': self.account,
            'account_id': self.account_id,
            'identifier': self.identifier,
            'type': self.type,
            'category': self.category,
            'timestamp': self.timestamp,
            'date': self.date,
            'user_id': self.user_id,
            'splits': self.splits,
            'attachments': self.attachments,
            'tags': self.tags
        }

class RecurringTransaction:
    def __init__(self, amount, desc, account, type_='in', category=None, 
                 frequency='monthly', start_date=None, end_date=None, 
                 user_id=None, identifier=None, last_processed=None, account_id=None,
                 status='active', skip_next=False, amount_type='fixed', amount_min=None, amount_max=None,
                 notification_days_before=1, instances_created=None):
        self.amount = amount
        self.desc = desc
        self.account = account  # Keep for backward compatibility
        self.account_id = account_id  # New field for specific bank account
        self.type = type_  # 'in' or 'out'
        self.category = category
        self.frequency = frequency  # 'weekly', 'monthly', 'yearly'
        self.start_date = start_date or date.today().isoformat()
        self.end_date = end_date  # None for indefinite
        self.user_id = user_id
        self.identifier = identifier or generate_identifier()
        self.last_processed = last_processed  # Last date this recurring transaction was processed
        self.active = True
        
        # Enhanced recurring transaction fields
        self.status = status  # 'active', 'paused', 'completed'
        self.skip_next = skip_next  # Skip the next occurrence
        self.amount_type = amount_type  # 'fixed', 'variable', 'prompt'
        self.amount_min = float(amount_min) if amount_min else None
        self.amount_max = float(amount_max) if amount_max else None
        self.notification_days_before = notification_days_before
        self.instances_created = instances_created or []  # List of dates when instances were created

    @property
    def type_(self):
        """Backward compatibility property for type_ access"""
        return self.type

    def to_dict(self):
        return {
            'amount': self.amount,
            'desc': self.desc,
            'account': self.account,
            'account_id': self.account_id,
            'type': self.type,
            'category': self.category,
            'frequency': self.frequency,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'user_id': self.user_id,
            'identifier': self.identifier,
            'last_processed': self.last_processed,
            'active': self.active,
            # Enhanced fields
            'status': self.status,
            'skip_next': self.skip_next,
            'amount_type': self.amount_type,
            'amount_min': self.amount_min,
            'amount_max': self.amount_max,
            'notification_days_before': self.notification_days_before,
            'instances_created': self.instances_created
        }

    def get_next_due_date(self):
        """Calculate the next date this recurring transaction should be processed"""
        start = date.fromisoformat(self.start_date)
        last_processed = date.fromisoformat(self.last_processed) if self.last_processed else start
        
        if self.frequency == 'weekly':
            return last_processed + timedelta(weeks=1)
        elif self.frequency == 'monthly':
            return last_processed + relativedelta(months=1)
        elif self.frequency == 'yearly':
            return last_processed + relativedelta(years=1)
        else:
            return last_processed + timedelta(days=30)  # Default to monthly

    @classmethod
    def from_dict(cls, data):
        """Create RecurringTransaction from dictionary data"""
        # Handle the type/type_ field name mismatch
        if 'type' in data and 'type_' not in data:
            data['type_'] = data.pop('type')
        
        # Get only the fields that the constructor accepts
        constructor_args = {
            'amount': data.get('amount'),
            'desc': data.get('desc'),
            'account': data.get('account'),
            'account_id': data.get('account_id'),
            'type_': data.get('type_'),
            'category': data.get('category'),
            'frequency': data.get('frequency'),
            'start_date': data.get('start_date'),
            'end_date': data.get('end_date'),
            'user_id': data.get('user_id'),
            'identifier': data.get('identifier'),
            'last_processed': data.get('last_processed'),
            # Enhanced fields
            'status': data.get('status', 'active'),
            'skip_next': data.get('skip_next', False),
            'amount_type': data.get('amount_type', 'fixed'),
            'amount_min': data.get('amount_min'),
            'amount_max': data.get('amount_max'),
            'notification_days_before': data.get('notification_days_before', 1),
            'instances_created': data.get('instances_created', [])
        }
        
        # Remove None values except for fields that can be None
        constructor_args = {k: v for k, v in constructor_args.items() 
                          if v is not None or k in ['amount_min', 'amount_max', 'end_date', 'last_processed']}
        
        instance = cls(**constructor_args)
        
        # Set any additional fields
        if 'active' in data:
            instance.active = data['active']
            
        return instance
    
    def get_average_amount(self):
        """Get average amount for variable amount recurring transactions"""
        if self.amount_type == 'variable' and self.amount_min is not None and self.amount_max is not None:
            return (self.amount_min + self.amount_max) / 2
        return self.amount
    
    def pause(self):
        """Pause this recurring transaction"""
        self.status = 'paused'
    
    def resume(self):
        """Resume this recurring transaction"""
        self.status = 'active'
    
    def mark_skip_next(self):
        """Mark to skip the next occurrence"""
        self.skip_next = True
    
    def clear_skip_next(self):
        """Clear the skip next flag"""
        self.skip_next = False
    
    def add_instance(self, instance_date):
        """Record that an instance was created on this date"""
        if isinstance(instance_date, date):
            instance_date = instance_date.isoformat()
        if instance_date not in self.instances_created:
            self.instances_created.append(instance_date)
    
    def get_upcoming_dates(self, days=30):
        """Get list of upcoming due dates for the next N days"""
        upcoming = []
        current_date = date.today()
        end_date = current_date + timedelta(days=days)
        
        check_date = self.get_next_due_date()
        while check_date <= end_date:
            if self.is_due(check_date):
                upcoming.append(check_date)
            check_date = check_date + (
                timedelta(weeks=1) if self.frequency == 'weekly' else
                relativedelta(months=1) if self.frequency == 'monthly' else
                relativedelta(years=1)
            )
            if len(upcoming) >= 12:  # Safety limit
                break
        
        return upcoming

    def is_due(self, check_date=None):
        """Check if this recurring transaction is due to be processed"""
        if not self.active:
            return False
            
        check_date = check_date or date.today()
        
        # Check if we're past the end date
        if self.end_date and check_date > date.fromisoformat(self.end_date):
            return False
            
        # Check if we're before the start date
        if check_date < date.fromisoformat(self.start_date):
            return False
            
        # Check if it's time for the next occurrence
        next_due = self.get_next_due_date()
        return check_date >= next_due

class Loan:
    """Represents a loan with recurring payments that are tracked separately from income/expenses."""
    def __init__(self, principal, annual_rate, payment_amount=None, minimum_payment=None, desc="", account_id=None, account_name=None,
                 frequency='monthly', start_date=None, end_date=None, user_id=None, identifier=None,
                 last_processed=None, remaining_principal=None, active=True, pay_from_account_id=None, pay_from_account_name=None):
        self.identifier = identifier or generate_identifier()
        self.desc = desc
        self.user_id = user_id
        self.account_id = account_id
        self.account_name = account_name  # display name fallback
        self.pay_from_account_id = pay_from_account_id  # account to withdraw payments from
        self.pay_from_account_name = pay_from_account_name  # display name for payment account
        self.principal = float(principal)
        self.annual_rate = float(annual_rate)  # e.g., 0.049 for 4.9%
        
        # Handle backward compatibility: payment_amount -> minimum_payment
        if minimum_payment is not None:
            self.minimum_payment = float(minimum_payment)
        elif payment_amount is not None:
            self.minimum_payment = float(payment_amount)
        else:
            self.minimum_payment = 0.0
            
        # Keep payment_amount as alias for backward compatibility
        self.payment_amount = self.minimum_payment
        
        self.frequency = frequency
        self.start_date = start_date or date.today().isoformat()
        self.end_date = end_date
        self.last_processed = last_processed
        self.remaining_principal = float(remaining_principal) if remaining_principal is not None else float(principal)
        self.active = active

    def to_dict(self):
        return {
            'identifier': self.identifier,
            'desc': self.desc,
            'user_id': self.user_id,
            'account_id': self.account_id,
            'account_name': self.account_name,
            'pay_from_account_id': self.pay_from_account_id,
            'pay_from_account_name': self.pay_from_account_name,
            'principal': self.principal,
            'annual_rate': self.annual_rate,
            'minimum_payment': self.minimum_payment,
            'payment_amount': self.payment_amount,  # Keep for backward compatibility
            'frequency': self.frequency,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'last_processed': self.last_processed,
            'remaining_principal': self.remaining_principal,
            'active': self.active,
        }

    @classmethod
    def from_dict(cls, data):
        # Filter out extra fields that aren't part of the Loan constructor
        valid_fields = {
            'principal', 'annual_rate', 'payment_amount', 'minimum_payment', 'desc',
            'account_id', 'account_name', 'frequency', 'start_date', 'end_date',
            'user_id', 'identifier', 'last_processed', 'remaining_principal', 'active',
            'pay_from_account_id', 'pay_from_account_name'
        }
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)

    def get_next_due_date(self):
        start = date.fromisoformat(self.start_date)
        last = date.fromisoformat(self.last_processed) if self.last_processed else start
        if self.frequency == 'weekly':
            return last + timedelta(weeks=1)
        if self.frequency == 'yearly':
            return last + relativedelta(years=1)
        return last + relativedelta(months=1)

    def is_due(self, check_date=None):
        if not self.active:
            return False
        check_date = check_date or date.today()
        if self.end_date and check_date > date.fromisoformat(self.end_date):
            return False
        if check_date < date.fromisoformat(self.start_date):
            return False
        return check_date >= self.get_next_due_date()

    def get_amortization_schedule(self, extra_monthly=0.0, lump_sum=0.0, lump_sum_month=0):
        """
        Get full amortization schedule for this loan.
        
        Args:
            extra_monthly: Extra monthly payment amount
            lump_sum: One-time lump sum payment
            lump_sum_month: Month to apply lump sum (0 = no lump sum)
        
        Returns:
            list: Amortization schedule
        """
        from loan_calculator import LoanCalculator
        
        calculator = LoanCalculator(
            principal=self.remaining_principal,
            annual_rate=self.annual_rate,
            monthly_payment=self.minimum_payment,
            start_date=date.fromisoformat(self.start_date)
        )
        
        return calculator.calculate_amortization_schedule(extra_monthly, lump_sum, lump_sum_month)
    
    def get_payoff_info(self, extra_monthly=0.0):
        """
        Get payoff date and total interest for this loan.
        
        Args:
            extra_monthly: Extra monthly payment amount
        
        Returns:
            dict: Payoff information
        """
        from loan_calculator import LoanCalculator
        
        calculator = LoanCalculator(
            principal=self.remaining_principal,
            annual_rate=self.annual_rate,
            monthly_payment=self.minimum_payment,
            start_date=date.fromisoformat(self.start_date)
        )
        
        return calculator.calculate_payoff_date(extra_monthly)
    
    def compare_payment_scenarios(self, extra_monthly=0.0, lump_sum=0.0, lump_sum_month=0):
        """
        Compare standard vs accelerated payment scenarios.
        
        Args:
            extra_monthly: Extra monthly payment
            lump_sum: Lump sum payment
            lump_sum_month: Month to apply lump sum
        
        Returns:
            dict: Comparison results with interest/time savings
        """
        from loan_calculator import LoanCalculator
        
        calculator = LoanCalculator(
            principal=self.remaining_principal,
            annual_rate=self.annual_rate,
            monthly_payment=self.minimum_payment,
            start_date=date.fromisoformat(self.start_date)
        )
        
        return calculator.compare_scenarios(extra_monthly, lump_sum, lump_sum_month)
    
    def get_summary_stats(self):
        """Get loan summary statistics"""
        from loan_calculator import LoanCalculator
        
        calculator = LoanCalculator(
            principal=self.remaining_principal,
            annual_rate=self.annual_rate,
            monthly_payment=self.minimum_payment,
            start_date=date.fromisoformat(self.start_date)
        )
        
        schedule = calculator.calculate_standard_schedule()
        return calculator.get_summary_stats(schedule)

class Bank:
    def __init__(self, current_user_id=None):
        self.transactions = []
        self.recurring_transactions = []
        self.loans = []
        self.user_finance_settings = {}
        self.current_user_id = current_user_id

        logger.info("Bank", f"Initializing Bank instance for user: {current_user_id}")
        # Initialize bank account manager
        from .bank_accounts import BankAccountManager
        self.account_manager = BankAccountManager()

        # Load persisted data
        logger.debug("Bank", "Loading persisted data")
        self.load()
        self.load_recurring()
        self.load_loans()
        self.load_user_settings()
        logger.info("Bank", "Bank initialization complete")

    def set_current_user(self, user_id):
        """Set the current user for finance operations"""
        logger.debug("Bank", f"Setting current user to: {user_id}")
        self.current_user_id = user_id

    def add_transaction(self, amount, desc, account, identifier=None, type_='in', category=None, user_id=None, date=None, account_id=None, splits=None, attachments=None, tags=None):
        logger.debug("Bank", f"Adding transaction: {desc} ({type_}) for amount: {amount}")
        # Use current user if no user_id specified
        if user_id is None:
            user_id = self.current_user_id
            
        # If identifier exists, update
        if identifier:
            logger.debug("Bank", f"Updating existing transaction with identifier: {identifier}")
            for t in self.transactions:
                if t['identifier'] == identifier and t['account'] == account:
                    t['amount'] = amount
                    t['desc'] = desc
                    t['type'] = type_
                    t['category'] = category
                    t['timestamp'] = datetime.now().isoformat()
                    t['user_id'] = user_id
                    t['account_id'] = account_id
                    t['splits'] = splits or []
                    t['attachments'] = attachments or []
                    t['tags'] = tags or []
                    if date:
                        t['date'] = date
                    self.save()
                    logger.info("Bank", f"Transaction updated successfully: {identifier}")
                    return t
        # Else, add new
        tx = Transaction(amount, desc, account, identifier, type_, category, user_id=user_id, date=date, account_id=account_id, splits=splits, attachments=attachments, tags=tags)
        
        # Validate splits if provided
        if not tx.validate_splits():
            logger.error("Bank", f"Split validation failed for transaction: {identifier}")
            raise ValueError(f"Split amounts (${sum(s['amount'] for s in tx.splits):.2f}) do not equal transaction amount (${amount:.2f})")
        
        self.transactions.append(tx.to_dict())
        logger.info("Bank", f"Transaction added successfully: {tx.identifier}")
        self.save()
        return tx.to_dict()

    def add_recurring_transaction(self, amount, desc, account, type_='in', category=None, 
                                frequency='monthly', start_date=None, end_date=None, user_id=None, account_id=None):
        """Add a recurring transaction"""
        logger.info("Bank", f"Adding recurring transaction: {desc} ({frequency}) - {type_}")
        if user_id is None:
            user_id = self.current_user_id
            
        recurring_tx = RecurringTransaction(
            amount=amount, desc=desc, account=account, account_id=account_id, type_=type_, 
            category=category, frequency=frequency, start_date=start_date, 
            end_date=end_date, user_id=user_id
        )
        self.recurring_transactions.append(recurring_tx.to_dict())
        logger.debug("Bank", f"Recurring transaction created with identifier: {recurring_tx.identifier}")
        self.save_recurring()
        return recurring_tx.to_dict()

    def process_recurring_transactions(self, process_date=None, force_identifier=None):
        """
        Process all due recurring transactions and create actual transactions.
        
        Args:
            process_date: Date to process (defaults to today)
            force_identifier: If provided, process this specific recurring transaction regardless of due date
        
        Returns:
            int: Number of transactions processed
        """
        process_date = process_date or date.today()
        logger.info("Bank", f"Processing recurring transactions for date: {process_date}")
        processed_count = 0
        
        for recurring_data in self.recurring_transactions:
            recurring_tx = RecurringTransaction.from_dict(recurring_data)
            
            # Check if we're forcing this specific transaction
            force_process = force_identifier and recurring_tx.identifier == force_identifier
            
            # Skip if paused (unless forced)
            if not force_process and recurring_tx.status == 'paused':
                logger.debug("Bank", f"Skipping paused recurring transaction: {recurring_tx.desc}")
                continue
            
            # Skip if skip_next is set (then clear the flag)
            if not force_process and recurring_tx.skip_next:
                logger.debug("Bank", f"Skipping next occurrence for: {recurring_tx.desc}")
                recurring_tx.clear_skip_next()
                # Update in the list
                for i, rt in enumerate(self.recurring_transactions):
                    if rt['identifier'] == recurring_tx.identifier:
                        self.recurring_transactions[i] = recurring_tx.to_dict()
                        break
                self.save_recurring()
                continue
            
            if force_process or recurring_tx.is_due(process_date):
                logger.debug("Bank", f"Processing recurring transaction: {recurring_tx.desc}")
                # Determine amount based on amount_type
                transaction_amount = recurring_tx.amount
                
                if recurring_tx.amount_type == 'variable' and recurring_tx.amount_min and recurring_tx.amount_max:
                    # Use average for automatic processing
                    transaction_amount = recurring_tx.get_average_amount()
                    logger.debug("Bank", f"Using average amount for variable transaction: {transaction_amount}")
                elif recurring_tx.amount_type == 'prompt':
                    # For prompt type, we'll need to handle this in the UI
                    # Skip automatic processing for prompt type
                    if not force_process:
                        logger.debug("Bank", f"Skipping prompt-type transaction, requires user input: {recurring_tx.desc}")
                        continue
                
                # Create actual transaction
                self.add_transaction(
                    amount=transaction_amount,
                    desc=f"{recurring_tx.desc} (Recurring)",
                    account=recurring_tx.account,
                    account_id=recurring_tx.account_id,
                    type_=recurring_tx.type,
                    category=recurring_tx.category,
                    user_id=recurring_tx.user_id
                )
                
                # Update last processed date and add to instances
                recurring_tx.last_processed = process_date.isoformat()
                recurring_tx.add_instance(process_date)
                
                # Update in the list
                for i, rt in enumerate(self.recurring_transactions):
                    if rt['identifier'] == recurring_tx.identifier:
                        self.recurring_transactions[i] = recurring_tx.to_dict()
                        break
                
                processed_count += 1
        
        if processed_count > 0:
            logger.info("Bank", f"Successfully processed {processed_count} recurring transactions")
            self.save_recurring()
        else:
            logger.debug("Bank", "No recurring transactions were due for processing")
            
        return processed_count

    # Loan management
    def add_loan(self, principal, annual_rate, payment_amount, desc, account_id=None, account_name=None,
                 frequency='monthly', start_date=None, end_date=None, user_id=None, pay_from_account_id=None, pay_from_account_name=None,
                 auto_create_account=True):
        logger.info("Bank", f"Adding loan: {desc} - Principal: {principal}, Annual Rate: {annual_rate}%")
        if user_id is None:
            user_id = self.current_user_id
            
        # Auto-create loan account if requested and no account info provided
        if auto_create_account and not account_id and not account_name:
            logger.debug("Bank", "Auto-creating loan account")
            from .bank_accounts import BankAccount
            
            # Create a loan account automatically
            loan_account = BankAccount(
                bank_name="Loan Services",
                account_type="Loan",
                account_name=f"{desc} Account",
                account_number="",  # Loans don't typically show account numbers
                user_id=str(user_id) if user_id is not None else "",
                initial_balance=-principal,  # Negative balance for loan (debt)
                active=True
            )
            
            # Add the account to the bank account manager
            added_account = self.account_manager.add_account(loan_account)
            account_id = added_account.account_id
            account_name = added_account.get_display_name()
            
            logger.debug("Bank", f"Auto-created loan account: {account_name} (ID: {account_id})")
        
        loan = Loan(
            principal=principal,
            annual_rate=annual_rate,
            payment_amount=payment_amount,
            desc=desc,
            account_id=account_id,
            account_name=account_name,
            frequency=frequency,
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
            pay_from_account_id=pay_from_account_id,
            pay_from_account_name=pay_from_account_name,
        )
        loan_dict = loan.to_dict()
        logger.debug("Bank", f"Loan created with identifier: {loan.identifier}")
        
        # Store reference to auto-created account
        if auto_create_account and account_id:
            loan_dict['auto_created_account'] = True
            loan_dict['loan_account_id'] = account_id
            
        self.loans.append(loan_dict)
        logger.info("Bank", f"Loan added successfully: {loan.identifier}")
        self.save_loans()
        return loan_dict

    def list_loans(self, user_id=None):
        user_id = user_id or self.current_user_id
        logger.debug("Bank", f"Listing loans for user: {user_id}")
        loans = [Loan.from_dict(l) for l in self.loans if l.get('user_id') == user_id]
        logger.debug("Bank", f"Found {len(loans)} loans for user")
        return loans

    def remove_loan(self, loan_identifier):
        logger.info("Bank", f"Removing loan: {loan_identifier}")
        self.loans = [l for l in self.loans if l.get('identifier') != loan_identifier]
        self.save_loans()
        logger.debug("Bank", f"Loan removed and saved successfully")
        return True

    def is_loan_account(self, account_name, user_id=None):
        """Check if an account is associated with any loan"""
        user_id = user_id or self.current_user_id
        logger.debug("Bank", f"Checking if account '{account_name}' is a loan account")
        for loan_data in self.loans:
            if loan_data.get('user_id') == user_id:
                if loan_data.get('account_name') == account_name or loan_data.get('account_id') == account_name:
                    logger.debug("Bank", f"Account '{account_name}' is a loan account")
                    return True
        logger.debug("Bank", f"Account '{account_name}' is not a loan account")
        return False

    def get_loan_for_account(self, account_name, user_id=None):
        """Get the loan associated with an account"""
        user_id = user_id or self.current_user_id
        logger.debug("Bank", f"Looking up loan for account: {account_name}")
        for loan_data in self.loans:
            if loan_data.get('user_id') == user_id:
                if loan_data.get('account_name') == account_name or loan_data.get('account_id') == account_name:
                    logger.debug("Bank", f"Found loan for account: {account_name}")
                    return Loan.from_dict(loan_data)
        logger.debug("Bank", f"No loan found for account: {account_name}")
        return None

    def process_loan_payments(self, process_date=None):
        """Process all due loan payments. We record them in a neutral way (not income/expense).
        Optionally, if desired later, we could add an expense for the payment and reduce loan principal separately.
        For now, we simply decrement remaining principal and do not create in/out transactions to keep UX simple."""
        process_date = process_date or date.today()
        logger.info("Bank", f"Processing loan payments for date: {process_date}")
        processed = 0
        updated = []
        for l in self.loans:
            loan = Loan.from_dict(l)
            if not loan.is_due(process_date):
                logger.debug("Bank", f"Loan {loan.desc} is not due yet")
                updated.append(loan.to_dict())
                continue

            logger.debug("Bank", f"Processing payment for loan: {loan.desc}")
            # Compute interest portion for the period (approx monthly)
            periods_per_year = 12 if loan.frequency == 'monthly' else (52 if loan.frequency == 'weekly' else 12)
            period_rate = loan.annual_rate / periods_per_year
            interest = loan.remaining_principal * period_rate
            principal_paid = max(0.0, loan.payment_amount - interest)
            loan.remaining_principal = max(0.0, loan.remaining_principal - principal_paid)
            loan.last_processed = process_date.isoformat()
            
            logger.debug("Bank", f"Loan payment applied - Interest: {interest:.2f}, Principal: {principal_paid:.2f}, Remaining: {loan.remaining_principal:.2f}")

            updated.append(loan.to_dict())
            processed += 1

        if processed:
            logger.info("Bank", f"Successfully processed {processed} loan payments")
            self.loans = updated
            self.save_loans()
        else:
            logger.debug("Bank", "No loan payments were due for processing")
        return processed

    def process_single_recurring(self, recurring, process_date=None):
        """Process a single recurring transaction"""
        process_date = process_date or date.today()
        logger.debug("Bank", f"Processing single recurring transaction for date: {process_date}")
        
        if hasattr(recurring, 'identifier'):
            # It's a RecurringTransaction object
            recurring_tx = recurring
        else:
            # It's a dict, convert it
            recurring_tx = RecurringTransaction.from_dict(recurring)
        
        # Handle loan payments differently
        if recurring_tx.type == 'loan_payment':
            logger.debug("Bank", f"Processing loan payment recurring transaction: {recurring_tx.desc}")
            # Find the loan by description or account
            loans = self.list_loans()
            target_loan = None
            for loan in loans:
                loan_desc = loan.desc.lower() if loan.desc else ""
                loan_account = loan.account_name.lower() if loan.account_name else ""
                recurring_desc = recurring_tx.desc.lower() if recurring_tx.desc else ""
                
                if (loan_desc in recurring_desc) or (loan_account in recurring_desc):
                    target_loan = loan
                    logger.debug("Bank", f"Found matching loan for payment: {loan.desc}")
                    break
            
            if target_loan:
                # Apply payment to loan - reduce remaining principal
                target_loan.remaining_principal = max(0, target_loan.remaining_principal - recurring_tx.amount)
                logger.debug("Bank", f"Applied payment to loan, remaining principal: {target_loan.remaining_principal:.2f}")
                
                # Create a transaction for the payment
                self.add_transaction(
                    amount=recurring_tx.amount,
                    desc=f"{recurring_tx.desc} - Loan Payment",
                    account=recurring_tx.account,
                    account_id=recurring_tx.account_id,
                    type_='out',  # Loan payments are outgoing
                    category=recurring_tx.category,
                    user_id=recurring_tx.user_id
                )
                
                # Save updated loan data
                self.save_loans()
            else:
                logger.warning("Bank", f"No matching loan found for payment, creating regular transaction: {recurring_tx.desc}")
                # If no matching loan found, create a regular transaction
                self.add_transaction(
                    amount=recurring_tx.amount,
                    desc=f"{recurring_tx.desc} (Recurring Loan Payment)",
                    account=recurring_tx.account,
                    account_id=recurring_tx.account_id,
                    type_='out',  # Loan payments are outgoing
                    category=recurring_tx.category,
                    user_id=recurring_tx.user_id
                )
        else:
            logger.debug("Bank", f"Processing standard recurring transaction: {recurring_tx.desc}")
            # Create regular transaction
            self.add_transaction(
                amount=recurring_tx.amount,
                desc=f"{recurring_tx.desc} (Recurring)",
                account=recurring_tx.account,
                account_id=recurring_tx.account_id,
                type_=recurring_tx.type,
                category=recurring_tx.category,
                user_id=recurring_tx.user_id
            )
        
        # Update last processed date
        recurring_tx.last_processed = process_date.isoformat()
        
        # Update in the list
        for i, rt in enumerate(self.recurring_transactions):
            if rt['identifier'] == recurring_tx.identifier:
                self.recurring_transactions[i] = recurring_tx.to_dict()
                break
        
        logger.info("Bank", f"Recurring transaction processed and saved")
        self.save_recurring()
        return True

    def get_user_finances(self, user_id=None, include_combined=True):
        """Get all financial transactions for a user, optionally including combined finances"""
        if user_id is None:
            user_id = self.current_user_id
        
        logger.debug("Bank", f"Retrieving finances for user: {user_id}, include_combined: {include_combined}")
        user_transactions = [t for t in self.transactions if t.get('user_id') == user_id]
        
        if include_combined:
            # Check if this user has combined finances with other users
            combined_users = self.get_combined_users(user_id)
            logger.debug("Bank", f"Found {len(combined_users)} combined users for {user_id}")
            for combined_user in combined_users:
                combined_transactions = [t for t in self.transactions if t.get('user_id') == combined_user]
                user_transactions.extend(combined_transactions)
        
        logger.debug("Bank", f"Retrieved {len(user_transactions)} transactions")
        return user_transactions

    def combine_user_finances(self, user1_id, user2_id):
        """Combine finances between two users (marriage/partnership)"""
        logger.info("Bank", f"Combining finances between users: {user1_id} and {user2_id}")
        if user1_id not in self.user_finance_settings:
            self.user_finance_settings[user1_id] = {'combined_with': []}
        if user2_id not in self.user_finance_settings:
            self.user_finance_settings[user2_id] = {'combined_with': []}
            
        # Add each user to the other's combined list
        if user2_id not in self.user_finance_settings[user1_id]['combined_with']:
            self.user_finance_settings[user1_id]['combined_with'].append(user2_id)
            logger.debug("Bank", f"Added {user2_id} to {user1_id}'s combined list")
        if user1_id not in self.user_finance_settings[user2_id]['combined_with']:
            self.user_finance_settings[user2_id]['combined_with'].append(user1_id)
            logger.debug("Bank", f"Added {user1_id} to {user2_id}'s combined list")
            
        logger.debug("Bank", f"Finances combined and settings saved")
        self.save_user_settings()

    def separate_user_finances(self, user1_id, user2_id):
        """Separate finances between two users"""
        logger.info("Bank", f"Separating finances between users: {user1_id} and {user2_id}")
        if user1_id in self.user_finance_settings and user2_id in self.user_finance_settings[user1_id].get('combined_with', []):
            self.user_finance_settings[user1_id]['combined_with'].remove(user2_id)
            logger.debug("Bank", f"Removed {user2_id} from {user1_id}'s combined list")
        if user2_id in self.user_finance_settings and user1_id in self.user_finance_settings[user2_id].get('combined_with', []):
            self.user_finance_settings[user2_id]['combined_with'].remove(user1_id)
            logger.debug("Bank", f"Removed {user1_id} from {user2_id}'s combined list")
            
        logger.debug("Bank", f"Finances separated and settings saved")
        self.save_user_settings()

    def get_combined_users(self, user_id):
        """Get list of users whose finances are combined with the given user"""
        logger.debug("Bank", f"Retrieving combined users for: {user_id}")
        if user_id in self.user_finance_settings:
            combined = self.user_finance_settings[user_id].get('combined_with', [])
            logger.debug("Bank", f"Found {len(combined)} combined users")
            return combined
        return []

    def get_financial_summary(self, user_id=None, start_date=None, end_date=None):
        """Get financial summary for a user including income, expenses, and balance"""
        transactions = self.get_user_finances(user_id)
        
        # Filter by date range if provided
        if start_date or end_date:
            filtered_transactions = []
            for t in transactions:
                tx_date = datetime.fromisoformat(t['timestamp']).date()
                if start_date and tx_date < start_date:
                    continue
                if end_date and tx_date > end_date:
                    continue
                filtered_transactions.append(t)
            transactions = filtered_transactions
        
        total_income = sum(t['amount'] for t in transactions if t['type'] == 'in')
        total_expenses = sum(t['amount'] for t in transactions if t['type'] == 'out')
        net_balance = total_income - total_expenses
        
        # Category breakdown - handle split transactions
        income_by_category = {}
        expense_by_category = {}
        
        for t in transactions:
            # Check if this transaction is split
            splits = t.get('splits', [])
            
            if splits:
                # Transaction is split - count each split separately
                for split in splits:
                    category = split.get('category', 'Uncategorized')
                    amount = split.get('amount', 0)
                    
                    if t['type'] == 'in':
                        income_by_category[category] = income_by_category.get(category, 0) + amount
                    else:
                        expense_by_category[category] = expense_by_category.get(category, 0) + amount
            else:
                # Regular transaction - use main category
                category = t.get('category', 'Uncategorized')
                if t['type'] == 'in':
                    income_by_category[category] = income_by_category.get(category, 0) + t['amount']
                else:
                    expense_by_category[category] = expense_by_category.get(category, 0) + t['amount']
        
        return {
            'total_income': total_income,
            'total_expenses': total_expenses,
            'net_balance': net_balance,
            'income_by_category': income_by_category,
            'expense_by_category': expense_by_category,
            'transaction_count': len(transactions)
        }

    def get_recurring_transactions(self, user_id=None):
        """Get recurring transactions as RecurringTransaction objects"""
        if user_id is None:
            user_id = self.current_user_id
            
        recurring_objects = []
        for recurring_data in self.recurring_transactions:
            try:
                recurring_tx = RecurringTransaction.from_dict(recurring_data)
                if user_id is None or recurring_tx.user_id == user_id:
                    recurring_objects.append(recurring_tx)
            except Exception as e:
                logger.error("Bank", f"Error loading recurring transaction: {e}")
                continue
                
        return recurring_objects

    # Bank Account Management Methods
    def get_user_bank_accounts(self, user_id=None):
        """Get all bank accounts for a user"""
        if user_id is None:
            user_id = self.current_user_id
        return self.account_manager.get_user_accounts(user_id)
    
    def add_bank_account(self, bank_name, account_type, account_name="", account_number="", initial_balance=0.0, user_id=None):
        """Add a new bank account for the user"""
        if user_id is None:
            user_id = self.current_user_id
        
        from .bank_accounts import BankAccount
        account = BankAccount(
            bank_name=bank_name,
            account_type=account_type,
            account_name=account_name,
            account_number=account_number,
            user_id=str(user_id) if user_id is not None else "",
            initial_balance=initial_balance
        )
        return self.account_manager.add_account(account)
    
    def get_account_balance(self, account_id):
        """Get current balance for a specific account"""
        return self.account_manager.calculate_account_balance(account_id, self)
    
    def get_account_transactions(self, account_id, user_id=None):
        """Get all transactions for a specific account"""
        if user_id is None:
            user_id = self.current_user_id
        
        user_transactions = self.get_user_finances(user_id)
        return [t for t in user_transactions if t.get('account_id') == account_id]
    
    def get_accounts_summary(self, user_id=None):
        """Get summary of all accounts with balances"""
        if user_id is None:
            user_id = self.current_user_id
        
        accounts = self.get_user_bank_accounts(user_id)
        summary = []
        
        for account in accounts:
            balance = self.get_account_balance(account.account_id)
            summary.append({
                'account_id': account.account_id,
                'display_name': account.get_display_name(),
                'bank_name': account.bank_name,
                'account_type': account.account_type,
                'balance': balance,
                'account': account
            })
        
        return summary
    
    def transfer_between_accounts(self, from_account_id, to_account_id, amount, description="Account Transfer"):
        """Transfer money between two accounts"""
        from_account = self.account_manager.get_account(from_account_id)
        to_account = self.account_manager.get_account(to_account_id)
        
        if not from_account or not to_account:
            raise ValueError("One or both accounts not found")
        
        if from_account.user_id != to_account.user_id:
            raise ValueError("Cannot transfer between accounts of different users")
        
        # Add withdrawal from source account
        self.add_transaction(
            amount=amount,
            desc=f"{description} (to {to_account.get_display_name()})",
            account=from_account.get_display_name(),
            account_id=from_account_id,
            type_='out',
            category='Transfer',
            user_id=from_account.user_id
        )
        
        # Add deposit to destination account
        self.add_transaction(
            amount=amount,
            desc=f"{description} (from {from_account.get_display_name()})",
            account=to_account.get_display_name(),
            account_id=to_account_id,
            type_='in',
            category='Transfer',
            user_id=to_account.user_id
        )
        
        return True

    def remove_transaction(self, transaction):
        """Remove a transaction - can accept either transaction dict or identifier+account"""
        if isinstance(transaction, dict):
            identifier = transaction.get('identifier')
            account = transaction.get('account')
        else:
            # Assume it's an identifier for backward compatibility
            identifier = transaction
            account = None
        
        logger.info("Bank", f"Removing transaction: {identifier}")
        if account:
            self.transactions = [t for t in self.transactions if not (t['identifier'] == identifier and t['account'] == account)]
        else:
            self.transactions = [t for t in self.transactions if t['identifier'] != identifier]
        logger.debug("Bank", f"Transaction removed successfully")
        self.save()

    def remove_recurring_transaction(self, recurring):
        """Remove a recurring transaction - can accept RecurringTransaction object or identifier"""
        if hasattr(recurring, 'identifier'):
            identifier = recurring.identifier
        elif isinstance(recurring, dict):
            identifier = recurring.get('identifier')
        else:
            identifier = recurring
        
        logger.info("Bank", f"Removing recurring transaction: {identifier}")
        self.recurring_transactions = [rt for rt in self.recurring_transactions if rt['identifier'] != identifier]
        logger.debug("Bank", f"Recurring transaction removed successfully")
        self.save_recurring()

    def get_transaction(self, identifier, account):
        logger.debug("Bank", f"Retrieving transaction {identifier} from account {account}")
        for t in self.transactions:
            if t['identifier'] == identifier and t['account'] == account:
                logger.debug("Bank", f"Transaction found")
                return t
        logger.debug("Bank", f"Transaction not found")
        return None

    def get_recurring_transaction(self, identifier):
        """Get a recurring transaction by identifier"""
        logger.debug("Bank", f"Retrieving recurring transaction: {identifier}")
        for rt in self.recurring_transactions:
            if rt['identifier'] == identifier:
                logger.debug("Bank", f"Recurring transaction found")
                return rt
        logger.debug("Bank", f"Recurring transaction not found")
        return None

    def list_transactions(self, account=None, user_id=None):
        """List transactions, optionally filtered by account and/or user"""
        logger.debug("Bank", f"Listing transactions for account: {account}, user: {user_id}")
        transactions = self.transactions
        
        if user_id:
            # Use get_user_finances to include combined finances
            transactions = self.get_user_finances(user_id)
            
        if account:
            transactions = [t for t in transactions if t['account'] == account]
        
        logger.debug("Bank", f"Found {len(transactions)} transactions")
        return transactions

    def list_recurring_transactions(self, user_id=None):
        """List recurring transactions for a user"""
        if user_id is None:
            user_id = self.current_user_id
        
        logger.debug("Bank", f"Listing recurring transactions for user: {user_id}")
        if user_id:
            recurring = [rt for rt in self.recurring_transactions if rt.get('user_id') == user_id]
        else:
            recurring = self.recurring_transactions
        
        logger.debug("Bank", f"Found {len(recurring)} recurring transactions")
        return recurring

    def search_transactions(self, **criteria):
        logger.debug("Bank", f"Searching transactions with criteria: {criteria}")
        def match(t, criteria):
            for key, value in criteria.items():
                if key == 'amount_range':
                    min_amt, max_amt = value
                    if not (min_amt <= t['amount'] <= max_amt):
                        return False
                elif key == 'user_id':
                    # Handle user filtering with combined finances
                    user_transactions = self.get_user_finances(value)
                    if t not in user_transactions:
                        return False
                elif key in t:
                    if isinstance(value, (list, tuple)):
                        if t[key] not in value:
                            return False
                    else:
                        if t[key] != value:
                            return False
                else:
                    return False
            return True
        
        results = [t for t in self.transactions if match(t, criteria)]
        logger.debug("Bank", f"Search found {len(results)} matching transactions")
        return results

    def save(self):
        logger.debug("Bank", "Saving transactions to disk")
        with open(BANK_DATA_FILE, 'w') as f:
            json.dump(self.transactions, f, indent=2)
        logger.debug("Bank", "Transactions saved successfully")

    def save_recurring(self):
        """Save recurring transactions to file"""
        logger.debug("Bank", "Saving recurring transactions to disk")
        with open(RECURRING_DATA_FILE, 'w') as f:
            json.dump(self.recurring_transactions, f, indent=2)
        logger.debug("Bank", "Recurring transactions saved successfully")

    def save_user_settings(self):
        """Save user finance settings to file"""
        logger.debug("Bank", "Saving user finance settings to disk")
        with open(USER_FINANCE_SETTINGS_FILE, 'w') as f:
            json.dump(self.user_finance_settings, f, indent=2)
        logger.debug("Bank", "User settings saved successfully")

    def save_loans(self):
        logger.debug("Bank", "Saving loans to disk")
        with open(LOANS_DATA_FILE, 'w') as f:
            json.dump(self.loans, f, indent=2)
        logger.debug("Bank", "Loans saved successfully")

    def load(self):
        logger.debug("Bank", "Loading transactions from disk")
        if os.path.exists(BANK_DATA_FILE):
            with open(BANK_DATA_FILE, 'r') as f:
                content = f.read().strip()
                if content:
                    self.transactions = json.loads(content)
                else:
                    self.transactions = []
        else:
            self.transactions = []
        logger.debug("Bank", "Transactions loaded successfully")

    def load_recurring(self):
        """Load recurring transactions from file"""
        logger.debug("Bank", "Loading recurring transactions from disk")
        if os.path.exists(RECURRING_DATA_FILE):
            with open(RECURRING_DATA_FILE, 'r') as f:
                content = f.read().strip()
                if content:
                    self.recurring_transactions = json.loads(content)
                else:
                    self.recurring_transactions = []
        else:
            self.recurring_transactions = []
        logger.debug("Bank", "Recurring transactions loaded successfully")

    def load_user_settings(self):
        """Load user finance settings from file"""
        logger.debug("Bank", "Loading user finance settings from disk")
        if os.path.exists(USER_FINANCE_SETTINGS_FILE):
            with open(USER_FINANCE_SETTINGS_FILE, 'r') as f:
                content = f.read().strip()
                if content:
                    self.user_finance_settings = json.loads(content)
                else:
                    self.user_finance_settings = {}
        else:
            self.user_finance_settings = {}
        logger.debug("Bank", "User settings loaded successfully")

    def load_loans(self):
        logger.debug("Bank", "Loading loans from disk")
        if os.path.exists(LOANS_DATA_FILE):
            with open(LOANS_DATA_FILE, 'r') as f:
                content = f.read().strip()
                if content:
                    self.loans = json.loads(content)
                else:
                    self.loans = []
        else:
            self.loans = []
        logger.debug("Bank", "Loans loaded successfully")

    def export_csv(self, csv_path, account=None, user_id=None):
        fieldnames = ['amount', 'desc', 'account', 'identifier', 'type', 'category', 'timestamp', 'user_id']
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for t in self.list_transactions(account, user_id):
                writer.writerow(t)
