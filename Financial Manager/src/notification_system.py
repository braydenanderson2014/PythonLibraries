import os
import sys
import time
import threading
from datetime import datetime, date
from typing import Optional, Dict, Any, List
import json
from assets.Logger import Logger
logger = Logger()
try:
    from .app_paths import NOTIFICATION_STATE_FILE, SETTINGS_FILE
except ImportError:
    from app_paths import NOTIFICATION_STATE_FILE, SETTINGS_FILE

# Email imports with fallback
try:
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False
    print("[WARNING] Email libraries not available. Email notifications will not work.")

# Windows notification imports
try:
    from plyer import notification
    PLYER_AVAILABLE = True
except ImportError:
    notification = None
    PLYER_AVAILABLE = False
    print("[WARNING] plyer not installed. Windows notifications will not work.")

try:
    import win10toast
    WIN10TOAST_AVAILABLE = True
except ImportError:
    WIN10TOAST_AVAILABLE = False
    print("[INFO] win10toast not available, using plyer for notifications.")

class NotificationSystem:
    """
    Comprehensive notification system for Windows with daemon support
    Integrates with the action queue system for scheduled notifications
    """
    
    def __init__(self, action_queue=None, rent_tracker=None):
        logger.debug("NotificationSystem", f"Initializing with action_queue={bool(action_queue)}, rent_tracker={bool(rent_tracker)}")
        
        self.action_queue = action_queue
        self.rent_tracker = rent_tracker
        self.daemon_running = False
        self.daemon_thread = None
        self.check_interval = 60  # Check every 60 seconds
        
        # Notification timing control
        self.last_notification_check = None
        self.minimum_check_interval = 3600  # Minimum 1 hour between full notification checks
        self.notification_state_file = NOTIFICATION_STATE_FILE
        self._load_notification_state()
        
        # Email configuration (can be set via settings)
        self.email_config = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'email': '',  # Will be loaded from settings
            'password': '',  # Will be loaded from settings
            'enabled': False
        }
        
        # SMS configuration (placeholder for future implementation)
        self.sms_config = {
            'provider': 'twilio',  # Could support multiple providers
            'account_sid': '',
            'auth_token': '',
            'from_number': '',
            'enabled': False
        }
        
        # Load email/SMS settings
        self.load_notification_settings()

        # Initialize Windows toast notifier if available
        # NOTE: Disabled by default due to WNDPROC/WPARAM integration issues in some PyQt Windows setups
        # We'll prefer plyer or console logging to avoid crashes.
        self.toaster = None
        # if WIN10TOAST_AVAILABLE:
        #     try:
        #         self.toaster = win10toast.ToastNotifier()
        #     except Exception as e:
        #         print(f"[WARNING] Failed to initialize win10toast: {e}")
        
        logger.info("NotificationSystem", "NotificationSystem initialized successfully")
    
    def _load_notification_state(self):
        """Load the last notification check time from file"""
        try:
            if os.path.exists(self.notification_state_file):
                with open(self.notification_state_file, 'r') as f:
                    state = json.load(f)
                    self.last_notification_check = state.get('last_notification_check')
                    logger.debug("NotificationSystem", f"Loaded last notification check: {self.last_notification_check}")
        except Exception as e:
            logger.warning("NotificationSystem", f"Failed to load notification state: {str(e)}")
            self.last_notification_check = None
    
    def _save_notification_state(self):
        """Save the last notification check time to file"""
        try:
            os.makedirs(os.path.dirname(self.notification_state_file), exist_ok=True)
            state = {
                'last_notification_check': self.last_notification_check
            }
            with open(self.notification_state_file, 'w') as f:
                json.dump(state, f, indent=2)
            logger.debug("NotificationSystem", f"Saved notification state: last_check={self.last_notification_check}")
        except Exception as e:
            logger.warning("NotificationSystem", f"Failed to save notification state: {str(e)}")
    
    def _should_check_notifications(self):
        """Check if enough time has passed since last notification check"""
        if not self.last_notification_check:
            logger.debug("NotificationSystem", "No previous notification check, proceeding")
            return True
        
        try:
            last_check = datetime.fromisoformat(self.last_notification_check)
            now = datetime.now()
            time_since_last = (now - last_check).total_seconds()
            
            should_check = time_since_last >= self.minimum_check_interval
            if not should_check:
                remaining = self.minimum_check_interval - time_since_last
                logger.debug("NotificationSystem", f"Skipping check - {remaining/60:.1f} minutes remaining")
            
            return should_check
        except Exception as e:
            logger.warning("NotificationSystem", f"Error checking notification timing: {str(e)}")
            return True
    
    def load_notification_settings(self):
        """Load email and SMS settings from configuration"""
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r') as f:
                    settings = json.load(f)
                    
                email_settings = settings.get('email_notifications', {})
                self.email_config.update(email_settings)
                
                sms_settings = settings.get('sms_notifications', {})
                self.sms_config.update(sms_settings)
                
                logger.info("NotificationSystem", f"Settings loaded - Email: {self.email_config['enabled']}, SMS: {self.sms_config['enabled']}")
                
                # Provide helpful configuration status
                if not self.email_config['enabled']:
                    logger.debug("NotificationSystem", "Email notifications disabled in settings")
                elif not self.email_config['email']:
                    logger.debug("NotificationSystem", "Email enabled but no email address configured")
                elif not self.email_config['password']:
                    logger.debug("NotificationSystem", "Email enabled but no password configured")
                else:
                    logger.info("NotificationSystem", f"Email configured for: {self.email_config['email']}")
                    
            else:
                logger.debug("NotificationSystem", "Settings file not found, using defaults")
                
        except Exception as e:
            logger.warning("NotificationSystem", f"Failed to load notification settings: {str(e)}")
            
    def get_email_setup_status(self) -> Dict[str, Any]:
        """Get detailed status of email configuration"""
        status = {
            'email_libraries_available': EMAIL_AVAILABLE,
            'email_enabled': self.email_config['enabled'],
            'email_configured': bool(self.email_config['email']),
            'password_configured': bool(self.email_config['password']),
            'smtp_server': self.email_config['smtp_server'],
            'smtp_port': self.email_config['smtp_port'],
            'ready_to_send': (
                EMAIL_AVAILABLE and 
                self.email_config['enabled'] and 
                self.email_config['email'] and 
                self.email_config['password']
            )
        }
        logger.debug("NotificationSystem", f"Email setup status: ready={status['ready_to_send']}, libs={EMAIL_AVAILABLE}")
        return status
        
    def enable_email_notifications(self) -> bool:
        """Enable email notifications by updating settings"""
        try:
            logger.debug("NotificationSystem", "Enabling email notifications")
            self.email_config['enabled'] = True
            
            # Save to settings file
            settings = {}
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r') as f:
                    settings = json.load(f)
            
            if 'email_notifications' not in settings:
                settings['email_notifications'] = self.email_config
            else:
                settings['email_notifications']['enabled'] = True
            
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(settings, f, indent=2)
            
            logger.info("NotificationSystem", "Email notifications enabled successfully")
            return True
            
        except Exception as e:
            logger.error("NotificationSystem", f"Failed to enable email notifications: {str(e)}")
            return False
    
    def disable_email_notifications(self) -> bool:
        """Disable email notifications by updating settings"""
        try:
            logger.debug("NotificationSystem", "Disabling email notifications")
            self.email_config['enabled'] = False
            
            # Save to settings file
            settings = {}
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r') as f:
                    settings = json.load(f)
            
            if 'email_notifications' not in settings:
                settings['email_notifications'] = self.email_config
            else:
                settings['email_notifications']['enabled'] = False
            
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(settings, f, indent=2)
            
            logger.info("NotificationSystem", "Email notifications disabled successfully")
            return True
            
        except Exception as e:
            logger.error("NotificationSystem", f"Failed to disable email notifications: {str(e)}")
            return False
        
    def configure_email(self, email: str, password: str, smtp_server: str = "smtp.gmail.com", 
                       smtp_port: int = 587, enabled: bool = True) -> bool:
        """Configure email settings programmatically"""
        try:
            logger.debug("NotificationSystem", f"Configuring email for {email}")
            self.email_config.update({
                'email': email,
                'password': password,
                'smtp_server': smtp_server,
                'smtp_port': smtp_port,
                'enabled': enabled
            })
            
            # Save to settings file
            settings = {}
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r') as f:
                    settings = json.load(f)
            
            settings['email_notifications'] = self.email_config
            
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(settings, f, indent=2)
            
            logger.info("NotificationSystem", f"Email configuration saved for: {email}")
            return True
            
        except Exception as e:
            logger.error("NotificationSystem", f"Failed to configure email: {str(e)}")
            return False
    
    def send_comprehensive_notification(self, title: str, message: str, tenant_id: Optional[str] = None,
                                      send_methods: Optional[List[str]] = None, urgency: str = "normal",
                                      icon_path: Optional[str] = None) -> Dict[str, bool]:
        """
        Send notification via multiple methods (system, email, SMS)
        
        Args:
            title: Notification title
            message: Notification message
            tenant_id: ID of tenant to send to (for email/SMS)
            send_methods: List of methods ['system', 'email', 'sms']
            urgency: Urgency level
            icon_path: Path to icon file
            
        Returns:
            dict: Results for each send method {method: success}
        """
        if send_methods is None:
            send_methods = ['system']
        
        logger.debug("NotificationSystem", f"Sending comprehensive notification: {title} via {send_methods}")
        results = {}
        
        # Get tenant contact info if tenant_id provided
        tenant_contact = self.get_tenant_contact_info(tenant_id) if tenant_id else {}
        
        # Send system notification
        if 'system' in send_methods:
            results['system'] = self.send_notification(title, message, icon_path, urgency=urgency)
        
        # Send email notification
        if 'email' in send_methods:
            email = tenant_contact.get('email')
            if email:
                results['email'] = self.send_email_notification(email, title, message)
            else:
                results['email'] = False
                logger.warning("NotificationSystem", f"No email for tenant {tenant_id}")
        
        # Send SMS notification
        if 'sms' in send_methods:
            phone = tenant_contact.get('phone')
            if phone:
                results['sms'] = self.send_sms_notification(phone, title, message)
            else:
                results['sms'] = False
                logger.warning("NotificationSystem", f"No phone for tenant {tenant_id}")
        
        # Log summary
        successful = [k for k, v in results.items() if v]
        logger.info("NotificationSystem", f"Comprehensive notification completed: {successful} succeeded")
        return results
    
    def get_tenant_contact_info(self, tenant_id: str) -> Dict[str, str]:
        """Get tenant contact information"""
        if not self.rent_tracker or not tenant_id:
            logger.debug("NotificationSystem", f"Cannot get contact: rent_tracker={bool(self.rent_tracker)}, tenant_id={tenant_id}")
            return {}
        
        try:
            tenant = self.rent_tracker.tenant_manager.get_tenant(tenant_id)
            if not tenant:
                logger.warning("NotificationSystem", f"Tenant not found: {tenant_id}")
                return {}
            
            contact_info = getattr(tenant, 'contact_info', {})
            if isinstance(contact_info, dict):
                info = {
                    'email': contact_info.get('email', ''),
                    'phone': contact_info.get('phone', ''),
                    'contact': contact_info.get('contact', '')  # Legacy field
                }
                logger.debug("NotificationSystem", f"Retrieved contact info for tenant {tenant_id}")
                return info
            else:
                # Legacy string contact field
                return {'contact': str(contact_info)}
                
        except Exception as e:
            logger.error("NotificationSystem", f"Failed to get tenant contact info: {str(e)}")
            return {}
    
    def send_email_notification(self, email: str, title: str, message: str) -> bool:
        """Send email notification"""
        if not EMAIL_AVAILABLE:
            logger.warning("NotificationSystem", "Email libraries not available")
            return False
            
        if not self.email_config['enabled'] or not self.email_config['email']:
            logger.warning("NotificationSystem", "Email notifications not configured")
            return False
        
        try:
            logger.debug("NotificationSystem", f"Sending email to {email}: {title}")
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email_config['email']
            msg['To'] = email
            msg['Subject'] = title
            
            # Add body
            body = f"""
            Financial Manager Notification
            
            {title}
            
            {message}
            
            ---
            This is an automated message from Financial Manager.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['email'], self.email_config['password'])
            text = msg.as_string()
            server.sendmail(self.email_config['email'], email, text)
            server.quit()
            
            logger.info("NotificationSystem", f"Email sent to {email}: {title}")
            return True
            
        except Exception as e:
            logger.error("NotificationSystem", f"Failed to send email to {email}: {str(e)}")
            return False
    
    def send_sms_notification(self, phone: str, title: str, message: str) -> bool:
        """Send SMS notification (placeholder implementation)"""
        if not self.sms_config['enabled']:
            logger.warning("NotificationSystem", "SMS notifications not configured")
            return False
        
        try:
            logger.debug("NotificationSystem", f"Sending SMS to {phone}: {title}")
            # This is a placeholder - would need actual SMS service integration
            # Examples: Twilio, AWS SNS, etc.
            
            # For now, just simulate SMS sending
            sms_message = f"{title}: {message}"
            logger.info("NotificationSystem", f"SMS simulation - To {phone}: {sms_message}")
            
            # In a real implementation, this would integrate with SMS provider:
            # from twilio.rest import Client
            # client = Client(self.sms_config['account_sid'], self.sms_config['auth_token'])
            # message = client.messages.create(
            #     body=sms_message,
            #     from_=self.sms_config['from_number'],
            #     to=phone
            # )
            
            return True  # Simulated success
            
        except Exception as e:
            logger.error("NotificationSystem", f"Failed to send SMS to {phone}: {str(e)}")
            return False
    
    def send_notification(self, title: str, message: str, icon_path: Optional[str] = None, 
                         duration: int = 10, urgency: str = "normal") -> bool:
        """
        Send a Windows notification
        
        Args:
            title: Notification title
            message: Notification message
            icon_path: Path to icon file (optional)
            duration: Duration in seconds
            urgency: Urgency level (low, normal, critical)
            
        Returns:
            bool: True if notification was sent successfully
        """
        try:
            logger.debug("NotificationSystem", f"Sending notification: {title} (urgency={urgency})")
            # Try win10toast first (better Windows integration)
            if self.toaster:
                try:
                    # Use direct call without threading to avoid Windows integration issues
                    def send_toast():
                        try:
                            if self.toaster:
                                self.toaster.show_toast(
                                    title=title,
                                    msg=message,
                                    icon_path=icon_path,
                                    duration=duration,
                                    threaded=False
                                )
                        except AttributeError as e:
                            if 'classAtom' in str(e):
                                logger.warning("NotificationSystem", f"win10toast Windows error: {str(e)}")
                                # Fall back to plyer immediately
                                raise Exception("win10toast Windows integration failed")
                            else:
                                raise
                        except Exception as e:
                            logger.warning("NotificationSystem", f"win10toast error: {str(e)}")
                            raise
                    
                    # Try direct call first, then threading if needed
                    try:
                        send_toast()
                        logger.info("NotificationSystem", f"Notification sent via win10toast: {title}")
                        return True
                    except:
                        # If direct call fails, try threading with timeout
                        toast_thread = threading.Thread(target=send_toast, daemon=True)
                        toast_thread.start()
                        toast_thread.join(timeout=1)  # Shorter timeout
                        logger.info("NotificationSystem", f"Notification sent via win10toast (threaded): {title}")
                        return True
                    
                except Exception as e:
                    logger.warning("NotificationSystem", f"win10toast failed: {str(e)}, falling back to plyer")
                    # Disable win10toast for this session if it keeps failing
                    self.toaster = None
            
            # Fallback to plyer
            if PLYER_AVAILABLE and notification:
                try:
                    # Map urgency to plyer timeout
                    timeout_map = {"low": 5, "normal": 10, "critical": 15}
                    timeout = timeout_map.get(urgency, 10)
                    
                    # Explicit None check for type safety
                    if notification is not None:
                        notification.notify(  # type: ignore
                            title=title,
                            message=message,
                            app_icon=icon_path,
                            timeout=timeout
                        )
                        logger.info("NotificationSystem", f"Notification sent via plyer: {title}")
                        return True
                except Exception as e:
                    logger.warning("NotificationSystem", f"plyer failed: {str(e)}")
            
            # If no notification libraries available or all failed, log to console
            logger.info("NotificationSystem", f"Notification (fallback): {title}: {message}")
            return True
            
        except Exception as e:
            logger.error("NotificationSystem", f"Failed to send notification: {str(e)}")
            return False
    
    def queue_notification(self, title: str, message: str, scheduled_date: str,
                          tenant_id: Optional[str] = None, urgency: str = "normal", 
                          icon_path: Optional[str] = None, notes: str = "") -> str:
        """
        Queue a notification for future delivery
        
        Args:
            title: Notification title
            message: Notification message
            scheduled_date: Date to send notification (YYYY-MM-DD)
            tenant_id: Optional tenant ID for tenant-specific notifications
            urgency: Urgency level (low, normal, critical)
            icon_path: Path to icon file
            notes: Optional notes about the notification
            
        Returns:
            action_id: Unique identifier for the queued notification
        """
        if not self.action_queue:
            raise Exception("Action queue not initialized")
        
        action_data = {
            'title': title,
            'message': message,
            'urgency': urgency,
            'icon_path': icon_path,
            'notes': notes,
            'notification_type': 'scheduled'
        }
        
        description = f"Send notification: {title}"
        if tenant_id:
            description += f" (for tenant {tenant_id})"
        
        return self.action_queue.add_action(
            action_type='notification',
            scheduled_date=scheduled_date,
            tenant_id=tenant_id or 'system',
            action_data=action_data,
            description=description
        )
    
    def send_test_notification(self, urgency: str = "normal") -> bool:
        """
        Send a test notification to verify the system is working
        
        Args:
            urgency: Test urgency level
            
        Returns:
            bool: True if test was successful
        """
        current_time = datetime.now().strftime("%H:%M:%S")
        title = "Financial Manager - Test Notification"
        message = f"Test notification sent at {current_time}. System is working correctly!"
        
        return self.send_notification(
            title=title,
            message=message,
            urgency=urgency
        )
    
    def test_email_functionality(self, test_email: Optional[str] = None) -> Dict[str, Any]:
        """
        Test email functionality and return detailed status
        
        Args:
            test_email: Optional email address to send test to (defaults to configured email)
            
        Returns:
            dict: Detailed test results
        """
        status = self.get_email_setup_status()
        
        test_results = {
            'email_libraries_available': status['email_libraries_available'],
            'email_enabled': status['email_enabled'],
            'email_configured': status['email_configured'],
            'password_configured': status['password_configured'],
            'smtp_connection_test': False,
            'test_email_sent': False,
            'error_messages': []
        }
        
        # Check basic configuration
        if not status['email_libraries_available']:
            test_results['error_messages'].append("Email libraries not available")
            return test_results
            
        if not status['email_enabled']:
            test_results['error_messages'].append("Email notifications are disabled in settings")
            return test_results
            
        if not status['email_configured']:
            test_results['error_messages'].append("No email address configured")
            return test_results
            
        if not status['password_configured']:
            test_results['error_messages'].append("No password/app password configured")
            return test_results
        
        # Test SMTP connection
        try:
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['email'], self.email_config['password'])
            server.quit()
            
            test_results['smtp_connection_test'] = True
            print("[SUCCESS] SMTP connection test passed")
            
        except Exception as e:
            test_results['error_messages'].append(f"SMTP connection failed: {str(e)}")
            print(f"[ERROR] SMTP connection test failed: {e}")
            return test_results
        
        # Send test email
        try:
            target_email = test_email or self.email_config['email']
            
            test_title = "Financial Manager - Email Test"
            test_message = f"""
            This is a test email from Financial Manager.
            
            Email functionality is working correctly!
            
            Configuration Details:
            - SMTP Server: {self.email_config['smtp_server']}:{self.email_config['smtp_port']}
            - From Email: {self.email_config['email']}
            - Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            If you received this email, your notification system is configured properly.
            """
            
            success = self.send_email_notification(target_email, test_title, test_message)
            test_results['test_email_sent'] = success
            
            if success:
                print(f"[SUCCESS] Test email sent to {target_email}")
            else:
                test_results['error_messages'].append("Failed to send test email")
                
        except Exception as e:
            test_results['error_messages'].append(f"Test email failed: {str(e)}")
            print(f"[ERROR] Test email failed: {e}")
        
        return test_results
    
    def create_reminder_notification(self, reminder_type: str, tenant_name: Optional[str] = None,
                                   amount: Optional[float] = None, due_date: Optional[str] = None) -> Dict[str, str]:
        """
        Create predefined notification templates for common reminders
        
        Args:
            reminder_type: Type of reminder (rent_due, lease_expiry, payment_overdue, etc.)
            tenant_name: Name of the tenant
            amount: Amount involved (for payment reminders)
            due_date: Due date for the reminder
            
        Returns:
            dict: Title and message for the notification
        """
        templates = {
            'rent_due': {
                'title': f"Rent Due Reminder - {tenant_name}",
                'message': f"Rent payment of ${amount:.2f} is due on {due_date} for {tenant_name}."
            },
            'lease_expiry': {
                'title': f"Lease Expiry Warning - {tenant_name}",
                'message': f"Lease for {tenant_name} expires on {due_date}. Consider renewal discussions."
            },
            'payment_overdue': {
                'title': f"Overdue Payment - {tenant_name}",
                'message': f"Payment of ${amount:.2f} from {tenant_name} is overdue (due: {due_date})."
            },
            'maintenance_reminder': {
                'title': f"Maintenance Reminder - {tenant_name}",
                'message': f"Scheduled maintenance reminder for {tenant_name} on {due_date}."
            },
            'lease_renewal': {
                'title': f"Lease Renewal Applied - {tenant_name}",
                'message': f"Lease renewal for {tenant_name} has been automatically applied."
            },
            'rent_change': {
                'title': f"Rent Change Applied - {tenant_name}",
                'message': f"Rent change for {tenant_name} has been applied. New amount: ${amount:.2f}."
            }
        }
        
        template = templates.get(reminder_type, {
            'title': f"Financial Manager Reminder - {tenant_name}",
            'message': f"Reminder for {tenant_name}: Please check the system for details."
        })
        
        return template
    
    def start_daemon(self):
        """Start the notification daemon in a background thread"""
        if self.daemon_running:
            logger.debug("NotificationSystem", "Daemon is already running")
            return
        
        if not self.action_queue:
            logger.error("NotificationSystem", "Cannot start daemon: Action queue not initialized")
            return
        
        self.daemon_running = True
        self.daemon_thread = threading.Thread(target=self._daemon_loop, daemon=True)
        self.daemon_thread.start()
        logger.info("NotificationSystem", f"Notification daemon started (check interval: {self.check_interval}s)")
    
    def stop_daemon(self):
        """Stop the notification daemon"""
        if not self.daemon_running:
            logger.debug("NotificationSystem", "Daemon is not running")
            return
        
        self.daemon_running = False
        if self.daemon_thread:
            self.daemon_thread.join(timeout=5)
        logger.info("NotificationSystem", "Notification daemon stopped")
    
    def _daemon_loop(self):
        """Main daemon loop that checks for due notifications"""
        logger.info("NotificationSystem", "Notification daemon loop started")
        
        while self.daemon_running:
            try:
                # Check if enough time has passed since last notification check
                if not self._should_check_notifications():
                    # Sleep for the check interval and continue
                    time.sleep(self.check_interval)
                    continue
                
                # Update last notification check time
                self.last_notification_check = datetime.now().isoformat()
                self._save_notification_state()
                
                # Check for due notification actions
                current_date = date.today().strftime('%Y-%m-%d')
                due_actions = self.action_queue.get_due_actions(current_date) if self.action_queue else []
                logger.debug("NotificationSystem", f"Found {len(due_actions)} due actions for {current_date}")
                
                # Process notification actions
                notification_actions = [
                    action for action in due_actions 
                    if action['action_type'] == 'notification'
                ]
                
                for action in notification_actions:
                    try:
                        self._execute_notification_action(action)
                    except Exception as e:
                        logger.error("NotificationSystem", f"Failed to execute action {action['action_id']}: {str(e)}")
                
                # Sleep for the check interval
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error("NotificationSystem", f"Daemon loop error: {str(e)}")
                time.sleep(30)  # Wait before retrying
    
    def _execute_notification_action(self, action: Dict[str, Any]):
        """Execute a notification action from the queue"""
        action_data = action['action_data']
        
        title = action_data['title']
        message = action_data['message']
        urgency = action_data.get('urgency', 'normal')
        icon_path = action_data.get('icon_path')
        send_methods = action_data.get('send_methods', ['system'])
        tenant_id = action.get('tenant_id')
        
        logger.debug("NotificationSystem", f"Executing notification action: {action['action_id']}")
        
        # Send the notification via specified methods
        results = self.send_comprehensive_notification(
            title=title,
            message=message,
            tenant_id=str(tenant_id) if tenant_id is not None else None,
            send_methods=send_methods,
            urgency=urgency,
            icon_path=icon_path
        )
        
        # Check if any method succeeded
        success = any(results.values())
        
        # Mark the action as executed
        execution_result = {
            'title': title,
            'message': message,
            'urgency': urgency,
            'send_methods': send_methods,
            'results': results,
            'success': success,
            'sent_at': datetime.now().isoformat()
        }
        
        if self.action_queue:
            self.action_queue.execute_action(action['action_id'], execution_result)
        
        if success:
            successful_methods = [method for method, result in results.items() if result]
            logger.info("NotificationSystem", f"Action executed: {action['action_id']} via {successful_methods}")
        else:
            logger.warning("NotificationSystem", f"Action executed with failures: {action['action_id']}")
    
    def get_daemon_status(self) -> Dict[str, Any]:
        """Get the current status of the notification daemon"""
        return {
            'running': self.daemon_running,
            'check_interval': self.check_interval,
            'thread_alive': self.daemon_thread.is_alive() if self.daemon_thread else False,
            'plyer_available': PLYER_AVAILABLE,
            'win10toast_available': WIN10TOAST_AVAILABLE,
            'toaster_initialized': self.toaster is not None
        }

# Example usage and testing
if __name__ == "__main__":
    # Test the notification system
    notification_system = NotificationSystem()
    
    print("Testing notification system...")
    
    # Test basic notification
    notification_system.send_test_notification()
    
    # Test different urgency levels
    notification_system.send_notification(
        title="Low Priority Test",
        message="This is a low priority notification",
        urgency="low"
    )
    
    notification_system.send_notification(
        title="Critical Test",
        message="This is a critical notification",
        urgency="critical"
    )