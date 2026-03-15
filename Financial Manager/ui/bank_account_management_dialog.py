"""
Bank Account Management UI
Allows users to add, edit, and manage their specific bank accounts
"""

from typing import Optional, List, Dict, Any
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
                             QComboBox, QDoubleSpinBox, QFormLayout, QDialogButtonBox,
                             QMessageBox, QGroupBox, QCheckBox, QTabWidget, QWidget,
                             QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from src.bank_accounts import BankAccount, BankAccountManager

from assets.Logger import Logger
logger = Logger()

class AddBankAccountDialog(QDialog):
    def __init__(self, parent=None, user_id=None, account_to_edit=None, account_manager=None):
        super().__init__(parent)
        logger.debug("AddBankAccountDialog", f"Initializing AddBankAccountDialog (edit={account_to_edit is not None})")
        self.user_id = user_id
        self.account_to_edit = account_to_edit
        # Use provided account manager or create new one as fallback
        self.account_manager = account_manager if account_manager else BankAccountManager()
        
        self.setWindowTitle('Edit Bank Account' if account_to_edit else 'Add Bank Account')
        self.setMinimumWidth(450)
        self.init_ui()
        
        if account_to_edit:
            self.populate_fields()
            logger.debug("AddBankAccountDialog", f"Populating fields for account {account_to_edit.account_id}")
    
    def init_ui(self):
        layout = QFormLayout()
        
        # Bank Name
        self.bank_name_input = QLineEdit()
        self.bank_name_input.setPlaceholderText('e.g., Tab Bank, Granite Credit Union, Mountain America')
        layout.addRow('Bank Name:', self.bank_name_input)
        
        # Account Type
        self.account_type_combo = QComboBox()
        self.account_type_combo.setEditable(True)
        self.account_type_combo.addItems(['Checking', 'Savings', 'Credit Card', 'Investment', 'Money Market', 'CD', 'Other'])
        layout.addRow('Account Type:', self.account_type_combo)
        
        # Account Name (user-friendly name)
        self.account_name_input = QLineEdit()
        self.account_name_input.setPlaceholderText('e.g., Main Checking, Emergency Savings, Daily Spending')
        layout.addRow('Account Name:', self.account_name_input)
        
        # Account Number (last 4 digits or identifier)
        self.account_number_input = QLineEdit()
        self.account_number_input.setPlaceholderText('Last 4 digits or identifier (e.g., 1234)')
        layout.addRow('Account Number:', self.account_number_input)
        
        # Initial Balance
        self.initial_balance_spin = QDoubleSpinBox()
        self.initial_balance_spin.setRange(-999999.99, 999999.99)
        self.initial_balance_spin.setPrefix('$')
        self.initial_balance_spin.setDecimals(2)
        layout.addRow('Initial Balance:', self.initial_balance_spin)
        
        # Help text
        help_label = QLabel('The initial balance is the starting amount in this account when you began tracking it.')
        help_label.setWordWrap(True)
        help_label.setStyleSheet('color: #666; font-style: italic;')
        layout.addRow('', help_label)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
        self.setLayout(layout)
    
    def populate_fields(self):
        """Populate fields when editing an existing account"""
        if self.account_to_edit:
            self.bank_name_input.setText(self.account_to_edit.bank_name)
            self.account_type_combo.setCurrentText(self.account_to_edit.account_type)
            self.account_name_input.setText(self.account_to_edit.account_name)
            self.account_number_input.setText(self.account_to_edit.account_number)
            self.initial_balance_spin.setValue(self.account_to_edit.initial_balance)
    
    def get_account_data(self):
        """Get the account data from the form"""
        return {
            'bank_name': self.bank_name_input.text().strip(),
            'account_type': self.account_type_combo.currentText().strip(),
            'account_name': self.account_name_input.text().strip(),
            'account_number': self.account_number_input.text().strip(),
            'initial_balance': self.initial_balance_spin.value()
        }
    
    def validate_data(self):
        """Validate the form data"""
        logger.debug("AddBankAccountDialog", "Validating form data")
        data = self.get_account_data()
        
        if not data['bank_name']:
            logger.warning("AddBankAccountDialog", "Validation failed: bank_name is empty")
            QMessageBox.warning(self, 'Validation Error', 'Bank name is required.')
            return False
        
        if not data['account_type']:
            logger.warning("AddBankAccountDialog", "Validation failed: account_type is empty")
            QMessageBox.warning(self, 'Validation Error', 'Account type is required.')
            return False
        
        logger.debug("AddBankAccountDialog", "Form validation passed")
        return True
    
    def accept(self):
        if self.validate_data():
            super().accept()

