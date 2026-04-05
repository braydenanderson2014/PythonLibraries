from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QListWidget, QHBoxLayout, QMessageBox, QListWidgetItem, QCheckBox, QFormLayout, QLineEdit, QWidget, QScrollArea, QListWidgetItem as ListItem, QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
import urllib.request
from src.account import AccountManager
from src.account_db import AccountDatabaseManager
from src.rent_web_server_runner import UnifiedApiAccountManager
from src.rent_api_auth import generate_totp_secret, build_totp_uri, build_totp_qr_url
from src.tenant import TenantManager
from assets.Logger import Logger

logger = Logger()

class UserManagementDialog(QDialog):
    def __init__(self, account_manager, parent=None):
        super().__init__(parent)
        logger.debug("UserManagementDialog", "Initializing UserManagementDialog")
        self.setWindowTitle('User Management')
        self.setMinimumSize(500, 400)
        self.account_manager = account_manager
        self.db_manager = AccountDatabaseManager()
        
        layout = QVBoxLayout()
        
        # User list
        layout.addWidget(QLabel('Users:'))
        self.user_list = QListWidget()
        self.user_list.itemSelectionChanged.connect(self.on_user_selected)
        self.refresh_users()
        layout.addWidget(self.user_list)
        
        # Button layout
        btn_layout = QHBoxLayout()
        add_btn = QPushButton('Add User')
        edit_btn = QPushButton('Edit User')
        delete_btn = QPushButton('Delete User')
        assign_tenants_btn = QPushButton('Assign Tenants')
        
        add_btn.clicked.connect(self.add_user)
        edit_btn.clicked.connect(self.edit_user)
        delete_btn.clicked.connect(self.delete_user)
        assign_tenants_btn.clicked.connect(self.assign_tenants)
        
        self.edit_btn = edit_btn
        self.delete_btn = delete_btn
        self.assign_tenants_btn = assign_tenants_btn
        
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(delete_btn)
        btn_layout.addWidget(assign_tenants_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        self.on_user_selected()  # Disable edit/delete initially

    def refresh_users(self):
        """Refresh user list from both database and JSON backends"""
        self.user_list.clear()
        users_dict = {}  # Map username -> (source, is_admin, is_tenant)
        
        # Get users from database
        try:
            db_users = self.db_manager.list_users()
            for user in db_users:
                username = user.get('username')
                is_admin = user.get('is_admin') == 1
                details = user.get('details') or {}
                if not isinstance(details, dict):
                    details = {}
                is_tenant = bool(details.get('tenant_account', details.get('role') == 'tenant'))
                users_dict[username] = ('database', is_admin, is_tenant)
        except Exception as e:
            logger.warning("UserManagementDialog", f"Could not load database users: {e}")
        
        # Get users from JSON (in case they're not yet migrated)
        try:
            self.account_manager.load()
            for username in self.account_manager.accounts.keys():
                if username not in users_dict:  # Only add if not in database
                    details = self.account_manager.accounts[username].get('details', {})
                    is_admin = details.get('role') == 'admin'
                    is_tenant = bool(details.get('tenant_account', details.get('role') == 'tenant'))
                    users_dict[username] = ('json', is_admin, is_tenant)
        except Exception as e:
            logger.warning("UserManagementDialog", f"Could not load JSON users: {e}")
        
        # Display users with admin status and backend source
        for username in sorted(users_dict.keys()):
            source, is_admin, is_tenant = users_dict[username]
            admin_label = " (Admin)" if is_admin else ""
            tenant_label = " (Tenant)" if is_tenant else ""
            display_text = f"{username}{admin_label}{tenant_label} [{source}]"
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, username)  # Store username
            self.user_list.addItem(item)

    def on_user_selected(self):
        """Enable/disable edit, delete, and assign tenants buttons based on selection"""
        has_selection = len(self.user_list.selectedItems()) > 0
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
        self.assign_tenants_btn.setEnabled(has_selection)

    def get_selected_username(self):
        """Get the currently selected username"""
        selected = self.user_list.selectedItems()
        if selected:
            return selected[0].data(Qt.ItemDataRole.UserRole)
        return None

    def add_user(self):
        dlg = CreateOrEditUserDialog(self.account_manager, mode='create', db_manager=self.db_manager, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.refresh_users()

    def edit_user(self):
        username = self.get_selected_username()
        if not username:
            QMessageBox.warning(self, 'No Selection', 'Please select a user to edit.')
            return
        
        dlg = CreateOrEditUserDialog(self.account_manager, mode='edit', username=username, db_manager=self.db_manager, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.refresh_users()

    def delete_user(self):
        username = self.get_selected_username()
        if not username:
            QMessageBox.warning(self, 'No Selection', 'Please select a user to delete.')
            return
        
        reply = QMessageBox.question(
            self, 
            'Confirm Delete', 
            f'Are you sure you want to delete user "{username}"?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Try to delete from database first
                db_user = self.db_manager.get_user_by_username(username)
                if db_user:
                    self.db_manager.delete_user(username)
                    logger.info("UserManagementDialog", f"Deleted user {username} from database")
                else:
                    # Delete from JSON
                    del self.account_manager.accounts[username]
                    self.account_manager.save()
                    logger.info("UserManagementDialog", f"Deleted user {username} from JSON")
                
                QMessageBox.information(self, 'Success', f'User "{username}" deleted.')
                self.refresh_users()
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Failed to delete user: {e}')
                logger.error("UserManagementDialog", f"Error deleting user {username}: {e}")
    
    def assign_tenants(self):
        """Open dialog to assign tenants to selected user"""
        username = self.get_selected_username()
        if not username:
            QMessageBox.warning(self, 'No Selection', 'Please select a user to assign tenants to.')
            return
        
        dlg = TenantAssignmentDialog(username, parent=self)
        dlg.exec()


class CreateOrEditUserDialog(QDialog):
    def __init__(self, account_manager, mode='create', username=None, db_manager=None, parent=None):
        super().__init__(parent)
        self.account_manager = account_manager
        self.db_manager = db_manager
        self.mode = mode
        self.username = username
        self.user_backend = None  # Track which backend user is from
        self.current_two_factor_secret = None
        
        if mode == 'create':
            self.setWindowTitle('Create New User')
        else:
            self.setWindowTitle(f'Edit User: {username}')
        
        self.setMinimumSize(450, 500)
        self.setup_ui()
        
        # Load existing data if editing
        if mode == 'edit' and username:
            self.load_user_data(username)

    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Form layout
        form = QFormLayout()
        
        # Username field
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText('Enter username')
        if self.mode == 'edit':
            self.username_input.setText(self.username)
            self.username_input.setReadOnly(True)  # Can't change username when editing
        form.addRow('Username:', self.username_input)
        
        # Email field
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText('Enter email address')
        form.addRow('Email:', self.email_input)
        
        # Full Name field
        self.fullname_input = QLineEdit()
        self.fullname_input.setPlaceholderText('Enter full name')
        form.addRow('Full Name:', self.fullname_input)
        
        # Phone field
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText('Enter phone number')
        form.addRow('Phone:', self.phone_input)
        
        # Password field
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText('Leave blank to keep current password')
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        if self.mode == 'create':
            self.password_input.setPlaceholderText('Enter password')
        form.addRow('Password:', self.password_input)
        
        # Confirm password field
        self.confirm_input = QLineEdit()
        self.confirm_input.setPlaceholderText('Confirm password')
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow('Confirm Password:', self.confirm_input)
        
        # Admin checkbox
        self.admin_checkbox = QCheckBox('Grant Admin Privileges')
        form.addRow('', self.admin_checkbox)

        # Tenant-only account checkbox
        self.tenant_account_checkbox = QCheckBox('Tenant Account (not admin/landlord)')
        self.tenant_account_checkbox.setChecked(False)
        self.tenant_account_checkbox.toggled.connect(self.on_tenant_flag_changed)
        form.addRow('', self.tenant_account_checkbox)

        # Optional two-factor authentication
        self.two_factor_checkbox = QCheckBox('Require 2FA for this account (optional)')
        self.two_factor_checkbox.setChecked(False)
        form.addRow('', self.two_factor_checkbox)

        # Create now, complete later via setup link
        self.setup_later_checkbox = QCheckBox('Create now and let user finish setup via secure link')
        self.setup_later_checkbox.setChecked(self.mode == 'create')
        self.setup_later_checkbox.toggled.connect(self.on_setup_later_changed)
        if self.mode != 'create':
            self.setup_later_checkbox.setChecked(False)
            self.setup_later_checkbox.setEnabled(False)
        form.addRow('', self.setup_later_checkbox)

        # Access privilege checkboxes
        self.desktop_access_checkbox = QCheckBox('Allow Desktop Access')
        self.desktop_access_checkbox.setChecked(True)
        form.addRow('', self.desktop_access_checkbox)

        self.online_access_checkbox = QCheckBox('Allow Online/API Access')
        self.online_access_checkbox.setChecked(False)
        form.addRow('', self.online_access_checkbox)
        
        layout.addLayout(form)
        
        # Button layout
        btn_layout = QHBoxLayout()
        save_btn = QPushButton('Save')
        cancel_btn = QPushButton('Cancel')
        
        save_btn.clicked.connect(self.save_user)
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        self.on_setup_later_changed(self.setup_later_checkbox.isChecked())

    def load_user_data(self, username):
        """Load existing user data when editing - checks database first, then JSON"""
        is_admin = False
        
        # Check database first
        if self.db_manager:
            try:
                db_user = self.db_manager.get_user_by_username(username)
                if db_user:
                    is_admin = db_user.get('is_admin') == 1
                    self.user_backend = 'database'
                    self.admin_checkbox.setChecked(is_admin)

                    details = db_user.get('details') or {}
                    if not isinstance(details, dict):
                        details = {}

                    # Backward compatible defaults:
                    # - Old API-only accounts used details.api_only=True
                    # - Older desktop users may have no explicit flags
                    api_only = bool(details.get('api_only', False))
                    desktop_access = bool(details.get('desktop_access', not api_only))
                    online_access = bool(details.get('online_access', api_only))
                    tenant_account = bool(details.get('tenant_account', details.get('role') == 'tenant'))
                    two_factor_enabled = bool(details.get('two_factor_enabled', False))
                    self.current_two_factor_secret = details.get('two_factor_secret')

                    self.desktop_access_checkbox.setChecked(desktop_access)
                    self.online_access_checkbox.setChecked(online_access)
                    self.tenant_account_checkbox.setChecked(tenant_account)
                    self.two_factor_checkbox.setChecked(two_factor_enabled)
                    
                    # Load additional fields
                    self.email_input.setText(db_user.get('email', '') or '')
                    self.fullname_input.setText(db_user.get('full_name', '') or '')
                    self.phone_input.setText(db_user.get('phone', '') or '')
                    return
            except Exception as e:
                pass  # Fall through to JSON
        
        # Fall back to JSON
        try:
            account = self.account_manager.get_account(username)
            if account:
                details = account.get('details', {})
                is_admin = details.get('role') == 'admin'
                self.user_backend = 'json'
                self.admin_checkbox.setChecked(is_admin)

                api_only = bool(details.get('api_only', False))
                desktop_access = bool(details.get('desktop_access', not api_only))
                online_access = bool(details.get('online_access', api_only))
                tenant_account = bool(details.get('tenant_account', details.get('role') == 'tenant'))
                two_factor_enabled = bool(details.get('two_factor_enabled', False))
                self.current_two_factor_secret = details.get('two_factor_secret')

                self.desktop_access_checkbox.setChecked(desktop_access)
                self.online_access_checkbox.setChecked(online_access)
                self.tenant_account_checkbox.setChecked(tenant_account)
                self.two_factor_checkbox.setChecked(two_factor_enabled)
                
                # Load additional fields from details
                self.email_input.setText(details.get('email', '') or '')
                self.fullname_input.setText(details.get('full_name', '') or '')
                self.phone_input.setText(details.get('phone', '') or '')
        except Exception as e:
            pass

    def save_user(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        confirm = self.confirm_input.text()
        is_admin = self.admin_checkbox.isChecked()
        tenant_account = self.tenant_account_checkbox.isChecked()
        two_factor_enabled = self.two_factor_checkbox.isChecked()
        setup_later = self.setup_later_checkbox.isChecked() and self.mode == 'create'
        desktop_access = self.desktop_access_checkbox.isChecked()
        online_access = self.online_access_checkbox.isChecked()
        email = self.email_input.text().strip()
        fullname = self.fullname_input.text().strip()
        phone = self.phone_input.text().strip()
        
        # Validation
        if not username:
            QMessageBox.warning(self, 'Error', 'Username is required.')
            return

        if not desktop_access and not online_access:
            QMessageBox.warning(self, 'Error', 'At least one access type (Desktop or Online/API) must be enabled.')
            return

        if is_admin and tenant_account:
            QMessageBox.warning(self, 'Error', 'A tenant account cannot also be an admin/landlord account.')
            return

        role = 'tenant' if tenant_account else ('admin' if is_admin else 'user')
        two_factor_secret = self.current_two_factor_secret
        if two_factor_enabled and not two_factor_secret:
            two_factor_secret = generate_totp_secret()
        if not two_factor_enabled:
            two_factor_secret = None
        
        if self.mode == 'create':
            # Creating new user - password is required
            if not setup_later and not password:
                QMessageBox.warning(self, 'Error', 'Password is required for new users.')
                return
            
            if not setup_later and password != confirm:
                QMessageBox.warning(self, 'Error', 'Passwords do not match.')
                return
            
            # Check both backends for existing user
            existing_db = None
            existing_json = None
            
            if self.db_manager:
                try:
                    existing_db = self.db_manager.get_user_by_username(username)
                except:
                    pass
            
            try:
                existing_json = self.account_manager.get_account(username)
            except:
                pass
            
            if existing_db or existing_json:
                QMessageBox.warning(self, 'Error', 'Username already exists.')
                return
            
            try:
                if setup_later:
                    unified_manager = UnifiedApiAccountManager()
                    result = unified_manager.create_pending_account(
                        username=username,
                        email=email or None,
                        full_name=fullname or None,
                        phone=phone or None,
                        is_admin=1 if is_admin else 0,
                        role=role,
                        tenant_account=tenant_account,
                        two_factor_enabled=False,
                        desktop_access=desktop_access,
                        online_access=online_access,
                        api_only=online_access and not desktop_access
                    )

                    setup_token = result.get('setup_token')
                    setup_link = f"http://localhost:5001/setup_account.html?api=http://localhost:5000&token={setup_token}"
                    QApplication.clipboard().setText(setup_link)
                    QMessageBox.information(
                        self,
                        'Setup Link Created',
                        f'User "{username}" created in pending setup mode.\n\n'
                        f'Setup link copied to clipboard:\n{setup_link}\n\n'
                        'Share this link with the user to complete their password and optional 2FA setup.'
                    )
                    self.accept()
                    return

                # Create in database if available
                if self.db_manager:
                    from src.account_id_generator import generate_account_id
                    account_id = generate_account_id()
                    self.db_manager.create_user(
                        username=username,
                        password=password,
                        account_id=account_id,
                        email=email or None,
                        full_name=fullname or None,
                        phone=phone or None,
                        is_admin=1 if is_admin else 0,
                        role=role,
                        tenant_account=tenant_account,
                        two_factor_enabled=two_factor_enabled,
                        two_factor_secret=two_factor_secret,
                        desktop_access=desktop_access,
                        online_access=online_access,
                        # Keep legacy compatibility for existing API auth logic.
                        api_only=online_access and not desktop_access
                    )
                else:
                    # Fall back to JSON creation
                    details = {
                        'role': role,
                        'tenant_account': tenant_account,
                        'two_factor_enabled': two_factor_enabled,
                        'two_factor_secret': two_factor_secret,
                        'email': email,
                        'full_name': fullname,
                        'phone': phone,
                        'desktop_access': desktop_access,
                        'online_access': online_access,
                        'api_only': online_access and not desktop_access
                    }
                    self.account_manager.create_account(username, password, **details)
                
                QMessageBox.information(self, 'Success', f'User "{username}" created successfully.')
                if two_factor_enabled and two_factor_secret:
                    self.show_two_factor_setup_dialog(username, two_factor_secret)
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Failed to create user: {e}')
        
        else:  # Edit mode
            try:
                # Update password if provided
                if password:
                    if password != confirm:
                        QMessageBox.warning(self, 'Error', 'Passwords do not match.')
                        return
                    
                    if self.user_backend == 'database' and self.db_manager:
                        self.db_manager.update_user(username, password=password)
                    else:
                        self.account_manager.change_password(username, password)
                
                # Update user details in correct backend
                if self.user_backend == 'database' and self.db_manager:
                    self.db_manager.update_user(
                        username,
                        email=email or None,
                        full_name=fullname or None,
                        phone=phone or None,
                        is_admin=1 if is_admin else 0,
                        role=role,
                        tenant_account=tenant_account,
                        two_factor_enabled=two_factor_enabled,
                        two_factor_secret=two_factor_secret,
                        desktop_access=desktop_access,
                        online_access=online_access,
                        # Keep legacy compatibility for existing API auth logic.
                        api_only=online_access and not desktop_access
                    )
                else:
                    # Update JSON backend
                    account = self.account_manager.get_account(username)
                    if account:
                        account['details']['role'] = role
                        account['details']['tenant_account'] = tenant_account
                        account['details']['two_factor_enabled'] = two_factor_enabled
                        account['details']['two_factor_secret'] = two_factor_secret
                        account['details']['email'] = email
                        account['details']['full_name'] = fullname
                        account['details']['phone'] = phone
                        account['details']['desktop_access'] = desktop_access
                        account['details']['online_access'] = online_access
                        account['details']['api_only'] = online_access and not desktop_access
                        self.account_manager.save()
                
                QMessageBox.information(self, 'Success', f'User "{username}" updated successfully.')
                if two_factor_enabled and two_factor_secret:
                    self.show_two_factor_setup_dialog(username, two_factor_secret)
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Failed to update user: {e}')

    def on_tenant_flag_changed(self, checked):
        """Tenant accounts cannot be admin accounts."""
        if checked:
            self.admin_checkbox.setChecked(False)
            self.admin_checkbox.setEnabled(False)
        else:
            self.admin_checkbox.setEnabled(True)

    def on_setup_later_changed(self, checked):
        """When setup is deferred, password entry is not required in this dialog."""
        self.password_input.setEnabled(not checked)
        self.confirm_input.setEnabled(not checked)
        self.two_factor_checkbox.setEnabled(not checked)
        if checked:
            self.password_input.clear()
            self.confirm_input.clear()
            self.two_factor_checkbox.setChecked(False)

    def show_two_factor_setup_dialog(self, username, secret):
        """Show QR and manual provisioning details for authenticator app setup."""
        try:
            otpauth_uri = build_totp_uri(secret, username)
            qr_url = build_totp_qr_url(otpauth_uri)

            dlg = QDialog(self)
            dlg.setWindowTitle('2FA Provisioning')
            dlg.setMinimumSize(500, 520)

            layout = QVBoxLayout()
            layout.addWidget(QLabel(f'2FA is enabled for user: {username}'))
            layout.addWidget(QLabel('Scan this QR code with your authenticator app or use the manual setup code below.'))

            qr_label = QLabel()
            qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            try:
                data = urllib.request.urlopen(qr_url, timeout=8).read()
                pixmap = QPixmap()
                if pixmap.loadFromData(data):
                    qr_label.setPixmap(pixmap)
                else:
                    qr_label.setText('Unable to load QR image. Use manual code below.')
            except Exception:
                qr_label.setText('Unable to load QR image. Use manual code below.')
            layout.addWidget(qr_label)

            secret_input = QLineEdit(secret)
            secret_input.setReadOnly(True)
            layout.addWidget(QLabel('Manual setup code:'))
            layout.addWidget(secret_input)

            uri_input = QLineEdit(otpauth_uri)
            uri_input.setReadOnly(True)
            layout.addWidget(QLabel('Authenticator URI:'))
            layout.addWidget(uri_input)

            close_btn = QPushButton('Close')
            close_btn.clicked.connect(dlg.accept)
            layout.addWidget(close_btn)

            dlg.setLayout(layout)
            dlg.exec()
        except Exception as e:
            logger.warning('UserManagementDialog', f'Failed to render 2FA provisioning dialog: {e}')

class TenantAssignmentDialog(QDialog):
    """Dialog for assigning tenants to a user"""
    
    def __init__(self, username, parent=None):
        super().__init__(parent)
        logger.debug("TenantAssignmentDialog", f"Initializing TenantAssignmentDialog for user {username}")
        self.username = username
        self.tenant_manager = TenantManager()
        
        self.setWindowTitle(f'Assign Tenants to {username}')
        self.setMinimumSize(600, 500)
        
        layout = QVBoxLayout()
        
        # Title
        title = QLabel(f'Assign Tenants to User: {username}')
        title.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Instructions
        instructions = QLabel('Check the tenants you want to assign to this user:')
        layout.addWidget(instructions)
        
        # Tenant list with checkboxes
        self.tenant_list = QListWidget()
        self.tenant_checkboxes = {}  # Map tenant_id -> checkbox
        
        # Get all tenants directly from the manager's dictionary (not filtered)
        all_tenants = list(self.tenant_manager.tenants.values())
        
        for tenant in sorted(all_tenants, key=lambda t: t.name):
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, tenant.tenant_id)
            
            # Create checkbox widget
            checkbox = QCheckBox(f"{tenant.name} (ID: {tenant.tenant_id})")
            
            # Check if tenant is already assigned to this user
            if self.username in tenant.user_ids:
                checkbox.setChecked(True)
            
            self.tenant_checkboxes[tenant.tenant_id] = checkbox
            
            # Add item to list
            item.setSizeHint(checkbox.sizeHint())
            self.tenant_list.addItem(item)
            self.tenant_list.setItemWidget(item, checkbox)
        
        layout.addWidget(self.tenant_list)
        
        # Button layout
        btn_layout = QHBoxLayout()
        
        # Select All / Deselect All buttons
        select_all_btn = QPushButton('Select All')
        select_all_btn.clicked.connect(self.select_all)
        btn_layout.addWidget(select_all_btn)
        
        deselect_all_btn = QPushButton('Deselect All')
        deselect_all_btn.clicked.connect(self.deselect_all)
        btn_layout.addWidget(deselect_all_btn)
        
        btn_layout.addStretch()
        
        save_btn = QPushButton('Save Assignments')
        save_btn.clicked.connect(self.save_assignments)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        btn_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton('Cancel')
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
    
    def select_all(self):
        """Select all tenant checkboxes"""
        for checkbox in self.tenant_checkboxes.values():
            checkbox.setChecked(True)
    
    def deselect_all(self):
        """Deselect all tenant checkboxes"""
        for checkbox in self.tenant_checkboxes.values():
            checkbox.setChecked(False)
    
    def save_assignments(self):
        """Save tenant assignments to the selected user"""
        try:
            # Get all tenants
            all_tenants = self.tenant_manager.tenants
            
            # Update tenant assignments
            changes = 0
            for tenant_id, checkbox in self.tenant_checkboxes.items():
                tenant = all_tenants.get(tenant_id)
                if tenant:
                    if checkbox.isChecked():
                        # Add this user to the tenant's user list (if not already there)
                        if self.username not in tenant.user_ids:
                            tenant.user_ids.append(self.username)
                            self.tenant_manager.update_tenant(tenant)
                            changes += 1
                            logger.info("TenantAssignmentDialog", f"Assigned tenant {tenant_id} to user {self.username}")
                    else:
                        # Remove this user from the tenant's user list (if present)
                        if self.username in tenant.user_ids:
                            tenant.user_ids.remove(self.username)
                            self.tenant_manager.update_tenant(tenant)
                            changes += 1
                            logger.info("TenantAssignmentDialog", f"Unassigned tenant {tenant_id} from user {self.username}")
            
            if changes > 0:
                QMessageBox.information(
                    self,
                    'Success',
                    f'Tenant assignments updated. {changes} change(s) made.'
                )
                logger.info("TenantAssignmentDialog", f"Saved {changes} tenant assignment changes for user {self.username}")
            else:
                QMessageBox.information(
                    self,
                    'No Changes',
                    'No changes were made to tenant assignments.'
                )
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to save tenant assignments: {e}')
            logger.error("TenantAssignmentDialog", f"Error saving assignments: {e}")