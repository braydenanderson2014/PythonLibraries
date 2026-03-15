from datetime import date, timedelta, datetime
import os, sys
from typing import Dict, List, Any, Optional, Callable, Tuple
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ui')))

from tenant import TenantManager
try:
    from account import AccountManager
except ImportError:
    AccountManager = None
from bank import Bank
from action_queue import ActionQueue
from assets.Logger import Logger
logger = Logger()
class RentTracker:
    def check_and_update_delinquency(self, target_tenant_id=None):
        import logging
        today = date.today()
        try:
            tenants_to_update = [self.tenant_manager.get_tenant(target_tenant_id)] if target_tenant_id else self.tenant_manager.list_tenants()
            
            for tenant in tenants_to_update:
                if not tenant:
                    continue
                    
                logger.debug("Rent Tracker",f"[DEBUG] Recalculating delinquency for {tenant.name} (ID: {tenant.tenant_id})")
                
                # Check if lease has expired and update status
                self.check_and_update_lease_status(tenant)
                
                # Ensure months_to_charge is populated based on rental period
                self.ensure_months_to_charge(tenant)
                
                # Get due day (default to 1 if not set)
                try:
                    due_day = int(tenant.rent_due_date) if tenant.rent_due_date else 1
                except Exception:
                    due_day = 1
                    
                # Reset delinquency data for full recalculation
                tenant.delinquency_balance = 0.0
                tenant.delinquent_months = []
                # Don't reset overpayment_credit yet - we'll calculate it based on payments
                total_overpayment = 0.0
                total_credit_used = 0.0
                
                # Clear monthly status for months outside the rental period
                if hasattr(tenant, 'monthly_status'):
                    # Only keep monthly status for months within the current rental period
                    new_monthly_status = {}
                    for year, month in tenant.months_to_charge:
                        month_key = f"{year}-{month:02d}"
                        if month_key in tenant.monthly_status:
                            new_monthly_status[month_key] = tenant.monthly_status[month_key]
                    tenant.monthly_status = new_monthly_status
                else:
                    tenant.monthly_status = {}
                
                logger.debug("Rent Tracker",f"[DEBUG] {tenant.name} months to charge: {tenant.months_to_charge}")
                
                # Check all months in months_to_charge up to today
                for year, month in tenant.months_to_charge:
                    # Ensure year and month are integers
                    try:
                        year = int(year)
                        month = int(month)
                    except (ValueError, TypeError):
                        logger.warning("Rent Tracker",f"[WARNING] Invalid year/month format: {year}, {month}")
                        continue
                        
                    due_date = date(year, month, due_day)
                    month_key = f"{year}-{month:02d}"
                    
                    # Calculate total paid for this month
                    total_paid_this_month = 0.0
                    credit_usage_this_month = 0.0
                    if hasattr(tenant, 'payment_history'):
                        for payment in tenant.payment_history:
                            if payment['year'] == year and payment['month'] == month:
                                if payment.get('is_credit_usage', False):
                                    # Track overpayment credit usage separately (not service credits)
                                    # Service credits are treated as regular payments
                                    credit_usage_this_month += payment['amount']
                                    total_credit_used += payment['amount']
                                else:
                                    # Count all actual payments (cash, zelle, service credits, etc.)
                                    total_paid_this_month += payment['amount']
                    
                    # Adjust total for credit usage - if more credit was used than new money available,
                    # we need to account for overpayment from previous months
                    adjusted_total_for_this_month = total_paid_this_month - credit_usage_this_month
                    
                    expected_rent = self.get_effective_rent(tenant, year, month)
                    # For unpaid amount, account for both new money and credit usage
                    total_applied_to_month = total_paid_this_month + credit_usage_this_month
                    unpaid_amount = expected_rent - total_applied_to_month
                    
                    if today > due_date:
                        # Past due date
                        if unpaid_amount > 0:
                            tenant.delinquency_balance += unpaid_amount
                            tenant.monthly_status[month_key] = 'Delinquent'
                            if (year, month) not in tenant.delinquent_months:
                                tenant.delinquent_months.append((year, month))
                        elif total_applied_to_month >= expected_rent:
                            # Overpayment should be calculated against the remaining amount
                            # due after any applied overpayment credit for this month.
                            remaining_due_after_credit = max(0.0, expected_rent - credit_usage_this_month)
                            overpayment = max(0.0, total_paid_this_month - remaining_due_after_credit)
                            if overpayment > 0:
                                total_overpayment += overpayment
                                tenant.monthly_status[month_key] = 'Overpayment'
                            else:
                                tenant.monthly_status[month_key] = 'Paid in Full'
                        else:
                            tenant.monthly_status[month_key] = 'Partial Payment'
                    else:
                        # Future month
                        if total_applied_to_month >= expected_rent:
                            tenant.monthly_status[month_key] = 'Paid in Full'
                        elif total_applied_to_month > 0:
                            tenant.monthly_status[month_key] = 'Partial Payment'
                        else:
                            tenant.monthly_status[month_key] = 'Pending'
                            
                logger.debug("Rent Tracker",f"[DEBUG] {tenant.name} final delinquency balance: ${tenant.delinquency_balance}")
                logger.debug("Rent Tracker",f"[DEBUG] {tenant.name} delinquent months: {tenant.delinquent_months}")
                
                # Calculate final overpayment credit:
                # total_overpayment - total_credit_used = remaining credit
                tenant.overpayment_credit = max(0.0, total_overpayment - total_credit_used)
                logger.debug("Rent Tracker",f"[DEBUG] {tenant.name} overpayment calculation: ${total_overpayment:.2f} (new) - ${total_credit_used:.2f} (used) = ${tenant.overpayment_credit:.2f}")
                            
                            
            self.tenant_manager.save()
        except Exception as e:
            logging.error(f"Error in check_and_update_delinquency: {e}")
            logger.error("Rent Tracker",f"[ERROR] check_and_update_delinquency: {e}")
            import traceback
            traceback.print_exc()
    
    def check_and_update_lease_status(self, tenant):
        """Check if lease has expired and automatically update status to Inactive"""
        try:
            if not tenant.rental_period:
                logger.debug("Rent Tracker",f"[DEBUG] {tenant.name} has no rental period")
                return
            
            today = date.today()
            
            # Handle both old format (tuple) and new format (dict)
            if isinstance(tenant.rental_period, dict):
                end_date_str = tenant.rental_period.get('end_date')
            elif isinstance(tenant.rental_period, (list, tuple)) and len(tenant.rental_period) >= 2:
                end_date_str = tenant.rental_period[1]
            else:
                logger.debug("Rent Tracker",f"[DEBUG] {tenant.name} has invalid rental period format: {tenant.rental_period}")
                return
            
            if not end_date_str:
                logger.debug("Rent Tracker",f"[DEBUG] {tenant.name} has no end date")
                return
            
            end_date = date.fromisoformat(end_date_str)
            current_status = getattr(tenant, 'account_status', 'active')
            
            logger.debug("Rent Tracker",f"[DEBUG] Lease status check for {tenant.name}: end_date={end_date}, today={today}, status={current_status}")
            
            # If lease has expired and tenant is still active, mark as inactive
            if today > end_date and current_status.lower() == 'active':
                tenant.account_status = 'inactive'
                
                # Add automatic note
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                lease_expired_note = f"[{timestamp}] Lease expired on {end_date}. Account automatically set to Inactive."
                tenant.add_note(lease_expired_note)
                
                # Set $0 overrides for remaining months since lease expired
                if not hasattr(tenant, 'monthly_exceptions'):
                    tenant.monthly_exceptions = {}
                
                current_month_key = f"{today.year}-{today.month:02d}"
                if current_month_key not in tenant.monthly_exceptions:
                    end_date_for_overrides = date(today.year + 5, 12, 31)
                    self.set_range_override(
                        tenant.name,
                        today,
                        end_date_for_overrides,
                        0.0,
                        notes=f"Lease expired: rent set to $0"
                    )
                
                logger.info("Rent Tracker",f"[INFO] Lease expired for {tenant.name}. Account status changed to Inactive.")
                self.tenant_manager.save()
            else:
                logger.debug("Rent Tracker",f"[DEBUG] No status change needed for {tenant.name}: end_date > today = {end_date > today}, is_active = {current_status == 'Active'}")
                
        except Exception as e:
            logger.warning("Rent Tracker",f"[WARNING] Error checking lease status for {tenant.name}: {e}")
            import traceback
            traceback.print_exc()
    
    def ensure_months_to_charge(self, tenant):
        """Ensure months_to_charge is populated based on rental period"""
        if not tenant.rental_period:
            return
            
        try:
            # Handle both old format (tuple) and new format (dict)
            if isinstance(tenant.rental_period, dict):
                start_date_str = tenant.rental_period.get('start_date')
                end_date_str = tenant.rental_period.get('end_date')
            elif isinstance(tenant.rental_period, (list, tuple)) and len(tenant.rental_period) >= 2:
                start_date_str, end_date_str = tenant.rental_period[0], tenant.rental_period[1]
            else:
                logger.warning("Rent Tracker",f"[WARNING] Invalid rental_period format for {tenant.name}: {tenant.rental_period}")
                return
            
            if not start_date_str or not end_date_str:
                return
                
            start_date = date.fromisoformat(start_date_str)
            end_date = date.fromisoformat(end_date_str)
            
            # Generate all months between start and end dates
            current_date = start_date.replace(day=1)  # First day of start month
            months_to_charge = []
            
            while current_date <= end_date:
                months_to_charge.append((current_date.year, current_date.month))
                # Move to next month
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1)
            
            tenant.months_to_charge = months_to_charge
            logger.debug("Rent Tracker",f"[DEBUG] Updated months_to_charge for {tenant.name}: {months_to_charge}")
            
        except Exception as e:
            logger.debug("Rent Tracker",f"[DEBUG] Error updating months_to_charge for {tenant.name}: {e}")
    
    def __init__(self, current_user_id=None):
        logger.debug("RentTracker", f"Initializing RentTracker with user_id={current_user_id}")
        
        self.tenant_manager = TenantManager(current_user_id)
        self.action_queue = ActionQueue()
        self.current_user_id = current_user_id
        
        # Initialize database
        try:
            from src.database import DatabaseManager
            self.db = DatabaseManager()
        except ImportError:
            from database import DatabaseManager
            self.db = DatabaseManager()
        
        # Initialize dispute manager with database reference
        try:
            from src.disputes import DisputeManager
            self.dispute_manager = DisputeManager(db_manager=self.db)
        except Exception as e:
            logger.error("RentTracker", f"Failed to initialize dispute manager: {e}")
            self.dispute_manager = None
        
        # Initialize notification system and automation
        self.notification_system = None
        self.notification_automation = None
        self._initialize_notification_systems()
        
        logger.info("RentTracker", "RentTracker initialized successfully")
    
    def set_current_user(self, user_id):
        """Set the current user for the rent tracker"""
        logger.debug("RentTracker", f"Setting current user to {user_id}")
        self.current_user_id = user_id
        self.tenant_manager.set_current_user(user_id)
        logger.info("RentTracker", f"Current user set to {user_id}")
    
    def _initialize_notification_systems(self):
        """Initialize notification system and automation"""
        try:
            from src.notification_system import NotificationSystem
            from src.tenant_notification_automation import TenantNotificationAutomation
            
            # Initialize notification system
            self.notification_system = NotificationSystem(
                action_queue=self.action_queue, 
                rent_tracker=self
            )
            
            # Initialize automation system
            self.notification_automation = TenantNotificationAutomation(
                rent_tracker=self,
                notification_system=self.notification_system,
                action_queue=self.action_queue
            )
            
            # Start automation daemon
            self.notification_automation.start_automation()
            
            logger.info("RentTracker", "[INFO] Notification systems initialized successfully")
            
        except Exception as e:
            logger.warning("RentTracker", f"[WARNING] Failed to initialize notification systems: {e}")
            # Don't fail if notification system can't be initialized
    
    def process_due_actions(self, check_date=None):
        """Process all actions that are due to be executed"""
        if check_date is None:
            check_date = date.today().strftime('%Y-%m-%d')
        
        due_actions = self.action_queue.get_due_actions(check_date)
        results = []
        
        for action in due_actions:
            try:
                if action['action_type'] == 'rent_change':
                    result = self._execute_rent_change(action)
                    results.append(result)
                elif action['action_type'] == 'rental_period_change':
                    result = self._execute_rental_period_change(action)
                    results.append(result)
                elif action['action_type'] == 'notification':
                    result = self._execute_notification(action)
                    results.append(result)
                # Add more action types as needed
                    
            except Exception as e:
                error_result = {
                    'action_id': action['action_id'],
                    'success': False,
                    'error': str(e),
                    'action_type': action['action_type']
                }
                results.append(error_result)
                logger.error("RentTracker", f"[ERROR] Failed to execute action {action['action_id']}: {e}")
        
        return results
    
    def _execute_rent_change(self, action):
        """Execute a rent change action"""
        action_data = action['action_data']
        tenant = self.tenant_manager.get_tenant(action['tenant_id'])
        
        if not tenant:
            raise Exception(f"Tenant {action['tenant_id']} not found")
        
        old_rent = tenant.rent_amount
        new_rent = action_data['new_rent']
        
        # Apply the rent change
        tenant.rent_amount = new_rent
        self.tenant_manager.save()
        
        # Mark action as executed
        execution_result = {
            'old_rent': old_rent,
            'new_rent': new_rent,
            'tenant_name': tenant.name,
            'success': True
        }
        
        self.action_queue.execute_action(action['action_id'], execution_result)
        
        logger.info("RentTracker", f"[INFO] Executed rent change for {tenant.name}: ${old_rent:.2f} -> ${new_rent:.2f}")
        
        return {
            'action_id': action['action_id'],
            'success': True,
            'action_type': 'rent_change',
            'tenant_name': tenant.name,
            'details': execution_result
        }
    
    def _execute_rental_period_change(self, action):
        """Execute a rental period change action (lease renewal)"""
        action_data = action['action_data']
        tenant = self.tenant_manager.get_tenant(action['tenant_id'])
        
        if not tenant:
            raise Exception(f"Tenant {action['tenant_id']} not found")
        
        # Get old period info
        old_period = getattr(tenant, 'rental_period', None)
        
        # Apply the rental period change
        new_start_date = action_data['new_start_date']
        new_end_date = action_data['new_end_date']
        tenant.rental_period = [new_start_date, new_end_date]
        
        # Generate new months_to_charge for the renewal period
        from datetime import datetime
        start_date = datetime.strptime(new_start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(new_end_date, '%Y-%m-%d').date()
        
        new_months = []
        current_date = start_date
        
        while current_date <= end_date:
            new_months.append([current_date.year, current_date.month])
            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        # Extend the tenant's months_to_charge
        if not hasattr(tenant, 'months_to_charge'):
            tenant.months_to_charge = []
        
        # Add new months to existing ones (avoid duplicates)
        existing_months = set(tuple(month) for month in tenant.months_to_charge)
        for month in new_months:
            month_tuple = tuple(month)
            if month_tuple not in existing_months:
                tenant.months_to_charge.append(month)
        
        # Sort months chronologically
        tenant.months_to_charge.sort(key=lambda x: (x[0], x[1]))
        
        # Save changes
        self.tenant_manager.save()
        
        # Mark action as executed
        execution_result = {
            'old_period': old_period,
            'new_start_date': new_start_date,
            'new_end_date': new_end_date,
            'period_description': action_data.get('period_description', ''),
            'tenant_name': tenant.name,
            'success': True,
            'months_added': len(new_months)
        }
        
        self.action_queue.execute_action(action['action_id'], execution_result)
        
        start_formatted = datetime.strptime(new_start_date, '%Y-%m-%d').strftime('%b %d, %Y')
        end_formatted = datetime.strptime(new_end_date, '%Y-%m-%d').strftime('%b %d, %Y')
        logger.info("RentTracker", f"[INFO] Executed rental period change for {tenant.name}: {start_formatted} - {end_formatted}")
        
        return {
            'action_id': action['action_id'],
            'success': True,
            'action_type': 'rental_period_change',
            'tenant_name': tenant.name,
            'details': execution_result
        }
    
    def _execute_notification(self, action):
        """Execute a notification action"""
        action_data = action['action_data']
        
        # Import notification system
        from src.notification_system import NotificationSystem
        notification_system = NotificationSystem()
        
        # Extract notification details
        title = action_data['title']
        message = action_data['message']
        urgency = action_data.get('urgency', 'normal')
        icon_path = action_data.get('icon_path')
        
        # Send the notification
        success = notification_system.send_notification(
            title=title,
            message=message,
            icon_path=icon_path,
            urgency=urgency
        )
        
        # Mark action as executed
        execution_result = {
            'title': title,
            'message': message,
            'urgency': urgency,
            'success': success,
            'sent_at': datetime.now().isoformat()
        }
        
        self.action_queue.execute_action(action['action_id'], execution_result)
        
        logger.info("RentTracker", f"[INFO] Executed notification: {title} (Success: {success})")
        
        return {
            'action_id': action['action_id'],
            'success': success,
            'action_type': 'notification',
            'details': execution_result
        }
    
    def get_pending_actions_for_tenant(self, tenant_name):
        """Get pending actions for a specific tenant"""
        tenant = self.get_tenant_by_name(tenant_name)
        if not tenant:
            return []
        
        return self.action_queue.get_pending_actions(tenant.tenant_id)
    
    # Missing methods that the UI needs
    def add_payment(self, tenant_name, amount, payment_type='Cash', payment_date=None, payment_month=None, is_credit_usage=False, notes=None):
        """Add a payment for a tenant with enhanced tracking"""
        logger.debug("RentTracker", f"Adding payment for {tenant_name}: ${amount}")
        tenant = self.get_tenant_by_name(tenant_name)
        if not tenant:
            logger.warning("RentTracker", f"Tenant '{tenant_name}' not found")
            return False
        
        # Parse payment date
        if payment_date:
            if isinstance(payment_date, str):
                try:
                    payment_date = datetime.strptime(payment_date, '%Y-%m-%d').date()
                except ValueError:
                    payment_date = date.today()
        else:
            payment_date = date.today()
        
        # Determine which month this payment is for
        if payment_month:
            # Parse payment_month (format: YYYY-MM)
            try:
                year, month = payment_month.split('-')
                payment_year = int(year)
                payment_month_num = int(month)
            except (ValueError, AttributeError):
                # Fallback to payment date month
                payment_year = payment_date.year
                payment_month_num = payment_date.month
        else:
            # Use payment date month
            payment_year = payment_date.year
            payment_month_num = payment_date.month
        
        # Add to total rent paid
        tenant.total_rent_paid += amount
        
        # Initialize payment history if it doesn't exist
        if not hasattr(tenant, 'payment_history'):
            tenant.payment_history = []
        
        # Add detailed payment record
        payment_record = {
            'amount': amount,
            'type': payment_type,
            'date': payment_date.strftime('%Y-%m-%d'),
            'payment_month': f"{payment_year}-{payment_month_num:02d}",
            'year': payment_year,
            'month': payment_month_num,
            'is_credit_usage': is_credit_usage,  # Flag for reporting and tracking
            'notes': notes if notes else ''  # Store notes if provided
        }
        tenant.payment_history.append(payment_record)
        logger.debug("RentTracker", f"Payment record added: {payment_record}")
        logger.debug("RentTracker", f"Total payment history entries: {len(tenant.payment_history)}")
        
        # Update monthly status for the specified month
        month_key = (payment_year, payment_month_num)
        current_status = tenant.monthly_status.get(month_key, {})
        if isinstance(current_status, str):
            current_status = {'status': current_status}
        
        # Calculate if this payment covers the month fully
        expected_rent = self.get_effective_rent(tenant, payment_year, payment_month_num)
        
        # Calculate total paid for this month including this payment
        total_paid_this_month = amount
        for existing_payment in tenant.payment_history[:-1]:  # Exclude the current payment we just added
            if existing_payment['year'] == payment_year and existing_payment['month'] == payment_month_num:
                total_paid_this_month += existing_payment['amount']
        
        if total_paid_this_month >= expected_rent:
            current_status['status'] = 'Paid in Full'
            if total_paid_this_month > expected_rent and not is_credit_usage:
                # Only create overpayment credit if this is NOT a credit usage payment
                # Credit usage payments consume existing credit; they don't create new credit
                overpayment = total_paid_this_month - expected_rent
                tenant.overpayment_credit += overpayment
        else:
            current_status['status'] = 'Partial Payment'
        
        current_status['payment_type'] = payment_type
        current_status['payment_date'] = payment_date.isoformat()
        tenant.monthly_status[month_key] = current_status
        
        # Reduce delinquency if applicable
        if tenant.delinquency_balance > 0:
            reduction = min(tenant.delinquency_balance, amount)
            tenant.delinquency_balance -= reduction
        
        self.tenant_manager.save()
        logger.info("RentTracker", f"Payment of ${amount:.2f} added for {tenant_name} for month {payment_year}-{payment_month_num:02d}")
        return True
    
    def get_tenant_by_name(self, name):
        """Get tenant by name"""
        tenants = self.tenant_manager.search_tenants(name=name)
        if tenants:
            logger.debug("RentTracker", f"Found tenant: {name}")
            return tenants[0]
        logger.warning("RentTracker", f"Tenant not found: {name}")
        return None
    
    def save_tenants(self, progress_callback: Optional[Callable] = None):
        """
        Save all tenant data
        
        Args:
            progress_callback: Optional callback for progress updates (percentage, message)
        """
        try:
            if progress_callback:
                progress_callback(20, "Saving tenant data...")
            
            self.tenant_manager.save()
            
            if progress_callback:
                progress_callback(60, "Syncing to database...")
            
            # Sync to database if available
            if hasattr(self, 'db') and self.db:
                self.db.sync_all_tenants(self.tenant_manager.tenants)
            
            if progress_callback:
                progress_callback(90, "Reloading data...")
            
            # IMPORTANT: Reload the tenant manager cache from disk after saving
            # This ensures that subsequent get_tenant_by_name() calls get the updated data
            self.tenant_manager.load()
            
            if progress_callback:
                progress_callback(100, "Save complete!")
            
            logger.debug("RentTracker", "Tenants saved and reloaded successfully")
            return True
        except Exception as e:
            logger.error("RentTracker", f"Failed to save tenants: {str(e)}")
            raise  # Re-raise to let caller handle the error
    
    def get_all_tenants(self):
        """Get all tenants"""
        return self.tenant_manager.list_tenants()
    
    def delete_tenant(self, tenant_name):
        """Delete a tenant by name and return the tenant_id"""
        logger.debug("RentTracker", f"Deleting tenant: {tenant_name}")
        try:
            tenants = self.tenant_manager.list_tenants()
            tenant_to_delete = None
            tenant_id_to_delete = None
            
            # Find the tenant by name
            for tenant in tenants:
                if tenant.name == tenant_name:
                    tenant_to_delete = tenant
                    tenant_id_to_delete = tenant.tenant_id
                    break
            
            if not tenant_to_delete:
                logger.warning("RentTracker", f"Tenant '{tenant_name}' not found")
                return None
            
            # Delete from the tenants dictionary
            del self.tenant_manager.tenants[tenant_id_to_delete]
            logger.info("RentTracker", f"Deleted tenant '{tenant_name}' (ID: {tenant_id_to_delete})")
            return tenant_id_to_delete
        except Exception as e:
            logger.error("RentTracker", f"Failed to delete tenant: {str(e)}")
            return None
    
    def sync_all_tenants_to_database(self) -> Dict[str, Any]:
        """
        Sync all tenants from JSON to database
        Returns summary of sync results and any mismatches found
        """
        logger.debug("RentTracker", "Starting sync of all tenants to database")
        tenants = self.get_all_tenants()
        results = {
            'total_tenants': len(tenants),
            'synced': 0,
            'failed': 0,
            'payments_synced': 0,
            'mismatches': [],
            'summary': {}
        }
        
        for tenant in tenants:
            try:
                sync_result = self.db.sync_tenant_from_json(tenant.__dict__)
                results['synced'] += 1
                logger.debug("RentTracker", f"Synced tenant: {tenant.name}")
                
                if sync_result.get('mismatches'):
                    results['mismatches'].append({
                        'tenant_id': tenant.tenant_id,
                        'name': tenant.name,
                        'mismatches': sync_result['mismatches']
                    })
                
                # Sync payments for this tenant with payment index
                if hasattr(tenant, 'payment_history') and tenant.payment_history:
                    for payment_index, payment in enumerate(tenant.payment_history):
                        # Enrich payment with tenant_id and status from monthly_status
                        payment['tenant_id'] = tenant.tenant_id
                        
                        # Ensure payment_type is set (payment dict uses 'type', but sync expects 'payment_type')
                        if 'payment_type' not in payment and 'type' in payment:
                            payment['payment_type'] = payment.get('type', '')
                        
                        # Derive status from monthly_status if not already present
                        if 'status' not in payment or not payment['status']:
                            payment_year = payment.get('year')
                            payment_month = payment.get('month')
                            if payment_year and payment_month:
                                month_key = (payment_year, payment_month)
                                monthly_status = tenant.monthly_status.get(month_key, {})
                                if isinstance(monthly_status, dict):
                                    payment['status'] = monthly_status.get('status', '')
                                elif isinstance(monthly_status, str):
                                    payment['status'] = monthly_status
                        
                        # Generate details if not present
                        if 'details' not in payment or not payment['details']:
                            details_parts = []
                            if payment.get('is_credit_usage'):
                                details_parts.append('Service Credit Applied')
                            payment['details'] = '; '.join(details_parts) if details_parts else ''
                        
                        # Ensure date_received is set (payment dict uses 'date', but sync expects 'date_received')
                        if 'date_received' not in payment and 'date' in payment:
                            payment['date_received'] = payment.get('date', '')
                        
                        payment_result = self.db.sync_payment_from_json(payment, payment_index)
                        if payment_result.get('success'):
                            results['payments_synced'] += 1
                        
            except Exception as e:
                logger.warning("RentTracker", f"Failed to sync tenant {tenant.tenant_id}: {e}")
                results['failed'] += 1
        
        # Get mismatch summary
        results['summary'] = self.db.get_mismatch_summary()
        
        logger.info("RentTracker", f"Sync complete: {results['synced']} synced, {results['failed']} failed")
        if results['mismatches']:
            logger.info("RentTracker", f"[DATABASE SYNC] Found {len(results['mismatches'])} tenants with data mismatches")
        
        return results
    
    def get_database_sync_status(self) -> Dict[str, Any]:
        """Get current database sync status and mismatch summary"""
        return {
            'database_path': self.db.db_path,
            'mismatch_summary': self.db.get_mismatch_summary(),
            'recent_logs': self.db.get_sync_logs(limit=20)
        }
    
    def get_effective_rent(self, tenant, year, month):
        """Get the effective rent for a specific month, considering overrides"""
        logger.debug("RentTracker", f"Getting effective rent for {tenant.name}: {year}-{month:02d}")
        # Check for monthly override first
        monthly_key = f"{year}-{month:02d}"
        if monthly_key in tenant.monthly_exceptions:
            logger.debug("RentTracker", f"Using monthly override: ${tenant.monthly_exceptions[monthly_key]}")
            return tenant.monthly_exceptions[monthly_key]
        
        # Check for yearly override
        yearly_key = str(year)
        if yearly_key in tenant.monthly_exceptions:
            logger.debug("RentTracker", f"Using yearly override: ${tenant.monthly_exceptions[yearly_key]}")
            return tenant.monthly_exceptions[yearly_key]
        
        # Return base rent
        logger.debug("RentTracker", f"Using base rent: ${tenant.rent_amount}")
        return tenant.rent_amount
    
    def modify_rent(self, tenant_name, new_rent, effective_date, notes="", backdate=False):
        """Modify rent for a tenant with effective date"""
        logger.debug("RentTracker", f"Modifying rent for {tenant_name}: ${new_rent}, effective {effective_date}, backdate={backdate}")
        tenant = self.get_tenant_by_name(tenant_name)
        if not tenant:
            logger.warning("RentTracker", f"Tenant not found: {tenant_name}")
            return False
        
        if isinstance(effective_date, str):
            effective_date = date.fromisoformat(effective_date)
        
        # Update base rent amount
        tenant.rent_amount = new_rent
        
        # If backdating, update rent for all months from effective date
        if backdate:
            current_date = date.today()
            temp_date = effective_date
            months_updated = 0
            
            while temp_date <= current_date:
                year, month = temp_date.year, temp_date.month
                monthly_key = f"{year}-{month:02d}"
                
                # Set monthly override for this period
                tenant.monthly_exceptions[monthly_key] = new_rent
                months_updated += 1
                
                # Move to next month
                if temp_date.month == 12:
                    temp_date = date(temp_date.year + 1, 1, 1)
                else:
                    temp_date = date(temp_date.year, temp_date.month + 1, 1)
            
            logger.debug("RentTracker", f"Applied backdate to {months_updated} months")
        
        # Add note if provided
        if notes:
            timestamp = date.today().isoformat()
            rent_note = f"[{timestamp}] Rent modified to ${new_rent:.2f}: {notes}"
            if hasattr(tenant, 'add_note'):
                tenant.add_note(rent_note)
            else:
                current_notes = tenant.notes or ""
                tenant.notes = f"{current_notes}\n{rent_note}" if current_notes else rent_note
        
        self.tenant_manager.save()
        logger.info("RentTracker", f"Rent modification saved for {tenant_name}")
        return True
    
    def set_monthly_override(self, tenant_name, year, month, override_amount, notes=""):
        """Set a monthly rent override"""
        logger.debug("RentTracker", f"Setting monthly override for {tenant_name}: {year}-{month:02d} = ${override_amount}")
        tenant = self.get_tenant_by_name(tenant_name)
        if not tenant:
            logger.warning("RentTracker", f"Tenant not found: {tenant_name}")
            return False
        
        monthly_key = f"{year}-{month:02d}"
        
        if override_amount is None:
            # Remove the override
            if monthly_key in tenant.monthly_exceptions:
                del tenant.monthly_exceptions[monthly_key]
                logger.info("RentTracker", f"Removed monthly override for {tenant_name}: {monthly_key}")
        else:
            # Set the override
            tenant.monthly_exceptions[monthly_key] = override_amount
            logger.info("RentTracker", f"Set monthly override for {tenant_name}: {monthly_key} = ${override_amount}")
        
        if notes:
            timestamp = date.today().isoformat()
            if override_amount is None:
                override_note = f"[{timestamp}] Monthly override removed for {year}-{month:02d} - {notes}"
            else:
                override_note = f"[{timestamp}] Monthly override for {year}-{month:02d}: ${override_amount:.2f} - {notes}"
            if hasattr(tenant, 'add_note'):
                tenant.add_note(override_note)
            else:
                current_notes = tenant.notes or ""
                tenant.notes = f"{current_notes}\n{override_note}" if current_notes else override_note
        
        self.tenant_manager.save()
        return True
    
    def set_yearly_override(self, tenant_name, year, override_amount, notes=""):
        """Set a yearly rent override"""
        logger.debug("RentTracker", f"Setting yearly override for {tenant_name}: {year} = ${override_amount}")
        tenant = self.get_tenant_by_name(tenant_name)
        if not tenant:
            logger.warning("RentTracker", f"Tenant not found: {tenant_name}")
            return False
        
        yearly_key = str(year)
        
        if override_amount is None:
            # Remove the yearly override
            if yearly_key in tenant.monthly_exceptions:
                del tenant.monthly_exceptions[yearly_key]
                logger.info("RentTracker", f"Removed yearly override for {tenant_name}: {year}")
        else:
            # Set the yearly override
            tenant.monthly_exceptions[yearly_key] = override_amount
            logger.info("RentTracker", f"Set yearly override for {tenant_name}: {year} = ${override_amount}")
        
        if notes:
            timestamp = date.today().isoformat()
            if override_amount is None:
                override_note = f"[{timestamp}] Yearly override removed for {year} - {notes}"
            else:
                override_note = f"[{timestamp}] Yearly override for {year}: ${override_amount:.2f} - {notes}"
            if hasattr(tenant, 'add_note'):
                tenant.add_note(override_note)
            else:
                current_notes = tenant.notes or ""
                tenant.notes = f"{current_notes}\n{override_note}" if current_notes else override_note
        
        self.tenant_manager.save()
        return True
    
    def set_range_override(self, tenant_name, start_date, end_date, override_amount, notes=""):
        """Set a rent override for a date range"""
        tenant = self.get_tenant_by_name(tenant_name)
        if not tenant:
            return False
        
        if isinstance(start_date, str):
            start_date = date.fromisoformat(start_date)
        if isinstance(end_date, str):
            end_date = date.fromisoformat(end_date)
        
        # Set monthly overrides for each month in the range
        current_date = start_date
        while current_date <= end_date:
            monthly_key = f"{current_date.year}-{current_date.month:02d}"
            tenant.monthly_exceptions[monthly_key] = override_amount
            
            # Move to next month
            if current_date.month == 12:
                current_date = date(current_date.year + 1, 1, 1)
            else:
                current_date = date(current_date.year, current_date.month + 1, 1)
        
        if notes:
            timestamp = date.today().isoformat()
            range_note = f"[{timestamp}] Range override {start_date} to {end_date}: ${override_amount:.2f} - {notes}"
            if hasattr(tenant, 'add_note'):
                tenant.add_note(range_note)
            else:
                current_notes = tenant.notes or ""
                tenant.notes = f"{current_notes}\n{range_note}" if current_notes else range_note
        
        self.tenant_manager.save()
        return True
    
    def modify_payment(self, tenant_name, year, month, new_amount, payment_type=None):
        """Modify an existing payment"""
        tenant = self.get_tenant_by_name(tenant_name)
        if not tenant:
            return False
        
        # Get current payment info
        current_status = tenant.monthly_status.get((year, month), {})
        if isinstance(current_status, str):
            current_status = {'status': current_status}
        
        # Calculate old amount from status
        expected_rent = self.get_effective_rent(tenant, year, month)
        old_amount = 0
        if current_status.get('status') == 'Paid in Full':
            old_amount = expected_rent
        elif current_status.get('status') == 'Partial Payment':
            old_amount = expected_rent - tenant.delinquency_balance
        
        # Adjust total rent paid
        tenant.total_rent_paid = tenant.total_rent_paid - old_amount + new_amount
        
        # Update status
        if new_amount >= expected_rent:
            current_status['status'] = 'Paid in Full'
            if new_amount > expected_rent:
                overpayment = new_amount - expected_rent
                tenant.overpayment_credit += overpayment
        elif new_amount > 0:
            current_status['status'] = 'Partial Payment'
        else:
            current_status['status'] = 'Not Paid'
        
        if payment_type:
            current_status['payment_type'] = payment_type
        
        tenant.monthly_status[(year, month)] = current_status
        self.tenant_manager.save()
        return True
    
    def delete_payment(self, tenant_name, year, month):
        """Delete a payment"""
        tenant = self.get_tenant_by_name(tenant_name)
        if not tenant:
            return False
        
        # Get current payment info
        current_status = tenant.monthly_status.get((year, month), {})
        if isinstance(current_status, str):
            current_status = {'status': current_status}
        
        # Calculate amount to remove
        expected_rent = self.get_effective_rent(tenant, year, month)
        amount_to_remove = 0
        if current_status.get('status') == 'Paid in Full':
            amount_to_remove = expected_rent
        elif current_status.get('status') == 'Partial Payment':
            amount_to_remove = expected_rent - tenant.delinquency_balance
        
        # Adjust total rent paid
        tenant.total_rent_paid -= amount_to_remove
        
        # Remove the payment status
        if (year, month) in tenant.monthly_status:
            del tenant.monthly_status[(year, month)]
        
        self.tenant_manager.save()
        return True

    def set_rent_period(self, tenant_id, start_date, end_date):
        tenant = self.tenant_manager.get_tenant(tenant_id)
        if tenant:
            # Store old rental period for comparison
            old_rental_period = tenant.rental_period
            
            # Update rental period
            tenant.rental_period = {'start_date': start_date, 'end_date': end_date, 'lease_type': getattr(tenant.rental_period, 'lease_type', 'Fixed Term') if isinstance(tenant.rental_period, dict) else 'Fixed Term'}
            
            # Generate new months to charge rent for
            months = self._generate_months(start_date, end_date)
            tenant.months_to_charge = months
            
            # Clear old delinquency data that might be from previous rental period
            tenant.delinquency_balance = 0.0
            tenant.delinquent_months = []
            tenant.monthly_status = {}
            
            # Add note about rental period change
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y-%m-%d')
            if old_rental_period != tenant.rental_period:
                # Format old rental period properly for the note
                if isinstance(old_rental_period, dict):
                    old_period_str = f"{old_rental_period.get('start_date', 'Unknown')} to {old_rental_period.get('end_date', 'Unknown')}"
                elif isinstance(old_rental_period, (list, tuple)) and len(old_rental_period) >= 2:
                    old_period_str = f"{old_rental_period[0]} to {old_rental_period[1]}"
                else:
                    old_period_str = str(old_rental_period)
                    
                note = f"[{timestamp}] Rental period updated from {old_period_str} to {start_date} - {end_date}"
                if hasattr(tenant, 'add_note'):
                    tenant.add_note(note)
                else:
                    if not hasattr(tenant, '_notes_list'):
                        tenant._notes_list = []
                    tenant._notes_list.append(note)
            
            # Save and trigger full recalculation
            self.tenant_manager.save()
            
            # Force a full recalculation of delinquency based on new rental period
            self.check_and_update_delinquency(target_tenant_id=tenant_id)
            
            return True
        return False

    def _generate_months(self, start_date, end_date):
        # Returns list of (year, month) tuples between start_date and end_date
        months = []
        current = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
        while current <= end:
            months.append((current.year, current.month))
            # Move to next month
            if current.month == 12:
                current = date(current.year + 1, 1, 1)
            else:
                current = date(current.year, current.month + 1, 1)
        return months

    def get_tenant_summary(self, tenant_id):
        tenant = self.tenant_manager.get_tenant(tenant_id)
        if not tenant:
            return None
        summary = {
            'name': tenant.name,
            'tenant_id': tenant.tenant_id,
            'rental_period': tenant.rental_period,
            'rent_amount': tenant.rent_amount,
            'total_rent_paid': tenant.total_rent_paid,
            'delinquency_balance': tenant.delinquency_balance,
            'delinquent_months': tenant.delinquent_months,
            'account_status': tenant.account_status,
            'overpayment_credit': tenant.overpayment_credit,
            'monthly_status': tenant.monthly_status,
            'months_to_charge': tenant.months_to_charge,
            'deposit_amount': tenant.deposit_amount,
            'contact_info': tenant.contact_info,
            'notes': tenant.notes
        }
        return summary

    def update_monthly_status(self, tenant_id, year, month, status, payment_type=None, other_type=None, overpayment=0.0):
        tenant = self.tenant_manager.get_tenant(tenant_id)
        if tenant:
            entry = {'status': status}
            if payment_type:
                entry['payment_type'] = payment_type
            if other_type:
                entry['other_type'] = other_type
            tenant.monthly_status[(year, month)] = entry
            if status == 'Overpayment':
                tenant.overpayment_credit += overpayment
            elif status == 'Delinquent':
                tenant.delinquent_months.append((year, month))
            self.tenant_manager.save()
            return True
        return False

    def get_all_tenants_summary(self):
        return [self.get_tenant_summary(t.tenant_id) for t in self.tenant_manager.list_tenants()]

    def change_rent_details(self, tenant_id, username, password, **kwargs):
        # Require password verification before changing rent details
        if AccountManager:
            account_manager = AccountManager()
            if not account_manager.verify_password(username, password):
                logger.warning("RentTracker", f"Invalid credentials for user {username}")
                raise PermissionError('Invalid credentials')
        
        tenant = self.tenant_manager.get_tenant(tenant_id)
        if not tenant:
            logger.warning("RentTracker", f"Tenant not found: {tenant_id}")
            return None
        
        for k, v in kwargs.items():
            if hasattr(tenant, k):
                setattr(tenant, k, v)
        
        self.tenant_manager.save()
        logger.info("RentTracker", f"Updated rent details for tenant {tenant_id}")
        return tenant

    def send_income_to_financial_tracker(self, tenant_id, account_id):
        # Manually add paid rent as income to financial tracker/bank
        tenant = self.tenant_manager.get_tenant(tenant_id)
        if not tenant:
            return False
        bank = Bank()
        amount = tenant.total_rent_paid
        desc = f'Rent income from tenant {tenant.name} ({tenant.tenant_id})'
        bank.add_transaction(amount, desc, account_id, type_='in', category='rent')
        return True

    def get_rent_summary_for_financial_tracker(self):
        # Returns total paid, expected, and remaining rent for all tenants
        tenants = self.tenant_manager.list_tenants()
        total_paid = sum(t.total_rent_paid for t in tenants)
        expected = sum(
            (len(t.months_to_charge) * t.rent_amount if t.months_to_charge else 0)
            for t in tenants
        )
        remaining = expected - total_paid
        unpaid_tenants = [t for t in tenants if t.total_rent_paid < (len(t.months_to_charge) * t.rent_amount if t.months_to_charge else 0)]
        return {
            'total_paid': total_paid,
            'expected': expected,
            'remaining': remaining,
            'unpaid_tenants': [t.tenant_id for t in unpaid_tenants]
        }

    def compensate_expected_remaining(self, tenant_id, amount):
        # RentTracker deals with expected remaining rent for a tenant
        tenant = self.tenant_manager.get_tenant(tenant_id)
        if not tenant:
            return False
        # This could be used to record a payment or adjustment
        tenant.total_rent_paid += amount
        self.tenant_manager.save()
        return True

    def set_deposit(self, tenant_id, amount):
        tenant = self.tenant_manager.get_tenant(tenant_id)
        if tenant:
            tenant.deposit_amount = amount
            self.tenant_manager.save()
            return True
        return False

    def update_deposit(self, tenant_id, amount):
        return self.set_deposit(tenant_id, amount)

    def get_deposit(self, tenant_id):
        tenant = self.tenant_manager.get_tenant(tenant_id)
        return tenant.deposit_amount if tenant else None

    def set_late_fee(self, tenant_id, enabled, amount=0.0):
        tenant = self.tenant_manager.get_tenant(tenant_id)
        if tenant:
            tenant.late_fee_enabled = enabled
            tenant.late_fee_amount = amount if enabled else 0.0
            self.tenant_manager.save()
            return True
        return False

    def get_late_fee(self, tenant_id):
        tenant = self.tenant_manager.get_tenant(tenant_id)
        if tenant and getattr(tenant, 'late_fee_enabled', False):
            return getattr(tenant, 'late_fee_amount', 0.0)
        return 0.0

    def apply_late_fee(self, tenant_id, year, month):
        tenant = self.tenant_manager.get_tenant(tenant_id)
        if tenant and getattr(tenant, 'late_fee_enabled', False):
            fee = getattr(tenant, 'late_fee_amount', 0.0)
            tenant.delinquency_balance += fee
            if (year, month) not in tenant.delinquent_months:
                tenant.delinquent_months.append((year, month))
            self.tenant_manager.save()
            return True
        return False
    
    # Query System for Rent Analysis
    def query_rent_info(self, tenant_name, query_date):
        """
        Query comprehensive rent information for a specific date
        Returns: {
            'date': date,
            'base_rent': float,
            'effective_rent': float,
            'override_type': str or None,
            'override_amount': float or None,
            'payments': [list of payments for that month],
            'total_paid': float,
            'balance_due': float,
            'payment_status': str,
            'payment_details': [detailed payment info],
            'service_credit_info': dict,
            'overpayment_credit_info': dict,
            'notification_events': [list of notifications for the date]
        }
        """
        from datetime import datetime
        
        tenant = self.get_tenant_by_name(tenant_name)
        if not tenant:
            return None
        
        if isinstance(query_date, str):
            query_date = datetime.strptime(query_date, '%Y-%m-%d').date()
        
        year_month = (query_date.year, query_date.month)
        year_month_str = f"{query_date.year}-{query_date.month:02d}"
        
        # Get base rent amount
        base_rent = tenant.rent_amount
        
        # Check for rent modifications (backdated changes)
        effective_rent = self._get_effective_rent_for_date(tenant, query_date)
        
        # Check for monthly override
        monthly_override = tenant.monthly_exceptions.get(year_month_str)
        override_type = None
        override_amount = None
        final_rent = effective_rent
        
        if monthly_override is not None:
            override_type = 'monthly'
            override_amount = monthly_override
            final_rent = monthly_override
        else:
            # Check for yearly override
            yearly_override = self._get_yearly_override_for_date(tenant, query_date)
            if yearly_override is not None:
                override_type = 'yearly'
                override_amount = yearly_override
                final_rent = yearly_override
        
        # Get payment status and calculate totals
        payment_status = tenant.monthly_status.get(year_month, 'No Payment')
        total_paid = 0.0
        payment_details = []
        overpayment_used = 0.0
        service_credit_used = 0.0
        cash_payments = 0.0
        
        # Analyze payments from payment history
        if hasattr(tenant, 'payment_history'):
            for payment in tenant.payment_history:
                if payment['year'] == query_date.year and payment['month'] == query_date.month:
                    total_paid += payment['amount']
                    
                    # Categorize payment types
                    payment_type = payment.get('type', 'Unknown')
                    is_credit_usage = payment.get('is_credit_usage', False)
                    
                    if 'Overpayment Credit' in payment_type:
                        overpayment_used += payment['amount']
                    elif 'Service Credit' in payment_type:
                        service_credit_used += payment['amount']
                    else:
                        cash_payments += payment['amount']
                    
                    # Create detailed payment record
                    payment_details.append({
                        'amount': payment['amount'],
                        'type': payment_type,
                        'date': payment.get('date', 'Unknown'),
                        'is_credit_usage': is_credit_usage,
                        'payment_month': payment.get('payment_month', year_month_str)
                    })
        
        # Get service credit information
        service_credit_info = {
            'current_balance': getattr(tenant, 'service_credit', 0.0),
            'used_this_month': service_credit_used,
            'history_count': len(getattr(tenant, 'service_credit_history', []))
        }
        
        # Get overpayment credit information
        overpayment_credit_info = {
            'current_balance': getattr(tenant, 'overpayment_credit', 0.0),
            'used_this_month': overpayment_used
        }
        
        # Get notification events for this date
        notification_events = self._get_notification_events_for_date(tenant.tenant_id, query_date)
        
        # Calculate balance
        balance_due = final_rent - total_paid
        
        return {
            'tenant_name': tenant_name,
            'date': query_date,
            'year_month': year_month,
            'base_rent': base_rent,
            'effective_rent': effective_rent,
            'final_rent': final_rent,
            'override_type': override_type,
            'override_amount': override_amount,
            'total_paid': total_paid,
            'balance_due': balance_due,
            'payment_status': payment_status,
            'payment_details': payment_details,
            'cash_payments': cash_payments,
            'service_credit_info': service_credit_info,
            'overpayment_credit_info': overpayment_credit_info,
            'notification_events': notification_events,
            'tenant_total_overpayment': tenant.overpayment_credit,
            'tenant_total_delinquency': tenant.delinquency_balance,
            'tenant_total_service_credit': getattr(tenant, 'service_credit', 0.0),
            'tenant_total_rent_paid': sum(payment['amount'] for payment in tenant.payment_history) if hasattr(tenant, 'payment_history') else 0.0
        }
    
    def _get_effective_rent_for_date(self, tenant, query_date):
        """Get the effective rent amount for a specific date, considering rent modifications"""
        from datetime import datetime
        # Check if tenant has rent modification history
        if hasattr(tenant, 'rent_modifications'):
            for mod in tenant.rent_modifications:
                mod_date = datetime.strptime(mod['effective_date'], '%Y-%m-%d').date()
                if query_date >= mod_date:
                    return mod['rent_amount']
        
        return tenant.rent_amount
    
    def _get_yearly_override_for_date(self, tenant, query_date):
        """Check if there's a yearly override for the given date"""
        if hasattr(tenant, 'yearly_overrides'):
            return tenant.yearly_overrides.get(str(query_date.year))
        return None
    
    def _get_notification_events_for_date(self, tenant_id, query_date):
        """Get notification events for a specific tenant and date"""
        try:
            # Get notifications from action queue
            notifications = []
            
            # Check action queue for notifications
            if hasattr(self, 'action_queue') and self.action_queue:
                # Get all actions for this tenant
                tenant_actions = [action for action in self.action_queue.actions 
                                if action.get('tenant_id') == tenant_id]
                
                # Filter notifications for the specific date
                query_date_str = query_date.strftime('%Y-%m-%d')
                for action in tenant_actions:
                    if (action.get('action_type') == 'notification' and 
                        action.get('scheduled_date') == query_date_str):
                        
                        action_data = action.get('action_data', {})
                        notifications.append({
                            'type': action_data.get('notification_type', 'Unknown'),
                            'message': action_data.get('message', ''),
                            'status': action.get('status', 'pending'),
                            'created_date': action.get('created_date'),
                            'executed_date': action.get('executed_date'),
                            'urgency': action_data.get('urgency', 'normal')
                        })
            
            # Also check for system notifications if notification system is available
            if hasattr(self, 'notification_system') and self.notification_system:
                # This would require the notification system to store sent notifications
                # For now, we'll just return the action queue notifications
                pass
            
            return notifications
            
        except Exception as e:
            logger.warning("RentTracker", f"[WARNING] Failed to get notification events: {e}")
            return []
    
    def query_rent_timeline(self, tenant_name, start_date, end_date):
        """
        Query rent information for a date range
        Returns list of monthly rent info
        """
        from datetime import datetime
        from calendar import monthrange
        
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        timeline = []
        current_year = start_date.year
        current_month = start_date.month
        
        while True:
            # Create date for first day of current month
            current_date = datetime(current_year, current_month, 1).date()
            
            # Break if we've passed the end date
            if current_date > end_date:
                break
                
            rent_info = self.query_rent_info(tenant_name, current_date)
            if rent_info:
                timeline.append(rent_info)
            
            # Move to next month
            current_month += 1
            if current_month > 12:
                current_month = 1
                current_year += 1
        
        return timeline
    
    def test_rent_scenarios(self, tenant_name):
        """
        Test various rent scenarios for debugging
        Returns comprehensive test results
        """
        from datetime import datetime, timedelta
        
        tenant = self.get_tenant_by_name(tenant_name)
        if not tenant:
            return f"Tenant '{tenant_name}' not found"
        
        test_results = {
            'tenant': tenant_name,
            'base_rent': tenant.rent_amount,
            'scenarios': []
        }
        
        # Test current month
        current_date = datetime.now().date()
        current_info = self.query_rent_info(tenant_name, current_date)
        test_results['scenarios'].append({
            'scenario': 'Current Month',
            'date': current_date,
            'info': current_info
        })
        
        # Test previous month
        prev_month = current_date.replace(day=1) - timedelta(days=1)
        prev_info = self.query_rent_info(tenant_name, prev_month)
        test_results['scenarios'].append({
            'scenario': 'Previous Month',
            'date': prev_month,
            'info': prev_info
        })
        
        # Test next month
        if current_date.month == 12:
            next_month = current_date.replace(year=current_date.year + 1, month=1, day=1)
        else:
            next_month = current_date.replace(month=current_date.month + 1, day=1)
        next_info = self.query_rent_info(tenant_name, next_month)
        test_results['scenarios'].append({
            'scenario': 'Next Month',
            'date': next_month,
            'info': next_info
        })
        
        return test_results
    
    def print_query_results(self, results):
        """Pretty print query results for testing"""
        if isinstance(results, str):
            print(results)
            return
        
        if isinstance(results, list):  # Timeline results
            print(f"\n=== RENT TIMELINE ===")
            for month_data in results:
                self._print_single_query(month_data)
                print("-" * 50)
        elif isinstance(results, dict) and 'scenarios' in results:  # Test scenarios
            print(f"\n=== RENT SCENARIOS TEST FOR {results['tenant']} ===")
            print(f"Base Rent: ${results['base_rent']:.2f}")
            print()
            for scenario in results['scenarios']:
                print(f"--- {scenario['scenario']} ({scenario['date']}) ---")
                self._print_single_query(scenario['info'])
                print()
        else:  # Single query
            self._print_single_query(results)
    
    def _print_single_query(self, query_result):
        """Print a single query result"""
        if not query_result:
            print("No data available")
            return
        
        print(f"Tenant: {query_result['tenant_name']}")
        print(f"Date: {query_result['date']} ({query_result['year_month'][1]:02d}/{query_result['year_month'][0]})")
        print(f"Base Rent: ${query_result['base_rent']:.2f}")
        print(f"Effective Rent: ${query_result['effective_rent']:.2f}")
        print(f"Final Rent: ${query_result['final_rent']:.2f}")
        
        if query_result['override_type']:
            print(f"Override: {query_result['override_type'].title()} (${query_result['override_amount']:.2f})")
        
        print(f"Total Paid: ${query_result['total_paid']:.2f}")
        print(f"Balance Due: ${query_result['balance_due']:.2f}")
        print(f"Status: {query_result['payment_status']}")
    
    def query_rent_for_date(self, tenant_name: str, query_date_str: str) -> Dict[str, Any]:
        """
        Query rent information for a specific date.
        Returns detailed information about rent amount, payments, and overrides.
        
        Args:
            tenant_name (str): Name of the tenant
            query_date_str (str): Date in 'YYYY-MM-DD' format
            
        Returns:
            dict: Comprehensive rent information for the date
        """
        from datetime import datetime
        
        # Parse the query date
        try:
            query_date = datetime.strptime(query_date_str, '%Y-%m-%d').date()
        except ValueError:
            return {"error": "Invalid date format. Use YYYY-MM-DD"}
        
        # Get the tenant
        tenant = self.get_tenant_by_name(tenant_name)
        if not tenant:
            return {"error": f"Tenant '{tenant_name}' not found"}
        
        year = query_date.year
        month = query_date.month
        
        # Get base rent amount for this date
        base_rent = self.get_effective_rent(tenant, year, month)
        
        # Check for overrides
        override_info = self._get_override_info(tenant, year, month, query_date)
        
        # Get payment information
        payment_info = self._get_payment_info(tenant, year, month)
        
        # Calculate balance
        effective_rent = override_info.get('effective_amount', base_rent)
        balance_due = effective_rent - payment_info['total_paid']
        
        return {
            'tenant_name': tenant_name,
            'query_date': query_date_str,
            'base_rent': base_rent,
            'effective_rent': effective_rent,
            'override_info': override_info,
            'payment_info': payment_info,
            'balance_due': balance_due,
            'payment_status': payment_info['status'],
            'is_delinquent': balance_due > 0 and query_date < date.today()
        }
    
    def _get_override_info(self, tenant, year: int, month: int, query_date) -> Dict[str, Any]:
        """Get override information for a specific date"""
        override_info = {
            'has_override': False,
            'override_type': None,
            'override_amount': 0.0,
            'effective_amount': tenant.rent_amount
        }
        
        # Check monthly override first (highest priority)
        if hasattr(tenant, 'monthly_exceptions') and tenant.monthly_exceptions:
            monthly_key = (year, month)
            if monthly_key in tenant.monthly_exceptions:
                override_info.update({
                    'has_override': True,
                    'override_type': 'monthly',
                    'override_amount': tenant.monthly_exceptions[monthly_key],
                    'effective_amount': tenant.monthly_exceptions[monthly_key]
                })
                return override_info
        
        # Check yearly override
        if hasattr(tenant, 'yearly_overrides') and tenant.yearly_overrides:
            if year in tenant.yearly_overrides:
                override_info.update({
                    'has_override': True,
                    'override_type': 'yearly',
                    'override_amount': tenant.yearly_overrides[year],
                    'effective_amount': tenant.yearly_overrides[year]
                })
                return override_info
        
        # Check range overrides
        if hasattr(tenant, 'range_overrides') and tenant.range_overrides:
            for range_data in tenant.range_overrides:
                start_date = datetime.strptime(range_data['start_date'], '%Y-%m-%d').date()
                end_date = datetime.strptime(range_data['end_date'], '%Y-%m-%d').date()
                
                if start_date <= query_date <= end_date:
                    override_info.update({
                        'has_override': True,
                        'override_type': 'range',
                        'override_amount': range_data['amount'],
                        'effective_amount': range_data['amount'],
                        'range_start': range_data['start_date'],
                        'range_end': range_data['end_date']
                    })
                    return override_info
        
        return override_info
    
    def _get_payment_info(self, tenant, year: int, month: int) -> Dict[str, Any]:
        """Get payment information for a specific month"""
        month_key = (year, month)
        
        payment_info = {
            'total_paid': 0.0,
            'payment_history': [],
            'status': 'Not Paid'
        }
        
        # Check monthly status
        if hasattr(tenant, 'monthly_status') and tenant.monthly_status:
            status = tenant.monthly_status.get(month_key, 'Not Paid')
            payment_info['status'] = status
            
            if status == 'Paid in Full':
                payment_info['total_paid'] = self.get_effective_rent(tenant, year, month)
            elif status == 'Partial Payment':
                # Calculate partial payment amount
                expected_rent = self.get_effective_rent(tenant, year, month)
                payment_info['total_paid'] = expected_rent - tenant.delinquency_balance
        
        # Get detailed payment history if available
        if hasattr(tenant, 'payment_history') and tenant.payment_history:
            for payment in tenant.payment_history:
                payment_date = datetime.strptime(payment['date'], '%Y-%m-%d').date()
                if payment_date.year == year and payment_date.month == month:
                    payment_info['payment_history'].append(payment)
        
        return payment_info
    
    def get_rent_timeline(self, tenant_name: str, start_date_str: Optional[str] = None, end_date_str: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get a timeline of rent changes, overrides, and payments for a tenant.
        
        Args:
            tenant_name (str): Name of the tenant
            start_date_str (str): Start date in 'YYYY-MM-DD' format (optional)
            end_date_str (str): End date in 'YYYY-MM-DD' format (optional)
            
        Returns:
            list: Timeline of rent events
        """
        from datetime import datetime, timedelta
        
        tenant = self.get_tenant_by_name(tenant_name)
        if not tenant:
            return []
        
        timeline = []
        
        # Set default date range if not provided
        if not start_date_str:
            if tenant.rental_period:
                start_date_str = tenant.rental_period[0]
            else:
                start_date_str = '2024-01-01'  # Default fallback
        
        if not end_date_str:
            if tenant.rental_period:
                end_date_str = tenant.rental_period[1]
            else:
                end_date_str = date.today().strftime('%Y-%m-%d')
        
        # Ensure we have string values for parsing
        assert start_date_str is not None, "start_date_str should not be None at this point"
        assert end_date_str is not None, "end_date_str should not be None at this point"
        
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        # Generate monthly timeline
        current_date = start_date.replace(day=1)  # Start from first of month
        
        while current_date <= end_date:
            month_data = self.query_rent_for_date(tenant_name, current_date.strftime('%Y-%m-%d'))
            if 'error' not in month_data:
                # Ensure proper type casting for dictionary access
                override_info: Dict[str, Any] = month_data['override_info']
                payment_info: Dict[str, Any] = month_data['payment_info']
                
                timeline.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'year_month': f"{current_date.year}-{current_date.month:02d}",
                    'base_rent': month_data['base_rent'],
                    'effective_rent': month_data['effective_rent'],
                    'has_override': override_info['has_override'],
                    'override_type': override_info['override_type'],
                    'total_paid': payment_info['total_paid'],
                    'balance_due': month_data['balance_due'],
                    'status': month_data['payment_status']
                })
            
            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        return timeline
    
    def print_query_result(self, query_result):
        """Print a formatted query result"""
        if 'error' in query_result:
            print(f"Error: {query_result['error']}")
            return
        
        print(f"\n=== Rent Query for {query_result['tenant_name']} on {query_result['query_date']} ===")
        print(f"Base Rent: ${query_result['base_rent']:.2f}")
        print(f"Effective Rent: ${query_result['effective_rent']:.2f}")
        
        if query_result['override_info']['has_override']:
            override_info = query_result['override_info']
            print(f"Override: {override_info['override_type'].title()} (${override_info['override_amount']:.2f})")
            if override_info['override_type'] == 'range':
                print(f"  Range: {override_info['range_start']} to {override_info['range_end']}")
        
        print(f"Total Paid: ${query_result['payment_info']['total_paid']:.2f}")
        print(f"Balance Due: ${query_result['balance_due']:.2f}")
        print(f"Status: {query_result['payment_status']}")
        
        if query_result['is_delinquent']:
            print("⚠️  DELINQUENT")
        
        if query_result['payment_info']['payment_history']:
            print("\nPayment History:")
            for payment in query_result['payment_info']['payment_history']:
                print(f"  - {payment['date']}: ${payment['amount']:.2f} ({payment['type']})")
    
    def test_query_system(self):
        """Test the query system with sample data"""
        print("=== Testing Rent Query System ===")
        
        # Get first tenant for testing
        tenants = self.tenant_manager.list_tenants()
        if not tenants:
            print("No tenants found for testing")
            return
        
        tenant = tenants[0]
        print(f"Testing with tenant: {tenant.name}")
        
        # Test current date query
        today = date.today().strftime('%Y-%m-%d')
        result = self.query_rent_for_date(tenant.name, today)
        self.print_query_result(result)
        
        # Test timeline
        print(f"\n=== Rent Timeline for {tenant.name} ===")
        timeline = self.get_rent_timeline(tenant.name)
        for entry in timeline[-6:]:  # Show last 6 months
            status_icon = "✅" if entry['balance_due'] == 0 else "❌" if entry['balance_due'] > 0 else "💰"
            override_icon = "🔄" if entry['has_override'] else ""
            print(f"{entry['year_month']}: ${entry['effective_rent']:.2f} {override_icon} | Paid: ${entry['total_paid']:.2f} | Balance: ${entry['balance_due']:.2f} {status_icon}")

    def cleanup(self):
        """Cleanup notification systems and stop automation daemon"""
        try:
            if hasattr(self, 'notification_automation') and self.notification_automation:
                self.notification_automation.stop_automation()
                print("[INFO] Notification automation stopped")
        except Exception as e:
            print(f"[WARNING] Error during cleanup: {e}")
    
    # ========== DISPUTE MANAGEMENT METHODS ==========
    
    def create_dispute(
        self,
        tenant_id: str,
        dispute_type: str,
        description: str,
        amount: Optional[float] = None,
        reference_month: Optional[Tuple[int, int]] = None,
        evidence_notes: Optional[str] = None,
        reference_payment_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new dispute for a tenant
        
        Args:
            tenant_id: Tenant ID
            dispute_type: Type of dispute
            description: Description of dispute
            amount: Amount in dispute
            reference_month: Reference month (year, month) tuple
            evidence_notes: Supporting evidence notes
            reference_payment_id: ID of payment being disputed (optional)
            
        Returns:
            Dispute dictionary or None if failed
        """
        if not self.dispute_manager:
            logger.error("RentTracker", "Dispute manager not initialized")
            return None
        
        try:
            dispute = self.dispute_manager.create_dispute(
                tenant_id=tenant_id,
                dispute_type=dispute_type,
                description=description,
                amount=amount,
                reference_month=reference_month,
                evidence_notes=evidence_notes,
                created_by="web_ui",
                reference_payment_id=reference_payment_id
            )
            
            logger.info("RentTracker", f"Created dispute {dispute.dispute_id} for tenant {tenant_id}")
            return dispute.to_dict()
        except Exception as e:
            logger.error("RentTracker", f"Failed to create dispute: {e}")
            return None
    
    def get_dispute(self, dispute_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific dispute by ID"""
        if not self.dispute_manager:
            return None
        
        dispute = self.dispute_manager.get_dispute(dispute_id)
        return dispute.to_dict() if dispute else None
    
    def get_tenant_disputes(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get all disputes for a tenant"""
        if not self.dispute_manager:
            return []
        
        disputes = self.dispute_manager.get_tenant_disputes(tenant_id)
        return [d.to_dict() for d in disputes]
    
    def get_all_disputes(self) -> List[Dict[str, Any]]:
        """Get all disputes across all tenants"""
        if not self.dispute_manager:
            return []
        
        disputes = self.dispute_manager.get_all_disputes()
        return [d.to_dict() for d in disputes]
    
    def update_dispute_status(
        self,
        dispute_id: str,
        status: str,
        admin_notes: Optional[str] = None
    ) -> bool:
        """
        Update dispute status
        
        Args:
            dispute_id: ID of dispute
            status: New status
            admin_notes: Admin notes
            
        Returns:
            True if successful, False otherwise
        """
        if not self.dispute_manager:
            return False
        
        success = self.dispute_manager.update_dispute_status(
            dispute_id,
            status,
            admin_notes
        )
        
        if success:
            logger.info("RentTracker", f"Updated dispute {dispute_id} status to {status}")
        
        return success
    
    def get_dispute_stats(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Get dispute statistics"""
        if not self.dispute_manager:
            return {'total': 0, 'by_status': {}, 'by_type': {}, 'total_amount': 0.0}
        
        return self.dispute_manager.get_dispute_stats(tenant_id)
    
    def get_disputes_for_payment(self, payment_id: str) -> List[Dict[str, Any]]:
        """Get all disputes related to a specific payment"""
        if not self.db:
            return []
        
        try:
            disputes = self.db.get_disputes_for_payment(payment_id)
            logger.info("RentTracker", f"Retrieved {len(disputes)} disputes for payment {payment_id}")
            return disputes
        except Exception as e:
            logger.error("RentTracker", f"Failed to get disputes for payment {payment_id}: {e}")
            return []
    
    def get_disputes_for_month(self, tenant_id: str, year: int, month: int) -> List[Dict[str, Any]]:
        """Get all disputes for a tenant in a specific month (delinquency-related)"""
        if not self.db:
            return []
        
        try:
            # Get all disputes for the tenant
            disputes = self.db.get_tenant_disputes(tenant_id)
            
            # Filter by reference month
            reference_month_str = f"{year}-{month:02d}"
            month_disputes = [
                d for d in disputes 
                if d.get('reference_month') == reference_month_str
            ]
            
            logger.info("RentTracker", f"Retrieved {len(month_disputes)} disputes for {tenant_id} in {reference_month_str}")
            return month_disputes
        except Exception as e:
            logger.error("RentTracker", f"Failed to get disputes for month: {e}")
            return []
    
    def resolve_dispute(self, dispute_id: str, admin_notes: str) -> bool:
        """Mark a dispute as resolved"""
        return self.update_dispute_status(dispute_id, "resolved", admin_notes)
    
    def reject_dispute(self, dispute_id: str, admin_notes: str) -> bool:
        """Mark a dispute as rejected"""
        return self.update_dispute_status(dispute_id, "rejected", admin_notes)
    
    def acknowledge_dispute(self, dispute_id: str) -> bool:
        """Mark a dispute as acknowledged"""
        return self.update_dispute_status(dispute_id, "acknowledged")
    
    # ========== DISPUTE DISPLAY AND ADMIN ACTIONS ==========
    
    def get_payment_dispute_status(self, payment_id: str) -> Dict[str, Any]:
        """
        Get dispute status for a specific payment
        Returns info on whether payment is disputed and what disputes exist
        """
        if not self.db:
            return {'is_disputed': False, 'disputes': []}
        
        try:
            disputes = self.db.get_disputes_for_payment(payment_id)
            open_disputes = [d for d in disputes if d.get('status') in ['open', 'acknowledged', 'pending_review']]
            
            return {
                'is_disputed': len(open_disputes) > 0,
                'dispute_count': len(disputes),
                'open_dispute_count': len(open_disputes),
                'disputes': disputes,
                'has_unresolved': len(open_disputes) > 0
            }
        except Exception as e:
            logger.warning("RentTracker", f"Failed to get payment dispute status: {e}")
            return {'is_disputed': False, 'disputes': []}
    
    def get_delinquency_dispute_status(self, tenant_id: str, year: int, month: int) -> Dict[str, Any]:
        """
        Get dispute status for a delinquent month
        Returns info on whether delinquency is disputed
        """
        disputes = self.get_disputes_for_month(tenant_id, year, month)
        open_disputes = [d for d in disputes if d.get('status') in ['open', 'acknowledged', 'pending_review']]
        
        return {
            'is_disputed': len(open_disputes) > 0,
            'dispute_count': len(disputes),
            'open_dispute_count': len(open_disputes),
            'disputes': disputes,
            'has_unresolved': len(open_disputes) > 0
        }
    
    def get_tenant_dispute_summary(self, tenant_id: str) -> Dict[str, Any]:
        """
        Get summary of all disputes for a tenant (for admin dashboard)
        Shows which items have active disputes
        """
        if not self.db:
            return {
                'total_disputes': 0,
                'open_disputes': 0,
                'disputed_payments': {},
                'disputed_months': {},
                'awaiting_review': 0
            }
        
        try:
            disputes = self.db.get_tenant_disputes(tenant_id)
            
            # Categorize by type
            disputed_payments = {}  # payment_id -> dispute info
            disputed_months = {}    # month -> dispute info
            
            for dispute in disputes:
                if dispute.get('reference_payment_id'):
                    payment_id = dispute['reference_payment_id']
                    if payment_id not in disputed_payments:
                        disputed_payments[payment_id] = []
                    disputed_payments[payment_id].append(dispute)
                elif dispute.get('reference_month'):
                    month_key = dispute['reference_month']
                    if month_key not in disputed_months:
                        disputed_months[month_key] = []
                    disputed_months[month_key].append(dispute)
            
            open_count = sum(1 for d in disputes if d.get('status') in ['open', 'acknowledged', 'pending_review'])
            pending_review = sum(1 for d in disputes if d.get('status') == 'pending_review')
            
            return {
                'total_disputes': len(disputes),
                'open_disputes': open_count,
                'pending_review_count': pending_review,
                'resolved_count': sum(1 for d in disputes if d.get('status') == 'resolved'),
                'rejected_count': sum(1 for d in disputes if d.get('status') == 'rejected'),
                'disputed_payments': disputed_payments,
                'disputed_months': disputed_months,
                'awaiting_review': pending_review,
                'all_disputes': disputes
            }
        except Exception as e:
            logger.error("RentTracker", f"Failed to get tenant dispute summary: {e}")
            return {
                'total_disputes': 0,
                'open_disputes': 0,
                'disputed_payments': {},
                'disputed_months': {},
                'awaiting_review': 0
            }
    
    def uphold_dispute(self, dispute_id: str, admin_notes: str, action: str = "payment_corrected") -> bool:
        """
        Admin upholds a dispute (tenant was right)
        action can be: 'payment_corrected', 'balance_adjusted', 'delinquency_removed', etc.
        """
        dispute = self.get_dispute(dispute_id)
        if not dispute:
            return False
        
        # Mark as resolved
        success = self.resolve_dispute(dispute_id, f"[UPHELD] {action} - {admin_notes}")
        
        if success:
            logger.info("RentTracker", f"Dispute {dispute_id} upheld: {action}")
            # In a real system, you would apply the action here
            # e.g., refund payment, remove delinquency, etc.
        
        return success
    
    def deny_dispute(self, dispute_id: str, admin_notes: str, reason: str = "evidence_insufficient") -> bool:
        """
        Admin denies/rejects a dispute (tenant was wrong)
        reason can be: 'evidence_insufficient', 'already_resolved', 'invalid_claim', etc.
        """
        dispute = self.get_dispute(dispute_id)
        if not dispute:
            return False
        
        # Mark as rejected
        success = self.reject_dispute(dispute_id, f"[DENIED] {reason} - {admin_notes}")
        
        if success:
            logger.info("RentTracker", f"Dispute {dispute_id} denied: {reason}")
        
        return success
    
    def acknowledge_and_review_dispute(self, dispute_id: str) -> bool:
        """
        Admin acknowledges dispute and marks for review
        """
        return self.update_dispute_status(dispute_id, "pending_review", "Marked for review by admin")
    
    def get_disputes_awaiting_admin_review(self) -> List[Dict[str, Any]]:
        """
        Get all disputes that need admin attention (open or pending_review)
        """
        if not self.db:
            return []
        
        try:
            all_disputes = self.db.get_all_disputes()
            awaiting_review = [
                d for d in all_disputes 
                if d.get('status') in ['open', 'pending_review']
            ]
            
            logger.info("RentTracker", f"Found {len(awaiting_review)} disputes awaiting review")
            return awaiting_review
        except Exception as e:
            logger.error("RentTracker", f"Failed to get disputes awaiting review: {e}")
            return []
    
    def __del__(self):
        """Destructor to ensure cleanup on deletion"""
        self.cleanup()