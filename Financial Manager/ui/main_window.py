from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QMenuBar, QMenu, QMessageBox, QDialog
from PyQt6.QtGui import QAction, QIcon
from ui.dashboard_tab import DashboardTab
from ui.financial_tracker import FinancialTracker
from ui.rent_dashboard_tab import RentDashboardTab
from ui.rent_management_tab import RentManagementTab
from ui.tenant_dashboard import TenantDashboard
from ui.comprehensive_tenant_analysis_tab import ComprehensiveTenantAnalysisTab
from ui.pos_tab import POSTab
from ui.store_settings_dialog import StoreSettingsDialog
#from ui.settings_tab import SettingsTab
from src.account import AccountManager
from ui.action_queue_dialog import ActionQueueDialog
from assets.Logger import Logger
import os
import sys

logger = Logger()

class MainWindow(QMainWindow):
    def __init__(self, username=None):
        super().__init__()
        logger.debug("MainWindow", f"Initializing MainWindow for user {username}")
        self.setWindowTitle('Financial Manager')
        # Set a reasonable default size for the window
        self.resize(1200, 800)
        self.setMinimumSize(800, 600)
        
        # Set window icon
        try:
            if getattr(sys, 'frozen', False):
                BASE_PATH = sys._MEIPASS
            else:
                BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            icon_path = os.path.join(BASE_PATH, 'resources', 'icons', 'Rent_Tracker.ico')
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
                logger.debug("MainWindow", f"Window icon set from {icon_path}")
            else:
                logger.warning("MainWindow", f"Icon file not found at {icon_path}")
        except Exception as e:
            logger.warning("MainWindow", f"Failed to set window icon: {e}")
        
        self.tabs = QTabWidget()
        self.tabs.addTab(DashboardTab(), 'Dashboard')
        
        # Financial tracker (the original comprehensive interface)
        logger.debug("MainWindow", f"Creating FinancialTracker for user: {username}")
        try:
            self.financial_tracker = FinancialTracker(username)
            logger.info("MainWindow", "FinancialTracker created successfully")
        except Exception as e:
            logger.error("MainWindow", f"Failed to create FinancialTracker: {e}")
            import traceback
            traceback.print_exc()
            # Create a placeholder widget to avoid crashes
            from PyQt6.QtWidgets import QLabel
            error_widget = QLabel("Error loading Financial Dashboard. Please check the logs.")
            error_widget.setStyleSheet("color: red; font-size: 14px;")
            self.financial_tracker = error_widget
        
        self.tabs.addTab(self.financial_tracker, 'Financial Dashboard')
        
        # Rent tabs
        self.rent_dashboard_tab = RentDashboardTab(username)
        self.rent_management_tab = RentManagementTab(self.rent_dashboard_tab.rent_tracker)
        self.tenant_dashboard = TenantDashboard(self.rent_dashboard_tab.rent_tracker)
        self.rent_dashboard_tab.set_rent_management_tab(self.rent_management_tab)
        
        # Allow rent management to refresh dashboard charts
        self.rent_management_tab.set_dashboard_tab(self.rent_dashboard_tab)
        # Connect tenant dashboard to rent management selection
        self.rent_management_tab.set_tenant_dashboard(self.tenant_dashboard)
        
        # Comprehensive Tenant Analysis tab
        self.comprehensive_analysis_tab = ComprehensiveTenantAnalysisTab(self.rent_dashboard_tab.rent_tracker)
        self.rent_management_tab.set_comprehensive_analysis_tab(self.comprehensive_analysis_tab)
        
        self.tabs.addTab(self.rent_dashboard_tab, 'Rent Dashboard')
        self.tabs.addTab(self.rent_management_tab, 'Rent Management')
        self.tabs.addTab(self.tenant_dashboard, 'Tenant Analytics')
        self.tabs.addTab(self.comprehensive_analysis_tab, 'Comprehensive Analysis')
        
        # Point of Sale tab
        logger.debug("MainWindow", "Creating POSTab")
        try:
            self.pos_tab = POSTab()
            self.tabs.addTab(self.pos_tab, 'Point of Sale')
            logger.info("MainWindow", "POSTab created successfully")
        except Exception as e:
            logger.error("MainWindow", f"Failed to create POSTab: {e}")
            import traceback
            traceback.print_exc()
            # Create a placeholder widget to avoid crashes
            from PyQt6.QtWidgets import QLabel
            error_widget = QLabel("Error loading POS System. Please check the logs.")
            error_widget.setStyleSheet("color: red; font-size: 14px;")
            self.pos_tab = error_widget
        
        #self.tabs.addTab(SettingsTab(), 'Settings')
        self.setCentralWidget(self.tabs)
        self.account_manager = AccountManager()
        self.current_user = username  # Set from login
        # Initialize rent_menu before menu bar
        self.rent_menu = None
        self.init_menu_bar()
        self.tabs.currentChanged.connect(self.on_tab_changed)
        self.rent_management_tab.tenant_viewed.connect(self.on_tenant_viewed)
        self.rent_dashboard_tab.tenant_selected.connect(self.on_dashboard_tenant_selected)
        
        # Process any due actions on startup
        self.process_startup_actions()

    def on_dashboard_tenant_selected(self, tenant):
        # Called when a tenant is selected from the dashboard
        print('[DEBUG] Tenant selected from dashboard:', tenant.name)
        self.rent_management_tab.load_tenant(tenant)
        # Switch to Rent Management tab
        for i in range(self.tabs.count()):
            if self.tabs.widget(i) is self.rent_management_tab:
                self.tabs.setCurrentIndex(i)
                break
        # Force menu update after tab switch
        self.on_tenant_viewed(True)

    def on_tenant_viewed(self, viewed):
        # Enable/disable tenant-dependent actions based on whether a tenant is loaded
        print(f'[DEBUG] on_tenant_viewed: viewed={viewed}, rent_menu_exists={self.rent_menu is not None}')
        if hasattr(self, 'tenant_dependent_actions'):
            # Always enable when a tenant is viewed, and check if we should disable
            if viewed:
                for action in self.tenant_dependent_actions:
                    action.setEnabled(True)
            else:
                # Only disable if no tenant is loaded in rent management tab
                if hasattr(self.rent_management_tab, 'selected_tenant') and self.rent_management_tab.selected_tenant:
                    for action in self.tenant_dependent_actions:
                        action.setEnabled(True)  # Keep enabled if tenant still loaded
                else:
                    for action in self.tenant_dependent_actions:
                        action.setEnabled(False)  # Disable if no tenant
            logger.debug("MainWindow", f"Tenant-dependent actions enabled: {viewed or (hasattr(self.rent_management_tab, 'selected_tenant') and self.rent_management_tab.selected_tenant)}")

    def init_menu_bar(self):
        menu_bar = self.menuBar()
        menu_bar.clear()
        
        # File menu
        file_menu = QMenu('File', self)
        file_menu.addAction(QAction('Backup & Restore', self, triggered=self.show_backup_restore_dialog))
        file_menu.addSeparator()
        file_menu.addAction(QAction('Logout', self, triggered=self.logout))
        file_menu.addAction(QAction('Exit', self, triggered=self.close))
        menu_bar.addMenu(file_menu)
        
        # Edit menu
        edit_menu = QMenu('Edit', self)
        menu_bar.addMenu(edit_menu)
        
        # Rent menu
        self.rent_menu = QMenu('Rent', self)
        edit_tenant_action = QAction('Edit Tenant Details', self, triggered=self.edit_tenant_details)
        edit_rent_action = QAction('Edit Rent Amount', self, triggered=self.edit_rent_amount)
        edit_deposit_action = QAction('Edit Deposit Amount', self, triggered=self.edit_deposit_amount)
        
        # Add separator
        self.rent_menu.addAction(edit_tenant_action)
        self.rent_menu.addAction(edit_rent_action)
        self.rent_menu.addAction(edit_deposit_action)
        self.rent_menu.addSeparator()
        
        # Payment and override actions
        add_payment_action = QAction('Add Payment', self, triggered=self.add_payment)
        add_service_credit_action = QAction('Add Service Credit', self, triggered=self.add_service_credit)
        convert_credits_action = QAction('Convert Credits', self, triggered=self.convert_credits)
        monthly_override_action = QAction('Monthly Override', self, triggered=self.monthly_override)
        yearly_override_action = QAction('Yearly Override', self, triggered=self.yearly_override)
        renew_lease_action = QAction('Renew Lease', self, triggered=self.renew_lease)
        query_system_action = QAction('Query System', self, triggered=self.query_system)
        
        self.rent_menu.addAction(add_payment_action)
        self.rent_menu.addAction(add_service_credit_action)
        self.rent_menu.addAction(convert_credits_action)
        self.rent_menu.addSeparator()
        self.rent_menu.addAction(monthly_override_action)
        self.rent_menu.addAction(yearly_override_action)
        self.rent_menu.addAction(renew_lease_action)
        self.rent_menu.addSeparator()
        self.rent_menu.addAction(query_system_action)
        self.rent_menu.addSeparator()
        
        # Import legacy data action (always enabled, doesn't require tenant selection)
        import_legacy_action = QAction('Import Legacy Data...', self, triggered=self.import_legacy_data)
        self.rent_menu.addAction(import_legacy_action)
        
        # Import backup data action (always enabled, doesn't require tenant selection)
        import_backup_action = QAction('Import Backup Data...', self, triggered=self.import_backup_data)
        self.rent_menu.addAction(import_backup_action)
        
        # Store actions that require tenant selection for later enabling/disabling
        self.tenant_dependent_actions = [
            edit_tenant_action, edit_rent_action, edit_deposit_action,
            add_payment_action, add_service_credit_action, convert_credits_action,
            monthly_override_action, yearly_override_action, renew_lease_action,
            query_system_action
        ]
        
        # Disable tenant-dependent actions by default, but keep menu enabled
        for action in self.tenant_dependent_actions:
            action.setEnabled(False)
        
        self.rent_menu.setEnabled(True)  # Always keep menu enabled
        menu_bar.addMenu(self.rent_menu)
        logger.debug("MainWindow", f"Rent menu created: {self.rent_menu is not None}")
        
        # Admin menu logic
        is_admin = self.is_admin(self.current_user)
        any_admin = self.any_admin_exists()
        admin_menu = QMenu('Admin', self)
        become_admin_action = QAction('Become Admin', self, triggered=self.become_admin)
        manage_users_action = QAction('Manage Users', self, triggered=self.manage_users)
        
        # Add scheduled actions to admin menu
        scheduled_actions_action = QAction('Action Queue', self, triggered=self.show_scheduled_actions)
        queue_control_action = QAction('Queue Control Center', self, triggered=self.show_queue_control)
        notification_manager_action = QAction('Notification Manager', self, triggered=self.show_notification_manager)
        database_sync_action = QAction('Database Sync Status', self, triggered=self.show_database_sync_status)
        set_tax_action = QAction('Set Tax Rates', self, triggered=self.show_tax_settings)
        store_settings_action = QAction('Store Settings', self, triggered=self.show_store_settings)
        
        # Only enable 'Become Admin' if user is not admin and no admin exists
        become_admin_action.setEnabled(not is_admin and not any_admin)
        # Only enable 'Manage Users' if user is admin
        manage_users_action.setEnabled(is_admin)
        # Only enable 'Action Queue' if user is admin
        scheduled_actions_action.setEnabled(is_admin)
        # Only enable 'Queue Control Center' if user is admin
        queue_control_action.setEnabled(is_admin)
        # Only enable 'Notification Manager' if user is admin
        notification_manager_action.setEnabled(is_admin)
        # Only enable 'Database Sync' if user is admin
        database_sync_action.setEnabled(is_admin)
        # Only enable 'Set Tax Rates' if user is admin
        set_tax_action.setEnabled(is_admin)
        # Only enable 'Store Settings' if user is admin
        store_settings_action.setEnabled(is_admin)
        
        admin_menu.addAction(become_admin_action)
        admin_menu.addAction(manage_users_action)
        admin_menu.addSeparator()
        admin_menu.addAction(set_tax_action)
        admin_menu.addAction(store_settings_action)
        admin_menu.addSeparator()
        admin_menu.addAction(scheduled_actions_action)
        admin_menu.addAction(queue_control_action)
        admin_menu.addAction(notification_manager_action)
        admin_menu.addAction(database_sync_action)
        menu_bar.addMenu(admin_menu)
        
        # Help menu
        help_menu = QMenu('Help', self)
        help_menu.addAction(QAction('About', self, triggered=self.show_about))
        menu_bar.addMenu(help_menu)
        
    def on_tab_changed(self, index):
        # Get current tab name
        tab_text = self.tabs.tabText(index)
        
        try:
            # Refresh charts when switching to Rent Dashboard tab
            if tab_text == 'Rent Dashboard':
                logger.debug("MainWindow", "Switching to Rent Dashboard - refreshing charts")
                self.rent_dashboard_tab.refresh_charts()
            
            # Refresh tenant dropdown when switching to Rent Management tab
            elif tab_text == 'Rent Management':
                self.rent_management_tab.refresh_tenant_dropdown()
                # Re-enable tenant-dependent actions if a tenant is currently loaded
                if hasattr(self.rent_management_tab, 'selected_tenant') and self.rent_management_tab.selected_tenant:
                    if hasattr(self, 'tenant_dependent_actions'):
                        for action in self.tenant_dependent_actions:
                            action.setEnabled(True)
            
            # Handle Financial Dashboard tab access
            elif tab_text == 'Financial Dashboard':
                logger.debug("MainWindow", "Switching to Financial Dashboard - ensuring data is loaded")
                # The FinancialTracker should already be initialized, but we can add any specific refresh logic here
                if hasattr(self.financial_tracker, 'refresh_data'):
                    logger.debug("MainWindow", "Financial Dashboard - calling refresh_data")
                    self.financial_tracker.refresh_data()
                    
        except Exception as e:
            logger.error("MainWindow", f"on_tab_changed: Error switching to tab '{tab_text}': {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Tab Switch Error", f"Error switching to {tab_text} tab: {str(e)}")

    def edit_tenant_details(self):
        """Open the tenant details editing dialog"""
        if not self.rent_management_tab or not hasattr(self.rent_management_tab, 'selected_tenant') or not self.rent_management_tab.selected_tenant:
            QMessageBox.warning(self, 'No Tenant Selected', 'Please select a tenant first in the Rent Management tab.')
            return
        
        try:
            from ui.tenant_details_dialog import TenantDetailsDialog
            tenant = self.rent_management_tab.selected_tenant
            rent_tracker = self.rent_management_tab.rent_tracker
            
            dlg = TenantDetailsDialog(self, tenant=tenant, rent_tracker=rent_tracker)
            dlg.tenant_updated.connect(self.refresh_tenant_data)
            dlg.exec()
            
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to open tenant details dialog: {str(e)}')
            logger.error("MainWindow", f"Failed to open tenant details dialog: {e}")

    def edit_rent_amount(self):
        """Use the existing rent modification dialog from rent management tab"""
        if self.rent_management_tab and hasattr(self.rent_management_tab, 'show_modify_rent_dialog'):
            self.rent_management_tab.show_modify_rent_dialog()
        else:
            QMessageBox.warning(self, 'Edit Rent', 'Please select a tenant first in the Rent Management tab.')

    def edit_deposit_amount(self):
        """Open the deposit amount editing dialog"""
        if not self.rent_management_tab or not hasattr(self.rent_management_tab, 'selected_tenant') or not self.rent_management_tab.selected_tenant:
            QMessageBox.warning(self, 'No Tenant Selected', 'Please select a tenant first in the Rent Management tab.')
            return
        
        try:
            from ui.deposit_amount_dialog import DepositAmountDialog
            tenant = self.rent_management_tab.selected_tenant
            rent_tracker = self.rent_management_tab.rent_tracker
            
            dlg = DepositAmountDialog(self, tenant=tenant, rent_tracker=rent_tracker)
            dlg.deposit_updated.connect(self.refresh_tenant_data)
            dlg.exec()
            
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to open deposit amount dialog: {str(e)}')
            logger.error("MainWindow", f"Failed to open deposit amount dialog: {e}")
    
    def refresh_tenant_data(self):
        """Refresh tenant data after updates"""
        try:
            # Refresh rent management tab
            if hasattr(self.rent_management_tab, 'refresh_tenant_display'):
                self.rent_management_tab.refresh_tenant_display()
            elif hasattr(self.rent_management_tab, 'selected_tenant') and self.rent_management_tab.selected_tenant:
                # Reload the tenant
                tenant_id = self.rent_management_tab.selected_tenant.tenant_id
                self.rent_management_tab.load_tenant_by_id(tenant_id)
            
            # Refresh rent dashboard charts
            if hasattr(self.rent_dashboard_tab, 'refresh_charts'):
                self.rent_dashboard_tab.refresh_charts()
                
        except Exception as e:
            logger.error("MainWindow", f"Failed to refresh tenant data: {e}")

    def add_payment(self):
        """Use the existing add payment dialog from rent management tab"""
        if self.rent_management_tab and hasattr(self.rent_management_tab, 'show_add_payment_dialog'):
            self.rent_management_tab.show_add_payment_dialog()
        else:
            QMessageBox.warning(self, 'Add Payment', 'Please select a tenant first in the Rent Management tab.')

    def add_service_credit(self):
        """Use the service credit dialog from rent management tab"""
        if self.rent_management_tab and hasattr(self.rent_management_tab, 'show_service_credit_dialog'):
            self.rent_management_tab.show_service_credit_dialog()
        else:
            QMessageBox.warning(self, 'Add Service Credit', 'Please select a tenant first in the Rent Management tab.')

    def convert_credits(self):
        """Show credit conversion dialog"""
        if self.rent_management_tab and hasattr(self.rent_management_tab, 'show_credit_conversion_dialog'):
            self.rent_management_tab.show_credit_conversion_dialog()
        else:
            QMessageBox.warning(self, 'Convert Credits', 'Please select a tenant first in the Rent Management tab.')

    def monthly_override(self):
        """Use the existing monthly override dialog from rent management tab"""
        if self.rent_management_tab and hasattr(self.rent_management_tab, 'show_monthly_override_dialog'):
            self.rent_management_tab.show_monthly_override_dialog()
        else:
            QMessageBox.warning(self, 'Monthly Override', 'Please select a tenant first in the Rent Management tab.')

    def yearly_override(self):
        """Use the existing yearly override dialog from rent management tab"""
        if self.rent_management_tab and hasattr(self.rent_management_tab, 'show_yearly_override_dialog'):
            self.rent_management_tab.show_yearly_override_dialog()
        else:
            QMessageBox.warning(self, 'Yearly Override', 'Please select a tenant first in the Rent Management tab.')

    def query_system(self):
        """Use the existing query dialog from rent management tab"""
        if self.rent_management_tab and hasattr(self.rent_management_tab, 'show_query_dialog'):
            self.rent_management_tab.show_query_dialog()
        else:
            QMessageBox.warning(self, 'Query System', 'Query system is not available.')

    def renew_lease(self):
        """Use the existing renew lease dialog from rent management tab"""
        if self.rent_management_tab and hasattr(self.rent_management_tab, 'show_renew_lease_dialog'):
            self.rent_management_tab.show_renew_lease_dialog()
        else:
            QMessageBox.warning(self, 'Renew Lease', 'Please select a tenant first in the Rent Management tab.')

    def logout(self):
        """Logout and return to login screen"""
        reply = QMessageBox.question(self, 'Logout', 'Are you sure you want to logout?',
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                    QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            # Clear current user
            self.current_user = None
            
            # Close the main window
            self.close()
            
            # Show login dialog again
            from ui.login import LoginDialog
            login_dialog = LoginDialog()
            result = login_dialog.exec()
            
            if result == QDialog.DialogCode.Accepted:
                # Get new username
                username = login_dialog.username_edit.text().strip()
                
                # Create new main window
                new_window = MainWindow(username)
                new_window.show()
                
                # Keep reference to prevent garbage collection
                QApplication.instance().main_window = new_window
            else:
                # If login cancelled, exit application
                QApplication.instance().quit()

    def is_admin(self, username):
        """Check if user is admin - checks both database and JSON"""
        if not username:
            return False
        
        # Try database first
        try:
            from src.account_db import AccountDatabaseManager
            db_mgr = AccountDatabaseManager()
            db_user = db_mgr.get_user_by_username(username)
            if db_user and db_user.get('is_admin') == 1:
                return True
        except Exception as e:
            logger.debug("MainWindow", f"Could not check database for admin status: {e}")
        
        # Fall back to JSON
        acc = self.account_manager.get_account(username) if username else None
        return bool(acc and acc['details'].get('role') == 'admin')

    def any_admin_exists(self):
        """Check if any admin exists - checks both database and JSON"""
        # Check database
        try:
            from src.account_db import AccountDatabaseManager
            db_mgr = AccountDatabaseManager()
            db_users = db_mgr.list_users()
            if any(u.get('is_admin') == 1 for u in db_users):
                return True
        except Exception as e:
            logger.debug("MainWindow", f"Could not check database for admin existence: {e}")
        
        # Check JSON
        return any(acc['details'].get('role') == 'admin' for acc in self.account_manager.accounts.values())

    def become_admin(self):
        """Promote current user to admin in appropriate backend"""
        if self.current_user:
            try:
                # Determine which backend the user is in
                from src.account_db import AccountDatabaseManager
                db_mgr = AccountDatabaseManager()
                db_user = db_mgr.get_user_by_username(self.current_user)
                
                if db_user:
                    # User is in database
                    db_mgr.update_user(self.current_user, is_admin=1)
                    logger.info("MainWindow", f"User {self.current_user} promoted to admin in database")
                    QMessageBox.information(self, 'Admin', 'You are now an admin.')
                else:
                    # User is in JSON (or nowhere)
                    account = self.account_manager.get_account(self.current_user)
                    if account:
                        account['details']['role'] = 'admin'
                        self.account_manager.save()
                        logger.info("MainWindow", f"User {self.current_user} promoted to admin in JSON")
                        QMessageBox.information(self, 'Admin', 'You are now an admin.')
                    else:
                        QMessageBox.critical(self, 'Admin Error', 'Account not found in either backend.')
                
                self.init_menu_bar()
            except Exception as e:
                QMessageBox.critical(self, 'Admin Error', f'Failed to become admin: {e}')
        else:
            QMessageBox.critical(self, 'Admin Error', 'No user is currently logged in.')

    def manage_users(self):
        if not self.is_admin(self.current_user):
            QMessageBox.critical(self, 'Access Denied', 'You must be an admin to manage users.')
            return
        from ui.user_management_dialog import UserManagementDialog
        dlg = UserManagementDialog(self.account_manager, self)
        dlg.exec()

    def show_about(self):
        QMessageBox.information(self, 'About', 'Financial Manager v1.0')
    
    def process_startup_actions(self):
        """Process any actions that are due when the application starts"""
        try:
            rent_tracker = self.rent_dashboard_tab.rent_tracker
            results = rent_tracker.process_due_actions()
            
            if results:
                executed_count = sum(1 for r in results if r['success'])
                failed_count = len(results) - executed_count
                
                message_parts = []
                if executed_count > 0:
                    message_parts.append(f"{executed_count} scheduled action(s) executed successfully")
                if failed_count > 0:
                    message_parts.append(f"{failed_count} action(s) failed to execute")
                
                if message_parts:
                    message = "Startup Actions:\n" + "\n".join(message_parts)
                    
                    # Show details for important actions like rent changes
                    rent_changes = [r for r in results if r['action_type'] == 'rent_change' and r['success']]
                    if rent_changes:
                        message += "\n\nRent Changes Applied:"
                        for change in rent_changes:
                            details = change['details']
                            message += f"\n• {details['tenant_name']}: ${details['old_rent']:.2f} → ${details['new_rent']:.2f}"
                    
                    # Show details for rental period changes
                    period_changes = [r for r in results if r['action_type'] == 'rental_period_change' and r['success']]
                    if period_changes:
                        message += "\n\nLease Renewals Applied:"
                        for change in period_changes:
                            details = change['details']
                            from datetime import datetime
                            start_formatted = datetime.strptime(details['new_start_date'], '%Y-%m-%d').strftime('%b %d, %Y')
                            end_formatted = datetime.strptime(details['new_end_date'], '%Y-%m-%d').strftime('%b %d, %Y')
                            message += f"\n• {details['tenant_name']}: New lease period {start_formatted} - {end_formatted}"
                    
                    # Show details for notifications sent
                    notifications_sent = [r for r in results if r['action_type'] == 'notification' and r['success']]
                    if notifications_sent:
                        message += "\n\nNotifications Sent:"
                        for notification in notifications_sent:
                            details = notification['details']
                            message += f"\n• {details['title']}"
                    
                    QMessageBox.information(self, "Scheduled Actions Processed", message)
            
            # Perform automatic cleanup of old actions (older than 90 days)
            try:
                removed_count = rent_tracker.action_queue.cleanup_old_actions(days_old=90)
                if removed_count > 0:
                    logger.info("MainWindow", f"Automatic cleanup: Removed {removed_count} old actions")
            except Exception as cleanup_error:
                logger.warning("MainWindow", f"Automatic cleanup failed: {cleanup_error}")
        
        except Exception as e:
            logger.error("MainWindow", f"Failed to process startup actions: {e}")
            # Don't show error to user unless it's critical
    
    def show_scheduled_actions(self):
        """Show the action queue dialog for system-wide scheduled actions"""
        rent_tracker = self.rent_dashboard_tab.rent_tracker
        action_queue = rent_tracker.action_queue
        dlg = ActionQueueDialog(self, action_queue=action_queue, rent_tracker=rent_tracker)
        dlg.exec()
    
    def show_queue_control(self):
        """Show the queue control center dialog"""
        rent_tracker = self.rent_dashboard_tab.rent_tracker
        action_queue = rent_tracker.action_queue
        from ui.queue_control_dialog import QueueControlDialog
        dlg = QueueControlDialog(self, action_queue=action_queue, rent_tracker=rent_tracker)
        
        # Connect queue updates to refresh other dialogs
        dlg.queue_updated.connect(self.refresh_data)
        
        dlg.exec()
    
    def refresh_data(self):
        """Refresh data in various tabs when queue is updated"""
        try:
            # Refresh rent management tab if it has monthly balance view
            if hasattr(self.rent_management_tab, 'refresh_monthly_balance_display'):
                self.rent_management_tab.refresh_monthly_balance_display()
            
            # Refresh rent dashboard charts
            if hasattr(self.rent_dashboard_tab, 'refresh_charts'):
                self.rent_dashboard_tab.refresh_charts()
                
        except Exception as e:
            logger.error("MainWindow", f"Failed to refresh data after queue update: {e}")
    
    def show_notification_manager(self):
        """Show the notification manager dialog"""
        rent_tracker = self.rent_dashboard_tab.rent_tracker
        action_queue = rent_tracker.action_queue
        from ui.notification_dialog import NotificationDialog
        dlg = NotificationDialog(self, action_queue=action_queue, rent_tracker=rent_tracker)
        dlg.exec()
    
    def show_database_sync_status(self):
        """Show the database sync status dialog"""
        try:
            rent_tracker = self.rent_dashboard_tab.rent_tracker
            from src.database_utils import DatabaseUI
            dlg = DatabaseUI.create_sync_status_dialog(rent_tracker)
            dlg.exec()
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to open database sync dialog: {e}')
    
    def show_tax_settings(self):
        """Show the tax settings dialog"""
        try:
            from ui.tax_settings_dialog import TaxSettingsDialog
            dlg = TaxSettingsDialog(self)
            dlg.exec()
        except Exception as e:
            logger.error("MainWindow", f"Failed to open tax settings dialog: {e}")
            QMessageBox.critical(self, 'Error', f'Failed to open tax settings: {e}')
    
    def show_store_settings(self):
        """Show the store settings dialog"""
        try:
            dlg = StoreSettingsDialog(self)
            dlg.exec()
        except Exception as e:
            logger.error("MainWindow", f"Failed to open store settings dialog: {e}")
            QMessageBox.critical(self, 'Error', f'Failed to open store settings: {e}')
    
    def import_legacy_data(self):
        """Show the legacy data import dialog"""
        try:
            from ui.legacy_data_import_dialog import LegacyDataImportDialog
            rent_tracker = self.rent_dashboard_tab.rent_tracker
            
            dlg = LegacyDataImportDialog(self, rent_tracker=rent_tracker, current_user_id=self.current_user)
            
            # Connect to refresh data when import is complete
            dlg.data_imported.connect(self.refresh_data)
            dlg.data_imported.connect(self.rent_management_tab.refresh_tenant_dropdown)
            
            dlg.exec()
            
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to open legacy data import dialog: {str(e)}')
            logger.error("MainWindow", f"Failed to open legacy data import dialog: {e}")
            import traceback
            traceback.print_exc()
    
    def import_backup_data(self):
        """Show the backup data import dialog"""
        try:
            from ui.backup_data_import_dialog import BackupDataImportDialog
            rent_tracker = self.rent_dashboard_tab.rent_tracker
            
            dlg = BackupDataImportDialog(self, rent_tracker=rent_tracker, current_user_id=self.current_user)
            
            # Connect to refresh data when import is complete
            dlg.data_imported.connect(self.refresh_data)
            dlg.data_imported.connect(self.rent_management_tab.refresh_tenant_dropdown)
            
            dlg.exec()
            
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to open backup data import dialog: {str(e)}')
            logger.error("MainWindow", f"Failed to open backup data import dialog: {e}")
            import traceback
            traceback.print_exc()
    
    def closeEvent(self, event):
        """Handle application close event to cleanup notification systems"""
        try:
            # Cleanup notification systems from rent tracker
            if hasattr(self, 'rent_dashboard_tab') and hasattr(self.rent_dashboard_tab, 'rent_tracker'):
                rent_tracker = self.rent_dashboard_tab.rent_tracker
                if hasattr(rent_tracker, 'cleanup'):
                    rent_tracker.cleanup()
                    logger.info("MainWindow", "Notification systems cleaned up successfully")
        except Exception as e:
            logger.warning("MainWindow", f"Error during application cleanup: {e}")
        
        # Accept the close event
        event.accept()
    
    def show_backup_restore_dialog(self):
        """Show backup and restore dialog for tenants"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox, QFileDialog, QLabel
        import json
        import os
        from datetime import datetime
        
        dialog = QDialog(self)
        dialog.setWindowTitle('Backup & Restore Tenants')
        dialog.setFixedSize(400, 150)
        
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel('Manage tenant backups')
        instructions.setStyleSheet("font-weight: bold; font-size: 12px; margin-bottom: 10px;")
        layout.addWidget(instructions)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        # Backup all tenants
        backup_all_btn = QPushButton('Backup All Tenants')
        backup_all_btn.clicked.connect(lambda: self.backup_all_tenants())
        buttons_layout.addWidget(backup_all_btn)
        
        # Restore from backup
        restore_btn = QPushButton('Restore Tenant from Backup')
        restore_btn.clicked.connect(lambda: self.restore_tenant_from_backup())
        buttons_layout.addWidget(restore_btn)
        
        # View backups folder
        view_btn = QPushButton('Open Backups Folder')
        view_btn.clicked.connect(lambda: self.open_backups_folder())
        buttons_layout.addWidget(view_btn)
        
        layout.addLayout(buttons_layout)
        dialog.setLayout(layout)
        dialog.exec()
    
    def backup_all_tenants(self):
        """Backup all tenants to a single JSON file"""
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        import json
        from datetime import datetime
        
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Backup All Tenants",
                f"all_tenants_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "JSON Files (*.json);;All Files (*)"
            )
            
            if not file_path:
                return
            
            tenants = self.rent_tracker.get_all_tenants()
            
            backup_data = {
                'backup_date': datetime.now().isoformat(),
                'backup_type': 'all_tenants',
                'tenant_count': len(tenants),
                'tenants': []
            }
            
            for tenant in tenants:
                tenant_data = {
                    'name': tenant.name,
                    'contact_info': tenant.contact_info,
                    'rent_amount': tenant.rent_amount,
                    'deposit_amount': tenant.deposit_amount,
                    'rental_period': tenant.rental_period,
                    'rent_due_date': tenant.rent_due_date,
                    'account_status': tenant.account_status,
                    'delinquency_balance': tenant.delinquency_balance,
                    'overpayment_credit': tenant.overpayment_credit,
                    'service_credit': getattr(tenant, 'service_credit', 0.0),
                    'payment_history': tenant.payment_history if hasattr(tenant, 'payment_history') else [],
                    'notes': tenant.notes
                }
                backup_data['tenants'].append(tenant_data)
            
            with open(file_path, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            QMessageBox.information(self, "Backup Successful", 
                f"Backed up {len(tenants)} tenant(s) to:\n{file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Backup Error", f"Failed to backup tenants: {str(e)}")
    
    def restore_tenant_from_backup(self):
        """Restore a tenant from a backup JSON file"""
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        import json
        
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Restore Tenant from Backup",
                "resources/tenant_backups",
                "JSON Files (*.json);;All Files (*)"
            )
            
            if not file_path:
                return
            
            with open(file_path, 'r') as f:
                backup_data = json.load(f)
            
            # Handle both single tenant and all tenants backups
            if backup_data.get('backup_type') == 'all_tenants':
                # Restore multiple tenants
                tenants_data = backup_data.get('tenants', [])
                restored_count = 0
                
                for tenant_data in tenants_data:
                    try:
                        # Check if tenant already exists
                        existing = self.rent_tracker.get_tenant_by_name(tenant_data['name'])
                        if existing:
                            reply = QMessageBox.question(self, "Tenant Exists",
                                f"Tenant '{tenant_data['name']}' already exists. Overwrite?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                            if reply != QMessageBox.StandardButton.Yes:
                                continue
                        
                        # Create and add the tenant
                        from src.tenant import Tenant
                        tenant = Tenant(
                            name=tenant_data['name'],
                            contact_info=tenant_data.get('contact_info', ''),
                            rent_amount=tenant_data.get('rent_amount', 0.0),
                            deposit_amount=tenant_data.get('deposit_amount', 0.0),
                            rental_period=tenant_data.get('rental_period'),
                            rent_due_date=tenant_data.get('rent_due_date', 1),
                            account_status=tenant_data.get('account_status', 'active'),
                            notes=tenant_data.get('notes', '')
                        )
                        
                        # Restore payment history and credits
                        tenant.payment_history = tenant_data.get('payment_history', [])
                        tenant.delinquency_balance = tenant_data.get('delinquency_balance', 0.0)
                        tenant.overpayment_credit = tenant_data.get('overpayment_credit', 0.0)
                        tenant.service_credit = tenant_data.get('service_credit', 0.0)
                        
                        # Add tenant to the tenants dictionary
                        self.rent_tracker.tenant_manager.tenants[tenant.tenant_id] = tenant
                        restored_count += 1
                    except Exception as e:
                        logger.error("MainWindow", f"Error restoring tenant {tenant_data.get('name')}: {str(e)}")
                
                self.rent_tracker.save_tenants()
                QMessageBox.information(self, "Restore Successful", 
                    f"Restored {restored_count} tenant(s) from backup.")
            else:
                # Restore single tenant
                tenant_data = backup_data.get('tenant_data', {})
                
                # Check if tenant already exists
                existing = self.rent_tracker.get_tenant_by_name(tenant_data['name'])
                if existing:
                    reply = QMessageBox.question(self, "Tenant Exists",
                        f"Tenant '{tenant_data['name']}' already exists. Overwrite?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                    if reply != QMessageBox.StandardButton.Yes:
                        return
                
                from src.tenant import Tenant
                tenant = Tenant(
                    name=tenant_data['name'],
                    contact_info=tenant_data.get('contact_info', ''),
                    rent_amount=tenant_data.get('rent_amount', 0.0),
                    deposit_amount=tenant_data.get('deposit_amount', 0.0),
                    rental_period=tenant_data.get('rental_period'),
                    rent_due_date=tenant_data.get('rent_due_date', 1),
                    account_status=tenant_data.get('account_status', 'active'),
                    notes=tenant_data.get('notes', '')
                )
                
                tenant.payment_history = tenant_data.get('payment_history', [])
                tenant.delinquency_balance = tenant_data.get('delinquency_balance', 0.0)
                tenant.overpayment_credit = tenant_data.get('overpayment_credit', 0.0)
                tenant.service_credit = tenant_data.get('service_credit', 0.0)
                
                # Add tenant to the tenants dictionary
                self.rent_tracker.tenant_manager.tenants[tenant.tenant_id] = tenant
                self.rent_tracker.save_tenants()
                
                QMessageBox.information(self, "Restore Successful", 
                    f"Tenant '{tenant_data['name']}' has been restored.")
            
            # Refresh the UI
            if hasattr(self, 'rent_tab'):
                self.rent_tab.refresh_tenant_dropdown()
                self.rent_tab.refresh_tenant_display()
            
        except Exception as e:
            QMessageBox.critical(self, "Restore Error", f"Failed to restore tenant: {str(e)}")
    
    def open_backups_folder(self):
        """Open the backups folder in file explorer"""
        import os
        import subprocess
        import platform
        
        try:
            backups_dir = os.path.abspath('resources/tenant_backups')
            os.makedirs(backups_dir, exist_ok=True)
            
            if platform.system() == 'Windows':
                os.startfile(backups_dir)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', backups_dir])
            else:  # Linux
                subprocess.run(['xdg-open', backups_dir])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open backups folder: {str(e)}")

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

