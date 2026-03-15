import os
import json
import random
import string
from datetime import date, datetime
try:
    from .app_paths import TENANT_DB
except ImportError:
    from app_paths import TENANT_DB
from assets.Logger import Logger
logger = Logger()
def generate_tenant_id(length=10):
    chars = string.ascii_letters + string.digits
    return ''.join(random.SystemRandom().choice(chars) for _ in range(length))

class Tenant:
    def __init__(self, name, rental_period, rent_amount, deposit_amount=0.0, contact_info=None, notes=None, tenant_id=None,
                 monthly_exceptions=None, months_to_charge=None, total_rent_paid=0.0, delinquency_balance=0.0,
                 delinquent_months=None, account_status='active', monthly_status=None, overpayment_credit=0.0, rent_due_date=None, payment_history=None,
                 service_credit=0.0, service_credit_history=None, user_id=None, user_ids=None, last_modified=None):
        self.name = name
        self.tenant_id = tenant_id if tenant_id is not None else generate_tenant_id()
        self.rental_period = rental_period  # (start_date, end_date)
        self.deposit_amount = deposit_amount
        self.contact_info = contact_info or {}
        # Notes are stored internally as a list for better JSON compatibility
        def _split_to_lines(val):
            if not val:
                return []
            # Split by any newline variants and trim; drop empties
            if isinstance(val, str):
                return [ln.strip() for ln in val.splitlines() if ln.strip()]
            return []

        if isinstance(notes, list):
            # Flatten any embedded newlines within list items
            flat = []
            for item in notes:
                flat.extend(_split_to_lines(str(item)))
            self._notes_list = flat
        elif isinstance(notes, str):
            self._notes_list = _split_to_lines(notes)
        else:
            self._notes_list = []
        self.rent_amount = rent_amount
        self.monthly_exceptions = monthly_exceptions or {}
        self.months_to_charge = months_to_charge or []
        self.total_rent_paid = total_rent_paid
        self.delinquency_balance = delinquency_balance
        self.delinquent_months = delinquent_months or []
        self.account_status = account_status.lower() if account_status else 'active'
        # monthly_status structure: {(year, month): {'status': ..., 'payment_type': ..., 'other_type': ...}}
        self.monthly_status = monthly_status or {}
        self.overpayment_credit = overpayment_credit
        self.rent_due_date = rent_due_date
        self.payment_history = payment_history or []  # Add payment_history initialization
        self.service_credit = service_credit  # Available service credit balance
        self.service_credit_history = service_credit_history or []  # Track service credit transactions
        # Support both user_id (legacy) and user_ids (new multi-user)
        if user_ids is not None:
            self.user_ids = user_ids if isinstance(user_ids, list) else [user_ids]
        elif user_id is not None:
            self.user_ids = [user_id]
        else:
            self.user_ids = []  # List of users who have access to this tenant
        
        # Track last modified timestamp
        self.last_modified = last_modified or datetime.now().isoformat()

    @property 
    def due_day(self):
        """Return the due day of the month, derived from rent_due_date"""
        try:
            return int(self.rent_due_date) if self.rent_due_date else 1
        except (ValueError, TypeError):
            return 1
    
    @due_day.setter
    def due_day(self, value):
        """Set the due day of the month, updates rent_due_date"""
        try:
            # Validate the day is between 1-31
            day_int = int(value)
            if 1 <= day_int <= 31:
                self.rent_due_date = str(day_int)
                logger.debug("Tenant", f"Due day set to {day_int}")
            else:
                logger.warning("Tenant", f"Due day {day_int} out of range (1-31), setting to 1")
                self.rent_due_date = "1"
        except (ValueError, TypeError) as e:
            logger.warning("Tenant", f"Invalid due day value '{value}': {e}. Setting to 1.")
            self.rent_due_date = "1"

    def to_dict(self):
        logger.debug("Tenant", f"Converting tenant {self.tenant_id} to dictionary")
        # Convert monthly_status keys to strings for JSON
        monthly_status_str = {}
        for k, v in self.monthly_status.items():
            if isinstance(k, tuple) and len(k) == 2:
                # Convert tuple (year, month) to string format
                try:
                    year, month = int(k[0]), int(k[1])
                    key_str = f"{year}-{month:02d}"
                except (ValueError, TypeError):
                    logger.warning("Tenant", f"Invalid monthly_status key format: {k}")
                    continue
            elif isinstance(k, str):
                # Already in string format
                key_str = k
            else:
                logger.warning("Tenant", f"Unknown monthly_status key format: {k}")
                continue
            monthly_status_str[key_str] = v
        return {
            'name': self.name,
            'tenant_id': self.tenant_id,
            'rental_period': self.rental_period,
            'deposit_amount': self.deposit_amount,
            'contact_info': self.contact_info,
            # Store notes as a list in JSON
            'notes': self._notes_list,
            'rent_amount': self.rent_amount,
            'monthly_exceptions': self.monthly_exceptions,
            'months_to_charge': self.months_to_charge,
            'total_rent_paid': self.total_rent_paid,
            'delinquency_balance': self.delinquency_balance,
            'delinquent_months': self.delinquent_months,
            'account_status': self.account_status,
            'monthly_status': monthly_status_str,
            'overpayment_credit': self.overpayment_credit,
            'rent_due_date': self.rent_due_date,
            'payment_history': self.payment_history,  # Add payment_history to save data
            'service_credit': self.service_credit,
            'service_credit_history': self.service_credit_history,
            'user_ids': self.user_ids,
            'user_id': self.user_ids[0] if self.user_ids else None,  # Backward compatibility
            'last_modified': self.last_modified
        }

    @property
    def notes(self):
        """Backward-compatible notes as a single string (joined by newlines)."""
        return "\n".join(self._notes_list).strip()

    @notes.setter
    def notes(self, value):
        """Accepts a string or list and updates the internal list representation."""
        if isinstance(value, list):
            self._notes_list = [str(v) for v in value if str(v).strip()]
        elif isinstance(value, str):
            # Treat as single entry; keep existing split behavior simple
            v = value.strip()
            # If contains newlines, split into entries; else single
            if "\n" in v:
                self._notes_list = [line for line in (ln.strip() for ln in v.split("\n")) if line]
            else:
                self._notes_list = [v] if v else []
        else:
            self._notes_list = []

    def add_note(self, message):
        msg = (message or "").strip()
        if msg:
            self._notes_list.append(msg)

