"""
Banking API Integration UI Widget

Provides user interface for linking bank accounts and syncing transactions.
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
    QFormLayout, QLineEdit, QComboBox, QSpinBox, QCheckBox,
    QMessageBox, QGroupBox, QTextEdit, QProgressBar
)
from PyQt6.QtCore import Qt, QThread, QTimer, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices, QIcon
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


PLAID_LINK_HELPER_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Financial Manager Plaid Link</title>
    <script src="https://cdn.plaid.com/link/v2/stable/link-initialize.js"></script>
    <style>
        :root {
            color-scheme: light;
            --bg: #f4efe5;
            --panel: #fffaf2;
            --ink: #1f2933;
            --accent: #006d77;
            --accent-soft: #e4f3f0;
            --border: #d8cbb8;
        }
        body {
            margin: 0;
            font-family: Georgia, 'Times New Roman', serif;
            background: radial-gradient(circle at top left, #fffdf7, var(--bg));
            color: var(--ink);
            min-height: 100vh;
            display: grid;
            place-items: center;
            padding: 24px;
        }
        .panel {
            width: min(680px, 100%);
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 20px;
            box-shadow: 0 18px 48px rgba(31, 41, 51, 0.12);
            padding: 28px;
        }
        h1 {
            margin: 0 0 12px;
            font-size: 2rem;
        }
        p {
            line-height: 1.55;
            margin: 0 0 14px;
        }
        .status {
            padding: 14px 16px;
            background: var(--accent-soft);
            border-radius: 14px;
            margin: 18px 0;
            min-height: 24px;
        }
        button {
            border: 0;
            border-radius: 999px;
            background: var(--accent);
            color: white;
            font: inherit;
            padding: 12px 20px;
            cursor: pointer;
        }
        code {
            display: block;
            white-space: pre-wrap;
            overflow-wrap: anywhere;
            background: #f7f1e6;
            border-radius: 14px;
            padding: 12px;
            border: 1px solid var(--border);
            min-height: 22px;
        }
    </style>
</head>
<body>
    <main class="panel">
        <h1>Connect with Plaid</h1>
        <p>This page launches Plaid Link for Financial Manager. When the connection succeeds, the app will capture the resulting public token automatically.</p>
        <button id="launch">Open Plaid Link</button>
        <div class="status" id="status">Preparing Plaid Link...</div>
        <p>If your browser blocks the popup, click the button again.</p>
        <code id="token"></code>
    </main>
    <script>
        const linkToken = __LINK_TOKEN__;
        const statusEl = document.getElementById('status');
        const tokenEl = document.getElementById('token');

        function setStatus(message) {
            statusEl.textContent = message;
        }

        async function postJson(path, payload) {
            const response = await fetch(path, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                throw new Error(`Local callback failed with ${response.status}`);
            }
        }

        const handler = Plaid.create({
            token: linkToken,
            onSuccess: async (publicToken, metadata) => {
                tokenEl.textContent = publicToken;
                setStatus('Plaid Link completed. Return to Financial Manager to finish linking the account.');
                try {
                    await postJson('/api/plaid/success', {
                        public_token: publicToken,
                        metadata,
                    });
                } catch (error) {
                    setStatus(`Plaid Link succeeded, but the local callback failed: ${error.message}`);
                }
            },
            onExit: async (error, metadata) => {
                if (!error) {
                    setStatus('Plaid Link closed before completion.');
                    return;
                }

                setStatus(error.display_message || error.error_message || 'Plaid Link exited with an error.');
                try {
                    await postJson('/api/plaid/error', { error, metadata });
                } catch (postError) {
                    setStatus(`Plaid Link exited and the local callback failed: ${postError.message}`);
                }
            },
        });

        document.getElementById('launch').addEventListener('click', () => handler.open());

        window.addEventListener('load', () => {
            setStatus('Ready. Launching Plaid Link...');
            handler.open();
        });
    </script>
</body>
</html>
"""


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


