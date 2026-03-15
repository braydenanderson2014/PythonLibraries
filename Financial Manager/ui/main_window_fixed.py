from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QMenuBar, QMenu, QMessageBox, QDialog
from PyQt6.QtGui import QAction
from ui.dashboard_tab import DashboardTab
from ui.finances_tab import FinancesTab
from ui.rent_dashboard_tab import RentDashboardTab
from ui.rent_management_tab import RentManagementTab
#from ui.settings_tab import SettingsTab
from src.account import AccountManager

class MainWindow(QMainWindow):
    def __init__(self, username=None):
        super().__init__()
        self.setWindowTitle('Financial Manager')
        # Set a reasonable default size for the window
        self.resize(1200, 800)
        self.setMinimumSize(800, 600)
        self.tabs = QTabWidget()
        self.tabs.addTab(DashboardTab(), 'Dashboard')
        self.tabs.addTab(FinancesTab(), 'Finances')
        self.rent_dashboard_tab = RentDashboardTab()
        self.rent_management_tab = RentManagementTab(self.rent_dashboard_tab.rent_tracker)
        self.rent_dashboard_tab.set_rent_management_tab(self.rent_management_tab)
        self.tabs.addTab(self.rent_dashboard_tab, 'Rent Dashboard')
        self.tabs.addTab(self.rent_management_tab, 'Rent Management')
        #self.tabs.addTab(SettingsTab(), 'Settings')
        self.setCentralWidget(self.tabs)
        self.account_manager = AccountManager()
        self.current_user = username  # Set from login
        self.init_menu_bar()
        # Track Rent menu for enabling/disabling
        self.rent_menu = None
        self.tabs.currentChanged.connect(self.on_tab_changed)
        self.rent_management_tab.tenant_viewed.connect(self.on_tenant_viewed)
        self.rent_dashboard_tab.tenant_selected.connect(self.on_dashboard_tenant_selected)

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
        # Enable Rent menu only if viewing a tenant and Rent Management tab is active
        tab_text = self.tabs.tabText(self.tabs.currentIndex())
        should_enable = viewed and tab_text == 'Rent Management'
        print(f'[DEBUG] on_tenant_viewed: viewed={viewed}, tab={tab_text}, should_enable={should_enable}, rent_menu_exists={self.rent_menu is not None}')
        if self.rent_menu:
            print(f'[DEBUG] Rent menu enabled before: {self.rent_menu.isEnabled()}')
            self.rent_menu.setEnabled(should_enable)
            print(f'[DEBUG] Rent menu enabled after: {self.rent_menu.isEnabled()}')

    def init_menu_bar(self):
        menu_bar = self.menuBar()
        menu_bar.clear()
        
        # File menu
        file_menu = QMenu('File', self)
        file_menu.addAction(QAction('Logout', self, triggered=self.logout))
        file_menu.addAction(QAction('Exit', self, triggered=self.close))
        # Test action to confirm menu bar visibility
        file_menu.addAction(QAction('Test Menu', self, triggered=lambda: QMessageBox.information(self, 'Test', 'Menu bar is visible!')))
        menu_bar.addMenu(file_menu)
        
        # Edit menu
        edit_menu = QMenu('Edit', self)
        menu_bar.addMenu(edit_menu)
        
        # Rent menu
        self.rent_menu = QMenu('Rent', self)
        edit_tenant_action = QAction('Edit Tenant Details', self, triggered=self.edit_tenant_details)
        edit_rent_action = QAction('Edit Rent Amount', self, triggered=self.edit_rent_amount)
        edit_deposit_action = QAction('Edit Deposit Amount', self, triggered=self.edit_deposit_amount)
        self.rent_menu.addAction(edit_tenant_action)
        self.rent_menu.addAction(edit_rent_action)
        self.rent_menu.addAction(edit_deposit_action)
        self.rent_menu.setEnabled(False)  # Disabled by default
        menu_bar.addMenu(self.rent_menu)
        
        # Admin menu logic
        is_admin = self.is_admin(self.current_user)
        any_admin = self.any_admin_exists()
        admin_menu = QMenu('Admin', self)
        become_admin_action = QAction('Become Admin', self, triggered=self.become_admin)
        manage_users_action = QAction('Manage Users', self, triggered=self.manage_users)
        # Only enable 'Become Admin' if user is not admin and no admin exists
        become_admin_action.setEnabled(not is_admin and not any_admin)
        # Only enable 'Manage Users' if user is admin
        manage_users_action.setEnabled(is_admin)
        admin_menu.addAction(become_admin_action)
        admin_menu.addAction(manage_users_action)
        menu_bar.addMenu(admin_menu)
        
        # Help menu
        help_menu = QMenu('Help', self)
        help_menu.addAction(QAction('About', self, triggered=self.show_about))
        menu_bar.addMenu(help_menu)
        
    def on_tab_changed(self, index):
        # When switching away from Rent Management, disable the Rent menu
        tab_text = self.tabs.tabText(index)
        if self.rent_menu and tab_text != 'Rent Management':
            self.rent_menu.setEnabled(False)

    def edit_tenant_details(self):
        QMessageBox.information(self, 'Edit Tenant', 'Edit Tenant Details dialog would appear here.')

    def edit_rent_amount(self):
        QMessageBox.information(self, 'Edit Rent', 'Edit Rent Amount dialog would appear here.')

    def edit_deposit_amount(self):
        QMessageBox.information(self, 'Edit Deposit', 'Edit Deposit Amount dialog would appear here.')

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
        acc = self.account_manager.get_account(username) if username else None
        return bool(acc and acc['details'].get('role') == 'admin')

    def any_admin_exists(self):
        return any(acc['details'].get('role') == 'admin' for acc in self.account_manager.accounts.values())

    def become_admin(self):
        # Logic to promote current user to admin
        if self.current_user:
            try:
                account = self.account_manager.get_account(self.current_user)
                if account:
                    account['details']['role'] = 'admin'
                    self.account_manager.save()  # Save to accounts.json
                    QMessageBox.information(self, 'Admin', 'You are now an admin.')
                    self.init_menu_bar()
                else:
                    QMessageBox.critical(self, 'Admin Error', 'Account not found.')
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

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
