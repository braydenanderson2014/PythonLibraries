from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QListWidget, QHBoxLayout, QMessageBox, QListWidgetItem, QCheckBox, QFormLayout, QLineEdit, QWidget, QScrollArea, QListWidgetItem as ListItem
from PyQt6.QtCore import Qt
from src.account import AccountManager
from src.account_db import AccountDatabaseManager
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
        users_dict = {}  # Map username -> (source, is_admin)
        
        # Get users from database
        try:
            db_users = self.db_manager.list_users()
            for user in db_users:
                username = user.get('username')
                is_admin = user.get('is_admin') == 1
                users_dict[username] = ('database', is_admin)
        except Exception as e:
            logger.warning("UserManagementDialog", f"Could not load database users: {e}")
        
        # Get users from JSON (in case they're not yet migrated)
        try:
            self.account_manager.load()
            for username in self.account_manager.accounts.keys():
                if username not in users_dict:  # Only add if not in database
                    is_admin = self.account_manager.accounts[username].get('details', {}).get('role') == 'admin'
                    users_dict[username] = ('json', is_admin)
        except Exception as e:
            logger.warning("UserManagementDialog", f"Could not load JSON users: {e}")
        
        # Display users with admin status and backend source
        for username in sorted(users_dict.keys()):
            source, is_admin = users_dict[username]
            admin_label = " (Admin)" if is_admin else ""
            display_text = f"{username}{admin_label} [{source}]"
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
        email = self.email_input.text().strip()
        fullname = self.fullname_input.text().strip()
        phone = self.phone_input.text().strip()
        
        # Validation
        if not username:
            QMessageBox.warning(self, 'Error', 'Username is required.')
            return
        
        if self.mode == 'create':
            # Creating new user - password is required
            if not password:
                QMessageBox.warning(self, 'Error', 'Password is required for new users.')
                return
            
            if password != confirm:
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
                        is_admin=1 if is_admin else 0
                    )
                else:
                    # Fall back to JSON creation
                    details = {
                        'role': 'admin' if is_admin else 'user',
                        'email': email,
                        'full_name': fullname,
                        'phone': phone
                    }
                    self.account_manager.create_account(username, password, **details)
                
                QMessageBox.information(self, 'Success', f'User "{username}" created successfully.')
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
                        is_admin=1 if is_admin else 0
                    )
                else:
                    # Update JSON backend
                    account = self.account_manager.get_account(username)
                    if account:
                        account['details']['role'] = 'admin' if is_admin else 'user'
                        account['details']['email'] = email
                        account['details']['full_name'] = fullname
                        account['details']['phone'] = phone
                        self.account_manager.save()
                
                QMessageBox.information(self, 'Success', f'User "{username}" updated successfully.')
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Failed to update user: {e}')

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