class TenantManager:
    def __init__(self, current_user_id=None):
        logger.debug("TenantManager", f"Initializing TenantManager for user: {current_user_id}")
        self.tenants = {}
        self.current_user_id = current_user_id
        self.load()
        logger.info("TenantManager", f"TenantManager initialized with {len(self.tenants)} tenants")

    def set_current_user(self, user_id):
        """Set the current user for filtering tenants"""
        logger.debug("TenantManager", f"Setting current user to {user_id}")
        self.current_user_id = user_id
        self.load()  # Reload to apply user filtering
        logger.info("TenantManager", f"Current user set to {user_id}")

    def is_admin(self):
        """Check if current user is admin"""
        if not self.current_user_id:
            return False
        try:
            from src.account import AccountManager
            am = AccountManager()
            account = am.get_account(self.current_user_id)
            if account and account.get('details', {}).get('role') == 'admin':
                return True
        except Exception:
            pass
        return False

    def add_tenant(self, name, rental_period, rent_amount, deposit_amount=0.0, contact_info=None, notes=None, rent_due_date=None, user_id=None):
        logger.debug("TenantManager", f"Adding tenant: {name}")
        # Use current user if no user_id specified
        if user_id is None:
            user_id = self.current_user_id
        # Convert to user_ids list format
        user_ids = [user_id] if user_id else []
        tenant = Tenant(name, rental_period, rent_amount, deposit_amount, contact_info, notes, rent_due_date=rent_due_date, user_ids=user_ids)
        self.tenants[tenant.tenant_id] = tenant
        self.save()
        logger.info("TenantManager", f"Tenant '{name}' added with ID {tenant.tenant_id}")
        return tenant

    def get_tenant(self, tenant_id):
        return self.tenants.get(tenant_id)

    def update_tenant(self, tenant_or_id, **kwargs):
        """Update tenant by ID or tenant object"""
        logger.debug("TenantManager", f"Updating tenant: {tenant_or_id}")
        if isinstance(tenant_or_id, Tenant):
            # Update the existing tenant object in our dictionary
            tenant = tenant_or_id
            if tenant.tenant_id in self.tenants:
                tenant.last_modified = datetime.now().isoformat()  # Update timestamp
                self.tenants[tenant.tenant_id] = tenant
                self.save()
                logger.info("TenantManager", f"Tenant {tenant.tenant_id} updated")
                return tenant
            else:
                logger.warning("TenantManager", f"Tenant {tenant.tenant_id} not found in manager")
                return None
        else:
            # Update by ID with kwargs
            tenant_id = tenant_or_id
            tenant = self.get_tenant(tenant_id)
            if not tenant:
                logger.warning("TenantManager", f"Tenant {tenant_id} not found")
                return None
            for k, v in kwargs.items():
                if hasattr(tenant, k):
                    setattr(tenant, k, v)
            tenant.last_modified = datetime.now().isoformat()  # Update timestamp
            self.save()
            logger.info("TenantManager", f"Tenant {tenant_id} updated with {len(kwargs)} changes")
            return tenant

    def list_tenants(self):
        """Return list of tenants filtered by current user (or all if admin)"""
        if self.is_admin():
            return list(self.tenants.values())
        elif self.current_user_id:
            return [t for t in self.tenants.values() if self.current_user_id in t.user_ids]
        else:
            return []  # No user set, return empty list

    def save(self):
        try:
            logger.debug("TenantManager", f"Saving {len(self.tenants)} tenants to database")
            
            # Save to JSON
            with open(TENANT_DB, 'w') as f:
                json.dump({tid: t.to_dict() for tid, t in self.tenants.items()}, f, indent=2)
            
            # Also sync to SQLite database for backup/reporting
            try:
                from .rent_db import RentDatabaseManager
            except ImportError:
                from rent_db import RentDatabaseManager
            
            rent_db = RentDatabaseManager()
            rent_db.sync_all_tenants(self.tenants)
            
            logger.info("TenantManager", f"Saved {len(self.tenants)} tenants to both JSON and database")
        except Exception as e:
            logger.error("TenantManager", f"Failed to save tenants: {e}")

    def load(self):
        logger.debug("TenantManager", "Loading tenants from database")
        if os.path.exists(TENANT_DB):
            try:
                with open(TENANT_DB, 'r') as f:
                    content = f.read().strip()
                    if not content:
                        data = {}
                    else:
                        data = json.loads(content)
                for tid, t in data.items():
                    # Convert monthly_status keys back to tuples
                    if 'monthly_status' in t:
                        ms = t['monthly_status']
                        new_ms = {}
                        for k, v in ms.items():
                            if isinstance(k, str) and '-' in k:
                                # Convert string format "YYYY-MM" to tuple (year, month)
                                try:
                                    year, month = k.split('-')
                                    new_ms[tuple(map(int, [year, month]))] = v
                                except ValueError:
                                    logger.warning("TenantManager", f"Invalid monthly_status key format: {k}")
                                    continue
                            elif isinstance(k, (list, tuple)) and len(k) == 2:
                                # Already in tuple/list format
                                try:
                                    new_ms[tuple(map(int, k))] = v
                                except ValueError:
                                    logger.warning("TenantManager", f"Invalid monthly_status key values: {k}")
                                    continue
                            else:
                                logger.warning("TenantManager", f"Unknown monthly_status key format: {k}")
                                continue
                        t['monthly_status'] = new_ms
                    
                    # Migrate notes to list: split strings by newline; also normalize any list items with embedded newlines
                    if 'notes' not in t:
                        t['notes'] = []
                    else:
                        if isinstance(t['notes'], str):
                            notes_lines = [ln.strip() for ln in t['notes'].splitlines() if ln.strip()]
                            t['notes'] = notes_lines
                        elif isinstance(t['notes'], list):
                            flat = []
                            for item in t['notes']:
                                flat.extend([ln.strip() for ln in str(item).splitlines() if ln.strip()])
                            t['notes'] = flat

                    # Migration: Add payment_history if it doesn't exist
                    if 'payment_history' not in t:
                        t['payment_history'] = []
                    
                    # Migration: Add service credit fields if they don't exist
                    if 'service_credit' not in t:
                        t['service_credit'] = 0.0
                    if 'service_credit_history' not in t:
                        t['service_credit_history'] = []
                    
                    # Migration: Convert user_id to user_ids (new multi-user system)
                    if 'user_ids' not in t:
                        # Migrate from old user_id format
                        if t.get('user_id'):
                            t['user_ids'] = [t['user_id']]
                        else:
                            t['user_ids'] = []
                    else:
                        # Ensure user_ids is a list
                        if isinstance(t.get('user_ids'), str):
                            t['user_ids'] = [t['user_ids']]
                    
                    self.tenants[tid] = Tenant(**t)
                logger.info("TenantManager", f"Loaded {len(self.tenants)} tenants from database")
            except Exception as e:
                logger.error("TenantManager", f"Failed to load tenants: {e}")
                self.tenants = {}
        else:
            logger.debug("TenantManager", f"Tenant database not found at {TENANT_DB}")
            self.tenants = {}

    def search_tenants(self, **criteria):
        """Search tenants filtered by current user access"""
        logger.debug("TenantManager", f"Searching tenants with criteria: {criteria}")
        def match(t, criteria):
            for key, value in criteria.items():
                if key in t.__dict__:
                    tenant_val = t.__dict__[key]
                    # Case-insensitive and whitespace-insensitive for strings
                    if isinstance(tenant_val, str) and isinstance(value, str):
                        if tenant_val.strip().lower() != value.strip().lower():
                            return False
                    elif isinstance(value, (list, tuple)):
                        if tenant_val not in value:
                            return False
                    else:
                        if tenant_val != value:
                            return False
                else:
                    return False
            return True
        
        # Apply user filtering
        available_tenants = self.list_tenants()
        results = [t for t in available_tenants if match(t, criteria)]
        logger.info("TenantManager", f"Search found {len(results)} tenant(s) matching criteria")
        return results
