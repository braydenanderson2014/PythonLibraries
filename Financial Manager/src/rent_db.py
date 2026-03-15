"""
Rent Database Manager - Syncs rent and payment data to SQLite database
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager

try:
    from .app_paths import get_resource_path
except ImportError:
    from app_paths import get_resource_path

try:
    from .assets.Logger import Logger
except ImportError:
    from assets.Logger import Logger

logger = Logger()

class RentDatabaseManager:
    """Manages rent and payment data in SQLite database with connection pooling"""
    
    def __init__(self, db_path=None):
        self.db_path = db_path or get_resource_path('rent_data.db')
        # Enable WAL mode for better concurrent access
        self._enable_wal_mode()
        self.init_database()
    
    def _enable_wal_mode(self):
        """Enable Write-Ahead Logging mode for better concurrency"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA synchronous=NORMAL')  # Faster writes
            conn.execute('PRAGMA cache_size=10000')    # Larger cache
            conn.execute('PRAGMA temp_store=MEMORY')   # Use memory for temp storage
            conn.close()
            logger.debug("RentDB", "WAL mode and optimizations enabled")
        except Exception as e:
            logger.warning("RentDB", f"Could not enable WAL mode: {e}")
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()
    
    def init_database(self):
        """Initialize database with required tables"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Tenants table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tenants (
                        tenant_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        rental_period TEXT,
                        rent_amount REAL,
                        deposit_amount REAL,
                        contact_info TEXT,
                        notes TEXT,
                        total_rent_paid REAL,
                        delinquency_balance REAL,
                        account_status TEXT,
                        overpayment_credit REAL,
                        rent_due_date TEXT,
                        service_credit REAL,
                        user_ids TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Payments table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS payments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tenant_id TEXT NOT NULL,
                        amount REAL NOT NULL,
                        payment_type TEXT,
                        payment_date DATE,
                        payment_month TEXT,
                        year INTEGER,
                        month INTEGER,
                        is_credit_usage BOOLEAN DEFAULT 0,
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
                    )
                ''')
                
                # Monthly status table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS monthly_status (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tenant_id TEXT NOT NULL,
                        year INTEGER,
                        month INTEGER,
                        status TEXT,
                        payment_type TEXT,
                        payment_date TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(tenant_id, year, month),
                        FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
                    )
                ''')
                
                # Create indices for better performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_payments_tenant_id ON payments(tenant_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_payments_year_month ON payments(year, month)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_monthly_status_tenant_id ON monthly_status(tenant_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_monthly_status_year_month ON monthly_status(year, month)')
                
                conn.commit()
            logger.info("RentDB", "Database initialized successfully with indices")
        except Exception as e:
            logger.error("RentDB", f"Failed to initialize database: {e}")
    
    def sync_tenant(self, tenant):
        """Sync a single tenant to database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Serialize user_ids list to JSON
                user_ids_json = json.dumps(tenant.user_ids) if hasattr(tenant, 'user_ids') else '[]'
                
                # Upsert tenant
                cursor.execute('''
                    INSERT OR REPLACE INTO tenants 
                    (tenant_id, name, rental_period, rent_amount, deposit_amount, contact_info,
                     notes, total_rent_paid, delinquency_balance, account_status, overpayment_credit,
                     rent_due_date, service_credit, user_ids, last_modified)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    tenant.tenant_id,
                    tenant.name,
                    json.dumps(tenant.rental_period) if tenant.rental_period else None,
                    tenant.rent_amount,
                    tenant.deposit_amount,
                    json.dumps(tenant.contact_info) if tenant.contact_info else None,
                    tenant.notes if hasattr(tenant, 'notes') else '',
                    tenant.total_rent_paid,
                    tenant.delinquency_balance,
                    tenant.account_status,
                    tenant.overpayment_credit,
                    tenant.rent_due_date,
                    tenant.service_credit if hasattr(tenant, 'service_credit') else 0.0,
                    user_ids_json,
                    datetime.now().isoformat()
                ))
                
                conn.commit()
            logger.debug("RentDB", f"Synced tenant {tenant.tenant_id} to database")
            return True
        except Exception as e:
            logger.error("RentDB", f"Failed to sync tenant: {e}")
            return False
    
    def sync_payment(self, tenant_id, payment_record):
        """Sync a single payment to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO payments 
                (tenant_id, amount, payment_type, payment_date, payment_month, year, month,
                 is_credit_usage, notes, last_modified)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                tenant_id,
                payment_record.get('amount'),
                payment_record.get('type'),
                payment_record.get('date'),
                payment_record.get('payment_month'),
                payment_record.get('year'),
                payment_record.get('month'),
                1 if payment_record.get('is_credit_usage') else 0,
                payment_record.get('notes', ''),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            logger.debug("RentDB", f"Synced payment for tenant {tenant_id} to database")
            return True
        except Exception as e:
            logger.error("RentDB", f"Failed to sync payment: {e}")
            return False
    
    def sync_monthly_status(self, tenant_id, year, month, status_data):
        """Sync monthly status to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO monthly_status 
                (tenant_id, year, month, status, payment_type, payment_date, last_modified)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                tenant_id,
                year,
                month,
                status_data.get('status'),
                status_data.get('payment_type'),
                status_data.get('payment_date'),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            logger.debug("RentDB", f"Synced monthly status for tenant {tenant_id} ({year}-{month:02d})")
            return True
        except Exception as e:
            logger.error("RentDB", f"Failed to sync monthly status: {e}")
            return False
    
    def sync_all_tenants(self, tenants_dict):
        """
        Sync all tenants and their payment history to database
        Optimized with batch operations for better performance
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Prepare batch data for tenants
                tenant_data = []
                payment_data = []
                monthly_status_data = []
                
                for tenant_id, tenant in tenants_dict.items():
                    # Prepare tenant data
                    user_ids_json = json.dumps(tenant.user_ids) if hasattr(tenant, 'user_ids') else '[]'
                    
                    # Normalize rental_period to standard format (list with two ISO date strings)
                    normalized_rental_period = None
                    if tenant.rental_period:
                        try:
                            # Handle different formats: list, tuple, or dict
                            if isinstance(tenant.rental_period, dict):
                                # Dict format: {'start_date': '...', 'end_date': '...'}
                                start_date = tenant.rental_period.get('start_date')
                                end_date = tenant.rental_period.get('end_date')
                                if start_date and end_date:
                                    normalized_rental_period = json.dumps([start_date, end_date])
                            elif isinstance(tenant.rental_period, (list, tuple)) and len(tenant.rental_period) >= 2:
                                # List or tuple format: [start_date, end_date] or (start_date, end_date)
                                normalized_rental_period = json.dumps([tenant.rental_period[0], tenant.rental_period[1]])
                            else:
                                # Already in acceptable format or unknown - store as-is
                                normalized_rental_period = json.dumps(tenant.rental_period)
                        except Exception as e:
                            logger.warning("RentDB", f"Failed to normalize rental_period for tenant {tenant_id}: {e}")
                            normalized_rental_period = None
                    
                    tenant_data.append((
                        tenant.tenant_id,
                        tenant.name,
                        normalized_rental_period,
                        tenant.rent_amount,
                        tenant.deposit_amount,
                        json.dumps(tenant.contact_info) if tenant.contact_info else None,
                        tenant.notes if hasattr(tenant, 'notes') else '',
                        tenant.total_rent_paid,
                        tenant.delinquency_balance,
                        tenant.account_status,
                        tenant.overpayment_credit,
                        tenant.rent_due_date,
                        tenant.service_credit if hasattr(tenant, 'service_credit') else 0.0,
                        user_ids_json,
                        datetime.now().isoformat()
                    ))
                    
                    # Prepare payment history data
                    if hasattr(tenant, 'payment_history') and tenant.payment_history:
                        for payment_record in tenant.payment_history:
                            payment_data.append((
                                tenant_id,
                                payment_record.get('amount'),
                                payment_record.get('type'),
                                payment_record.get('date'),
                                payment_record.get('payment_month'),
                                payment_record.get('year'),
                                payment_record.get('month'),
                                1 if payment_record.get('is_credit_usage') else 0,
                                payment_record.get('notes', '')
                            ))
                    
                    # Prepare monthly status data
                    if hasattr(tenant, 'monthly_status') and tenant.monthly_status:
                        for key, status_data in tenant.monthly_status.items():
                            # Handle both tuple keys (year, month) and string keys (e.g., "2026-01")
                            try:
                                if isinstance(key, tuple) and len(key) == 2:
                                    year, month = key
                                elif isinstance(key, str) and '-' in key:
                                    year_str, month_str = key.split('-')
                                    year = int(year_str)
                                    month = int(month_str)
                                else:
                                    # Skip invalid keys
                                    logger.warning("RentDB", f"Skipping invalid monthly_status key for tenant {tenant_id}: {key}")
                                    continue
                                
                                # Extract payment info from status_data (which is just a status string)
                                status_str = status_data.get('status') if isinstance(status_data, dict) else status_data
                                
                                # Get payment_type and payment_date from actual payments in that month
                                payment_type = None
                                payment_date = None
                                if hasattr(tenant, 'payment_history'):
                                    for payment in tenant.payment_history:
                                        if payment.get('year') == year and payment.get('month') == month:
                                            # Use the first real payment (not credit usage) in this month
                                            if not payment.get('is_credit_usage', False):
                                                if payment_type is None:
                                                    payment_type = payment.get('type')
                                                    payment_date = payment.get('date')
                                                break
                                
                                monthly_status_data.append((
                                    tenant_id,
                                    year,
                                    month,
                                    status_str,
                                    payment_type,
                                    payment_date,
                                    datetime.now().isoformat()
                                ))
                            except (ValueError, TypeError) as e:
                                logger.warning("RentDB", f"Error processing monthly_status for tenant {tenant_id}, key {key}: {e}")
                                continue
                
                # Batch insert tenants
                if tenant_data:
                    cursor.executemany('''
                        INSERT OR REPLACE INTO tenants 
                        (tenant_id, name, rental_period, rent_amount, deposit_amount, contact_info,
                         notes, total_rent_paid, delinquency_balance, account_status, overpayment_credit,
                         rent_due_date, service_credit, user_ids, last_modified)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', tenant_data)
                
                # Clear old payments and batch insert new ones
                if payment_data:
                    # More efficient: delete all payments first, then batch insert
                    cursor.execute('DELETE FROM payments')
                    cursor.executemany('''
                        INSERT INTO payments 
                        (tenant_id, amount, payment_type, payment_date, payment_month, year, month,
                         is_credit_usage, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', payment_data)
                
                # Clear old monthly status and batch insert new ones
                if monthly_status_data:
                    # Deduplicate monthly_status_data to prevent UNIQUE constraint violations
                    # Keep only the most recent entry for each (tenant_id, year, month) combination
                    unique_monthly_status = {}
                    for entry in monthly_status_data:
                        key = (entry[0], entry[1], entry[2])  # (tenant_id, year, month)
                        unique_monthly_status[key] = entry  # Last one wins
                    
                    cursor.execute('DELETE FROM monthly_status')
                    cursor.executemany('''
                        INSERT INTO monthly_status 
                        (tenant_id, year, month, status, payment_type, payment_date, last_modified)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', list(unique_monthly_status.values()))
                
                conn.commit()
            logger.info("RentDB", f"Synced {len(tenants_dict)} tenants to database (optimized batch)")
            return True
        except Exception as e:
            logger.error("RentDB", f"Failed to sync all tenants: {e}")
            return False
    
    def get_last_modified(self, tenant_id):
        """Get last modified timestamp for a tenant"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT last_modified FROM tenants WHERE tenant_id = ?',
                (tenant_id,)
            )
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return result[0]
            return None
        except Exception as e:
            logger.error("RentDB", f"Failed to get last modified: {e}")
            return None
    
    def get_payment_history(self, tenant_id):
        """Get all payments for a tenant from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT * FROM payments WHERE tenant_id = ? ORDER BY created_at DESC',
                (tenant_id,)
            )
            results = cursor.fetchall()
            conn.close()
            
            return results
        except Exception as e:
            logger.error("RentDB", f"Failed to get payment history: {e}")
            return []
    
    def delete_tenant(self, tenant_id):
        """Delete a tenant and all associated data from the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Delete from monthly_status table
            cursor.execute('DELETE FROM monthly_status WHERE tenant_id = ?', (tenant_id,))
            logger.debug("RentDB", f"Deleted monthly status records for tenant {tenant_id}")
            
            # Delete from payments table
            cursor.execute('DELETE FROM payments WHERE tenant_id = ?', (tenant_id,))
            logger.debug("RentDB", f"Deleted payment records for tenant {tenant_id}")
            
            # Delete from tenants table
            cursor.execute('DELETE FROM tenants WHERE tenant_id = ?', (tenant_id,))
            logger.debug("RentDB", f"Deleted tenant record for tenant {tenant_id}")
            
            conn.commit()
            conn.close()
            
            logger.info("RentDB", f"Successfully deleted tenant {tenant_id} and all associated data from database")
            return True
        except Exception as e:
            logger.error("RentDB", f"Failed to delete tenant {tenant_id}: {e}")
            return False