class PlaidLinkHelperServer:
    """Serve a local Plaid Link helper page and capture its public token."""

    def __init__(self, link_token):
        self.link_token = link_token
        self.public_token = None
        self.metadata = {}
        self.error_message = None
        self._server = None
        self._thread = None

    def start(self):
        """Start the helper server and return the launch URL."""
        if self._server:
            return f"http://127.0.0.1:{self._server.server_address[1]}/"

        helper = self

        class Handler(BaseHTTPRequestHandler):
            def _send_html(self, body, status=200):
                payload = body.encode('utf-8')
                self.send_response(status)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def _send_json(self, payload, status=200):
                body = json.dumps(payload).encode('utf-8')
                self.send_response(status)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                if self.path not in ('/', '/index.html'):
                    self.send_error(404)
                    return

                page = PLAID_LINK_HELPER_HTML.replace(
                    '__LINK_TOKEN__',
                    json.dumps(helper.link_token)
                )
                self._send_html(page)

            def do_POST(self):
                if self.path not in ('/api/plaid/success', '/api/plaid/error'):
                    self.send_error(404)
                    return

                raw_length = self.headers.get('Content-Length', '0')
                try:
                    content_length = int(raw_length)
                except ValueError:
                    content_length = 0

                raw_body = self.rfile.read(content_length) if content_length else b'{}'
                try:
                    payload = json.loads(raw_body.decode('utf-8') or '{}')
                except json.JSONDecodeError:
                    payload = {}

                if self.path == '/api/plaid/success':
                    helper.public_token = payload.get('public_token')
                    helper.metadata = payload.get('metadata') or {}
                    helper.error_message = None
                else:
                    error = payload.get('error') or {}
                    helper.error_message = (
                        error.get('display_message')
                        or error.get('error_message')
                        or 'Plaid Link closed before completion.'
                    )

                self._send_json({'ok': True})

            def log_message(self, format, *args):
                return

        self._server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        return f"http://127.0.0.1:{self._server.server_address[1]}/"

    def stop(self):
        """Stop the helper server."""
        if not self._server:
            return

        self._server.shutdown()
        self._server.server_close()
        self._server = None
        self._thread = None