class TransferDialog(QDialog):
    def __init__(self, parent=None, bank=None, user_id=None):
        super().__init__(parent)
        logger.debug("TransferDialog", f"Initializing TransferDialog for user {user_id}")
        self.bank = bank
        self.user_id = user_id
        
        self.setWindowTitle('Transfer Between Accounts')
        self.setMinimumWidth(400)
        self.init_ui()
    
    def init_ui(self):
        layout = QFormLayout()
        
        # Get user accounts
        if not self.bank:
            QMessageBox.warning(self, 'No Bank System', 'Bank system is not available.')
            self.reject()
            return
            
        accounts = self.bank.get_accounts_summary(self.user_id)
        account_choices = [(acc['account_id'], f"{acc['display_name']} (${acc['balance']:,.2f})") for acc in accounts]
        
        if len(account_choices) < 2:
            QMessageBox.warning(self, 'Not Enough Accounts', 'You need at least 2 accounts to make transfers.')
            self.reject()
            return
        
        # From Account
        self.from_account_combo = QComboBox()
        for account_id, display_name in account_choices:
            self.from_account_combo.addItem(display_name, account_id)
        layout.addRow('From Account:', self.from_account_combo)
        
        # To Account
        self.to_account_combo = QComboBox()
        for account_id, display_name in account_choices:
            self.to_account_combo.addItem(display_name, account_id)
        layout.addRow('To Account:', self.to_account_combo)
        
        # Amount
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0.01, 999999.99)
        self.amount_spin.setPrefix('$')
        self.amount_spin.setDecimals(2)
        layout.addRow('Amount:', self.amount_spin)
        
        # Description
        self.description_input = QLineEdit()
        self.description_input.setText('Account Transfer')
        layout.addRow('Description:', self.description_input)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
        self.setLayout(layout)
    
    def get_transfer_data(self):
        """Get transfer data from the form"""
        return {
            'from_account_id': self.from_account_combo.currentData(),
            'to_account_id': self.to_account_combo.currentData(),
            'amount': self.amount_spin.value(),
            'description': self.description_input.text().strip()
        }
    
    def validate_data(self):
        """Validate transfer data"""
        logger.debug("TransferDialog", "Validating transfer data")
        data = self.get_transfer_data()
        
        if data['from_account_id'] == data['to_account_id']:
            logger.warning("TransferDialog", "Validation failed: same account selected")
            QMessageBox.warning(self, 'Validation Error', 'Cannot transfer to the same account.')
            return False
        
        if data['amount'] <= 0:
            logger.warning("TransferDialog", "Validation failed: invalid amount")
            QMessageBox.warning(self, 'Validation Error', 'Transfer amount must be greater than zero.')
            return False
        
        logger.debug("TransferDialog", "Transfer validation passed")
        return True
    
    def accept(self):
        if self.validate_data():
            super().accept()

