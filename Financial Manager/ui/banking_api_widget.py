"""
Banking API Integration UI Widget

Provides user interface for linking bank accounts and syncing transactions.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
    QFormLayout, QLineEdit, QComboBox, QSpinBox, QCheckBox,
    QMessageBox, QGroupBox, QTextEdit, QProgressBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon
from datetime import datetime, date
from assets.Logger import Logger
logger = Logger()

try:
    from ..src.banking_api import BankingAPIManager
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.banking_api import BankingAPIManager


class SyncWorker(QThread):
    """Worker thread for syncing transactions in background"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, api_manager, link_id, days_back, bank_instance):
        super().__init__()
        logger.debug("SyncWorker", f"Initializing SyncWorker for link {link_id}")
        self.api_manager = api_manager
        self.link_id = link_id
        self.days_back = days_back
        self.bank_instance = bank_instance
    
    def run(self):
        logger.debug("SyncWorker", f"Starting sync for link {self.link_id} ({self.days_back} days)")
        try:
            self.progress.emit(f"Syncing transactions...")
            count, errors = self.api_manager.sync_transactions(
                self.link_id, 
                self.days_back, 
                self.bank_instance
            )
            logger.info("SyncWorker", f"Sync completed: {count} transactions, {len(errors)} errors")
            self.finished.emit({'count': count, 'errors': errors})
        except Exception as e:
            logger.error("SyncWorker", f"Sync failed: {str(e)}")
            self.error.emit(str(e))


