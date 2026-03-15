"""
Database module for Financial Manager
Handles SQLite database operations for rent tracking and tenant data
"""

import sqlite3
import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import sys

# Import app paths
try:
    from .app_paths import get_app_data_dir
except ImportError:
    from app_paths import get_app_data_dir
from assets.Logger import Logger
logger = Logger()

# Import TenantManager for mismatch detection
try:
    from .tenant import TenantManager
except ImportError:
    from tenant import TenantManager
class DatabaseManager:
    """Manages SQLite database operations for Financial Manager"""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize database manager"""
        logger.debug("DatabaseManager", "Initializing DatabaseManager")
        if db_path is None:
            # Use data directory from app_paths
            data_dir = get_app_data_dir()
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, 'financial_manager.db')
            logger.debug("DatabaseManager", f"Using default database path: {db_path}")
        
        self.db_path = db_path
        self.connection = None
        logger.info("DatabaseManager", f"Initializing database at {db_path}")
        self.initialize_database()
    
    def connect(self):
        """Establish database connection"""
        if self.connection is None:
            logger.debug("DatabaseManager", f"Establishing database connection to {self.db_path}")
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
            logger.info("DatabaseManager", "Database connection established")
        return self.connection
    
    def close(self):
        """Close database connection"""
        if self.connection:
            logger.debug("DatabaseManager", "Closing database connection")
            self.connection.close()
            self.connection = None
            logger.info("DatabaseManager", "Database connection closed")
    
    def execute_query(self, query: str, params: Tuple = ()) -> sqlite3.Cursor:
        """Execute a database query"""
        logger.debug("DatabaseManager", f"Executing query: {query[:100]}..." if len(query) > 100 else f"Executing query: {query}")
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor
    
    def commit(self):
        """Commit changes to database"""
        if self.connection:
            logger.debug("DatabaseManager", "Committing database changes")
            self.connection.commit()
            logger.debug("DatabaseManager", "Changes committed successfully")
    
    def initialize_database(self):
        """Create database tables if they don't exist"""
        logger.debug("DatabaseManager", "Initializing database tables")
        conn = self.connect()
        cursor = conn.cursor()
        
        # Tenants table
        logger.debug("DatabaseManager", "Creating tenants table")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tenants (
                tenant_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                contact_info TEXT,
                account_status TEXT DEFAULT 'active',
                rent_amount REAL DEFAULT 0.0,
                deposit_amount REAL DEFAULT 0.0,
                rent_due_date INTEGER DEFAULT 1,
                delinquency_balance REAL DEFAULT 0.0,
                overpayment_credit REAL DEFAULT 0.0,
                service_credit REAL DEFAULT 0.0,
                rental_period_start TEXT,
                rental_period_end TEXT,
                lease_type TEXT,
                notes TEXT,
                user_ids TEXT,
                last_modified TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_synced_at TIMESTAMP
            )
        ''')
        
        # Payment history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payment_history (
                payment_id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                date_received TEXT,
                amount REAL,
                payment_type TEXT,
                payment_month TEXT,
                status TEXT,
                details TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE
            )
        ''')
        
        # Monthly overrides table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS monthly_overrides (
                override_id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                month TEXT,
                year INTEGER,
                override_amount REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE
            )
        ''')
        
        # Data sync log table (for tracking mismatches)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_log (
                sync_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                entity_type TEXT,
                entity_id TEXT,
                source TEXT,
                mismatch_type TEXT,
                json_data TEXT,
                db_data TEXT,
                notes TEXT
            )
        ''')
        
        # Disputes table
        logger.debug("DatabaseManager", "Creating disputes table")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS disputes (
                dispute_id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                dispute_type TEXT NOT NULL,
                description TEXT,
                amount REAL,
                reference_month TEXT,
                reference_payment_id TEXT,
                created_by TEXT DEFAULT 'tenant_web_ui',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'open',
                admin_notes TEXT,
                evidence_notes TEXT,
                resolved_at TIMESTAMP,
                FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
                FOREIGN KEY (reference_payment_id) REFERENCES payment_history(payment_id) ON DELETE SET NULL
            )
        ''')
        
        conn.commit()        
        logger.info("DatabaseManager", "Database initialization complete")    
    # ==================== TENANT OPERATIONS ====================
    
    def add_tenant(self, tenant_id: str, name: str, **kwargs) -> bool:
        """Add a new tenant to the database"""
        logger.debug("DatabaseManager", f"Adding tenant: {tenant_id}, name: {name}")
        try:
            query = '''
                INSERT INTO tenants (
                    tenant_id, name, contact_info, account_status, rent_amount,
                    deposit_amount, rent_due_date, delinquency_balance, overpayment_credit,
                    service_credit, rental_period_start, rental_period_end, lease_type, notes,
                    last_synced_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            
            params = (
                tenant_id,
                name,
                kwargs.get('contact_info', ''),
                (kwargs.get('account_status', 'active') or 'active').lower(),
                kwargs.get('rent_amount', 0.0),
                kwargs.get('deposit_amount', 0.0),
                kwargs.get('rent_due_date', 1),
                kwargs.get('delinquency_balance', 0.0),
                kwargs.get('overpayment_credit', 0.0),
                kwargs.get('service_credit', 0.0),
                kwargs.get('rental_period_start', None),
                kwargs.get('rental_period_end', None),
                kwargs.get('lease_type', None),
                kwargs.get('notes', ''),
                kwargs.get('last_synced_at', datetime.now().isoformat())
            )
            
            cursor = self.execute_query(query, params)
            self.commit()
            logger.info("DatabaseManager", f"Tenant added successfully: {tenant_id}")
            return True
        except Exception as e:
            logger.error("DatabaseManager", f"Failed to add tenant {tenant_id}: {str(e)}")
            return False
    
    def get_tenant(self, tenant_id: str) -> Optional[Dict]:
        """Get tenant from database"""
        logger.debug("DatabaseManager", f"Retrieving tenant: {tenant_id}")
        try:
            cursor = self.execute_query(
                'SELECT * FROM tenants WHERE tenant_id = ?',
                (tenant_id,)
            )
            row = cursor.fetchone()
            if row:
                logger.debug("DatabaseManager", f"Tenant found: {tenant_id}")
                return dict(row)
            logger.warning("DatabaseManager", f"Tenant not found: {tenant_id}")
            return None
        except Exception as e:
            logger.error("DatabaseManager", f"Failed to get tenant {tenant_id}: {str(e)}")
            return None
    
    def get_all_tenants(self) -> List[Dict]:
        """Get all tenants from database"""
        logger.debug("DatabaseManager", "Retrieving all tenants")
        try:
            cursor = self.execute_query('SELECT * FROM tenants ORDER BY name')
            rows = cursor.fetchall()
            logger.info("DatabaseManager", f"Retrieved {len(rows)} tenants")
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error("DatabaseManager", f"Failed to get all tenants: {str(e)}")
            return []
    
    def update_tenant(self, tenant_id: str, **kwargs) -> bool:
        """Update tenant in database"""
        logger.debug("DatabaseManager", f"Updating tenant: {tenant_id} with {len(kwargs)} fields")
        try:
            # Build dynamic update query
            fields = []
            values = []
            for key, value in kwargs.items():
                fields.append(f"{key} = ?")
                values.append(value)
            
            fields.append("updated_at = CURRENT_TIMESTAMP")
            
            query = f"UPDATE tenants SET {', '.join(fields)} WHERE tenant_id = ?"
            values.append(tenant_id)
            
            cursor = self.execute_query(query, tuple(values))
            self.commit()
            logger.info("DatabaseManager", f"Tenant updated successfully: {tenant_id}")
            return True
        except Exception as e:
            logger.error("DatabaseManager", f"Failed to update tenant {tenant_id}: {str(e)}")
            return False
    
    def delete_tenant(self, tenant_id: str) -> bool:
        """Delete tenant and all related data from database"""
        logger.debug("DatabaseManager", f"Deleting tenant: {tenant_id}")
        try:
            self.execute_query('DELETE FROM payment_history WHERE tenant_id = ?', (tenant_id,))
            self.execute_query('DELETE FROM monthly_overrides WHERE tenant_id = ?', (tenant_id,))
            self.execute_query('DELETE FROM tenants WHERE tenant_id = ?', (tenant_id,))
            self.commit()
            logger.info("DatabaseManager", f"Tenant deleted successfully: {tenant_id}")
            return True
        except Exception as e:
            logger.error("DatabaseManager", f"Failed to delete tenant {tenant_id}: {str(e)}")
            return False
    
    # ==================== PAYMENT OPERATIONS ====================
    
    def add_payment(self, payment_id: str, tenant_id: str, **kwargs) -> bool:
        """Add a payment to the database"""
        logger.debug("DatabaseManager", f"Adding payment: {payment_id} for tenant: {tenant_id}")
        try:
            query = '''
                INSERT INTO payment_history (
                    payment_id, tenant_id, date_received, amount, payment_type,
                    payment_month, status, details, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            
            params = (
                payment_id,
                tenant_id,
                kwargs.get('date_received', ''),
                kwargs.get('amount', 0.0),
                kwargs.get('payment_type', ''),
                kwargs.get('payment_month', ''),
                kwargs.get('status', ''),
                kwargs.get('details', ''),
                kwargs.get('notes', '')
            )
            
            cursor = self.execute_query(query, params)
            self.commit()
            logger.info("DatabaseManager", f"Payment added successfully: {payment_id}")
            return True
        except Exception as e:
            logger.error("DatabaseManager", f"Failed to add payment {payment_id}: {str(e)}")
            return False
    
    def get_tenant_payments(self, tenant_id: str) -> List[Dict]:
        """Get all payments for a tenant"""
        logger.debug("DatabaseManager", f"Retrieving payments for tenant: {tenant_id}")
        try:
            cursor = self.execute_query(
                'SELECT * FROM payment_history WHERE tenant_id = ? ORDER BY date_received DESC',
                (tenant_id,)
            )
            rows = cursor.fetchall()
            logger.info("DatabaseManager", f"Retrieved {len(rows)} payments for tenant {tenant_id}")
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error("DatabaseManager", f"Failed to get payments for tenant {tenant_id}: {str(e)}")
            return []
    
    def update_payment(self, payment_id: str, **kwargs) -> bool:
        """Update a payment in the database"""
        logger.debug("DatabaseManager", f"Updating payment: {payment_id} with {len(kwargs)} fields")
        try:
            fields = []
            values = []
            for key, value in kwargs.items():
                fields.append(f"{key} = ?")
                values.append(value)
            
            values.append(payment_id)
            query = f"UPDATE payment_history SET {', '.join(fields)} WHERE payment_id = ?"
            
            cursor = self.execute_query(query, tuple(values))
            self.commit()
            logger.info("DatabaseManager", f"Payment updated successfully: {payment_id}")
            return True
        except Exception as e:
            logger.error("DatabaseManager", f"Failed to update payment {payment_id}: {str(e)}")
            return False
    
    def delete_payment(self, payment_id: str) -> bool:
        """Delete a payment from the database"""
        logger.debug("DatabaseManager", f"Deleting payment: {payment_id}")
        try:
            self.execute_query('DELETE FROM payment_history WHERE payment_id = ?', (payment_id,))
            self.commit()
            logger.info("DatabaseManager", f"Payment deleted successfully: {payment_id}")
            return True
        except Exception as e:
            logger.error("DatabaseManager", f"Failed to delete payment {payment_id}: {str(e)}")
            return False
    
    # ==================== DISPUTE OPERATIONS ====================
    
    def add_dispute(self, dispute_id: str, tenant_id: str, **kwargs) -> bool:
        """Add a new dispute to the database"""
        logger.debug("DatabaseManager", f"Adding dispute: {dispute_id} for tenant: {tenant_id}")
        try:
            query = '''
                INSERT INTO disputes 
                (dispute_id, tenant_id, dispute_type, description, amount, reference_month, 
                 reference_payment_id, created_by, created_at, updated_at, status, admin_notes, evidence_notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            
            params = (
                dispute_id,
                tenant_id,
                kwargs.get('dispute_type', ''),
                kwargs.get('description', ''),
                kwargs.get('amount'),
                kwargs.get('reference_month'),
                kwargs.get('reference_payment_id'),
                kwargs.get('created_by', 'tenant_web_ui'),
                kwargs.get('created_at', datetime.now().isoformat()),
                kwargs.get('updated_at', datetime.now().isoformat()),
                kwargs.get('status', 'open'),
                kwargs.get('admin_notes'),
                kwargs.get('evidence_notes')
            )
            
            cursor = self.execute_query(query, params)
            self.commit()
            logger.info("DatabaseManager", f"Dispute added successfully: {dispute_id}")
            return True
        except Exception as e:
            logger.error("DatabaseManager", f"Failed to add dispute {dispute_id}: {str(e)}")
            return False
    
    def get_dispute(self, dispute_id: str) -> Optional[Dict]:
        """Get a specific dispute by ID"""
        logger.debug("DatabaseManager", f"Retrieving dispute: {dispute_id}")
        try:
            cursor = self.execute_query(
                'SELECT * FROM disputes WHERE dispute_id = ?',
                (dispute_id,)
            )
            row = cursor.fetchone()
            if row:
                logger.debug("DatabaseManager", f"Found dispute: {dispute_id}")
                return dict(row)
            else:
                logger.debug("DatabaseManager", f"Dispute not found: {dispute_id}")
                return None
        except Exception as e:
            logger.error("DatabaseManager", f"Failed to get dispute {dispute_id}: {str(e)}")
            return None
    
    def get_tenant_disputes(self, tenant_id: str) -> List[Dict]:
        """Get all disputes for a tenant"""
        logger.debug("DatabaseManager", f"Retrieving disputes for tenant: {tenant_id}")
        try:
            cursor = self.execute_query(
                'SELECT * FROM disputes WHERE tenant_id = ? ORDER BY created_at DESC',
                (tenant_id,)
            )
            rows = cursor.fetchall()
            logger.info("DatabaseManager", f"Retrieved {len(rows)} disputes for tenant {tenant_id}")
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error("DatabaseManager", f"Failed to get disputes for tenant {tenant_id}: {str(e)}")
            return []
    
    def get_all_disputes(self) -> List[Dict]:
        """Get all disputes across all tenants"""
        logger.debug("DatabaseManager", "Retrieving all disputes")
        try:
            cursor = self.execute_query(
                'SELECT * FROM disputes ORDER BY created_at DESC'
            )
            rows = cursor.fetchall()
            logger.info("DatabaseManager", f"Retrieved {len(rows)} total disputes")
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error("DatabaseManager", f"Failed to get all disputes: {str(e)}")
            return []
    
    def update_dispute(self, dispute_id: str, **kwargs) -> bool:
        """Update a dispute in the database"""
        logger.debug("DatabaseManager", f"Updating dispute: {dispute_id}")
        try:
            # Always update the updated_at timestamp
            kwargs['updated_at'] = datetime.now().isoformat()
            
            # If status is being changed to resolved, set resolved_at
            if kwargs.get('status') == 'resolved' and 'resolved_at' not in kwargs:
                kwargs['resolved_at'] = datetime.now().isoformat()
            
            fields = []
            values = []
            for key, value in kwargs.items():
                fields.append(f"{key} = ?")
                values.append(value)
            
            values.append(dispute_id)
            query = f"UPDATE disputes SET {', '.join(fields)} WHERE dispute_id = ?"
            
            cursor = self.execute_query(query, tuple(values))
            self.commit()
            logger.info("DatabaseManager", f"Dispute updated successfully: {dispute_id}")
            return True
        except Exception as e:
            logger.error("DatabaseManager", f"Failed to update dispute {dispute_id}: {str(e)}")
            return False
    
    def delete_dispute(self, dispute_id: str) -> bool:
        """Delete a dispute from the database"""
        logger.debug("DatabaseManager", f"Deleting dispute: {dispute_id}")
        try:
            self.execute_query('DELETE FROM disputes WHERE dispute_id = ?', (dispute_id,))
            self.commit()
            logger.info("DatabaseManager", f"Dispute deleted successfully: {dispute_id}")
            return True
        except Exception as e:
            logger.error("DatabaseManager", f"Failed to delete dispute {dispute_id}: {str(e)}")
            return False
    
    def get_disputes_for_payment(self, payment_id: str) -> List[Dict]:
        """Get all disputes related to a specific payment"""
        logger.debug("DatabaseManager", f"Retrieving disputes for payment: {payment_id}")
        try:
            cursor = self.execute_query(
                'SELECT * FROM disputes WHERE reference_payment_id = ? ORDER BY created_at DESC',
                (payment_id,)
            )
            rows = cursor.fetchall()
            logger.info("DatabaseManager", f"Retrieved {len(rows)} disputes for payment {payment_id}")
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error("DatabaseManager", f"Failed to get disputes for payment {payment_id}: {str(e)}")
            return []
    
    def get_dispute_stats(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Get dispute statistics"""
        logger.debug("DatabaseManager", f"Getting dispute stats for tenant: {tenant_id}")
        try:
            stats = {
                'total': 0,
                'by_status': {},
                'by_type': {},
                'total_amount': 0.0
            }
            
            if tenant_id:
                query = 'SELECT * FROM disputes WHERE tenant_id = ?'
                cursor = self.execute_query(query, (tenant_id,))
            else:
                query = 'SELECT * FROM disputes'
                cursor = self.execute_query(query)
            
            rows = cursor.fetchall()
            
            for row in rows:
                row_dict = dict(row)
                stats['total'] += 1
                
                # Count by status
                status = row_dict.get('status', 'open')
                stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
                
                # Count by type
                d_type = row_dict.get('dispute_type', 'other')
                stats['by_type'][d_type] = stats['by_type'].get(d_type, 0) + 1
                
                # Sum amounts
                amount = row_dict.get('amount')
                if amount:
                    stats['total_amount'] += amount
            
            logger.debug("DatabaseManager", f"Dispute stats: {stats}")
            return stats
        except Exception as e:
            logger.error("DatabaseManager", f"Failed to get dispute stats: {str(e)}")
            return {'total': 0, 'by_status': {}, 'by_type': {}, 'total_amount': 0.0}
    
    # ==================== SYNC AND VALIDATION ====================

    
    def sync_tenant_from_json(self, tenant_json: Dict) -> Dict[str, Any]:
        """
        Sync tenant from JSON to database including overrides
        Returns a dict with sync status and any mismatches found
        """
        logger.debug("DatabaseManager", "Starting tenant sync from JSON")
        tenant_id = tenant_json.get('tenant_id')
        if not tenant_id:
            logger.error("DatabaseManager", "No tenant_id provided in JSON")
            return {'success': False, 'error': 'No tenant_id provided'}
        
        mismatches = []
        
        # Get existing DB record
        db_tenant = self.get_tenant(tenant_id)
        
        # Extract rental period
        rental_period = tenant_json.get('rental_period', {})
        if isinstance(rental_period, dict):
            period_start = rental_period.get('start_date')
            period_end = rental_period.get('end_date')
            lease_type = rental_period.get('lease_type')
        elif isinstance(rental_period, (list, tuple)) and len(rental_period) >= 2:
            period_start = rental_period[0]
            period_end = rental_period[1]
            lease_type = None
        else:
            period_start = None
            period_end = None
            lease_type = None
        
        tenant_data = {
            'name': tenant_json.get('name', ''),
            'contact_info': str(tenant_json.get('contact_info', '')),
            'account_status': (tenant_json.get('account_status', 'active') or 'active').lower(),
            'rent_amount': float(tenant_json.get('rent_amount', 0.0)),
            'deposit_amount': float(tenant_json.get('deposit_amount', 0.0)),
            'rent_due_date': int(tenant_json.get('rent_due_date', 1)),
            'delinquency_balance': float(tenant_json.get('delinquency_balance', 0.0)),
            'overpayment_credit': float(tenant_json.get('overpayment_credit', 0.0)),
            'service_credit': float(getattr(tenant_json, 'service_credit', 0.0)),
            'rental_period_start': period_start,
            'rental_period_end': period_end,
            'lease_type': lease_type,
            'notes': tenant_json.get('notes', ''),
            'user_ids': json.dumps(tenant_json.get('user_ids', [])) if isinstance(tenant_json.get('user_ids'), list) else '[]',
            'last_synced_at': datetime.now().isoformat(),
            'last_modified': tenant_json.get('last_modified', datetime.now().isoformat())
        }
        
        logger.debug("DatabaseManager", f"Syncing tenant {tenant_id}, checking for existing record")
        # Check for mismatches if record exists
        if db_tenant:
            for key, json_value in tenant_data.items():
                if key == 'last_synced_at':
                    continue
                db_value = db_tenant.get(key)
                
                # Handle type conversions for comparison
                try:
                    if isinstance(json_value, (int, float)) and db_value is not None:
                        if float(json_value) != float(db_value):
                            mismatches.append({
                                'field': key,
                                'json_value': json_value,
                                'db_value': db_value
                            })
                            logger.debug("DatabaseManager", f"Mismatch found in {key}: JSON={json_value}, DB={db_value}")
                    elif json_value != db_value:
                        mismatches.append({
                            'field': key,
                            'json_value': json_value,
                            'db_value': db_value
                        })
                        logger.debug("DatabaseManager", f"Mismatch found in {key}: JSON={json_value}, DB={db_value}")
                except Exception as e:
                    mismatches.append({
                        'field': key,
                        'error': str(e),
                        'json_value': json_value,
                        'db_value': db_value
                    })
                    logger.warning("DatabaseManager", f"Error comparing {key}: {str(e)}")
            
            # Update existing record
            logger.debug("DatabaseManager", f"Updating existing tenant record: {tenant_id}")
            self.update_tenant(tenant_id, **tenant_data)
            
            # Verify update by reloading from database
            updated_db_tenant = self.get_tenant(tenant_id)
            if updated_db_tenant:
                mismatches = []  # Clear mismatches, will recheck after update
                for key, json_value in tenant_data.items():
                    if key == 'last_synced_at':
                        continue
                    db_value = updated_db_tenant.get(key)
                    
                    try:
                        if isinstance(json_value, (int, float)) and db_value is not None:
                            if float(json_value) != float(db_value):
                                mismatches.append({
                                    'field': key,
                                    'json_value': json_value,
                                    'db_value': db_value
                                })
                                logger.debug("DatabaseManager", f"Post-update mismatch in {key}: JSON={json_value}, DB={db_value}")
                        elif json_value != db_value:
                            mismatches.append({
                                'field': key,
                                'json_value': json_value,
                                'db_value': db_value
                            })
                            logger.debug("DatabaseManager", f"Post-update mismatch in {key}: JSON={json_value}, DB={db_value}")
                    except Exception as e:
                        logger.warning("DatabaseManager", f"Error comparing {key} after update: {str(e)}")
        else:
            # Create new record
            logger.debug("DatabaseManager", f"Creating new tenant record: {tenant_id}")
            self.add_tenant(tenant_id, **tenant_data)
        
        # Sync monthly overrides/exceptions
        monthly_exceptions = tenant_json.get('monthly_exceptions', {})
        if monthly_exceptions and isinstance(monthly_exceptions, dict):
            logger.debug("DatabaseManager", f"Syncing {len(monthly_exceptions)} monthly overrides for tenant {tenant_id}")
            for month_str, override_amount in monthly_exceptions.items():
                try:
                    # Parse month string (format: "YYYY-MM" or "2024-01")
                    if isinstance(month_str, str) and '-' in month_str:
                        year_str, month_str = month_str.split('-')
                        year = int(year_str)
                        month = month_str
                    else:
                        # Fallback for other formats
                        continue
                    
                    override_id = f"override_{tenant_id}_{year}_{month}"
                    self.sync_monthly_override(override_id, tenant_id, month, year, float(override_amount))
                except Exception as e:
                    logger.warning("DatabaseManager", f"Failed to sync monthly override for {tenant_id} {month_str}: {e}")
        
        # Log mismatches
        if mismatches:
            logger.warning("DatabaseManager", f"Found {len(mismatches)} mismatches for tenant {tenant_id}")
            self.log_sync_mismatch(
                entity_type='tenant',
                entity_id=tenant_id,
                source='json',
                mismatches=mismatches,
                json_data=tenant_data,
                db_data=db_tenant
            )
        
        logger.info("DatabaseManager", f"Tenant sync complete for {tenant_id}, mismatches: {len(mismatches)}")
        
        # Log sync operation to sync_log table
        try:
            sync_operation = {
                'tenant_id': tenant_id,
                'tenant_name': tenant_data.get('name', ''),
                'deposit_amount': tenant_data.get('deposit_amount', 0.0),
                'last_synced_at': tenant_data.get('last_synced_at', ''),
                'action': 'update' if db_tenant else 'create'
            }
            self.log_sync_operation('tenant', tenant_id, 'json', sync_operation, success=True)
        except Exception as e:
            logger.warning("DatabaseManager", f"Failed to log sync operation for tenant {tenant_id}: {e}")
        
        return {
            'success': True,
            'tenant_id': tenant_id,
            'is_new': db_tenant is None,
            'mismatches': mismatches,
            'mismatch_count': len(mismatches)
        }
    
    def sync_payment_from_json(self, payment_json: Dict, payment_index: int = 0) -> Dict[str, Any]:
        """
        Sync payment from JSON to database
        Returns a dict with sync status and any mismatches found
        """
        logger.debug("DatabaseManager", f"Syncing payment (index {payment_index}) from JSON")
        # Generate or get payment ID
        if 'payment_id' in payment_json:
            payment_id = payment_json.get('payment_id')
            logger.debug("DatabaseManager", f"Using existing payment_id: {payment_id}")
        else:
            # Create a unique ID using tenant_id, date, amount, and index
            tenant_id = payment_json.get('tenant_id', 'unknown')
            date_str = str(payment_json.get('date_received', '')).replace('-', '').replace('/', '')
            amount_str = str(payment_json.get('amount', 0.0)).replace('.', '')
            # Use UUID to ensure uniqueness
            payment_id = f"payment_{tenant_id}_{date_str}_{amount_str}_{payment_index}_{uuid.uuid4().hex[:8]}"
            logger.debug("DatabaseManager", f"Generated payment_id: {payment_id}")
        
        tenant_id = payment_json.get('tenant_id')
        
        if not tenant_id:
            logger.error("DatabaseManager", "No tenant_id provided in payment JSON")
            return {'success': False, 'error': 'No tenant_id provided'}
        
        # Map payment record fields to database schema
        # Payment records use 'date' and 'type', but DB uses 'date_received' and 'payment_type'
        payment_data = {
            'date_received': str(payment_json.get('date_received') or payment_json.get('date', '')),
            'amount': float(payment_json.get('amount', 0.0)),
            'payment_type': str(payment_json.get('payment_type') or payment_json.get('type', '')),
            'payment_month': str(payment_json.get('payment_month', '')),
            'status': str(payment_json.get('status', '')),
            'details': str(payment_json.get('details', '')),
            'notes': str(payment_json.get('notes', ''))
        }
        
        try:
            self.add_payment(payment_id, tenant_id, **payment_data)
            logger.info("DatabaseManager", f"Payment synced successfully: {payment_id} for tenant {tenant_id}")
            # Log sync operation
            try:
                self.log_sync_operation('payment', payment_id, 'json', payment_data, success=True)
            except Exception as e:
                logger.warning("DatabaseManager", f"Failed to log payment sync operation: {e}")
            return {
                'success': True,
                'payment_id': payment_id,
                'tenant_id': tenant_id
            }
        except sqlite3.IntegrityError as e:
            # Payment already exists - try to update instead
            logger.debug("DatabaseManager", f"Payment already exists, attempting update: {payment_id}")
            if 'UNIQUE constraint failed' in str(e):
                try:
                    self.update_payment(payment_id, **payment_data)
                    logger.info("DatabaseManager", f"Payment updated successfully: {payment_id}")
                    # Log sync operation
                    try:
                        self.log_sync_operation('payment', payment_id, 'json', payment_data, success=True, action='update')
                    except Exception as e:
                        logger.warning("DatabaseManager", f"Failed to log payment update operation: {e}")
                    return {
                        'success': True,
                        'payment_id': payment_id,
                        'tenant_id': tenant_id,
                        'action': 'updated'
                    }
                except Exception as update_error:
                    logger.error("DatabaseManager", f"Failed to update payment {payment_id}: {str(update_error)}")
                    return {
                        'success': False,
                        'error': f"Failed to update: {update_error}",
                        'payment_id': payment_id
                    }
            else:
                logger.error("DatabaseManager", f"Integrity error for payment {payment_id}: {str(e)}")
                return {
                    'success': False,
                    'error': str(e),
                    'payment_id': payment_id
                }
        except Exception as e:
            logger.error("DatabaseManager", f"Failed to sync payment {payment_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'payment_id': payment_id
            }
    
    def log_sync_operation(self, entity_type: str, entity_id: str, source: str, operation_data: Dict, success: bool = True, action: str = 'create') -> bool:
        """
        Log a successful sync operation for audit trail
        
        Args:
            entity_type: Type of entity (tenant, payment, override)
            entity_id: ID of the entity
            source: Source of sync (json, api, etc.)
            operation_data: Data that was synced
            success: Whether operation was successful
            action: Action performed (create, update)
            
        Returns:
            True if logged successfully
        """
        logger.debug("DatabaseManager", f"Logging sync operation: {entity_type} {entity_id} ({action})")
        try:
            query = '''
                INSERT INTO sync_log (entity_type, entity_id, source, mismatch_type, json_data, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            '''
            
            mismatch_type = f"{action}_{entity_type}"
            notes = f"Sync {action}: {entity_type} {entity_id} from {source}"
            
            params = (
                entity_type,
                entity_id,
                source,
                mismatch_type,
                json.dumps(operation_data),
                notes
            )
            
            self.execute_query(query, params)
            self.commit()
            logger.info("DatabaseManager", f"Sync operation logged: {entity_type} {entity_id}")
            return True
        except Exception as e:
            logger.error("DatabaseManager", f"Failed to log sync operation: {str(e)}")
            return False
    
    def log_sync_mismatch(self, entity_type: str, entity_id: str, source: str, 
                         mismatches: List[Dict], json_data: Dict, db_data: Optional[Dict]):
        """Log data mismatches for review"""
        logger.debug("DatabaseManager", f"Logging sync mismatch for {entity_type} {entity_id}, {len(mismatches)} fields")
        try:
            query = '''
                INSERT INTO sync_log (entity_type, entity_id, source, mismatch_type, json_data, db_data, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            '''
            
            mismatch_types = [m.get('field', 'unknown') for m in mismatches]
            
            params = (
                entity_type,
                entity_id,
                source,
                ','.join(mismatch_types),
                json.dumps(json_data),
                json.dumps(db_data) if db_data else None,
                json.dumps(mismatches)
            )
            
            self.execute_query(query, params)
            self.commit()
            logger.info("DatabaseManager", f"Sync mismatch logged for {entity_type} {entity_id}")
        except Exception as e:
            logger.error("DatabaseManager", f"Failed to log sync mismatch: {str(e)}")
    
    def sync_monthly_override(self, override_id: str, tenant_id: str, month: str, year: int, override_amount: float) -> bool:
        """
        Sync a monthly override (from monthly_exceptions) to the database
        
        Args:
            override_id: Unique override ID
            tenant_id: Tenant ID
            month: Month (MM format)
            year: Year (YYYY format)
            override_amount: Override rent amount
            
        Returns:
            True if successful
        """
        logger.debug("DatabaseManager", f"Syncing monthly override {override_id} for {tenant_id}: {year}-{month} = {override_amount}")
        try:
            # Check if override already exists
            cursor = self.execute_query(
                'SELECT override_id FROM monthly_overrides WHERE override_id = ?',
                (override_id,)
            )
            existing = cursor.fetchone()
            
            if existing:
                # Update existing override
                query = '''
                    UPDATE monthly_overrides 
                    SET override_amount = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE override_id = ?
                '''
                self.execute_query(query, (override_amount, override_id))
                logger.debug("DatabaseManager", f"Updated monthly override {override_id}")
                action = 'update'
            else:
                # Insert new override
                query = '''
                    INSERT INTO monthly_overrides (override_id, tenant_id, month, year, override_amount)
                    VALUES (?, ?, ?, ?, ?)
                '''
                self.execute_query(query, (override_id, tenant_id, month, year, override_amount))
                logger.debug("DatabaseManager", f"Created monthly override {override_id}")
                action = 'create'
            
            self.commit()
            logger.info("DatabaseManager", f"Monthly override synced successfully: {override_id}")
            
            # Log sync operation
            try:
                override_data = {
                    'override_id': override_id,
                    'tenant_id': tenant_id,
                    'month': month,
                    'year': year,
                    'override_amount': override_amount
                }
                self.log_sync_operation('monthly_override', override_id, 'json', override_data, success=True, action=action)
            except Exception as e:
                logger.warning("DatabaseManager", f"Failed to log override sync operation: {e}")
            
            return True
        except Exception as e:
            logger.error("DatabaseManager", f"Failed to sync monthly override {override_id}: {str(e)}")
            return False
    
    def get_sync_logs(self, limit: int = 100) -> List[Dict]:
        """Get recent sync logs"""
        logger.debug("DatabaseManager", f"Retrieving sync logs (limit: {limit})")
        try:
            cursor = self.execute_query(
                'SELECT * FROM sync_log ORDER BY timestamp DESC LIMIT ?',
                (limit,)
            )
            rows = cursor.fetchall()
            logger.info("DatabaseManager", f"Retrieved {len(rows)} sync logs")
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error("DatabaseManager", f"Failed to get sync logs: {str(e)}")
            return []
    
    def _load_json_file(self, filename: str) -> Optional[Dict]:
        """Load JSON file from data directory"""
        try:
            # Try to find the file in data/ directory
            data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
            filepath = os.path.join(data_dir, filename)
            
            # If not found, try alternate paths
            if not os.path.exists(filepath):
                # Try from current working directory
                filepath = os.path.join('data', filename)
            
            if not os.path.exists(filepath):
                logger.debug("DatabaseManager", f"JSON file not found: {filename}")
                return None
            
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning("DatabaseManager", f"Failed to load JSON file {filename}: {str(e)}")
            return None
    
    def get_mismatch_summary(self) -> Dict[str, Any]:
        """Get summary of current mismatches by comparing JSON vs Database"""
        logger.debug("DatabaseManager", "Retrieving current mismatch summary")
        try:
            summary = {
                'tenant_mismatches': 0,
                'payment_mismatches': 0,
                'details': []
            }
            
            # Load JSON data
            try:
                tenant_manager = TenantManager()
                json_tenants = tenant_manager.tenants  # Dictionary of tenant_id -> Tenant objects
            except Exception as e:
                logger.warning("DatabaseManager", f"Failed to load tenants: {str(e)}")
                json_tenants = {}
            
            # Load JSON payments
            try:
                json_payments_data = self._load_json_file('data/payment_data.json')
                json_payments = json_payments_data if isinstance(json_payments_data, dict) else {}
            except Exception as e:
                logger.warning("DatabaseManager", f"Failed to load payments: {str(e)}")
                json_payments = {}
            
            # Check tenant mismatches
            db_cursor = self.execute_query('SELECT tenant_id FROM tenants')
            db_tenant_ids = {row[0] for row in db_cursor.fetchall()}
            json_tenant_ids = set(json_tenants.keys()) if json_tenants else set()
            
            # Tenants in JSON but not in DB
            missing_in_db = json_tenant_ids - db_tenant_ids
            summary['tenant_mismatches'] += len(missing_in_db)
            if missing_in_db:
                summary['details'].append(f"Tenants in JSON but not in DB: {missing_in_db}")
            
            # Tenants in DB but not in JSON
            extra_in_db = db_tenant_ids - json_tenant_ids
            summary['tenant_mismatches'] += len(extra_in_db)
            if extra_in_db:
                summary['details'].append(f"Tenants in DB but not in JSON: {extra_in_db}")
            
            # Check payment mismatches
            try:
                db_cursor = self.execute_query('SELECT tenant_id, COUNT(*) as count FROM payments GROUP BY tenant_id')
                db_payment_counts = {row[0]: row[1] for row in db_cursor.fetchall()}
                
                # Safely iterate over payments - handle different data structures
                if json_payments and isinstance(json_payments, dict):
                    for tenant_id, payments_data in json_payments.items():
                        # Handle case where payments_data might be a dict of payments or just a number
                        if isinstance(payments_data, dict):
                            json_count = len(payments_data)
                        elif isinstance(payments_data, (list, tuple)):
                            json_count = len(payments_data)
                        else:
                            # Skip non-dict/list values
                            logger.debug("DatabaseManager", f"Skipping non-dict payment data for {tenant_id}: {type(payments_data)}")
                            continue
                        
                        db_count = db_payment_counts.get(tenant_id, 0)
                        
                        if json_count != db_count:
                            summary['payment_mismatches'] += abs(json_count - db_count)
                            summary['details'].append(f"Tenant {tenant_id}: JSON has {json_count} payments, DB has {db_count}")
            except Exception as e:
                logger.warning("DatabaseManager", f"Error checking payment mismatches: {str(e)}")
            
            logger.info("DatabaseManager", f"Mismatch summary: {summary['tenant_mismatches']} tenant, {summary['payment_mismatches']} payment")
            return summary
        except Exception as e:
            logger.error("DatabaseManager", f"Failed to get mismatch summary: {str(e)}")
            return {'tenant_mismatches': 0, 'payment_mismatches': 0, 'details': [f"Error: {str(e)}"]}
    
    def sync_all_tenants(self, tenants_dict) -> bool:
        """
        Sync all tenants and their associated data to the database
        This is a wrapper that syncs all tenants from the tenant manager
        
        Args:
            tenants_dict: Dictionary of tenant_id -> Tenant object
            
        Returns:
            True if all syncs completed (even with some failures)
        """
        logger.info("DatabaseManager", f"Starting sync of {len(tenants_dict)} tenants to database")
        
        try:
            sync_count = 0
            error_count = 0
            
            for tenant_id, tenant in tenants_dict.items():
                try:
                    # Prepare tenant data from tenant object
                    tenant_data = {
                        'name': getattr(tenant, 'name', ''),
                        'contact_info': str(getattr(tenant, 'contact_info', '')),
                        'account_status': (getattr(tenant, 'account_status', 'active') or 'active').lower(),
                        'rent_amount': float(getattr(tenant, 'rent_amount', 0.0)),
                        'deposit_amount': float(getattr(tenant, 'deposit_amount', 0.0)),
                        'rent_due_date': int(getattr(tenant, 'rent_due_date', 1)),
                        'delinquency_balance': float(getattr(tenant, 'delinquency_balance', 0.0)),
                        'overpayment_credit': float(getattr(tenant, 'overpayment_credit', 0.0)),
                        'service_credit': float(getattr(tenant, 'service_credit', 0.0)),
                        'notes': str(getattr(tenant, 'notes', '')),
                        'user_ids': json.dumps(getattr(tenant, 'user_ids', [])) if isinstance(getattr(tenant, 'user_ids', []), list) else '[]',
                        'last_synced_at': datetime.now().isoformat()
                    }
                    
                    # Handle rental period
                    rental_period = getattr(tenant, 'rental_period', None)
                    if rental_period:
                        if isinstance(rental_period, dict):
                            tenant_data['rental_period_start'] = rental_period.get('start_date')
                            tenant_data['rental_period_end'] = rental_period.get('end_date')
                            tenant_data['lease_type'] = rental_period.get('lease_type')
                        elif isinstance(rental_period, (list, tuple)) and len(rental_period) >= 2:
                            tenant_data['rental_period_start'] = rental_period[0]
                            tenant_data['rental_period_end'] = rental_period[1]
                    
                    # Check if tenant exists
                    existing_tenant = self.get_tenant(tenant_id)
                    if existing_tenant:
                        # Update existing tenant
                        self.update_tenant(tenant_id, **tenant_data)
                        logger.debug("DatabaseManager", f"Updated tenant {tenant_id}: {tenant_data.get('name')}")
                    else:
                        # Add new tenant
                        self.add_tenant(tenant_id, **tenant_data)
                        logger.debug("DatabaseManager", f"Added new tenant {tenant_id}: {tenant_data.get('name')}")
                    
                    sync_count += 1
                    
                except Exception as e:
                    error_count += 1
                    logger.error("DatabaseManager", f"Failed to sync tenant {tenant_id}: {str(e)}")
                    continue
            
            logger.info("DatabaseManager", f"Tenant sync complete: {sync_count} synced, {error_count} failed")
            return True
            
        except Exception as e:
            logger.error("DatabaseManager", f"Failed to sync all tenants: {str(e)}")
            return False