class LinkAccountDialog(QDialog):
    """Dialog for linking a new bank account."""

    def __init__(self, api_manager, bank_accounts, parent=None):
        super().__init__(parent)
        logger.debug("LinkAccountDialog", "Initializing LinkAccountDialog")
        self.api_manager = api_manager
        self.bank_accounts = bank_accounts
        self.provider_lookup = {}
        self.plaid_helper = None
        self.plaid_poll_timer = QTimer(self)
        self.plaid_poll_timer.setInterval(500)
        self.plaid_poll_timer.timeout.connect(self.check_plaid_link_status)
        self.setWindowTitle("Link Bank Account")
        self.setModal(True)
        self.setMinimumWidth(560)

        self.setup_ui()
        logger.info("LinkAccountDialog", f"LinkAccountDialog initialized with {len(bank_accounts)} available accounts")

    def setup_ui(self):
        layout = QVBoxLayout()

        info_label = QLabel(
            "Link a real bank account to automatically import transactions.\n"
            "Demo Bank remains available as a sample institution for testing."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        form_layout = QFormLayout()

        self.provider_combo = QComboBox()
        for provider in self.api_manager.get_available_providers():
            self.provider_lookup[provider['provider_name']] = provider
            self.provider_combo.addItem(provider['display_name'], userData=provider['provider_name'])
        self.provider_combo.currentIndexChanged.connect(self.on_provider_changed)
        form_layout.addRow("Banking Provider:", self.provider_combo)

        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("Paste the Plaid public token or access token")
        self.token_label = QLabel("Plaid Token:")
        form_layout.addRow(self.token_label, self.token_input)

        self.plaid_link_button = QPushButton("Open Plaid Link")
        self.plaid_link_button.clicked.connect(self.start_plaid_link_flow)
        form_layout.addRow("", self.plaid_link_button)

        self.account_combo = QComboBox()
        for account in self.bank_accounts:
            self.account_combo.addItem(
                f"{account['name']} ({account['type']})",
                userData=account
            )
        form_layout.addRow("Link to App Account:", self.account_combo)

        layout.addLayout(form_layout)

        self.instructions_text = QTextEdit()
        self.instructions_text.setReadOnly(True)
        self.instructions_text.setMaximumHeight(120)
        layout.addWidget(QLabel("Instructions:"))
        layout.addWidget(self.instructions_text)

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
        self.on_provider_changed()

    def current_provider_name(self):
        """Return the internal provider name for the current selection."""
        return self.provider_combo.currentData() or self.provider_combo.currentText()

    def on_provider_changed(self, *_):
        """Update the dialog based on the selected provider."""
        provider_name = self.current_provider_name()

        if provider_name != 'plaid':
            self.cleanup_plaid_helper()

        self.link_button.setEnabled(provider_name in ('plaid', 'mock'))

        if provider_name == 'mock':
            self.token_input.setEnabled(False)
            self.token_input.clear()
            self.token_label.setEnabled(False)
            self.plaid_link_button.setVisible(False)
            self.instructions_text.setPlainText(
                "Demo Bank behaves like a normal institution option, but it returns sample transactions.\n"
                "No credentials are required; just select the app account you want to connect."
            )
            return

        if provider_name == 'plaid':
            self.token_input.setEnabled(True)
            self.token_label.setEnabled(True)
            self.plaid_link_button.setVisible(True)
            self.instructions_text.setPlainText(
                "For Plaid:\n"
                "1. Click 'Open Plaid Link' to launch a local Plaid Link helper page\n"
                "2. Complete the Link flow in your browser\n"
                "3. Financial Manager will capture the resulting public token automatically\n"
                "4. Click 'Link Account' to exchange the token and store the connection\n"
                "Note: Plaid client_id and secret must be configured first."
            )
            return

        self.token_input.setEnabled(False)
        self.token_input.clear()
        self.token_label.setEnabled(False)
        self.plaid_link_button.setVisible(False)
        self.instructions_text.setPlainText(
            "This provider uses a provider-specific setup flow that is not exposed in this dialog yet.\n"
            "Plaid and Demo Bank are ready to use here."
        )

    def start_plaid_link_flow(self):
        """Create a Plaid link token and open a local helper page."""
        logger.debug("LinkAccountDialog", "Starting Plaid Link flow")
        link_token = self.api_manager.create_plaid_link_token()
        if not link_token:
            QMessageBox.critical(
                self,
                "Plaid Link Error",
                "Could not create a Plaid link token. Check your Plaid credentials and environment settings."
            )
            return

        self.cleanup_plaid_helper()
        self.plaid_helper = PlaidLinkHelperServer(link_token)
        helper_url = self.plaid_helper.start()
        self.plaid_poll_timer.start()
        self.instructions_text.setPlainText(
            "Plaid Link helper is running locally. Finish the bank login flow in your browser.\n"
            "When the public token is captured, it will populate this dialog automatically."
        )
        QDesktopServices.openUrl(QUrl(helper_url))

    def check_plaid_link_status(self):
        """Poll the helper server for a completed Plaid Link flow."""
        if not self.plaid_helper:
            return

        if self.plaid_helper.public_token:
            public_token = self.plaid_helper.public_token
            self.token_input.setText(public_token)
            self.instructions_text.setPlainText(
                "Plaid Link completed successfully. Review the selected app account and click 'Link Account' to finish linking the bank feed."
            )
            self.cleanup_plaid_helper()
            QMessageBox.information(
                self,
                "Plaid Ready",
                "Plaid Link completed. The public token has been captured and is ready to link."
            )
            return

        if self.plaid_helper.error_message:
            error_message = self.plaid_helper.error_message
            self.cleanup_plaid_helper()
            QMessageBox.warning(self, "Plaid Link Closed", error_message)

    def cleanup_plaid_helper(self):
        """Stop any active Plaid helper instance."""
        self.plaid_poll_timer.stop()
        if self.plaid_helper:
            self.plaid_helper.stop()
            self.plaid_helper = None

    def link_account(self):
        """Link the selected account."""
        logger.debug("LinkAccountDialog", "Linking account")
        provider_name = self.current_provider_name()
        token_value = self.token_input.text().strip()

        if provider_name == 'plaid' and not token_value:
            logger.warning("LinkAccountDialog", "Linking failed: missing Plaid token")
            QMessageBox.warning(self, "Missing Token", "Complete Plaid Link or paste a Plaid token first.")
            return

        account_data = self.account_combo.currentData()
        if not account_data:
            logger.warning("LinkAccountDialog", "Linking failed: no app account selected")
            QMessageBox.warning(self, "No Account", "Please select an app account.")
            return

        provider_params = {}
        if provider_name == 'plaid':
            if token_value.startswith('access-'):
                provider_params['access_token'] = token_value
            else:
                provider_params['public_token'] = token_value

        logger.debug("LinkAccountDialog", f"Linking account {account_data['account_id']} to {provider_name}")
        success = self.api_manager.link_account(
            provider_name=provider_name,
            app_account_id=account_data['account_id'],
            app_account_name=account_data['name'],
            **provider_params
        )

        if success:
            self.cleanup_plaid_helper()
            logger.info("LinkAccountDialog", f"Account linked successfully from {provider_name}")
            QMessageBox.information(
                self,
                "Success",
                f"Successfully linked account(s) from {self.provider_combo.currentText()}!"
            )
            self.accept()
            return

        logger.error("LinkAccountDialog", f"Failed to link account from {provider_name}")
        QMessageBox.critical(self, "Error", "Failed to link account. Check logs for details.")

    def reject(self):
        self.cleanup_plaid_helper()
        super().reject()

    def closeEvent(self, event):
        self.cleanup_plaid_helper()
        super().closeEvent(event)


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
            "Plaid brings in live data, while Demo Bank remains available for testing."
        )
        config_info.setWordWrap(True)
        config_layout.addWidget(config_info)
        
        # Show configured providers
        provider_names = ', '.join(
            provider['display_name']
            for provider in self.api_manager.get_available_providers()
        )
        providers_label = QLabel(f"Available providers: {provider_names}")
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
            bank_name = (
                account.get('institution_name')
                or account.get('provider_display_name')
                or account['bank_account_name']
            )
            self.accounts_table.setItem(row, 0, QTableWidgetItem(bank_name))
            
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
