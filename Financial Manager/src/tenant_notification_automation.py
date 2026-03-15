import threading
import time
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Union
import json
import os
from queue import Queue, Empty
from dataclasses import dataclass
from enum import Enum
from assets.Logger import Logger
logger = Logger()
try:
    from .app_paths import AUTOMATION_STATE_FILE, AUTOMATION_SETTINGS_FILE
except ImportError:
    from app_paths import AUTOMATION_STATE_FILE, AUTOMATION_SETTINGS_FILE

@dataclass
class NotificationEvent:
    """Represents a notification event to be processed"""
    tenant_id: str
    notification_type: str
    scheduled_date: str
    data: Dict[str, Any]
    priority: int = 1  # 1=low, 2=normal, 3=high, 4=critical

class NotificationPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

class TenantNotificationAutomation:
    """
    Thread-safe automated notification system for tenants
    Handles rent due, payment overdue, lease expiry, and custom notifications
    """
    
    def __init__(self, rent_tracker=None, notification_system=None, action_queue=None):
        logger.debug("TenantNotificationAutomation", "Initializing TenantNotificationAutomation")
        self.rent_tracker = rent_tracker
        self.notification_system = notification_system
        self.action_queue = action_queue
        
        # Thread management
        self.is_running = False
        self.automation_thread = None
        self.check_interval = 3600  # Check every hour
        
        # Thread-safe notification queue
        self.notification_queue = Queue()
        
        # Synchronization locks
        self.tenant_lock = threading.RLock()
        self.queue_lock = threading.RLock()
        
        # Automation settings
        self.automation_settings = {
            'enabled': True,
            'check_interval_hours': 1,
            'max_retries': 3,
            'retry_delay_minutes': 30,
            'batch_size': 10
        }
        
        # Load automation settings
        self.load_automation_settings()
        
        # Tracking processed notifications to avoid duplicates
        self.processed_notifications = set()
        self.processed_notifications_lock = threading.Lock()
        
        # Last automation run tracking
        self.last_automation_run = None
        self.minimum_automation_interval = 1800  # 30 minutes between automation checks
        self.automation_state_file = AUTOMATION_STATE_FILE
        self._load_automation_state()
        logger.info("TenantNotificationAutomation", "TenantNotificationAutomation initialized")
        
    def load_automation_settings(self):
        """Load automation settings from configuration"""
        logger.debug("TenantNotificationAutomation", "Loading automation settings")
        try:
            if os.path.exists(AUTOMATION_SETTINGS_FILE):
                with open(AUTOMATION_SETTINGS_FILE, 'r') as f:
                    settings = json.load(f)
                    self.automation_settings.update(settings)
                    
                # Update check interval
                self.check_interval = self.automation_settings.get('check_interval_hours', 1) * 3600
                
                logger.info("TenantNotificationAutomation", f"Automation settings loaded: {self.automation_settings}")
        except Exception as e:
            logger.warning("TenantNotificationAutomation", f"Failed to load automation settings: {e}")
    
    def _load_automation_state(self):
        """Load the last automation run time from file"""
        logger.debug("TenantNotificationAutomation", "Loading automation state")
        try:
            if os.path.exists(self.automation_state_file):
                with open(self.automation_state_file, 'r') as f:
                    state = json.load(f)
                    self.last_automation_run = state.get('last_automation_run')
                    logger.info("TenantNotificationAutomation", f"Loaded last automation run: {self.last_automation_run}")
        except Exception as e:
            logger.warning("TenantNotificationAutomation", f"Failed to load automation state: {e}")
            self.last_automation_run = None
    
    def _save_automation_state(self):
        """Save the last automation run time to file"""
        try:
            os.makedirs(os.path.dirname(self.automation_state_file), exist_ok=True)
            state = {
                'last_automation_run': self.last_automation_run
            }
            with open(self.automation_state_file, 'w') as f:
                json.dump(state, f, indent=2)
            logger.debug("TenantNotificationAutomation", "Automation state saved")
        except Exception as e:
            logger.warning("TenantNotificationAutomation", f"Failed to save automation state: {e}")
    
    def _should_run_automation(self):
        """Check if enough time has passed since last automation run"""
        if not self.last_automation_run:
            return True
        
        try:
            from datetime import datetime
            last_run = datetime.fromisoformat(self.last_automation_run)
            now = datetime.now()
            time_since_last = (now - last_run).total_seconds()
            
            should_run = time_since_last >= self.minimum_automation_interval
            if not should_run:
                remaining = self.minimum_automation_interval - time_since_last
                logger.info("TenantNotificationAutomation", f"Skipping automation - {remaining/60:.1f} minutes remaining")
            
            return should_run
        except Exception as e:
            logger.warning("TenantNotificationAutomation", f"Error checking automation timing: {e}")
            return True
    
    def save_automation_settings(self):
        """Save automation settings to configuration"""
        try:
            os.makedirs(os.path.dirname(AUTOMATION_SETTINGS_FILE), exist_ok=True)
            
            with open(AUTOMATION_SETTINGS_FILE, 'w') as f:
                json.dump(self.automation_settings, f, indent=2)
                
            logger.info("TenantNotificationAutomation", "Automation settings saved")
        except Exception as e:
            logger.error("TenantNotificationAutomation", f"Failed to save automation settings: {e}")
    
    def start_automation(self):
        """Start the automated notification system"""
        logger.debug("TenantNotificationAutomation", "Starting automation")
        if self.is_running:
            logger.info("TenantNotificationAutomation", "Notification automation is already running")
            return
        
        if not self.automation_settings.get('enabled', True):
            logger.info("TenantNotificationAutomation", "Notification automation is disabled")
            return
        
        self.is_running = True
        
        # Send startup summary notification asynchronously
        startup_thread = threading.Thread(target=self._send_startup_summary, daemon=True)
        startup_thread.start()
        
        # Start main automation loop
        self.automation_thread = threading.Thread(target=self._automation_loop, daemon=True)
        self.automation_thread.start()
        
        logger.info("TenantNotificationAutomation", f"Notification automation started (check interval: {self.check_interval}s)")
    
    def _send_startup_summary(self):
        """Send a consolidated startup summary notification instead of individual notifications"""
        try:
            if not self.rent_tracker:
                return
            
            # Give the system a moment to fully initialize
            time.sleep(2)
            
            tenants = self.rent_tracker.tenant_manager.list_tenants()
            if not tenants:
                return
            
            today = date.today()
            overdue_count = 0
            due_soon_count = 0
            lease_expiring_count = 0
            
            for tenant in tenants:
                try:
                    # Skip non-active tenants
                    account_status = getattr(tenant, 'account_status', 'Active')
                    if account_status and account_status.lower() != 'active':
                        continue
                    
                    # Check for overdue payments
                    if hasattr(tenant, 'delinquent_months') and tenant.delinquent_months:
                        overdue_count += 1
                    
                    # Check for payments due soon (next 3 days)
                    try:
                        due_day = int(getattr(tenant, 'rent_due_date', 1))
                    except:
                        due_day = 1
                    
                    next_due = today.replace(day=due_day)
                    if next_due <= today:
                        # Next month
                        if today.month == 12:
                            next_due = next_due.replace(year=today.year + 1, month=1)
                        else:
                            next_due = next_due.replace(month=today.month + 1)
                    
                    days_until_due = (next_due - today).days
                    if 0 <= days_until_due <= 3:
                        due_soon_count += 1
                    
                    # Check for lease expiring soon (next 30 days)
                    if hasattr(tenant, 'rental_period'):
                        rental_period = tenant.rental_period
                        end_date_str = None
                        
                        if isinstance(rental_period, dict):
                            end_date_str = rental_period.get('end_date')
                        elif isinstance(rental_period, (list, tuple)) and len(rental_period) >= 2:
                            end_date_str = rental_period[1]
                        
                        if end_date_str:
                            try:
                                end_date = date.fromisoformat(end_date_str)
                                days_until_expiry = (end_date - today).days
                                if 0 <= days_until_expiry <= 30:
                                    lease_expiring_count += 1
                            except:
                                pass
                                
                except Exception as e:
                    logger.debug("TenantNotificationAutomation", f"Error checking tenant {tenant.tenant_id}: {e}")
            
            # Only send notification if there are items to report
            if overdue_count > 0 or due_soon_count > 0 or lease_expiring_count > 0:
                summary_parts = []
                
                if overdue_count > 0:
                    summary_parts.append(f"{overdue_count} tenant(s) with overdue payments")
                
                if due_soon_count > 0:
                    summary_parts.append(f"{due_soon_count} tenant(s) with rent due soon")
                
                if lease_expiring_count > 0:
                    summary_parts.append(f"{lease_expiring_count} lease(s) expiring within 30 days")
                
                title = "Financial Manager - Tenant Status Summary"
                message = f"System startup complete.\n\n" + "\n".join(f"• {part}" for part in summary_parts)
                
                # Send the consolidated notification
                if self.notification_system:
                    self.notification_system.send_notification(
                        title=title,
                        message=message
                    )
                    logger.info("TenantNotificationAutomation", f"Startup summary sent: {'; '.join(summary_parts)}")
            else:
                logger.info("TenantNotificationAutomation", "No urgent tenant issues found during startup")
                
        except Exception as e:
            print(f"[ERROR] Failed to send startup summary: {e}")
    
    def stop_automation(self):
        """Stop the automated notification system"""
        logger.debug("TenantNotificationAutomation", "Stopping automation")
        if not self.is_running:
            logger.info("TenantNotificationAutomation", "Notification automation is not running")
            return
        
        self.is_running = False
        
        if self.automation_thread:
            self.automation_thread.join(timeout=10)
        
        logger.info("TenantNotificationAutomation", "Notification automation stopped")
    
    def _automation_loop(self):
        """Main automation loop"""
        logger.info("TenantNotificationAutomation", "Notification automation loop started")
        
        # Startup delay to prevent immediate notification spam
        startup_delay = 30  # Wait 30 seconds after startup before processing notifications
        logger.info("TenantNotificationAutomation", f"Waiting {startup_delay} seconds before starting notification checks...")
        
        for _ in range(startup_delay):
            if not self.is_running:
                return
            time.sleep(1)
        
        while self.is_running:
            try:
                # Check if enough time has passed since last automation run
                if not self._should_run_automation():
                    # Sleep for the check interval and continue
                    for _ in range(self.check_interval):
                        if not self.is_running:
                            break
                        time.sleep(1)
                    continue
                
                # Update last automation run time
                self.last_automation_run = datetime.now().isoformat()
                self._save_automation_state()
                
                # Process due notifications first (these are time-sensitive)
                self._process_due_notifications()
                
                # Generate new notifications (but rate-limited)
                self._generate_automatic_notifications()
                
                # Process notification queue asynchronously
                queue_thread = threading.Thread(target=self._process_notification_queue, daemon=True)
                queue_thread.start()
                
                # Sleep for check interval
                for _ in range(self.check_interval):
                    if not self.is_running:
                        break
                    time.sleep(1)
                
            except Exception as e:
                logger.error("TenantNotificationAutomation", f"Automation loop error: {e}")
                time.sleep(60)  # Wait before retrying
    
    def _process_due_notifications(self):
        """Process notifications that are due"""
        if not self.action_queue:
            return
        
        try:
            logger.debug("TenantNotificationAutomation", "Processing due notifications")
            current_date = date.today().strftime('%Y-%m-%d')
            due_actions = self.action_queue.get_due_actions(current_date) if self.action_queue else []
            
            notification_actions = [
                action for action in due_actions 
                if action['action_type'] == 'notification'
            ]
            
            for action in notification_actions:
                try:
                    self._execute_notification_action(action)
                except Exception as e:
                    logger.error("TenantNotificationAutomation", f"Failed to execute notification action {action.get('action_id')}: {e}")
                    
        except Exception as e:
            logger.error("TenantNotificationAutomation", f"Failed to process due notifications: {e}")
    
    def _generate_automatic_notifications(self):
        """Generate automatic notifications based on tenant status"""
        if not self.rent_tracker:
            return
        
        try:
            logger.debug("TenantNotificationAutomation", "Generating automatic notifications")
            with self.tenant_lock:
                tenants = self.rent_tracker.tenant_manager.list_tenants()
            
            for tenant in tenants:
                try:
                    # Skip non-active tenants
                    account_status = getattr(tenant, 'account_status', 'Active')
                    if account_status and account_status.lower() != 'active':
                        continue
                    
                    self._check_tenant_notifications(tenant)
                except Exception as e:
                    logger.error("TenantNotificationAutomation", f"Failed to check notifications for tenant {tenant.tenant_id}: {e}")
                    
        except Exception as e:
            logger.error("TenantNotificationAutomation", f"Failed to generate automatic notifications: {e}")
    
    def _check_tenant_notifications(self, tenant):
        """Check and gather notification data for a specific tenant"""
        # Get tenant notification preferences
        notification_prefs = getattr(tenant, 'notification_preferences', {})
        
        if not notification_prefs:
            # Use default preferences
            notification_prefs = {
                'methods': ['system'],
                'types': ['rent_due', 'payment_overdue', 'lease_expiry'],
                'timing': {
                    'rent_reminder_days': 3,
                    'overdue_notice_days': 1,
                    'lease_expiry_days': 30
                }
            }
        
        # Collect notification data instead of scheduling individual notifications
        notification_data = {
            'tenant': tenant,
            'notification_prefs': notification_prefs,
            'alerts': []
        }
        
        # Check for rent due notifications
        if 'rent_due' in notification_prefs.get('types', []):
            rent_alert = self._check_rent_due_data(tenant, notification_prefs)
            if rent_alert:
                notification_data['alerts'].append(rent_alert)
        
        # Check for payment overdue notifications
        if 'payment_overdue' in notification_prefs.get('types', []):
            overdue_alert = self._check_payment_overdue_data(tenant, notification_prefs)
            if overdue_alert:
                notification_data['alerts'].append(overdue_alert)
        
        # Check for lease expiry notifications
        if 'lease_expiry' in notification_prefs.get('types', []):
            expiry_alert = self._check_lease_expiry_data(tenant, notification_prefs)
            if expiry_alert:
                notification_data['alerts'].append(expiry_alert)
        
        # Check for paid up confirmation
        paid_up_alert = self._check_paid_up_data(tenant, notification_prefs)
        if paid_up_alert:
            notification_data['alerts'].append(paid_up_alert)
        
        # If there are any alerts for this tenant, send a consolidated notification
        if notification_data['alerts']:
            self._send_consolidated_tenant_notification(notification_data)
    
    def _check_rent_due_data(self, tenant, notification_prefs):
        """Check if rent due notification should be sent and return alert data"""
        try:
            today = date.today()
            due_day = getattr(tenant, 'due_day', 1)
            reminder_days = notification_prefs.get('timing', {}).get('rent_reminder_days', 3)
            
            # Calculate next due date
            if today.day <= due_day:
                # Due date is this month
                due_date = date(today.year, today.month, due_day)
            else:
                # Due date is next month
                if today.month == 12:
                    due_date = date(today.year + 1, 1, due_day)
                else:
                    due_date = date(today.year, today.month + 1, due_day)
            
            # Calculate reminder date
            reminder_date = due_date - timedelta(days=reminder_days)
            
            # Check if we should send reminder today
            if today == reminder_date:
                notification_id = f"rent_due_{tenant.tenant_id}_{due_date.strftime('%Y-%m-%d')}"
                
                with self.processed_notifications_lock:
                    if notification_id not in self.processed_notifications:
                        self.processed_notifications.add(notification_id)
                        return {
                            'type': 'rent_due',
                            'tenant_id': tenant.tenant_id,
                            'tenant_name': getattr(tenant, 'name', 'Unknown'),
                            'due_date': due_date,
                            'days_until_due': (due_date - today).days,
                            'message': f"Rent reminder: Payment due on {due_date.strftime('%Y-%m-%d')}"
                        }
                        
        except Exception as e:
            logger.error("TenantNotificationAutomation", f"Failed to check rent due data for {tenant.tenant_id}: {e}")
        
        return None
    
    def _check_payment_overdue_data(self, tenant, notification_prefs):
        """Check if payment overdue notification should be sent and return alert data"""
        try:
            today = date.today()
            due_day = getattr(tenant, 'due_day', 1)
            overdue_days = notification_prefs.get('timing', {}).get('overdue_notice_days', 1)
            
            # Calculate last due date
            if today.day >= due_day:
                # Due date was this month
                last_due_date = date(today.year, today.month, due_day)
            else:
                # Due date was last month
                if today.month == 1:
                    last_due_date = date(today.year - 1, 12, due_day)
                else:
                    last_due_date = date(today.year, today.month - 1, due_day)
            
            # Calculate overdue notification date
            overdue_date = last_due_date + timedelta(days=overdue_days)
            
            # Check if payment is overdue and we should notify today
            delinquency_balance = getattr(tenant, 'delinquency_balance', 0)
            if today >= overdue_date and delinquency_balance > 0:
                notification_id = f"payment_overdue_{tenant.tenant_id}_{last_due_date.strftime('%Y-%m-%d')}"
                
                with self.processed_notifications_lock:
                    if notification_id not in self.processed_notifications:
                        self.processed_notifications.add(notification_id)
                        return {
                            'type': 'payment_overdue',
                            'tenant_id': tenant.tenant_id,
                            'tenant_name': getattr(tenant, 'name', 'Unknown'),
                            'due_date': last_due_date,
                            'days_overdue': (today - last_due_date).days,
                            'amount_owed': delinquency_balance,
                            'message': f"Payment overdue: ${delinquency_balance:.2f} past due since {last_due_date.strftime('%Y-%m-%d')}"
                        }
                        
        except Exception as e:
            print(f"[ERROR] Failed to check payment overdue data for {tenant.tenant_id}: {e}")
        
        return None
    
    def _check_lease_expiry_data(self, tenant, notification_prefs):
        """Check if lease expiry notification should be sent and return alert data"""
        try:
            today = date.today()
            expiry_days = notification_prefs.get('timing', {}).get('lease_expiry_days', 30)
            
            # Get lease end date
            rental_period = getattr(tenant, 'rental_period', {})
            if isinstance(rental_period, dict):
                end_date_str = rental_period.get('end_date')
            elif isinstance(rental_period, (list, tuple)) and len(rental_period) >= 2:
                end_date_str = rental_period[1]
            else:
                return None  # No valid lease end date
            
            if not end_date_str:
                return None
            
            # Parse end date
            try:
                end_date = datetime.fromisoformat(end_date_str).date()
            except:
                return None
            
            # Calculate notification date
            notification_date = end_date - timedelta(days=expiry_days)
            
            # Check if we should send notification today
            if today == notification_date:
                notification_id = f"lease_expiry_{tenant.tenant_id}_{end_date.strftime('%Y-%m-%d')}"
                
                with self.processed_notifications_lock:
                    if notification_id not in self.processed_notifications:
                        self.processed_notifications.add(notification_id)
                        return {
                            'type': 'lease_expiry',
                            'tenant_id': tenant.tenant_id,
                            'tenant_name': getattr(tenant, 'name', 'Unknown'),
                            'expiry_date': end_date,
                            'days_until_expiry': (end_date - today).days,
                            'message': f"Lease expiring in {(end_date - today).days} days on {end_date.strftime('%Y-%m-%d')}"
                        }
                        
        except Exception as e:
            print(f"[ERROR] Failed to check lease expiry data for {tenant.tenant_id}: {e}")
        
        return None
    
    def _check_paid_up_data(self, tenant, notification_prefs):
        """Check if tenant has paid up and return confirmation data"""
        try:
            # Only send if tenant was previously delinquent
            delinquency_balance = getattr(tenant, 'delinquency_balance', 0)
            if (hasattr(tenant, '_was_delinquent') and tenant._was_delinquent and delinquency_balance <= 0):
                
                notification_id = f"paid_up_{tenant.tenant_id}_{date.today().strftime('%Y-%m-%d')}"
                
                with self.processed_notifications_lock:
                    if notification_id not in self.processed_notifications:
                        self.processed_notifications.add(notification_id)
                        tenant._was_delinquent = False
                        return {
                            'type': 'paid_up',
                            'tenant_id': tenant.tenant_id,
                            'tenant_name': getattr(tenant, 'name', 'Unknown'),
                            'message': f"Account brought current - all payments up to date"
                        }
            
            # Track delinquency status
            if delinquency_balance > 0:
                tenant._was_delinquent = True
                        
        except Exception as e:
            print(f"[ERROR] Failed to check paid up data for {tenant.tenant_id}: {e}")
        
        return None
    
    def _send_consolidated_tenant_notification(self, notification_data):
        """Send a single consolidated notification for all tenant alerts"""
        try:
            tenant = notification_data['tenant']
            alerts = notification_data['alerts']
            notification_prefs = notification_data['notification_prefs']
            
            if not alerts:
                return
            
            # Build consolidated message
            tenant_name = getattr(tenant, 'name', 'Unknown')
            title = f"Financial Manager - {tenant_name} Alert"
            
            # Group alerts by type for better organization
            alert_groups = {
                'rent_due': [],
                'payment_overdue': [],
                'lease_expiry': [],
                'paid_up': []
            }
            
            for alert in alerts:
                alert_type = alert.get('type', 'unknown')
                if alert_type in alert_groups:
                    alert_groups[alert_type].append(alert)
            
            # Build message sections
            message_parts = [f"Tenant: {tenant_name}"]
            
            # Priority order: overdue first, then due, then expiry, then good news
            if alert_groups['payment_overdue']:
                message_parts.append("🔴 OVERDUE PAYMENTS:")
                for alert in alert_groups['payment_overdue']:
                    message_parts.append(f"  • {alert['message']}")
            
            if alert_groups['rent_due']:
                message_parts.append("🟡 UPCOMING RENT:")
                for alert in alert_groups['rent_due']:
                    message_parts.append(f"  • {alert['message']}")
            
            if alert_groups['lease_expiry']:
                message_parts.append("📅 LEASE EXPIRY:")
                for alert in alert_groups['lease_expiry']:
                    message_parts.append(f"  • {alert['message']}")
            
            if alert_groups['paid_up']:
                message_parts.append("✅ GOOD NEWS:")
                for alert in alert_groups['paid_up']:
                    message_parts.append(f"  • {alert['message']}")
            
            message = "\n".join(message_parts)
            
            # Send using notification system in a separate thread to keep it non-blocking
            notification_thread = threading.Thread(
                target=self._send_notification_async_consolidated,
                args=(title, message, tenant.tenant_id, notification_prefs),
                daemon=True
            )
            notification_thread.start()
                
            print(f"[INFO] Queued consolidated notification for {tenant_name}: {len(alerts)} alerts")
                
        except Exception as e:
            print(f"[ERROR] Failed to send consolidated tenant notification: {e}")
            import traceback
            traceback.print_exc()
    
    def _send_notification_async_consolidated(self, title, message, tenant_id, notification_prefs):
        """Send consolidated notification asynchronously"""
        try:
            if self.notification_system:
                # Determine urgency and methods
                urgency = 'high' if '🔴 OVERDUE' in message else 'normal'
                send_methods = notification_prefs.get('methods', ['system'])
                
                self.notification_system.send_comprehensive_notification(
                    title=title,
                    message=message,
                    tenant_id=tenant_id,
                    send_methods=send_methods,
                    urgency=urgency
                )
            else:
                print(f"[WARNING] No notification system available for tenant {tenant_id}")
        except Exception as e:
            print(f"[ERROR] Failed to send async consolidated notification: {e}")
    
    def _schedule_rent_due_notification(self, tenant, due_date, notification_prefs):
        """Schedule a rent due notification - DISABLED: Using consolidated notifications instead"""
        return  # Disabled - using consolidated notification system
        try:
            # Get custom template or use default
            templates = notification_prefs.get('templates', {})
            template = templates.get('rent_due', 'Your rent payment of ${amount} is due on {due_date}.')
            
            # Format message
            message = template.format(
                amount=getattr(tenant, 'rent_amount', 0),
                due_date=due_date.strftime('%B %d, %Y'),
                tenant_name=tenant.name
            )
            
            # Create notification data
            action_data = {
                'title': f'Rent Due Reminder - {tenant.name}',
                'message': message,
                'urgency': 'normal',
                'send_methods': notification_prefs.get('methods', ['system']),
                'notification_type': 'rent_due'
            }
            
            # Schedule today
            scheduled_date = date.today().strftime('%Y-%m-%d')
            
            # Add to action queue
            if self.action_queue:
                self.action_queue.add_action(
                    action_type='notification',
                    scheduled_date=scheduled_date,
                    tenant_id=tenant.tenant_id,
                    action_data=action_data,
                    description=f"Automatic rent due reminder for {tenant.name}"
                )
                print(f"[INFO] Scheduled rent due notification for {tenant.name}")
            else:
                print(f"[WARNING] No action queue available to schedule rent due notification for {tenant.name}")
            
        except Exception as e:
            print(f"[ERROR] Failed to schedule rent due notification: {e}")
    
    def _schedule_payment_overdue_notification(self, tenant, due_date, notification_prefs):
        """Schedule a payment overdue notification - DISABLED: Using consolidated notifications instead"""
        return  # Disabled - using consolidated notification system
        try:
            # Get custom template or use default
            templates = notification_prefs.get('templates', {})
            template = templates.get('overdue', 'Your rent payment of ${amount} is overdue. Please pay immediately.')
            
            # Format message
            message = template.format(
                amount=getattr(tenant, 'delinquency_balance', 0),
                due_date=due_date.strftime('%B %d, %Y'),
                tenant_name=tenant.name
            )
            
            # Create notification data
            action_data = {
                'title': f'Payment Overdue - {tenant.name}',
                'message': message,
                'urgency': 'high',
                'send_methods': notification_prefs.get('methods', ['system']),
                'notification_type': 'payment_overdue'
            }
            
            # Schedule today
            scheduled_date = date.today().strftime('%Y-%m-%d')
            
            # Add to action queue
            if self.action_queue:
                self.action_queue.add_action(
                    action_type='notification',
                    scheduled_date=scheduled_date,
                    tenant_id=tenant.tenant_id,
                    action_data=action_data,
                    description=f"Automatic payment overdue notice for {tenant.name}"
                )
                print(f"[INFO] Scheduled payment overdue notification for {tenant.name}")
            else:
                print(f"[WARNING] No action queue available to schedule payment overdue notification for {tenant.name}")
            
        except Exception as e:
            print(f"[ERROR] Failed to schedule payment overdue notification: {e}")
    
    def _schedule_lease_expiry_notification(self, tenant, end_date, notification_prefs):
        """Schedule a lease expiry notification - DISABLED: Using consolidated notifications instead"""
        return  # Disabled - using consolidated notification system
        try:
            message = f"Your lease expires on {end_date.strftime('%B %d, %Y')}. Please contact us to discuss renewal options."
            
            # Create notification data
            action_data = {
                'title': f'Lease Expiry Warning - {tenant.name}',
                'message': message,
                'urgency': 'normal',
                'send_methods': notification_prefs.get('methods', ['system']),
                'notification_type': 'lease_expiry'
            }
            
            # Schedule today
            scheduled_date = date.today().strftime('%Y-%m-%d')
            
            # Add to action queue
            if self.action_queue:
                self.action_queue.add_action(
                    action_type='notification',
                    scheduled_date=scheduled_date,
                    tenant_id=tenant.tenant_id,
                    action_data=action_data,
                    description=f"Automatic lease expiry warning for {tenant.name}"
                )
                print(f"[INFO] Scheduled lease expiry notification for {tenant.name}")
            else:
                print(f"[WARNING] No action queue available to schedule lease expiry notification for {tenant.name}")
            
        except Exception as e:
            print(f"[ERROR] Failed to schedule lease expiry notification: {e}")
    
    def _schedule_paid_up_confirmation(self, tenant, notification_prefs):
        """Schedule a paid up confirmation notification - DISABLED: Using consolidated notifications instead"""
        return  # Disabled - using consolidated notification system
        try:
            message = f"Thank you! Your account is now current. We appreciate your prompt payment."
            
            # Create notification data
            action_data = {
                'title': f'Payment Received - {tenant.name}',
                'message': message,
                'urgency': 'low',
                'send_methods': notification_prefs.get('methods', ['system']),
                'notification_type': 'payment_received'
            }
            
            # Schedule today
            scheduled_date = date.today().strftime('%Y-%m-%d')
            
            # Add to action queue
            if self.action_queue:
                self.action_queue.add_action(
                    action_type='notification',
                    scheduled_date=scheduled_date,
                    tenant_id=tenant.tenant_id,
                    action_data=action_data,
                    description=f"Automatic payment confirmation for {tenant.name}"
                )
                print(f"[INFO] Scheduled paid up confirmation for {tenant.name}")
            else:
                print(f"[WARNING] No action queue available to schedule paid up confirmation for {tenant.name}")
            
        except Exception as e:
            print(f"[ERROR] Failed to schedule paid up confirmation: {e}")
    
    def _process_notification_queue(self):
        """Process notifications in the queue"""
        try:
            batch_size = self.automation_settings.get('batch_size', 10)
            processed = 0
            
            while processed < batch_size and not self.notification_queue.empty():
                try:
                    notification_event = self.notification_queue.get_nowait()
                    self._process_notification_event(notification_event)
                    processed += 1
                except Empty:
                    break
                except Exception as e:
                    print(f"[ERROR] Failed to process notification event: {e}")
                    
        except Exception as e:
            print(f"[ERROR] Failed to process notification queue: {e}")
    
    def _process_notification_event(self, event: NotificationEvent):
        """Process a single notification event"""
        # This would integrate with the existing notification system
        print(f"[INFO] Processing notification event: {event.notification_type} for {event.tenant_id}")
    
    def _execute_notification_action(self, action):
        """Execute a notification action using the notification system (non-blocking)"""
        if not self.notification_system:
            print("[WARNING] No notification system available")
            return
        
        # Execute notification in separate thread to prevent blocking
        notification_thread = threading.Thread(
            target=self._send_notification_async,
            args=(action,),
            daemon=True
        )
        notification_thread.start()
    
    def _send_notification_async(self, action):
        """Send notification asynchronously"""
        try:
            action_data = action['action_data']
            tenant_id = action.get('tenant_id')
            
            # Use the comprehensive notification system
            if self.notification_system:
                results = self.notification_system.send_comprehensive_notification(
                    title=action_data['title'],
                    message=action_data['message'],
                    tenant_id=tenant_id,
                    send_methods=action_data.get('send_methods', ['system']),
                    urgency=action_data.get('urgency', 'normal')
                )
            else:
                print(f"[WARNING] No notification system available for action: {action.get('action_id', 'unknown')}")
                results = {'system': False}
            
            # Mark as executed
            success = any(results.values())
            execution_result = {
                'results': results,
                'success': success,
                'executed_at': datetime.now().isoformat()
            }
            
            if self.action_queue:
                self.action_queue.execute_action(action['action_id'], execution_result)
            else:
                print(f"[WARNING] No action queue available to mark action as executed: {action.get('action_id', 'unknown')}")
            
            if success:
                print(f"[INFO] Notification executed successfully: {action['action_id']}")
            else:
                print(f"[WARNING] Notification execution failed: {action['action_id']}")
                
        except Exception as e:
            print(f"[ERROR] Failed to execute notification action: {e}")
    
    def add_custom_notification(self, tenant_id: str, notification_type: str, 
                              scheduled_date: str, data: Dict[str, Any], 
                              priority: NotificationPriority = NotificationPriority.NORMAL):
        """Add a custom notification to the queue"""
        try:
            event = NotificationEvent(
                tenant_id=tenant_id,
                notification_type=notification_type,
                scheduled_date=scheduled_date,
                data=data,
                priority=priority.value
            )
            
            with self.queue_lock:
                self.notification_queue.put(event)
            
            print(f"[INFO] Added custom notification for {tenant_id}: {notification_type}")
            
        except Exception as e:
            print(f"[ERROR] Failed to add custom notification: {e}")
    
    def get_automation_status(self) -> Dict[str, Any]:
        """Get the current status of the automation system"""
        return {
            'running': self.is_running,
            'thread_alive': self.automation_thread.is_alive() if self.automation_thread else False,
            'check_interval': self.check_interval,
            'queue_size': self.notification_queue.qsize(),
            'processed_notifications_count': len(self.processed_notifications),
            'settings': self.automation_settings
        }
    
    def update_settings(self, new_settings: Dict[str, Any]):
        """Update automation settings"""
        try:
            self.automation_settings.update(new_settings)
            self.check_interval = self.automation_settings.get('check_interval_hours', 1) * 3600
            self.save_automation_settings()
            
            print(f"[INFO] Automation settings updated: {new_settings}")
            
        except Exception as e:
            print(f"[ERROR] Failed to update automation settings: {e}")

# Example usage
if __name__ == "__main__":
    # This would be initialized with actual rent_tracker, notification_system, and action_queue
    automation = TenantNotificationAutomation()
    
    # Start automation
    automation.start_automation()
    
    # Keep running for demo
    try:
        time.sleep(60)
    except KeyboardInterrupt:
        pass
    finally:
        automation.stop_automation()