class LinkAccountDialog(QDialog):
    """Dialog for linking a new bank account"""
    
    def __init__(self, api_manager, bank_accounts, parent=None):
        super().__init__(parent)
        logger.debug("LinkAccountDialog", "Initializing LinkAccountDialog")
        self.api_manager = api_manager
        self.bank_accounts = bank_accounts
        self.setWindowTitle("Link Bank Account")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        self.setup_ui()
        logger.info("LinkAccountDialog", f"LinkAccountDialog initialized with {len(bank_accounts)} available accounts")
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Info label
        info_label = QLabel(
            "Link a real bank account to automatically import transactions.\n"
            "Note: Mock provider is for testing without real credentials."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Form
        form_layout = QFormLayout()
        
        # Provider selection
        self.provider_combo = QComboBox()
        available_providers = list(self.api_manager.providers.keys())
        self.provider_combo.addItems(available_providers)
        self.provider_combo.currentTextChanged.connect(self.on_provider_changed)
        form_layout.addRow("Banking Provider:", self.provider_combo)
        
        # Access token (for Plaid)
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("Enter access token (for Plaid after Link flow)")
        self.token_label = QLabel("Access Token:")
        form_layout.addRow(self.token_label, self.token_input)
        
        # App account selection
        self.account_combo = QComboBox()
        for account in self.bank_accounts:
            self.account_combo.addItem(
                f"{account['name']} ({account['type']})",
                userData=account
            )
        form_layout.addRow("Link to App Account:", self.account_combo)
        
        layout.addLayout(form_layout)
        
        # Instructions
        self.instructions_text = QTextEdit()
        self.instructions_text.setReadOnly(True)
        self.instructions_text.setMaximumHeight(100)
        layout.addWidget(QLabel("Instructions:"))
        layout.addWidget(self.instructions_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.link_button = QPushButton("Link Account")
        self.link_button.clicked.connect(self.link_account)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(self.link_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Update UI based on provider
        self.on_provider_changed(self.provider_combo.currentText())
    
    def on_provider_changed(self, provider_name):
        """Update UI based on selected provider"""
        if provider_name == 'mock':
            self.token_input.setEnabled(False)
            self.token_input.clear()
            self.token_label.setEnabled(False)
            self.instructions_text.setPlainText(
                "Mock provider creates test accounts with sample data.\n"
                "No credentials needed - just select which app account to link to."
            )
        elif provider_name == 'plaid':
            self.token_input.setEnabled(True)
            self.token_label.setEnabled(True)
            self.instructions_text.setPlainText(
                "For Plaid:\n"
                "1. Complete Plaid Link flow (separate web interface)\n"
                "2. Exchange public token for access token\n"
                "3. Paste access token here\n"
                "Note: This requires proper Plaid credentials in settings."
            )
    
    def link_account(self):
        """Link the selected account"""
        logger.debug("LinkAccountDialog", "Linking account")
        provider_name = self.provider_combo.currentText()
        access_token = self.token_input.text() if provider_name != 'mock' else 'mock_token'
        
        if provider_name == 'plaid' and not access_token:
            logger.warning("LinkAccountDialog", "Linking failed: missing access token")
            QMessageBox.warning(self, "Missing Token", "Please enter an access token.")
            return
        
        account_data = self.account_combo.currentData()
        if not account_data:
            logger.warning("LinkAccountDialog", "Linking failed: no app account selected")
            QMessageBox.warning(self, "No Account", "Please select an app account.")
            return
        
        logger.debug("LinkAccountDialog", f"Linking account {account_data['account_id']} to {provider_name}")
        # Link the account
        success = self.api_manager.link_account(
            provider_name=provider_name,
            access_token=access_token,
            app_account_id=account_data['account_id'],
            app_account_name=account_data['name']
        )
        
        if success:
            logger.info("LinkAccountDialog", f"Account linked successfully from {provider_name}")
            QMessageBox.information(
                self, 
                "Success", 
                f"Successfully linked account(s) from {provider_name}!"
            )
            self.accept()
        else:
            logger.error("LinkAccountDialog", f"Failed to link account from {provider_name}")
            QMessageBox.critical(
                self, 
                "Error", 
                f"Failed to link account. Check logs for details."
            )


class BankingAPIWidget(QWidget):
    """Main widget for banking API integration"""
    
    def __init__(self, bank_instance, user_id=None, parent=None):
        super().__init__(parent)
        logger.debug("BankingAPIWidget", f"Initializing BankingAPIWidget for user {user_id}")
        self.bank_instance = bank_instance
        self.user_id = user_id
        self.api_manager = BankingAPIManager(user_id)
        self.sync_worker = None
        
        self.setup_ui()
        self.load_linked_accounts()
        logger.info("BankingAPIWidget", f"BankingAPIWidget initialized for user {user_id}")
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("<h2>Banking API Integration</h2>")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_linked_accounts)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Linked accounts group
        accounts_group = QGroupBox("Linked Bank Accounts")
        accounts_layout = QVBoxLayout()
        
        # Table
        self.accounts_table = QTableWidget()
        self.accounts_table.setColumnCount(7)
        self.accounts_table.setHorizontalHeaderLabels([
            "Bank Name", "Account Type", "Mask", "App Account", 
            "Last Sync", "Status", "Actions"
        ])
        self.accounts_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.accounts_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        accounts_layout.addWidget(self.accounts_table)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        link_btn = QPushButton("Link New Account")
        link_btn.clicked.connect(self.show_link_dialog)
        buttons_layout.addWidget(link_btn)
        
        sync_all_btn = QPushButton("Sync All Accounts")
        sync_all_btn.clicked.connect(self.sync_all_accounts)
        buttons_layout.addWidget(sync_all_btn)
        
        buttons_layout.addStretch()
        
        accounts_layout.addLayout(buttons_layout)
        accounts_group.setLayout(accounts_layout)
        layout.addWidget(accounts_group)
        
        # Progress section
        progress_group = QGroupBox("Sync Progress")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("")
        progress_layout.addWidget(self.status_label)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        # Provider configuration group
        config_group = QGroupBox("Provider Configuration")
        config_layout = QVBoxLayout()
        
        config_info = QLabel(
            "Configure banking providers in settings.\n"
            "Mock provider is enabled by default for testing."
        )
        config_info.setWordWrap(True)
        config_layout.addWidget(config_info)
        
        # Show configured providers
        providers_label = QLabel(f"Available providers: {', '.join(self.api_manager.providers.keys())}")
        config_layout.addWidget(providers_label)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def load_linked_accounts(self):
        """Load and display linked accounts"""
        logger.debug("BankingAPIWidget", "Loading linked accounts")
        self.api_manager.load_linked_accounts()
        accounts = self.api_manager.get_linked_accounts()
        logger.info("BankingAPIWidget", f"Loaded {len(accounts)} linked accounts")
        
        self.accounts_table.setRowCount(len(accounts))
        
        for row, account in enumerate(accounts):
            # Bank name
            self.accounts_table.setItem(row, 0, QTableWidgetItem(account['bank_account_name']))
            
            # Account type
            acc_type = account.get('bank_account_type', 'Unknown')
            self.accounts_table.setItem(row, 1, QTableWidgetItem(acc_type))
            
            # Mask (last 4 digits)
            mask = account.get('bank_account_mask', 'N/A')
            self.accounts_table.setItem(row, 2, QTableWidgetItem(f"***{mask}"))
            
            # App account
            self.accounts_table.setItem(row, 3, QTableWidgetItem(account['app_account_name']))
            
            # Last sync
            last_sync = account.get('last_sync')
            if last_sync:
                sync_time = datetime.fromisoformat(last_sync)
                sync_str = sync_time.strftime("%Y-%m-%d %H:%M")
            else:
                sync_str = "Never"
            self.accounts_table.setItem(row, 4, QTableWidgetItem(sync_str))
            
            # Status
            status = "Active" if account.get('auto_sync') else "Manual"
            self.accounts_table.setItem(row, 5, QTableWidgetItem(status))
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(4, 2, 4, 2)
            
            sync_btn = QPushButton("Sync")
            sync_btn.clicked.connect(lambda checked, lid=account['link_id']: self.sync_account(lid))
            actions_layout.addWidget(sync_btn)
            
            unlink_btn = QPushButton("Unlink")
            unlink_btn.clicked.connect(lambda checked, lid=account['link_id']: self.unlink_account(lid))
            actions_layout.addWidget(unlink_btn)
            
            actions_widget.setLayout(actions_layout)
            self.accounts_table.setCellWidget(row, 6, actions_widget)
        
        self.status_label.setText(f"Total linked accounts: {len(accounts)}")
    
    def show_link_dialog(self):
        """Show dialog to link a new account"""
        # Get bank accounts from the bank instance
        bank_accounts_list = self.bank_instance.account_manager.get_user_accounts(self.user_id)
        
        if not bank_accounts_list:
            QMessageBox.warning(
                self,
                "No Accounts",
                "Please create at least one bank account in the app first."
            )
            return
        
        # Convert BankAccount objects to dictionaries
        bank_accounts = []
        for acc in bank_accounts_list:
            bank_accounts.append({
                'account_id': acc.account_id,
                'name': acc.get_display_name(),
                'type': acc.account_type
            })
        
        dialog = LinkAccountDialog(self.api_manager, bank_accounts, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_linked_accounts()
    
    def sync_account(self, link_id):
        """Sync a specific account"""
        # Ask for days to sync
        days, ok = self.get_sync_days()
        if not ok:
            return
        
        self.status_label.setText(f"Syncing account...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        
        # Create worker thread
        self.sync_worker = SyncWorker(self.api_manager, link_id, days, self.bank_instance)
        self.sync_worker.progress.connect(self.on_sync_progress)
        self.sync_worker.finished.connect(self.on_sync_finished)
        self.sync_worker.error.connect(self.on_sync_error)
        self.sync_worker.start()
    
    def sync_all_accounts(self):
        """Sync all linked accounts"""
        days, ok = self.get_sync_days()
        if not ok:
            return
        
        accounts = self.api_manager.get_linked_accounts()
        if not accounts:
            QMessageBox.information(self, "No Accounts", "No linked accounts to sync.")
            return
        
        self.status_label.setText(f"Syncing {len(accounts)} account(s)...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        # Sync all accounts
        results = self.api_manager.sync_all_accounts(days, self.bank_instance)
        
        # Show results
        total_count = sum(r[0] for r in results.values())
        all_errors = []
        for errors in [r[1] for r in results.values()]:
            all_errors.extend(errors)
        
        self.progress_bar.setVisible(False)
        
        if all_errors:
            error_msg = "\n".join(all_errors[:5])  # Show first 5 errors
            if len(all_errors) > 5:
                error_msg += f"\n... and {len(all_errors) - 5} more errors"
            QMessageBox.warning(
                self,
                "Sync Completed with Errors",
                f"Imported {total_count} transactions.\n\nErrors:\n{error_msg}"
            )
        else:
            QMessageBox.information(
                self,
                "Sync Complete",
                f"Successfully imported {total_count} new transactions!"
            )
        
        self.status_label.setText(f"Synced {total_count} transactions from {len(accounts)} account(s)")
        self.load_linked_accounts()
    
    def unlink_account(self, link_id):
        """Unlink an account"""
        reply = QMessageBox.question(
            self,
            "Confirm Unlink",
            "Are you sure you want to unlink this account?\n"
            "This will not delete existing transactions.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success = self.api_manager.unlink_account(link_id)
            if success:
                QMessageBox.information(self, "Success", "Account unlinked successfully.")
                self.load_linked_accounts()
            else:
                QMessageBox.critical(self, "Error", "Failed to unlink account.")
    
    def get_sync_days(self):
        """Ask user how many days to sync"""
        from PyQt6.QtWidgets import QInputDialog
        days, ok = QInputDialog.getInt(
            self,
            "Sync Period",
            "How many days back to sync?",
            value=30,
            min=1,
            max=365
        )
        return days, ok
    
    def on_sync_progress(self, message):
        """Update progress message"""
        self.status_label.setText(message)
    
    def on_sync_finished(self, result):
        """Handle sync completion"""
        self.progress_bar.setVisible(False)
        
        count = result['count']
        errors = result['errors']
        
        if errors:
            error_msg = "\n".join(errors[:5])
            if len(errors) > 5:
                error_msg += f"\n... and {len(errors) - 5} more errors"
            QMessageBox.warning(
                self,
                "Sync Completed with Errors",
                f"Imported {count} transactions.\n\nErrors:\n{error_msg}"
            )
        else:
            QMessageBox.information(
                self,
                "Sync Complete",
                f"Successfully imported {count} new transactions!"
            )
        
        self.status_label.setText(f"Last sync: {count} new transactions")
        self.load_linked_accounts()
    
    def on_sync_error(self, error_msg):
        """Handle sync error"""
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Sync Error", f"Failed to sync:\n{error_msg}")
        self.status_label.setText("Sync failed")


if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # Create mock bank instance for testing
    class MockBank:
        def __init__(self):
            self.transactions = []
            from src.bank_accounts import BankAccountManager
            self.account_manager = BankAccountManager()
        
        def add_transaction(self, **kwargs):
            tx = {'identifier': 'test_' + str(len(self.transactions)), **kwargs}
            self.transactions.append(tx)
            return tx
        
        def save(self):
            pass
    
    bank = MockBank()
    widget = BankingAPIWidget(bank, user_id='test_user')
    widget.setMinimumSize(900, 600)
    widget.show()
    
    sys.exit(app.exec())