class BankAccountManagementDialog(QDialog):
    accounts_changed = pyqtSignal()
    
    def __init__(self, parent=None, bank=None, user_id=None):
        super().__init__(parent)
        logger.debug("BankAccountManagementDialog", f"Initializing BankAccountManagementDialog for user {user_id}")
        self.bank = bank
        self.user_id = user_id
        # Use the account manager from the Bank object to ensure consistency
        self.account_manager = bank.account_manager if bank else BankAccountManager()
        
        self.setWindowTitle('Bank Account Management')
        self.setMinimumSize(900, 700)  # Increased from 800x600 for better viewing
        self.resize(1000, 750)  # Set default size
        self.init_ui()
        self.refresh_accounts()
        logger.info("BankAccountManagementDialog", f"BankAccountManagementDialog initialized for user {user_id}")
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel('Bank Account Management')
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Tab widget
        tab_widget = QTabWidget()
        
        # Accounts tab
        accounts_tab = self.create_accounts_tab()
        tab_widget.addTab(accounts_tab, 'My Accounts')
        
        # Transfers tab
        transfers_tab = self.create_transfers_tab()
        tab_widget.addTab(transfers_tab, 'Transfers')
        
        layout.addWidget(tab_widget)
        
        # Close button
        close_btn = QPushButton('Close')
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
    
    def create_accounts_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Controls (these should stay at the top, not scrollable)
        controls_layout = QHBoxLayout()
        
        add_btn = QPushButton('Add Account')
        add_btn.clicked.connect(self.add_account)
        add_btn.setStyleSheet('QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 8px; }')
        controls_layout.addWidget(add_btn)
        
        edit_btn = QPushButton('Edit Account')
        edit_btn.clicked.connect(self.edit_account)
        edit_btn.setStyleSheet('QPushButton { background-color: #2196F3; color: white; font-weight: bold; padding: 8px; }')
        controls_layout.addWidget(edit_btn)
        
        remove_btn = QPushButton('Remove Account')
        remove_btn.clicked.connect(self.remove_account)
        remove_btn.setStyleSheet('QPushButton { background-color: #F44336; color: white; font-weight: bold; padding: 8px; }')
        controls_layout.addWidget(remove_btn)
        
        controls_layout.addStretch()
        
        refresh_btn = QPushButton('Refresh')
        refresh_btn.clicked.connect(self.refresh_accounts)
        controls_layout.addWidget(refresh_btn)
        
        layout.addLayout(controls_layout)
        
        # Create scrollable content area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Content widget for the scroll area
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        
        # Accounts table
        self.accounts_table = QTableWidget()
        self.accounts_table.setColumnCount(6)
        self.accounts_table.setHorizontalHeaderLabels(['Bank', 'Account Type', 'Account Name', 'Account #', 'Balance', 'Status'])
        header = self.accounts_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.accounts_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.accounts_table.setMinimumHeight(400)  # Ensure minimum height for better viewing
        
        content_layout.addWidget(self.accounts_table)
        
        # Add some spacing at the bottom
        content_layout.addStretch()
        
        content_widget.setLayout(content_layout)
        scroll_area.setWidget(content_widget)
        
        layout.addWidget(scroll_area)
        
        widget.setLayout(layout)
        return widget
    
    def create_transfers_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Transfer button (should stay at top, not scrollable)
        transfer_btn = QPushButton('Transfer Between Accounts')
        transfer_btn.clicked.connect(self.transfer_money)
        transfer_btn.setStyleSheet('QPushButton { background-color: #FF9800; color: white; font-weight: bold; padding: 10px; }')
        layout.addWidget(transfer_btn)
        
        # Create scrollable content area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Content widget for the scroll area
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        
        # Recent transfers
        transfers_label = QLabel('Recent Transfers')
        transfers_label.setStyleSheet('font-size: 14px; font-weight: bold; margin-top: 20px;')
        content_layout.addWidget(transfers_label)
        
        self.transfers_table = QTableWidget()
        self.transfers_table.setColumnCount(5)
        self.transfers_table.setHorizontalHeaderLabels(['Date', 'Description', 'From Account', 'To Account', 'Amount'])
        header = self.transfers_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.transfers_table.setMinimumHeight(300)  # Ensure minimum height for better viewing
        
        content_layout.addWidget(self.transfers_table)
        
        # Add some spacing at the bottom
        content_layout.addStretch()
        
        content_widget.setLayout(content_layout)
        scroll_area.setWidget(content_widget)
        
        layout.addWidget(scroll_area)
        
        widget.setLayout(layout)
        return widget
    
    def refresh_accounts(self):
        """Refresh the accounts table"""
        logger.debug("BankAccountManagementDialog", "Refreshing accounts table")
        if not self.bank:
            logger.warning("BankAccountManagementDialog", "Bank system not available")
            QMessageBox.warning(self, 'No Bank System', 'Bank system is not available.')
            return
            
        accounts_summary = self.bank.get_accounts_summary(self.user_id)
        logger.debug("BankAccountManagementDialog", f"Loaded {len(accounts_summary)} accounts")
        
        self.accounts_table.setRowCount(len(accounts_summary))
        
        for row, account_info in enumerate(accounts_summary):
            account = account_info['account']
            
            self.accounts_table.setItem(row, 0, QTableWidgetItem(account.bank_name))
            self.accounts_table.setItem(row, 1, QTableWidgetItem(account.account_type))
            self.accounts_table.setItem(row, 2, QTableWidgetItem(account.account_name))
            self.accounts_table.setItem(row, 3, QTableWidgetItem(account.account_number))
            
            balance_item = QTableWidgetItem(f"${account_info['balance']:,.2f}")
            if account_info['balance'] >= 0:
                balance_item.setForeground(Qt.GlobalColor.darkGreen)
            else:
                balance_item.setForeground(Qt.GlobalColor.red)
            self.accounts_table.setItem(row, 4, balance_item)
            
            status = "Active" if account.active else "Inactive"
            self.accounts_table.setItem(row, 5, QTableWidgetItem(status))
            
            # Store account ID in the first item for reference
            item = self.accounts_table.item(row, 0)
            if item:
                item.setData(Qt.ItemDataRole.UserRole, account.account_id)
        
        self.refresh_transfers()
    
    def refresh_transfers(self):
        """Refresh the transfers table"""
        if not self.bank:
            return
            
        # Get transfer transactions (category = 'Transfer')
        transactions = self.bank.get_user_finances(self.user_id)
        transfers = [t for t in transactions if t.get('category') == 'Transfer']
        transfers.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Take only recent transfers (limit to 20)
        recent_transfers = transfers[:20]
        
        self.transfers_table.setRowCount(len(recent_transfers))
        
        for row, transfer in enumerate(recent_transfers):
            date = transfer.get('date', transfer['timestamp'][:10])
            self.transfers_table.setItem(row, 0, QTableWidgetItem(date))
            self.transfers_table.setItem(row, 1, QTableWidgetItem(transfer['desc']))
            self.transfers_table.setItem(row, 2, QTableWidgetItem(transfer['account']))
            self.transfers_table.setItem(row, 3, QTableWidgetItem(''))  # To account not easily determined
            
            amount_str = f"${transfer['amount']:,.2f}"
            if transfer['type'] == 'out':
                amount_str = f"-{amount_str}"
            self.transfers_table.setItem(row, 4, QTableWidgetItem(amount_str))
    
    def add_account(self):
        """Add a new bank account"""
        logger.debug("BankAccountManagementDialog", "Add account dialog opened")
        dialog = AddBankAccountDialog(self, self.user_id, account_manager=self.account_manager)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_account_data()
            
            try:
                if not self.bank:
                    logger.error("BankAccountManagementDialog", "Bank system not available for add_account")
                    QMessageBox.critical(self, 'Error', 'Bank system is not available.')
                    return
                    
                self.bank.add_bank_account(
                    bank_name=data['bank_name'],
                    account_type=data['account_type'],
                    account_name=data['account_name'],
                    account_number=data['account_number'],
                    initial_balance=data['initial_balance'],
                    user_id=self.user_id
                )
                
                logger.info("BankAccountManagementDialog", f"Account added: {data['bank_name']} - {data['account_name']}")
                self.refresh_accounts()
                self.accounts_changed.emit()
                QMessageBox.information(self, 'Success', 'Bank account added successfully!')
                
            except Exception as e:
                logger.error("BankAccountManagementDialog", f"Failed to add account: {str(e)}")
                QMessageBox.critical(self, 'Error', f'Failed to add account: {str(e)}')
    
    def edit_account(self):
        """Edit selected bank account"""
        logger.debug("BankAccountManagementDialog", "Edit account requested")
        selected_row = self.accounts_table.currentRow()
        if selected_row < 0:
            logger.warning("BankAccountManagementDialog", "No account selected for edit")
            QMessageBox.warning(self, 'No Selection', 'Please select an account to edit.')
            return
        
        item = self.accounts_table.item(selected_row, 0)
        if not item:
            logger.error("BankAccountManagementDialog", "Unable to get account information")
            QMessageBox.warning(self, 'Error', 'Unable to get account information.')
            return
            
        account_id = item.data(Qt.ItemDataRole.UserRole)
        account = self.account_manager.get_account(account_id)
        
        if not account:
            logger.warning("BankAccountManagementDialog", f"Account not found: {account_id}")
            QMessageBox.warning(self, 'Error', 'Account not found.')
            return
        
        logger.debug("BankAccountManagementDialog", f"Edit account dialog opened for {account_id}")
        dialog = AddBankAccountDialog(self, self.user_id, account, account_manager=self.account_manager)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_account_data()
            
            try:
                self.account_manager.update_account(account_id, **data)
                logger.info("BankAccountManagementDialog", f"Account updated: {account_id}")
                self.refresh_accounts()
                self.accounts_changed.emit()
                QMessageBox.information(self, 'Success', 'Account updated successfully!')
                
            except Exception as e:
                logger.error("BankAccountManagementDialog", f"Failed to update account: {str(e)}")
                QMessageBox.critical(self, 'Error', f'Failed to update account: {str(e)}')
    
    def remove_account(self):
        """Remove selected bank account"""
        logger.debug("BankAccountManagementDialog", "Remove account requested")
        selected_row = self.accounts_table.currentRow()
        if selected_row < 0:
            logger.warning("BankAccountManagementDialog", "No account selected for removal")
            QMessageBox.warning(self, 'No Selection', 'Please select an account to remove.')
            return
        
        item_0 = self.accounts_table.item(selected_row, 0)
        item_2 = self.accounts_table.item(selected_row, 2)
        
        if not item_0 or not item_2:
            logger.error("BankAccountManagementDialog", "Unable to get account information")
            QMessageBox.warning(self, 'Error', 'Unable to get account information.')
            return
            
        account_id = item_0.data(Qt.ItemDataRole.UserRole)
        bank_name = item_0.text()
        account_name = item_2.text()
        
        logger.debug("BankAccountManagementDialog", f"Confirming removal of account {account_id}")
        reply = QMessageBox.question(self, 'Confirm Removal', 
                                   f'Are you sure you want to remove the account "{bank_name} - {account_name}"?\n\n'
                                   'This will mark it as inactive but preserve transaction history.',
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.account_manager.remove_account(account_id)
                logger.info("BankAccountManagementDialog", f"Account removed: {account_id}")
                self.refresh_accounts()
                self.accounts_changed.emit()
                QMessageBox.information(self, 'Success', 'Account removed successfully!')
                
            except Exception as e:
                logger.error("BankAccountManagementDialog", f"Failed to remove account: {str(e)}")
                QMessageBox.critical(self, 'Error', f'Failed to remove account: {str(e)}')
    
    def transfer_money(self):
        """Transfer money between accounts"""
        logger.debug("BankAccountManagementDialog", "Transfer dialog opened")
        dialog = TransferDialog(self, self.bank, self.user_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_transfer_data()
            
            try:
                if not self.bank:
                    logger.error("BankAccountManagementDialog", "Bank system not available for transfer")
                    QMessageBox.critical(self, 'Error', 'Bank system is not available.')
                    return
                    
                logger.debug("BankAccountManagementDialog", f"Processing transfer: {data['amount']} from {data['from_account_id']} to {data['to_account_id']}")
                self.bank.transfer_between_accounts(
                    from_account_id=data['from_account_id'],
                    to_account_id=data['to_account_id'],
                    amount=data['amount'],
                    description=data['description']
                )
                
                logger.info("BankAccountManagementDialog", f"Transfer completed: ${data['amount']}")
                self.refresh_accounts()
                self.accounts_changed.emit()
                QMessageBox.information(self, 'Success', 'Transfer completed successfully!')
                
            except Exception as e:
                logger.error("BankAccountManagementDialog", f"Transfer failed: {str(e)}")
                QMessageBox.critical(self, 'Error', f'Transfer failed: {str(e)}')
